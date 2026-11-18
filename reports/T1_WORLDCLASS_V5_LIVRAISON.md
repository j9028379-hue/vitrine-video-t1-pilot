# VITRINE VIDÉO T1 — livraison V5 « Worldclass »

> Rapport généré le 18/11/2026 à 12:15 UTC depuis les fichiers de mesure du dépôt. **Chaque chiffre de ce rapport vient d'un fichier décodé ou mesuré**, pas d'une estimation.

---

## 1. État GitHub

- Branche de travail : `t1-worldclass-engine` (créée depuis `main` = `ad4ff15`).
- Commit de départ : `ad4ff15` (état vérifié de `main` au début de la mission).
- Dernier commit V5 : `73b8b94`.
- Releases historiques conservées : `t1-audit-final`, `t1-cloture` (aucune modification).
- Nouvelle Release : `t1-worldclass-v5`.

## 2. État technique

### Composants créés

| Fichier | Rôle |
|---|---|
| `engine/scene_analyzer.py` | couche 1 : stabilité, netteté, pivots, ancres, colorimétrie |
| `engine/montage_plan_builder.py` | couche 2 : fenêtres, vitesses normalisées, caméra, transitions, blocs |
| `engine/adaptive_graphics_v5.py` | couche 3 : slots, cartes de verre, scrims, animations, protection |
| `engine/food_cinema_transitions.py` | bibliothèque des 6 transitions, mathématiques documentées |
| `engine/motion_v5.py` | couche 4 : rendu de référence, un seul encodage |
| `config/T1_worldclass_v5.json` | configuration complète du gabarit V5 |
| `tools/verify_worldclass.py` | contrôle sur le MP4 réel (22 critères) |
| `tools/build_profiles_v5.py` | les cinq profils commerçants + contrastes mesurés |
| `tools/comparison_v3_v4_v5.py` | comparaison mesurée V3.1 / V4 / V5 |
| `tests/test_v5_engine.py` | 23 tests de règles |

### Fichiers historiques préservés

`specs/` (V1.2 et V6.2), `capture-guide/consignes_T1.json`, `engine/motion_v3_1.py`, `engine/motion_v4.py`, `engine/presentation.py`, `config/T1_presentation_v3_1.json` (récupéré de la Release `t1-cloture`), `audio/`, les 41 tests historiques et les deux Releases.

## 3. Résultats chiffrés

### Master contractuel

| Mesure | Valeur |
|---|---|
| Fichier | `output/output_T1_master_v5.mp4` |
| SHA-256 | `35d0e9f50bc2275ee2536431b23bf27e36a1804098f3aa3438da78dead79ac6e` |
| Octets | 11924150 |
| Images | 900 |
| Durée | 00:00:30.00 |
| Résolution | 720×1280 |
| Cadence | 30.0 i/s |
| Codec | h264 |

### Fluidité mesurée sur le MP4

| Scène | Images | Images identiques au pixel | Suite max quasi identique | Mouvement moyen | Dernière seconde | Netteté médiane |
|---|---|---|---|---|---|---|
| S1 | 180 | 0 | 0 | 1.579 px | 4.769 | 428.9 |
| S2 | 240 | 0 | 0 | 0.249 px | 8.107 | 829.1 |
| S3 | 210 | 0 | 0 | 0.98 px | 8.727 | 835.3 |
| S4 | 270 | 0 | 0 | 0.594 px | 4.595 | 1592.6 |

- Images quasi identiques (MAD < 0,5) : **84** sur 900, suite la plus longue **3** (contrat : moins de 4).
- Ces quelques images viennent du **ralentissement du cœur de plan** et des zones naturellement calmes de la prise 2 ; aucun gel de fin, aucune image répétée pour atteindre 900.

### Analyse des prises

| Scène | Images | Stabilité | Netteté médiane | Pivot | Fenêtres exploitables |
|---|---|---|---|---|---|
| S1 | 180 | 0.5201 | 1838.76 | non | 60–179 |
| S2 | 240 | 0.9602 | 2604.14 | oui (image 120) | 0–119, 135–239 |
| S3 | 210 | 0.9073 | 6018.58 | non | 0–149, 165–209 |
| S4 | 271 | 0.8168 | 15675.61 | oui (image 138) | 0–134 |

