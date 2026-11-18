"""Moteur graphique adaptatif V5 — sixième brique.

Ce que fait ce module : afficher les six champs commerciaux (nom, produit, prix, whatsapp,
quartier, accroche) **sans jamais casser la composition**, en lisant tout dans
`config/T1_worldclass_v5.json`. Aucune coordonnée de bloc, aucune taille de police, aucune
couleur et aucune durée d'animation n'est écrite en dur ici.

Sept mécanismes
---------------
1. **Slots sémantiques** — `top_left`, `top_editorial`, `lower_third`, `end_packshot`. Le moteur
   mesure les vrais textes (métriques de police) et en déduit la boîte de la carte.
2. **Cartes Frosted Glass** — flou du fond réellement présent derrière la carte (calculé une fois
   par bloc et par image, à 1/4 de résolution), fond sombre translucide, bordure crème, ombre
   douce, coins arrondis, masque anticrénelé.
3. **Scrim contextuel** — plus aucun vignettage global : seules les zones qui portent du texte
   sont assombries, et seulement si le contraste mesuré l'exige.
4. **Animations typographiques** — masque de révélation ligne par ligne, mot à mot, rebond
   `easeOutBack` réel, chiffres tabulaires (chasse fixe calculée), filet qui pousse.
5. **Ajustement des textes** — 1 à 40 caractères pour le nom, 1 à 32 pour le produit, accroche
   facultative, quartier avec séparateurs `,` `—` `-` `/`, prix FCFA, WhatsApp tabulaire.
6. **Protection des sujets** — les boîtes sont confrontées aux zones protégées issues de
   l'analyseur (produit, visage, yeux/bouche, mains). En cas de collision, le bloc est déplacé
   ou rétréci, jamais posé sur le sujet.
7. **Contraste** — mesure WCAG du fond réel sous le texte ; renforcement du scrim jusqu'à la
   cible de 4,5:1, plafonné par la configuration.

    from engine.adaptive_graphics_v5 import GraphicsV5
    g = GraphicsV5("config/T1_worldclass_v5.json", data, analyzer)
    frame = g.draw(frame_bgr, fno)
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- #
def _clamp01(t: float) -> float:
    return max(0.0, min(1.0, float(t)))


def ease_out_cubic(t: float) -> float:
    t = _clamp01(t)
    return 1 - (1 - t) ** 3


def ease_out_expo(t: float) -> float:
    t = _clamp01(t)
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def ease_in_out_quad(t: float) -> float:
    t = _clamp01(t)
    return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2


def ease_out_back(t: float, s: float = 1.70158) -> float:
    """Vrai rebond `easeOutBack` : dépasse 1 puis revient (jamais un alias d'une autre courbe)."""
    t = _clamp01(t)
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


COURBES = {"linear": _clamp01, "easeOutCubic": ease_out_cubic, "easeOutExpo": ease_out_expo,
           "easeOutQuint": lambda t: 1 - (1 - _clamp01(t)) ** 5,
           "easeInOutQuad": ease_in_out_quad, "easeOutBack": ease_out_back,
           "easeSmooth": lambda t: (lambda u: u * u * u * (u * (u * 6 - 15) + 10))(_clamp01(t))}


def courbe(nom: str | None):
    return COURBES.get(nom or "easeOutCubic", ease_out_cubic)


def luminance_rel(rgb: tuple[float, float, float]) -> float:
    """Luminance relative WCAG."""
    def canal(v: float) -> float:
        v = v / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (canal(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def srgb_depuis_luminance(lum: float) -> float:
    """Inverse de la luminance relative WCAG → valeur sRGB 0..1."""
    lum = max(0.0, min(1.0, float(lum)))
    v = 1.055 * (lum ** (1 / 2.4)) - 0.055 if lum > 0.0031308 else 12.92 * lum
    return max(0.0, min(1.0, v))


def alpha_scrim_requis(couleur_texte: tuple[int, int, int], fond: tuple[float, float, float],
                       cible: float) -> float:
    """Opacité de scrim nécessaire pour atteindre `cible` sur un fond donné (0 si déjà conforme)."""
    if contraste(couleur_texte, fond) >= cible:
        return 0.0
    lt = luminance_rel(couleur_texte)
    lb_cible = (lt + 0.05) / cible - 0.05
    if lb_cible <= 0.0:
        # la cible exigerait une luminance négative : aucun scrim sombre ne peut l'atteindre.
        # C'est la carte (aplat, bouton) qui porte alors le contraste — on ne dégrade pas l'image.
        return 0.0
    v_cible = srgb_depuis_luminance(lb_cible) * 255.0
    v_fond = srgb_depuis_luminance(luminance_rel(fond)) * 255.0
    return max(0.0, min(0.95, 1.0 - v_cible / max(1.0, v_fond)))


def contraste(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    la, lb = luminance_rel(a), luminance_rel(b)
    grand, petit = max(la, lb), min(la, lb)
    return (grand + 0.05) / (petit + 0.05)


SEPARATEURS = [",", " — ", "—", " - ", "/", "·"]


@dataclass
class Ligne:
    texte: str
    y: float
    largeur: float
    taille: int


@dataclass
class Element:
    type: str
    boite: tuple[float, float, float, float]      # x, y, l, h en pixels
    couleur: tuple[int, int, int]
    alpha: float = 1.0
    police: ImageFont.FreeTypeFont | None = None
    lignes: list[Ligne] = field(default_factory=list)
    animation: str = "fondu"
    decalage_f: int = 0
    parametres: dict[str, Any] = field(default_factory=dict)


@dataclass
class Bloc:
    id: str
    nom: str
    carte: tuple[float, float, float, float] | None
    rayon: int
    remplissage: tuple[int, int, int] | None
    alpha_carte: float
    contour: tuple[int, int, int] | None
    flou_verre: bool
    ombre: dict[str, float] | None
    elements: list[Element]
    debut_f: int
    fin_f: int
    voile: str
    decisions: list[str] = field(default_factory=list)


class GraphicsV5:
    """Composition graphique adaptative, pilotée par la configuration V5."""

    def __init__(self, config_path: Path | str, data: dict[str, str], analyzer: dict[str, Any] | None = None,
                 quality: str = "standard"):
        self.cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
        self.W = int(self.cfg["canevas"]["largeur"])
        self.H = int(self.cfg["canevas"]["hauteur"])
        self.palette = {k: tuple(int(c) for c in v) for k, v in self.cfg["palette"].items()}
        self.data = {k: ("" if v is None else str(v)) for k, v in data.items()}
        self.analyzer = analyzer or {}
        self.quality = quality
        self.qcfg = self.cfg["qualite"][quality]
        self.regles = self.cfg["regles_globales"]
        self.marge = float(self.regles["marge_safe"]) * self.W
        self._fonts: dict[tuple[str, int, str], ImageFont.FreeTypeFont] = {}
        self.decisions: list[dict[str, Any]] = []
        self._zones = self._zones_protegees()
        self.blocs = self._construire()

    # -- ressources --------------------------------------------------------- #
    def police(self, famille: str, taille: int, graisse: str | None) -> ImageFont.FreeTypeFont:
        graisse = graisse or self.cfg["polices"][famille]["graisse_defaut"]
        cle = (famille, int(taille), graisse)
        if cle not in self._fonts:
            f = ImageFont.truetype(str(ROOT / self.cfg["polices"][famille]["fichier"]), int(taille))
            try:
                f.set_variation_by_name(graisse)
            except (AttributeError, OSError, ValueError):
                pass
            self._fonts[cle] = f
        return self._fonts[cle]

    def _mesure(self, texte: str, police: ImageFont.FreeTypeFont) -> float:
        return float(police.getlength(texte))

    # -- texte : ajustement et césure --------------------------------------- #
    def _mots(self, texte: str) -> list[str]:
        return [m for m in texte.split(" ") if m]

    def ajuster(self, texte: str, famille: str, graisse: str, taille_max: int, taille_min: int,
                largeur: float, lignes_max: int) -> tuple[ImageFont.FreeTypeFont, int, list[str]]:
        """Diminue la taille jusqu'à tenir dans `largeur` × `lignes_max`, sans jamais couper un mot."""
        texte = " ".join(texte.split())
        if not texte:
            return self.police(famille, taille_min, graisse), taille_min, []
        taille = int(taille_max)
        while taille >= taille_min:
            f = self.police(famille, taille, graisse)
            lignes = self._repartir(self._mots(texte), f, largeur)
            if len(lignes) <= lignes_max:
                return f, taille, lignes
            taille -= 1
        f = self.police(famille, taille_min, graisse)
        return f, taille_min, self._repartir(self._mots(texte), f, largeur)

    def _repartir(self, mots: list[str], police: ImageFont.FreeTypeFont, largeur: float) -> list[str]:
        """Césure aux frontières de mots, équilibrée : aucune coupure à l'intérieur d'un mot."""
        lignes: list[str] = []
        courant = ""
        for mot in mots:
            essai = f"{courant} {mot}".strip()
            if self._mesure(essai, police) <= largeur or not courant:
                courant = essai
            else:
                lignes.append(courant)
                courant = mot
        if courant:
            lignes.append(courant)
        # équilibrage : on essaie de réduire l'écart entre lignes sans dépasser la largeur
        return lignes

    def _segments(self, texte: str) -> list[str]:
        """Quartier / accroche : respecte les séparateurs naturels saisis par le commerçant."""
        for sep in SEPARATEURS:
            if sep in texte and len(texte.split(sep)) in (2, 3):
                parts = [p.strip() for p in texte.split(sep) if p.strip()]
                if len(parts) >= 2:
                    return parts
        return []

    # -- zones protégées ---------------------------------------------------- #
    def _zones_protegees(self) -> dict[str, list[dict[str, Any]]]:
        """Zones à ne pas couvrir, par scène, dérivées de l'analyseur (jamais inventées)."""
        zones: dict[str, list[dict[str, Any]]] = {s: [] for s in ("S1", "S2", "S3", "S4")}
        rayon = float(self.cfg["zones_protegees"]["sujet"]["rayon_defaut"])
        for scene in ("S1", "S2", "S3", "S4"):
            info = next((s for s in self.analyzer.get("scenes", []) if s["scene"] == scene), None)
            if not info:
                continue
            ancre = info.get("ancre_sujet", {})
            if scene == "S3" and ancre.get("visage"):
                v = ancre["visage"]
                zones[scene].append({"nom": "visage", "type": "rect",
                                     "x": v["x"], "y": v["y"], "largeur": v["w"], "hauteur": v["h"],
                                     "priorite": 0})
                zones[scene].append({"nom": "yeux_bouche", "type": "rect",
                                     "x": v["x"] + 0.08 * v["w"], "y": v["y"] + 0.22 * v["h"],
                                     "largeur": 0.84 * v["w"], "hauteur": 0.66 * v["h"], "priorite": 0})
            zones[scene].append({"nom": "sujet", "type": "cercle", "x": ancre.get("x", 0.5),
                                 "y": ancre.get("y", 0.5), "rayon": rayon, "priorite": 1})
        mains = self.cfg["zones_protegees"]["mains"]
        if mains.get("actif"):
            z = mains["zone"]
            zones["S1"].append({"nom": "mains", "type": "rect", **z, "priorite": 2})
        return zones

    def _collision(self, boite: tuple[float, float, float, float], zones: list[dict[str, Any]]) -> tuple[float, list[str]]:
        """Part de la surface du bloc qui recouvre une zone protégée, et les zones touchées."""
        x, y, w, h = boite
        aire = max(1.0, w * h)
        touche, pire = [], 0.0
        for z in zones:
            if z["type"] == "rect":
                zx, zy = z["x"] * self.W, z["y"] * self.H
                zw, zh = z["largeur"] * self.W, z["hauteur"] * self.H
                ix = max(0.0, min(x + w, zx + zw) - max(x, zx))
                iy = max(0.0, min(y + h, zy + zh) - max(y, zy))
            else:
                cx, cy = z["x"] * self.W, z["y"] * self.H
                r = z["rayon"] * self.W
                # échantillonnage déterministe 16×16 : bien plus juste que la boîte englobante
                n = 16
                dedans = 0
                for iy_ in range(n):
                    py = y + (iy_ + 0.5) * h / n
                    for ix_ in range(n):
                        px = x + (ix_ + 0.5) * w / n
                        if (px - cx) ** 2 + (py - cy) ** 2 <= r * r:
                            dedans += 1
                part = dedans / (n * n)
                if part > 0.02:
                    touche.append(z["nom"])
                    pire = max(pire, part)
                continue
            part = (ix * iy) / aire
            if part > 0.02:
                touche.append(z["nom"])
                pire = max(pire, part)
        return pire, touche

    # -- construction des blocs -------------------------------------------- #
    def _construire(self) -> dict[str, Bloc]:
        blocs: dict[str, Bloc] = {}
        slots = self.cfg["slots"]
        fenetres = self.cfg["fenetres_blocs"]
        # ordre de construction : les piles déclarées sont traitées de bas en haut
        ordre = list(self.cfg["blocs"].keys())
        for slot in slots.values():
            pile = slot.get("pile")
            if pile:
                connus = [b for b in pile["ordre"] if b in ordre]
                ordre = [b for b in ordre if b not in connus] + connus
        occupation: dict[str, float] = {}          # reste à empiler, par slot
        for bid in ordre:
            conf = self.cfg["blocs"][bid]
            champ = conf.get("champ", "")
            valeur = self.data.get(champ, "")
            if conf.get("facultatif") and not valeur.strip():
                self.decisions.append({"bloc": bid, "decision": "non affiché",
                                       "motif": conf.get("repli_v1_2", "champ vide")})
                continue
            if not valeur.strip():
                self.decisions.append({"bloc": bid, "decision": "non affiché", "motif": f"champ « {champ} » vide"})
                continue

            slot = slots[conf["slot"]]
            sx, sy = slot["x"] * self.W, slot["y"] * self.H
            sw, sh = slot["largeur_max"] * self.W, slot["hauteur_max"] * self.H
            carte_conf = conf.get("carte") or {}
            marge_interne = 0.028 * self.W if carte_conf.get("forme") not in (None, "aucune") else 0.0

            # 1. mesure des éléments textuels pour dimensionner la carte
            elements: list[Element] = []
            for el in conf["elements"]:
                if el["type"] == "texte":
                    texte = self.data.get(el.get("champ", champ), valeur)
                    largeur_dispo = sw - 2 * marge_interne
                    if el.get("boite_rel"):
                        largeur_dispo = sw * float(el["boite_rel"]["largeur"]) - 2 * marge_interne
                    segments = self._segments(texte) if el.get("champ") in ("quartier", "accroche") else []
                    if segments and len(segments) <= int(el.get("lignes_max", 1)):
                        f, taille, lignes = self.police(el["police"], int(el["taille_px"]),
                                                        el.get("graisse")), int(el["taille_px"]), segments
                    else:
                        f, taille, lignes = self.ajuster(texte, el["police"], el.get("graisse", ""),
                                                         int(el["taille_px"]), int(el.get("taille_min_px", el["taille_px"])),
                                                         largeur_dispo, int(el.get("lignes_max", 1)))
                    hauteur_ligne = taille * 1.18
                    largeur_reelle = max((self._mesure(l, f) for l in lignes), default=0.0)
                    elements.append(Element(
                        type="texte", boite=(0, 0, largeur_reelle, hauteur_ligne * len(lignes)),
                        couleur=self.palette[el["couleur"]],
                        alpha=float(el.get("opacite", 1.0)), police=f,
                        lignes=[Ligne(l, i * hauteur_ligne, self._mesure(l, f), taille) for i, l in enumerate(lignes)],
                        animation=el.get("animation", "fondu"), decalage_f=int(el.get("decalage_f", 0)),
                        parametres=el))
                elif el["type"] == "accent":
                    b = el["boite"]
                    rel = el.get("unite") == "rel_carte"
                    if rel:                            # exprimé en fraction de la carte, résolu plus bas
                        elements.append(Element(type="accent", boite=(b["x"], b["y"],
                                                                      b.get("taille", b.get("largeur", 0.04)),
                                                                      b.get("hauteur", 0.0) or b.get("taille", 0.04)),
                                                couleur=self.palette[el["couleur"]],
                                                animation=el.get("animation", "fondu"), parametres=el))
                    else:
                        taille = b.get("taille", b.get("largeur", 0.04)) * self.W
                        elements.append(Element(type="accent", boite=(b["x"] * self.W, b["y"] * self.H,
                                                                      taille, b.get("hauteur", 0) * self.H or taille),
                                                couleur=self.palette[el["couleur"]],
                                                animation=el.get("animation", "fondu"), parametres=el))
                elif el["type"] == "filet":
                    elements.append(Element(type="filet", boite=(0, 0, float(el.get("largeur", 0.3)) * self.W,
                                                                 float(el.get("hauteur_px", 4))),
                                            couleur=self.palette[el["couleur"]],
                                            animation=el.get("animation", "croissance_horizontale"),
                                            parametres=el))

            texte_els = [e for e in elements if e.type == "texte"]
            contenu_l = max((e.boite[2] for e in texte_els), default=0.0)
            contenu_h = sum(e.boite[3] for e in texte_els) + 0.012 * self.H * max(0, len(texte_els) - 1)
            acc = [e for e in elements if e.type == "accent"]
            for e in acc:
                contenu_l = max(contenu_l, e.boite[0] + e.boite[2])
            carte_l = min(sw, contenu_l + 2 * marge_interne) if carte_conf.get("forme") not in (None, "aucune") else min(sw, contenu_l)
            carte_h = min(sh, contenu_h + 2 * marge_interne) if carte_conf.get("forme") not in (None, "aucune") else min(sh, contenu_h)

            # 2. placement dans le slot, avec protection des sujets et empilement déclaré
            pile = slot.get("pile")
            if pile and bid in pile["ordre"]:
                espace = float(pile.get("espace", 0.012)) * self.H
                empile = occupation.get(conf["slot"], 0.0)
                if conf["slot"] in occupation:
                    boite = self._placer(bid, slot, sx, sy, sw, sh, carte_l, carte_h, conf,
                                         decalage=-empile - espace)
                else:
                    boite = self._placer(bid, slot, sx, sy, sw, sh, carte_l, carte_h, conf, decalage=0.0)
                occupation[conf["slot"]] = empile + espace + boite[3]
            else:
                boite = self._placer(bid, slot, sx, sy, sw, sh, carte_l, carte_h, conf)

            # 3. positionnement interne des éléments
            ox = boite[0] + marge_interne
            oy = boite[1] + marge_interne
            for el in elements:
                if el.type == "texte":
                    if el.parametres.get("boite_rel"):
                        br = el.parametres["boite_rel"]
                        el.boite = (boite[0] + br["x"] * boite[2], boite[1] + br["y"] * boite[3],
                                    el.boite[2], el.boite[3])
                    else:
                        el.boite = (ox, oy, el.boite[2], el.boite[3])
                        oy += el.boite[3] + 0.012 * self.H
                elif el.type == "accent":
                    if el.parametres.get("unite") == "rel_carte":
                        el.boite = (boite[0] + el.boite[0] * boite[2], boite[1] + el.boite[1] * boite[3],
                                    el.boite[2] * boite[2], el.boite[3] * boite[3])
                    else:
                        el.boite = (boite[0] + el.boite[0], boite[1] + el.boite[1], el.boite[2], el.boite[3])
                elif el.type == "filet":
                    dernier = [e for e in texte_els if e.boite[1] < 1e9]
                    y_filet = (dernier[-1].boite[1] + dernier[-1].boite[3] + 0.008 * self.H) if dernier else boite[1] + boite[3]
                    el.boite = (boite[0] + marge_interne, min(y_filet, boite[1] + boite[3] - el.boite[3]),
                                el.boite[2], el.boite[3])

            rayon = int(float(carte_conf.get("rayon", 0.03)) * self.W)
            blocs[bid] = Bloc(
                id=bid, nom=conf.get("nom", bid),
                carte=boite if carte_conf.get("forme") not in (None, "aucune") else None,
                rayon=rayon,
                remplissage=self.palette[carte_conf["remplissage"]] if carte_conf.get("remplissage") else None,
                alpha_carte=float(carte_conf.get("alpha", 1.0)),
                contour=(self.palette[carte_conf["contour"]["couleur"]]
                         if carte_conf.get("contour") else None),
                flou_verre=bool(carte_conf.get("flou_verre")) and bool(self.qcfg.get("flou_verre", True)),
                ombre=carte_conf.get("ombre"),
                elements=elements,
                debut_f=int(fenetres[bid]["debut_f"]), fin_f=int(fenetres[bid]["fin_f"]),
                voile=str(conf.get("voile", "aucun")),
                decisions=[])
        self._resoudre_collisions(blocs)
        return blocs

    def _resoudre_collisions(self, blocs: dict[str, Bloc]) -> None:
        """Deux blocs visibles en même temps ne peuvent pas se recouvrir.

        Les candidats sont testés dans un ordre fixe (aucun aléatoire) : position nominale, puis
        décalages verticaux croissants. Le premier candidat libre est retenu et consigné.
        """
        def rect(b: Bloc) -> tuple[float, float, float, float]:
            if b.carte:
                return b.carte
            xs = [e.boite[0] for e in b.elements]
            ys = [e.boite[1] for e in b.elements]
            xe = [e.boite[0] + e.boite[2] for e in b.elements]
            ye = [e.boite[1] + e.boite[3] for e in b.elements]
            return (min(xs), min(ys), max(xe) - min(xs), max(ye) - min(ys))

        def chevauche(a, b) -> float:
            ix = max(0.0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
            iy = max(0.0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
            return ix * iy

        marge = float(self.regles["marge_safe"]) * self.H
        places: list[tuple[str, tuple[float, float, float, float], int, int]] = []
        for bid, bloc in blocs.items():
            boite = rect(bloc)
            conflit = None
            for autre_id, autre_boite, d, f in places:
                if bloc.debut_f < f and d < bloc.fin_f:          # fenêtres qui se chevauchent
                    if chevauche(boite, autre_boite) > 0.02 * max(1.0, boite[2] * boite[3]):
                        conflit = autre_id
                        break
            if conflit:
                for dy in (-0.10, 0.10, -0.19, 0.19, -0.28, 0.28):
                    essai = (boite[0], boite[1] + dy * self.H, boite[2], boite[3])
                    if essai[1] < marge or essai[1] + essai[3] > self.H - marge:
                        continue
                    libre = all(not (bloc.debut_f < f and d < bloc.fin_f) or
                                chevauche(essai, autre_boite) <= 0.02 * max(1.0, boite[2] * boite[3])
                                for _, autre_boite, d, f in places)
                    if libre:
                        self._decaler(bloc, essai[1] - boite[1])
                        boite = essai
                        self.decisions.append({"bloc": bid, "decision": "décalé verticalement",
                                               "pour": "éviter le bloc " + conflit,
                                               "decalage_px": round(dy * self.H, 1)})
                        break
                else:
                    self.decisions.append({"bloc": bid, "decision": "conflit non résolu",
                                           "avec": conflit,
                                           "motif": "aucune position libre dans la marge de sécurité"})
            places.append((bid, boite, bloc.debut_f, bloc.fin_f))

    def _decaler(self, bloc: Bloc, dy: float) -> None:
        if bloc.carte:
            bloc.carte = (bloc.carte[0], bloc.carte[1] + dy, bloc.carte[2], bloc.carte[3])
        for e in bloc.elements:
            e.boite = (e.boite[0], e.boite[1] + dy, e.boite[2], e.boite[3])

    def _placer(self, bid: str, slot: dict[str, Any], sx: float, sy: float, sw: float, sh: float,
                l: float, h: float, conf: dict[str, Any],
                decalage: float = 0.0) -> tuple[float, float, float, float]:
        """Choisit la position finale : slot nominal, empilement, puis repli anti-collision.

        Les candidats sont évalués dans un ordre **fixe** (donc déterministe) : d'abord la place
        nominale du slot, puis les positions de repli. Le premier candidat qui ne recouvre pas une
        zone protégée au-delà de la tolérance déclarée est retenu.
        """
        marge = float(self.regles["marge_safe"]) * self.H
        bas = slot["ancrage"].startswith("bas")
        y_nominal = (sy + sh - h) if bas else sy
        candidats_y = [
            y_nominal + decalage,
            (sy if bas else sy + sh - h),
            sy + (sh - h) / 2,
            self.H - marge - h,
            marge,
            sy + (sh - h) / 2 + decalage,
        ]
        scenes = self._scenes_du_bloc(bid)
        zones = [z for s in scenes for z in self._zones.get(s, [])]
        tolerance = float(self.cfg["zones_protegees"].get("tolerance_recouvrement", 0.10))
        evaluations = []
        for cy in candidats_y:
            cx = min(max(marge, sx), self.W - marge - l)
            cy = min(max(marge, cy), self.H - marge - h)
            part, touche = self._collision((cx, cy, l, h), zones)
            evaluations.append((part, (cx, cy), touche))
        part, (cx, cy), touche = min(evaluations, key=lambda e: (e[0],))
        if part > tolerance:
            for facteur in (0.86, 0.74, 0.62):
                nl = l * facteur
                cx2 = min(max(marge, sx), self.W - marge - nl)
                part2, _ = self._collision((cx2, cy, nl, h), zones)
                if part2 <= tolerance:
                    self.decisions.append({"bloc": bid, "decision": "largeur réduite",
                                           "facteur": facteur,
                                           "pour": "protéger " + ", ".join(sorted(set(touche)))})
                    return (cx2, cy, nl, h)
            self.decisions.append({"bloc": bid, "decision": "maintenu avec scrim renforcé",
                                   "motif": "collision inévitable avec " + ", ".join(sorted(set(touche))),
                                   "part_couverte": round(part, 3)})
        elif touche:
            self.decisions.append({"bloc": bid, "decision": "position de repli retenue",
                                   "pour": "éviter " + ", ".join(sorted(set(touche)))})
        return (cx, cy, l, h)

    def _scenes_du_bloc(self, bid: str) -> list[str]:
        f = self.cfg["fenetres_blocs"][bid]
        debut, fin = int(f["debut_f"]), int(f["fin_f"])
        if fin <= 180:
            return ["S1"]
        if debut >= 630:
            return ["S4"]
        if debut >= 420:
            return ["S3"]
        if debut < 420 <= fin:
            return ["S2", "S3"]
        return ["S2"]

    # -- rendu -------------------------------------------------------------- #
    def actifs(self, fno: int) -> list[Bloc]:
        return [b for b in self.blocs.values() if b.debut_f <= fno < b.fin_f]

    def _enveloppe(self, bloc: Bloc, fno: int) -> tuple[float, float]:
        local = fno - bloc.debut_f
        total = max(1, bloc.fin_f - bloc.debut_f)
        entree = min(9, max(1, total // 6))
        tenue = int(self.regles.get("tenue_finale_f", 0))
        tient_jusqu_au_bout = tenue and bloc.fin_f >= tenue
        sortie = 0 if (tient_jusqu_au_bout or any(e.parametres.get("sortie") == "aucune" for e in bloc.elements)) \
            else min(10, max(1, total // 5))
        q_in = courbe("easeOutCubic")((local + 1) / entree)
        q_out = 1.0 if sortie == 0 else courbe("easeSmooth")((total - local) / sortie)
        return _clamp01(q_in), _clamp01(q_out)

    def _ouvrir(self, x: float, y: float, l: float, h: float, rayon: int) -> Image.Image:
        """Masque arrondi anticrénelé (rendu 2× puis réduction)."""
        s = 2
        m = Image.new("L", (max(1, int(l) * s), max(1, int(h) * s)), 0)
        d = ImageDraw.Draw(m)
        d.rounded_rectangle([0, 0, int(l) * s - 1, int(h) * s - 1], radius=max(1, rayon * s), fill=255)
        return m.resize((max(1, int(l)), max(1, int(h))), Image.LANCZOS)

    def _zoner(self, l: int, h: int, rayon: int) -> Image.Image:
        return self._ouvrir(0, 0, l, h, rayon)

    def _scrim(self, img: Image.Image, bloc: Bloc, need: float) -> Image.Image:
        """Assombrit localement la zone du texte, sans toucher au reste de l'image."""
        if bloc.voile == "aucun" or need <= 0:
            return img
        alpha_max = float(self.regles["scrim"]["alpha_max"])
        marge = float(self.regles["scrim"]["hauteur_marge"]) * self.H
        x, y, l, h = bloc.carte if bloc.carte else (bloc.elements[0].boite[0], bloc.elements[0].boite[1],
                                                    max(e.boite[0] + e.boite[2] for e in bloc.elements) - bloc.elements[0].boite[0],
                                                    max(e.boite[1] + e.boite[3] for e in bloc.elements) - bloc.elements[0].boite[1])
        x0 = int(max(0, x - marge * 0.7))
        y0 = int(max(0, y - marge))
        x1 = int(min(self.W, x + l + marge * 0.7))
        y1 = int(min(self.H, y + h + marge))
        if x1 <= x0 or y1 <= y0:
            return img
        alpha = min(alpha_max, need)
        crop = np.asarray(img.crop((x0, y0, x1, y1))).astype(np.float32)
        # dégradé doux : plein au centre, nul aux bords
        hh, ww = crop.shape[:2]
        # plein à l'intérieur du cadre de texte, retombée douce dans la marge
        my = max(1.0, hh * 0.22)
        mx = max(1.0, ww * 0.10)
        gy = np.clip(np.minimum(np.arange(hh), np.arange(hh)[::-1]) / my + 0.55, 0, 1)
        gx = np.clip(np.minimum(np.arange(ww), np.arange(ww)[::-1]) / mx + 0.45, 0, 1)
        masque = np.clip(np.minimum(gy[:, None], gx[None, :]), 0, 1) ** 0.6
        assombri = crop * (1 - alpha * masque[..., None])
        out = img.copy()
        out.paste(Image.fromarray(np.clip(assombri, 0, 255).astype(np.uint8)), (x0, y0))
        return out

    def _fond_sous_texte(self, img: Image.Image, bloc: Bloc) -> tuple[float, float, float] | None:
        """Couleur moyenne du fond réel sous les textes du bloc (hors pixels de texte)."""
        zones = [e for e in bloc.elements if e.type == "texte" and e.lignes]
        if not zones:
            return None
        xs = [min(e.boite[0] for e in zones), max(e.boite[0] + e.boite[2] for e in zones)]
        ys = [min(e.boite[1] for e in zones), max(e.boite[1] + e.boite[3] for e in zones)]
        x0, y0 = int(max(0, xs[0])), int(max(0, ys[0]))
        x1, y1 = int(min(self.W, xs[1])), int(min(self.H, ys[1]))
        if x1 <= x0 or y1 <= y0:
            return None
        tab = np.asarray(img.crop((x0, y0, x1, y1))).reshape(-1, 3).astype(np.float32)
        couleur = np.array(zones[0].couleur, dtype=np.float32)
        loin = np.abs(tab - couleur).sum(axis=1) > 90        # on écarte les pixels de glyphes
        fond = tab[loin] if loin.sum() > 32 else tab
        return tuple(float(v) for v in fond.mean(axis=0))

    def _contraste_mesure(self, img: Image.Image, bloc: Bloc) -> float:
        """Contraste WCAG entre la couleur du texte principal et le fond réel sous la boîte."""
        texte = next((e for e in bloc.elements if e.type == "texte"), None)
        if texte is None:
            return 99.0
        x, y, l, h = texte.boite
        x0, y0 = int(max(0, x)), int(max(0, y))
        x1, y1 = int(min(self.W, x + l)), int(min(self.H, y + h))
        if x1 <= x0 or y1 <= y0:
            return 99.0
        zone = np.asarray(img.crop((x0, y0, x1, y1))).astype(np.float32)
        fond = tuple(float(v) for v in zone.reshape(-1, 3).mean(axis=0)[:3])
        return contraste(texte.couleur, fond)

    def draw(self, frame_bgr: np.ndarray, fno: int) -> np.ndarray:
        blocs = self.actifs(fno)
        if not blocs:
            return frame_bgr
        img = Image.fromarray(frame_bgr[:, :, ::-1]).convert("RGB")
        for bloc in blocs:
            img = self._dessiner_bloc(img, bloc, fno)
        return np.asarray(img)[:, :, ::-1].copy()

    def _dessiner_bloc(self, img: Image.Image, bloc: Bloc, fno: int) -> Image.Image:
        q_in, q_out = self._enveloppe(bloc, fno)
        q = min(q_in, q_out)
        if q <= 0.001:
            return img

        # 1. contraste mesuré sur le fond réel, puis scrim si nécessaire
        cible = float(self.regles["contraste_cible"]) + float(self.regles.get("contraste_marge", 0.0))
        texte = next((e for e in bloc.elements if e.type == "texte" and e.lignes), None)
        # le fond évolue pendant la fenêtre du bloc : le scrim est vérifié, pas supposé
        for _ in range(3):
            fond = self._fond_sous_texte(img, bloc)
            if not (texte and fond):
                break
            mesure = contraste(texte.couleur, fond)
            if mesure >= cible:
                break
            need = min(float(self.regles["scrim"]["alpha_max"]),
                       alpha_scrim_requis(texte.couleur, fond, cible) + 0.03)
            if bloc.id not in [d.get("bloc") for d in self.decisions
                               if str(d.get("decision", "")).startswith("scrim")]:
                self.decisions.append({"bloc": bloc.id, "decision": "scrim contextuel",
                                       "contraste_mesure": round(mesure, 2), "alpha": round(need, 3)})
            img = self._scrim(img, bloc, need)

        # 2. carte (verre dépoli ou bouton plein)
        if bloc.carte:
            x, y, l, h = (int(round(v)) for v in bloc.carte)
            x, y = int(max(0, min(self.W - 1, x))), int(max(0, min(self.H - 1, y)))
            l, h = int(max(8, min(self.W - x, l))), int(max(8, min(self.H - y, h)))
            if bloc.ombre and self.qcfg.get("scrims") is not None:
                # ombre douce : silhouette décalée, floutée
                ombre = Image.new("L", img.size, 0)
                dx = int(float(bloc.ombre.get("decalage", 0.006)) * self.W)
                dy = int(float(bloc.ombre.get("decalage", 0.006)) * self.H)
                ImageDraw.Draw(ombre).rounded_rectangle([x + dx, y + dy, x + dx + l, y + dy + h],
                                                        radius=bloc.rayon, fill=int(255 * float(bloc.ombre.get("alpha", 0.3))))
                ombre = ombre.filter(ImageFilter.GaussianBlur(float(bloc.ombre.get("flou", 18))))
                noir = Image.new("RGB", img.size, (0, 0, 0))
                img = Image.composite(noir, img, ombre.point(lambda v: int(v * q)))
            if bloc.flou_verre:
                facteur = int(self.regles["flou_carte"]["reduction_calcul"])
                crop = img.crop((x, y, x + l, y + h))
                petit = crop.resize((max(1, l // facteur), max(1, h // facteur)), Image.BILINEAR)
                flou = petit.filter(ImageFilter.GaussianBlur(float(self.regles["flou_carte"]["rayon_px"]) / facteur))
                flou = flou.resize((l, h), Image.BILINEAR)
                masque = self._zoner(l, h, bloc.rayon)
                img.paste(flou, (x, y), masque.point(lambda v: int(v * q + 0.5)))
            if bloc.remplissage:
                couche = Image.new("RGBA", (l, h), (*bloc.remplissage, int(255 * bloc.alpha_carte * q)))
                img.paste(couche, (x, y), self._zoner(l, h, bloc.rayon).point(lambda v: int(v * q + 0.5)))
            if bloc.contour:
                cadre = Image.new("RGBA", (l, h), (0, 0, 0, 0))
                ImageDraw.Draw(cadre).rounded_rectangle([0, 0, l - 1, h - 1], radius=bloc.rayon,
                                                        outline=(*bloc.contour, int(92 * q)), width=1)
                img.paste(cadre, (x, y), cadre.split()[3])

        # 3. éléments
        calque = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(calque)
        for el in bloc.elements:
            a = q * el.alpha
            if el.type == "accent":
                self._accent(d, el, a)
            elif el.type == "filet":
                self._filet(d, el, a, q)
            elif el.type == "texte":
                self._texte(calque, d, el, a, q, fno - bloc.debut_f)
        img = Image.alpha_composite(img.convert("RGBA"), calque).convert("RGB")
        return img

    # -- primitives --------------------------------------------------------- #
    def _accent(self, d: ImageDraw.ImageDraw, el: Element, a: float) -> None:
        if a <= 0.01:
            return
        x, y, l, h = el.boite
        forme = el.parametres.get("forme", "pastille")
        couleur = (*el.couleur, int(255 * a))
        if forme == "pastille":
            d.ellipse([x, y, x + l, y + h], fill=couleur)
        elif forme == "barre_verticale":
            d.rounded_rectangle([x, y, x + max(3, l), y + h], radius=max(2, int(l / 2)), fill=couleur)
        else:
            d.rectangle([x, y, x + l, y + h], fill=couleur)

    def _filet(self, d: ImageDraw.ImageDraw, el: Element, a: float, q: float) -> None:
        x, y, l, h = el.boite
        pousse = q if el.animation == "croissance_horizontale" else 1.0
        if pousse <= 0.01:
            return
        d.rounded_rectangle([x, y, x + max(2.0, l * pousse), y + max(2.0, h)], radius=max(1, int(h / 2)),
                            fill=(*el.couleur, int(255 * a)))

    def _chiffres_tabulaires(self, d: ImageDraw.ImageDraw, texte: str, x: float, y: float,
                             police: ImageFont.FreeTypeFont, couleur: tuple[int, int, int, int]) -> float:
        """Chasse fixe calculée : chaque chiffre occupe la largeur du plus large (0..9)."""
        avance = max(police.getlength(str(i)) for i in range(10))
        curseur = x
        for ch in texte:
            if ch.isdigit():
                l = police.getlength(ch)
                d.text((curseur + (avance - l) / 2, y), ch, font=police, fill=couleur)
                curseur += avance
            else:
                l = police.getlength(ch)
                d.text((curseur, y), ch, font=police, fill=couleur)
                curseur += l
        return curseur - x

    def _texte(self, calque: Image.Image, d: ImageDraw.ImageDraw, el: Element, a: float, q: float,
               local: int) -> None:
        if a <= 0.01 or not el.lignes:
            return
        x, y, l, h = el.boite
        couleur = (*el.couleur, int(255 * a))
        anim = el.animation
        tabulaire = bool(el.parametres.get("chiffres_tabulaires"))

        # rebond du prix : scale easeOutBack autour du centre de la boîte
        echelle = 1.0
        if anim == "rebond_prix":
            duree = int(self.cfg["animations"]["types"]["rebond_prix"]["duree_f"])
            amplitude = float(self.cfg["animations"]["types"]["rebond_prix"]["amplitude"])
            p = _clamp01((local + 1) / max(1, duree))
            echelle = 1.0 - amplitude * (1.0 - ease_out_back(p))

        # mot à mot / ligne par ligne : décalage temporel
        for i, ligne in enumerate(el.lignes):
            if anim == "masque_revelation":
                debut = i * 3
                p = _clamp01((local - debut + 1) / 9.0)
                if p <= 0:
                    continue
                e = ease_out_expo(p)
                # masque de révélation : on découpe dans un calque intermédiaire
                largeur = max(1, int(ligne.largeur + 8))
                hauteur = int(ligne.taille * 1.5)
                inter = Image.new("RGBA", (largeur, hauteur), (0, 0, 0, 0))
                di = ImageDraw.Draw(inter)
                if tabulaire:
                    self._chiffres_tabulaires(di, ligne.texte, 0, -ligne.taille * 0.22, el.police, couleur)
                else:
                    di.text((0, -ligne.taille * 0.22), ligne.texte, font=el.police, fill=couleur)
                haut = int(hauteur * (1 - e))
                inter = inter.crop((0, haut, largeur, hauteur))
                if echelle != 1.0:
                    inter = inter.resize((max(1, int(largeur * echelle)), max(1, int(inter.height * echelle))),
                                         Image.BICUBIC)
                calque.alpha_composite(inter, (int(x), int(y + ligne.y + ligne.taille * 0.22 + haut)))
            elif anim == "mot_a_mot":
                mots = ligne.texte.split(" ")
                curseur = x
                for j, mot in enumerate(mots):
                    p = _clamp01((local - el.decalage_f - j * 2 + 1) / 8.0)
                    if p <= 0:
                        curseur += self._mesure(mot + " ", el.police)
                        continue
                    e = ease_out_expo(p)
                    a_mot = int(255 * a * e)
                    montee = (1 - e) * 8
                    d.text((curseur, y + ligne.y + montee), mot, font=el.police, fill=(*el.couleur, a_mot))
                    curseur += self._mesure(mot + " ", el.police)
            else:
                p = _clamp01((local + 1) / 8.0) if anim == "fondu" else 1.0
                a_ligne = int(255 * a * (ease_out_cubic(p) if anim == "fondu" else 1.0))
                if tabulaire:
                    self._chiffres_tabulaires(d, ligne.texte, x, y + ligne.y, el.police, (*el.couleur, a_ligne))
                else:
                    d.text((x, y + ligne.y), ligne.texte, font=el.police, fill=(*el.couleur, a_ligne))

    # -- rapport ------------------------------------------------------------ #
    def rapport(self) -> dict[str, Any]:
        return {
            "version": self.cfg["version"], "qualite": self.quality,
            "blocs": {b.id: {"nom": b.nom, "carte": [round(v, 1) for v in b.carte] if b.carte else None,
                             "fenetre_f": [b.debut_f, b.fin_f],
                             "elements": [{"type": e.type,
                                           "boite": [round(v, 1) for v in e.boite],
                                           "lignes": [l.texte for l in e.lignes],
                                           "taille_px": e.lignes[0].taille if e.lignes else None,
                                           "animation": e.animation} for e in b.elements]}
                      for b in self.blocs.values()},
            "decisions": self.decisions,
            "zones_protegees": self._zones,
        }
