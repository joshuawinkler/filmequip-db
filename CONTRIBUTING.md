# Mitmachen

Danke, dass du zur Filmequipment-Datenbank beitragen willst! Zwei Wege stehen offen:

## Weg 1: Ohne Git-Kenntnisse

Öffne ein [Issue](../../issues/new/choose) mit der Vorlage "Neues Gerät hinzufügen"
und trage die Daten ein, die du kennst. Ein Maintainer baut daraus einen Pull Request.

## Weg 2: Per Pull Request

1. Repo forken, Branch anlegen
2. Neue Datei unter `data/<kategorie>/<id>.yaml` anlegen
   - `<id>` = `hersteller-modell-slug`, nur Kleinbuchstaben, Zahlen, Bindestriche
   - Dateiname muss exakt der `id` im Dokument entsprechen
3. Lokal validieren, bevor du den PR öffnest:
   ```bash
   pip install pyyaml jsonschema
   python3 scripts/validate.py
   ```
4. PR öffnen. Die CI validiert automatisch; ein Maintainer reviewt danach.

## Regeln für Daten

- **Nur öffentlich verifizierbare technische Daten** (Herstellerseite, Datenblatt) —
  keine Vermutungen, keine persönlichen Erfahrungswerte als Fakt eintragen.
- Jeder Eintrag braucht eine `source_url`.
- Keine Preise, keine Verleih-spezifischen Informationen — das Projekt bildet
  Geräte-Fakten ab, keine kommerziellen Konditionen.
- Bilder: nur `image_url` auf frei lizenzierte Quellen (z.B. Wikimedia Commons)
  verlinken, keine eigenen Bild-Uploads ins Repo.

## Neue Kategorie / neues Schema-Feld vorschlagen

Öffne ein Issue mit Label `schema-change` und beschreibe den Bedarf — Schema-Änderungen
betreffen alle Integratoren der API, deshalb werden sie bewusst langsamer behandelt.
