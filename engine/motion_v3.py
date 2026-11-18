"""V3 typographic and ergonomic finish, preserving the V2 edit for the locked T1 template. Diagnostic imagery is never composited."""
from __future__ import annotations

import json
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
W, H, FPS, FRAMES = 720, 1280, 30, 900
SOURCE_WINDOWS = {"S2": (0.0, 0.76)}  # discard the late take where a hand occludes the lens
INK = (12, 19, 31)
CREAM = (255, 248, 239)
ORANGE = (245, 111, 49)
GREEN = (31, 177, 111)
WHITE = (255, 255, 255)
SAFE = (44, 613, 160, 960)  # scaled from the locked V6.2 zones to 720x1280


def ease(t: float) -> float:
    t = max(0.0, min(1.0, float(t)))
    return t * t * t * (t * (t * 6 - 15) + 10)


def out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, float(t)))
    return 1.0 - (1.0 - t) ** 3


def source_progress(scene_id: str, progress: float) -> float:
    progress = max(0.0, min(1.0, float(progress)))
    # Gentle ease-speed-ease on the burger preparation beat; derivative stays positive.
    if scene_id == "S2":
        progress += 0.06 * math.sin(2 * math.pi * progress)
    return max(0.0, min(1.0, progress))


def font(path: Path, size: int, weight: str) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(path), size=size)
    try:
        f.set_variation_by_name(weight)
    except (AttributeError, OSError):
        pass
    return f


def box_text(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont) -> tuple[int, int, int, int]:
    return draw.textbbox((0, 0), text, font=f, stroke_width=0)


def draw_center(draw: ImageDraw.ImageDraw, x: float, y: float, text: str,
                f: ImageFont.FreeTypeFont, fill: tuple[int, ...], anchor: str = "mm") -> None:
    draw.text((int(round(x)), int(round(y))), text, font=f, fill=fill, anchor=anchor)


def draw_left(draw: ImageDraw.ImageDraw, x: float, y: float, text: str,
              f: ImageFont.FreeTypeFont, fill: tuple[int, ...]) -> None:
    draw.text((int(round(x)), int(round(y))), text, font=f, fill=fill, anchor="lt")


def gradient_overlay(frame: np.ndarray) -> np.ndarray:
    # Controlled top/bottom vignettes put every line of type on a deliberate contrast bed.
    y = np.arange(H, dtype=np.float32)
    top = np.clip(1.0 - y / 500.0, 0.0, 1.0) ** 1.7 * 0.56
    bottom = np.clip((y - 700.0) / 580.0, 0.0, 1.0) ** 1.25 * 0.57
    alpha = np.maximum(top, bottom)[:, None, None]
    return np.clip(frame.astype(np.float32) * (1.0 - alpha), 0, 255).astype(np.uint8)


def camera_move(frame: np.ndarray, local: int, duration: int, shot_index: int) -> np.ndarray:
    p = ease(local / max(1, duration - 1))
    # Deliberate varied Ken Burns moves; crop remains inside frame (no blank edges).
    start = 1.015 + 0.006 * (shot_index % 3)
    end = 1.085 if shot_index % 2 == 0 else 1.035
    scale = start + (end - start) * p
    h, w = frame.shape[:2]
    cw, ch = int(w / scale), int(h / scale)
    phase = math.sin(math.pi * p)
    dx = ((shot_index % 4) - 1.5) * 0.018 * phase
    dy = (((shot_index + 1) % 3) - 1) * 0.013 * phase
    cx, cy = w * (0.5 + dx), h * (0.5 + dy)
    # Keep the planned camera path continuous at sub-pixel precision instead of
    # quantizing crop origins to integers (which can create isolated duplicate frames).
    cx = max(cw / 2.0, min(w - cw / 2.0, cx))
    cy = max(ch / 2.0, min(h - ch / 2.0, cy))
    crop = cv2.getRectSubPix(frame, (cw, ch), (float(cx), float(cy)))
    return cv2.resize(crop, (w, h), interpolation=cv2.INTER_LANCZOS4)


