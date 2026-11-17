"""Small deterministic FFmpeg/Python renderer for the locked T1 pilot."""
from __future__ import annotations

import json
import math
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, FPS = 720, 1280, 30
ORANGE = (242, 98, 27)
NAVY = (20, 34, 94)
CREAM = (255, 243, 234)
WHITE = (255, 255, 255)
DARK = (15, 23, 42)
GREEN = (37, 211, 102)


def run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, **kwargs)


def load_plan(path: Path) -> dict[str, Any]:
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan["output"] != {"width": 720, "height": 1280, "fps": 30, "frames": 900, "duration_s": 30.0, "audio": False}:
        raise ValueError("Render plan output must remain 720x1280, 30 fps, 900 frames, silent.")
    if len(plan["shots"]) != 12 or len(plan["overlays"]) != 8 or len(plan["motion_presets"]) != 14:
        raise ValueError("T1 contract mismatch: expected 12 shots, 8 overlays, 14 motion presets.")
    return plan


def font(path: Path, size: int, weight: str = "ExtraBold") -> ImageFont.FreeTypeFont:
    result = ImageFont.truetype(str(path), size=size)
    try:
        result.set_variation_by_name(weight)
    except (AttributeError, OSError):
        pass
    return result


def easing(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def fit_font(draw: ImageDraw.ImageDraw, text: str, path: Path, max_size: int, min_size: int, width: int, weight: str) -> ImageFont.FreeTypeFont:
    size = max_size
    while size > min_size:
        current = font(path, size, weight)
        if draw.textbbox((0, 0), text, font=current, stroke_width=1)[2] <= width:
            return current
        size -= 2
    return font(path, min_size, weight)


def center_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fnt: ImageFont.FreeTypeFont,
                fill: tuple[int, ...] = WHITE, stroke: int = 1) -> None:
    x, y = xy
    box = draw.textbbox((0, 0), text, font=fnt, stroke_width=stroke)
    draw.text((x - (box[2] - box[0]) / 2, y - (box[3] - box[1]) / 2), text,
              font=fnt, fill=fill, stroke_width=stroke, stroke_fill=(20, 23, 28, 230))


def zoom_frame(frame: np.ndarray, factor: float, dx: float = 0.0, dy: float = 0.0) -> np.ndarray:
    factor = max(1.0, factor)
    h, w = frame.shape[:2]
    crop_w, crop_h = max(1, int(w / factor)), max(1, int(h / factor))
    cx = w * (0.5 + dx)
    cy = h * (0.5 + dy)
    left = int(max(0, min(w - crop_w, cx - crop_w / 2)))
    top = int(max(0, min(h - crop_h, cy - crop_h / 2)))
    crop = frame[top:top + crop_h, left:left + crop_w]
    return cv2.resize(crop, (w, h), interpolation=cv2.INTER_LANCZOS4)


def transition_frame(old: np.ndarray | None, new: np.ndarray, kind: str, step: int, duration: int = 6) -> np.ndarray:
    if old is None or step >= duration:
        return new
    progress = (step + 1) / duration
    if kind == "TR05":
        return cv2.addWeighted(old, 1.0 - progress, new, progress, 0.0)
    if kind == "TR03":
        yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
        mask = (xx / WIDTH + yy / HEIGHT) / 2.0 <= progress
        result = old.copy()
        result[mask] = new[mask]
        return result
    if kind == "TR04":
        result = old.copy()
        edge = int(WIDTH * progress)
        result[:, :edge] = new[:, :edge]
        return result
    if kind == "TR02":
        factor = 1.12 - 0.12 * easing(progress)
        return zoom_frame(new, factor)
    return new


def rgba_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: tuple[int, int, int], radius: int = 22,
              outline: tuple[int, int, int] | None = None, width: int = 0) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=(*fill, 210), outline=((*outline, 240) if outline else None), width=width)


