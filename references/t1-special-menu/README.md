# Référence approuvée — T1 « Plat du jour »

Référence publique : [TikTok — Special Menu | Food Template](https://www.tiktok.com/@ctemplate99/video/7525857155178712376)

## Sources de vérité

1. `reference_decompilation_v1.json` — mesures observées sur les 570 images de la référence ;
2. `../../config/T1_special_menu_reference_v1.json` — adaptation 4 scènes / 900 images ;
3. `../../reports/T1_SPECIAL_MENU_REFERENCE_ENGINEERING.md` — explication d’ingénierie en français ;
4. `../../engine/special_menu_style.py` — moteur de prévisualisation ;
5. `../../output/output_T1_special_menu_reference_v1.mp4` — première preuve visuelle muette ;
6. `../../config/T1_special_menu_reference_v2.json` — révision prix + transitions impact ;
7. `../../reports/T1_SPECIAL_MENU_V2_REFINEMENT.md` — spécification de la V2 ;
8. `../../output/output_T1_special_menu_reference_v2.mp4` — prévisualisation V2 ;
9. `../../config/T1_special_menu_reference_v3.json` — identité finale unifiée + chorégraphie évolutive ;
10. `../../reports/T1_SPECIAL_MENU_V3_UNIFICATION.md` — spécification V3 ;
11. `../../output/output_T1_special_menu_reference_v3.mp4` — prévisualisation V3 approuvée ;
12. `../../config/T1_special_menu_reference_v3_1.json` — même rendu, contrat d’intégration explicite des 12 écrans ;
13. `../../reports/T1_CAPTURE_FLOW_12_SCREENS_INTEGRATION.md` — passage formulaire → captures → moteur.

## Reproduire les rendus

```bash
# V1 conservée
PYTHONPATH=. python3 tools/render_t1_special_menu.py

# V2 conservée
PYTHONPATH=. python3 tools/render_t1_special_menu_v2.py

# V3 visuelle approuvée
PYTHONPATH=. python3 tools/render_t1_special_menu_v3.py
PYTHONPATH=. python3 tools/validate_t1_special_menu.py \
  --config config/T1_special_menu_reference_v3.json \
  --video output/output_T1_special_menu_reference_v3.mp4 \
  --report reports/T1_special_menu_v3_render_validation.json

# V3.1 : régénérer le contrat programmeur des 12 écrans (aucun nouveau rendu)
PYTHONPATH=. python3 tools/build_t1_capture_flow_v3_1.py

PYTHONPATH=. pytest -q \
  tests/test_t1_special_menu_reference.py \
  tests/test_special_menu_renderer.py \
  tests/test_special_menu_v2_refinements.py \
  tests/test_special_menu_v3_choreography.py \
  tests/test_t1_capture_flow_12_screens.py
```

## Règles de sécurité produit

- ne pas modifier le guide des quatre captures ;
- ne pas modifier `main` ni les releases déjà livrées ;
- ne pas ajouter de champ marchand obligatoire ;
- ne pas retimer la parole ;
- ne pas poser de sous-titre sur la parole ;
- ne pas remplacer les coupes franches par des wipes, glitchs ou fondus ;
- ne pas substituer les polices embarquées ;
- maintenir le CTA jusqu’à l’image 899.

Le MP4 tiers n’est pas commité. Son URL, ses dimensions, son hash et sa décompilation sont suffisants pour rendre l’analyse reproductible sans redistribuer le contenu du créateur.
