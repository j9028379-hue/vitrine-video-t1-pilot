"""Analyseur de scènes T1 — couche 1 du moteur V5.

Rôle : **comprendre les prises** au lieu de les découper aveuglément. Aucune dépendance à
FFmpeg, uniquement de la lecture d'images et des mesures déterministes.

Ce module ne décide de rien : il mesure et publie `reports/scene_analysis_T1.json`.
Les décisions de montage sont prises par `engine/montage_plan_builder.py`.

Six mesures par scène
---------------------
1. **Stabilité** — corrélation de phase (`cv2.phaseCorrelate`) sur miniatures 180×320 : glissement
   moyen en pixels, détail par image, portions où le cadrage est stable (secousse initiale du
   doigt, tremblement, mouvement final). Le mouvement *intentionnel* n'est pas pénalisé : seule
   l'irrégularité (écart-type du glissement) est pénalisée.
2. **Netteté** — variance du Laplacien par image, puis par fenêtre. Sert au choix des fenêtres
   propres et au hook.
3. **Pivots** — détection des deux sous-moments de S2 et S4 par écart structurel (corrélation de
   phase + différence de gradient) ; seuil relatif à la distribution de la scène. Aucun pivot
   inventé : si le seuil n'est pas franchi, le rapport écrit `pivot_detecte: false` et la
   stratégie de secours utilisée par le constructeur de plan.
4. **Ancre du sujet** — saillance par énergie de gradient (Sobel) sur une grille 9×16, barycentre
   normalisé. Pour S3, tentative de détection de visage (Haar, léger) puis repli sur la saillance.
5. **Colorimétrie** — P10/P50/P90 de luminance et écart de balance des blancs (R/B, G/moyenne).
   La correction proposée est bornée et n'est qu'une **proposition** : le rendu décide.
6. **Fenêtres exploitables** — segments contigus stables et nets, exprimés en images.

Déterminisme : aucun tirage aléatoire, aucun échantillonnage aléatoire. Deux exécutions sur les
mêmes fichiers produisent le même JSON (hormis les durées de calcul, isolées dans `performance`).

    PYTHONPATH=. python3 engine/scene_analyzer.py --out reports/scene_analysis_T1.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
THUMB_W, THUMB_H = 180, 320
SCENES = ["S1", "S2", "S3", "S4"]


# --------------------------------------------------------------------------- #
# outils de mesure
def _gray_thumb(frame: np.ndarray) -> np.ndarray:
    g = cv2.cvtColor(cv2.resize(frame, (THUMB_W, THUMB_H), interpolation=cv2.INTER_AREA),
                     cv2.COLOR_BGR2GRAY)
    return g.astype(np.float32)


def _sharpness(gray: np.ndarray) -> float:
    """Variance du Laplacien — mesure de netteté sans agrandissement."""
    return float(cv2.Laplacian(gray, cv2.CV_32F, ksize=3).var())


def _saliency_anchor(frame: np.ndarray, grid_x: int = 9, grid_y: int = 16) -> dict[str, float]:
    """Barycentre de l'énergie de gradient, en coordonnées normalisées [0,1]."""
    small = cv2.resize(frame, (grid_x * 8, grid_y * 8), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    energy = cv2.magnitude(gx, gy)
    cells = energy.reshape(grid_y, 8, grid_x, 8).mean(axis=(1, 3))
    total = float(cells.sum()) or 1.0
    ys, xs = np.mgrid[0:grid_y, 0:grid_x]
    cx = float((cells * xs).sum() / total + 0.5) / grid_x
    cy = float((cells * ys).sum() / total + 0.5) / grid_y
    # dispersion : à quel point la matière visuelle est concentrée
    var_x = float((cells * (xs - (cx * grid_x - 0.5)) ** 2).sum() / total)
    spread = float(np.sqrt(var_x)) / grid_x
    return {"x": round(cx, 4), "y": round(cy, 4), "dispersion": round(spread, 4),
            "energie_moyenne": round(float(cells.mean()), 4)}


def _face_box(frame: np.ndarray) -> dict[str, Any] | None:
    """Détection de visage légère (Haar). Rend None si indisponible ou incertaine."""
    try:
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        if cascade.empty():
            return None
        import shutil

        # Analyse sur une miniature, jamais sur l'image pleine : coût constant et borné.
        scale = 240.0 / max(1, frame.shape[0])
        small = cv2.resize(frame, (int(frame.shape[1] * scale), int(frame.shape[0] * scale)),
                           interpolation=cv2.INTER_AREA) if scale != 1.0 else frame
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=6,
                                         minSize=(48, 48))
        if len(faces) == 0:
            return None
        # Visage le plus central
        cx, cy = small.shape[1] / 2, small.shape[0] / 2
        faces = sorted(faces, key=lambda f: (f[0] + f[2] / 2 - cx) ** 2 + (f[1] + f[3] / 2 - cy) ** 2)
        x, y, w, h = [float(v) for v in faces[0]]
        return {"x": round(x / small.shape[1], 4), "y": round(y / small.shape[0], 4),
                "w": round(w / small.shape[1], 4), "h": round(h / small.shape[0], 4),
                "methode": "haar_frontalface", "confiance": "moyenne"}
    except Exception:                                    # pragma: no cover - robustesse
        return None


