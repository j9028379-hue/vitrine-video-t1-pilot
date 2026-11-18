# T1 — Audit final : parcours de capture et montage

**Projet** : VITRINE VIDÉO — T1 « Plat du jour », démonstration pour restaurants et maquis (Bénin)
**Date de l'audit** : 17 novembre 2026 · **Dépôt** : `j9028379-hue/vitrine-video-t1-pilot`, branche `main`
**Périmètre** : (1) les 4 écrans de consignes du parcours de capture ; (2) l'ingénierie réelle du montage 30 s.
**Hors périmètre, non touché** : tout l'audio (aucune musique, aucun effet, aucune modification de fichier son).

---

## 1. Espace de travail et nettoyage

### 1.1 État de départ et état final

| Mesure | Avant nettoyage | Après nettoyage | Aujourd'hui (fin d'audit) |
|---|---|---|---|
| Taille du dépôt local | 199 Mo | 75 Mo | 126 Mo |
| Fichiers (hors `.git`) | 269 | 152 | 158 |
| Clone | ancien clone divergent (`HEAD f0e8c72`) | clone complet, `HEAD 42989e4` | idem + travaux de l'audit |

Le workspace avait été tronqué par la limite de sauvegarde (281 fichiers non enregistrés). L'ancien clone **n'était plus la source de vérité** : `git log` comparé à GitHub a montré que les commits `42989e4` et `2d40955` manquaient localement. Un clone complet a été refait depuis GitHub : c'est lui qui sert désormais de base.

### 1.2 Ce qui a été supprimé (uniquement du régénérable identifié un par un)

`t1-ci-artifacts/`, `t1-ci-artifacts-final/`, `t1-v2-candidates/`, `audit_frames/`, `repo_restore/`, `main.bundle`, l'archive ZIP de livraison, les caches Python, les doublons de planches.
Aucune suppression globale, aucun `rm -rf` sur un dossier contenant un livrable.

### 1.3 Ce qui a été conservé, et où

- **Sources de vérité** : `specs/T1_ENGINEERING_SPEC_V1_2.json` (autorité technique, intacte), `specs/restaurants_maquis_T1.spec_v6_2.json` (autorité des textes, intacte), `capture-guide/consignes_T1.json` (source unique des 4 fiches), `rushes/manifest.json` + `rushes/build_scenes.sh` (prises et licences).
- **Référence visuelle approuvée** : `V3.1` intacte — `output/…` et copie de sécurité `/tmp/preserve/masters/output_T1_sans_voix_v3_1.mp4`.
- **Livrables vidéo** : V2, V3, V3.1, V4 démo, plus le **master final** produit par cet audit (§10).
- **Preuves** : `preuves/audit_versions/` (planches V2/V3/V3.1), `preuves/audit_v4/` (nouvelles planches), `ui-screens/` (23 PNG), `reports/`.
- **Rushes** : `rushes/source/demo_v4/` — 6 clips Mixkit sous licence, vérifiés par SHA-256 à chaque exécution (`engine/verify_raw_rushes.py`).

