from __future__ import annotations

import numpy as np

from engine.special_menu_style import (
    ROOT,
    _display_price,
    apply_impact_transition,
    impact_transition_state,
    load_json,
    validate_config,
)

CONFIG_PATH = ROOT / "config" / "T1_special_menu_reference_v2.json"


def test_v2_config_keeps_identity_time_and_four_scenes() -> None:
    config = load_json(CONFIG_PATH)
    validate_config(config)
    impact = config["impact_transition_system"]
    assert impact["source_time_map"] == "identity"
    assert impact["audio_time_map"] == "identity"
    assert impact["text_layer_affected"] is False
    assert impact["major_scene_cuts"]["cut_frames"] == [180, 420, 630]
    assert [s["frames"] for s in config["scene_capture_contract"]["scenes"]] == [180, 240, 210, 270]


def test_price_groups_numeric_digits_and_keeps_currency_separate() -> None:
    assert _display_price("2500") == ("2 500", "FCFA")
    assert _display_price("2 500") == ("2 500", "FCFA")
    assert _display_price("2500 FCFA") == ("2 500", "FCFA")
    assert _display_price("1000000") == ("1 000 000", "FCFA")
    assert _display_price("prix libre") == ("prix libre", "FCFA")


def test_price_graphic_is_one_baseline_lockup() -> None:
    config = load_json(CONFIG_PATH)
    price = next(g for g in config["graphics"] if g["id"] == "G02_PRICE")
    assert price["layout"]["mode"] == "single_line_baseline"
    assert price["layout"]["number_currency_gap_px"] == 18
    assert price["layout"]["non_breaking"] is True
    assert config["price_format"]["example_output"] == "2 500 FCFA"


def test_major_impact_has_symmetric_peak_around_scene_cut() -> None:
    config = load_json(CONFIG_PATH)
    outgoing = impact_transition_state(config, 179)
    incoming = impact_transition_state(config, 180)
    assert outgoing is not None and incoming is not None
    assert outgoing["kind"] == incoming["kind"] == "major"
    assert outgoing["phase"] == "outgoing"
    assert incoming["phase"] == "incoming"
    assert outgoing["intensity"] == incoming["intensity"] == 1.0
    assert impact_transition_state(config, 175) is None


def test_minor_zoom_snap_and_major_whip_change_pixels_deterministically() -> None:
    config = load_json(CONFIG_PATH)
    gradient = np.zeros((96, 54, 3), dtype=np.uint8)
    gradient[..., 0] = np.arange(54, dtype=np.uint8)[None, :] * 3
    gradient[..., 1] = np.arange(96, dtype=np.uint8)[:, None] * 2
    gradient[..., 2] = 80
    for frame_index in (60, 180):
        state = impact_transition_state(config, frame_index)
        first = apply_impact_transition(gradient, state)
        second = apply_impact_transition(gradient, state)
        assert first.shape == gradient.shape
        assert np.array_equal(first, second)
        assert not np.array_equal(first, gradient)


def test_no_transition_treatment_on_final_cta_hold() -> None:
    config = load_json(CONFIG_PATH)
    assert impact_transition_state(config, 899) is None
