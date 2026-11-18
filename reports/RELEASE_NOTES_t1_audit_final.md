# T1 — Audit final : parcours de capture et montage (30 s)

Cette release contient les **fichiers binaires** de l'audit final. Les liens ci-dessous sont des liens de téléchargement direct : aucune connexion au compte propriétaire n'est nécessaire.

## Vidéos

| Fichier | Contenu | Format |
|---|---|---|
| `output_T1_master_final.mp4` | **Master final** — 12 plans, 4 prises réelles, moteur piloté par le plan, muet | 720×1280, 30 i/s, 30,000 s, 900 images |
| `output_T1_sans_voix_v3_1.mp4` | **Référence visuelle approuvée V3.1** (inchangée) | 720×1280, 30 i/s, 30,000 s |
| `output_T1_sans_voix_v4_demo.mp4` | Version V4 démo produite par l'ancien moteur | 720×1280, 30 i/s, 30,000 s |
| `output_T1_sans_voix_v3.mp4` | Version V3 conservée pour comparaison | 720×1280, 30 i/s |
| `output_T1_sans_voix_v2.mp4` | Version V2 conservée pour comparaison | 720×1280, 30 i/s |

Tous les masters sont **muets** : l'audio est hors périmètre de cette mission.

## Parcours de capture

| Fichier | Contenu |
|---|---|
| `ui-screens_et_planche.zip` | 23 PNG : les 12 états (4 scènes × A/B/C), la planche des 12 états, montage, publicité, fin, navigation, preuves 360 px et 430 px |

## Audit du montage

| Fichier | Contenu |
|---|---|
| `T1_AUDIT_FINAL_PARCOURS_ET_MONTAGE.md` | Rapport final en 12 sections |
| `planches_audit_montage.zip` | Planches de contrôle : 12 plans, transitions exécutées, 8 blocs graphiques, comparaisons V3.1 / master final |
| `execution_manifest_v4.json` | Journal d'exécution : par plan — source, fenêtre d'images, mouvement, paramètres, transition, blocs actifs |
| `final_master_checks.json` | Contrôle du MP4 : 24 points de mesure (indice source + zoom), conteneur, silence, images noires |

## Empreintes SHA-256

```
97c3477d8043b3c1b8f5f11144d8b9f1aa65a803c0f5aa68a7747d6fb27dea91  output_T1_master_final.mp4
33abc850265242b91fb61284e7e7649cc92b7750414212fa8f05ed4e455c2039  output_T1_sans_voix_v3_1.mp4
a5421eadc87a537fbe3ff49e6c207be405990220a33d036bf31b47fe25609efa  output_T1_sans_voix_v4_demo.mp4
9f03b9cbdebbdb089783cb2becda7004b222aca7de48340a9f96bc45d1969121  output_T1_sans_voix_v3.mp4
21e8f5d80fcdcd3ac552c4200d6ab9ee316391fca86bce04c1b94253bf5d622e  output_T1_sans_voix_v2.mp4
```

## Droits et mentions

- Prises : clips Mixkit sous **Mixkit Stock Video Free License** (usage commercial autorisé), assemblés en 4 prises `S1..S4` par `rushes/build_scenes.sh`.
- Valeurs commerciales (`MAQUIS DÉMO`, `BURGER MAISON`, `2 500 FCFA`, `ARCONVILLE`, `NUMÉRO FICTIF`) : **valeurs de démonstration fictives**, aucun contact réel.
- Aucune enseigne réelle n'existe dans les prises : le nom est affiché par une carte de texte.
- Les captures d'interface sont une **simulation navigateur**, pas une caméra Android.

## Reproduire

```bash
bash rushes/build_scenes.sh
PYTHONPATH=. python3 engine/motion_v4.py --plan render_plan_v4_demo.json \
    --output output/output_T1_master_final.mp4 --manifest reports/execution_manifest_v4.json
python3 tools/verify_master.py
PYTHONPATH=. python3 tools/frames_audit_v4.py
```
