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

    [furnishings]    # $ each, keyed by catalog type tag — the same rows [placeables]
    ikea-sofa-84 = { low = 700, high = 2400 }   # reads, but reported beside the total

Unpriced rows are never silently dropped from a total: every estimate carries the list of
quantity rows it could not price, so a partial catalog reads as a partial estimate rather
than a low bid.

Nor are they silently *added*: what a sofa costs is not what the house costs. Sections in
``EXCLUDED_FROM_TOTAL`` are priced and reported like any other and then summed into
``excluded_total`` rather than ``total``, which is why there is a [furnishings] table with
the same keys as [placeables] — where the line falls between built-in and loose is the
owner's call, made by which table a type is written into, and no type may sit in both.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:  # tomllib is stdlib on 3.11+; the engine still supports 3.9
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on <3.11 only
    import tomli as tomllib  # type: ignore[no-redef,import-not-found]

PRICES_FILENAME = "prices.toml"

_SECTIONS = ("framing", "sheet_goods", "hardware", "concrete", "floor_heat", "placeables",
             "floor_finishes", "envelope_layers", "wood_surfaces", "openings",
             "footing_bedding",
             "pipe_runs", "ducts", "sleeves", "conduit",
             # Plumbing specialties (2026-08-01): devices by the piece, their loose install
             # kits, and hot-line insulation by the foot.
             "plumbing_specialties", "install_parts", "pipe_insulation",
             "edge_trim",
             # Monolithic wall structure (2026-08-03): concrete/masonry walls by the yard.
             "wall_structure",
             # Sheet-metal families the yard is the wrong unit for (2026-08-08): guards and
             # gutter/leader runs by the foot.
             "railings", "drainage",
             # Pre-framing construction-rule returns (2026-08-18), by the lineal foot.
             "construction_returns",
             # Loose furnishings (2026-08-08) — priced, reported, and deliberately *not*
             # summed into the construction total. See ``EXCLUDED_FROM_TOTAL``.
             "furnishings")


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

    def times(self, quantity: float) -> PriceRange:
        ends = sorted((self.low * quantity, self.high * quantity))
        return PriceRange(ends[0], ends[1])

    def plus(self, other: PriceRange) -> PriceRange:
        return PriceRange(self.low + other.low, self.high + other.high)

    def fmt(self, signed: bool = False) -> str:
        prefix = "+" if signed and self.low >= 0 else ""
        if self.is_exact:
            return prefix + _dollars(self.low)
        return f"{prefix}{_dollars(self.low)} – {_dollars(self.high)}"

    def as_dict(self) -> dict[str, float]:
        return {"low": round(self.low, 2), "high": round(self.high, 2)}


ZERO = PriceRange(0.0, 0.0)

#: What a unit price *includes*. The distinction lived only in prose comments at the top of
#: houses/catlin/prices.toml until now, which meant no consumer could act on it: an estimate
#: could not tell a homeowner's material budget from a contractor's installed number, and
#: sales tax (material only, in MN) had nothing to apply itself to.
MATERIAL, LABOUR, INSTALLED = "material", "labour", "installed"
BASES = (MATERIAL, LABOUR, INSTALLED)


