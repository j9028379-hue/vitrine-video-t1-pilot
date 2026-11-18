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

Les quatre fichiers sont locaux, MP3 stéréo 44,1 kHz / 160 kbit/s, décodent exactement en 30,000 secondes et ont été préparés autour de 120 BPM et −17,4 LUFS. Le catalogue et le JSON canonique T1 partagent l'identifiant sémantique `audio_profile: afrobeat_amapiano`; ce champ n'est ni une piste ni une version. Le rendu Android n'effectue aucun téléchargement.

## Intégration réelle dans le plan de rendu

Le gabarit silencieux publié reste byte-identique. Son adaptateur accepte désormais le sidecar musical :

```bash
python3 -m adapter.t1_adapter \
  --enable-music \
  --render-job-id t1-production-0001 \
  --music-state /var/lib/vitrine-video/t1-music-state.json \
  --music-variant auto \
  --output /tmp/render_plan_music_0001.json
```

Les identifiants approuvés forment un ordre fermé et immuable :

1. `t1_music_239426`
2. `t1_music_464383`
3. `t1_music_406552`
4. `t1_music_178406`

L'état initial sélectionne exclusivement la piste 1. Après chaque rendu **réussi**, `auto` sélectionne exclusivement le successeur exact `1→2→3→4→1`; un échec ou un QC refusé laisse l'état inchangé. Un choix explicite ne sert qu'à confirmer ce même successeur : il ne peut ni répéter la piste précédente, ni sauter une position, y compris au premier rendu. Le chemin recommandé est l'état JSON persistant passé par `--music-state`, qui contient le dernier succès et le registre durable `successful_render_jobs`. Aucun hash de `render_job_id`, hasard ou autre sélection alternative n'intervient.

Après le premier rendu, l'orchestrateur valide la piste 1 :

```bash
python3 tools/record_t1_music_result.py \
  --state /var/lib/vitrine-video/t1-music-state.json \
  --render-job-id t1-production-0001 \
  --selected-music-id t1_music_239426 \
  --status success
```

Le rendu suivant sélectionne alors la piste 2 :

```bash
python3 -m adapter.t1_adapter \
  --enable-music \
  --render-job-id t1-production-0002 \
  --music-state /var/lib/vitrine-video/t1-music-state.json \
  --music-variant auto \
  --output /tmp/render_plan_music_0002.json
```

Après ce rendu, l'orchestrateur confirme explicitement la piste 2 :

```bash
python3 tools/record_t1_music_result.py \
  --state /var/lib/vitrine-video/t1-music-state.json \
  --render-job-id t1-production-0002 \
  --selected-music-id t1_music_464383 \
  --status success
```

Avec `--status failed`, le fichier d'état n'est ni créé ni modifié. Une réussite est écrite atomiquement sous verrou interprocessus. Le registre `successful_render_jobs` rend idempotent le rejeu de **tout** succès déjà enregistré, même après un ou plusieurs tours complets; le même job ne peut jamais changer de piste. Deux validations concurrentes sont sérialisées et toute validation qui ne correspond pas au successeur attendu est rejetée sans mutation. Le contrat de l'état est `schemas/T1_music_selection_state.schema.json`. Aucun champ n'est ajouté au commerçant, aucun réseau n'est requis et aucun code OTA/Cloudflare n'est introduit. Le plan produit référence le fichier local, son SHA-256, les images 0–900 et les paramètres de mixage.

## Lecture Android hors ligne

Utiliser AndroidX Media3 avec l'asset local indiqué par `audio_track.file`. Préparer le lecteur avant l'image 0, lancer à l'image 0 et arrêter à l'image 900. La grille cible est 120 BPM : un temps vaut environ 0,5 seconde / 15 images, et les scènes restent `[0, 180, 420, 630, 900]`.

## Référence voix off et ducking validée

Le paquet musical publié reste inchangé. Un sidecar non destructif ajoute maintenant une même voix française masculine aux quatre scènes et permet de comparer le comportement réel des quatre musiques sans modifier le montage visuel :

- départs voix : `1,20 / 6,80 / 14,70 / 21,80 s` ;
- musique sans parole : `−3 dB` ;
- musique sous voix : `−10 dB` ;
- attaque du ducking : `120 ms` ;
- relâchement : `450 ms` ;
- aucun SFX ;
- master WAV : cible `−16 LUFS`, plafond `−2 dBTP` ;
- voix et musique : durée identité `1,0×`.

Le contrat est dans `config/T1_special_menu_voice_mix_v1_0_0.json`, la tige voix de 30 secondes dans `audio/voice/t1-voice-v1/t1_voice_stem_30s.wav`, et le rapport objectif dans `reports/T1_voice_music_v1_validation.json`.

Reconstruction des quatre WAV/MP3/MP4 :

```bash
python3 audio/scripts/mix_t1_voice_music_v1.py \
  --preview-dir output/t1-voice-music-v1
python3 audio/scripts/build_t1_voice_listening_board.py \
  --preview-dir output/t1-voice-music-v1
```

Attachement au plan de rendu (exemple avec Match Out) :

```bash
python3 -m adapter.t1_adapter \
  --enable-music \
  --previous-music-variant t1_music_406552 \
  --music-variant t1_music_178406 \
  --enable-voice \
  --render-job-id t1-voice-demo-0001 \
  --output /tmp/render_plan_voice.json
```

Le QC automatique mesure la durée, les LUFS, le true peak WAV/AAC, l'absence d'écrêtage et le rapport voix/musique sur chaque variante. La validation créative et la prononciation restent volontairement soumises à une écoute humaine des quatre aperçus.

## Rendu final sur GitHub Actions

Le workflow `.github/workflows/render_t1_complete_voice.yml` exécute sur `ubuntu-latest` le moteur canonique `engine.special_menu_style.render_project`, vérifie les trois polices enregistrées, reconstruit le master visuel, génère les quatre mixes et exécute les tests. Sur `push`, il publie uniquement l’artefact Actions. La Release historique `t1-complete-voice-video-v1.0.0` n’est envisagée que par lancement manuel avec `publish_release=true` et le workflow refuse désormais de l’écraser si elle existe.

Le fichier principal publié est `VIDEO_T1_MONTAGE_COMPLET_A_VALIDER.mp4`. Le rendu local n'est qu'un contrôle préalable ; le livrable de validation doit provenir de cette exécution serveur.

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
