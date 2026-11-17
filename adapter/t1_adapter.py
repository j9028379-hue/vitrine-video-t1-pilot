"""Read-only adapter from the locked T1 V1.2 + V6.2 specs to render_plan.json."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
V12_PATH = ROOT / "specs" / "T1_ENGINEERING_SPEC_V1_2.json"
V62_PATH = ROOT / "specs" / "restaurants_maquis_T1.spec_v6_2.json"
INPUT_PATH = ROOT / "demo" / "T1_demo_input.json"
OUTPUT_PATH = ROOT / "render_plan.json"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def normalize_fields(data: dict[str, Any], contract: dict[str, Any]) -> dict[str, str]:
    """Apply only the input cleaning/presentation rules written in V1.2."""
    definitions = {item["id"]: item for item in contract["champs"]}
    cleaned: dict[str, str] = {}
    for key, definition in definitions.items():
        value = data.get(key, "")
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise ValueError(f"Le champ {key!r} doit être du texte.")
        value = re.sub(r"\s+", " ", value.strip())
        if key in {"nom", "produit", "accroche"}:
            value = value.rstrip(".")
        if definition.get("obligatoire") and not value:
            raise ValueError(f"Champ obligatoire manquant : {key}")
        if len(value) > int(definition["max"]):
            raise ValueError(f"Champ {key} trop long : {len(value)} > {definition['max']} caractères.")
        cleaned[key] = value
    return cleaned


def display_price(price: str) -> str:
    if not price:
        return price
    return price if "FCFA" in price.upper() else f"{price} FCFA"


def validate_specs(v12: dict[str, Any], v62: dict[str, Any]) -> None:
    assert v12["spec_version"] == "1.2"
    assert v62["spec_version"] == "6.2"
    assert v12["gabarit"]["id"] == v62["gabarit_id"] == "restaurants_maquis_T1"
    assert v12["units"]["fps"] == 30 and v12["units"]["total_frames"] == 900
    assert len(v12["scenes"]) == len(v62["scenes"]) == 4
    assert len(v12["plans"]) == len(v62["video_track"]) == 12
    assert len(v12["graphic_blocks"]) == 8 and len(v12["presets"]) == 14
    zones62 = v62["design_system"]["zones_de_securite"]
    assert v12["safe_zones"] == {key: zones62[key] for key in ("x_min", "x_max", "y_min", "y_max")}
    expected = [("S1", 180), ("S2", 240), ("S3", 210), ("S4", 270)]
    assert [(s["id"], s["frames"]) for s in v12["scenes"]] == expected
    assert sum(p["out_frames"] for p in v12["plans"]) == 900
    assert len(v12["text_blocks"]) == 8 and len(v12["events"]) == 28


def build_render_plan(v12: dict[str, Any], v62: dict[str, Any], raw_input: dict[str, Any]) -> dict[str, Any]:
    validate_specs(v12, v62)
    if raw_input.get("demo") is not True:
        raise ValueError("Le fichier d'entrée de ce pilote doit rester explicitement marqué demo=true.")
    data = normalize_fields(raw_input, v12["data_contract"])
    scene_specs = {scene["id"]: scene for scene in v12["scenes"]}
    video_by_plan = {item["plan_id"]: item for item in v62["video_track"]}
    motion_by_id = {item["id"]: item for item in v12["movements"]}
    rush_manifest = load_json(ROOT / "rushes" / "manifest.json")
    rush_by_scene = {item["id"]: item for item in rush_manifest["sources"]}
    shots = []
    for shot in v12["plans"]:
        scene = shot["scene"]
        video = video_by_plan[shot["id"]]
        motion_id = shot["movement"].split("+")[0]
        motion = motion_by_id[motion_id]
        shots.append({
            "id": shot["id"], "scene": scene,
            "out_start_f": shot["out_start_f"], "out_end_f": shot["out_end_f"],
            "out_frames": shot["out_frames"],
            "source": {
                "asset_id": scene,
                "file": f"rushes/source/{rush_by_scene[scene]['filename']}",
                "sha256": rush_by_scene[scene]["sha256"],
                "in_frame": shot["source_in_f"], "out_frame": shot["source_out_f"],
                "source_frames": shot["source_frames"], "freeze_tail_f": shot["freeze_tail_f"],
            },
            "zoom_curve": {
                "base": shot["k_base"], "movement_id": motion_id,
                "movement": motion["nom"], "parameters": motion["parametres"],
            },
            "transition_out": shot["transition_out"],
            "color_grade": video.get("etalonnage"),
        })
    overlay = []
    for block in v12["text_blocks"]:
        overlay.append({
            "id": block["id"], "graphic_block": block["bloc"], "composition": block["compo"],
            "field": block["champ"], "start_f": block["start_f"], "end_f": block["end_f"],
            "text_preset": next((p["id"] for p in v12["presets"] if p.get("bloc") == block["bloc"]), None),
        })
    return {
        "plan_version": 1,
        "project": "VITRINE VIDÉO — Restaurants et Maquis / T1 — Plat du jour",
        "reconstruction_note": "Sources du projet moteur précédent absentes de l'espace local et de Drive; adapter reconstitué depuis les documents de référence immuables.",
        "demo_only": True,
        "spec_sources": {
            "v12": "specs/T1_ENGINEERING_SPEC_V1_2.json",
            "v62": "specs/restaurants_maquis_T1.spec_v6_2.json",
            "write_back": False,
        },
        "output": {"width": 720, "height": 1280, "fps": 30, "frames": 900, "duration_s": 30.0, "audio": False},
        "fields": data,
        "display": {**data, "prix": display_price(data["prix"])},
        "scenes": [{"id": s["id"], "frames": s["frames"], "name": s["nom"]} for s in v12["scenes"]],
        "shots": shots,
        "cuts": v12["transitions"]["assignments"],
        "overlays": overlay,
        "graphic_blocks": v12["graphic_blocks"],
        "motion_presets": v12["presets"],
        "design_system": v62["design_system"],
        "safe_zones": v12["safe_zones"],
        "audio_track": {"enabled": False, "note": "Premier rendu T1 volontairement muet; musique, SFX, voix et sous-titres hors périmètre."},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v12", type=Path, default=V12_PATH)
    parser.add_argument("--v62", type=Path, default=V62_PATH)
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    plan = build_render_plan(load_json(args.v12), load_json(args.v62), load_json(args.input))
    args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"render_plan.json écrit : {args.output} — {len(plan['shots'])} plans, {len(plan['overlays'])} blocs, {plan['output']['frames']} images.")


if __name__ == "__main__":
    main()
