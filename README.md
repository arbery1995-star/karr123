# karr123

Setup für [ScrapeGraphAI](https://github.com/ScrapeGraphAI/Scrapegraph-ai) — ein Python-Framework zum Scrapen von Webseiten mit LLMs.

## Installation

```bash
pip install -r requirements.txt
```

Für den Playwright-basierten Headless-Browser (wird von manchen Graphs benötigt):

```bash
playwright install
```

## Verwendung

Setze deinen LLM-API-Key als Umgebungsvariable (z. B. `OPENAI_API_KEY`) und führe das Beispiel aus:

```bash
export OPENAI_API_KEY=sk-...
python example.py
```

Siehe `example.py` für ein minimales Beispiel mit `SmartScraperGraph`.

## Lead-Finder: Unternehmen ohne Website (GMB + Instagram)

Findet Unternehmen, die weder in ihrem Google-My-Business-Profil noch in
ihrer Instagram-Bio eine Website hinterlegt haben. Zwei Schritte:

**1. Google-My-Business-Check** (offizielle Places API, braucht API-Key aus
der [Google Cloud Console](https://console.cloud.google.com/google/maps-apis/credentials)
mit aktivierter "Places API"):

```bash
export GOOGLE_PLACES_API_KEY=AIza...
python gmb_no_website.py --query "Friseur in Berlin" --max-results 60 --out leads.csv
```

Ergebnis: `leads.csv` mit Name, Adresse, Telefon, Bewertung und Maps-Link
aller Treffer ohne Website im GMB-Profil.

**2. Instagram-Check** — ergänze in `leads.csv` manuell eine Spalte
`instagram_handle` (Instagram bietet keine öffentliche Such-API mehr, die
Handles musst du selbst recherchieren, z. B. über die Google-Suche). Dann:

```bash
python check_instagram_website.py --in leads.csv --out final_leads.csv
```

**Wichtig:** `check_instagram_website.py` muss auf deinem eigenen Rechner
laufen, nicht in einer Sandbox/CI-Umgebung ohne Zugriff auf instagram.com.
Instagram blockt Anfragen von Rechenzentrums-IPs schnell — bei vielen
Handles ggf. den `--delay` erhöhen.