Le dossier `/tmp/preserve` (87 Mo : 4 masters, planches d'audit, plan de référence V3.1, spec V6.2) est **hors workspace** : il a servi de filet de sécurité pendant l'audit. Les masters y seront re-téléchargeables depuis la Release (§12) ; ce dossier n'est pas un livrable.

### 1.4 Environnement d'exécution (à savoir pour reproduire)

`ffmpeg` **n'est pas** installé dans l'image de base et `ffprobe` non plus. Installé ici via `pip install imageio-ffmpeg` + lien `~/.local/bin/ffmpeg` (ffmpeg 9.0.2). Playwright et son navigateur ne persistent pas dans les captures d'espace de travail : à réinstaller avant toute capture d'écran. `ruff`/`pytest` : `pytest` disponible.

---

## 2. Vérification des 4 consignes

### 2.1 Une seule source

`capture-guide/consignes_T1.json` est la **source unique**. `tools/build_consignes.py` génère à partir d'elle :
- `simulation/consignes.js` (maquette HTML 540×960),
- `capture-guide/consignes_4_scenes.md` (guide de tournage lisible).

Aucun texte de consigne n'est saisi ailleurs : ni dans `simulation/index.html`, ni dans les outils de capture, ni dans le futur composant Android (qui devra lire le même JSON).

### 2.2 La mention vocale — divergence corrigée

Une variante existait en scène 2. Elle a été remplacée par la formulation unique V6.2, **identique dans les 4 scènes** :

> « Tu peux parler pendant que tu filmes, en fon, yoruba, français ou anglais, pour présenter ton produit. »

Caractères : **102**. Présente une seule fois dans le JSON (`mention_voix_commune`), donc identique par construction dans la maquette, le guide et les 12 captures.

### 2.3 Les 4 consignes, mot pour mot

| Scène | Titre | Durée | Consigne (caractères) | À filmer | À éviter | Exemple facultatif |
|---|---|---|---|---|---|---|
| 1/4 | LE PLAT | **6 s** | 133 | 3 | 3 | 1 |
| 2/4 | LE DESSUS ET LES DÉTAILS | **8 s** | 139 | 2 | 2 | 1 |
| 3/4 | LA PERSONNE QUI SERT | **7 s** | 123 | 3 | 2 | 1 |
| 4/4 | LE LIEU ET LE CONTACT | **9 s** | 112 | 3 | 2 | 1 |

Contrôles passés :
- scène 1 = **6 s** partout (jamais 5 s) : vérifié dans le JSON, dans `consignes.js`, dans le guide, dans les 12 captures et dans la maquette ;
- total 30 s = 6 + 8 + 7 + 9, cohérent avec le montage (900 images à 30 i/s) ;
- les 4 consignes, les listes « à filmer / à éviter » et les exemples sont ceux de V6.2, sans reformulation ;
- les exemples sont annoncés comme **facultatifs** dans l'interface (mention explicite + style secondaire) ;
- le bouton est `COMMENCER À FILMER`, et `VOIR MON MONTAGE` après la scène 4.

---

## 3. Lisibilité et 12 états

### 3.1 Ordre imposé de la fiche (vérifié à l'écran)

1. `SCÈNE n/4` + progression · 2. durée immédiatement visible · 3. titre · 4. consigne · 5. `À FILMER` · 6. `À ÉVITER` · 7. mention vocale · 8. exemple facultatif · 9. bouton principal en bas.

Une seule colonne, jamais deux colonnes étroites. Le contenu est défilable et le bouton reste accessible en bas (pied fixe), avec un dégradé de 30 px qui évite qu'une ligne soit coupée net sous le CTA.

### 3.2 Mesures typographiques (Playwright, 12 combinaisons)

| Élément | Cible | Mesuré | Verdict |
|---|---|---|---|
| Consigne | 17–18 px | **17,5 px** | conforme |
| `À FILMER` / `À ÉVITER` (items) | 14–16 px | **15 px** | conforme |
| Titres de section | 12–14 px | **12,5 px** | conforme |
| Mention vocale | 14–15 px | **14,5 px** | conforme |
| Exemple facultatif | 14–15 px | **14,5 px** | conforme |
| Bouton principal | 16–18 px | **17 px** | conforme |

Tailles testées : **360×800, 390×844, 430×932** × 4 scènes. Résultat global : **OK sur les 12 combinaisons** — `overflow_horizontal: false`, `cta_visible: true`, fiche défilable, aucun texte coupé, masqué ou superposé. Mesures brutes : `reports/verification_lisibilite.json`.

### 3.3 Les 3 états

| État | Contenu attendu | Vérifié |
|---|---|---|
| **A** | fiche complète + bouton | oui, 4 scènes |
| **B** | **la fiche disparaît complètement** : aperçu vidéo + chrono + barre uniquement | oui — la planche montre B sans aucune carte de texte |
| **C** | relecture + `REFAIRE` / `SCÈNE SUIVANTE`, et `VOIR MON MONTAGE` après la scène 4 | oui, 4 scènes |

Défauts trouvés par la capture et corrigés avant livraison :
1. la ligne `SCÈNE 1/4` était masquée par le bouton `DÉMO` → `max-height` du panneau ramené de 90 % à 86 % ;
2. `DÉMO` masquait la lecture → bouton déplacé à gauche, réduit à 10 px, et masqué en mode capture (`body.capture`, `?capture=1`) ;
3. le texte était coupé net sous le CTA → dégradé de 30 px au-dessus du pied ;
4. l'état C basculait en `VOIR MON MONTAGE` parce que le chrono continuait de tourner → ajout de `window.__demo.freezeAt(pct)` (arrêt réel de l'enregistrement puis positionnement de la barre).

### 3.4 Livrables du parcours

- `ui-screens/` — **23 PNG** : 12 états (`ecran_08_scene{1..4}_etat{A,B,C}_*.png`), 1 vue du bas de fiche, 2 écrans de montage, publicité, fin, navigation, 2 preuves 360 px, 2 preuves 430 px.
- `ui-screens/planche_12_etats.png` — planche regroupant **les 12 états** (4 × A/B/C), 972×2970 px.
- `simulation/index.html` — navigation clavier/URL pour atteindre chaque scène et chaque état.

Rappel de statut : la maquette est une **simulation navigateur** de l'interface de capture. Ce n'est pas une caméra Android et elle n'enregistre pas de vidéo.

