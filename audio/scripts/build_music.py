"""Composition et rendu des deux pistes originales T1 « Restaurants et Maquis ».

Famille : maquis_afrobeats_120 — 120 BPM, 30,000 s exactement, 15 mesures de 2 s.
Aucun échantillon : uniquement la synthèse de `synth_lib.py`.

Piste A « Braise & service » : Am7–F–C–G, balafon + corde pincée, groove afrobeat franc.
Piste B « Maquis doré »     : Dm7–B♭–F–C, kalimba + e-piano, groove plus berceur, cloche 12/8.

Les deux pistes sont instrumentales (aucune parole, aucun vocalise) et partagent la même
partition temporelle que le montage V3.1 :
  S1 0–6 s      accroche immédiate, énergie gourmande
  S2 6–14 s     découverte, couches qui s'ajoutent (cordes / e-piano, couverts)
  S3 14–21 s    service et présence humaine : arrangement creusé, place laissée à la voix
  S4 21–30 s    retour plein, conclusion, respiration CTA à partir de 28,5 s
"""
from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np

import synth_lib as L

ROOT = Path(__file__).resolve().parents[1]
SR = L.SR
N = int(round(L.TOTAL * SR))


# --------------------------------------------------------------------------- #
def beats_to_s(beats: float) -> float:
    return beats * L.BEAT


def bar_start(bar: int) -> float:
    return bar * L.BAR


def render_note(fn, freq, dur, at, gain, buf, pan=0.0):
    sig = fn(freq, dur) if dur else fn(freq)
    L.add_stereo(buf, sig, at, gain=gain, pan=pan)


