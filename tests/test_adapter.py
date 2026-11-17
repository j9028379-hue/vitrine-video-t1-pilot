from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from adapter.t1_adapter import ROOT, build_render_plan, normalize_fields

V12_PATH = ROOT / "specs" / "T1_ENGINEERING_SPEC_V1_2.json"
V62_PATH = ROOT / "specs" / "restaurants_maquis_T1.spec_v6_2.json"
if os.environ.get("T1_PUBLIC_SAFE") == "1" or not V62_PATH.exists():
    V62_PATH = ROOT / "specs" / "restaurants_maquis_T1.spec_v6_2.public-safe.json"
INPUT_PATH = ROOT / "demo" / "T1_demo_input.json"
V12 = json.loads(V12_PATH.read_text(encoding="utf-8"))
V62 = json.loads(V62_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", [V12_PATH, V62_PATH], ids=["v1.2", "v6.2"])
def test_reference_json_is_parseable(path: Path) -> None:
    assert isinstance(json.loads(path.read_text(encoding="utf-8")), dict)


def test_total_duration_is_900_frames() -> None:
    assert V12["units"]["total_frames"] == 900
    assert V12["units"]["fps"] == 30


def test_exactly_four_scenes() -> None:
    assert len(V12["scenes"]) == 4
    assert [s["frames"] for s in V12["scenes"]] == [180, 240, 210, 270]


def test_exactly_twelve_shots() -> None:
    assert len(V12["plans"]) == 12
    assert len(V62["video_track"]) == 12


def test_exactly_eight_graphic_blocks() -> None:
    assert len(V12["graphic_blocks"]) == 8
    assert len(V12["text_blocks"]) == 8


def test_exactly_fourteen_motion_presets() -> None:
    assert len(V12["presets"]) == 14
    assert [p["id"] for p in V12["presets"]] == [f"MD-T1-{i:02d}" for i in range(1, 15)]


def test_portrait_output_contract() -> None:
    assert V12["units"]["fps"] == 30
    assert V12["units"]["total_s"] == 30.0
    assert V12["units"]["pixels"].startswith("base 1080x1920, export 720x1280")


def test_demo_values_are_explicitly_fictional() -> None:
    demo = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    assert demo["demo"] is True
    assert "FICTIF" in demo["whatsapp"]
    assert "FICTIVE" in demo["quartier"]


@pytest.mark.parametrize("shot", V12["plans"], ids=lambda shot: shot["id"])
def test_each_shot_duration_and_contiguity(shot: dict) -> None:
    assert shot["out_end_f"] - shot["out_start_f"] == shot["out_frames"]
    assert shot["source_out_f"] - shot["source_in_f"] == shot["source_frames"]
    assert shot["freeze_tail_f"] >= 0


@pytest.mark.parametrize("block", V12["text_blocks"], ids=lambda block: block["id"])
def test_each_text_block_has_valid_half_open_interval(block: dict) -> None:
    assert 0 <= block["start_f"] < block["end_f"] <= 900
    assert block["end_f"] - block["start_f"] == block["dur_f"]


@pytest.mark.parametrize(
    ("field", "raw", "expected"),
    [
        ("nom", "  Maquis   Démo  ", "Maquis Démo"),
        ("accroche", "  Chaud   · servi. ", "Chaud · servi"),
    ],
)
def test_input_normalization(field: str, raw: str, expected: str) -> None:
    payload = {
        "nom": "Maquis Démo", "produit": "Riz poulet", "prix": "2500",
        "whatsapp": "NUMÉRO FICTIF", "quartier": "Cotonou — adresse fictive", "accroche": "Chaud",
    }
    payload[field] = raw
    cleaned = normalize_fields(payload, V12["data_contract"])
    assert cleaned[field] == expected


def test_plan_uses_read_only_specs_and_silent_audio() -> None:
    raw = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    plan = build_render_plan(V12, V62, raw)
    assert plan["spec_sources"]["write_back"] is False
    assert plan["output"]["audio"] is False
    assert len(plan["shots"]) == 12


def test_render_plan_expands_currency_suffix_without_mutating_value() -> None:
    raw = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    plan = build_render_plan(V12, V62, raw)
    assert plan["fields"]["prix"] == "2 500"
    assert plan["display"]["prix"] == "2 500 FCFA"
