"""Beispieldaten, um Frontend, Matching und Mailversand ohne Netz zu testen."""

from .base import Listing, SearchQuery

_DATA = [
    ("1", "wohnung", "Vermietete 2-Zi.-Wohnung als Kapitalanlage", 99000, 58, 2, 640),
    ("2", "wohnung", "Helle 3-Zimmer-Wohnung mit Balkon", 289000, 78, 3, None),
    ("3", "wohnung", "Kleines Apartment nahe Uni", 79000, 31, 1, None),
    ("4", "haus", "Reihenhaus mit Garten", 349000, 120, 5, None),
    ("5", "mehrfamilienhaus", "MFH mit 6 Einheiten, voll vermietet", 690000, 410, 18, 4300),
]


def search(query: SearchQuery, session=None):
    out = []
    for id_, ptype, title, price, size, rooms, rent in _DATA:
        if ptype != query.property_type:
            continue
        if query.max_price and price > query.max_price:
            continue
        out.append(Listing(
            source="demo", id=id_, title=title, url=f"https://example.com/expose/{id_}",
            price=price, size_sqm=size, rooms=rooms, location=f"{query.location} (Demo)",
            actual_rent=rent,
        ))
    return out