def draw_overlay(base: np.ndarray, frame_no: int, plan: dict[str, Any], fonts: tuple[Path, Path]) -> np.ndarray:
    blocks = [b for b in plan["overlays"] if b["start_f"] <= frame_no < b["end_f"]]
    if not blocks:
        return base
    block = blocks[0]
    comp = block["composition"]
    data = plan["display"]
    mont, jakarta = fonts
    image = Image.fromarray(cv2.cvtColor(base, cv2.COLOR_BGR2RGB)).convert("RGBA")
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    local = frame_no - block["start_f"]
    entrance = easing(min(1.0, local / 8.0))
    lift = int(round((1.0 - entrance) * 18))
    opacity = int(255 * min(1.0, 0.28 + entrance * 0.72))

    if comp in ("enseigne_mot_a_mot", "enseigne_rappel"):
        title = data["nom"].upper()
        f = fit_font(d, title, mont, 52, 34, 600, "ExtraBold")
        rgba_card(d, (42, 205 - lift, 678, 352 - lift), DARK, radius=24)
        center_text(d, (360, 275 - lift), title, f, WHITE, 2)
        d.rounded_rectangle((247, 330 - lift, 473, 338 - lift), radius=4, fill=(*ORANGE, 255))

    elif comp == "bandeau_produit":
        title = data["produit"].upper()
        f = fit_font(d, title, mont, 46, 30, 590, "ExtraBold")
        rgba_card(d, (38, 535 - lift, 682, 663 - lift), DARK, radius=24)
        center_text(d, (360, 598 - lift), title, f, WHITE, 2)

    elif comp == "hero_lockup":
        product = data["produit"].upper()
        price = data["prix"]
        f = fit_font(d, product, mont, 42, 28, 570, "ExtraBold")
        rgba_card(d, (34, 500 - lift, 686, 662 - lift), DARK, radius=26)
        center_text(d, (360, 548 - lift), "PLAT DU JOUR", font(jakarta, 21, "Bold"), CREAM, 1)
        center_text(d, (360, 598 - lift), product, f, WHITE, 2)
        d.rounded_rectangle((112, 625 - lift, 608, 694 - lift), radius=24, fill=(*ORANGE, 255), outline=(*WHITE, 255), width=3)
        pf = fit_font(d, price, jakarta, 34, 25, 450, "ExtraBold")
        center_text(d, (360, 659 - lift), price, pf, NAVY, 1)

    elif comp == "accroche_segments":
        phrase = data.get("accroche", "")
        if phrase:
            pieces = [p.strip() for p in phrase.replace("•", "·").split("·") if p.strip()]
            if len(pieces) < 2:
                pieces = [phrase]
            index = min(len(pieces) - 1, int(local / max(1, (block["end_f"] - block["start_f"]) / len(pieces))))
            active = pieces[index].upper()
            f = fit_font(d, active, mont, 44, 28, 580, "ExtraBold")
            w = min(620, d.textbbox((0, 0), active, font=f)[2] + 68)
            x = (WIDTH - w) // 2
            d.rounded_rectangle((x, 545 - lift, x + w, 635 - lift), radius=36, fill=(*ORANGE, 235))
            center_text(d, (360, 590 - lift), active, f, WHITE, 1)
            if len(pieces) > 1:
                labels = "  ·  ".join(p.upper() for p in pieces)
                small = fit_font(d, labels, jakarta, 19, 14, 640, "Bold")
                center_text(d, (360, 664 - lift), labels, small, CREAM, 0)

    elif comp == "prix_plein":
        price = data["prix"]
        d.rounded_rectangle((64, 522 - lift, 656, 690 - lift), radius=42, fill=(*ORANGE, 245), outline=(*WHITE, 255), width=4)
        pf = fit_font(d, price, jakarta, 76, 48, 540, "ExtraBold")
        center_text(d, (360, 604 - lift), price, pf, NAVY, 1)

    elif comp == "adresse":
        location = data["quartier"].upper()
        f = fit_font(d, location, jakarta, 34, 24, 570, "Bold")
        rgba_card(d, (36, 746 - lift, 684, 846 - lift), DARK, radius=28)
        d.ellipse((68, 779 - lift, 94, 805 - lift), outline=(*ORANGE, 255), width=4)
        d.ellipse((77, 788 - lift, 85, 796 - lift), fill=(*ORANGE, 255))
        center_text(d, (386, 796 - lift), location, f, WHITE, 1)
        center_text(d, (360, 866 - lift), "ADRESSE FICTIVE · DÉMO", font(jakarta, 18, "Bold"), CREAM, 0)

    elif comp == "cta_whatsapp":
        contact = data["whatsapp"].upper()
        d.rounded_rectangle((42, 796 - lift, 678, 956 - lift), radius=78, fill=(*GREEN, 247), outline=(*WHITE, 255), width=3)
        center_text(d, (360, 845 - lift), "COMMANDER · WHATSAPP", font(mont, 26, "ExtraBold"), WHITE, 1)
        cf = fit_font(d, contact, jakarta, 31, 22, 540, "ExtraBold")
        center_text(d, (360, 905 - lift), contact, cf, WHITE, 1)
        center_text(d, (360, 974 - lift), "DONNÉES FICTIVES — DÉMONSTRATION", font(jakarta, 16, "Bold"), WHITE, 0)

    # Ease the whole graphic group in, keeping fully transparent area clear.
    alpha = layer.getchannel("A").point(lambda value: int(value * opacity / 255))
    layer.putalpha(alpha)
    composed = Image.alpha_composite(image, layer).convert("RGB")
    return cv2.cvtColor(np.asarray(composed), cv2.COLOR_RGB2BGR)


