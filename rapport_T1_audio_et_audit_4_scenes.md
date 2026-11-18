# T1 — Restaurants et Maquis · Identité sonore originale + audit des quatre scènes
### Rapport de mission — 17 novembre 2026 · référence visuelle conservée : V3.1

---

## 0. Résumé exécutif

| Volet | État | Verdict court |
|---|---|---|
| Audit des 4 consignes de tournage V6.2 | **fait** | Scène 1 PARTIEL · Scène 2 PARTIEL · Scène 3 CONFORME (sur rush de démonstration) · Scène 4 **NON CONFORME** |
| Audit du parcours de capture Android (7 points) | **non vérifiable** | Aucun code Android (ni `.kt`, ni `build.gradle`, ni `AndroidManifest.xml`, ni APK) dans l'espace de travail ni sur Google Drive. La seule capture d'écran 08 disponible **contredit** 3 des 7 points. |
| Deux musiques originales 120 BPM / 30 s / 15 mesures | **faites** | Piste A « Braise & service » (La mineur) + Piste B « Maquis doré » (Ré mineur), instrumentales, synthèse originale par code, aucun sample |
| Effets et ambiances du secteur, fichiers séparés | **faits** | 13 effets + 1 ambiance, tous originaux, dont 1 volontairement **non utilisé** (grésillement : aucune cuisson à l'image) |
| Synchronisation des 11 repères V6.2 | **faite et mesurée** | Placement exact, écart maximal mesuré **2,08 ms** (arrondi d'échantillon) |
| Voix réelle du commerçant | **absente des rushs** | Les 4 rushs n'ont **aucune piste audio** (voir §5.3) : aucun master avec voix n'est prétendu. Aucune voix artificielle n'a été intégrée. |
| Ducking | **testé séparément** | Signal de test parlé synthétique (étiqueté comme tel) : profondeur −10 dB, avance 57 ms, descente 54 ms, retour à −1 dB en 394 ms |
| Master final `output_T1_audio_final.mp4` | **produit** | 30,000 s · 900 images · flux vidéo **bit-à-bit identique à V3.1** · −16,77 LUFS · −2,46 dBTP · 0 échantillon écrêté · latence A/V 0,0 ms |
| Écoute humaine | **non réalisée** | Je ne dispose pas de retour d'écoute : voir §7, ce que je peux affirmer et ce que je ne peux pas |

**Point dur à retenir :** le son est fait et synchronisé, mais **la scène 4 ne montre pas un établissement**.
Le montage visuel V3.1 n'a pas été touché (interdiction de mission) : la correction relève d'une
nouvelle version visuelle, à autoriser séparément.

---

## 1. Nature de ce rapport

Il distingue explicitement, comme demandé :

1. l'audit des quatre consignes de tournage V6.2 (§2) ;
2. la vérification du parcours Android (§3) ;
3. la correspondance réelle des scènes avec les rushs (§2.2 et §2.3) ;
4. les fichiers audio originaux créés (§4) ;
5. la synchronisation des effets (§5.1) ;
6. les tests techniques (§6) ;
7. l'écoute et la validation audio (§7), avec ses limites.

Sources consultées, sans aucune modification : `specs/restaurants_maquis_T1.spec_v6_2.json`,
`specs/restaurants_maquis_T1.spec_v6_2.public-safe.json`, `render_plan.json`,
`rushes/manifest.json`, `rushes/source/*.mp4`, `docs/audio_sync_T1_v2.md`,
`output/output_T1_sans_voix_v3_1.mp4`, et la spec V6.2 du Drive
(`V6_2_restaurants_maquis_T1.spec.json`, identique en contenu aux textes de la mission).

---

## 2. Partie A — Audit des quatre scènes

### 2.1 Méthode

1. Lecture de la consigne exacte (`guide_tournage.consigne`), de la durée imposée
   (`duree_a_tourner_s`), des listes « à montrer » / « à éviter » dans la spec V6.2.
2. Extraction des plans réellement montés depuis `render_plan.json` (12 plans, 900 images) et
   **extraction d'images du master V3.1** aux instants clés de chaque scène (planches fournies :
   `revue_audit/s1_planche.png` … `s4_planche.png`, `revue_audit/planche_master.png`).
3. Comparaison image par image avec les critères de contenu — **jamais** une validation sur la
   durée seule.

> Rappel méthodologique : une durée respectée n'est pas une conformité de contenu. Les quatre
> scènes respectent leurs durées ; **deux contenus sur quatre ne sont pas conformes**.

### 2.2 Tableau de conformité

| Scène | Consigne exacte V6.2 | Durée attendue | Rushs et plans réellement utilisés | Ce que les images montrent réellement | Correspondance | Résultat |
|---|---|---|---|---|---|---|
| **1 — Le plat** | « Approche ton téléphone tout près du plat bien chaud pour montrer tous les détails. Commence un peu loin puis rapproche-toi doucement. » | 6,0 s (180 img : 0–6,000 s) | **3552.mp4** (Mixkit, *Burgers on plates on a table*) — P01 img 9–62 (0–2,5 s), P02 img 65–104 (2,5–4,5 s), P03 img 107–170 (4,5–6,0 s) | Deux hamburgers dressés sur assiettes blanches, vue plongeante sur table noire ; pain glacé brillant, graines, sauce visible ; couverts posés à côté. **Aucune main**, **aucune fumée**, plan déjà serré au départ. Textes : « MAQUIS DÉMO » (0,5–3 s), « BURGER MAISON » (3,5–6 s) | Assiette entière : oui mais **tronquée** par le recadrage 9:16 · Fumée/brillant : brillant oui, **fumée non** · Main qui sert : **non** · « démarre loin puis rapproche » : suggéré par zoom lent 1,00→1,05 et un cut plus serré, **pas un vrai geste continu** · sol/plafond : non · mouvement rapide : non | **PARTIEL** |
| **2 — Le dessus et les détails** | « Passe ton téléphone au-dessus du plat pour montrer tout ce qu'il y a dedans, puis approche-toi très près de la partie la plus appétissante. » | 8,0 s (240 img : 6,000–14,000 s) | **3533.mp4** (Mixkit, *Burger being prepared with french fries*) — P04 img 9–77 (6–9 s), P05 img 80–148 (9–11,5 s), P06 img 151–230 (11,5–14 s) | Très gros plans : œuf au plat, sauce brillante, pain, frites ; vers 11,2 s une **main presse une bouteille de sauce** dans le cadre. Aucune vue d'ensemble du plat rempli vu d'au-dessus. Textes : hero lockup + prix (6,5–9,5 s), accroche « CHAUD · SERVI · AUJOURD'HUI » (10–14,5 s) | Détail « au plus près » : **oui, très réussi** · Plat rempli vu d'au-dessus : **non** (cadrage déjà serré) · Doigts devant l'objectif : main visible mais **ne masque pas** l'objectif · Contre-jour fenêtre : non | **PARTIEL** |
| **3 — La personne qui sert** | « Filme la personne qui sert ou qui mange : sa main, son visage, son sourire. Mets-toi devant elle ou de côté, comme tu veux. » | 7,0 s (210 img : 14,000–21,000 s) | **327.mp4** (Mixkit, *Hamburger being served in restaurant*) — P07 img 9–77 (14–17 s), P08 img 80–133 (17–19 s), P09 img 136–200 (19–21 s) | **Un serveur porte l'assiette à deux mains et la pose** devant un client attablé ; le client, **visage et sourire visibles**, prend le burger et mange ; table en bois, verre, salle derrière. Le geste de service est l'action principale. Textes : nom rappelé (15–17,5 s), prix seul (18–20,5 s) | Main qui sert : **oui** · Visage/sourire : **oui** · Comptoir propre derrière : **oui (table de salle)** · Personne non consentante : personnes tierces d'un rush de stock, **à remplacer par l'équipe du commerçant en production** · Coin sombre : non | **CONFORME** (dimension humaine réelle présente) — avec réserve « stock » |
| **4 — Le lieu et le contact** | « Recule et filme l'entrée de ton local avec le nom écrit dessus, puis le comptoir. On doit reconnaître l'endroit. » | 9,0 s (270 img : 21,000–30,000 s) | **3552.mp4 — le même rush que la scène 1** — P10 img 9–79 (21–23,5 s), P11 img 82–167 (23,5–26,5 s), P12 img 170–245 (26,5–30 s) | Vue plongeante sur des hamburgers en assiette, sur une table. **Aucune entrée, aucune enseigne, aucun nom de local, aucune rue, aucun comptoir**. L'adresse n'existe que sous forme de texte : « COTONOU — ADRESSE FICTIVE » (21,5–25 s) puis pilule « COMMANDER SUR WHATSAPP — NUMÉRO FICTIF » (26,5–30 s) | Nom/enseigne : **non** · Rue autour : **non** · Entrée de face : **non** · Reconnaître un établissement : **impossible** — l'adresse est plaquée sur un plan produit quelconque, exactement le cas à éviter | **NON CONFORME** |

### 2.3 Constats détaillés

**Scène 1 — la durée est bonne, le contenu est incomplet.** Le plan d'ouverture est joli et
appétissant, mais il ne raconte pas la consigne : on ne voit ni la main qui amène le plat, ni la
vapeur, ni un vrai mouvement d'approche (le « rapprochement » est simulé par un zoom de 5 % et un
cut plus serré). Dans un tournage réel, il faudra démarrer large (table + assiette entière) et
terminer serré, en un seul geste.

