"""Cost codes for BOM rows — NAHB primary, CSI MasterFormat optional, and the trade.

A contractor's estimating software, accounting package and schedule key on a *code*, not a
material name. **NAHB is primary** because this is residential: it is what builders, lenders
and accountants use, and Buildertrend / CoConstruct ship it as the default. CSI MasterFormat
rides alongside and is nullable — the commercial-specification vocabulary, noise otherwise.

Per **decision #28** the house owns its numbers: a ``[codes]`` table in ``prices.toml``
overrides the NAHB account, keyed ``"section"`` or ``"section:key"``. The built-in table is
a starting point, never an authority.

The ``trade`` column is :data:`typehaus.emit.trades.TRADES`, the same vocabulary the 3D
viewer's toggles and ``haus tasks`` use. **Facts beat spelling**: :func:`_fact_code` reads
what the BOM row *says* (a placeable's domain, a layer's function, a member's categories, an
edge trim's kind) before any key pattern or section default is consulted.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from typehaus.emit.trade_rules import solid_trades
from typehaus.emit.trades import TRADES
from typehaus.takeoff.cost_facts import fact_trade
from typehaus.takeoff.solid_sections import SOLID_SECTIONS


@dataclass(frozen=True)
class CostCode:
    """One row's filing: NAHB account, optional CSI division, and a trade."""

    nahb: str
    csi: str | None
    trade: str

    def as_dict(self) -> dict[str, str | None]:
        return {"nahb_code": self.nahb, "csi_code": self.csi, "trade": self.trade}


#: The default account for each trade: what a row files under once a rule has named its
#: trade and nothing sharper (a key pattern, a section refinement) applies.
TRADE_CODES: dict[str, CostCode] = {
    "general": CostCode("9000", "01 50 00", "general"),
    "earth": CostCode("1000", "31 20 00", "earth"),
    "drainage": CostCode("2600", "33 46 00", "drainage"),
    "landscaping": CostCode("1100", "32 90 00", "landscaping"),
    "concrete": CostCode("1300", "03 30 00", "concrete"),
    "masonry": CostCode("1200", "04 20 00", "masonry"),
    "framing": CostCode("2000", "06 11 00", "framing"),
    "stairs": CostCode("2700", "06 43 00", "stairs"),
    "roofing": CostCode("2500", "07 41 00", "roofing"),
    "gutters": CostCode("2600", "07 71 00", "gutters"),
    "siding": CostCode("2100", "07 46 00", "siding"),
    "spray_foam": CostCode("2100", "07 21 19", "spray_foam"),
    "insulation": CostCode("2100", "07 21 00", "insulation"),
    "drywall": CostCode("4300", "09 29 00", "drywall"),
    "paint": CostCode("4400", "09 91 00", "paint"),
    "openings": CostCode("2400", "08 00 00", "openings"),
    "tile": CostCode("4000", "09 30 00", "tile"),
    "flooring": CostCode("4000", "09 60 00", "flooring"),
    "resilient": CostCode("4000", "09 65 00", "resilient"),
    "carpentry": CostCode("4100", "06 20 00", "carpentry"),
    "millwork": CostCode("4100", "06 22 00", "millwork"),
    "countertops": CostCode("4100", "12 36 00", "countertops"),
    "plumbing": CostCode("3100", "22 00 00", "plumbing"),
    "electrical": CostCode("3300", "26 00 00", "electrical"),
    "low_voltage": CostCode("3300", "27 00 00", "low_voltage"),
    "mechanical": CostCode("3200", "23 00 00", "mechanical"),
    "furniture": CostCode("4200", "12 50 00", "furniture"),
}

