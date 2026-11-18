# T1 — Audit final : parcours de capture et montage (version de clôture)

**Projet** : VITRINE VIDÉO — T1 « Plat du jour », démonstration pour restaurants et maquis (Bénin)
**Mission** : clôture — dernière réconciliation du moteur et du parcours · 17 novembre 2026
**Dépôt** : `j9028379-hue/vitrine-video-t1-pilot`, branche `main`
**Hors périmètre, non touché** : tout l'audio (aucune musique, aucun effet, aucune modification de fichier son).

Cette version **remplace** l'audit précédent, qui reste la base technique. Elle ne refait aucune partie du travail : elle corrige trois choses (le titre de la section voix, la présentation de la zone défilable, la géométrie graphique pilotée par la configuration), réconcilie les trois transitions avec la dynamique approuvée et traite la netteté des plans faibles.

---

## 1. Espace de travail et nettoyage

| Mesure | Audit précédent | Aujourd'hui |
|---|---|---|
| Taille du dépôt local | 126 Mo | 291 Mo (rushes HD + video de contrôle) |
| Fichiers suivis | 152 | 168 |
| Commit de départ | `42989e4` | `1d2fb54` (audit) + commit de clôture |
| Master final | 900 images, 30 s | 900 images, 30 s (**nouveau**, un seul) |

Nouveaux fichiers de cette mission :

| Fichier | Rôle |
|---|---|
| `config/T1_presentation_v3_1.json` | **configuration de présentation** : 8 blocs, 31 éléments (géométrie, taille, alignement, typographie, couleur, proportions, forme, espacements, entrées/sorties) |
| `engine/presentation.py` | moteur de rendu **générique** qui consomme cette configuration |
| `engine/motion_v4.py` | chaîne de montage réconciliée (fenêtres, caméra, transitions, blocs) |
| `rushes/build_scenes.sh` | prises reconstruites dans la définition native des rushs |
| `tools/verify_master.py` | contrôle du MP4 : 24 points (indice source + zoom mesurés) |
| `tools/tableau_final.py` | tableau final JSON / code / MP4 |
| `tools/comparaison_transitions.py` | comparaison temporelle des trois transitions |
| `preuves/audit_v4/` | 9 planches de contrôle |

Aucune ancienne vidéo n'a été écrasée. Rien n'a été supprimé sans que le fichier existe ailleurs (GitHub ou Release).

---

## 2. Vérification des 4 consignes

La **source unique** reste `capture-guide/consignes_T1.json`, consommée par `tools/build_consignes.py` → `simulation/consignes.js` + `capture-guide/consignes_4_scenes.md`.

Deux corrections demandées, et seulement deux :

1. **Titre de la section voix** : « Enregistrer sa voix » → **« TU PEUX PARLER PENDANT QUE TU FILMES »**. La mention V6.2 elle-même n'est pas touchée :
   > « Tu peux parler pendant que tu filmes, en fon, yoruba, français ou anglais, pour présenter ton produit. » — **102 caractères**, une seule occurrence dans le JSON, donc identique dans les 4 scènes.
2. **Zone défilable** : le contenu ne paraît plus coupé sous le bouton fixe (voir §3.3).

Les quatre consignes et les durées sont inchangées :

| Scène | Titre | Durée | Consigne | À filmer | À éviter |
|---|---|---|---|---|---|
| 1/4 | LE PLAT | **6 s** | inchangée | 3 | 3 |
| 2/4 | LE DESSUS ET LES DÉTAILS | **8 s** | inchangée | 2 | 2 |
| 3/4 | LA PERSONNE QUI SERT | **7 s** | inchangée | 3 | 2 |
| 4/4 | LE LIEU ET LE CONTACT | **9 s** | inchangée | 3 | 2 |

---

## 3. Lisibilité et 12 états

### 3.1 Mesures (12 combinaisons 360/390/430 × 4 scènes) — inchangées et conformes