**Scène 2 — le détail est excellent, la vue d'ensemble manque.** Les gros plans (œuf, sauce, frites)
créent bien l'envie, mais la première moitié de la consigne (« passe au-dessus du plat pour montrer
tout ce qu'il y a dedans ») n'est pas illustrée : aucun plan plongeant du plat complet.

**Scène 3 — la dimension humaine est réellement là.** C'est la scène la plus juste du montage :
une main qui sert, un visage, un sourire, un geste de service, un client qui mange. Deux réserves
de production : (a) ce sont des personnes tierces d'un rush de stock — il faut filmer l'équipe du
commerçant et recueillir son accord ; (b) aucun son n'a été capté (rush muet), donc la scène ne
porte pas la voix du commerçant alors que la spec l'autorise et l'encourage.

**Scène 4 — non conforme, et c'est le point bloquant du gabarit.** Le plan de rendu réutilise le
rush de la scène 1 : aucune enseigne, aucune devanture, aucune rue, aucun comptoir. La seule
information de lieu est un texte (« COTONOU — ADRESSE FICTIVE ») posé sur un plan de burgers.
C'est précisément ce que la consigne interdit (« On doit reconnaître l'endroit »). Tant que la
scène 4 n'est pas tournée devant une devanture réelle, la vidéo ne peut pas être vendue comme
« vitrine d'un établissement » : elle reste une publicité produit anonyme.

