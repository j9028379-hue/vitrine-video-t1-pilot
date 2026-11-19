# T1 Special Menu — V3 : identité unifiée et effets évolutifs

## Demande produit

1. La fin ne doit plus employer une composition différente de l’ouverture.
2. Le même langage `BURGER MAISON / PLAT DU JOUR` doit gouverner tout le gabarit.
3. Les effets premium ne doivent plus répéter le même battement jusqu’à la fin.
4. La progression doit être professionnelle, lumineuse et narrative.

## 1. Verrou final unifié

### Ouverture

- primaire : champ `produit` ;
- DM Serif Display ;
- taille maximale 84 px, minimale 52 px ;
- secondaire : `PLAT DU JOUR` ;
- Montserrat Light 35 px ;
- tracking 0,15 em ;
- révélation horizontale linéaire sur 20 images.

### Fin V3

- primaire : même champ `produit` ;
- même DM Serif Display ;
- mêmes tailles 84/52 px ;
- secondaire : `COMMANDER MAINTENANT` ;
- même Montserrat Light 35 px ;
- même tracking 0,15 em ;
- même révélation horizontale sur 20 images ;
- même couleur ivoire `#FBF7EE` ;
- aucun cadre, aucune bordure, aucune carte dure.

Sous ce verrou commun restent uniquement les données d’action :

- prix `2 500 FCFA` ;
- point WhatsApp vert et numéro ;
- micro-signature du restaurant.

La fin n’est donc plus un deuxième design : elle est la résolution commerciale du design d’ouverture.

## 2. Chorégraphie premium évolutive

La V2 utilisait deux familles répétées. La V3 attribue un événement distinct à chacune des treize coupes.

| Image | Temps | Effet | Phase |
|---:|---:|---|---|
| 60 | 2 s | `focus_snap` | Appétit |
| 120 | 4 s | `amber_macro_push` | Appétit |
| 180 | 6 s | `golden_whip_reveal` | Détails |
| 240 | 8 s | `silk_slide_left` | Détails |
| 300 | 10 s | `aperture_bloom` | Détails |
| 360 | 12 s | `gold_rack_focus` | Détails |
| 420 | 14 s | `portrait_luma_bloom` | Humain |
| 480 | 16 s | `editorial_punch_in` | Humain |
| 540 | 18 s | `editorial_release` | Humain |
| 630 | 21 s | `architectural_light_sweep` | Lieu |
| 690 | 23 s | `gallery_glide_left` | Lieu |
| 750 | 25 s | `gallery_glide_right` | Lieu |
| 810 | 27 s | `luxury_hero_resolve` | CTA |

### Phase 1 — Appétit

Effets optiques courts : mise au point, zoom macro, lumière ambrée.

### Phase 2 — Détails

Effets plus expressifs : glissement soyeux, ouverture lumineuse, rack-focus doré.

### Phase 3 — Humain

Effets volontairement plus doux : bloom de luminance puis changements de cadrage éditoriaux. Aucun décalage chromatique sur le visage.

### Phase 4 — Lieu et CTA

Balayage architectural, glissements de galerie opposés, puis résolution luxueuse. Après l’image 817, l’image cesse de battre : le CTA reste stable jusqu’à l’image 899.

## 3. Effets disponibles dans le moteur

- zoom optique ;
- translation réfléchie sans bord noir ;
- flou directionnel ;
- douceur gaussienne / rack focus ;
- bloom sur les hautes lumières ;
- flash ambre ;
- décalage chromatique limité ;
- sweep doré horizontal, vertical ou diagonal.

Chaque événement combine seulement les outils adaptés à sa fonction. La diversité est contrôlée et narrative, pas aléatoire.

## 4. Parole et Android

- temps source : identité ;
- temps audio : identité ;
- aucune image supprimée, répétée ou gelée ;
- un seul décodeur vidéo ;
- texte dessiné après l’effet et donc net ;
- scène humaine sans effet chromatique ;
- Android : `MatrixTransformation` + un `GlEffect` piloté par événements et temps de présentation.

## 5. Validation

- 720 × 1280 ;
- 30 fps ;
- 900 images ;
- 30,00 s ;
- CTA visible à pleine opacité à l’image 899 ;
- zéro paire statique ou quasi statique ;
- 26 tests T1 ciblés réussis ;
- capture inchangée ;
- `main` inchangé à `ad4ff15` ;
- V1 et V2 conservées.
