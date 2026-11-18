"""Captures d'écran et vérification de lisibilité de la fiche de tournage T1.

Produit :
  ui-screens/ecran_08_scene{n}_etat{A,B,C}.png   — les 12 états (390 × 844, ×2)
  ui-screens/lisibilite_360_scene4_etatA.png     — preuves aux tailles extrêmes
  ui-screens/lisibilite_430_scene1_etatA.png
  ui-screens/planche_12_etats.png                — planche récapitulative
  reports/verification_lisibilite.json           — mesures de mise en page et de typographie

    cd <dépôt> && python3 tools/capture_ui.py
"""
from __future__ import annotations

import http.server
import json
import socketserver
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ui-screens"
REPORTS = ROOT / "reports"
PORT = 8811
VIEWPORTS = {"360": (360, 800), "390": (390, 844), "430": (430, 932)}
CANON = "390"

MESURE_JS = """() => {
  const px = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return {font: parseFloat(cs.fontSize), lh: parseFloat(cs.lineHeight) || null,
            w: Math.round(r.width), h: Math.round(r.height),
            bottom: Math.round(r.bottom), top: Math.round(r.top)};
  };
  const sheet = document.getElementById('sheetBody');
  const cta = document.querySelector('#cta').getBoundingClientRect();
  return {
    viewport: {w: innerWidth, h: innerHeight},
    overflow_horizontal: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    cta_visible: cta.bottom <= innerHeight + 0.5 && cta.top >= 0,
    cta_font: parseFloat(getComputedStyle(document.querySelector('#cta')).fontSize),
    body_scrollable: sheet.scrollHeight > sheet.clientHeight + 1,
    body_scroll_height: sheet.scrollHeight,
    body_client_height: sheet.clientHeight,
    consigne: px('#consigne'),
    titre_section: px('.block.film .block-title'),
    item_liste: px('#listFilm li'),
    mention_voix: px('#voiceText'),
    exemple: px('#exempleText'),
    titre_scene: px('#sceneTitle'),
    duree: px('#durationLabel'),
    scene: document.querySelector('#sceneCounter').textContent,
    duree_affichee: document.querySelector('#durationLabel').textContent
  };
}"""


def serve() -> socketserver.TCPServer:
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(ROOT), **k)  # noqa: E731
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main() -> None:
    OUT.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    httpd = serve()
    url = f"http://127.0.0.1:{PORT}/simulation/index.html"
    url_capture = url + "?capture=1"
    mesures: list[dict] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])

            # ---------- 1. contrôle de mise en page sur les trois tailles ----------
            for label, (w, h) in VIEWPORTS.items():
                page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
                page.goto(url_capture, wait_until="load")
                page.wait_for_timeout(700)
                for n in range(4):
                    page.evaluate(f"window.__demo.showCard({n})")
                    page.wait_for_timeout(420)
                    m = page.evaluate(MESURE_JS)
                    m.update({"taille_ecran": label, "scene": n + 1, "etat": "A"})
                    mesures.append(m)
                if label in ("360", "430"):
                    for n, nm in ((0, "scene1"), (3, "scene4")):
                        page.evaluate(f"window.__demo.showCard({n})")
                        page.wait_for_timeout(400)
                        page.screenshot(path=str(OUT / f"lisibilite_{label}_{nm}_etatA.png"))
                page.close()

            # ---------- 2. les 12 états canoniques ----------
            w, h = VIEWPORTS[CANON]
            page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
            page.goto(url_capture, wait_until="load")
            page.wait_for_timeout(900)
            for n in range(4):
                page.evaluate(f"window.__demo.showCard({n})")
                page.wait_for_timeout(800)
                page.screenshot(path=str(OUT / f"ecran_08_scene{n + 1}_etatA_consigne.png"))

                # décompte 3 · 2 · 1 : capturé séparément, avant le départ du chronomètre
                page.evaluate("window.__demo.startRecording()")
                page.wait_for_timeout(620)
                page.screenshot(path=str(OUT / f"ecran_08_scene{n + 1}_etatB_decompte.png"))
                # le décompte dure 1,5 s : on attend le départ réel avant de figer la barre
                page.wait_for_timeout(1100)
                page.evaluate("window.__demo.freezeAt(46)")
                page.wait_for_timeout(260)
                page.screenshot(path=str(OUT / f"ecran_08_scene{n + 1}_etatB_enregistrement.png"))
                page.evaluate("document.getElementById('rec').classList.remove('on')")
                page.evaluate("document.getElementById('marks').classList.remove('on')")

                page.evaluate("window.__demo.finishRecording()")
                page.wait_for_timeout(700)
                page.screenshot(path=str(OUT / f"ecran_08_scene{n + 1}_etatC_validation.png"))

            # preuve : la fiche défile jusqu'à l'exemple et au bouton
            page.evaluate("window.__demo.showCard(0)")
            page.wait_for_timeout(500)
            page.evaluate("document.getElementById('sheetBody').scrollTop = 9999")
            page.wait_for_timeout(400)
            page.screenshot(path=str(OUT / "ecran_08_scene1_etatA_bas_de_fiche.png"))

            page.evaluate("window.__demo.showMontage()")
            page.wait_for_timeout(2600)
            page.screenshot(path=str(OUT / "ecran_09_montage_en_cours.png"))
            page.wait_for_timeout(2600)
            page.screenshot(path=str(OUT / "ecran_09_montage_pret.png"))

            page.evaluate("window.__demo.forceEtat('ad')")
            page.wait_for_timeout(1600)
            page.screenshot(path=str(OUT / "ecran_10_publicite.png"))

            page.evaluate("window.__demo.forceEtat('end')")
            page.wait_for_timeout(500)
            page.screenshot(path=str(OUT / "ecran_11_fin.png"))

            # ---------- 3. la barre de navigation de démonstration ----------
            page.goto(url, wait_until="load")
            page.wait_for_timeout(600)
            page.evaluate("window.__demo.showCard(1)")
            page.wait_for_timeout(400)
            page.click("#demoFab")
            page.wait_for_timeout(400)
            page.screenshot(path=str(OUT / "ecran_00_navigation_demo.png"))
            browser.close()
    finally:
        httpd.shutdown()

    (REPORTS / "verification_lisibilite.json").write_text(
        json.dumps({"cible": {"consigne": "17–18 px", "listes": "14–16 px", "titres": "12–14 px",
                              "voix": "14–15 px", "exemple": "14–15 px", "bouton": "16–18 px"},
                    "mesures": mesures}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # synthèse
    ok = True
    for m in mesures:
        c = m["consigne"]["font"]; li = m["item_liste"]["font"]; ts = m["titre_section"]["font"]
        vx = m["mention_voix"]["font"]; ex = m["exemple"]["font"]; ct = m["cta_font"]
        cond = (17 <= c <= 18.6 and 14 <= li <= 16.5 and 12 <= ts <= 14.5
                and 14 <= vx <= 15.5 and 14 <= ex <= 15.5 and 16 <= ct <= 18.5
                and not m["overflow_horizontal"] and m["cta_visible"])
        ok = ok and cond
        print(f"{m['taille_ecran']}px scène {m['scene']}: consigne {c} · listes {li} · titres {ts} · "
              f"voix {vx} · exemple {ex} · bouton {ct} · débordement {m['overflow_horizontal']} · "
              f"bouton visible {m['cta_visible']} → {'OK' if cond else 'À REVOIR'}")
    print("Vérification globale :", "OK" if ok else "ÉCARTS")
    print(f"{len(list(OUT.glob('*.png')))} captures dans ui-screens/")


if __name__ == "__main__":
    main()
