"""Bibliothèque de transitions « Food Cinema » — cinquième brique du moteur V5.

Six transitions, toutes pilotées par le plan JSON (`config/T1_worldclass_v5.json` →
`transitions.catalogue`). Ce module ne contient **aucune durée, aucune position, aucun seuil
décisionnel** : il reçoit `p` (progression 0..1), les paramètres déclarés et deux images.

Contrat commun
--------------
* `old` et `new` sont deux images **déjà remappées et vivantes** : le rendu les fait avancer
  toutes les deux pendant la transition. Aucune image figée n'est utilisée comme plan sortant.
* Les fonctions sont pures : mêmes entrées → mêmes sorties, sans aléatoire ni état.
* Aucun bord dupliqué : les zooms et translations sont calculés en *échantillonnant* à
  l'intérieur de l'image (`cv2.warpAffine` avec matrice inverse), jamais en repliant les bords.

Correspondance Android (voir `reports/PORTABILITY_ANDROID_T1.md`)
----------------------------------------------------------------
Chaque transition correspond à un shader fragmentaire GLSL ES 2.0 dont la mathématique est
donnée dans la docstring de la fonction.
"""
from __future__ import annotations

import math
from typing import Any

import cv2
import numpy as np

Palette = dict[str, tuple[int, int, int]]


# --------------------------------------------------------------------------- #
# utilitaires géométriques (matrices affines, aucune coordonnée entière)
def _sample(img: np.ndarray, zoom: float, tx: float, ty: float, size: tuple[int, int],
            interpolation: int = cv2.INTER_CUBIC) -> np.ndarray:
    """Échantillonne `img` avec un zoom et une translation exprimés en fraction de la taille.

    zoom > 1 ⇒ on prélève une fenêtre plus petite (aucun bord n'apparaît).
    tx, ty ∈ [-1, 1] : déplacement relatif de la fenêtre (1 = une largeur).
    """
    h, w = img.shape[:2]
    W, H = size
    z = max(1e-6, float(zoom))
    # matrice directe : (x,y) → z*(x - w/2) + w/2 + tx*w
    m = np.array([[z, 0, (1 - z) * w / 2 + tx * w],
                  [0, z, (1 - z) * h / 2 + ty * h]], dtype=np.float32)
    # on ramène à la taille de sortie
    m[0, :] *= W / w
    m[1, :] *= H / h
    # cv2.warpAffine attend la transformation DIRECTE (source → destination) : il inverse
    # lui-même en interne. Passer l'inverse ici échantillonnait hors champ et repliait les bords.
    return cv2.warpAffine(img, m, (W, H), flags=interpolation, borderMode=cv2.BORDER_REPLICATE)