| Élément | Cible | Mesuré |
|---|---|---|
| Consigne | 17–18 px | **17,5 px** |
| `À FILMER` / `À ÉVITER` | 14–16 px | **15 px** |
| Titres de section | 12–14 px | **12,5 px** |
| Mention vocale | 14–15 px | **14,5 px** |
| Exemple facultatif | 14–15 px | **14,5 px** |
| Bouton | 16–18 px | **17 px** |

`overflow_horizontal: false`, `cta_visible: true` sur les 12 combinaisons. Source : `reports/verification_lisibilite.json`.

### 3.2 Les 3 états

A = fiche + bouton · B = **la fiche disparaît complètement** (aperçu + chrono + barre) · C = relecture + `REFAIRE` / `SCÈNE SUIVANTE` (et `VOIR MON MONTAGE` après la scène 4). Les 12 captures sont régénérées : `ui-screens/ecran_08_scene{1..4}_etat{A,B,C}_*.png`, planche `ui-screens/planche_12_etats.png`.

### 3.3 Ce qui a changé dans la zone défilable

| Avant | Après |
|---|---|
| dégradé de 30 px, texte encore lisible jusqu'au bord | dégradé de **52 px** qui dissout la ligne au lieu de la couper |
| pas de repère de défilement | repère discret **↓** dans la marge droite, affiché seulement si le contenu dépasse et disparaît en fin de fiche |
| barre de défilement invisible sur certains navigateurs | barre fine stylée (6 px) + `scroll-padding-bottom` |
| marge basse de 6 px | marge basse de **34 px** : le dernier bloc ne colle jamais au bouton |

Mesure conservée après correction : **12/12 combinaisons OK**, bouton visible, aucun débordement horizontal.

---

## 4. Versions vidéo conservées

| Version | Fichier | Taille | SHA-256 (début) | Statut |
|---|---|---|---|---|
| V2 | `output_T1_sans_voix_v2.mp4` | 22 Mo | `21e8f5d80fcd…` | conservée |
| V3 | `output_T1_sans_voix_v3.mp4` | 8,5 Mo | `9f03b9cbdebb…` | conservée |
| **V3.1** | `output_T1_sans_voix_v3_1.mp4` | 8,9 Mo | `33abc8502652…` | **référence approuvée, intacte** |
| V4 démo | `output_T1_sans_voix_v4_demo.mp4` | 9,1 Mo | `a5421eadc87a…` | conservée |
| **Master final (clôture)** | `output/output_T1_master_final.mp4` | **9 801 769 o** | `b202514af94fa204d8ddda769682f870d336154c36b06c3a9264ab5d6625a632` | **un seul nouveau master** |

Format : 720×1280, 30 i/s, 900 images, 30,000 s, **muet** (aucune piste audio — vérifié dans le conteneur).

---

## 5. Ingénierie réelle du montage

### 5.1 Chaîne exécutée, fichier par fonction

| Étape | Fichier / fonction | Paramètres réels |
|---|---|---|
| 1. Prises | `rushes/build_scenes.sh` | S1 = 327 (0,30 s + 6,0 s) · 606×1080 ; S2 = 48322 (720) + 3533 (1080) · 606×1080 ; S3 = 29059 (720) · **404×720** ; S4 = 2597 + 41222 (1080) · 606×1080. Recadrage 9:16 **dans les pixels du rush** |
| 2. Normalisation | `motion_v4.render` | `minterpolate` (30 i/s) + `eq` — **plus aucune mise à l'échelle ici** |
| 3. Fenêtre du plan | `ShotReader.frame_at` | `in_frame` + local, borné, gel de fin réel ; lecture séquentielle |
| 4. Caméra | `camera_move` | `base`, `k_ratio`, `pan_px`, `easing`, `dur_f` **lus dans le plan** ; recadrage sur les pixels natifs puis **une seule** mise à l'échelle |
| 5. Transitions | `do_transition` | identifiant et durée **lus dans `plan.cuts`** ; rendus : `punch_cut`, `whip_blur`, `push_rampe`, `diagonale` |
| 6. Vignettage | `gradient_overlay` | identique à V3.1 |
| 7. Graphismes | `Presentation.dessiner` | **configuration consommée** : `config/T1_presentation_v3_1.json` |
| 8. Assemblage | ffmpeg rawvideo | H.264 CRF 19, `+faststart`, `-an` |
| 9. Contrôle | `tools/verify_master.py` | 24 points ; conteneur ; silence ; images noires |

