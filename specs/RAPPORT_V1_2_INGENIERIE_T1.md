# Rapport d'ingénierie V1.2 — Gabarit T1 « Plat du jour » — **CLÔTURE**

**État final : consolidation technique terminée.** Les deux livrables sont complets, cohérents et validés syntaxiquement. Aucune production n'a été lancée.

| Livrable | Contenu | Taille |
|---|---|---|
| `T1_ENGINEERING_SPEC_V1_2.json` | source de vérité, 25 sections, 12 plans, 8 blocs, 28 événements, 14 presets, registre des images, 11 assertions, 8 décisions | 89 203 octets · 3 422 lignes · `json.tool` OK |
| `RAPPORT_V1_2_INGENIERIE_T1.md` | ce document, sections A → I | — |

**Périmètre exclusif** : Restaurants et Maquis / T1 / 4 scènes / 12 plans / 30,0 s / 6 champs / 8 blocs graphiques / 14 presets. Aucun autre gabarit.

| Statut | Sens |
|---|---|
| **CORRIGÉ** | défaut identifié, cause nommée, valeur remplacée et verrouillée par un contrôle |
| **COHÉRENT** | vérifié par calcul à la génération du JSON |
| **DÉCIDÉ** | arbitrage d'ingénierie pris ici, plus renvoyé à l'utilisateur |
| **À CONFIRMER AU RENDU** | seul un rendu réel peut trancher (perception) — n'empêche pas le test |

---

## A. Objet, méthode, ce qui n'a pas bougé

La V1.2 corrigée répond aux neuf points de la clôture **sans refaire l'ingénierie** et **sans nouvelle recherche générale**. Trois défauts de la V1.2 initiale ont été trouvés et corrigés dans cette passe (section B.2) : le budget d'images qui ne se refermait pas, une distance de transition mal calculée, et des statuts d'API présentés comme stables à tort.

Méthode : le JSON n'est pas écrit à la main mais **généré** par un script qui refuse de s'écrire si un contrôle échoue (12 plans contigus, 900 images, boîtes dans la safe zone, événements loin des transitions, registre clos, durées de preset égales aux durées de bloc). Le fichier produit est ensuite **relu et validé** (`json.loads` + `json.tool`, détection de clé dupliquée, vérification des références croisées entre blocs, textes, événements et presets).

**Inchangé et non négociable** : durées de tournage V6.2 (6 / 8 / 7 / 9 s), 30,0 s exactement, CTA 3,5 s, fade-out 1,5 s, 6 champs, 8 blocs de textes commerciaux, aucun sous-titre de dialogue, ni logo ni filigrane ni signature, deux polices SIL OFL, audio hors périmètre, safe zone x 64–920 / y 240–1440.

---

## B. Audit

### B.1 Corrections de la V1.1 (rappel, inchangé depuis la V1.2 initiale)

| ID | Défaut V1.1 | Statut |
|---|---|---|
| ERR-01 | « aucune composition spatiale de deux flux » — faux : `Composition` documente le chevauchement de séquences ; seule limitation = crossfade natif | **CORRIGÉ** |
| ERR-02 | animations « quantifiées à 20 états/s » en bitmaps | **CORRIGÉ** (overlay redessiné par image) |
| ERR-03 | `bandeau_produit` entrait sur la punch cut de 3,500 s | **CORRIGÉ** — GB02 à 120, soit 9 images après la fin de TR02 |
| ERR-04 | fin de bloc non contrôlée : `accroche` sortait 0,10 s avant la coupe de 14,000 s | **CORRIGÉ** — sortie à 405, coupe à 420 |
| ERR-05 | contrôle A6 inopérant (il ne regardait que les apparitions et affichait « 0 ») | **CORRIGÉ** — A6 sur les 28 événements |
| ERR-06 | MV11 défini en zoom avant, appliqué en zoom arrière sur P12 | **CORRIGÉ** |
| ERR-07 | MV11 exigeait ≥ 3 s de drift dans un plan qui n'en offre que 2,5 | **CORRIGÉ** — 75 images |
| ERR-08 | +0,80 s de tournage forfaitaire sur les 4 prises | **CORRIGÉ** — V6.2 rétabli, écart absorbé par le gel (D) |
| ERR-09 | safe zone contrôlée sur le rectangle nominal | **CORRIGÉ** (F) |
| ERR-10 | A1 tautologique (égalité avec un exemple) | **CORRIGÉ** (G.2) |
| ERR-11 | seuil de recadrage énoncé en k absolu, présenté comme universel | **CORRIGÉ** (H) |
| ERR-12 | poignées exprimées en secondes, jamais converties en images | **CORRIGÉ** (D) |

