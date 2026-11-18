# Index de livraison — démonstration T1 « Restaurants et Maquis »

Commit : **`2d40955`** (branche `main`, dépôt `j9028379-hue/vitrine-video-t1-pilot`).
Date : 18 novembre 2026.

## Les 12 éléments publiés

| # | Élément | Où | État |
|---|---|---|---|
| 1 | Sources et moteur (renderer 720 × 1280, adaptateur, tests) | `engine/`, `adapter/`, `specs/`, `tests/` | ✅ 41 tests au vert |
| 2 | Documentation en français (lire, lancer, reconstruire) | `README.md` | ✅ |
| 3 | Captures d'écran — 19 PNG | `ui-screens/` | ✅ |
| 4 | Maquette de parcours jouable | `simulation/index.html` (+ `simulation/media/`) | ✅ |
| 5 | Guide de tournage des 4 scènes | `capture-guide/README.md` | ✅ |
| 6 | Rushs : manifeste (URL, licence, SHA-256) + script de reconstruction | `rushes/manifest.json`, `rushes/build_scenes.sh` | ✅ |
| 7 | Voix de synthèse — 4 fichiers séparés | `audio/voice/` | ✅ |
| 8 | Musiques originales — 2 propositions, 120 BPM / 30 s | `audio/music/v2/` (+ stems `audio/stems/v2/`) | ✅ |
| 9 | Effets et ambiance | `audio/sfx/`, `audio/ambience/` | ✅ (3 matières utilisées sur 13) |
| 10 | Mixages et tiges | `audio/synced/v2/` | ✅ |
| 11 | Documents d'analyse et de synchro | `audio/video_edit_analysis_T1.md`, `audio/note_tendances_musicales_afrique_ouest_2026.md`, `audio/sync/synchro_T1_demo.md`, `reports/rapport_mixage_T1_demo.md` | ✅ |
| 12 | Vidéos finales consultables et téléchargeables | `output/output_T1_audio_demo_A.mp4`, `_B.mp4`, `output_T1_sans_voix_v4_demo.mp4`, `output_T1_sans_voix_v3_1.mp4` | ✅ |

## Empreintes SHA-256 des vidéos

| Fichier | SHA-256 | Taille |
|---|---|---|
| `output/output_T1_audio_demo_A.mp4` | `4f6b5754bfc1a158a4d765efdf2bbb8f040f3a367f41934d70fb8be0d82497c9` | 9,8 Mo |
| `output/output_T1_audio_demo_B.mp4` | `6858c38baa7cd4a1325d138468689cb70ce14af2fbc2f30247d4984a7bc4c966` | 9,8 Mo |
| `output/output_T1_sans_voix_v4_demo.mp4` | `a5421eadc87a537fbe3ff49e6c207be405990220a33d036bf31b47fe25609efa` | 9,1 Mo |
| `output/output_T1_sans_voix_v3_1.mp4` (référence intacte) | `33abc850265242b91fb61284e7e7649cc92b7750414212fa8f05ed4e455c2039` | 8,9 Mo |

## Publication — ce qui reste à faire côté dépôt distant

Le commit est prêt **localement** dans cet environnement. Le dépôt distant n'a pas pu être mis à jour ici :
aucun remote n'est configuré et aucun identifiant GitHub n'est disponible (`gh` absent, helper de credentials
pointant vers un binaire inexistant, `git push --dry-run` → « No configured push destination »).

Depuis une machine où vous êtes authentifié sur `j9028379-hue/vitrine-video-t1-pilot` :

```bash
# option 1 — depuis un clone existant
git clone https://github.com/j9028379-hue/vitrine-video-t1-pilot.git
cd vitrine-video-t1-pilot
git pull /home/user/vitrine-video-t1-pilot-main.bundle main   # ou copier le dossier puis : git fetch ../bundle main
git push origin main
```

```bash
# option 2 — pousser directement le bundle
cd <votre clone>
git fetch /chemin/vitrine-video-t1-pilot-main.bundle main:demo-t1
git checkout main && git merge --ff-only demo-t1 && git push origin main
```

Puis, pour la simulation en ligne : `Settings → Pages → Deploy from a branch → main / (root)`,
et ouvrir `https://j9028379-hue.github.io/vitrine-video-t1-pilot/simulation/`.

## Ce qui reste ouvert (assumé)

1. **Scène 4 sans enseigne lisible** : aucun rush libre avec une enseigne exploitable ; le nom n'apparaît que dans les
   textes du gabarit (documenté dans `capture-guide/`).
2. **Mixage non écouté par un humain** : contrôle objectif complet, liste d'écoute au §5 de `reports/rapport_mixage_T1_demo.md`.
3. **Aucun outil de génération musicale par IA** disponible : les 2 musiques sont composées et synthétisées en code,
   déclarées comme telles.
4. **Pas de validation Android** : la maquette de parcours le dit explicitement.