#: Sharper CSI sections where a (section, trade) pair has one. Consulted by the fact rules;
#: anything not listed takes :data:`TRADE_CODES`.
_SECTION_TRADE_CODES: dict[tuple[str, str], CostCode] = {
    ("envelope_layers", "roofing"): CostCode("2500", "07 41 13", "roofing"),
    ("envelope_layers", "siding"): CostCode("2100", "07 46 00", "siding"),
    ("envelope_layers", "concrete"): CostCode("1300", "07 26 00", "concrete"),
    ("envelope_layers", "framing"): CostCode("2000", "06 16 00", "framing"),
    ("sheet_goods", "drywall"): CostCode("4300", "09 29 00", "drywall"),
    ("wall_structure", "masonry"): CostCode("1200", "04 21 13", "masonry"),
    ("wall_structure", "landscaping"): CostCode("1100", "32 32 23", "landscaping"),
    ("hardware", "roofing"): CostCode("2500", "07 72 00", "roofing"),
    ("hardware", "electrical"): CostCode("3300", "26 31 00", "electrical"),
    ("hardware", "concrete"): CostCode("1000", "03 15 00", "concrete"),
    ("hardware", "siding"): CostCode("2100", "07 46 00", "siding"),
    ("hardware", "mechanical"): CostCode("3200", "23 05 29", "mechanical"),
    ("edge_trim", "roofing"): CostCode("2500", "07 62 00", "roofing"),
    ("edge_trim", "siding"): CostCode("2100", "07 62 00", "siding"),
    ("cladding_trim", "roofing"): CostCode("2500", "07 62 00", "roofing"),
    ("cladding_trim", "siding"): CostCode("2100", "07 62 00", "siding"),
    ("edge_trim", "masonry"): CostCode("1200", "07 92 00", "masonry"),
    ("install_parts", "electrical"): CostCode("3300", "26 05 33", "electrical"),
    ("install_parts", "plumbing"): CostCode("3100", "22 05 00", "plumbing"),
    ("construction_returns", "insulation"): CostCode("2100", "07 21 00", "insulation"),
    ("construction_returns", "drywall"): CostCode("4300", "09 22 00", "drywall"),
    ("framing", "gutters"): CostCode("2600", "07 71 00", "gutters"),
    ("framing", "stairs"): CostCode("2700", "06 43 00", "stairs"),
    ("floor_finishes", "tile"): CostCode("4000", "09 30 13", "tile"),
    ("floor_finishes", "concrete"): CostCode("1300", "03 35 00", "concrete"),
    ("floor_finishes", "resilient"): CostCode("4000", "09 65 00", "resilient"),
    ("placeables", "carpentry"): CostCode("4100", "12 30 00", "carpentry"),
    ("furnishings", "carpentry"): CostCode("4100", "12 30 00", "carpentry"),
    ("placeables", "low_voltage"): CostCode("3300", "27 10 00", "low_voltage"),
    ("placeables", "plumbing"): CostCode("3100", "22 40 00", "plumbing"),
    ("furnishings", "plumbing"): CostCode("3100", "22 40 00", "plumbing"),
    ("placeables", "electrical"): CostCode("3300", "26 27 26", "electrical"),
    ("furnishings", "electrical"): CostCode("3300", "26 27 26", "electrical"),
    ("placeables", "mechanical"): CostCode("3200", "23 80 00", "mechanical"),
    ("furnishings", "mechanical"): CostCode("3200", "23 80 00", "mechanical"),
    ("placeables", "furniture"): CostCode("4200", "11 30 00", "furniture"),
    ("furnishings", "furniture"): CostCode("4200", "11 30 00", "furniture"),
}


def _trade_code(section: str, trade: str) -> CostCode:
    return _SECTION_TRADE_CODES.get((section, trade)) or TRADE_CODES[trade]


_POCKET_FRAME_CODE = CostCode("2000", "08 71 00", "framing")

