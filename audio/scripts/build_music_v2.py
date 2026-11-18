"""Composition et synthèse des deux nouvelles musiques T1 (120 BPM / 30 s).

Aucun échantillon tiers, aucune œuvre existante : tout est synthétisé (oscillateurs,
bruit filtré, Karplus-Strong, synthèse modale) à 48 kHz. Deux propositions seulement :
  A — « adjapiano maquis » (recommandée) : basse ronde, kick 4/4, shakers, kalimba.
  B — « gangan acoustique » (alternative) : tambours parlants, balafon, djembé, peu d'électronique.

Structure calée sur le fichier vidéo réel (cf. audio/video_edit_analysis_T1.md §5) :
mesures 1-3 intro · 4-7 groove · 8-10,5 plus sombre (scène 3) · 11-15 montée vers le CTA.
"""
from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np

import synth_lib as L

SR = L.SR
BEAT = L.BEAT            # 0,500 s
BAR = L.BAR              # 2,000 s
TOTAL = L.TOTAL          # 30,0 s
ROOT = Path(__file__).resolve().parents[1]
rng = np.random.default_rng(20261118)

# --------------------------------------------------------------------------- #
# Grille harmonique : i – VI – III – VII en La mineur, 4 mesures, 3 cycles + 3 mesures
CHORDS = [
    ("Am", ["A3", "C4", "E4"], "A2"),
    ("F",  ["F3", "A3", "C4"], "F2"),
    ("C",  ["C4", "E4", "G4"], "C3"),
    ("G",  ["G3", "B3", "D4"], "G2"),
]
PENTA = ["A4", "C5", "D5", "E5", "G5", "A5", "C6"]

# Motif de 4 mesures (en temps depuis le début du cycle) : (temps, degré pentatonique, vélocité)
MOTIF = [
    (0.0, 0, 1.0), (0.75, 2, .82), (1.5, 1, .90), (2.5, 4, .78), (3.0, 2, .86), (3.75, 3, .72),
    (4.0, 1, .95), (4.75, 3, .80), (5.5, 2, .88), (6.5, 5, .74), (7.0, 4, .84), (7.75, 2, .70),
]


def section(t: float) -> str:
    if t < 3 * BAR:
        return "intro"
    if t < 7 * BAR:
        return "groove"
    if t < 10.5 * BAR:
        return "sombre"
    return "montee"


def gain_section(t: float, table: dict[str, float], default: float = 1.0) -> float:
    return table.get(section(t), default)