@dataclass(frozen=True)
class UnitPrice(PriceRange):
    """A unit price that knows what it includes.

    Subclasses :class:`PriceRange` rather than wrapping it so every existing consumer —
    ``.times()``, ``.plus()``, ``.fmt()``, ``.as_dict()``, ``prices.framing["2x6"].low`` —
    keeps working untouched; the basis simply rides alongside.

    ``material``/``labour`` are set only when the file declares a real split. An
    ``INSTALLED`` row without one is *merged*, and the estimate reports it as merged rather
    than inventing a percentage: a made-up split is worse than an admitted one, because it
    reads exactly like a real one.
    """

    basis: str = MATERIAL
    material: PriceRange | None = None
    labour: PriceRange | None = None

    @property
    def is_split(self) -> bool:
        return self.material is not None and self.labour is not None


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
    # Species wood (2026-08-02), keyed on material tag. Mind the mirrors: rows flagged
    # ``also_in_*`` are billed primarily in envelope_layers / floor_finishes /
    # structural_solids — price a material here OR there, not in both tables.
    wood_surfaces: Mapping[str, PriceRange] = field(default_factory=dict)
    openings: Mapping[str, PriceRange] = field(default_factory=dict)
    footing_bedding: Mapping[str, PriceRange] = field(default_factory=dict)
    pipe_runs: Mapping[str, PriceRange] = field(default_factory=dict)
    ducts: Mapping[str, PriceRange] = field(default_factory=dict)
    sleeves: Mapping[str, PriceRange] = field(default_factory=dict)
    conduit: Mapping[str, PriceRange] = field(default_factory=dict)
    # Plumbing specialties (2026-08-01). Keyed on the accessory *kind* / part name / spec
    # rather than a model number: a price list is written before the model is chosen.
    plumbing_specialties: Mapping[str, PriceRange] = field(default_factory=dict)
    install_parts: Mapping[str, PriceRange] = field(default_factory=dict)
    pipe_insulation: Mapping[str, PriceRange] = field(default_factory=dict)
    # Edge trim by the lineal foot (2026-08-02), keyed on the row category — fascia,
    # soffit, drip_flashing, edge_cladding, corner_trim, ridge_cap ...
    edge_trim: Mapping[str, PriceRange] = field(default_factory=dict)
    # Monolithic wall structure (2026-08-03), keyed on the *assembly* tag rather than the
    # material: a placed yard of SUNKEN_GARDEN_WALL and a yard of CATLIN_BASEMENT_12 are
    # both "concrete" and are not the same price. Priced by the cubic yard; the rows also
    # carry net_area_sqft, so a face-priced second plan entry can be added later — but
    # price each assembly in one table only.
    wall_structure: Mapping[str, PriceRange] = field(default_factory=dict)
    # Guards by the lineal foot of guard line (2026-08-08), keyed on the railing product
    # type. A count cannot price a railing: a 6-ft balcony guard and a 20-ft stair guard
    # are both "1".
    railings: Mapping[str, PriceRange] = field(default_factory=dict)
    # Gutters and leaders by the foot (2026-08-08), keyed on the drainage row category.
    # Mind the mirror: these runs also surface in ``structural_solids`` as a fraction of a
    # cubic yard of sheet metal — price them here, and leave `gutter`/`downspout` blank in
    # [concrete]. The drywell rows carry length 0 and bill their aggregate there instead.
    drainage: Mapping[str, PriceRange] = field(default_factory=dict)
    # Construction-rule returns by the lineal foot (2026-08-18), keyed on the row's
    # ``takeoff_category`` — "pt-sill-plate", "rim-spray-foam", "sauna-liner-return", ...
    #
    # This table was the last section of the BOM with no price join at all, which was
    # tolerable while every return was a *lap* of material some other table already bought
    # (the sauna liner turning a corner is more of the polyiso already in [envelope_layers]).
    # ``rim-spray-foam`` broke that: closed-cell foam in a rim cavity is in no assembly and
    # no other table, so it is material nobody was paying for. Mind the same mirror the
    # drainage note describes — price a return here only where it is a *separate purchase*,
    # and leave the pure laps blank rather than billing the same material twice.
    construction_returns: Mapping[str, PriceRange] = field(default_factory=dict)
    # Loose furnishings (2026-08-08), keyed on the same catalog type tag as [placeables]
    # and read against the same BOM rows. A sofa is not a construction cost, and rolling
    # one into the build number makes the build number wrong in both directions — it is
    # too high to bid against and too volatile to track. Split rather than dropped: the
    # estimate still prices and reports it, beside the total instead of inside it.
    # ``load_prices`` rejects a type priced in both tables.
    furnishings: Mapping[str, PriceRange] = field(default_factory=dict)

    # --- what the numbers above include, and what to do with them ------------------------
    #: Section -> "material" | "labour" | "installed". Always complete over ``_SECTIONS``.
    basis: Mapping[str, str] = field(default_factory=dict)
    #: False when the file declares no ``[basis]`` at all, so a reader can tell "this house
    #: says its prices are material" from "nobody has said". Never guessed at silently.
    basis_declared: bool = False
    #: The provenance sentences that used to live only in ``prices.toml``'s prose header.
    basis_notes: Mapping[str, str] = field(default_factory=dict)
    #: ``[codes]`` — a builder's own NAHB numbers, keyed "section" or "section:key" (#28).
    codes: Mapping[str, str] = field(default_factory=dict)
    adjustments: Adjustments = field(default_factory=lambda: Adjustments())

    def basis_for(self, section: str, key: str) -> str:
        """The basis a specific row is on: its own override, else its section's."""
        price = getattr(self, section, {}).get(key)
        return getattr(price, "basis", None) or self.basis.get(section, MATERIAL)


