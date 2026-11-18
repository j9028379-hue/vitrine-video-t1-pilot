"""Génère les dérivés des consignes depuis l'unique source `capture-guide/consignes_T1.json`.

Sorties :
  simulation/consignes.js              — données consommées par la maquette HTML
  capture-guide/consignes_4_scenes.md  — fiche de tournage imprimable

Aucune consigne n'est écrite en dur ailleurs : pour changer un texte, on modifie le JSON
puis on relance ce script.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "capture-guide" / "consignes_T1.json"


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    scenes = data["scenes"]
    mention = data["mention_voix_commune"]
    bouton = data["bouton_principal"]

    # --- 1. données JS pour la maquette -------------------------------------------------
    js = (
        "/* Fichier GÉNÉRÉ par tools/build_consignes.py — ne pas modifier à la main.\n"
        "   Source : capture-guide/consignes_T1.json (elle-même dérivée de la spec V6.2). */\n"
        "window.CONSIGNES_T1 = "
        + json.dumps({"mention_voix_commune": mention, "bouton_principal": bouton, "scenes": scenes},
                     ensure_ascii=False, indent=2)
        + ";\n"
    )
    (ROOT / "simulation" / "consignes.js").write_text(js, encoding="utf-8")

    # --- 2. fiche de tournage markdown --------------------------------------------------
    lignes = [
        "# Les quatre consignes de tournage — T1 « Restaurants et Maquis »",
        "",
        "> Fichier généré depuis `capture-guide/consignes_T1.json` (source unique). "
        "Les consignes sont celles de la spécification V6.2, mot pour mot.",
        "",
        "| Scène | Titre | Durée |",
        "|---|---|---|",
    ]
    for s in scenes:
        lignes.append(f"| {s['n']}/{s['total']} | {s['titre']} | **{s['secondes']} secondes** |")
    lignes.append("")
    for s in scenes:
        lignes += [
            f"## Scène {s['n']}/{s['total']} — {s['titre']} — {s['secondes']} secondes",
            "",
            f"**Consigne** : « {s['consigne']} »",
            "",
            "**À FILMER**",
            "",
        ]
        lignes += [f"- {x}" for x in s["a_filmer"]]
        lignes += ["", "**À ÉVITER**", ""]
        lignes += [f"- {x}" for x in s["a_eviter"]]
        lignes += [
            "",
            f"**Enregistrer sa voix** : « {mention} »",
            "",
            f"**Exemple de phrase (facultatif)** : « {s['exemple']} »",
            "",
            f"Bouton de l'écran : `{bouton}`",
            "",
        ]
    (ROOT / "capture-guide" / "consignes_4_scenes.md").write_text("\n".join(lignes), encoding="utf-8")

    print("simulation/consignes.js et capture-guide/consignes_4_scenes.md régénérés "
          f"({len(scenes)} scènes, mention commune de {len(mention)} caractères).")


if __name__ == "__main__":
    main()
