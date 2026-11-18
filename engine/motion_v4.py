"""Moteur de montage T1 — réconcilié (clôture).

Ce que le moteur lit **dans les fichiers de configuration** (rien n'est codé en dur) :

| Élément | Fichier consommé |
|---|---|
| Fenêtre source de chaque plan (`in_frame`, `source_frames`, gel) | `render_plan_v4_demo.json` → `shots[].source` |
| Mouvement caméra (`base`, `k_ratio`, `pan_px`, `easing`, `dur_f`) | `render_plan_v4_demo.json` → `shots[].zoom_curve` |
| Identifiant et durée des transitions | `render_plan_v4_demo.json` → `cuts[].transition` + bibliothèque V1.2 |
| Fenêtre de chaque bloc graphique | `render_plan_v4_demo.json` → `overlays[].start_f/end_f` |
| Géométrie, typographie, couleurs, forme, espacements, entrées/sorties des 8 blocs | `config/T1_presentation_v3_1.json` → `engine/presentation.py` |

Définition de travail : les prises ne sont **plus** mises à l'échelle à la normalisation. Le recadrage
du plan se fait dans les pixels natifs du rush (606×1080 ou 404×720), puis une **seule** mise à
l'échelle 720×1280 a lieu en fin de chaîne. C'est ce qui récupère la netteté perdue.

    PYTHONPATH=. python3 engine/motion_v4.py --plan render_plan_v4_demo.json \
        --output output/output_T1_master_final.mp4 --manifest reports/execution_manifest_v4.json
"""
from __future__ import annotations

import json
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image

from engine.presentation import Presentation, courbe

ROOT = Path(__file__).resolve().parents[1]
W, H, FPS, FRAMES = 720, 1280, 30, 900

# Bibliothèque de transitions V1.2. `rendu` nomme la famille visuelle effectivement dessinée.
# Les trois grandes transitions reprennent la dynamique de la V3.1 approuvée (voir §7 du rapport).
TRANSITIONS = {
    "TR01": {"nom": "cut_sec", "dur_f": 0, "rendu": "cut"},
    "TR02": {"nom": "punch_cut", "dur_f": 6, "rendu": "punch_cut"},
    "TR03": {"nom": "wipe_geometrique", "dur_f": 6, "rendu": "diagonale"},
    "TR04": {"nom": "wipe_directionnel", "dur_f": 6, "rendu": "whip_blur"},
    "TR05": {"nom": "fondu_court_crossfade", "dur_f": 6, "rendu": "fondu"},
    "TR06": {"nom": "speed_ramp_entrant", "dur_f": 6, "rendu": "push_rampe"},
    "TR07": {"nom": "match_cut", "dur_f": 0, "rendu": "cut"},
    "TR08": {"nom": "mask_reveal", "dur_f": 7, "rendu": "diagonale"},  # hors pilote V1.2
}


def clamp01(t: float) -> float:
    return max(0.0, min(1.0, float(t)))


# --------------------------------------------------------------------------- #
# caméra pilotée par le plan
def camera_move(frame: np.ndarray, local: int, duration: int, shot: dict[str, Any]) -> np.ndarray:
    curve = shot["zoom_curve"]
    params = curve.get("parameters") or {}
    mid = curve.get("movement_id", "")
    base = float(curve.get("base", 1.0))
    prog = clamp01(local / max(1, duration - 1))
    e = courbe(params.get("easing"))(prog)

    zoom, dx, dy = 1.0, 0.0, 0.0
    k_ratio = params.get("k_ratio")
    if k_ratio:
        k0, k1 = float(k_ratio[0]), float(k_ratio[1])
        if mid == "MV03":                      # push_in_rapide : attaque courte puis maintien
            e = courbe("easeOutQuint")(clamp01(local / max(1, int(params.get("dur_f", 6)))))
        zoom = k0 + (k1 - k0) * e
    pan = params.get("pan_px")
    if pan:
        p0, p1 = float(pan[0]), float(pan[1])
        delta = p0 + (p1 - p0) * e
        if mid == "MV06":
            dy = delta / H
        else:
            dx = delta / W

    h, w = frame.shape[:2]
    scale = max(1.0, base * zoom)
    cw, ch = int(round(w / scale)), int(round(h / scale))
    cx, cy = w * (0.5 + dx), h * (0.5 + dy)
    x0 = int(max(0, min(w - cw, cx - cw / 2)))
    y0 = int(max(0, min(h - ch, cy - ch / 2)))
    crop = frame[y0:y0 + ch, x0:x0 + cw]
    # une seule mise à l'échelle, en fin de chaîne
    return cv2.resize(crop, (W, H), interpolation=cv2.INTER_LANCZOS4)


