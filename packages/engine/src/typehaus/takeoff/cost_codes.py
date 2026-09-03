"""Cost codes for BOM rows — NAHB primary, CSI MasterFormat optional.

A contractor's estimating software, accounting package and schedule all key on a *code*, not
on a material name: "2x6" is not something RSMeans Online, Craftsman Cloud, Buildertrend or a
QuickBooks job-cost report can file. Nothing in this repo carried a code taxonomy of any kind
before this module, so a Type:Haus export had to be re-coded by hand on the way in.

**NAHB is primary** because this is residential: the NAHB Chart of Accounts is what
residential builders, their lenders and their accountants actually use, and Buildertrend /
CoConstruct ship it as their default cost-code set. CSI MasterFormat is carried alongside
and is nullable — it is the commercial-specification vocabulary, useful when an architect or
a commercial sub is in the loop and merely noise otherwise.

Per **decision #28** the house owns its own numbers: a `[codes]` table in ``prices.toml``
overrides anything here, keyed ``"section"`` or ``"section:key"``. Custom codes are the
residential norm — most builders have inherited a numbering scheme from their accountant —
so the built-in table is a *starting point*, never an authority.

The ``trade`` column deliberately reuses :data:`typehaus.emit.trades.TRADES`, the same
13-value vocabulary the 3D viewer's visibility toggles use (and that
``tests/test_solid_trade_parity.py`` pins against ``ui/src/state/vocabulary.ts``). A parallel
trade vocabulary invented here would drift from it within a release.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass

from typehaus.emit.trades import TRADES, solid_trade


@dataclass(frozen=True)
class CostCode:
    """One row's filing: NAHB account, optional CSI division, and a viewer trade."""

    nahb: str
    csi: str | None
    trade: str

    def as_dict(self) -> dict[str, str | None]:
        return {"nahb_code": self.nahb, "csi_code": self.csi, "trade": self.trade}


