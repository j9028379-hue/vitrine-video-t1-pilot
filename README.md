# VITRINE VIDÉO — pilote Restaurants & Maquis / T1 « Plat du jour »

Ce dépôt porte uniquement sur T1 : quatre scènes, douze plans, huit blocs graphiques, quatorze presets, 30 secondes, 720 × 1280, 30 images/s. Le rendu initial est muet. Aucun son, aucune voix, transcription ou sous-titre n'est généré.

## État de reprise

L'espace local remis à cette session ne contenait ni dépôt Git, ni commit `98fe258`, ni MP4. La recherche Drive n'a retrouvé, comme archive du pilote, que les documents de spécification V6.2 et non le moteur, le manifeste historique, le plan de rendu, les rushs, les tests ou le rendu. Les deux JSON de référence ont été téléchargés par leurs identifiants Drive exacts, validés et copiés ici sans modification. `adapter/t1_adapter.py` est donc une reconstitution limitée à ce qui manquait, dérivée des deux spécifications, et conserve celles-ci en lecture seule.

Le code, le plan de rendu, les médias téléchargés et le rendu créés dans ce dépôt ne sont pas présentés comme des fichiers restaurés depuis l'ancienne session. Le commit historique `98fe258` n'est pas disponible.

## Références immuables

- `specs/T1_ENGINEERING_SPEC_V1_2.json` — copie exacte du fichier Drive `19CDfmQsJdt0sI4_QhbKGn7aJ5p7gE3Dh`.
- `specs/RAPPORT_V1_2_INGENIERIE_T1.md` — copie exacte du fichier Drive `1IeTbq0CPPwEYpKXjGXQmM8LPZfSLtGKC`.
- `specs/restaurants_maquis_T1.spec_v6_2.json` — copie locale exacte et en lecture seule du JSON Drive V6.2; ce fichier est ignoré par Git et n'est pas publié.
- `specs/restaurants_maquis_T1.spec_v6_2.public-safe.json` — copie dérivée publiée pour CI. Uniquement l'exemple CTA contenant une chaîne au format de numéro téléphonique béninois a été remplacé par `NUMÉRO DE DÉMO NON ATTRIBUÉ`; l'original Drive et la copie canonique locale restent inchangés.

Cette précaution évite de publier une chaîne téléphonique au format valide dont l'absence d'attribution réelle ne peut pas être établie. Le rendu local et ses tests ont utilisé le V6.2 canonique exact; GitHub Actions utilise le JSON public-safe et vérifie les structures/montage. La durée de tournage V6.2 ne remplace pas le timing du montage V1.2.

## Données de démonstration

`demo/T1_demo_input.json` utilise des valeurs fictives. Le commerce est nommé « Maquis Démo », le quartier porte une mention d'adresse fictive et le contact est `NUMÉRO FICTIF` ; ce ne sont pas les coordonnées d'un commerce réel. Les rushs illustrent des exemples de stock et ne sont pas des images du commerce.

## Vidéos sources et licence

`rushes/manifest.json` référence quatre clips Mixkit explicitement indiqués sur leurs pages comme utilisables à des fins commerciales sous la Mixkit Stock Video Free License. Les URL, pages, licences et empreintes SHA-256 y figurent. Les originaux sont téléchargés temporairement au rendu, leur empreinte est contrôlée, et `rushes/source/` est ignoré par Git. Aucun rush brut n'est inclus dans l'historique public ni dans les artefacts du workflow.

## Exécution locale

Prérequis : Python 3.11+, FFmpeg/FFprobe, `curl`.

```bash
python -m pip install -r requirements.txt
python -m json.tool specs/T1_ENGINEERING_SPEC_V1_2.json >/dev/null
python -m json.tool specs/restaurants_maquis_T1.spec_v6_2.json >/dev/null
python -m engine.fetch_rushes
python -m adapter.t1_adapter
python -m pytest -q
python -m engine.render
python -m engine.verify
```

Résultats locaux : `render_plan.json`, `output/output_T1_sans_voix.mp4`, `output/verification.json` et `output/planche_controle.png`.

## GitHub Actions

Le workflow manuel est `.github/workflows/render_t1.yml` (`workflow_dispatch`). Il valide les deux JSON, retélécharge et contrôle les quatre rushs, génère `render_plan.json`, exécute les tests, rend le MP4 et vérifie les métadonnées avec FFprobe. Il publie le MP4, le plan, la vérification, la planche et le manifeste comme artefacts téléchargeables pour sept jours. Il n'ajoute pas les fichiers source Mixkit au dépôt.

## Limites connues

- Les sources exactes de l'ancienne session, son historique Git local, le commit `98fe258`, son manifeste de rushs et son MP4 n'ont pas persisté dans les emplacements inspectés.
- Les clips Mixkit référencés ici sont de nouveaux clips de remplacement, choisis et vérifiés sous une licence autorisant l'usage commercial ; ils ne sont pas prétendus identiques aux rushs initiaux.
- C'est un pilote Python/FFmpeg de démonstration visuelle, pas le backend Android Media3.
- L'adresse et le numéro sont volontairement fictifs. Ne pas les substituer à des coordonnées commerciales sans saisie et validation par leur propriétaire.
