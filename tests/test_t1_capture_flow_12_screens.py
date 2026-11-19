"""Contrat d'intégration des 12 écrans T1 (4 scènes × A/B/C)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.build_t1_capture_flow_v3_1 import build_contract

ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "config" / "T1_special_menu_reference_v3.json"
V31 = ROOT / "config" / "T1_special_menu_reference_v3_1.json"
GUIDE = ROOT / "capture-guide" / "consignes_T1.json"
GUIDE_SHA256 = "93a807f88e0e0f909cb589e8539419a4d1c387c12bc1b9966ba7dbe1a936075c"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def handoff() -> dict:
    return load(V31)["implementation_handoff"]


def test_committed_v31_is_reproducible_from_locked_sources() -> None:
    assert load(V31) == build_contract()
    assert hashlib.sha256(GUIDE.read_bytes()).hexdigest() == GUIDE_SHA256


def test_exactly_twelve_stable_screens_in_scene_state_order() -> None:
    screens = handoff()["screens"]
    expected = [
        f"T1_CAPTURE_S{scene}_{state}_{name}"
        for scene in range(1, 5)
        for state, name in (("A", "GUIDE"), ("B", "RECORDING"), ("C", "REVIEW"))
    ]
    assert len(screens) == 12
    assert [screen["ordinal"] for screen in screens] == list(range(1, 13))
    assert [screen["screen_id"] for screen in screens] == expected
    assert len({screen["screen_id"] for screen in screens}) == 12
    assert handoff()["counts"]["stable_capture_screens"] == 12


def test_every_guide_screen_resolves_exact_locked_copy() -> None:
    guide = load(GUIDE)
    screens = handoff()["screens"]
    for index, scene in enumerate(guide["scenes"]):
        screen = screens[index * 3]
        text = screen["resolved_text"]
        assert screen["state"] == "A_GUIDE"
        assert text["scene_counter"] == f"SCÈNE {index + 1}/4"
        assert text["duration"] == f"{scene['secondes']} secondes"
        assert text["title"] == scene["titre"]
        assert text["instruction"] == scene["consigne"]
        assert text["film_list"] == scene["a_filmer"]
        assert text["avoid_list"] == scene["a_eviter"]
        assert text["voice_note"] == guide["mention_voix_commune"]
        assert text["example"] == scene["exemple"]
        assert text["primary_action"] == guide["bouton_principal"] == "COMMENCER À FILMER"


def test_recording_screens_are_clean_exact_and_voice_safe() -> None:
    expected_ms = [6000, 8000, 7000, 9000]
    screens = handoff()["screens"]
    for index, duration_ms in enumerate(expected_ms):
        screen = screens[index * 3 + 1]
        assert screen["state"] == "B_RECORDING"
        assert screen["visible_components"] == ["camera_preview", "recording_timer", "recording_progress"]
        assert "instruction_sheet" in screen["forbidden_components"]
        assert "merchant_fields" in screen["forbidden_components"]
        assert "subtitles" in screen["forbidden_components"]
        assert screen["capture"]["duration_ms"] == duration_ms
        assert screen["capture"]["auto_stop"] is True
        assert screen["capture"]["manual_stop"] is False
        assert screen["capture"]["microphone_audio"] is True
        assert screen["capture"]["source_speed"] == 1.0


def test_review_screens_retake_same_scene_and_accept_in_order() -> None:
    screens = handoff()["screens"]
    for index in range(4):
        review = screens[index * 3 + 2]
        actions = {action["event"]: action for action in review["actions"]}
        assert review["state"] == "C_REVIEW"
        assert review["playback"] == {"audio": True, "loop": True, "source_speed": 1.0}
        assert actions["RETAKE"]["next_screen_id"] == f"T1_CAPTURE_S{index + 1}_A_GUIDE"
        if index < 3:
            assert actions["ACCEPT_CAPTURE"]["label"] == "SCÈNE SUIVANTE"
            assert actions["ACCEPT_CAPTURE"]["next_screen_id"] == f"T1_CAPTURE_S{index + 2}_A_GUIDE"
        else:
            assert actions["ACCEPT_CAPTURE"]["label"] == "VOIR MON MONTAGE"
            assert actions["ACCEPT_CAPTURE"]["next_screen_id"] == "T1_MONTAGE_STATUS"


def test_countdown_is_transient_and_not_a_thirteenth_screen() -> None:
    transient = handoff()["transient_states"]
    assert transient == [{
        "id": "COUNTDOWN_3_2_1",
        "counted_in_12_stable_screens": False,
        "sequence": [3, 2, 1],
        "trigger": "START_RECORDING",
        "then": "B_RECORDING",
        "must_not_be_written_into_capture": True,
    }]
    assert len(handoff()["screens"]) == 12


def test_six_universal_merchant_fields_feed_the_renderer_directly() -> None:
    schema = handoff()["merchant_payload_schema"]
    assert list(schema["properties"]) == ["nom", "produit", "prix", "whatsapp", "quartier", "accroche"]
    assert schema["required"] == ["nom", "produit", "prix", "whatsapp", "quartier"]
    assert schema["optional"] == ["accroche"]
    assert schema["additionalProperties"] is False
    bindings = handoff()["renderer_handoff"]["merchant_bindings"]
    assert [item["source"] for item in bindings] == [
        "merchant_payload.nom",
        "merchant_payload.produit",
        "merchant_payload.prix",
        "merchant_payload.whatsapp",
        "merchant_payload.quartier",
        "merchant_payload.accroche",
    ]


def test_four_capture_slots_have_exact_durations_and_identity_maps() -> None:
    schema = handoff()["capture_payload_schema"]
    assert schema["required"] == ["S1", "S2", "S3", "S4"]
    assert [schema["properties"][scene]["properties"]["duration_ms"]["const"] for scene in schema["required"]] == [6000, 8000, 7000, 9000]
    bindings = handoff()["renderer_handoff"]["capture_bindings"]
    assert [item["duration_ms"] for item in bindings] == [6000, 8000, 7000, 9000]
    assert all(item["source_time_map"] == "identity" for item in bindings)
    assert all(item["audio_time_map"] == "identity" for item in bindings)


def test_each_screen_has_a_real_visual_proof_file() -> None:
    for screen in handoff()["screens"]:
        proof = ROOT / screen["proof_png"]
        assert proof.is_file(), proof
        assert proof.stat().st_size > 100_000


def test_v31_changes_integration_metadata_not_v3_visual_rendering() -> None:
    v3 = load(V3)
    v31 = load(V31)
    immutable_render_keys = [
        "canvas",
        "cadence",
        "merchant_input_contract",
        "fonts",
        "look_pipeline",
        "edit_timeline",
        "speech_continuity",
        "graphics",
        "fallbacks",
        "android_media3_contract",
        "price_format",
        "impact_transition_system",
        "premium_transition_choreography",
        "end_lockup_consistency",
    ]
    for key in immutable_render_keys:
        assert v31[key] == v3[key], key
    assert v31["scene_capture_contract"]["scenes"] == v3["scene_capture_contract"]["scenes"]
    assert v31["revision"]["visual_renderer_changed"] is False
    assert v31["revision"]["render_output_equivalent_to_v3"] is True