#: Per-key refinements, matched with :func:`fnmatch.fnmatchcase` against the BOM key and
#: tried before the section default. Ordered: the first pattern that matches wins, so put
#: the specific ones first.
#:
#: Kept deliberately short. A code table that tries to classify every key is a table that is
#: wrong about most of them; the section default is the honest answer for anything whose
#: key does not carry its trade on its face.
KEY_PATTERNS: tuple[tuple[str, str, CostCode], ...] = (
    # Concrete solids: the category *is* the account. Footings and flatwork are separate
    # NAHB accounts and separate subs, and lumping them loses the distinction the
    # estimator most wants. Only the refinements live here — everything else in the section
    # is derived from the category by :func:`_solid_code` below, so a `slab*` pattern that
    # merely restated the section default has been removed: it was shadowing the derivation
    # and filing composite decking as cast-in-place concrete.
    ("concrete", "footing*", CostCode("1200", "03 30 00", "concrete")),
    ("concrete", "pier*", CostCode("1200", "03 30 00", "concrete")),
    # Gutters and leaders are 07 71 00 Roof Specialties, not the 33 46 00 subdrainage the
    # trade derivation would reach for; the pattern keeps the sharper CSI division.
    ("concrete", "gutter", CostCode("2600", "07 71 00", "drainage")),
    ("concrete", "downspout", CostCode("2600", "07 71 00", "drainage")),
    # Framing profiles that are not lumber.
    ("framing", "gutter*", CostCode("2600", "07 71 00", "drainage")),
    # The Larsen/Swinburne corner box: sheet good closing a wall cavity, not glazing trim —
    # tried before the generic "*panel*" catch-all below (first-match-wins), which would
    # otherwise file it as 08 80 00 Glazing alongside window/door panel infill.
    ("framing", "* corner panel", CostCode("2100", "06 16 00", "walls")),
    # I-joist web stiffeners: a plywood rip that the framer cuts and nails with the roof,
    # not trim and not glazing. Same account as the joist it reinforces, ahead of the
    # "*panel*" catch-all for the same reason the corner box above is.
    ("framing", "* stiffener panel", CostCode("2000", "06 17 00", "framing")),
    ("framing", "*panel*", CostCode("2400", "08 80 00", "openings")),
    # Sheet goods: roof and wall sheathing bill to the same account as the framing they
    # skin, insulated sheathing to insulation.
    ("sheet_goods", "zip-r*", CostCode("2100", "07 21 00", "walls")),
    # A pocket door's frame kit is Door Hardware (08 71 00), not the 06 05 23 rough
    # carpentry the `hardware` section defaults to. Named for its trade on purpose — see
    # the allowance note below: the key prefix is the trade declaration, and a kit filed
    # under framing lands the carpenter's number in the framer's work package.
    ("hardware", "pocket-frame-*", CostCode("2400", "08 71 00", "openings")),
    # A cast-in anchor bolt is Concrete Accessories (03 15 00), set by the sub who
    # pours the wall, hours before the framer who lands a plate on it exists on site.
    # Same reasoning as the pocket-frame row above: the key prefix declares the trade,
    # and filing this under the framer's 06 05 23 would put a bolt that has to be in
    # wet concrete into a work package that starts after the concrete has cured.
    ("hardware", "ab-*", CostCode("1000", "03 15 00", "concrete")),
    # Openings: doors and windows are one NAHB account but two CSI divisions.
    ("openings", "*door*", CostCode("2400", "08 10 00", "openings")),
    ("openings", "*window*", CostCode("2400", "08 50 00", "openings")),
    # Pipe runs carry their system in the key.
    ("pipe_runs", "vent", CostCode("3100", "22 13 00", "plumbing")),
    ("pipe_runs", "drain", CostCode("3100", "22 13 00", "plumbing")),
    ("pipe_runs", "water_*", CostCode("3100", "22 11 00", "plumbing")),
    ("pipe_runs", "gas", CostCode("3300", "22 11 00", "plumbing")),
    ("pipe_runs", "radon", CostCode("3200", "23 05 00", "mechanical")),
    # Fittings ride with the pipe they join: same NAHB account, same CSI section, same work
    # package. One wildcard because the key names the part and its size, never its trade.
    ("pipe_fittings", "*", CostCode("3100", "22 13 00", "plumbing")),
    # Construction returns are one BOM section and several trades — that is the nature of a
    # "return": it is named by what it closes, not by who buys it. The section default files
    # them as rough carpentry; these four go where the trade actually is.
    ("construction_returns", "*spray-foam*", CostCode("2100", "07 21 00", "walls")),
    ("construction_returns", "*foam-return*", CostCode("2100", "07 21 00", "walls")),
    ("construction_returns", "*masonry*", CostCode("1200", "04 20 00", "concrete")),
    ("construction_returns", "resilient-channel", CostCode("4300", "09 22 00", "walls")),
    # A gasket is never rough carpentry — it is the air/weather-barrier accessory the framer
    # rolls out ahead of the plate. Matched here as well as defaulted for the
    # ``sill_gaskets`` section below, so a house that files one as a construction return
    # still lands on the right trade.
    ("construction_returns", "*gasket*", CostCode("2100", "07 27 00", "walls")),
    # Allowances. ** THE KEY PREFIX IS THE TRADE DECLARATION. ** These match on a
    # leading segment rather than a substring, and that is a correctness requirement, not a
    # style choice: the first draft used substrings and filed "waterproofing" under ROOF,
    # because "p-r-o-o-f" contains "roof", and "egress-window-wells" under PLUMBING via
    # "*well*". A trade is not a decoration — `haus tasks` builds work packages at
    # (trade x storey), so a mis-filed allowance lands the excavator's number in the
    # plumber's package. Prefixes are unambiguous and a new key declares its own trade by
    # being named for it. Ordered specific-first, as everywhere in this table.
    ("allowances", "permits-*", CostCode("1000", "01 41 00", "earth")),
    ("allowances", "site-general-conditions", CostCode("9000", "01 50 00", "earth")),
    ("allowances", "site-drain-tile-*", CostCode("2600", "33 46 00", "drainage")),
    ("allowances", "site-*", CostCode("1000", "31 20 00", "earth")),
    ("allowances", "foundation-*", CostCode("1200", "07 10 00", "concrete")),
    ("allowances", "concrete-*", CostCode("1300", "03 30 00", "concrete")),
    ("allowances", "radon-*", CostCode("1100", "31 21 00", "concrete")),
    ("allowances", "roof-*", CostCode("2500", "07 60 00", "roof")),
    ("allowances", "envelope-*", CostCode("2100", "07 20 00", "walls")),
    ("allowances", "electrical-*", CostCode("3300", "26 00 00", "electrical")),
    ("allowances", "plumbing-*", CostCode("3100", "22 00 00", "plumbing")),
    ("allowances", "hvac-*", CostCode("3200", "23 00 00", "mechanical")),
    ("allowances", "paint-*", CostCode("4400", "09 90 00", "walls")),
    ("allowances", "cabinet-*", CostCode("4200", "12 30 00", "furniture")),
    ("allowances", "finish-floor-*", CostCode("4000", "09 60 00", "floors")),
    ("allowances", "finish-transitions-*", CostCode("4000", "09 60 00", "floors")),
    ("allowances", "finish-door-*", CostCode("2400", "08 71 00", "openings")),
    ("allowances", "finish-garage-door-*", CostCode("2400", "08 36 00", "openings")),
    ("allowances", "finish-tile-*", CostCode("4000", "09 30 00", "floors")),
    ("allowances", "finish-*", CostCode("4100", "06 20 00", "walls")),
)

