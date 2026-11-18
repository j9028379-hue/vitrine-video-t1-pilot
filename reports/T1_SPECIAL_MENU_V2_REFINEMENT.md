# T1 Special Menu — Révision V2 : prix et transitions impact

**Demande produit :** corriger la présentation du prix et ajouter une signature de transition plus spectaculaire, tout en conservant les quatre scènes, la police et le filtre validés.

## 1. Prix corrigé

Ancien comportement :

- nombre principal en DM Serif Display ;
- `FCFA` empilé sous le nombre ;
- proximité verticale pouvant donner un chevauchement visuel.

Nouveau verrou :

```text
2 500 FCFA
```

Règles :

- affichage sur une seule ligne ;
- nombre en DM Serif Display ;
- `FCFA` en Plus Jakarta Sans 700 ;
- même ligne de base ;
- espace visuel protégé de 18 px entre le nombre et la devise ;
- regroupement automatique par milliers : `2500` devient `2 500` ;
- la valeur marchande brute reste inchangée ;
- aucun retour à la ligne entre le nombre et `FCFA`.

## 2. Transitions premium

La coupe de montage reste une coupe franche sur l’image exacte prévue. La V2 lui ajoute un traitement spatial et lumineux sans chevaucher deux vidéos.

### Coupes internes

Profil `premium_zoom_snap` :

- 2 images avant la coupe ;
- 3 images après ;
- zoom supplémentaire maximal : 3,8 % ;
- flou directionnel maximal : 2 px ;
- flash chaud maximal : 7,5 % ;
- direction alternée gauche/droite.

Images concernées :

`60, 120, 240, 300, 360, 480, 540, 690, 750, 810`.

### Frontières des quatre scènes

Profil `golden_whip_flash` :

- 4 images avant la coupe ;
- 5 images après ;
- zoom supplémentaire maximal : 8,2 % ;
- translation maximale : 10 px ;
- flou directionnel maximal : 14 px ;
- flash ambre maximal : 30 % ;
- aberration chromatique maximale : 3 px ;
- balayage lumineux doré maximal : 24 %.

Images concernées :

- `180` : S1 → S2, vers la droite ;
- `420` : S2 → S3, vers la gauche ;
- `630` : S3 → S4, vers la droite.

## 3. Protection de la parole

Ces transitions ne sont pas des transitions temporelles :

- `source_time_map = identity` ;
- `audio_time_map = identity` ;
- aucune image supprimée ;
- aucune image dupliquée ;
- aucun gel ;
- aucune accélération ;
- aucun fondu entre deux décodeurs ;
- le texte est dessiné après l’effet et reste donc net.

La scène humaine S3 reste lue chronologiquement à vitesse 1,0. Les lèvres et la voix restent synchronisées.

## 4. Portabilité Android Media3

- zoom et translation : `MatrixTransformation` ;
- blur directionnel, flash, chromatic shift et sweep doré : un seul `GlEffect` personnalisé ;
- intensité calculée depuis le temps de présentation ;
- un seul décodeur vidéo ;
- aucun recouvrement temporel de rushes.

## 5. Validation

- 720 × 1280 ;
- 30 fps ;
- 900/900 images ;
- 30,00 secondes ;
- zéro image adjacente figée ;
- CTA intact à l’image 899 ;
- guide de capture inchangé ;
- `main` inchangé à `ad4ff15` ;
- 20 tests T1 ciblés réussis.

La V1 et sa prérelease restent disponibles. La V2 est une révision additive et réversible.