# --------------------------------------------------------------------------- #
# transitions
def do_transition(old: np.ndarray, new: np.ndarray, rendu: str, p: float,
                  palette: dict[str, tuple[int, int, int]]) -> np.ndarray:
    p = clamp01(p)
    orange = np.array(palette["orange"][::-1], dtype=np.uint8)

    if rendu == "punch_cut":
        e = courbe("easeOutQuint")(p)
        scale = 0.94 + 0.06 * e
        m = cv2.getRotationMatrix2D((W / 2, H / 2), 0, scale)
        incoming = cv2.warpAffine(new, m, (W, H), borderMode=cv2.BORDER_REFLECT_101)
        return cv2.addWeighted(incoming, e, old, 1 - e, 0)

    if rendu == "diagonale":               # V3.1 : révélation diagonale + ruban orange
        e = courbe("easeInOutQuad")(p)
        edge = int(-550 + 1300 * e)
        yy, xx = np.mgrid[0:H, 0:W]
        signed = xx - 0.42 * yy
        out = old.copy()
        mask = signed <= edge
        out[mask] = new[mask]
        ribbon = (np.abs(signed - edge) < 13) & ~mask
        out[ribbon] = orange
        return out

    if rendu == "whip_blur":               # V3.1 : translation + flou directionnel (whip pan)
        e = courbe("easeInOutQuad")(p)
        mat_old = np.float32([[1, 0, -int(W * e)], [0, 1, 0]])
        mat_new = np.float32([[1, 0, int(W * (1.0 - e))], [0, 1, 0]])
        a = cv2.warpAffine(old, mat_old, (W, H), borderMode=cv2.BORDER_REFLECT_101)
        b = cv2.warpAffine(new, mat_new, (W, H), borderMode=cv2.BORDER_REFLECT_101)
        seam = int(W * (1.0 - e))
        mask = np.tile((np.arange(W) >= seam).astype(np.float32), (H, 1))
        feather = max(1, int(8 + 18 * math.sin(math.pi * e)))
        mask = cv2.GaussianBlur(mask, (feather * 2 + 1, 1), 0)[:, :, None]
        out = (a.astype(np.float32) * (1 - mask) + b.astype(np.float32) * mask).astype(np.uint8)
        blur = max(0, int(34 * math.sin(math.pi * p)))
        if blur >= 3:
            out = cv2.GaussianBlur(out, (blur * 2 + 1, 1), 0)
        return out

    if rendu == "push_rampe":              # V3.1 : directional push (échelles croisées)
        # courbe symétrique : sur 6 images, une attaque easeOutQuint ferait disparaître le push
        e = courbe("easeInOutQuad")(p)
        a_scale = 1.0 + 0.035 * e
        b_scale = 1.08 - 0.08 * e

        def transformed(img: np.ndarray, scale: float, tx: float) -> np.ndarray:
            m = cv2.getRotationMatrix2D((W / 2, H / 2), 0, scale)
            m[0, 2] += tx
            return cv2.warpAffine(img, m, (W, H), borderMode=cv2.BORDER_REFLECT_101)

        a = transformed(old, a_scale, -W * e)
        b = transformed(new, b_scale, W * (1 - e))
        seam = int(W * (1.0 - e))
        mask = np.tile((np.arange(W) >= seam).astype(np.float32), (H, 1))
        mask = cv2.GaussianBlur(mask, (25, 1), 0)[:, :, None]
        return (a.astype(np.float32) * (1 - mask) + b.astype(np.float32) * mask).astype(np.uint8)

    # fondu court
    e = courbe("easeInOutQuad")(p)
    return cv2.addWeighted(new, e, old, 1 - e, 0)


# --------------------------------------------------------------------------- #
def gradient_overlay(frame: np.ndarray) -> np.ndarray:
    y = np.arange(H, dtype=np.float32)
    top = np.clip(1.0 - y / 500.0, 0.0, 1.0) ** 1.7 * 0.56
    bottom = np.clip((y - 700.0) / 580.0, 0.0, 1.0) ** 1.25 * 0.57
    alpha = np.maximum(top, bottom)[:, None, None]
    return np.clip(frame.astype(np.float32) * (1.0 - alpha), 0, 255).astype(np.uint8)


