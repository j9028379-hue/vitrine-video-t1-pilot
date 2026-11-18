# Rapport de finition artistique — T1 V3

**Statut : terminé et contrôlé**  
**Périmètre : finition graphique/typographique du master V2, sans refaire le montage**  
**Livrable vidéo :** `output/output_T1_sans_voix_v3.mp4`

## Résumé du résultat

La V3 est un nouveau master silencieux, distinct de la V2. Le montage conserve ses quatre scènes et ses timings (6 s, 8 s, 7 s, 9 s), ses rushs et la logique de mouvements caméra. Les trois transitions sont maintenues : **whip-pan horizontal** à 6 s, **directional push** à 14 s et **révélation diagonale au ruban orange** à 21 s. Aucun fondu générique ne les remplace.

Les six champs commerciaux et le format verrouillé restent inchangés : **720 × 1280, 30 i/s, 900 images, 30 s, 9:16, sans piste audio**. La spécification canonique n’a pas été modifiée.

## Corrections réellement apportées

- Recomposition du titre et de l’accroche en entrées décalées : « CHAUD », « SERVI », « AUJOURD’HUI » ont des positions, tailles et accents différents; un champ de contraste commun soutient la lecture sans transformer chaque mot en carte.
- Ajustement de la carte tarifaire : produit identifié au-dessus du prix, prix dominant, marges et proportions équilibrées, apparition animée conservée.
- Refonte de la localisation avec repère cartographique dessiné, ville et détail sur deux lignes. Comme il s’agit d’une démo, le texte demeure explicitement fictif (« COTONOU — ADRESSE FICTIVE »); aucune adresse réelle n’a été inventée.
- CTA simplifié et hiérarchisé (« COMMANDER SUR / WHATSAPP »), vert limité à l’identification WhatsApp et aucun faux logo/pictogramme ni faux numéro. Le contact reste « NUMÉRO FICTIF ».
- Mention « MAQUIS DÉMO · DÉMO FICTIVE » conservée à l’écran.
- Après le premier contrôle, une paire d’images quasi identiques détectée dans un mouvement très lent a motivé une correction du recadrage caméra : échantillonnage subpixel continu, sans changer les trajectoires prévues. Le nouveau master a ensuite passé le contrôle intégral sans paire suspecte.

## Contrôles réalisés

| Contrôle | Résultat |
|---|---|
| Contrat de sortie / `verification_v3.json` | **PASS** — 720×1280, 30/1 i/s, 900 images, 30,0 s, 0 piste audio |
| Décodage et intégrité visuelle / `visual_qc_v3.json` | **PASS** — 900/900 images décodées; aucun écran noir; aucun cadre rouge de diagnostic candidat; aucune paire quasi identique signalée |
| Revue des compositions | Planche des temps et captures plein format contrôlées pour ouverture, accroche, prix, localisation, CTA et fin |
| Revue du mouvement | Planche de contrôle à intervalles réguliers et planche des images successives autour des trois transitions contrôlées |
| Tests du dépôt | **41 réussis** (`python -m pytest -q`) |
| Hygiène du diff | `git diff --check` : **PASS** |
| Préservation V2 | SHA-256 V2 inchangé : `ff03d6140f43841aea568fb10fcdec83dd9c140b001345cc175923d34755a736` |

## Fichiers de livraison

- `output/output_T1_sans_voix_v3.mp4` — master silencieux.
- `output/planche_controle_v3.png` — planche des moments et compositions clés.
- `output/planche_temps_v3.png` — revue chronologique à intervalles réguliers.
- `output/transitions_v3.png` — images successives des trois transitions.
- `output/captures_v3/` — six captures plein format : accroche, typographie, prix, localisation, CTA et fin.
- `output/verification_v3.json` et `output/visual_qc_v3.json` — résultats machine des contrôles.

## Limites et précautions

Il s’agit toujours d’un **exemple fictif**, pas d’une fiche prête à publier pour un établissement réel. Le prix, la ville et le contact doivent être remplacés/confirmés par les informations autorisées du client avant toute diffusion réelle. Aucun son n’a été ajouté; la feuille de synchronisation existante est laissée intacte pour plus tard.

**Empreinte SHA-256 du master V3 :** `9f03b9cbdebbdb089783cb2becda7004b222aca7de48340a9f96bc45d1969121`
