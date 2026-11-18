"""Bibliothèque de synthèse audio originale — VITRINE VÍDEO / T1 Restaurants et Maquis.

Aucun échantillon, aucune boucle tierce, aucune œuvre existante n'est utilisée :
tout est calculé par synthèse numérique (oscillateurs, bruit filtré, synthèse modale
et Karplus-Strong) à 48 kHz, 24 bits. Les matières sonores sont choisies pour
décrire la cuisine de maquis : assiette, couverts, service, salle, braise.

Licence : création originale pour VITRINE VIDÉO (voir audio/metadata/LICENCES.md).
"""
from __future__ import annotations

import numpy as np
from scipy import signal

SR = 48_000
BPM = 120.0
BEAT = 60.0 / BPM          # 0,500 s
BAR = 4 * BEAT             # 2,000 s
TOTAL = 30.0               # 15 mesures


# --------------------------------------------------------------------------- #
# utilitaires
# --------------------------------------------------------------------------- #
def t_axis(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR)), dtype=np.float64) / SR


def place(buf: np.ndarray, sig: np.ndarray, at: float, gain: float = 1.0) -> None:
    """Additionne `sig` dans `buf` à l'instant `at` (secondes), avec repliement borné."""
    i0 = int(round(at * SR))
    if i0 >= buf.shape[0]:
        return
    n = min(sig.shape[0], buf.shape[0] - i0)
    buf[i0:i0 + n] += gain * sig[:n]


def stereo(*layers: np.ndarray) -> np.ndarray:
    return np.stack(layers, axis=1).astype(np.float64)


def add_stereo(buf: np.ndarray, mono: np.ndarray, at: float, gain: float = 1.0, pan: float = 0.0) -> None:
    """place un signal mono dans un buffer stéréo (pan -1..1, loi constante)."""
    l = np.cos((pan + 1) * np.pi / 4) * 1.41421356237
    r = np.sin((pan + 1) * np.pi / 4) * 1.41421356237
    tmp = np.zeros((mono.shape[0], 2))
    tmp[:, 0] = mono * l
    tmp[:, 1] = mono * r
    i0 = int(round(at * SR))
    if i0 >= buf.shape[0]:
        return
    n = min(tmp.shape[0], buf.shape[0] - i0)
    buf[i0:i0 + n] += gain * tmp[:n]


def lp(x: np.ndarray, cutoff: float, order: int = 2) -> np.ndarray:
    b, a = signal.butter(order, min(cutoff, SR * 0.49) / (SR / 2), "low")
    return signal.lfilter(b, a, x, axis=0)


def hp(x: np.ndarray, cutoff: float, order: int = 2) -> np.ndarray:
    b, a = signal.butter(order, cutoff / (SR / 2), "high")
    return signal.lfilter(b, a, x, axis=0)


def bp(x: np.ndarray, lo: float, hi: float, order: int = 2) -> np.ndarray:
    b, a = signal.butter(order, [lo / (SR / 2), min(hi, SR * 0.49) / (SR / 2)], "band")
    return signal.lfilter(b, a, x, axis=0)


def env(n: int, attack: float, decay: float, curve: float = 4.0) -> np.ndarray:
    """enveloppe attaque linéaire + décroissance exponentielle."""
    a = max(1, int(attack * SR))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    rest = np.arange(n - a) / SR
    e[a:] = np.exp(-curve * rest / max(decay, 1e-4))
    return e


def fade(x: np.ndarray, fade_in: float, fade_out: float, curve: str = "cubic") -> np.ndarray:
    n = x.shape[0]
    ni, no = int(fade_in * SR), int(fade_out * SR)
    y = x.copy()
    if ni > 0:
        y[:ni] *= np.linspace(0, 1, ni)[:, None] if x.ndim == 2 else np.linspace(0, 1, ni)
    if no > 0:
        ramp = np.linspace(1, 0, no)
        if curve == "cubic":                     # easeOutCubic (descendant)
            ramp = 1 - (1 - ramp) ** 3 if False else (1 - np.linspace(0, 1, no)) ** 3
            ramp = np.clip(ramp, 0, 1)
        if x.ndim == 2:
            y[-no:] *= ramp[:, None]
        else:
            y[-no:] *= ramp
    return y


