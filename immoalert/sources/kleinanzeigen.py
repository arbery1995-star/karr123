"""Scraper für kleinanzeigen.de (Immobilien zum Kauf).

Nutzt die Umkreissuche der Seite selbst (PLZ/Ort + Radius), daher ist kein
eigenes Geocoding nötig. Die HTML-Struktur kann sich jederzeit ändern –
Selektoren ggf. in parse_results() anpassen.
"""

import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .. import config
from .base import Listing, SearchQuery, extract_rent, parse_number

BASE = "https://www.kleinanzeigen.de"
SEARCH_URL = BASE + "/s-suchanfrage.html"
CATEGORIES = {"wohnung": 196, "haus": 208, "mehrfamilienhaus": 208}
KEYWORDS = {"mehrfamilienhaus": "Mehrfamilienhaus"}
ALLOWED_RADII = [5, 10, 20, 30, 50, 100, 150, 200]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9",
}


def _radius(km):
    return next((r for r in ALLOWED_RADII if r >= km), ALLOWED_RADII[-1])


def parse_results(html):
    soup = BeautifulSoup(html, "html.parser")
    listings = []
    for item in soup.select("article.aditem"):
        ad_id = item.get("data-adid")
        link = item.select_one("a.ellipsis") or item.select_one("h2 a")
        if not ad_id or not link:
            continue
        tags = [t.get_text(" ", strip=True) for t in item.select(".simpletag")]
        size = next((parse_number(t) for t in tags if "m²" in t), None)
        rooms = next((parse_number(t) for t in tags if "Zi" in t), None)
        price_el = item.select_one(".aditem-main--middle--price-shipping--price")
        desc_el = item.select_one(".aditem-main--middle--description")
        loc_el = item.select_one(".aditem-main--top--left")
        img_el = item.select_one(".imagebox img")
        description = desc_el.get_text(" ", strip=True) if desc_el else ""
        title = link.get_text(" ", strip=True)
        listings.append(Listing(
            source="kleinanzeigen",
            id=ad_id,
            title=title,
            url=urljoin(BASE, item.get("data-href") or link.get("href", "")),
            price=parse_number(price_el.get_text(" ", strip=True)) if price_el else None,
            size_sqm=size,
            rooms=rooms,
            location=loc_el.get_text(" ", strip=True) if loc_el else "",
            description=description,
            image=(img_el.get("src") or img_el.get("data-imgsrc") or "") if img_el else "",
            actual_rent=extract_rent(f"{title} {description}"),
        ))
    next_link = soup.select_one("a.pagination-next")
    next_url = urljoin(BASE, next_link["href"]) if next_link and next_link.get("href") else None
    return listings, next_url


def search(query: SearchQuery, session=None):
    session = session or requests.Session()
    params = {
        "keywords": KEYWORDS.get(query.property_type, ""),
        "categoryId": CATEGORIES[query.property_type],
        "locationStr": query.location,
        "radius": _radius(query.radius_km),
        "sortingField": "SORTING_DATE",
    }
    if query.max_price:
        params["maxPrice"] = int(query.max_price)

    resp = session.get(SEARCH_URL, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    results = []
    for page in range(config.MAX_PAGES):
        listings, next_url = parse_results(resp.text)
        results.extend(listings)
        if not next_url or page + 1 >= config.MAX_PAGES:
            break
        time.sleep(config.REQUEST_DELAY)
        resp = session.get(next_url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    return results
