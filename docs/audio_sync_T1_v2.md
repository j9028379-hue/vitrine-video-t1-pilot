# Feuille de synchronisation sonore — T1 V2 (préparation uniquement)

Aucun son n'est généré, sélectionné ou intégré dans le rendu V2. Repères verrouillés à 30 i/s, 900 images, durée 30 s. Les plages de frames sont semi-ouvertes `[début, fin)`.

| Repère | Temps | Frames | Événement visuel synchronisable | Piste future suggérée |
|---|---:|---:|---|---|
| Ouverture food-first | 0,00 s | 0 | Gros plan burger, sans écran-titre statique | Départ musical immédiat, niveau modéré; ambiance cuisine très légère si validée |
| Signature / premier mot | 0,43 s | 13 | Le titre BURGER entre, puis MAISON à 0,63 s (frame 19) | Petit accent éditorial discret, pas de voix par défaut |
| Transition S1→S2 | 5,87–6,27 s | [176,188) | Whip-pan horizontal | Whoosh court, panoramique gauche→droite; attaque sur 176, relâche avant 188 |
| Accroche en séquence | 6,40 / 8,17 / 9,93 s | 192 / 245 / 298 | « CHAUD », « SERVI », « AUJOURD’HUI » se construisent par étapes | Trois accents feutrés espacés; aucun son culinaire sans action sonore justifiée |
| Préparation / speed ramp | 6,00–14,00 s | [180,420) | Accélération douce au milieu du mouvement source, ralenti relatif aux extrémités; trajectoire continue | Une texture culinaire très légère si elle correspond à l'image; pas de crépitement générique ajouté |
| Transition S2→S3 | 13,87–14,27 s | [416,428) | Directional push / zoom contrôlé vers la scène de service | Whoosh plus bas et plus court que le premier; synchronisé au push |
| Révélation du prix | 15,40 s | 462 | Carte « BURGER MAISON · 2 500 FCFA » se révèle | Accent de prix bref, rond et non agressif; point principal sur 462–471 |
| Transition S3→S4 | 20,87–21,27 s | [626,638) | Révélation diagonale avec ruban orange | Whoosh doux, timbre cohérent avec les deux transitions précédentes |
| Adresse | 21,40 s | 642 | Repère de localisation / adresse fictive | Pas de son obligatoire; éventuel accent léger uniquement si utile |
| CTA WhatsApp | 24,67 s | 740 | Entrée du bouton final WhatsApp | Tap/notification propriétaire très discrète, sans imiter une alerte réelle |
| Fin / hold CTA | 25,83–30,00 s | [775,900) | Nom du maquis fictif et action WhatsApp maintenus à l'écran | Résolution musicale à préparer après validation visuelle; laisser respirer les dernières secondes |

## Architecture audio à prévoir après validation

- Ambiance culinaire seulement sous des plans qui la justifient (préparation/service); ne pas suggérer des sons de cuisson absents de l'image.
- Un bus musical avec points de ducking aux trois transitions, à la révélation du prix et au CTA.
- Événements SFX exprimés en frames de sortie et attachés aux identifiants `TRANSITION_1`, `ACCROCHE_1..3`, `PRICE_REVEAL`, `CTA_WHATSAPP`; aucune heure approximative côté lecteur.
- La piste audio restera désactivée dans ce master; cette feuille n'est ni une piste ni une autorisation d'utiliser une œuvre musicale tierce.