### B.2 Auto-audit de la V1.2 — les trois défauts signalés

| ID | Défaut de la V1.2 initiale | Ce qui n'allait pas | Correction |
|---|---|---|---|
| V12-01 | « 863 images de matière + 97 images de gel » | 863 comptait l'amorce et les écarts entre extraits, qui ne sont **pas** exportés : le total affiché valait 960 | **CORRIGÉ** — registre image par image (D) : 900 = 785 images de prise **utilisées** + 115 images figées ; 18 images de poignée de transition et 97 images non lues comptées à part |
| V12-02 | « l'événement de l'image 120 se produit 15 images après la fin de TR02 à l'image 111 » | 120 − 111 = **9**, pas 15 (le 15 venait de la comparaison avec le début de TR02, image 105) | **CORRIGÉ** — les 28 distances sont recalculées et tabulées (`checks.distances_evenements_transitions`), minimum **9 images** |
| V12-03 | `MatrixTransformation`, `Transformer`, transitions et export décrits « stable » ; `CanvasOverlay` présenté comme « aucun bitmap par image » | Les quatre sont annotés `@UnstableApi` dans la référence officielle ; `CanvasOverlay` **dérive de `BitmapOverlay`** et expose une `Bitmap` de la taille du Canvas | **CORRIGÉ** — statuts vérifiés un par un (C.2), réalité bitmap décrite et budgétée (C.5) |

Les trois points sont désormais tenus par des contrôles exécutés : le registre est une section du JSON avec équations par plan, par scène et au total ; les distances sont une table de 28 lignes ; les statuts citent l'annotation et l'URL.

---

## C. Moteur de rendu, statuts réels des API, techniques d'animation

### C.1 Architecture

- **2 séquences** : séquence A = plan principal ; séquence B = plan entrant, utilisée **seulement** sur les 3 transitions à deux séquences (TR03 à 180, TR05 à 420, TR04 à 630).
- **1 overlay** : `T1GraphicsOverlay extends CanvasOverlay`, qui dessine toutes les compositions graphiques à `presentationTimeUs`.
- Ordre figé : étalonnage (matrice 4×5) → transformation géométrique (k + mouvement) → composition des séquences → overlay → encodeur. Aucun tirage aléatoire.

### C.2 Statuts vérifiés (référence officielle, consultée le 2026-11-17)

| API | Annotation réelle | Statut retenu | Conséquence pratique |
|---|---|---|---|
| `effect.MatrixTransformation` | **`@UnstableApi`**, interface `extends GlMatrixTransformation` | unstable | `@OptIn(UnstableApi::class)` ; signature susceptible de changer entre versions mineures → version figée dans le version catalog |
| `effect.CanvasOverlay` | **`@UnstableApi`**, `extends BitmapOverlay`, `onDraw(Canvas, long)`, `getBitmap(long)` | unstable | idem + une `Bitmap` allouée (C.5) |
| `effect.TextOverlay` | **`@UnstableApi`**, `extends BitmapOverlay`, `SpannableString`, `TEXT_SIZE_PIXELS = 100` | unstable | non retenu : texte rastérisé à 100 px puis mis à l'échelle |
| `effect.lottie.LottieOverlay` | **`@UnstableApi`**, `extends CanvasOverlay` | unstable | non retenu (C.4) |
| `transformer.Transformer` | **`@UnstableApi`**, classe finale | unstable | opt-in ; API d'export à surveiller à chaque montée de version |
| `RgbMatrix`, `HslAdjustment`, `Contrast` | module `media3-effect` entièrement `@UnstableApi` ; annotation individuelle **non vérifiée** | unstable (présumé) | traité comme instable par prudence |
| `Composition` / `EditedMediaItemSequence` / `VideoCompositorSettings` | documentés dans le guide Transformer ; **page de référence `VideoCompositorSettings` inaccessible (404)** à la vérification | à confirmer à l'intégration | signature exacte de `getOverlaySettings` à valider sur la version embarquée |
| `EditedMediaItem.Builder.setFrameRate` | cité dans les notes de version Media3 | à confirmer à l'intégration | — |

Aucun de ces points ne bloque le test : **le prototype Python/FFmpeg ne dépend d'aucune API Media3**. La vérification de version appartient à l'intégration Android (D-04).

