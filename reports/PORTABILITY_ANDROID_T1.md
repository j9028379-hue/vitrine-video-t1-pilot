# Portabilité Android — moteur V5 « Worldclass »

> **Statut : architecture préparée, portage non réalisé et non validé.** Ce document décrit ce qui
> est portable, ce qui a été mesuré côté Python, et ce qui reste à vérifier sur un appareil réel.
> Aucun test sur téléphone n'a été effectué pendant cette mission.

---

## 1. Les quatre couches

| Couche | Fichier Python | Dépendances | Portable tel quel ? |
|---|---|---|---|
| 1. Analyse des sources | `engine/scene_analyzer.py` | OpenCV (phase correlation, Laplacien, Sobel, Haar) | **Non** : les mesures doivent être réécrites en natif ; **les formules, oui** |
| 2. Construction du montage | `engine/montage_plan_builder.py` | aucune (JSON pur, `math`) | **Oui** : aucune image touchée, aucune API graphique |
| 3. Présentation graphique | `engine/adaptive_graphics_v5.py` | PIL (polices, masques, flou) | **Partiellement** : la géométrie et les enveloppes sont pures, le tracé doit passer par CanvasOverlay |
| 4. Rendu | `engine/motion_v5.py`, `engine/food_cinema_transitions.py` | OpenCV (`warpAffine`, `LUT`), ffmpeg | **Non** : remplacé par Media3 Transformer + OpenGL ES |

Les couches 2 et 3 ne décodent aucune image et n'appellent ni FFmpeg ni OpenCV : elles produisent
et consomment uniquement le plan JSON. C'est le point d'appui du portage.

---

## 2. Contrat JSON commun

Un seul fichier décrit intégralement le montage : `reports/montage_plan_v5_demo.json`
(version `T1-V5-montage-plan-1`). Il contient :

| Bloc du contrat | Contenu | Utilisation Android |
|---|---|---|
| `output` | 720×1280, 30 i/s, 900 images, 30,000 s, muet | configuration de l'encodeur Media3 |
| `scenes[]` | bornes en images **et** en secondes, source, colorimétrie, ancre, stabilité, netteté | pistes de timeline |
| `shots[]` | fenêtre source (`in_frame`, `source_frames`), `indices_sources`, `positions_sous_pixel`, zoom, panoramique, `lip_sync_safe` | `MediaItem` + `SpeedProvider` + matrices |
| `cuts[]` | instant, transition, durée, paramètres, justification | `ShaderProgram` + plage de temps |
| `blocs[]` | fenêtre de chaque bloc | `CanvasOverlay` piloté par le temps |
| `qualite` | profils `standard` / `android_leger` | choix du programme de rendu |
| `rendu` | encodeur, CRF, `faststart`, audio désactivé | `Transformer` |

Les positions graphiques sont **normalisées** (0..1) : le même plan se calcule en 720×1280 et en
1080×1920 sans réécrire une seule valeur. Les instants sont donnés en images **et** en secondes,
ce qui évite les arrondis à 30 i/s (1 image = 33,333… ms).

### Remappage temporel : ce qu'il faut porter

`shots[].speed.indices_sources` donne, pour chaque image de sortie, l'image source à afficher.
Sur Android, deux approches :

1. **`SpeedProvider` Media3** quand la vitesse est constante par segment — c'est le cas simple.
2. **Table d'indices** (144 entrées par plan en moyenne) quand la vitesse varie continûment :
   lire l'image source `indices_sources[i]` pour l'image de sortie `i`. Coût mémoire négligeable,
   comportement strictement identique au rendu Python.

La courbe est normalisée pour consommer **exactement** la fenêtre source : aucune image n'est
inventée, aucun gel n'est nécessaire.

---

## 3. Caméra sous-pixel

Python, `engine/motion_v5.py::camera_frame` :

```python
ch = hs / k                      # hauteur de fenêtre pour un zoom k
cw = ch * (720/1280)
x0 = clamp(cx - cw/2, 0, ws - cw)   # flottant
y0 = clamp(cy - ch/2, 0, hs - ch)
M = [[720/cw, 0, -x0*720/cw],
     [0, 1280/ch, -y0*1280/ch]]
warpAffine(src, M, (720, 1280), INTER_CUBIC)
```

OpenGL ES 2.0 équivalent (vertex shader) :

```glsl
uniform mat3 uTexMatrix;      // matrice 3×3 calculée côté CPU, identique à M
attribute vec2 aPos;
varying vec2 vUv;
void main() {
  vec3 t = uTexMatrix * vec3(aPos, 1.0);
  vUv = t.xy;
  gl_Position = vec4(aPos * 2.0 - 1.0, 0.0, 1.0);
}
```

`uTexMatrix` est exactement la matrice ci-dessus, divisée par les dimensions de la texture.
Un seul échantillonnage, donc une seule interpolation, comme en Python. `k ≤ 1,32` est un
plafond vérifié dans le plan (`shots[].camera.zoom.plafond_respecte`).

---

## 4. Shaders à porter

| Transition | Mathématique | Shader GLSL ES 2.0 |
|---|---|---|
| `TR_CUT` | remplacement | aucun |
| `TR_FLASH_PUNCH` | `uv' = (uv-0.5)/z + 0.5`, `z = 1+(z0-1)(1-e)`, `e = easeOutExpo(p)` | 1 texture, 20 lignes |
| `TR_WARM_BURN` | deux zooms opposés + `screen(a,b)`, bloom sur seuil | 2 textures + seuil de luminance |
| `TR_WHIP_BLUR` | `uv.x - (1-e)`, flou ∝ vitesse instantanée | flou directionnel = 8 à 12 taps |
| `TR_PORTAL_EXPAND` | SDF de rectangle arrondi : `alpha = smoothstep(r, r-w, sdf)` | 2 textures + ombre (offset) |
| `TR_SPLIT_DIPTYCH` | `uv.y` sélectionne la texture, 2 bandes, mouvement opposé | 2 textures |

