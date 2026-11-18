"""Mixage de la démonstration T1 : voix synthétiques + musique (A ou B) + effets + ambiance.

Réglages V6.2 conservés : musique -6 dB (−16 dB sous la voix), effets -5 dB (−8 dB sous la voix),
seuil de ducking −26 dBFS, lookahead 80 ms, attaque 60 ms, hold 200 ms, relâchement 400 ms,
profondeur −10 dB, fondu 28,50 → 30,00 s.

Écrit :
  audio/synced/v2/mix_A.wav · mix_B.wav              (master du mixage)
  audio/synced/v2/stems_A_{voix,musique,effets}.wav  (tiges séparées)
  audio/metadata/mix_v2_report.json                  (mesures + journal de ducking)
"""
from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly

import ducking
import loudness as Ld

SR = 48_000
TOTAL = 30.0
HERE = Path(__file__).resolve().parent
AUDIO = HERE.parent

# Où tombe chaque prise de parole dans les 30 s (fenêtres des scènes 0-6, 6-14, 14-21, 21-30)
VOIX_PLAN = [(1, 1.20), (2, 6.80), (3, 14.70), (4, 21.80)]
# Effets : uniquement là où une action est visible dans le montage
EFFETS_PLAN = [
    ("sfx/sfx_01_assiette_posee.wav", 2.10, -5.0, "l'assiette est posée sur la table (S1)"),
    ("sfx/sfx_01_assiette_posee.wav", 28.30, -9.0, "la tasse est posée sur le comptoir (fin S4)"),
]
AMBIANCE = ("ambience/ambiance_maquis_salle_30s.wav", -32.0, "salle du restaurant, présent du début à la fin")


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        sr, ch, n, sw = w.getframerate(), w.getnchannels(), w.getnframes(), w.getsampwidth()
        raw = w.readframes(n)
    if sw != 2:
        raise ValueError(f"{path} : attendu 16 bits, trouvé {sw*8} bits")
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    x = x.reshape(-1, ch).mean(axis=1) if ch > 1 else x
    if sr != SR:
        g = np.gcd(sr, SR)
        x = resample_poly(x, SR // g, sr // g)
    return x


def fit(x: np.ndarray, n: int) -> np.ndarray:
    if x.size >= n:
        return x[:n]
    return np.concatenate([x, np.zeros(n - x.size)])


def place(buf: np.ndarray, sig: np.ndarray, at: float, gain_db: float = 0.0) -> None:
    i0 = int(round(at * SR))
    if i0 >= buf.size:
        return
    n = min(sig.size, buf.size - i0)
    buf[i0:i0 + n] += sig[:n] * 10 ** (gain_db / 20.0)


def build(track: str) -> dict:
    n = int(round(TOTAL * SR))

    # ---------------- voix (bus) ----------------
    voix = np.zeros(n)
    voix_detail = []
    for num, at in VOIX_PLAN:
        x = fit(read_wav(AUDIO / "voice" / f"voix_fr_scene{num}.wav"), n)
        x = x / max(np.abs(x).max(), 1e-9) * 10 ** (-3.0 / 20.0)   # crête -3 dBFS par prise
        place(voix, x, at)
        voix_detail.append({"scene": num, "debut_s": at, "duree_s": round(len(x) / SR, 3)})

    # ---------------- musique ----------------
    music_file = AUDIO / "music" / "v2" / (
        "music_A_adjapiano_maquis_30s.wav" if track == "A" else "music_B_gangan_acoustique_30s.wav")
    music = fit(read_wav(music_file), n)
    music = music / max(np.abs(music).max(), 1e-9) * 10 ** (-3.5 / 20.0)

    # ---------------- effets + ambiance ----------------
    sfx = np.zeros(n)
    for rel, at, gain_db, pourquoi in EFFETS_PLAN:
        place(sfx, fit(read_wav(AUDIO / rel), n), at, gain_db)
    amb_rel, amb_gain, _ = AMBIANCE
    amb = fit(read_wav(AUDIO / amb_rel), n)
    amb = amb / max(np.abs(amb).max(), 1e-9) * 10 ** (amb_gain / 20.0)
    sfx = sfx + amb

    # ---------------- ducking (V6.2) ----------------
    curve, journal = ducking.gain_curve(voix, total_s=TOTAL)
    curve = curve[:n] if curve.size >= n else np.pad(curve, (0, n - curve.size))
    music_duck = music * curve * 10 ** (-6.0 / 20.0)
    sfx_duck = sfx * (curve ** 0.8) * 10 ** (-5.0 / 20.0)

    # ---------------- bus master ----------------
    comp = Ld.compressor(music_duck, sr=SR, threshold_db=-20.0, ratio=2.6)
    mix = voix + comp + sfx_duck
    # Loudness mesurée sur le bus STÉRÉO (deux canaux identiques = +3 dB par rapport au mono)
    target = -16.0
    stereo = np.stack([mix, mix], axis=1)
    limited = stereo
    for _ in range(4):                       # le limiteur et le fondu font baisser le LUFS mesuré
        lufs = Ld.integrated_lufs(limited, SR)
        if abs(lufs - target) < 0.15:
            break
        limited = Ld.limiter(limited * 10 ** ((target - lufs) / 20.0),
                            ceiling_db=-3.6, sr=SR, lookahead=0.010, release=0.120)
    # fondu final 28,50 → 30,00 s
    i0 = int(28.5 * SR)
    fade = np.ones(n)
    fade[i0:] = np.linspace(1.0, 0.0, n - i0) ** 1.3
    limited = limited * fade[:, None]

    out = AUDIO / "synced" / "v2"
    out.mkdir(parents=True, exist_ok=True)
    write_wav(out / f"mix_{track}.wav", limited)
    write_wav(out / f"stems_{track}_voix.wav", np.stack([voix, voix], axis=1))
    write_wav(out / f"stems_{track}_musique.wav", np.stack([music_duck, music_duck], axis=1))
    write_wav(out / f"stems_{track}_effets.wav", np.stack([sfx_duck, sfx_duck], axis=1))

    def seg(a: float, b: float) -> dict:
        s = limited[int(a * SR):int(b * SR)]
        v = voix[int(a * SR):int(b * SR)]
        return {"lufs": round(Ld.integrated_lufs(s, SR), 2),
                "crete_db": round(Ld.peak_db(s), 2),
                "voix_lufs": round(Ld.integrated_lufs(v, SR), 2) if np.any(v) else None}

    return {
        "piste": track,
        "musique": music_file.name,
        "duree_s": TOTAL,
        "grille_bpm": 120,
        "gains_v62": {"musique_db": -6.0, "musique_sous_voix_db": -16.0,
                      "effets_db": -5.0, "effets_sous_voix_db": -8.0, "ambiance_db": -32.0},
        "voix": voix_detail,
        "effets": [{"fichier": r, "a_s": a, "gain_db": g, "justification": w} for r, a, g, w in EFFETS_PLAN],
        "ambiance": {"fichier": amb_rel, "gain_db": amb_gain},
        "ducking": journal,
        "master": {
            "lufs_integrated": round(Ld.integrated_lufs(limited, SR), 2),
            "true_peak_db": round(Ld.true_peak_db(limited, SR), 2),
            "crete_db": round(Ld.peak_db(limited), 2),
            "plafond_db": -3.6,
            "compression": "une seule fois, seuil -20 dB / ratio 2,6 avant la boucle de gain",
        },
        "sections": {f"{a}-{b} s": seg(a, b) for a, b in [(0, 6), (6, 14), (14, 21), (21, 28.5), (28.5, 30)]},
    }


def write_wav(path: Path, x: np.ndarray) -> None:
    x = np.clip(x, -1.0, 1.0)
    pcm = np.round(x * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(x.shape[1]); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"  {path.relative_to(AUDIO.parent)}  {x.shape[0]/SR:.3f} s  pic {Ld.peak_db(x):+.1f} dBFS")


def main() -> None:
    reports = [build("A"), build("B")]
    (AUDIO / "metadata" / "mix_v2_report.json").write_text(
        json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for r in reports:
        print(f"Piste {r['piste']} : {r['master']['lufs_integrated']} LUFS · TP {r['master']['true_peak_db']} dB · "
              f"ducking {r['ducking']['duree_ducking_s']} s (profondeur {r['ducking']['gain_min_db']} dB)")


if __name__ == "__main__":
    main()
