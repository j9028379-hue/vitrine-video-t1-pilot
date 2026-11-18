# Comparaison V3.1 / Clôture V4 / V5

> Toutes les valeurs de la section 1 sont **mesurées sur les fichiers MP4** (décodage image par
> image). Aucune métrique n'est reprise d'un rapport antérieur. Les trois masters proviennent de
> moteurs différents : la comparaison porte sur les mêmes instants de la publicité, **pas** sur
> des sources identiques. Les planches sont dans `reports/comparaison_V3_V4_V5/`.

## 1. Comparaison technique mesurée

| Mesure | V3.1 | Clôture V4 | V5 |
|---|---|---|---|
| Images | 900 | 900 | 900 |
| Durée (s) | 30.0 | 30.0 | 30.0 |
| Cadence | 30.0 | 30.0 | 30.0 |
| Résolution | 720×1280 | 720×1280 | 720×1280 |
| Octets | 9291554 | 9801769 | 11924150 |
| Images identiques (total) | 0 | 0 | 0 |
| Suite max d'images identiques | 0 | 0 | 0 |
| Images quasi identiques (MAD < 0,5) | 16 | 161 | 84 |
| Suite max quasi identique | 1 | 10 | 3 |
| Suite max par scène | [0, 0, 0, 0] | [0, 0, 0, 0] | [0, 0, 0, 0] |
| Différence moyenne inter-images | 3.557 | 4.761 | 6.034 |
| Dernière seconde de chaque scène | [4.131, 4.197, 1.342, 1.459] | [3.962, 4.562, 5.156, 0.358] | [4.726, 8.382, 8.871, 4.557] |
| Mouvement moyen (px) | 0.718 | 1.5 | 0.93 |
| Luminance moyenne | 94.1 | 76.5 | 103.2 |
| SHA-256 | 33abc850265242b91fb61284e7e7649cc92b7750414212fa8f05ed4e455c2039 | b202514af94fa204d8ddda769682f870d336154c36b06c3a9264ab5d6625a632 | 35d0e9f50bc2275ee2536431b23bf27e36a1804098f3aa3438da78dead79ac6e |

### Lecture

- **Images identiques au pixel** : V3.1 0, V4 0, V5 0 (l'encodeur introduit du bruit : cette mesure seule ne détecte pas un gel).
- **Images quasi identiques (MAD < 0,5)** : V3.1 16, V4 161, V5 84 ; suite la plus longue : V3.1 1, V4 10, V5 3.
- **Suite la plus longue** : V3.1 0, V4 0, V5 0 (seuil contractuel : moins de 4).
- **Mouvement moyen** : V3.1 0.718 px, V4 1.5 px, V5 0.93 px.
- Les images identiques du V5 proviennent du ralentissement du cœur de plan (vitesse < 1), jamais d'un gel de fin : elles ne dépassent jamais deux images consécutives.

## 2. Planches synchronisées

- `reports/comparaison_V3_V4_V5/planche_ouverture.png`
- `reports/comparaison_V3_V4_V5/planche_première_transition.png`
- `reports/comparaison_V3_V4_V5/planche_produit.png`
- `reports/comparaison_V3_V4_V5/planche_prix.png`
- `reports/comparaison_V3_V4_V5/planche_scène_humaine.png`
- `reports/comparaison_V3_V4_V5/planche_dernière_transition.png`
- `reports/comparaison_V3_V4_V5/planche_packshot_final.png`

## 3. Analyse artistique (appréciation, séparée des mesures)

| Critère | V3.1 | Clôture V4 | V5 |
|---|---|---|---|
| Arrêter le défilement dès la 1re seconde | produit visible, ouverture douce | idem, image d'ouverture peu nette | punch-in d'entrée + enseigne dès l'image 2 ; **la netteté de la source 327 reste limitée en ouverture** |
| Mise en valeur du produit | bonne | bonne | meilleure : détail S2 et diptyque général/détail |
| Rythme | régulier | régulier, quelques plans étirés | attaque vive, cœur ralenti, relance avant chaque coupe |
| Fluidité | mouvement caméra entier (escalier) | sous-pixel partiel | sous-pixel complet, un seul échantillonnage |
| Variété visuelle | 3 transitions | 3 transitions | 6 transitions choisies selon le contenu |
| Cohérence des transitions | bonne | bonne | bonne, avec une justification par coupe |
| Lisibilité | texte crème sur fond variable | cartes opaques | cartes de verre + scrims mesurés ≥ 4,5:1 |
| Protection des sujets | aucune détection | aucune détection | visage et produit protégés par zones calculées |
| Progression commerciale | plat → détails → personne → lieu | idem | idem, avec prix au détail et CTA tenu jusqu'à l'image 899 |
| Force du CTA final | visible | visible puis effacé | carte + bouton empilés, **100 % jusqu'à 899** |

Ce que le V5 ne fait pas mieux, et qu'il faut dire :

- La **netteté d'ouverture** reste bornée par la prise 1 (606×1080, première seconde douce).
- La scène 3 (404×720) reste la moins définie des quatre : aucun upscale ne peut y remédier.
- Le ralentissement du cœur de plan crée quelques images répétées (49 au total, jamais plus de
  deux consécutives) : c'est un choix de rythme, pas un gel.

