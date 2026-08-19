"""Prueft fuer eine Liste von Instagram-Handles, ob im Profil (Bio) ein
externer Website-Link hinterlegt ist.

WICHTIG: Muss lokal auf deinem eigenen Rechner laufen (nicht in dieser
Sandbox), da instagram.com hier per Netzwerk-Policy blockiert ist.

Instagram bietet keine offizielle Such-API fuer beliebige Business-Profile
mehr, daher muss die Spalte "instagram_handle" manuell befuellt werden
(z.B. handle aus der Google-Suche, dem Linktree im GMB-Profil, etc.).

Usage:
    pip install requests
    python check_instagram_website.py --in leads_with_handles.csv --out final_leads.csv

Erwartet in der Input-CSV mindestens eine Spalte "instagram_handle"
(ohne @, z.B. "friseur_mueller_berlin"). Alle anderen Spalten werden
durchgereicht.
"""

import argparse
import csv
import re
import time

import requests

PROFILE_URL = "https://www.instagram.com/{handle}/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9",
}

EXTERNAL_URL_RE = re.compile(r'"external_url":"([^"]*)"')


def get_external_url(handle: str) -> str | None:
    resp = requests.get(PROFILE_URL.format(handle=handle), headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        return None
    match = EXTERNAL_URL_RE.search(resp.text)
    if not match or not match.group(1):
        return None
    return match.group(1).replace("\\u0026", "&")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="infile", required=True)
    parser.add_argument("--out", dest="outfile", default="final_leads.csv")
    parser.add_argument("--delay", type=float, default=3.0, help="Sekunden zwischen Requests")
    args = parser.parse_args()

    with open(args.infile, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows or "instagram_handle" not in rows[0]:
        raise SystemExit('Input-CSV braucht eine Spalte "instagram_handle".')

    fieldnames = list(rows[0].keys()) + ["instagram_website"]
    results = []

    for row in rows:
        handle = (row.get("instagram_handle") or "").strip().lstrip("@")
        if not handle:
            row["instagram_website"] = "kein handle angegeben"
            results.append(row)
            continue
        try:
            url = get_external_url(handle)
        except requests.RequestException as exc:
            url = f"FEHLER: {exc}"
        row["instagram_website"] = url or "keine Website in Bio"
        results.append(row)
        print(f"{handle}: {row['instagram_website']}")
        time.sleep(args.delay)

    with open(args.outfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    no_website = [r for r in results if r["instagram_website"] == "keine Website in Bio"]
    print(f"\n{len(no_website)} von {len(results)} haben auch auf Instagram keine Website.")
    print(f"Gespeichert in {args.outfile}")


if __name__ == "__main__":
    main()
