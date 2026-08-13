# Film Equipment Database

An open, collaboratively curated database of film equipment (cameras, grip,
lighting, sound) — as structured raw data (YAML) in this Git repo, and as a
free, static JSON API for integration into your own projects (kit list tools,
prep apps, etc.).

## How it works

- Raw data lives under `/data/<root-category>/*.yaml`, one file per device,
  where `<root-category>` is `camera`, `grip`, `lighting`, `sound`, or
  `miscellaneous`
- The full category tree (root down to leaf) lives in `/data/categories.json`;
  each entry's `category` field is a `" > "`-joined breadcrumb path through it
- Every file is validated against the common base schema
  (`/data/schemas/base.schema.json`) plus any category-specific fields from
  `/data/schemas/fields/<category_id>.json` (CI, on every PR)
- On every merge to `main`, GitHub Actions builds static JSON bundles from it
  and deploys them to GitHub Pages — with no server of your own

## Using the API

Live at:

```
https://joshuawinkler.github.io/filmequip-db/v1/camera.json
https://joshuawinkler.github.io/filmequip-db/v1/grip.json
https://joshuawinkler.github.io/filmequip-db/v1/lighting.json
https://joshuawinkler.github.io/filmequip-db/v1/sound.json
https://joshuawinkler.github.io/filmequip-db/v1/miscellaneous.json
https://joshuawinkler.github.io/filmequip-db/v1/all.json
https://joshuawinkler.github.io/filmequip-db/v1/categories.json
https://joshuawinkler.github.io/filmequip-db/v1/version.json
```

`categories.json` is the full category tree (`id`, `name`, `parent_id`,
`sort_order`) — each entry's `category` field is a `" > "`-joined breadcrumb
path through this tree, root to leaf.

Example fetch in Swift:

```swift
struct Camera: Codable {
    let id: String
    let category: String
    let manufacturer: String
    let model: String
    // ... more fields depending on schema
}

let url = URL(string: "https://joshuawinkler.github.io/filmequip-db/v1/cameras.json")!
let (data, _) = try await URLSession.shared.data(from: url)
let cameras = try JSONDecoder().decode([Camera].self, from: data)
```

For offline use, cache the JSON locally and only refetch when
`version.json` (field `built_at`) changes.

## Admin UI (Decap CMS)

`/admin` hosts a graphical interface ([Decap CMS](https://decapcms.org/))
where contributors can create/edit entries via forms, without needing to know
Git or YAML syntax. Behind the scenes it does exactly what a manual PR does:
new branch, YAML file matching the schema, automatic pull request. CI
validates and a maintainer reviews as usual.

### Setup (one-time)

1. **Create a GitHub OAuth App**: GitHub → Settings → Developer settings →
   OAuth Apps → "New OAuth App". Homepage URL = your Pages URL, Authorization
   callback URL depends on your chosen OAuth proxy (see step 2).
2. **Deploy an OAuth proxy** (free, since GitHub Pages itself has no server).
   Ready-made, open templates, also referenced by the Decap CMS docs:
   - [ottmartens/decap-cms-github-oauth-provider-cloudflare](https://github.com/ottmartens/decap-cms-github-oauth-provider-cloudflare)
   - [sterlingwes/decap-proxy](https://github.com/sterlingwes/decap-proxy)

   Both run as a Cloudflare Worker (free tier is enough); you just store
   `CLIENT_ID`/`CLIENT_SECRET` from step 1 as secrets there.
3. In `admin/config.yml`, set `repo` to `your-name/your-repo` and `base_url`
   to your deployed worker's URL.
4. Done — `/admin` is reachable at `https://<your-name>.github.io/<repo>/admin/`

Contributors still need GitHub collaborator access to your repo for login to
work — the UI replaces the way of editing, not the access control.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Or use the form under `/admin`.

## License

- Code (scripts, workflows): MIT
- Data (`/data`): [ODbL](https://opendatacommons.org/licenses/odbl/) —
  redistribution/derivatives of the database must be shared under the same
  license, attribution required.

## Maintainer setup (one-time)

1. Create the GitHub repo, push this folder's contents
2. Under *Settings → Pages*, select "GitHub Actions" as the source
3. Fill in `.github/CODEOWNERS` with real usernames
4. Enable branch protection on `main`: require PRs + passing CI
5. Create a first tag/release (e.g. `v1.0.0`) once there's enough data in,
   so integrators can reference a stable snapshot
