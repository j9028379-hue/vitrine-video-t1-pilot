"""Vérifie par SHA-256 les rushs Mixkit téléchargés avant assemblage des prises."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "rushes" / "manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    bad = 0
    for item in manifest.get("raw_sources", []):
        path = ROOT / "rushes" / "source" / item["filename"]
        actual = sha256(path) if path.is_file() else None
        if actual != item["sha256"]:
            print(f"ÉCHEC {item['id']} {item['title']} — attendu {item['sha256'][:16]}…, obtenu {str(actual)[:16]}…", file=sys.stderr)
            bad += 1
        else:
            print(f"Vérifié {item['id']} — {item['title']} — {actual}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