#: The default code for every section in ``cli.prices.ESTIMATE_PLANS``. Every section must
#: appear here; ``tests/test_cost_codes.py`` pins that, the same way ``ESTIMATE_PLANS``
#: itself is pinned against ``_SECTIONS``.
SECTION_CODES: dict[str, CostCode] = {
    "framing": CostCode("2000", "06 11 00", "framing"),
    "sheet_goods": CostCode("2000", "06 16 00", "framing"),
    "hardware": CostCode("2000", "06 05 23", "framing"),
    # 03 21 00 is CSI's "Reinforcement Bars", a division of its own beside the cast
    # concrete it sits in — which is exactly what this section is: the steel came OUT of the
    # $/cy line when it stopped being invisible.
    "reinforcement": CostCode("1310", "03 21 00", "concrete"),
    "concrete": CostCode("1300", "03 30 00", "concrete"),
    "floor_heat": CostCode("3200", "23 83 00", "mechanical"),
    "placeables": CostCode("4200", "11 30 00", "furniture"),
    "floor_finishes": CostCode("4000", "09 60 00", "floors"),
    "envelope_layers": CostCode("2100", "07 20 00", "walls"),
    "wood_surfaces": CostCode("4100", "06 20 00", "walls"),
    "openings": CostCode("2400", "08 00 00", "openings"),
    "footing_bedding": CostCode("1100", "31 23 00", "earth"),
    "pipe_runs": CostCode("3100", "22 10 00", "plumbing"),
    "pipe_fittings": CostCode("3100", "22 13 00", "plumbing"),
    "ducts": CostCode("3200", "23 31 00", "mechanical"),
    # 23 31 00 is "HVAC Ducts and Casings"; a duct fitting is part of that section, and
    # 23 07 13 is "Duct Insulation" — the air-side twin of the 22 07 00 pipe row below.
    "duct_fittings": CostCode("3200", "23 31 00", "mechanical"),
    "duct_insulation": CostCode("3200", "23 07 13", "mechanical"),
    "sleeves": CostCode("3100", "22 05 17", "plumbing"),
    "conduit": CostCode("3300", "26 05 33", "electrical"),
    # The wire in that raceway. CSI 26 05 19 is "Low-Voltage Electrical Power
    # Conductors and Cables", the section a branch circuit's NM-B belongs to; 26 31 00 is
    # "Photovoltaic Collectors"; and a data raceway is the same 26 05 33 as a power one,
    # because a raceway is a raceway — what differs is the service pulled through it.
    "conductors": CostCode("3300", "26 05 19", "electrical"),
    "solar_modules": CostCode("3300", "26 31 00", "electrical"),
    "data_raceways": CostCode("3300", "26 05 33", "electrical"),
    "plumbing_specialties": CostCode("3100", "22 40 00", "plumbing"),
    "install_parts": CostCode("3100", "22 05 00", "plumbing"),
    "pipe_insulation": CostCode("3100", "22 07 00", "plumbing"),
    # Heater cable is an ELECTRICAL buy on a plumbing run: 26 05 33 raceway/boxes, and
    # the electrical trade, not the plumber who hung the pipe it wraps.
    "freeze_protection": CostCode("3200", "26 05 33", "electrical"),
    "edge_trim": CostCode("2500", "07 62 00", "roof"),
    # Self-adhered membrane on framing tops. 07 26 00 (weather barriers) rather than
    # the roof's 07 62 00: it is applied by the framer, with the framing, and it is
    # gone under the deck sheet before the roof trade arrives.
    "member_protection": CostCode("2000", "07 26 00", "framing"),
    "wall_structure": CostCode("1200", "03 30 00", "concrete"),
    # Structural wood solids — free-standing beams and posts, which is rough
    # carpentry however they are measured. Reached only when ``_solid_code`` declines,
    # which it does not for a beam or a column; it is the honest default for a wood solid
    # in a category the trade table has not classified.
    "timber": CostCode("2000", "06 11 00", "framing"),
    "railings": CostCode("2700", "05 52 00", "stairs"),
    "drainage": CostCode("2600", "07 71 00", "drainage"),
    "furnishings": CostCode("4200", "12 50 00", "furniture"),
    # Pre-framing returns. The default is rough carpentry — the sill plate and
    # the liner laps are a framer's work; KEY_PATTERNS above re-files the insulation, the
    # masonry and the channel rows onto their own trades.
    "construction_returns": CostCode("2000", "06 11 00", "framing"),
    # Sill seal, the seal under those plates. CSI 07 27 00 is Air Barriers,
    # which is what the peel-and-stick form is; the plain foam is the same trade's material
    # on the same joint.
    "sill_gaskets": CostCode("2100", "07 27 00", "walls"),
    # Lump sums. NAHB 1000 is Land and Site Work and CSI 01 21 00 is literally
    # "Allowances", so the pair is the honest default for scope the model cannot resolve.
    # A key that lands HERE rather than on a KEY_PATTERNS prefix above is an unclassified
    # one: readable, but it will be scheduled as earthwork. Name it for its trade instead.
    "allowances": CostCode("1000", "01 21 00", "earth"),
}


