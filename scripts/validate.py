#!/usr/bin/env python3
"""
Validates all YAML records in /data/<category>/*.yaml against the
matching JSON schema in /data/schemas/<category>.schema.json.

Also checks:
- unique IDs across the whole database
- that the ID in the filename matches the ID in the document
"""

import sys
import json
from pathlib import Path

import yaml
from jsonschema import validate, ValidationError

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SCHEMA_DIR = DATA_DIR / "schemas"

# Mapping: folder name in /data -> schema file name
CATEGORY_SCHEMAS = {
    "cameras": "camera.schema.json",
    "lighting": "lighting.schema.json",
}


def load_schema(name: str) -> dict:
    with open(SCHEMA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    errors = []
    seen_ids = {}

    for folder, schema_file in CATEGORY_SCHEMAS.items():
        folder_path = DATA_DIR / folder
        if not folder_path.exists():
            continue

        schema = load_schema(schema_file)

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

            try:
                validate(instance=doc, schema=schema)
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
