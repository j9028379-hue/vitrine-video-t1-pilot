"""Contract tests for the approved T1-A Special Menu adaptation.

These tests protect the four-scene capture flow and distinguish observed facts
about the reference from product adaptations.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "T1_special_menu_reference_v1.json"
REFERENCE_PATH = ROOT / "references" / "t1-special-menu" / "reference_decompilation_v1.json"
V12_PATH = ROOT / "specs" / "T1_ENGINEERING_SPEC_V1_2.json"
CAPTURE_PATH = ROOT / "capture-guide" / "consignes_T1.json"
CAPTURE_SHA256_AT_BASE = "93a807f88e0e0f909cb589e8539419a4d1c387c12bc1b9966ba7dbe1a936075c"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_reference_forensics_are_exact() -> None:
    ref = load(REFERENCE_PATH)
    assert ref["reference"]["tiktok_video_id"] == "7525857155178712376"
    assert ref["reference"]["analyzed_copy"] == {
        "width": 576,
        "height": 1024,
        "fps": 30.0,
        "frames": 570,
        "duration_s": 19.0,
        "sha256": "2e73cd3192e1b5b347703d87cf06956d549343ba76127c192f9cf533592a2d1d",
        "bytes": 1965092,
        "storage_policy": "not_committed_third_party_media",
        "reason": "Le MP4 tiers reste hors du dépôt; seules les mesures, le hash et l'architecture dérivée sont versionnés.",
    }
    assert ref["video_structure"]["hard_cut_frames"] == [51, 113, 176, 240, 303, 366, 430, 492]
    assert ref["video_structure"]["outro_fade"] == {
        "start_f": 562,
        "end_f_exclusive": 570,
        "duration_f": 8,
        "duration_s": 0.2667,
        "target": "black",
    }
    assert len(ref["observed_shots"]) == 9
    assert sum(shot["duration_f"] for shot in ref["observed_shots"]) == 562


def test_canvas_and_four_scene_contract() -> None:
    cfg = load(CONFIG_PATH)
    assert cfg["canvas"] == {
        "width": 720,
        "height": 1280,
        "fps": 30,
        "frames": 900,
        "duration_s": 30.0,
        "frame_interval_ms": 33.333333,
    }
    scenes = cfg["scene_capture_contract"]["scenes"]
    assert [(s["id"], s["start_f"], s["end_f_exclusive"], s["frames"]) for s in scenes] == [
        ("S1", 0, 180, 180),
        ("S2", 180, 420, 240),
        ("S3", 420, 630, 210),
        ("S4", 630, 900, 270),
    ]
    assert cfg["scene_capture_contract"]["source"] == "capture-guide/consignes_T1.json"
    assert cfg["scene_capture_contract"]["voice_allowed_all_scenes"] is True
    assert cfg["scene_capture_contract"]["speech_subtitles"] is False


def test_capture_guide_is_byte_identical_to_locked_base() -> None:
    assert sha256(CAPTURE_PATH) == CAPTURE_SHA256_AT_BASE
    assert load(CONFIG_PATH)["non_destructive_contract"]["capture_guide_unchanged"] is True


def test_shots_cover_output_once_and_sources_are_contiguous() -> None:
    cfg = load(CONFIG_PATH)
    shots = cfg["edit_timeline"]["shots"]
    assert len(shots) == 14
    assert shots[0]["out_start_f"] == 0
    assert shots[-1]["out_end_f_exclusive"] == 900
    for previous, current in zip(shots, shots[1:]):
        assert previous["out_end_f_exclusive"] == current["out_start_f"]
    for shot in shots:
        assert shot["out_frames"] == shot["out_end_f_exclusive"] - shot["out_start_f"]
        assert shot["source_frames"] == shot["source_out_f_exclusive"] - shot["source_in_f"]
        assert shot["source_frames"] == shot["out_frames"]
        assert shot["source_speed"] == 1.0
        assert shot["source_contiguous"] is True
        assert shot["lip_sync_safe"] is True
        assert shot["transition_in"] in {"none", "hard_cut"}

    by_scene: dict[str, list[dict]] = {}
    for shot in shots:
        by_scene.setdefault(shot["scene"], []).append(shot)
    expected_end = {"S1": 180, "S2": 240, "S3": 210, "S4": 270}
    for scene, scene_shots in by_scene.items():
        assert scene_shots[0]["source_in_f"] == 0
        for previous, current in zip(scene_shots, scene_shots[1:]):
            assert previous["source_out_f_exclusive"] == current["source_in_f"]
        assert scene_shots[-1]["source_out_f_exclusive"] == expected_end[scene]


def test_reference_transition_grammar_is_preserved_at_120_bpm() -> None:
    cfg = load(CONFIG_PATH)
    cadence = cfg["cadence"]
    assert cadence["bpm"] == 120
    assert cadence["beat_frames"] == 15
    assert cadence["four_beat_phrase_frames"] == 60
    timeline = cfg["edit_timeline"]
    assert timeline["crossfades"] == []
    assert timeline["wipes"] == []
    assert timeline["glitches"] == []
    assert timeline["speed_ramps"] == []
    assert timeline["freeze_frames"] == []
    assert timeline["hard_cut_frames"] == [60, 120, 180, 240, 300, 360, 420, 480, 540, 630, 690, 750, 810]


def test_speech_and_face_scene_are_protected() -> None:
    cfg = load(CONFIG_PATH)
    s3 = [shot for shot in cfg["edit_timeline"]["shots"] if shot["scene"] == "S3"]
    assert [(s["source_in_f"], s["source_out_f_exclusive"]) for s in s3] == [(0, 60), (60, 120), (120, 210)]
    graphics = cfg["graphics"]
    for graphic in graphics:
        assert graphic["end_f_exclusive"] <= 420 or graphic["start_f"] >= 630
    assert cfg["speech_continuity"]["S3_face_rule"].startswith("no source-frame drop")


def test_merchant_fields_are_unchanged() -> None:
    cfg = load(CONFIG_PATH)
    v12 = load(V12_PATH)
    old_fields = [(x["id"], x["obligatoire"], x["max"]) for x in v12["data_contract"]["champs"]]
    new_fields = [(x["id"], x["required"], x["max_chars"]) for x in cfg["merchant_input_contract"]["fields"]]
    assert new_fields == old_fields
    assert cfg["merchant_input_contract"]["new_required_fields"] == 0


def test_fonts_are_bundled_and_locked() -> None:
    cfg = load(CONFIG_PATH)
    for font in cfg["fonts"].values():
        if not isinstance(font, dict) or "file" not in font:
            continue
        path = ROOT / font["file"]
        assert path.is_file()
    display = cfg["fonts"]["display_serif"]
    assert sha256(ROOT / display["file"]) == display["sha256"]
    assert display["family"] == "DM Serif Display"
    assert cfg["fonts"]["light_sans"]["family"] == "Montserrat"


def test_optional_hook_and_final_cta_rules() -> None:
    cfg = load(CONFIG_PATH)
    graphics = {g["id"]: g for g in cfg["graphics"]}
    assert graphics["G03_HOOK"]["optional"] is True
    assert graphics["G03_HOOK"]["empty_behavior"] == "omit"
    cta = graphics["G05_CTA"]
    assert cta["end_f_exclusive"] == 900
    assert cta["animation"]["hold_full_opacity_through_f"] == 899
    assert cta["background_outro"]["start_f"] == 892
    assert cta["background_outro"]["fade_to_black_alpha"] < 1.0