### C.3 Comparaison des techniques d'animation (section `animation_techniques` du JSON)

| Technique | Principe | Avantages | Limites | Coût | Dépendance | Compatibilité | Intérêt T1 |
|---|---|---|---|---|---|---|---|
| Bitmaps précalculées | 5 à 7 PNG par apparition | aucune API instable, dessin quasi gratuit | quantification visible, explosion du nombre de fichiers, aucune adaptation aux 6 champs | 1 à 3 Mo par bloc | aucune | toutes | repli |
| `BitmapOverlay` | une Bitmap + réglages par image | API documentée, simple | contenu figé : une image = un état | 1 bitmap | aucune | `@UnstableApi` | brique de repli |
| **`CanvasOverlay`** | composition redessinée chaque image sur une Bitmap unique | animation continue sans quantification, paramétrable par les 6 champs, une classe pour 14 presets | dessin CPU à tenir, Bitmap de la taille du Canvas | ~6 ms/image visés | `media3-effect` | `@UnstableApi` | **retenu** |
| `TextOverlay` | `SpannableString` rastérisé à 100 px puis mis à l'échelle | styles par caractère | flou sur un titre de 116 px, pas de masque | faible | `media3-effect` | `@UnstableApi` | non retenu |
| `LottieOverlay` | dessine un fichier Bodymovin | animations riches, prévisualisation | dépendance Lottie + 1 fichier par animation, injection des champs dans le JSON | moyen à élevé | Media3 + Lottie | `@UnstableApi` | non retenu |
| Rendu personnalisé (`GlEffect`) | shader GPU | effets impossibles autrement (masque) | développement, risque GPU sur 2 Go | élevé | — | variable | réservé à TR08, hors pilote |

**Pourquoi pas Lottie** : nos 14 presets sont **paramétriques** (le nom, le prix, le quartier changent à chaque publicité). Un fichier Lottie devrait être régénéré ou templaté pour chaque combinaison, avec une dépendance supplémentaire et un temps de parse au premier rendu, pour un résultat identique à ce qu'un `CanvasOverlay` produit déjà. La décision est documentée dans le JSON (`SRC05`, `media3_spec`), pas laissée ouverte.

### C.4 Crossfade — description corrigée

`VideoCompositorSettings.getOverlaySettings(int inputId, long presentationTimeUs)` est appelé **à chaque image** et **retourne** un `OverlaySettings` recalculé pour cette image. Ce n'est **pas** une instance statique dont on modifierait les propriétés en continu — c'est exactement l'erreur de description corrigée ici.

Forme retenue pour TR05 (6 images, 200 ms) : `t = (presentationTimeUs − t0) / durée`, `alpha_A = 1 − easeInOutQuad(t)`, `alpha_B = easeInOutQuad(t)`, retournés via `StaticOverlaySettings.Builder().setAlphaScale(...).build()`. Aucun effet natif de crossfade n'existe : c'est une construction custom, à valider au premier rendu (D-08).

### C.5 Charge réelle de l'overlay (pas de « coût nul »)

`CanvasOverlay` **n'élimine pas la bitmap** : il en fournit une, de la taille du Canvas, allouée une fois dans `configure()`, puis effacée et redessinée à chaque image.

