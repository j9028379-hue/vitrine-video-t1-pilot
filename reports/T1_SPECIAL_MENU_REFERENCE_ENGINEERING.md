# T1 — « Plat du jour » — Décompilation de la référence Special Menu

**Statut :** référence T1-A approuvée par le responsable produit
**Référence :** `https://www.tiktok.com/@ctemplate99/video/7525857155178712376`
**Branche d’ingénierie :** `feat/t1-special-menu-reference-v1`
**Date de l’analyse :** 18 novembre 2026
**Périmètre :** moteur visuel uniquement — musique, SFX et mixage restent en pause.

---

## 1. Décision de produit

Cette vidéo devient la référence officielle du premier gabarit Restaurants & Maquis :

- **Code :** T1
- **Titre :** Plat du jour
- **Objectif :** faire saliver en trois secondes puis pousser à commander maintenant.

L’adaptation ne remplace ni les quatre prises du commerçant, ni les consignes de tournage, ni la possibilité de parler. Elle remplace seulement la grammaire de montage et de présentation qui avait produit la V5 défectueuse.

## 2. Contrat non destructif

Les éléments suivants restent intacts :

1. `main` au commit de base `ad4ff15` ;
2. les releases antérieures ;
3. `capture-guide/consignes_T1.json` et les quatre écrans de capture ;
4. les durées S1=6 s, S2=8 s, S3=7 s, S4=9 s ;
5. les six champs marchands existants ;
6. la parole libre en fon, yoruba, français, anglais ou toute autre langue ;
7. l’absence de sous-titres automatiques de la parole ;
8. la grille 120 BPM et les règles audio déjà validées, réservées à la phase audio.

Aucun nouveau champ obligatoire n’est ajouté.

---

## 3. Vérité forensique de la vidéo de référence

### 3.1 Fichier analysé

- 576 × 1024, vertical 9:16 ;
- 30 images/s ;
- 570 images ;
- 19,00 s ;
- SHA-256 : `2e73cd3192e1b5b347703d87cf06956d549343ba76127c192f9cf533592a2d1d`.

Le MP4 tiers n’est pas redistribué dans le dépôt. Le dépôt contient son URL canonique, son empreinte et toutes les mesures nécessaires à une reproduction propre.

### 3.2 Neuf plans observés

| Plan | Images | Temps | Sujet / geste |
|---|---:|---:|---|
| R01 | 0–50 | 0,000–1,700 s | sauce versée sur le plat héros + titre |
| R02 | 51–112 | 1,700–3,767 s | baguettes dans un plat avec riz |
| R03 | 113–175 | 3,767–5,867 s | huile versée sur une pizza |
| R04 | 176–239 | 5,867–8,000 s | macro d’un plat roulé et dressé |
| R05 | 240–302 | 8,000–10,100 s | sauce déposée sur œufs et légumes |
| R06 | 303–365 | 10,100–12,200 s | couteau ouvrant un jaune d’œuf |
| R07 | 366–429 | 12,200–14,333 s | boisson rouge versée dans un verre |
| R08 | 430–491 | 14,333–16,400 s | finition d’une assiette de viande |
| R09 | 492–561 | 16,400–18,733 s | saumon assaisonné |
| Sortie | 562–569 | 18,733–19,000 s | fondu au noir sur 8 images |

### 3.3 Ce que sont réellement les transitions

La découverte importante est simple : **la référence n’emploie pas de transitions spectaculaires**.

Les huit raccords sont des **coupes franches d’une image**, aux images :

`51, 113, 176, 240, 303, 366, 430, 492`.

Il n’y a :

- aucun fondu enchaîné entre deux plats ;
- aucun wipe ;
- aucun portail circulaire ;
- aucun whip numérique ;
- aucun glitch ;
- aucune double exposition ;
- aucune strie de pixels.

Le sentiment de fluidité vient de quatre choses :

1. une coupe au moment où la main ou le liquide agit ;
2. un changement net d’angle ou d’échelle ;
3. un plat toujours grand dans le cadre ;
4. une cohérence de contraste et de température entre les plans.

Copier cette référence signifie donc **supprimer les transitions décoratives de la V5**, pas en inventer de nouvelles.

### 3.4 Relation à la musique

L’audio public analysé mesure environ **114,84 BPM**. Les coupes arrivent toutes les quatre pulsations, soit environ toutes les 2,09 secondes.

