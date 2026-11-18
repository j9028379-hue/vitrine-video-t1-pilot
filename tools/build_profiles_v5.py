"""Construction et validation des cinq profils commerçants V5.

Chaque profil produit : un plan JSON, un master MP4, une validation mesurée sur le fichier et une
planche de contrôle. Le profil 5 utilise une **fixture de fond entièrement blanc** (générée par
ffmpeg), clairement identifiée comme telle : ce n'est pas un rush commerçant.

    PYTHONPATH=. python3 tools/build_profiles_v5.py --out reports/profils_v5

Les cinq profils (mission §15.F) :
1. `demo_nominal`        — MAQUIS DÉMO / BURGER MAISON / 2 500 / ARCONVILLE — ADRESSE FICTIVE
2. `champs_longs`        — CHEZ MAMAN CLARISSE / RIZ AU POULET BRAISÉ ET ALLOCO / 12 500
3. `accroche_vide`       — accroche "" : aucun GB04, aucun mot inventé
4. `accroche_un_mot`     — accroche « Chaud », produit court
5. `fond_blanc`          — mêmes données que 1, fond vidéo entièrement blanc
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from engine.adaptive_graphics_v5 import GraphicsV5, contraste
from engine.montage_plan_builder import PROFILS_COMMERCIAUX, construire
from engine.motion_v5 import render
from tools.verify_worldclass import verifier

ROOT = Path(__file__).resolve().parents[1]
PROFILS = ["demo_nominal", "champs_longs", "accroche_vide", "accroche_un_mot", "fond_blanc"]


def mesurer_contraste(video: Path, graphics: GraphicsV5) -> dict[str, object]:
    """Contraste WCAG réellement mesuré sur les pixels du MP4, sous chaque texte essentiel.

    Le fond est échantillonné dans la boîte du texte, sur trois images au cœur de la fenêtre du
    bloc ; le texte est comparé à la couleur déclarée dans la configuration.
    """
    resultats = []
    cap = cv2.VideoCapture(str(video))
    for bid, bloc in graphics.blocs.items():
        for el in bloc.elements:
            if el.type != "texte" or not el.lignes:
                continue
            x, y, w, h = (int(v) for v in el.boite)
            x0, y0 = max(0, x), max(0, y)
            x1, y1 = min(graphics.W, x + max(1, w)), min(graphics.H, y + max(1, h))
            mesures = []
            for fno in (bloc.debut_f + (bloc.fin_f - bloc.debut_f) // 3,
                        bloc.debut_f + (bloc.fin_f - bloc.debut_f) // 2,
                        bloc.debut_f + 2 * (bloc.fin_f - bloc.debut_f) // 3):
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(fno))
                ok, frame = cap.read()
                if not ok:
                    continue
                zone = frame[y0:y1, x0:x1]
                if zone.size == 0:
                    continue
                # on écarte les pixels de texte pour ne mesurer que le fond réel
                plat = zone.reshape(-1, 3).astype(np.int32)
                couleur_bgr = np.array(list(el.couleur)[::-1], dtype=np.int32)
                loin = np.abs(plat - couleur_bgr).sum(axis=1) > 90
                fond_bgr = np.median(plat[loin] if loin.sum() > 32 else plat, axis=0)
                fond = (float(fond_bgr[2]), float(fond_bgr[1]), float(fond_bgr[0]))
                mesures.append(round(contraste(el.couleur, fond), 2))
            if mesures:
                resultats.append({"bloc": bid, "texte": el.lignes[0].texte,
                                  "couleur": list(el.couleur), "contrastes": mesures,
                                  "minimum": min(mesures)})
    cap.release()
    essentiels = [r for r in resultats if r["bloc"] in ("GB02", "GB03", "GB06", "GB07", "GB08")]
    return {
        "mesures": resultats,
        "minimum_essentiels": min((r["minimum"] for r in essentiels), default=None),
        "cible": 4.5,
        "conforme": bool(essentiels) and all(r["minimum"] >= 4.5 for r in essentiels),
        "sous_cible": [{"bloc": r["bloc"], "texte": r["texte"], "minimum": r["minimum"]}
                       for r in essentiels if r["minimum"] < 4.5],
    }


def planche(video: Path, graphics: GraphicsV5, sortie: Path, titre: str) -> None:
    """Planche de contrôle : six instants couvrant les huit blocs."""
    instants = [10, 60, 130, 210, 300, 470, 700, 830, 899]
    cap = cv2.VideoCapture(str(video))
    tuiles = []
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i in instants:
            petit = cv2.resize(frame, (200, 356), interpolation=cv2.INTER_AREA)
            cv2.putText(petit, str(i), (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)
            tuiles.append(petit)
        i += 1
    cap.release()
    if not tuiles:
        return
    planche_img = np.hstack(tuiles)
    bandeau = np.full((34, planche_img.shape[1], 3), 22, dtype=np.uint8)
    cv2.putText(bandeau, titre, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(sortie), np.vstack([bandeau, planche_img]))


def executer(profil: str, out_dir: Path, fixture_dir: str | None = None) -> dict[str, object]:
    sources = fixture_dir if profil == "fond_blanc" else "rushes/source/demo_v4"
    plan = construire(profil, sources_dir=sources)
    if profil == "fond_blanc":
        plan["fixture"] = ("fond entièrement blanc synthétique (ffmpeg color=white) : "
                           "fixture de validation graphique, jamais présentée comme un rush commerçant")
    plan_path = out_dir / f"plan_v5_{profil}.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    video = out_dir / f"master_v5_{profil}.mp4"
    render(plan_path, video, out_dir / f"manifest_v5_{profil}.json")
    graphics = GraphicsV5(ROOT / plan["config"], plan["display"],
                          json.loads((ROOT / plan["analyse"]).read_text(encoding="utf-8")))
    val = verifier(video, plan_path, out_dir / f"validation_v5_{profil}.json",
                   fixture=(profil == "fond_blanc"))
    ctr = mesurer_contraste(video, graphics)
    planche(video, graphics, out_dir / f"planche_v5_{profil}.png",
            f"PROFIL {profil} — {plan['display']['nom']} · {plan['display']['prix']}")
    return {
        "profil": profil, "champs": plan["display"], "video": str(video.relative_to(ROOT)),
        "plan": str(plan_path.relative_to(ROOT)), "sha256_video": val["sha256_video"],
        "resume_validation": val["resume"], "contraste": ctr,
        "blocs_affiches": sorted(graphics.blocs), "decisions_layout": graphics.decisions,
        "fixture": plan.get("fixture"),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Les cinq profils commerçants V5")
    ap.add_argument("--out", default="reports/profils_v5")
    ap.add_argument("--only", default=None, help="un seul profil")
    args = ap.parse_args(argv)
    out_dir = ROOT / args.out
    resultats = []
    for profil in ([args.only] if args.only else PROFILS):
        print(f"— profil {profil}", flush=True)
        resultats.append(executer(profil, out_dir, "rushes/source/fixture_blanc"))
        r = resultats[-1]
        print(f"   {r['resume_validation']} · contraste min {r['contraste']['minimum_essentiels']} "
              f"· blocs {len(r['blocs_affiches'])}", flush=True)
    (out_dir / "profils_v5.json").write_text(
        json.dumps({"version": "T1-V5-profils-1", "profils": resultats,
                    "note": "trois premiers profils sur rushs réels ; le profil 5 sur fixture blanche déclarée"},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(resultats)} profils → {out_dir.relative_to(ROOT)}/profils_v5.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
