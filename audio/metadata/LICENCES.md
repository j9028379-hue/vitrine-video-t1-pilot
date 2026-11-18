# Licences et provenance — démonstration T1 « Restaurants et Maquis »

Dernière mise à jour : 18 novembre 2026.

## 1. Rushs vidéo (Mixkit Stock Video Free License)

Les quatre prises de la démonstration sont **assemblées** à partir de six clips Mixkit. Chaque page produit a été
consultée et annonce un téléchargement gratuit pour un usage **commercial ou personnel**.

| ID | Titre Mixkit | Page | Utilisé pour |
|---|---|---|---|
| 327 | Hamburger being served in restaurant | <https://mixkit.co/free-stock-video/hamburger-being-served-in-restaurant-327/> | prise 1 |
| 48322 | Top down view of a burger and crisps | <https://mixkit.co/free-stock-video/top-down-view-of-a-burger-and-crisps-48322/> | prise 2 (1ʳᵉ partie) |
| 3533 | Burger being prepared with french fries | <https://mixkit.co/free-stock-video/burger-being-prepared-with-french-fries-3533/> | prise 2 (2ᵉ partie) |
| 29059 | Man eating a burger and smiling | <https://mixkit.co/free-stock-video/man-eating-a-burger-and-smiling-29059/> | prise 3 |
| 2597 | Outdoor restaurant seating on cobbled street | <https://mixkit.co/free-stock-video/outdoor-restaurant-seating-on-cobbled-street-2597/> | prise 4 (1ʳᵉ partie) |
| 41222 | Two girls chatting at the counter of a coffee shop | <https://mixkit.co/free-stock-video/two-girls-chatting-at-the-counter-of-a-coffee-shop-41222/> | prise 4 (2ᵉ partie) |

Licence : <https://mixkit.co/license/#videoFree>. Les URL, titres et empreintes SHA-256 sont dans `rushes/manifest.json`.

**Ce qui est publié et ce qui ne l'est pas**

- Les **originaux** Mixkit ne sont pas versionnés : `rushes/source/**` est ignoré par Git, et `bash rushes/build_scenes.sh`
  les télécharge puis vérifie leur SHA-256 avant de reconstruire les quatre prises.
- Les **quatre prises web** de `simulation/media/S1..S4.mp4` (540 × 960, sans audio) sont des dérivés réduits de ces clips,
  publiés uniquement pour que la maquette de parcours fonctionne dans un navigateur. Ils ne sont pas revendus ni
  re-licenciés ; la licence Mixkit reste celle des originaux. Si la redistribution de dérivés n'est pas souhaitée,
  supprimer `simulation/media/` : la maquette reste lisible mais sans vidéo, et les captures de `ui-screens/` documentent
  les écrans.

## 2. Voix

Voix de **synthèse** française (texte → parole) générées avec l'outil de synthèse vocale de la plateforme Arena.ai
(Agent Mode), même identité vocale pour les quatre prises. Ce ne sont pas des voix de personnes réelles, il n'y a ni
clonage ni imitation. Détail et conditions : `audio/metadata/VOIX_SYNTHETIQUES.md`.
Avant une diffusion commerciale large, vérifier les conditions d'utilisation de la plateforme utilisée.

## 3. Musiques et effets

Les deux musiques (`audio/music/v2/`) et les effets (`audio/sfx/`) sont des **créations originales synthétisées en code**
(oscillateurs, bruit filtré, Karplus-Strong, synthèse modale) via `audio/scripts/build_music_v2.py` et `build_sfx.py`.

- Aucun échantillon tiers, aucune boucle, aucun extrait d'œuvre existante, aucune mélodie reprise.
- **Aucun outil de génération musicale par IA n'a été utilisé** (aucun n'est disponible dans cet environnement) : les deux
  pistes sont donc composées et synthétisées en code, et déclarées comme telles. Elles ne doivent pas être présentées
  comme « générées par une IA musicale ».
- L'ambiance de salle (`audio/ambience/ambiance_maquis_salle_30s.wav`) est également synthétisée.

## 4. Polices

`assets/fonts/Montserrat-Variable.ttf` et `assets/fonts/PlusJakartaSans-Variable.ttf` — SIL Open Font License 1.1,
fichiers de licence conservés dans le même dossier.

## 5. Images et données

- **Aucune photographie fixe n'est utilisée comme prise** : les quatre scènes sont des vidéos `.mp4`. Une image de
  devanture générée par IA a été produite puis **écartée** et n'est pas publiée, précisément parce qu'une prise doit être
  une séquence vidéo.
- Aucune image de burger n'est utilisée comme image de devanture, aucune adresse n'est écrite sur une image alimentaire.
- « Maquis Démo », « Burger maison », « 2 500 FCFA », « ARCONVILLE — ADRESSE FICTIVE », « NUMÉRO FICTIF » : valeurs de
  démonstration fictives. Aucun contact réel, aucune donnée personnelle.
- Aucune enseigne réelle n'est lisible dans les rushs : le nom du commerce n'existe que dans les textes du gabarit.

## 6. Code

Le code du moteur, de l'adaptateur, de la maquette et des scripts audio est fourni avec ce dépôt de démonstration.
Aucune dépendance à un contenu tiers payant.
