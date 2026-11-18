#!/usr/bin/env python3
"""Construit le contrat T1 V3.1 prêt pour intégration.

La V3 visuelle reste immuable. V3.1 ajoute à son JSON la machine d'états
explicite des 12 écrans de capture (4 scènes × A/B/C), les liaisons de données
et le contrat de passage au moteur. La planche PNG n'est qu'une preuve visuelle :
le JSON produit ici est la source destinée au programmeur.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
V3_PATH = ROOT / "config" / "T1_special_menu_reference_v3.json"
GUIDE_PATH = ROOT / "capture-guide" / "consignes_T1.json"
OUT_PATH = ROOT / "config" / "T1_special_menu_reference_v3_1.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _runtime_path(scene_id: str, field: str) -> str:
    return f"runtime.captures.{scene_id}.{field}"


def _screen_triplet(scene: dict[str, Any], scene_index: int, guide: dict[str, Any]) -> list[dict[str, Any]]:
    scene_id = scene["id"]
    n = scene_index + 1
    total = len(guide["scenes"])
    seconds = int(scene["duration_s"])
    duration_label = f"{seconds} secondes"
    take_label = f"PRISE {n} · 0:{seconds:02d}"
    guide_scene = guide["scenes"][scene_index]
    next_guide = f"T1_CAPTURE_S{n + 1}_A_GUIDE" if n < total else "T1_MONTAGE_STATUS"
    primary_review_label = "SCÈNE SUIVANTE" if n < total else "VOIR MON MONTAGE"

    common = {
        "scene_id": scene_id,
        "scene_index": n,
        "scene_total": total,
        "capture_duration_ms": seconds * 1000,
        "capture_slot": f"captures.{scene_id}.uri",
    }

    guide_screen = {
        **common,
        "ordinal": (n - 1) * 3 + 1,
        "screen_id": f"T1_CAPTURE_S{n}_A_GUIDE",
        "route_key": f"t1.capture.s{n}.guide",
        "state": "A_GUIDE",
        "purpose": "expliquer la prise avant d'ouvrir l'enregistrement",
        "bindings": {
            "scene_counter": f"literal:SCÈNE {n}/{total}",
            "duration": f"capture-guide/consignes_T1.json#/scenes/{scene_index}/secondes",
            "title": f"capture-guide/consignes_T1.json#/scenes/{scene_index}/titre",
            "instruction": f"capture-guide/consignes_T1.json#/scenes/{scene_index}/consigne",
            "film_list": f"capture-guide/consignes_T1.json#/scenes/{scene_index}/a_filmer",
            "avoid_list": f"capture-guide/consignes_T1.json#/scenes/{scene_index}/a_eviter",
            "voice_note": "capture-guide/consignes_T1.json#/mention_voix_commune",
            "example": f"capture-guide/consignes_T1.json#/scenes/{scene_index}/exemple",
            "primary_action_label": "capture-guide/consignes_T1.json#/bouton_principal",
        },
        "resolved_text": {
            "scene_counter": f"SCÈNE {n}/{total}",
            "duration": duration_label,
            "title": guide_scene["titre"],
            "instruction": guide_scene["consigne"],
            "film_section_label": "À FILMER",
            "film_list": guide_scene["a_filmer"],
            "avoid_section_label": "À ÉVITER",
            "avoid_list": guide_scene["a_eviter"],
            "voice_section_label": "TU PEUX PARLER PENDANT QUE TU FILMES",
            "voice_note": guide["mention_voix_commune"],
            "example_section_label": "EXEMPLE DE PHRASE — FACULTATIF",
            "example": guide_scene["exemple"],
            "primary_action": guide["bouton_principal"],
        },
        "visible_components": [
            "camera_preview_dimmed",
            "scene_progress",
            "instruction_sheet",
            "film_list",
            "avoid_list",
            "voice_note",
            "optional_example",
            "start_recording_button",
        ],
        "forbidden_components": ["recording_timer", "recording_progress", "review_actions", "subtitles"],
        "actions": [
            {
                "event": "START_RECORDING",
                "label": guide["bouton_principal"],
                "effects": ["close_instruction_sheet", "run_COUNTDOWN_3_2_1"],
                "next_screen_id": f"T1_CAPTURE_S{n}_B_RECORDING",
            }
        ],
        "proof_png": f"ui-screens/ecran_08_scene{n}_etatA_consigne.png",
    }

    recording_screen = {
        **common,
        "ordinal": (n - 1) * 3 + 2,
        "screen_id": f"T1_CAPTURE_S{n}_B_RECORDING",
        "route_key": f"t1.capture.s{n}.recording",
        "state": "B_RECORDING",
        "purpose": "capturer exactement la durée de la scène, image et voix",
        "bindings": {
            "elapsed_ms": "runtime.capture.elapsed_ms",
            "progress_0_to_1": "runtime.capture.progress",
            "output_uri": _runtime_path(scene_id, "uri"),
        },
        "resolved_text": {
            "status": "ENREGISTREMENT",
            "timer_initial": "0:00",
            "timer_terminal": f"0:{seconds:02d}",
        },
        "visible_components": ["camera_preview", "recording_timer", "recording_progress"],
        "forbidden_components": [
            "instruction_sheet",
            "merchant_fields",
            "example_text",
            "manual_stop_button",
            "review_actions",
            "subtitles",
        ],
        "capture": {
            "starts_after": "COUNTDOWN_3_2_1_COMPLETE",
            "video": True,
            "microphone_audio": True,
            "source_speed": 1.0,
            "duration_ms": seconds * 1000,
            "auto_stop": True,
            "manual_stop": False,
            "last_three_seconds_feedback": ["timer_accent", "progress_accent", "haptic_pulse"],
            "write_to": _runtime_path(scene_id, "uri"),
        },
        "actions": [
            {
                "event": "CAPTURE_DURATION_REACHED",
                "effects": ["stop_recorder", "finalize_capture_file", "open_audio_review"],
                "next_screen_id": f"T1_CAPTURE_S{n}_C_REVIEW",
            }
        ],
        "proof_png": f"ui-screens/ecran_08_scene{n}_etatB_enregistrement.png",
    }

    review_screen = {
        **common,
        "ordinal": (n - 1) * 3 + 3,
        "screen_id": f"T1_CAPTURE_S{n}_C_REVIEW",
        "route_key": f"t1.capture.s{n}.review",
        "state": "C_REVIEW",
        "purpose": "faire écouter et valider la prise avant de continuer",
        "bindings": {
            "preview_uri": _runtime_path(scene_id, "uri"),
            "audio_enabled": "literal:true",
            "loop": "literal:true",
        },
        "resolved_text": {
            "take_label": take_label,
            "status": "PRISE ENREGISTRÉE",
            "playback_note": "Lecture avec le son, en boucle",
            "secondary_action": "REFAIRE",
            "primary_action": primary_review_label,
        },
        "visible_components": [
            "captured_video_preview",
            "captured_audio_playback",
            "take_label",
            "redo_button",
            "accept_button",
        ],
        "forbidden_components": ["instruction_sheet", "recording_timer", "recording_progress", "subtitles"],
        "playback": {"audio": True, "loop": True, "source_speed": 1.0},
        "actions": [
            {
                "event": "RETAKE",
                "label": "REFAIRE",
                "effects": [f"delete:{_runtime_path(scene_id, 'uri')}", "reset_scene_capture_state"],
                "next_screen_id": f"T1_CAPTURE_S{n}_A_GUIDE",
            },
            {
                "event": "ACCEPT_CAPTURE",
                "label": primary_review_label,
                "effects": [f"persist:{_runtime_path(scene_id, 'uri')}"],
                "next_screen_id": next_guide,
            },
        ],
        "proof_png": f"ui-screens/ecran_08_scene{n}_etatC_validation.png",
    }
    return [guide_screen, recording_screen, review_screen]


def build_contract() -> dict[str, Any]:
    v3 = _load(V3_PATH)
    guide = _load(GUIDE_PATH)
    result = copy.deepcopy(v3)
    result["schema_version"] = "1.3.0"
    result["id"] = "restaurants_maquis_T1_special_menu_reference_v3_1"
    result["display_name"] = "T1 — Plat du jour — Special Menu Reference V3.1 — contrat 12 écrans"
    result["status"] = "implementation_ready_with_explicit_12_screen_capture_flow"
    result["revision"] = {
        "from": v3["id"],
        "requested_at": "2026-11-18",
        "requested_changes": [
            "make the 4-scene x 3-state capture flow explicit in the template JSON",
            "provide direct programmer bindings from merchant input and captured files to the renderer",
        ],
        "visual_renderer_changed": False,
        "render_output_equivalent_to_v3": True,
        "capture_guide_changed": False,
        "previous_preview_releases_untouched": [
            "t1-special-menu-reference-v1-preview",
            "t1-special-menu-reference-v2-preview",
            "t1-special-menu-reference-v3-preview",
        ],
    }
    result["non_destructive_contract"]["previous_preview_releases_untouched"] = [
        "t1-special-menu-reference-v1-preview",
        "t1-special-menu-reference-v2-preview",
        "t1-special-menu-reference-v3-preview",
    ]
    result["scene_capture_contract"]["stable_ui_screen_count"] = 12
    result["scene_capture_contract"]["stable_ui_screen_formula"] = "4 scenes x 3 states (A guide, B recording, C review)"
    result["scene_capture_contract"]["implementation_handoff_pointer"] = "#/implementation_handoff"

    fields = v3["merchant_input_contract"]["fields"]
    properties: dict[str, Any] = {}
    required: list[str] = []
    for field in fields:
        item = {"type": "string", "maxLength": field["max_chars"], "render_targets": field["uses"]}
        if field["id"] == "prix":
            item["normalization"] = "format as grouped integer and append FCFA only when absent"
        if field["id"] == "accroche":
            item["empty_behavior"] = "omit G03_HOOK; never invent copy"
        properties[field["id"]] = item
        if field["required"]:
            required.append(field["id"])

    screens: list[dict[str, Any]] = []
    for index, scene in enumerate(v3["scene_capture_contract"]["scenes"]):
        screens.extend(_screen_triplet(scene, index, guide))

    capture_properties = {
        scene["id"]: {
            "type": "object",
            "required": ["uri", "duration_ms", "has_audio"],
            "additionalProperties": False,
            "properties": {
                "uri": {"type": "string", "format": "uri", "must_be_app_readable": True},
                "duration_ms": {"const": int(scene["duration_s"] * 1000)},
                "has_audio": {"const": True},
                "rotation_metadata_applied": {"const": True},
            },
        }
        for scene in v3["scene_capture_contract"]["scenes"]
    }

    result["implementation_handoff"] = {
        "contract_type": "runtime_template_integration_contract",
        "not_a_mockup": True,
        "purpose": "single JSON handoff for merchant data, the 12 capture screens, four media slots and the deterministic renderer",
        "binding_syntax": "RFC 6901 pointer for files; runtime.* for values produced by the application",
        "sources": {
            "visual_template": {
                "path": "config/T1_special_menu_reference_v3.json",
                "role": "locked rendering behavior",
            },
            "capture_copy": {
                "path": "capture-guide/consignes_T1.json",
                "sha256": _sha256(GUIDE_PATH),
                "must_remain_byte_identical": True,
            },
            "visual_proof_only": {
                "path": "ui-screens/planche_12_etats.png",
                "runtime_source": False,
                "note": "The PNG verifies the contract visually; production code consumes this JSON, not the PNG or HTML simulation.",
            },
        },
        "counts": {
            "merchant_fields": 6,
            "required_merchant_fields": 5,
            "optional_merchant_fields": 1,
            "capture_scenes": 4,
            "stable_capture_screens": 12,
            "stable_states_per_scene": 3,
            "captured_video_files": 4,
            "output_video_files": 1,
        },
        "runtime_order": [
            {
                "step": 1,
                "id": "MERCHANT_INPUT",
                "consumes": "merchant form",
                "produces": "merchant_payload",
                "next": "T1_CAPTURE_S1_A_GUIDE",
            },
            {
                "step": 2,
                "id": "GUIDED_CAPTURE",
                "consumes": "camera + microphone",
                "produces": ["captures.S1", "captures.S2", "captures.S3", "captures.S4"],
                "stable_screens": 12,
                "next": "T1_MONTAGE_STATUS",
            },
            {
                "step": 3,
                "id": "DETERMINISTIC_RENDER",
                "consumes": ["merchant_payload", "captures.S1", "captures.S2", "captures.S3", "captures.S4", "this template JSON"],
                "produces": "output.publicity_uri",
                "next": "T1_AD_REVIEW",
            },
        ],
        "merchant_payload_schema": {
            "type": "object",
            "additionalProperties": False,
            "required": required,
            "optional": [field["id"] for field in fields if not field["required"]],
            "properties": properties,
        },
        "capture_payload_schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["S1", "S2", "S3", "S4"],
            "properties": capture_properties,
        },
        "state_definitions": {
            "A_GUIDE": {
                "owns_camera": False,
                "preview_camera": True,
                "shows_scene_copy": True,
                "records_media": False,
            },
            "B_RECORDING": {
                "owns_camera": True,
                "preview_camera": True,
                "shows_scene_copy": False,
                "records_media": True,
                "instruction_sheet_must_be_absent_from_first_recorded_frame": True,
            },
            "C_REVIEW": {
                "owns_camera": False,
                "preview_captured_media": True,
                "playback_audio": True,
                "records_media": False,
            },
        },
        "transient_states": [
            {
                "id": "COUNTDOWN_3_2_1",
                "counted_in_12_stable_screens": False,
                "sequence": [3, 2, 1],
                "trigger": "START_RECORDING",
                "then": "B_RECORDING",
                "must_not_be_written_into_capture": True,
            }
        ],
        "screens": screens,
        "navigation_rules": {
            "initial_screen_id": "T1_CAPTURE_S1_A_GUIDE",
            "back_from_review": "return to A_GUIDE for the same scene; never enter B_RECORDING directly",
            "retake": "delete only the current scene file and return to its A_GUIDE screen",
            "accept_s1_to_s3": "persist current capture and open next scene A_GUIDE",
            "accept_s4": "persist S4 and open T1_MONTAGE_STATUS",
            "process_death_recovery": "restore the last accepted capture slots; any incomplete B_RECORDING file is discarded",
        },
        "renderer_handoff": {
            "template_config": "config/T1_special_menu_reference_v3_1.json",
            "merchant_bindings": [
                {"source": f"merchant_payload.{field['id']}", "targets": [f"graphics.{target}" for target in field["uses"]]}
                for field in fields
            ],
            "capture_bindings": [
                {
                    "source": f"captures.{scene['id']}.uri",
                    "target": f"scene_capture_contract.scenes[{index}]",
                    "duration_ms": int(scene["duration_s"] * 1000),
                    "source_time_map": "identity",
                    "audio_time_map": "identity",
                }
                for index, scene in enumerate(v3["scene_capture_contract"]["scenes"])
            ],
            "job_example": {
                "template_id": result["id"],
                "merchant_payload": {field["id"]: f"${{merchant.{field['id']}}}" for field in fields},
                "captures": {
                    scene["id"]: {
                        "uri": f"${{captures.{scene['id']}.uri}}",
                        "duration_ms": int(scene["duration_s"] * 1000),
                        "has_audio": True,
                    }
                    for scene in v3["scene_capture_contract"]["scenes"]
                },
                "output": {"width": 720, "height": 1280, "fps": 30, "duration_ms": 30000, "container": "mp4"},
            },
            "runtime_invariants": [
                "validate merchant_payload before opening screen 1",
                "require all four accepted capture URIs before render",
                "preserve scene audio at 1.0x",
                "never generate subtitles",
                "render exactly 900 frames at 30 fps",
                "show CTA through frame 899",
            ],
        },
        "android_mapping": {
            "screen_model": "CaptureScreenModel(screenId, sceneId, state, resolvedText, visibleComponents, actions)",
            "session_model": "T1Session(merchantPayload, captures: Map<SceneId, CaptureAsset>, currentScreenId)",
            "events": ["START_RECORDING", "COUNTDOWN_COMPLETE", "CAPTURE_DURATION_REACHED", "RETAKE", "ACCEPT_CAPTURE"],
            "recommended_state_holder": "ViewModel + SavedStateHandle; persist accepted content URIs with takePersistableUriPermission when applicable",
            "renderer_entry_point": "submit RenderJob built from implementation_handoff.renderer_handoff.job_example",
        },
        "acceptance_gates": [
            "12 unique stable screen IDs in S1A,S1B,S1C ... S4A,S4B,S4C order",
            "all A-screen copy resolves byte-for-byte from capture-guide/consignes_T1.json",
            "all B screens hide the instruction sheet and stop automatically at the exact scene duration",
            "all C screens replay with sound and expose RETAKE plus the correct accept action",
            "only S4C routes to T1_MONTAGE_STATUS",
            "merchant schema exposes exactly the six universal fields and introduces no new required field",
            "visual render sections remain equal to V3",
        ],
    }
    return result


def main() -> None:
    OUT_PATH.write_text(json.dumps(build_contract(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT_PATH.relative_to(ROOT))


if __name__ == "__main__":
    main()