### 5.2 Les 4 soupçons de l'audit précédent : clos

| Soupçon | État |
|---|---|
| progression de scène entière au lieu des fenêtres de plan | **clos** : 12 fenêtres lues dans le plan, mesurées dans le MP4 |
| caméra recalculée par index de plan | **clos** : 5 paramètres du plan lus ; zooms mesurés ≈ déclarés |
| plages graphiques codées en dur | **clos** : fenêtres `overlays` + géométrie de la configuration |
| 3 transitions définies dans le moteur | **clos** : identifiants dans le plan, rendus nommés dans la bibliothèque |

---

## 6. Tableau des 12 plans

Source : `render_plan_v4_demo.json` (déclaré) · `reports/execution_manifest_v4.json` (exécuté) · `reports/final_master_checks.json` (mesuré dans le MP4). Version détaillée : `reports/tableau_final_json_code_mp4.md`.

| # | Scène | Sortie (s) | Source | Fenêtre source | Mouvement | Paramètres | Transition | Bloc | Verdict de contrôle |
|---|---|---|---|---|---|---|---|---|---|
| P01 | S1 | 0,00–2,00 | S1 | 9→61 (53) + gel 7 | MV01 `zoom_in_doux` | base 1,00 · k 1,00→1,05 · easeInOutQuad | TR01 cut | GB01 | **conforme** (0,962 / 0,967) |
| P02 | S1 | 2,00–3,50 | S1 | 65→103 (39) + gel 6 | MV03 `push_in_rapide` | base **1,25** · k 1,00→1,08 · dur_f 6 | TR02 punch_cut | GB01 | **conforme** (0,955 / 0,957) |
| P03 | S1 | 3,50–6,00 | S1 | 107→169 (63) + gel 12 | MV05 `pan_horizontal` | base **1,28** · pan −14→+14 | TR04 whip | GB02 | à vérifier / partiel (0,780 · 0,863) |
| P04 | S2 | 6,00–8,50 | S2 | 9→76 (68) + gel 7 | MV01 | base 1,00 · k 1,00→1,05 | TR01 | GB03 | **conforme** (0,982 / 0,957) |
| P05 | S2 | 8,50–11,00 | S2 | 80→147 (68) + gel 7 | MV05 | base **1,24** · pan −14→+14 | TR01 | GB03+GB04 | **conforme** / partiel (0,916 · 0,812) |
| P06 | S2 | 11,00–14,00 | S2 | 151→229 (79) + gel 11 | MV02 `zoom_out_doux` | base 1,10 · k 1,00→0,96 | TR06 push | GB04 | **conforme** (0,907 / 0,934) |
| P07 | S3 | 14,00–16,50 | S3 | 9→76 (68) + gel 7 | MV06 `pan_vertical` | base 1,25 · pan +10→−10 | TR01 | GB05 | **conforme** (0,904 / 0,944) |
| P08 | S3 | 16,50–18,50 | S3 | 80→132 (53) + gel 7 | MV03 | base **1,28** · k 1,00→1,08 · dur_f 6 | TR01 | GB05+GB06 | **conforme** (0,941 / 0,945) |
| P09 | S3 | 18,50–21,00 | S3 | 136→199 (64) + gel 11 | MV05 | base 1,00 · pan −14→+14 | TR03 diagonale | GB06 | **conforme** (0,985 / 0,988) |
| P10 | S4 | 21,00–23,50 | S4 | 9→78 (70) + gel 5 | MV01 | base **1,24** · k 1,00→1,05 | TR01 | GB07 | **conforme** (0,941 / 0,947) |
| P11 | S4 | 23,50–26,50 | S4 | 82→166 (85) + gel 5 | MV02 | base 1,05 · k 1,00→0,96 | TR01 | GB07 | **conforme** / partiel (0,929 · 0,840) |
| P12 | S4 | 26,50–30,00 | S4 | 170→244 (75) + gel 30 | MV11 `maintien` | base **1,24** · k 1,00→1,02 · linear | TR01 | GB08 | partiel / **conforme** (0,866 · 0,924) |