### 2.4 Ce que les rushs de démonstration ne permettent pas de vérifier

- **Toute la dimension « local »** (enseigne, rue, entrée, comptoir) : aucun rush de démonstration
  ne contient d'extérieur ni de devanture.
- **La voix du commerçant** : les quatre fichiers de rushs n'ont **aucune piste audio**
  (`ffprobe` : une seule piste vidéo par fichier). Les consignes de voix, de langues (fon, yoruba,
  français, anglais) et le ducking sur voix réelle ne peuvent donc pas être validés sur ce
  prototype, seulement spécifiés et testés séparément (§5.4).
- **La fumée** et le **brillant de la sauce chaude** en conditions réelles de maquis.
- **L'identification du produit par le commerçant** : le produit monté (« BURGER MAISON ») est
  celui du rush, pas celui du commerçant de démonstration.

Deux plans référencés par `render_plan.json` (`3533.mp4`, `327.mp4`) sont **absents du dossier
local** `rushes/source/` alors que le master V3.1 les contient bien à l'image : ils ont donc été
utilisés au moment du rendu, sur une copie de travail qui n'est plus là. Trois fichiers présents
(`2597.mp4`, `3075.mp4`, `4672.mp4`) ne sont référencés par aucun plan : ce sont des rushs
téléchargés mais **non montés**. Aucun fichier de rush n'est redistribué.

---

## 3. Partie A (suite) — Parcours de capture Android, 7 points

### 3.1 Ce qui a été cherché, et ce qui existe

Recherches effectuées : espace de travail local (`/home/user`, tout le dépôt du projet) et
Google Drive (recherche par nom sur `gradle`, `.kt`, `AndroidManifest`, `apk`, `CaptureScene`,
`GuideScene`). **Résultat : aucun projet Android, aucun fichier Kotlin, aucun manifeste, aucun APK.**
Le dossier Drive du projet (`1mkphSxkJyEpy8J0P5HMTA3H4R3XlAdJL`) ne contient que des specs, des
rapports, des ZIP de specs et des planches de design.

Conséquence : **les 7 points ne peuvent pas être vérifiés dans le code.** Je ne peux pas affirmer
que le parcours V6.2 est appliqué, ni qu'il ne l'est pas.

### 3.2 Ce qui EST documenté (et ce que montre la seule capture disponible)

| # | Exigence V6.2 | Ce que dit la spec (écran 08) | Preuve d'implémentation disponible | Statut |
|---|---|---|---|---|
| 1 | Carte de consigne **avant** « GO · Commencer » | État 1 : carte 620 px, fond `rgba(15,23,42,0.92)`, une seule action « GO · Commencer » | Aucune (code absent) ; capture design `08_camera_guidee.png` : carte présente mais **aucun bouton GO visible** | **NON VÉRIFIABLE** |
| 2 | Carte **disparaît entièrement** au début de l'enregistrement | « DISPARAÎT IMMÉDIATEMENT — retirée à l'image 0 » | Capture design : la carte est affichée **pendant** un enregistrement en cours (chrono `00:00:05`, boutons arrêt/pause) → contredit l'exigence | **CONTREDIT PAR LA CAPTURE** |
| 3 | Pendant la prise, **seuls** chrono + barre de progression | « autres_textes : aucun », « autres_boutons : aucun » | Capture design : carte de consigne, bouton galerie, 2 boutons de commande → contredit | **CONTREDIT PAR LA CAPTURE** |
| 4 | Arrêt automatique à la durée imposée | `CameraX.setDurationLimit(6,0 s / 8,0 s / 7,0 s / 9,0 s)` + « aucune action du commerçant » | Aucune (code absent) | **NON VÉRIFIABLE** |
| 5 | Aperçu de la scène **lu avec le son**, en boucle | État 3 : « aperçu immédiat, AVEC LE SON, en boucle » | Aucune (code absent) | **NON VÉRIFIABLE** |
| 6 | Boutons « Refaire » et « Scène suivante » fonctionnels | État 3 : Refaire = revient à l'état 1 de la même scène ; Scène suivante = carte de la scène suivante | Aucune (code absent) | **NON VÉRIFIABLE** |
| 7 | Après la scène 4 : « Voir mon montage » | `apres_scene_4.texte = « Voir mon montage »` | Aucune (code absent) | **NON VÉRIFIABLE** |

