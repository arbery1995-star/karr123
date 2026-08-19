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
