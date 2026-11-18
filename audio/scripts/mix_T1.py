"""Mixage T1 — musique originale + effets + ambiance, synchronisés au montage V3.1 (900 images).

Aucune voix n'est fabriquée : si `--voice` n'est pas fourni, le master démonstratif reste
sans voix et la musique ne bouge pas (conforme à la règle « pas de ducking inutile »).
Le mécanisme de ducking est testé séparément (ducking_test.py).

Niveaux V6.2 appliqués :
  musique -6 dB (bus), musique pendant la voix -16 dB (ducking -10 dB),
  effets -5 dB et -8 dB pendant la parole, ambiance très basse (documentée),
  fade-out musique de 28,50 à 30,00 s (easeOutCubic).
"""
from __future__ import annotations

import argparse
import json
import wave
from pathlib import Path

import numpy as np

import ducking
import loudness as LU
import synth_lib as L

ROOT = Path(__file__).resolve().parents[1]
SR = L.SR
TOTAL = L.TOTAL

MUSIC_BUS_DB = -6.0
MUSIC_DUCK_DB = -16.0
SFX_BUS_DB = -5.0
SFX_BUS_VOICE_DB = -8.0
AMB_BUS_DB = -20.0

# --- les 11 repères V6.2 (heures exactes de la spécification) --------------- #
MARKERS = [
    (5.90, "transition vers la deuxième scène (wipe géométrique)",
     ["sfx_05_shekere_roulement"], 3.0),
    (6.50, "apparition du bandeau commercial (hero lockup)",
     ["sfx_01_assiette_posee", "sfx_12_impact_grave"], 3.0),
    (7.34, "mise en valeur du prix (rebond de la pastille)",
     ["sfx_08_balafon_prix"], 0.0),
    (8.90, "préparation du changement de plan (zoom punch)",
     ["sfx_03_couverts_glisse_montee"], 0.0),
    (13.90, "préparation de la transition vers la scène 3 (fondu enchaîné)",
     ["sfx_05_shekere_roulement"], 2.0),
    (16.90, "accent avant la coupe suivante",
     ["sfx_07_cloche_agogo"], 0.0),
    (18.34, "apparition du prix seul (rebond)",
     ["sfx_09_balafon_prix_variante"], 0.0),
    (20.90, "préparation de la transition vers la scène 4 (wipe directionnel)",
     ["sfx_06_porcelaine_montee"], 0.0),
    (21.50, "apparition de la localisation",
     ["sfx_01_assiette_posee", "sfx_12_impact_grave"], 1.5),
    (23.90, "préparation du changement vers le CTA (punch cut)",
     ["sfx_04_couverts_glisse_descente"], 0.0),
    (26.50, "apparition de l'appel à commander sur WhatsApp",
     ["sfx_11_kalimba_cta"], 0.0),
]

# --- sons directs motivés par l'image, hors repères (niveau plus bas) ------- #
SYNC_IMAGE = [
    (0.15, "S1 — les assiettes sont sur la table (ouverture)", "sfx_01_assiette_posee", -7.0),
    (14.45, "S3 — le serveur arrive avec le plateau (mouvement visible)", "sfx_10_service_tissu", -2.0),
    (15.05, "S3 — l'assiette est posée devant le client (geste visible)", "sfx_01_assiette_posee", -5.0),
]
# note volontairement absente : 11,20 s (main qui presse la sauce) — aucune matière
# sonore de la bibliothèque ne correspond ; on n'ajoute pas d'effet générique.
# note volontairement absente : aucun son de rue / d'enseigne : la scène 4 ne montre
# ni entrée, ni rue, ni enseigne (voir rapport, audit V6.2).

AMBIENCE_WINDOW = (13.80, 21.20)   # la salle n'est visible que dans la scène 3


