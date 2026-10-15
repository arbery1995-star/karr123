"""Konfiguration über Umgebungsvariablen (siehe README)."""

import os

DB_PATH = os.environ.get("IMMOALERT_DB", "immoalert.sqlite3")
BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5000").rstrip("/")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "ImmoAlert <alert@example.com>")
# Ohne SMTP_HOST werden Mails nicht verschickt, sondern als .html in diesen Ordner geschrieben.
OUTBOX_DIR = os.environ.get("OUTBOX_DIR", "outbox")

# Aktive Quellen, kommagetrennt. "demo" liefert Beispieldaten zum Testen ohne Netz.
SOURCES = [s.strip() for s in os.environ.get("IMMOALERT_SOURCES", "kleinanzeigen").split(",") if s.strip()]
# Pause zwischen zwei Requests an dieselbe Seite (Sekunden).
REQUEST_DELAY = float(os.environ.get("REQUEST_DELAY", "3"))
MAX_PAGES = int(os.environ.get("MAX_PAGES", "3"))