#: The estimate sections that price ``structural_solids``. Named because these are the
#: sections whose *table* name and whose *content* disagree: ``[concrete]`` in a
#: ``prices.toml`` bills every resolved solid there is a $/cy for — the elm timbers, the
#: breezeway polycarbonate, the composite deck, the soakaway stone — and only some of them
#: are pours. ``[timber]`` splits the structural wood back out of it, and
#: reads the same BOM rows, so it needs the same category-versus-material reasoning.
SOLID_SECTIONS = frozenset({"concrete", "timber"})

#: Where a ``structural_solids`` row files once its solid *category* has named the trade
#: that owns it (:func:`typehaus.emit.trades.solid_trade`).
#:
#: ** THE SECTION NAME IS NOT THE TRADE. ** A ``[concrete]`` row is not necessarily concrete
#: work: ``column:ELM_TIMBER``, ``glazing:BREEZEWAY_GLAZED_WALL`` and ``soffit`` are all
#: priced there but belong to framing, openings and floors respectively — this table routes
#: each solid category to its real trade instead of inheriting ``SECTION_CODES["concrete"]``.
#:
#: Keyed by trade rather than by category so it cannot drift from that table: a new solid
#: category files itself the moment ``SOLID_CATEGORY_TRADE`` names its trade.
_SOLID_TRADE_CODES: dict[str, CostCode] = {
    "concrete": CostCode("1300", "03 30 00", "concrete"),
    "framing": CostCode("2000", "06 11 00", "framing"),        # beams, posts, timbers
    "floors": CostCode("2000", "06 15 00", "floors"),          # decking, dropped soffits
    "roof": CostCode("2500", "07 62 00", "roof"),              # fascia, flashing, clamps
    "openings": CostCode("2400", "08 80 00", "openings"),      # glazing, trim, bug screen
    "drainage": CostCode("2600", "33 46 00", "drainage"),      # tile, drywell, sump
    "plumbing": CostCode("3100", "22 10 00", "plumbing"),      # routed pipe, sleeves, valves
    "electrical": CostCode("3300", "26 05 33", "electrical"),  # raceways
    "mechanical": CostCode("3200", "23 31 00", "mechanical"),  # vent runs
    "stairs": CostCode("2700", "05 52 00", "stairs"),          # guards and handrails
}

