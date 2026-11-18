# T1 — Contrat d’intégration des 12 écrans

## Réponse directe

Les douze écrans correspondent à **4 scènes × 3 états stables** :

- **A — Guide** : le commerçant lit la consigne puis appuie sur `COMMENCER À FILMER` ;
- **B — Enregistrement** : la fiche disparaît entièrement ; seuls la caméra, le chrono et la progression restent visibles ;
- **C — Validation** : la prise est relue avec le son ; le commerçant choisit `REFAIRE` ou valide.

La planche `ui-screens/planche_12_etats.png` sert uniquement de preuve visuelle. La source destinée au programmeur est désormais le JSON autonome :

`config/T1_special_menu_reference_v3_1.json#/implementation_handoff`

Ce n’est pas un contrat de maquette. Il décrit les données, les états, les événements, les fichiers produits et le passage au moteur de rendu.

## Les 12 écrans dans le JSON

| Nº | `screen_id` | Ce qui est affiché | Sortie / action |
|---:|---|---|---|
| 1 | `T1_CAPTURE_S1_A_GUIDE` | Scène 1/4, 6 s, LE PLAT, consigne, à filmer, à éviter, voix, exemple | `COMMENCER À FILMER` |
| 2 | `T1_CAPTURE_S1_B_RECORDING` | caméra + chrono 0:00→0:06 + progression | écrit `captures.S1.uri`, arrêt automatique |
| 3 | `T1_CAPTURE_S1_C_REVIEW` | PRISE 1 · 0:06, lecture avec le son | `REFAIRE` ou scène 2A |
| 4 | `T1_CAPTURE_S2_A_GUIDE` | Scène 2/4, 8 s, LE DESSUS ET LES DÉTAILS, contenus guidés | `COMMENCER À FILMER` |
| 5 | `T1_CAPTURE_S2_B_RECORDING` | caméra + chrono 0:00→0:08 + progression | écrit `captures.S2.uri`, arrêt automatique |
| 6 | `T1_CAPTURE_S2_C_REVIEW` | PRISE 2 · 0:08, lecture avec le son | `REFAIRE` ou scène 3A |
| 7 | `T1_CAPTURE_S3_A_GUIDE` | Scène 3/4, 7 s, LA PERSONNE QUI SERT, contenus guidés | `COMMENCER À FILMER` |
| 8 | `T1_CAPTURE_S3_B_RECORDING` | caméra + chrono 0:00→0:07 + progression | écrit `captures.S3.uri`, arrêt automatique |
| 9 | `T1_CAPTURE_S3_C_REVIEW` | PRISE 3 · 0:07, lecture avec le son | `REFAIRE` ou scène 4A |
| 10 | `T1_CAPTURE_S4_A_GUIDE` | Scène 4/4, 9 s, LE LIEU ET LE CONTACT, contenus guidés | `COMMENCER À FILMER` |
| 11 | `T1_CAPTURE_S4_B_RECORDING` | caméra + chrono 0:00→0:09 + progression | écrit `captures.S4.uri`, arrêt automatique |
| 12 | `T1_CAPTURE_S4_C_REVIEW` | PRISE 4 · 0:09, lecture avec le son | `REFAIRE` ou `VOIR MON MONTAGE` |

Un décompte transitoire `3 · 2 · 1` relie A à B. Il n’est pas compté comme treizième écran et n’est jamais écrit dans le fichier filmé.

## Chemin complet pour l’application

```text
Formulaire commerçant
  └─ merchant_payload { nom, produit, prix, whatsapp, quartier, accroche? }
       └─ 12 écrans guidés
            ├─ captures.S1.uri — 6 000 ms, image + voix
            ├─ captures.S2.uri — 8 000 ms, image + voix
            ├─ captures.S3.uri — 7 000 ms, image + voix
            └─ captures.S4.uri — 9 000 ms, image + voix
                 └─ RenderJob T1 V3.1
                      └─ MP4 720×1280, 30 fps, 900 images, 30 s
```

### Champs commerçant

Le JSON impose exactement les six champs universels :

- obligatoires : `nom`, `produit`, `prix`, `whatsapp`, `quartier` ;
- facultatif : `accroche` ;
- `additionalProperties: false` : aucun champ obligatoire caché ne peut être ajouté.

Chaque champ contient ses limites, sa normalisation éventuelle et ses cibles graphiques (`G01` à `G05`).

### Fichiers vidéo

Le contrat `capture_payload_schema` exige quatre URI lisibles par l’application :

| Slot | Durée exacte | Audio | Remappage temps |
|---|---:|---|---|
| `captures.S1` | 6 000 ms | oui | identité |
| `captures.S2` | 8 000 ms | oui | identité |
| `captures.S3` | 7 000 ms | oui | identité |
| `captures.S4` | 9 000 ms | oui | identité |

## Ce que lit directement le programmeur

Dans `implementation_handoff` :

- `runtime_order` : ordre formulaire → capture → rendu ;
- `merchant_payload_schema` : validation des informations saisies ;
- `capture_payload_schema` : validation des quatre fichiers ;
- `state_definitions` : règles communes A/B/C ;
- `screens[0..11]` : chaque écran résolu, son texte, ses composants, ses actions et sa preuve PNG ;
- `navigation_rules` : reprise, retour, suppression et validation ;
- `renderer_handoff` : liaisons vers les graphismes et les quatre scènes ;
- `renderer_handoff.job_example` : objet prêt à convertir en DTO Android ;
- `android_mapping` : modèles, événements et point d’entrée recommandés ;
- `acceptance_gates` : règles testables avant livraison.

## Invariants

- le guide `capture-guide/consignes_T1.json` reste octet pour octet inchangé ;
- les textes des quatre écrans A sont résolus depuis cette source, jamais recopiés à la main dans l’application ;
- aucune consigne ni information commerçant n’apparaît pendant B ;
- la voix est enregistrée et relue dans C ;
- aucun sous-titre n’est créé ;
- la V3 visuelle et son MP4 restent inchangés ;
- V3.1 ajoute uniquement le contrat d’intégration explicite.