---

## 4. Versions vidéo conservées

Aucune ancienne vidéo n'a été écrasée. Les 4 masters + le nouveau sont présents, avec empreintes vérifiées.

| Version | Fichier | Taille | SHA-256 (début) | Statut |
|---|---|---|---|---|
| V2 | `output_T1_sans_voix_v2.mp4` | 22 Mo | `21e8f5d80fcd…` | conservée, non utilisée |
| V3 | `output_T1_sans_voix_v3.mp4` | 8,5 Mo | `9f03b9cbdebb…` | conservée, non utilisée |
| **V3.1** | `output_T1_sans_voix_v3_1.mp4` | 8,9 Mo | `33abc8502652…` | **référence visuelle approuvée — intacte** |
| V4 démo | `output_T1_sans_voix_v4_demo.mp4` | 9,1 Mo | `a5421eadc87a…` | conservée (sortie du moteur V3.1 sur le plan V4) |
| **Master final** | `output/output_T1_master_final.mp4` | 9,1 Mo | `97c3477d8043…` | **nouveau, une seule version** |

Format commun : 720×1280, 30 i/s, 900 images, 30,000 s, **muet** (aucune piste audio — vérifié sur le conteneur).

Deux pièges évités : (1) les images d'audit sont extraites **des MP4**, jamais du JSON ; (2) `simulation/media/S*.mp4` ne sont pas les prises : ce sont des copies re-encodées pour le web (SHA différents) — l'audit utilise `rushes/source/demo_v4/`.

---

## 5. Ingénierie réelle du montage

### 5.1 La chaîne, telle qu'elle est codée

| Étape | Fichier / fonction | Paramètres réels |
|---|---|---|
| 1. Prises | `rushes/build_scenes.sh` → `rushes/source/demo_v4/S{1..4}.mp4` | S1 = 327 (0,30 s + 6,0 s) ; S2 = 48322 (1,0 s + 4,0 s) + 3533 ; S3 = 29059 (3,0 s + 7,0 s) ; S4 = 2597 (0,4 s + 4,6 s) + 41222 ; `scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,fps=30` |
| 2. Normalisation | `engine/motion_v4.py::render` (identique à V3.1) | `minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir` puis `eq=saturation=1.12:contrast=1.06:brightness=0.006`, H.264 CRF 18 |
| 3. Fenêtre source du plan | `ShotReader.frame_at(local)` | `in_frame` + `local`, borné par `source_frames`, dernière image **gelée** (`freeze_tail_f`) ; lecture strictement séquentielle |
| 4. Recadrage caméra | `camera_move(frame, local, duration, shot)` | lus **dans le plan** : `base`, `k_ratio`, `pan_px`, `easing`, `dur_f` |
| 5. Transitions | `do_transition(old, new, kind, p)` + table `TRANSITIONS` | `plan.cuts[i].transition` → TR01…TR05, durées V1.2 (0 ou 6 images) |
| 6. Vignettage | `gradient_overlay()` | haut `clip(1-y/500)^1.7×0,56`, bas `clip((y-700)/580)^1.25×0,57` |
| 7. Graphismes | `render_graphics()` + `plan.overlays` | 8 blocs GB01…GB08, fenêtres `start_f`/`end_f` du plan ; DA V3.1 pour les styles |
| 8. Assemblage | `ffmpeg` tube rawvideo | `libx264 -preset medium -crf 19 -pix_fmt yuv420p -movflags +faststart`, `-an` |
| 9. Contrôle | `tools/verify_master.py`, `tools/frames_audit_v4.py` | 24 points de mesure, planches visuelles, conteneur, silence, images noires |

### 5.2 Les 4 soupçons : vérifiés dans le code (V3.1) et traités

