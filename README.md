# Filmequipment-Datenbank

Eine offene, kollaborativ kuratierte Datenbank für Filmequipment (Kameras, Grip,
Lighting, Sound) — als strukturierte Rohdaten (YAML) im Git-Repo und als
kostenlose, statische JSON-API für die Integration in eigene Projekte
(Kitlist-Tools, Prep-Apps, etc.).

## Wie funktioniert das?

- Rohdaten liegen unter `/data/<kategorie>/*.yaml`, ein File pro Gerät
- Jedes File wird gegen ein Schema in `/data/schemas/` validiert (CI, bei jedem PR)
- Bei jedem Merge auf `main` baut GitHub Actions daraus statische JSON-Bundles
  und deployed sie auf GitHub Pages — komplett ohne eigenen Server

## API nutzen

Nach dem ersten Deploy erreichbar unter (Platzhalter, echte URL nach Setup einsetzen):

```
https://<dein-github-name>.github.io/<repo-name>/v1/cameras.json
https://<dein-github-name>.github.io/<repo-name>/v1/lighting.json
https://<dein-github-name>.github.io/<repo-name>/v1/all.json
https://<dein-github-name>.github.io/<repo-name>/v1/version.json
```

Beispiel-Fetch in Swift:

```swift
struct Camera: Codable {
    let id: String
    let category: String
    let manufacturer: String
    let model: String
    // ... weitere Felder je nach Schema
}

let url = URL(string: "https://<dein-github-name>.github.io/<repo-name>/v1/cameras.json")!
let (data, _) = try await URLSession.shared.data(from: url)
let cameras = try JSONDecoder().decode([Camera].self, from: data)
```

Für Offline-Nutzung empfiehlt sich, das JSON lokal zu cachen und nur bei Änderung
von `version.json` (Feld `built_at`) neu zu laden.

## Verwaltungsoberfläche (Decap CMS)

Unter `/admin` liegt eine grafische Oberfläche ([Decap CMS](https://decapcms.org/)),
mit der Mitwirkende Einträge per Formular anlegen/bearbeiten können, ohne Git oder
YAML-Syntax zu kennen. Im Hintergrund passiert exakt das Gleiche wie bei einem
manuellen PR: neuer Branch, YAML-Datei nach Schema, automatischer Pull Request.
Eure CI validiert und ein Maintainer reviewt wie gewohnt.

### Setup (einmalig)

1. **GitHub OAuth App anlegen**: GitHub → Settings → Developer settings → OAuth Apps
   → "New OAuth App". Homepage URL = eure Pages-URL, Authorization callback URL
   je nach gewähltem OAuth-Proxy (siehe Schritt 2).
2. **OAuth-Proxy deployen** (kostenlos, da GitHub Pages selbst keinen Server hat).
   Fertige, offene Vorlagen, auf die auch die Decap-CMS-Doku verweist:
   - [ottmartens/decap-cms-github-oauth-provider-cloudflare](https://github.com/ottmartens/decap-cms-github-oauth-provider-cloudflare)
   - [sterlingwes/decap-proxy](https://github.com/sterlingwes/decap-proxy)

   Beide laufen als Cloudflare Worker (kostenloses Free-Tier reicht), ihr hinterlegt
   dort nur `CLIENT_ID`/`CLIENT_SECRET` aus Schritt 1 als Secrets.
3. In `admin/config.yml` `repo` auf `dein-name/dein-repo` setzen und `base_url`
   auf die URL eures deployten Workers.
4. Fertig – `/admin` ist erreichbar unter `https://<dein-name>.github.io/<repo>/admin/`

Mitwirkende brauchen weiterhin GitHub-Collaborator-Zugriff auf euer Repo, damit
der Login funktioniert – die Oberfläche ersetzt nicht die Zugriffskontrolle,
nur die Bedienung.

## Mitmachen

Siehe [CONTRIBUTING.md](CONTRIBUTING.md). Alternativ: Formular unter `/admin` nutzen.

## Lizenz

- Code (Scripts, Workflows): MIT
- Daten (`/data`): [ODbL](https://opendatacommons.org/licenses/odbl/) —
  Weitergabe/Ableitungen der Datenbank müssen unter derselben Lizenz erfolgen,
  Namensnennung erforderlich.

## Setup für Maintainer (einmalig)

1. Repo auf GitHub erstellen, diesen Ordnerinhalt pushen
2. Unter *Settings → Pages* als Source "GitHub Actions" wählen
3. `.github/CODEOWNERS` mit echten Usernamen befüllen
4. Branch Protection auf `main`: PR-Pflicht + CI muss grün sein
5. Ersten Tag/Release erstellen (z.B. `v1.0.0`), sobald genug Daten drin sind,
   damit Integratoren einen stabilen Snapshot referenzieren können
