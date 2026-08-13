#!/usr/bin/env python3
"""
Validiert alle YAML-Datensätze in /data/<kategorie>/*.yaml gegen das
passende JSON-Schema in /data/schemas/<kategorie>.schema.json.

Prüft zusätzlich:
- eindeutige IDs über die gesamte Datenbank hinweg
- dass die ID im Dateinamen mit der ID im Dokument übereinstimmt
"""

import sys
import json
from pathlib import Path

import yaml
from jsonschema import validate, ValidationError

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SCHEMA_DIR = DATA_DIR / "schemas"

# Mapping: Ordnername in /data -> Schema-Dateiname
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
                    errors.append(f"{yaml_path}: YAML-Parsing-Fehler: {e}")
                    continue

            if doc is None:
                errors.append(f"{yaml_path}: Datei ist leer")
                continue

            try:
                validate(instance=doc, schema=schema)
            except ValidationError as e:
                errors.append(f"{yaml_path}: Schema-Fehler: {e.message}")

            doc_id = doc.get("id")
            expected_stem = yaml_path.stem
            if doc_id and doc_id != expected_stem:
                errors.append(
                    f"{yaml_path}: Dateiname '{expected_stem}' passt nicht zur id '{doc_id}'"
                )

            if doc_id:
                if doc_id in seen_ids:
                    errors.append(
                        f"{yaml_path}: Doppelte id '{doc_id}' (bereits in {seen_ids[doc_id]})"
                    )
                else:
                    seen_ids[doc_id] = yaml_path

    if errors:
        print(f"❌ {len(errors)} Fehler gefunden:\n")
        for e in errors:
            print(f" - {e}")
        return 1

    print(f"✅ Alle {len(seen_ids)} Einträge sind valide.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