- Mémoire : 1080 × 1920 × 4 o = **8,3 Mo** ; 720 × 1280 × 4 o = **3,7 Mo** (format du pilote).
- Allocations par image : **zéro** — `Path`, `Paint` et mesures de texte sont construits une fois et réutilisés ; aucun objet créé dans `onDraw`.
- Budget CPU cible : **≤ 6 ms de dessin par image** (marge sous les 33,3 ms d'une image à 30 fps) ; à mesurer au test réel.
- Coût des courbes d'easing : 5 itérations de Newton par piste et par image, négligeable devant le dessin.

---

## D. Registre des images — 900 images, sans ambiguïté

`frame_ledger` du JSON est la référence. Trois catégories distinctes, jamais confondues :

1. **images de prise utilisées** — jouées telles quelles dans la publicité ;
2. **images figées** — répétition de la dernière image de prise du plan, ajoutée à la timeline ;
3. **images lues et non exportées** — amorce caméra, écarts entre extraits, poignées de transition, réserve de fin de prise.

Équation vérifiée à la génération, plan par plan, scène par scène et au total :

```
images_sortie_du_plan = images_source_utilisées + images_figées
900                   = 785                    + 115
```

### D.1 Registre par plan (intervalles semi-ouverts, images @30 fps)

| Plan | Sc. | Sortie | Prise lue | Utilisées | Poignée transition | Figées | Exportées | Équation |
|---|---|---|---|---|---|---|---|---|
| P01 | S1 | 0–60 | 9–62 | 53 | 0 | 7 | 60 | 60 = 53 + 7 |
| P02 | S1 | 60–105 | 65–104 | 39 | 0 | 6 | 45 | 45 = 39 + 6 |
| P03 | S1 | 105–180 | 107–176 | 63 | **6** | 12 | 75 | 75 = 63 + 12 |
| P04 | S2 | 180–255 | 9–77 | 68 | 0 | 7 | 75 | 75 = 68 + 7 |
| P05 | S2 | 255–330 | 80–148 | 68 | 0 | 7 | 75 | 75 = 68 + 7 |
| P06 | S2 | 330–420 | 151–236 | 79 | **6** | 11 | 90 | 90 = 79 + 11 |
| P07 | S3 | 420–495 | 9–77 | 68 | 0 | 7 | 75 | 75 = 68 + 7 |
| P08 | S3 | 495–555 | 80–133 | 53 | 0 | 7 | 60 | 60 = 53 + 7 |
| P09 | S3 | 555–630 | 136–206 | 64 | **6** | 11 | 75 | 75 = 64 + 11 |
| P10 | S4 | 630–705 | 9–79 | 70 | 0 | 5 | 75 | 75 = 70 + 5 |
| P11 | S4 | 705–795 | 82–167 | 85 | 0 | 5 | 90 | 90 = 85 + 5 |
| P12 | S4 | 795–900 | 170–245 | 75 | 0 | **30** | 105 | 105 = 75 + 30 |
| **Σ** | | **900** | | **785** | **18** | **115** | **900** | **900 = 785 + 115** |

Les trois poignées de transition correspondent aux trois transitions à deux séquences (TR03 à 180, TR05 à 420, TR04 à 630) : pendant 6 images, le plan sortant continue d'être lu pour être composé avec le plan entrant. Ces images **sont** dans les 30 secondes (elles composent l'image de transition) mais **ne sont pas** des images propres du plan sortant : elles sont donc comptées séparément et n'entrent pas dans son équation de sortie.

### D.2 Réconciliation par scène

| Scène | Images exportées | Équation de sortie | Équation de prise |
|---|---|---|---|
| S1 | **180** | 180 = 155 + 25 | 180 = 9 (amorce) + 6 (écarts) + 155 (source) + 6 (poignées) + 4 (réserve) |
| S2 | **240** | 240 = 215 + 25 | 240 = 9 + 6 + 215 + 6 + 4 |
| S3 | **210** | 210 = 185 + 25 | 210 = 9 + 6 + 185 + 6 + 4 |
| S4 | **270** | 270 = 230 + 40 | 270 = 9 + 6 + 230 + 0 + 25 |
| **Total** | **900** | | |

Chaque scène est donc **exactement** à sa durée V6.2 : 180 / 240 / 210 / 270 images = 6 / 8 / 7 / 9 s. **Aucune seconde de tournage n'est ajoutée.**

### D.3 Ce que le gel est — et ce qu'il n'est pas

Le gel vaut 115 images (3,833 s) au total, dont **30 images de verrou CTA** (870–899). Hors CTA : 85 images réparties sur 11 plans, soit 5 à 12 images par plan (0,17 à 0,40 s). L'amorce caméra de 0,30 s (9 images) et les écarts de 0,10 s entre extraits d'une même prise sont **conservés** : ce sont eux qui protègent la mise au point et évitent de couper dans un mouvement de main.

**La discrétion visuelle des gels n'est pas un fait démontré.** Elle repose sur une hypothèse raisonnable (tenir 0,2 à 0,4 s en fin de plan ne se lit pas comme une image figée) et devient un **critère explicite du premier test réel** : si un gel se voit à la lecture, la répartition est reprise plan par plan sans toucher au tournage. Aucune phrase de ce rapport ne présente cette discrétion comme mesurée.

---

## E. Matrice unique de référence