#: Per-key refinements, matched with :func:`fnmatch.fnmatchcase` against the BOM key and
#: tried after the fact rules and before the section default. First match wins. Kept short:
#: a table that classifies every key is wrong about most of them.
KEY_PATTERNS: tuple[tuple[str, str, CostCode], ...] = (
    # Footings and flatwork are separate NAHB accounts and often separate subs.
    ("concrete", "footing*", CostCode("1200", "03 30 00", "concrete")),
    ("concrete", "pier*", CostCode("1200", "03 30 00", "concrete")),
    # Gutters and leaders are 07 71 00 Roof Specialties, not 33 46 00 subdrainage.
    ("site", "gutter", CostCode("2600", "07 71 00", "gutters")),
    ("site", "downspout", CostCode("2600", "07 71 00", "gutters")),
    ("framing", "gutter*", CostCode("2600", "07 71 00", "gutters")),
    # The Larsen/Swinburne corner box closes a wall cavity on the cladding plane.
    ("framing", "* corner panel", CostCode("2100", "07 46 00", "siding")),
    # I-joist web stiffeners: a plywood rip the framer nails with the roof.
    ("framing", "* stiffener panel", CostCode("2000", "06 17 00", "framing")),
    ("sheet_goods", "zip-r*", CostCode("2100", "07 21 00", "insulation")),
    # A pocket door's frame kit is Door Hardware (08 71 00), set in the rough framing before
    # the board closes it in. Matched by role in ``_fact_code`` too, since a kit with a part
    # number bills under that key.
    ("hardware", "pocket-frame-*", _POCKET_FRAME_CODE),
    # A cast-in anchor bolt is set by the sub who pours the wall (03 15 00).
    ("hardware", "ab-*", CostCode("1000", "03 15 00", "concrete")),
    ("openings", "*door*", CostCode("2400", "08 10 00", "openings")),
    ("openings", "*window*", CostCode("2400", "08 50 00", "openings")),
    ("pipe_runs", "vent", CostCode("3100", "22 13 00", "plumbing")),
    ("pipe_runs", "drain", CostCode("3100", "22 13 00", "plumbing")),
    ("pipe_runs", "water_*", CostCode("3100", "22 11 00", "plumbing")),
    ("pipe_runs", "gas", CostCode("3300", "22 11 00", "plumbing")),
    ("pipe_runs", "radon", CostCode("3200", "23 05 00", "mechanical")),
    ("pipe_runs", "sump_discharge", CostCode("3100", "22 14 00", "plumbing")),
    ("pipe_fittings", "*", CostCode("3100", "22 13 00", "plumbing")),
    # A base the floor trade makes from the floor itself goes with that trade's arrival.
    ("interior_trim", "tile-base", CostCode("4000", "09 30 00", "tile")),
    ("interior_trim", "flash-cove", CostCode("4000", "09 65 00", "resilient")),
    ("interior_trim", "resilient-base", CostCode("4000", "09 65 13", "resilient")),
    # Allowances. ** THE KEY PREFIX IS THE TRADE DECLARATION. ** Leading segments, never
    # substrings: "waterproofing" contains "roof" and "egress-window-wells" contains "well".
    # A key that reaches none of these files under general conditions — readable, but it is
    # then somebody's overhead. Name it for its trade instead. Specific-first.
    ("allowances", "permits-*", CostCode("9000", "01 41 00", "general")),
    ("allowances", "site-general-conditions", CostCode("9000", "01 50 00", "general")),
    ("allowances", "site-drain-tile-*", CostCode("2600", "33 46 00", "drainage")),
    ("allowances", "site-excavation-*", CostCode("1000", "31 20 00", "earth")),
    ("allowances", "site-survey-*", CostCode("1000", "31 20 00", "earth")),
    ("allowances", "site-*", CostCode("9000", "01 50 00", "general")),
    ("allowances", "foundation-*", CostCode("1200", "07 10 00", "concrete")),
    ("allowances", "concrete-*", CostCode("1300", "03 30 00", "concrete")),
    ("allowances", "radon-*", CostCode("1100", "31 21 00", "concrete")),
    # Rough carpentry consumables the cut list cannot hold — the subfloor adhesive is the
    # first. Same code as the `sheet_goods` SECTION default: the glue and the panel are
    # one carpenter, one visit, one work package.
    ("allowances", "framing-*", CostCode("2000", "06 16 00", "framing")),
    ("allowances", "roof-*", CostCode("2500", "07 60 00", "roofing")),
    ("allowances", "envelope-air-sealing-*", CostCode("2100", "07 27 00", "insulation")),
    ("allowances", "envelope-*", CostCode("2100", "07 46 00", "siding")),
    ("allowances", "electrical-*", CostCode("3300", "26 00 00", "electrical")),
    ("allowances", "plumbing-*", CostCode("3100", "22 00 00", "plumbing")),
    ("allowances", "hvac-*", CostCode("3200", "23 00 00", "mechanical")),
    ("allowances", "paint-*", CostCode("4400", "09 90 00", "paint")),
    ("allowances", "cabinet-*", CostCode("4100", "12 30 00", "carpentry")),
    # Seasonal porch enclosure panels: window treatments, hung on the track that bills
    # through [placeables] as furniture. One article, one package.
    ("allowances", "porch-enclosure-*", CostCode("4200", "12 20 00", "furniture")),
    ("allowances", "finish-carpet-*", CostCode("4000", "09 68 00", "resilient")),
    ("allowances", "finish-floor-*", CostCode("4000", "09 60 00", "flooring")),
    ("allowances", "finish-transitions-*", CostCode("4000", "09 60 00", "flooring")),
    # Interior door hardware: the carpenter hangs the door. An exterior set goes with the unit.
    ("allowances", "finish-door-*", CostCode("2400", "08 71 00", "carpentry")),
    ("allowances", "exterior-door-*", CostCode("2400", "08 71 00", "openings")),
    ("allowances", "window-*", CostCode("2400", "08 50 00", "openings")),
    ("allowances", "finish-garage-door-*", CostCode("2400", "08 36 00", "openings")),
    ("allowances", "finish-tile-*", CostCode("4000", "09 30 00", "tile")),
    ("allowances", "finish-wall-tile-*", CostCode("4000", "09 30 00", "tile")),
    ("allowances", "finish-countertops*", CostCode("4100", "12 36 00", "countertops")),
    ("allowances", "finish-millwork-*", CostCode("4100", "06 22 00", "millwork")),
    ("allowances", "finish-*", CostCode("4100", "06 20 00", "carpentry")),
)