def _color_profile(frames: list[np.ndarray]) -> dict[str, Any]:
    """Luminance P10/P50/P90 et écart de balance des blancs, moyennés sur la scène."""
    lums, rb, gm = [], [], []
    for f in frames:
        small = cv2.resize(f, (90, 160), interpolation=cv2.INTER_AREA).astype(np.float32)
        b, g, r = float(small[..., 0].mean()), float(small[..., 1].mean()), float(small[..., 2].mean())
        gray = cv2.cvtColor(small.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
        lums.append(float(np.percentile(gray, 10)))
        lums.append(float(np.percentile(gray, 50)))
        lums.append(float(np.percentile(gray, 90)))
        rb.append(float(r / max(1e-3, b)))
        gm.append(float(g / max(1e-3, (r + b) / 2)))
    p10 = float(np.percentile(lums[0::3], 50)) if lums else 0.0
    p50 = float(np.percentile(lums[1::3], 50)) if lums else 0.0
    p90 = float(np.percentile(lums[2::3], 50)) if lums else 0.0
    return {
        "luminance_p10": round(p10, 2), "luminance_p50": round(p50, 2), "luminance_p90": round(p90, 2),
        "balance_rouge_bleu": round(float(np.median(rb)), 3),
        "balance_vert": round(float(np.median(gm)), 3),
        "gains_gray_world": {
            "rouge": round(float(np.clip(1.0 / float(np.median(rb)), 0.97, 1.03)), 4) if np.median(rb) > 0 else 1.0,
            "vert": round(float(np.clip(1.0 / float(np.median(gm)), 0.97, 1.03)), 4) if np.median(gm) > 0 else 1.0,
            "bleu": round(float(np.clip(float(np.median(rb)), 0.97, 1.03)), 4) if np.median(rb) > 0 else 1.0,
        },
        "dynamique": round(p90 - p10, 2),
    }


def proposed_grading(profile: dict[str, Any]) -> dict[str, float]:
    """Correction contextuelle, légère et bornée. Jamais de filtre orange global."""
    p50 = float(profile["luminance_p50"])
    rb = float(profile["balance_rouge_bleu"])
    gamma = 1.0
    if p50 < 92:
        gamma = float(np.clip(1.0 + (92 - p50) / 420.0, 1.0, 1.12))     # scène sombre : +12 % max
    elif p50 > 168:
        gamma = float(np.clip(1.0 - (p50 - 168) / 900.0, 0.94, 1.0))    # scène claire : -6 % max
    # Balance des blancs : gain gray-world borné à ±3 %, appliqué seulement si l'écart est réel.
    gains = profile.get("gains_gray_world") or {}
    if gains:
        warm = float(np.clip(gains.get("rouge", 1.0) - 1.0, -0.03, 0.03))
    else:                                             # repli : écart rouge/bleu borné
        warm = float(np.clip((1.0 / max(0.2, rb) - 1.0) * 0.05, -0.03, 0.03))
    return {"gamma": round(gamma, 4), "rechauffement": round(warm, 4),
            "saturation": 1.0, "plafond_zoom_numerique": 1.32}


# --------------------------------------------------------------------------- #
# analyse d'une scène
def analyze_scene(path: Path, scene: str) -> dict[str, Any]:
    t0 = time.perf_counter()
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Source illisible : {path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    grays: list[np.ndarray] = []
    colors: list[np.ndarray] = []
    prev_small: np.ndarray | None = None
    shifts: list[float] = []
    sharp: list[float] = []
    struct_diff: list[float] = []

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        g = _gray_thumb(frame)
        grays.append(g)
        if len(colors) < 40:                       # profil colorimétrique : 40 images suffisent
            colors.append(frame)
        if prev_small is not None:
            try:
                (dx, dy), response = cv2.phaseCorrelate(prev_small, g)
                shifts.append(float(np.hypot(dx, dy)))
            except cv2.error:                      # pragma: no cover
                shifts.append(0.0)
            # écart structurel : différence de gradient normalisée (robuste au mouvement régulier)
            ga = cv2.Sobel(prev_small, cv2.CV_32F, 1, 0, ksize=3)
            gb = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
            struct_diff.append(float(np.abs(ga - gb).mean()))
        prev_small = g
        sharp.append(_sharpness(g))
    cap.release()

    n = len(grays)
    if n == 0:
        raise RuntimeError(f"Aucune image lue dans {path}")
    shifts_full = [0.0] + shifts
    shift_mean = float(np.mean(shifts_full))
    shift_std = float(np.std(shifts_full))
    # Un panoramique régulier est *stable* : c'est l'irrégularité qui trahit la secousse.
    # Statistique robuste (médiane / écart absolu médian) : une coupe franche entre deux prises
    # produirait un pic de corrélation parasite et ne doit pas dégrader la note de stabilité.
    med = float(np.median(shifts_full))
    mad = float(np.median(np.abs(np.asarray(shifts_full) - med)))
    irregularite = mad / (med + 1.0)
    stability = float(np.clip(1.0 - 0.9 * irregularite, 0.0, 1.0))
    tremblements = int(sum(1 for v in shifts_full if v > med + max(2.5, 8.0 * mad)))
    sharp_med = float(np.median(sharp))
    sharp_p75 = float(np.percentile(sharp, 75))

    # --- fenêtres exploitables : stables ET nettes, par blocs de 15 images
    win = 15
    windows = []
    for start in range(0, n - win + 1, win):
        seg_s = shifts_full[start:start + win]
        seg_sh = sharp[start:start + win]
        ok = (float(np.std(seg_s)) < max(0.9, shift_std * 1.8)) and (float(np.median(seg_sh)) >= sharp_med * 0.82)
        windows.append({"debut_f": start, "fin_f": start + win - 1, "stable": bool(ok),
                        "glissement_moyen_px": round(float(np.mean(seg_s)), 3),
                        "nettete_mediane": round(float(np.median(seg_sh)), 2)})
    # regroupe les fenêtres contiguës retenues
    fenetres: list[dict[str, int]] = []
    for w in windows:
        if not w["stable"]:
            continue
        if fenetres and fenetres[-1]["fin_f"] + 1 == w["debut_f"]:
            fenetres[-1]["fin_f"] = w["fin_f"]
        else:
            fenetres.append({"debut_f": w["debut_f"], "fin_f": w["fin_f"]})
    if not fenetres:                                # repli documenté : toute la prise est utilisable
        fenetres = [{"debut_f": 0, "fin_f": n - 1}]

    # --- pivot : changement de cadrage (S2 / S4)
    pivot: dict[str, Any] = {"pivot_detecte": False, "methode": "gradient_structurel"}
    pivot["applicable"] = scene in ("S2", "S4")
    if not pivot["applicable"]:
        pivot["note"] = "une seule intention de cadrage attendue dans cette scène : pas de pivot recherché"
    elif struct_diff:
        lo = int(n * 0.25)
        hi = int(n * 0.75)
        seg = struct_diff[max(0, lo - 1):max(1, hi)]
        if seg:
            idx = int(np.argmax(seg)) + max(0, lo - 1) + 1
            peak = float(np.max(seg))
            med = float(np.median(struct_diff)) or 1e-6
            ratio = peak / med
            pivot = {
                "pivot_detecte": bool(ratio >= 2.6 and peak > 6.0),
                "applicable": True,
                "methode": "maximum du gradient structurel entre 25 % et 75 % de la prise",
                "frame": idx, "ratio_pic_mediane": round(ratio, 3), "pic": round(peak, 3),
                "seuil_ratio": 2.6,
            }
            if not pivot["pivot_detecte"]:
                pivot["repli"] = ("aucun changement de cadrage fiable : le constructeur garde une "
                                  "fenêtre unique et n'invente pas de pivot")

    # --- ancre du sujet
    mid = [grays[i] for i in range(0, n, max(1, n // 12))]
    anchors = [_saliency_anchor(cv2.cvtColor(g.astype(np.uint8), cv2.COLOR_GRAY2BGR)) for g in mid]
    ax = float(np.median([a["x"] for a in anchors]))
    ay = float(np.median([a["y"] for a in anchors]))
    anchor: dict[str, Any] = {"x": round(ax, 4), "y": round(ay, 4),
                              "methode": "barycentre de l'énergie de gradient",
                              "dispersion": round(float(np.median([a["dispersion"] for a in anchors])), 4)}
    if scene == "S3":
        face = None
        for i in range(0, n, max(1, n // 8)):
            cap = cv2.VideoCapture(str(path))
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, frame = cap.read()
            cap.release()
            if ok:
                face = _face_box(frame)
                if face:
                    break
        if face:
            anchor.update({"methode": "haar_frontalface", "visage": face,
                           "x": round(face["x"] + face["w"] / 2, 4),
                           "y": round(face["y"] + face["h"] / 2, 4),
                           "zone_sure_visage": {
                               "y_haut": round(face["y"] - 0.02, 4),
                               "y_bas": round(face["y"] + face["h"] + 0.06, 4),
                               "x_gauche": round(max(0.0, face["x"] - 0.04), 4),
                               "x_droite": round(min(1.0, face["x"] + face["w"] + 0.04), 4)}})
        else:
            anchor.update({"repli": "visage non détecté : la zone protégée est la partie haute "
                                    "centrale de l'image, calculée depuis la saillance"})

    profile = _color_profile(colors)
    hook_frame = int(np.argmax([sharp[i] for i in range(min(n, 45))]))
    elapsed = time.perf_counter() - t0

    return {
        "scene": scene, "fichier": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()[:16],
        "cadence_native": round(fps, 3), "largeur": width, "hauteur": height,
        "images": n, "duree_s": round(n / fps, 3),
        "stabilite": {"score": round(stability, 4),
                      "glissement_moyen_px": round(shift_mean, 3),
                      "glissement_ecart_type_px": round(shift_std, 3),
                      "irregularite": round(irregularite, 4),
                      "lecture": ("mouvement régulier (panoramique assumé)" if irregularite < 0.55
                                  else "cadrage irrégulier : secousses à éviter aux coupes"),
                      "images_tremblement": tremblements,
                      "glissement_median_px": round(med, 3),
                      "ecart_absolu_median_px": round(mad, 3)},
        "nettete": {"mediane": round(sharp_med, 2), "p75": round(sharp_p75, 2),
                    "max": round(float(np.max(sharp)), 2),
                    "meilleure_image_hook": hook_frame,
                    "nettete_hook": round(sharp[hook_frame], 2)},
        "fenetres_exploitables": fenetres,
        "pivot": pivot,
        "ancre_sujet": anchor,
        "colorimetrie": {**profile, "correction_proposee": proposed_grading(profile)},
        "incertitudes": [
            "pivot non détecté" if not pivot.get("pivot_detecte") else "pivot détecté",
            "visage détecté" if anchor.get("visage") else "ancre calculée par saillance",
        ],
        "performance": {"analyse_s": round(elapsed, 3), "miniature": f"{THUMB_W}x{THUMB_H}"},
    }


def analyze(sources: dict[str, Path]) -> dict[str, Any]:
    t0 = time.perf_counter()
    scenes = [analyze_scene(sources[s], s) for s in SCENES]
    total = time.perf_counter() - t0
    return {
        "version": "T1-V5-scene-analyzer-1",
        "principe": "mesurer d'abord, décider ensuite ; aucune image inventée, aucun aléatoire",
        "miniature": {"largeur": THUMB_W, "hauteur": THUMB_H},
        "scenes": scenes,
        "performance": {"total_s": round(total, 3),
                        "moyenne_par_scene_s": round(total / len(scenes), 3),
                        "objectif_0_5_s": "non atteint en Python pur sur 150 images par scène" if total / len(scenes) >= 0.5 else "atteint",
                        "miniature": f"{THUMB_W}x{THUMB_H}"},
    }


def default_sources() -> dict[str, Path]:
    base = ROOT / "rushes" / "source" / "demo_v4"
    return {s: base / f"{s}.mp4" for s in SCENES}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Analyse des quatre prises T1")
    ap.add_argument("--out", default="reports/scene_analysis_T1.json")
    args = ap.parse_args(argv)
    sources = default_sources()
    missing = [str(p) for p in sources.values() if not p.exists()]
    if missing:
        raise SystemExit(f"Prises absentes : {missing}\nLancer d'abord : bash rushes/build_scenes.sh")
    report = analyze(sources)
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for s in report["scenes"]:
        print(f"{s['scene']}: {s['images']} images · stabilité {s['stabilite']['score']:.3f} · "
              f"netteté médiane {s['nettete']['mediane']:.1f} · pivot {s['pivot'].get('pivot_detecte')} · "
              f"{s['performance']['analyse_s']:.2f} s")
    print(f"total {report['performance']['total_s']:.2f} s → {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