Toutes les courbes sont dans `config/T1_worldclass_v5.json` (catalogue) et se réduisent à des
polynômes ou à `1-2^(-10t)` : aucune bibliothèque d'animation n'est nécessaire. `CanvasOverlay`
reste le choix validé pour le graphisme ; **Lottie n'est pas introduit**.

### Flou du verre dépoli

Python : réduction 1/4, `GaussianBlur(σ = rayon/4)`, remontée bilinéaire. Coût mesuré : négligeable
devant l'encodage. Android : `RenderEffect.createBlurEffect` (API 31+) sur la vue de fond, ou
pré-flou GPU en deux passes (descente + montée). En profil `android_leger`, le flou est désactivé
et remplacé par un aplat translucide : **la géométrie et la progression commerciale sont
identiques**, aucun bloc n'est supprimé.

---

## 5. Correspondance demandée

| Composant V5 | Cible Android | État |
|---|---|---|
| Scene Analyzer | analyse native légère des images (renderscript/GPU ou OpenCV Android) | à écrire |
| Montage Plan Builder | modèle de timeline partagé (JSON identique) | **prêt** |
| Remappage temporel | `SpeedProvider` / table d'indices | **spécifié** |
| Caméra sous-pixel | transformations OpenGL ES (mat3) | **spécifié** |
| Transitions Food Cinema | shaders OpenGL ES | **spécifié** |
| Adaptive Graphics Engine | `CanvasOverlay` | **spécifié** |
| Animations typographiques | courbes natives (ValueAnimator/matrices) | **spécifié** |
| Encodage | Media3 `Transformer` | **spécifié** |

---

## 6. Contraintes de mémoire et de performance mesurées (Python, référence)

| Mesure | Valeur | Contexte |
|---|---|---|
| Analyse des 4 prises | 4,9 s (≈ 1,2 s / scène) | miniatures 180×320, 901 images |
| Construction du plan | < 0,1 s | aucune image lue |
| Rendu complet (900 images) | 86 s | 1 cœur, `INTER_CUBIC`, graphismes compris |
| Mémoire maximale du rendu | ≈ 600 Mo | 7 lecteurs + composition |
| Encodage | 1 seul passage libx264 CRF 18 | aucun intermédiaire encodé |

Deux écueils rencontrés et évités, à ne pas reproduire côté Android :

1. **Cache d'images par plan** : 7 lecteurs × 240 images tenaient 3 Go et faisaient tuer le
   processus. Le cache est maintenant borné à 6 images par lecteur ; côté Android, garder 3 à 5
   `MediaItem` ouverts au maximum et libérer dès la fin d'un plan.
2. **Tableaux flottants temporaires** dans les transitions : un masque mal dimensionné a demandé
   13 Go. Toute opération doit rester en `float` simple précision et de la taille de l'image.

## 7. Différences connues entre les deux rendus

| Point | Python (référence) | Android (attendu) |
|---|---|---|
| Interpolation | `INTER_CUBIC` (bicubique Catmull-Rom approché) | bilinéaire GPU par défaut ; `GL_LINEAR` — écart perceptible sur les diagonales |
| Flou gaussien | noyau PIL, σ exact | approximation par deux passes ; léger écart |
| Gamma / LUT | table 256 entrées par canal | shader de correction, à calibrer (espace colorimétrique BT.709) |
| Arrondis temporels | 30 i/s, positions en `float` | `presentationTimeUs`, arrondi à la microseconde |
| Encodage | libx264 CRF 18, `yuv420p` | MediaCodec H.264, bitrate cible (différence de qualité à mesurer) |
| Blur/frosted glass | recalculé par image | `RenderEffect` (API 31+) ou aplat en profil léger |

**Aucune de ces différences n'a été observée sur un appareil réel** : elles sont anticipées à
partir des spécifications, pas mesurées.

## 8. Ce qui reste à valider sur un téléphone

1. Reproduction du plan JSON sur un appareil de milieu de gamme (Media3 Transformer + OpenGL ES 2.0).
2. Fluidité perçue du remappage temporel avec `SpeedProvider` (risque de saccade aux bornes de
   segment).
3. Rendu du verre dépoli sur API < 31 (repli obligatoire).
4. Fidélité colorimétrique après correction par scène (BT.709 ↔ sRGB).
5. Coût réel des shaders `TR_WARM_BURN` et `TR_WHIP_BLUR` sur GPU mobile (2 textures + taps).
6. Mémoire crête pendant l'encodage d'un 720×1280 de 30 s.
7. Comportement de `CanvasOverlay` sur les animations de masque ligne par ligne.
8. Validation des polices variables (Montserrat, Plus Jakarta Sans) en `setVariationByName` natif.

## 9. Rappel des verrous

- Aucune API `@UnstableApi` de Media3 n'a été utilisée ni vérifiée dans cette mission.
- Les signatures déjà vérifiées dans la spécification V1.2 restent la référence.
- Le master V5 est muet : aucune décision audio n'est prise ici.
- Le portage Android n'est **pas** déclaré validé.
