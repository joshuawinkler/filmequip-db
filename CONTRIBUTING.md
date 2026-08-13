# Contributing

Thanks for wanting to contribute to the Film Equipment Database! There are two ways in:

## Route 1: Without Git knowledge

Open an [issue](../../issues/new/choose) using the "Add new item" template
and fill in whatever data you know. A maintainer will turn it into a pull request.

## Route 2: Via pull request

1. Fork the repo, create a branch
2. Add a new file under `data/<root-category>/<id>.yaml`, where
   `<root-category>` is one of `camera`, `grip`, `lighting`, `sound`,
   `miscellaneous`
   - `<id>` = `manufacturer-model-slug`, lowercase letters, numbers, hyphens only
   - The filename must exactly match the `id` in the document
   - `category` in the document is the full breadcrumb path from
     `data/categories.json`, root to leaf, joined by `" > "`, e.g.
     `Camera > Cameras > Digital Cameras`
   - Depending on the category, extra fields may be defined in
     `data/schemas/fields/<category_id>.json` (and inherited from any parent
     category's field schema) — see that folder for what's available
3. Validate locally before opening the PR:
   ```bash
   pip install pyyaml jsonschema
   python3 scripts/validate.py
   ```
4. Open the PR. CI validates automatically; a maintainer reviews afterwards.

## Data rules

- **Only publicly verifiable technical data** (manufacturer page, datasheet) —
  no guesses, no personal anecdotal figures presented as fact.
- Every entry needs a `source_url`.
- No prices, no rental-specific information — this project captures
  device facts, not commercial terms.
- Images: only link `image_url` to freely licensed sources (e.g. Wikimedia
  Commons), no image uploads into the repo.

## Proposing a new category / new schema field

Open an issue with the `schema-change` label and describe the need — schema
changes affect every consumer of the API, so they're deliberately handled
more slowly.