def load_mono(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        assert w.getframerate() == SR, f"{path} n'est pas à {SR} Hz"
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
    return data


def load_stereo(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        ch = w.getnchannels()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
    return data.reshape(-1, ch)


def fade_window(n: int, start: float, end: float, ramp: float = 0.4) -> np.ndarray:
    g = np.zeros(n)
    i0, i1 = int(start * SR), int(end * SR)
    i0r, i1r = i0 + int(ramp * SR), i1 - int(ramp * SR)
    g[i0:i0r] = np.linspace(0, 1, i0r - i0)
    g[i0r:i1r] = 1.0
    g[i1r:i1] = np.linspace(1, 0, i1 - i1r)
    return g


def build(music_id: str, voice: np.ndarray | None = None) -> tuple[np.ndarray, dict]:
    n = int(round(TOTAL * SR))
    music = load_stereo(ROOT / "music" / f"{music_id}_mix_30s.wav")
    assert music.shape[0] >= n
    music = music[:n]

    sfx_bus = np.zeros((n, 2))
    sfx_events = []
    for at, desc, assets, extra_db in MARKERS:
        for aid in assets:
            sig = load_mono(ROOT / "sfx" / f"{aid}.wav")
            L.add_stereo(sfx_bus, sig, at, L.db_to_gain(extra_db), pan=0.0)
            sfx_events.append({"temps_s": at, "evenement": desc, "fichier": f"sfx/{aid}.wav",
                               "gain_relatif_db": extra_db, "type": "repere_v6_2"})
    for at, desc, aid, extra_db in SYNC_IMAGE:
        sig = load_mono(ROOT / "sfx" / f"{aid}.wav")
        L.add_stereo(sfx_bus, sig, at, L.db_to_gain(extra_db), pan=-0.15)
        sfx_events.append({"temps_s": at, "evenement": desc, "fichier": f"sfx/{aid}.wav",
                           "gain_relatif_db": extra_db, "type": "son_direct_image"})

    amb = load_mono(ROOT / "ambience" / "ambiance_maquis_salle_30s.wav")[:n]
    amb_win = fade_window(n, *AMBIENCE_WINDOW, ramp=0.5)
    amb_bus = np.stack([amb * amb_win, amb * amb_win], axis=1)

    voice_gain = np.ones(n) * L.db_to_gain(MUSIC_BUS_DB)
    duck_journal = None
    sfx_voice_mask = np.zeros(n, dtype=bool)
    if voice is not None:
        g, duck_journal = ducking.gain_curve(voice, TOTAL)
        # -6 dB nominal -> -16 dB pendant la parole, exactement comme la spec
        voice_gain = L.db_to_gain(MUSIC_BUS_DB) * (g / db_to_gain_local(ducking.DEPTH_DB))
        rip = np.abs(g - db_to_gain_local(ducking.DEPTH_DB)) < 1e-6
        sfx_voice_mask = rip
    sfx_gain = np.where(sfx_voice_mask, L.db_to_gain(SFX_BUS_VOICE_DB), L.db_to_gain(SFX_BUS_DB))[:, None]

    mixed = music * voice_gain[:, None] + sfx_bus * sfx_gain + amb_bus * L.db_to_gain(AMB_BUS_DB)

    # niveau relatif de chaque effet dans le mix (avant mastering) — mesure d'audibilité
    for ev in sfx_events:
        a0 = int(round(ev["temps_s"] * SR))
        a1 = min(n, a0 + int(0.15 * SR))
        if a1 <= a0:
            continue
        ev_sig = np.zeros((n, 2))
        L.add_stereo(ev_sig, load_mono(ROOT / "sfx" / Path(ev["fichier"]).name),
                     ev["temps_s"], L.db_to_gain(ev["gain_relatif_db"]))
        e_rms = np.sqrt(np.mean(ev_sig[a0:a1] ** 2))
        m_rms = np.sqrt(np.mean(mixed[a0:a1] ** 2))
        ev["niveau_effet_relatif_db"] = round(float(20 * np.log10(max(e_rms, 1e-9) / max(m_rms, 1e-9))), 1)
        ev["perceptible"] = bool(ev["niveau_effet_relatif_db"] >= -20.0)

    pre_lufs = LU.integrated_lufs(mixed)
    target_lufs = -16.0
    # chaîne de mastering : compression de bus douce -> limiteur avec anticipation,
    # puis étalonnage itératif vers -16 LUFS avec true peak <= -1 dBTP
    mixed = LU.compressor(mixed, threshold_db=-21.0, ratio=2.0, attack=0.006, release=0.150)
    for _ in range(4):
        cur = LU.integrated_lufs(mixed)
        mixed = mixed * L.db_to_gain(target_lufs - cur)
        mixed = LU.limiter(mixed, ceiling_db=-2.6)
        tp = LU.true_peak_db(mixed)
        if tp > -1.0:
            mixed = mixed * L.db_to_gain(-2.65 - tp)
        if abs(LU.integrated_lufs(mixed) - target_lufs) < 0.35 and LU.true_peak_db(mixed) <= -2.6:
            break
    for _ in range(4):
        tp = LU.true_peak_db(mixed)
        if tp <= -2.6:
            break
        mixed = mixed * L.db_to_gain(-2.65 - tp)

    report = {
        "piste_musique": music_id,
        "voix_reelle": voice is not None,
        "gains_db": {
            "musique_nominale": MUSIC_BUS_DB, "musique_pendant_voix": MUSIC_DUCK_DB,
            "effets": SFX_BUS_DB, "effets_pendant_voix": SFX_BUS_VOICE_DB,
            "ambiance": AMB_BUS_DB,
            "fade_out": [28.5, 30.0],
        },
        "evenements": sfx_events,
        "ducking": duck_journal,
        "loudness": {
            "avant_normalisation_lufs": round(pre_lufs, 2),
            "gain_total_db": round(20 * np.log10(np.max(np.abs(mixed)) / max(np.max(np.abs(music[:n])), 1e-12)), 2),
            "cible_lufs": target_lufs,
            "apres_lufs": round(LU.integrated_lufs(mixed), 2),
            "true_peak_dbtp": round(LU.true_peak_db(mixed), 2),
            "crete_db": round(LU.peak_db(mixed), 2),
        },
        "sections": {},
    }
    for name, (a, b) in [("S1", (0.0, 6.0)), ("S2", (6.0, 14.0)), ("S3", (14.0, 21.0)),
                         ("S4", (21.0, 28.5)), ("fade_out", (28.5, 30.0))]:
        seg = mixed[int(a * SR):int(b * SR)]
        report["sections"][name] = {"rms_db": round(LU.rms_db(seg), 2),
                                    "lufs": round(LU.integrated_lufs(seg), 2)}
    return mixed, report


def db_to_gain_local(db: float) -> float:
    return 10 ** (db / 20.0)


def write_wav(path: Path, x: np.ndarray) -> None:
    pcm = np.round(np.clip(x, -1, 1) * 32767).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", type=Path, default=None,
                    help="WAV mono de la voix réelle captée pendant les prises (optionnel)")
    ap.add_argument("--out", default="mix_T1_audio_final.wav")
    ap.add_argument("--alt", action="store_true", help="produire aussi la version piste B")
    args = ap.parse_args()

    voice = None
    if args.voice:
        voice = load_mono(args.voice)
        if voice.size < int(TOTAL * SR):
            voice = np.pad(voice, (0, int(TOTAL * SR) - voice.size))

    mixed, report = build("maquis_afro_A_braise", voice)
    out = ROOT / "synced" / args.out
    write_wav(out, mixed)
    print(f"écrit {out.relative_to(ROOT)}  LUFS {report['loudness']['apres_lufs']}  "
          f"TP {report['loudness']['true_peak_dbtp']} dBTP")

    metas = [report]
    if args.alt:
        mixed_b, report_b = build("maquis_afro_B_maquis_dore", voice)
        out_b = ROOT / "synced" / "mix_T1_audio_final_pisteB.wav"
        write_wav(out_b, mixed_b)
        metas.append(report_b)
        print(f"écrit {out_b.relative_to(ROOT)}  LUFS {report_b['loudness']['apres_lufs']}")

    (ROOT / "metadata" / "mix_report.json").write_text(
        json.dumps(metas if args.alt else metas[0], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
