"""Scrapt alle Quellen für alle aktiven Suchaufträge und verschickt die Treffer.

    python -m immoalert.jobs --slot morning   # alle Abos (1x und 2x täglich)
    python -m immoalert.jobs --slot evening   # nur Abos mit 2x täglich
    python -m immoalert.jobs --loop           # läuft dauerhaft, 07:00 und 18:00 Uhr
"""

import argparse
import time
import traceback
from datetime import datetime, timedelta

import requests

from . import cashflow, config, db, mailer
from .sources import REGISTRY
from .sources.base import SearchQuery

MAX_RESULTS_PER_MAIL = 30
RUN_TIMES = {"morning": (7, 0), "evening": (18, 0)}


def _query_for(sub):
    return SearchQuery(
        property_type=sub["property_type"],
        location=sub["location"].strip().lower(),
        radius_km=sub["radius_km"],
        max_price=sub["max_price"],
    )


def collect(queries):
    """Scrapt jede eindeutige Suche genau einmal pro Quelle."""
    session = requests.Session()
    results = {}
    for q in queries:
        key = (q.property_type, q.location, q.radius_km, q.max_price)
        if key in results:
            continue
        found = []
        for name in config.SOURCES:
            try:
                found.extend(REGISTRY[name](q, session=session))
            except Exception:
                print(f"[scrape] Fehler bei {name} für {key}:")
                traceback.print_exc()
            time.sleep(config.REQUEST_DELAY if name != "demo" else 0)
        print(f"[scrape] {key}: {len(found)} Inserate")
        results[key] = found
    return results


def matches_for(sub, listings, already_sent):
    a = cashflow.Assumptions(
        rent_per_sqm=sub["rent_per_sqm"], equity=sub["equity"],
        interest_pct=sub["interest_pct"], repayment_pct=sub["repayment_pct"],
        closing_pct=sub["closing_pct"], costs_pct=sub["costs_pct"],
    )
    out = []
    for listing in listings:
        if listing.key in already_sent:
            continue
        if sub["min_size"] and (not listing.size_sqm or listing.size_sqm < sub["min_size"]):
            continue
        if sub["max_price"] and listing.price and listing.price > sub["max_price"]:
            continue
        calc = cashflow.calculate(listing.price, listing.size_sqm, a, listing.actual_rent)
        if calc and calc.cashflow >= sub["min_cashflow"]:
            out.append((listing, calc))
    out.sort(key=lambda lc: lc[1].cashflow, reverse=True)
    return out[:MAX_RESULTS_PER_MAIL]


def run(slot="morning"):
    db.init()
    with db.connect() as conn:
        subs = conn.execute(
            "SELECT * FROM subscriptions WHERE confirmed = 1 AND active = 1"
            + (" AND frequency = 2" if slot == "evening" else "")
        ).fetchall()
    if not subs:
        print("Keine aktiven Suchaufträge.")
        return

    results = collect(_query_for(s) for s in subs)

    for sub in subs:
        q = _query_for(sub)
        listings = results[(q.property_type, q.location, q.radius_km, q.max_price)]
        with db.connect() as conn:
            sent = {r[0] for r in conn.execute(
                "SELECT listing_key FROM sent_listings WHERE subscription_id = ?", (sub["id"],))}
            hits = matches_for(sub, listings, sent)
            if not hits:
                continue
            unsubscribe = f"{config.BASE_URL}/abmelden/{sub['token']}"
            html = mailer.render("email_results.html", sub=sub, hits=hits, unsubscribe_url=unsubscribe)
            try:
                mailer.send(sub["email"], f"{len(hits)} neue Immobilien mit Überschuss ≥ "
                            f"{sub['min_cashflow']:.0f} €", html, unsubscribe)
            except Exception:
                traceback.print_exc()
                continue
            conn.executemany(
                "INSERT OR IGNORE INTO sent_listings (subscription_id, listing_key) VALUES (?, ?)",
                [(sub["id"], listing.key) for listing, _ in hits],
            )
        print(f"[mail] {sub['email']}: {len(hits)} Treffer")


def loop():
    while True:
        now = datetime.now()
        upcoming = []
        for slot, (h, m) in RUN_TIMES.items():
            t = now.replace(hour=h, minute=m, second=0, microsecond=0)
            upcoming.append((t if t > now else t + timedelta(days=1), slot))
        when, slot = min(upcoming)
        print(f"Nächster Lauf ({slot}) um {when:%d.%m. %H:%M}")
        time.sleep((when - datetime.now()).total_seconds())
        try:
            run(slot)
        except Exception:
            traceback.print_exc()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--slot", choices=RUN_TIMES, default="morning")
    p.add_argument("--loop", action="store_true")
    args = p.parse_args()
    loop() if args.loop else run(args.slot)
