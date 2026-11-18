"""Moteur de rendu V5 « Worldclass » — quatrième couche (rendu de référence).

Il **n'écrit aucune décision** : tout vient du plan JSON produit par
`engine/montage_plan_builder.py` et de la configuration `config/T1_worldclass_v5.json`.

Quatre corrections de fond par rapport au moteur de clôture V4
--------------------------------------------------------------
1. **Aucun gel** : la durée de chaque plan est construite à partir des images réellement
   disponibles ; `freeze_tail_f` n'est plus lu (et le plan l'interdit).
2. **Remappage temporel continu** : chaque image de sortie connaît sa position source continue
   (`positions_sous_pixel`) et son image (`indices_sources`). Vitesse d'attaque, cœur et sortie
   normalisées sur la fenêtre disponible.
3. **Caméra sous-pixel** : un seul `cv2.warpAffine` avec matrice affine flottante et
   interpolation cubique fait *à la fois* le recadrage et la mise à l'échelle finale. Plus aucun
   mouvement en escalier, plus aucune suite d'agrandissements.
4. **Un seul encodage avec perte** : les sources sont décodées en mémoire, composées, puis
   envoyées une seule fois à libx264. Aucun fichier intermédiaire encodé (V4 en produisait un
   par scène).

    PYTHONPATH=. python3 engine/motion_v5.py --plan reports/montage_plan_v5_demo.json \
        --output output/output_T1_master_v5.mp4 --manifest reports/execution_manifest_v5.json
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from engine.adaptive_graphics_v5 import GraphicsV5, courbe
from engine.food_cinema_transitions import apply_transition

ROOT = Path(__file__).resolve().parents[1]
FPS = 30


# --------------------------------------------------------------------------- #
def lut_colorimetrie(correction: dict[str, Any]) -> np.ndarray:
    """Table de correction par scène : gamma borné + gains de balance bornés.

    Appliquée en une seule passe LUT (0 allocation par image), identique au futur shader.
    """
    gamma = float(correction.get("gamma", 1.0))
    warm = float(correction.get("rechauffement", 0.0))
    xs = np.arange(256, dtype=np.float32) / 255.0
    base = np.power(np.clip(xs, 0, 1), 1.0 / max(0.2, gamma)) * 255.0
    lut = np.zeros((256, 3), dtype=np.uint8)
    lut[:, 0] = np.clip(base * (1.0 - warm * 0.05), 0, 255).astype(np.uint8)   # bleu
    lut[:, 1] = np.clip(base, 0, 255).astype(np.uint8)                          # vert
    lut[:, 2] = np.clip(base * (1.0 + warm), 0, 255).astype(np.uint8)           # rouge
    return np.ascontiguousarray(lut).reshape(1, 256, 3)


class ShotReader:
    """Lecture d'une fenêtre source, image par image, sans gel ni interpolation temporelle."""

    def __init__(self, path: Path, in_frame: int, frames: int):
        self.cap = cv2.VideoCapture(str(path))
        if not self.cap.isOpened():
            raise RuntimeError(f"Source illisible : {path}")
        self.path = path
        self.in_frame = int(in_frame)
        self.frames = int(frames)
        self.pos = -1
        # cache volontairement minuscule : sept lecteurs × 240 images tiendraient 3 Go
        self.cache: dict[int, np.ndarray] = {}
        self.cache_max = 6
        self.last: np.ndarray | None = None

    def goto(self, absolute: int) -> np.ndarray:
        if absolute in self.cache:
            return self.cache[absolute]
        if absolute < self.pos:                      # retour en arrière : on ré-ouvre
            self.cap.release()
            self.cap = cv2.VideoCapture(str(self.path))
            self.pos = -1
        while self.pos < absolute:
            ok, img = self.cap.read()
            if not ok:
                break
            self.pos += 1
            self.last = img
        if self.last is None:
            raise RuntimeError(f"Décodage impossible : {self.path}")
        if len(self.cache) >= self.cache_max:
            self.cache.pop(next(iter(self.cache)))
        self.cache[absolute] = self.last
        return self.last

    def frame(self, local_index: int) -> np.ndarray:
        idx = max(0, min(self.frames - 1, int(local_index)))
        return self.goto(self.in_frame + idx)

    def release(self) -> None:
        self.cap.release()