class ShotReader:
    """Lecture séquentielle de la fenêtre source du plan, gel de fin inclus."""

    def __init__(self, path: Path, shot: dict[str, Any]):
        self.cap = cv2.VideoCapture(str(path))
        if not self.cap.isOpened():
            raise RuntimeError(f"Source illisible : {path}")
        self.in_frame = int(shot["source"]["in_frame"])
        self.span = int(shot["source"]["source_frames"])
        self.pos = -1
        self.last = None
        while self.pos < self.in_frame - 1:
            ok, img = self.cap.read()
            if not ok:
                raise RuntimeError(f"Fenêtre hors fichier : {path} (in_frame={self.in_frame})")
            self.pos += 1

    def frame_at(self, local: int) -> np.ndarray:
        offset = min(max(0, local), max(0, self.span - 1))
        target = self.in_frame + offset
        while self.pos < target:
            ok, img = self.cap.read()
            if not ok:
                break
            self.pos += 1
            self.last = img
        if self.last is None:
            raise RuntimeError("Décodage impossible : fenêtre vide")
        return self.last

    def release(self):
        self.cap.release()


def render(plan_path: Path, output: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    expected = {"width": 720, "height": 1280, "fps": 30, "frames": 900, "duration_s": 30.0, "audio": False}
    if plan.get("output") != expected or [int(s["frames"]) for s in plan["scenes"]] != [180, 240, 210, 270]:
        raise ValueError("Contrat T1 (4 scènes muettes, 900 images) non respecté par le plan")
    if len(plan["shots"]) != 12:
        raise ValueError("Le plan doit contenir 12 plans")

    presentation = Presentation(ROOT / plan["presentation"])
    from engine.fetch_rushes import ensure_rushes
    ensure_rushes()

    shots = plan["shots"]
    windows = {o["graphic_block"]: (int(o["start_f"]), int(o["end_f"])) for o in plan["overlays"]}
    data = {k: str(v) for k, v in plan["display"].items()}
    cuts = {int(c["at_f"]): c["transition"] for c in plan["cuts"]}
    active = {}
    for cut_f, tid in cuts.items():
        info = TRANSITIONS[tid]
        if info["dur_f"] > 0:
            start = cut_f - 1   # la transition se lit à travers la coupe, pas avant le montage
            active[cut_f] = {"id": tid, "info": info, "start": start, "end": start + info["dur_f"]}

    tmp = Path(tempfile.mkdtemp(prefix="t1-v4-"))
    readers: dict[str, ShotReader] = {}
    normalized: dict[str, Path] = {}
    manifest: dict[str, Any] = {"plan": plan_path.name, "moteur": "engine/motion_v4.py",
                                "presentation": plan["presentation"], "frames": FRAMES,
                                "plans": [], "transitions": [], "blocs": []}
    try:
        for shot in shots:
            src = ROOT / shot["source"]["file"]
            key = str(shot["source"]["sha256"]) + shot["scene"]
            if key not in normalized:
                target = tmp / f"{shot['scene']}.mp4"
                # Recadrage 9:16 et interpolation temporelle seulement : aucune mise à l'échelle ici.
                filt = ("minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir,setsar=1,"
                        "eq=saturation=1.12:contrast=1.06:brightness=0.006")
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-an",
                                "-vf", filt, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "16",
                                "-pix_fmt", "yuv420p", str(target)], check=True)
                normalized[key] = target
            readers[shot["id"]] = ShotReader(normalized[key], shot)

        output.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
                                 "-pixel_format", "bgr24", "-video_size", f"{W}x{H}", "-framerate", str(FPS),
                                 "-i", "-", "-an", "-frames:v", str(FRAMES), "-c:v", "libx264",
                                 "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                                 "-movflags", "+faststart", str(output)], stdin=subprocess.PIPE)
        if proc.stdin is None:
            raise RuntimeError("ffmpeg n'a pas ouvert le tube")

        actifs: dict[str, set[str]] = {s["id"]: set() for s in shots}

        def shot_at(fno: int) -> tuple[int, dict[str, Any], int]:
            for i, s in enumerate(shots):
                if int(s["out_start_f"]) <= fno < int(s["out_end_f"]):
                    return i, s, fno - int(s["out_start_f"])
            return len(shots) - 1, shots[-1], int(shots[-1]["out_frames"]) - 1

        def shot_frame(shot: dict[str, Any], local: int) -> np.ndarray:
            raw = readers[shot["id"]].frame_at(local)
            return camera_move(raw, local, int(shot["out_frames"]), shot)

        for fno in range(FRAMES):
            i, shot, local = shot_at(fno)
            transition = None
            for cut_f, info in active.items():
                if info["start"] <= fno < info["end"]:
                    transition = (cut_f, info)
                    break
            if transition is None:
                img = shot_frame(shot, local)
            else:
                cut_f, info = transition
                prev, nxt = shots[i - 1], shots[i]
                # le plan sortant continue d'avancer, le plan entrant démarre : aucune image figée
                old_local = max(0, int(prev["out_frames"]) - 1 - (cut_f - fno))
                new_local = max(0, fno - cut_f)
                old = shot_frame(prev, old_local)
                new = shot_frame(nxt, new_local)
                p = (fno - info["start"] + 1) / info["info"]["dur_f"]
                img = do_transition(old, new, info["info"]["rendu"], p, presentation.palette)
            img = gradient_overlay(img)
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            draw = ImageDrawFactory(layer)
            base_im = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert("RGBA")
            for block_id, (start, end) in sorted(windows.items()):
                if start <= fno < end:
                    presentation.dessiner(layer, draw, block_id, data, fno - start, end - start)
                    actifs[shot["id"]].add(block_id)
            if layer.getchannel("A").getbbox():
                base_im = Image.alpha_composite(base_im, layer)
            img = cv2.cvtColor(np.asarray(base_im.convert("RGB")), cv2.COLOR_RGB2BGR)
            proc.stdin.write(img.astype(np.uint8).tobytes())
        proc.stdin.close()
        proc.wait()

        for cut_f, info in sorted(active.items()):
            manifest["transitions"].append({
                "frame_debut": info["start"], "frame_fin": info["end"],
                "seconde": round(cut_f / FPS, 2), "id": info["id"], "nom": info["info"]["nom"],
                "rendu": info["info"]["rendu"], "dur_f": info["info"]["dur_f"],
                "coupe_f": cut_f})
        for s in shots:
            manifest["plans"].append({
                "id": s["id"], "scene": s["scene"],
                "sortie": {"debut_f": int(s["out_start_f"]), "fin_f": int(s["out_end_f"]),
                           "debut_s": round(int(s["out_start_f"]) / FPS, 3),
                           "fin_s": round(int(s["out_end_f"]) / FPS, 3)},
                "source": {"fichier": s["source"]["file"], "in_frame": int(s["source"]["in_frame"]),
                           "source_frames": int(s["source"]["source_frames"]),
                           "fin_reelle": int(s["source"]["in_frame"]) + int(s["source"]["source_frames"]) - 1,
                           "gel_fin_f": int(s["source"].get("freeze_tail_f", 0))},
                "mouvement": {"id": s["zoom_curve"]["movement_id"], "nom": s["zoom_curve"]["movement"],
                              "parametres": s["zoom_curve"]["parameters"], "base": s["zoom_curve"]["base"]},
                "transition_sortie": s["transition_out"],
                "blocs_visibles": sorted(actifs[s["id"]]),
            })
        manifest["blocs"] = [{"id": o["graphic_block"], "champ": o["field"], "composition": o["composition"],
                              "start_f": int(o["start_f"]), "end_f": int(o["end_f"]),
                              "start_s": round(int(o["start_f"]) / FPS, 2),
                              "end_s": round(int(o["end_f"]) / FPS, 2)} for o in plan["overlays"]]
        manifest["presentation_blocs"] = sorted(presentation.blocs)
        if manifest_path:
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {"frames": FRAMES, "duration_s": 30.0, "fps": FPS, "width": W, "height": H,
                "video": str(output), "presentation": plan["presentation"],
                "manifest": str(manifest_path) if manifest_path else None}
    finally:
        for r in readers.values():
            r.release()
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def ImageDrawFactory(layer: Image.Image):
    from PIL import ImageDraw
    return ImageDraw.Draw(layer)


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="Moteur T1 réconcilié (plan + configuration de présentation)")
    p.add_argument("--plan", type=Path, default=ROOT / "render_plan_v4_demo.json")
    p.add_argument("--output", type=Path, default=ROOT / "output/output_T1_master_final.mp4")
    p.add_argument("--manifest", type=Path, default=ROOT / "reports/execution_manifest_v4.json")
    a = p.parse_args()
    print(json.dumps(render(a.plan, a.output, a.manifest), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
