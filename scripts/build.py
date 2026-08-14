#!/usr/bin/env python3
"""
Builds static JSON bundles for the API from /data/<root-category>/**/*.yaml,
and assembles the full GitHub Pages deploy folder.

Root categories (and their data folders) are read from data/categories.json
rather than hardcoded, so adding a new root category is just a data change.
A file's category is implied by its folder path (mirroring
data/categories.json), not stored in the YAML - the built JSON output adds a
resolved `category` breadcrumb string to each item.

Output:
  site/v1/<root-slug>.json  (e.g. camera.json, grip.json, lighting.json, ...)
  site/v1/all.json
  site/v1/categories.json   (full category tree, from data/categories.json)
  site/v1/fields.json       (category_id -> field schema, from data/schemas/fields)
  site/v1/version.json      (timestamp + entry count, for cache invalidation)
  site/admin/...            (copy of the Decap CMS admin UI)
  site/manage/...           (copy of the structure manager tool)
  site/index.html           (copy of the public browse/search UI)
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
BROWSE_SRC = ROOT / "browse" / "index.html"  # public browse/search UI source
CATEGORIES_PATH = DATA_DIR / "categories.json"
FIELDS_DIR = DATA_DIR / "schemas" / "fields"


def load_categories() -> tuple[list[dict], dict]:
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        nodes = json.load(f)
    by_id = {n["id"]: n for n in nodes}
    return nodes, by_id


def load_root_slugs(nodes: list[dict]) -> list[str]:
    roots = [n for n in nodes if n["parent_id"] is None]
    roots.sort(key=lambda n: n["sort_order"])
    return [n["slug"] for n in roots]


def slug_path_to_category_id(slug_parts: tuple, nodes: list[dict]) -> str | None:
    children_by_parent: dict = {}
    for n in nodes:
        children_by_parent.setdefault(n["parent_id"], []).append(n)

    parent_id = None
    category_id = None
    for slug in slug_parts:
        candidates = [n for n in children_by_parent.get(parent_id, []) if n["slug"] == slug]
        if not candidates:
            return None
        category_id = candidates[0]["id"]
        parent_id = category_id
    return category_id


def category_id_to_breadcrumb(category_id: str | None, by_id: dict) -> str | None:
    names = []
    current = category_id
    while current:
        names.append(by_id[current]["name"])
        current = by_id[current]["parent_id"]
    return " > ".join(reversed(names)) if names else None


def load_category(folder: str, nodes: list[dict], by_id: dict) -> list[dict]:
    items = []
    folder_path = DATA_DIR / folder
    if not folder_path.exists():
        return items
    for yaml_path in sorted(folder_path.rglob("*.yaml")):
        with open(yaml_path, "r", encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        if not doc:
            continue
        slug_parts = yaml_path.relative_to(DATA_DIR).parent.parts
        category_id = slug_path_to_category_id(slug_parts, nodes)
        doc = {
            "category_id": category_id,
            "category": category_id_to_breadcrumb(category_id, by_id),
            **doc,
        }
        items.append(doc)
    return items


def load_fields() -> dict:
    """category_id -> {category_id, category_name, fields}, from data/schemas/fields/*.json."""
    fields_by_category = {}
    if not FIELDS_DIR.exists():
        return fields_by_category
    for schema_path in sorted(FIELDS_DIR.glob("*.json")):
        with open(schema_path, "r", encoding="utf-8") as f:
            parsed = json.load(f)
        fields_by_category[parsed["category_id"]] = parsed
    return fields_by_category


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

    if BROWSE_SRC.exists():
        shutil.copyfile(BROWSE_SRC, SITE_DIR / "index.html")
        print(f"→ {(SITE_DIR / 'index.html').relative_to(ROOT)}: browse UI copied")

    shutil.copyfile(CATEGORIES_PATH, OUT_DIR / "categories.json")
    print(f"→ {(OUT_DIR / 'categories.json').relative_to(ROOT)}: category tree copied")

    fields = load_fields()
    with open(OUT_DIR / "fields.json", "w", encoding="utf-8") as f:
        json.dump(fields, f, ensure_ascii=False, indent=2)
    print(f"→ {(OUT_DIR / 'fields.json').relative_to(ROOT)}: {len(fields)} field schemas")

    nodes, by_id = load_categories()
    categories = load_root_slugs(nodes)
    all_items = []
    for category in categories:
        items = load_category(category, nodes, by_id)
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
        "categories": {c: len(load_category(c, nodes, by_id)) for c in categories},
    }
    with open(OUT_DIR / "version.json", "w", encoding="utf-8") as f:
        json.dump(version_info, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Build complete: {len(all_items)} entries total.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