def camera_frame(src: np.ndarray, k: float, pan_x: float, pan_y: float,
                 anchor: tuple[float, float], out_w: int, out_h: int,
                 interpolation: int = cv2.INTER_CUBIC) -> np.ndarray:
    """Recadrage + mise à l'échelle en **un seul** échantillonnage sous-pixel.

    `k` est le zoom numérique (>= 1). `pan_x`/`pan_y` sont des fractions de la dimension source.
    La fenêtre est centrée sur l'ancre du sujet, puis contrainte à rester dans l'image.
    """
    hs, ws = src.shape[:2]
    k = max(1.0, float(k))
    ratio = out_w / out_h
    ch = hs / k
    cw = ch * ratio
    if cw > ws:
        cw = ws / max(1e-6, 1.0) / 1.0
        ch = cw / ratio
    cx = anchor[0] * ws + pan_x * ws
    cy = anchor[1] * hs + pan_y * hs
    x0 = min(max(0.0, cx - cw / 2), ws - cw)
    y0 = min(max(0.0, cy - ch / 2), hs - ch)
    m = np.array([[out_w / cw, 0, -x0 * out_w / cw],
                  [0, out_h / ch, -y0 * out_h / ch]], dtype=np.float32)
    return cv2.warpAffine(src, m, (out_w, out_h), flags=interpolation,
                          borderMode=cv2.BORDER_REPLICATE)


def plan_camera(shot: dict[str, Any]) -> dict[str, Any]:
    return shot["camera"]


def camera_at(shot: dict[str, Any], local: int) -> tuple[float, float, float]:
    cam = plan_camera(shot)
    n = max(1, int(shot["out_frames"]))
    t = min(1.0, max(0.0, local / (n - 1)))
    e = courbe(cam.get("courbe", "easeInOutQuad"))(t)
    k = cam["zoom"]["debut"] + (cam["zoom"]["fin"] - cam["zoom"]["debut"]) * e
    px = cam["pan_rel"]["debut"] + (cam["pan_rel"]["fin"] - cam["pan_rel"]["debut"]) * e
    py = px if cam.get("axe_pan") == "vertical" else 0.0
    if cam.get("axe_pan") == "vertical":
        px = 0.0
    return (float(k), float(px), float(py))