def normalize_source(source: Path, output: Path) -> None:
    vf = "fps=30,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,eq=saturation=1.08:contrast=1.03:brightness=0.01"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source), "-an", "-vf", vf,
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "19", "-pix_fmt", "yuv420p", str(output)])


def text_moments(plan: dict[str, Any]) -> list[tuple[int, str]]:
    return [(int((shot["out_start_f"] + shot["out_end_f"]) / 2), shot["id"]) for shot in plan["shots"]]


def create_contact_sheet(video_path: Path, plan: dict[str, Any], output_path: Path) -> None:
    import cv2
    thumbs = []
    cap = cv2.VideoCapture(str(video_path))
    for frame_no, shot_id in text_moments(plan):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ok, frame = cap.read()
        if not ok:
            continue
        im = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((180, 320), Image.Resampling.LANCZOS)
        tile = Image.new("RGB", (200, 354), (18, 22, 34))
        tile.paste(im, (10, 8))
        ImageDraw.Draw(tile).text((12, 332), f"{shot_id} · f{frame_no}", fill=WHITE)
        thumbs.append(tile)
    cap.release()
    sheet = Image.new("RGB", (4 * 200 + 5 * 14, 3 * 354 + 4 * 14), (9, 13, 23))
    for idx, thumb in enumerate(thumbs):
        x = 14 + (idx % 4) * 214
        y = 14 + (idx // 4) * 368
        sheet.paste(thumb, (x, y))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, optimize=True)


