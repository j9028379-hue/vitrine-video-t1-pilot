"""Read-only adapter from the locked T1 V1.2 + V6.2 specs to render_plan.json."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
V12_PATH = ROOT / "specs" / "T1_ENGINEERING_SPEC_V1_2.json"
V62_PATH = ROOT / "specs" / "restaurants_maquis_T1.spec_v6_2.json"
V62_PUBLIC_PATH = ROOT / "specs" / "restaurants_maquis_T1.spec_v6_2.public-safe.json"
DEFAULT_V62_PATH = V62_PATH if V62_PATH.exists() else V62_PUBLIC_PATH
INPUT_PATH = ROOT / "demo" / "T1_demo_input.json"
OUTPUT_PATH = ROOT / "render_plan.json"
MUSIC_PACK_PATH = ROOT / "config" / "T1_special_menu_music_pack_v1_0_0.json"
VOICE_MIX_PATH = ROOT / "config" / "T1_special_menu_voice_mix_v1_0_0.json"


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


def build_render_plan(v12: dict[str, Any], v62: dict[str, Any], raw_input: dict[str, Any], v62_source: str | None = None) -> dict[str, Any]:
    validate_specs(v12, v62)
    if v62_source is None:
        v62_source = str(DEFAULT_V62_PATH.relative_to(ROOT))
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
            "v62": v62_source,
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


def select_music_track(
    music_pack: dict[str, Any],
    *,
    render_job_id: str,
    requested_variant_id: str = "auto",
) -> dict[str, Any]:
    """Select one of the four approved, production-ready local tracks."""
    tracks = music_pack.get("tracks", [])
    approved_ids = music_pack.get("selection_contract", {}).get("allowed_variant_ids", [])
    expected_pixabay_ids = [239426, 464383, 406552, 178406]
    if len(tracks) != 4 or [track.get("id") for track in tracks] != approved_ids:
        raise ValueError("Le pack musical doit contenir exactement les quatre variantes approuvées.")
    if [track.get("pixabay_id") for track in tracks] != expected_pixabay_ids:
        raise ValueError("Le pack musical ne correspond pas au lot approuvé.")
    if any(track.get("content_id_registered") or not track.get("production_eligible") for track in tracks):
        raise ValueError("Toutes les variantes doivent être sans Content ID et prêtes pour la production.")
    by_id = {track["id"]: track for track in tracks}
    if requested_variant_id != "auto":
        if requested_variant_id not in by_id:
            raise ValueError(f"Variante musicale inconnue : {requested_variant_id}")
        return by_id[requested_variant_id]
    if not render_job_id:
        raise ValueError("render_job_id est obligatoire pour une sélection automatique reproductible.")
    digest = hashlib.sha256(render_job_id.encode("utf-8")).digest()
    return tracks[int.from_bytes(digest[:8], "big") % 4]


def attach_music_track(
    plan: dict[str, Any],
    music_pack: dict[str, Any],
    *,
    render_job_id: str,
    requested_variant_id: str = "auto",
) -> dict[str, Any]:
    """Attach the selected local MP3 without changing merchant data or visual timing."""
    selected = select_music_track(
        music_pack,
        render_job_id=render_job_id,
        requested_variant_id=requested_variant_id,
    )
    plan["output"]["audio"] = True
    plan["audio_track"] = {
        "enabled": True,
        "mode": "offline_music_sidecar_v1",
        "pack_id": music_pack["id"],
        "variant_id": selected["id"],
        "pixabay_id": selected["pixabay_id"],
        "file": selected["file"],
        "sha256": selected["sha256"],
        "start_f": 0,
        "end_f_exclusive": 900,
        "time_map": "identity_1_0x",
        "network_required": False,
        "runtime_no_speech_gain_db": selected["runtime_no_speech_gain_db"],
        "runtime_speech_gain_db": selected["runtime_speech_gain_db"],
        "duck_attack_ms": music_pack["mix_contract"]["duck_attack_ms"],
        "duck_release_ms": music_pack["mix_contract"]["duck_release_ms"],
        "final_ducking_status": music_pack["mix_contract"]["final_ducking_status"],
        "sfx": False,
        "production_eligible": True,
    }
    return plan


def attach_voice_track(plan: dict[str, Any], voice_mix: dict[str, Any]) -> dict[str, Any]:
    """Attach the validated 30 s French voice stem and its ducking contract."""
    audio_track = plan.get("audio_track", {})
    if not audio_track.get("enabled"):
        raise ValueError("La voix T1 exige qu'une des quatre musiques approuvées soit déjà attachée.")
    clips = voice_mix.get("voice", {}).get("clips", [])
    if len(clips) != 4 or [clip.get("scene") for clip in clips] != [1, 2, 3, 4]:
        raise ValueError("Le sidecar voix doit contenir exactement une prise pour chacune des quatre scènes.")
    mix = voice_mix["mix_contract"]
    stem_rel = voice_mix["voice"]["stem_file"]
    stem = ROOT / stem_rel
    if not stem.is_file():
        raise ValueError(f"Tige voix locale absente : {stem_rel}")
    plan["voice_track"] = {
        "enabled": True,
        "mode": "offline_voice_stem_v1",
        "file": stem_rel,
        "sha256": hashlib.sha256(stem.read_bytes()).hexdigest(),
        "voice_id": voice_mix["voice"]["voice_id"],
        "language": voice_mix["voice"]["language"],
        "start_f": 0,
        "end_f_exclusive": 900,
        "time_map": "identity_1_0x",
        "gain_db": mix["voice_gain_db"],
        "network_required": False,
        "placements": [
            {
                "scene": clip["scene"],
                "start_s": clip["start_s"],
                "start_f": int(round(float(clip["start_s"]) * 30)),
                "text": clip["text"],
            }
            for clip in clips
        ],
    }
    audio_track.update({
        "runtime_no_speech_gain_db": mix["music_open_gain_db"],
        "runtime_speech_gain_db": mix["music_under_voice_gain_db"],
        "duck_attack_ms": mix["duck_attack_ms"],
        "duck_release_ms": mix["duck_release_ms"],
        "final_ducking_status": "validated_offline_reference_mix_v1",
        "sfx": False,
    })
    plan["audio_mix"] = {
        "mode": "music_plus_voice_ducking_v1",
        "music_variant_count": 4,
        "duck_depth_db": mix["duck_depth_db"],
        "attack_curve": mix["duck_attack_curve"],
        "release_curve": mix["duck_release_curve"],
        "master_target_lufs": mix["master_target_lufs"],
        "master_true_peak_dbtp_max": mix["master_true_peak_dbtp_max"],
        "sfx": False,
        "validation_report": "reports/T1_voice_music_v1_validation.json",
    }
    return plan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v12", type=Path, default=V12_PATH)
    parser.add_argument("--v62", type=Path, default=DEFAULT_V62_PATH)
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--enable-music", action="store_true", help="Attach the approved T1 four-track offline music sidecar.")
    parser.add_argument("--music-pack", type=Path, default=MUSIC_PACK_PATH)
    parser.add_argument("--music-variant", default="auto", help="Variant ID, or 'auto' for deterministic selection.")
    parser.add_argument("--render-job-id", default="t1-demo-0001", help="Stable key used by automatic music selection.")
    parser.add_argument("--enable-voice", action="store_true", help="Attach the validated French 30 s voice stem and ducking contract.")
    parser.add_argument("--voice-mix", type=Path, default=VOICE_MIX_PATH)
    args = parser.parse_args()
    try:
        v62_source = str(args.v62.resolve().relative_to(ROOT))
    except ValueError:
        v62_source = str(args.v62.resolve())
    plan = build_render_plan(load_json(args.v12), load_json(args.v62), load_json(args.input), v62_source=v62_source)
    if args.enable_music:
        plan = attach_music_track(
            plan,
            load_json(args.music_pack),
            render_job_id=args.render_job_id,
            requested_variant_id=args.music_variant,
        )
    if args.enable_voice:
        if not args.enable_music:
            raise ValueError("--enable-voice exige --enable-music.")
        plan = attach_voice_track(plan, load_json(args.voice_mix))
    args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    music_note = f", musique {plan['audio_track']['variant_id']}" if plan["audio_track"]["enabled"] else ", silencieux"
    voice_note = ", voix française + ducking validé" if plan.get("voice_track", {}).get("enabled") else ""
    print(f"render_plan.json écrit : {args.output} — {len(plan['shots'])} plans, {len(plan['overlays'])} blocs, {plan['output']['frames']} images{music_note}{voice_note}.")


if __name__ == "__main__":
    main()
