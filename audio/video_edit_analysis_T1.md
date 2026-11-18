# Analyse réelle du fichier exporté — `output/output_T1_sans_voix_v3_1.mp4`

Analyse faite **sur le fichier vidéo lui-même** (décodage image par image), pas sur le JSON de montage.
Fichier analysé : `output/output_T1_sans_voix_v3_1.mp4`
SHA-256 `33abc850265242b91fb61284e7e7649cc92b7750414212fa8f05ed4e455c2039` · 30,000 s · 720 × 1280 · 30 i/s · 900 images · piste audio : **aucune**.

> Ce fichier est la référence muette V3.1 et reste **intacte** (empreinte inchangée après tout le travail audio).
> La démonstration vidéo publiée avec ce dépôt utilise les mêmes durées, les mêmes transitions et les mêmes blocs de texte,
> avec quatre prises vidéo conformes aux consignes (`output/output_T1_sans_voix_v4_demo.mp4`).

---

## 1. Ce que mesure réellement le fichier

| Mesure | Méthode | Résultat |
|---|---|---|
| Durée / images | `ffprobe` | 30,000 s · 900 images · 30 i/s constants |
| Définition | `ffprobe` | 720 × 1280 (9:16), yuv420p, H.264 |
| Piste audio | `ffprobe` | **absente** (le master est muet, la musique et la voix sont ajoutées au mixage) |
| Coupures franches | différence moyenne entre images consécutives (seuil > 6) | **3 changements de scène** : 5,93–6,13 s · 13,97 s · 21,03 s |
| Pics internes | même méthode | 15,63 · 15,87 · 16,10 s (mouvement de caméra dans la scène 3, pas une coupure) |
| Différence moyenne | toutes les paires d'images | 3,96 (médiane 2,71) → montage calme, sans clignotement |
| Luminosité moyenne | `signalstats` (YAVG) | 115–122 (S1) · 97–105 (S2) · **50→74 (S3, la plus sombre)** · 101–108 (S4) |

Le profil de luminosité confirme à lui seul la structure : deux scènes claires encadrant une scène 3 nettement plus sombre
(50–74) — c'est un point à connaître pour le mixage : une musique très chargée en médiums sur la scène 3 écrase l'image.

## 2. Structure réelle, plan par plan (vérifiée sur les images)

| Plan | Scène | Fenêtre | Durée | Mouvement de caméra observé |
|---|---|---|---|---|
| P01 | S1 Le plat | 0,00 → 2,00 s | 2,0 s | zoom avant lent |
| P02 | S1 | 2,00 → 3,50 s | 1,5 s | push-in rapide |
| P03 | S1 | 3,50 → 6,00 s | 2,5 s | panoramique horizontal |
| P04 | S2 Le dessus et les détails | 6,00 → 8,50 s | 2,5 s | zoom avant lent |
| P05 | S2 | 8,50 → 11,00 s | 2,5 s | panoramique horizontal |
| P06 | S2 | 11,00 → 14,00 s | 3,0 s | zoom arrière lent |
| P07 | S3 La personne qui sert | 14,00 → 16,50 s | 2,5 s | panoramique vertical |
| P08 | S3 | 16,50 → 18,50 s | 2,0 s | push-in rapide |
| P09 | S3 | 18,50 → 21,00 s | 2,5 s | panoramique horizontal |
| P10 | S4 Le lieu et le contact | 21,00 → 23,50 s | 2,5 s | zoom avant lent |
| P11 | S4 | 23,50 → 26,50 s | 3,0 s | zoom arrière lent |
| P12 | S4 | 26,50 → 30,00 s | 3,5 s | dérive lente (plan de fin) |

12 plans, longueur moyenne **2,5 s**, la plus courte 1,5 s (P02), la plus longue 3,5 s (P12, plan de fin).

**Scènes** : S1 0–6 s (180 images) · S2 6–14 s (240) · S3 14–21 s (210) · S4 21–30 s (270) = **6 / 8 / 7 / 9 s**, exactement les durées imposées.

## 3. Les trois transitions (mesurées sur les images)

| Position | Type | Ce qu'on voit réellement |
|---|---|---|
| 5,93 → 6,13 s (images 178–184) | **whip pan** (12 images conçues) | balayage horizontal rapide de S1 vers S2 ; c'est le pic de différence le plus fort du fichier (34,0) |
| 13,97 s (image 419) | **directional push** | poussée directionnelle de S2 vers S3, entrée sur une image nettement plus sombre |
| 21,03 s (image 631) | **mask reveal** | révélation par masque de S3 vers S4 |

Aucun autre fondu : à l'intérieur d'une scène, les changements de plan sont des **coupes franches** (P01→P02, P02→P03, etc.).
Conséquence audio : il n'y a **pas** de fondu à accompagner à l'intérieur des scènes — les effets de transition n'ont de sens qu'aux trois frontières.

