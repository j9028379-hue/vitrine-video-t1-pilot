"""Final template-side contract for T1 before music calibration."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from engine.special_menu_style import report_path
from tools.build_t1_template_package_v1 import (
    GOLDEN_PATH,
    MANIFEST_PATH,
    OUT_CONFIG,
    ROOT,
    build_error_fixture,
    build_golden,
    build_manifest,
    build_render_job,
    build_result_fixture,
    build_template,
    sha256,
    video_metadata,
)
from tools.validate_t1_template_package import validate_package


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(instance: str, schema: str) -> None:
    validator = Draft202012Validator(load(ROOT / schema))
    errors = sorted(validator.iter_errors(load(ROOT / instance)), key=lambda e: list(e.path))
    assert not errors, [error.message for error in errors]


def test_canonical_files_are_reproducible() -> None:
    assert load(OUT_CONFIG) == build_template()
    assert load(ROOT / "fixtures/t1-special-menu/render_job.valid.json") == build_render_job()
    assert load(ROOT / "fixtures/t1-special-menu/render_result.valid.json") == build_result_fixture()
    assert load(ROOT / "fixtures/t1-special-menu/render_error.unsupported_media.json") == build_error_fixture()
    assert load(GOLDEN_PATH) == build_golden()
    assert load(MANIFEST_PATH) == build_manifest()


def test_all_four_formal_schemas_accept_canonical_documents() -> None:
    validate("config/T1_special_menu_template_v1_0_0.json", "schemas/T1_template_package.schema.json")
    validate("fixtures/t1-special-menu/render_job.valid.json", "schemas/T1_render_job.schema.json")
    validate("fixtures/t1-special-menu/render_result.valid.json", "schemas/T1_render_result.schema.json")
    validate("fixtures/t1-special-menu/render_error.unsupported_media.json", "schemas/T1_render_error.schema.json")


def test_visual_recipe_is_byte_semantically_equal_to_approved_v31() -> None:
    base = load(ROOT / "config/T1_special_menu_reference_v3_1.json")
    final = load(OUT_CONFIG)
    keys = [
        "canvas",
        "cadence",
        "merchant_input_contract",
        "fonts",
        "look_pipeline",
        "edit_timeline",
        "speech_continuity",
        "graphics",
        "fallbacks",
        "price_format",
        "impact_transition_system",
        "premium_transition_choreography",
        "end_lockup_consistency",
    ]
    for key in keys:
        assert final[key] == base[key], key
    assert final["scene_capture_contract"]["scenes"] == base["scene_capture_contract"]["scenes"]
    assert final["revision"]["visual_renderer_changed"] is False


def test_exact_capture_and_merchant_shape_remains_locked() -> None:
    template = load(OUT_CONFIG)
    assert [field["id"] for field in template["merchant_input_contract"]["fields"]] == [
        "nom", "produit", "prix", "whatsapp", "quartier", "accroche"
    ]
    assert [(scene["id"], scene["frames"], scene["duration_s"]) for scene in template["scene_capture_contract"]["scenes"]] == [
        ("S1", 180, 6.0), ("S2", 240, 8.0), ("S3", 210, 7.0), ("S4", 270, 9.0)
    ]
    assert len(template["implementation_handoff"]["screens"]) == 12


def test_media_contract_is_exact_and_never_retimes() -> None:
    contract = load(OUT_CONFIG)["media_ingest_contract"]
    assert contract["accepted_container"] == ["mp4"]
    assert contract["accepted_video_mime"] == ["video/avc"]
    assert contract["fps"] == {
        "required": 30,
        "tolerance": 0,
        "variable_frame_rate": False,
        "conversion": "reject instead of silently dropping or duplicating speech frames",
    }
    assert contract["normalization"]["retiming"] is False
    assert contract["normalization"]["frame_interpolation"] is False
    assert contract["normalization"]["frame_blending"] is False
    assert [contract["scene_frame_contract"][scene]["required_frames"] for scene in ("S1", "S2", "S3", "S4")] == [180, 240, 210, 270]
    assert all(contract["scene_frame_contract"][scene]["tail_trim_frames_max"] == 1 for scene in contract["scene_frame_contract"])


def test_low_end_profile_is_offline_bounded_and_media3_first() -> None:
    profile = load(ROOT / "profiles/T1_android_offline_2gb.json")
    assert profile["device_floor"]["ram_mb"] == 2048
    assert profile["network_policy"] == {
        "render_server": False,
        "network_required_for_capture": False,
        "network_required_for_render": False,
        "network_required_for_export": False,
        "all_runtime_assets_bundled": True,
    }
    assert profile["engine_policy"]["decoder_count"] == 1
    assert profile["engine_policy"]["encoder_count"] == 1
    assert profile["engine_policy"]["bundled_ffmpeg_required"] is False
    assert "Media3" in profile["engine_policy"]["preferred_android_backend"]
    assert profile["resource_budgets"]["peak_managed_plus_native_memory_hard_limit_mb"] == 256
    assert profile["resource_budgets"]["render_concurrency"] == 1


def test_low_end_degradation_never_changes_story_or_commercial_lockup() -> None:
    profile = load(ROOT / "profiles/T1_android_offline_2gb.json")
    rules = " ".join(profile["effect_tiers"]["LOW_END_2GB"]["rules"])
    assert "keep every cut" in rules
    assert "never degrade face safety" in rules
    invariants = profile["non_degradable_invariants"]
    assert "900 output frames at 30 fps" in invariants
    assert "price remains on one line" in invariants
    assert "CTA remains fully visible through frame 899" in invariants


def test_audio_is_explicitly_deferred_and_sfx_are_none() -> None:
    audio = load(OUT_CONFIG)["audio_policy"]
    assert audio["phase"] == "deferred_after_silent_template_freeze"
    assert audio["merchant_voice_timeline"] == "reserved_identity_1_0x"
    assert "20 to 30" in audio["music"]
    assert audio["sfx"] == "none; approved reference contains no SFX grammar"
    assert audio["automatic_subtitles"] is False


def test_render_protocol_is_local_typed_and_idempotent() -> None:
    protocol = load(OUT_CONFIG)["render_protocol"]
    assert protocol["remote_server_required"] is False
    assert protocol["idempotent"] is True
    assert protocol["progress_states"] == [
        "VALIDATING", "ANALYZING", "RENDERING", "ENCODING", "FINALIZING", "COMPLETED"
    ]
    job = load(ROOT / "fixtures/t1-special-menu/render_job.valid.json")
    assert job["network_policy"] == "offline_only"
    assert job["output"]["frames"] == 900


def test_error_catalog_matches_formal_error_schema() -> None:
    template_codes = {item["code"] for item in load(OUT_CONFIG)["error_catalog"]}
    schema_codes = set(load(ROOT / "schemas/T1_render_error.schema.json")["properties"]["code"]["enum"])
    assert template_codes == schema_codes
    assert len(template_codes) == 14


def test_capture_fixtures_match_declared_job_and_one_frame_tail_rule() -> None:
    job = load(ROOT / "fixtures/t1-special-menu/render_job.valid.json")
    required = {"S1": 180, "S2": 240, "S3": 210, "S4": 270}
    for scene, capture in job["captures"].items():
        path = ROOT / capture["uri"]
        observed = video_metadata(path)
        assert observed["fps"] == 30.0
        assert observed["frames"] in {required[scene], required[scene] + 1}
        assert observed["frames"] == capture["frame_count"]
        assert sha256(path) == capture["sha256"]
        assert (ROOT / capture["audio_uri"]).is_file()


def test_golden_master_and_keyframes_are_locked() -> None:
    golden = load(GOLDEN_PATH)
    assert golden["reference_output"]["sha256"] == "784bd77591508995822237bf8633d6ec50d245cac39afdca91f9b130296c50c7"
    assert golden["reference_output"]["bytes"] == 20276905
    assert [item["frame"] for item in golden["keyframes"]] == [0, 45, 179, 180, 419, 420, 629, 630, 809, 810, 817, 899]
    assert all(len(item["decoded_bgr_sha256_reference_backend"]) == 64 for item in golden["keyframes"])
    assert golden["semantic_checks"]["cta_full_opacity_frame"] == 899


def test_manifest_covers_required_package_and_every_hash_matches() -> None:
    manifest = load(MANIFEST_PATH)
    roles = {item["role"] for item in manifest["artifacts"]}
    assert {
        "canonical_template",
        "template_schema",
        "render_job_schema",
        "render_result_schema",
        "render_error_schema",
        "required_low_end_profile",
        "golden_conformance_manifest",
        "golden_master",
        "package_validator",
    }.issubset(roles)
    for item in manifest["artifacts"]:
        path = ROOT / item["path"]
        assert path.is_file(), path
        assert path.stat().st_size == item["bytes"]
        assert sha256(path) == item["sha256"]


def test_reference_cli_accepts_caller_owned_paths_outside_the_repository(tmp_path: Path) -> None:
    outside = tmp_path / "merchant-output.mp4"
    assert report_path(outside) == str(outside.resolve())
    assert report_path(ROOT / "demo/T1_demo_input.json") == "demo/T1_demo_input.json"


def test_complete_package_validator_passes() -> None:
    report = validate_package(require_golden=True)
    assert report["status"] == "PASS"
    assert report["checks_passed"] == report["checks_total"] == 14
