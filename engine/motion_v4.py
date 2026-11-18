"""Moteur de montage T1 **piloté par le plan** — remplace les valeurs codées en dur de `motion_v3_1.py`.

Différences avec `motion_v3_1.py` (conservé intact comme référence visuelle approuvée) :

| Élément | V3.1 | ce moteur |
|---|---|---|
| Fenêtre source | progression sur la scène entière + `SOURCE_WINDOWS` codé en dur | `shot.source.in_frame` / `out_frame` / `freeze_tail_f` du plan |
| Mouvement caméra | recalculé à partir de l'index du plan | `shot.zoom_curve.movement_id` + `parameters` du plan (k_ratio, pan_px, easing, dur_f, base) |
| Transitions | 3 types codés en dur aux positions 180 / 420 / 630 | `plan["cuts"][i].transition` → bibliothèque V1.2 (TR01…TR05), durées de la spec |
| Graphismes | fenêtres d'images codées dans le code | `plan["overlays"]` (GB01…GB08 : start_f / end_f) |
| Éléments non déclarés | titre produit géant en scène 1, pastille accroche non déclarée | aucun : seuls les 8 blocs déclarés sont dessinés |

Chaîne réelle : 4 vidéos → normalisation ffmpeg (même étalonnage) → sélection de la fenêtre source du plan
→ recadrage caméra du plan → transition du plan → vignettage → blocs graphiques du plan → assemblage H.264.

    PYTHONPATH=. python3 engine/motion_v4.py --plan render_plan_v4_demo.json \
        --output output/output_T1_master_final.mp4 \
        --manifest reports/execution_manifest_v4.json
"""
from __future__ import annotations

import json
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H, FPS, FRAMES = 720, 1280, 30, 900
INK = (12, 19, 31)
CREAM = (255, 248, 239)
ORANGE = (245, 111, 49)
GREEN = (31, 177, 111)

# Bibliothèque de transitions V1.2 (durées de la spécification, en images)
TRANSITIONS = {
    "TR01": {"nom": "cut_sec", "dur_f": 0, "rendu": "cut"},
    "TR02": {"nom": "punch_cut", "dur_f": 6, "rendu": "punch_cut"},
    "TR03": {"nom": "wipe_geometrique", "dur_f": 6, "rendu": "wipe_diagonale"},
    "TR04": {"nom": "wipe_directionnel", "dur_f": 6, "rendu": "wipe_directionnel"},
    "TR05": {"nom": "fondu_court_crossfade", "dur_f": 6, "rendu": "fondu"},
    "TR06": {"nom": "speed_ramp_entrant", "dur_f": 6, "rendu": "punch_cut"},
    "TR07": {"nom": "match_cut", "dur_f": 0, "rendu": "cut"},
    "TR08": {"nom": "mask_reveal", "dur_f": 7, "rendu": "wipe_diagonale"},  # hors pilote V1.2
}


# --------------------------------------------------------------------------- #
# easing
def clamp01(t: float) -> float:
    return max(0.0, min(1.0, float(t)))


def ease_inout_quad(t: float) -> float:
    t = clamp01(t)
    return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2


def ease_out_cubic(t: float) -> float:
    t = clamp01(t)
    return 1 - pow(1 - t, 3)


def ease_out_quint(t: float) -> float:
    t = clamp01(t)
    return 1 - pow(1 - t, 5)


def ease_out_expo(t: float) -> float:
    t = clamp01(t)
    return 1.0 if t >= 1 else 1 - pow(2, -10 * t)


def ease_smooth(t: float) -> float:
    t = clamp01(t)
    return t * t * t * (t * (t * 6 - 15) + 10)


EASINGS = {
    "linear": lambda t: clamp01(t),
    "easeInOutQuad": ease_inout_quad,
    "easeOutCubic": ease_out_cubic,
    "easeOutQuint": ease_out_quint,
    "easeOutExpo": ease_out_expo,
    "easeOutBack": ease_out_cubic,
}


def easing(name: str | None):
    return EASINGS.get(name or "linear", EASINGS["linear"])


# --------------------------------------------------------------------------- #
# typographie
def font(path: Path, size: int, weight: str) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(path), size=size)
    try:
        f.set_variation_by_name(weight)
    except (AttributeError, OSError):
        pass
    return f