_VALUE_SHAPES = (
    '   "2x6"  = 1.10                                       # exact, section-default basis\n'
    '   "2x6"  = { low = 1.10, high = 1.40 }                 # a range, section-default basis\n'
    '   "2x10" = { low = 2.8, high = 3.4, basis = "installed" }   # a real merged quote\n'
    '   "LVL"  = { material = { low = 7, high = 9 }, labour = { low = 3, high = 5 } }'
)


def _range(section: str, key: str, raw: object, path: Path, what: str = "") -> PriceRange:
    label = f"[{section}] {key!r}{what}"
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        value = float(raw)
        if value < 0:
            raise ValueError(f"{path}: {label} is negative")
        return PriceRange(value, value)
    if isinstance(raw, dict) and set(raw) == {"low", "high"}:
        low, high = float(raw["low"]), float(raw["high"])
        if low < 0 or high < low:
            raise ValueError(f"{path}: {label} needs 0 <= low <= high")
        return PriceRange(low, high)
    raise ValueError(f"{path}: {label} must be a number or {{ low, high }} table")


def _price(section: str, key: str, raw: object, path: Path,
           default_basis: str = MATERIAL) -> UnitPrice:
    """One price-table value, in any of the four accepted shapes.

    The grammar grew rather than changed: an existing bare number or ``{low, high}`` still
    means exactly what it meant, and picks up its section's declared basis. Only the two new
    shapes — a ``basis =`` override and an explicit ``material``/``labour`` split — say
    anything the old file could not.
    """
    if isinstance(raw, dict) and ("material" in raw or "labour" in raw):
        missing = {"material", "labour"} - set(raw)
        extra = set(raw) - {"material", "labour"}
        if missing or extra:
            raise ValueError(
                f"{path}: [{section}] {key!r} is a split price and needs exactly "
                f"`material` and `labour`; accepted shapes are:\n{_VALUE_SHAPES}")
        material = _range(section, key, raw["material"], path, " material")
        labour = _range(section, key, raw["labour"], path, " labour")
        merged = material.plus(labour)
        return UnitPrice(merged.low, merged.high, INSTALLED, material, labour)
    basis = default_basis
    if isinstance(raw, dict) and "basis" in raw:
        basis = str(raw["basis"])
        if basis not in BASES:
            raise ValueError(f"{path}: [{section}] {key!r} has basis {basis!r}; "
                             f"expected one of {list(BASES)}")
        raw = {k: v for k, v in raw.items() if k != "basis"}
    if isinstance(raw, dict) and set(raw) - {"low", "high"}:
        raise ValueError(f"{path}: [{section}] {key!r} has unexpected key(s) "
                         f"{sorted(set(raw) - {'low', 'high'})}; accepted shapes are:\n"
                         f"{_VALUE_SHAPES}")
    value = _range(section, key, raw, path)
    return UnitPrice(value.low, value.high, basis)


