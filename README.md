# VITRINE VIDÉO — T1 « Restaurants et Maquis »

Démonstration complète du gabarit **T1** : quatre prises vidéo (6 s · 8 s · 7 s · 9 s), un montage de 30 s,
une maquette de parcours jouable dans le navigateur, et tout le son (voix, musique, effets) publié séparément.

> **Ce dépôt est une démonstration.** Les valeurs commerciales sont fictives (« Maquis Démo », « Burger maison »,
> « 2 500 FCFA », « ARCONVILLE — ADRESSE FICTIVE », « NUMÉRO FICTIF ») : aucun contact réel, aucune donnée personnelle.
> Les rushs sont des extraits de stock sous licence libre, ce ne sont pas les images d'un vrai commerce.
> La voix est une **voix de synthèse** déclarée comme telle. La maquette de parcours n'est **pas** une validation de
> l'application Android (caméra, permissions, arrêt système) : c'est une maquette d'écrans et d'enchaînement.

---

## 1. Voir la démonstration en 30 secondes

| Ce que vous cherchez | Fichier |
|---|---|
| La publicité finie, avec le son | `output/output_T1_audio_demo_A.mp4` (recommandée) · `output/output_T1_audio_demo_B.mp4` (alternative) |
| La même vidéo sans son | `output/output_T1_sans_voix_v4_demo.mp4` |
| La référence muette V3.1 (inchangée) | `output/output_T1_sans_voix_v3_1.mp4` |
| **Le master V5 « Worldclass » (moteur actuel)** | `output/output_T1_master_v5.mp4` |
| Le parcours dans le navigateur | `simulation/index.html` |
| Les écrans, en images | `ui-screens/` (19 captures) |
| Les quatre consignes de tournage | `capture-guide/README.md` |

## 2. Lancer la maquette de parcours

**En ligne (GitHub Pages)** : `Settings → Pages → Deploy from a branch → main / (root)`, puis ouvrir
`https://j9028379-hue.github.io/vitrine-video-t1-pilot/simulation/`. Le fichier `.nojekyll` est déjà présent.

**En local** — un simple serveur statique suffit (les vidéos ne se chargent pas en `file://`) :

```bash
python3 -m http.server 8000
# puis ouvrir http://127.0.0.1:8000/simulation/
```

Ce qu'on voit, dans l'ordre :

1. **Scène 1/4 — LE PLAT · 6 secondes.** La prise tourne déjà derrière la carte de consigne. Le bouton `GO · COMMENCER`
   lance l'enregistrement.
2. **Pendant l'enregistrement, la carte disparaît complètement** : il ne reste que l'aperçu caméra, le chrono et la barre
   de progression. Toutes les durées sont imposées (6 / 8 / 7 / 9 s) et l'enregistrement s'arrête tout seul.
3. **Après la prise** : elle est rejouée **avec le son**, avec deux boutons `REFAIRE` et `SCÈNE SUIVANTE`
   (après la scène 4 : `VOIR MON MONTAGE`).
4. **Montage en cours**, puis la **publicité finale**, puis l'écran de fin.

Les quatre consignes affichées sont celles de la spécification V6.2, **mot pour mot** (titre, durée, « À montrer »,
« À éviter », mention vocale, exemple de phrase). ⚠️ La scène 1 dure **6 secondes** : l'ancienne capture qui affichait
« 5 s » sur la scène 1 est une erreur, elle n'est pas reproduite ici.

## 3. Contenu du dépôt

```
capture-guide/          les 4 consignes de tournage, les listes à montrer / à éviter, les limites des rushs
ui-screens/             19 captures : 4 × (état A consigne, B enregistrement, C validation) + montage + fin
simulation/             maquette de parcours (HTML autonome) + media/ (4 prises web + voix)
rushes/                 manifest.json (URL, licence, SHA-256 des rushs) + build_scenes.sh (reconstruit les 4 prises)
audio/voice/            4 voix de synthèse françaises, un fichier par scène
audio/music/v2/         les 2 musiques originales, 120 BPM / 30 s
audio/stems/v2/         les stems des 2 musiques (FLAC sans perte)
audio/sfx/              13 matières sonores originales (3 seulement sont utilisées, voir plus bas)
audio/ambience/         ambiance de salle synthétisée
audio/synced/v2/        mix_A.wav, mix_B.wav et les 3 tiges du mixage par piste
audio/sync/             document de synchronisation (repères, départs de voix, ducking)
audio/scripts/          build_music_v2.py, mix_v2.py, qc_v2.py, loudness.py, ducking.py, synth_lib.py
audio/metadata/         LICENCES.md, VOIX_SYNTHETIQUES.md, mesures JSON (mix_v2_report, qc_v2, music_v2_build)
audio/video_edit_analysis_T1.md     analyse du fichier vidéo exporté (coupes mesurées, textes, rythme)
audio/note_tendances_musicales_afrique_ouest_2026.md   note sourcée et datée
output/                 MP4 livrés + planches de contrôle
reports/                rapport de mixage, plan de rendu V3.1 archivé
engine/, adapter/       moteur de rendu 720 × 1280 et adaptateur V1.2 → plan de rendu
specs/, tests/          spécifications de référence et tests
tools/capture_ui.py     régénère les captures d'écran (Playwright + Chromium)
```

