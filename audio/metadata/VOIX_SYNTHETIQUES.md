# Voix de la démonstration — déclaration et conditions

## Ce que sont ces quatre fichiers

`audio/voice/voix_fr_scene1.wav` … `voix_fr_scene4.wav` sont des **voix de synthèse** (texte → parole) en français.

- **Ce ne sont pas** des enregistrements d'un commerçant réel, ni l'imitation d'une personne identifiable.
- **Une seule identité vocale** est utilisée pour les quatre prises (même voix, même débit, même couleur), afin qu'on
  entende la même personne dans les quatre scènes.
- Aucun sous-titre, aucune transcription, aucune traduction n'est produite : le son est livré seul, conformément à la consigne.
- Les voix sont générées avec l'outil de synthèse vocale de la plateforme **Arena.ai (Agent Mode)** : voix masculin,
  usage conversationnel, français. La voix obtenue est un modèle de synthèse fourni par la plateforme ; ses conditions
  d'utilisation sont celles de la plateforme et doivent être vérifiées avant toute diffusion commerciale à grande échelle.
  Aucune bibliothèque tierce, aucun enregistrement d'acteur, aucun « clonage » de voix réelle n'a été utilisé.

## Textes exacts (inchangés)

| Fichier | Scène | Texte prononcé | Durée du fichier |
|---|---|---|---|
| `voix_fr_scene1.wav` | 1/4 (0–6 s) | « Voici notre burger maison, préparé pour vous. » | 3,019 s |
| `voix_fr_scene2.wav` | 2/4 (6–14 s) | « Regardez le pain doré, la garniture et tous les détails. » | 4,516 s |
| `voix_fr_scene3.wav` | 3/4 (14–21 s) | « On vous le sert tout juste préparé. Venez le découvrir ! » | 3,448 s |
| `voix_fr_scene4.wav` | 4/4 (21–30 s) | « Retrouvez Maquis Démo à Arconville. Pour commander, contactez-nous sur WhatsApp. » | 4,435 s |

## Placement dans le montage

| Scène | Fenêtre | Départ de la voix | Fin de la voix | Marge restante |
|---|---|---|---|---|
| 1 | 0,00 → 6,00 s | 1,20 s | 4,22 s | 1,78 s de respiration |
| 2 | 6,00 → 14,00 s | 6,80 s | 11,32 s | 2,68 s |
| 3 | 14,00 → 21,00 s | 14,70 s | 18,15 s | 2,85 s |
| 4 | 21,00 → 30,00 s | 21,80 s | 26,24 s | 3,76 s, dont le CTA texte (26,5–30 s) sans voix |

La voix ne chevauche jamais les trois transitions (6, 14 et 21 s) : elle démarre 0,7 à 0,8 s après chaque coupe.

## Traitement appliqué

- normalisation de chaque prise à une crête de −3 dBFS ;
- fondu d'entrée/sortie très court pour éviter les clics ;
- aucune égalisation corrective agressive (la voix reste naturelle) ;
- ducking de la musique de −10 dB sous la voix (voir `audio/sync/synchro_T1_demo.md`).