#: The default code for every section in ``cli.prices.ESTIMATE_PLANS``.
SECTION_CODES: dict[str, CostCode] = {
    "framing": CostCode("2000", "06 11 00", "framing"),
    "sheet_goods": CostCode("2000", "06 16 00", "framing"),
    "hardware": CostCode("2000", "06 05 23", "framing"),
    # 03 21 00 Reinforcement Bars: the steel came OUT of the $/cy line when it stopped
    # being invisible.
    "reinforcement": CostCode("1310", "03 21 00", "concrete"),
    "concrete": CostCode("1300", "03 30 00", "concrete"),
    # Electric floor-warming cable is a resistance heater on its own circuit; the tile
    # setter lays the membrane, the electrician the cable and the stat (adjudicated
    # audit:2026-09-12#floor_heat:electric, Schluter DITRA-HEAT handbook).
    "floor_heat": CostCode("3300", "23 83 13", "electrical"),
    "placeables": CostCode("4100", "12 30 00", "carpentry"),
    "floor_finishes": CostCode("4000", "09 60 00", "flooring"),
    "envelope_layers": CostCode("2100", "07 46 00", "siding"),
    "wood_surfaces": CostCode("4100", "06 20 00", "carpentry"),
    "shelving": CostCode("4100", "06 41 00", "carpentry"),
    # 12 36 00 Countertops: fabricated off site and set by the yard that cut it.
    "countertops": CostCode("4100", "12 36 00", "countertops"),
    # 06 20 00 Finish Carpentry: base and casing. A tile base and a flash cove are the floor
    # trade's work but file here with the trim they replace (→ takeoff/interior_trim.py).
    "interior_trim": CostCode("4100", "06 20 00", "carpentry"),
    # 06 43 00 Wood Stairs and Railings: the stair installer sets the treads.
    "stair_treads": CostCode("2700", "06 43 00", "stairs"),
    "openings": CostCode("2400", "08 00 00", "openings"),
    # Washed stone under a footing, tile bedded in it: placed by the excavator BEFORE the
    # pour, so it files ahead of concrete in the sequence (drainage follows concrete, and a
    # footing visit that waited on a drainage package would be a cycle). The viewer draws
    # it under drainage and earth both (→ trade_rules.RECORD_FAMILY_TRADES).
    "footing_bedding": CostCode("1000", "31 23 00", "earth"),
    "excavation": CostCode("1000", "31 23 00", "earth"),
    "pipe_runs": CostCode("3100", "22 10 00", "plumbing"),
    "pipe_fittings": CostCode("3100", "22 13 00", "plumbing"),
    "ducts": CostCode("3200", "23 31 00", "mechanical"),
    "duct_fittings": CostCode("3200", "23 31 00", "mechanical"),
    "duct_insulation": CostCode("3200", "23 07 13", "mechanical"),
    "duct_parts": CostCode("3200", "23 31 00", "mechanical"),
    "duct_supports": CostCode("3200", "23 05 29", "mechanical"),
    "duct_sealing": CostCode("3200", "23 31 00", "mechanical"),
    "sleeves": CostCode("3100", "22 05 17", "plumbing"),
    "conduit": CostCode("3300", "26 05 33", "electrical"),
    "conduit_fittings": CostCode("3300", "26 05 33", "electrical"),
    "electrical_boxes": CostCode("3300", "26 05 33", "electrical"),
    "conductors": CostCode("3300", "26 05 19", "electrical"),
    "solar_modules": CostCode("3300", "26 31 00", "electrical"),
    "data_raceways": CostCode("3300", "26 05 33", "electrical"),
    "plumbing_specialties": CostCode("3100", "22 40 00", "plumbing"),
    "install_parts": CostCode("3100", "22 05 00", "plumbing"),
    "pipe_insulation": CostCode("3100", "22 07 00", "plumbing"),
    # Heater cable is an ELECTRICAL buy on a plumbing run.
    "freeze_protection": CostCode("3200", "26 05 33", "electrical"),
    "edge_trim": CostCode("2500", "07 62 00", "roofing"),
    "cladding_trim": CostCode("2100", "07 62 00", "siding"),
    "bug_screens": CostCode("2100", "07 62 00", "siding"),
    # Self-adhered membrane on framing tops: applied by the framer, with the framing.
    "member_protection": CostCode("2000", "07 26 00", "framing"),
    # Fireblock penetration seal: the framer's, at the framing inspection.
    "fireblock_sealant": CostCode("2000", "07 84 00", "framing"),
    "drywall_trims": CostCode("4300", "09 29 00", "drywall"),
    "trim_paint": CostCode("4400", "09 91 00", "paint"),
    "wall_structure": CostCode("1200", "03 30 00", "concrete"),
    # Structural wood solids, reached only when ``_solid_code`` declines.
    "timber": CostCode("2000", "06 11 00", "framing"),
    # Reached only when ``_solid_code`` declines, i.e. the row's trade is concrete (an XPS
    # frost wing laid in the foundation sequence).
    "site": CostCode("1300", "03 30 00", "concrete"),
    "solids": CostCode("1300", "03 30 00", "concrete"),
    # Rolled steel members by the foot of their section (``takeoff/steel.py``). MasterFormat
    # 05 12 00 is structural steel framing; the trade is ``framing`` rather than a steel
    # erector's, because on this scale the piece is set by whoever is already there — the
    # mason laying the course it lands in.
    "steel_members": CostCode("2000", "05 12 00", "framing"),
    "railings": CostCode("2700", "05 52 00", "stairs"),
    "drainage": CostCode("2600", "07 71 00", "drainage"),
    # Cove/LED channel, tape, caps and connectors: the Class 2 side of a driver the
    # electrician wires, so low voltage even where a joiner routs the fascia it sits in.
    "light_run_materials": CostCode("3300", "26 51 00", "low_voltage"),
    "furnishings": CostCode("4200", "12 50 00", "furniture"),
    # Pre-framing returns default to rough carpentry (the sill plate); the fact rules
    # re-file the foam, masonry and channel rows.
    "construction_returns": CostCode("2000", "06 11 00", "framing"),
    # Sill seal is rolled out by the framer ahead of the plate. 07 27 00 Air Barriers.
    "sill_gaskets": CostCode("2000", "07 27 00", "framing"),
    # Lump sums: 01 21 00 is literally "Allowances". An unnamed one is overhead.
    "allowances": CostCode("9000", "01 21 00", "general"),
}



