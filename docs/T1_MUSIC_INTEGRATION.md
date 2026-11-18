# T1 — intégration musicale Afrobeat/Amapiano v1.0.0

## Lot définitif validé

Ce paquet est un successeur musical non destructif de la release silencieuse T1 `cab2aa2a4a841341c9e84aeb08e243ea9baec0f4`.
Il contient **exactement quatre** éditions de 30 secondes validées par l'utilisateur :

| ID Pixabay | Musique | Artiste | Content ID | Production |
|---:|---|---|---|---|
| 239426 | Go Down | WizzykeyzBeat | non affiché | prête |
| 464383 | ALONE | DMSOUNDWORKS | non affiché | prête |
| 406552 | PAUSE | audiolibraryinfinite | non affiché | prête |
| 178406 | Match Out | artbybigvee | non affiché | prête |

`Match Out` remplace définitivement la piste `573944`, rejetée à cause de sa dépendance à un certificat Content ID. La piste `573944` n'est ni embarquée, ni sélectionnable, ni référencée comme variante.

Les quatre fichiers sont locaux, MP3 stéréo 44,1 kHz / 160 kbit/s, décodent exactement en 30,000 secondes et ont été préparés autour de 120 BPM et −17,4 LUFS. Le rendu Android n'effectue aucun téléchargement.

## Intégration réelle dans le plan de rendu

Le gabarit silencieux publié reste byte-identique. Son adaptateur accepte désormais le sidecar musical :

```bash
python3 -m adapter.t1_adapter \
  --enable-music \
  --render-job-id t1-production-0001 \
  --music-variant auto \
  --output /tmp/render_plan_music.json
```

La sélection peut être explicite avec l'un des identifiants suivants :

- `t1_music_239426`
- `t1_music_464383`
- `t1_music_406552`
- `t1_music_178406`

Le mode `auto` utilise `sha256(render_job_id) mod 4`, ce qui rend la sélection stable et reproductible. Aucun champ n'est ajouté au commerçant. Le plan produit référence le fichier local, son SHA-256, les images 0–900 et les paramètres de mixage.

## Lecture Android hors ligne

Utiliser AndroidX Media3 avec l'asset local indiqué par `audio_track.file`. Préparer le lecteur avant l'image 0, lancer à l'image 0 et arrêter à l'image 900. La grille cible est 120 BPM : un temps vaut environ 0,5 seconde / 15 images, et les scènes restent `[0, 180, 420, 630, 900]`.

## Préparation de la phase voix off

Cette livraison n'ajoute encore aucune voix ni aucun SFX. Elle réserve toutefois le comportement à tester pendant la phase suivante :

- musique sans parole : `−3 dB` ;
- musique sous voix : `−10 dB` ;
- attaque du ducking : `120 ms` ;
- relâchement : `450 ms` ;
- voix et audio capturé : durée identité `1,0×` ;
- éventuel creux dynamique futur entre `1,5 et 4 kHz`, uniquement pendant la parole.

La génération des voix off pourra donc tester successivement le même moteur contre les quatre variantes sans modifier le montage visuel.

## Licence et preuves

Chaque piste dispose d'une page officielle, de son URL CDN officielle, du nom de fichier d'origine, de l'empreinte SHA-256 et d'une preuve JSON-LD. Les pages officielles rendues ne présentent ni le label ni la propriété `Content ID Registered` pour ces quatre pistes. La licence est la Pixabay Content License ; les originaux complets ne sont pas inclus dans le dépôt, seulement les adaptations de 30 secondes intégrées au gabarit.

## Validation et construction

```bash
python3 tools/refresh_t1_music_manifest.py
python3 tools/validate_t1_music_pack.py
python3 tools/build_t1_music_pack.py
python3 -m pytest -q
```

Le bundle reproductible est :

`packages/t1-special-menu-music-v1/t1-special-menu-afrobeat-amapiano-music-v1.zip`
