from __future__ import annotations

import numpy as np

from engine.special_menu_style import (
    ROOT,
    apply_impact_transition,
    impact_transition_state,
    load_json,
    validate_config,
)

CONFIG_PATH = ROOT / "config" / "T1_special_menu_reference_v3.json"


def test_v3_config_is_valid_and_preserves_identity_time() -> None:
    config = load_json(CONFIG_PATH)
    validate_config(config)
    choreography = config["premium_transition_choreography"]
    assert choreography["enabled"] is True
    assert choreography["source_time_map"] == "identity"
    assert choreography["audio_time_map"] == "identity"
    assert choreography["text_layer_affected"] is False
    assert config["impact_transition_system"]["enabled"] is False


def test_final_lockup_mirrors_opening_typography_and_reveal() -> None:
    config = load_json(CONFIG_PATH)
    graphics = {item["id"]: item for item in config["graphics"]}
    opening = graphics["G01_HERO"]
    opening_label = graphics["G01_LABEL"]
    final = graphics["G05_CTA"]
    assert final["layout"]["mode"] == "mirror_opening"
    assert final["fields"][0] == "produit"
    assert final["style"]["primary_font"] == opening["style"]["font"] == "display_serif"
    assert final["style"]["primary_size_px"] == opening["style"]["size_px"] == 84
    assert final["style"]["primary_min_size_px"] == opening["style"]["min_size_px"] == 52
    assert final["style"]["secondary_font"] == opening_label["style"]["font"] == "light_sans"
    assert final["style"]["secondary_size_px"] == opening_label["style"]["size_px"] == 35
    assert final["style"]["secondary_tracking_em"] == opening_label["style"]["tracking_em"] == 0.15
    assert final["fixed_text"] == "COMMANDER MAINTENANT"
    assert final["style"]["hard_card"] is False
    assert final["style"]["border"] is False
    assert final["animation"]["reveal_frames"] == 20


def test_every_cut_has_a_unique_evolving_event() -> None:
    config = load_json(CONFIG_PATH)
    events = config["premium_transition_choreography"]["events"]
    cuts = [event["cut_f"] for event in events]
    names = [event["name"] for event in events]
    assert cuts == config["edit_timeline"]["hard_cut_frames"]
    assert len(events) == len(set(cuts)) == len(set(names)) == 13
    assert {event["phase"] for event in events} == {"appetite", "detail", "human", "place_and_cta"}


def test_human_phase_is_face_safe() -> None:
    config = load_json(CONFIG_PATH)
    human = [e for e in config["premium_transition_choreography"]["events"] if e["phase"] == "human"]
    assert [event["cut_f"] for event in human] == [420, 480, 540]
    assert all(event["face_safe"] for event in human)
    assert all(event["chromatic_shift_px_max"] == 0 for event in human)


def test_event_state_changes_name_and_optical_treatment_over_time() -> None:
    config = load_json(CONFIG_PATH)
    expected = {
        60: "focus_snap",
        120: "amber_macro_push",
        180: "golden_whip_reveal",
        240: "silk_slide_left",
        300: "aperture_bloom",
        360: "gold_rack_focus",
        420: "portrait_luma_bloom",
        480: "editorial_punch_in",
        540: "editorial_release",
        630: "architectural_light_sweep",
        690: "gallery_glide_left",
        750: "gallery_glide_right",
        810: "luxury_hero_resolve",
    }
    for frame, name in expected.items():
        state = impact_transition_state(config, frame)
        assert state is not None
        assert state["name"] == name
        assert state["intensity"] == 1.0

    gradient = np.zeros((96, 54, 3), dtype=np.uint8)
    gradient[..., 0] = np.arange(54, dtype=np.uint8)[None, :] * 3
    gradient[..., 1] = np.arange(96, dtype=np.uint8)[:, None] * 2
    gradient[..., 2] = 90
    outputs = [
        apply_impact_transition(gradient, impact_transition_state(config, frame))
        for frame in (60, 120, 180, 300, 420, 630, 810)
    ]
    hashes = {output.tobytes() for output in outputs}
    assert len(hashes) == len(outputs)


def test_luxury_resolve_stops_before_stable_cta_hold() -> None:
    config = load_json(CONFIG_PATH)
    assert impact_transition_state(config, 817) is not None
    assert impact_transition_state(config, 818) is None
    assert impact_transition_state(config, 899) is None
    assert config["premium_transition_choreography"]["safety"]["CTA_stable_after_f"] == 817