def render_track(cfg: dict) -> dict[str, np.ndarray]:
    """rend les 4 bus (batterie, basse, harmonie, melodie) puis le mix de la piste."""
    drums = np.zeros((N, 2))
    bass = np.zeros((N, 2))
    harm = np.zeros((N, 2))
    lead = np.zeros((N, 2))

    chords = cfg["chords"]            # liste de 15 (nom, [notes], basse)
    pattern = cfg["drum_pattern"]     # dict listes de beats
    hook = cfg["hook"]                # liste (bar, beat, note, dur_en_beats, gain)
    arp = cfg["arp"]                  # liste (bar, [notes]) ou []
    pad_bars = set(cfg["pad_bars"])
    pluck_bars = set(cfg["pluck_bars"])
    clap_bars = set(cfg["clap_bars"])
    light_bars = set(cfg["light_bars"])
    stab_beats = cfg["stabs"]         # liste (temps_s, [notes])

    # ---- batterie -------------------------------------------------------- #
    for bar in range(15):
        t0 = bar_start(bar)
        light = bar in light_bars
        for b in pattern["kick"]:
            kick = L.kick(punch=0.9 if light else 1.0)
            L.add_stereo(drums, kick, t0 + b * L.BEAT, 0.95 if not light else 0.7)
        if not light:
            for b in pattern["rim"]:
                L.add_stereo(drums, L.rim(), t0 + b * L.BEAT, 0.42, pan=-0.25)
        if bar in clap_bars:
            for b in pattern["clap"]:
                L.add_stereo(drums, L.clap(), t0 + b * L.BEAT, 0.30, pan=0.15)
        # shakers : croches ou doubles-croches selon la densité du passage
        steps = pattern["shaker_light"] if light else pattern["shaker"]
        for i, b in enumerate(steps):
            acc = pattern.get("shaker_accents", [])
            g = 0.34 if (i % 4 == 0 or b in acc) else 0.20
            L.add_stereo(drums, L.shaker(bright=0.9 + 0.2 * (i % 2)), t0 + b * L.BEAT, g,
                         pan=0.35 if i % 2 else -0.35)
        if not light:
            for b, f in pattern["conga"]:
                L.add_stereo(drums, L.conga(f=f), t0 + b * L.BEAT, 0.34, pan=-0.3)
        for b, base, g in pattern["bell"]:
            if light and g > 0.3:
                g *= 0.5
            L.add_stereo(drums, L.agogo(base=base), t0 + b * L.BEAT, g, pan=0.45)
        for b in pattern.get("wood", []):
            L.add_stereo(drums, L.woodblock(), t0 + b * L.BEAT, 0.22, pan=0.3)

    # ---- basse ----------------------------------------------------------- #
    for bar, (name, notes, root) in enumerate(chords):
        t0 = bar_start(bar)
        root_f = L.hz(root)
        light = bar in light_bars
        for b, dur_b, interval, g in pattern["bass"]:
            if light and g > 0.8:
                g *= 0.8
            f = root_f * 2 ** (interval / 12)
            sig = L.bass_note(f, beats_to_s(dur_b) + 0.12, bright=0.45 if light else 0.6)
            L.add_stereo(bass, sig, t0 + b * L.BEAT, g, pan=0.0)

    # ---- harmonie -------------------------------------------------------- #
    for bar, (name, notes, root) in enumerate(chords):
        t0 = bar_start(bar)
        freqs = [L.hz(n) for n in notes]
        if bar in pad_bars:
            sig = L.pad_chord(freqs, L.BAR * 1.05, attack=0.5, release=0.6)
            L.add_stereo(harm, sig, t0, 0.5)
        if bar in pluck_bars:
            for i, b in enumerate([0, 0.75, 1.5, 2.0, 2.75, 3.5]):
                f = freqs[i % len(freqs)] * (2 if i == 3 else 1)
                L.add_stereo(harm, L.pluck_ks(f, 0.7), t0 + b * L.BEAT, 0.30,
                             pan=(-0.4 if i % 2 else 0.4))
        # nappe d'e-piano / balafon d'accompagnement
        if cfg["comp_style"] == "epiano":
            for i, b in enumerate([0, 2.0]):
                for j, f in enumerate(freqs):
                    L.add_stereo(harm, L.epiano(f, 1.0), t0 + b * L.BEAT, 0.16,
                                 pan=-0.2 + 0.13 * j)
        else:
            for i, b in enumerate([0.5, 2.5]):
                for j, f in enumerate(freqs[:3]):
                    L.add_stereo(harm, L.balafon(f, 0.5, hard=0.7), t0 + b * L.BEAT, 0.15,
                                 pan=-0.25 + 0.15 * j)

    for at, notes in stab_beats:
        L.add_stereo(harm, L.brass_stab([L.hz(n) for n in notes], 0.4), at, 0.5, pan=0.1)

    # ---- mélodie --------------------------------------------------------- #
    for bar, beat, note, dur_b, g in hook:
        at = bar_start(bar) + beats_to_s(beat)
        if cfg["lead_style"] == "kalimba":
            sig = L.marimba_soft(L.hz(note), max(0.6, beats_to_s(dur_b) + 0.4))
        else:
            sig = L.balafon(L.hz(note), max(0.35, beats_to_s(dur_b) + 0.25), hard=1.0)
        L.add_stereo(lead, sig, at, g, pan=0.12)

    # ---- fin : respiration 28,5–30,0 s ---------------------------------- #
    fade_gain = L.ease_out_cubic_gain(N, 28.5, 30.0)

    curve_db = cfg.get("eq_db")

    def _fb(x):
        eqd = L.bus_eq(x, curve_db=curve_db) if curve_db is not None else L.bus_eq(x)
        return eqd * fade_gain[:, None]

    drums, bass, harm, lead = _fb(drums), _fb(bass), _fb(harm), _fb(lead)
    mix = drums * 0.95 + bass * 0.42 + harm * 0.78 + lead * 1.05
    return {"drums": drums, "bass": bass, "harm": harm, "lead": lead, "mix": mix}


# --------------------------------------------------------------------------- #
# PISTE A — « Braise & service »
# --------------------------------------------------------------------------- #
CHORDS_A = [
    ("Am7", ["A2", "E3", "G3", "C4"], "A2"),
    ("Fmaj7", ["F2", "C3", "E3", "A3"], "F2"),
    ("C", ["C3", "G3", "E4", "C4"], "C3"),
    ("G", ["G2", "D3", "B3", "F4"], "G2"),
    ("Am7", ["A2", "E3", "G3", "C4"], "A2"),
    ("Fmaj7", ["F2", "C3", "E3", "A3"], "F2"),
    ("C", ["C3", "G3", "E4", "C4"], "C3"),
    ("G", ["G2", "D3", "B3", "F4"], "G2"),
    ("Am7", ["A2", "E3", "G3", "C4"], "A2"),
    ("Fmaj7", ["F2", "C3", "E3", "A3"], "F2"),
    ("C", ["C3", "G3", "E4", "C4"], "C3"),
    ("G", ["G2", "D3", "B3", "F4"], "G2"),
    ("Fmaj7", ["F2", "C3", "E3", "A3", "C4"], "F2"),
    ("G", ["G2", "D3", "B3", "F4"], "G2"),
    ("Am9", ["A2", "E3", "B3", "C4", "E4"], "A2"),
]

