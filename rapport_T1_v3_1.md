# Compte rendu final — Direction artistique T1 V3.1

**Statut : master rendu; validations technique et revue visuelle terminées.**  
**Fichier livré :** `output/output_T1_sans_voix_v3_1.mp4`  
**Périmètre :** correction ciblée du design V3; aucun remontage ni changement aux spécifications canoniques.

## 1. Corrections apportées par composition

### Ouverture et identité du maquis
- Conservation du plan burger, du nom « MAQUIS DÉMO » et du titre produit.
- Recalage du nom et du produit sur un axe gauche commun; maintien d’un titre à deux lignes, ample et lisible.
- Suppression du monogramme « V » non explicite; le nom écrit porte l’identité. Le point orange est désormais un simple repère de couleur, pas un faux logo.
- La ligne orange sous le titre garde une fonction de séparation et de révélation, plutôt qu’une multiplication de traits.

### Accroche et phrase « CHAUD — SERVI — AUJOURD’HUI »
- Remplacement de la composition précédente aux alignements et accents dispersés par un **bloc éditorial unique**, posé sur une grille commune et aligné à gauche.
- « CHAUD » et « SERVI » forment les deux lignes principales; « AUJOURD’HUI » est le niveau secondaire, plus petit mais toujours confortable à lire.
- Un seul fond de contraste fonctionnel et un seul repère vertical orange organisent le bloc.
- Les trois lignes entrent, se déplacent et sortent ensemble avec la même courbe douce : aucun mot ne part de son côté, aucun trait décoratif ne se promène.
- La phrase complète apparaît très tôt dans la séquence, reste stable plusieurs secondes et s’efface avant la transition suivante.

### Présentation du produit et carte de prix
- Conservation de l’animation d’apparition et du prix dominant.
- Harmonisation avec les autres cartes : fond encre sombre, texte crème, accent orange unique, mêmes proportions et famille de coins arrondis.
- Nom du produit séparé du prix par un filet de fonction; suppression du reflet/glint décoratif.
- Sortie accélérée et nette, avec un court temps de respiration avant la scène suivante.

### Localisation
- Le repère cartographique demeure reconnaissable et porte seul l’accent orange de ce bloc.
- Ville et précision sont alignées sur la même grille; le panneau conserve un contraste stable.
- « COTONOU — ADRESSE FICTIVE » reste explicitement présenté comme exemple : aucune adresse réelle n’a été ajoutée.

### Bouton WhatsApp et fin
- Cartouche sobre cohérent avec les autres cartes; hiérarchie « COMMANDER SUR / WHATSAPP / NUMÉRO FICTIF ».
- Vert réservé à l’identification WhatsApp; suppression du soulignement redondant et absence de faux pictogramme ou de faux numéro.
- Les cartes de localisation et de contact gardent une séparation et des marges visibles; la mention « MAQUIS DÉMO · DÉMO FICTIVE » reste à l’écran final.

## 2. Grammaire de direction artistique appliquée

- **Typographie :** Montserrat pour les accroches et chiffres dominants; Plus Jakarta Sans pour les informations de service.
- **Hiérarchie :** titres/valeurs en premier, détails commerciaux en second; les tailles secondaires restent lisibles à 720 × 1280.
- **Alignement :** axe gauche commun pour les compositions éditoriales et commerciales; centrage seulement à l’intérieur des cartes lorsque cela sert leur fonction.
- **Palette :** encre sombre et crème pour la lecture; orange comme accent de marque/localisation; vert uniquement associé à WhatsApp.
- **Formes :** panneaux arrondis cohérents quand ils portent une information ou un contraste nécessaire; suppression des ornements redondants.
- **Mouvement :** entrées/sorties brèves, douces et synchronisées par composition; les unités éditoriales se déplacent en groupe. Aucun micro-mouvement n’a été ajouté pour contourner le détecteur de gel.

## 3. Contrôle et validation — deux niveaux distincts

### Contrôles automatiques
- `verification_v3_1.json` : **PASS** — 720 × 1280, 30/1 i/s, 900 images, 30 s, zéro piste audio.
- `visual_qc_v3_1.json` : **PASS** — 900/900 images décodées; aucun écran noir, aucun rectangle rouge de diagnostic candidat, aucune paire d’images quasi identiques.
- Tests du dépôt : **41 réussis**; ces tests vérifient le logiciel, ils ne constituent pas une note artistique.
- `git diff --check` : **PASS**.

### Revue visuelle humaine réalisée
- Déroulement complet échantillonné sur **121 repères temporels** : un repère à chaque quart de seconde de 0 à 29,75 s, plus l’image terminale à 29,97 s (`planche_controle_0_25s_v3_1.png`). Ce contrôle complète le décodage automatique des 900 images; il ne prétend pas remplacer une lecture individuelle de chaque image.
- Accroche typographique contrôlée sur **42 repères** couvrant l’entrée, le mouvement, l’état stable et la sortie (`planche_typographie_v3_1.png`).
- États clés d’ouverture, accroche, prix, localisation et CTA contrôlés sur **41 repères** supplémentaires (`planche_etats_animation_v3_1.png`).
- Les **36 images** autour des trois transitions ont été contrôlées dans leur ordre (`transitions_v3_1.png`); aucun remplacement par un fondu générique.
- Six captures plein format consultées pour les principaux écrans (`captures_v3_1/`).

### Résultat artistique
Les compositions contrôlées sont cohérentes entre elles, lisibles dans les captures plein format et distinctes sans paraître appartenir à des gabarits différents. Les entrées et sorties sont reliées aux blocs graphiques concernés; le mouvement n’est pas utilisé comme substitut à la composition. **Aucun défaut graphique bloquant n’a été relevé dans les éléments échantillonnés et les séquences de transition examinées.**

## 4. Préservation et limites

- Quatre scènes conservées : **6 / 8 / 7 / 9 s**; rushs burger cohérents, mouvements de caméra prévus et trois transitions conservés : whip-pan à 6 s, directional push à 14 s, révélation diagonale au ruban orange à 21 s.
- Les six champs commerciaux, le format 9:16, 720 × 1280, 30 FPS, 900 images, 30 secondes et le rendu muet sont conservés.
- Aucun changement aux spécifications V1.2/V6.2; aucune modification des masters V2 ou V3. Aucune musique, voix ou SFX ajoutés; la feuille de synchronisation existante reste intacte.
- La vidéo demeure une démo fictive. Le prix, l’adresse et le numéro doivent être confirmés/remplacés avec les données autorisées avant publication réelle.
- Aucun défaut bloquant restant identifié dans cette revue; la démo fictive et l’absence volontaire de numéro réel sont des limites de contenu, non des erreurs de composition.

**SHA-256 du master V3.1 :** `33abc850265242b91fb61284e7e7649cc92b7750414212fa8f05ed4e455c2039`  
**SHA-256 V2 (référence préservée) :** `ff03d6140f43841aea568fb10fcdec83dd9c140b001345cc175923d34755a736`  
**SHA-256 V3 (référence préservée) :** `9f03b9cbdebbdb089783cb2becda7004b222aca7de48340a9f96bc45d1969121`