## 4. Apparition des textes (vérifiée image par image)

| Bloc | Champ | Fenêtre | Ce que ça raconte |
|---|---|---|---|
| TXT01 | nom | 0,50 → 3,00 s | « MAQUIS DÉMO » écrit mot à mot, sur le premier plan |
| TXT02 | produit | 4,00 → 5,50 s | « BURGER MAISON » en bandeau |
| TXT03 | produit + prix | 6,50 → 9,50 s | lockup héros : produit et **2 500 FCFA** |
| TXT04 | accroche | 10,00 → 13,50 s | « CHAUD · SERVI · AUJOURD'HUI » en segments |
| TXT05 | nom (rappel) | 15,00 → 17,50 s | rappel de l'enseigne sur la scène humaine |
| TXT06 | prix | 18,00 → 20,50 s | prix plein écran |
| TXT07 | quartier / localisation | 21,50 → 25,50 s | « COTONOU — ADRESSE FICTIVE » (V3.1) → remplacé par « ARCONVILLE — ADRESSE FICTIVE » dans la démo V4 |
| TXT08 | WhatsApp (CTA) | 26,50 → 30,00 s | appel à l'action final, tenu jusqu'à la dernière image |

Le prix apparaît donc **deux fois** (6,5–9,5 s et 18–20,5 s), la marque **deux fois** (0,5–3 s et 15–17,5 s), la localisation **une fois**
(21,5–25,5 s) et le CTA **une fois** mais sur 3,5 s jusqu'à la fin. Les textes se chevauchent rarement : un seul bloc dominant à la fois,
sauf TXT06 (prix) qui commence 0,5 s après la fin de TXT05.

## 5. Rythme — ce que ça implique pour la musique

- Tous les changements de plan tombent sur des **multiples de 0,5 s** : 2,0 · 3,5 · 6,0 · 8,5 · 11,0 · 14,0 · 16,5 · 18,5 · 21,0 · 23,5 · 26,5 · 30,0.
- À **120 BPM**, une noire = 0,5 s et une mesure 4/4 = **2,0 s**. Chaque coupe tombe donc exactement sur une noire, et les trois
  transitions sur une mesure entière (6 s = mesure 3, 14 s = mesure 7, 21 s = mesure 10 + 2 temps).
  **Conclusion mesurée : la grille 120 BPM / 30 s est compatible avec le fichier** — aucune adaptation de tempo n'est justifiée.
- 30 s à 120 BPM = 15 mesures. Le plan de fin P12 (26,5–30 s) couvre 1,75 mesure : c'est là que doit se placer la retombée finale.
- Densité : un changement toutes les 2,5 s en moyenne → une musique à motif de 2 mesures (4 s) se répète 7 fois, ce qui est trop
  audible ; il faut un motif de **4 mesures (8 s)** et trois variations (0–14 s, 14–21 s plus sombre, 21–30 s qui monte vers le CTA).

## 6. Ce qu'il faut entendre — et ce qu'il ne faut pas entendre

Actions réellement visibles dans le fichier V3.1 (vérifiées sur les images échantillonnées) :

| Fenêtre | Action réellement visible | Son justifié |
|---|---|---|
| 0,5–3,0 s | texte « MAQUIS DÉMO » écrit mot à mot | aucun effet : le texte n'est pas une action physique |
| 6,0–14,0 s | plat vu d'au-dessus puis détail de sauce/œuf | éventuellement un son de service **si** une main bouge à l'image ; sinon rien |
| 14,0–21,0 s | personne qui mange | aucun son de bouche, aucun bruit de cuisson |
| 21,0–25,5 s | lieu et adresse | ambiance du lieu uniquement si le lieu est visible — ici oui (terrasse réelle) |
| 26,5–30,0 s | CTA WhatsApp | un seul repère discret à l'apparition du CTA, pas de « ding » de notification |

Interdits tirés de l'analyse : la V3.1 **ne montre aucune cuisson** (aucune flamme, aucun grill) → **aucun bruit de grillade**.
Elle **ne montre pas de rue animée** au sens passants proches → **aucune ambiance de rue dense**. Aucun plan ne montre
une action de « pop » ou de « whoosh » → **pas de whoosh/pop/ding systématique**.

Les 11 repères de synchronisation V6.2 (5,90 · 6,50 · 7,34 · 8,90 · 13,90 · 16,90 · 18,34 · 20,90 · 21,50 · 23,90 · 26,50 s) restent la
référence : l'analyse du fichier confirme qu'ils tombent sur des noires à 120 BPM (5,90 s ≈ image 177, juste avant le whip pan ;
6,50 s = première image de S2 + début de TXT03 ; 21,50 s = début de TXT07 et 0,5 s après le mask reveal).
