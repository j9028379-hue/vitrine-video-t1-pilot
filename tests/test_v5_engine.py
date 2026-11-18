"""Tests du moteur V5 — analyse, plan, transitions, graphismes.

Ces tests ne remplacent jamais la vérification sur le MP4 (`tools/verify_worldclass.py`) : ils
verrouillent les **règles** (aucun gel, normalisation, bornes, repli d'accroche, courbes) et
empêchent une régression silencieuse.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from engine.adaptive_graphics_v5 import (GraphicsV5, alpha_scrim_requis, contraste, ease_out_back,
                                        luminance_rel)
from engine.food_cinema_transitions import TRANSITIONS, apply_transition
from engine.montage_plan_builder import (PROFILS_COMMERCIAUX, construire, courbe_vitesse,
                                        valider_profil)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "T1_worldclass_v5.json"


# --------------------------------------------------------------------------- #
# plan de montage
@pytest.fixture(scope="module")
def plan():
    return construire("demo_nominal")


def test_contrat_temporel(plan):
    assert plan["output"] == {**plan["output"], "width": 720, "height": 1280, "fps": 30,
                              "frames": 900, "duration_s": 30.0, "audio": False}
    durees = {s["id"]: s["frames"] for s in plan["scenes"]}
    assert durees == {"S1": 180, "S2": 240, "S3": 210, "S4": 270}
    assert sum(s["out_frames"] for s in plan["shots"]) == 900


def test_aucun_gel_dans_le_plan(plan):
    for shot in plan["shots"]:
        assert shot["source"]["freeze_tail_f"] == 0
        assert shot["speed"]["gel_de_fin"] == 0
        assert shot["speed"]["repetition_max_consecutive"] <= 2


def test_fenetre_source_consommee_exactement(plan):
    for shot in plan["shots"]:
        idx = shot["speed"]["indices_sources"]
        dispo = shot["source"]["source_frames"]
        assert idx[0] == 0
        assert idx[-1] == dispo - 1, "la fenêtre source doit être consommée jusqu'à la dernière image"
        assert all(b >= a for a, b in zip(idx, idx[1:])), "aucun retour en arrière"
        assert max(idx) < dispo


def test_normalisation_de_la_courbe():
    v = courbe_vitesse(120, 120, {"attaque": 1.4, "coeur": 0.85, "sortie": 1.45,
                                  "part_attaque": 0.14, "part_sortie": 0.2},
                       {"min": 0.8, "max": 1.55})
    assert abs(v["vitesse_moyenne_reelle"] - 1.0) < 0.01
    assert 0.8 <= v["vitesse_min"] and v["vitesse_max"] <= 1.55
    assert v["repetition_max_consecutive"] <= 2


def test_plan_deterministe(plan):
    a = construire("demo_nominal")
    assert a["sha256_plan"] == plan["sha256_plan"]


def test_lip_sync_sur_la_scene_humaine(plan):
    s3 = [s for s in plan["shots"] if s["scene"] == "S3"][0]
    assert s3["lip_sync_safe"] is True
    assert s3["speed"]["vitesse_max"] <= 1.10, "aucune accélération marquée sur un visage qui parle"


def test_camera_sous_le_plafond(plan):
    for shot in plan["shots"]:
        cam = shot["camera"]
        assert max(cam["zoom"]["debut"], cam["zoom"]["fin"]) <= 1.32
        if abs(cam["pan_rel"]["debut"]) + abs(cam["pan_rel"]["fin"]) > 0:
            assert cam["pan_rel"]["deplacement_px"] >= 6.0


def test_transitions_declarees(plan):
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    catalogue = config["transitions"]["catalogue"]
    for cut in plan["cuts"]:
        assert cut["transition"] in catalogue
        assert cut["dur_f"] == catalogue[cut["transition"]]["duree_f"]
        assert cut["justification"]
    assert len({c["transition"] for c in plan["cuts"]}) == 6


# --------------------------------------------------------------------------- #
# profils commerciaux
def test_limites_des_champs():
    assert valider_profil(PROFILS_COMMERCIAUX["champs_longs"]) == []
    trop = dict(PROFILS_COMMERCIAUX["demo_nominal"], nom="X" * 41)
    assert valider_profil(trop), "un nom de 41 caractères doit être refusé"
    assert "FCFA" not in PROFILS_COMMERCIAUX["demo_nominal"]["prix"], \
        "la devise est ajoutée par le moteur, pas saisie dans le champ"


def test_accroche_vide_desactive_gb04():
    plan = construire("accroche_vide")
    assert plan["display"]["accroche"] == ""
    graphics = GraphicsV5(CONFIG, plan["display"],
                          json.loads((ROOT / "reports" / "scene_analysis_T1.json").read_text(encoding="utf-8")))
    assert "GB04" not in graphics.blocs
    motifs = [d for d in graphics.decisions if d.get("bloc") == "GB04"]
    assert motifs and all(d["decision"] == "non affiché" for d in motifs), \
        "GB04 doit être explicitement non affiché, sans autre effet de bord"


# --------------------------------------------------------------------------- #
# graphismes
@pytest.fixture(scope="module")
def graphics():
    plan = construire("champs_longs")
    analyse = json.loads((ROOT / "reports" / "scene_analysis_T1.json").read_text(encoding="utf-8"))
    return GraphicsV5(CONFIG, plan["display"], analyse)


def test_huit_blocs(graphics):
    assert sorted(graphics.blocs) == [f"GB0{i}" for i in range(1, 9)]


def test_textes_jamais_coupes(graphics):
    for bloc in graphics.blocs.values():
        for el in bloc.elements:
            if el.type != "texte":
                continue
            for ligne in el.lignes:
                assert ligne.largeur <= el.boite[2] + 2, f"{bloc.id} : ligne plus large que sa boîte"
                assert "  " not in ligne.texte
            assert len(el.lignes) <= (el.parametres.get("lignes_max") or 2)


def test_aucune_collision_entre_blocs(graphics):
    blocs = list(graphics.blocs.values())
    for i, a in enumerate(blocs):
        for b in blocs[i + 1:]:
            if a.debut_f < b.fin_f and b.debut_f < a.fin_f:
                ra = a.carte or (a.elements[0].boite if a.elements else None)
                rb = b.carte or (b.elements[0].boite if b.elements else None)
                if not ra or not rb:
                    continue
                ix = max(0.0, min(ra[0] + ra[2], rb[0] + rb[2]) - max(ra[0], rb[0]))
                iy = max(0.0, min(ra[1] + ra[3], rb[1] + rb[3]) - max(ra[1], rb[1]))
                assert ix * iy < 0.02 * max(1.0, ra[2] * ra[3]), f"{a.id} recouvre {b.id}"


def test_ease_out_back_depasse_un():
    valeurs = [ease_out_back(t) for t in np.linspace(0, 1, 40)]
    assert max(valeurs) > 1.02, "easeOutBack doit produire un vrai rebond"
    assert abs(valeurs[-1] - 1.0) < 1e-6


def test_contraste_et_scrim():
    blanc, noir = (255, 255, 255), (12, 19, 31)
    assert contraste(blanc, noir) > 15
    assert alpha_scrim_requis(blanc, blanc, 4.5) > 0.3
    assert alpha_scrim_requis(noir, (10.0, 10.0, 10.0), 4.5) == 0.0


def test_ordre_de_dessin_du_packshot(graphics):
    gb08, gb07 = graphics.blocs["GB08"].carte, graphics.blocs["GB07"].carte
    assert gb07[1] >= gb08[1] + gb08[3], "le bouton WhatsApp doit être sous la carte packshot"
    assert graphics.blocs["GB07"].fin_f >= 900 and graphics.blocs["GB08"].fin_f >= 900


# --------------------------------------------------------------------------- #
# transitions
def _images(w=720, h=1280):
    a = np.zeros((h, w, 3), np.uint8)
    a[: h // 2] = (40, 90, 200)
    b = np.zeros((h, w, 3), np.uint8)
    b[:, w // 2:] = (200, 120, 40)
    return a, b


@pytest.mark.parametrize("nom", sorted(TRANSITIONS))
def test_transitions_produisent_une_image(nom):
    a, b = _images()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    params = {**config["transitions"]["catalogue"][nom].get("parametres", {}),
              "duree_f": config["transitions"]["catalogue"][nom]["duree_f"]}
    for p in (0.0, 0.25, 0.5, 0.75, 1.0):
        out = apply_transition(nom, a, b, p, params, {"amber": (120, 196, 255), "cream": (239, 248, 255)})
        assert out.shape == (1280, 720, 3)
        assert out.dtype == np.uint8
        assert out.std() > 0


def test_cut_est_un_remplacement():
    a, b = _images()
    out = apply_transition("TR_CUT", a, b, 0.3, {}, {})
    assert np.array_equal(out, b)