#: Tables that are *not* price sections: they describe the file rather than price a row.
#: Split out so an unknown-section error still names real typos.
_META_SECTIONS = ("basis", "basis_notes", "waste", "contingency", "markup", "tax", "codes")


@dataclass(frozen=True)
class Adjustments:
    """The four multipliers that turn a net subtotal into a bid number.

    Deliberately four separate stages rather than one blended factor: waste is a *quantity*
    fact, contingency is an *unknowns* fact, markup is the builder's business, and tax is the
    state's. Blending them makes every one unauditable, and which of the four is included is
    the first question anyone asks about an estimate.
    """

    #: Section -> rate, plus ``"section:key"`` per-key overrides.
    waste: Mapping[str, float] = field(default_factory=dict)
    contingency: float = 0.0
    overhead: float = 0.0
    profit: float = 0.0
    #: Applied to the material portion only — which is the whole reason ``[basis]`` exists.
    material_tax_rate: float = 0.0

    def waste_rate(self, section: str, key: str) -> float:
        override = self.waste.get(f"{section}:{key}")
        return float(override if override is not None else self.waste.get(section, 0.0))


def _rate(path: Path, table: str, key: str, raw: object) -> float:
    if not isinstance(raw, (int, float)) or isinstance(raw, bool):
        raise ValueError(f"{path}: [{table}] {key!r} must be a number (a fraction, e.g. 0.10)")
    value = float(raw)
    if not 0.0 <= value < 1.0:
        raise ValueError(f"{path}: [{table}] {key!r} = {value} must be a fraction in [0, 1) — "
                         f"0.10 means 10%, not 10")
    return value


def _load_basis(data: dict[str, Any], path: Path, priced: set[str]) -> dict[str, str]:
    """Section -> declared basis, with the whole-file default when ``[basis]`` is absent.

    A ``[basis]`` table that exists but does not cover a section the file actually prices is
    a hard error. Half a declaration is worse than none: the reader assumes the sections it
    does cover are the exceptions and silently treats the rest as material.
    """
    declared = data.get("basis") or {}
    unknown = sorted(set(declared) - set(_SECTIONS))
    if unknown:
        raise ValueError(f"{path}: [basis] names unknown section(s) {unknown}")
    for section, value in declared.items():
        if value not in BASES:
            raise ValueError(f"{path}: [basis] {section} = {value!r}; expected one of "
                             f"{list(BASES)}")
    if declared:
        missing = sorted(priced - set(declared))
        if missing:
            raise ValueError(
                f"{path}: [basis] is declared but does not cover {missing}, which this file "
                f"prices. Every priced section needs a basis, or the ones you did declare "
                f"read as the exceptions and the rest are silently assumed material.")
    return {section: str(declared.get(section, MATERIAL)) for section in _SECTIONS}


def _load_adjustments(data: dict[str, Any], path: Path) -> Adjustments:
    waste: dict[str, float] = {}
    for key, raw in (data.get("waste") or {}).items():
        section = str(key).split(":", 1)[0]
        if section not in _SECTIONS:
            raise ValueError(f"{path}: [waste] {key!r} names unknown section {section!r}")
        if section in WASTE_IN_QUANTITY:
            raise ValueError(
                f"{path}: [waste] {key!r} would double-count. {section} is billed on an "
                f"ORDER quantity that already carries its waste — see "
                f"{WASTE_IN_QUANTITY[section]}. Change the factor there, or price the "
                f"section net, but never both.")
        waste[str(key)] = _rate(path, "waste", str(key), raw)
    markup = data.get("markup") or {}
    unknown = sorted(set(markup) - {"overhead", "profit"})
    if unknown:
        raise ValueError(f"{path}: [markup] has unexpected key(s) {unknown}; "
                         f"expected overhead and/or profit")
    tax = data.get("tax") or {}
    unknown = sorted(set(tax) - {"material_rate"})
    if unknown:
        raise ValueError(f"{path}: [tax] has unexpected key(s) {unknown}; expected material_rate")
    contingency = data.get("contingency") or {}
    unknown = sorted(set(contingency) - {"rate"})
    if unknown:
        raise ValueError(f"{path}: [contingency] has unexpected key(s) {unknown}; expected rate")
    return Adjustments(
        waste=waste,
        contingency=_rate(path, "contingency", "rate", contingency.get("rate", 0.0)),
        overhead=_rate(path, "markup", "overhead", markup.get("overhead", 0.0)),
        profit=_rate(path, "markup", "profit", markup.get("profit", 0.0)),
        material_tax_rate=_rate(path, "tax", "material_rate", tax.get("material_rate", 0.0)),
    )


