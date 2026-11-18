"""Comparaison temporelle des trois grandes transitions : V3.1 approuvée vs master réconcilié."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "assets/fonts/PlusJakartaSans-Variable.ttf"
OUT = ROOT / "preuves/audit_v4"
V31 = ROOT / "output/output_T1_sans_voix_v3_1.mp4"
FINAL = ROOT / "output/output_T1_master_final.mp4"

# fenêtres réelles : V3.1 = 12 images [coupe-4, coupe+8) ; réconcilié = 6 images [coupe-3, coupe+3)
TRANSITIONS = [
    {"coupe": 180, "nom": "6,0 s — whip pan → TR04 wipe_directionnel"},
    {"coupe": 420, "nom": "14,0 s — push → TR06 speed_ramp_entrant"},
    {"coupe": 630, "nom": "21,0 s — diagonale → TR03 wipe_geometrique"},
]


def frame(video: Path, index: int):
    cap = cv2.VideoCapture(str(video))
    cap.set(cv2.CAP_PROP_POS_FRAMES, index)
    ok, img = cap.read()
    cap.release()
    assert ok, (video, index)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def bande(video: Path, start: int, count: int, pas: int, etiquette: str):
    return [(frame(video, start + i * pas), f"{etiquette} f{(start + i * pas) - (start - 4 * pas)}") for i in range(count)]


def main() -> None:
    cw, ch = 200, 356
    pad, label_h, title_h = 12, 30, 58
    lignes = []  # (titre, [(img, label)])
    data = []
    for t in TRANSITIONS:
        c = t["coupe"]
        v31_idx = [c - 4, c - 2, c, c + 2, c + 4, c + 7]
        fin_idx = [c - 1, c, c + 1, c + 2, c + 3, c + 4]
        lignes.append((f"V3.1 (12 images) — {t['nom']}",
                       [(frame(V31, i), f"{i/30:.2f}s") for i in v31_idx]))
        lignes.append((f"Master réconcilié (6 images) — {t['nom']}",
                       [(frame(FINAL, i), f"{i/30:.2f}s") for i in fin_idx]))
        data.append({"seconde": c / 30, "v3_1_images": v31_idx, "v3_1_duree_f": 12,
                     "reconcilie_images": fin_idx, "reconcilie_duree_f": 6, "nom": t["nom"]})

    cols = 6
    W = pad + cols * (cw + pad)
    H = title_h + len(lignes) * (label_h + ch + pad) + pad
    canvas = Image.new("RGB", (W, H), (16, 20, 28))
    d = ImageDraw.Draw(canvas)
    d.text((pad, 14), "Comparaison temporelle des trois transitions — avant / après réconciliation",
           font=ImageFont.truetype(str(FONT), 22), fill=(255, 248, 239))
    y = title_h
    for titre, items in lignes:
        d.text((pad, y - 2), titre, font=ImageFont.truetype(str(FONT), 14), fill=(255, 200, 150))
        y += label_h - 12
        for j, (img, lab) in enumerate(items):
            x = pad + j * (cw + pad)
            canvas.paste(Image.fromarray(img).resize((cw, ch), Image.LANCZOS), (x, y))
            d.text((x, y + ch + 4), lab, font=ImageFont.truetype(str(FONT), 13), fill=(200, 210, 225))
        y += ch + pad + 24
    OUT.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT / "planche_comparaison_transitions.png")
    (ROOT / "reports/comparaison_transitions.json").write_text(
        json.dumps({"methode": "images réelles des deux MP4, fenêtres d'images déclarées",
                    "transitions": data}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT / "planche_comparaison_transitions.png")


if __name__ == "__main__":
    main()