**Contrôle global : 24 points — 19 conformes, 4 partiels, 1 à vérifier, 0 image noire, master muet.**

### 6.1 Qualité d'image : ce qui a été fait, et ce que ça donne

Trois leviers, aucun micro-mouvement artificiel :

1. **Rushs plus définis.** Mixkit publie une variante 1080 pour R1 (327), R3 (3533), R5 (2597) et R6 (41222) : elle est désormais utilisée. Seules R2 (48322) et R4 (29059) n'existent qu'en 720 — c'est déclaré dans `rushes/manifest.json` (`variante_1080_disponible`, `definition_utilisee`).
2. **Recadrage mieux maîtrisé.** Les prises ne sont plus écrasées en 720×1280 à la construction : elles sont découpées en 9:16 à la définition native (606×1080, ou 404×720 pour S3). Le recadrage du plan se fait dans ces pixels et **une seule** mise à l'échelle 720×1280 a lieu, en fin de chaîne. Avant, on cumulait un agrandissement 1,78× puis un recadrage 1,4–1,7× puis un nouvel agrandissement.
3. **Plafond de recadrage à 1,28** (contre 1,70 avant) pour P02, P03, P05, P07, P08, P10, P12. Aucune scène, aucune durée, aucun cadrage d'intention n'est modifié.

Effet mesuré (voir le tableau) : **P08 passe de « à vérifier » (0,750 / 0,729) à « conforme » (0,941 / 0,945)** ; P05 remonte à 0,916 au premier point ; P10 et P12 remontent aussi.

Ce qui reste partiel, sans être un défaut :

- **P03 (0,780 / 0,863)** : bande haute peu texturée (mur, suspension) et base 1,28 ; le meilleur indice reste l'indice déclaré.
- **P05 second point (0,812) et P11 dernier point (0,840)** : images de fin de plan, proches d'une coupe, où la bande haute est majoritairement plate.
- **P12 premier point (0,866)** : plan de maintien sur un comptoir sombre.

Ces valeurs sont reportées telles quelles, sans les maquiller en « conformes ».

---

## 7. Les trois transitions : réconciliation, pas remplacement

### 7.1 Ce que la V3.1 faisait, ce que la spec nomme, ce que le master fait

| Instant | V3.1 (approuvée) | Identifiant V1.2 retenu | Rendu dans le master | Durée |
|---|---|---|---|---|
| **6,0 s** | `whip_pan` : translation horizontale + flou directionnel | **TR04 `wipe_directionnel`** | `whip_blur` — translation + flou jusqu'à 34 px | 6 images |
| **14,0 s** | `directional_push` : échelles croisées 1,035 / 1,08 + translation | **TR06 `speed_ramp_entrant`** | `push_rampe` — poussée croisée, courbe symétrique | 6 images |
| **21,0 s** | révélation diagonale + ruban orange, étiquetée à tort « mask_reveal » | **TR03 `wipe_geometrique`** | `diagonale` — front `x − 0,42·y` + ruban orange de 13 px | 6 images |