**Défaut supplémentaire relevé sur la capture 08** (au-delà des états) : le texte affiché est
« Scène 1/4 : Filme l'entrée ou la devanture de ton commerce (**5 s**) ». C'est le texte de la
**scène 4** avec une **durée fausse** (5 s au lieu de 6 s), présenté sur la **scène 1**. Si cette
capture reflète le code, la consigne exacte n'est pas celle de la spec : c'est un défaut à
corriger en priorité, car il envoie le commerçant filmer autre chose que ce que le montage attend.

**Recommandation** : fournir le module Android (ou l'APK de test) pour que les 7 points soient
vérifiés sur le code et sur l'appareil, et remplacer la capture 08 par une capture conforme
(carte avant GO, chrono seul pendant la prise, aperçu sonore, Refaire / Scène suivante, puis
« Voir mon montage » après la scène 4).

---

## 4. Partie B — Création de l'identité sonore « Restaurants et Maquis »

### 4.1 Principe

Famille `maquis_afrobeats_120` : 120 BPM (1 temps = 500 ms, 1 mesure = 2 s), **30,000 s exactement**,
**15 mesures**. Aucune parole, aucune vocalise : la place est réservée à la voix du commerçant.
Tout est **synthétisé par code** (`audio/scripts/`) — oscillateurs, bruit filtré, synthèse modale
(porcelaine, métal), Karplus-Strong (corde pincée) — donc **aucun sample, aucune boucle, aucun
morceau commercial**. Voir `audio/metadata/LICENCES.md`.

La musique est écrite **pour la timeline existante**, dans cet ordre :

| Section | Temps | Rôle musical | Moyens |
|---|---|---|---|
| Ouverture / Scène 1 | 0–6 s | accrocher tout de suite, énergie gourmande | groove complet dès l'image 0 : kick syncopé, shekere, conga, cloche agogo, balafon qui énonce le motif principal |
| Scène 2 | 6–14 s | soutenir la découverte et le détail | ajout de la corde pincée en arpèges, claps, motif qui se déploie |
| Scène 3 | 14–21 s | accompagner le service, laisser respirer | arrangement **creusé** : plus de clap, kick allégé, nappe ; l'espace est gardé pour la voix (−5 dB de RMS par rapport aux autres sections) |
| Scène 4 | 21–28,5 s | conclusion dynamique et mémorable | retour plein, cuivres synthétiques, motif conclusif |
| Fin | 28,5–30 s | laisser respirer l'appel à commander | accord final tenu, fondu easeOutCubic 1,5 s |

### 4.2 Les deux pistes de la famille (sélection sans répétition)

| id catalogue | Piste | Tonalité | Grille | Timbres dominants | Signature rythmique |
|---|---|---|---|---|---|
| `maquis_afro_01` | **Braise & service** (`maquis_afro_A_braise`) | La mineur | Am7 – F – C – G (puis F – G – Am9 pour conclure) | balafon, corde pincée, cloche agogo | kick 1 / 2,5 temps syncopé, shekere en doubles-croches, conga tumbao |
| `maquis_afro_02` | **Maquis doré** (`maquis_afro_B_maquis_dore`) | Ré mineur | Dm7 – B♭ – F – C (puis Dm9) | kalimba, e-piano, agogo plus aigu | groove plus berceur : kick 1 / 2,25 / 3,5, contretemps de basse, cloche 12/8 |

Les deux pistes partagent la famille et la fonction, **mais ne sont pas des copies** : tonalité,
grille, timbres, motif mélodique et profil rythmique diffèrent. La piste A est livrée dans le
master ; la piste B est livrée montée à l'identique (`output_T1_audio_final_pisteB.mp4`) pour
permettre la sélection automatique sans répétition prévue par la spec (pool ≥ 2).

### 4.3 Effets sonores : matières du métier, jamais génériques

Aucun *whoosh*, *pop* ou *ding* de bibliothèque : les transitions sont faites **avec de la
vaisselle et des couverts**, les accents de prix avec un **balafon**, l'appel à commander avec un
**motif de kalimba**. Les onze repères sont tenus par 10 matières différentes.

| Fichier | Matière | Rôle | Crête |
|---|---|---|---|
| `sfx_01_assiette_posee` | porcelaine posée sur la table | service (S3), ouverture S1 | −12 dBFS |
| `sfx_02_couverts_contact` | couverts qui se touchent | plan avec couverts visibles | −16 dBFS |
| `sfx_03_couverts_glisse_montee` | glissement de couvert montant | transition (repère 8,90 s) | −10 dBFS |
| `sfx_04_couverts_glisse_descente` | glissement descendant | transition (repère 23,90 s) | −10 dBFS |
| `sfx_05_shekere_roulement` | graines sur calebasse | transitions (5,90 s et 13,90 s) | −10 dBFS |
| `sfx_06_porcelaine_montee` | porcelaine frottée qui monte | transition (20,90 s) | −11 dBFS |
| `sfx_07_cloche_agogo` | double cloche métallique | accent (16,90 s) | −11 dBFS |
| `sfx_08_balafon_prix` | lame de bois, deux notes | prix (7,34 s) | −9 dBFS |
| `sfx_09_balafon_prix_variante` | variante plus basse | prix seul (18,34 s) | −9,5 dBFS |
| `sfx_10_service_tissu` | tissu + pas feutrés | arrivée du serveur (S3) | −20 dBFS |
| `sfx_11_kalimba_cta` | kalimba 3 notes + cloche douce | CTA (26,50 s) | −11 dBFS |
| `sfx_12_impact_grave` | impact grave feutré | bloc visuel (6,50 s / 21,50 s) | −10 dBFS |
| `sfx_13_gresillement_braise` | huile et braise | **non utilisé** : aucune cuisson à l'image (§4.4) | −14 dBFS |

### 4.4 Discipline « son motivé par l'image »

Ce qui a été **volontairement refusé**, pour ne pas plaquer une bande-son générique :

- **pas de grésillement de cuisson** : aucun plan ne montre de cuisson (burger déjà dressé, œuf déjà
  cuit). Le fichier existe dans la bibliothèque, prêt pour un futur gabarit montrant une plancha ;
  il n'est pas dans le mix.
- **pas de son de rue, de moteur ou d'enseigne** : la scène 4 ne montre ni rue, ni entrée, ni
  enseigne. Ajouter une ambiance extérieure aurait « habillé » un plan qui contredit la consigne —
  c'est exactement le placage à éviter.
- **pas d'ambiance de salle sur les scènes 1, 2 et 4** : la salle n'est visible qu'en scène 3
  (fenêtre 13,80–21,20 s, fondu de 500 ms de chaque côté).
- **aucune notification imitée** sur le CTA WhatsApp : un motif chaleureux de kalimba, pas une
  alerte, conformément à la consigne « pas de notifications agressives ».
- **pas d'effet sur la main qui presse la sauce** (≈ 11,2 s) : aucune matière de la bibliothèque
  ne correspond à ce geste ; mieux vaut rien qu'un son faux.

---

## 5. Partie C — Synchronisation, voix, mixage

### 5.1 Les 11 repères V6.2 (heures imposées, conservées à l'identique)

| # | Temps V6.2 | Événement visuel | Élément sonore | Gain au bus | Niveau relatif mesuré (effet / mix) | Placement mesuré |
|---|---|---|---|---|---|---|
| 1 | 5,90 s | transition vers la scène 2 | shekere (roulement) | +3,0 dB | −5,6 dB | 0,17 ms |
| 2 | 6,50 s | apparition du bandeau commercial | assiette posée + impact grave | +3,0 dB | −3,6 / +3,9 dB | 0,00 ms |
| 3 | 7,34 s | mise en valeur du prix | balafon, 2 notes | 0,0 dB | +3,6 dB | 0,00 ms |
| 4 | 8,90 s | préparation du zoom punch | couvert qui glisse (montée) | 0,0 dB | +3,0 dB | 0,25 ms |
| 5 | 13,90 s | transition vers la scène 3 | shekere (roulement, plus discret) | +2,0 dB | −4,4 dB | 0,17 ms |
| 6 | 16,90 s | accent avant la coupe | cloche agogo | 0,0 dB | +4,1 dB | 0,00 ms |
| 7 | 18,34 s | apparition du prix seul | balafon, variante plus basse | 0,0 dB | +4,9 dB | 0,00 ms |
| 8 | 20,90 s | transition vers la scène 4 | porcelaine qui monte | 0,0 dB | −12,7 dB | 2,08 ms |
| 9 | 21,50 s | apparition de la localisation | assiette posée + impact grave | +1,5 dB | −3,4 / +4,1 dB | 0,00 ms |
| 10 | 23,90 s | préparation du cut vers le CTA | couvert qui glisse (descente) | 0,0 dB | +0,3 dB | 0,15 ms |
| 11 | 26,50 s | appel à commander sur WhatsApp | kalimba 3 notes + cloche | 0,0 dB | +4,1 dB | 0,00 ms |

Sons **directs** (hors repères, motivés par l'image) : 0,15 s assiettes sur la table (−7 dB),
14,45 s mouvement de service (−2 dB), 15,05 s assiette posée devant le client (−5 dB).

« Gain au bus » = réglage propre à chaque repère (les fichiers ont des crêtes différentes, la
relation naturelle entre une porcelaine et un balafon est conservée) ; le **bus d'effets** est
appliqué globalement à **−5 dB** (et **−8 dB** sous parole), conformément à la spec.

### 5.2 Paramètres V6.2 : appliqués / non applicables

| Paramètre | Valeur spec | Application dans ce master |
|---|---|---|
| Musique | −6 dB | **appliqué** (gain du bus musique 0,501) |
| Musique pendant la voix | −16 dB | **implémenté et testé** (§5.4) ; inactif ici faute de voix |
| Seuil détecteur | −26 dBFS (RMS 10 ms) | **implémenté et testé** |
| Attaque / relâche / hold / lookahead | 60 / 400 / 200 / 80 ms | **implémentés et mesurés** (§5.4) |
| Voix | −16 LUFS / −1 dBTP | **non applicable** : aucune voix dans les rushs |
| Effets | −5 dB, −8 dB sous parole | **appliqué** (−5 dB ; −8 dB testé dans le fichier de test) |
| Fade-out musique et voix | 28,50 → 30,00 s | **appliqué** à la musique (easeOutCubic) ; voix inexistante |
| Ambiance | non chiffrée dans la spec | **−20 dB**, uniquement 13,80–21,20 s (choix documenté) |

### 5.3 Voix du commerçant : état factuel

Les quatre rushs (`3552.mp4`, `3533.mp4`, `327.mp4` — et les non montés) **n'ont aucun flux audio** :
`ffprobe` ne renvoie qu'une piste vidéo par fichier. Il n'existe donc **aucune voix réelle** pour ce
montage de démonstration. Décisions prises, conformes à la mission :

- **aucune voix fabriquée** dans le master (pas de voix de synthèse, pas de voix-off) ;
- **aucune transcription, traduction ni sous-titre automatique** ajouté ;
- le mécanisme de ducking est **testé séparément** sur un signal de test (§5.4) ;
- la chaîne est prête : `python3 audio/scripts/mix_T1.py --voice <prises.wav>` produit le master
  avec la voix réelle conservée, normalisée à −16 LUFS / −1 dBTP, et la musique duckée.

### 5.4 Test du ducking (séparé, avec un signal de test — pas une voix)

Fichier de test : `audio/synced/ducking_test_signal_de_test.wav` (formants + syllabes synthétiques,
**étiqueté comme signal de test**), 5 phrases réparties dont deux dans la scène 3.

| Mesure | Valeur mesurée | Référence spec |
|---|---|---|
| Voix cumulée au-dessus du seuil | 5,84 s (19,5 % du montage) | — (déclenche le ducking) |
| Profondeur atteinte | **−10,0 dB** (musique −6 → −16 dB) | −10 dB ✔ |
| Avance de la descente (anticipation) | 57 ms avant le début de la salve | lookahead 80 ms (mesure après détection, tolérance 10 ms) ✔ |
| Durée de la descente | 54 ms | attaque 60 ms ✔ |
| Retour à −1 dB après la voix | 394 ms (courbe easeOutCubic) | relâchement 400 ms ✔ |
| Retour complet à 0 dB | 540 ms après la fin de la salve | hold 200 ms + relâchement 400 ms ✔ |
| Sans voix (contrôle) | musique **constante** à −6 dB, aucun ducking | « la musique ne baisse pas sans voix » ✔ |
| Effets sous parole | −8 dB au lieu de −5 dB | ✔ |

Courbe de contrôle : `audio/metadata/ducking_test_courbe.png`.
Mixage de test : `audio/synced/ducking_test_T1_pisteA_avec_signal.wav`.

### 5.5 Mastering (documenté)

Chaîne : compression de bus douce (seuil −21 dBFS, 2:1, attaque 6 ms, relâche 150 ms) → limiteur
avec anticipation (plafond −2,6 dB) → étalonnage itératif.

| Mesure | WAV de mixage | MP4 final (AAC 192 kb/s) |
|---|---|---|
| Loudness intégrée (BS.1770-4) | −16,69 LUFS | **−16,77 LUFS** |
| True peak (4× suréchantillonné) | −2,65 dBTP | **−2,46 dBTP** |
| Crête échantillon | — | −2,47 dBFS |
| Échantillons écrêtés | 0 | **0** |

Le niveau global a été calé sur **−16 LUFS** (référence usuelle pour une vidéo verticale), ce qui
laisse ~1,5 dB de marge sous le true peak maximal autorisé par la spec (−1 dBTP) pour absorber
l'encodage AAC. Les rapports internes (musique/effets/ambiance) sont ceux de la spec.

---

## 6. Partie D — Tests techniques

| Contrôle | Exigence | Résultat | Statut |
|---|---|---|---|
| Durée exacte | 30,000 s | vidéo 30,000 s / 900 images ; audio 30,000 s (1 408 trames AAC) | **OK** |
| Montage visuel inchangé | identique à V3.1 | flux vidéo copié : MD5 `b89c79e13bf668ad23c6f877d700caf5` **identique** à `output_T1_sans_voix_v3_1.mp4` | **OK** |
| Synchronisation des 11 repères | ±1 image (33 ms) | écart max mesuré **2,08 ms** (arrondi d'échantillon) | **OK** |
| Latence A/V du conteneur | 0 | **0,0 ms** (corrélation croisée WAV ↔ audio décodé du MP4) | **OK** |
| Continuité musicale | pas de coupure entre scènes | sections enchaînées ; hors attaque du fichier (0–40 ms) et hors fondu final, le point le plus bas d'une fenêtre de 20 ms est **−49,8 dB** (à 3,22 s) ; la section la plus creuse (14–21 s) reste à −37,9 dB minimum | **OK** |
| Fondu final | 28,50 → 30,00 s | dernier échantillon −116,7 dBFS, RMS des 50 dernières ms −74,7 dBFS : décroissance douce, pas de coupure sèche | **OK** |
| Saturation / écrêtage | aucun | 0 échantillon écrêté, true peak −2,46 dBTP | **OK** |
| Clics / discontinuités | aucun | ratio dérivée max / RMS dérivée 19,0 (< 40), 0 dépassement | **OK** |
| Équilibre spectral (lisible sur haut-parleur de téléphone) | médiums/aigus présents | 20–80 Hz 21,2 % · 80–250 Hz 24,5 % · 250–2 000 Hz 30,3 % · 2–8 kHz 19,2 % · 8–20 kHz 4,7 % | **OK** |
| Dynamique par scène (rôle dramatique) | S3 plus creusé | RMS : S1 −20,6 · S2 −19,3 · **S3 −21,5** · S4 −19,0 · fondu −23,7 dB | **OK** |
| Rendu sur téléphone | vérification physique | **non réalisée** (voir §7) | **À FAIRE** |

Contrôles détaillés : `audio/metadata/qc_audio.json`, `audio/metadata/mix_report.json`,
`audio/metadata/ducking_test.json`. Planche : `audio/metadata/planche_synchronisation_audio.png`.

---

## 7. Écoute et validation audio — ce que je peux affirmer, ce que je ne peux pas

**Ce que je peux affirmer**, sur la base de mesures reproductibles et de contrôles visuels
(spectrogrammes, enveloppes, courbes de gain) : la musique dure exactement 30 s et se termine en
fondu ; les 11 repères sont placés à l'échantillon près ; les effets sont tous présents entre −12,7
et +4,9 dB par rapport au mix local ; aucun écrêtage, aucun clic ; le true peak et la loudness sont
dans les clous ; la stéréo est équilibrée pour un petit haut-parleur.

**Ce que je ne peux pas affirmer** : qu'un auditeur humain trouve le résultat *beau*, ou que le
rendu sonne exactement comme prévu sur un téléphone réel. **Je n'ai pas de retour d'écoute** : ce
rapport ne remplace pas une écoute. Les fichiers sont livrés prêts pour cette écoute.

Protocole d'écoute proposé (10 minutes) :

1. **Téléphone, haut-parleur intégré, volume 60 %** — vérifier que la mélodie (balafon) reste
   audible, que la basse ne « mange » pas tout, que les effets ne piquent pas.
2. **Écouteurs** — vérifier la propreté des transitions (5,90 / 13,90 / 20,90 s) et l'absence de
   pompage sur les impacts (6,50 / 21,50 s).
3. **Trois passages comparés** : piste A, piste B, et la version muette V3.1, pour vérifier que le
   son « raconte » bien les quatre scènes.
4. **Test voix (optionnel)** : lancer
   `python3 audio/scripts/mix_T1.py --voice chemin/prises.wav` avec de vraies prises pour valider
   le ducking sur voix réelle avant production.

Grille d'écoute à remplir (à joindre à la prochaine revue) :

| Critère | 1 (à revoir) → 5 (excellent) | Commentaire |
|---|---|---|
| Accroche des 2 premières secondes | | |
| Adéquation musique / métier (maquis) | | |
| Effets crédibles et non caricaturaux | | |
| Équilibre musique / effets | | |
| Lisibilité sur haut-parleur de téléphone | | |
| Cohérence de la fin (CTA) | | |

---

## 8. Livrables

### 8.1 Master final

- `output/output_T1_audio_final.mp4` — **30,000 s, 720×1280, 30 i/s, 900 images**, vidéo V3.1
  intacte, musique piste A + effets + ambiance, **sans voix** (aucune n'existe), AAC 192 kb/s.
  SHA-256 : `8cdea99885b79ef0…` (liste complète : `audio/metadata/SHA256SUMS_audio.txt`).
- `output/output_T1_audio_final_pisteB.mp4` — même montage avec la seconde piste de la famille.

### 8.2 Sources audio séparées (modifiables indépendamment)

```
audio/
├── music/        maquis_afro_A_braise_mix_30s.wav · maquis_afro_B_maquis_dore_mix_30s.wav
├── stems/        4 stems par piste (batterie, basse, harmonie, mélodie) = 8 fichiers
├── sfx/          13 effets individuels (dont 1 réservé, non utilisé)
├── ambience/     ambiance_maquis_salle_30s.wav
├── synced/       mix_T1_audio_final.wav · mix_T1_audio_final_pisteB.wav
│                 ducking_test_signal_de_test.wav · ducking_test_T1_pisteA_avec_signal.wav
├── metadata/     music_build.json · sfx_manifest.json · mix_report.json · qc_audio.json
│                 ducking_test.json · LICENCES.md · SHA256SUMS_audio.txt · SHA256_audio.json
│                 planche_synchronisation_audio.png · ducking_test_courbe.png
└── scripts/      synth_lib.py · build_music.py · build_sfx.py · mix_T1.py
                  ducking.py · loudness.py · ducking_test.py · qc_audio.py
```

Reconstruction complète, dans l'ordre (aucune dépendance hors numpy/scipy/soundfile/matplotlib/ffmpeg) :

```bash
cd audio/scripts
python3 build_music.py      # les deux pistes + stems
python3 build_sfx.py        # effets + ambiance
python3 mix_T1.py --alt     # mixage synchronisé (piste A + variante B)
python3 ducking_test.py     # test séparé du ducking
python3 qc_audio.py         # contrôles techniques
```

### 8.3 Empreintes SHA-256

Toutes les empreintes (38 fichiers, dont les deux MP4 et l'archive) sont dans
`audio/metadata/SHA256SUMS_audio.txt` (`sha256sum -c` compatible) et en JSON dans
`audio/metadata/SHA256_audio.json`.

- `output/output_T1_audio_final.mp4` : `8cdea99885b79ef0328edc31619243ac365066a9a699900d137e20bf61858ab3`
- `output/output_T1_audio_final_pisteB.mp4` : `96f020409dd3e82ba026db4b3ae1ca58180237ae2b9ba30c228f17d74eeea040`
- `output/T1_audio_v1_livraison.zip` (52 Mo, 58 entrées) : son empreinte est fournie à côté de l'archive, dans `output/T1_audio_v1_livraison.zip.sha256` (une archive ne peut pas contenir sa propre empreinte).

### 8.4 Archive de livraison

`output/T1_audio_v1_livraison.zip` contient : les deux MP4, ce rapport, `revue_audit/` (planches
des 4 scènes, planche temporelle du master, spectrogrammes des deux pistes, courbe de ducking,
capture écran 08 du Drive), `audio/music_flac/` et `audio/synced_flac/` (transcodages **sans
perte** des WAV pour une archive portable), `audio/sfx/`, `audio/ambience/`, `audio/metadata/`,
`audio/scripts/` et un `LISEZ-MOI_ARCHIVE.md`. Les WAV lourds (`audio/stems/`, `audio/synced/`)
restent dans l'espace de travail et sont régénérables par script.

---

## 9. Ce qui n'a pas été modifié (vérifié)

| Élément | État |
|---|---|
| `output/output_T1_sans_voix_v3_1.mp4` (référence visuelle) | **intact** — SHA-256 `33abc850265242b91fb61284e7e7649cc92b7750414212fa8f05ed4e455c2039` |
| Masters V2 / V3 | **intacts** |
| `specs/*` V1.2 et V6.2 | **intacts** (aucune écriture) |
| `render_plan.json`, `adapter/`, `engine/` | **intacts** (lecture seule) |
| `rushes/` | **intacts** (lecture seule, rien redistribué) |
| Livraison V3.1 (`T1_v3_1_livraison.zip`, rapport) | **intacte** |
| 19 autres gabarits | **non commencés** |

Seuls fichiers **écrits** : `output/output_T1_audio_final.mp4`,
`output/output_T1_audio_final_pisteB.mp4`, le dossier `audio/`, ce rapport et l'archive de livraison.

---

## 10. Points à décider avant production

1. **Scène 4** : retourner une vraie devanture (enseigne + rue + entrée de face + comptoir). Sans
   cela, le gabarit ne remplit pas sa promesse « on reconnaît l'endroit ». Une nouvelle version
   visuelle est nécessaire — V3.1 reste la référence et n'a pas été touchée.
2. **Scènes 1 et 2** : compléter le tournage (main qui sert, vapeur, vue plongeante du plat
   complet) pour passer de PARTIEL à CONFORME.
3. **Voix du commerçant** : organiser les prises avec son audio (fon, yoruba, français ou anglais),
   puis lancer `mix_T1.py --voice` : la chaîne appliquera −16 dB de musique sous la parole, sans
   jamais toucher à sa voix.
4. **Android** : fournir le module pour vérifier les 7 points sur le code et l'appareil, et corriger
   la carte 08 (texte de la scène 4 + « 5 s » affichés sur la scène 1, carte visible pendant la prise).
5. **Écoute humaine** : valider le mix sur téléphone et écouteurs avec la grille du §7 avant de
   figer l'identité sonore du secteur.

---

*Rapport produit le 17 novembre 2026 — aucune écoute humaine n'a été réalisée à ce stade ;
les affirmations de ce document sont toutes adossées à une mesure ou à un fichier listé.*