def ease_out_cubic_gain(n: int, start: float, end: float) -> np.ndarray:
    """gain 1->0 en easeOutCubic sur [start, end] secondes (pour un buffer donné)."""
    g = np.ones(n)
    i0, i1 = int(start * SR), min(int(end * SR), n)
    k = i1 - i0
    if k > 0:
        p = np.linspace(0, 1, k)
        g[i0:i1] = 1 - p ** 3       # easeOutCubic descendant
    g[i1:] = 0.0
    return g


def note_hz(semi_from_a4: float) -> float:
    return 440.0 * 2 ** (semi_from_a4 / 12.0)


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def hz(name: str) -> float:
    """'A4', 'C#5', 'Bb3' -> fréquence."""
    pitch = name[:-1].replace("♭", "b").replace("♯", "#")
    octave = int(name[-1])
    letter = pitch[0].upper()
    accidental = pitch[1:]
    letter = {"B": "B"}.get(letter, letter) if letter != "B" else "B"
    if accidental == "b":
        idx = (NOTE_NAMES.index(letter) - 1) % 12
    elif accidental == "#":
        idx = (NOTE_NAMES.index(letter) + 1) % 12
    else:
        idx = NOTE_NAMES.index(letter)
    semi = idx
    return 440.0 * 2 ** ((semi - 9) / 12 + (octave - 4))


# --------------------------------------------------------------------------- #
# percussions
# --------------------------------------------------------------------------- #
def kick(dur: float = 0.42, f0: float = 118.0, f1: float = 46.0, punch: float = 1.0) -> np.ndarray:
    t = t_axis(dur)
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.0)
    click = np.exp(-t * 900) * 0.35 * punch * np.random.default_rng(3).standard_normal(t.size)
    return np.tanh(1.4 * (body + click)) * 0.9


def rim(dur: float = 0.13, f: float = 1720.0) -> np.ndarray:
    t = t_axis(dur)
    rng = np.random.default_rng(11)
    tone = np.sin(2 * np.pi * f * t) * np.exp(-t * 55)
    noise = bp(rng.standard_normal(t.size), 1400, 5200) * np.exp(-t * 90) * 0.5
    return (tone + noise) * 0.5


def shaker(dur: float = 0.10, bright: float = 1.0) -> np.ndarray:
    t = t_axis(dur)
    rng = np.random.default_rng(23)
    n = rng.standard_normal(t.size)
    n = bp(n, 3800 * bright, 11000)
    return n * np.exp(-t * 46) * 0.75


def conga(dur: float = 0.22, f: float = 196.0) -> np.ndarray:
    t = t_axis(dur)
    bend = f * (1 + 0.35 * np.exp(-t * 45))
    body = np.sin(2 * np.pi * np.cumsum(bend) / SR) * np.exp(-t * 17)
    skin = bp(np.random.default_rng(31).standard_normal(t.size), 700, 2600) * np.exp(-t * 70) * 0.25
    return body * 0.8 + skin


def clap(dur: float = 0.24) -> np.ndarray:
    t = t_axis(dur)
    rng = np.random.default_rng(41)
    out = np.zeros(t.size)
    for delay, g in [(0.0, 1.0), (0.011, 0.7), (0.021, 0.5), (0.031, 0.35)]:
        i = int(delay * SR)
        seg = bp(rng.standard_normal(t.size - i), 900, 4200) * np.exp(-np.arange(t.size - i) / SR * 95)
        out[i:] += g * seg
    return out * 0.5


def agogo(dur: float = 0.35, base: float = 760.0) -> np.ndarray:
    """cloche métallique double — couleur maquis / highlife."""
    t = t_axis(dur)
    parts = [(1.0, 1.0), (2.41, 0.55), (3.83, 0.32), (5.72, 0.18)]
    y = np.zeros(t.size)
    for mult, g in parts:
        y += g * np.sin(2 * np.pi * base * mult * t) * np.exp(-t * (10 + 6 * mult))
    y += bp(np.random.default_rng(53).standard_normal(t.size), 3000, 9000) * np.exp(-t * 120) * 0.15
    return y * 0.45