PATTERN_A = {
    "kick": [0.0, 1.5, 2.75],
    "rim": [1.0, 3.0],
    "clap": [1.0, 3.0],
    "shaker": [i * 0.25 for i in range(16)],
    "shaker_light": [i * 0.5 for i in range(8)],
    "shaker_accents": [0.5, 1.5, 2.5, 3.5],
    "conga": [(0.5, 196.0), (1.75, 233.0), (2.5, 196.0), (3.25, 175.0)],
    "bell": [(0.0, 760.0, 0.30), (1.5, 1013.0, 0.22), (2.5, 760.0, 0.26), (3.5, 1013.0, 0.18)],
    "wood": [2.25],
    "bass": [(0.0, 0.9, 0, 0.95), (0.75, 0.4, 0, 0.6), (1.5, 0.45, 7, 0.72),
             (2.5, 0.6, 0, 0.9), (3.25, 0.4, 12, 0.55)],
}

HOOK_A = [
    # S1 — accroche (mesures 1–3)
    (0, 0.5, "A4", 0.5, 0.62), (0, 1.0, "C5", 0.5, 0.58), (0, 1.5, "D5", 0.5, 0.62),
    (0, 2.0, "E5", 0.75, 0.66), (0, 2.75, "D5", 0.25, 0.5), (0, 3.25, "C5", 0.5, 0.5),
    (1, 0.0, "A4", 0.75, 0.6), (1, 1.0, "G4", 0.5, 0.5), (1, 1.5, "E4", 0.5, 0.46),
    (1, 2.5, "A4", 0.5, 0.55), (1, 3.0, "C5", 0.75, 0.55),
    (2, 0.5, "D5", 0.5, 0.55), (2, 1.0, "E5", 0.5, 0.6), (2, 1.5, "G5", 0.75, 0.62),
    (2, 2.75, "E5", 0.5, 0.5), (2, 3.5, "D5", 0.4, 0.46),
    # S2 — découverte / détails (mesures 4–7)
    (3, 0.5, "C5", 0.5, 0.5), (3, 1.0, "D5", 0.5, 0.52), (3, 1.75, "E5", 0.5, 0.55),
    (3, 2.5, "D5", 0.5, 0.48), (3, 3.25, "B4", 0.5, 0.44),
    (4, 0.0, "A4", 0.5, 0.5), (4, 0.75, "C5", 0.5, 0.5), (4, 1.5, "E5", 0.75, 0.55),
    (4, 2.75, "G5", 0.5, 0.56),
    (5, 0.5, "E5", 0.5, 0.5), (5, 1.25, "D5", 0.5, 0.48), (5, 2.0, "C5", 0.5, 0.46),
    (5, 2.75, "A4", 0.75, 0.5),
    (6, 0.0, "G4", 0.5, 0.44), (6, 0.75, "A4", 0.5, 0.46), (6, 1.5, "C5", 0.75, 0.5),
    (6, 2.75, "D5", 0.5, 0.5),
    # S3 — service, place laissée à la voix (mesures 8–10, plus aéré)
    (7, 1.0, "E5", 1.0, 0.42), (7, 2.5, "D5", 0.75, 0.38),
    (8, 0.0, "C5", 0.75, 0.4), (8, 1.5, "A4", 1.0, 0.38),
    (9, 0.5, "G4", 1.0, 0.36), (9, 2.0, "E4", 1.0, 0.34),
    (10, 1.0, "A4", 0.5, 0.36), (10, 2.0, "C5", 1.0, 0.38),
    # S4 — conclusion dynamique et mémorable (mesures 11–15)
    (11, 0.0, "A4", 0.5, 0.55), (11, 0.5, "C5", 0.5, 0.55), (11, 1.0, "E5", 0.5, 0.6),
    (11, 1.5, "G5", 0.75, 0.62), (11, 2.5, "A5", 0.75, 0.64), (11, 3.5, "G5", 0.5, 0.5),
    (12, 0.5, "E5", 0.5, 0.55), (12, 1.0, "D5", 0.5, 0.5), (12, 1.75, "C5", 0.5, 0.5),
    (12, 2.5, "A4", 0.75, 0.5),
    (13, 0.0, "B4", 0.5, 0.48), (13, 0.75, "D5", 0.5, 0.5), (13, 1.5, "G5", 0.75, 0.55),
    (13, 2.5, "D5", 0.5, 0.48),
    # dernier accord : laisse respirer l'appel à l'action
    (14, 0.0, "A4", 1.0, 0.5), (14, 0.0, "C5", 1.0, 0.42), (14, 0.25, "E5", 1.0, 0.4),
]

