"""Optional user-supplied unit prices (``prices.toml``) → $ / $-range estimates.

Type:Haus ships **no** default prices — material cost is local, seasonal, and negotiated,
so any bundled number would be authoritative-looking fiction. If a house directory carries
a ``prices.toml`` (next to ``preferences.toml``), `haus takeoff` and `haus variants
compare` decorate their quantity output with dollar estimates; without the file both
commands behave exactly as before.

Format — every section is optional, and every value is either a single number (an exact
unit price) or an inline table ``{ low = ..., high = ... }`` (a $-range, e.g. quotes from
two yards)::

    [framing]        # $ per lineal foot of ORDERED stock, keyed by lumber profile
    "2x4" = 0.72
    "2x6" = { low = 0.95, high = 1.35 }

    [sheet_goods]    # $ per 4x8 sheet, keyed by material tag
    osb = 22.50
    zip-r = { low = 42.0, high = 55.0 }

    [hardware]       # $ per takeoff unit (usually each), keyed by part number
    LUS210 = 1.85

    [concrete]       # $ per cubic yard placed, keyed by solid category (slab, footing, ...)
    slab = { low = 180, high = 240 }

    [floor_heat]     # $ per lineal foot of element/wire, keyed by system name
    electric = 12.0

    [placeables]     # $ each, keyed by catalog type tag
    wolf-range-36 = { low = 9500, high = 12500 }

Unpriced rows are never silently dropped from a total: every estimate carries the list of
quantity rows it could not price, so a partial catalog reads as a partial estimate rather
than a low bid.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Optional

try:  # tomllib is stdlib on 3.11+; the engine still supports 3.9
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on <3.11 only
    import tomli as tomllib  # type: ignore[no-redef]

PRICES_FILENAME = "prices.toml"

_SECTIONS = ("framing", "sheet_goods", "hardware", "concrete", "floor_heat", "placeables",
             "floor_finishes", "envelope_layers", "openings", "footing_bedding",
             "pipe_runs", "ducts", "sleeves", "conduit")


def _dollars(value: float) -> str:
    return f"-${abs(value):,.2f}" if value < 0 else f"${value:,.2f}"


@dataclass(frozen=True)
class PriceRange:
    """An exact price is a range whose ends coincide; arithmetic keeps ends sorted."""

    low: float
    high: float

    @property
    def is_exact(self) -> bool:
        return abs(self.high - self.low) < 1e-9

    def times(self, quantity: float) -> "PriceRange":
        ends = sorted((self.low * quantity, self.high * quantity))
        return PriceRange(ends[0], ends[1])

    def plus(self, other: "PriceRange") -> "PriceRange":
        return PriceRange(self.low + other.low, self.high + other.high)

    def fmt(self, signed: bool = False) -> str:
        prefix = "+" if signed and self.low >= 0 else ""
        if self.is_exact:
            return prefix + _dollars(self.low)
        return f"{prefix}{_dollars(self.low)} – {_dollars(self.high)}"

    def as_dict(self) -> dict:
        return {"low": round(self.low, 2), "high": round(self.high, 2)}


ZERO = PriceRange(0.0, 0.0)


@dataclass(frozen=True)
class Prices:
    """The parsed ``prices.toml``: per-section unit prices, each an exact $ or a $-range."""

    path: Path
    framing: Mapping[str, PriceRange] = field(default_factory=dict)
    sheet_goods: Mapping[str, PriceRange] = field(default_factory=dict)
    hardware: Mapping[str, PriceRange] = field(default_factory=dict)
    concrete: Mapping[str, PriceRange] = field(default_factory=dict)
    floor_heat: Mapping[str, PriceRange] = field(default_factory=dict)
    placeables: Mapping[str, PriceRange] = field(default_factory=dict)
    # The 2026-07-25 BOM sweep. An unpriced section is invisible in `haus variants compare`,
    # so every new billable family gets a table here even where no house supplies prices yet.
    floor_finishes: Mapping[str, PriceRange] = field(default_factory=dict)
    envelope_layers: Mapping[str, PriceRange] = field(default_factory=dict)
    openings: Mapping[str, PriceRange] = field(default_factory=dict)
    footing_bedding: Mapping[str, PriceRange] = field(default_factory=dict)
    pipe_runs: Mapping[str, PriceRange] = field(default_factory=dict)
    ducts: Mapping[str, PriceRange] = field(default_factory=dict)
    sleeves: Mapping[str, PriceRange] = field(default_factory=dict)
    conduit: Mapping[str, PriceRange] = field(default_factory=dict)


def _price(section: str, key: str, raw: object, path: Path) -> PriceRange:
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        value = float(raw)
        if value < 0:
            raise ValueError(f"{path}: [{section}] {key!r} is negative")
        return PriceRange(value, value)
    if isinstance(raw, dict):
        extra = set(raw) - {"low", "high"}
        if extra or set(raw) != {"low", "high"}:
            raise ValueError(
                f"{path}: [{section}] {key!r} must be a number or {{ low = ..., high = ... }}")
        low, high = float(raw["low"]), float(raw["high"])
        if low < 0 or high < low:
            raise ValueError(f"{path}: [{section}] {key!r} needs 0 <= low <= high")
        return PriceRange(low, high)
    raise ValueError(f"{path}: [{section}] {key!r} must be a number or {{ low, high }} table")


def load_prices(house_dir: Path) -> Optional[Prices]:
    """Read ``prices.toml`` if the house supplies one; ``None`` (not an error) if absent.

    A *malformed* file raises ``ValueError`` with the offending key — a mistyped price must
    never be silently priced at zero.
    """
    path = Path(house_dir) / PRICES_FILENAME
    if not path.exists():
        return None
    data = tomllib.loads(path.read_text())
    unknown = set(data) - set(_SECTIONS)
    if unknown:
        raise ValueError(f"{path}: unknown section(s) {sorted(unknown)}; "
                         f"expected {list(_SECTIONS)}")
    sections = {
        section: {str(key): _price(section, str(key), raw, path)
                  for key, raw in (data.get(section) or {}).items()}
        for section in _SECTIONS
    }
    return Prices(path=path, **sections)


def _sum(ranges: Iterable[PriceRange]) -> PriceRange:
    total = ZERO
    for item in ranges:
        total = total.plus(item)
    return total


def estimate_costs(bom: dict, prices: Prices) -> dict:
    """Price a :func:`typehaus.takeoff.bill_of_materials` payload against ``prices``.

    Returns ``{"sections": {name: {"rows": [...], "subtotal": {...}}}, "total": {...},
    "unpriced": [...]}}``. Sections the BOM has no rows for are omitted; rows without a
    price land in ``unpriced`` so the total is honest about what it excludes.
    """
    plans = (
        # (estimate section, bom key, price table, price key field, quantity field, unit)
        ("framing", "framing_by_size", prices.framing, "profile", "order_length_ft", "LF"),
        ("sheet_goods", "sheet_goods", prices.sheet_goods, "material", "sheets_4x8", "sheets"),
        ("hardware", "hardware", prices.hardware, "part_number", "count", "ea"),
        ("concrete", "structural_solids", prices.concrete, "category",
         "volume_cubic_yards", "cy"),
        ("floor_heat", "floor_heat", prices.floor_heat, "system", "wire_length_ft", "LF"),
        ("placeables", "placeables", prices.placeables, "type", "count", "ea"),
        # Priced on the *order* quantity, not the net area: a finish is bought with its
        # waste, and pricing net area would under-cost every plank and tile room.
        ("floor_finishes", "floor_finishes", prices.floor_finishes, "finish",
         "order_area_sqft", "SF"),
        ("envelope_layers", "envelope_layers", prices.envelope_layers, "material",
         "net_area_sqft", "SF"),
        ("openings", "openings", prices.openings, "type", "count", "ea"),
        ("footing_bedding", "footing_bedding", prices.footing_bedding, "aggregate",
         "volume_cubic_yards", "cy"),
        ("pipe_runs", "pipe_runs", prices.pipe_runs, "system", "length_ft", "LF"),
        ("ducts", "ducts", prices.ducts, "system", "length_ft", "LF"),
        ("sleeves", "sleeves", prices.sleeves, "sleeve_diameter_in", "count", "ea"),
        ("conduit", "conduit", prices.conduit, "trade_size_in", "length_ft", "LF"),
    )
    sections: dict[str, dict] = {}
    unpriced: list[dict] = []
    total = ZERO
    for name, bom_key, table, key_field, quantity_field, unit in plans:
        rows = []
        for row in bom.get(bom_key, []) or []:
            key = str(row.get(key_field))
            quantity = float(row.get(quantity_field) or 0.0)
            price = table.get(key)
            if price is None:
                if quantity:
                    unpriced.append({"section": name, "key": key,
                                     "quantity": round(quantity, 2), "unit": unit})
                continue
            cost = price.times(quantity)
            rows.append({"key": key, "quantity": round(quantity, 2), "unit": unit,
                         "unit_price": price.as_dict(), "cost": cost.as_dict(),
                         "cost_fmt": cost.fmt()})
        if rows:
            subtotal = _sum(PriceRange(r["cost"]["low"], r["cost"]["high"]) for r in rows)
            sections[name] = {"rows": rows, "subtotal": subtotal.as_dict(),
                              "subtotal_fmt": subtotal.fmt()}
            total = total.plus(subtotal)
    return {"sections": sections, "total": total.as_dict(), "total_fmt": total.fmt(),
            "unpriced": unpriced}
