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
        # Variante la plus définie disponible : 1080 si elle a été publiée par Mixkit, sinon 720.
        filename = item.get("filename_hd") or item["filename"]
        attendu = item.get("sha256_hd") or item["sha256"]
        path = ROOT / "rushes" / "source" / filename
        actual = sha256(path) if path.is_file() else None
        if actual != attendu:
            print(f"ÉCHEC {item['id']} {item['title']} — attendu {attendu[:16]}…, obtenu {str(actual)[:16]}…", file=sys.stderr)
            bad += 1
        else:
            print(f"Vérifié {item['id']} — {item['title']} — {filename} — {actual}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
