# T1 — voix française × quatre musiques — rapport v1

Date : 18 novembre 2026

État du contrôle objectif : **PASS**

État de l’écoute créative : **à valider par une personne**

## Résultat

Une seule identité vocale française masculine (`voice-00`) a été nivelée puis placée sur les quatre scènes. La même tige voix de 30,000 s est mixée avec chacune des quatre musiques approuvées, sans SFX et sans modifier le master vidéo silencieux.

| Scène | Début | Fin | Durée | Texte |
|---:|---:|---:|---:|---|
| 1 | 1,20 s | 4,07 s | 2,87 s | Voici notre burger maison, préparé pour vous. |
| 2 | 6,80 s | 10,31 s | 3,51 s | Regardez le pain doré, la garniture et tous les détails. |
| 3 | 14,70 s | 17,89 s | 3,19 s | On vous le sert tout juste préparé. Venez le découvrir ! |
| 4 | 21,80 s | 26,27 s | 4,47 s | Retrouvez Maquis Démo à Arconville. Pour commander, contactez-nous sur WhatsApp. |

Les quatre prises traitées mesurent entre **−20,18 et −19,99 LUFS**. La tige complète décode en exactement **1 440 000 échantillons à 48 kHz**, sans écrêtage.

## Ducking réellement appliqué

- musique hors voix : **−3 dB** ;
- musique sous voix : **−10 dB** ;
- profondeur : **−7 dB** ;
- attaque : **120 ms**, linéaire en dB ;
- relâchement : **450 ms**, linéaire en dB ;
- durée à pleine réduction : **14,040 s** ;
- durée cumulée des rampes : **2,280 s** ;
- SFX : **aucun**.

La courbe échantillonnée à 10 ms se trouve dans `output/t1-voice-music-v1/T1_ducking_automation_10ms.csv`; sa visualisation est `T1_ducking_voice_timeline.png` dans le même dossier.

## Mesures des quatre rendus

| ID | Musique | WAV LUFS | WAV dBTP | AAC LUFS | AAC dBTP | Voix/musique active | Écrêtage |
|---:|---|---:|---:|---:|---:|---:|---:|
| 239426 | Go Down | −16,31 | −1,98 | −16,34 | −1,71 | +10,92 dB | 0 |
| 464383 | ALONE | −16,21 | −1,99 | −16,24 | −1,89 | +10,45 dB | 0 |
| 406552 | PAUSE | −16,33 | −1,99 | −16,35 | −1,58 | +8,81 dB | 0 |
| 178406 | Match Out | −16,17 | −1,99 | −16,21 | −1,83 | +11,15 dB | 0 |

Le proxy d’intelligibilité est le rapport énergétique voix/musique calculé sur des fenêtres de 20 ms où la voix dépasse −38 dBFS, avant mastering. Les quatre variantes dépassent le seuil de contrôle fixé à **+4 dB**. Ce proxy ne remplace pas une écoute humaine de la diction, du timbre et du confort musical.

Chaque MP4 contient exactement **900 images à 30 i/s**, une piste H.264 720 × 1280 inchangée et une piste AAC stéréo 48 kHz. La durée conteneur est **30,000 s** pour les quatre variantes. Le flux vidéo encodé est byte-identique à celui du master silencieux dans les quatre fichiers (`SHA-256 07db529e…526e`).

## Livrables d’écoute

Dossier : `output/t1-voice-music-v1/`

- `T1_voice_music_239426.mp4` / `.mp3` / `.wav`
- `T1_voice_music_464383.mp4` / `.mp3` / `.wav`
- `T1_voice_music_406552.mp4` / `.mp3` / `.wav`
- `T1_voice_music_178406.mp4` / `.mp3` / `.wav`
- `T1_voice_music_listening_board.html` — les quatre MP3 réunis sur une planche autonome ;
- `T1_voice_music_validation.json` — mesures complètes, empreintes et sondes vidéo.

## Intégration moteur

Le sidecar `config/T1_special_menu_voice_mix_v1_0_0.json` est pris en charge par `adapter/t1_adapter.py`. Avec `--enable-music --enable-voice`, le plan de rendu référence la tige voix locale, les quatre placements, les gains −3/−10 dB, les temps d’attaque et de relâchement, et le rapport de validation. Le montage visuel et les données commerçant restent inchangés.

Reconstruction reproductible :

```bash
python3 audio/scripts/mix_t1_voice_music_v1.py \
  --preview-dir output/t1-voice-music-v1
```

Deux reconstructions consécutives ont produit des empreintes SHA-256 byte-identiques sur les 22 fichiers contrôlés (**REPRODUCIBILITY PASS**). La preuve est dans `reports/T1_voice_music_v1_reproducibility.json`.

Le rapport machine faisant foi est `reports/T1_voice_music_v1_validation.json`.
