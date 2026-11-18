"""Captures d'écran de la maquette de parcours (Playwright + Chromium local).

Produit, pour chaque scène, les trois états (A consigne, B enregistrement, C validation),
plus la progression du montage, la publicité finale et l'écran de fin.

    cd <dépôt> && python3 tools/capture_ui.py
"""
from __future__ import annotations

import http.server
import socketserver
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ui-screens"
PORT = 8801


def serve() -> socketserver.TCPServer:
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(ROOT), **k)  # noqa: E731
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def shot_phone(page, path: Path) -> None:
    page.locator(".phone").screenshot(path=str(path))


def shot_page(page, path: Path) -> None:
    page.screenshot(path=str(path), full_page=False)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    httpd = serve()
    url = f"http://127.0.0.1:{PORT}/simulation/index.html"
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
            page = browser.new_page(viewport={"width": 1360, "height": 1020}, device_scale_factor=2)
            page.goto(url, wait_until="load")
            page.wait_for_timeout(1200)

            for n in range(4):
                page.evaluate(f"window.__demo.showCard({n})")
                page.wait_for_timeout(900)
                shot_phone(page, OUT / f"ecran_08_scene{n+1}_etatA_consigne.png")
                if n == 0:
                    shot_page(page, OUT / "ecran_08_scene1_etatA_page_complete.png")

                page.evaluate("window.__demo.forceEtat('B')")
                page.wait_for_timeout(250)          # laisse l'enregistrement se terminer avant de figer la barre
                page.evaluate("window.__demo.setProgress(46)")
                page.wait_for_timeout(400)
                shot_phone(page, OUT / f"ecran_08_scene{n+1}_etatB_enregistrement.png")

                page.evaluate("window.__demo.forceEtat('C')")
                page.wait_for_timeout(700)
                shot_phone(page, OUT / f"ecran_08_scene{n+1}_etatC_validation.png")

            page.evaluate("window.__demo.scene(3); window.__demo.showCard(3)")
            page.wait_for_timeout(400)
            page.evaluate("window.__demo.forceEtat('C')")
            page.wait_for_timeout(300)
            shot_phone(page, OUT / "ecran_08_scene4_etatC_voir_mon_montage.png")

            page.evaluate("window.__demo.showMontage()")
            page.wait_for_timeout(2600)
            shot_phone(page, OUT / "ecran_09_montage_en_cours.png")
            page.wait_for_timeout(2500)
            shot_phone(page, OUT / "ecran_09_montage_pret.png")

            page.evaluate("window.__demo.forceEtat('ad')")
            page.wait_for_timeout(1800)
            shot_phone(page, OUT / "ecran_10_publicite.png")
            shot_page(page, OUT / "ecran_10_publicite_page_complete.png")

            page.evaluate("window.__demo.forceEtat('end')")
            page.wait_for_timeout(600)
            shot_phone(page, OUT / "ecran_11_fin.png")

            browser.close()
    finally:
        httpd.shutdown()
    files = sorted(OUT.glob("*.png"))
    print(f"{len(files)} captures dans {OUT.relative_to(ROOT)}")
    for f in files:
        print("  ", f.name)


if __name__ == "__main__":
    main()