def woodblock(dur: float = 0.12, f: float = 880.0) -> np.ndarray:
    t = t_axis(dur)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 60) * 0.7 + \
        np.sin(2 * np.pi * f * 2.7 * t) * np.exp(-t * 95) * 0.2


# --------------------------------------------------------------------------- #
# matières harmoniques
# --------------------------------------------------------------------------- #
def bass_note(freq: float, dur: float, bright: float = 0.55) -> np.ndarray:
    t = t_axis(dur)
    sub = np.sin(2 * np.pi * freq * t)
    saw = 2 * ((freq * t) % 1.0) - 1
    saw = lp(saw, 320 + 900 * bright)
    e = env(t.size, 0.006, 0.42, curve=3.0) * (0.55 + 0.45 * np.exp(-t * 3))
    return np.tanh((0.78 * sub + 0.42 * saw) * e) * 0.9


def balafon(freq: float, dur: float = 0.55, hard: float = 1.0) -> np.ndarray:
    """lame de bois frappée : FM courte + partiel de bois."""
    t = t_axis(dur)
    mod = np.sin(2 * np.pi * freq * 4.02 * t) * np.exp(-t * 26) * 1.6 * hard
    y = np.sin(2 * np.pi * freq * t + mod)
    y += 0.35 * np.sin(2 * np.pi * freq * 2.0 * t) * np.exp(-t * 16)
    y += 0.12 * bp(np.random.default_rng(59).standard_normal(t.size), 2000, 7000) * np.exp(-t * 180)
    return y * np.exp(-t * 6.5) * 0.55


def marimba_soft(freq: float, dur: float = 0.9) -> np.ndarray:
    t = t_axis(dur)
    y = np.sin(2 * np.pi * freq * t)
    y += 0.25 * np.sin(2 * np.pi * freq * 3.98 * t) * np.exp(-t * 12)
    y += 0.10 * np.sin(2 * np.pi * freq * 8.04 * t) * np.exp(-t * 26)
    return y * np.exp(-t * 3.6) * 0.45


def epiano(freq: float, dur: float = 1.2) -> np.ndarray:
    t = t_axis(dur)
    mod = np.sin(2 * np.pi * freq * 2.0 * t) * np.exp(-t * 3.2) * 1.1
    y = np.sin(2 * np.pi * freq * t + mod)
    return y * env(t.size, 0.004, 0.9, curve=4.5) * 0.4


def pluck_ks(freq: float, dur: float = 0.8, damp: float = 0.9965) -> np.ndarray:
    """corde pincée (Karplus-Strong) — couleur guitare de maquis."""
    n = int(dur * SR)
    N = max(2, int(round(SR / freq)))
    rng = np.random.default_rng(int(freq) % 997 + 7)
    buf = list(rng.uniform(-1, 1, N))
    out = np.empty(n)
    for i in range(n):
        v = buf.pop(0)
        out[i] = v
        buf.append(damp * 0.5 * (v + buf[0]))
    e = env(n, 0.002, 0.5, curve=4.0)
    return out * e * 0.5


def pad_chord(freqs, dur: float, attack: float = 0.6, release: float = 1.2) -> np.ndarray:
    t = t_axis(dur)
    y = np.zeros(t.size)
    for i, f in enumerate(freqs):
        for det in (-0.07, 0.0, 0.09):
            y += np.sin(2 * np.pi * f * (1 + det / 12) * t + i) * 0.33
    y = lp(y / max(1, len(freqs)), 1800)
    return y * env(t.size, attack, dur * 0.9, curve=2.2) * 0.32


def brass_stab(freqs, dur: float = 0.35) -> np.ndarray:
    t = t_axis(dur)
    y = np.zeros(t.size)
    for f in freqs:
        y += 2 * ((f * t) % 1.0) - 1
    y = lp(y / len(freqs), 2600)
    return np.tanh(1.6 * y * env(t.size, 0.02, 0.28, curve=5.0)) * 0.35


def sub_boom(dur: float = 0.9, f0: float = 78.0) -> np.ndarray:
    t = t_axis(dur)
    f = f0 * (1 + 0.5 * np.exp(-t * 12))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.4) * 0.7


