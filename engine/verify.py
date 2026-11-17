"""FFprobe-based contract verification for the silent T1 MP4."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inspect_video(path: Path) -> dict:
    result = subprocess.run([
        "ffprobe", "-v", "error", "-count_frames", "-show_entries",
        "format=duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,nb_read_frames,duration",
        "-of", "json", str(path),
    ], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def verify(path: Path) -> dict:
    probe = inspect_video(path)
    streams = probe.get("streams", [])
    video = [s for s in streams if s.get("codec_type") == "video"]
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    if len(video) != 1:
        raise AssertionError(f"Expected exactly one video stream; got {len(video)}")
    stream = video[0]
    frames = int(stream.get("nb_read_frames", -1))
    duration = float(probe.get("format", {}).get("duration", 0))
    checks = {
        "width_720": stream.get("width") == 720,
        "height_1280": stream.get("height") == 1280,
        "fps_30": stream.get("avg_frame_rate") == "30/1" or stream.get("r_frame_rate") == "30/1",
        "frames_900": frames == 900,
        "duration_30s": abs(duration - 30.0) <= 1 / 30,
        "no_audio": len(audio) == 0,
    }
    report = {
        "file": path.name,
        "result": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "width": stream.get("width"), "height": stream.get("height"),
        "fps": stream.get("avg_frame_rate"), "frames": frames,
        "duration_seconds": round(duration, 6), "audio_streams": len(audio),
        "size_bytes": int(probe.get("format", {}).get("size", 0)),
    }
    if not all(checks.values()):
        raise AssertionError(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, default=ROOT / "output" / "output_T1_sans_voix.mp4")
    parser.add_argument("--out", type=Path, default=ROOT / "output" / "verification.json")
    args = parser.parse_args()
    report = verify(args.video)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