CFG_A = {
    "id": "maquis_afro_A_braise",
    "nom": "Braise & service",
    "chords": CHORDS_A,
    "drum_pattern": PATTERN_A,
    "hook": HOOK_A,
    "arp": [],
    "pad_bars": [7, 8, 9, 13, 14],
    "pluck_bars": [3, 4, 5, 6, 11, 12],
    "clap_bars": [3, 4, 5, 6, 11, 12, 13],
    "light_bars": [7, 8, 9],
    "stabs": [(21.0, ["A4", "C5", "E5"]), (24.0, ["A4", "C5", "E5"]),
              (26.0, ["G4", "B4", "D5"])],
    "lead_style": "balafon",
    "comp_style": "balafon",
}

# --------------------------------------------------------------------------- #
# PISTE B — « Maquis doré »
# --------------------------------------------------------------------------- #
CHORDS_B = [
    ("Dm7", ["D3", "A3", "C4", "F4"], "D3"),
    ("Bb", ["Bb2", "F3", "D4", "F4"], "Bb2"),
    ("F", ["F2", "C3", "A3", "F4"], "F2"),
    ("C", ["C3", "G3", "E4", "G4"], "C3"),
    ("Dm7", ["D3", "A3", "C4", "F4"], "D3"),
    ("Bb", ["Bb2", "F3", "D4", "F4"], "Bb2"),
    ("F", ["F2", "C3", "A3", "F4"], "F2"),
    ("C", ["C3", "G3", "E4", "G4"], "C3"),
    ("Dm7", ["D3", "A3", "C4", "F4"], "D3"),
    ("Bb", ["Bb2", "F3", "D4", "F4"], "Bb2"),
    ("F", ["F2", "C3", "A3", "F4"], "F2"),
    ("C", ["C3", "G3", "E4", "G4"], "C3"),
    ("Bb", ["Bb2", "F3", "D4", "F4", "A4"], "Bb2"),
    ("C", ["C3", "G3", "E4", "G4"], "C3"),
    ("Dm9", ["D3", "A3", "E4", "F4", "C5"], "D3"),
]

PATTERN_B = {
    "kick": [0.0, 1.25, 2.5, 3.25],
    "rim": [1.75, 3.75],
    "clap": [1.75, 3.25],
    "shaker": [i * 0.25 for i in range(16)],
    "shaker_light": [i * 0.5 for i in range(8)],
    "shaker_accents": [0.75, 2.25, 2.75, 3.75],
    "conga": [(0.75, 175.0), (1.5, 208.0), (2.25, 196.0), (3.0, 233.0), (3.75, 175.0)],
    "bell": [(0.0, 880.0, 0.24), (0.75, 1174.0, 0.2), (1.5, 880.0, 0.22),
             (2.5, 1174.0, 0.18), (3.0, 880.0, 0.2), (3.75, 1174.0, 0.16)],
    "wood": [0.5, 2.0],
    "bass": [(0.0, 1.0, 0, 0.9), (1.25, 0.4, 7, 0.62), (1.75, 0.35, 0, 0.55),
             (2.5, 0.6, 12, 0.8), (3.25, 0.35, 7, 0.6), (3.75, 0.25, 0, 0.5)],
}