def transition(old: np.ndarray, new: np.ndarray, kind: str, p: float) -> np.ndarray:
    """12-frame scene transitions; all transforms are edge-filled, never black."""
    p = ease(p)
    if kind == "whip_pan":
        mat_old = np.float32([[1, 0, -int(W * p)], [0, 1, 0]])
        mat_new = np.float32([[1, 0, int(W * (1.0 - p))], [0, 1, 0]])
        a = cv2.warpAffine(old, mat_old, (W, H), borderMode=cv2.BORDER_REFLECT_101)
        b = cv2.warpAffine(new, mat_new, (W, H), borderMode=cv2.BORDER_REFLECT_101)
        seam = int(W * (1.0 - p))
        mask = np.tile((np.arange(W) >= seam).astype(np.float32), (H, 1))
        feather = max(1, int(8 + 18 * math.sin(math.pi * p)))
        mask = cv2.GaussianBlur(mask, (feather * 2 + 1, 1), 0)[:, :, None]
        out = (a.astype(np.float32) * (1 - mask) + b.astype(np.float32) * mask).astype(np.uint8)
        blur = max(0, int(28 * math.sin(math.pi * p)))
        if blur >= 3:
            out = cv2.GaussianBlur(out, (blur * 2 + 1, 1), 0)
        return out
    if kind == "directional_push":
        a_scale = 1.0 + 0.035 * p
        b_scale = 1.08 - 0.08 * p
        def transformed(img: np.ndarray, scale: float, tx: float) -> np.ndarray:
            mat = cv2.getRotationMatrix2D((W / 2, H / 2), 0, scale)
            mat[0, 2] += tx
            return cv2.warpAffine(img, mat, (W, H), borderMode=cv2.BORDER_REFLECT_101)
        a = transformed(old, a_scale, -W * p)
        b = transformed(new, b_scale, W * (1 - p))
        seam = int(W * (1.0 - p))
        mask = np.tile((np.arange(W) >= seam).astype(np.float32), (H, 1))
        mask = cv2.GaussianBlur(mask, (25, 1), 0)[:, :, None]
        return (a.astype(np.float32) * (1 - mask) + b.astype(np.float32) * mask).astype(np.uint8)
    # Brand-signature diagonal reveal, with a narrow orange leading ribbon.
    edge = int(-550 + 1300 * p)
    yy, xx = np.mgrid[0:H, 0:W]
    signed = xx - 0.42 * yy
    mask = signed <= edge
    out = old.copy()
    out[mask] = new[mask]
    ribbon = (np.abs(signed - edge) < 13) & ~mask
    out[ribbon] = np.array(ORANGE[::-1], dtype=np.uint8)  # OpenCV frames are BGR; preserve the brand's warm orange.
    return out