#: The one thing a solid's *category* cannot say: whether a flat horizontal solid was cast
#: or laid. "slab" covers SL-M-DECK (9" of cast concrete), SL-SG-DECK (aluminium plank on
#: 2x8 joists) and SL-BW-DECK (composite plank on joists), and only the first is a pour.
#: Consulted only when the row's ``structure_material`` *positively* says it is not
#: concrete — a row with no assembly has said nothing, and silence is not evidence.
_NOT_A_POUR: dict[str, CostCode] = {
    "slab": CostCode("2000", "06 15 00", "floors"),  # deck boards laid on framing
    "pad": CostCode("2000", "06 15 00", "floors"),
}


def _solid_code(key: str, material: str | None) -> CostCode | None:
    """The code for one ``structural_solids`` row, or ``None`` for "it really is concrete".

    ``None`` rather than the concrete code so the caller falls through to ``KEY_PATTERNS``
    and ``SECTION_CODES``, which carry refinements this cannot know — a footing's 1200
    account against flatwork's 1300, and a house's own ``[codes]`` override.
    """
    category = key.split(":", 1)[0]
    trade = solid_trade(category)
    if trade == "concrete":
        # A category the trade table calls concrete, on a solid whose material says
        # otherwise: the deck that is planks, not mud.
        if material and material != "concrete":
            return _NOT_A_POUR.get(category)
        return None
    return _SOLID_TRADE_CODES.get(trade)


def cost_code(section: str, key: str, overrides: dict[str, str] | None = None,
              material: str | None = None) -> CostCode:
    """The code for one BOM row: house override, then key pattern, then section default.

    ``overrides`` is ``prices.toml``'s ``[codes]`` table, keyed ``"section"`` or
    ``"section:key"``. It supplies the NAHB code only — the CSI code and the trade come
    from the built-in table either way, because a builder overriding their chart of
    accounts is not thereby renaming MasterFormat.

    ``material`` is the BOM row's ``structure_material``, and only the
    :data:`SOLID_SECTIONS` read it. See :func:`_solid_code`: the section prices solids by
    CATEGORY, and a category is not a material. Callers that cannot supply it get the
    category-only answer, which is right for everything but a laid deck in a ``slab`` row.
    """
    base = None
    for plan_section, pattern, code in KEY_PATTERNS:
        if plan_section == section and fnmatch.fnmatchcase(key.lower(), pattern):
            base = code
            break
    if base is None and section in SOLID_SECTIONS:
        base = _solid_code(key, material)
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
    """Import-time guard: every trade named here must be one the viewer actually has."""
    named = {code.trade for code in SECTION_CODES.values()}
    named |= {code.trade for _, _, code in KEY_PATTERNS}
    named |= {code.trade for code in _SOLID_TRADE_CODES.values()}
    named |= {code.trade for code in _NOT_A_POUR.values()}
    unknown = sorted(named - TRADES)
    if unknown:
        raise ValueError(f"cost_codes names trades the viewer does not have: {unknown}")


_validate()
