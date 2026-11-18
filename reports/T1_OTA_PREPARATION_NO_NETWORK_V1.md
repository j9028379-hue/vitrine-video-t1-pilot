# T1 — préparation catalogue OTA sans réseau et rotation musicale stricte persistante

**Statut : PASS — 18 novembre 2026**

Ce lot prépare les métadonnées de T1 pour un futur catalogue, sans intégrer d’OTA, de téléchargement, de dépendance Cloudflare ni de nouvelle ressource musicale. Les Releases stables existantes ne sont ni modifiées ni remplacées.

Le rapport machine faisant foi est `reports/T1_ota_preparation_no_network_v1_validation.json`.

## 1. Audit des Releases et choix des identifiants

### Release silencieuse stable

- Tag : `t1-special-menu-template-v1.0.0-silent`
- Commit cible : `cab2aa2a4a841341c9e84aeb08e243ea9baec0f4`
- JSON canonique publié : 84 151 octets, SHA-256 `5a742abf8307b6347d28e6eb7d540b8d17e88482c3548422affa8e54c38d7b1b`
- Schéma publié : SHA-256 `bfc7c9a781ce7071817aeed67938ec46aa6c1779840407446300a882a6395493`
- Manifest publié : SHA-256 `e1148f3d3fea0259072632b3a5e3d5db12340f3eb176b19cd8512329b2bd29c0`

### Successeur musical

- Tag : `t1-special-menu-music-v1.0.0`
- Catalogue publié : SHA-256 `2ddb781df3934a770bf3312a8a6c3f005d8bbf2ebe6beb08ca48164c68d18c81`
- Bundle publié : SHA-256 `4fba896ebee2181927edb07a92e182c7da72835430ce95a77945df7e07f4edf5`
- Direction livrée : Afrobeat/Amapiano, quatre variantes locales, cible 120 BPM.

L’audit du dépôt et des deux Releases n’a trouvé **aucun identifiant formel `audio_profile` préexistant**. L’identifiant sémantique retenu est donc :

```json
"audio_profile": "afrobeat_amapiano"
```

Il décrit l’ambiance réellement livrée. Il ne contient ni nom de piste, ni nom de MP3, ni version du catalogue musical. Le catalogue musical candidat expose désormais le même champ afin que la liaison soit vérifiable sans interpréter son nom de fichier ou son identifiant de paquet.

## 2. Métadonnées canoniques

Le début de `config/T1_special_menu_template_v1_0_0.json` porte maintenant :

```json
{
  "$schema": "../schemas/T1_template_package.schema.json",
  "schema_version": "2.1.0",
  "template_id": "T1",
  "version": "1.0.0",
  "audio_profile": "afrobeat_amapiano"
}
```

Séparation volontaire des notions :

- `schema_version: 2.1.0` versionne uniquement la forme du contrat JSON ;
- `template_id: T1` est l’identifiant court et stable du gabarit ;
- `version: 1.0.0` est la version du gabarit ;
- `audio_profile: afrobeat_amapiano` est un identifiant d’ambiance ;
- `id: restaurants_maquis_T1_special_menu_v1_0_0` reste l’identifiant interne historique du paquet ;
- le champ canonique historique `template_version` a été supprimé pour ne pas dupliquer `version`.

Le schéma strict `schemas/T1_template_package.schema.json` impose ces valeurs. Aucun identifiant de variante, ID Pixabay ou nom de fichier musical n’apparaît dans le JSON canonique.

## 3. Rotation musicale stricte 1 → 2 → 3 → 4

La rotation reste locale, hors ligne et reproductible :

1. **État initial** : `previous_variant_id` vaut `null`; seule la piste 1 peut être sélectionnée et validée.
2. **Rendus réussis suivants** : l’orchestrateur local conserve le `variant_id` du dernier rendu réussi.
3. L’adaptateur choisit uniquement le successeur exact dans l’ordre 1 → 2 → 3 → 4 → 1.
4. Un choix explicite ne peut que confirmer ce successeur exact; toute répétition ou tout saut est rejeté.
5. Un échec ou un QC refusé ne fait jamais avancer l’état.
6. Le registre durable `successful_render_jobs` rend idempotent le rejeu de tout ancien succès, même après un tour complet.
7. Les callbacks concurrents sont sérialisés; tout succès hors séquence est rejeté sans mutation.

Entrée CLI correspondante :

```text
--previous-music-variant <variant_id_du_dernier_rendu_réussi>
```

Le contrat est déclaré dans `config/T1_special_menu_music_pack_v1_0_0.json`, contrôlé par `schemas/T1_music_pack.schema.json` et exécuté par `adapter/t1_adapter.py`.

## 4. Lot musical préservé

La liste et l’ordre restent strictement :