# --------------------------------------------------------------------------- #
# foley de cuisine / salle (matières du secteur)
# --------------------------------------------------------------------------- #
def plate_set(dur: float = 0.55, base: float = 1150.0, gain: float = 1.0) -> np.ndarray:
    """assiette posée sur la table : modes de porcelaine + contact bref."""
    t = t_axis(dur)
    modes = [(1.0, 1.0, 16), (2.06, 0.62, 22), (3.19, 0.4, 28), (4.42, 0.22, 34)]
    y = np.zeros(t.size)
    for mult, g, d in modes:
        y += g * np.sin(2 * np.pi * base * mult * t + mult) * np.exp(-t * d)
    y += bp(np.random.default_rng(71).standard_normal(t.size), 500, 6000) * np.exp(-t * 260) * 1.1
    return np.tanh(y * 0.55) * gain * 0.6


def cutlery(dur: float = 0.45, gain: float = 1.0) -> np.ndarray:
    """couverts qui se touchent : aigus métalliques brefs, jamais stridents."""
    t = t_axis(dur)
    rng = np.random.default_rng(83)
    y = np.zeros(t.size)
    for f, g, d in [(3120, 1.0, 30), (4180, 0.7, 40), (5470, 0.45, 52), (2310, 0.5, 26)]:
        y += g * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t * d)
    y += bp(rng.standard_normal(t.size), 2500, 9000) * np.exp(-t * 200) * 0.4
    return lp(y, 9500) * gain * 0.34


def cutlery_sweep(dur: float = 0.40, up: bool = True, gain: float = 1.0) -> np.ndarray:
    """glissement de couvert / assiette qui sert de transition sectorielle."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(97)
    noise = rng.standard_normal(n)
    # filtre passe-bande balayé par blocs de 512 échantillons
    out = np.zeros(n)
    centers = np.geomspace(900, 6200, 12) if up else np.geomspace(6200, 900, 12)
    blk = int(np.ceil(n / 12))
    for i, c in enumerate(centers):
        seg = noise[i * blk:(i + 1) * blk]
        if seg.size == 0:
            break
        out[i * blk:i * blk + seg.size] = bp(seg, c * 0.7, min(c * 1.6, 20000))
    shape = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.4
    shimmer = 0.35 * np.sin(2 * np.pi * (2400 if up else 1800) * t) * np.exp(-t * 12)
    return (out * 0.9 + shimmer) * shape * gain * 0.45


def shaker_swell(dur: float = 0.55, gain: float = 1.0) -> np.ndarray:
    """roulement de shekere qui amène une transition."""
    t = t_axis(dur)
    rng = np.random.default_rng(101)
    grains = np.zeros(t.size)
    step = int(0.028 * SR)
    for i in range(0, t.size, step):
        amp = 0.35 + 0.65 * (i / t.size)
        seg = shaker(0.09) * amp
        grains[i:i + min(seg.size, t.size - i)] += seg[:min(seg.size, t.size - i)]
    del rng
    ramp = np.sin(np.pi * np.linspace(0, 1, t.size)) ** 1.2
    return grains * ramp * gain * 0.5


def plate_riser(dur: float = 0.6, gain: float = 1.0) -> np.ndarray:
    """montée de porcelaine (résonance + souffle) pour préparer un changement de plan."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(103)
    sweep_f = 300 * (6 ** (t / dur))
    tone = np.sin(2 * np.pi * np.cumsum(sweep_f) / SR) * 0.5
    air = bp(rng.standard_normal(n), 1200, 9000) * 0.5
    shape = (t / dur) ** 1.6
    return (tone + air) * shape * gain * 0.34