def render(plan_path: Path, output: Path, manifest_path: Path | None = None,
           quality: str = "standard", limit_frames: int | None = None) -> dict[str, Any]:
    t_global = time.perf_counter()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    config = json.loads((ROOT / plan["config"]).read_text(encoding="utf-8"))
    analysis = json.loads((ROOT / plan["analyse"]).read_text(encoding="utf-8"))
    out_cfg = plan["output"]
    W, H, FRAMES = int(out_cfg["width"]), int(out_cfg["height"]), int(out_cfg["frames"])
    if limit_frames:
        FRAMES = min(FRAMES, int(limit_frames))

    interp = cv2.INTER_CUBIC if config["camera"]["interpolation"] == "INTER_CUBIC" else cv2.INTER_LINEAR
    if config["qualite"][quality].get("interpolation") == "INTER_LINEAR":
        interp = cv2.INTER_LINEAR

    graphics = GraphicsV5(ROOT / plan["config"], plan["display"], analysis, quality=quality)
    luts = {s["id"]: lut_colorimetrie(s["colorimetrie"]) for s in plan["scenes"]}
    palette = {k: tuple(v) for k, v in config["palette"].items()}

    readers: dict[str, ShotReader] = {}
    for shot in plan["shots"]:
        readers[shot["id"]] = ShotReader(ROOT / shot["source"]["file"], shot["source"]["in_frame"],
                                         shot["source"]["source_frames"])

    shots = plan["shots"]
    cuts = {int(c["debut_f"]): c for c in plan["cuts"] if int(c["dur_f"]) > 0}
    manifest: dict[str, Any] = {
        "moteur": "engine/motion_v5.py", "plan": plan_path.name,
        "config": plan["config"], "version_plan": plan["version"],
        "profil": plan["profil"]["id"], "qualite": quality,
        "frames": FRAMES, "fps": FPS, "resolution": f"{W}x{H}",
        "transitions": [], "plans": [], "graphismes": graphics.rapport(),
        "render_s": None, "encodeur": config["rendu"]["encodeur"],
    }

    def shot_at(fno: int) -> tuple[int, dict[str, Any], int]:
        for i, s in enumerate(shots):
            if int(s["out_start_f"]) <= fno < int(s["out_end_f"]):
                return i, s, fno - int(s["out_start_f"])
        return len(shots) - 1, shots[-1], int(shots[-1]["out_frames"]) - 1

    def shot_frame(shot: dict[str, Any], local: int) -> np.ndarray:
        idx = int(shot["speed"]["indices_sources"][max(0, min(local, len(shot["speed"]["indices_sources"]) - 1))])
        raw = readers[shot["id"]].frame(idx)
        k, px, py = camera_at(shot, local)
        ancre = (float(shot["camera"]["ancre_source"]["x"]), float(shot["camera"]["ancre_source"]["y"]))
        img = camera_frame(raw, k, px, py, ancre, W, H, interp)
        lut = luts[shot["scene"]]
        return cv2.LUT(img, lut)

    output.parent.mkdir(parents=True, exist_ok=True)
    enc = config["rendu"]["encodeur"]
    proc = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                             "-f", "rawvideo", "-pixel_format", "bgr24",
                             "-video_size", f"{W}x{H}", "-framerate", str(FPS), "-i", "-",
                             "-an", "-frames:v", str(FRAMES), "-c:v", enc["codec"],
                             "-preset", enc["preset"], "-crf", str(enc["crf"]),
                             "-pix_fmt", enc["pix_fmt"], "-movflags", enc["movflags"], str(output)],
                            stdin=subprocess.PIPE)
    if proc.stdin is None:
        raise RuntimeError("ffmpeg n'a pas ouvert le tube")

    transitions_vues: dict[str, dict[str, Any]] = {}
    try:
        for fno in range(FRAMES):
            i, shot, local = shot_at(fno)
            transition = None
            for debut, c in cuts.items():
                if debut <= fno < debut + int(c["dur_f"]):
                    transition = c
                    break
            if transition is None:
                img = shot_frame(shot, local)
            else:
                idx_prev = i - 1
                prev = shots[idx_prev]
                p = (fno - int(transition["debut_f"]) + 1) / int(transition["dur_f"])
                # les deux flux avancent : le plan sortant continue, le plan entrant démarre
                local_old = int(prev["out_frames"]) - 1 - (int(transition["fin_f"]) - fno)
                local_new = fno - int(transition["debut_f"])
                old = shot_frame(prev, max(0, min(local_old, int(prev["out_frames"]) - 1)))
                new = shot_frame(shot, max(0, min(local_new, int(shot["out_frames"]) - 1)))
                img = apply_transition(transition["transition"], old, new, p,
                                       transition["parametres"], palette, interp)
                nom = transition["transition"]
                entry = transitions_vues.setdefault(nom, {"transition": nom, "coupe_f": transition["coupe_f"],
                                                          "debut_f": transition["debut_f"],
                                                          "fin_f": transition["fin_f"], "images": [],
                                                          "flux_sortant_avance": [], "flux_entrant_avance": []})
                entry["images"].append(fno)
                entry["flux_sortant_avance"].append(local_old)
                entry["flux_entrant_avance"].append(local_new)

            img = graphics.draw(img, fno)
            proc.stdin.write(np.ascontiguousarray(img, dtype=np.uint8).tobytes())
            if fno % 150 == 0:
                print(f"  image {fno}/{FRAMES}", flush=True)
    finally:
        proc.stdin.close()
        code = proc.wait()
        for r in readers.values():
            r.release()
    if code != 0:
        raise RuntimeError(f"ffmpeg a échoué (code {code})")

    manifest["render_s"] = round(time.perf_counter() - t_global, 2)
    for nom, e in transitions_vues.items():
        sortant = e["flux_sortant_avance"]
        entrant = e["flux_entrant_avance"]
        manifest["transitions"].append({
            "transition": nom, "coupe_f": e["coupe_f"], "debut_f": e["debut_f"], "fin_f": e["fin_f"],
            "images": len(e["images"]),
            "flux_sortant_de_vers": [min(sortant), max(sortant)],
            "flux_entrant_de_vers": [min(entrant), max(entrant)],
            "sortant_avance": bool(len(set(sortant)) > 1),
            "entrant_avance": bool(len(set(entrant)) > 1),
        })
    for shot in shots:
        manifest["plans"].append({
            "id": shot["id"], "scene": shot["scene"], "intention": shot["intention"],
            "sortie_f": [int(shot["out_start_f"]), int(shot["out_end_f"])],
            "source_f": [int(shot["source"]["in_frame"]),
                         int(shot["source"]["in_frame"]) + int(shot["source"]["source_frames"]) - 1],
            "vitesse": {k: shot["speed"][k] for k in ("vitesse_min", "vitesse_max",
                                                      "vitesse_moyenne_reelle", "images_repetees",
                                                      "repetition_max_consecutive", "gel_de_fin")},
            "camera": shot["camera"], "lip_sync_safe": shot["lip_sync_safe"],
        })
    manifest["sha256_plan"] = plan.get("sha256_plan")
    if manifest_path:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"video": str(output), "frames": FRAMES, "render_s": manifest["render_s"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Rendu du master V5")
    ap.add_argument("--plan", default="reports/montage_plan_v5_demo.json")
    ap.add_argument("--output", default="output/output_T1_master_v5.mp4")
    ap.add_argument("--manifest", default="reports/execution_manifest_v5.json")
    ap.add_argument("--quality", default="standard", choices=["standard", "android_leger"])
    args = ap.parse_args(argv)
    res = render(ROOT / args.plan, ROOT / args.output, ROOT / args.manifest, quality=args.quality)
    print(f"rendu {res['frames']} images en {res['render_s']} s → {res['video']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
