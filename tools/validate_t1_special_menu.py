#!/usr/bin/env python3
"""Forensic validation of a rendered T1 Special Menu preview."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

from engine.special_menu_style import ROOT, load_json, validate_config

CAPTURE_SHA256_AT_BASE = "93a807f88e0e0f909cb589e8539419a4d1c387c12bc1b9966ba7dbe1a936075c"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "config" / "T1_special_menu_reference_v1.json"
    )
    parser.add_argument(
        "--video", type=Path, default=ROOT / "output" / "output_T1_special_menu_reference_v1.mp4"
    )
    parser.add_argument(
        "--report", type=Path, default=ROOT / "reports" / "T1_special_menu_render_validation.json"
    )
    args = parser.parse_args()

    config = load_json(args.config)
    validate_config(config)
    capture_path = ROOT / config["scene_capture_contract"]["source"]
    capture_hash = sha256(capture_path)
    if capture_hash != CAPTURE_SHA256_AT_BASE:
        raise AssertionError("Le guide de capture a été modifié.")

    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise FileNotFoundError(args.video)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    advertised_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    previous: np.ndarray | None = None
    differences: list[float] = []
    decoded_frames = 0
    final_frame: np.ndarray | None = None
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        proxy = cv2.resize(frame, (144, 256), interpolation=cv2.INTER_AREA).astype(np.float32)
        if previous is not None:
            differences.append(float(np.mean(np.abs(proxy - previous))))
        previous = proxy
        final_frame = frame
        decoded_frames += 1
    cap.release()

    canvas = config["canvas"]
    assert (width, height) == (canvas["width"], canvas["height"])
    assert abs(fps - canvas["fps"]) < 0.01
    assert advertised_frames == decoded_frames == canvas["frames"]
    assert final_frame is not None

    delta = np.asarray(differences, dtype=np.float32)
    cuts = config["edit_timeline"]["hard_cut_frames"]
    cut_metrics = [{"at_f": cut, "mad": round(float(delta[cut - 1]), 6)} for cut in cuts]
    # Each declared crop/scene cut must be visibly different from an accidental
    # duplicate, while there must be no frozen adjacent pair anywhere.
    assert all(item["mad"] > 1.0 for item in cut_metrics)
    assert int(np.sum(delta < 0.15)) == 0

    # The final CTA includes a small official-green WhatsApp accent and remains
    # visible over a darkened, not fully black, background.
    roi = final_frame[int(height * 0.50) : int(height * 0.85), int(width * 0.10) : int(width * 0.90)]
    blue, green, red = cv2.split(roi)
    green_pixels = int(np.sum((green > 110) & (green > red * 1.25) & (green > blue * 1.10)))
    assert green_pixels >= 40
    final_mean = float(final_frame.mean())
    assert final_mean > 10.0

    try:
        origin_main = subprocess.check_output(
            ["git", "rev-parse", "origin/main"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        origin_main = None

    report = {
        "status": "PASS",
        "config": str(args.config.relative_to(ROOT)),
        "video": str(args.video.relative_to(ROOT)),
        "video_sha256": sha256(args.video),
        "video_bytes": args.video.stat().st_size,
        "decoded": {
            "width": width,
            "height": height,
            "fps": fps,
            "advertised_frames": advertised_frames,
            "decoded_frames": decoded_frames,
            "duration_s": decoded_frames / fps,
        },
        "motion": {
            "adjacent_pair_count": len(differences),
            "mad_mean": round(float(delta.mean()), 6),
            "mad_median": round(float(np.median(delta)), 6),
            "mad_p95": round(float(np.percentile(delta, 95)), 6),
            "mad_max": round(float(delta.max()), 6),
            "static_pairs_mad_lt_0_15": int(np.sum(delta < 0.15)),
            "near_static_pairs_mad_lt_0_50": int(np.sum(delta < 0.50)),
            "declared_cut_metrics": cut_metrics,
        },
        "cta_final_frame": {
            "frame": 899,
            "green_accent_pixels": green_pixels,
            "frame_mean_luma_proxy": round(final_mean, 6),
            "graphics_opacity_contract": 1.0,
        },
        "non_destructive": {
            "capture_guide_sha256": capture_hash,
            "capture_guide_matches_base": True,
            "origin_main": origin_main,
            "expected_origin_main": "ad4ff15a76dcba7bd08b7e8f56052e842b3e794f",
            "origin_main_untouched": origin_main
            == "ad4ff15a76dcba7bd08b7e8f56052e842b3e794f",
        },
        "audio": {
            "present_in_visual_preview": False,
            "reason": "Audio phase remains intentionally paused.",
            "speech_timeline_contract": "1.0x continuous source time per scene",
        },
    }
    if origin_main is not None:
        assert report["non_destructive"]["origin_main_untouched"] is True
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
