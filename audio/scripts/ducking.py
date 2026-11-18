"""Ducking V6.2 — détecteur de voix et courbe de gain musique.

Paramètres imposés : seuil -26 dBFS (enveloppe RMS fenêtre 10 ms), lookahead 80 ms,
attaque 60 ms (rampe linéaire), hold 200 ms, relâchement 400 ms (easeOutCubic),
profondeur -10 dB (musique -6 dB -> -16 dB).
Une scène n'est « parlée » que si la voix cumule >= 400 ms au-dessus du seuil.
"""
from __future__ import annotations

import numpy as np

SR = 48_000
WIN_S = 0.010
THRESH_DB = -26.0
LOOKAHEAD = 0.080
ATTACK = 0.060
HOLD = 0.200
RELEASE = 0.400
DEPTH_DB = -10.0
SCENE_MIN_VOICE = 0.400


def rms_envelope(voice: np.ndarray, win_s: float = WIN_S, sr: int = SR) -> tuple[np.ndarray, int]:
    """enveloppe RMS par fenêtre de 10 ms (pas = fenêtre)."""
    if voice.ndim == 2:
        voice = voice.mean(axis=1)
    win = max(1, int(win_s * sr))
    n = int(np.ceil(voice.size / win))
    padded =np.zeros(n * win)
    padded[:voice.size] = voice
    frames = padded.reshape(n, win)
    env = np.sqrt(np.mean(frames ** 2, axis=1))
    return env, win


def detect_voice(voice: np.ndarray, sr: int = SR) -> dict:
    env, win = rms_envelope(voice, sr=sr)
    env_db = 20 * np.log10(np.maximum(env, 1e-12))
    above = env_db > THRESH_DB
    voiced_s = float(np.count_nonzero(above) * win / sr)
    # fusion des trous plus courts que le hold, pour ne pas pomper entre deux mots
    hold_frames = int(round(HOLD / (win / sr)))
    merged = above.copy()
    i = 0
    while i < merged.size:
        if not merged[i]:
            j = i
            while j < merged.size and not merged[j]:
                j += 1
            if 0 < i and j < merged.size and (j - i) <= hold_frames:
                merged[i:j] = True
            i = j
        else:
            i += 1
    return {
        "env_db": env_db, "hop_s": win / sr, "voiced_s": voiced_s,
        "voiced_ratio": voiced_s / (voice.size / sr), "merged": merged,
        "scene_parlee": voiced_s >= SCENE_MIN_VOICE,
    }


def gain_curve(voice: np.ndarray, total_s: float = 30.0, sr: int = SR) -> tuple[np.ndarray, dict]:
    """courbe de gain musique (linéaire, par échantillon) + journal des paramètres.

    1. détection RMS 10 ms au seuil -26 dBFS, trous < hold comblés ;
    2. chaque fenêtre parlée est étendue de 80 ms en amont (lookahead) et 200 ms en aval (hold) ;
    3. attaque linéaire 60 ms, maintien, relâchement easeOutCubic 400 ms, profondeur -10 dB.
    """
    info = detect_voice(voice, sr=sr)
    hop = info["hop_s"]
    n_total = int(round(total_s * sr))
    mask = np.zeros(n_total, dtype=bool)
    la = LOOKAHEAD
    hold = HOLD
    for k in np.flatnonzero(info["merged"]):
        t0 = max(0.0, k * hop - la)
        t1 = min(total_s, (k + 1) * hop + hold)
        mask[int(t0 * sr):int(t1 * sr)] = True

    # segments d'activité
    edges = np.flatnonzero(np.diff(mask.astype(np.int8)) != 0) + 1
    bounds = np.concatenate(([0], edges, [n_total]))
    smooth_db = np.zeros(n_total)
    a_len = max(1, int(ATTACK * sr))
    r_len = max(1, int(RELEASE * sr))
    for i in range(len(bounds) - 1):
        s0, s1 = bounds[i], bounds[i + 1]
        if mask[s0]:                      # segment actif : attaque depuis le niveau courant
            n = s1 - s0
            prev = smooth_db[s0 - 1] if s0 > 0 else 0.0
            ramp = min(a_len, n)
            smooth_db[s0:s0 + ramp] = np.linspace(prev, DEPTH_DB, ramp, endpoint=False)
            smooth_db[s0 + ramp:s1] = DEPTH_DB
        else:                             # segment inactif : relâchement easeOutCubic
            n = s1 - s0
            ramp = min(r_len, n)
            p = np.linspace(0, 1, ramp, endpoint=False) if ramp else np.array([])
            start_level = smooth_db[s0 - 1] if s0 > 0 else 0.0
            smooth_db[s0:s0 + ramp] = start_level * (1 - p) ** 3
            smooth_db[s0 + ramp:s1] = 0.0

    journal = {
        "seuil_db": THRESH_DB, "fenetre_enveloppe_ms": WIN_S * 1000,
        "lookahead_ms": LOOKAHEAD * 1000, "attaque_ms": ATTACK * 1000,
        "hold_ms": HOLD * 1000, "relachement_ms": RELEASE * 1000, "profondeur_db": DEPTH_DB,
        "scene_parlee": info["scene_parlee"], "voix_cumulee_s": round(info["voiced_s"], 3),
        "voix_ratio": round(info["voiced_ratio"], 3),
        "gain_min_db": round(float(smooth_db.min()), 2),
        "gain_max_db": round(float(smooth_db.max()), 2),
        "duree_ducking_s": round(float(np.count_nonzero(smooth_db < -0.5)) / sr, 2),
        "duree_pleine_profondeur_s": round(float(np.count_nonzero(smooth_db < -9.5)) / sr, 2),
    }
    return 10 ** (smooth_db / 20.0), journal