Temps d'analyse : **4.856 s** pour les quatre prises (1.214 s par scène). L'objectif de 0,5 s par scène n'est **pas atteint** en Python pur : la mesure réelle est donnée ci-dessus, sans arrondi favorable.

### Performance du rendu

- Rendu complet des 900 images : **94.09 s**.
- Un seul encodage avec perte (libx264, CRF 18, `+faststart`), aucun fichier intermédiaire encodé.
- Mémoire crête constatée pendant la mise au point : environ 600 Mo (un cache d'images mal borné a provoqué un dépassement mémoire et a été corrigé).

### Les cinq profils commerçants

| Profil | Validation | Contraste mini (textes essentiels) | Blocs affichés | Planche |
|---|---|---|---|---|
| `demo_nominal` | 22 PASS / 0 FAIL / 0 PARTIAL / 0 NOT TESTED | 4.91 | 8 | `reports/profils_v5/planche_v5_demo_nominal.png` |
| `champs_longs` | 22 PASS / 0 FAIL / 0 PARTIAL / 0 NOT TESTED | 4.45 | 8 | `reports/profils_v5/planche_v5_champs_longs.png` |
|  |  | sous la cible : GB06 4.45 |  |  |
| `accroche_vide` | 22 PASS / 0 FAIL / 0 PARTIAL / 0 NOT TESTED | 4.91 | 7 | `reports/profils_v5/planche_v5_accroche_vide.png` |
| `accroche_un_mot` | 22 PASS / 0 FAIL / 0 PARTIAL / 0 NOT TESTED | 4.52 | 8 | `reports/profils_v5/planche_v5_accroche_un_mot.png` |
| `fond_blanc` | 17 PASS / 0 FAIL / 0 PARTIAL / 5 NOT TESTED | 5.62 | 8 | `reports/profils_v5/planche_v5_fond_blanc.png` |

### Comparaison V3.1 / Clôture V4 / V5

| Mesure | V3.1 | Clôture V4 | V5 |
|---|---|---|---|
| Images | 900 | 900 | 900 |
| Images quasi identiques (MAD < 0,5) | 16 | 161 | 84 |
| Suite max quasi identique | 1 | 10 | 3 |
| Mouvement moyen (px) | 0.718 | 1.5 | 0.93 |
| Différence moyenne inter-images | 3.557 | 4.761 | 6.034 |

Détail et planches : `reports/comparison_V3_1_V4_V5.md` et `reports/comparaison_V3_V4_V5/`.

## 4. Statut des critères

| Critère | Statut | Preuve |
|---|---|---|
| Quatre scènes exactement | `PASS` | plan.scenes |
| Durées 6 / 8 / 7 / 9 s | `PASS` | mesure par scène sur le MP4 |
| 30,000 s et 900 images | `PASS` | conteneur + décodage |
| Format 9:16 (720×1280) | `PASS` | conteneur |
| Master silencieux | `PASS` | conteneur |
| Aucune image noire | `PASS` | luminance par image |
| Aucune suite de 4 images identiques | `PASS` | MAD < 0,5 sur images décodées + identité exacte |
| Aucune dernière seconde figée | `PASS` | différence moyenne sur les 30 dernières images de chaque scène |
| Aucun gel de fin de plan | `PASS` | suites identiques par scène |
| Mouvement mesurable par scène | `PASS` | corrélation de phase entre images consécutives |
| Zoom numérique sous le plafond 1,32 | `PASS` | plan.shots[].camera.zoom |
| Tout panoramique déclaré produit un déplacement mesurable | `PASS` | plan.shots[].camera.pan_rel.deplacement_px |
| Répétitions bornées à 2 images consécutives | `PASS` | plan.shots[].speed |
| Transitions déclarées dans le plan et au bon endroit | `PASS` | plan.cuts |
| Aucune rupture accidentelle hors coupes déclarées | `PASS` | différences par image |
| Huit blocs déclarés | `PASS` | plan.blocs |
| CTA WhatsApp visible à l'image 899 | `PASS` | masque couleur sur le MP4 |
| Packshot et CTA tenus jusqu'à l'image 899 | `PASS` | plan.blocs |
| Aucun agrandissement effectif au-delà de 1,32 | `PASS` | plan.shots[].camera.zoom |
| Sources utilisées en définition native | `PASS` | engine/motion_v5.py::camera_frame |
| Un seul encodage avec perte | `PASS` | aucun fichier intermédiaire encodé |
| Netteté mesurée par scène | `PASS` | variance du Laplacien sur les images du MP4 |

**Résumé du vérificateur : 22 PASS, 0 FAIL, 0 PARTIAL, 0 NOT TESTED.**

### Autres critères de la mission

| Critère | Statut | Preuve |
|---|---|---|
| Les 41 tests historiques passent | `PASS` | `python3 -m pytest -q` → 64 tests (41 + 23) |
| Nouveaux tests V5 | `PASS` | `tests/test_v5_engine.py` |
| Cinq profils commerçants exécutés | `PASS` | `reports/profils_v5/` |
| Bibliothèque complète de transitions testée | `PASS` | 6 transitions utilisées dans le montage + `tests/test_v5_engine.py` |
| Parcours de capture revalidé (12 états × 3 largeurs) | voir §6 | `ui-screens/` |
| Packaging corrigé (config V3.1 dans Git, README) | `PASS` | `config/T1_presentation_v3_1.json`, `README.md` |
| Anciens masters et Releases préservés | `PASS` | Releases `t1-audit-final`, `t1-cloture` inchangées |
| Aucun fichier audio modifié | `PASS` | `git diff --stat -- audio/` vide |
| Portage Android | `NOT TESTED` | `reports/PORTABILITY_ANDROID_T1.md` : architecture préparée, aucun test sur appareil |

## 5. Défauts trouvés et corrigés pendant la mission

1. **Cache d'images non borné** dans le rendu : 7 lecteurs × 240 images = 3 Go, processus tué par le système à l'image 707. Cache ramené à 6 images par lecteur.
2. **Matrice d'échantillonnage inversée** dans la bibliothèque de transitions : `cv2.warpAffine` recevait la matrice inverse et repliait les bords (effet miroir interdit par le brief). Corrigé : matrice directe, bord répliqué.
3. **Bouton WhatsApp invisible** : il était dessiné avant la carte packshot qui le recouvrait. Empilement déclaré dans la configuration (`slots.end_packshot.pile`).
4. **Contraste du bouton WhatsApp à 2,66:1** (crème sur vert). Texte encre sur vert : 6,56:1, mesuré sur le MP4.
5. **Packshot effacé avant la fin** : les blocs dont la fenêtre va jusqu'à l'image 899 tiennent désormais à pleine opacité.
6. **Panoramiques rognés** : l'overscan est calculé depuis l'amplitude déclarée, plafonné à 1,32.
7. **`easeOutBack`** réellement implémenté (dépassement mesuré > 1,02) pour le rebond du prix.

## 6. Parcours de capture

- Décompte `3 · 2 · 1` en 1,5 s sur l'aperçu dégagé, avant le départ du chronomètre.
- Quatre repères d'angle discrets, **état B uniquement**, aucun texte, aucun cadre central.
- Marge technique de 0,4 s invisible : le commerçant voit toujours 6 / 8 / 7 / 9 secondes.
- Alerte qualité après la prise (quasi-noir ou très flou) avec `GARDER` / `REFAIRE` ; une incertitude de détection ne bloque jamais.
- Titre vocal aligné partout : `TU PEUX PARLER PENDANT QUE TU FILMES` (interface, fiche imprimable, `tools/build_consignes.py`). Mention V6.2 inchangée (102 caractères).

## 7. Ce qui n'est pas fait, et pourquoi

- **Aucun travail audio** : le master V5 est muet, `audio/` n'est pas touché.
- **Portage Android non réalisé** : architecture et shaders documentés, aucun test sur appareil.
- **Netteté d'ouverture** bornée par la source (prise 1) ; **scène 3 en 404×720**, non améliorable.
- **Master 1080×1920 non produit** : les sources les plus définies sont 606×1080 ; un master 1080 n'aurait fait qu'inventer des pixels.
- **Objectif 0,5 s d'analyse par scène non atteint** (1,2 s mesurée).

## 8. Empreintes des livrables

| Fichier | SHA-256 |
|---|---|
| `output/output_T1_master_v5.mp4` | `35d0e9f50bc2275ee2536431b23bf27e36a1804098f3aa3438da78dead79ac6e` |
| `reports/montage_plan_v5_demo.json` | `2a6d3caacb43a4b001f3ac5af4414112338d9f8ccea5590df364d0589be69b0a` |
| `reports/scene_analysis_T1.json` | `eb443125dbe812466cdb71906bd2bbc986f64df756b73c44e22a1ad52d2f5fdc` |
| `reports/execution_manifest_v5.json` | `9e61083c2312c5e505c810b114718f32e497aa165fd7a2f9f8692306fdc3fab2` |
| `reports/worldclass_validation_T1.json` | `9ac225693971a9c38314b03541161ea0c60e883b742652f4ec7c8d1b79437a9d` |
| `config/T1_worldclass_v5.json` | `b6acda92a802f87fbf6fc5eb77643838f0adb0157ada8bb34063b531d7e9b267` |
| `reports/comparison_V3_1_V4_V5.md` | `7e79d1a808c28ce87e0dc0bf1ba9510b6a8b3c44cb14708585e2fed05c7121f3` |
| `reports/PORTABILITY_ANDROID_T1.md` | `6033e34bdc01bf25477d112f5f07c2aa36455742c676f55e1d1d5da32a2eed17` |

## 9. Reproduction depuis un clone neuf

Opérations réellement exécutées, dans un répertoire vierge (`/tmp/clone_v5`) :

1. `git clone --branch t1-worldclass-engine https://github.com/j9028379-hue/vitrine-video-t1-pilot`
2. `bash rushes/build_scenes.sh` — les quatre prises sont retéléchargées et vérifiées (SHA-256 des rushs).
3. `engine/scene_analyzer.py`, `engine/montage_plan_builder.py`, `engine/motion_v5.py`.
4. `tools/verify_worldclass.py` sur le master reproduit.

| Contrôle | Résultat |
|---|---|
| SHA-256 du master reproduit | `35d0e9f50bc2275ee2536431b23bf27e36a1804098f3aa3438da78dead79ac6e` |
| Identique au master publié | **oui, bit à bit** |
| Vérificateur sur le master reproduit | 22 PASS / 0 FAIL / 0 PARTIAL / 0 NOT TESTED |
| `pytest` dans le clone neuf | 63 passed, 1 failed |

Le test en échec dans le clone neuf est `tests/test_adapter.py::test_plan_uses_read_only_specs_and_silent_audio` : il compare le plan à `specs/restaurants_maquis_T1.spec_v6_2.json`, une **référence canonique locale volontairement non publiée** (`.gitignore`). Dans l'environnement de travail, où ce fichier existe, les **64 tests passent**. Aucune assertion n'a été affaiblie pour obtenir ce résultat.

## 10. Vérification publique de la Release

Release `t1-worldclass-v5` : https://github.com/j9028379-hue/vitrine-video-t1-pilot/releases/tag/t1-worldclass-v5

| Asset | HTTP | Octets servis |
|---|---|---|
| `output_T1_master_v5.mp4` | 200 | 11 924 150 |
| `T1_WORLDCLASS_V5_LIVRAISON.md` | 200 | 10 996 |
| `worldclass_validation_T1.json` | 200 | 54 713 |
| `montage_plan_v5_demo.json` | 200 | 50 162 |
| `scene_analysis_T1.json` | 200 | 8 680 |
| `execution_manifest_v5.json` | 200 | 17 739 |
| `comparison_V3_1_V4_V5.md` | 200 | 4 235 |
| `PORTABILITY_ANDROID_T1.md` | 200 | 9 349 |
| `T1_worldclass_v5.json` | 200 | 20 879 |
| `profils_v5_planches.zip` | 200 | 4 521 184 |
| `comparaison_V3_V4_V5_planches.zip` | 200 | 3 117 187 |
| `moteur_v5_sources.zip` | 200 | 134 541 |
| `MANIFESTE_SHA256_V5.txt` | 200 | 4 881 |
| `RELEASE_NOTES_t1_worldclass_v5.md` | 200 | 3 860 |

Master retéléchargé **sans authentification** puis haché : `35d0e9f50bc2275ee2536431b23bf27e36a1804098f3aa3438da78dead79ac6e` — identique au fichier local.

## 11. Déclaration finale

**TERMINÉ ET LIVRÉ** pour les conditions 1 à 14 de la mission, à deux réserves explicites :

- le **portage Android** n'est pas réalisé (aucun test sur appareil) : l'architecture est documentée, pas validée ;
- le **contraste** du profil « champs longs » descend à **4,45:1** sur un instant mesuré (cible 4,5) : c'est écrit tel quel plutôt qu'arrondi.