# --------------------------------------------------------------------------- #
def render_A() -> dict[str, np.ndarray]:
    n = int(round(TOTAL * SR))
    drums = np.zeros((n, 2)); bass = np.zeros((n, 2))
    harm = np.zeros((n, 2)); lead = np.zeros((n, 2))

    for bar in range(15):
        t0 = bar * BAR
        chord = CHORDS[bar % 4]

        # --- batterie : kick 4/4 léger, clap 2 et 4, shaker 16e, congas syncopées
        for beat in range(4):
            k = L.kick(0.40, 112.0, 44.0, punch=0.9 if beat in (0, 2) else 0.75)
            L.add_stereo(drums, k, t0 + beat * BEAT, gain=0.62 if beat in (0, 2) else 0.42)
        for beat in (1, 3):
            L.add_stereo(drums, L.clap(0.22), t0 + beat * BEAT, gain=0.30)
        for i in range(16):
            g = 0.13 if i % 4 == 0 else (0.07 if i % 2 == 0 else 0.045)
            L.add_stereo(drums, L.shaker(0.075), t0 + i * BEAT / 4, gain=g, pan=0.22 - 0.03 * (i % 4))
        for at, f, g in [(0.75, 196.0, .22), (2.25, 233.0, .17), (3.25, 175.0, .19)]:
            L.add_stereo(drums, L.conga(0.20, f), t0 + at * BEAT, gain=g, pan=-0.18)

        # --- basse ronde type log-drum (note tenue + glisse)
        root = L.hz(chord[2])
        for at, dur, g in [(0.0, 0.62, .95), (1.5, 0.38, .70), (3.0, 0.55, .80)]:
            L.add_stereo(bass, L.bass_note(root, dur, bright=0.42), t0 + at * BEAT, gain=g)

        # --- nappe chaude (discrète, filtrée, plus sombre au milieu)
        pad_cut = 700.0 if section(t0) != "sombre" else 480.0
        pad = L.lp(L.pad_chord([L.hz(x) for x in chord[1]], BAR * 1.05, 0.55, 1.0), pad_cut)
        L.add_stereo(harm, pad, t0, gain=0.16 if section(t0) != "montee" else 0.20)

    # --- motif kalimba/marimba, 3 cycles de 4 mesures + reprise
    for cycle in range(4):
        for (bt, deg, vel) in MOTIF:
            t = cycle * 4 * BAR + bt * BEAT
            if t > TOTAL - 0.9:
                continue
            f = L.hz(PENTA[deg % len(PENTA)])
            if section(t) == "sombre":
                f *= 0.5
                sig = L.marimba_soft(f, 0.75)
                g = 0.16 * vel
            elif section(t) == "intro":
                sig = L.balafon(f, 0.60, hard=0.8)
                g = 0.13 * vel
            else:
                sig = L.balafon(f, 0.62, hard=0.95)
                g = 0.21 * vel
            L.add_stereo(lead, sig, t, gain=g, pan=0.12 * np.sin(t))

    # --- événements de structure : accents musicaux aux 3 transitions + CTA + fin
    for t, g in [(6.0, .30), (14.0, .26), (21.0, .34)]:
        L.add_stereo(harm, L.brass_stab([L.hz(x) for x in CHORDS[int(t // BAR) % 4][1]], 0.40), t, gain=g)
    L.add_stereo(harm, L.brass_stab([L.hz(x) for x in ["C4", "E4", "G4"]], 0.55), 26.5, gain=0.26)
    L.add_stereo(bass, L.sub_boom(1.1, 60.0), 28.5, gain=0.55)
    return {"drums": drums, "bass": bass, "harm": harm, "lead": lead}


def render_B() -> dict[str, np.ndarray]:
    n = int(round(TOTAL * SR))
    drums = np.zeros((n, 2)); bass = np.zeros((n, 2))
    harm = np.zeros((n, 2)); lead = np.zeros((n, 2))

    def tambour(freq: float, dur: float, bend: float = 0.0) -> np.ndarray:
        """Tambour parlant simulé : membrane + glisse de hauteur."""
        t = L.t_axis(dur)
        f = freq * np.exp(-t * 6.0) + bend
        phase = 2 * np.pi * np.cumsum(f) / SR
        body = np.sin(phase) + 0.35 * np.sin(2.02 * phase) + 0.12 * np.sin(3.1 * phase)
        return L.env(body.shape[0], 0.002, dur * 0.85, 3.0) * body

    for bar in range(15):
        t0 = bar * BAR
        chord = CHORDS[bar % 4]
        sec = section(t0)

        # djembé/tambours : motif ternaire-feel sur grille binaire
        pattern = [(0.0, 196.0, 0.30), (0.5, 262.0, 0.20), (0.75, 233.0, 0.22),
                   (1.5, 175.0, 0.26), (2.0, 196.0, 0.30), (2.5, 294.0, 0.20),
                   (3.0, 233.0, 0.24), (3.5, 262.0, 0.22)]
        for at, f, g in pattern:
            L.add_stereo(drums, tambour(f, 0.42), t0 + at * BEAT, gain=g, pan=-0.12)
        # woodblock régulier + shaker léger
        for beat in range(4):
            L.add_stereo(drums, L.woodblock(0.09, 1080.0), t0 + beat * BEAT, gain=0.10, pan=0.25)
        for i in range(8):
            L.add_stereo(drums, L.shaker(0.07), t0 + i * BEAT / 2, gain=0.05 if i % 2 else 0.075, pan=0.18)
        if sec != "intro":
            L.add_stereo(drums, L.kick(0.35, 96.0, 42.0, punch=0.7), t0, gain=0.34)
            L.add_stereo(drums, L.kick(0.35, 96.0, 42.0, punch=0.6), t0 + 2 * BEAT, gain=0.28)

        # basse discrète
        root = L.hz(chord[2]) * (1.0 if sec != "sombre" else 0.5)
        for at, dur, g in [(0.0, 0.70, .85), (2.5, 0.40, .55)]:
            L.add_stereo(bass, L.bass_note(root, dur, bright=0.30), t0 + at * BEAT, gain=g)

        # harmonie : balafon lent plutôt que nappe
        for k, note in enumerate(chord[1]):
            if sec == "intro" and k == 2:
                continue
            L.add_stereo(harm, L.balafon(L.hz(note) * 0.5, 1.2, hard=0.6), t0 + k * 0.06, gain=0.12)

    # mélodie : balafon, plus aérée que dans A
    for cycle in range(4):
        for (bt, deg, vel) in MOTIF[::2]:
            t = cycle * 4 * BAR + bt * BEAT + 0.25
            if t > TOTAL - 1.0:
                continue
            f = L.hz(PENTA[(deg + 1) % len(PENTA)])
            if section(t) == "sombre":
                f *= 0.5
            L.add_stereo(lead, L.balafon(f, 0.9, hard=0.75), t, gain=0.20 * vel, pan=0.10)

    L.add_stereo(harm, L.agogo(0.5, 690.0), 6.0, gain=0.22)
    L.add_stereo(harm, L.agogo(0.5, 620.0), 14.0, gain=0.20)
    L.add_stereo(harm, L.agogo(0.6, 740.0), 21.0, gain=0.24)
    L.add_stereo(drums, tambour(150.0, 0.8, bend=40.0), 26.5, gain=0.34)
    L.add_stereo(bass, L.sub_boom(1.0, 58.0), 28.5, gain=0.5)
    return {"drums": drums, "bass": bass, "harm": harm, "lead": lead}


# --------------------------------------------------------------------------- #
def finish(stems: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Équilibre des stems, léger élargissement, fondu final 28,5 → 30 s."""
    out = {
        "drums": stems["drums"] * 1.00,
        "bass": stems["bass"] * 1.00,
        "harm": stems["harm"] * 1.00,
        "lead": stems["lead"] * 1.00,
    }
    mix = out["drums"] + 0.85 * out["bass"] + 0.80 * out["harm"] + 0.90 * out["lead"]
    # douceur dans les aigus pour laisser la voix parler
    mix = 0.55 * mix + 0.45 * L.lp(mix, 5200.0)
    mix = L.hp(mix, 34.0)
    n = mix.shape[0]
    fade = np.ones(n)
    i0 = int(28.5 * SR)
    fade[i0:] = np.linspace(1.0, 0.0, n - i0) ** 1.6
    fade[:int(0.03 * SR)] = np.linspace(0.0, 1.0, int(0.03 * SR))
    out["mix"] = mix * fade[:, None]
    # normalisation de sécurité, le mastering final se fait au mixage
    out["mix"] = L.normalize_peak(out["mix"], -6.0) / L.db_to_gain(-6.0) * L.db_to_gain(-9.0)
    return out


def write_wav(path: Path, x: np.ndarray, target_peak_db: float) -> None:
    x = L.normalize_peak(x, target_peak_db)
    x = np.clip(x, -1.0, 1.0)
    pcm = np.round(x * 32767.0).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"  {path.relative_to(ROOT.parent)}  {x.shape[0]/SR:.3f} s  pic {L.peak_db(x):+.1f} dBFS")


def main() -> None:
    meta = {"sr": SR, "bpm": L.BPM, "bar_s": BAR, "bars": 15, "duree_s": TOTAL,
            "outil": "composition et synthèse originales en code (aucun outil de génération musicale par IA disponible)",
            "pistes": []}
    for cfg in (("A", "adjapiano maquis", render_A), ("B", "gangan acoustique", render_B)):
        tid, nom, fn = cfg
        print(f"Piste {tid} — {nom}")
        stems = finish(fn())
        write_wav(ROOT / "music" / "v2" / f"music_{tid}_{'adjapiano_maquis' if tid=='A' else 'gangan_acoustique'}_30s.wav", stems["mix"], -3.5)
        for k in ("drums", "bass", "harm", "lead"):
            write_wav(ROOT / "stems" / "v2" / f"music_{tid}_{k}.wav", stems[k] if k in stems else stems["mix"], -7.0)
        meta["pistes"].append({
            "id": tid, "nom": nom, "bpm": L.BPM, "duree_s": TOTAL, "mesures": 15,
            "tonalite": "La mineur", "instrumental": True, "paroles": False,
            "grille": ["Am", "F", "C", "G"],
            "structure": {"intro": "0–6 s", "groove": "6–14 s", "sombre": "14–21 s", "montee": "21–30 s"},
            "recommandation": "A est la proposition recommandée, B l'alternative" if tid == "A" else "alternative",
            "stems": ["drums", "bass", "harm", "lead"],
            "originalite": "composition originale synthétisée ; aucune mélodie, aucun sample ni extrait d'œuvre existante",
        })
    (ROOT / "metadata" / "music_v2_build.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("metadata/music_v2_build.json écrit")


if __name__ == "__main__":
    main()
