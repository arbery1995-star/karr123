from pathlib import Path

import pytest

from immoalert import cashflow
from immoalert.sources import kleinanzeigen
from immoalert.sources.base import extract_rent, parse_number

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_number():
    assert parse_number("199.000 € VB") == 199000
    assert parse_number("81,5 m²") == 81.5
    assert parse_number("VB") is None


def test_extract_rent():
    assert extract_rent("vermietet, Kaltmiete 520 € monatlich") == 520
    assert extract_rent("vermietet, Jahresnettokaltmiete 12.000 €") == 1000
    assert extract_rent("Frei ab sofort, Kaufpreis 199.000 €") is None


def test_cashflow():
    a = cashflow.Assumptions(rent_per_sqm=10, equity=20000, interest_pct=4, repayment_pct=2,
                             closing_pct=10, costs_pct=10)
    r = cashflow.calculate(100000, 60, a)
    # Darlehen 110.000 - 20.000 = 90.000 -> Rate 450 €, Miete 600 €, Kosten 60 €
    assert (r.loan, r.loan_payment, r.rent, r.costs, r.cashflow) == (90000, 450, 600, 60, 90)
    assert r.rent_estimated
    assert cashflow.calculate(100000, None, a, actual_rent=700).rent_estimated is False
    assert cashflow.calculate(None, 60, a) is None


def test_kleinanzeigen_parse():
    listings, next_url = kleinanzeigen.parse_results((FIXTURES / "kleinanzeigen_search.html").read_text())
    assert next_url.endswith("/seite:2/c196l1234r20")
    a, b = listings
    assert (a.id, a.price, a.size_sqm, a.rooms, a.actual_rent) == ("2901", 119000, 54, 2, 520)
    assert a.url == "https://www.kleinanzeigen.de/s-anzeige/vermietete-wohnung/2901-196-3331"
    assert a.location.startswith("44135")
    assert (b.price, b.size_sqm, b.actual_rent) == (249500, 81.5, None)


@pytest.fixture
def app_env(tmp_path, monkeypatch):
    from immoalert import config
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setattr(config, "OUTBOX_DIR", str(tmp_path / "outbox"))
    monkeypatch.setattr(config, "SMTP_HOST", "")
    monkeypatch.setattr(config, "SOURCES", ["demo"])
    monkeypatch.setattr(config, "REQUEST_DELAY", 0)
    from immoalert import db, web
    db.init()
    return web.app.test_client(), tmp_path


FORM = {"property_type": "wohnung", "location": "44135", "radius_km": "20", "min_cashflow": "50",
        "rent_per_sqm": "11", "equity": "30000", "interest_pct": "3.8", "repayment_pct": "2",
        "closing_pct": "10", "costs_pct": "15", "email": "test@example.com", "frequency": "2",
        "consent": "1"}


def test_full_flow(app_env):
    from immoalert import db, jobs
    client, tmp = app_env
    assert client.get("/").status_code == 200
    assert client.post("/", data={**FORM, "email": "kaputt"}).status_code == 400
    assert client.post("/", data=FORM).status_code == 200

    with db.connect() as conn:
        token = conn.execute("SELECT token FROM subscriptions").fetchone()[0]
    jobs.run("morning")  # noch nicht bestätigt -> keine Treffer-Mail
    assert len(list((tmp / "outbox").iterdir())) == 1  # nur Bestätigungsmail

    assert client.get(f"/bestaetigen/{token}").status_code == 200
    jobs.run("evening")
    mails = sorted((tmp / "outbox").iterdir())
    assert len(mails) == 2
    body = mails[-1].read_text()
    assert "Vermietete 2-Zi.-Wohnung" in body       # Ist-Miete 640 € -> positiver Cashflow
    assert "Helle 3-Zimmer-Wohnung" not in body     # 289k bei 78 m² lohnt sich nicht

    jobs.run("morning")  # gleiche Inserate werden nicht erneut geschickt
    assert len(list((tmp / "outbox").iterdir())) == 2

    assert client.get(f"/abmelden/{token}").status_code == 200
    assert client.get("/abmelden/falsch").status_code == 404