## 4. Les quatre prises vidéo

Les quatre scènes sont des **séquences vidéo `.mp4`**, jamais des photographies — même avec un zoom ou un mouvement
artificiel. Chacune correspond à ce que le commerçant doit filmer :

| Scène | Durée | Consigne (résumé) | Rush réel utilisé |
|---|---|---|---|
| 1/4 | 6 s | le plat, la main qui sert, l'assiette entière | un serveur porte puis pose un hamburger |
| 2/4 | 8 s | le dessus du plat, puis un détail très proche | plat vu d'au-dessus (4 s) + gros plan sauce/œuf/frites (4 s) |
| 3/4 | 7 s | la personne qui sert ou qui mange | un homme mange son hamburger, mains et visage visibles |
| 4/4 | 9 s | le lieu, l'enseigne, la rue, puis le comptoir | terrasse et entrée vues de la rue (4,6 s) + comptoir avec clients (4,4 s) |

**Limite assumée sur la scène 4** : dans les rushs libres d'usage commercial disponibles, **aucune enseigne lisible**
n'apparaissait. Le nom du commerce n'est donc affiché que par les textes du gabarit. Une vraie campagne doit tourner
cette scène devant l'enseigne réelle du commerçant (voir `capture-guide/README.md`).

Reconstruire les prises (télécharge les 6 clips Mixkit, vérifie leurs empreintes, assemble les 4 fichiers) :

```bash
bash rushes/build_scenes.sh
```

## 5. Le son

- **Voix** : 4 fichiers séparés, même identité vocale, textes exacts, aucun sous-titre ni traduction.
  Voir `audio/metadata/VOIX_SYNTHETIQUES.md`. Ce sont des voix de **synthèse**, pas l'enregistrement d'un commerçant.
- **Musique** : 2 propositions seulement, 120 BPM / 30 s, compositions originales.
  - **A — « afro-maquis 120 »** (recommandée) : basse ronde, kick 4/4, shakers, kalimba/marimba, nappe discrète.
  - **B — « gangan acoustique »** (alternative) : tambours parlants simulés, balafon, djembé, très peu d'électronique.
  - ⚠️ Aucun outil de génération musicale par IA n'était disponible : les pistes sont **composées et synthétisées en
    code**, pas générées par un modèle de musique. C'est dit aussi dans `audio/metadata/LICENCES.md`.
- **Effets** : 3 matières seulement, toutes justifiées par une action visible — l'assiette posée à 2,10 s, la tasse posée
  à 28,30 s, l'ambiance de salle à −32 dB. **Aucun whoosh, pop ou ding systématique**, aucun bruit de grillade (la vidéo
  ne montre aucune cuisson), aucune ambiance de rue dense.
- **Réglages V6.2 conservés** : musique −6 dB (−16 dB sous la voix), effets −5 dB (−8 dB sous la voix), ducking seuil
  −26 dBFS, lookahead 80 ms, hold 200 ms, attaque 60 ms, relâchement 400 ms, profondeur −10 dB, fondu 28,5 → 30 s.
- **Mesures** : −16,0 LUFS, true peak −2,7 dBTP, 0 écrêtage, audio du MP4 fidèle au WAV (−0,03 dB) et **0,0 ms de
  décalage** audio/vidéo. Détail : `reports/rapport_mixage_T1_demo.md`.
- **Honnêteté** : je n'ai pas pu écouter le mixage (aucune sortie audio ici). Le contrôle est objectif ; la liste
  d'écoute à faire avant diffusion est au §5 du rapport de mixage.

## 6. Le moteur actuel (V5 « Worldclass »)

Trois moteurs cohabitent dans le dépôt, et c'est volontaire :

| Moteur | Fichier | Statut |
|---|---|---|
| **V5 — actuel** | `engine/motion_v5.py` | moteur de référence : analyse des prises, plan construit, caméra sous-pixel, 6 transitions, graphismes adaptatifs |
| V4 — clôture | `engine/motion_v4.py` | conservé, reproductible, publication `t1-cloture` |
| V3.1 — historique | `engine/motion_v3_1.py` | conservé comme référence visuelle approuvée |

### Dépendances

```bash
python3 -m pip install -r requirements.txt        # numpy, opencv, pillow, pytest
python3 -m pip install imageio-ffmpeg             # fournit le binaire ffmpeg
mkdir -p ~/.local/bin && ln -sf "$(python3 -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())')" ~/.local/bin/ffmpeg
export PATH=$HOME/.local/bin:$PATH
```