| Soupçon | Vérifié ? | Preuve dans `engine/motion_v3_1.py` | Traitement |
|---|---|---|---|
| 1. `get_scene_frame()` utilise la progression de la **scène entière** au lieu des fenêtres du plan | **oui** | boucle de rendu : `bg = get_scene_frame(scene_i, fno - cumulative, …)` puis `progress = local / (frames-1)` ; `SOURCE_WINDOWS = {"S2": (0.0, 0.76)}` est la seule fenêtre codée en dur, et `source_progress()` ajoute `progress += 0.06*sin(2π·progress)` pour S2 uniquement | nouveau moteur : `in_frame`/`source_frames` lus plan par plan ; aucun correctif sinusoïdal ; plus de constante `SOURCE_WINDOWS` |
| 2. `camera_move()` recalcule suivant le **numéro de plan** | **oui** | `start = 1.015 + 0.006*(shot_index % 3)`, `end = 1.085 if shot_index % 2 == 0 else 1.035`, `dx = ((shot_index % 4) - 1.5)*0.018`, `dy = (((shot_index+1) % 3) - 1)*0.013` — aucun champ de `zoom_curve` n'est lu | nouveau moteur : `base`, `k_ratio`, `pan_px`, `easing`, `dur_f` du plan |
| 3. `render_graphics()` a des **plages codées en dur** | **oui** | `if 0 <= fno < 177`, `if 172 <= fno < 417`, `if 410 <= fno < 627`, `if fno >= 620`, puis `local = fno - 180/420/630` et des seuils en dur (`t >= 31`, `t >= 116`, `local >= 42`, `local >= 12`, `local >= 110`, `local >= 145`) | nouveau moteur : `plan.overlays[].start_f/end_f` |
| 4. Les **3 grandes transitions** sont définies dans le moteur | **oui** | `transition_kinds = {cuts[0]: "whip_pan", cuts[1]: "directional_push", cuts[2]: "mask_reveal"}` puis fenêtre `cut - 4 <= fno < cut + 8` et `p = k/11.0` (12 images) | nouveau moteur : transitions lues dans `plan.cuts`, durées V1.2 (6 images), rendu nommé par la bibliothèque |

**Preuve en plus, importante** : dans V3.1, l'étiquette `mask_reveal` de 21 s **ne correspond à aucun masque**. La fonction `transition()` ne connaît que trois branches : `whip_pan`, `directional_push`, et sinon la révélation diagonale à ruban orange. `mask_reveal` tombait donc dans la branche diagonale — la même que celle utilisée à 6 s. L'étiquette était fausse (voir §7 et `preuves/audit_v4/planche_transitions_v3_1_vs_final.png`).

---

## 6. Tableau des 12 plans

Source de chaque ligne : `render_plan_v4_demo.json` (déclaré) + `reports/execution_manifest_v4.json` (exécuté) + `reports/final_master_checks.json` (mesuré dans les pixels du MP4).

| # | Scène | Position finale (s) | Source | Fenêtre source | Mouvement | Paramètres | Transition | Graphisme | Intention | Résultat |
|---|---|---|---|---|---|---|---|---|---|---|
| P01 | S1 | 0,00–2,00 | S1 | images 9→61 (53) + gel 7 | MV01 `zoom_in_doux` | base 1,00 · k 1,00→1,05 · easeInOutQuad | TR01 `cut_sec` → P02 | GB01 nom (0,5–3,0) | poser le lieu et l'enseigne | **conforme** (corr. 0,962 / 0,966) |
| P02 | S1 | 2,00–3,50 | S1 | 65→103 (39) + gel 6 | MV03 `push_in_rapide` | base **1,35** · k 1,00→1,08 · dur_f 6 · easeOutQuint | TR02 `punch_cut` | GB01 | entrer dans le plat, coup sec | **conforme** (0,955 / 0,933) |
| P03 | S1 | 3,50–6,00 | S1 | 107→169 (63) + gel 12 | MV05 `pan_horizontal` | base **1,70** · pan −14→+14 px · easeInOutQuad | TR03 `wipe_geometrique` | GB02 produit (4,0–5,5) | balayer la table, titre produit | **partiel** (0,868 puis 0,930 ; base 1,70 ⇒ recadrage à 424 px) |
| P04 | S2 | 6,00–8,50 | S2 | 9→76 (68) + gel 7 | MV01 | base 1,00 · k 1,00→1,05 | TR01 `cut_sec` | GB03 produit+prix (6,5–9,5) | plat vu d'au-dessus, prix | **conforme** (0,983 / 0,946) |
| P05 | S2 | 8,50–11,00 | S2 | 80→147 (68) + gel 7 | MV05 | base **1,40** · pan −14→+14 | TR01 | GB03 + GB04 accroche (10,0–13,5) | détail appétissant | **partiel** (0,866 / 0,840) |
| P06 | S2 | 11,00–14,00 | S2 | 151→229 (79) + gel 11 | MV02 `zoom_out_doux` | base 1,10 · k 1,00→0,96 | TR05 `fondu_court_crossfade` | GB04 | respirer avant la personne | **conforme** (0,908 / 0,936) |
| P07 | S3 | 14,00–16,50 | S3 | 9→76 (68) + gel 7 | MV06 `pan_vertical` | base 1,25 · pan +10→−10 px | TR01 | GB05 rappel enseigne (15,0–17,5) | humaniser : visage, sourire | **conforme** (0,909 / 0,941) |
| P08 | S3 | 16,50–18,50 | S3 | 80→132 (53) + gel 7 | MV03 | base **1,55** · k 1,00→1,08 · dur_f 6 | TR01 | GB05 + GB06 prix (18,0–20,5) | personne + prix | **à vérifier** (0,750 / 0,729) — corrélation abaissée par l'agrandissement 1,67× |
| P09 | S3 | 18,50–21,00 | S3 | 136→199 (64) + gel 11 | MV05 | base 1,00 · pan −14→+14 | TR04 `wipe_directionnel` | GB06 | sortie de la personne vers le lieu | **conforme** (0,985 / 0,988) |
| P10 | S4 | 21,00–23,50 | S4 | 9→78 (70) + gel 5 | MV01 | base **1,40** · k 1,00→1,05 | TR01 | GB07 adresse (21,5–25,5) | on doit reconnaître l'endroit | **conforme** (0,942 / 0,905) |
| P11 | S4 | 23,50–26,50 | S4 | 82→166 (85) + gel 5 | MV02 | base 1,05 · k 1,00→0,96 | TR01 | GB07 | plan large, rue autour | **conforme** (0,930) / **partiel** (0,825) |
| P12 | S4 | 26,50–30,00 | S4 | 170→244 (75) + gel 30 | MV11 `maintien` | base **1,35** · k 1,00→1,02 · linear · dur_min 75 | — (fin) | GB08 CTA WhatsApp (26,5–30,0) | convertir : commander | **partiel** (0,858 / 0,896) |