def _motion_blur(img: np.ndarray, length_px: int, horizontal: bool = True) -> np.ndarray:
    """Flou directionnel par accumulation de copies décalées (coût linéaire, borné)."""
    length_px = int(max(0, min(64, length_px)))
    if length_px < 3:
        return img
    samples = min(12, max(3, length_px // 3))
    acc = np.zeros_like(img, dtype=np.float32)
    for i in range(samples):
        t = i / (samples - 1) - 0.5
        d = t * length_px
        m = np.float32([[1, 0, d], [0, 1, 0]]) if horizontal else np.float32([[1, 0, 0], [0, 1, d]])
        acc += cv2.warpAffine(img, m, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REFLECT_101).astype(np.float32)
    return np.clip(acc / samples, 0, 255).astype(np.uint8)


def _screen(a: np.ndarray, b: np.ndarray, alpha: float) -> np.ndarray:
    """Composition Screen bornée : 1-(1-a)(1-b), mélangée par alpha."""
    af = a.astype(np.float32) / 255.0
    bf = b.astype(np.float32) / 255.0 * float(alpha)
    return np.clip((1 - (1 - af) * (1 - bf)) * 255.0, 0, 255).astype(np.uint8)


def _bloom(img: np.ndarray, seuil: float = 0.72, force: float = 0.55) -> np.ndarray:
    """Bloom limité aux hautes lumières (aucune surexposition du produit)."""
    lum = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    mask = np.clip((lum - seuil) / max(1e-3, 1 - seuil), 0, 1)[..., None]
    small = cv2.resize(img, (img.shape[1] // 4, img.shape[0] // 4), interpolation=cv2.INTER_AREA)
    soft = cv2.GaussianBlur(small, (0, 0), 6.0)
    soft = cv2.resize(soft, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
    return np.clip(img.astype(np.float32) + soft.astype(np.float32) * mask * force, 0, 255).astype(np.uint8)


def _ease(name: str, t: float) -> float:
    t = max(0.0, min(1.0, float(t)))
    if name == "easeOutExpo":
        return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)
    if name == "easeOutQuint":
        return 1 - (1 - t) ** 5
    if name == "easeOutCubic":
        return 1 - (1 - t) ** 3
    if name == "easeInOutQuad":
        return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2
    return t


def _rounded_mask(size: tuple[int, int], w: int, h: int, rayon: int) -> np.ndarray:
    """Masque arrondi anticrénelé (rendu 2× puis réduction)."""
    W, H = size
    s = 2
    m = np.zeros((h * s, w * s), dtype=np.uint8)
    cv2.rectangle(m, (rayon * s, 0), (w * s - rayon * s, h * s), 255, -1)
    cv2.rectangle(m, (0, rayon * s), (w * s, h * s - rayon * s), 255, -1)
    for cx, cy in ((rayon * s, rayon * s), (w * s - rayon * s, rayon * s),
                   (rayon * s, h * s - rayon * s), (w * s - rayon * s, h * s - rayon * s)):
        cv2.circle(m, (cx, cy), rayon * s, 255, -1)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0


# --------------------------------------------------------------------------- #
# les six transitions
def tr_cut(old: np.ndarray, new: np.ndarray, p: float, params: dict[str, Any],
           palette: Palette, interp: int = cv2.INTER_CUBIC) -> np.ndarray:
    """Coupe franche : le plan entrant remplace le sortant sans aucun effet."""
    return new.copy()


def tr_flash_punch(old: np.ndarray, new: np.ndarray, p: float, params: dict[str, Any],
                   palette: Palette, interp: int = cv2.INTER_CUBIC) -> np.ndarray:
    """Flash punch — GLSL : `uv' = (uv-0.5)/z + 0.5`, z = 1+(z0-1)*(1-e), e = easeOutExpo(p).

    Zoom entrant de `zoom_depart` (1,14) vers 1,00, voile lumineux très court, flou radial
    décroissant. Aucun fantôme : le plan sortant n'est jamais mélangé, il est remplacé dès p>0.
    """
    z0 = float(params.get("zoom_depart", 1.14))
    e = _ease(str(params.get("courbe", "easeOutExpo")), p)
    z = 1.0 + (z0 - 1.0) * (1.0 - e)
    img = _sample(new, z, 0.0, 0.0, (new.shape[1], new.shape[0]), interp)
    flou = float(params.get("flou_radial_max", 3.0)) * (1.0 - e)
    if flou >= 0.8:
        small = cv2.resize(img, (img.shape[1] // 3, img.shape[0] // 3), interpolation=cv2.INTER_AREA)
        small = cv2.GaussianBlur(small, (0, 0), flou)
        img = cv2.resize(small, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
    voile = float(params.get("voile_max", 0.10)) * math.sin(math.pi * min(1.0, p * 1.6))
    if voile > 0.002:
        blanc = np.full_like(img, 255, dtype=np.uint8)
        img = cv2.addWeighted(img, 1.0 - voile, blanc, voile, 0)
    return img


def tr_warm_burn(old: np.ndarray, new: np.ndarray, p: float, params: dict[str, Any],
                 palette: Palette, interp: int = cv2.INTER_CUBIC) -> np.ndarray:
    """Warm burn — GLSL : deux zooms opposés, bloom sur seuil haut, voile Screen.

    `old` accélère vers l'avant (zoom + translation sortante), `new` entre en mouvement opposé.
    Le voile ambré/ crème est une vraie composition Screen, jamais un aplat jaune.
    """
    e = _ease(str(params.get("courbe", "easeInOutQuad")), p)
    W, H = old.shape[1], old.shape[0]
    so = float(params.get("rampe_sortante", 1.35))
    si = float(params.get("rampe_entrante", 1.30))
    a = _sample(old, 1.0 + (so - 1.0) * e, 0.10 * e, 0.0, (W, H), interp)
    b = _sample(new, 1.0 + (si - 1.0) * (1 - e), -0.10 * (1 - e), 0.0, (W, H), interp)
    a = _bloom(a, float(params.get("bloom_seuil", 0.72)), 0.35)
    b = _bloom(b, float(params.get("bloom_seuil", 0.72)), 0.35)
    w = e * e * (3 - 2 * e)                      # fondu organique entre les deux plans
    out = (a.astype(np.float32) * (1 - w) + b.astype(np.float32) * w).astype(np.uint8)
    voile = float(params.get("voile_alpha_max", 0.16)) * math.sin(math.pi * p) ** 0.8
    if voile > 0.002:
        ambre = np.zeros_like(out)
        ambre[:] = palette.get("amber", (120, 196, 255))
        out = _screen(out, ambre, voile)
        creme = np.zeros_like(out)
        creme[:] = palette.get("cream", (239, 248, 255))
        out = _screen(out, creme, voile * 0.35)
    return out


def tr_whip_blur(old: np.ndarray, new: np.ndarray, p: float, params: dict[str, Any],
                 palette: Palette, interp: int = cv2.INTER_CUBIC) -> np.ndarray:
    """Whip blur — GLSL : translation `uv.x - (1-e)`, flou proportionnel à la vitesse instantanée.

    La vitesse est la dérivée de la courbe : `v = |de/dp|`, donc le flou est maximal au milieu
    et **nul à l'atterrissage** (netteté retrouvée).
    """
    e = _ease(str(params.get("courbe", "easeInOutQuad")), p)
    dv = min(1.0, abs(1.0 - abs(2.0 * p - 1.0)))          # vitesse normalisée : 1 au centre
    v = math.sin(math.pi * p) ** 0.85                      # profil lissé de vitesse
    v = max(v, dv * 0.55)
    W, H = old.shape[1], old.shape[0]
    horiz = str(params.get("axe", "horizontal")) == "horizontal"
    a = _sample(old, 1.06, (1.0 if horiz else 0.0) * e, (0.0 if horiz else 1.0) * e, (W, H), interp)
    b = _sample(new, 1.06, -(1.0 if horiz else 0.0) * (1 - e), -(0.0 if horiz else 1.0) * (1 - e), (W, H), interp)
    blur = int(float(params.get("flou_max_px", 42)) * v)
    a = _motion_blur(a, blur, horiz)
    b = _motion_blur(b, blur, horiz)
    seam = e
    xs = np.linspace(0.0, 1.0, W, dtype=np.float32)
    feather = max(0.02, 0.09 * math.sin(math.pi * p))
    mask = np.clip((xs - (seam - feather)) / (2 * feather), 0.0, 1.0)[None, :, None]
    return (a.astype(np.float32) * (1 - mask) + b.astype(np.float32) * mask).astype(np.uint8)


def tr_portal_expand(old: np.ndarray, new: np.ndarray, p: float, params: dict[str, Any],
                     palette: Palette, interp: int = cv2.INTER_CUBIC) -> np.ndarray:
    """Portal expand — GLSL : SDF de rectangle arrondi, `alpha = smoothstep(r, r-w, sdf)`.

    Le plan sortant continue d'avancer derrière ; la fenêtre du plan entrant s'ouvre jusqu'au
    plein écran. Angles anticrénelés (masque rendu en 2×), ombre douce portée.
    """
    e = _ease(str(params.get("courbe", "easeInOutQuad")), p)
    W, H = old.shape[1], old.shape[0]
    behind = _sample(old, 1.0 + 0.05 * e, 0.03 * e, 0.0, (W, H), interp)
    front = _sample(new, 1.06 - 0.06 * e, 0.0, 0.0, (W, H), interp)

    w0 = float(params.get("largeur_rel_depart", 0.42))
    h0 = float(params.get("hauteur_rel_depart", 0.34))
    w = int(W * (w0 + (1.0 - w0) * e))
    h = int(H * (h0 + (1.0 - h0) * e))
    rayon = int(max(6, float(params.get("rayon_rel", 0.11)) * W * (1.0 - 0.7 * e)))
    x0 = (W - w) // 2
    y0 = (H - h) // 2
    mask = _rounded_mask((W, H), w, h, rayon)
    cadre = np.zeros((H, W, 1), dtype=np.float32)
    cadre[y0:y0 + h, x0:x0 + w, 0] = mask

    # ombre douce : masque décalé et dilaté, très flou
    shadow = cv2.GaussianBlur((cadre[:, :, 0] * 255).astype(np.uint8), (0, 0), 14).astype(np.float32) / 255.0
    shadow = np.roll(shadow, 6, axis=1)
    a = float(params.get("ombre_alpha", 0.35))
    behind = np.clip(behind.astype(np.float32) * (1 - a * shadow[..., None]), 0, 255).astype(np.uint8)
    return (behind.astype(np.float32) * (1 - cadre) + front.astype(np.float32) * cadre).astype(np.uint8)


def tr_split_diptych(old: np.ndarray, new: np.ndarray, p: float, params: dict[str, Any],
                     palette: Palette, interp: int = cv2.INTER_CUBIC) -> np.ndarray:
    """Split diptych — GLSL : deux bandes, `uv.y` sélectionne la texture, mouvement opposé.

    Vue générale en haut (`old` continue d'avancer), détail en bas (`new` avance aussi), puis
    ouverture finale en plein écran sur le plan entrant.
    """
    e = _ease(str(params.get("courbe", "easeInOutQuad")), p)
    W, H = old.shape[1], old.shape[0]
    mv = float(params.get("mouvement_oppose", 0.06))
    fin = int(params.get("ouverture_fin_f", 6))
    # mouvement opposé : le haut glisse à gauche, le bas à droite
    top = _sample(old, 1.04, 0.5 * mv - mv * e, 0.0, (W, H), interp)
    bot = _sample(new, 1.04, -0.5 * mv + mv * e, 0.0, (W, H), interp)

    out = np.zeros_like(old)
    sep = int(H * (0.5 + 0.16 * e))            # la séparation monte : le détail gagne du terrain
    out[:sep] = top[:sep]
    out[sep:] = bot[sep:]
    # liseré crème discret à la séparation
    ep = 2
    out[max(0, sep - ep):sep + ep] = palette.get("cream", (239, 248, 255))

    duree = max(1.0, float(params.get("duree_f", 12)))
    if fin > 0 and p > (1.0 - fin / duree):
        q = (p - (1.0 - fin / duree)) / (fin / duree)
        q = max(0.0, min(1.0, q))
        full = _sample(new, 1.0 + 0.04 * (1 - q), 0.0, 0.0, (W, H), interp)
        out = (out.astype(np.float32) * (1 - q) + full.astype(np.float32) * q).astype(np.uint8)
    return out


TRANSITIONS = {
    "TR_CUT": tr_cut,
    "TR_FLASH_PUNCH": tr_flash_punch,
    "TR_WARM_BURN": tr_warm_burn,
    "TR_WHIP_BLUR": tr_whip_blur,
    "TR_PORTAL_EXPAND": tr_portal_expand,
    "TR_SPLIT_DIPTYCH": tr_split_diptych,
}


def apply_transition(name: str, old: np.ndarray, new: np.ndarray, p: float,
                     params: dict[str, Any] | None = None, palette: Palette | None = None,
                     interp: int = cv2.INTER_CUBIC) -> np.ndarray:
    """Point d'entrée unique. `p` ∈ [0,1] ; `params` vient du plan (aucune valeur en dur ici)."""
    fn = TRANSITIONS.get(name)
    if fn is None:
        raise ValueError(f"Transition inconnue : {name}")
    return fn(old, new, max(0.0, min(1.0, p)), params or {}, palette or {}, interp)
