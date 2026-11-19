#!/usr/bin/env python3
"""Build and validate the four T1 French voice/music reference mixes.

Inputs are entirely local: the selected Arena.ai French voice, the four approved
Afrobeat/Amapiano masters, and the locked 30 s silent video. The script creates a
30 s voice stem, applies deterministic clip-based music ducking, masters each
variant, produces WAV/MP3/MP4 deliverables, and writes machine-readable QC.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
VOICE_MIX_CONFIG = ROOT / "config/T1_special_menu_voice_mix_v1_0_0.json"
REPORT_COPY = ROOT / "reports/T1_voice_music_v1_validation.json"
SR = 48_000
TOTAL_S = 30.0
N = int(SR * TOTAL_S)


def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, **kwargs)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def decode_audio(path: Path, channels: int) -> np.ndarray:
    raw = run(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0",
            "-ar", str(SR), "-ac", str(channels), "-f", "f32le", "-",
        ],
        capture_output=True,
    ).stdout
    data = np.frombuffer(raw, dtype="<f4").astype(np.float64)
    return data.reshape(-1, channels) if channels > 1 else data


def write_float_wav(path: Path, data: np.ndarray, codec: str = "pcm_s24le") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    channels = data.shape[1] if data.ndim == 2 else 1
    process = subprocess.Popen(
        [
            "ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR),
            "-ac", str(channels), "-i", "-", "-map_metadata", "-1",
            "-c:a", codec, str(path),
        ],
        stdin=subprocess.PIPE,
    )
    process.communicate(np.asarray(data, dtype="<f4").tobytes())
    if process.returncode:
        raise RuntimeError(f"ffmpeg failed while writing {path}")


def loudness_stats(path: Path, target_i: float, target_tp: float) -> dict[str, float | str]:
    filter_value = f"loudnorm=I={target_i}:TP={target_tp}:LRA=7:print_format=json"
    process = run(
        [
            "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
            "-map", "0:a:0", "-af", filter_value, "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
    )
    blocks = re.findall(r'\{\s*"input_i".*?\}', process.stderr, re.S)
    if not blocks:
        raise RuntimeError(f"loudnorm did not return JSON for {path}")
    return json.loads(blocks[-1])


def normalize_voice(source: Path, target: Path, target_i: float, target_tp: float) -> dict:
    """Match clip loudness, then catch only peaks above the voice ceiling."""
    before = loudness_stats(source, target_i, target_tp)
    gain_db = target_i - float(before["input_i"])
    # 0.1 dB safety margin prevents inter-sample overs after 48 kHz conversion.
    limit = 10 ** ((target_tp - 0.1) / 20.0)
    audio_filter = (
        f"afade=t=in:st=0:d=0.006,volume={gain_db:.6f}dB,"
        f"alimiter=limit={limit:.9f}:attack=5:release=50:level=false:latency=true"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(source),
            "-map", "0:a:0", "-af", audio_filter, "-ar", str(SR), "-ac", "1",
            "-map_metadata", "-1", "-c:a", "pcm_s16le", str(target),
        ]
    )
    after = loudness_stats(target, target_i, target_tp)
    return {
        "applied_gain_db": round(gain_db, 3),
        "integrated_lufs": float(after["input_i"]),
        "true_peak_dbtp": float(after["input_tp"]),
        "loudness_range_lu": float(after["input_lra"]),
    }


def duck_envelope(
    spans: list[tuple[float, float]], attack_s: float, release_s: float
) -> np.ndarray:
    """Return 0=open and 1=fully ducked; ramps are linear in dB."""
    envelope = np.zeros(N, dtype=np.float64)
    for start, end in spans:
        attack_start = max(0, int(round((start - attack_s) * SR)))
        full_start = int(round(start * SR))
        full_end = min(N, int(round(end * SR)))
        release_end = min(N, int(round((end + release_s) * SR)))
        if full_start > attack_start:
            envelope[attack_start:full_start] = np.maximum(
                envelope[attack_start:full_start],
                np.linspace(0.0, 1.0, full_start - attack_start, endpoint=False),
            )
        envelope[full_start:full_end] = 1.0
        if release_end > full_end:
            envelope[full_end:release_end] = np.maximum(
                envelope[full_end:release_end],
                np.linspace(1.0, 0.0, release_end - full_end, endpoint=False),
            )
    return envelope


def master_mix(source: Path, target: Path, target_i: float, target_tp: float) -> tuple[dict, dict]:
    """Two-pass EBU R128 mastering with a true-peak ceiling."""
    before = loudness_stats(source, target_i, target_tp)
    audio_filter = (
        f"loudnorm=I={target_i}:TP={target_tp}:LRA=7:"
        f"measured_I={before['input_i']}:measured_LRA={before['input_lra']}:"
        f"measured_TP={before['input_tp']}:measured_thresh={before['input_thresh']}:"
        f"offset={before['target_offset']}:linear=false:print_format=summary"
    )
    run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(source),
            "-map", "0:a:0", "-af", audio_filter, "-t", str(TOTAL_S),
            "-ar", str(SR), "-ac", "2", "-map_metadata", "-1",
            "-c:a", "pcm_s24le", str(target),
        ]
    )
    after = loudness_stats(target, target_i, target_tp)
    return before, after


def probe(path: Path) -> dict:
    return json.loads(
        run(
            [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration,size:stream=codec_name,codec_type,sample_rate,channels,nb_frames",
                "-of", "json", str(path),
            ],
            capture_output=True,
            text=True,
        ).stdout
    )


def encoded_stream_sha256(path: Path, stream: str) -> str:
    """Hash encoded packets without decoding; proves the video stream was copied."""
    output = run(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-map", stream,
            "-c", "copy", "-f", "hash", "-hash", "sha256", "-",
        ],
        capture_output=True,
        text=True,
    ).stdout.strip()
    return output.split("=", 1)[1]


def frame_speech_metrics(
    voice: np.ndarray, music: np.ndarray, spans: list[tuple[float, float]], threshold_db: float = -38.0
) -> dict:
    frame = int(0.020 * SR)
    values: list[float] = []
    voice_powers: list[float] = []
    music_powers: list[float] = []
    by_scene: list[dict] = []
    for scene, (start, end) in enumerate(spans, 1):
        scene_values: list[float] = []
        first = int(start * SR) // frame
        last = min(len(voice) // frame, int(np.ceil(end * SR / frame)))
        for index in range(first, last):
            a, b = index * frame, (index + 1) * frame
            vp = float(np.mean(voice[a:b] ** 2))
            voice_db = 10 * np.log10(max(vp, 1e-20))
            if voice_db <= threshold_db:
                continue
            mp = float(np.mean(music[a:b] ** 2))
            ratio = 10 * np.log10(max(vp, 1e-20) / max(mp, 1e-20))
            values.append(ratio)
            scene_values.append(ratio)
            voice_powers.append(vp)
            music_powers.append(mp)
        by_scene.append(
            {
                "scene": scene,
                "active_speech_s": round(len(scene_values) * frame / SR, 3),
                "median_speech_to_music_db": round(float(np.median(scene_values)), 2),
                "p10_speech_to_music_db": round(float(np.percentile(scene_values, 10)), 2),
            }
        )
    aggregate = 10 * np.log10(np.mean(voice_powers) / np.mean(music_powers))
    return {
        "method": "20 ms frames; voice RMS above -38 dBFS; pre-master stems",
        "active_speech_s": round(len(values) * frame / SR, 3),
        "aggregate_speech_to_music_db": round(float(aggregate), 2),
        "median_speech_to_music_db": round(float(np.median(values)), 2),
        "p10_speech_to_music_db": round(float(np.percentile(values, 10)), 2),
        "scenes": by_scene,
    }


def sample_qc(audio: np.ndarray) -> dict:
    peak = float(np.max(np.abs(audio)))
    if audio.ndim == 1:
        dc = [float(np.mean(audio))]
    else:
        dc = [float(value) for value in np.mean(audio, axis=0)]
    return {
        "sample_peak_dbfs": round(float(20 * np.log10(max(peak, 1e-12))), 3),
        "clipped_sample_count": int(np.count_nonzero(np.abs(audio) >= 0.999999)),
        "nan_count": int(np.isnan(audio).sum()),
        "inf_count": int(np.isinf(audio).sum()),
        "dc_offset_max_abs": round(max(abs(value) for value in dc), 7),
    }


def write_automation_csv(
    path: Path, music_gain_db: np.ndarray, spans: list[tuple[float, float]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    step = int(0.010 * SR)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time_s", "music_gain_db", "voice_clip_active"])
        for sample in range(0, N + 1, step):
            index = min(sample, N - 1)
            time_s = sample / SR
            active = int(any(start <= time_s < end for start, end in spans))
            writer.writerow([f"{time_s:.3f}", f"{music_gain_db[index]:.4f}", active])


def draw_ducking_plot(
    path: Path, voice: np.ndarray, music_gain_db: np.ndarray, spans: list[tuple[float, float]]
) -> None:
    """Draw the QC timeline with Pillow, already required by the project."""
    from PIL import Image, ImageDraw, ImageFont

    width, height = 1600, 700
    image = Image.new("RGB", (width, height), "#f7f1e8")
    draw = ImageDraw.Draw(image, "RGBA")
    font_path = ROOT / "assets/fonts/PlusJakartaSans-Variable.ttf"
    title_font = ImageFont.truetype(str(font_path), 34)
    label_font = ImageFont.truetype(str(font_path), 19)
    small_font = ImageFont.truetype(str(font_path), 16)
    left, right = 100, 1545
    top_box = (left, 90, right, 330)
    bottom_box = (left, 390, right, 625)
    draw.rounded_rectangle(top_box, 18, fill="#fffaf4", outline="#ded2c5", width=2)
    draw.rounded_rectangle(bottom_box, 18, fill="#fffaf4", outline="#ded2c5", width=2)
    draw.text((left, 30), "T1 — tige voix 30 s et automation de ducking", fill="#201d19", font=title_font)

    def x_at(time_s: float) -> int:
        return int(round(left + time_s / TOTAL_S * (right - left)))

    for marker in [0, 6, 14, 21, 30]:
        x = x_at(marker)
        draw.line((x, top_box[1], x, top_box[3]), fill="#9b9187", width=1)
        draw.line((x, bottom_box[1], x, bottom_box[3]), fill="#9b9187", width=1)
        draw.text((x - 10, 638), f"{marker}", fill="#6e665e", font=small_font)

    # Voice waveform: min/max sample per horizontal pixel keeps transients visible.
    center = (top_box[1] + top_box[3]) // 2
    peak = max(float(np.max(np.abs(voice))), 1e-9)
    samples_per_pixel = max(1, len(voice) // (right - left))
    for column in range(right - left):
        a = column * samples_per_pixel
        b = min(len(voice), a + samples_per_pixel)
        segment = voice[a:b]
        low = int(center - float(np.max(segment)) / peak * 96)
        high = int(center - float(np.min(segment)) / peak * 96)
        draw.line((left + column, low, left + column, high), fill="#a73337", width=1)
    draw.line((left, center, right, center), fill="#d6b2ae", width=1)
    draw.text((22, center - 12), "Voix", fill="#9b2d30", font=label_font)

    # Shade full voice clip windows, then draw the music gain curve.
    for start, end in spans:
        draw.rectangle((x_at(start), bottom_box[1], x_at(end), bottom_box[3]), fill="#f0a33b28")
    gain_top, gain_bottom = -2.3, -10.7

    def y_at(gain_db: float) -> int:
        return int(round(bottom_box[1] + (gain_top - gain_db) / (gain_top - gain_bottom) * (bottom_box[3] - bottom_box[1])))

    for db in range(-10, -2):
        y = y_at(float(db))
        draw.line((left, y, right, y), fill="#ded2c5", width=1)
        draw.text((55, y - 10), str(db), fill="#6e665e", font=small_font)
    points = []
    for column in range(right - left + 1):
        index = min(N - 1, int(column / (right - left) * (N - 1)))
        points.append((left + column, y_at(float(music_gain_db[index]))))
    draw.line(points, fill="#16796f", width=4, joint="curve")
    draw.text((15, 485), "Gain", fill="#16796f", font=label_font)
    draw.text((14, 510), "musique", fill="#16796f", font=label_font)
    draw.text((x_at(0.4), y_at(-3) + 10), "hors voix −3 dB", fill="#16796f", font=small_font)
    draw.text((x_at(1.4), y_at(-10) - 30), "sous voix −10 dB", fill="#9b2d30", font=small_font)
    draw.text((right - 20, 638), "s", fill="#6e665e", font=small_font)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--preview-dir", type=Path, default=ROOT / "output/t1-voice-music-v1"
    )
    args = parser.parse_args()
    output_dir = args.preview_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    voice_config = json.loads(VOICE_MIX_CONFIG.read_text(encoding="utf-8"))
    music_config_path = ROOT / voice_config["music_pack"]
    music_config = json.loads(music_config_path.read_text(encoding="utf-8"))
    mix = voice_config["mix_contract"]
    gates = voice_config["quality_gates"]
    clips_config = voice_config["voice"]["clips"]
    expected_ids = gates["approved_variant_ids"]
    actual_ids = [track["id"] for track in music_config["tracks"]]
    if len(actual_ids) != gates["exact_music_variant_count"] or actual_ids != expected_ids:
        raise ValueError("The music pack does not contain the exact approved four variants.")

    clips: list[np.ndarray] = []
    voice_entries: list[dict] = []
    for item in clips_config:
        source = ROOT / item["source"]
        processed = ROOT / item["processed"]
        normalization = normalize_voice(
            source,
            processed,
            float(voice_config["voice"]["normalization_target_lufs"]),
            float(voice_config["voice"]["normalization_true_peak_dbtp_max"]),
        )
        clip = decode_audio(processed, 1)
        clips.append(clip)
        end_s = float(item["start_s"]) + len(clip) / SR
        voice_entries.append(
            {
                **item,
                "end_s": round(end_s, 3),
                "duration_s": round(len(clip) / SR, 3),
                "decoded_samples": len(clip),
                "source_sha256": sha256(source),
                "processed_sha256": sha256(processed),
                "normalization": normalization,
            }
        )

    voice = np.zeros(N, dtype=np.float64)
    for item, clip in zip(voice_entries, clips):
        start = int(round(float(item["start_s"]) * SR))
        count = min(len(clip), N - start)
        voice[start : start + count] += clip[:count]
    spans = [(float(item["start_s"]), float(item["end_s"])) for item in voice_entries]

    voice_stem = ROOT / voice_config["voice"]["stem_file"]
    write_float_wav(voice_stem, voice, "pcm_s24le")
    stem_stats = loudness_stats(voice_stem, -20, -3)

    attack_s = float(mix["duck_attack_ms"]) / 1000.0
    release_s = float(mix["duck_release_ms"]) / 1000.0
    envelope = duck_envelope(spans, attack_s, release_s)
    open_db = float(mix["music_open_gain_db"])
    under_db = float(mix["music_under_voice_gain_db"])
    music_gain_db = open_db + (under_db - open_db) * envelope
    music_gain = 10 ** (music_gain_db / 20.0)

    automation_csv = output_dir / "T1_ducking_automation_10ms.csv"
    ducking_plot = output_dir / "T1_ducking_voice_timeline.png"
    write_automation_csv(automation_csv, music_gain_db, spans)
    draw_ducking_plot(ducking_plot, voice, music_gain_db, spans)

    variants: list[dict] = []
    visual_source = ROOT / voice_config["visual_source"]
    visual_video_hash = encoded_stream_sha256(visual_source, "0:v:0")
    with tempfile.TemporaryDirectory(prefix="t1-voice-mix-") as temporary:
        temporary_dir = Path(temporary)
        for track in music_config["tracks"]:
            track_id = int(track["pixabay_id"])
            music = decode_audio(ROOT / track["file"], 2)
            if len(music) < N:
                music = np.pad(music, ((0, N - len(music)), (0, 0)))
            music = music[:N]
            music_stem = music * music_gain[:, None]
            voice_stereo = np.column_stack((voice, voice))
            premix = music_stem + voice_stereo
            raw = temporary_dir / f"{track_id}_premix.wav"
            write_float_wav(raw, premix)

            wav = output_dir / f"T1_voice_music_{track_id}.wav"
            before, after = master_mix(
                raw, wav, float(mix["master_target_lufs"]), float(mix["master_true_peak_dbtp_max"])
            )
            mp3 = output_dir / f"T1_voice_music_{track_id}.mp3"
            run(
                [
                    "ffmpeg", "-y", "-v", "error", "-i", str(wav), "-t", str(TOTAL_S),
                    "-map_metadata", "-1", "-c:a", "libmp3lame", "-b:a", "192k", str(mp3),
                ]
            )
            mp4 = output_dir / f"T1_voice_music_{track_id}.mp4"
            run(
                [
                    "ffmpeg", "-y", "-v", "error", "-i", str(visual_source), "-i", str(wav),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-ar", str(SR), "-ac", "2", "-t", str(TOTAL_S),
                    "-map_metadata", "-1", "-movflags", "+faststart", str(mp4),
                ]
            )

            wav_audio = decode_audio(wav, 2)
            aac_audio = decode_audio(mp4, 2)
            mp3_audio = decode_audio(mp3, 2)
            wav_stats = loudness_stats(wav, -16, -2)
            aac_stats = loudness_stats(mp4, -16, -1)
            mp3_stats = loudness_stats(mp3, -16, -1)
            speech = frame_speech_metrics(voice, music_stem, spans)
            wav_qc = sample_qc(wav_audio)
            aac_qc = sample_qc(aac_audio)
            mp3_qc = sample_qc(mp3_audio)
            mp4_probe = probe(mp4)
            output_video_hash = encoded_stream_sha256(mp4, "0:v:0")
            variant_pass = all(
                [
                    len(wav_audio) == N,
                    gates["integrated_lufs_min"] <= float(wav_stats["input_i"]) <= gates["integrated_lufs_max"],
                    float(wav_stats["input_tp"]) <= gates["wav_true_peak_dbtp_max"],
                    float(aac_stats["input_tp"]) <= gates["aac_true_peak_dbtp_max"],
                    speech["aggregate_speech_to_music_db"] >= gates["minimum_active_speech_to_music_db"],
                    wav_qc["clipped_sample_count"] <= gates["clipped_sample_count_max"],
                    aac_qc["clipped_sample_count"] <= gates["clipped_sample_count_max"],
                    wav_qc["nan_count"] == wav_qc["inf_count"] == 0,
                    aac_qc["nan_count"] == aac_qc["inf_count"] == 0,
                    float(mp4_probe["format"]["duration"]) == TOTAL_S,
                    output_video_hash == visual_video_hash,
                ]
            )
            variants.append(
                {
                    "status": "PASS" if variant_pass else "FAIL",
                    "variant_id": track["id"],
                    "pixabay_id": track_id,
                    "title": track["title"],
                    "artist": track["artist"],
                    "music_file": track["file"],
                    "pre_master": {
                        "integrated_lufs": float(before["input_i"]),
                        "true_peak_dbtp": float(before["input_tp"]),
                    },
                    "master_wav": {
                        "file": rel(wav), "sha256": sha256(wav), "bytes": wav.stat().st_size,
                        "decoded_samples": len(wav_audio), "duration_s": len(wav_audio) / SR,
                        "integrated_lufs": float(wav_stats["input_i"]),
                        "true_peak_dbtp": float(wav_stats["input_tp"]), **wav_qc,
                    },
                    "preview_mp3": {
                        "file": rel(mp3), "sha256": sha256(mp3), "bytes": mp3.stat().st_size,
                        "decoded_samples": len(mp3_audio), "duration_s": len(mp3_audio) / SR,
                        "integrated_lufs": float(mp3_stats["input_i"]),
                        "true_peak_dbtp": float(mp3_stats["input_tp"]), **mp3_qc,
                    },
                    "preview_mp4": {
                        "file": rel(mp4), "sha256": sha256(mp4), "bytes": mp4.stat().st_size,
                        "decoded_audio_samples": len(aac_audio),
                        "decoded_audio_duration_s": len(aac_audio) / SR,
                        "integrated_lufs": float(aac_stats["input_i"]),
                        "true_peak_dbtp": float(aac_stats["input_tp"]), **aac_qc,
                        "video_bitstream_sha256": output_video_hash,
                        "visual_source_bitstream_identical": output_video_hash == visual_video_hash,
                        "probe": mp4_probe,
                    },
                    "intelligibility_proxy": speech,
                }
            )

    all_pass = all(item["status"] == "PASS" for item in variants)
    report = {
        "schema_version": "1.0.0",
        "status": "PASS" if all_pass else "FAIL",
        "generated_on": "2026-11-18",
        "configuration": rel(VOICE_MIX_CONFIG),
        "music_pack": rel(music_config_path),
        "visual_source": rel(visual_source),
        "visual_source_video_bitstream_sha256": visual_video_hash,
        "sample_rate_hz": SR,
        "duration_s": TOTAL_S,
        "voice": {
            "provider": voice_config["voice"]["provider"],
            "voice_id": voice_config["voice"]["voice_id"],
            "language": voice_config["voice"]["language"],
            "identity": voice_config["voice"]["identity"],
            "clips": voice_entries,
            "stem": {
                "file": rel(voice_stem), "sha256": sha256(voice_stem),
                "bytes": voice_stem.stat().st_size, "decoded_samples": len(voice),
                "duration_s": len(voice) / SR,
                "integrated_lufs": float(stem_stats["input_i"]),
                "true_peak_dbtp": float(stem_stats["input_tp"]),
                **sample_qc(voice),
            },
        },
        "ducking": {
            **mix,
            "minimum_music_gain_db": round(float(music_gain_db.min()), 4),
            "maximum_music_gain_db": round(float(music_gain_db.max()), 4),
            "duration_at_full_duck_s": round(float(np.count_nonzero(music_gain_db <= under_db + 1e-6)) / SR, 3),
            "duration_in_attack_or_release_s": round(float(np.count_nonzero((music_gain_db > under_db + 1e-6) & (music_gain_db < open_db - 1e-6))) / SR, 3),
            "automation_csv": rel(automation_csv),
            "timeline_plot": rel(ducking_plot),
        },
        "quality_gates": gates,
        "variants": variants,
        "human_review": {
            "status": "PENDING",
            "required": True,
            "note": "Objective QC is complete; creative choice and pronunciation must be approved by listening to the four previews."
        },
    }
    report_path = output_dir / "T1_voice_music_validation.json"
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    report_path.write_text(payload, encoding="utf-8")
    REPORT_COPY.write_text(payload, encoding="utf-8")

    manifest = {
        "schema_version": "1.0.0",
        "status": "generated_and_objectively_validated" if all_pass else "validation_failed",
        "configuration": rel(VOICE_MIX_CONFIG),
        "voice_provider": voice_config["voice"]["provider"],
        "voice_id": voice_config["voice"]["voice_id"],
        "language": voice_config["voice"]["language"],
        "clips": voice_entries,
        "stem": report["voice"]["stem"],
        "mix_validation": rel(REPORT_COPY),
    }
    manifest_path = voice_stem.parent / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    compact = {
        "status": report["status"],
        "voice_stem": rel(voice_stem),
        "preview_dir": rel(output_dir),
        "variants": [
            {
                "pixabay_id": item["pixabay_id"],
                "status": item["status"],
                "wav_lufs": item["master_wav"]["integrated_lufs"],
                "wav_tp": item["master_wav"]["true_peak_dbtp"],
                "aac_tp": item["preview_mp4"]["true_peak_dbtp"],
                "speech_to_music_db": item["intelligibility_proxy"]["aggregate_speech_to_music_db"],
            }
            for item in variants
        ],
    }
    print(json.dumps(compact, ensure_ascii=False, indent=2))
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