Lecture du tableau :
- **coupes** : 2,0 s · 3,5 s · 6,0 s · 8,5 s · 11,0 s · 14,0 s · 16,5 s · 18,5 s · 21,0 s · 23,5 s · 26,5 s — les 12 plans tombent exactement sur les `cuts` du plan ;
- **aucun plan ne dépasse sa fenêtre** : 12/12 fenêtres conformes au déclaré (gel inclus) ;
- **réserves honnêtes** : 16 points de mesure « conformes », 6 « partiels », 2 « à vérifier ». Les « partiels » ne sont pas des erreurs d'ingénierie : ce sont des plans à fort recadrage (base 1,35–1,70), où le master ré-agrandit une zone de 424–530 px vers 720 px. La mesure de corrélation baisse parce que l'image est plus douce, pas parce que la fenêtre est fausse — la meilleure correspondance reste à l'indice déclaré (±1 image).

---

## 7. Les trois grandes transitions

| Instant | Spec V1.2 | V3.1 (référence) : ce qui est réellement codé | Master final : ce qui est réellement rendu |
|---|---|---|---|
| **6,0 s** | `TR03 wipe_geometrique` (6 images, *beta*) | `whip_pan` : translation + flou gaussien montant à 28 px, sur **12 images** (`cut-4` → `cut+8`) | `wipe_diagonale` : front `x − 0,42·y` + ruban orange de 13 px, **6 images** |
| **14,0 s** | `TR05 fondu_court_crossfade` (6 images, *beta*) | `directional_push` : échelles 1,035 / 1,08 + translation, sur **12 images** | `fondu` : crossfade court, **6 images** |
| **21,0 s** | `TR04 wipe_directionnel` (6 images, *beta*) | étiquette `mask_reveal` — mais **aucune branche masque** : rendu identique à la révélation diagonale de 6 s, sur 12 images | `wipe_directionnel` : deux plans poussés latéralement, joint flouté, **6 images** |

Constat majeur : le brief parle de « whip-pan 6 s / directional push 14 s / mask reveal 21 s ». Ce sont bien les **noms codés dans V3.1**, pas les intentions de la spec. `TR08 mask_reveal` est explicitement `custom_required` et **hors pilote** dans V1.2 : il n'aurait jamais dû porter ce nom dans le montage. Le master final applique les identifiants de la spec (`TR03`, `TR05`, `TR04`) aux mêmes instants, avec la durée de 6 images.

Autres coupes : TR02 `punch_cut` à 3,5 s (6 images) et `cut_sec` (TR01, 0 image) aux 7 autres coupes. Les 11 changements de plan sont tous présents et visibles.

Preuves : `preuves/audit_v4/planche_transitions_master_final.png` (milieu de chaque transition exécutée) et `preuves/audit_v4/planche_transitions_v3_1_vs_final.png` (V3.1 vs final aux mêmes timecodes).

---

## 8. Comparaison JSON / code / MP4 — et matrice de décision

### 8.1 Ce que le plan déclare, ce que le code exécute, ce que le MP4 montre

