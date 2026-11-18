"""Mesures normalisées : loudness intégrée ITU-R BS.1770-4, true peak 4x, détection de clics."""
from __future__ import annotations

import numpy as np
from scipy import signal

SR = 48_000


def k_weight(x: np.ndarray, sr: int = SR) -> np.ndarray:
    """Filtre K (shelf + RLB) de BS.1770-4, appliqué par canal."""
    # étage 1 : shelf aigu (pré-filtre)
    f0, G, Q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    A = 10 ** (G / 40.0)
    w0 = 2 * np.pi * f0 / sr
    alpha = np.sin(w0) / (2 * Q)
    b0 = A * ((A + 1) + (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha)
    b1 = -2 * A * ((A - 1) + (A + 1) * np.cos(w0))
    b2 = A * ((A + 1) + (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha)
    a0 = (A + 1) - (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha
    a1 = 2 * ((A - 1) - (A + 1) * np.cos(w0))
    a2 = (A + 1) - (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha
    b1s = np.array([b0, b1, b2]) / a0
    a1s = np.array([a0, a1, a2]) / a0
    # étage 2 : RLB passe-haut
    f0, Q = 38.13547087602444, 0.5003270373238773
    w0 = 2 * np.pi * f0 / sr
    alpha = np.sin(w0) / (2 * Q)
    b0, b1, b2 = [1, -2, 1]
    a0 = 1 + alpha
    a1, a2 = -2 * np.cos(w0), 1 - alpha
    b2s = np.array([b0, b1, b2]) / a0
    a2s = np.array([a0, a1, a2]) / a0
    y = signal.lfilter(b1s, a1s, x, axis=0)
    y = signal.lfilter(b2s, a2s, y, axis=0)
    return y


def integrated_lufs(x: np.ndarray, sr: int = SR, block: float = 0.4, hop: float = 0.1) -> float:
    if x.ndim == 1:
        x = x[:, None]
    y = k_weight(x, sr)
    n = int(block * sr)
    h = int(hop * sr)
    if y.shape[0] < n:
        return -70.0
    powers = []
    for i in range(0, y.shape[0] - n + 1, h):
        seg = y[i:i + n]
        powers.append(float(np.mean(np.sum(seg ** 2, axis=1))))
    powers = np.array(powers)
    lufs = -0.691 + 10 * np.log10(np.maximum(powers, 1e-20))
    # gating absolu puis relatif
    keep = lufs > -70.0
    if not np.any(keep):
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(powers[keep])) - 10.0
    keep2 = keep & (lufs > rel)
    if not np.any(keep2):
        return float(np.mean(lufs[keep]))
    return float(-0.691 + 10 * np.log10(np.mean(powers[keep2])))


def true_peak_db(x: np.ndarray, sr: int = SR, factor: int = 4) -> float:
    if x.ndim == 1:
        x = x[:, None]
    up = signal.resample_poly(x, factor, 1, axis=0)
    return float(20 * np.log10(max(np.max(np.abs(up)), 1e-12)))


def peak_db(x: np.ndarray) -> float:
    return float(20 * np.log10(max(np.max(np.abs(x)), 1e-12)))


def rms_db(x: np.ndarray) -> float:
    return float(20 * np.log10(max(np.sqrt(np.mean(np.asarray(x) ** 2)), 1e-12)))


def limiter(x: np.ndarray, ceiling_db: float = -1.0, sr: int = SR,
            lookahead: float = 0.005, release: float = 0.100) -> np.ndarray:
    """limiteur avec anticipation : garantit |sortie| <= plafond (stéréo lié)."""
    from scipy.ndimage import minimum_filter1d
    from scipy.signal import lfilter

    ceiling = 10 ** (ceiling_db / 20.0)
    x = np.asarray(x, dtype=np.float64)
    mono = np.max(np.abs(x), axis=1) if x.ndim == 2 else np.abs(x)
    need = np.minimum(1.0, ceiling / np.maximum(mono, 1e-9))
    k = max(3, int(lookahead * sr))
    pre = minimum_filter1d(need, size=k, mode="nearest")
    # relâchement exponentiel du gain (attaque déjà anticipée par le filtre minimum)
    a = np.exp(-1.0 / (release * sr))
    smooth = lfilter([1 - a], [1, -a], pre)
    g = np.minimum(pre, smooth)
    return x * g[:, None] if x.ndim == 2 else x * g


def compressor(x: np.ndarray, sr: int = SR, threshold_db: float = -20.0, ratio: float = 2.6,
               attack: float = 0.010, release: float = 0.150, knee_db: float = 6.0) -> np.ndarray:
    """compresseur de bus doux (stéréo lié) — maîtrise le facteur de crête des percussions."""
    x = np.asarray(x, dtype=np.float64)
    mono = np.max(np.abs(x), axis=1) if x.ndim == 2 else np.abs(x)
    a = np.exp(-1.0 / (attack * sr))
    r = np.exp(-1.0 / (release * sr))
    env = np.empty(mono.size)
    e = 0.0
    for i in range(mono.size):
        coef = a if mono[i] > e else r
        e = coef * e + (1 - coef) * mono[i]
        env[i] = e
    level_db = 20 * np.log10(np.maximum(env, 1e-9))
    over = level_db - threshold_db
    gain_db = np.where(over <= -knee_db / 2, 0.0,
                       np.where(over >= knee_db / 2, -(over * (1 - 1 / ratio)),
                                -((over + knee_db / 2) ** 2) / (2 * knee_db) * (1 - 1 / ratio)))
    g = 10 ** (gain_db / 20.0)
    return x * g[:, None] if x.ndim == 2 else x * g


def soft_clip(x: np.ndarray, drive: float = 1.0) -> np.ndarray:
    return np.tanh(x * drive) / np.tanh(drive)