#: Where a ``structural_solids`` row files once its category (and material) name a trade.
#: Keyed by trade so a new solid category files itself the moment ``SOLID_CATEGORY_TRADE``
#: names its trade. The concrete row is absent on purpose: a pour falls through to
#: ``KEY_PATTERNS`` (footing vs flatwork) and ``SECTION_CODES``.
_SOLID_TRADE_CODES: dict[str, CostCode] = {
    "framing": CostCode("2000", "06 11 00", "framing"),        # beams, posts, timbers, decks
    "roofing": CostCode("2500", "07 62 00", "roofing"),        # flashing, clamps, ridge
    "siding": CostCode("2100", "07 62 00", "siding"),          # fascia, corners, screens
    "openings": CostCode("2400", "08 80 00", "openings"),      # glazing and its trim
    "drainage": CostCode("2600", "33 46 00", "drainage"),      # tile, drywell, sump
    "gutters": CostCode("2600", "07 71 00", "gutters"),        # gutter and leader solids
    "plumbing": CostCode("3100", "22 10 00", "plumbing"),      # routed pipe, sleeves, valves
    "electrical": CostCode("3300", "26 05 33", "electrical"),  # raceways
    "mechanical": CostCode("3200", "23 31 00", "mechanical"),  # vent runs
    "stairs": CostCode("2700", "05 52 00", "stairs"),          # guards and handrails
    "drywall": CostCode("4300", "09 29 00", "drywall"),        # dropped soffits, ceilings
    "insulation": CostCode("2100", "07 21 00", "insulation"),  # rigid board on framing
    "landscaping": CostCode("1100", "32 90 00", "landscaping"),  # the putting green
    "masonry": CostCode("1200", "07 92 00", "masonry"),        # a wythe's sealant joints
    "earth": CostCode("1000", "31 20 00", "earth"),            # terrace fill, slab base
    "countertops": CostCode("4100", "12 36 00", "countertops"),  # a slab's Corian top
    "carpentry": CostCode("4100", "06 20 00", "carpentry"),    # a slab's finish layer
}


