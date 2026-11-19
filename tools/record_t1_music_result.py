#!/usr/bin/env python3
"""Persist a T1 music choice only after the caller reports render success."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapter.t1_adapter import load_json, record_music_render_result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--render-job-id", required=True)
    parser.add_argument("--selected-music-id", required=True)
    parser.add_argument("--status", choices=["success", "failed"], required=True)
    parser.add_argument(
        "--music-pack",
        type=Path,
        default=ROOT / "config/T1_special_menu_music_pack_v1_0_0.json",
    )
    args = parser.parse_args()
    state = record_music_render_result(
        load_json(args.music_pack),
        state_path=args.state,
        render_job_id=args.render_job_id,
        selected_music_id=args.selected_music_id,
        succeeded=args.status == "success",
    )
    print(json.dumps(state, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
