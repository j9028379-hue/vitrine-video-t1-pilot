#!/usr/bin/env python3
"""Validate the complete T1 template-side package.

The validator is intentionally offline. It validates schemas, hashes, media,
state flow, the 2 GB profile and (when present) the approved golden MP4.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2
from jsonschema import Draft202012Validator

from tools.build_t1_template_package_v1 import (
    GOLDEN_PATH,
    MANIFEST_PATH,
    REFERENCE_OUTPUT,
    ROOT,
    extract_keyframe_metrics,
    sha256,
    video_metadata,
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def add(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any) -> None:
    checks.append({"name": name, "status": "PASS" if passed else "FAIL", "detail": detail})


def validate_schema(instance_path: Path, schema_path: Path, checks: list[dict[str, Any]]) -> None:
    schema = load(schema_path)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(load(instance_path)), key=lambda e: list(e.path))
    add(
        checks,
        f"schema:{instance_path.relative_to(ROOT)}",
        not errors,
        [f"{'/'.join(map(str, error.path))}: {error.message}" for error in errors[:20]],
    )


def validate_package(require_golden: bool) -> dict[str, Any]:
    manifest = load(MANIFEST_PATH)
    checks: list[dict[str, Any]] = []

    # 1. Every package artifact is immutable and checksummed.
    missing: list[str] = []
    mismatches: list[dict[str, Any]] = []
    for artifact in manifest["artifacts"]:
        path = ROOT / artifact["path"]
        if not path.is_file():
            if artifact["role"] == "golden_master" and not require_golden:
                continue
            if artifact["required"]:
                missing.append(artifact["path"])
            continue
        observed = {"bytes": path.stat().st_size, "sha256": sha256(path)}
        if observed["bytes"] != artifact["bytes"] or observed["sha256"] != artifact["sha256"]:
            mismatches.append({"path": artifact["path"], "expected": {"bytes": artifact["bytes"], "sha256": artifact["sha256"]}, "observed": observed})
    add(checks, "manifest_artifacts_present", not missing, missing)
    add(checks, "manifest_hashes_and_sizes", not mismatches, mismatches)

    # 2. Formal schemas are valid and all canonical examples conform.
    validate_schema(ROOT / "config" / "T1_special_menu_template_v1_0_0.json", ROOT / "schemas" / "T1_template_package.schema.json", checks)
    validate_schema(ROOT / "fixtures" / "t1-special-menu" / "render_job.valid.json", ROOT / "schemas" / "T1_render_job.schema.json", checks)
    validate_schema(ROOT / "fixtures" / "t1-special-menu" / "render_result.valid.json", ROOT / "schemas" / "T1_render_result.schema.json", checks)
    validate_schema(ROOT / "fixtures" / "t1-special-menu" / "render_error.unsupported_media.json", ROOT / "schemas" / "T1_render_error.schema.json", checks)

    template = load(ROOT / "config" / "T1_special_menu_template_v1_0_0.json")
    job = load(ROOT / "fixtures" / "t1-special-menu" / "render_job.valid.json")
    profile = load(ROOT / "profiles" / "T1_android_offline_2gb.json")
    golden = load(GOLDEN_PATH)

    # 3. Template semantic invariants.
    screens = template["implementation_handoff"]["screens"]
    expected_ids = [
        f"T1_CAPTURE_S{scene}_{state}_{label}"
        for scene in range(1, 5)
        for state, label in (("A", "GUIDE"), ("B", "RECORDING"), ("C", "REVIEW"))
    ]
    add(checks, "twelve_screen_order", [screen["screen_id"] for screen in screens] == expected_ids, [screen["screen_id"] for screen in screens])
    field_ids = [field["id"] for field in template["merchant_input_contract"]["fields"]]
    add(checks, "six_universal_fields", field_ids == ["nom", "produit", "prix", "whatsapp", "quartier", "accroche"], field_ids)
    scenes = template["scene_capture_contract"]["scenes"]
    scene_shape = [(scene["id"], scene["frames"], scene["duration_s"]) for scene in scenes]
    add(checks, "four_scene_timing", scene_shape == [("S1", 180, 6.0), ("S2", 240, 8.0), ("S3", 210, 7.0), ("S4", 270, 9.0)], scene_shape)
    add(checks, "audio_phase", template["audio_policy"] == {
        "phase": "deferred_after_silent_template_freeze",
        "merchant_voice_timeline": "reserved_identity_1_0x",
        "music": "deferred; future curated catalogue target 20 to 30 models",
        "sfx": "none; approved reference contains no SFX grammar",
        "automatic_subtitles": False,
    }, template["audio_policy"])

    # 4. The low-end profile is genuinely local and bounded.
    low_end_ok = (
        profile["device_floor"]["ram_mb"] == 2048
        and profile["network_policy"]["render_server"] is False
        and profile["network_policy"]["network_required_for_render"] is False
        and profile["engine_policy"]["decoder_count"] == 1
        and profile["engine_policy"]["bundled_ffmpeg_required"] is False
        and profile["resource_budgets"]["peak_managed_plus_native_memory_hard_limit_mb"] <= 256
        and profile["resource_budgets"]["render_concurrency"] == 1
    )
    add(checks, "offline_2gb_profile", low_end_ok, {
        "ram_mb": profile["device_floor"]["ram_mb"],
        "server": profile["network_policy"]["render_server"],
        "decoder_count": profile["engine_policy"]["decoder_count"],
        "memory_hard_limit_mb": profile["resource_budgets"]["peak_managed_plus_native_memory_hard_limit_mb"],
        "ffmpeg_required": profile["engine_policy"]["bundled_ffmpeg_required"],
    })

    # 5. Every capture fixture satisfies the exact media/frame contract.
    media_failures: list[dict[str, Any]] = []
    for scene_id, capture in job["captures"].items():
        path = ROOT / capture["uri"]
        observed = video_metadata(path)
        contract = template["media_ingest_contract"]["scene_frame_contract"][scene_id]
        if not (
            observed["width"] == capture["width"]
            and observed["height"] == capture["height"]
            and abs(observed["fps"] - 30.0) < 0.001
            and observed["frames"] in contract["accepted_input_frames"]
            and observed["duration_ms"] <= contract["maximum_duration_ms"]
            and sha256(path) == capture["sha256"]
            and (ROOT / capture["audio_uri"]).is_file()
        ):
            media_failures.append({"scene": scene_id, "declared": capture, "observed": observed})
    add(checks, "capture_media_contract", not media_failures, media_failures)

    # 6. Golden master is exact for the reference backend; portable ports use tolerances.
    if REFERENCE_OUTPUT.is_file():
        meta = video_metadata(REFERENCE_OUTPUT)
        exact = (
            sha256(REFERENCE_OUTPUT) == golden["reference_output"]["sha256"]
            and REFERENCE_OUTPUT.stat().st_size == golden["reference_output"]["bytes"]
            and meta["width"] == 720
            and meta["height"] == 1280
            and abs(meta["fps"] - 30.0) < 0.001
            and meta["frames"] == 900
            and meta["duration_ms"] == 30000
        )
        add(checks, "golden_master", exact, {"sha256": sha256(REFERENCE_OUTPUT), "bytes": REFERENCE_OUTPUT.stat().st_size, "decoded": meta})
        expected_indices = [item["frame"] for item in golden["keyframes"]]
        observed_keys = extract_keyframe_metrics(REFERENCE_OUTPUT, expected_indices)
        key_ok = all(
            observed["decoded_bgr_sha256_reference_backend"] == expected["decoded_bgr_sha256_reference_backend"]
            and observed["dhash64"] == expected["dhash64"]
            for observed, expected in zip(observed_keys, golden["keyframes"])
        )
        add(checks, "golden_keyframes", key_ok, {"frames": expected_indices, "count": len(expected_indices)})
    else:
        add(checks, "golden_master", not require_golden, "external golden MP4 absent; use the stable release bundle")

    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    return {
        "status": status,
        "package_id": manifest["package_id"],
        "template_id": manifest["template_id"],
        "template_version": manifest["template_version"],
        "offline": True,
        "target_ram_mb": 2048,
        "checks_passed": sum(check["status"] == "PASS" for check in checks),
        "checks_total": len(checks),
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--report", type=Path, default=ROOT / "reports" / "T1_template_package_v1_validation.json")
    parser.add_argument("--require-golden", action="store_true")
    args = parser.parse_args()
    if args.manifest.resolve() != MANIFEST_PATH.resolve():
        raise SystemExit("This validator currently accepts the canonical T1 manifest only.")
    report = validate_package(args.require_golden)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