### Chaîne complète, depuis un clone neuf

```bash
bash rushes/build_scenes.sh                       # 1. les 4 prises (6/8/7/9 s), téléchargées et vérifiées
PYTHONPATH=. python3 engine/scene_analyzer.py \
    --out reports/scene_analysis_T1.json          # 2. analyse : stabilité, netteté, pivots, ancres, couleurs
PYTHONPATH=. python3 engine/montage_plan_builder.py \
    --profile demo_nominal \
    --out reports/montage_plan_v5_demo.json       # 3. plan de montage (aucune image lue)
PYTHONPATH=. python3 engine/motion_v5.py \
    --plan reports/montage_plan_v5_demo.json \
    --output output/output_T1_master_v5.mp4 \
    --manifest reports/execution_manifest_v5.json # 4. rendu : 900 images, un seul encodage
PYTHONPATH=. python3 tools/verify_worldclass.py   # 5. contrôle sur le MP4 réel
PYTHONPATH=. python3 tools/build_profiles_v5.py   # 6. les cinq profils commerçants
PYTHONPATH=. python3 tools/comparison_v3_v4_v5.py # 7. comparaison V3.1 / V4 / V5
python3 -m pytest -q                              # 8. 64 tests
```

Les cinq profils commerciaux sont dans `engine/montage_plan_builder.py` (`PROFILS_COMMERCIAUX`) :
`demo_nominal`, `champs_longs`, `accroche_vide`, `accroche_un_mot`, `fond_blanc`.

### Fichiers de configuration

| Fichier | Rôle |
|---|---|
| `config/T1_worldclass_v5.json` | configuration V5 : slots, cartes, typographie, animations, transitions, vitesses, qualité |
| `config/T1_presentation_v3_1.json` | configuration historique V3.1, lue par `engine/presentation.py` (moteur V4) |
| `reports/montage_plan_v5_demo.json` | plan de montage V5 (contrat JSON Python ↔ Android) |

### Résultats produits

| Chemin | Contenu |
|---|---|
| `output/output_T1_master_v5.mp4` | master V5, 900 images, 30 s, 720×1280, muet |
| `reports/scene_analysis_T1.json` | analyse des quatre prises |
| `reports/execution_manifest_v5.json` | journal d'exécution du rendu V5 |
| `reports/worldclass_validation_T1.json` | 22 contrôles mesurés sur le MP4 |
| `reports/profils_v5/` | cinq profils : plans, masters, validations, planches, contrastes |
| `reports/comparison_V3_1_V4_V5.md` | comparaison mesurée + analyse artistique |
| `reports/PORTABILITY_ANDROID_T1.md` | architecture et limites du portage Android |

### Limitations connues du V5

- La netteté d'ouverture est bornée par la prise 1 (606×1080, première seconde douce).
- La scène 3 reste en 404×720 : aucun upscale ne restitue des détails absents.
- Le ralentissement du cœur de plan réutilise quelques images (jamais plus de deux consécutives) ;
  ce sont des répétitions de rythme, pas des gels.
- Aucun test sur appareil Android : le portage est préparé, pas réalisé.
- Le profil `fond_blanc` utilise une fixture synthétique : il valide le graphisme, pas la fluidité.

## 7. Reconstruire de bout en bout (chaîne historique V4)

```bash
python3 -m pip install -r requirements.txt      # numpy, scipy, pillow, opencv, pytest
bash rushes/build_scenes.sh                     # 4 prises vidéo (6/8/7/9 s)
PYTHONPATH=. python3 engine/motion_v4.py \
    --plan render_plan_v4_demo.json \
    --output output/output_T1_sans_voix_v4_demo.mp4 \
    --sheet output/planche_controle_v4_demo.png
cd audio/scripts && python3 build_music_v2.py && python3 mix_v2.py && python3 qc_v2.py && cd ../..
for t in A B; do
  ffmpeg -y -i output/output_T1_sans_voix_v4_demo.mp4 -i audio/synced/v2/mix_$t.wav \
    -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -movflags +faststart output/output_T1_audio_demo_$t.mp4
done
python3 tools/capture_ui.py                     # régénère ui-screens/
python3 -m pytest -q                            # tests de l'adaptateur et du moteur
```

## 8. Ce qui n'est pas fait, et pourquoi

- **Pas de nouvelle spécification** V1/V2/V3 : la direction artistique visuelle et le montage V3.1 ne sont pas refaits.
  Seule la correspondance entre scènes et rushs a été corrigée, plus les valeurs de démonstration (adresse fictive).
- **Pas de test Android** : aucun code Android n'est disponible ; la maquette le dit explicitement.
- **Pas de validation subjective du mixage** : voir §5 du rapport.
