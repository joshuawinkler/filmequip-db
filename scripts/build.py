#!/usr/bin/env python3
"""
Baut aus /data/<kategorie>/*.yaml statische JSON-Bundles fuer die API.

Output:
  api/v1/cameras.json
  api/v1/lighting.json
  api/v1/all.json
  api/v1/version.json   (Zeitstempel + Anzahl Eintraege, fuer Cache-Invalidierung)
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "api" / "v1"

CATEGORIES = ["cameras", "lighting"]


def load_category(folder: str) -> list[dict]:
    items = []
    folder_path = DATA_DIR / folder
    if not folder_path.exists():
        return items
    for yaml_path in sorted(folder_path.glob("*.yaml")):
        with open(yaml_path, "r", encoding="utf-8") as f:
            doc = yaml.safe_load(f)
            if doc:
                items.append(doc)
    return items


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_items = []
    for category in CATEGORIES:
        items = load_category(category)
        out_path = OUT_DIR / f"{category}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print(f"→ {out_path.relative_to(ROOT)}: {len(items)} Eintraege")
        all_items.extend(items)

    with open(OUT_DIR / "all.json", "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    version_info = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "total_items": len(all_items),
        "categories": {c: len(load_category(c)) for c in CATEGORIES},
    }
    with open(OUT_DIR / "version.json", "w", encoding="utf-8") as f:
        json.dump(version_info, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Build fertig: {len(all_items)} Eintraege insgesamt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