| Élément du plan | Déclaré | Exécuté par le code | Visible dans le MP4 |
|---|---|---|---|
| 12 plans (`shots`) | `out_start_f`/`out_end_f` | oui, découpage exact | oui, 12 plans distincts |
| Fenêtres sources (`in_frame`, `source_frames`, `freeze_tail_f`) | 12 fenêtres | oui (`ShotReader`) | oui — indice retrouvé = indice déclaré (±1) |
| Mouvement (`zoom_curve.base`, `k_ratio`, `pan_px`, `easing`, `dur_f`) | 14 presets MD-T1-01…14 | oui pour ces 5 champs | oui — zoom mesuré ≈ zoom déclaré (±0,02 à ±0,10) |
| Transitions (`cuts[i].transition`) | TR01, TR02, TR03, TR05, TR04 | oui, table V1.2 | oui, aux 11 coupes |
| Blocs graphiques (`overlays[].start_f/end_f`, `field`) | GB01…GB08 | oui | oui, 8/8 aux fenêtres déclarées |
| **Géométrie nominale des blocs** (`graphic_blocks[].nominal`, base 1080) | boîtes x/y/w/h, `text_px_720`, `radius_px`, `shadow_px` | **non lue** | positions = celles de la DA V3.1 |
| `zoom_curve.parameters.dur_min_f` (P12) | 75 images | non utilisé (maintien) | sans effet visible attendu |

Le point en gras est un **écart assumé et documenté**, pas une réussite : le plan V4 contient une géométrie nominale par bloc (par exemple GB02 à `y 826–974` en base 1080) qui est **incompatible avec la DA V3.1 réellement approuvée** (le titre produit de V3.1 est en haut de l'image, `y 260–443`). Deux autorités se contredisent ; la consigne « ne pas changer la DA V3.1 » a été suivie : les positions typographiques restent celles de la DA, le plan pilote la présence et la fenêtre des blocs.

**Formulation exacte du statut du moteur** : il est piloté par le plan pour *quand* (fenêtres, plans, coupes, transitions) et *comment bouge l'image* (zoom, pan, easing, durée) ; il ne l'est pas encore pour *où se placent les textes* (constantes de dessinateur). C'est écrit ici pour que personne ne le décrive comme entièrement data-driven.

### 8.2 Matrice de décision

| Critère | Prévu | Exécuté par le code | Visible dans le MP4 | Décision |
|---|---|---|---|---|
| Ouverture (0–2 s) | plan large, enseigne, plat | P01/MV01, GB01 | oui | **garder** |
| Présentation du plat | gros plans appétissants | P02–P06 | oui | **garder** |
| Présentation de la personne | visage, sourire | P07–P09 | oui | **garder** |
| Lieu et contact | rue + enseigne + CTA | P10–P12, GB07, GB08 | oui | **garder** |
| Progression dramatique | plat → détail → personne → lieu | 4 scènes, 12 plans | oui | **garder** |
| Rythme | coupes toutes les 1,5–3,5 s | 11 coupes | oui | **garder** |
| Durées de plan | 1,5–3,5 s | respectées | oui | **garder** |
| Mouvement | varié, jamais gratuit | 4 familles (zoom in/out, pan H, pan V, push) | oui | **garder** |
| Transitions | bibliothèque V1.2, 6 images | TR01/02/03/04/05 | oui | **corrigé** (12 images → 6) |
| Graphismes | 8 blocs, fenêtres du plan | 8/8 | oui | **corrigé** (plages en dur → plan) |
| Densité typographique | 1 bloc à la fois | jamais plus de 2 blocs simultanés (GB03+GB04, GB05+GB06, tous deux déclarés) | oui | **garder** |
| Conversion | prix + WhatsApp + quartier | GB06/GB07/GB08 | oui | **garder** |
| DA (couleurs, polices, cartes) | V3.1 | INK/CREAM/orange, Montserrat + Plus Jakarta Sans | oui | **inchangée** |
| Zones de sécurité | aucun texte hors cadre | `fit_font` + boîtes | oui, aucun débordement | **garder** |
| Qualité d'image | netteté constante | base jusqu'à **1,70** ⇒ 424 px utiles | oui, P03/P08 plus doux | **signalé** — non corrigé : corriger changerait le cadrage approuvé |
| Audio | hors périmètre | master muet | oui | **inchangé** |

---

## 9. Écarts constatés

| # | Écart | Gravité | État |
|---|---|---|---|
| E1 | V3.1 lisait la progression de la scène entière au lieu des fenêtres de plan | **haute** | corrigé (§10) |
| E2 | V3.1 calculait la caméra à partir de l'index du plan (14 presets du plan ignorés) | **haute** | corrigé |
| E3 | V3.1 avait des plages d'images codées en dur pour les 8 graphismes | **haute** | corrigé |
| E4 | Les 3 grandes transitions étaient nommées dans le moteur, sur 12 images au lieu de 6 | **haute** | corrigé |
| E5 | L'étiquette `mask_reveal` de V3.1 ne correspondait à aucun masque (rendu = ruban diagonal) | moyenne | corrigé (TR04 nommé pour ce qu'il est) |
| E6 | `SOURCE_WINDOWS` codé en dur pour S2 + accélération `0,06·sin(2πp)` non déclarée | moyenne | supprimé |
| E7 | Le plan déclare une géométrie nominale des blocs que le moteur ne lit pas | moyenne | **assumé** : la DA V3.1 prime, écart documenté (§8.1) |
| E8 | Recadrages jusqu'à 1,70× ⇒ 424 px utiles ré-agrandis en 720 px (P03, P08) | moyenne | **signalé**, non corrigé (toucherait le cadrage approuvé) |
| E9 | En scène 1, V3.1 affichait une pastille d'accroche non déclarée par le plan (absente du master final) | faible | **assumé** : le plan ne la déclare pas ; à déclarer si elle doit revenir |
| E10 | `dur_min_f` déclaré pour P12 n'a pas d'effet dans le moteur | faible | documenté |
| E11 | `ffprobe` absent de l'environnement (le script de prises affiche des durées vides) | faible | contourné (mesure par OpenCV) |
| E12 | La divergence de mention vocale en scène 2 existait avant l'audit | moyenne | corrigé (§2.2) |