def load_prices(house_dir: Path) -> Prices | None:
    """Read ``prices.toml`` if the house supplies one; ``None`` (not an error) if absent.

    A *malformed* file raises ``ValueError`` with the offending key — a mistyped price must
    never be silently priced at zero.
    """
    path = Path(house_dir) / PRICES_FILENAME
    if not path.exists():
        return None
    data = tomllib.loads(path.read_text())
    unknown = set(data) - set(_SECTIONS) - set(_META_SECTIONS)
    if unknown:
        raise ValueError(f"{path}: unknown section(s) {sorted(unknown)}; "
                         f"expected {list(_SECTIONS)} or {list(_META_SECTIONS)}")
    priced = {section for section in _SECTIONS if data.get(section)}
    basis = _load_basis(data, path, priced)
    sections = {
        section: {str(key): _price(section, str(key), raw, path, basis[section])
                  for key, raw in (data.get(section) or {}).items()}
        for section in _SECTIONS
    }
    notes = {str(k): str(v) for k, v in (data.get("basis_notes") or {}).items()}
    unknown_notes = sorted(set(notes) - set(_SECTIONS))
    if unknown_notes:
        raise ValueError(f"{path}: [basis_notes] names unknown section(s) {unknown_notes}")
    codes = {str(k): str(v) for k, v in (data.get("codes") or {}).items()}
    for key in codes:
        if key.split(":", 1)[0] not in _SECTIONS:
            raise ValueError(f"{path}: [codes] {key!r} names an unknown section")
    # [placeables] and [furnishings] price the same BOM rows, so a type in both would be
    # billed twice — once in the construction total and once beside it.
    both = sorted(set(sections["placeables"]) & set(sections["furnishings"]))
    if both:
        raise ValueError(f"{path}: {both} priced in both [placeables] and [furnishings]; "
                         "each catalog type belongs to exactly one (furnishings are "
                         "reported beside the construction total, not inside it)")
    return Prices(path=path, basis=basis, basis_notes=notes, codes=codes,
                  basis_declared=bool(data.get("basis")),
                  adjustments=_load_adjustments(data, path), **sections)


#: Sections whose BOM quantity is an ORDER quantity — it already carries its waste, so a
#: price-side ``[waste]`` factor on one of these double-counts. Keyed to the takeoff module
#: that owns the factor, because "you already have waste" is useless without "and it is
#: set over there". ``load_prices`` raises with this name attached.
WASTE_IN_QUANTITY = {
    "framing": "takeoff/framing.py::_order_length_ft (stock-length rounding)",
    "sheet_goods": "takeoff/framing.py + takeoff/glazing.py (`sheets_4x8` ceiling)",
    "floor_finishes": "takeoff/finishes.py::_WASTE",
    "wood_surfaces": "takeoff/wood_surfaces.py::_WASTE",
}



def waste_in_quantity(section: str) -> bool:
    """True when the BOM already bills this section on an ordered (waste-inclusive) quantity."""
    return section in WASTE_IN_QUANTITY