def fit_font(draw, text: str, path: Path, max_size: int, min_size: int, width: int, weight: str):
    size = max_size
    while size > min_size:
        f = font(path, size, weight)
        if draw.textbbox((0, 0), text, font=f)[2] <= width:
            return f
        size -= 1
    return font(path, min_size, weight)


def round_card(layer, box, radius, fill, outline=None, width=1):
    ImageDraw.Draw(layer).rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def gradient_overlay(frame: np.ndarray) -> np.ndarray:
    y = np.arange(H, dtype=np.float32)
    top = np.clip(1.0 - y / 500.0, 0.0, 1.0) ** 1.7 * 0.56
    bottom = np.clip((y - 700.0) / 580.0, 0.0, 1.0) ** 1.25 * 0.57
    alpha = np.maximum(top, bottom)[:, None, None]
    return np.clip(frame.astype(np.float32) * (1.0 - alpha), 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------- #
# caméra pilotée par le plan
def camera_move(frame: np.ndarray, local: int, duration: int, shot: dict[str, Any]) -> np.ndarray:
    """Applique EXACTEMENT le mouvement déclaré dans le plan pour ce plan."""
    curve = shot["zoom_curve"]
    params = curve.get("parameters") or {}
    mid = curve.get("movement_id", "")
    base = float(curve.get("base", 1.0))
    prog = clamp01(local / max(1, duration - 1))
    e = easing(params.get("easing"))(prog)

    zoom = 1.0
    dx = dy = 0.0

    k_ratio = params.get("k_ratio")
    if k_ratio:
        k0, k1 = float(k_ratio[0]), float(k_ratio[1])
        if mid == "MV03":                     # push_in_rapide : attaque courte puis maintien
            attack = clamp01(local / max(1, int(params.get("dur_f", 6))))
            e = ease_out_quint(attack)
        zoom = k0 + (k1 - k0) * e

    pan = params.get("pan_px")
    if pan:
        p0, p1 = float(pan[0]), float(pan[1])
        delta = p0 + (p1 - p0) * e
        if mid == "MV06":
            dy = delta / H
        else:
            dx = delta / W

    scale = base * zoom
    scale = max(1.0, scale)
    cw, ch = int(round(W / scale)), int(round(H / scale))
    cx = W * (0.5 + dx)
    cy = H * (0.5 + dy)
    x0 = int(max(0, min(W - cw, cx - cw / 2)))
    y0 = int(max(0, min(H - ch, cy - ch / 2)))
    crop = frame[y0:y0 + ch, x0:x0 + cw]
    return cv2.resize(crop, (W, H), interpolation=cv2.INTER_LANCZOS4)


# --------------------------------------------------------------------------- #
# transitions de la bibliothèque V1.2
def do_transition(old: np.ndarray, new: np.ndarray, kind: str, p: float) -> np.ndarray:
    p = clamp01(p)
    if kind == "punch_cut":
        e = ease_out_quint(p)
        scale = 0.94 + 0.06 * e
        m = cv2.getRotationMatrix2D((W / 2, H / 2), 0, scale)
        incoming = cv2.warpAffine(new, m, (W, H), borderMode=cv2.BORDER_REFLECT_101)
        a = e
        return cv2.addWeighted(incoming, a, old, 1 - a, 0)
    if kind == "wipe_diagonale":
        e = ease_inout_quad(p)
        edge = int(-550 + 1300 * e)
        yy, xx = np.mgrid[0:H, 0:W]
        signed = xx - 0.42 * yy
        out = old.copy()
        mask = signed <= edge
        out[mask] = new[mask]
        ribbon = (np.abs(signed - edge) < 13) & ~mask
        out[ribbon] = np.array(ORANGE[::-1], dtype=np.uint8)
        return out
    if kind == "wipe_directionnel":
        e = ease_inout_quad(p)
        mat_old = np.float32([[1, 0, -int(W * e)], [0, 1, 0]])
        mat_new = np.float32([[1, 0, int(W * (1.0 - e))], [0, 1, 0]])
        a = cv2.warpAffine(old, mat_old, (W, H), borderMode=cv2.BORDER_REFLECT_101)
        b = cv2.warpAffine(new, mat_new, (W, H), borderMode=cv2.BORDER_REFLECT_101)
        seam = int(W * (1.0 - e))
        mask = np.tile((np.arange(W) >= seam).astype(np.float32), (H, 1))
        feather = max(1, int(8 + 18 * math.sin(math.pi * e)))
        mask = cv2.GaussianBlur(mask, (feather * 2 + 1, 1), 0)[:, :, None]
        return (a.astype(np.float32) * (1 - mask) + b.astype(np.float32) * mask).astype(np.uint8)
    # fondu
    e = ease_inout_quad(p)
    return cv2.addWeighted(new, e, old, 1 - e, 0)


# --------------------------------------------------------------------------- #
# blocs graphiques pilotés par plan["overlays"]
def build_windows(plan: dict[str, Any]) -> dict[str, tuple[int, int]]:
    return {o["graphic_block"]: (int(o["start_f"]), int(o["end_f"])) for o in plan["overlays"]}


def render_graphics(base: np.ndarray, fno: int, plan: dict[str, Any], windows: dict[str, tuple[int, int]],
                    mont: Path, jakarta: Path) -> tuple[np.ndarray, list[str]]:
    data = plan["display"]
    im = Image.fromarray(cv2.cvtColor(base, cv2.COLOR_BGR2RGB)).convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    actifs: list[str] = []

    name = data["nom"].upper()
    product = data["produit"].upper()
    price = data["prix"].upper()
    tagline = data["accroche"].replace("·", "•").upper()
    location = data["quartier"].upper()
    contact = data["whatsapp"].upper()

    def win(block: str) -> tuple[int, int] | None:
        w = windows.get(block)
        if not w:
            return None
        return w if w[0] <= fno < w[1] else None

    def q_in_out(local: int, duration: int, din: int = 6, dout: int = 8) -> float:
        return min(ease_out_expo(local / max(1, din)), ease_smooth((duration - local) / max(1, dout)))

    # ---- GB01 : enseigne, mot à mot (MD-T1-01) --------------------------------
    if (w := win("GB01")):
        start, end = w
        local = fno - start
        duration = end - start
        q = q_in_out(local, duration)
        bx = int(58 - 38 * (1 - ease_out_expo(local / 8)))
        by = int(172 + 8 * (1 - ease_out_expo(local / 8)))
        round_card(layer, (bx, by, bx + 264, by + 54), 24, (*INK, int(212 * q)))
        d.ellipse((bx + 11, by + 10, bx + 43, by + 42), fill=(*ORANGE, int(255 * q)))
        brand_f = fit_font(d, name, mont, 21, 18, 204, "Bold")
        for i, word in enumerate(name.split()):
            qw = ease_out_expo((local - i * 5) / 8)
            if qw > 0:
                x = bx + 55 + (i * 96)
                d.text((x, by + 14 + int((1 - qw) * 8)), word, font=brand_f,
                       fill=(*CREAM, int(255 * qw * q)))
        actifs.append("GB01 nom (enseigne mot à mot)")

    # ---- GB02 : bandeau produit (MD-T1-03) ------------------------------------
    # Rendu identique à la DA V3.1 approuvée : titre produit empilé mot à mot, filet orange,
    # sur-titre « PLAT DU JOUR ». Seule la fenêtre (start_f/end_f) vient du plan.
    if (w := win("GB02")):
        start, end = w
        local = fno - start
        duration = end - start
        q_out = ease_smooth((duration - local) / 10)
        for i, word in enumerate(product.split()):
            qw = ease_out_cubic((local - i * 7) / 12) * q_out
            if qw > 0:
                y = 260 + i * 82 + int((1 - ease_out_cubic((local - i * 7) / 12)) * 26)
                size = 78 if len(word) < 11 else 67
                d.text((58, y), word, font=font(mont, size, "ExtraBold"),
                       fill=(*CREAM, int(255 * qw)),
                       stroke_width=1, stroke_fill=(*INK, int(90 * qw)))
        rule_p = clamp01((local - 13) / 14) * q_out
        if rule_p > 0:
            d.rounded_rectangle((61, 443, int(61 + (485 - 61) * ease_out_cubic(rule_p)), 449), radius=3,
                                fill=(*ORANGE, int(255 * q_out)))
        if local >= 18:
            qs = ease_out_cubic((local - 18) / 10) * q_out
            d.text((61, 472), "PLAT DU JOUR", font=font(jakarta, 23, "Bold"), fill=(*CREAM, int(242 * qs)))
        actifs.append("GB02 bandeau produit")

    # ---- GB03 : lockup produit + prix (MD-T1-04 / MD-T1-05) -------------------
    if (w := win("GB03")):
        start, end = w
        local = fno - start
        duration = end - start
        q = q_in_out(local, duration, 6, 8)
        scale = 0.94 + 0.075 * ease_out_cubic(local / 10) - 0.015 * ease_smooth((local - 10) / 9)
        cx, cy = 336, 620
        bw, bh = int(520 * scale), int(268 * scale)
        x0, y0 = cx - bw // 2, cy - bh // 2
        round_card(layer, (x0, y0, x0 + bw, y0 + bh), 28, (*INK, int(224 * q)), (*CREAM, int(60 * q)), 1)
        d.rounded_rectangle((x0 + 24, y0 + 26, x0 + 30, y0 + bh - 26), radius=3, fill=(*ORANGE, int(255 * q)))
        lf = fit_font(d, product, jakarta, 27, 22, bw - 70, "Bold")
        d.text((x0 + 52, y0 + 26), product, font=lf, fill=(*CREAM, int(240 * q)))
        d.line((x0 + 52, y0 + 74, x0 + bw - 40, y0 + 74), fill=(*ORANGE, int(190 * q)), width=2)
        prf = fit_font(d, price, mont, 78, 52, bw - 70, "ExtraBold")
        d.text((x0 + 52, y0 + 96), price, font=prf, fill=(*CREAM, int(255 * q)))
        actifs.append("GB03 lockup produit + prix")

    # ---- GB04 : accroche en segments (MD-T1-06) -------------------------------
    if (w := win("GB04")):
        start, end = w
        local = fno - start
        duration = end - start
        q = q_in_out(local, duration, 6, 10)
        words = [x.strip() for x in tagline.replace("•", "·").split("·") if x.strip()][:3]
        lift = int((1 - ease_out_expo(local / 8)) * 14)
        round_card(layer, (52, 205 + lift, 586, 551 + lift), 24, (*INK, int(198 * q)))
        d.rounded_rectangle((70, 239 + lift, 75, 516 + lift), radius=2, fill=(*ORANGE, int(255 * q)))
        primary = font(mont, 62, "ExtraBold")
        secondary = fit_font(d, words[2] if len(words) > 2 else "", mont, 43, 36, 430, "Bold")
        for i, (word, y, f) in enumerate(((words[0] if words else "CHAUD", 238, primary),
                                          (words[1] if len(words) > 1 else "SERVI", 324, primary),
                                          (words[2] if len(words) > 2 else "AUJOURD’HUI", 420, secondary))):
            qs = ease_out_expo((local - i * 4) / 9)
            if qs > 0:
                d.text((105, y + lift + int((1 - qs) * 10)), word, font=f,
                       fill=(*CREAM, int(255 * qs * q)))
        actifs.append("GB04 accroche segmentée")

    # ---- GB05 : rappel de l'enseigne (MD-T1-07) -------------------------------
    if (w := win("GB05")):
        start, end = w
        local = fno - start
        duration = end - start
        q = q_in_out(local, duration, 6, 8)
        bx = int(58 - 26 * (1 - ease_out_cubic(local / 8)))
        round_card(layer, (bx, 168, bx + 264, 222), 24, (*INK, int(210 * q)))
        d.ellipse((bx + 11, 178, bx + 43, 210), fill=(*ORANGE, int(255 * q)))
        bf = fit_font(d, name, mont, 21, 17, 204, "Bold")
        d.text((bx + 55, 182), name, font=bf, fill=(*CREAM, int(255 * q)))
        actifs.append("GB05 rappel enseigne")

    # ---- GB06 : prix plein écran (MD-T1-08) -----------------------------------
    if (w := win("GB06")):
        start, end = w
        local = fno - start
        duration = end - start
        q = q_in_out(local, duration, 6, 8)
        scale = 0.94 + 0.075 * ease_out_cubic(local / 10)
        cx, cy = 336, 572
        bw, bh = int(448 * scale), int(162 * scale)
        x0, y0 = cx - bw // 2, cy - bh // 2
        round_card(layer, (x0, y0, x0 + bw, y0 + bh), 26, (*INK, int(238 * q)), (*CREAM, int(70 * q)), 1)
        d.rounded_rectangle((x0 + 22, y0 + 24, x0 + 28, y0 + bh - 24), radius=3, fill=(*ORANGE, int(255 * q)))
        lf = fit_font(d, product, jakarta, 25, 20, bw - 62, "Bold")
        d.text((x0 + 48, y0 + 26), product, font=lf, fill=[(*CREAM, int(238 * q))][0])
        d.line((x0 + 48, y0 + 68, x0 + bw - 36, y0 + 68), fill=(*ORANGE, int(185 * q)), width=2)
        prf = fit_font(d, price, mont, 64, 46, bw - 54, "ExtraBold")
        d.text((x0 + 48, y0 + 84), price, font=prf, fill=[(*CREAM, int(255 * q))][0])
        actifs.append("GB06 prix plein écran")

    # ---- GB07 : adresse + épingle (MD-T1-09) ----------------------------------
    if (w := win("GB07")):
        start, end = w
        local = fno - start
        duration = end - start
        q = q_in_out(local, duration, 7, 9)
        bx, by = 70, 613 + int((1 - ease_out_expo(local / 9)) * 16)
        round_card(layer, (bx, by, 602, by + 134), 26, (*INK, int(226 * q)), (*CREAM, int(58 * q)), 1)
        pin_x, pin_y = bx + 40, by + 43
        d.ellipse((pin_x - 11, pin_y - 13, pin_x + 11, pin_y + 9), fill=(*ORANGE, int(255 * q)))
        d.polygon([(pin_x - 9, pin_y + 3), (pin_x + 9, pin_y + 3), (pin_x, pin_y + 23)], fill=(*ORANGE, int(255 * q)))
        d.ellipse((pin_x - 4, pin_y - 6, pin_x + 4, pin_y + 2), fill=(*CREAM, int(255 * q)))
        if "—" in location:
            place, detail = [s.strip() for s in location.split("—", 1)]
        else:
            place, detail = location, ""
        pf = fit_font(d, place, mont, 28, 22, 420, "Bold")
        d.text((bx + 78, by + 25), place, font=pf, fill=(*CREAM, int(255 * q)))
        if detail:
            df = fit_font(d, detail, jakarta, 22, 18, 420, "Medium")
            d.text((bx + 78, by + 73), detail, font=df, fill=(*CREAM, int(230 * q)))
        actifs.append("GB07 adresse + épingle")

    # ---- GB08 : CTA WhatsApp (MD-T1-10) ---------------------------------------
    if (w := win("GB08")):
        start, end = w
        local = fno - start
        duration = end - start
        q = q_in_out(local, duration, 8, 6)
        scale = 0.985 + 0.015 * ease_out_cubic(local / 10)
        bx, by, bw, bh = 76, 777, 526, 130
        bw2, bh2 = int(bw * scale), int(bh * scale)
        x0 = bx + (bw - bw2) // 2
        y0 = by + (bh - bh2) // 2 + int((1 - ease_out_expo(local / 9)) * 13)
        round_card(layer, (x0, y0, x0 + bw2, y0 + bh2), 28, (*INK, int(232 * q)), (*CREAM, int(65 * q)), 1)
        d.rounded_rectangle((x0 + 22, y0 + 22, x0 + 27, y0 + 108), radius=2, fill=(*GREEN, int(255 * q)))
        d.text((x0 + bw2 // 2 + 8, y0 + 30), "COMMANDER SUR", font=font(jakarta, 21, "Bold"),
               fill=(*CREAM, int(245 * q)), anchor="mt")
        d.text((x0 + bw2 // 2 + 8, y0 + 60), "WHATSAPP", font=font(mont, 31, "ExtraBold"),
               fill=(44, 207, 126, int(255 * q)), anchor="mt")
        if contact:
            cf = fit_font(d, contact, jakarta, 20, 16, bw2 - 64, "Bold")
            d.text((x0 + bw2 // 2 + 8, y0 + 104), contact, font=cf, fill=(*CREAM, int(245 * q)), anchor="mt")
        actifs.append("GB08 CTA WhatsApp")

    if layer.getchannel("A").getbbox():
        im = Image.alpha_composite(im, layer)
    return cv2.cvtColor(np.asarray(im.convert("RGB")), cv2.COLOR_RGB2BGR), actifs


# --------------------------------------------------------------------------- #
class ShotReader:
    """Lecture **séquentielle** de la fenêtre source du plan.

    Aucun saut d'image en cours de lecture (les seeks d'OpenCV sont approximatifs) : on avance
    image par image depuis le début du fichier jusqu'à `in_frame`, puis on suit la fenêtre.
    Quand la fenêtre est épuisée, la dernière image de la fenêtre est répétée : c'est le gel de
    fin déclaré par `freeze_tail_f`. Preuve : `tools/verify_master.py` retrouve l'indice déclaré.
    """

    def __init__(self, path: Path, shot: dict[str, Any]):
        self.cap = cv2.VideoCapture(str(path))
        if not self.cap.isOpened():
            raise RuntimeError(f"Source illisible : {path}")
        self.in_frame = int(shot["source"]["in_frame"])
        self.span = int(shot["source"]["source_frames"])
        self.pos = -1
        self.last = None
        while self.pos < self.in_frame - 1:
            ok, img = self.cap.read()
            if not ok:
                raise RuntimeError(f"Fenêtre source hors du fichier : {path} (in_frame={self.in_frame})")
            self.pos += 1

    def frame_at(self, local: int) -> np.ndarray:
        offset = min(max(0, local), max(0, self.span - 1))
        target = self.in_frame + offset
        while self.pos < target:
            ok, img = self.cap.read()
            if not ok:
                break
            self.pos += 1
            self.last = img
        if self.last is None:
            raise RuntimeError("Décodage impossible : fenêtre vide")
        return self.last

    def release(self):
        self.cap.release()


def render(plan_path: Path, output: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    expected = {"width": 720, "height": 1280, "fps": 30, "frames": 900, "duration_s": 30.0, "audio": False}
    if plan.get("output") != expected or [int(s["frames"]) for s in plan["scenes"]] != [180, 240, 210, 270]:
        raise ValueError("Contrat T1 (4 scènes muettes, 900 images) non respecté par le plan")
    if len(plan["shots"]) != 12:
        raise ValueError("Le plan doit contenir 12 plans")

    from engine.fetch_rushes import ensure_rushes
    ensure_rushes()

    tmp = Path(tempfile.mkdtemp(prefix="t1-v4-"))
    windows = build_windows(plan)
    shots = plan["shots"]
    cuts = {int(c["at_f"]): c["transition"] for c in plan["cuts"]}
    readers: dict[str, ShotReader] = {}
    normalized: dict[str, Path] = {}
    manifest: dict[str, Any] = {"plan": plan_path.name, "moteur": "engine/motion_v4.py",
                                "frames": FRAMES, "plans": [], "transitions": [], "blocs": [],
                                "fenetres_graphiques": {k: v for k, v in sorted(windows.items())}}
    try:
        for scene in plan["scenes"]:
            shot = next(s for s in shots if s["scene"] == scene["id"])
            src = ROOT / shot["source"]["file"]
            key = str(shot["source"]["sha256"])
            if key not in normalized:
                target = tmp / f"{scene['id']}.mp4"
                filt = ("minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir,"
                        "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,"
                        "eq=saturation=1.12:contrast=1.06:brightness=0.006")
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-an",
                                "-vf", filt, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                                "-pix_fmt", "yuv420p", str(target)], check=True)
                normalized[key] = target
        for shot in shots:
            src = ROOT / shot["source"]["file"]
            key = str(shot["source"]["sha256"])
            readers[shot["id"]] = ShotReader(normalized[key], shot)

        mont = ROOT / "assets/fonts/Montserrat-Variable.ttf"
        jakarta = ROOT / "assets/fonts/PlusJakartaSans-Variable.ttf"
        output.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
                                 "-pixel_format", "bgr24", "-video_size", f"{W}x{H}", "-framerate", str(FPS),
                                 "-i", "-", "-an", "-frames:v", str(FRAMES), "-c:v", "libx264",
                                 "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                                 "-movflags", "+faststart", str(output)], stdin=subprocess.PIPE)
        if proc.stdin is None:
            raise RuntimeError("ffmpeg n'a pas ouvert le tube")
        actifs_par_plan: dict[str, set[str]] = {s["id"]: set() for s in shots}
        actifs_transition: dict[int, str] = {}

        def shot_at(fno: int) -> tuple[dict[str, Any], int]:
            for s in shots:
                if int(s["out_start_f"]) <= fno < int(s["out_end_f"]):
                    return s, fno - int(s["out_start_f"])
            return shots[-1], int(shots[-1]["out_frames"]) - 1

        def shot_frame(shot: dict[str, Any], local: int) -> np.ndarray:
            raw = readers[shot["id"]].frame_at(local)
            return camera_move(raw, local, int(shot["out_frames"]), shot)

        for fno in range(FRAMES):
            shot, local = shot_at(fno)
            img = shot_frame(shot, local)
            if fno in cuts:
                kind_id = cuts[fno]
                info = TRANSITIONS[kind_id]
                manifest["transitions"].append({
                    "frame": fno, "seconde": round(fno / FPS, 2), "id": kind_id, "nom": info["nom"],
                    "rendu": info["rendu"], "dur_f": info["dur_f"],
                    "de_plan": shots[shots.index(shot) - 1]["id"], "vers_plan": shot["id"]})
                if info["dur_f"] > 0:
                    actifs_transition[fno] = kind_id
            for cut_f, kind_id in list(actifs_transition.items()):
                info = TRANSITIONS[kind_id]
                if cut_f <= fno < cut_f + info["dur_f"]:
                    prev = shots[shots.index(shot) - 1]
                    old = shot_frame(prev, int(prev["out_frames"]) - 1)
                    img = do_transition(old, img, info["rendu"], (fno - cut_f + 1) / info["dur_f"])
                    break
            img = gradient_overlay(img)
            img, actifs = render_graphics(img, fno, plan, windows, mont, jakarta)
            actifs_par_plan[shot["id"]].update(actifs)
            proc.stdin.write(img.astype(np.uint8).tobytes())
        proc.stdin.close()
        proc.wait()

        for s in shots:
            manifest["plans"].append({
                "id": s["id"], "scene": s["scene"],
                "sortie": {"debut_f": int(s["out_start_f"]), "fin_f": int(s["out_end_f"]),
                           "debut_s": round(int(s["out_start_f"]) / FPS, 3),
                           "fin_s": round(int(s["out_end_f"]) / FPS, 3)},
                "source": {"fichier": s["source"]["file"], "in_frame": int(s["source"]["in_frame"]),
                           "source_frames": int(s["source"]["source_frames"]),
                           "fin_reelle": int(s["source"]["in_frame"]) + int(s["source"]["source_frames"]) - 1,
                           "gel_fin_f": int(s["source"].get("freeze_tail_f", 0))},
                "mouvement": {"id": s["zoom_curve"]["movement_id"], "nom": s["zoom_curve"]["movement"],
                              "parametres": s["zoom_curve"]["parameters"], "base": s["zoom_curve"]["base"]},
                "transition_sortie": s["transition_out"],
                "blocs_visibles": sorted(actifs_par_plan[s["id"]]),
            })
        manifest["blocs"] = [{"id": o["graphic_block"], "champ": o["field"], "composition": o["composition"],
                              "start_f": int(o["start_f"]), "end_f": int(o["end_f"]),
                              "start_s": round(int(o["start_f"]) / FPS, 2), "end_s": round(int(o["end_f"]) / FPS, 2)}
                             for o in plan["overlays"]]
        if manifest_path:
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {"frames": FRAMES, "duration_s": 30.0, "fps": FPS, "width": W, "height": H,
                "video": str(output), "manifest": str(manifest_path) if manifest_path else None}
    finally:
        for r in readers.values():
            r.release()
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="Moteur T1 piloté par le plan (correction de l'audit)")
    p.add_argument("--plan", type=Path, default=ROOT / "render_plan_v4_demo.json")
    p.add_argument("--output", type=Path, default=ROOT / "output/output_T1_master_final.mp4")
    p.add_argument("--manifest", type=Path, default=ROOT / "reports/execution_manifest_v4.json")
    a = p.parse_args()
    print(json.dumps(render(a.plan, a.output, a.manifest), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