---

## 10. Corrections apportées

### 10.1 Parcours de capture (phase 1)

- `capture-guide/consignes_T1.json` : source unique, mention V6.2 unique (102 car.), consignes mot pour mot, durées 6/8/7/9.
- `tools/build_consignes.py` : génère `simulation/consignes.js` et `capture-guide/consignes_4_scenes.md`.
- `simulation/index.html` : fiche verticale en 9 blocs, une colonne, défilable, CTA fixe en bas ; états A/B/C ; `?capture=1` ; `window.__demo.freezeAt`.
- `tools/capture_ui.py` : 12 combinaisons 360/390/430 × 4 scènes, mesures typographiques, 23 captures, `reports/verification_lisibilite.json`.
- `tools/build_planche_12_etats.py` : planche des 12 états.

### 10.2 Moteur (phase 3) — `engine/motion_v4.py` (nouveau fichier, V3.1 non modifiée)

- `ShotReader` : lecture **séquentielle** de la fenêtre du plan (pas de seek approximatif), gel de fin réel.
- `camera_move()` : `base`, `k_ratio`, `pan_px`, `easing`, `dur_f` lus dans le plan ; `MV03` = attaque courte puis maintien.
- `do_transition()` : TR01 coupe sèche, TR02 punch cut, TR03 wipe diagonal, TR04 wipe directionnel, TR05 fondu — durée de la spec (6 images), déclenchée par `plan.cuts`.
- `render_graphics()` : 8 blocs aux fenêtres `overlays`, styles de la DA V3.1 (dont le titre produit empilé et le filet orange de l'ouverture, réalignés après comparaison à l'image).
- `reports/execution_manifest_v4.json` : journal d'exécution (par plan : source, fenêtre, mouvement, paramètres, transition, blocs actifs).

**Un seul master produit** : `output/output_T1_master_final.mp4`. Aucune V4.1, V4.2, aucune série d'essais.

### 10.3 Reproductibilité

```bash
pip install imageio-ffmpeg && ln -sf "$(python3 -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())')" ~/.local/bin/ffmpeg
bash rushes/build_scenes.sh                    # pris les 4 prises + vérifie les SHA des rushes
PYTHONPATH=. python3 engine/motion_v4.py --plan render_plan_v4_demo.json \
    --output output/output_T1_master_final.mp4 --manifest reports/execution_manifest_v4.json
python3 tools/verify_master.py                 # 24 points de mesure + conteneur + silence
PYTHONPATH=. python3 tools/frames_audit_v4.py  # planches de contrôle
```

Parcours de capture : `python3 tools/build_consignes.py` → `python3 tools/capture_ui.py` → `python3 tools/build_planche_12_etats.py` (après `pip install playwright && playwright install --with-deps chromium`).

---

## 11. Tests finaux

### 11.1 Contrôle du master

| Test | Méthode | Résultat |
|---|---|---|
| Conteneur | OpenCV + ffmpeg | 900 images, 30,000 s, 720×1280, **30 i/s** |
| Silence | inspection des flux ffmpeg | **aucune piste audio** |
| Images noires | luminance moyenne < 4/255 | **0** |
| Fenêtres sources | recherche conjointe (indice, zoom) sur 24 points | 16 conformes, 6 partiels, **0 index aberrant au-delà de ±2 images** |
| Transitions | planche aux milieux de transition | TR02 (3,6 s), TR03 (6,1 s), TR05 (14,1 s), TR04 (21,1 s) visibles |
| Graphismes | planche d'un point par bloc | **8/8** présents dans leur fenêtre |
| Lisibilité des cartes | zoom 1,6× sur GB03 | aucun chevauchement, filet sous le libellé, prix lisible |
| Tests unitaires du dépôt | `pytest -q` | **41 passed** |
| Parcours de capture | 12 combinaisons Playwright | **OK** (voir §3.2) |

