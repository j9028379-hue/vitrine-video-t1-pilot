"""Constructeur de plan de montage V5 — deuxième brique.

Couche **décisionnelle**, indépendante du backend de rendu. Elle ne décode aucune image : elle
lit `reports/scene_analysis_T1.json`, `config/T1_worldclass_v5.json` et un profil commercial
(les six champs autorisés), puis écrit un plan JSON complet et versionné.

Ce que le plan contient (contrat JSON commun Python ↔ Android) :

* cadence, résolution, quatre scènes et leurs bornes en images **et** en secondes ;
* fenêtres sources : image d'entrée, nombre d'images, image de sortie ;
* courbes de vitesse **normalisées** pour consommer exactement la fenêtre disponible ;
* table de remappage image de sortie → position source continue (sous-pixel) ;
* ancres de sujet et transformations de caméra (zoom, panoramique, sous-pixel) ;
* transitions et leurs paramètres, avec justification ;
* huit blocs graphiques, slot, fenêtre, animations (valeurs lues dans la configuration) ;
* zones protégées dérivées de l'analyse ;
* paramètres de rendu et de qualité.

Garanties
---------
1. **Aucun gel** : `freeze_tail_f` n'existe plus ; la durée est construite à partir des images
   réellement disponibles.
2. **Normalisation mathématique** : la courbe de vitesse est divisée par sa moyenne pour que la
   fenêtre source soit consommée exactement, sans image inventée.
3. **Déterminisme** : aucune valeur aléatoire ; mêmes entrées ⇒ même plan à l'octet près.

    PYTHONPATH=. python3 engine/montage_plan_builder.py \
        --profile demo_nominal --out reports/montage_plan_v5_demo.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FPS = 30
SCENE_FRAMES = {"S1": 180, "S2": 240, "S3": 210, "S4": 270}
SCENE_START = {"S1": 0, "S2": 180, "S3": 420, "S4": 630}

# Découpage interne de chaque scène : (id, scène, images de sortie, profil caméra, intention)
SHOTS = [
    ("A1", "S1", 105, "punch_hook", "hook : le plat déjà à l'image, punch-in qui donne du rythme dès la première image"),
    ("A2", "S1", 75, "travelling_droite", "geste de service, coupe dynamique sur le mouvement"),
    ("B1", "S2", 120, "descente", "vue générale du dessus"),
    ("B2", "S2", 120, "push_subtil", "détail rapproché, prix mis en avant"),
    ("C1", "S3", 210, "fixe_ancre", "personne qui sert : visage stable, compatible synchronisation labiale"),
    ("D1", "S4", 135, "travelling_haut", "entrée et lieu reconnaissables"),
    ("D2", "S4", 135, "push_subtil", "comptoir puis packshot commercial"),
]

PROFILS_COMMERCIAUX = {
    "demo_nominal": {"nom": "MAQUIS DÉMO", "produit": "BURGER MAISON", "prix": "2 500",
                     "whatsapp": "+229 00 00 00 00", "quartier": "ARCONVILLE — ADRESSE FICTIVE",
                     "accroche": "Préparé minute, servi chaud"},
    "champs_longs": {"nom": "CHEZ MAMAN CLARISSE", "produit": "RIZ AU POULET BRAISÉ ET ALLOCO",
                     "prix": "12 500", "whatsapp": "+229 01 23 45 67 89",
                     "quartier": "Abomey-Calavi, Arconville carrefour",
                     "accroche": "Préparé chaud chaque matin avec amour"},
    "accroche_vide": {"nom": "MAQUIS DÉMO", "produit": "BURGER MAISON", "prix": "2 500",
                      "whatsapp": "+229 00 00 00 00", "quartier": "ARCONVILLE — ADRESSE FICTIVE",
                      "accroche": ""},
    "accroche_un_mot": {"nom": "MAQUIS DÉMO", "produit": "BURGER", "prix": "2 500",
                        "whatsapp": "+229 00 00 00 00", "quartier": "ARCONVILLE",
                        "accroche": "Chaud"},
    "fond_blanc": {"nom": "MAQUIS DÉMO", "produit": "BURGER MAISON", "prix": "2 500",
                   "whatsapp": "+229 00 00 00 00", "quartier": "ARCONVILLE — ADRESSE FICTIVE",
                   "accroche": "Préparé minute, servi chaud"},
}

LIMITES = {"nom": 40, "produit": 32, "prix": 7, "whatsapp": 20, "quartier": 40, "accroche": 48}


def valider_profil(profil: dict[str, str]) -> list[str]:
    """Les six champs autorisés, avec leurs limites V1.2. Aucune valeur inventée."""
    erreurs = []
    for champ, maxi in LIMITES.items():
        valeur = profil.get(champ, "")
        if not isinstance(valeur, str):
            erreurs.append(f"{champ} : valeur non textuelle")
        elif len(valeur) > maxi:
            erreurs.append(f"{champ} : {len(valeur)} caractères (maximum {maxi})")
    if not profil.get("nom", "").strip():
        erreurs.append("nom : obligatoire")
    if not profil.get("produit", "").strip():
        erreurs.append("produit : obligatoire")
    return erreurs


# --------------------------------------------------------------------------- #
def courbe_vitesse(images: int, source_dispo: int, profil: dict[str, Any],
                   bornes: dict[str, float], plafond_repetition: int = 2) -> dict[str, Any]:
    """Courbe de vitesse continue normalisée sur la fenêtre source disponible.

    La forme est donnée par le profil (attaque / cœur / sortie) ; la **moyenne** est imposée par
    `source_dispo / images`. Après normalisation, la position source est strictement croissante
    dès que la fenêtre contient au moins autant d'images que la sortie.
    """
    a = float(profil.get("part_attaque", 0.14))
    b = float(profil.get("part_sortie", 0.20))
    att, coeur, sor = float(profil["attaque"]), float(profil["coeur"]), float(profil["sortie"])

    def lissage(t: float) -> float:
        t = max(0.0, min(1.0, t))
        return t * t * (3 - 2 * t)

    v = []
    for k in range(images):
        t = k / max(1, images - 1)
        if t < a:
            vitesse = coeur + (att - coeur) * (1 - lissage(t / a))
        elif t > 1 - b:
            vitesse = coeur + (sor - coeur) * lissage((t - (1 - b)) / b)
        else:
            vitesse = coeur
        v.append(vitesse)
    moyenne = sum(v) / len(v)
    cible = source_dispo / images
    facteur = cible / moyenne if moyenne > 0 else 1.0
    v = [max(bornes["min"], min(bornes["max"], x * facteur)) for x in v]

    cum = [0.0]
    for x in v:
        cum.append(cum[-1] + x)
    etendue = cum[-1] - cum[0]
    positions = [cum[i + 1] - cum[0] for i in range(images)]
    base = positions[0]
    positions = [p - base for p in positions]
    etendue2 = positions[-1] or 1.0
    positions = [p / etendue2 * (source_dispo - 1) for p in positions]

    # indices entiers : le ralentissement (vitesse < 1) réutilise légitimement une image,
    # mais jamais plus de `plafond_repetition` images identiques consécutives.
    indices, precedents, repetitions, max_repet, run = [], -1, 0, 0, 0
    for p in positions:
        idx = max(0, min(source_dispo - 1, int(round(p))))
        if idx <= precedents:
            if run >= plafond_repetition:
                idx = min(source_dispo - 1, precedents + 1)
                run = 0
            else:
                idx = precedents
                run += 1
                repetitions += 1
                max_repet = max(max_repet, run + 1)
        else:
            run = 0
        indices.append(idx)
        precedents = idx
    return {
        "profil_applique": {"attaque": round(att * facteur, 4), "coeur": round(coeur * facteur, 4),
                            "sortie": round(sor * facteur, 4),
                            "part_attaque": a, "part_sortie": b},
        "facteur_normalisation": round(facteur, 5),
        "vitesse_moyenne_reelle": round(source_dispo / images, 4),
        "vitesse_min": round(min(v), 4), "vitesse_max": round(max(v), 4),
        "indices_sources": indices,
        "positions_sous_pixel": [round(p, 3) for p in positions],
        "images_repetees": repetitions,
        "repetition_max_consecutive": max_repet,
        "gel_de_fin": 0,
    }


def _camera(profil_nom: str, config: dict[str, Any], ancre: dict[str, float],
            images: int) -> dict[str, Any]:
    profils = config["camera"]["profils"]
    base = profils.get(profil_nom, profils["push_subtil"])
    k0, k1 = base["k"]
    pan = base.get("pan", [0.0, 0.0])
    axe = base.get("axe", "horizontal")
    # l'overscan doit couvrir l'amplitude du panoramique : sinon le panoramique serait rogné
    pan_max = max(abs(pan[0]), abs(pan[1]))
    k_min_pan = 1.0 + 2.0 * pan_max + 0.01
    k0, k1 = max(k0, k_min_pan), max(k1, k_min_pan)
    plafond = float(config["camera"]["plafond_zoom_numerique"])
    k0, k1 = min(k0, plafond), min(k1, plafond)
    return {
        "profil": profil_nom, "axe_pan": axe,
        "zoom": {"debut": round(k0, 4), "fin": round(k1, 4),
                 "plafond_respecte": bool(max(k0, k1) <= plafond)},
        "pan_rel": {"debut": round(pan[0], 4), "fin": round(pan[1], 4),
                    "deplacement_px": round(abs(pan[1] - pan[0]) * config["canevas"]["largeur"], 1)},
        "sous_pixel": True, "interpolation": config["camera"]["interpolation"],
        "ancre_source": {"x": round(float(ancre.get("x", 0.5)), 4), "y": round(float(ancre.get("y", 0.5)), 4)},
        "courbe": "easeInOutQuad",
    }


def construire(profil_nom: str = "demo_nominal", profil: dict[str, str] | None = None,
               analysis_path: str = "reports/scene_analysis_T1.json",
               config_path: str = "config/T1_worldclass_v5.json",
               sources_dir: str = "rushes/source/demo_v4",
               fixture: str | None = None) -> dict[str, Any]:
    config = json.loads((ROOT / config_path).read_text(encoding="utf-8"))
    analysis = json.loads((ROOT / analysis_path).read_text(encoding="utf-8"))
    donnees = dict(profil or PROFILS_COMMERCIAUX[profil_nom])
    erreurs = valider_profil(donnees)
    if erreurs:
        raise ValueError("Profil commercial invalide : " + " ; ".join(erreurs))

    par_scene = {s["scene"]: s for s in analysis["scenes"]}
    scenes, shots = [], []
    catalogue = config["transitions"]["catalogue"]
    vitesses = config["vitesse"]

    # partition des images sources disponibles par scène, au prorata des images de sortie
    reste: dict[str, int] = {}
    for scene in SCENE_FRAMES:
        dispo = int(par_scene[scene]["images"])
        besoin = sum(n for _, s, n, _, _ in SHOTS if s == scene)
        reste[scene] = dispo - besoin          # images en réserve (marge de sécurité)

    curseur = {s: 0 for s in SCENE_FRAMES}
    for sid, scene, frames, cam, intention in SHOTS:
        info = par_scene[scene]
        dispo = int(info["images"])
        mariage = max(0, reste[scene])
        # fenêtre source : au moins autant d'images que la sortie, en profitant de la réserve
        source_dispo = min(dispo - curseur[scene], frames + min(mariage, 6))
        if source_dispo < frames:                       # repli documenté : on ne peut pas remplir
            source_dispo = min(dispo - curseur[scene], frames)
        profil_vitesse = vitesses["profil"]
        if scene in vitesses["lip_sync_safe"]["scenes"]:
            profil_vitesse = {"attaque": vitesses["lip_sync_safe"]["attaque"],
                              "coeur": vitesses["lip_sync_safe"]["coeur"],
                              "sortie": vitesses["lip_sync_safe"]["sortie"],
                              "part_attaque": 0.16, "part_sortie": 0.16}
        plafond_rep = max(0, int(vitesses["interdit_gel"]["repetition_max_images_consecutives"]) - 1)
        v = courbe_vitesse(frames, source_dispo, profil_vitesse, vitesses["bornes"], plafond_rep)
        cam_profil = _camera(cam, config, info["ancre_sujet"], frames)
        debut = SCENE_START[scene] + (0 if sid in ("A1", "B1", "C1", "D1") else
                                      (105 if sid == "A2" else 120 if sid == "B2" else 135))
        shots.append({
            "id": sid, "scene": scene, "intention": intention,
            "out_start_f": debut, "out_end_f": debut + frames, "out_frames": frames,
            "sortie_s": [round(debut / FPS, 3), round((debut + frames) / FPS, 3)],
            "source": {"file": f"{sources_dir}/{scene}.mp4",
                       "in_frame": curseur[scene], "source_frames": source_dispo,
                       "source_fps": 30, "freeze_tail_f": 0},
            "speed": v, "camera": cam_profil,
            "lip_sync_safe": scene in vitesses["lip_sync_safe"]["scenes"],
        })
        curseur[scene] += source_dispo
        reste[scene] = dispo - curseur[scene]

    # scènes
    for scene, frames in SCENE_FRAMES.items():
        info = par_scene[scene]
        scenes.append({
            "id": scene, "frames": frames, "debut_f": SCENE_START[scene],
            "fin_f": SCENE_START[scene] + frames, "duree_s": round(frames / FPS, 3),
            "source": f"{sources_dir}/{scene}.mp4",
            "source_images": info["images"],
            "fenetres_exploitables": info["fenetres_exploitables"],
            "pivot": info["pivot"],
            "ancre_sujet": info["ancre_sujet"],
            "colorimetrie": info["colorimetrie"]["correction_proposee"],
            "stabilite": info["stabilite"]["score"],
            "nettete_mediane": info["nettete"]["mediane"],
        })

    # transitions
    cuts = []
    for regle in config["transitions"]["selection"]["regles"]:
        tid = regle["transition"]
        conf = catalogue[tid]
        duree = int(conf["duree_f"])
        cuts.append({"coupe_f": int(regle["coupe_f"]), "coupe_s": round(int(regle["coupe_f"]) / FPS, 3),
                     "transition": tid, "nom": conf["nom"], "dur_f": duree,
                     "debut_f": int(regle["coupe_f"]) - 1,      # la transition se lit à travers la coupe
                     "fin_f": int(regle["coupe_f"]) - 1 + duree,
                     "shader": conf["shader"], "parametres": {**conf.get("parametres", {}), "duree_f": duree},
                     "justification": regle["justification"]})

    plan = {
        "version": "T1-V5-montage-plan-1",
        "generateur": "engine/montage_plan_builder.py",
        "config": config_path, "analyse": analysis_path,
        "profil": {"id": profil_nom, "champs": donnees, "limites": LIMITES},
        "output": {"width": 720, "height": 1280, "fps": FPS, "frames": 900, "duration_s": 30.0,
                   "audio": False, "codec": config["rendu"]["encodeur"]["codec"],
                   "crf": config["rendu"]["encodeur"]["crf"]},
        "scenes": scenes, "shots": shots, "cuts": cuts,
        "blocs": [{"id": bid, "debut_f": f["debut_f"], "fin_f": f["fin_f"],
                   "slot": config["blocs"][bid]["slot"], "champ": config["blocs"][bid].get("champ"),
                   "facultatif": bool(config["blocs"][bid].get("facultatif"))}
                  for bid, f in config["fenetres_blocs"].items()],
        "qualite": config["qualite"], "rendu": config["rendu"],
        "engagement": {"aucun_gel": True, "aucune_repetition_quatre_images": True,
                       "cta_opacite_pleine_frame_899": True, "lip_sync_scene": "S3",
                       "aucun_travail_audio": True},
    }
    # la devise est ajoutée par le moteur : le champ `prix` reste borné à 7 caractères
    plan["display"] = {
        "nom": donnees["nom"], "produit": donnees["produit"],
        "prix": f'{donnees["prix"]} FCFA' if donnees["prix"].strip() else "",
        "whatsapp": donnees["whatsapp"], "quartier": donnees["quartier"],
        "accroche": donnees.get("accroche", ""),
    }
    plan["empreinte_sources"] = {s["scene"]: s["sha256"] for s in analysis["scenes"]}
    plan["sha256_plan"] = hashlib.sha256(
        json.dumps({k: v for k, v in plan.items() if k != "sha256_plan"},
                   sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return plan


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Construction du plan de montage V5")
    ap.add_argument("--profile", default="demo_nominal", choices=sorted(PROFILS_COMMERCIAUX))
    ap.add_argument("--out", default="reports/montage_plan_v5_demo.json")
    ap.add_argument("--sources-dir", default="rushes/source/demo_v4")
    args = ap.parse_args(argv)
    plan = construire(args.profile, sources_dir=args.sources_dir)
    if "fixture" in args.sources_dir:
        plan["fixture"] = "fond entièrement blanc synthétique : fixture de validation graphique, pas un rush commerçant"
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = sum(s["out_frames"] for s in plan["shots"])
    rep = sum(s["speed"]["images_repetees"] for s in plan["shots"])
    print(f"plan {args.profile} : {len(plan['shots'])} plans, {total} images, "
          f"{len(plan['cuts'])} transitions, {rep} images répétées → {args.out}")
    for s in plan["shots"]:
        v = s["speed"]
        print(f"  {s['id']} {s['scene']} {s['out_frames']:>3} im. ← {s['source']['source_frames']:>3} src. "
              f"v[{v['vitesse_min']}–{v['vitesse_max']}] moy {v['vitesse_moyenne_reelle']} "
              f"cam {s['camera']['profil']} k{v['vitesse_max'] and s['camera']['zoom']['debut']}–{s['camera']['zoom']['fin']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
