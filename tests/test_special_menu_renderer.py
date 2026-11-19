from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from engine.special_menu_style import (
    GradeParameters,
    ROOT,
    _filmic_lut,
    _vignette,
    apply_cinematic_grade,
    crop_zoom,
    load_json,
    normalize_fields,
    render_graphics,
    validate_config,
)

CONFIG_PATH = ROOT / "config" / "T1_special_menu_reference_v1.json"
INPUT_PATH = ROOT / "demo" / "T1_demo_input.json"


def test_config_is_accepted_by_renderer() -> None:
    validate_config(load_json(CONFIG_PATH))


def test_locked_demo_fields_normalize_without_invention() -> None:
    config = load_json(CONFIG_PATH)
    raw = load_json(INPUT_PATH)
    fields = normalize_fields(raw, config)
    assert fields == {
        "nom": "MAQUIS DÉMO",
        "produit": "BURGER MAISON",
        "prix": "2 500",
        "whatsapp": "NUMÉRO FICTIF",
        "quartier": "ARCONVILLE — ADRESSE FICTIVE",
        "accroche": "CHAUD · SERVI · AUJOURD’HUI",
    }


def test_crop_zoom_keeps_dimensions_and_is_deterministic() -> None:
    frame = np.arange(120 * 80 * 3, dtype=np.uint32).reshape(120, 80, 3).astype(np.uint8)
    first = crop_zoom(frame, 1.17, (0.42, 0.40))
    second = crop_zoom(frame, 1.17, (0.42, 0.40))
    assert first.shape == frame.shape
    assert np.array_equal(first, second)


def test_grade_is_deterministic_for_same_scene_and_frame() -> None:
    config = load_json(CONFIG_PATH)
    look = config["look_pipeline"]
    points = next(step["points"] for step in look["steps"] if step["op"] == "filmic_curve")
    lut = _filmic_lut(points)
    frame = np.full((96, 54, 3), (50, 90, 140), dtype=np.uint8)
    params = GradeParameters(1.0, (1.0, 1.0, 1.0))
    vig = _vignette(96, 54, 0.16)
    first = apply_cinematic_grade(frame, params, look, 2, 17, lut, vig)
    second = apply_cinematic_grade(frame, params, look, 2, 17, lut, vig)
    assert np.array_equal(first, second)
    assert first.shape == frame.shape


def test_key_graphic_frames_render_without_hard_cards() -> None:
    config = load_json(CONFIG_PATH)
    fields = normalize_fields(load_json(INPUT_PATH), config)
    base = np.full((1280, 720, 3), 128, dtype=np.uint8)
    for frame_index in (4, 24, 59, 184, 204, 304, 324, 634, 655, 810, 832, 899):
        rendered = render_graphics(base.copy(), frame_index, fields, config)
        assert rendered.shape == base.shape
        assert rendered.dtype == np.uint8
    final = render_graphics(base.copy(), 899, fields, config)
    assert not np.array_equal(final, base)
