#!/usr/bin/env python3
"""
Builds static JSON bundles for the API from /data/<root-category>/*.yaml,
and assembles the full GitHub Pages deploy folder.

Root categories (and their data folders) are read from data/categories.json
rather than hardcoded, so adding a new root category is just a data change.

Output:
  site/v1/<root-slug>.json  (e.g. camera.json, grip.json, lighting.json, ...)
  site/v1/all.json
  site/v1/categories.json   (full category tree, from data/categories.json)
  site/v1/version.json      (timestamp + entry count, for cache invalidation)
  site/admin/...            (copy of the Decap CMS admin UI)
"""

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SITE_DIR = ROOT / "site"          # full Pages deploy folder
OUT_DIR = SITE_DIR / "v1"         # JSON API lives under /v1/...
ADMIN_SRC = ROOT / "admin"        # Decap CMS source folder
ADMIN_DEST = SITE_DIR / "admin"   # gets deployed to Pages as well
MANAGE_SRC = ROOT / "manage"      # structure manager tool source folder
MANAGE_DEST = SITE_DIR / "manage" # gets deployed to Pages as well
CATEGORIES_PATH = DATA_DIR / "categories.json"


def load_root_slugs() -> list[str]:
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        nodes = json.load(f)
    roots = [n for n in nodes if n["parent_id"] is None]
    roots.sort(key=lambda n: n["sort_order"])
    return [n["name"].lower().replace(" ", "-") for n in roots]


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
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if ADMIN_SRC.exists():
        shutil.copytree(ADMIN_SRC, ADMIN_DEST)
        print(f"→ {ADMIN_DEST.relative_to(ROOT)}: admin/ copied")

    if MANAGE_SRC.exists():
        shutil.copytree(MANAGE_SRC, MANAGE_DEST)
        print(f"→ {MANAGE_DEST.relative_to(ROOT)}: manage/ copied")

    shutil.copyfile(CATEGORIES_PATH, OUT_DIR / "categories.json")
    print(f"→ {(OUT_DIR / 'categories.json').relative_to(ROOT)}: category tree copied")

    categories = load_root_slugs()
    all_items = []
    for category in categories:
        items = load_category(category)
        out_path = OUT_DIR / f"{category}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print(f"→ {out_path.relative_to(ROOT)}: {len(items)} entries")
        all_items.extend(items)

    with open(OUT_DIR / "all.json", "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    version_info = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "total_items": len(all_items),
        "categories": {c: len(load_category(c)) for c in categories},
    }
    with open(OUT_DIR / "version.json", "w", encoding="utf-8") as f:
        json.dump(version_info, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Build complete: {len(all_items)} entries total.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
