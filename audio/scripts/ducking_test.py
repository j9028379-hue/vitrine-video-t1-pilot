"""Test séparé du ducking V6.2 — avec un SIGNAL DE TEST, pas une voix.

Les rushs de démonstration ne contiennent aucune piste audio (voir rapport) : aucune voix
réelle n'existe pour ce master. On ne fabrique donc pas de voix dans le film. Le mécanisme
de ducking est vérifié ici sur un signal de test parlé synthétique (formants + syllabes),
explicitement identifié comme signal de test, afin de mesurer seuil, attaque, hold,
relâchement, profondeur et baisse des effets pendant la parole.
"""
from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np
from scipy import signal

import ducking
import loudness as LU
import synth_lib as L

ROOT = Path(__file__).resolve().parents[1]
SR = L.SR


def speech_like(total: float = 30.0, seed: int = 5) -> np.ndarray:
    """signal de test « parole » : formants balayés, syllabes 180–260 ms, pauses réelles."""
    rng = np.random.default_rng(seed)
    n = int(total * SR)
    out = np.zeros(n)
    # phrases (début, fin) en secondes : la scène 3 est parlée, les autres non
    phrases = [(0.60, 3.20), (3.90, 5.60), (14.60, 17.40), (18.10, 20.30), (24.30, 25.20)]
    for start, end in phrases:
        t = start
        while t < end - 0.18:
            dur = float(rng.uniform(0.18, 0.26))
            f0 = float(rng.uniform(108, 138))
            tt = np.arange(int(dur * SR)) / SR
            # source glottique en dents de scie + bruit
            src = 2 * ((f0 * tt) % 1.0) - 1
            src += 0.02 * rng.standard_normal(tt.size)
            # trois formants mobiles (voyelles)
            f1 = rng.uniform(420, 780)
            f2 = rng.uniform(1000, 2100)
            f3 = rng.uniform(2400, 3000)
            y = np.zeros(tt.size)
            for fc, bw, g in [(f1, 110, 1.0), (f2, 130, 0.6), (f3, 180, 0.3)]:
                b, a = signal.iirpeak(fc / (SR / 2), fc / bw)
                y += g * signal.lfilter(b, a, src)
            env = np.minimum(1, np.minimum(np.arange(tt.size) / (0.02 * SR),
                                          (tt.size - np.arange(tt.size)) / (0.03 * SR)))
            y = y / max(np.abs(y).max(), 1e-9) * env
            i = int(t * SR)
            if i + y.size < n:
                out[i:i + y.size] += y * rng.uniform(0.28, 0.42)
            t += dur + float(rng.uniform(0.03, 0.10))
    return out * 0.9


def write_wav(path: Path, x: np.ndarray) -> None:
    x = np.clip(x, -1, 1)
    pcm = np.array([np.round(x * 32767)] * 2).T.astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def burst_test() -> dict:
    """test unitaire du détecteur : une salve de 500 ms à -20 dBFS dans du silence."""
    sr = SR
    voice = np.zeros(int(6.0 * sr))
    t = np.arange(int(0.5 * sr)) / sr
    burst = np.sin(2 * np.pi * 220 * t) * 0.25 * (np.hanning(t.size) ** 0.3)
    voice[int(2.0 * sr):int(2.0 * sr) + burst.size] = burst
    gain, _ = ducking.gain_curve(voice, 6.0)
    g_db = 20 * np.log10(np.maximum(gain, 1e-9))
    i_on = int(2.0 * sr)
    i_off = int(2.5 * sr)
    g_prior = g_db[:i_on]
    # début de la descente (anticipation) et fin de la descente
    d0 = int(np.argmax(g_prior < -0.5))
    d1 = int(np.argmax(g_db < -9.5))
    tail = g_db[i_off:]
    r1 = i_off + int(np.argmax(tail > -1.0))
    r_zero = i_off + int(np.argmax(tail >= -0.01))
    return {
        "avance_de_la_descente_ms": round(1000 * (i_on - d0) / sr, 1),
        "duree_de_la_descente_ms": round(1000 * (d1 - d0) / sr, 1),
        "profondeur_atteinte_db": round(float(g_db[i_on:i_off].min()), 2),
        "relachement_jusqu_a_moins_1_db_ms": round(1000 * (r1 - i_off) / sr, 1),
        "retour_complet_a_0_db_ms": round(1000 * (r_zero - i_off) / sr, 1),
        "commentaire": "avance = lookahead 80 ms ; descente = attaque 60 ms ; "
                       "retour = hold 200 ms + relâchement easeOutCubic 400 ms",
    }