def heat_sizzle(dur: float = 4.0, gain: float = 1.0) -> np.ndarray:
    """grésillement de braise/plancha — disponible dans la bibliothèque,
    utilisé UNIQUEMENT sur un plan montrant réellement une cuisson."""
    t = t_axis(dur)
    rng = np.random.default_rng(107)
    base = bp(rng.standard_normal(t.size), 2400, 10000) * 0.35
    crackle = np.zeros(t.size)
    for _ in range(int(dur * 40)):
        p = rng.integers(0, t.size - 400)
        crackle[p:p + 400] += rng.uniform(0.2, 1.0) * hp(rng.standard_normal(400), 1800) * \
            np.exp(-np.arange(400) / SR * 260)
    y = base + crackle * 0.5
    mod = 0.7 + 0.3 * lp(rng.standard_normal(t.size), 4) * 6
    return np.clip(y * np.clip(mod, 0.3, 1.4), -1, 1) * gain * 0.35


def room_ambience(dur: float = 30.0, gain: float = 1.0, seed: int = 109) -> np.ndarray:
    """ambiance de salle de maquis : rumeur douce, vaisselle lointaine, aucune parole identifiable."""
    t = t_axis(dur)
    rng = np.random.default_rng(seed)
    murmur = lp(bp(rng.standard_normal(t.size), 180, 1400), 1200) * 0.30
    slow = 0.55 + 0.45 * lp(rng.standard_normal(t.size), 0.6) * 8
    murmur *= np.clip(slow, 0.2, 1.3)
    far = np.zeros(t.size)
    at = 1.7
    while at < dur - 1:
        g = rng.uniform(0.15, 0.4)
        seg = plate_set(0.5, base=rng.uniform(950, 1350)) * g
        i = int(at * SR)
        far[i:i + min(seg.size, far.size - i)] += seg[:min(seg.size, far.size - i)]
        at += rng.uniform(2.0, 4.2)
    return (murmur + far * 0.5) * gain


def service_cloth(dur: float = 0.5, gain: float = 1.0) -> np.ndarray:
    """mouvement de service : tissu + pas très léger, rasant le sol sonore."""
    t = t_axis(dur)
    rng = np.random.default_rng(113)
    cloth = bp(rng.standard_normal(t.size), 700, 4200) * np.sin(np.pi * t / dur) ** 2
    return lp(cloth, 5000) * gain * 0.22


# --------------------------------------------------------------------------- #
# mesure
# --------------------------------------------------------------------------- #
def db_to_gain(db: float) -> float:
    return 10 ** (db / 20.0)


def peak_db(x: np.ndarray) -> float:
    p = float(np.max(np.abs(x))) if x.size else 0.0
    return 20 * np.log10(max(p, 1e-12))


def rms_db(x: np.ndarray) -> float:
    r = float(np.sqrt(np.mean(x ** 2))) if x.size else 0.0
    return 20 * np.log10(max(r, 1e-12))


def normalize_peak(x: np.ndarray, target_db: float = -6.0) -> np.ndarray:
    return x * db_to_gain(target_db - peak_db(x))


# --------------------------------------------------------------------------- #
# égalisation hors-ligne (statique, zéro phase, FFT) — bus musique
# --------------------------------------------------------------------------- #
EQ_CURVE_HZ = np.array([20, 35, 50, 80, 140, 250, 400, 700, 1200, 2000,
                        3500, 6000, 10000, 16000, 22000], dtype=np.float64)
EQ_CURVE_DB = np.array([-40, -16, -9, -3.5, -1.5, -4.5, -4.0, 0.5, 3.0, 4.5,
                        5.5, 5.0, 2.2, 0.0, -4.0], dtype=np.float64)


def eq_gain_curve(freqs: np.ndarray, curve_hz=EQ_CURVE_HZ, curve_db=EQ_CURVE_DB) -> np.ndarray:
    return 10 ** (np.interp(freqs, curve_hz, curve_db) / 20.0)


def bus_eq(x: np.ndarray, curve_hz=EQ_CURVE_HZ, curve_db=EQ_CURVE_DB) -> np.ndarray:
    """EQ statique appliqué au bus musique (mono ou stéréo)."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        X = np.fft.rfft(x)
        f = np.fft.rfftfreq(x.size, 1 / SR)
        return np.fft.irfft(X * eq_gain_curve(f, curve_hz, curve_db), x.size)
    out = np.empty_like(x)
    for ch in range(x.shape[1]):
        out[:, ch] = bus_eq(x[:, ch], curve_hz, curve_db)
    return out
