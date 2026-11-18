"""Tableau final « JSON (déclaré) / code (exécuté) / MP4 (visible) » des 12 plans."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    plan = json.loads((ROOT / "render_plan_v4_demo.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "reports/execution_manifest_v4.json").read_text(encoding="utf-8"))
    checks = json.loads((ROOT / "reports/final_master_checks.json").read_text(encoding="utf-8"))
    cfg = json.loads((ROOT / "config/T1_presentation_v3_1.json").read_text(encoding="utf-8"))

    mesures: dict[str, list[dict]] = {}
    for r in checks["plans"]:
        mesures.setdefault(r["plan"], []).append(r)

    lignes = []
    for decl, exec_ in zip(plan["shots"], manifest["plans"]):
        assert decl["id"] == exec_["id"]
        params = exec_["mouvement"]["parametres"]
        param_txt = ", ".join(
            f"{k}={v}" for k, v in params.items()) if params else "—"
        blocs = exec_["blocs_visibles"] or ["—"]
        ctrl = mesures.get(decl["id"], [])
        verdicts = {c["verdict"] for c in ctrl}
        verdict = "conforme" if verdicts == {"conforme"} else ("partiel" if "partiel" in verdicts
                                                              else next(iter(verdicts)))
        lignes.append({
            "plan": decl["id"],
            "scene": decl["scene"],
            "json_declare": {
                "sortie_s": [round(int(decl["out_start_f"]) / 30, 2), round(int(decl["out_end_f"]) / 30, 2)],
                "source": decl["source"]["file"].split("/")[-1],
                "fenetre_images": [decl["source"]["in_frame"],
                                   decl["source"]["in_frame"] + decl["source"]["source_frames"] - 1],
                "gel_fin_f": decl["source"].get("freeze_tail_f", 0),
                "mouvement": [decl["zoom_curve"]["movement_id"], decl["zoom_curve"]["base"], params],
                "transition": decl["transition_out"],
            },
            "code_execute": {
                "sortie_images": [exec_["sortie"]["debut_f"], exec_["sortie"]["fin_f"]],
                "fenetre_images": [exec_["source"]["in_frame"], exec_["source"]["fin_reelle"]],
                "base_appliquee": exec_["mouvement"]["base"],
                "blocs": blocs,
                "config_presentation": sorted({b.split(":")[0] for b in blocs if b != "—"}),
            },
            "mp4_visible": {
                "controle": [{c["local"]: {"verdict": c["verdict"],
                                           "correlation": c["correlation_au_declare"],
                                           "zoom_mesure": c["zoom_declare"]}} for c in ctrl],
                "verdict": verdict,
            },
        })

    out = {"plan": "render_plan_v4_demo.json", "presentation": "config/T1_presentation_v3_1.json",
           "manifeste": "reports/execution_manifest_v4.json", "controle": "reports/final_master_checks.json",
           "blocs_configures": sorted(cfg["blocs"]), "lignes": lignes}
    (ROOT / "reports/tableau_final_json_code_mp4.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def f(x):
        return "—" if x in (None, "", []) else str(x)

    md = ["# Tableau final JSON / code / MP4 — 12 plans T1", "",
          f"Configuration de présentation consommée : `{out['presentation']}` — blocs : "
          + ", ".join(out["blocs_configures"]), "",
          "| # | Scène | Déclaré (JSON) : sortie · source · fenêtre · gel | Exécuté (code) : images · base · blocs | Visible (MP4) : contrôle | Verdict |",
          "|---|---|---|---|---|---|"]
    for l in lignes:
        d, e, v = l["json_declare"], l["code_execute"], l["mp4_visible"]
        ctrl = " ; ".join(f"local {k}: {val['verdict']} (corr {val['correlation']:.3f})"
                          for m in v["controle"] for k, val in m.items())
        md.append(f"| {l['plan']} | {l['scene']} | {d['sortie_s'][0]}–{d['sortie_s'][1]} s · {d['source']} · "
                  f"{d['fenetre_images'][0]}→{d['fenetre_images'][1]} · gel {d['gel_fin_f']} | "
                  f"{e['sortie_images'][0]}→{e['sortie_images'][1]} · base {e['base_appliquee']} · "
                  f"{', '.join(e['blocs'])} | {ctrl} | **{v['verdict']}** |")
    md += ["", "Sources : `render_plan_v4_demo.json` (déclaré) · `reports/execution_manifest_v4.json` "
               "(exécuté par `engine/motion_v4.py`) · `reports/final_master_checks.json` (mesuré dans les pixels du MP4)."]
    (ROOT / "reports/tableau_final_json_code_mp4.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:8]))
    print("…", len(lignes), "lignes écrites")


if __name__ == "__main__":
    main()
