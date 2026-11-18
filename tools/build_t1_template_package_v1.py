#!/usr/bin/env python3
"""Build the canonical, offline T1 template package and an optional bundle.

This is the final silent/capture/assembly contract. It reuses the approved V3
visual recipe without duplicating or altering the visual output. Music is a
future profile; the approved reference has no SFX grammar.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import zipfile
from typing import Any

import cv2

ROOT = Path(__file__).resolve().parents[1]
BASE_CONFIG = ROOT / "config" / "T1_special_menu_reference_v3_1.json"
OUT_CONFIG = ROOT / "config" / "T1_special_menu_template_v1_0_0.json"
GOLDEN_PATH = ROOT / "conformance" / "T1_special_menu_golden_v1.json"
MANIFEST_PATH = ROOT / "packages" / "t1-special-menu-v1" / "manifest.json"
FIXTURE_DIR = ROOT / "fixtures" / "t1-special-menu"
REFERENCE_OUTPUT = ROOT / "output" / "output_T1_special_menu_reference_v3.mp4"
REFERENCE_OUTPUT_SHA256 = "784bd77591508995822237bf8633d6ec50d245cac39afdca91f9b130296c50c7"
REFERENCE_OUTPUT_BYTES = 20276905
PACKAGE_PREFIX = "T1_special_menu_template_v1_0_0"

SCENE_EXPECTATIONS = {
    "S1": {"frames": 180, "duration_ms": 6000, "media": "simulation/media/S1.mp4", "voice": "simulation/media/voix1.mp3"},
    "S2": {"frames": 240, "duration_ms": 8000, "media": "simulation/media/S2.mp4", "voice": "simulation/media/voix2.mp3"},
    "S3": {"frames": 210, "duration_ms": 7000, "media": "simulation/media/S3.mp4", "voice": "simulation/media/voix3.mp3"},
    "S4": {"frames": 270, "duration_ms": 9000, "media": "simulation/media/S4.mp4", "voice": "simulation/media/voix4.mp3"},
}

ERRORS = [
    ("T1_INVALID_TEMPLATE_PACKAGE", False, "manifest, schema or template contract is invalid"),
    ("T1_INVALID_MERCHANT_PAYLOAD", False, "one of the six universal fields violates its contract"),
    ("T1_MISSING_CAPTURE", True, "one of S1 to S4 is absent"),
    ("T1_UNSUPPORTED_MEDIA", True, "container, codec, dimensions, frame rate or orientation is unsupported"),
    ("T1_CAPTURE_DURATION_OUT_OF_RANGE", True, "scene duration is shorter than required or exceeds the one-frame tail tolerance"),
    ("T1_CAPTURE_AUDIO_MISSING", True, "merchant voice track is missing from an accepted capture"),
    ("T1_CAPTURE_CORRUPT", True, "a capture cannot be decoded from first through required last frame"),
    ("T1_INSUFFICIENT_STORAGE", True, "less than the profile minimum free storage is available"),
    ("T1_UNSUPPORTED_DEVICE", False, "the device cannot provide hardware AVC decode, encode or GLES 3.0"),
    ("T1_ASSET_CHECKSUM_MISMATCH", False, "a bundled font, configuration or proof asset does not match the manifest"),
    ("T1_FONT_LOAD_FAILED", False, "one of the exact bundled fonts cannot be loaded"),
    ("T1_RENDER_CANCELLED", True, "the local user or host application cancelled the render"),
    ("T1_RENDER_FAILED", True, "the local render backend failed before producing a valid MP4"),
    ("T1_OUTPUT_VALIDATION_FAILED", True, "the output is not 720x1280, 30 fps, 900 frames, 30 seconds or visually conformant"),
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def video_metadata(path: Path) -> dict[str, Any]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {path}")
    width = int(round(cap.get(cv2.CAP_PROP_FRAME_WIDTH)))
    height = int(round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    frames = int(round(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    cap.release()
    if fps <= 0:
        raise RuntimeError(f"Invalid FPS: {path}")
    return {
        "width": width,
        "height": height,
        "fps": round(fps, 6),
        "frames": frames,
        "duration_ms": int(round(frames * 1000.0 / fps)),
    }


def dhash64(frame: Any) -> str:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    tiny = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
    bits = tiny[:, 1:] > tiny[:, :-1]
    value = 0
    for bit in bits.flatten():
        value = (value << 1) | int(bit)
    return f"{value:016x}"


def extract_keyframe_metrics(path: Path, indices: list[int]) -> list[dict[str, Any]]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open golden output: {path}")
    result: list[dict[str, Any]] = []
    for index in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = cap.read()
        if not ok:
            raise RuntimeError(f"Cannot decode golden frame {index}")
        raw_hash = hashlib.sha256(frame.tobytes()).hexdigest()
        mean = frame.mean(axis=(0, 1))
        luma = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).mean()
        result.append({
            "frame": index,
            "time_ms": int(round(index * 1000 / 30)),
            "decoded_bgr_sha256_reference_backend": raw_hash,
            "dhash64": dhash64(frame),
            "mean_bgr": [round(float(x), 6) for x in mean],
            "mean_luma": round(float(luma), 6),
        })
    cap.release()
    return result


def build_template() -> dict[str, Any]:
    base = load_json(BASE_CONFIG)
    result = copy.deepcopy(base)
    # JSON Schema annotation must be the first serialized key for easy discovery.
    result = {"$schema": "../schemas/T1_template_package.schema.json", **result}
    result["schema_version"] = "2.0.0"
    result["template_version"] = "1.0.0"
    result["package_phase"] = "visual_capture_assembly_complete_audio_deferred"
    result["id"] = "restaurants_maquis_T1_special_menu_v1_0_0"
    result["display_name"] = "T1 — Special Menu — paquet de gabarit hors ligne v1.0.0"
    result["status"] = "stable_silent_template_contract"
    result["revision"] = {
        "from": base["id"],
        "visual_revision": "V3 approved",
        "requested_at": "2026-11-18",
        "purpose": "freeze a complete template-side handoff before music calibration",
        "visual_renderer_changed": False,
        "capture_flow_changed": False,
        "new_required_merchant_fields": 0,
        "adds": [
            "formal schemas",
            "exact media ingest contract",
            "offline 2 GB execution profile",
            "typed render protocol and errors",
            "golden conformance pack",
            "checksummed package manifest",
        ],
    }
    releases = result["non_destructive_contract"].setdefault("previous_preview_releases_untouched", [])
    for tag in (
        "t1-special-menu-reference-v1-preview",
        "t1-special-menu-reference-v2-preview",
        "t1-special-menu-reference-v3-preview",
        "t1-special-menu-reference-v3-1-integration-preview",
    ):
        if tag not in releases:
            releases.append(tag)

    result["implementation_handoff"]["renderer_handoff"]["template_config"] = "config/T1_special_menu_template_v1_0_0.json"
    result["implementation_handoff"]["renderer_handoff"]["job_example"] = {
        "$ref": "fixtures/t1-special-menu/render_job.valid.json",
        "schema": "schemas/T1_render_job.schema.json",
        "authoritative": True,
    }

    result["media_ingest_contract"] = {
        "policy": "validate_then_normalize_without_retiming",
        "accepted_container": ["mp4"],
        "accepted_video_mime": ["video/avc"],
        "accepted_video_codec": ["H.264 Baseline", "H.264 Main"],
        "dimensions": {
            "preferred": [720, 1280],
            "minimum": [540, 960],
            "maximum": [1080, 1920],
            "aspect_ratio": "portrait 9:16 after rotation normalization",
            "fit": "cover crop around each shot anchor; never letterbox",
        },
        "fps": {
            "required": 30,
            "tolerance": 0,
            "variable_frame_rate": False,
            "conversion": "reject instead of silently dropping or duplicating speech frames",
        },
        "rotation": {
            "accepted_metadata_degrees": [0, 90, 180, 270],
            "normalization": "apply once before shot transforms",
        },
        "color": {
            "accepted": ["BT.709 limited", "BT.709 full", "sRGB-tagged AVC"],
            "working_space": "sRGB float32 0..1",
            "hdr": "reject",
        },
        "audio": {
            "required_in_production_capture": True,
            "accepted_codec": ["AAC-LC"],
            "sample_rates_hz": [44100, 48000],
            "channels": [1, 2],
            "time_map": "identity",
            "music_mix_status": "deferred",
        },
        "scene_frame_contract": {
            scene: {
                "required_frames": item["frames"],
                "accepted_input_frames": [item["frames"], item["frames"] + 1],
                "required_duration_ms": item["duration_ms"],
                "maximum_duration_ms": item["duration_ms"] + 34,
                "tail_trim_frames_max": 1,
                "head_trim_frames": 0,
            }
            for scene, item in SCENE_EXPECTATIONS.items()
        },
        "normalization": {
            "decode_order": "sequential",
            "timeline": "use the first required N frames; trim at most one recorder tail frame",
            "retiming": False,
            "frame_interpolation": False,
            "frame_blending": False,
            "audio_resampling": "only sample-rate conversion between 44.1 and 48 kHz; never duration change",
        },
        "rejection_rules": [
            "reject a missing or unreadable scene",
            "reject fewer frames than required",
            "reject more than one extra trailing frame",
            "reject non-30-fps input",
            "reject unsupported codec, HDR or dimensions outside the contract",
            "reject production captures without merchant voice audio",
        ],
    }
    result["execution_contract"] = {
        "mode": "offline_on_device",
        "network_required": False,
        "preferred_profile": "T1_ANDROID_OFFLINE_2GB",
        "profile_path": "profiles/T1_android_offline_2gb.json",
        "preferred_backend": "AndroidX Media3 Transformer + MediaCodec + custom GlEffect",
        "ffmpeg_runtime_required": False,
    }
    result["render_protocol"] = {
        "job_schema": "schemas/T1_render_job.schema.json",
        "result_schema": "schemas/T1_render_result.schema.json",
        "error_schema": "schemas/T1_render_error.schema.json",
        "progress_states": ["VALIDATING", "ANALYZING", "RENDERING", "ENCODING", "FINALIZING", "COMPLETED"],
        "idempotent": True,
        "remote_server_required": False,
    }
    result["error_catalog"] = [
        {"code": code, "retryable": retryable, "meaning": meaning}
        for code, retryable, meaning in ERRORS
    ]
    result["conformance_contract"] = {
        "golden_manifest": "conformance/T1_special_menu_golden_v1.json",
        "valid_job_fixture": "fixtures/t1-special-menu/render_job.valid.json",
        "reference_output": "output/output_T1_special_menu_reference_v3.mp4",
        "reference_output_sha256": REFERENCE_OUTPUT_SHA256,
        "portable_visual_tolerance": {
            "minimum_keyframe_ssim": 0.93,
            "maximum_keyframe_mean_absolute_error_0_255": 9.0,
            "maximum_dhash_hamming_distance": 8,
            "timeline_and_text_geometry_tolerance_px_at_720": 2,
            "reference_backend_requires_exact_hash": True,
            "portable_backends_use_tolerance_not_binary_mp4_hash": True,
        },
    }
    result["audio_policy"] = {
        "phase": "deferred_after_silent_template_freeze",
        "merchant_voice_timeline": "reserved_identity_1_0x",
        "music": "deferred; future curated catalogue target 20 to 30 models",
        "sfx": "none; approved reference contains no SFX grammar",
        "automatic_subtitles": False,
    }
    package_gates = [
        "canonical template validates against T1_template_package.schema.json",
        "RenderJob, RenderResult and RenderError fixtures validate against their schemas",
        "all package artifacts match manifest SHA-256 values",
        "all four source clips match the media ingest contract",
        "offline 2 GB profile requires one decoder and no remote server",
        "golden output hash and 12 keyframe metrics are locked",
        "music remains deferred and SFX remains none",
    ]
    for gate in package_gates:
        if gate not in result["quality_gates"]:
            result["quality_gates"].append(gate)
    return result


def build_render_job() -> dict[str, Any]:
    demo = load_json(ROOT / "demo" / "T1_demo_input.json")
    captures: dict[str, Any] = {}
    for scene, expected in SCENE_EXPECTATIONS.items():
        media_path = ROOT / expected["media"]
        meta = video_metadata(media_path)
        captures[scene] = {
            "uri": expected["media"],
            "mime_type": "video/mp4",
            "video_codec": "H.264",
            "width": meta["width"],
            "height": meta["height"],
            "fps": int(round(meta["fps"])),
            "frame_count": meta["frames"],
            "duration_ms": meta["duration_ms"],
            "rotation_degrees": 0,
            "has_audio": True,
            "audio_codec": "fixture_external_voice_track",
            "audio_uri": expected["voice"],
            "sha256": sha256(media_path),
        }
    return {
        "schema_version": "1.0.0",
        "job_id": "t1-golden-0001",
        "idempotency_key": "t1-special-menu-golden-v1",
        "template_id": "restaurants_maquis_T1_special_menu_v1_0_0",
        "template_version": "1.0.0",
        "execution_profile": "T1_REFERENCE_PYTHON",
        "network_policy": "offline_only",
        "merchant_payload": {key: demo[key] for key in ("nom", "produit", "prix", "whatsapp", "quartier", "accroche")},
        "captures": captures,
        "audio_mode": "silent_conformance_voice_timeline_reserved",
        "output": {
            "uri": "output/output_T1_special_menu_reference_v3.mp4",
            "container": "mp4",
            "video_mime": "video/avc",
            "width": 720,
            "height": 1280,
            "fps": 30,
            "frames": 900,
            "duration_ms": 30000,
            "target_video_bitrate_bps": 5000000,
            "overwrite": True,
        },
    }


def build_golden() -> dict[str, Any]:
    indices = [0, 45, 179, 180, 419, 420, 629, 630, 809, 810, 817, 899]
    if REFERENCE_OUTPUT.is_file():
        if sha256(REFERENCE_OUTPUT) != REFERENCE_OUTPUT_SHA256:
            raise RuntimeError("Reference output hash does not match the approved V3 golden master")
        output_meta = video_metadata(REFERENCE_OUTPUT)
        keyframes = extract_keyframe_metrics(REFERENCE_OUTPUT, indices)
    elif GOLDEN_PATH.is_file():
        existing = load_json(GOLDEN_PATH)
        output_meta = existing["reference_output"]["decoded"]
        keyframes = existing["keyframes"]
    else:
        raise RuntimeError("Golden MP4 is required for the first conformance build")
    inputs = {}
    for scene, expected in SCENE_EXPECTATIONS.items():
        path = ROOT / expected["media"]
        inputs[scene] = {
            "path": expected["media"],
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
            "decoded": video_metadata(path),
            "required_frames": expected["frames"],
        }
    return {
        "schema_version": "1.0.0",
        "template_id": "restaurants_maquis_T1_special_menu_v1_0_0",
        "template_version": "1.0.0",
        "reference_backend": "Python/OpenCV/Pillow renderer",
        "inputs": inputs,
        "reference_output": {
            "path": "output/output_T1_special_menu_reference_v3.mp4",
            "sha256": REFERENCE_OUTPUT_SHA256,
            "bytes": REFERENCE_OUTPUT_BYTES,
            "decoded": output_meta,
            "binary_hash_rule": "exact only for the reference backend",
        },
        "keyframes": keyframes,
        "semantic_checks": {
            "scene_boundaries": [180, 420, 630, 900],
            "cut_frames": [60, 120, 180, 240, 300, 360, 420, 480, 540, 630, 690, 750, 810],
            "cta_full_opacity_frame": 899,
            "stable_background_from_frame": 817,
            "static_pairs_allowed": 0,
            "source_time_map": "identity",
            "audio_time_map": "identity",
        },
        "portable_backend_tolerance": {
            "minimum_keyframe_ssim": 0.93,
            "maximum_keyframe_mean_absolute_error_0_255": 9.0,
            "maximum_dhash_hamming_distance": 8,
            "geometry_tolerance_px_at_720": 2,
        },
    }


def build_result_fixture() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "status": "COMPLETED",
        "job_id": "t1-golden-0001",
        "idempotency_key": "t1-special-menu-golden-v1",
        "template_id": "restaurants_maquis_T1_special_menu_v1_0_0",
        "template_version": "1.0.0",
        "profile_used": "T1_REFERENCE_PYTHON",
        "output": {
            "uri": "output/output_T1_special_menu_reference_v3.mp4",
            "mime_type": "video/mp4",
            "width": 720,
            "height": 1280,
            "fps": 30,
            "frames": 900,
            "duration_ms": 30000,
            "bytes": REFERENCE_OUTPUT_BYTES,
            "sha256": REFERENCE_OUTPUT_SHA256,
            "audio_present": False,
        },
        "metrics": {
            "elapsed_ms": 0,
            "peak_memory_mb": 0,
            "decoder_count": 1,
            "encoder_count": 1,
            "static_frame_pairs": 0,
        },
        "warnings": ["Reference fixture: runtime elapsed time and memory must be populated by the integrating engine."],
    }


def build_error_fixture() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "status": "FAILED",
        "job_id": "t1-invalid-0001",
        "template_id": "restaurants_maquis_T1_special_menu_v1_0_0",
        "code": "T1_UNSUPPORTED_MEDIA",
        "message": "S2 must be H.264/AVC MP4 at 30 fps.",
        "retryable": True,
        "stage": "VALIDATING",
        "scene_id": "S2",
        "details": {"observed_video_codec": "video/hevc", "accepted_video_mime": ["video/avc"]},
    }


def artifact_entry(path_text: str, role: str, *, required: bool = True, bundle: bool = True,
                   expected_sha: str | None = None, expected_bytes: int | None = None) -> dict[str, Any]:
    path = ROOT / path_text
    if path.is_file():
        actual_sha = sha256(path)
        actual_bytes = path.stat().st_size
    elif expected_sha is not None and expected_bytes is not None:
        actual_sha = expected_sha
        actual_bytes = expected_bytes
    elif required:
        raise FileNotFoundError(path)
    else:
        actual_sha = expected_sha
        actual_bytes = expected_bytes
    return {
        "path": path_text,
        "role": role,
        "required": required,
        "bundle": bundle,
        "bytes": actual_bytes,
        "sha256": actual_sha,
    }


def build_manifest() -> dict[str, Any]:
    artifacts = [
        artifact_entry("config/T1_special_menu_template_v1_0_0.json", "canonical_template"),
        artifact_entry("config/T1_special_menu_reference_v3_1.json", "immutable_visual_ancestor"),
        artifact_entry("schemas/T1_template_package.schema.json", "template_schema"),
        artifact_entry("schemas/T1_render_job.schema.json", "render_job_schema"),
        artifact_entry("schemas/T1_render_result.schema.json", "render_result_schema"),
        artifact_entry("schemas/T1_render_error.schema.json", "render_error_schema"),
        artifact_entry("profiles/T1_android_offline_2gb.json", "required_low_end_profile"),
        artifact_entry("fixtures/t1-special-menu/render_job.valid.json", "valid_job_fixture"),
        artifact_entry("fixtures/t1-special-menu/render_result.valid.json", "valid_result_fixture"),
        artifact_entry("fixtures/t1-special-menu/render_error.unsupported_media.json", "valid_error_fixture"),
        artifact_entry("conformance/T1_special_menu_golden_v1.json", "golden_conformance_manifest"),
        artifact_entry("capture-guide/consignes_T1.json", "locked_capture_copy"),
        artifact_entry("demo/T1_demo_input.json", "merchant_fixture"),
        artifact_entry("simulation/media/S1.mp4", "capture_fixture_S1"),
        artifact_entry("simulation/media/S2.mp4", "capture_fixture_S2"),
        artifact_entry("simulation/media/S3.mp4", "capture_fixture_S3"),
        artifact_entry("simulation/media/S4.mp4", "capture_fixture_S4"),
        artifact_entry("simulation/media/voix1.mp3", "fixture_voice_S1"),
        artifact_entry("simulation/media/voix2.mp3", "fixture_voice_S2"),
        artifact_entry("simulation/media/voix3.mp3", "fixture_voice_S3"),
        artifact_entry("simulation/media/voix4.mp3", "fixture_voice_S4"),
        artifact_entry("assets/fonts/DMSerifDisplay-Regular.ttf", "font_display"),
        artifact_entry("assets/fonts/Montserrat-Variable.ttf", "font_light_sans"),
        artifact_entry("assets/fonts/PlusJakartaSans-Variable.ttf", "font_utility"),
        artifact_entry("assets/fonts/OFL-DMSerifDisplay.txt", "font_license"),
        artifact_entry("assets/fonts/OFL-Montserrat.txt", "font_license"),
        artifact_entry("assets/fonts/OFL-PlusJakartaSans.txt", "font_license"),
        artifact_entry("engine/special_menu_style.py", "reference_renderer"),
        artifact_entry("tools/render_t1_special_menu_v3.py", "reference_render_cli"),
        artifact_entry("tools/validate_t1_special_menu.py", "visual_validator"),
        artifact_entry("tools/build_t1_template_package_v1.py", "package_builder"),
        artifact_entry("tools/validate_t1_template_package.py", "package_validator"),
        artifact_entry("reports/T1_TEMPLATE_PACKAGE_V1_SILENT.md", "integration_documentation"),
        artifact_entry("ui-screens/planche_12_etats.png", "visual_capture_proof"),
        artifact_entry(
            "output/output_T1_special_menu_reference_v3.mp4",
            "golden_master",
            expected_sha=REFERENCE_OUTPUT_SHA256,
            expected_bytes=REFERENCE_OUTPUT_BYTES,
        ),
    ]
    return {
        "manifest_schema_version": "1.0.0",
        "package_id": "restaurants_maquis_T1_special_menu_template",
        "template_id": "restaurants_maquis_T1_special_menu_v1_0_0",
        "template_version": "1.0.0",
        "release_tag": "t1-special-menu-template-v1.0.0-silent",
        "release_channel": "stable_silent",
        "status": "template_side_complete_audio_deferred",
        "canonical_template": "config/T1_special_menu_template_v1_0_0.json",
        "runtime": {
            "mode": "offline_on_device",
            "target": "Android phone with 2 GB RAM",
            "preferred_backend": "AndroidX Media3 Transformer + MediaCodec + custom GlEffect",
            "remote_render_server": False,
            "bundled_ffmpeg_required": False,
        },
        "audio": {
            "merchant_voice_timeline": "reserved_identity_1_0x",
            "music": "deferred_to_next_phase",
            "future_music_model_target": "20 to 30 curated models",
            "sfx": "none_for_this_reference",
        },
        "commands": {
            "rebuild_contract": "PYTHONPATH=. python3 tools/build_t1_template_package_v1.py",
            "validate": "PYTHONPATH=. python3 tools/validate_t1_template_package.py --require-golden",
            "build_bundle": "PYTHONPATH=. python3 tools/build_t1_template_package_v1.py --bundle /tmp/T1_special_menu_template_v1_0_0.zip",
        },
        "artifacts": artifacts,
    }


def build_all() -> dict[str, Any]:
    write_json(OUT_CONFIG, build_template())
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    write_json(FIXTURE_DIR / "render_job.valid.json", build_render_job())
    write_json(FIXTURE_DIR / "render_result.valid.json", build_result_fixture())
    write_json(FIXTURE_DIR / "render_error.unsupported_media.json", build_error_fixture())
    write_json(GOLDEN_PATH, build_golden())
    manifest = build_manifest()
    write_json(MANIFEST_PATH, manifest)
    return manifest


def write_bundle(manifest: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    paths = [MANIFEST_PATH.relative_to(ROOT)]
    for artifact in manifest["artifacts"]:
        if artifact["bundle"]:
            path = Path(artifact["path"])
            if (ROOT / path).is_file():
                paths.append(path)
            elif artifact["required"]:
                raise FileNotFoundError(ROOT / path)
    unique = sorted(set(paths), key=lambda p: p.as_posix())
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for rel in unique:
            data = (ROOT / rel).read_bytes()
            info = zipfile.ZipInfo(f"{PACKAGE_PREFIX}/{rel.as_posix()}")
            info.date_time = (2020, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    print(json.dumps({
        "bundle": str(output),
        "bytes": output.stat().st_size,
        "sha256": sha256(output),
        "files": len(unique),
    }, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, help="Optional deterministic ZIP path")
    args = parser.parse_args()
    manifest = build_all()
    print(MANIFEST_PATH.relative_to(ROOT))
    if args.bundle:
        write_bundle(manifest, args.bundle.resolve())


if __name__ == "__main__":
    main()
