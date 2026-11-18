"""Read-only adapter from the locked T1 V1.2 + V6.2 specs to render_plan.json."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import tempfile
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
    previous_variant_id: str | None = None,
) -> dict[str, Any]:
    """Select one approved local track in the strict 1 → 2 → 3 → 4 cycle.

    ``previous_variant_id`` is ``None`` only for the first render. Afterwards the
    local orchestrator passes the variant ID from the last *successful* render.
    Automatic retries of the same job therefore keep the same selection, while a
    failed render leaves the cycle unchanged. No network or catalogue lookup is
    required.
    """
    tracks = music_pack.get("tracks", [])
    selection = music_pack.get("selection_contract", {})
    approved_ids = selection.get("allowed_variant_ids", [])
    expected_pixabay_ids = [239426, 464383, 406552, 178406]
    if music_pack.get("audio_profile") != "afrobeat_amapiano":
        raise ValueError("Le profil audio ne correspond pas au catalogue Afrobeat/Amapiano approuvé.")
    if len(tracks) != 4 or [track.get("id") for track in tracks] != approved_ids:
        raise ValueError("Le pack musical doit contenir exactement les quatre variantes approuvées.")
    if [track.get("pixabay_id") for track in tracks] != expected_pixabay_ids:
        raise ValueError("Le pack musical ne correspond pas au lot approuvé.")
    if any(track.get("content_id_registered") or not track.get("production_eligible") for track in tracks):
        raise ValueError("Toutes les variantes doivent être sans Content ID et prêtes pour la production.")
    if (
        selection.get("default_variant_id") != approved_ids[0]
        or selection.get("runtime_mode") != "production auto and explicit selection follow the strict approved order 1→2→3→4 after each successful render"
        or selection.get("no_immediate_repeat") is not True
        or selection.get("automatic_candidate_count_after_first_render") != 1
        or selection.get("explicit_selection_policy") != "exact_successor_only"
        or selection.get("idempotency_ledger_key") != "successful_render_jobs"
        or selection.get("state_update_policy") != "after_success_only"
        or selection.get("failed_render_state_policy") != "unchanged"
    ):
        raise ValueError("Le contrat musical T1 doit imposer le cycle strict et avancer seulement après succès.")

    by_id = {track["id"]: track for track in tracks}
    if previous_variant_id is not None and previous_variant_id not in by_id:
        raise ValueError(f"Variante musicale précédente inconnue : {previous_variant_id}")
    if not render_job_id:
        raise ValueError("render_job_id est obligatoire pour une sélection cyclique reproductible.")
    previous_index = -1 if previous_variant_id is None else approved_ids.index(previous_variant_id)
    expected = tracks[(previous_index + 1) % len(tracks)]
    if requested_variant_id != "auto":
        if requested_variant_id not in by_id:
            raise ValueError(f"Variante musicale inconnue : {requested_variant_id}")
        if requested_variant_id == previous_variant_id:
            raise ValueError("Répétition musicale immédiate interdite.")
        if requested_variant_id != expected["id"]:
            raise ValueError(
                f"Le cycle T1 strict attend {expected['id']} ; {requested_variant_id} ne peut pas le contourner."
            )
        return expected
    return expected


MUSIC_STATE_SCHEMA_VERSION = "1.0.0"


def load_music_selection_state(state_path: Path) -> dict[str, Any]:
    """Load the caller-owned state that survives independent render attempts."""
    if not state_path.exists():
        return {
            "schema_version": MUSIC_STATE_SCHEMA_VERSION,
            "last_successful_music_id": None,
            "last_successful_render_job_id": None,
            "successful_render_count": 0,
            "successful_render_jobs": {},
        }
    state = load_json(state_path)
    required = {
        "schema_version",
        "last_successful_music_id",
        "last_successful_render_job_id",
        "successful_render_count",
        "successful_render_jobs",
    }
    if set(state) != required or state["schema_version"] != MUSIC_STATE_SCHEMA_VERSION:
        raise ValueError("État de rotation musicale T1 invalide.")
    allowed_ids = {None, "t1_music_239426", "t1_music_464383", "t1_music_406552", "t1_music_178406"}
    if state["last_successful_music_id"] not in allowed_ids:
        raise ValueError("Dernière musique réussie T1 inconnue.")
    if not isinstance(state["successful_render_count"], int) or state["successful_render_count"] < 0:
        raise ValueError("Compteur de réussites musicales T1 invalide.")
    receipts = state["successful_render_jobs"]
    if (
        not isinstance(receipts, dict)
        or any(not isinstance(job_id, str) or not job_id or music_id not in allowed_ids - {None} for job_id, music_id in receipts.items())
        or len(receipts) != state["successful_render_count"]
    ):
        raise ValueError("Registre idempotent des réussites musicales T1 invalide.")
    if (state["last_successful_music_id"] is None) != (state["last_successful_render_job_id"] is None):
        raise ValueError("L'état T1 doit renseigner ensemble la musique et le rendu réussis.")
    if (state["successful_render_count"] == 0) != (state["last_successful_music_id"] is None):
        raise ValueError("Un état T1 vide ne peut contenir aucune réussite, et inversement.")
    if state["last_successful_render_job_id"] is not None and receipts.get(state["last_successful_render_job_id"]) != state["last_successful_music_id"]:
        raise ValueError("La dernière réussite T1 doit être présente dans le registre idempotent.")
    return state


def select_music_track_from_state(
    music_pack: dict[str, Any],
    *,
    render_job_id: str,
    state_path: Path,
    requested_variant_id: str = "auto",
) -> dict[str, Any]:
    """Select against the last success persisted by the render orchestrator."""
    state = load_music_selection_state(state_path)
    return select_music_track(
        music_pack,
        render_job_id=render_job_id,
        requested_variant_id=requested_variant_id,
        previous_variant_id=state["last_successful_music_id"],
    )


def _record_music_render_result_unlocked(
    music_pack: dict[str, Any],
    *,
    state_path: Path,
    render_job_id: str,
    selected_music_id: str,
    succeeded: bool,
) -> dict[str, Any]:
    """Atomically advance rotation state after success and never after failure.

    Replaying any previously recorded successful callback is idempotent. Every
    new successful job must commit the exact successor of the last success.
    """
    if not render_job_id:
        raise ValueError("render_job_id est obligatoire pour enregistrer le résultat musical.")
    allowed = set(music_pack.get("selection_contract", {}).get("allowed_variant_ids", []))
    if selected_music_id not in allowed:
        raise ValueError("La musique rendue n'appartient pas au pool T1 approuvé.")
    current = load_music_selection_state(state_path)
    if not succeeded:
        return current
    if render_job_id in current["successful_render_jobs"]:
        if current["successful_render_jobs"][render_job_id] != selected_music_id:
            raise ValueError("Un même rendu réussi ne peut pas changer de musique après coup.")
        return current
    ordered_ids = list(music_pack["selection_contract"]["allowed_variant_ids"])
    previous_id = current["last_successful_music_id"]
    expected_id = ordered_ids[0] if previous_id is None else ordered_ids[(ordered_ids.index(previous_id) + 1) % len(ordered_ids)]
    if selected_music_id != expected_id:
        raise ValueError(
            f"Le succès T1 doit respecter le cycle strict : {expected_id} attendu, {selected_music_id} reçu."
        )
    updated_jobs = dict(current["successful_render_jobs"])
    updated_jobs[render_job_id] = selected_music_id
    updated = {
        "schema_version": MUSIC_STATE_SCHEMA_VERSION,
        "last_successful_music_id": selected_music_id,
        "last_successful_render_job_id": render_job_id,
        "successful_render_count": current["successful_render_count"] + 1,
        "successful_render_jobs": updated_jobs,
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{state_path.name}.", dir=state_path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(updated, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, state_path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
    return updated


def record_music_render_result(
    music_pack: dict[str, Any],
    *,
    state_path: Path,
    render_job_id: str,
    selected_music_id: str,
    succeeded: bool,
) -> dict[str, Any]:
    """Serialize callbacks across processes before applying the atomic update."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = state_path.parent / f".{state_path.name}.lock"
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            return _record_music_render_result_unlocked(
                music_pack,
                state_path=state_path,
                render_job_id=render_job_id,
                selected_music_id=selected_music_id,
                succeeded=succeeded,
            )
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def attach_music_track(
    plan: dict[str, Any],
    music_pack: dict[str, Any],
    *,
    render_job_id: str,
    requested_variant_id: str = "auto",
    previous_variant_id: str | None = None,
) -> dict[str, Any]:
    """Attach the selected local MP3 without changing merchant data or visual timing."""
    selected = select_music_track(
        music_pack,
        render_job_id=render_job_id,
        requested_variant_id=requested_variant_id,
        previous_variant_id=previous_variant_id,
    )
    plan["output"]["audio"] = True
    plan["audio_track"] = {
        "enabled": True,
        "mode": "offline_music_sidecar_v1",
        "pack_id": music_pack["id"],
        "audio_profile": music_pack["audio_profile"],
        "variant_id": selected["id"],
        "previous_variant_id": previous_variant_id,
        "last_successful_music_id": previous_variant_id,
        "no_immediate_repeat": True,
        "state_update_policy": "after_success_only",
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
    parser.add_argument(
        "--previous-music-variant",
        default=None,
        help="Variant ID used by the last successful render; omit only for the first render.",
    )
    parser.add_argument(
        "--music-state",
        type=Path,
        help="Caller-owned persistent JSON state; when supplied it is the source of the last successful music ID.",
    )
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
        previous_variant_id = args.previous_music_variant
        if args.music_state is not None:
            persisted = load_music_selection_state(args.music_state)["last_successful_music_id"]
            if previous_variant_id is not None and previous_variant_id != persisted:
                raise ValueError("--previous-music-variant diverge de --music-state.")
            previous_variant_id = persisted
        plan = attach_music_track(
            plan,
            load_json(args.music_pack),
            render_job_id=args.render_job_id,
            requested_variant_id=args.music_variant,
            previous_variant_id=previous_variant_id,
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
