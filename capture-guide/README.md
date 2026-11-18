# Guide de capture — T1 « Restaurants et Maquis »

Ce dossier décrit **ce que le commerçant doit filmer**. Il ne contient aucune consigne inventée : les quatre textes
ci-dessous sont ceux de la spécification V6.2 (`scenes[n].guide_tournage`), repris mot pour mot.

Règle de base : les quatre scènes sont **quatre prises vidéo**, jamais des photos. Le commerçant filme avec la caméra de
son téléphone, sans couper, et l'application arrête l'enregistrement toute seule à la durée imposée.

| Scène | Titre affiché | Durée imposée | Ce qu'on doit reconnaître |
|---|---|---|---|
| 1/4 | LE PLAT | **6 s** | l'assiette entière, le brillant, la main qui sert |
| 2/4 | LE DESSUS ET LES DÉTAILS | **8 s** | le plat vu d'au-dessus puis un détail très proche |
| 3/4 | LA PERSONNE QUI SERT | **7 s** | une main, un visage, un comptoir propre derrière |
| 4/4 | LE LIEU ET LE CONTACT | **9 s** | l'entrée avec le nom, la rue, puis le comptoir |

> ⚠️ Erreur à ne jamais reproduire : afficher « 5 s » sur la scène 1. La scène 1 dure **6 secondes**, la 4 dure 9 secondes.

---

## Scène 1/4 — LE PLAT — 6 secondes

**Consigne** : « Approche ton téléphone tout près du plat bien chaud pour montrer tous les détails. Commence un peu loin
puis rapproche-toi doucement. »

- **À montrer** : l'assiette entière · la fumée ou le brillant de la sauce · ta main qui sert
- **À éviter** : filmer de trop loin · montrer le sol ou le plafond · bouger trop vite
- **Mention affichée sous la consigne** : « Tu peux parler pendant que tu filmes, en fon, yoruba, français ou anglais,
  pour présenter ton produit. »
- **Exemple de phrase** : « Voici notre riz au poulet braisé bien chaud avec alloco, prêt maintenant ! »

## Scène 2/4 — LE DESSUS ET LES DÉTAILS — 8 secondes

**Consigne** : « Passe ton téléphone au-dessus du plat pour montrer tout ce qu'il y a dedans, puis approche-toi très près
de la partie la plus appétissante. »

- **À montrer** : le plat rempli vu d'au-dessus · le plus près possible de la sauce ou de la viande
- **À éviter** : tes doigts devant la caméra · filmer vers la fenêtre (tout devient sombre)
- **Exemple de phrase** : « Regardez la sauce : tout est préparé ce matin avec de l'huile propre. »

## Scène 3/4 — LA PERSONNE QUI SERT — 7 secondes

**Consigne** : « Filme la personne qui sert ou qui mange : sa main, son visage, son sourire. Mets-toi devant elle ou de
côté, comme tu veux. »

- **À montrer** : une main qui sert · le visage de la personne · le comptoir propre derrière
- **À éviter** : filmer quelqu'un qui ne veut pas être filmé · filmer un coin sombre
- **Exemple de phrase** : « C'est moi qui prépare tous les jours. Venez goûter, on sert de midi jusqu'au soir. »

## Scène 4/4 — LE LIEU ET LE CONTACT — 9 secondes

**Consigne** : « Recule et filme l'entrée de ton local avec le nom écrit dessus, puis le comptoir. On doit reconnaître
l'endroit. »

- **À montrer** : le nom ou l'enseigne de ton local · la rue autour · l'entrée de face
- **À éviter** : filmer les passants de près · filmer le ciel
- **Exemple de phrase** : « Nous sommes à Abomey-Calavi, Arconville, à côté de la station. Appelez-nous sur WhatsApp. »

---

## Ce que la démonstration utilise, et ses limites

Les quatre prises publiées dans `simulation/media/` (et assemblées par `rushes/build_scenes.sh`) sont de **vraies
séquences vidéo** sous licence Mixkit Stock Video Free License :

| Scène | Rush réel utilisé | Ce que la consigne demande | Écart assumé |
|---|---|---|---|
| 1 | un serveur porte puis pose un hamburger devant un client | main qui sert, assiette entière | la « fumée » n'est pas visible sur ce rush |
| 2 | plat vu d'au-dessus pendant 4 s, puis gros plan sur sauce/œuf/frites | vue du dessus puis détail | — |
| 3 | un homme mange son hamburger, mains et visage visibles | main, visage, sourire | pas de client identifiable ; comptoir visible en arrière-plan |
| 4 | terrasse et entrée vues depuis la rue (4,6 s) puis comptoir avec clients (4,4 s) | entrée avec **le nom écrit dessus** | **aucune enseigne lisible** dans les rushs libres disponibles : le nom « MAQUIS DÉMO » n'apparaît que dans les textes du gabarit, jamais dans l'image filmée |

Cette limite est reprise dans le README principal et dans `audio/metadata/LICENCES.md`. Pour une vraie campagne, la
scène 4 doit être tournée devant l'enseigne réelle du commerçant.
