# T1 — audit final de la migration musicale stricte

**Date : 18 novembre 2026**
**Statut local : PASS complet, golden stable inclus dans la validation locale**

## 1. Résultat fonctionnel

T1 utilise désormais quatre instrumentales propres dans l’ordre fermé suivant :

1. `t1_music_239426` — Go Down
2. `t1_music_464383` — ALONE
3. `t1_music_406552` — PAUSE
4. `t1_music_178406` — Match Out

L’état initial n’autorise que la piste 1. Chaque nouveau succès sélectionne et valide exclusivement le successeur exact `239426→464383→406552→178406→239426`. Un échec ou un QC refusé laisse l’état inchangé. Une sélection explicite ne peut ni répéter ni sauter une piste, y compris à l’état initial.

L’état persistant contient désormais `successful_render_jobs`. Ce registre conserve chaque association `render_job_id → music_id` réussie : le rejeu de tout ancien succès reste idempotent, même après un tour complet, et le même job ne peut jamais changer de piste. Les écritures sont atomiques sous verrou interprocessus; une validation concurrente hors séquence est rejetée sans mutation.

Aucun réseau, endpoint, Worker, bucket, téléchargement dynamique ou déploiement Cloudflare n’a été ajouté.

## 2. Contrats et artefacts mis à niveau

- `adapter/t1_adapter.py` : cycle exact, choix explicite strict, registre durable, échec sans mutation et sérialisation interprocessus.
- `config/T1_special_menu_music_pack_v1_0_0.json` : politique `exact_successor_only`, un seul candidat attendu et registre `successful_render_jobs`.
- `schemas/T1_music_pack.schema.json` : verrouillage de la nouvelle politique.
- `schemas/T1_music_selection_state.schema.json` : schéma du registre durable.
- `docs/T1_MUSIC_INTEGRATION.md` : suppression de l’ancien sélecteur par hash et description du cycle strict.
- `tests/test_t1_music_pack.py` : rejeu ancien après tour complet, saut explicite, concurrence par threads et par processus, échec sans mutation et fraîcheur du ZIP.
- `tools/validate_t1_music_pack.py` : contrôles fail-closed du cycle, de l’idempotence et des deux schémas.

## 3. Validation locale

| Contrôle | Résultat |
|---|---:|
| Tests musicaux ciblés | **20 PASS** |
| Suite brute complète | **113/113 PASS** |
| Validateur musical | **PASS** |
| Validateur du paquet avec golden exigé | **15/15 PASS** |
| Cycle CLI persistant | **PASS : 239426→464383→406552; échec inchangé** |
| Stress du cycle | **10 000 sélections exactes, 2 500 par piste** |
| Rejeu d’un ancien succès après 4 étapes | **PASS, aucune mutation** |
| Concurrence hors séquence | **PASS, une validation acceptée et l’autre rejetée** |
| Compilation Python | **PASS** |
| JSON suivis | **65/65 parsés** |
| YAML suivis | **2/2 parsés** |
| Schémas JSON suivis | **7/7 valides** |
| `git diff --check` | **PASS** |
| Scan de motifs de secrets | **PASS** |

La suite brute collecte 113 tests et les 113 passent avec une copie locale vérifiée du golden stable. Le fichier reste ignoré par Git et n’est pas ajouté au commit.

## 4. Bundle musical reproductible

Le bundle a été reconstruit deux fois consécutivement et les octets sont identiques :

- chemin : `packages/t1-special-menu-music-v1/t1-special-menu-afrobeat-amapiano-music-v1.zip`
- taille : **2 436 510 octets**
- SHA-256 : `b8b447592831e9a89adab45a61b32ad1ff43a4a09c80a232c7d34278071704e5`
- membres : **21**, aucun doublon
- configuration, adaptateur, schémas, outils et documentation embarqués : **identiques au checkout**
- `BUILD-MANIFEST.json` interne : tailles et SHA-256 vérifiés pour chaque membre

Le ZIP ne contient plus les anciennes versions du sélecteur, du schéma ou de la documentation.

## 5. Audit des références historiques

Aucune référence active au hash de `render_job_id`, aux trois candidates alternatives ou au mode « casino » ne subsiste dans l’adaptateur, les contrats, la documentation ou les rapports courants. La piste rejetée `573944` reste interdite et n’est ni sélectionnable ni embarquée.

Le fichier d’archives `audio/metadata/SHA256SUMS_audio.txt` référence 16 anciens dérivés générés et ignorés qui ne sont pas présents dans ce checkout; les 22 fichiers historiques présents correspondent à leurs sommes. Cet inventaire n’appartient pas au nouveau paquet musical et ne constitue pas un gate de sa migration.

## 6. Golden stable revalidé

Une copie locale du golden stable a été récupérée depuis le cache de travail antérieur puis vérifiée avant utilisation :

`output/output_T1_special_menu_reference_v3.mp4`

- taille : **20 276 905 octets** ;
- SHA-256 : `784bd77591508995822237bf8633d6ec50d245cac39afdca91f9b130296c50c7` ;
- vidéo : **720×1280, 30 i/s, 900 images, 30 s** ;
- 12 images-clés : **PASS**.

Le fichier est ignoré par Git. Il sert uniquement à fermer le gate local : suite brute **113/113 PASS** et validateur `--require-golden` **15/15 PASS**. Aucun remplacement de Release n’est effectué.

## 7. Publication

Au moment de cet audit, les changements sont uniquement locaux : **aucun commit, push, tag, déploiement production ou remplacement de Release n’a été effectué**.
