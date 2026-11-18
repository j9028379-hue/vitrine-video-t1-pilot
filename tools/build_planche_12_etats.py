"""Assemble la planche des 12 états de la fiche de tournage (4 scènes × 3 états).

    cd <dépôt> && python3 tools/build_planche_12_etats.py

Sortie : ui-screens/planche_12_etats.png
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui-screens"
OUT = UI / "planche_12_etats.png"

ETATS = [
    ("A", "A — fiche de tournage", "etatA_consigne"),
    ("B", "B — enregistrement (caméra + chrono + barre)", "etatB_enregistrement"),
    ("C", "C — validation avec le son", "etatC_validation"),
]
SCENES = [(1, "LE PLAT · 6 s"), (2, "LE DESSUS ET LES DÉTAILS · 8 s"),
          (3, "LA PERSONNE QUI SERT · 7 s"), (4, "LE LIEU ET LE CONTACT · 9 s")]

TW, TH = 300, 650        # taille des vignettes
FONT = ROOT / "assets" / "fonts" / "PlusJakartaSans-Variable.ttf"
PAD, HEAD = 18, 96


def main() -> None:
    tiles: list[tuple[Image.Image, str, str]] = []
    for n, label in SCENES:
        for _, etat_label, suffix in ETATS:
            f = UI / f"ecran_08_scene{n}_{suffix}.png"
            if not f.is_file():
                raise SystemExit(f"capture manquante : {f.name}")
            im = Image.open(f).convert("RGB").resize((TW, TH), Image.Resampling.LANCZOS)
            tiles.append((im, f"S{n} · {label}", etat_label.replace("état ", "")))

    cols, rows = 3, 4
    W = PAD + cols * (TW + PAD)
    H = HEAD + rows * (TH + 46 + PAD) + PAD
    sheet = Image.new("RGB", (W, H), (7, 10, 18))
    d = ImageDraw.Draw(sheet)
    f_title = ImageFont.truetype(str(FONT), 19)
    f_sub = ImageFont.truetype(str(FONT), 14)
    f_scene = ImageFont.truetype(str(FONT), 13)
    f_etat = ImageFont.truetype(str(FONT), 13)
    d.text((PAD, 26), "VITRINE VIDÉO — T1 « Restaurants et Maquis » — les 12 états de la fiche de tournage",
           fill=(255, 255, 255), font=f_title)
    d.text((PAD, 48), "Vue 390 × 844 (×2) · l'état B ne montre que l'aperçu, le chrono et la barre : la fiche disparaît",
           fill=(150, 168, 192), font=f_sub)
    d.text((PAD, 68), "Généré par tools/build_planche_12_etats.py — captures réelles de simulation/index.html",
           fill=(120, 138, 160), font=f_sub)

    for i, (im, titre, etat) in enumerate(tiles):
        r, c = divmod(i, cols)
        x = PAD + c * (TW + PAD)
        y = HEAD + r * (TH + 46 + PAD)
        d.rectangle([x - 2, y - 2, x + TW + 1, y + TH + 1], outline=(58, 74, 98))
        sheet.paste(im, (x, y))
        d.text((x, y + TH + 8), titre, fill=(242, 98, 27), font=f_scene)
        d.text((x, y + TH + 26), etat, fill=(175, 190, 210), font=f_etat)

    sheet.save(OUT, optimize=True)
    print(f"{OUT.relative_to(ROOT)} — {sheet.size[0]}×{sheet.size[1]} px, 12 vignettes")


if __name__ == "__main__":
    main()
