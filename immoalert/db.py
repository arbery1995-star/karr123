import sqlite3
from contextlib import contextmanager

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS subscriptions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT NOT NULL,
    property_type   TEXT NOT NULL,          -- wohnung | haus
    location        TEXT NOT NULL,          -- PLZ oder Ort
    radius_km       INTEGER NOT NULL,
    min_cashflow    REAL NOT NULL,          -- gewünschter Überschuss €/Monat
    max_price       REAL,
    min_size        REAL,
    rent_per_sqm    REAL NOT NULL,          -- erwartete Kaltmiete €/m²
    equity          REAL NOT NULL,          -- Eigenkapital €
    interest_pct    REAL NOT NULL,
    repayment_pct   REAL NOT NULL,
    closing_pct     REAL NOT NULL,          -- Kaufnebenkosten %
    costs_pct       REAL NOT NULL,          -- nicht umlagefähige Kosten % der Miete
    frequency       INTEGER NOT NULL,       -- 1 oder 2 Mails pro Tag
    token           TEXT NOT NULL UNIQUE,
    confirmed       INTEGER NOT NULL DEFAULT 0,
    active          INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS sent_listings (
    subscription_id INTEGER NOT NULL,
    listing_key     TEXT NOT NULL,
    sent_at         TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (subscription_id, listing_key)
);
"""


@contextmanager
def connect(path=None):
    conn = sqlite3.connect(path or config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init(path=None):
    with connect(path) as conn:
        conn.executescript(SCHEMA)
