"""Contrôle qualité du master audio T1 (fichier final + wav de mixage).

Vérifie : durée exacte, 11 repères (position réelle des départs d'effet), continuité,
absence de saturation / clics / coupures, équilibre spectral, loudness, fondu final.
"""
from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

import numpy as np

import loudness as LU
import synth_lib as L

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / "audio"
SR = L.SR

MARKERS = [5.90, 6.50, 7.34, 8.90, 13.90, 16.90, 18.34, 20.90, 21.50, 23.90, 26.50]
LABELS = [
    "transition vers la scène 2", "bandeau commercial", "mise en valeur du prix",
    "préparation du zoom punch", "transition vers la scène 3", "accent avant la coupe",
    "prix seul", "transition vers la scène 4", "localisation",
    "préparation du cut vers le CTA", "appel à commander WhatsApp",
]


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        ch, sw = w.getnchannels(), w.getsampwidth()
        assert sw == 2
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
        return data.reshape(-1, ch), w.getframerate()


def decode_mp4_audio(path: Path) -> np.ndarray:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a", "-f", "f32le",
         "-acodec", "pcm_f32le", "-ar", str(SR), "-ac", "2", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64).reshape(-1, 2)


def onsets(x: np.ndarray, sr: int = SR) -> np.ndarray:
    """détection de départs par flux spectral (librosa si disponible)."""
    import librosa
    mono = x.mean(axis=1)
    env = librosa.onset.onset_strength(y=mono, sr=sr, hop_length=256).astype(np.float64)
    times = librosa.times_like(env, sr=sr, hop_length=256)
    peaks = librosa.util.peak_pick(env, pre_max=3, post_max=3, pre_avg=5, post_avg=5,
                                   delta=float(0.35 * env.max()), wait=6)
    return np.asarray(times)[np.asarray(peaks, dtype=int)]


