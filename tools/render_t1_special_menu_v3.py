#!/usr/bin/env python3
"""Render T1 Special Menu V3: unified final lockup and evolving effects."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.special_menu_style import ROOT, render_project


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "T1_special_menu_reference_v3.json")
    parser.add_argument("--input", type=Path, default=ROOT / "demo" / "T1_demo_input.json")
    parser.add_argument("--media-dir", type=Path, default=ROOT / "simulation" / "media")
    parser.add_argument("--output", type=Path, default=ROOT / "output" / "output_T1_special_menu_reference_v3.mp4")
    parser.add_argument("--contact-sheet", type=Path, default=ROOT / "output" / "planche_T1_special_menu_reference_v3.jpg")
    parser.add_argument("--manifest", type=Path, default=ROOT / "reports" / "T1_special_menu_v3_render_manifest.json")
    args = parser.parse_args()

    report = render_project(
        config_path=args.config.resolve(),
        input_path=args.input.resolve(),
        media_dir=args.media_dir.resolve(),
        output_path=args.output.resolve(),
        contact_sheet_path=args.contact_sheet.resolve(),
    )
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