Méthode des fenêtres sources, pour éviter toute ambiguïté : l'image du master est comparée à la prise normalisée sur la **bande haute y = 20–170**, où aucune carte de texte ne peut se trouver, avec le recadrage de zoom du moteur et le vignettage appliqué des deux côtés ; corrélation de Pearson. Une mesure de différence d'images ne prouve pas la qualité d'un mouvement — c'est pourquoi chaque point est doublé d'une planche visuelle.

### 11.2 Limites déclarées

- Les deux points P08 « à vérifier » (0,750 / 0,729) s'expliquent par le recadrage 1,67× : même indice, image plus douce. Non maquillé en « conforme ».
- Aucun écoute audio possible dans cet environnement : le master est muet par construction, aucune mesure de loudness n'est revendiquée ici (et l'audio est hors périmètre).
- La maquette est une simulation navigateur, pas une caméra Android ; aucune capture ne prétend le contraire.

---

## 12. Liens directs (téléchargement testé)

Release : **`t1-audit-final`** — https://github.com/j9028379-hue/vitrine-video-t1-pilot/releases/tag/t1-audit-final

Préfixe commun : `https://github.com/j9028379-hue/vitrine-video-t1-pilot/releases/download/t1-audit-final/`

| Livrable | Fichier | Code HTTP | Octets servis |
|---|---|---|---|
| **Master final** | `output_T1_master_final.mp4` | 200 | 9 207 121 |
| Référence V3.1 | `output_T1_sans_voix_v3_1.mp4` | 200 | 9 291 554 |
| V4 démo | `output_T1_sans_voix_v4_demo.mp4` | 200 | 9 492 461 |
| V3 | `output_T1_sans_voix_v3.mp4` | 200 | 8 861 052 |
| V2 | `output_T1_sans_voix_v2.mp4` | 200 | 22 915 774 |
| 12 captures + planche des 12 états | `ui-screens_et_planche.zip` | 200 | 13 972 877 |
| Planches d'audit du montage | `planches_audit_montage.zip` | 200 | 7 250 217 |
| Ce rapport | `T1_AUDIT_FINAL_PARCOURS_ET_MONTAGE.md` | 200 | 29 214 |
| Journal d'exécution | `execution_manifest_v4.json` | 200 | 12 603 |
| Contrôle du master | `final_master_checks.json` | 200 | 8 289 |

### 12.1 Vérification faite, pas supposée

- Chaque lien a été appelé **sans aucun en-tête d'authentification** (`curl -sIL`) : **10/10 en 200** avec `content-length` non nul. Ce n'est donc pas une page GitHub qui affiche un lien, c'est le fichier qui se télécharge.
- Le master a été **entièrement retéléchargé** depuis ce lien puis comparé : SHA-256 `97c3477d8043b3c1b8f5f11144d8b9f1aa65a803c0f5aa68a7747d6fb27dea91` — identique au fichier produit ; relu ensuite par OpenCV : **900 images, 30,0 i/s, 720×1280**.
- Le message « fichier trop volumineux » du dépôt ne concerne plus l'accès : les binaires sont dans la Release, pas dans l'arborescence Git.
- Aucune connexion au compte propriétaire n'est nécessaire pour télécharger : le dépôt est public et les assets de Release sont publics.

### 12.2 Pages publiées

- Dépôt : https://github.com/j9028379-hue/vitrine-video-t1-pilot (commit de l'audit : `dc94572`)
- Démonstration (GitHub Pages) : https://j9028379-hue.github.io/vitrine-video-t1-pilot/
- Maquette du parcours : https://j9028379-hue.github.io/vitrine-video-t1-pilot/simulation/

Ces deux dernières pages servent le commit poussé : la fiche verticale, les états A/B/C et le mode `?capture=1` y sont désormais identiques aux captures livrées.

### 12.3 Note d'honnêteté sur l'espace de travail

Le dépôt complet, une fois l'audio versionné inclus, pèse ~240 Mo. Comme l'audio est hors périmètre et déjà sur GitHub, il n'a pas été matérialisé dans l'espace de travail (exclusion Git locale) ; les rushes Mixkit (45 Mo, régénérables par `bash rushes/build_scenes.sh`) et les MP4 antérieurs (V2, V3, V4 démo : présents dans la Release) ont été retirés du disque après publication. Rien n'est perdu : code et images sont sur GitHub, binaires sur la Release.
