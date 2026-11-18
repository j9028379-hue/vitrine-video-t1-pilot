# Tableau final JSON / code / MP4 — 12 plans T1

Configuration de présentation consommée : `config/T1_presentation_v3_1.json` — blocs : GB01, GB02, GB03, GB04, GB05, GB06, GB07, GB08

| # | Scène | Déclaré (JSON) : sortie · source · fenêtre · gel | Exécuté (code) : images · base · blocs | Visible (MP4) : contrôle | Verdict |
|---|---|---|---|---|---|
| P01 | S1 | 0.0–2.0 s · S1.mp4 · 9→61 · gel 7 | 0→60 · base 1.0 · GB01 | local 6: conforme (corr 0.962) ; local 52: conforme (corr 0.967) | **conforme** |
| P02 | S1 | 2.0–3.5 s · S1.mp4 · 65→103 · gel 6 | 60→105 · base 1.25 · GB01 | local 6: conforme (corr 0.955) ; local 38: conforme (corr 0.957) | **conforme** |
| P03 | S1 | 3.5–6.0 s · S1.mp4 · 107→169 · gel 12 | 105→180 · base 1.28 · GB02 | local 6: à vérifier (corr 0.780) ; local 62: partiel (corr 0.863) | **partiel** |
| P04 | S2 | 6.0–8.5 s · S2.mp4 · 9→76 · gel 7 | 180→255 · base 1.0 · GB03 | local 6: conforme (corr 0.982) ; local 67: conforme (corr 0.957) | **conforme** |
| P05 | S2 | 8.5–11.0 s · S2.mp4 · 80→147 · gel 7 | 255→330 · base 1.24 · GB03, GB04 | local 6: conforme (corr 0.916) ; local 67: partiel (corr 0.812) | **partiel** |
| P06 | S2 | 11.0–14.0 s · S2.mp4 · 151→229 · gel 11 | 330→420 · base 1.1 · GB04 | local 6: conforme (corr 0.907) ; local 78: conforme (corr 0.934) | **conforme** |
| P07 | S3 | 14.0–16.5 s · S3.mp4 · 9→76 · gel 7 | 420→495 · base 1.25 · GB05 | local 6: conforme (corr 0.903) ; local 67: conforme (corr 0.944) | **conforme** |
| P08 | S3 | 16.5–18.5 s · S3.mp4 · 80→132 · gel 7 | 495→555 · base 1.28 · GB05, GB06 | local 6: conforme (corr 0.941) ; local 52: conforme (corr 0.945) | **conforme** |
| P09 | S3 | 18.5–21.0 s · S3.mp4 · 136→199 · gel 11 | 555→630 · base 1.0 · GB06 | local 6: conforme (corr 0.985) ; local 63: conforme (corr 0.988) | **conforme** |
| P10 | S4 | 21.0–23.5 s · S4.mp4 · 9→78 · gel 5 | 630→705 · base 1.24 · GB07 | local 6: conforme (corr 0.941) ; local 69: conforme (corr 0.947) | **conforme** |
| P11 | S4 | 23.5–26.5 s · S4.mp4 · 82→166 · gel 5 | 705→795 · base 1.05 · GB07 | local 6: conforme (corr 0.929) ; local 84: partiel (corr 0.840) | **partiel** |
| P12 | S4 | 26.5–30.0 s · S4.mp4 · 170→244 · gel 30 | 795→900 · base 1.24 · GB08 | local 6: partiel (corr 0.866) ; local 74: conforme (corr 0.924) | **partiel** |

Sources : `render_plan_v4_demo.json` (déclaré) · `reports/execution_manifest_v4.json` (exécuté par `engine/motion_v4.py`) · `reports/final_master_checks.json` (mesuré dans les pixels du MP4).