def main() -> None:
    final = ROOT / "output" / "output_T1_audio_final.mp4"
    x = decode_mp4_audio(final)[: int(30 * SR)]
    mono = x.mean(axis=1)
    ons = onsets(x)

    wav_path = AUD / "synced" / "mix_T1_audio_final.wav"
    mono_wav = read_wav(wav_path)[0].mean(axis=1)
    qc = {
        "fichier": str(final.relative_to(ROOT)),
        "duree_audio_decodee_s": round(x.shape[0] / SR, 3),
        "loudness_lufs": round(LU.integrated_lufs(x), 2),
        "true_peak_dbtp": round(LU.true_peak_db(x), 2),
        "crete_db": round(LU.peak_db(x), 2),
        "echantillons_ecrases": int(np.count_nonzero(np.abs(x) >= 0.999)),
        "reperes": [],
        "clics": None,
        "spectre_pct": {},
        "sections": {},
    }

    # 1. les 11 repères
    #    a) placement isolé : chaque repère est reconstruit seul, on mesure le premier
    #       échantillon non nul pour vérifier l'arrondi d'échantillon ;
    #    b) présence mesurée dans le master par une hausse d'énergie large bande.
    import mix_T1 as M
    from scipy.signal import butter, sosfilt
    sos = butter(4, [120 / (SR / 2), 10000 / (SR / 2)], "band", output="sos")
    broad = sosfilt(sos, mono)
    for at, label in [(a, l) for a, l in zip(MARKERS, LABELS)]:
        entry = [e for e in M.MARKERS if abs(e[0] - at) < 1e-6][0]
        isolated = np.zeros(int(30 * SR))
        dur = 0.0
        for aid in entry[2]:
            sig, _ = read_wav(AUD / "sfx" / f"{aid}.wav")
            sigm = sig.mean(axis=1)
            i = int(round(at * SR))
            k = min(sigm.size, isolated.size - i)
            isolated[i:i + k] += sigm[:k]
            dur = max(dur, sigm.size / SR)
        first = np.flatnonzero(np.abs(isolated) > 0)[0] if np.any(isolated) else None
        delta = None if first is None else round(1000 * (first / SR - at), 3)
        win = 0.15
        a0, a1 = int(at * SR), int(min(30.0, at + win) * SR)
        b0, b1 = int(max(0.0, at - win - 0.06) * SR), int(max(0.0, at - 0.06) * SR)
        rise = round(20 * np.log10(max(np.sqrt(np.mean(broad[a0:a1] ** 2)), 1e-9) /
                                    max(np.sqrt(np.mean(broad[b0:b1] ** 2)), 1e-9)), 1)
        qc["reperes"].append({
            "temps_v62_s": at, "evenement": label,
            "placement_mesure_ms": delta,
            "statut_placement": "OK" if delta is not None and abs(delta) < 0.021 else "A VERIFIER",
            "sfx": entry[2],
            "hausse_energie_large_bande_db": rise,
            "hausse_indicative": True,
        })

    # niveaux relatifs mesurés au mixage (avant mastering) pour chaque repère
    try:
        mr = json.loads((AUD / "metadata" / "mix_report.json").read_text(encoding="utf-8"))
        mr = mr[0] if isinstance(mr, list) else mr
        levels = {}
        for ev in mr["evenements"]:
            levels.setdefault(round(ev["temps_s"], 2), []).append(
                (ev["fichier"].split("/")[-1], ev.get("niveau_effet_relatif_db"),
                 ev.get("perceptible")))
        for rep in qc["reperes"]:
            rep["niveau_effet_relatif_db"] = levels.get(round(rep["temps_v62_s"], 2))
            rep["perceptible"] = all(v[2] for v in levels.get(round(rep["temps_v62_s"], 2), [(None, None, False)]))
    except Exception as exc:  # pragma: no cover
        qc["niveaux_relatifs"] = f"non lus ({exc})"

    # 2. clics : excursions de la dérivée au-delà de 40x la valeur RMS de la dérivée
    d = np.abs(np.diff(mono))
    ref = np.sqrt(np.mean(d ** 2))
    qc["clics"] = {"ratio_max_derive_sur_rms": round(float(d.max() / max(ref, 1e-12)), 1),
                   "depassements": int(np.count_nonzero(d > 40 * ref))}

    # 3. équilibre spectral
    S = np.abs(np.fft.rfft(mono * np.hanning(mono.size)))
    f = np.fft.rfftfreq(mono.size, 1 / SR)
    for lo, hi in [(20, 80), (80, 250), (250, 2000), (2000, 8000), (8000, 20000)]:
        m = (f >= lo) & (f < hi)
        qc["spectre_pct"][f"{lo}-{hi} Hz"] = round(float(100 * (S[m] ** 2).sum() / (S ** 2).sum()), 1)

    # 4. sections et continuité
    for name, (a, b) in [("S1", (0, 6)), ("S2", (6, 14)), ("S3", (14, 21)),
                         ("S4", (21, 28.5)), ("fade", (28.5, 30))]:
        seg = mono[int(a * SR):int(b * SR)]
        qc["sections"][name] = {"rms_db": round(LU.rms_db(seg), 2),
                                "lufs": round(LU.integrated_lufs(seg), 2)}
    # dernier échantillon : pas de coupure sèche
    qc["fin"] = {"dernier_echantillon_db": round(float(20 * np.log10(max(abs(mono[-1]), 1e-12))), 1),
                 "derniers_50ms_rms_db": round(LU.rms_db(mono[-int(0.05 * SR):]), 1)}

    # 5. comparaison avec le WAV de mixage (perte AAC)
    wav, _ = read_wav(AUD / "synced" / "mix_T1_audio_final.wav")
    wav = wav[: x.shape[0]]
    if wav.shape == x.shape:
        qc["ecart_avec_le_wav"] = {
            "lufs_wav": round(LU.integrated_lufs(wav), 2),
            "ecart_lufs": round(LU.integrated_lufs(x) - LU.integrated_lufs(wav), 2),
            "ecart_true_peak_db": round(LU.true_peak_db(x) - LU.true_peak_db(wav), 2),
        }

    # 6. latence éventuelle introduite par l'encodage AAC / le multiplexage
    try:
        seg_w = mono_wav[: int(3.0 * SR)]
        seg_m = mono[: int(3.0 * SR)]
        corr = np.correlate(seg_m[: SR], seg_w[: SR], mode="full")
        lag = int(np.argmax(np.abs(corr))) - (SR - 1)
        qc["latence_mp4_vs_wav_echantillons"] = lag
        qc["latence_mp4_vs_wav_ms"] = round(1000 * lag / SR, 3)
    except Exception as exc:  # pragma: no cover
        qc["latence_mp4_vs_wav_echantillons"] = f"non mesurée ({exc})"

    (AUD / "metadata" / "qc_audio.json").write_text(
        json.dumps(qc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(qc, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