1. `t1_music_239426`
2. `t1_music_464383`
3. `t1_music_406552`
4. `t1_music_178406`

Les quatre objets `tracks` sont **exactement identiques avant/après**, y compris fichiers, SHA-256, durée 30 s, cible 120 BPM, LUFS, true peak, gains −3/−10 dB et marqueurs de scènes. Le `quality_gate` est également identique.

`573944` reste uniquement dans la liste d’interdiction et n’est ni embarquée ni sélectionnable. Elle ne pourra revenir qu’après validation explicite de son certificat.

## 5. Invariants fonctionnels et résultat moteur

Comparaison sémantique avant/après :

- 4 scènes inchangées : 6 s, 8 s, 7 s, 9 s ;
- timeline : 900 images, 30 i/s, 30 s ;
- 12 écrans inchangés ;
- contrats média, champs commerçant, typographies, graphismes, transitions et chorégraphie inchangés ;
- audio calibré et quatre fichiers musicaux inchangés ;
- guide de capture inchangé ;
- aucun code OTA, réseau ou Cloudflare ajouté.

Le moteur canonique a accepté le JSON enrichi et a produit :

- 720 × 1280 ;
- 30 i/s ;
- 900 images ;
- 30,000 s ;
- SHA-256 `784bd77591508995822237bf8633d6ec50d245cac39afdca91f9b130296c50c7` ;
- 20 276 905 octets.

Lors de la validation historique consignée, ce rendu était **byte-identique au golden silencieux publié**. Une copie locale vérifiée du golden stable a ensuite fermé le gate final : taille, SHA-256, caractéristiques vidéo et 12 images-clés ont été revalidés. Le fichier reste ignoré par Git.

## 6. Validations

| Contrôle | Résultat |
|---|---:|
| Suite musicale ciblée | **20 tests réussis** |
| Suite complète brute avec golden stable vérifié | **113/113 PASS** |
| Validateur du paquet T1 avec `--require-golden` | **15/15 PASS** |
| Validateur du pack musical | **PASS** |
| Stress test de rotation stricte | **10 000 rendus, ordre exact répété 2 500 fois** |
| Répartition des quatre variantes | **2 500 chacune, 0 répétition adjacente** |
| Rejeu d’un ancien succès après un tour complet | **PASS, aucune mutation** |
| Concurrence hors séquence | **PASS, sérialisée et rejetée sans mutation** |
| Rebuild du bundle musical | **deux builds byte-identiques** |
| Golden MP4 historique | **PASS : 20 276 905 octets, SHA-256 et 12 images-clés revalidés** |

Bundle candidat reconstruit :

- `packages/t1-special-menu-music-v1/t1-special-menu-afrobeat-amapiano-music-v1.zip`
- 2 436 510 octets
- 21 membres, aucun doublon; code, schémas, configuration et documentation embarqués identiques au checkout
- SHA-256 `b8b447592831e9a89adab45a61b32ad1ff43a4a09c80a232c7d34278071704e5`

Ce bundle candidat n’écrase pas l’asset de la Release musicale stable. Le golden `output/output_T1_special_menu_reference_v3.mp4` a été fourni localement depuis le cache stable puis vérifié à 20 276 905 octets et au SHA-256 `784bd77591508995822237bf8633d6ec50d245cac39afdca91f9b130296c50c7`. Il reste ignoré par Git; aucune Release n’est remplacée.

## 7. Fichiers concernés

### Métadonnées et schémas

- `config/T1_special_menu_template_v1_0_0.json`
- `schemas/T1_template_package.schema.json`
- `config/T1_special_menu_music_pack_v1_0_0.json`
- `schemas/T1_music_pack.schema.json`
- `schemas/T1_music_selection_state.schema.json`

### Sélection et documentation

- `adapter/t1_adapter.py`
- `docs/T1_MUSIC_INTEGRATION.md`

### Construction, validation et tests

- `tools/build_t1_template_package_v1.py`
- `tools/validate_t1_template_package.py`
- `tools/validate_t1_music_pack.py`
- `tests/test_t1_template_package_v1.py`
- `tests/test_t1_music_pack.py`
- `reports/T1_template_package_v1_validation.json`

### Artefacts déterministes régénérés

- `packages/t1-special-menu-v1/manifest.json`
- `packages/t1-special-menu-music-v1/manifest.json`
- `packages/t1-special-menu-music-v1/t1-special-menu-afrobeat-amapiano-music-v1.zip`

## 8. Hors périmètre confirmé

Aucun endpoint, worker, bucket, URL de catalogue, téléchargement dynamique, signature OTA, logique Cloudflare ou dépendance réseau n’a été ajouté. Le lot se limite aux métadonnées prêtes pour un futur catalogue et à la rotation locale persistante strictement ordonnée.
