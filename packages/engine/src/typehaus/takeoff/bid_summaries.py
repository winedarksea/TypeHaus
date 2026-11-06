"""The schedule a trade prices from, beside its bid BOM.

A window supplier reads a schedule, a roofer five roof numbers, an electrician an opening
count; the BOM (``bid_package``) stays the detail for a sub who wants it. Every summary is
a view of quantities the model already derives, regrouped the way that trade quotes; none
adds to the estimate. Cells are typed (a count is an ``int``) so the CSV opens as numbers.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from importlib import import_module
from typing import Any

from typehaus.quantities import M_PER_FT

Cell = str | int | float


@dataclass(frozen=True)
class SummaryTable:
    slug: str  # its CSV is ``<trade>-<slug>.csv``
    title: str
    columns: tuple[str, ...]
    rows: tuple[tuple[Cell, ...], ...]
    notes: tuple[str, ...] = ()

    def as_dicts(self) -> list[dict[str, Cell]]:
        return [dict(zip(self.columns, row, strict=True)) for row in self.rows]


@dataclass(frozen=True)
class SummaryInputs:
    model: Any
    bom: Mapping[str, Any]
    #: Opening tag -> the R308.4 clause making its glazing hazardous (``safety_glazing_clauses``).
    glazing: Mapping[str, str] = field(default_factory=dict)
    #: Window tag -> the sleeping room it is a compliant R310 escape for.
    egress: Mapping[str, str] = field(default_factory=dict)
    #: ``{trade: BidPackage}``: a summary may restate a package's own lines.
    packages: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TradeSummary:
    trade: str
    title: str
    intro: str
    tables: tuple[SummaryTable, ...]


Builder = Callable[[SummaryInputs], list[SummaryTable]]

#: trade -> (title, intro, "module:function"). Builders import lazily: most runs need few.
SUMMARIES: dict[str, tuple[str, str, str]] = {
    "openings": ("Window and door schedule",
                 "One row per opening, the marks on the plans: location, size, rough "
                 "opening, hand, jamb, and where code requires safety glazing or egress.",
                 "summary_openings:openings_summary"),
    "millwork": ("Interior door schedule and trim pack",
                 "Interior doors one row per opening, then base, casing and jambs packed "
                 "into the house's stock lengths.",
                 "summary_finishes:millwork_summary"),
    "roofing": ("Roof geometry",
                "Area in squares, pitch, and the eave, rake, ridge, hip and valley lengths.",
                "summary_envelope:roofing_summary"),
    "siding": ("Siding by elevation",
               "Cladding area per elevation in squares, then the trim and accessories.",
               "summary_envelope:siding_summary"),
    "drywall": ("Board summary",
                "Board area and sheet count by storey and type, ceiling heights, and the "
                "finish level.", "summary_envelope:drywall_summary"),
    "flooring": ("Room finish schedule",
                 "Net floor area per room by finish (add your own waste), its underlayment, "
                 "and the base.", "summary_finishes:flooring_summary"),
    "tile": ("Tile schedule", "Floor and wall tile per room, net, and the membrane under it.",
             "summary_finishes:tile_summary"),
    "plumbing": ("Fixture count",
                 "Fixtures by kind, then each fixture with its room, model and spec sheet.",
                 "summary_mep:plumbing_summary"),
    "electrical": ("Opening and device count",
                   "Devices and luminaires by kind and storey, the dedicated and 240 V "
                   "circuits, and the panels.", "summary_mep:electrical_summary"),
}


def _builder(path: str) -> Builder:
    module, name = path.split(":")
    return getattr(import_module(f"typehaus.takeoff.{module}"), name)


def build_summaries(inputs: SummaryInputs,
                    trades: tuple[str, ...] | None = None) -> dict[str, TradeSummary]:
    """``{trade: TradeSummary}`` for every trade with a summary and at least one row."""
    out: dict[str, TradeSummary] = {}
    for trade, (title, intro, path) in SUMMARIES.items():
        if trades is not None and trade not in trades:
            continue
        tables = tuple(t for t in _builder(path)(inputs) if t.rows)
        if tables:
            out[trade] = TradeSummary(trade, title, intro, tables)
    return out


def ft(length_m: float | None) -> float:
    """Metres to feet at 0.1 ft, the precision every summary prints."""
    return 0.0 if length_m is None else round(length_m / M_PER_FT, 1)


def sqft(area_m2: float | None) -> float:
    return 0.0 if area_m2 is None else round(area_m2 / M_PER_FT ** 2, 1)