def round_card(layer: Image.Image, box: tuple[int, int, int, int], radius: int,
               fill: tuple[int, int, int, int], outline: tuple[int, int, int, int] | None = None,
               width: int = 1) -> None:
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def line_reveal(draw: ImageDraw.ImageDraw, x0: int, y: int, x1: int, p: float,
                color: tuple[int, int, int, int], width: int = 5) -> None:
    draw.rounded_rectangle((x0, y, int(x0 + (x1 - x0) * ease(p)), y + width), radius=width // 2, fill=color)


def fit_font(draw: ImageDraw.ImageDraw, text: str, path: Path, max_size: int, min_size: int, width: int, weight: str) -> ImageFont.FreeTypeFont:
    size = max_size
    while size > min_size:
        f = font(path, size, weight)
        if draw.textbbox((0, 0), text, font=f)[2] <= width:
            return f
        size -= 1
    return font(path, min_size, weight)


def render_graphics(base: np.ndarray, fno: int, plan: dict[str, Any], mont: Path, jakarta: Path) -> np.ndarray:
    data = plan["display"]
    im = Image.fromarray(cv2.cvtColor(base, cv2.COLOR_BGR2RGB)).convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    name = data["nom"].upper()
    product = data["produit"].upper()
    price = data["prix"].upper()
    tagline = data["accroche"].replace("·", "•").upper()
    location = data["quartier"].upper()
    contact = data["whatsapp"].upper()

    # Scene 1: food-first opening, with a compact brand signature and a two-beat product title.
    if 0 <= fno < 177:
        t = fno
        p_brand = out_cubic((t - 2) / 11)
        if t >= 2:
            bx = int(58 - 38 * (1 - p_brand))
            by = int(172 + 8 * (1 - p_brand))
            round_card(layer, (bx, by, bx + 264, by + 54), 24, (*INK, 212))
            d.ellipse((bx + 11, by + 10, bx + 43, by + 42), fill=(*ORANGE, 255))
            draw_center(d, bx + 27, by + 26, "V", font(jakarta, 22, "ExtraBold"), WHITE)
            brand_f = fit_font(d, name, mont, 21, 20, 204, "Bold")
            draw_left(d, bx + 55, by + 14, name, brand_f, (*CREAM, 255))
        for i, word in enumerate(product.split()):
            start = 13 + i * 7
            q = out_cubic((t - start) / 12)
            if q > 0:
                y = 260 + i * 82 + int((1 - q) * 26)
                size = 78 if len(word) < 11 else 67
                d.text((58, y), word, font=font(mont, size, "ExtraBold"), fill=(*CREAM, int(255 * q)),
                       stroke_width=1, stroke_fill=(INK[0], INK[1], INK[2], int(90 * q)))
        line_reveal(d, 61, 443, 485, (t - 26) / 14, (*ORANGE, 255), 6)
        if t >= 31:
            q = min(out_cubic((t - 31) / 10), ease((176 - t) / 12))
            draw_left(d, 61, 472 + int((1 - q) * 10), "PLAT DU JOUR", font(jakarta, 23, "Bold"), (*CREAM, int(242 * q)))
        if t >= 116:
            q = min(out_cubic((t - 116) / 9), ease((176 - t) / 10))
            round_card(layer, (58, 847, 455, 913), 28, (*INK, int(220 * q)))
            tag_f = fit_font(d, tagline, jakarta, 22, 20, 360, "Bold")
            draw_left(d, 77, 868, tagline, tag_f, (*CREAM, int(255 * q)))

    # Scene 2: preserve the three-beat copy, but compose it asymmetrically with varied entries.
    if 172 <= fno < 417:
        local = fno - 180
        words = [w.strip() for w in tagline.replace("•", "·").split("·") if w.strip()][:3]
        # One soft-edged, angled contrast field under the whole typography composition (not three cards).
        if local >= 4:
            panel_q = out_cubic((local - 4) / 12) * ease((239 - local) / 14)
            panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            pd = ImageDraw.Draw(panel)
            pd.polygon([(46, 185), (385, 174), (532, 226), (495, 506), (50, 522)], fill=(*INK, int(106 * panel_q)))
            panel = panel.filter(ImageFilter.GaussianBlur(7))
            layer = Image.alpha_composite(layer, panel)
            d = ImageDraw.Draw(layer)
            # A single orange corner stroke cues the composition; word-specific bars carry the rhythm.
            d.line((61, 207, 136, 201), fill=(*ORANGE, int(225 * panel_q)), width=4)
        layout = [
            {"xy": (68, 225), "size": 56, "entry": (-58, 18), "accent": "underline"},
            {"xy": (121, 318), "size": 62, "entry": (48, -18), "accent": "side"},
            {"xy": (73, 418), "size": 46, "entry": (-30, 24), "accent": "long"},
        ]
        for i, word in enumerate(words):
            start = 12 + i * 53
            q = out_cubic((local - start) / 12) * ease((239 - local) / 12)
            if q <= 0:
                continue
            spec = layout[i]
            x0, y0 = spec["xy"]
            ex, ey = spec["entry"]
            entry = out_cubic((local - start) / 12)
            x = int(x0 + ex * (1 - entry))
            y = int(y0 + ey * (1 - entry))
            max_width = 440 if i == 2 else 390
            f = fit_font(d, word, mont, spec["size"], 40, max_width, "ExtraBold")
            d.text((x + 2, y + 3), word, font=f, fill=(0, 0, 0, int(92 * q)), stroke_width=2, stroke_fill=(0, 0, 0, int(92 * q)))
            d.text((x, y), word, font=f, fill=(*CREAM, int(255 * q)), stroke_width=1, stroke_fill=(*INK, int(105 * q)))
            bb = d.textbbox((0, 0), word, font=f)
            word_w = bb[2] - bb[0]
            if spec["accent"] == "underline":
                line_reveal(d, x + 2, y + bb[3] - bb[1] + 10, x + min(word_w + 12, 260), (local - start - 2) / 13, (*ORANGE, int(255 * q)), 5)
            elif spec["accent"] == "side":
                bar_h = int((bb[3] - bb[1] + 8) * ease((local - start - 3) / 11))
                d.rounded_rectangle((x - 16, y + 4, x - 10, y + 4 + bar_h), radius=3, fill=(*ORANGE, int(245 * q)))
            else:
                line_start = x + 12
                line_reveal(d, line_start, y + bb[3] - bb[1] + 9, x + word_w - 4, (local - start - 3) / 14, (*ORANGE, int(255 * q)), 5)

    # Scene 3: price remains the visual anchor; the product label is now comfortably readable.
    if 410 <= fno < 627:
        local = fno - 420
        if local >= 42:
            q = out_cubic((local - 42) / 12) * ease((163 - local) / 12)
            scale = 0.94 + 0.075 * out_cubic((local - 42) / 10) - 0.015 * ease((local - 52) / 9)
            cx, cy = 332, 572
            w, h = int(448 * scale), int(162 * scale)
            x0, y0 = cx - w // 2, cy - h // 2
            shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(shadow)
            sd.rounded_rectangle((x0 + 3, y0 + 8, x0 + w + 3, y0 + h + 8), radius=32, fill=(0, 0, 0, int(72 * q)))
            shadow = shadow.filter(ImageFilter.GaussianBlur(8))
            layer = Image.alpha_composite(layer, shadow)
            d = ImageDraw.Draw(layer)
            round_card(layer, (x0, y0, x0 + w, y0 + h), 32, (*ORANGE, int(248 * q)), (*CREAM, int(230 * q)), 2)
            d = ImageDraw.Draw(layer)
            label_f = fit_font(d, product, jakarta, 25, 23, w - 62, "Bold")
            draw_center(d, cx, y0 + 39, product, label_f, (*CREAM, int(255 * q)))
            d.line((x0 + 44, y0 + 68, x0 + w - 44, y0 + 68), fill=(255, 248, 239, int(92 * q)), width=2)
            price_f = fit_font(d, price, mont, 64, 48, w - 54, "ExtraBold")
            draw_center(d, cx, y0 + 115, price, price_f, (*INK, int(255 * q)))
            sweep = int(x0 + (w + 24) * ease((local - 50) / 13))
            if local < 66:
                glint_alpha = int(70 * max(0.0, 1 - abs(58 - local) / 16) * q)
                d.line((sweep - 22, y0 + 15, sweep + 8, y0 + h - 15), fill=(255, 255, 255, glint_alpha), width=4)

    # Scene 4: two-line location card, followed by a restrained dark CTA (green only identifies WhatsApp).
    if 620 <= fno < FRAMES:
        local = fno - 630
        if local >= 12:
            q = out_cubic((local - 12) / 14)
            bx, by = 70, 613 + int((1 - q) * 16)
            round_card(layer, (bx, by, 602, by + 134), 26, (*INK, int(226 * q)), (*CREAM, int(58 * q)), 1)
            d = ImageDraw.Draw(layer)
            d.rounded_rectangle((bx, by + 24, bx + 5, by + 110), radius=2, fill=(*ORANGE, int(255 * q)))
            # Clean, recognizable map pin, not a decorative glyph.
            pin_x, pin_y = bx + 40, by + 43
            d.ellipse((pin_x - 11, pin_y - 13, pin_x + 11, pin_y + 9), fill=(*ORANGE, int(255 * q)))
            d.polygon([(pin_x - 9, pin_y + 3), (pin_x + 9, pin_y + 3), (pin_x, pin_y + 23)], fill=(*ORANGE, int(255 * q)))
            d.ellipse((pin_x - 4, pin_y - 6, pin_x + 4, pin_y + 2), fill=(*CREAM, int(255 * q)))
            if "—" in location:
                place, detail = [s.strip() for s in location.split("—", 1)]
            elif "-" in location:
                place, detail = [s.strip() for s in location.split("-", 1)]
            else:
                place, detail = location, ""
            place_f = fit_font(d, place, mont, 28, 24, 420, "Bold")
            draw_left(d, bx + 78, by + 25, place, place_f, (*CREAM, int(255 * q)))
            if detail:
                detail_f = fit_font(d, detail, jakarta, 22, 20, 420, "Medium")
                draw_left(d, bx + 78, by + 73, detail, detail_f, (*CREAM, int(230 * q)))

        if local >= 110:
            q = out_cubic((local - 110) / 12)
            # Smaller footprint and no fake icon: typography carries the WhatsApp action.
            bx, by, bw, bh = 76, 777, 526, 130
            scale = 0.985 + 0.015 * out_cubic((local - 110) / 10)
            bw2, bh2 = int(bw * scale), int(bh * scale)
            x0 = bx + (bw - bw2) // 2
            y0 = by + (bh - bh2) // 2 + int((1 - q) * 13)
            round_card(layer, (x0, y0, x0 + bw2, y0 + bh2), 28, (*INK, int(232 * q)), (*CREAM, int(65 * q)), 1)
            d = ImageDraw.Draw(layer)
            d.rounded_rectangle((x0 + 22, y0 + 22, x0 + 27, y0 + 108), radius=2, fill=(*GREEN, int(255 * q)))
            draw_center(d, x0 + bw2 // 2 + 8, y0 + 34, "COMMANDER SUR", font(jakarta, 21, "Bold"), (*CREAM, int(245 * q)))
            draw_center(d, x0 + bw2 // 2 + 8, y0 + 68, "WHATSAPP", font(mont, 31, "ExtraBold"), (44, 207, 126, int(255 * q)))
            d.rounded_rectangle((x0 + bw2 // 2 - 58, y0 + 89, x0 + bw2 // 2 + 74, y0 + 93), radius=2, fill=(44, 207, 126, int(210 * q)))
            if contact:
                contact_f = fit_font(d, contact, jakarta, 20, 20, bw2 - 64, "Bold")
                draw_center(d, x0 + bw2 // 2 + 8, y0 + 111, contact, contact_f, (*CREAM, int(245 * q)))
        if local >= 145:
            q = out_cubic((local - 145) / 12)
            end_f = fit_font(d, name + " · DÉMO FICTIVE", jakarta, 20, 20, 500, "Bold")
            draw_center(ImageDraw.Draw(layer), 336, 937, name + " · DÉMO FICTIVE", end_f, (*CREAM, int(238 * q)))

    # Retain the V2 pre-cut fade, but keep the footage transitions themselves unchanged.
    if 168 <= fno < 177:
        fade = ease((177 - fno) / 9.0)
        alpha = layer.getchannel("A").point(lambda value: int(value * fade))
        layer.putalpha(alpha)
    if layer.getchannel("A").getbbox():
        im = Image.alpha_composite(im, layer)
    return cv2.cvtColor(np.asarray(im.convert("RGB")), cv2.COLOR_RGB2BGR)


def get_scene_frame(scene_i: int, scene_local: int, plan: dict[str, Any], caps: dict[str, cv2.VideoCapture],
                    source_counts: dict[str, int]) -> np.ndarray:
    scene = plan["scenes"][scene_i]
    sid = scene["id"]
    scene_shots = [s for s in plan["shots"] if s["scene"] == sid]
    start = min(s["out_start_f"] for s in scene_shots)
    local = max(0, min(int(scene["frames"]) - 1, int(scene_local)))
    global_frame = start + local
    shot = next((s for s in scene_shots if s["out_start_f"] <= global_frame < s["out_end_f"]), scene_shots[-1])
    shot_idx = int(shot["id"].replace("P", "")) - 1
    win0, win1 = SOURCE_WINDOWS.get(sid, (0.0, 1.0))
    first = int(round(max(0, source_counts[sid] - 1) * win0))
    last = int(round(max(0, source_counts[sid] - 1) * win1))
    progress = local / max(1, int(scene["frames"]) - 1)
    eased_progress = source_progress(sid, progress)
    idx = first + int(round(eased_progress * max(0, last - first)))
    cap = caps[sid]
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, raw = cap.read()
    if not ok:
        raise RuntimeError(f"Could not decode {sid} frame {idx}")
    return camera_move(raw, global_frame - int(shot["out_start_f"]), int(shot["out_frames"]), shot_idx)


def scene_boundaries(plan: dict[str, Any]) -> list[int]:
    cumulative = 0
    result = []
    for s in plan["scenes"][:-1]:
        cumulative += int(s["frames"])
        result.append(cumulative)
    return result


def create_sheet(video: Path, plan: dict[str, Any], dest: Path) -> None:
    cap = cv2.VideoCapture(str(video))
    moments = [0, 30, 75, 150, 174, 180, 186, 240, 360, 414, 420, 426, 510, 624, 630, 636, 720, 780, 840, 899]
    thumbs = []
    for n in moments:
        cap.set(cv2.CAP_PROP_POS_FRAMES, n)
        ok, fr = cap.read()
        if ok:
            im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).resize((160, 284), Image.Resampling.LANCZOS)
            tile = Image.new("RGB", (176, 310), (12, 17, 29))
            tile.paste(im, (8, 6))
            ImageDraw.Draw(tile).text((8, 292), f"{n:03d}f · {n/FPS:05.2f}s", fill=WHITE)
            thumbs.append(tile)
    cap.release()
    cols = 5
    sheet = Image.new("RGB", (cols * 176 + (cols + 1) * 10, math.ceil(len(thumbs) / cols) * 310 + (math.ceil(len(thumbs) / cols) + 1) * 10), (5, 9, 17))
    for i, tile in enumerate(thumbs):
        sheet.paste(tile, (10 + (i % cols) * 176, 10 + (i // cols) * 310))
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest, optimize=True)


def render(plan_path: Path, output: Path, sheet: Path | None = None) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    expected = {"width": 720, "height": 1280, "fps": 30, "frames": 900, "duration_s": 30.0, "audio": False}
    if plan.get("output") != expected or [int(s["frames"]) for s in plan["scenes"]] != [180, 240, 210, 270]:
        raise ValueError("V3 renderer accepts only the locked four-scene, silent 900-frame T1 contract")
    if len(plan["shots"]) != 12 or list(plan["fields"].keys()) != ["nom", "produit", "prix", "whatsapp", "quartier", "accroche"]:
        raise ValueError("T1 field/shot contract changed")
    from engine.fetch_rushes import ensure_rushes
    ensure_rushes()
    tmp = Path(tempfile.mkdtemp(prefix="t1-v2-"))
    caps: dict[str, cv2.VideoCapture] = {}
    counts: dict[str, int] = {}
    try:
        normalized_by_source: dict[str, Path] = {}
        for scene in plan["scenes"]:
            shot = next(s for s in plan["shots"] if s["scene"] == scene["id"])
            source = ROOT / shot["source"]["file"]
            source_key = str(shot["source"]["sha256"])
            if source_key not in normalized_by_source:
                normalized = tmp / f"{scene['id']}.mp4"
                filt = "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,eq=saturation=1.12:contrast=1.06:brightness=0.006"
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source), "-an", "-vf", filt, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", "-pix_fmt", "yuv420p", str(normalized)], check=True)
                normalized_by_source[source_key] = normalized
            normalized = normalized_by_source[source_key]
            cap = cv2.VideoCapture(str(normalized))
            if not cap.isOpened():
                raise RuntimeError(f"Normalized clip unavailable: {scene['id']}")
            caps[scene["id"]] = cap
            counts[scene["id"]] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        mont = ROOT / "assets/fonts/Montserrat-Variable.ttf"
        jakarta = ROOT / "assets/fonts/PlusJakartaSans-Variable.ttf"
        cuts = scene_boundaries(plan)
        transition_kinds = {cuts[0]: "whip_pan", cuts[1]: "directional_push", cuts[2]: "mask_reveal"}
        kinds = list(transition_kinds.items())
        output.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pixel_format", "bgr24", "-video_size", f"{W}x{H}", "-framerate", str(FPS), "-i", "-", "-an", "-frames:v", str(FRAMES), "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)], stdin=subprocess.PIPE)
        if proc.stdin is None:
            raise RuntimeError("FFmpeg pipe not opened")
        for fno in range(FRAMES):
            # Scene boundaries use 12-frame designed transitions; internal shot changes are clean, fast cuts.
            trans = next(((cut, kind) for cut, kind in kinds if cut - 4 <= fno < cut + 8), None)
            if trans:
                cut, kind = trans
                i = cuts.index(cut)
                prev_scene, next_scene = i, i + 1
                k = fno - (cut - 4)
                old_local = min(int(plan["scenes"][prev_scene]["frames"]) - 1,
                                int(plan["scenes"][prev_scene]["frames"]) - 4 + k)
                new_local = max(0, k - 4)
                old = get_scene_frame(prev_scene, old_local, plan, caps, counts)
                new = get_scene_frame(next_scene, new_local, plan, caps, counts)
                bg = transition(old, new, kind, k / 11.0)
            else:
                cumulative = 0
                scene_i = 0
                while scene_i < len(plan["scenes"]) - 1 and fno >= cumulative + int(plan["scenes"][scene_i]["frames"]):
                    cumulative += int(plan["scenes"][scene_i]["frames"])
                    scene_i += 1
                bg = get_scene_frame(scene_i, fno - cumulative, plan, caps, counts)
            bg = gradient_overlay(bg)
            # The final frame path composes only authored commercial graphics. Diagnostic layers are not an input.
            final = render_graphics(bg, fno, plan, mont, jakarta)
            if final.shape != (H, W, 3):
                raise RuntimeError(f"Bad rendered frame shape at {fno}: {final.shape}")
            proc.stdin.write(final.tobytes())
        proc.stdin.close()
        if proc.wait(timeout=900) != 0:
            raise RuntimeError("FFmpeg V3 encode failed")
        for c in caps.values():
            c.release()
        if sheet:
            create_sheet(output, plan, sheet)
        from engine.review_sheets import create_review_sheets
        timeline_sheet, transition_sheet = create_review_sheets(output, output.parent, cuts, suffix="v3")
        return {"frames": FRAMES, "duration_s": 30.0, "fps": FPS, "width": W, "height": H, "audio": False, "video": str(output), "scene_transitions": {str(c): k for c, k in transition_kinds.items()}, "full_timeline_sheet": str(timeline_sheet), "transition_frames_sheet": str(transition_sheet)}
    finally:
        for c in caps.values():
            c.release()
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="Render V3 typographic/art-direction finish; preserves V2 footage and transitions")
    p.add_argument("--plan", type=Path, default=ROOT / "render_plan.json")
    p.add_argument("--output", type=Path, default=ROOT / "output/output_T1_sans_voix_v3.mp4")
    p.add_argument("--sheet", type=Path, default=ROOT / "output/planche_controle_v3.png")
    a = p.parse_args()
    print(json.dumps(render(a.plan, a.output, a.sheet), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