Décisions explicites :
- **TR05 `fondu_court_crossfade` n'est plus utilisé** : c'était le remplacement qui adoucissait la dynamique approuvée à 14 s. Il reste dans la bibliothèque, simplement pas employé ici.
- **`mask_reveal` (TR08) n'est pas utilisé** : la spec V1.2 le déclare `custom_required` et hors pilote. L'étiquette de la V3.1 était fausse ; le rendu réel était la révélation diagonale, désormais nommée TR03.
- **Fenêtre** : `[coupe−1, coupe+5)` = 6 images (contrainte de durée V1.2). V3.1 utilisait 12 images `[coupe−4, coupe+8)`. Pour conserver le caractère « whip », la vitesse par image est doublée (flou porté à 34 px) et la courbe du push est symétrique — une attaque `easeOutQuint` sur 6 images aurait fait disparaître la poussée.

### 7.2 Comparaison temporelle (produite avant verrouillage)

`preuves/audit_v4/planche_comparaison_transitions.png` — six images par version, pour chacune des trois transitions, avec timecodes réels. Données : `reports/comparaison_transitions.json`.

| Transition | Fenêtre V3.1 (images) | Fenêtre master (images) | Ce que ça donne |
|---|---|---|---|
| 6,0 s | 176→187 (12) | **179→184 (6)** | départ flou + glissement, coupe nette sur l'image entrante |
| 14,0 s | 416→427 (12) | **419→424 (6)** | joint vertical qui balaie l'image, œuf → visage |
| 21,0 s | 626→637 (12) | **629→634 (6)** | front diagonal + ruban orange, personne → terrasse |

Autres coupes : TR02 `punch_cut` à 3,5 s (6 images) et `cut_sec` aux 7 autres.

---

## 8. Géométrie graphique pilotée par la configuration

### 8.1 Ce que le moteur lit désormais

`config/T1_presentation_v3_1.json` décrit, pour chacun des 8 blocs, une liste d'éléments typés (`carte`, `accent`, `filet`, `texte`, `texte_empile`, `texte_segments`) portant : position, taille, alignement, typographie, couleur, proportions, forme, espacements et règles d'entrée/sortie. `engine/presentation.py` ne connaît que ces **types** ; il ne contient **aucune coordonnée, taille, couleur ni police de bloc**.

| Bloc | Composition | Éléments | Entrée / sortie |
|---|---|---|---|
| GB01 | enseigne mot à mot | 3 | glissement horizontal −38 px / fondu, mots décalés de 5 images |
| GB02 | bandeau produit (titre empilé V3.1) | 3 | mot à mot 7 images + montée 26 px, filet révélé, sur-titre |
| GB03 | lockup produit + prix | 5 | échelle 0,94 → 1,015, filet révélé, fondu de sortie |
| GB04 | accroche en segments | 3 | glissement vertical 14 px, segments décalés de 4 images |
| GB05 | rappel d'enseigne | 3 | glissement horizontal −26 px |
| GB06 | prix plein écran | 5 | échelle 0,94 → 1,015 |
| GB07 | adresse + épingle | 4 | glissement vertical 16 px, épingle vectorielle |
| GB08 | CTA WhatsApp | 5 | échelle 0,985 → 1,0 + glissement 13 px |

Contrôle : les 8 blocs sont rendus **aux fenêtres déclarées** par le plan (`overlays[].start_f/end_f`), et la planche `preuves/audit_v4/planche_graphismes_master_final.png` montre un point par bloc.

### 8.2 Matrice de décision

| Critère | Prévu | Exécuté par le code | Visible dans le MP4 | Décision |
|---|---|---|---|---|
| Fenêtres sources | 12 fenêtres de plan | `ShotReader` | oui (indice mesuré = déclaré) | **validé** |
| Mouvement | base, k_ratio, pan, easing, dur_f | `camera_move` | oui (zoom mesuré ≈ déclaré) | **validé** |
| Transitions | TR01…TR06 du plan | `do_transition` | oui, 11 coupes | **validé** |
| Géométrie des blocs | configuration de présentation | `Presentation.dessiner` | oui, 8/8 | **validé (nouveau)** |
| Typographie des blocs | polices, graisses, tailles, min | `Presentation.police_ajustee` | oui | **validé (nouveau)** |
| Couleurs | palette de la configuration | `Presentation.couleur` | oui | **validé (nouveau)** |
| Règles d'entrée/sortie | par élément | `Presentation.enveloppe` | oui | **validé (nouveau)** |
| DA V3.1 | identique | — | oui (titre empilé, cartes, rail orange, filet, épingle) | **préservée** |
| Rythme / durées | 1,5–3,5 s par plan | respecté | oui | **validé** |
| Qualité d'image | netteté | base plafonnée à 1,28 | oui, P08 corrigé | **corrigé** |
| Audio | hors périmètre | master muet | oui | **inchangé** |