def render_video(plan_path: Path, video_path: Path, sheet_path: Path | None = None) -> dict[str, Any]:
    plan = load_plan(plan_path)
    from engine.fetch_rushes import ensure_rushes
    ensure_rushes()
    work_dir = Path(tempfile.mkdtemp(prefix="t1-render-"))
    clips: dict[str, Path] = {}
    caps: dict[str, cv2.VideoCapture] = {}
    last_source_index: dict[str, int] = {}
    try:
        for scene in plan["scenes"]:
            source_item = next(s for s in plan["shots"] if s["scene"] == scene["id"])
            source = ROOT / source_item["source"]["file"]
            normalized = work_dir / f"{scene['id']}.mp4"
            normalize_source(source, normalized)
            clips[scene["id"]] = normalized
            caps[scene["id"]] = cv2.VideoCapture(str(normalized))
            if not caps[scene["id"]].isOpened():
                raise RuntimeError(f"FFmpeg-normalized source could not be opened: {scene['id']}")

        cut_map = {int(c["at_f"]): c["transition"] for c in plan["cuts"]}
        shot_by_start = {int(s["out_start_f"]): s for s in plan["shots"]}
        overlay_font_mont = ROOT / "assets" / "fonts" / "Montserrat-Variable.ttf"
        overlay_font_jakarta = ROOT / "assets" / "fonts" / "PlusJakartaSans-Variable.ttf"
        video_path.parent.mkdir(parents=True, exist_ok=True)
        error_log = work_dir / "ffmpeg-encode.log"
        with error_log.open("wb") as err:
            encoder = subprocess.Popen([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "rawvideo", "-pixel_format", "bgr24", "-video_size", f"{WIDTH}x{HEIGHT}",
                "-framerate", str(FPS), "-i", "-", "-an", "-frames:v", "900",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", str(video_path),
            ], stdin=subprocess.PIPE, stderr=err)
            previous_base: np.ndarray | None = None
            source_cache_frames: dict[str, np.ndarray] = {}
            current_shot: dict[str, Any] | None = None
            rendered = 0
            for frame_no in range(900):
                if frame_no in shot_by_start:
                    current_shot = shot_by_start[frame_no]
                if current_shot is None:
                    raise RuntimeError(f"No shot mapped for output frame {frame_no}")
                sid = current_shot["scene"]
                src = current_shot["source"]
                local = frame_no - int(current_shot["out_start_f"])
                src_idx = int(src["in_frame"]) + min(local, int(src["source_frames"]) - 1)
                cap = caps[sid]
                if last_source_index.get(sid) != src_idx:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, src_idx)
                    ok, raw = cap.read()
                    if not ok:
                        raise RuntimeError(f"Source {sid} ended before required frame {src_idx}")
                    last_source_index[sid] = src_idx
                    source_cache_frames[sid] = raw
                source_cache = source_cache_frames[sid]
                params = current_shot["zoom_curve"]["parameters"]
                ratios = params.get("k_ratio", [1.0, 1.0])
                ratio = float(ratios[0]) + (float(ratios[-1]) - float(ratios[0])) * easing(local / max(1, current_shot["out_frames"] - 1))
                scale = max(1.0, float(current_shot["zoom_curve"]["base"]) * ratio)
                base = zoom_frame(source_cache, scale)
                transition = None
                transition_start = None
                for cut in plan["cuts"]:
                    if cut_map[int(cut["at_f"])] != "TR01" and int(cut["at_f"]) <= frame_no < int(cut["at_f"]) + 6:
                        transition_start = int(cut["at_f"])
                        transition = cut["transition"]
                        break
                if transition:
                    old = previous_base
                    # At the cut frame, retain the last outgoing image for the full 6-frame transition.
                    base = transition_frame(old, base, transition, frame_no - int(transition_start), 6)
                clean_base = base.copy()
                base = draw_overlay(base, frame_no, plan, (overlay_font_mont, overlay_font_jakarta))
                if encoder.stdin is None:
                    raise RuntimeError("FFmpeg encoder pipe is closed")
                encoder.stdin.write(base.tobytes())
                # Keep the outgoing image without graphics for the next cut transition.
                if frame_no == int(current_shot["out_end_f"]) - 1:
                    previous_base = clean_base
                rendered += 1
            encoder.stdin.close()
            result = encoder.wait(timeout=600)
            if result != 0:
                raise RuntimeError(f"FFmpeg encode failed (exit {result}); see {error_log}")
            if rendered != 900:
                raise RuntimeError(f"Renderer emitted {rendered} frames, expected 900")
        for cap in caps.values():
            cap.release()
        if sheet_path:
            create_contact_sheet(video_path, plan, sheet_path)
        return {"frames_written": rendered, "duration_s": rendered / FPS, "audio": False, "video": str(video_path)}
    finally:
        for cap in caps.values():
            cap.release()
        # Temporary normalized footage lives only for the render and is removed afterwards.
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=ROOT / "render_plan.json")
    parser.add_argument("--output", type=Path, default=ROOT / "output" / "output_T1_sans_voix.mp4")
    parser.add_argument("--sheet", type=Path, default=ROOT / "output" / "planche_controle.png")
    args = parser.parse_args()
    result = render_video(args.plan, args.output, args.sheet)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
