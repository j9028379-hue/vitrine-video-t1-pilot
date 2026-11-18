"""Renderer for the approved T1-A "Special Menu" visual architecture.

The implementation is deliberately additive. It does not modify the existing
capture guide, legacy V1.2/V6.2 specs, previous engines, or audio assets.

Core constraints:
- 4 merchant scenes, 900 frames, 30 fps, 720x1280;
- source time stays continuous at 1.0x inside every scene;
- internal edits are zero-duration hard cuts between crop states;
- no crossfades, wipes, glitches, freeze frames, or speech subtitles;
- text is rendered only with bundled TTF files.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def report_path(path: Path) -> str:
    """Use a repo-relative path when possible, otherwise keep the absolute URI/path.

    The reference CLI is also shipped inside the standalone template bundle, so
    caller-owned captures and outputs are allowed to live outside the checkout.
    """
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


@dataclass(frozen=True)
class GradeParameters:
    exposure_gain: float
    gray_world_bgr: tuple[float, float, float]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_fields(raw: dict[str, Any], config: dict[str, Any]) -> dict[str, str]:
    """Apply the locked merchant contract without inventing or truncating text."""
    result: dict[str, str] = {}
    for definition in config["merchant_input_contract"]["fields"]:
        key = definition["id"]
        value = raw.get(key, "")
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise ValueError(f"Le champ {key!r} doit être du texte.")
        value = " ".join(value.strip().split())
        if key in {"nom", "produit", "accroche"}:
            value = value.rstrip(".")
        if definition["required"] and not value:
            raise ValueError(f"Champ obligatoire manquant : {key}")
        if len(value) > definition["max_chars"]:
            raise ValueError(
                f"Champ {key!r} trop long : {len(value)} > {definition['max_chars']} caractères."
            )
        result[key] = value
    return result


def validate_config(config: dict[str, Any]) -> None:
    canvas = config["canvas"]
    if (canvas["width"], canvas["height"], canvas["fps"], canvas["frames"]) != (720, 1280, 30, 900):
        raise ValueError("Le canevas T1 doit rester 720x1280, 30 fps, 900 images.")
    shots = config["edit_timeline"]["shots"]
    cursor = 0
    by_scene: dict[str, list[dict[str, Any]]] = {}
    for shot in shots:
        if shot["out_start_f"] != cursor:
            raise ValueError(f"Trou de timeline avant {shot['id']} : {cursor} != {shot['out_start_f']}")
        if shot["source_speed"] != 1.0 or not shot["source_contiguous"]:
            raise ValueError(f"{shot['id']} viole la continuité de parole.")
        if shot["out_frames"] != shot["source_frames"]:
            raise ValueError(f"{shot['id']} effectue un remappage temporel interdit.")
        if shot["transition_in"] not in {"none", "hard_cut"}:
            raise ValueError(f"Transition non conforme dans {shot['id']}.")
        cursor = shot["out_end_f_exclusive"]
        by_scene.setdefault(shot["scene"], []).append(shot)
    if cursor != 900:
        raise ValueError(f"Timeline incomplète : {cursor}/900 images.")
    for scene, scene_shots in by_scene.items():
        source_cursor = 0
        for shot in scene_shots:
            if shot["source_in_f"] != source_cursor:
                raise ValueError(f"Source non continue dans {scene}/{shot['id']}.")
            source_cursor = shot["source_out_f_exclusive"]
    for key in ("crossfades", "wipes", "glitches", "speed_ramps", "freeze_frames"):
        if config["edit_timeline"][key]:
            raise ValueError(f"{key} doit rester vide pour cette référence.")
    impact = config.get("impact_transition_system")
    if impact and impact.get("enabled"):
        if impact.get("source_time_map") != "identity" or impact.get("audio_time_map") != "identity":
            raise ValueError("Les transitions impact ne doivent jamais remapper la parole.")
        major = impact["major_scene_cuts"]["cut_frames"]
        minor = impact["minor_cuts"]["cut_frames"]
        declared = sorted(config["edit_timeline"]["hard_cut_frames"])
        if sorted(major + minor) != declared:
            raise ValueError("Chaque coupe doit recevoir exactement un profil impact.")
        if major != [180, 420, 630]:
            raise ValueError("Les effets majeurs sont réservés aux trois frontières de scènes.")
        if impact.get("text_layer_affected") is not False:
            raise ValueError("Les effets impact doivent rester derrière le texte net.")
    choreography = config.get("premium_transition_choreography")
    if choreography and choreography.get("enabled"):
        if choreography.get("source_time_map") != "identity" or choreography.get("audio_time_map") != "identity":
            raise ValueError("La chorégraphie premium ne doit jamais remapper la parole.")
        if choreography.get("text_layer_affected") is not False:
            raise ValueError("La chorégraphie doit rester derrière les textes nets.")
        events = choreography["events"]
        cuts = [int(event["cut_f"]) for event in events]
        if sorted(cuts) != sorted(config["edit_timeline"]["hard_cut_frames"]):
            raise ValueError("La chorégraphie doit couvrir chaque coupe exactement une fois.")
        if len(set(cuts)) != len(cuts) or len(set(event["name"] for event in events)) != len(events):
            raise ValueError("Les événements premium doivent être uniques, sans répétition générique.")
        for event in events:
            if event["phase"] == "human":
                if not event.get("face_safe") or event.get("chromatic_shift_px_max", 0) != 0:
                    raise ValueError(f"Effet visage non sûr : {event['name']}")
    for font in config["fonts"].values():
        if not isinstance(font, dict) or "file" not in font:
            continue
        path = ROOT / font["file"]
        if not path.is_file():
            raise FileNotFoundError(f"Police absente : {path}")
        if "sha256" in font:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != font["sha256"]:
                raise ValueError(f"Empreinte de police incorrecte : {path}")


def scene_grade_parameters(path: Path, frame_count: int, stride: int = 15) -> GradeParameters:
    """Measure one fixed grade per scene to prevent exposure/white-balance pumping."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Rush illisible : {path}")
    medians: list[float] = []
    means: list[np.ndarray] = []
    index = 0
    while index < frame_count:
        cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = cap.read()
        if not ok:
            break
        proxy = cv2.resize(frame, (135, 240), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(proxy, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        luma = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
        medians.append(float(np.median(luma)))
        means.append(proxy.reshape(-1, 3).mean(axis=0))  # BGR
        index += stride
    cap.release()
    if not medians:
        raise ValueError(f"Aucune image analysable : {path}")
    median_luma = max(float(np.median(medians)), 0.02)
    exposure = float(np.clip(0.29 / median_luma, 0.82, 1.18))
    channel_means = np.median(np.stack(means), axis=0)
    common = max(float(np.mean(channel_means)), 1.0)
    gray = common / np.maximum(channel_means, 1.0)
    gray = np.clip(gray, 0.94, 1.06)
    return GradeParameters(exposure_gain=exposure, gray_world_bgr=tuple(float(x) for x in gray))


def _filmic_lut(points: Iterable[Iterable[float]], size: int = 4096) -> np.ndarray:
    pts = np.asarray(list(points), dtype=np.float32)
    x = np.linspace(0.0, 1.0, size, dtype=np.float32)
    return np.interp(x, pts[:, 0], pts[:, 1]).astype(np.float32)


def _vignette(height: int, width: int, strength: float) -> np.ndarray:
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    nx = (xx / max(width - 1, 1) - 0.5) / 0.50
    ny = (yy / max(height - 1, 1) - 0.48) / 0.62
    radius = np.sqrt(nx * nx + ny * ny)
    t = np.clip((radius - 0.48) / (0.95 - 0.48), 0.0, 1.0)
    smooth = t * t * (3.0 - 2.0 * t)
    return (1.0 - strength * smooth)[..., None]


def apply_cinematic_grade(
    frame_bgr: np.ndarray,
    params: GradeParameters,
    look: dict[str, Any],
    scene_index: int,
    frame_index: int,
    lut: np.ndarray,
    vignette: np.ndarray,
) -> np.ndarray:
    """Apply the deterministic warm low-key food grade described by the JSON."""
    image = frame_bgr.astype(np.float32) / 255.0
    # BGR gray-world then warm RGB gains expressed here in BGR order.
    image *= np.asarray(params.gray_world_bgr, dtype=np.float32)[None, None, :]
    image *= params.exposure_gain
    image *= np.asarray([0.945, 1.005, 1.055], dtype=np.float32)[None, None, :]
    image = np.clip(image, 0.0, 1.0)

    indices = np.minimum((image * (len(lut) - 1)).astype(np.int32), len(lut) - 1)
    image = lut[indices]

    # Split tone: cool shadows, warm highlights (BGR channel order).
    luma = 0.0722 * image[..., 0] + 0.7152 * image[..., 1] + 0.2126 * image[..., 2]
    shadow = np.clip((0.35 - luma) / 0.35, 0.0, 1.0)[..., None]
    highlight = np.clip((luma - 0.62) / 0.38, 0.0, 1.0)[..., None]
    image *= 1.0 + shadow * (np.asarray([1.018, 1.005, 0.985], np.float32) - 1.0)
    image *= 1.0 + highlight * (np.asarray([0.970, 1.010, 1.030], np.float32) - 1.0)
    image = np.clip(image, 0.0, 1.0)

    # Selective saturation in HSV. OpenCV hue range is 0..179.
    u8 = np.clip(image * 255.0, 0, 255).astype(np.uint8)
    hsv = cv2.cvtColor(u8, cv2.COLOR_BGR2HSV).astype(np.float32)
    hue = hsv[..., 0]
    factor = np.full(hue.shape, 1.06, dtype=np.float32)
    orange_red = (hue <= 24) | (hue >= 170)
    green = (hue >= 35) & (hue <= 88)
    cyan_blue = (hue >= 89) & (hue <= 135)
    factor[orange_red] *= 1.10
    factor[green] *= 0.90
    factor[cyan_blue] *= 0.94
    hsv[..., 1] = np.clip(hsv[..., 1] * factor, 0, 255)
    u8 = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    # Very light local contrast.
    blurred = cv2.GaussianBlur(u8, (0, 0), 1.1)
    sharpened = cv2.addWeighted(u8, 1.12, blurred, -0.12, 0)
    image = sharpened.astype(np.float32) / 255.0
    image *= vignette

    # Deterministic luma-only grain. One noise value affects all three channels.
    rng = np.random.default_rng(scene_index * 100000 + frame_index)
    noise_small = rng.normal(0.0, 0.006, (max(1, image.shape[0] // 4), max(1, image.shape[1] // 4))).astype(np.float32)
    noise = cv2.resize(noise_small, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_CUBIC)[..., None]
    image = np.clip(image + noise, 0.0, 1.0)
    return (image * 255.0 + 0.5).astype(np.uint8)


def ease_in_out_sine(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return -(math.cos(math.pi * t) - 1.0) / 2.0


def crop_zoom(frame: np.ndarray, scale: float, anchor: tuple[float, float]) -> np.ndarray:
    """Crop around a normalized anchor and restore the source dimensions."""
    h, w = frame.shape[:2]
    crop_w = max(2, int(round(w / scale)))
    crop_h = max(2, int(round(h / scale)))
    cx = anchor[0] * w
    cy = anchor[1] * h
    x0 = int(round(cx - crop_w / 2))
    y0 = int(round(cy - crop_h / 2))
    x0 = min(max(x0, 0), max(0, w - crop_w))
    y0 = min(max(y0, 0), max(0, h - crop_h))
    crop = frame[y0 : y0 + crop_h, x0 : x0 + crop_w]
    return cv2.resize(crop, (w, h), interpolation=cv2.INTER_CUBIC)


def _font(path: Path, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(path), int(size))
    if weight is not None and hasattr(font, "set_variation_by_axes"):
        try:
            font.set_variation_by_axes([weight])
        except OSError:
            pass
    return font


def _text_width(text: str, font: ImageFont.FreeTypeFont, tracking_px: float = 0.0) -> float:
    if not text:
        return 0.0
    widths = [font.getlength(char) for char in text]
    return float(sum(widths) + tracking_px * max(0, len(text) - 1))


def _draw_tracking(
    draw: ImageDraw.ImageDraw,
    text: str,
    center_x: float,
    y: float,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    tracking_px: float,
) -> tuple[float, float, float, float]:
    width = _text_width(text, font, tracking_px)
    x = center_x - width / 2.0
    top = y
    for char in text:
        draw.text((x, y), char, font=font, fill=fill)
        x += font.getlength(char) + tracking_px
    bbox = font.getbbox(text or " ")
    return center_x - width / 2.0, top, center_x + width / 2.0, top + (bbox[3] - bbox[1])


def _balanced_split(text: str) -> tuple[str, str] | None:
    words = text.split()
    if len(words) < 2:
        return None
    best: tuple[float, str, str] | None = None
    for index in range(1, len(words)):
        left = " ".join(words[:index])
        right = " ".join(words[index:])
        score = abs(len(left) - len(right))
        candidate = (score, left, right)
        if best is None or candidate < best:
            best = candidate
    assert best is not None
    return best[1], best[2]


def _fit_lines(
    text: str,
    font_path: Path,
    maximum_size: int,
    minimum_size: int,
    maximum_width: int,
    weight: int | None = None,
    allow_two_lines: bool = True,
) -> tuple[list[str], ImageFont.FreeTypeFont]:
    for size in range(maximum_size, minimum_size - 1, -1):
        font = _font(font_path, size, weight)
        if font.getlength(text) <= maximum_width:
            return [text], font
    if allow_two_lines:
        split = _balanced_split(text)
        if split:
            for size in range(maximum_size, minimum_size - 1, -1):
                font = _font(font_path, size, weight)
                if max(font.getlength(split[0]), font.getlength(split[1])) <= maximum_width:
                    return [split[0], split[1]], font
    raise ValueError(f"Texte impossible à faire tenir sans troncature : {text!r}")


def _hex_rgba(value: str, alpha: int = 255) -> tuple[int, int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), alpha


def _reveal(layer: Image.Image, progress: float) -> Image.Image:
    progress = min(max(progress, 0.0), 1.0)
    if progress >= 1.0:
        return layer
    array = np.asarray(layer).copy()
    alpha = array[..., 3]
    ys, xs = np.nonzero(alpha)
    if len(xs) == 0:
        return layer
    left, right = int(xs.min()), int(xs.max()) + 1
    threshold = int(round(left + progress * (right - left)))
    if threshold < array.shape[1]:
        array[:, threshold:, 3] = 0
    return Image.fromarray(array, mode="RGBA")


def _soft_scrim(frame: np.ndarray, center_y: float, strength: float, sigma_y: float, sigma_x: float = 0.65) -> np.ndarray:
    """Feathered elliptical darkening; never creates a hard-edged card."""
    h, w = frame.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xx / max(w - 1, 1) - 0.5) / sigma_x
    ny = (yy / max(h - 1, 1) - center_y) / sigma_y
    mask = np.exp(-0.5 * (nx * nx + ny * ny))
    multiplier = 1.0 - strength * mask[..., None]
    return np.clip(frame.astype(np.float32) * multiplier, 0, 255).astype(np.uint8)


def _display_price(value: str) -> tuple[str, str]:
    """Return a grouped number and currency without mutating merchant data.

    Numeric values are grouped from the right (``2500`` -> ``2 500``). The
    renderer then keeps number + currency in one non-breaking visual lockup.
    Non-numeric merchant strings are preserved verbatim after whitespace
    normalization.
    """
    clean = " ".join(value.replace("\u00a0", " ").replace("\u202f", " ").strip().split())
    upper = clean.upper()
    if upper.endswith("FCFA"):
        clean = clean[:-4].strip()
    compact = clean.replace(" ", "")
    if compact.isdigit():
        groups: list[str] = []
        while compact:
            groups.append(compact[-3:])
            compact = compact[:-3]
        clean = " ".join(reversed(groups))
    return clean, "FCFA"


def _new_layer(width: int, height: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    return layer, ImageDraw.Draw(layer)


def render_graphics(
    frame_bgr: np.ndarray,
    frame_index: int,
    fields: dict[str, str],
    config: dict[str, Any],
) -> np.ndarray:
    """Render all active sparse editorial graphics for one output frame."""
    h, w = frame_bgr.shape[:2]
    font_cfg = config["fonts"]
    display_path = ROOT / font_cfg["display_serif"]["file"]
    sans_path = ROOT / font_cfg["light_sans"]["file"]
    utility_path = ROOT / font_cfg["utility"]["file"]
    ivory = _hex_rgba("#FBF7EE")
    secondary = _hex_rgba("#EDE4D5", 220)

    active_ids = {
        g["id"] for g in config["graphics"] if g["start_f"] <= frame_index < g["end_f_exclusive"]
    }
    if {"G01_HERO", "G01_LABEL"} & active_ids:
        frame_bgr = _soft_scrim(frame_bgr, 0.31, 0.18, 0.19)
    if "G02_PRICE" in active_ids:
        frame_bgr = _soft_scrim(frame_bgr, 0.73, 0.20, 0.18)
    if "G03_HOOK" in active_ids and fields.get("accroche"):
        frame_bgr = _soft_scrim(frame_bgr, 0.26, 0.18, 0.20)
    if "G04_LOCATION" in active_ids:
        frame_bgr = _soft_scrim(frame_bgr, 0.27, 0.20, 0.22)
    if "G05_CTA" in active_ids:
        frame_bgr = _soft_scrim(frame_bgr, 0.68, 0.28, 0.30)

    base = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
    layer, draw = _new_layer(w, h)

    # Opening hero: same sparse two-family lockup as "Special / Menu".
    if "G01_HERO" in active_ids:
        lines, display_font = _fit_lines(fields["produit"], display_path, 84, 52, int(w * 0.78), allow_two_lines=True)
        bbox_height = display_font.getbbox("Ag")[3] - display_font.getbbox("Ag")[1]
        line_height = int(round(bbox_height * 0.96))
        start_y = int(h * 0.238)
        for offset, line in enumerate(lines):
            width = display_font.getlength(line)
            draw.text(((w - width) / 2, start_y + offset * line_height), line, font=display_font, fill=ivory)
        # FreeType's visible serif bbox is taller than its cap-height. Keep a
        # deliberate editorial gap so the light line never touches the hero.
        label_y = start_y + len(lines) * max(line_height, int(display_font.size * 0.96)) + 20
        sans_font = _font(sans_path, 35, 300)
        _draw_tracking(draw, "PLAT DU JOUR", w / 2, label_y, sans_font, ivory, 35 * 0.15)
        progress = (frame_index - 4) / 20.0
        layer = _reveal(layer, progress)

    if "G01_MICRO" in active_ids:
        micro_layer, micro_draw = _new_layer(w, h)
        font = _font(sans_path, 12, 300)
        _draw_tracking(micro_draw, fields["nom"], w / 2, int(h * 0.845), font, secondary, 1.2)
        layer = Image.alpha_composite(layer, micro_layer)

    if "G02_PRICE" in active_ids:
        main, suffix = _display_price(fields["prix"])
        price_layer, price_draw = _new_layer(w, h)
        price_font = _font(display_path, 86)
        util = _font(utility_path, 28, 700)
        price_spec = next(g for g in config["graphics"] if g["id"] == "G02_PRICE")
        single_line = price_spec.get("layout", {}).get("mode") == "single_line_baseline"
        if single_line:
            gap = int(price_spec["layout"].get("number_currency_gap_px", 18))
            suffix_w = util.getlength(suffix)
            while price_font.getlength(main) + gap + suffix_w > w * 0.82 and price_font.size > 58:
                price_font = _font(display_path, price_font.size - 1)
            main_w = price_font.getlength(main)
            total_w = main_w + gap + suffix_w
            start_x = (w - total_w) / 2
            baseline = int(h * float(price_spec["layout"].get("baseline_y", 0.72)))
            # ``ls`` anchors both fonts to the same baseline: a clear protected
            # gap replaces the former stacked/overlapping currency label.
            price_draw.text((start_x, baseline), main, font=price_font, fill=ivory, anchor="ls")
            price_draw.text(
                (start_x + main_w + gap, baseline),
                suffix,
                font=util,
                fill=secondary,
                anchor="ls",
            )
        else:
            while price_font.getlength(main) > w * 0.72 and price_font.size > 58:
                price_font = _font(display_path, price_font.size - 1)
            main_w = price_font.getlength(main)
            y = int(h * 0.66)
            price_draw.text(((w - main_w) / 2, y), main, font=price_font, fill=ivory)
            suffix_w = util.getlength(suffix)
            price_draw.text(((w - suffix_w) / 2, y + int(price_font.size * 0.92)), suffix, font=util, fill=secondary)
        progress = (frame_index - 184) / 20.0
        layer = Image.alpha_composite(layer, _reveal(price_layer, progress))

    if "G03_HOOK" in active_ids and fields.get("accroche"):
        hook_layer, hook_draw = _new_layer(w, h)
        hook_text = fields["accroche"]
        # Long all-caps hooks look weak when squeezed onto one line. Prefer a
        # semantic separator split, then a balanced split, before shrinking.
        segments = [part.strip() for part in hook_text.replace("•", "·").split("·") if part.strip()]
        if len(segments) == 3:
            split = (f"{segments[0]} · {segments[1]}", segments[2])
        elif len(segments) == 2:
            split = (segments[0], segments[1])
        else:
            split = _balanced_split(hook_text) if len(hook_text) > 22 else None
        if split:
            lines = list(split)
            font = _font(display_path, 58)
            while max(font.getlength(line) for line in lines) > w * 0.78 and font.size > 44:
                font = _font(display_path, font.size - 1)
        else:
            lines, font = _fit_lines(hook_text, display_path, 58, 44, int(w * 0.78), allow_two_lines=True)
        line_height = int(font.size * 0.96)
        y = int(h * 0.18)
        for offset, line in enumerate(lines):
            width = font.getlength(line)
            hook_draw.text(((w - width) / 2, y + offset * line_height), line, font=font, fill=ivory)
        progress = (frame_index - 304) / 20.0
        layer = Image.alpha_composite(layer, _reveal(hook_layer, progress))

    if "G04_LOCATION" in active_ids:
        loc_layer, loc_draw = _new_layer(w, h)
        lines, font = _fit_lines(fields["nom"], display_path, 62, 42, int(w * 0.80), allow_two_lines=True)
        y = int(h * 0.205)
        line_height = int(font.size * 0.92)
        for offset, line in enumerate(lines):
            width = font.getlength(line)
            loc_draw.text(((w - width) / 2, y + offset * line_height), line, font=font, fill=ivory)
        secondary_y = y + len(lines) * line_height + 14
        secondary_font = _font(sans_path, 24, 300)
        tracking = 2.4
        location_text = fields["quartier"]
        # The locked data contract already permits a semantic split on a
        # separator. Use it instead of shrinking an address to microscopic type.
        location_lines: list[str]
        if "—" in location_text:
            location_lines = [part.strip() for part in location_text.split("—", 1)]
        elif "," in location_text:
            location_lines = [part.strip() for part in location_text.split(",", 1)]
        else:
            balanced = _balanced_split(location_text) if len(location_text) > 24 else None
            location_lines = list(balanced) if balanced else [location_text]
        while max(_text_width(line, secondary_font, tracking) for line in location_lines) > w * 0.80 and secondary_font.size > 20:
            secondary_font = _font(sans_path, secondary_font.size - 1, 300)
            tracking = secondary_font.size * 0.10
        for offset, location_line in enumerate(location_lines):
            _draw_tracking(
                loc_draw,
                location_line,
                w / 2,
                secondary_y + offset * int(secondary_font.size * 1.25),
                secondary_font,
                secondary,
                tracking,
            )
        progress = (frame_index - 634) / 21.0
        layer = Image.alpha_composite(layer, _reveal(loc_layer, progress))

    if "G05_CTA" in active_ids:
        cta_layer, cta_draw = _new_layer(w, h)
        cta_spec = next(g for g in config["graphics"] if g["id"] == "G05_CTA")
        mirror_opening = cta_spec.get("layout", {}).get("mode") == "mirror_opening"
        if mirror_opening:
            # Final resolution reuses the exact opening hierarchy: merchant
            # product in DM Serif, tracked Montserrat action line, then utility
            # information. There is no second visual identity, border, or card.
            y = int(h * float(cta_spec["layout"].get("top_y", 0.49)))
            lines, product_font = _fit_lines(
                fields["produit"], display_path, 84, 52, int(w * 0.78), allow_two_lines=True
            )
            line_height = int(product_font.size * 0.96)
            for offset, line in enumerate(lines):
                line_w = product_font.getlength(line)
                cta_draw.text(((w - line_w) / 2, y + offset * line_height), line, font=product_font, fill=ivory)
            label_y = y + len(lines) * line_height + 20
            label_font = _font(sans_path, 35, 300)
            _draw_tracking(
                cta_draw,
                "COMMANDER MAINTENANT",
                w / 2,
                label_y,
                label_font,
                ivory,
                35 * 0.15,
            )

            price_main, suffix = _display_price(fields["prix"])
            price_text = f"{price_main} {suffix}"
            price_font = _font(utility_path, 26, 700)
            price_w = price_font.getlength(price_text)
            support_y = label_y + 62
            cta_draw.text(((w - price_w) / 2, support_y), price_text, font=price_font, fill=secondary)

            phone_font = _font(utility_path, 34, 700)
            phone_w = phone_font.getlength(fields["whatsapp"])
            total_w = 20 + 12 + phone_w
            start_x = (w - total_w) / 2
            green = _hex_rgba("#25D366")
            cta_draw.ellipse((start_x, support_y + 57, start_x + 20, support_y + 77), fill=green)
            cta_draw.text((start_x + 32, support_y + 44), fields["whatsapp"], font=phone_font, fill=ivory)

            name_font = _font(sans_path, 13, 300)
            _draw_tracking(cta_draw, fields["nom"], w / 2, support_y + 112, name_font, secondary, 1.3)
            reveal_frames = int(cta_spec.get("animation", {}).get("reveal_frames", 20))
            progress = (frame_index - 810) / max(reveal_frames, 1)
        else:
            y = int(h * 0.535)
            headline = "Commander"
            head_font = _font(display_path, 72)
            head_w = head_font.getlength(headline)
            cta_draw.text(((w - head_w) / 2, y), headline, font=head_font, fill=ivory)
            sans = _font(sans_path, 24, 300)
            _draw_tracking(cta_draw, "MAINTENANT", w / 2, y + 82, sans, ivory, 24 * 0.13)

            price_main, _ = _display_price(fields["prix"])
            offer = f"{fields['produit']}  ·  {price_main} FCFA"
            util_small = _font(utility_path, 22, 700)
            while util_small.getlength(offer) > w * 0.80 and util_small.size > 16:
                util_small = _font(utility_path, util_small.size - 1, 700)
            offer_w = util_small.getlength(offer)
            cta_draw.text(((w - offer_w) / 2, y + 132), offer, font=util_small, fill=secondary)

            phone_font = _font(utility_path, 34, 700)
            phone_w = phone_font.getlength(fields["whatsapp"])
            total_w = 20 + 12 + phone_w
            start_x = (w - total_w) / 2
            green = _hex_rgba("#25D366")
            cta_draw.ellipse((start_x, y + 183, start_x + 20, y + 203), fill=green)
            cta_draw.text((start_x + 32, y + 170), fields["whatsapp"], font=phone_font, fill=ivory)

            name_font = _font(sans_path, 13, 300)
            _draw_tracking(cta_draw, fields["nom"], w / 2, y + 240, name_font, secondary, 1.3)
            progress = (frame_index - 810) / 22.0
        layer = Image.alpha_composite(layer, _reveal(cta_layer, progress))

    composed = Image.alpha_composite(base, layer).convert("RGB")
    return cv2.cvtColor(np.asarray(composed), cv2.COLOR_RGB2BGR)


def impact_transition_state(config: dict[str, Any], frame_index: int) -> dict[str, Any] | None:
    """Return a non-temporal cut treatment for one output frame.

    V3 uses an event-by-event choreography. V2 falls back to its two generic
    profiles. Neither mode changes the source or audio clock.
    """
    choreography = config.get("premium_transition_choreography")
    if choreography and choreography.get("enabled"):
        for event in choreography["events"]:
            cut = int(event["cut_f"])
            pre = int(event["pre_frames"])
            post = int(event["post_frames"])
            start, end = cut - pre, cut + post
            if not start <= frame_index < end:
                continue
            if frame_index < cut:
                phase = "outgoing"
                intensity = (frame_index - start + 1) / max(pre, 1)
            else:
                phase = "incoming"
                intensity = 1.0 - (frame_index - cut) / max(post, 1)
            return {
                "kind": "choreographed",
                "name": event["name"],
                "narrative_phase": event["phase"],
                "profile": event,
                "cut_f": cut,
                "phase": phase,
                "intensity": float(np.clip(intensity, 0.0, 1.0)),
                "window_progress": float(np.clip((frame_index - start) / max(end - start - 1, 1), 0.0, 1.0)),
                "direction": int(event.get("direction", 0)),
            }
        return None

    system = config.get("impact_transition_system")
    if not system or not system.get("enabled"):
        return None
    profiles = (("major", system["major_scene_cuts"]), ("minor", system["minor_cuts"]))
    for kind, profile in profiles:
        for index, cut in enumerate(profile["cut_frames"]):
            pre, post = int(profile["pre_frames"]), int(profile["post_frames"])
            start, end = cut - pre, cut + post
            if not start <= frame_index < end:
                continue
            if frame_index < cut:
                phase = "outgoing"
                intensity = (frame_index - start + 1) / max(pre, 1)
            else:
                phase = "incoming"
                intensity = 1.0 - (frame_index - cut) / max(post, 1)
            if kind == "major":
                direction = 1 if profile["directions_by_cut"].get(str(cut), "right") == "right" else -1
            else:
                direction = 1 if index % 2 == 0 else -1
            return {
                "kind": kind,
                "profile": profile,
                "cut_f": cut,
                "phase": phase,
                "intensity": float(np.clip(intensity, 0.0, 1.0)),
                "window_progress": float(np.clip((frame_index - start) / max(end - start - 1, 1), 0.0, 1.0)),
                "direction": direction,
            }
    return None


def _translate_reflect(frame: np.ndarray, dx: float) -> np.ndarray:
    matrix = np.float32([[1.0, 0.0, dx], [0.0, 1.0, 0.0]])
    return cv2.warpAffine(
        frame,
        matrix,
        (frame.shape[1], frame.shape[0]),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT_101,
    )


def _directional_blur(frame: np.ndarray, pixels: int, direction: int) -> np.ndarray:
    if pixels <= 0:
        return frame
    samples = 5
    accumulator = np.zeros_like(frame, dtype=np.float32)
    weights = np.asarray([0.10, 0.17, 0.26, 0.27, 0.20], dtype=np.float32)
    for sample, weight in zip(np.linspace(0.0, pixels, samples), weights):
        accumulator += _translate_reflect(frame, direction * float(sample)).astype(np.float32) * weight
    return np.clip(accumulator, 0, 255).astype(np.uint8)


def _chromatic_shift(frame: np.ndarray, pixels: int, direction: int) -> np.ndarray:
    if pixels <= 0:
        return frame
    blue, green, red = cv2.split(frame)
    red = _translate_reflect(red, direction * pixels)
    blue = _translate_reflect(blue, -direction * pixels)
    return cv2.merge((blue, green, red))


def apply_impact_transition(frame: np.ndarray, state: dict[str, Any] | None) -> np.ndarray:
    """Premium zoom/whip/flash treatment applied to background video only."""
    if state is None:
        return frame
    profile = state["profile"]
    intensity = state["intensity"]
    direction = state["direction"]
    phase_sign = 1 if state["phase"] == "outgoing" else -1

    translation_max = float(profile.get("translation_px_max", 0.0))
    if translation_max and direction:
        frame = _translate_reflect(frame, phase_sign * direction * translation_max * intensity)

    blur_px = int(round(float(profile.get("directional_blur_px_max", 0)) * intensity))
    if direction:
        frame = _directional_blur(frame, blur_px, phase_sign * direction)

    softness = float(profile.get("gaussian_softness_px_max", 0.0)) * intensity
    if softness > 0.05:
        softened = cv2.GaussianBlur(frame, (0, 0), max(softness, 0.1))
        soft_mix = min(0.62, 0.42 + 0.20 * intensity)
        frame = cv2.addWeighted(frame, 1.0 - soft_mix, softened, soft_mix, 0)

    chromatic_px = int(round(float(profile.get("chromatic_shift_px_max", 0)) * intensity))
    if direction:
        frame = _chromatic_shift(frame, chromatic_px, direction)

    image = frame.astype(np.float32)
    bloom_alpha = float(profile.get("highlight_bloom_alpha_max", 0.0)) * intensity
    if bloom_alpha:
        luma = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        highlights = np.clip((luma - 150.0) / 105.0, 0.0, 1.0)
        highlights = cv2.GaussianBlur(highlights, (0, 0), 6.0)[..., None]
        warm_white = np.asarray([205.0, 235.0, 255.0], dtype=np.float32)
        alpha = bloom_alpha * highlights
        image = image * (1.0 - alpha) + warm_white[None, None, :] * alpha

    flash_alpha = float(profile.get("warm_flash_alpha_max", 0.0)) * intensity
    if flash_alpha:
        amber_bgr = np.asarray([58.0, 174.0, 255.0], dtype=np.float32)
        image = image * (1.0 - flash_alpha) + amber_bgr[None, None, :] * flash_alpha

    sweep_alpha = float(profile.get("gold_light_sweep_alpha_max", 0.0))
    if sweep_alpha:
        h, w = frame.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        nx = xx / max(w - 1, 1)
        ny = yy / max(h - 1, 1)
        orientation = profile.get("sweep_orientation", "diagonal_forward")
        progress = state["window_progress"]
        if orientation == "horizontal":
            coordinate, extent = nx, 1.0
            if direction < 0:
                progress = 1.0 - progress
        elif orientation == "vertical":
            coordinate, extent = ny, 1.0
        elif orientation == "diagonal_reverse":
            coordinate, extent = (1.0 - nx) + 0.62 * ny, 1.62
        else:
            coordinate, extent = nx + 0.62 * ny, 1.62
        center = -0.18 + (extent + 0.36) * progress
        band = np.exp(-0.5 * ((coordinate - center) / 0.10) ** 2)[..., None]
        gold = np.asarray([80.0, 196.0, 255.0], dtype=np.float32)
        alpha = sweep_alpha * band * (0.45 + 0.55 * intensity)
        image = image * (1.0 - alpha) + gold[None, None, :] * alpha
    return np.clip(image, 0, 255).astype(np.uint8)


def find_shot(config: dict[str, Any], frame_index: int) -> dict[str, Any]:
    for shot in config["edit_timeline"]["shots"]:
        if shot["out_start_f"] <= frame_index < shot["out_end_f_exclusive"]:
            return shot
    raise IndexError(f"Aucun plan pour l'image {frame_index}")


def render_project(
    config_path: Path,
    input_path: Path,
    media_dir: Path,
    output_path: Path,
    contact_sheet_path: Path | None = None,
) -> dict[str, Any]:
    config = load_json(config_path)
    validate_config(config)
    fields = normalize_fields(load_json(input_path), config)
    canvas = config["canvas"]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        float(canvas["fps"]),
        (canvas["width"], canvas["height"]),
    )
    if not writer.isOpened():
        raise RuntimeError("Impossible d'ouvrir l'encodeur MP4V OpenCV.")

    look = config["look_pipeline"]
    filmic_points = next(step["points"] for step in look["steps"] if step["op"] == "filmic_curve")
    lut = _filmic_lut(filmic_points)
    samples: list[tuple[int, np.ndarray]] = []
    frames_written = 0
    scene_reports: list[dict[str, Any]] = []

    try:
        for scene_index, scene in enumerate(config["scene_capture_contract"]["scenes"]):
            scene_id = scene["id"]
            source = media_dir / f"{scene_id}.mp4"
            grade = scene_grade_parameters(source, scene["frames"])
            cap = cv2.VideoCapture(str(source))
            if not cap.isOpened():
                raise FileNotFoundError(f"Rush absent ou illisible : {source}")
            source_fps = cap.get(cv2.CAP_PROP_FPS)
            if abs(source_fps - canvas["fps"]) > 0.01:
                raise ValueError(f"{scene_id} est à {source_fps} fps au lieu de 30 fps.")
            source_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if source_frames < scene["frames"]:
                raise ValueError(f"{scene_id} ne contient que {source_frames}/{scene['frames']} images.")

            local_index = 0
            vignette: np.ndarray | None = None
            while local_index < scene["frames"]:
                ok, frame = cap.read()
                if not ok:
                    raise ValueError(f"Lecture interrompue dans {scene_id} à l'image {local_index}.")
                global_index = scene["start_f"] + local_index
                shot = find_shot(config, global_index)
                shot_t = (global_index - shot["out_start_f"]) / max(shot["out_frames"] - 1, 1)
                eased = ease_in_out_sine(shot_t)
                impact_state = impact_transition_state(config, global_index)
                scale = shot["zoom"]["start"] + (shot["zoom"]["end"] - shot["zoom"]["start"]) * eased
                if impact_state is not None:
                    scale *= 1.0 + float(impact_state["profile"].get("zoom_extra", 0.0)) * impact_state["intensity"]
                frame = crop_zoom(frame, scale, tuple(shot["anchor_normalized"]))
                if vignette is None or vignette.shape[:2] != frame.shape[:2]:
                    vignette = _vignette(frame.shape[0], frame.shape[1], 0.16)
                frame = apply_cinematic_grade(frame, grade, look, scene_index, local_index, lut, vignette)
                frame = apply_impact_transition(frame, impact_state)
                frame = cv2.resize(frame, (canvas["width"], canvas["height"]), interpolation=cv2.INTER_CUBIC)

                # Reproduce the 8-frame outro darkening on video only. CTA stays opaque.
                if global_index >= 892:
                    progress = (global_index - 892 + 1) / 8.0
                    frame = np.clip(frame.astype(np.float32) * (1.0 - 0.34 * progress), 0, 255).astype(np.uint8)
                frame = render_graphics(frame, global_index, fields, config)
                writer.write(frame)
                if global_index % 60 == 0:
                    samples.append((global_index, frame.copy()))
                frames_written += 1
                local_index += 1
            cap.release()
            scene_reports.append(
                {
                    "scene": scene_id,
                    "frames": scene["frames"],
                    "source": report_path(source),
                    "source_fps": source_fps,
                    "grade": {
                        "exposure_gain": round(grade.exposure_gain, 6),
                        "gray_world_bgr": [round(x, 6) for x in grade.gray_world_bgr],
                    },
                }
            )
    finally:
        writer.release()

    if frames_written != canvas["frames"]:
        raise RuntimeError(f"Rendu incomplet : {frames_written}/{canvas['frames']} images.")
    if contact_sheet_path is not None:
        make_contact_sheet(samples, contact_sheet_path)

    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    return {
        "renderer":"engine.special_menu_style.render_project",
        "config":report_path(config_path),
        "input":report_path(input_path),
        "output":report_path(output_path),
        "width":canvas["width"],
        "height":canvas["height"],
        "fps":canvas["fps"],
        "frames":frames_written,
        "duration_s":frames_written / canvas["fps"],
        "audio":False,
        "impact_transitions": {
            "generic_v2_enabled": bool(config.get("impact_transition_system", {}).get("enabled")),
            "choreography_v3_enabled": bool(config.get("premium_transition_choreography", {}).get("enabled")),
            "event_names": [
                event["name"] for event in config.get("premium_transition_choreography", {}).get("events", [])
            ],
            "source_time_map": config.get("premium_transition_choreography", config.get("impact_transition_system", {})).get("source_time_map", "identity"),
        },
        "sha256":digest,
        "bytes":output_path.stat().st_size,
        "scenes":scene_reports,
    }


def make_contact_sheet(samples: list[tuple[int, np.ndarray]], path: Path) -> None:
    if not samples:
        return
    thumb_w, thumb_h = 180, 320
    cells: list[np.ndarray] = []
    for frame_index, frame in samples:
        thumb = cv2.resize(frame, (thumb_w, thumb_h), interpolation=cv2.INTER_AREA)
        cv2.rectangle(thumb, (0, 0), (thumb_w, 24), (8, 8, 8), -1)
        cv2.putText(
            thumb,
            f"f{frame_index:03d}  {frame_index / 30:.1f}s",
            (5, 17),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 240, 190),
            1,
            cv2.LINE_AA,
        )
        cells.append(thumb)
    columns = 5
    rows = math.ceil(len(cells) / columns)
    while len(cells) < rows * columns:
        cells.append(np.zeros((thumb_h, thumb_w, 3), dtype=np.uint8))
    board = np.vstack([np.hstack(cells[row * columns : (row + 1) * columns]) for row in range(rows)])
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), board, [cv2.IMWRITE_JPEG_QUALITY, 92]):
        raise RuntimeError(f"Impossible d'écrire la planche : {path}")
