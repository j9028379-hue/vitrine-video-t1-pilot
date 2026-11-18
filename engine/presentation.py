"""Rendu des blocs graphiques T1 à partir de `config/T1_presentation_v3_1.json`.

Aucune coordonnée, taille, couleur, police ou règle d'animation de bloc n'est écrite ici :
ce module lit la configuration de présentation du gabarit et l'exécute. Il ne connaît que des
*types* de primitives (carte, accent, filet, texte, texte empilé, texte en segments) et des
*types* d'entrée/sortie (glissement, échelle, fondu, mot à mot, révélation de ligne, segments).

Utilisation :
    pres = Presentation(ROOT / "config/T1_presentation_v3_1.json")
    pres.actifs(bloc, local, duree)          -> bool
    pres.dessiner(layer, draw, bloc, data, local, duree)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- #
# courbes
def _clamp01(t: float) -> float:
    return max(0.0, min(1.0, float(t)))


def ease_out_cubic(t: float) -> float:
    t = _clamp01(t)
    return 1 - (1 - t) ** 3


def ease_out_quint(t: float) -> float:
    t = _clamp01(t)
    return 1 - (1 - t) ** 5


def ease_out_expo(t: float) -> float:
    t = _clamp01(t)
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def ease_in_out_quad(t: float) -> float:
    t = _clamp01(t)
    return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2


def ease_smooth(t: float) -> float:
    t = _clamp01(t)
    return t * t * t * (t * (t * 6 - 15) + 10)


COURBES = {
    "linear": _clamp01,
    "easeOutCubic": ease_out_cubic,
    "easeOutQuint": ease_out_quint,
    "easeOutExpo": ease_out_expo,
    "easeInOutQuad": ease_in_out_quad,
    "easeSmooth": ease_smooth,
}


def courbe(nom: str | None):
    return COURBES.get(nom or "easeOutCubic", ease_out_cubic)


# --------------------------------------------------------------------------- #
class Presentation:
    """Configuration de présentation consommée par le moteur."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.cfg = json.loads(self.path.read_text(encoding="utf-8"))
        self.W = int(self.cfg["canevas"]["largeur"])
        self.H = int(self.cfg["canevas"]["hauteur"])
        self.palette = {k: tuple(v) for k, v in self.cfg["palette"].items()}
        self.polices = self.cfg["polices"]
        self.blocs: dict[str, Any] = self.cfg["blocs"]
        self._fonts: dict[tuple[str, int, str], ImageFont.FreeTypeFont] = {}

    # -- couleurs ----------------------------------------------------------- #
    def couleur(self, jeton: str, alpha_multiplicateur: float = 1.0) -> tuple[int, int, int, int]:
        nom, _, force = str(jeton).partition("@")
        base = self.palette[nom]
        alpha = int(force) if force else 255
        return (*base, int(round(alpha * _clamp01(alpha_multiplicateur)))) if alpha_multiplicateur < 1 else (*base, alpha)

    # -- typographie -------------------------------------------------------- #
    def police(self, famille: str, taille: int, graisse: str | None) -> ImageFont.FreeTypeFont:
        graisse = graisse or self.polices[famille]["graisse_defaut"]
        cle = (famille, taille, graisse)
        if cle not in self._fonts:
            chemin = ROOT / self.polices[famille]["fichier"]
            f = ImageFont.truetype(str(chemin), size=int(taille))
            try:
                f.set_variation_by_name(graisse)
            except (AttributeError, OSError):
                pass
            self._fonts[cle] = f
        return self._fonts[cle]

    def police_ajustee(self, draw, texte: str, typo: dict[str, Any], largeur: int):
        taille, mini = int(typo["taille"]), int(typo.get("taille_min", typo["taille"]))
        pas = int(self.cfg["regles_globales"].get("reduction_police_px", 1))
        while taille > mini:
            f = self.police(typo["police"], taille, typo.get("graisse"))
            if draw.textbbox((0, 0), texte, font=f)[2] <= largeur:
                return f
            taille -= pas
        return self.police(typo["police"], mini, typo.get("graisse"))

    # -- enveloppe d'un élément --------------------------------------------- #
    @staticmethod
    def enveloppe(element: dict[str, Any], local: int, duree: int) -> float:
        entree = element.get("entree") or {}
        sortie = element.get("sortie") or {}
        debut = int(entree.get("debut_f", 0))
        q_in = 1.0
        if local < debut:
            q_in = 0.0
        elif "duree_f" in entree:
            q_in = courbe(entree.get("courbe"))((local - debut) / max(1, int(entree["duree_f"])))
        q_out = 1.0
        if sortie:
            fin = duree - int(sortie.get("decalage_f", 0))
            q_out = courbe(sortie.get("courbe"))((fin - local) / max(1, int(sortie.get("duree_f", 8))))
        return min(q_in, q_out)

    # -- valeurs relatives --------------------------------------------------- #
    @staticmethod
    def _valeur(v: Any, largeur_carte: int, hauteur_carte: int) -> float:
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v)
        if s.startswith("largeur_carte"):
            base = largeur_carte
            return float(eval(s.replace("largeur_carte", str(base)), {"__builtins__": {}}))
        if s.startswith("hauteur_carte"):
            base = hauteur_carte
            return float(eval(s.replace("hauteur_carte", str(base)), {"__builtins__": {}}))
        return float(s)

    # -- carte --------------------------------------------------------------- #
    def _carte(self, element: dict[str, Any], q: float):
        boite = dict(element["boite"])
        if "centre_x" in boite:
            x0 = boite["centre_x"] - boite["largeur"] / 2
            y0 = boite["centre_y"] - boite["hauteur"] / 2
            cx, cy = boite["centre_x"], boite["centre_y"]
        else:
            x0, y0 = boite["x"], boite["y"]
            cx, cy = x0 + boite["largeur"] / 2, y0 + boite["hauteur"] / 2
        w, h = boite["largeur"], boite["hauteur"]
        entree = element.get("entree") or {}
        if entree.get("type") == "echelle":
            depart = float(entree.get("depuis", 1.0))
            arrivee = float(entree.get("vers", 1.0))
            duree = max(1, int(entree.get("duree_f", 10)))
            stabil = entree.get("stabilisation_f")
            p = courbe(entree.get("courbe"))(q if q < 1 else 1.0)
            s = depart + (arrivee - depart) * p
            if stabil:
                s -= 0.015 * ease_smooth((q * duree - 10) / max(1, int(stabil)))
            w, h = w * s, h * s
            x0, y0 = cx - w / 2, cy - h / 2
        if entree.get("type") == "glissement_horizontal":
            x0 += float(entree.get("depuis_px", 0)) * (1 - q)
        if entree.get("type") == "glissement_vertical":
            y0 += float(entree.get("depuis_px", 0)) * (1 - q)
        if entree.get("type") == "echelle" and entree.get("glissement_vertical_px"):
            y0 += float(entree["glissement_vertical_px"]) * (1 - q)
        return int(round(x0)), int(round(y0)), int(round(w)), int(round(h))

    # -- dessin -------------------------------------------------------------- #
    def dessiner(self, layer: Image.Image, draw: ImageDraw.ImageDraw, bloc_id: str,
                 donnees: dict[str, str], local: int, duree: int) -> list[str]:
        bloc = self.blocs[bloc_id]
        trace: list[str] = []
        carte = None
        champ = bloc.get("champ", "")
        for element_brut in bloc["elements"]:
            element = dict(element_brut)
            # « champ » = le champ déclaré par le bloc dans le plan (nom, produit, prix, ...)
            if element.get("source") == "champ":
                element["source"] = champ
            if element["type"] == "carte":
                q = self.enveloppe(element, local, duree)
                carte = self._carte(element, q)
                if q > 0:
                    self._dessiner_carte(layer, carte, element, q)
                continue
            if carte is None:
                carte = (0, 0, self.W, self.H)
            q = self.enveloppe(element, local, duree)
            if q <= 0:
                continue
            self._dessiner_element(draw, element, carte, q, donnees, local, duree)
            trace.append(f"{bloc_id}:{element['type']}")
        return trace

    def _dessiner_carte(self, layer: Image.Image, carte, element: dict[str, Any], q: float):
        x0, y0, w, h = carte
        forme = element.get("forme") or {}
        d = ImageDraw.Draw(layer)
        remplissage = self.couleur(forme.get("remplissage", "ink"), forme.get("alpha", 255) / 255 * q)
        contour = None
        if forme.get("contour"):
            c = forme["contour"]
            contour = self.couleur(c["couleur"], c.get("alpha", 255) / 255 * q)
        d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=int(forme.get("rayon", 0)),
                            fill=remplissage, outline=contour, width=int((forme.get("contour") or {}).get("px", 1)))

    def _dessiner_element(self, draw: ImageDraw.ImageDraw, element: dict[str, Any], carte,
                          q: float, donnees: dict[str, str], local: int, duree: int):
        cx0, cy0, cw, ch = carte
        style = element["type"]

        if style == "accent":
            self._accent(draw, element, carte, q)
            return

        if style == "filet":
            longueur = self._valeur(element["longueur"], cw, ch) if "longueur" in element else 100
            if (element.get("entree") or {}).get("type") == "revelation_ligne":
                entree = element["entree"]
                p = courbe(entree.get("courbe"))((local - int(entree.get("debut_f", 0)))
                                                 / max(1, int(entree.get("duree_f", 10))))
                longueur = longueur * p
            if longueur <= 0:
                return
            couleur = self.couleur(element.get("couleur", "orange"), element.get("alpha", 255) / 255 * q)
            x = cx0 + int(element["x"])
            y = cy0 + int(element["y"])
            ep = int(element.get("epaisseur", 2))
            draw.rounded_rectangle((x, y, x + int(longueur), y + ep),
                                   radius=int(element.get("rayon", ep // 2)), fill=couleur)
            return

        if style in ("texte", "texte_empile", "texte_segments"):
            self._texte(draw, element, carte, q, donnees, local, style)
            return

    def _accent(self, draw: ImageDraw.ImageDraw, element: dict[str, Any], carte, q: float):
        x0, y0, w, h = carte
        couleur = self.couleur(element.get("couleur", "orange"), q)
        forme = element.get("forme")
        boite = element.get("boite") or {}
        if forme == "pastille":
            bx, by = x0 + int(boite.get("x", 0)), y0 + int(boite.get("y", 0))
            draw.ellipse((bx, by, bx + int(boite["largeur"]), by + int(boite["hauteur"])), fill=couleur)
        elif forme in ("barre_laterale", "barre_verticale"):
            bx, by = x0 + int(boite.get("x", 0)), y0 + int(boite.get("y", 0))
            bh = int(boite["hauteur"])
            hauteur = (h - by + y0 - int(boite.get("y", 0)) + bh) if bh < 0 else bh
            if bh < 0:  # hauteur relative au bas de la carte
                hauteur = h + bh - int(boite.get("y", 0))
            draw.rounded_rectangle((bx, by, bx + int(boite["largeur"]), by + hauteur),
                                   radius=int(element.get("rayon", 2)), fill=couleur)
        elif forme == "epingle":
            centre = element["centre"]
            cx, cy = int(centre["x"]), int(centre["y"])
            r = int(element.get("dimensions", {}).get("rayon_tete", 11))
            pointe = int(element.get("dimensions", {}).get("pointe_px", 20))
            draw.ellipse((cx - r, cy - r - 2, cx + r, cy + r - 2), fill=couleur)
            draw.polygon([(cx - r + 2, cy + 1), (cx + r - 2, cy + 1), (cx, cy + pointe)], fill=couleur)
            interieur = self.couleur(element.get("couleur_centre", "cream"), q)
            draw.ellipse((cx - 4, cy - 8, cx + 4, cy + 0), fill=interieur)

    def _texte(self, draw: ImageDraw.ImageDraw, element: dict[str, Any], carte, q: float,
               donnees: dict[str, str], local: int, style: str):
        x0, y0, w, h = carte
        couleur = self.couleur(element.get("couleur", "cream"), q)
        typo = element["typographie"]
        majuscules = element.get("majuscules", True)
        alignement = element.get("alignement", "gauche")
        contour = element.get("contour")
        stroke = 0
        stroke_fill = None
        if contour:
            stroke = int(contour.get("px", 0))
            stroke_fill = self.couleur(contour["couleur"], contour.get("alpha", 255) / 255 * q)

        def valeur(cle: str) -> str:
            if "texte_fixe" in element:
                return element["texte_fixe"]
            if "partie" in element:
                sep = element.get("separateur", "—")
                brut = donnees.get(element["source"], "")
                morceaux = [m.strip() for m in brut.split(sep)] if sep in brut else [brut]
                idx = int(element["partie"])
                return morceaux[idx] if idx < len(morceaux) else ""
            return donnees.get(element.get("source", ""), "")

        brut = valeur("texte")
        texte = brut.upper() if majuscules else brut
        if style == "texte":
            boite = element["boite"]
            if "centre_x" in boite:
                bx = boite["centre_x"] - boite["largeur"] / 2 + int(boite.get("centre_x_depuis_carte", 0))
            elif "centre_x_depuis_carte" in boite:
                bx = x0 + w / 2 - boite["largeur"] / 2 + int(boite["centre_x_depuis_carte"])
            else:
                bx = x0 + int(boite["x"])
            by = y0 + int(boite["y"])
            entree = element.get("entree") or {}
            if entree.get("montee_px"):
                by += int(entree["montee_px"]) * (1 - q)
            f = self.police_ajustee(draw, texte, typo, int(boite["largeur"]))
            if alignement == "centre":
                draw.text((bx + boite["largeur"] / 2, by), texte, font=f, fill=couleur,
                          anchor="mt", stroke_width=stroke, stroke_fill=stroke_fill)
            else:
                draw.text((bx, by), texte, font=f, fill=couleur,
                          stroke_width=stroke, stroke_fill=stroke_fill)
            return

        if style == "texte_empile":
            mots = texte.split()
            entree = element.get("entree") or {}
            decalage = int(entree.get("decalage_f", 7))
            duree_e = max(1, int(entree.get("duree_f", 12)))
            montee = int(entree.get("montee_px", 0))
            regle = element.get("regle_taille") or {}
            for i, mot in enumerate(mots):
                p = courbe(entree.get("courbe"))((local - i * decalage) / duree_e)
                if p <= 0:
                    continue
                typo_mot = dict(typo)
                if regle and len(mot) >= int(regle.get("si_longueur_superieure_ou_egale", 99)):
                    typo_mot["taille"] = int(regle.get("taille_min_px", typo["taille"]))
                    typo_mot["taille_min"] = int(regle.get("taille_min_px", typo["taille"]))
                f = self.police(typo_mot["police"], int(typo_mot["taille"]), typo_mot.get("graisse"))
                c = self.couleur(element.get("couleur", "cream"), p * q)
                sc = None
                if contour:
                    sc = self.couleur(contour["couleur"], int(contour.get("alpha", 90)) / 255 * p * q)
                draw.text((x0 + int(element["x"]),
                           y0 + int(element["y"]) + i * int(element["interligne_px"])
                           + int((1 - p) * montee)),
                          mot, font=f, fill=c, stroke_width=stroke, stroke_fill=sc)
            return

        if style == "texte_segments":
            separateur = element.get("separateur", "·")
            morceaux = [m.strip() for m in brut.upper().split(separateur) if m.strip()][: int(element.get("segments_max", 3))]
            entree = element.get("entree") or {}
            decalage = int(entree.get("decalage_f", 4))
            duree_e = max(1, int(entree.get("duree_f", 9)))
            montee = int(entree.get("montee_px", 0))
            largeur_max = int(element.get("largeur_max_px", 400))
            for i, mot in enumerate(morceaux):
                p = courbe(entree.get("courbe"))((local - i * decalage) / duree_e)
                if p <= 0:
                    continue
                typo_i = dict(typo)
                if i == len(morceaux) - 1 and element.get("dernier_segment"):
                    typo_i = dict(element["dernier_segment"])
                f = self.police_ajustee(draw, mot, typo_i, largeur_max)
                draw.text((x0 + int(element["x"]),
                           y0 + int(element["premier_y"]) + i * int(element["interligne_px"])
                           + int((1 - p) * montee)),
                          mot, font=f, fill=self.couleur(element.get("couleur", "cream"), p * q))
