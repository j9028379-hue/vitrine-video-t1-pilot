"""Contrôle objectif du mixage v2 (mesures, pas d'écoute subjective).

Vérifie : écrêtage, décalage continu, clics, niveaux par section, présence et placement
des quatre prises de voix, profondeur réelle du ducking, présence des deux effets,
et comparaison entre le WAV de mixage et l'audio réellement décodé depuis le MP4 livré.
"""
from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

import numpy as np

import loudness as Ld

SR = 48_000
AUDIO = Path(__file__).resolve().parent.parent
ROOT = AUDIO.parent
OUT = AUDIO / "metadata" / "qc_v2.json"


def read(path: Path, sr_expected: int = SR) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        sr, ch, n, sw = w.getframerate(), w.getnchannels(), w.getnframes(), w.getsampwidth()
        raw = w.readframes(n)
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    x = x.reshape(-1, ch)
    if sr != sr_expected:
        raise ValueError(f"{path}: {sr} Hz")
    return x


def decode_mp4(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "2", "-ar", "48000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).astype(np.float64)


def env_db(x: np.ndarray, win: float = 0.010) -> tuple[np.ndarray, float]:
    m = x.mean(axis=1)
    k = int(win * SR)
    n = m.size // k
    frames = m[:n * k].reshape(n, k)
    e = np.sqrt((frames ** 2).mean(axis=1))
    return 20 * np.log10(np.maximum(e, 1e-9)), win


def qc(track: str) -> dict:
    mix = read(AUDIO / "synced" / "v2" / f"mix_{track}.wav")
    voix = read(AUDIO / "synced" / "v2" / f"stems_{track}_voix.wav")
    mus = read(AUDIO / "synced" / "v2" / f"stems_{track}_musique.wav")
    eff = read(AUDIO / "synced" / "v2" / f"stems_{track}_effets.wav")

    peak = float(np.abs(mix).max())
    clipped = int(np.count_nonzero(np.abs(mix) >= 0.999))
    dc = float(mix.mean())
    # clics : cherche uniquement dans la tige voix (aucune percussion), seuil relatif à sa crête
    dv = np.abs(np.diff(voix.mean(axis=1)))
    seuil = 0.30 * float(np.abs(voix).max())
    clicks = int(np.count_nonzero(dv > seuil))
    transitoires = int(np.count_nonzero(np.abs(np.diff(mix.mean(axis=1))) > 0.25))
    e, win = env_db(mix)
    env_v, _ = env_db(voix)

    # plages de voix détectées (>= -26 dBFS, trous < 200 ms comblés)
    above = env_v > -26.0
    spans, start = [], None
    for i, a in enumerate(above):
        if a and start is None:
            start = i
        if not a and start is not None:
            if (i - start) * win * 1000 >= 120:
                spans.append((round(start * win, 2), round(i * win, 2)))
            start = None
    if start is not None:
        spans.append((round(start * win, 2), round(above.size * win, 2)))

    # profondeur du ducking : niveau musique pendant la voix vs hors voix
    in_v = np.zeros(mix.shape[0], dtype=bool)
    for a, b in spans:
        in_v[int(a * SR):int(b * SR)] = True
    m_db, _ = env_db(mus)
    per = int(0.05 / win)
    n_per = m_db.size // per
    m_blocks = m_db[:n_per * per].reshape(n_per, per).mean(axis=1)
    in_v_blocks = np.array([in_v[int(i * 0.05 * SR):int((i + 1) * 0.05 * SR)].mean() > 0.5 for i in range(n_per)])
    duck_level = float(np.median(m_blocks[in_v_blocks])) if in_v_blocks.any() else float("nan")
    open_level = float(np.median(m_blocks[~in_v_blocks])) if (~in_v_blocks).any() else float("nan")

    # effets : crête locale des 300 ms suivant chaque repère
    events = []
    for at, nom in [(2.10, "assiette posée (S1)"), (28.30, "tasse posée (S4)")]:
        seg = eff[int((at - 0.05) * SR):int((at + 0.30) * SR)]
        before = eff[int((at - 0.40) * SR):int((at - 0.06) * SR)]
        events.append({"a_s": at, "evenement": nom,
                       "crete_db": round(Ld.peak_db(seg), 1),
                       "avant_db": round(Ld.peak_db(before), 1),
                       "audible": bool(Ld.peak_db(seg) - Ld.peak_db(before) > 3.0)})

    mp4 = ROOT / "output" / f"output_T1_audio_demo_{track}.mp4"
    mp4_report = {}
    if mp4.is_file():
        dec = decode_mp4(mp4)
        a = mix.mean(axis=1)
        b = dec.mean(axis=1)
        n = min(a.size, b.size)
        # décalage par corrélation croisée (fenêtre 1 s au centre)
        c = np.correlate(b[int(10 * SR):int(11 * SR)], a[int(10 * SR):int(11 * SR)], mode="full")
        lag = int(np.argmax(c)) - (a[int(10 * SR):int(11 * SR)].size - 1)
        mp4_report = {
            "fichier": str(mp4.relative_to(ROOT)),
            "duree_s": round(dec.shape[0] / SR, 3),
            "lufs": round(Ld.integrated_lufs(dec[:, 0], SR), 2),
            "true_peak_db": round(Ld.true_peak_db(dec[:, 0], SR), 2),
            "ecart_wav_mp4_lufs": round(Ld.integrated_lufs(dec[:, 0], SR) - Ld.integrated_lufs(mix[:, 0], SR), 2),
            "decalage_audio_video_ms": round(lag / SR * 1000, 2),
        }

    return {
        "piste": track,
        "ecrêtage": clipped,
        "crete_db": round(20 * np.log10(peak), 2),
        "dc_offset": round(dc, 6),
        "transitoires_forts_tige_voix": clicks, "transitoires_percussifs": transitoires,
        "lufs": round(Ld.integrated_lufs(mix, SR), 2),
        "true_peak_db": round(Ld.true_peak_db(mix, SR), 2),
        "voix_detectees": spans,
        "ducking": {"musique_pendant_voix_db": round(duck_level, 1),
                    "musique_hors_voix_db": round(open_level, 1),
                    "profondeur_mesuree_db": round(duck_level - open_level, 1)},
        "effets": events,
        "mp4": mp4_report,
    }


def main() -> None:
    rep = {"SR": SR, "note": "contrôle objectif — aucune écoute subjective n'est possible depuis cet environnement",
           "pistes": [qc("A"), qc("B")]}
    OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for r in rep["pistes"]:
        print(f"Piste {r['piste']}: {r['lufs']} LUFS, TP {r['true_peak_db']} dB, écrêtage {r['ecrêtage']}, "
              f"clics {r['clics_detectes']}, ducking {r['ducking']['profondeur_mesuree_db']} dB, "
              f"voix {r['voix_detectees']}, effets {[e['audible'] for e in r['effets']]}")
    print("metadata/qc_v2.json écrit")


if __name__ == "__main__":
    main()
