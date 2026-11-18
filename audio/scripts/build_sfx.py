"""Bibliothèque d'effets et d'ambiances originales T1 — Restaurants et Maquis.

Chaque effet est rendu dans un fichier séparé (donc remplaçable sans retoucher la musique)
et normalisé à une crête documentée. Les matières sont celles d'un maquis : porcelaine,
couverts, service, cloche métallique, balafon, salle.
Aucun whoosh / pop / ding générique : les transitions sont faites avec de la vaisselle,
des couverts, un roulement de shekere et de la porcelaine qui monte.
"""
from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np

import synth_lib as L

ROOT = Path(__file__).resolve().parents[1]


def write_mono(path: Path, x: np.ndarray, peak_db: float) -> None:
    x = L.normalize_peak(np.asarray(x, dtype=np.float64), peak_db)
    x = np.clip(x, -1, 1)
    pcm = np.round(x * 32767).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(L.SR)
        w.writeframes(pcm.tobytes())


def two_notes(f1: float, f2: float, gap: float = 0.11, kind: str = "balafon") -> np.ndarray:
    a = L.balafon(f1, 0.7, hard=1.0) if kind == "balafon" else L.marimba_soft(f1, 0.9)
    b = L.balafon(f2, 0.8, hard=0.95) if kind == "balafon" else L.marimba_soft(f2, 1.0)
    n = int((gap + max(a.size, b.size) / L.SR) * L.SR)
    out = np.zeros(n)
    L.place(out, a, 0.0)
    L.place(out, b, gap, 0.9)
    return out


def cta_motif() -> np.ndarray:
    """motif chaleureux de trois notes (kalimba + cloche douce) pour l'apparition du CTA."""
    notes = [(L.hz("A4"), 0.0), (L.hz("C5"), 0.14), (L.hz("E5"), 0.28)]
    n = int(1.4 * L.SR)
    out = np.zeros(n)
    for f, at in notes:
        L.place(out, L.marimba_soft(f, 1.1), at, 0.9)
    L.place(out, L.agogo(0.25, base=1180.0), 0.28, 0.22)
    L.place(out, L.shaker(0.09), 0.0, 0.18)
    return out


def bass_hit() -> np.ndarray:
    """impact grave feutré (poitrine) — accompagne un bloc visuel, jamais une notification."""
    out = L.sub_boom(0.8, f0=72.0)
    L.place(out, L.kick(0.35, 100.0, 48.0), 0.0, 0.5)
    return out


def main() -> None:
    sfx_dir = ROOT / "sfx"
    amb_dir = ROOT / "ambience"
    entries = []

    def add(name: str, desc: str, sig: np.ndarray, peak_db: float, matiere: str, usage: str):
        path = sfx_dir / f"{name}.wav"
        write_mono(path, sig, peak_db)
        entries.append({
            "fichier": f"sfx/{name}.wav",
            "description": desc,
            "matiere": matiere,
            "usage_prevu": usage,
            "duree_s": round(sig.size / L.SR, 3),
            "crete_db": peak_db,
            "licence": "création originale VITRINE VÍDEO — aucun échantillon tiers",
            "synthese": "numpy/scipy — build_sfx.py",
        })

    add("sfx_01_assiette_posee", "assiette de porcelaine posée sur la table",
        L.plate_set(0.55, base=1150.0), -12.0, "porcelaine + contact de table",
        "ouverture S1 (assiettes sur table visibles à l'image) ; service S3")
    add("sfx_02_couverts_contact", "couverts qui se touchent, très bas",
        L.cutlery(0.45), -16.0, "métal fin",
        "plan avec couverts visibles (fourchette/couteau en S1-S2)")
    add("sfx_03_couverts_glisse_montee", "glissement de couvert montant (transition)",
        L.cutlery_sweep(0.40, up=True), -10.0, "métal glissé + air",
        "repère 8,90 s — préparation du zoom punch")
    add("sfx_04_couverts_glisse_descente", "glissement de couvert descendant (transition)",
        L.cutlery_sweep(0.38, up=False), -10.0, "métal glissé + air",
        "repère 23,90 s — préparation du punch cut")
    add("sfx_05_shekere_roulement", "roulement de shekere qui amène une transition",
        L.shaker_swell(0.55), -10.0, "graines sur calebasse",
        "repères 5,90 s et 13,90 s")
    add("sfx_06_porcelaine_montee", "porcelaine qui monte (résonance + souffle de service)",
        L.plate_riser(0.60), -11.0, "porcelaine frottée",
        "repère 20,90 s — préparation de la transition vers la scène 4")
    add("sfx_07_cloche_agogo", "accent de cloche agogo (double métal)",
        L.agogo(0.35, base=760.0), -11.0, "cloche de maquis",
        "repère 16,90 s — accent avant la coupe")
    add("sfx_08_balafon_prix", "deux notes de balafon (accent de prix)",
        two_notes(L.hz("A5"), L.hz("C6")), -9.0, "lame de bois",
        "repères 7,34 s et 18,34 s — apparition / rebond du prix")
    add("sfx_09_balafon_prix_variante", "variante plus basse du double coup de balafon",
        two_notes(L.hz("E5"), L.hz("A5")), -9.5, "lame de bois",
        "repère 18,34 s (prix seul) — évite la répétition à l'identique")
    add("sfx_10_service_tissu", "mouvement de service : tissu et pas feutrés",
        L.service_cloth(0.55), -20.0, "tissu + salle",
        "scène 3 — arrivée du serveur, plan de service")
    add("sfx_11_kalimba_cta", "motif chaleureux de trois notes pour l'appel à commander",
        cta_motif(), -11.0, "kalimba + cloche douce",
        "repère 26,50 s — apparition du bouton WhatsApp (aucune notification imitée)")
    add("sfx_12_impact_grave", "impact grave feutré sous un bloc visuel",
        bass_hit(), -10.0, "graves feutrés",
        "repères 6,50 s et 21,50 s — apparition du bandeau puis du bloc localisation")
    add("sfx_13_gresillement_braise", "grésillement de braise / plancha (réservé)",
        L.heat_sizzle(4.0), -14.0, "huile et braise",
        "RÉSERVÉ — volontairement non utilisé : aucun plan de cuisson à l'image dans V3.1")

    amb = L.room_ambience(30.0, gain=1.0)
    write_mono(amb_dir / "ambiance_maquis_salle_30s.wav", amb, -14.0)
    entries.append({
        "fichier": "ambience/ambiance_maquis_salle_30s.wav",
        "description": "rumeur de salle de maquis, vaisselle lointaine, aucune parole identifiable",
        "matiere": "salle + vaisselle lointaine",
        "usage_prevu": "scène 3 uniquement (salle et présence humaine visibles)",
        "duree_s": 30.0,
        "crete_db": -14.0,
        "licence": "création originale VITRINE VÍDEO",
        "synthese": "numpy/scipy — build_sfx.py",
    })

    (ROOT / "metadata" / "sfx_manifest.json").write_text(
        json.dumps({"elements": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for e in entries:
        print(f"  {e['fichier']:48s} {e['duree_s']:6.3f} s  crête {e['crete_db']:+.1f} dBFS")


if __name__ == "__main__":
    main()
