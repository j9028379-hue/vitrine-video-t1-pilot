# Rapport final — refonte visuelle et motion design T1 V2

## Résultat livré

Nouveau master : `output/output_T1_sans_voix_v2.mp4`. Il s'agit d'un rendu distinct; le master précédent `output/output_T1_sans_voix.mp4` est conservé sans modification. Aucun JSON canonique V1.2/V6.2 n'a été modifié.

La V2 reste dans le périmètre T1 : quatre scènes de 180, 240, 210 et 270 images (6/8/7/9 s), douze plans, 720×1280, 30 i/s, 900 images, 30 s, sans audio. Les six clés de données commerciales demeurent `nom`, `produit`, `prix`, `whatsapp`, `quartier`, `accroche`; seule la valeur fictive `produit` a été alignée sur les images (`BURGER MAISON`).

## Causes observées et corrections

- **Cadres de diagnostic :** inspection du renderer disponible (`engine/t1_engine.py`) et recherche des chemins debug/bounding-box n'ont pas retrouvé de fonction qui dessine des cadres rouges; l'origine exacte des cadres de la capture antérieure n'est donc pas attribuable aux fichiers disponibles. La V2 possède un chemin de composition commercial séparé, sans couche d'annotation/diagnostic branchée à l'encodeur. `engine/visual_qc.py` analyse toute image décodée et rejette un contour rectangulaire rouge à quatre côtés.
- **Hiérarchie et lisibilité :** remplacement des badges répétés par une composition éditoriale à deux typographies, titre en deux temps, accroche séquencée, carte de prix dédiée, localisation et CTA unique. Les éléments restent dans les zones verticales de sécurité adaptées depuis V6.2; les fonds textuels sont renforcés par dégradés, contrastes et espacements. Aucun doublon de titre n'est posé dans une même composition.
- **Transitions :** suppression du fondu générique des coupes de scène au profit de mouvements de transition définis par le contexte. Les coupes internes restent nettes avec recadrage animé.
- **Continuité de cadence :** interpolation de mouvement des rushs 24 i/s vers le master 30 i/s, animation de recadrage continue et speed-ramp doux uniquement pendant la préparation. Le segment de rush qui masquait l'objectif par une main a été exclu de la fenêtre de lecture.
- **Cohérence image/produit :** remplacement des anciens plans salade, burgers mélangés et ragoût par trois rushs licenciés autour d'un même exemple fictif de burger; le plan de burger dressé revient en scène 4 comme rappel produit. Les URL, statuts de licence et empreintes sont dans `rushes/manifest.json`; les rushs bruts restent exclus du dépôt.

## Transitions implémentées

Durée de chacune : 12 images, soit 0,40 s. Les intervalles sont semi-ouverts `[début, fin)`.

| Coupure | Temps de référence | Images | Transition | Traitement |
|---|---:|---:|---|---|
| Scène 1 → 2 | 6,00 s | [176,188) | Whip-pan horizontal | Déplacement opposé des plans, feathering et flou directionnel bref; entrée sur le burger préparé |
| Scène 2 → 3 | 14,00 s | [416,428) | Directional push | Le plan de service pousse le plan détail avec léger changement d'échelle, sans fondu fantôme |
| Scène 3 → 4 | 21,00 s | [626,638) | Mask reveal diagonal | Révélation diagonale et ruban orange de marque pour revenir au burger dressé |

La source conserve un mouvement continu de part et d'autre des transitions; les bordures sont réfléchies, aucun noir n'est utilisé. Les trois transitions et leurs 36 images sont présentes dans `output/transitions_v2.png` pour revue image par image.

## Motion design réalisé

- **0,00 s :** le produit est visible dès la première image; l'identité puis « BURGER / MAISON » entrent par décalage et déplacement amorti, suivis d'un trait dessiné.
- **3,87 s :** l'accroche commerciale apparaît dans une pastille sobre.
- **6,40 / 8,17 / 9,93 s :** « CHAUD », « SERVI », puis « AUJOURD'HUI » se construisent par étapes; chaque mot a son soulignement animé.
- **Scènes :** recadrages Ken Burns à échelle et direction variées; speed-ramp monotone et modéré dans le plan de préparation, sans saut temporel.
- **15,40 s :** prix animé par entrée en échelle avec anticipation contenue, carte orange, contraste typographique et bref balayage de lumière; il se retire avant le plan final.
- **21,40 s :** adresse révélée dans une carte à repère géographique.
- **24,67 s :** CTA WhatsApp entre par montée/échelle puis reste posé jusqu'à la fin; vert réservé à l'action et libellé de contact clairement fictif.
- Les sorties des éléments intermédiaires sont fondues/décalées; l'écran final garde une tenue lisible plutôt que de terminer sur un écran vide.

## Contrôle technique et revue visuelle

- Tests : **41 réussis** (`python -m pytest -q`).
- FFprobe : **PASS**, 720×1280, 30/1 i/s, 900 images décodées, 30,0 s, 0 piste audio; master de 9 697 201 octets.
- Analyse intégrale des 900 images : **PASS**; 0 image noire, 0 cadre diagnostique rouge candidat, 0 paire quasi-identique détectée, dimensions/fréquence correctes.
- Revue humaine du déroulé par planche à 0,5 s sur les 30 s et revue image par image des 36 images de transition.
- Planches livrées : `output/planche_controle_v2.png`, `output/planche_temps_v2.png`, `output/transitions_v2.png`.
- Les JSON de référence V1.2 et V6.2/public-safe ont été parsés et leurs fichiers restent inchangés. Le JSON V6.2 canonique reste local; sa copie publique est le dérivé public-safe déjà en place.

## Préparation audio — sans génération ni intégration

`docs/audio_sync_T1_v2.md` donne les repères en images et secondes pour musique, ambiances, transitions, accents de prix et CTA. Le MP4 demeure volontairement muet : aucun SFX générique, aucune musique, aucune voix ni sous-titre n'a été ajouté.

## Limites à retenir

Il s'agit d'un exemple publicitaire fictif et visuel, pas d'une captation de Maquis Démo ni d'une promesse sur le menu, le tarif, l'adresse ou le contact d'un commerce réel. Le rush de remise du burger est une image de stock en restaurant; la réutilisation du plan de burgers en scène 4 est intentionnelle pour refermer la boucle produit. Il faudra remplacer les valeurs de démo et les images par celles d'un commerçant avant diffusion commerciale. Les specs canoniques restent en lecture seule.
