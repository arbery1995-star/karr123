"""Findet Unternehmen via Google Places API, die in ihrem Google-My-Business-
Profil KEINE Website hinterlegt haben.

Nutzt die offizielle Google Places API (Text Search + Place Details).
Braucht einen API-Key mit aktivierter "Places API":
https://console.cloud.google.com/google/maps-apis/credentials

Usage:
    export GOOGLE_PLACES_API_KEY=AIza...
    python gmb_no_website.py --query "Friseur in Berlin" --max-results 60 --out leads.csv
"""

import argparse
import csv
import os
import time

import requests

TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


def search_places(query: str, api_key: str, max_results: int):
    results = []
    params = {"query": query, "key": api_key}
    while True:
        resp = requests.get(TEXT_SEARCH_URL, params=params, timeout=15).json()
        status = resp.get("status")
        if status not in ("OK", "ZERO_RESULTS"):
            raise RuntimeError(f"Places API error: {status} - {resp.get('error_message')}")
        results.extend(resp.get("results", []))
        next_token = resp.get("next_page_token")
        if not next_token or len(results) >= max_results:
            break
        # Google requires a short delay before a next_page_token becomes valid.
        time.sleep(2)
        params = {"pagetoken": next_token, "key": api_key}
    return results[:max_results]


def get_details(place_id: str, api_key: str):
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,url,rating,user_ratings_total",
        "key": api_key,
    }
    resp = requests.get(DETAILS_URL, params=params, timeout=15).json()
    if resp.get("status") != "OK":
        return None
    return resp.get("result", {})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True, help='z.B. "Friseur in Berlin"')
    parser.add_argument("--max-results", type=int, default=60)
    parser.add_argument("--out", default="leads_no_website.csv")
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise SystemExit("Bitte GOOGLE_PLACES_API_KEY als Umgebungsvariable setzen.")

    print(f"Suche: {args.query!r} (bis zu {args.max_results} Treffer) ...")
    places = search_places(args.query, api_key, args.max_results)
    print(f"{len(places)} Treffer gefunden, hole Details ...")

    leads = []
    for place in places:
        details = get_details(place["place_id"], api_key)
        if details is None:
            continue
        if not details.get("website"):
            leads.append(details)
        time.sleep(0.05)  # sanftes Rate-Limiting

    print(f"{len(leads)} Unternehmen OHNE Website im GMB-Profil gefunden.")

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "address", "phone", "rating", "reviews", "maps_url"])
        for lead in leads:
            writer.writerow([
                lead.get("name", ""),
                lead.get("formatted_address", ""),
                lead.get("formatted_phone_number", ""),
                lead.get("rating", ""),
                lead.get("user_ratings_total", ""),
                lead.get("url", ""),
            ])

    print(f"Gespeichert in {args.out}")


if __name__ == "__main__":
    main()
