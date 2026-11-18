# T1 Special Menu — paquet de gabarit v1.0.0, phase silencieuse

## Statut

Ce paquet ferme à 100 % le périmètre **gabarit** avant la calibration musicale. Il ne remplace ni la maquette de l’application ni le serveur. Il fournit à l’agent intégrateur un contrat autonome pour comprendre, valider et exécuter T1 sans décision créative cachée.

- rendu visuel : V3 approuvée, inchangée ;
- saisie : six champs universels ;
- capture : quatre scènes et douze écrans ;
- assemblage : 900 images, 30 fps, 30 secondes ;
- exécution cible : hors ligne sur téléphone Android de 2 Go ;
- musique : différée ;
- SFX : aucun, conformément à la grammaire de la référence approuvée ;
- serveur de rendu distant : interdit par le profil T1.

## 1. Point d’entrée unique

Le fichier canonique est :

`config/T1_special_menu_template_v1_0_0.json`

Il conserve toute la recette visuelle V3.1 et ajoute :

- `media_ingest_contract` ;
- `execution_contract` ;
- `render_protocol` ;
- `error_catalog` ;
- `conformance_contract` ;
- `audio_policy`.

Le manifeste racine est :

`packages/t1-special-menu-v1/manifest.json`

L’agent commence par vérifier ce manifeste, puis charge le fichier canonique.

## 2. Contrats formels

| Contrat | Rôle |
|---|---|
| `schemas/T1_template_package.schema.json` | structure complète du gabarit |
| `schemas/T1_render_job.schema.json` | entrée obligatoire du moteur |
| `schemas/T1_render_result.schema.json` | résultat réussi |
| `schemas/T1_render_error.schema.json` | erreur normalisée et récupérable |

Les exemples conformes se trouvent dans `fixtures/t1-special-menu/`.

## 3. Contrat média

Le moteur accepte un fichier MP4 H.264/AVC par scène :

| Scène | Images utilisées | Durée | Tolérance d’enregistreur |
|---|---:|---:|---:|
| S1 | 180 | 6 000 ms | au plus 1 image finale supplémentaire |
| S2 | 240 | 8 000 ms | au plus 1 image finale supplémentaire |
| S3 | 210 | 7 000 ms | au plus 1 image finale supplémentaire |
| S4 | 270 | 9 000 ms | au plus 1 image finale supplémentaire |

Règles :

- 30 fps constants ;
- portrait 9:16 après application des métadonnées de rotation ;
- 540×960 minimum, 720×1280 préféré, 1080×1920 maximum ;
- aucun retiming, aucune interpolation et aucun frame blending ;
- seule une image finale produite en trop par l’enregistreur peut être retirée ;
- une prise trop courte est rejetée ;
- la voix commerçant reste à 1,0× ;
- HDR et codecs non déclarés sont rejetés explicitement.

## 4. Téléphone Android 2 Go, entièrement hors ligne

Profil : `profiles/T1_android_offline_2gb.json`.

### Moteur recommandé

Le moteur principal recommandé est :

`AndroidX Media3 Transformer + MediaCodec + un GlEffect personnalisé`

Ce choix conserve :

- décodage et encodage matériels ;
- un seul décodeur ;
- une seule séquence S1→S4 ;
- tous les traitements sur le téléphone ;
- aucune dépendance à un serveur de rendu.

### FFmpeg

FFmpeg n’est **pas requis** et n’est pas le moteur principal du paquet. Un port FFmpeg reste techniquement possible, mais il ne sera accepté que s’il passe exactement le même paquet de conformité. Cela évite d’imposer un gros binaire natif et des filtres logiciels coûteux aux téléphones de 2 Go.

### Budgets

- un décodeur ;
- un encodeur ;
- un rendu simultané ;
- trois images décodées conservées au maximum ;
- deux intermédiaires RGBA plein format au maximum ;
- cible mémoire : 220 Mo ; limite contractuelle : 256 Mo ;
- espace libre avant rendu : 350 Mo ;
- sortie H.264 720×1280, 30 fps, 5 Mbit/s cible.

### Repli visuel approuvé

Sur le profil 2 Go :

- les textes sont prérastérisés ;
- bloom et douceur gaussienne utilisent un intermédiaire demi-résolution ;
- flash, sweep et couleur sont combinés dans une seule passe GL ;
- le grain peut être désactivé ;
- le contraste local peut être simplifié.

Ne peuvent jamais être dégradés : les coupes, les durées, les mouvements, les textes, les polices, le prix, les visages, la couleur principale et le CTA final.

## 5. Protocole local

Le moteur reçoit un `RenderJob`, émet les états :

`VALIDATING → ANALYZING → RENDERING → ENCODING → FINALIZING → COMPLETED`

Il retourne soit un `RenderResult`, soit un `RenderError` typé. Les codes couvrent notamment : données invalides, scène absente, codec non pris en charge, durée incorrecte, voix absente, média corrompu, espace insuffisant, appareil incompatible, checksum erroné, annulation et sortie non conforme.

Le même `idempotency_key` doit produire le même résultat logique sans dupliquer le travail.

## 6. Conformité

`conformance/T1_special_menu_golden_v1.json` verrouille :

- les quatre vidéos d’entrée et leurs hashes ;
- le master V3 et son SHA-256 ;
- douze images-clés couvrant ouverture, frontières de scènes, CTA et dernière image ;
- les treize coupes ;
- les limites de comparaison pour un port Android ;
- les contrats temporels identité.

Le hash MP4 exact est exigé uniquement du moteur Python de référence. Un encodeur matériel Android peut produire un conteneur binaire différent ; il doit alors respecter les tolérances visuelles et toutes les contraintes sémantiques.

## 7. Audio

Cette livraison ferme volontairement la phase silencieuse :

- la place temporelle de la voix commerçant est réservée ;
- aucun sous-titre automatique ;
- musique différée vers une bibliothèque future de 20 à 30 modèles calibrés ;
- aucun SFX pour T1, car la référence approuvée ne possède pas de grammaire SFX à reproduire.

L’ajout musical futur ne modifiera ni les douze écrans, ni le montage, ni la typographie, ni les effets visuels.

## 8. Commandes

```bash
PYTHONPATH=. python3 tools/build_t1_template_package_v1.py
PYTHONPATH=. python3 tools/validate_t1_template_package.py --require-golden
PYTHONPATH=. python3 tools/build_t1_template_package_v1.py \
  --bundle /tmp/T1_special_menu_template_v1_0_0.zip
```

Le ZIP produit est autonome : manifeste, JSON canonique, schémas, profil 2 Go, fixtures, polices et licences, preuves, moteur de référence et golden master.