def section_report(gain: np.ndarray) -> dict:
    g_db = 20 * np.log10(np.maximum(gain, 1e-9))
    out = {}
    for name, (a, b) in [("S1", (0, 6)), ("S2", (6, 14)), ("S3", (14, 21)), ("S4", (21, 30))]:
        seg = g_db[int(a * SR):int(b * SR)]
        out[name] = {"gain_moyen_db": round(float(seg.mean()), 2),
                     "gain_min_db": round(float(seg.min()), 2)}
    return out


def main() -> None:
    voice = speech_like()
    voice = voice / max(np.abs(voice).max(), 1e-9) * L.db_to_gain(-13.0)
    write_wav(ROOT / "synced" / "ducking_test_signal_de_test.wav", voice)

    gain, journal = ducking.gain_curve(voice, L.TOTAL)
    steps = {"burst_test": burst_test(), "par_scene_signal_de_test": section_report(gain)}

    import mix_T1 as M
    mixed, report = M.build("maquis_afro_A_braise", voice)
    write_wav(ROOT / "synced" / "ducking_test_T1_pisteA_avec_signal.wav", mixed)

    # contrôle : sans voix, aucune baisse de musique (règle V6.2)
    sans_voix, report_sv = M.build("maquis_afro_A_braise", None)
    music = M.load_stereo(ROOT / "music" / "maquis_afro_A_braise_mix_30s.wav")
    assert report_sv["ducking"] is None

    result = {
        "nature_du_fichier_test": "signal de test parlé synthétique (formants) — PAS une voix, "
                                  "aucune voix artificielle n'est intégrée au master",
        "parametres_v62": journal,
        "mesures": steps,
        "controle_sans_voix": {
            "ducking_applique": False,
            "note": "music bus constant à -6 dB : la musique ne baisse pas sans voix détectée",
        },
        "controle_avec_signal": {
            "musique_nominale_db": report["gains_db"]["musique_nominale"],
            "musique_pendant_parole_db": report["gains_db"]["musique_pendant_voix"],
            "effets_nominal_db": report["gains_db"]["effets"],
            "effets_pendant_parole_db": report["gains_db"]["effets_pendant_voix"],
            "lufs_du_mixage_de_test": report["loudness"]["apres_lufs"],
            "true_peak_test": report["loudness"]["true_peak_dbtp"],
        },
    }
    (ROOT / "metadata" / "ducking_test.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # planche de contrôle : enveloppe de la voix + gain musique
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    env, win = ducking.rms_envelope(voice)
    t_env = np.arange(env.size) * win / SR
    fig, ax = plt.subplots(2, 1, figsize=(13, 5.5), sharex=True)
    ax[0].plot(t_env, 20 * np.log10(np.maximum(env, 1e-9)), color="tab:blue", lw=1)
    ax[0].axhline(-26, color="tab:red", ls="--", lw=1, label="seuil -26 dBFS")
    ax[0].set_ylabel("voix de test (dBFS)")
    ax[0].legend(loc="lower right")
    ax[1].plot(np.arange(gain.size) / SR, 20 * np.log10(gain), color="tab:orange", lw=1)
    ax[1].axhline(-6, color="0.5", ls=":", lw=1, label="musique -6 dB")
    ax[1].axhline(-16, color="0.5", ls="--", lw=1, label="musique pendant voix -16 dB")
    ax[1].set_ylabel("gain musique (dB)")
    ax[1].set_xlabel("secondes")
    ax[1].legend(loc="lower right")
    for a in ax:
        a.grid(alpha=0.25)
    plt.tight_layout()
    (ROOT / "metadata").mkdir(parents=True, exist_ok=True)
    plt.savefig(str(ROOT / "metadata" / "ducking_test_courbe.png"), dpi=110)
    print("courbe :", ROOT / "metadata" / "ducking_test_courbe.png")


if __name__ == "__main__":
    main()
