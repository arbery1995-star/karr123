import re
from dataclasses import dataclass, field


@dataclass
class SearchQuery:
    property_type: str  # wohnung | haus | mehrfamilienhaus
    location: str
    radius_km: int
    max_price: float | None = None


@dataclass
class Listing:
    source: str
    id: str
    title: str
    url: str
    price: float | None = None
    size_sqm: float | None = None
    rooms: float | None = None
    location: str = ""
    description: str = ""
    image: str = ""
    actual_rent: float | None = None  # aus dem Inserat gelesene Ist-Miete €/Monat
    extra: dict = field(default_factory=dict)

    @property
    def key(self):
        return f"{self.source}:{self.id}"


def parse_number(text):
    """'199.000 € VB' -> 199000.0, '85,5 m²' -> 85.5, 'VB' -> None"""
    if not text:
        return None
    m = re.search(r"\d[\d.]*(?:,\d+)?", text)
    if not m:
        return None
    return float(m.group(0).replace(".", "").replace(",", "."))


_RENT_MONTHLY = re.compile(
    r"(?:kaltmiete|nettokaltmiete|mieteinnahmen?|ist-miete|miete)\D{0,40}?"
    r"(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?)\s*(?:€|eur)",
    re.IGNORECASE,
)
_RENT_YEARLY = re.compile(
    r"(?:jahres(?:netto)?(?:kalt)?miete|mieteinnahmen?\s*(?:p\.\s?a\.|pro jahr|jährlich))\D{0,40}?"
    r"(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?)\s*(?:€|eur)",
    re.IGNORECASE,
)


def extract_rent(text):
    """Liest eine Ist-Miete (€/Monat) aus dem Inseratstext, falls angegeben."""
    if not text or not re.search(r"vermietet|mieteinnahme|kapitalanlage|ist-miete", text, re.I):
        return None
    if m := _RENT_YEARLY.search(text):
        value = parse_number(m.group(1))
        return round(value / 12, 2) if value else None
    if m := _RENT_MONTHLY.search(text):
        value = parse_number(m.group(1))
        # Plausibilitätscheck gegen Treffer wie Kaufpreise
        return value if value and 100 <= value <= 50000 else None
    return None
