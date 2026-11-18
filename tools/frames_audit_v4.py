"""Extrait les images de contrôle du master final et des anciennes versions (jamais le JSON)."""
from __future__ import annotations
import json, sys
from pathlib import Path
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "assets/fonts/PlusJakartaSans-Variable.ttf"
OUT = ROOT / "preuves/audit_v4"

def frame(video: Path, t: float):
    cap = cv2.VideoCapture(str(video))
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, img = cap.read(); cap.release()
    assert ok, (video, t)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def sheet(items, cols, cell, path, title):
    w, h = cell
    rows = (len(items) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * w + 20 * (cols + 1), rows * (h + 54) + 20 * (rows + 1) + 44), (16, 20, 28))
    d = ImageDraw.Draw(canvas)
    d.text((20, 14), title, font=ImageFont.truetype(str(FONT), 26), fill=(255, 248, 239))
    for i, (img, label) in enumerate(items):
        r, c = divmod(i, cols)
        x = 20 + c * (w + 20); y = 64 + r * (h + 54) + 20 * r
        canvas.paste(Image.fromarray(img).resize((w, h), Image.LANCZOS), (x, y))
        d.text((x, y + h + 8), label, font=ImageFont.truetype(str(FONT), 16), fill=(255, 200, 150))
    canvas.save(path)
    return path

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    master = ROOT / "output/output_T1_master_final.mp4"
    manifest = json.loads((ROOT / "reports/execution_manifest_v4.json").read_text(encoding="utf-8"))
    # planche A : un point par plan
    items = []
    for p in manifest["plans"]:
        t = round((p["sortie"]["debut_s"] + p["sortie"]["fin_s"]) / 2, 2)
        items.append((frame(master, t), f"{p['id']} {t:04.1f}s · {p['mouvement']['id']}"))
    print(sheet(items, 4, (270, 480), OUT / "planche_plans_master_final.png", "Master final piloté par le plan — 12 plans"))
    # planche B : transitions (milieu de chaque transition de durée > 0)
    items = []
    for tr in manifest["transitions"]:
        if tr["dur_f"] == 0:
            continue
        t = round((tr["frame"] + tr["dur_f"] / 2) / 30, 3)
        items.append((frame(master, t), f"{t:04.2f}s {tr['id']} {tr['nom']}"))
    print(sheet(items, 2, (300, 534), OUT / "planche_transitions_master_final.png", "Transitions réellement exécutées (durée V1.2)"))
    # planche C : un point par bloc graphique
    items = []
    for b in manifest["blocs"]:
        t = round((b["start_s"] + min(b["end_s"], 29.9)) / 2, 2)
        items.append((frame(master, t), f"{b['id']} {b['champ']} {t:04.1f}s"))
    print(sheet(items, 4, (270, 480), OUT / "planche_graphismes_master_final.png", "8 blocs graphiques déclarés — exécutés aux fenêtres du plan"))

if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    main()