HOOK_B = [
    (0, 0.75, "D5", 0.5, 0.55), (0, 1.25, "F5", 0.5, 0.55), (0, 1.75, "A5", 0.75, 0.58),
    (0, 2.75, "G5", 0.5, 0.5), (0, 3.25, "F5", 0.5, 0.46),
    (1, 0.0, "D5", 0.75, 0.5), (1, 1.0, "C5", 0.5, 0.45), (1, 1.75, "A4", 0.75, 0.46),
    (2, 0.5, "C5", 0.5, 0.46), (2, 1.25, "D5", 0.5, 0.5), (2, 2.0, "F5", 0.75, 0.52),
    (2, 3.0, "D5", 0.5, 0.46),
    (3, 0.75, "E5", 0.5, 0.5), (3, 1.5, "G5", 0.75, 0.52), (3, 2.75, "E5", 0.5, 0.46),
    (4, 0.0, "D5", 0.5, 0.5), (4, 0.75, "F5", 0.5, 0.5), (4, 1.5, "A5", 0.75, 0.55),
    (4, 2.5, "C6", 0.75, 0.5),
    (5, 0.5, "A5", 0.5, 0.46), (5, 1.25, "G5", 0.5, 0.44), (5, 2.0, "F5", 0.75, 0.46),
    (6, 0.75, "E5", 0.5, 0.44), (6, 1.5, "F5", 0.5, 0.46), (6, 2.5, "A5", 0.75, 0.48),
    (7, 1.0, "G5", 1.0, 0.4), (7, 2.75, "E5", 0.75, 0.34),
    (8, 0.5, "F5", 1.0, 0.38), (8, 2.0, "D5", 1.0, 0.36),
    (9, 0.75, "C5", 1.0, 0.34), (9, 2.25, "A4", 1.0, 0.32),
    (10, 1.0, "D5", 0.5, 0.34), (10, 2.0, "F5", 1.0, 0.36),
    (11, 0.0, "D5", 0.5, 0.5), (11, 0.5, "F5", 0.5, 0.5), (11, 1.0, "A5", 0.5, 0.55),
    (11, 1.5, "C6", 0.75, 0.56), (11, 2.5, "A5", 0.5, 0.5), (11, 3.25, "G5", 0.5, 0.46),
    (12, 0.75, "F5", 0.5, 0.48), (12, 1.5, "D5", 0.5, 0.46), (12, 2.25, "C5", 0.75, 0.44),
    (13, 0.0, "E5", 0.5, 0.44), (13, 0.75, "G5", 0.5, 0.46), (13, 1.75, "C6", 0.75, 0.5),
    (14, 0.0, "D5", 1.0, 0.46), (14, 0.0, "F5", 1.0, 0.38), (14, 0.25, "A5", 1.0, 0.36),
]

CFG_B = {
    "id": "maquis_afro_B_maquis_dore",
    "nom": "Maquis doré",
    "chords": CHORDS_B,
    "drum_pattern": PATTERN_B,
    "hook": HOOK_B,
    "arp": [],
    "pad_bars": [7, 8, 9, 12, 13, 14],
    "pluck_bars": [],
    "clap_bars": [4, 5, 6, 11, 12, 13],
    "light_bars": [7, 8, 9],
    "stabs": [(21.0, ["D4", "F4", "A4"]), (25.0, ["C4", "E4", "G4"])],
    "lead_style": "kalimba",
    "comp_style": "epiano",
    # piste B volontairement plus « claire » (kalimba + e-piano) : on compense
    # la faible teneur en aigus de ces timbres pour le haut-parleur du téléphone
    "eq_db": np.array([-40, -17, -10, -4.0, -2.0, -6.0, -5.0, 0.5, 4.0, 6.0,
                       7.0, 6.5, 3.0, 0.5, -4.0]),
}


# --------------------------------------------------------------------------- #
def write_wav(path: Path, data: np.ndarray, peak_db: float | None = None) -> None:
    x = np.asarray(data, dtype=np.float64)
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    if peak_db is not None:
        x = L.normalize_peak(x, peak_db)
    x = np.clip(x, -1.0, 1.0)
    pcm = np.round(x * 32767.0).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"  écrit {path.relative_to(ROOT)}  {x.shape[0] / SR:.3f} s  pic {L.peak_db(x):+.1f} dBFS")


def main() -> None:
    meta = {"sr": SR, "bpm": L.BPM, "bar_s": L.BAR, "bars": 15, "duree_s": L.TOTAL, "pistes": []}
    for cfg in (CFG_A, CFG_B):
        print(f"Piste {cfg['id']} — {cfg['nom']}")
        stems = render_track(cfg)
        base = ROOT
        write_wav(base / "music" / f"{cfg['id']}_mix_30s.wav", stems["mix"], -3.5)
        write_wav(base / "stems" / f"{cfg['id']}_drums.wav", stems["drums"], -6.0)
        write_wav(base / "stems" / f"{cfg['id']}_bass.wav", stems["bass"], -6.0)
        write_wav(base / "stems" / f"{cfg['id']}_harmonie.wav", stems["harm"], -6.0)
        write_wav(base / "stems" / f"{cfg['id']}_melodie.wav", stems["lead"], -6.0)
        meta["pistes"].append({
            "id": cfg["id"],
            "nom": cfg["nom"],
            "bpm": L.BPM,
            "duree_s": stems["mix"].shape[0] / SR,
            "mesures": 15,
            "instrumental": True,
            "paroles": False,
            "tonalite": "La mineur" if cfg is CFG_A else "Ré mineur",
            "grille": [c[0] for c in cfg["chords"]],
            "stems": ["drums", "bass", "harmonie", "melodie"],
        })
    (ROOT / "metadata" / "music_build.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