La grille Vitrine Vidéo est déjà à 120 BPM :

- 1 pulsation = 0,5 s = 15 images ;
- 4 pulsations = 2,0 s = 60 images.

La transposition propre est donc une coupe franche toutes les **60 images**, avec une résolution de trois secondes dans les scènes de durée impaire et dans le CTA.

---

## 4. Typographie décompilée

### 4.1 Animation du titre

Dans le premier plan :

- première trace visible vers l’image 4 ;
- révélation complète à l’image 24 ;
- durée du masque : 20 images, soit 0,667 s ;
- masque horizontal de gauche à droite ;
- progression linéaire ;
- aucune variation d’échelle ;
- aucun rebond ;
- aucun fondu de l’opacité ;
- titre maintenu jusqu’à la coupe de l’image 51.

### 4.2 Familles retenues

Le MP4 est aplati : il ne contient pas le nom des polices éditables. Il est donc impossible d’extraire cryptographiquement le nom interne de la police. Une comparaison des silhouettes a néanmoins donné les correspondances portables les plus proches :

| Fonction | Correspondance | Confiance | Fichier |
|---|---|---:|---|
| `Special` | **DM Serif Display Regular** | 0,93 | `assets/fonts/DMSerifDisplay-Regular.ttf` |
| `Menu` | **Montserrat Light**, tracking ≈ 0,15 em | 0,90 | `assets/fonts/Montserrat-Variable.ttf`, poids 300 |
| Prix et contact | **Plus Jakarta Sans Bold** | utilitaire | `assets/fonts/PlusJakartaSans-Variable.ttf` |

DM Serif Display est livrée sous licence SIL OFL 1.1. Aucune substitution silencieuse par Roboto, OpenCV Hershey ou une police Android générique n’est autorisée : le rendu doit échouer explicitement si une police manque.

### 4.3 Adaptation T1

Le verrou d’ouverture devient :

- ligne principale en DM Serif Display : **nom du plat marchand** ;
- ligne secondaire en Montserrat Light espacée : **PLAT DU JOUR** ;
- micro-signature : **nom du restaurant**.

Le texte marchand n’est jamais tronqué. Le moteur réduit la taille dans la plage autorisée, puis répartit le produit sur deux lignes équilibrées si nécessaire.

---

## 5. Filtre / ambiance cinématique

### 5.1 Mesures de la référence

Médianes sur les images utiles :

- luminance moyenne : 64,84 / 255 ;
- luminance P5 : 5 / 255 ;
- luminance P95 : 196 / 255 ;
- saturation HSV moyenne : 136,65 / 255 ;
- moyenne rouge moins bleu : +29,86.

Cela confirme :

- noirs très profonds ;
- hautes lumières ambrées ;
- environnement parfois légèrement cyan/bleu ;
- nourriture chaude et plus saturée que le décor ;
- contraste marqué, mais hautes lumières non brûlées.

### 5.2 Pipeline reproductible

Le preset `warm_low_key_food_cinema_v1` applique, dans cet ordre :

1. exposition adaptative mesurée une fois par scène ;
2. balance des blancs plafonnée pour éviter les sauts ;
3. gains chauds R/G/B = 1,055 / 1,005 / 0,945 ;
4. courbe filmique avec toe noir et épaule douce ;
5. ombres légèrement froides et hautes lumières chaudes ;
6. saturation sélective des rouges/oranges, réduction des verts et bleus ;
7. contraste local léger ;
8. vignettage doux de 16 % ;
9. grain de luminance déterministe très fin.

Les paramètres sont figés à l’intérieur d’une scène : aucune correction image par image qui ferait pomper la luminosité.

### 5.3 Limite physique assumée

Un filtre ne peut pas créer une profondeur de champ, une mise au point nette, une belle vapeur ou une lumière absentes de la prise. C’est pourquoi les consignes de capture existantes restent indispensables. Le filtre harmonise les quatre rushes ; il ne doit jamais être présenté comme un remplacement de la lumière et du cadrage.

---

## 6. Adaptation exacte aux quatre scènes

### S1 — Le plat — 0 à 6 s — 180 images

Trois fenêtres de 60 images :

1. assiette entière, zoom 1,00 → 1,04 ;
2. sauce/brillance/main, coupe de cadrage à 2 s, zoom 1,08 → 1,12 ;
3. macro appétissante, coupe de cadrage à 4 s, zoom 1,16 → 1,20.

