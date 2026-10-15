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

## ImmoAlert: Renditeimmobilien mit Überschuss per Mail

Web-Formular, in dem Nutzer Immobilientyp, Ort + Umkreis und den gewünschten
monatlichen Überschuss angeben. Ein Job scrapt 1–2× täglich die Portale,
rechnet jedes Inserat durch und schickt nur passende, noch nicht verschickte
Treffer per Mail (Double-Opt-in, Abmeldelink in jeder Mail).

**Überschuss** = Kaltmiete − Kreditrate (Zins + Tilgung auf Kaufpreis +
Nebenkosten − Eigenkapital) − nicht umlagefähige Kosten, vor Steuern. Steht im
Inserat eine Ist-Miete („vermietet, Kaltmiete 650 €“), wird diese genommen,
sonst Fläche × erwartete €/m²-Miete des Nutzers.

```bash
pip install -r requirements.txt
flask --app immoalert.web run                  # Frontend auf http://localhost:5000
python -m immoalert.jobs --slot morning        # einmal scrapen + Mails schicken
python -m immoalert.jobs --loop                # dauerhaft: 07:00 (alle) und 18:00 (2×-täglich-Abos)
IMMOALERT_SOURCES=demo python -m immoalert.jobs  # Testlauf mit Beispieldaten ohne Netz
pytest
```

Alternativ per Cron statt `--loop`:

```
0 7  * * *  cd /pfad/karr123 && python -m immoalert.jobs --slot morning
0 18 * * *  cd /pfad/karr123 && python -m immoalert.jobs --slot evening
```

Konfiguration über Umgebungsvariablen (`immoalert/config.py`):
`APP_BASE_URL` (für Links in Mails), `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`,
`SMTP_PASSWORD`, `SMTP_FROM`, `IMMOALERT_SOURCES` (Standard: `kleinanzeigen`),
`REQUEST_DELAY`, `MAX_PAGES`, `IMMOALERT_DB`. Ohne `SMTP_HOST` landen Mails
als HTML-Datei in `outbox/`.

**Quellen:** Aktuell ist Kleinanzeigen angebunden (`immoalert/sources/kleinanzeigen.py`),
weitere Portale werden als Funktion `search(query, session)` in
`immoalert/sources/__init__.py` registriert. Jede Suche (Typ + Ort + Radius)
wird pro Lauf nur einmal gescrapt, egal wie viele Nutzer sie abonniert haben.

**Rechtlicher Hinweis:** ImmoScout24, Immowelt und Kleinanzeigen untersagen
automatisiertes Auslesen in ihren AGB, ImmoScout24 blockt Scraper zudem aktiv.
Für einen öffentlichen Dienst mit fremden Nutzern solltest du die offiziellen
Partner-Schnittstellen (z. B. ImmoScout24-API) nutzen oder die Erlaubnis der
Portale einholen. Außerdem brauchst du Impressum und Datenschutzerklärung.
