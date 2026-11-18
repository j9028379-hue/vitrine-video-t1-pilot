# Note courte — tendances musicales africaines actuelles (novembre 2026)

But de la note : décider quelle **identité sonore** donner à la publicité T1 « Restaurants et Maquis », sans choisir un genre
simplement parce qu'il s'appelle « Afrobeats ». Les sources sont datées ; la conclusion est en fin de note.

## 1. Ce qui circule vraiment, pays par pays

**Bénin.** Le genre le plus commenté localement est l'**Adjapiano**, fusion d'afrobeat, d'amapiano sud-africain et d'un rythme
adja local (le « Gogohoun »), attribuée au beatmaker Rauny Beatz, portée par des artistes comme Ghix et X Time
([Wikipédia FR, article « Rap », consulté le 09/11/2026](https://fr.wikipedia.org/wiki/Rap) ; panorama 2025 :
[circuit-voyage.com, 19/10/2025](https://circuit-voyage.com/panorama-de-la-musique-beninoise-histoire-artistes-et-tendances-actuelles-en-2025/)).
À côté : afro-trap/drill béninois (Joe Kingston, Vano Baby), **Gangan trap** (tambours parlants + trap, Bobo Wê), afropop (Fanicko).

**Côte d'Ivoire.** Le **coupé-décalé** continue de se muer en « street-pop » et en collaborations transfrontalières
(Didi B × Mavo, Himra × BabyDaiz × Zlatan) — [OkayAfrica, « Best West African songs of 2026 so far », 30/06/2026](https://www.okayafrica.com/the-best-west-african-songs-of-2026-so-far/1434059).
Josey y incarne un afro-pop conversationnel, dansant mais très « parlé ».

**Sénégal.** Le **mbalax moderne** domine toujours les plateformes (Wally B. Seck, Amadeus × Wally Seck « Jëli », Mia Guissé),
avec sabar très présent — [RIF XALIMA, 13/05/2026](https://rifxalima.com/100-cash-le-top-5-des-sons-senegalais-qui-dominent-2026/).

**Togo / Cameroun.** Pas de source récente solide trouvée dans cette recherche : je ne tranche pas, plutôt que d'inventer.
Le Togo suit la même vague afro-pop/adjapiano régionale ; le Cameroun reste marqué par bikutsi/makossa dans le fond
et par l'afro-trap/afro-R&B chez les jeunes, mais **sans référence datée collectée ici** — à vérifier avant toute décision artistique.

**Vue continentale.** Amapiano et afro-house continuent de se fondre dans l'afrobeats ; le « 3-Step » (deep house + amapiano + afro-tech)
est présenté comme le son panafricain montant ; les samples nostalgiques et les rythmes traditionnels reviennent via TikTok
([showcaseafricaonline.com, 07/01/2026](https://www.showcaseafricaonline.com/posts/african-music-genres-to-watch-out-for-in-2026)).
Côté hits 2026, la fusion amapiano-afrobeats reste dominante, avec des refrains en pidgin/street-pop
([afrobeatsmagazine.com, 09/10/2026](https://afrobeatsmagazine.com/trending-afrobeats-songs/)).

## 2. Ce que ces tendances ne disent pas

- Un morceau « afrobeats » de playlist est **chanté** : la publicité T1, elle, porte une **voix parlée** synthétique. Un
  instrumental très mélodique et très chargé en aigus (flûtes, synthés brillants) entrerait en concurrence avec la parole.
- Les tempos des hits actuels sont souvent **100–112 BPM** (afro-pop mid-tempo) ou **108–115 BPM** (amapiano dérivé), mais la
  grille de la vidéo est mesurée à **120 BPM / 30 s** (voir `audio/video_edit_analysis_T1.md` §5) et **toutes les coupes tombent
  sur une noire à 120 BPM**. Changer de tempo obligerait à modifier une spécification canonique : ce n'est pas autorisé.
- Les genres cités s'appuient sur des **log drums graves** et des **percus sèches** : c'est justement ce qui laisse de la place
  à une voix parlée dans les médiums, à condition de limiter la musique à −16 dB sous la voix.

## 3. Décision d'identité sonore (2 propositions maximum)

**A — recommandée : « afro-maquis 120 ».** Mid-tempo afro-pop teinté **adjapiano** : basse ronde type log-drum simplifiée,
kick 4/4, claps sur les temps 2 et 4, shakers en doubles-croches, plucks de kalimba/marimba, nappe chaude discrète.
Justification : ancré dans ce qui se danse au Bénin aujourd'hui (adjapiano), compatible 120 BPM, médiums libres pour la voix,
et **aucune mélodie ni sample repris d'un morceau existant** (composition originale, générée par synthèse).
Ce n'est **pas** « de l'afrobeats parce que ça s'appelle afrobeats » : c'est un choix de tempo, de densité spectrale et de
couleur locale, dicté par le fichier vidéo réel et par la voix parlée.

**B — alternative : « gangan acoustique ».** Plus organique : tambours parlants simulés (toms pitched), balafon, djembé,
basse discrète, très peu d'électronique. Justification : proximité avec le Gangan trap et les percussions béninoises,
utile si le client trouve la proposition A trop « club ».

Les deux tiennent **120 BPM / 30 s**, sans dépasser 2 propositions, et sont livrées en stems séparés.

## 4. Limite à dire clairement

Aucun outil de génération musicale par IA autorisé commercialement n'est disponible dans cet environnement d'exécution.
Les deux pistes sont donc **composées et synthétisées en code** (oscillateurs, bruit filtré, enveloppes, échantillons de percussion
synthétisés) : ce sont des compositions originales, déclarées comme synthétiques, et **pas** des morceaux générés par un modèle
de musique. Cette limite est reprise dans `audio/metadata/LICENCES.md` et dans le README du dépôt.
