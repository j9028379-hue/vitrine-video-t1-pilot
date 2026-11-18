"""Contrôle complet du master final : conteneur, silence, images noires, fenêtres sources, zoom mesuré.

Mesure indépendante (sans relire les formules du moteur) : pour deux instants par plan, on cherche la
meilleure correspondance (indice d'image source k, facteur de zoom z) entre l'image du master et la
prise normalisée. On compare ensuite (k, z) à ce que le plan déclare (in_frame + temps local, base × k_ratio).
Le descripteur est recalé sur le vignettage (étape de rendu connue) puis réduit en 180×320.
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "output/output_T1_master_final.mp4"
NORM = Path("/tmp/norm")
GRID = (180, 40)
BANDE = (20, 170)  # bande haute : aucune carte de texte ne s'y trouve (hors pastille y=168)


def vignette(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    y = np.arange(h, dtype=np.float32)[:, None]
    alpha = np.maximum(np.clip(1.0 - (y / h) / (500 / 1280), 0, 1) ** 1.7 * 0.56,
                       np.clip(((y / h) - (700 / 1280)) / (580 / 1280), 0, 1) ** 1.25 * 0.57)
    return (img.astype(np.float32) * (1.0 - alpha)[:, :, None]).astype(np.uint8)


def descriptor(img: np.ndarray, z: float = 1.0) -> np.ndarray:
    """Descripteur du cadrage : recadrage du zoom z puis bande haute réduite.

    On reproduit exactement la géométrie du moteur (recadrage puis retour à 720×1280), puis on
    ne garde que la bande haute : les cartes de texte (produit, prix, accroche, adresse, CTA) sont
    toutes sous y=200 et ne peuvent donc pas fausser la mesure.
    """
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = g.shape[:2]
    if z > 1.0:
        cw, ch = int(round(w / z)), int(round(h / z))
        x0, y0 = (w - cw) // 2, (h - ch) // 2
        g = cv2.resize(g[y0:y0 + ch, x0:x0 + cw], (w, h), interpolation=cv2.INTER_LINEAR)
    return cv2.resize(g[BANDE[0]:BANDE[1]], GRID, interpolation=cv2.INTER_AREA).astype(np.float32)


def zoomed(img: np.ndarray, z: float) -> np.ndarray:
    h, w = img.shape[:2]
    cw, ch = int(round(w / z)), int(round(h / z))
    x0, y0 = (w - cw) // 2, (h - ch) // 2
    return cv2.resize(img[y0:y0 + ch, x0:x0 + cw], (w, h), interpolation=cv2.INTER_LANCZOS4)


def corr(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    return float((a * b).sum() / ((np.linalg.norm(a) * np.linalg.norm(b)) or 1e-6))


def load(path: Path) -> list[np.ndarray]:
    cap = cv2.VideoCapture(str(path))
    out = []
    while True:
        ok, img = cap.read()
        if not ok:
            break
        out.append(img)
    cap.release()
    return out


def ease(name: str, t: float) -> float:
    t = max(0.0, min(1.0, t))
    if name == "easeInOutQuad":
        return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2
    if name == "easeOutQuint":
        return 1 - (1 - t) ** 5
    if name == "easeOutCubic":
        logger = 1 - (1 - t) ** 3
        return logger
    return t


def zoom_attendu(shot: dict, local: int) -> float:
    curve = shot["zoom_curve"]
    p = curve.get("parameters") or {}
    base = float(curve.get("base", 1.0))
    prog = local / max(1, int(shot["out_frames"]) - 1)
    e = ease(p.get("easing", "linear"), prog)
    z = 1.0
    if p.get("k_ratio"):
        k0, k1 = p["k_ratio"]
        if curve["movement_id"] == "MV03":
            e = ease("easeOutQuint", min(1.0, local / int(p.get("dur_f", 6))))
        z = k0 + (k1 - k0) * e
    return base * z


ZOOMS = [round(1.0 + i * 0.02, 2) for i in range(-5, 41)]
TOL_K = 6      # fenêtre d'indices explorée autour de l'indice déclaré
SEUIL_OK = 0.90
SEUIL_PARTIEL = 0.80


def main() -> None:
    plan = json.loads((ROOT / "render_plan_v4_demo.json").read_text(encoding="utf-8"))

    # 1) points de contrôle : deux instants par plan (local 6 et dernière image de la fenêtre)
    points = []
    for shot in plan["shots"]:
        span = int(shot["source"]["source_frames"])
        for local in (6, span - 1):
            points.append({"shot": shot, "local": local,
                           "frame": int(shot["out_start_f"]) + local,
                           "k_declare": int(shot["source"]["in_frame"]) + local,
                           "z_declare": min(ZOOMS, key=lambda z: abs(z - zoom_attendu(shot, local)))})

    # 2) descripteurs du master pour ces images seulement
    by_frame = {p["frame"]: p for p in points}
    cap = cv2.VideoCapture(str(MASTER))
    i = 0
    moyennes = []
    while True:
        ok, img = cap.read()
        if not ok:
            break
        moyennes.append(float(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).mean()))
        if i in by_frame:
            by_frame[i]["descripteur"] = descriptor(vignette(img))
        i += 1
    cap.release()
    total_master = i

    # 3) une passe séquentielle par prise : couples (indice, zoom) utiles seulement
    besoins = {}
    for p in points:
        sid = p["shot"]["scene"]
        for k in range(max(0, p["k_declare"] - TOL_K), p["k_declare"] + TOL_K + 1):
            for z in ZOOMS:
                besoins.setdefault(sid, {}).setdefault(k, set()).add(z)

    mesures = {}
    for sid, table in besoins.items():
        lo, hi = min(table), max(table)
        cap = cv2.VideoCapture(str(NORM / f"{sid}.mp4"))
        k = 0
        while True:
            ok, img = cap.read()
            if not ok:
                break
            if lo <= k <= hi and k in table:
                v = vignette(img)
                for z in table[k]:
                    mesures[(sid, k, z)] = descriptor(v, z)
            k += 1
        cap.release()
        print(f"{sid} : {k} images parcourues, {len(table)} indices retenus", flush=True)

    # 4) comparaison
    report = {"master": str(MASTER.relative_to(ROOT)), "images_master": total_master,
              "duree_s": round(total_master / 30, 3), "plans": [],
              "images_noires": [n for n, m in enumerate(moyennes) if m < 4.0], "muet": None,
              "methode": "bande haute y=20..170 (hors cartes de texte), recadrage de zoom identique au "
                         "moteur, vignettage appliqué des deux côtés ; corrélation de Pearson"}
    for p in points:
        sid = p["shot"]["scene"]
        target = p["descripteur"]
        corr_declare = round(corr(target, mesures[(sid, p["k_declare"], p["z_declare"])]), 4)
        best = (-2.0, None, None)
        for k in range(max(0, p["k_declare"] - TOL_K), p["k_declare"] + TOL_K + 1):
            for z in ZOOMS:
                sc = corr(target, mesures[(sid, k, z)])
                if sc > best[0]:
                    best = (sc, k, z)
        verdict = ("conforme" if corr_declare >= SEUIL_OK
                   else "partiel" if corr_declare >= SEUIL_PARTIEL else "à vérifier")
        report["plans"].append({
            "plan": p["shot"]["id"], "scene": sid, "image_master": p["frame"], "local": p["local"],
            "indice_declare": p["k_declare"], "zoom_declare": p["z_declare"],
            "correlation_au_declare": corr_declare,
            "meilleur_indice": best[1], "meilleur_zoom": best[2],
            "correlation_max": round(best[0], 4), "verdict": verdict})

    ffmpeg = "ffmpeg"
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    probe = subprocess.run([ffmpeg, "-hide_banner", "-i", str(MASTER)], capture_output=True, text=True).stderr
    report["muet"] = "Audio:" not in probe
    report["textes"] = plan["display"]
    rows = report["plans"]
    conf = sum(1 for r in rows if r["verdict"] == "conforme")
    part = sum(1 for r in rows if r["verdict"] == "partiel")
    report["synthese"] = {
        "points_verifies": len(rows), "conformes": conf, "partiels": part,
        "a_verifier": len(rows) - conf - part, "images_noires": len(report["images_noires"]),
        "muet": report["muet"],
        "verdict": "OK" if conf + part == len(rows) and not report["images_noires"] and report["muet"]
        else "A VOIR"}
    out = ROOT / "reports/final_master_checks.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["synthese"], ensure_ascii=False, indent=2))
    for r in rows:
        print(f"{r['plan']} local {r['local']:>2} | déclaré k={r['indice_declare']} z={r['zoom_declare']}"
              f" | corr={r['correlation_au_declare']:.3f} | meilleur k={r['meilleur_indice']} "
              f"z={r['meilleur_zoom']} corr={r['correlation_max']:.3f} | {r['verdict']}")


if __name__ == "__main__":
    main()
