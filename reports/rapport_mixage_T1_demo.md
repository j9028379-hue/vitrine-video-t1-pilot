# Rapport de mixage — démonstration T1 « Restaurants et Maquis »

Date : 18 novembre 2026 · Livrables : `output/output_T1_audio_demo_A.mp4` (recommandé) et
`output/output_T1_audio_demo_B.mp4` (alternative) · Vidéo : `output/output_T1_sans_voix_v4_demo.mp4`
(V3.1 muette conservée intacte, SHA-256 `33abc850…`).

## 1. Ce qui a été fait, dans l'ordre

1. Analyse du fichier exporté réel (`audio/video_edit_analysis_T1.md`) : coupes mesurées à 5,93–6,13 / 13,97 / 21,03 s,
   12 plans, textes de 0,5 à 30 s, luminosité de la scène 3 nettement plus basse.
2. Note de tendances musicales datée et sourcée (`audio/note_tendances_musicales_afrique_ouest_2026.md`) → **deux**
   propositions, pas plus : **A** afro-maquis teinté adjapiano (recommandée), **B** gangan acoustique (alternative).
3. Composition et synthèse des deux musiques originales à 120 BPM / 30 s (`audio/scripts/build_music_v2.py`).
4. Synchronisation voix / musique / effets (`audio/sync/synchro_T1_demo.md`).
5. Mixage et mastering (`audio/scripts/mix_v2.py`) puis contrôle objectif (`audio/scripts/qc_v2.py`).

## 2. Réglages (V6.2 conservée)

| Élément | Valeur |
|---|---|
| Musique | −6 dB, duckée à −16 dB sous la voix (−10 dB de profondeur), fondu 28,50 → 30,00 s |
| Effets | −5 dB (−8 dB sous la voix) — **2 événements seulement**, tous justifiés par une action visible |
| Ambiance de salle | −32 dB, continue (la salle est visible du début à la fin) |
| Voix | 4 fichiers séparés, crête −3 dBFS chacun, départs 1,20 / 6,80 / 14,70 / 21,80 s |
| Ducking | seuil −26 dBFS, lookahead 80 ms, attaque 60 ms, hold 200 ms, relâchement 400 ms |
| Compression | une seule fois avant la boucle de gain : seuil −20 dB, ratio 2,6 |
| Mastering | cible −16 LUFS, plafond d'échantillon −3,6 dBFS (3 passes gain/limiteur) |

## 3. Mesures (contrôle objectif)

| Mesure | Piste A | Piste B |
|---|---|---|
| LUFS intégré (stéréo) | **−16,02** | −16,01 |
| True peak | −2,72 dBTP | −2,72 dBTP |
| Crête d'échantillon | −3,6 dBFS | −3,6 dBFS |
| Écrêtage (échantillons ≥ 0,999) | 0 | 0 |
| Décalage continu (DC) | 0,0001 | 0,0001 |
| Durée duckée | 14,85 s (dont 12,47 s à pleine profondeur) | idem |
| Niveau musique hors voix / sous voix | −33,7 / −41,0 dBFS | −33,3 / −40,0 dBFS |
| Effet 2,10 s (assiette) | présent, +17,2 dB au-dessus du niveau antérieur | idem |
| Effet 28,30 s (tasse) | présent, +14,2 dB | idem |
| Audio dans le MP4 livré | −19,07 LUFS mono, TP −2,64 dB, écart au WAV −0,03 dB | −19,05 LUFS mono, TP −2,62 dB |
| Décalage audio / vidéo mesuré | **0,0 ms** | 0,0 ms |

Niveaux par section (piste A) : 0–6 s −16,11 LUFS · 6–14 s −15,82 · 14–21 s −16,28 · 21–28,5 s −15,34 · 28,5–30 s −25,13 (fondu).

## 4. Ce que l'analyse de la vidéo a changé par rapport à l'ancienne version audio

- **Deux musiques neuves**, l'ancienne identité sonore n'est pas reprise : nouvelle grille (i–VI–III–VII en La mineur),
  nouveaux motifs, nouvelle instrumentation.
- **Effets réduits de 13 à 3 matières sonores** : plus de glissements de couverts "transition", plus de cloche, plus de
  "kalimba CTA", et surtout **plus aucun grésillement de braise** (la vidéo ne montre aucune cuisson).
- **Accents musicaux** placés sur les trois transitions et sur le CTA, à la place des whoosh/pop/ding systématiques.
- Scène 3 plus sombre à l'image → nappe filtrée plus bas et mélodie descendue d'une octave pour ne pas écraser l'image.

## 5. Limite à connaître : le mixage n'a pas été écouté par un humain

Je ne peux pas écouter le résultat. Le travail a donc été vérifié **objectivement** (niveaux, crêtes, écrêtage, DC,
détection des plages de voix, profondeur de ducking, présence des effets, fidélité du MP4, latence) et **pas**
subjectivement. Avant diffusion, il faut une écoute réelle, même au téléphone, avec cette liste de contrôle :

1. la voix est-elle toujours intelligible sur les quatre scènes, et notamment pendant les percussions ?
2. la musique porte-t-elle sans masquer le prix (6,5–9,5 s et 18–20,5 s) et l'adresse (21,5–25,5 s) ?
3. les deux effets (2,10 s et 28,30 s) sont-ils crédibles et discrets, ou trop « bruitage » ?
4. la fin (28,5 → 30 s) donne-t-elle une sensation de chute propre, sans coupure sèche ?
5. sur haut-parleur de téléphone, les graves de la basse ne brouillent-ils pas la voix ?

Si un point ne passe pas, les corrections ponctuelles sont dans `audio/scripts/mix_v2.py` (gains V6.2, `VOIX_PLAN`,
`EFFETS_PLAN`) sans toucher à la spécification.

## 6. Décision recommandée

**Piste A** (« afro-maquis 120 ») : plus proche de ce qui se danse aujourd'hui au Bénin (adjapiano), 120 BPM respecté,
médiums laissés libres pour la voix. La piste B reste disponible si le client veut plus acoustique.
