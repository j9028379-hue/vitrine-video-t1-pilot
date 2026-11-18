from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from engine.motion_v2 import SAFE, ease, source_progress, transition
from engine.visual_qc import red_outline_candidates

ROOT = Path(__file__).resolve().parents[1]


def test_v2_transitions_keep_dimensions_and_have_clean_endpoints() -> None:
    old = np.full((1280, 720, 3), (20, 35, 80), np.uint8)
    new = np.full((1280, 720, 3), (180, 110, 30), np.uint8)
    for kind in ("whip_pan", "directional_push", "mask_reveal"):
        start = transition(old, new, kind, 0.0)
        middle = transition(old, new, kind, 0.5)
        end = transition(old, new, kind, 1.0)
        assert start.shape == middle.shape == end.shape == old.shape
        assert end.mean() > 0
        assert not np.any(np.all(end == 0, axis=2))
    assert ease(0) == 0 and ease(1) == 1


def test_preparation_speed_ramp_is_smooth_and_monotone() -> None:
    values = [source_progress("S2", i / 240) for i in range(241)]
    assert values[0] == 0.0 and values[-1] == 1.0
    assert values == sorted(values)
    assert all(0.0 <= x <= 1.0 for x in values)


def test_locked_scenes_and_commercial_field_keys_preserved() -> None:
    spec = json.loads((ROOT / "specs/T1_ENGINEERING_SPEC_V1_2.json").read_text(encoding="utf-8"))
    demo = json.loads((ROOT / "demo/T1_demo_input.json").read_text(encoding="utf-8"))
    assert [s["frames"] for s in spec["scenes"]] == [180, 240, 210, 270]
    assert [k for k in ("nom", "produit", "prix", "whatsapp", "quartier", "accroche") if k in demo] == ["nom", "produit", "prix", "whatsapp", "quartier", "accroche"]
    assert demo["demo"] is True and demo["business_label"] == "Maquis Démo"
    assert demo["produit"] == "BURGER MAISON"  # matches all four demonstration rushes


def test_v2_layout_stays_inside_scaled_v62_safe_zone() -> None:
    x0, x1, y0, y1 = SAFE
    assert x0 >= 42 and x1 <= 614 and y0 >= 160 and y1 <= 960
    # Deliberate non-overlapping bands used by the V2 compositions.
    bands = [(174, 222), (260, 430), (444, 490), (629, 723), (775, 890), (925, 945)]
    for top, bottom in bands:
        assert y0 <= top < bottom <= y1
    for a, b in zip(bands, bands[1:]):
        assert a[1] < b[0]


def test_diagnostic_red_outline_guard_detects_rectangle_not_filled_badge() -> None:
    frame = np.zeros((1280, 720, 3), np.uint8)
    import cv2
    cv2.rectangle(frame, (160, 300), (560, 700), (0, 0, 255), 4)
    assert red_outline_candidates(frame)
    clean = np.zeros_like(frame)
    cv2.rectangle(clean, (160, 300), (560, 700), (0, 140, 245), -1)
    assert not red_outline_candidates(clean)