| Bloc | Composition | Images | Durée | Presets | Événements | Écart min. à une transition animée |
|---|---|---|---|---|---|---|
| GB01 | enseigne_mot_a_mot | 15 → 90 | 2,50 s | MD-T1-01, 02 | TXT01-E1/E2/E3/X | 15 (sortie 90 vs TR02 105) |
| GB02 | bandeau_produit | 120 → 165 | 1,50 s | MD-T1-03 | TXT02-E1/E2/E3/X | **9** (E1 120 vs fin TR02 111) |
| GB03 | hero_lockup + pastille + filets | 195 → 285 | 3,00 s | MD-T1-04, 05, 12 | TXT03-E1/E2/E3/X | **9** (E1 195 vs fin TR03 186) |
| GB04 | accroche_segments | 300 → 405 | 3,50 s | MD-T1-06 | TXT04-E1/E2/E3/X | 15 (X 405 vs TR05 420) |
| GB05 | enseigne_rappel | 450 → 525 | 2,50 s | MD-T1-07 | TXT05-E1/E2/E3/X | 24 (E1 450 vs fin TR05 426) |
| GB06 | prix_plein | 540 → 615 | 2,50 s | MD-T1-08, 13 | TXT06-E1/E2/X | 15 (X 615 vs TR04 630) |
| GB07 | adresse | 645 → 765 | 4,00 s | MD-T1-09 | TXT07-E1/E2/X | **9** (E1 645 vs fin TR04 636) |
| GB08 | cta_whatsapp | 795 → 900 | 3,50 s | MD-T1-10, 11 | TXT08-E1/X | 159 — entrée sur une coupe sèche, choix assumé |

Contrôles attachés : **A5** un seul bloc actif (0 intersection) ; **A6** aucun événement dans une transition animée ni à moins de 6 images (200 ms) de ses bords — **écart minimal mesuré 9 images, 0 collision** ; **A7** écart à la grille 250 ms ≤ 0,5 image, sorties de bloc exactement sur la grille ; **rythme** écart maximal entre deux événements 105 images (3,50 s), et cet écart est le maintien volontaire du CTA — hors CTA, jamais plus de 30 images (1,00 s).

> La phrase de la V1.2 initiale (« 15 images après la fin de TR02 ») est remplacée partout par **9 images** : TR02 occupe les images 105 à 110, sa borne de fin est 111, et 120 − 111 = 9. Les 28 distances sont tabulées dans `checks.distances_evenements_transitions` ; aucune fenêtre conforme n'a été déplacée.

### E.1 Transitions

- **11 points de coupe** : 60, 105, 180, 255, 330, 420, 495, 555, 630, 705, 795.
- **4 transitions animées** de 6 images : TR02 punch cut à 105, TR03 wipe géométrique à 180, TR05 crossfade court à 420, TR04 wipe directionnel à 630.
- **7 coupes sèches** TR01. La bibliothèque compte 8 entrées ; TR06, TR07 et TR08 ne sont pas utilisées dans T1.

### E.2 Traçabilité : des références marché aux 14 presets

Sources déjà établies en V6.2 (aucune recherche refaite), numérotation conservée.

