# Synchronisation de la démonstration T1 — musique, voix, effets

Fichier vidéo de référence : `output/output_T1_sans_voix_v4_demo.mp4` (30 s, 720 × 1280, 30 i/s), qui reprend la
structure mesurée de la V3.1 (`audio/video_edit_analysis_T1.md`).
Mixages livrés : `audio/synced/v2/mix_A.wav` (proposition A, recommandée) et `mix_B.wav` (alternative),
puis `output/output_T1_audio_demo_A.mp4` et `output/output_T1_audio_demo_B.mp4`.

## 1. Grille

- 120 BPM, 4/4 → **une noire = 0,500 s**, **une mesure = 2,000 s**, 15 mesures = 30,000 s.
- Toutes les coupes du montage tombent sur une noire (2,0 · 3,5 · 6,0 · 8,5 · 11,0 · 14,0 · 16,5 · 18,5 · 21,0 · 23,5 · 26,5 · 30,0 s) :
  tempo conservé, aucune modification de spécification.

## 2. Structure musicale et sections de la vidéo

| Section vidéo | Mesures | Traitement musical (A) | Traitement musical (B) |
|---|---|---|---|
| 0 – 6 s (S1, le plat) | 1–3 | intro : kick léger, shaker, kalimba, nappe qui entre | tambours + woodblock, balafon lent |
| 6 – 14 s (S2, détails) | 4–7 | groove complet, claps, basse ronde, balafon | djembé complet, basse discrète |
| 14 – 21 s (S3, plus sombre à l'image) | 8–10,5 | mélodie descendue d'une octave, nappe filtrée à 480 Hz | motif aéré, balafon grave |
| 21 – 30 s (S4, lieu + CTA) | 11–15 | montée, accent harmonique à 21,0 et 26,5 s, impact grave à 28,5 s | agogo à 21,0 s, tambour à 26,5 s, impact à 28,5 s |

Fondu final : 28,50 → 30,00 s.

## 3. Voix (4 prises séparées)

| Scène | Voix | Fenêtre scène | Départ | Fin | Chevauche une transition ? |
|---|---|---|---|---|---|
| 1 | `voix_fr_scene1.wav` | 0–6 s | 1,20 s | 4,22 s | non (coupe à 6,0 s) |
| 2 | `voix_fr_scene2.wav` | 6–14 s | 6,80 s | 11,32 s | non (coupe à 14,0 s) |
| 3 | `voix_fr_scene3.wav` | 14–21 s | 14,70 s | 18,15 s | non (coupe à 21,0 s) |
| 4 | `voix_fr_scene4.wav` | 21–30 s | 21,80 s | 26,24 s | non ; laisse le CTA texte seul de 26,5 à 30 s |

## 4. Effets — uniquement là où une action est visible

| Temps | Effet | Action visible qui le justifie |
|---|---|---|
| 2,10 s | assiette posée (porcelaine + table) | dans S1, la main du serveur pose l'assiette sur la table |
| 28,30 s | même matière, plus bas | dans S4, une main pose une tasse sur le comptoir |
| continu | ambiance de salle à −32 dB | la salle du restaurant est visible du début à la fin |

**Effets volontairement non utilisés** (aucune action ne les justifie dans la vidéo) : glissement de couverts « transition »,
cloche/agogo en tant qu'effet, kalimba « CTA », balafon « prix », **grésillement de braise** (aucune cuisson à l'image).
Aucun whoosh, pop ou ding n'est utilisé de façon systématique.

## 5. Les 11 repères V6.2

Les repères imposés restent la référence de synchronisation. Ce qui sonne à chaque repère est indiqué honnêtement :

| Repère | Ce qui se passe à l'image | Ce qui sonne réellement |
|---|---|---|
| 5,90 s | dernière image avant le whip pan | respiration musicale (fin de phrase) |
| 6,50 s | début S2 + apparition du lockup produit/prix | accent musical + voix 2 |
| 7,34 s | détail du plat | aucun effet dédié |
| 8,90 s | changement de plan interne | aucun effet (pas de whoosh) |
| 13,90 s | dernière image avant la poussée directionnelle | fin de phrase musicale |
| 16,90 s | visage de la personne qui mange | aucun effet (pas de son de bouche) |
| 18,34 s | prix plein écran | accent musical (pas de « ding ») |
| 20,90 s | dernière image avant le mask reveal | fin de phrase |
| 21,50 s | apparition de l'adresse | accent musical + voix 4 |
| 23,90 s | plan de la rue/de l'entrée | ambiance seule |
| 26,50 s | apparition du CTA WhatsApp | accent musical (pas de notification) |

Les repères restent donc **11 et inchangés** : ce sont les *effets sonores* qui ont été réduits à ce qui est visible,
la synchronisation musicale prenant le relais là où un effet aurait été gratuit.

## 6. Ducking (V6.2, inchangé)

Seuil −26 dBFS (enveloppe RMS 10 ms) · lookahead 80 ms · attaque 60 ms · hold 200 ms · relâchement 400 ms ·
profondeur −10 dB (musique −6 → −16 dB sous la voix). Durée totale duckée mesurée : **14,85 s**.

## 7. Reproduction

```bash
cd audio/scripts
python3 build_music_v2.py     # 2 musiques originales + stems
python3 mix_v2.py             # voix + musique + effets + ducking + mastering
python3 qc_v2.py              # mesures et contrôle du MP4 livré
```
