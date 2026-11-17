"""Fetch licensed demo footage temporarily and enforce its manifest SHA-256."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "rushes" / "manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_rushes(manifest_path: Path = MANIFEST, target_dir: Path | None = None) -> list[Path]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    target_dir = target_dir or ROOT / "rushes" / "source"
    target_dir.mkdir(parents=True, exist_ok=True)
    fetched = []
    for item in manifest["sources"]:
        path = target_dir / item["filename"]
        actual = sha256(path) if path.is_file() else None
        if actual != item["sha256"]:
            path.unlink(missing_ok=True)
            subprocess.run([
                "curl", "--fail", "--location", "--silent", "--show-error", "--retry", "3",
                "--max-time", "180", "--user-agent", "Mozilla/5.0",
                "--referer", "https://mixkit.co/free-stock-video/",
                item["download_url"], "--output", str(path),
            ], check=True)
            actual = sha256(path)
        if actual != item["sha256"]:
            path.unlink(missing_ok=True)
            raise RuntimeError(f"SHA-256 mismatch for {item['id']}: expected {item['sha256']}, got {actual}")
        fetched.append(path)
        print(f"Verified {item['id']} — {item['title']} — {actual}")
    return fetched


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    args = parser.parse_args()
    ensure_rushes(args.manifest)
    print("All four source clips verified; originals remain temporary and untracked.")


if __name__ == "__main__":
    main()