| Réf. | Observation retenue | Intérêt commercial | Adaptation aux 4 scènes | Presets concernés |
|---|---|---|---|---|
| R1 (V6.2 [3][5]) | segments de 3 à 7 mots sur 1 à 3 s ; 1 à 3 mots surlignés max | le commerçant est **lu** avant d'être écouté | S1 : nom puis produit en 1,5 s ; S2 : accroche en 3 segments | MD-T1-01, 02, 03, 06 |
| R2 (V6.2 [4]) | la typo cinétique au tiers médian retient mieux ; contour 2–3 px + ombre ~30 % / 10 px | lisible en plein soleil, sur dalle d'entrée de gamme | S1 (nom) et S3 (rappel du nom) | MD-T1-01, 07 |
| R3 (V6.2 [6]) | dépassement 15–20 % en translation, 5–10 % en échelle, jamais sur l'opacité ; sortie plus rapide que l'entrée | rendu « pro » sans artefact de flash | les 4 scènes | MD-T1-05, 08, 11, 14 + easing de tous |
| R4 (V6.2 [7]) | `easeOutExpo` = courbe d'entrée de référence, 200–260 ms | arrivée feutrée = perception de qualité | S1, S2, S4 | MD-T1-01, 03, 04, 06, 09 |
| R5 (V6.2 [9]) | effets de 0,2 à 0,4 s ; speed ramp tôt ; flash de 2 images ; **jamais plus de 2 effets par plan** | reset d'attention avant la décroissance | S1 : push sur P02 (2,0–3,5 s) ; S3 : push sur P08 (16,5–18,5 s) | MV03 (P02, P08), MD-T1-05, TR02 |
| R6 (V6.2 [12][13]) | la qualité perçue vient d'une **signature animée par gabarit**, pas d'effets génériques | le commerce paraît « fait par un pro » avec des rushes au téléphone | S2 : le lockup incliné + pastille ; S3 : passation | MD-T1-04, 05, 12, 13 |
| R7 (V6.2 [14][15][16]) | zone commune 900 × 1400 ; marges UI 108–220 haut, 310–320 bas, 84–140 droite | aucun prix ni numéro masqué par l'interface | les 4 scènes | boîtes GB01–GB08 (F) |
| R8 (V6.2 [8]) | n'animer qu'opacité, translation, échelle | export possible sur un Android 2 Go | les 4 scènes | les 14 presets (aucun n'anime autre chose) |
| R9 (V6.2 [22][23][24]) | zoom de 5 à 10 % ressenti sans être vu ; varier la direction | image vivante même si la main tremble | S1, S2, S4 | MD-T1-11, 12 ; MV01, MV02, MV11 |
| R10 (V6.2 [20][21]) | bitmaps de texte rastérisées une fois ; `setFrameRate` | le moteur tient sur les téléphones du marché cible | les 4 scènes | architecture (C) |
| R5b (V6.2 [9]) | jamais plus de 2 effets par plan | évite la surcharge qui fait sortir | les 4 scènes | règle appliquée : 1 mouvement + 1 transition max |

**Couverture : 14/14 presets** portent au moins une référence et un objectif commercial identifiable (le mapping est aussi dans `presets[].refs_marche` et `presets_justification`). Par scène : S1 = MD-01, 02, 03 ; S2 = MD-04, 05, 06, 12 ; S3 = MD-07, 08, 13 ; S4 = MD-09, 10, 11, 14.

**Avertissement conservé dans le JSON** : les pourcentages cités par R5 (+18 % de rétention, +42 % de complétion) viennent d'articles marketing sans méthodologie vérifiable. Ils justifient un **choix de montage**, jamais une promesse de performance. Aucune décision de cette spécification ne repose sur ces chiffres.

---

## F. Safe zones et boîtes complètes

Zone : **x 64–920, y 240–1440**. Pour chaque bloc, deux boîtes calculées : `box_shape` (rectangle dilaté par la rotation −3° et le contour) et `box_full` (+ flou et décalage d'ombre).

- `box_shape` dans la safe zone : **8/8** ;
- `box_full` dans le cadre 1080 × 1920 : **8/8** ;
- débord d'ombre maximal : **7 px** (GB08) ; les autres : 0 à 5 px ;
- **aucun glyphe** hors de `box_shape` ; boîtes texte dérivées avec les marges réelles (24 px, 20 px pour GB06, 16 px pour GB03).

GB03 (lockup pivoté) et GB08 (pilule pleine largeur à ombre de 16 px) ont été déplacés de quelques pixels par rapport à la V1.1 pour tenir dans la zone.

---

## G. Données

6 champs strictement inchangés : `nom`, `produit`, `prix`, `whatsapp`, `quartier`, `accroche`. Aucun séparateur imposé, aucune syntaxe de saisie créée.

- **Règles** : trim, espaces multiples réduits ; aucun changement d'accent, de casse, d'apostrophe ou de tiret ; aucune troncature ; seul le point final est retiré (`nom`, `produit`, `accroche`).
- **Prix** : chaîne conservée, « FCFA » ajouté **à l'affichage** seulement s'il est absent — le prix s'affiche donc identique en GB03 et GB06.
- **Quartier** : découpe sur virgule, sinon « - » ou « / », sinon un segment ; jamais de coupure de mot.
- **Accroche** : texte libre ; découpe sur « · » ou « • » si présent, sinon 3 segments aux frontières de mots.

**Replis d'accroche A→D, cohérents avec la matrice E** : aucun ne déplace une fenêtre. A = GB04 300/345/390 (sortie 405) ; B = accroche vide → GB04 supprimé, GB03 prolongé jusqu'à 345 (écart maximal 105 images = 3,50 s, conforme) ; C = B + GB03 affiche le produit seul (GB06 reste 540–615) ; D = accroche d'un mot → carton 300–360.

**A1 refondue** : toute chaîne affichée est traçable à un champ saisi (`provenance = user_input:<champ>`), plus un test négatif — saisir exactement les valeurs d'exemple doit produire un montage valide.

---

## H. Cadrage et résolution — justification du plafond 1,70

`sources : prise 1080 × 1920`, `sortie du pilote 720 × 1280`, `k = 1 / fraction de largeur prélevée`.

Le facteur d'agrandissement réel se calcule exactement : largeur prélevée = 1080 / k, affichée à 720 px, donc **agrandissement = 0,6667 × k**.

- `k ≤ 1,50` → aucun rééchantillonnage (720 / 720 = 1,000). C'est la limite sans perte.
- `k = 1,70` → agrandissement **1,133×** ;
- `k = 1,55` (fin de P08, avec son push) → agrandissement 1,116× au maximum.

Douze plans, dont **dix** restent sous 1,50 à tout instant ; **deux** dépassent en fin de mouvement : P03 (constant à 1,70 → 1,133×) et P08 (qui monte à 1,674 pendant son push de 2 s → 1,116×). Sur un écran de téléphone, 13 % d'agrandissement sur un plan large en mouvement n'est pas démontrable comme invisible : c'est une **limite de conception à confirmer au premier rendu** (D-07).

Pourquoi ne pas descendre à 1,50 tout de suite : la règle A4 (aucun écart d'échelle effectif dans ]2 %, 15 %[) impose 1,70 à la coupe 105. Le repli est déjà calculé et vérifié : **P03 1,70 → 1,55 et P02 1,35 → 1,22** donnent +16,2 % et +17,6 % aux coupures 60 et 105 — A4 reste respecté, l'agrandissement tombe à 1,03×, rien d'autre ne bouge.

L'export 1080 × 1920 reste **hors du premier test** (D-03) sans être déclaré impossible : à cette résolution le plafond tomberait à `k = 1080/1080 = 1,00`… ce qui rendrait A4 inapplicable en l'état — c'est un chantier de cadrage, à rouvrir seulement si le 1080p devient un objectif.

---

## I. Assertions, décisions, contrat de passage, état final

### I.1 Assertions (11, toutes vérifiées à la génération)

| ID | Objet | Résultat |
|---|---|---|
| A1 | provenance des textes + test négatif | **COHÉRENT** |
| A2 | 12 plans contigus, 900 images, aucun trou | **COHÉRENT** |
| A3 | fenêtres sources et poignées ≥ 4 images | **COHÉRENT** — 12/12 |
| A4 | écarts d'échelle effectifs aux 11 coupures | **COHÉRENT** — min 16,6 %, max 41,2 % |
| A5 | un seul bloc actif | **COHÉRENT** — 0 intersection |
| A6 | événements vs transitions animées (200 ms) | **CORRIGÉ** — min 9 images, 0 collision |
| A7 | images entières + grille 250 ms | **COHÉRENT** — 0,5 image max |
| A8 | CTA 795–899 inclus, 105 images = 3,500 s, sans sortie | **COHÉRENT** |
| A9 | boîtes complètes (rotation, contour, ombre) | **COHÉRENT** — 8/8, débord ≤ 7 px |
| A10 | indépendance piste graphique / audio | **COHÉRENT** |
| A11 | **registre des images clos** | **CORRIGÉ (V12-01)** — 900 = 785 + 115 ; 18 poignées ; 97 non lues |

### I.2 Décisions prises — il n'y a plus de question ouverte

| ID | Sujet | Décision | Statut |
|---|---|---|---|
| D-01 | tournage | **6 / 8 / 7 / 9 s conservées** | **DÉCIDÉ** |
| D-02 | sortie du pilote | 720 × 1280 à 30 fps | **DÉCIDÉ** |
| D-03 | 1080 × 1920 | hors du premier test, non déclaré impossible | **DÉCIDÉ** |
| D-04 | version Media3 | vérifiée à l'intégration Android ; non bloquante pour le prototype FFmpeg | **DÉCIDÉ** |
| D-05 | MV08 contre-mouvement | **écarté pour T1** : pan maximal 14 px × 0,30 = 4 px résiduels, sous le seuil perceptible ; la lisibilité prime et le couplage image/texte disparaît | **DÉCIDÉ** |
| D-06 | budget de gel | 115 images dont 30 de verrou CTA | **DÉCIDÉ** |
| D-07 | plafond de recadrage | 1,70 conservé (imposé par A4), repli P02 1,22 / P03 1,55 déjà calculé | **DÉCIDÉ**, qualité à confirmer au rendu |
| D-08 | crossfade TR05 | construit par `getOverlaySettings` par image | **DÉCIDÉ**, rendu à confirmer |

### I.3 Contrat de passage : V6.2, V1.2, prototype FFmpeg, backend Media3

Deux spécifications, deux autorités, aucun conflit silencieux.

| | `restaurants_maquis_T1.spec_v6_2.json` | `T1_ENGINEERING_SPEC_V1_2.json` |
|---|---|---|
| Autorité sur | durées de tournage (6/8/7/9), contenu des 6 champs, guide destiné au commerçant, direction artistique (polices, couleurs, contour, ombre), SFX et musique | positions et durées en images, fenêtres source, 8 blocs, 28 événements, transitions, mouvements, safe zones, format du prix, replis A–D, assertions |
| Statut | **lecture seule** | **lecture seule** |
| N'est pas | un plan de montage | un contrat de tournage |

**Règle de précédence** : en cas de divergence, V1.2 gagne sur tout ce qui relève du **montage** (temps, placements, cadrage, transitions) ; V6.2 gagne sur tout ce qui relève du **tournage et des données** (durées de prise, textes saisis, DA, audio). Aucune valeur V6.2 n'écrase une valeur corrigée de V1.2 : chaque valeur du plan de rendu porte sa provenance.

**Le chaînon manquant est l'adaptateur** (`t1_adapter`) : il lit les deux fichiers, produit un `render_plan.json` intermédiaire, et **n'écrit dans aucun des deux**. Mapping exact (section `adapter_contract` du JSON) :

| V6.2 | V1.2 | `render_plan.json` |
|---|---|---|
| `scenes[i].duree_enregistree_s` | `scenes[i].frames` (180/240/210/270) | `scene.frames` |
| `plans[j].fenetre_prise` (s) | `plans[j].source_in_f / source_out_f` | `shot.in_frame / out_frame` |
| `textes_ecran[k].champ` | `text_blocks[k]` + `events` | `overlay.block[]` |
| polices, couleurs, contour, ombre | `text_px_base`, `stroke_px`, `shadow_px` | `style` |
| musique + SFX | hors périmètre audio | `audio_track` (inchangé) |
| — | `k_base` + `movements` | `shot.zoom_curve` |
| — | `transitions.assignments` | `cut[i].transition` |

**Deux implémentations, une seule spécification** :

- **Prototype Python/FFmpeg** (le test prévu) : consomme `render_plan.json`, ne dépend d'aucune API Media3 ; il vérifie les 900 images, les coupes, les placements, la qualité perçue des gels et l'agrandissement de P03/P08.
- **Backend Android Media3** (production envisagée) : consomme le **même** `render_plan.json` ; il vérifie la disponibilité des API `@UnstableApi`, le budget mémoire (3,7 Mo d'overlay en 720p) et le CPU à 30 fps, et doit produire un rendu identique au rendu de référence FFmpeg.

### I.4 Ce qui reste réservé au rendu réel

Cinq jugements de perception, qui ne sont pas des questions produit et qui n'empêchent pas le test : visibilité des gels (D.3), agrandissement de P03/P08 (H), rendu du crossfade TR05 (C.4), lisibilité des 8 blocs à 720p, charge de dessin réelle de l'overlay à 30 fps (C.5).

### I.5 État final

- **Les 900 images sont réconciliées** : 900 = 785 images de prise + 115 images figées ; 18 images de poignée de transition et 97 images non lues comptées à part ; 180/240/210/270 par scène.
- **Les quatre durées de tournage sont respectées** (6/8/7/9 s) — aucun tournage supplémentaire.
- **Transitions et événements sont cohérents** : 11 coupes, 4 transitions animées, écart minimal 9 images, 0 collision.
- **Statuts d'API documentés** avec annotation et URL ; aucune API instable présentée comme stable.
- **6 techniques d'animation comparées** ; Lottie justifié et écarté.
- **14 presets reliés** aux 10+1 références marché, avec adaptation par scène.
- **Données et plans cohérents** : 6 champs, 8 blocs, 4 replis sans déplacement de fenêtre.
- **JSON valide** : 89 203 octets, `json.tool` OK, aucune clé dupliquée, références croisées vérifiées.
- **Le futur rendu sait quoi lire** : `render_plan.json` produit par `t1_adapter` depuis V1.2 (autorité montage) + V6.2 (autorité tournage/données).

**Consolidation documentaire terminée.** Aucun rendu, aucun assemblage, aucune modification de production n'a été effectué pendant cette mission. Prochaine étape, sans nouvelle mission de perfectionnement documentaire : dépôt GitHub privé, puis **test réel T1**.
