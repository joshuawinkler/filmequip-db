#!/usr/bin/env python3
"""
Validates all YAML records in /data/<root-category>/*.yaml.

Each entry is checked against:
- the common base schema (data/schemas/base.schema.json)
- the dynamic field schema(s) for its category, from
  data/schemas/fields/<category_id>.json - resolved by walking the entry's
  `category` breadcrumb path against data/categories.json, then merging the
  field schema of that leaf category with all of its ancestors' field
  schemas (fields defined higher up the tree, e.g. on "Cameras", apply to
  every category under it, e.g. "Digital Cameras")

Also checks:
- unique IDs across the whole database
- that the ID in the filename matches the ID in the document
- that `category` resolves to an actual leaf in data/categories.json
"""

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator, ValidationError

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SCHEMA_DIR = DATA_DIR / "schemas"
FIELDS_DIR = SCHEMA_DIR / "fields"
CATEGORIES_PATH = DATA_DIR / "categories.json"


def load_categories() -> tuple[dict, dict]:
    """Returns (by_id, children_by_parent) for data/categories.json."""
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        nodes = json.load(f)
    by_id = {n["id"]: n for n in nodes}
    children_by_parent: dict[str | None, list[dict]] = {}
    for n in nodes:
        children_by_parent.setdefault(n["parent_id"], []).append(n)
    return by_id, children_by_parent


def resolve_category_path(path: list[str], children_by_parent: dict) -> str | None:
    """Walks a root->leaf breadcrumb of category names, returns the leaf id or None."""
    parent_id = None
    leaf_id = None
    for name in path:
        candidates = [n for n in children_by_parent.get(parent_id, []) if n["name"] == name]
        if not candidates:
            return None
        leaf_id = candidates[0]["id"]
        parent_id = leaf_id
    return leaf_id


def ancestor_chain(category_id: str, by_id: dict) -> list[str]:
    """Returns [category_id, parent_id, ...] up to the root."""
    chain = []
    current = category_id
    while current:
        chain.append(current)
        current = by_id[current]["parent_id"]
    return chain


def load_field_schema(category_id: str) -> dict | None:
    path = FIELDS_DIR / f"{category_id}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def field_to_json_schema_property(field: dict) -> dict:
    t = field["type"]
    if t == "text":
        return {"type": "string"}
    if t == "number":
        return {"type": "number"}
    if t == "boolean":
        return {"type": "boolean"}
    if t == "select":
        return {"type": "string", "enum": field["options"]}
    if t == "multiselect":
        return {"type": "array", "items": {"type": "string", "enum": field["options"]}}
    if t == "multiselect_amounts":
        return {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "amount"],
                "properties": {
                    "name": {"type": "string", "enum": field["options"]},
                    "amount": {"type": "number"},
                },
                "additionalProperties": False,
            },
        }
    raise ValueError(f"Unknown field type: {t}")


def build_schema_for_category(category_id: str | None, base_schema: dict, by_id: dict) -> dict:
    schema = json.loads(json.dumps(base_schema))  # deep copy
    if category_id:
        for ancestor_id in ancestor_chain(category_id, by_id):
            field_schema = load_field_schema(ancestor_id)
            if not field_schema:
                continue
            for field in field_schema["fields"]:
                schema["properties"][field["key"]] = field_to_json_schema_property(field)
    schema["additionalProperties"] = False
    return schema


def main() -> int:
    errors = []
    seen_ids = {}

    with open(SCHEMA_DIR / "base.schema.json", "r", encoding="utf-8") as f:
        base_schema = json.load(f)

    by_id, children_by_parent = load_categories()

    for folder_path in sorted(p for p in DATA_DIR.iterdir() if p.is_dir() and p.name != "schemas"):
        for yaml_path in sorted(folder_path.glob("*.yaml")):
            with open(yaml_path, "r", encoding="utf-8") as f:
                try:
                    doc = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    errors.append(f"{yaml_path}: YAML parsing error: {e}")
                    continue

            if doc is None:
                errors.append(f"{yaml_path}: file is empty")
                continue

            category_str = doc.get("category")
            category_id = None
            if isinstance(category_str, str) and category_str:
                category_path = [part.strip() for part in category_str.split(" > ")]
                category_id = resolve_category_path(category_path, children_by_parent)
                if category_id is None:
                    errors.append(
                        f"{yaml_path}: category path '{category_str}' does not resolve to a "
                        f"known category in data/categories.json"
                    )
                elif category_path[0].lower().replace(" ", "-") != folder_path.name:
                    errors.append(
                        f"{yaml_path}: entry is in folder '{folder_path.name}' but its category "
                        f"root is '{category_path[0]}'"
                    )

            schema = build_schema_for_category(category_id, base_schema, by_id)
            try:
                Draft7Validator(schema).validate(doc)
            except ValidationError as e:
                errors.append(f"{yaml_path}: schema error: {e.message}")

            doc_id = doc.get("id")
            expected_stem = yaml_path.stem
            if doc_id and doc_id != expected_stem:
                errors.append(
                    f"{yaml_path}: filename '{expected_stem}' does not match id '{doc_id}'"
                )

            if doc_id:
                if doc_id in seen_ids:
                    errors.append(
                        f"{yaml_path}: duplicate id '{doc_id}' (already used in {seen_ids[doc_id]})"
                    )
                else:
                    seen_ids[doc_id] = yaml_path

    if errors:
        print(f"❌ {len(errors)} error(s) found:\n")
        for e in errors:
            print(f" - {e}")
        return 1

    print(f"✅ All {len(seen_ids)} entries are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