**Statut exact du moteur** : il est piloté par fichiers pour *quand* (fenêtres, plans, coupes), *comment bouge l'image* (zoom, pan, easing, durée) et *à quoi ressemblent les textes* (configuration de présentation). Il reste deux constantes de dessinateur assumées : la position du bandeau de vignettage et le tracé du ruban orange des transitions, qui font partie de la bibliothèque de rendu V1.2 et non du gabarit.

---

## 9. Écarts constatés et leur état

| # | Écart | Gravité | État |
|---|---|---|---|
| E1 | progression de scène entière (V3.1) | haute | **clos** |
| E2 | caméra recalculée par index (V3.1) | haute | **clos** |
| E3 | plages graphiques codées en dur (V3.1) | haute | **clos** |
| E4 | 3 transitions nommées dans le moteur, 12 images (V3.1) | haute | **clos** (identifiants plan + 6 images) |
| E5 | étiquette `mask_reveal` sans masque (V3.1) | moyenne | **clos** (TR03 nommé pour ce qu'il est) |
| E6 | `SOURCE_WINDOWS` et accélération `sin()` non déclarés | moyenne | **clos** |
| E7 | géométrie nominale du plan incompatible avec la DA V3.1 | moyenne | **clos autrement** : la géométrie est désormais portée par la configuration de présentation (DA V3.1), pas par les boîtes nominales du plan |
| E8 | recadrages jusqu'à 1,70× ⇒ perte de netteté | moyenne | **traité** (rushs 1080 + recadrage natif + plafond 1,28) |
| E9 | pastille d'accroche de scène 1 non déclarée | faible | **assumé** : à déclarer dans le plan si elle doit revenir |
| E10 | `dur_min_f` de P12 sans effet | faible | documenté |
| E11 | `ffprobe` absent de l'image de base | faible | contourné (OpenCV) ; documenté |
| E12 | divergence de mention vocale en scène 2 | moyenne | **clos** (audit précédent) |

---

## 10. Corrections apportées (cette mission)

1. **Parcours** — titre de la section voix remplacé ; zone défilable : dégradé 52 px, marge basse 34 px, repère ↓ conditionnel, barre de défilement stylée ; 12 captures régénérées.
2. **Configuration de présentation** — `config/T1_presentation_v3_1.json` (8 blocs, 31 éléments) + `engine/presentation.py` (rendu générique).
3. **Moteur** — `engine/motion_v4.py` : normalisation sans mise à l'échelle, lecture des fenêtres/mouvements/transitions/blocs, transitions réconciliées.
4. **Prises** — `rushes/build_scenes.sh` reconstruit en définition native ; `rushes/manifest.json` documente la variante 1080 utilisée et les empreintes ; `engine/verify_raw_rushes.py` vérifie la variante réellement utilisée.
5. **Recadrages** — plafond de base à 1,28 sur 7 plans (valeur précédente conservée dans le plan sous `base_precedent`).
6. **Outillage** — `tools/tableau_final.py`, `tools/comparaison_transitions.py`, `tools/verify_master.py` (bande relative, indépendante de la définition).

Commandes de reproduction :

```bash
pip install imageio-ffmpeg
ln -sf "$(python3 -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())')" ~/.local/bin/ffmpeg
bash rushes/build_scenes.sh
PYTHONPATH=. python3 engine/motion_v4.py --plan render_plan_v4_demo.json \
    --output output/output_T1_master_final.mp4 --manifest reports/execution_manifest_v4.json
python3 tools/verify_master.py && python3 tools/tableau_final.py
PYTHONPATH=. python3 tools/frames_audit_v4.py && python3 tools/comparaison_transitions.py
```

---

## 11. Tests finaux

| Test | Méthode | Résultat |
|---|---|---|
| Conteneur | OpenCV + ffmpeg | 900 images · 30,000 s · 720×1280 · 30 i/s |
| Silence | inspection des flux | **aucune piste audio** |
| Images noires | luminance moyenne < 4 | **0** |
| Fenêtres sources + zoom | 24 points, bande haute, recherche (indice, zoom) | **19 conformes · 4 partiels · 1 à vérifier** |
| Transitions | planches aux 6 images de chaque transition | TR02, TR04, TR06, TR03 visibles et dynamiques |
| Graphismes | planche d'un point par bloc | **8/8** dans leur fenêtre |
| Configuration consommée | `presentation_blocs` du manifeste = 8 blocs de la configuration | **oui** |
| Parcours | 12 combinaisons Playwright | **OK** (voir §3.1) |
| Tests unitaires | `pytest -q` | **41 passed** |
| Reproductibilité | second rendu du même plan | empreinte identique (`b202514a…`) |

---

## 12. Liens directs (téléchargement testé)

Release : **`t1-cloture`** — https://github.com/j9028379-hue/vitrine-video-t1-pilot/releases/tag/t1-cloture

Préfixe : `https://github.com/j9028379-hue/vitrine-video-t1-pilot/releases/download/t1-cloture/`

| Livrable | Fichier | Code HTTP | Octets |
|---|---|---|---|
| **Master final de clôture** | `output_T1_master_final.mp4` | voir tableau de vérification ci-dessous | |
| Moteur réconcilié | `engine_motion_v4_et_presentation.zip` | | |
| Plan de présentation réellement consommé | `render_plan_v4_demo.json` · `T1_presentation_v3_1.json` | | |
| Les 4 fiches corrigées | `capture-guide_consignes.zip` (JSON source unique + guide) | | |
| 12 captures + planche | `ui-screens_12_etats.zip` | | |
| Tableau final JSON / code / MP4 | `tableau_final_json_code_mp4.md` (+ `.json`) | | |
| Contrôle des 12 plans | `final_master_checks.json` · `execution_manifest_v4.json` | | |
| Comparaison des transitions | `planche_comparaison_transitions.png` · `comparaison_transitions.json` | | |
| Ce rapport | `T1_AUDIT_FINAL_PARCOURS_ET_MONTAGE.md` | | |

### 12.1 Vérification faite, pas supposée

Chaque lien est appelé **sans authentification** : code **200** et `content-length` non nul. Le master est ensuite **entièrement retéléchargé**, haché (SHA-256 identique à celui publié) et relu par OpenCV (900 images, 30 i/s, 720×1280). Les valeurs exactes sont reportées dans le tableau ci-dessus après publication.

### 12.2 Pages

- Dépôt : https://github.com/j9028379-hue/vitrine-video-t1-pilot
- Démonstration : https://j9028379-hue.github.io/vitrine-video-t1-pilot/
- Maquette du parcours : https://j9028379-hue.github.io/vitrine-video-t1-pilot/simulation/

### 12.3 Ce qui reste ouvert, dit franchement

- La pastille d'accroche de la scène 1 de la V3.1 n'est pas déclarée par le plan : elle reste absente. Si elle doit revenir, elle doit être **déclarée**, pas codée.
- R2 (48322) et R4 (29059) n'existent qu'en 720 : leur netteté est plafonnée par la source, pas par le moteur.
- Trois points de contrôle restent « partiels » sur la bande haute (P03, P05 fin, P11 fin) : ce sont des zones peu texturées, l'indice d'image reste le bon.
- Le portage Android n'est pas fait ici : la configuration de présentation et le JSON des fiches sont prêts à être lus par un composant natif.