La source reste chronologique à vitesse 1,0. L’ouverture typographique apparaît seulement pendant les deux premières secondes.

### S2 — Dessus et détails — 6 à 14 s — 240 images

Quatre fenêtres de 60 images :

1. vue du dessus large ;
2. détail A ;
3. détail B ;
4. détail final.

Le prix apparaît de 6,13 s à 8 s. L’accroche facultative apparaît sur la troisième fenêtre ; si elle est vide, le plan reste totalement propre.

### S3 — Personne qui sert — 14 à 21 s — 210 images

Fenêtres 60 + 60 + 90 images :

1. plan moyen ;
2. plan plus serré ;
3. visage, sourire ou service.

C’est la scène la plus protégée :

- source strictement continue ;
- vitesse 1,0 ;
- aucune image supprimée ou dupliquée ;
- aucun gel ;
- aucun texte sur la bouche ou les yeux ;
- les deux coupes internes ne changent que le recadrage.

La parole et les lèvres restent donc synchronisées.

### S4 — Lieu et contact — 21 à 30 s — 270 images

Fenêtres 60 + 60 + 60 + 90 images :

1. entrée large ;
2. enseigne ;
3. comptoir ;
4. fond du CTA.

Le nom et le quartier sont présentés au début. Le CTA apparaît à l’image 810, soit 27 s, et reste intégralement visible jusqu’à l’image 899.

Le fondu final de la référence est transposé uniquement sur le fond vidéo, à 34 % maximum pendant les huit dernières images. Le CTA ne baisse jamais d’opacité.

---

## 7. Continuité de la parole

La référence TikTok utilise neuf clips indépendants. Vitrine Vidéo utilise quatre prises dans lesquelles le commerçant peut parler. Pour conserver les deux avantages :

- les changements de plan internes sont des changements de cadrage, pas des sauts temporels ;
- les images source de chaque scène sont lues une fois, dans l’ordre, à vitesse 1,0 ;
- l’audio de la scène reste continu sous les coupes visuelles ;
- aucun speed-ramp n’est appliqué à une voix ;
- aucune phrase n’est coupée pour rejoindre un beat ;
- aucun sous-titre de parole n’est créé.

Cette règle est inscrite dans le JSON et testée automatiquement.

---

## 8. Champs marchands universels

| Champ existant | Obligatoire | Usage T1 Special Menu |
|---|---:|---|
| `nom` | oui | micro-signature, lieu, CTA |
| `produit` | oui | grand titre d’ouverture, rappel CTA |
| `prix` | oui | offre S2, rappel CTA |
| `whatsapp` | oui | CTA final |
| `quartier` | oui | identification du lieu |
| `accroche` | non | message éditorial S2 ; bloc supprimé si vide |

Textes fixes du gabarit :

- `PLAT DU JOUR` ;
- `COMMANDER MAINTENANT`.

Ces libellés décrivent la fonction du gabarit ; ils ne constituent pas un avantage commercial inventé.

---

## 9. Pourquoi cette architecture corrige la V5

| V5 rejetée | Architecture Special Menu |
|---|---|
| cartouches et rectangles gris | aucun rectangle dur ; obscurcissement doux seulement |
| Montserrat générique partout | DM Serif Display + Montserrat Light + Plus Jakarta Sans |
| transitions à glitch, fantôme et portail | coupes franches de zéro image |
| textes microscopiques | hiérarchie centrale, tailles plafonnées et auto-fit |
| plans figés | geste culinaire continu + changement d’échelle toutes les 2 s |
| CTA dispersé | verrou central maintenu jusqu’à la dernière image |
| risque de casser la voix | source continue à vitesse 1,0 dans chaque scène |

---

## 10. Fichiers faisant autorité

- Observation pure : `references/t1-special-menu/reference_decompilation_v1.json`
- Adaptation exécutable : `config/T1_special_menu_reference_v1.json`
- Police display : `assets/fonts/DMSerifDisplay-Regular.ttf`
- Licence : `assets/fonts/OFL-DMSerifDisplay.txt`
- Présent rapport : `reports/T1_SPECIAL_MENU_REFERENCE_ENGINEERING.md`

Le JSON d’observation ne doit jamais être modifié pour justifier une décision de produit. Les adaptations futures doivent être versionnées séparément dans le JSON de configuration.