def _solid_code(key: str, material: str | None) -> CostCode | None:
    """The code for one ``structural_solids`` row, or ``None`` for "it really is concrete"
    so the caller falls through to the footing/flatwork refinements."""
    category = key.split(":", 1)[0]
    trade = solid_trades(category, material)[0]
    if trade == "concrete":
        return None
    return _SOLID_TRADE_CODES.get(trade) or TRADE_CODES[trade]


# --- fact rules (→ takeoff/cost_facts.py) ----------------------------------------------


def _fact_code(section: str, row: Mapping[str, Any]) -> CostCode | None:
    """A code read from the row's own facts, or ``None`` to fall through."""
    if section == "hardware" and row.get("scope") == "door hardware (authored)":
        # The door's own installer: exterior with the unit, interior with the carpenter.
        return CostCode("2400", "08 71 00", "openings" if row.get("exterior") else "carpentry")
    if section == "hardware" and row.get("role") == "pocket_door_frame_kit":
        return _POCKET_FRAME_CODE
    trade = fact_trade(section, row)
    return _trade_code(section, trade) if trade is not None else None


def cost_code(section: str, key: str, overrides: dict[str, str] | None = None,
              material: str | None = None, *, row: Mapping[str, Any] | None = None
              ) -> CostCode:
    """The code for one BOM row: facts, then a material that positively says what it is,
    then key pattern, then solid category, then the section default, then the house's NAHB
    override.

    ** THE MATERIAL MOVED AHEAD OF THE KEY PATTERN ON 2026-09-15. ** ``KEY_PATTERNS``
    refines a CATEGORY — footing against flatwork against pier, which are separate NAHB
    accounts and often separate subs — and a category is not a material. While every footing
    was concrete the distinction never showed; a crushed-stone footing under 2024 IRC R403.5
    is one, and ``"footing*"`` was classifying it as a pour before anything got to ask what
    it was made of. ``_solid_code`` returns ``None`` for "it really is concrete", so a
    concrete footing still falls straight through to the pattern that has always claimed it
    and no existing row moves.

    ``overrides`` is ``prices.toml``'s ``[codes]`` table. It supplies the NAHB code only —
    the CSI code and the trade come from the built-in rules either way, because a builder
    overriding their chart of accounts is not thereby renaming MasterFormat.

    ``material`` is the BOM row's ``structure_material``; only :data:`SOLID_SECTIONS` read
    it. ``row`` is the raw BOM row, read by :func:`_fact_code`; callers without one get the
    key-and-section answer.
    """
    base = _fact_code(section, row) if row is not None else None
    if base is None and section in SOLID_SECTIONS:
        base = _solid_code(key, material)
    if base is None:
        for plan_section, pattern, code in KEY_PATTERNS:
            if plan_section == section and fnmatch.fnmatchcase(key.lower(), pattern):
                base = code
                break
    if base is None:
        base = SECTION_CODES.get(section)
    if base is None:
        raise KeyError(f"no cost code for section {section!r}; add it to SECTION_CODES")
    if overrides:
        custom = overrides.get(f"{section}:{key}") or overrides.get(section)
        if custom is not None:
            return CostCode(custom, base.csi, base.trade)
    return base


def _validate() -> None:
    """Import-time guard: every trade named here must exist, and every trade must have an
    account."""
    named = {code.trade for code in SECTION_CODES.values()}
    named |= {code.trade for _, _, code in KEY_PATTERNS}
    named |= {code.trade for code in _SOLID_TRADE_CODES.values()}
    named |= {code.trade for code in _SECTION_TRADE_CODES.values()}
    unknown = sorted(named - TRADES)
    if unknown:
        raise ValueError(f"cost_codes names trades that do not exist: {unknown}")
    if set(TRADE_CODES) != TRADES:
        raise ValueError("TRADE_CODES must have one entry per trade")
    for (_section, trade), code in _SECTION_TRADE_CODES.items():
        if code.trade != trade:
            raise ValueError(f"_SECTION_TRADE_CODES[{_section}, {trade}] files as {code.trade}")


_validate()
