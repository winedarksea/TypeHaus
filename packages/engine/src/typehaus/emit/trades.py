"""The trade vocabulary: one set of names the viewer toggles, the BOM and the schedule share.

A *trade* is a plausible separate bid on an owner-GC residential build. The 3D viewer
groups the building by trade (``ui/src/components/views/DisciplinesGrid.tsx``), the BOM
files every row on one (``takeoff/cost_codes.py``), and ``takeoff/tasks.py`` builds work
packages at (trade × storey), ordered by :data:`CONSTRUCTION_SEQUENCE`. Nothing here is
derived from geometry: it is judgment, authored once, beside the tables that order it.

Trades are partitioned into *groups* — the viewer's toggles. A "Walls" group keeps toggling
insulation, drywall, siding and paint as one, with a chip per trade inside. Regrouping is one
table edit, :data:`TRADE_GROUPS`.

``ui/src/generated/vocabulary.json`` carries every table below (``emit/vocabulary_manifest``)
and ``tests/test_trade_vocabulary.py`` pins the invariants. Per-category and per-row
classification rules live in :mod:`typehaus.emit.trade_rules`.
"""

from __future__ import annotations

from typehaus.model.enums import DuctSystem, PipeAccessoryKind, PipeSystem

#: ``(group id, group label, trades)`` in viewer order. The tuples partition :data:`TRADES`.
TRADE_GROUPS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("site", "Site", ("general", "earth", "drainage", "landscaping")),
    ("concrete_masonry", "Concrete & masonry", ("concrete", "masonry")),
    ("structure", "Framing", ("framing", "stairs")),
    ("roof", "Roof", ("roofing",)),
    ("walls", "Walls", ("siding", "insulation", "drywall", "paint")),
    ("openings", "Openings", ("openings",)),
    ("finishes", "Finishes", ("tile", "flooring", "millwork")),
    ("plumbing", "Plumbing", ("plumbing",)),
    ("electrical", "Electrical", ("electrical",)),
    ("mechanical", "Mechanical", ("mechanical",)),
    ("furniture", "Furniture", ("furniture",)),
)

#: trade -> group id.
TRADE_GROUP: dict[str, str] = {
    trade: group_id for group_id, _label, trades in TRADE_GROUPS for trade in trades}

#: What a chip or an estimate heading prints. Scope notes are in ``plans/`` (the trade
#: audit), not here.
TRADE_LABELS: dict[str, str] = {
    "general": "General conditions",   # permits, insurance, dumpsters, scaffolding
    "earth": "Earthwork",              # excavation, backfill, grading, aggregate base
    "drainage": "Drainage",            # tile, drywell, sump, gutters, footing bedding
    "landscaping": "Landscaping",      # sod, rootzone, geotextile, SRW block, final grade
    "concrete": "Concrete",            # everything cast, reinforcement, cast-in anchors
    "masonry": "Masonry",              # brick veneer, fireplace wythe, CMU
    "framing": "Framing",              # sticks, sheathing, structural hardware, laid decks
    "stairs": "Stairs & guards",       # stringers, treads, newels, guards, handrails
    "roofing": "Roofing",              # standing seam, underlayment, drip, snow retention
    "siding": "Siding & trim",         # cladding, WRB, furring, corners, fascia, eave soffit
    "insulation": "Insulation",        # foam, batts, blown, rim foam, air sealing
    "drywall": "Drywall",              # gwb, resilient channel, dropped soffits, ceilings
    "paint": "Paint",                  # latex, accent, foundation coating
    "openings": "Windows & doors",     # windows, doors, glazing, door hardware
    "tile": "Tile",                    # floor/wall tile, uncoupling membrane, backer
    "flooring": "Flooring",            # carpet, LVP, oak, rubber, sheet vinyl, sealed slab
    "millwork": "Millwork & casework", # casework, built-ins, tops, paneling, interior trim
    "plumbing": "Plumbing",            # pipe, fittings, sleeves, fixtures, water heater
    "electrical": "Electrical",        # devices, conduit, conductors, PV, inverter, battery
    "mechanical": "Mechanical",        # ducts, registers, ERV, heat pumps, floor heat
    "furniture": "Furniture & appliances",  # loose furniture, appliances, window treatments
}

#: Every trade. Spelled by the groups so a trade without a toggle cannot exist.
TRADES = frozenset(TRADE_GROUP)

#: What an unclassified solid resolves to. Named rather than implicit: concrete is right for
#: a pour, and a category landing here reads as "not classified", not as a claim.
FALLBACK_TRADE = "concrete"

#: Solid category -> trade, for every ``ResolvedSolid.category`` the resolver mints. Material
#: overrides (a cast column, a laid deck) are :func:`typehaus.emit.trade_rules.solid_trades`.
SOLID_CATEGORY_TRADE: dict[str, str] = {
    # Standalone structure (``resolve/envelope.py::resolve_columns_and_beams``): same lumber
    # as the studs around it. A concrete pier re-files by material.
    "beam": "framing",
    "column": "framing",
    # Routed plumbing, one category per ``PipeSystem`` (``resolve/mep.py``).
    "pipe_drain": "plumbing", "pipe_vent": "plumbing",
    "pipe_water_hot": "plumbing", "pipe_water_cold": "plumbing",
    "pipe_gas": "plumbing", "pipe_radon": "plumbing", "pipe_sump_discharge": "plumbing",
    # In-line supply devices, one category per ``PipeAccessoryKind`` so the inspector can
    # label a shutoff as a shutoff.
    "main_shutoff": "plumbing", "shutoff": "plumbing", "backflow_preventer": "plumbing",
    "vacuum_breaker": "plumbing", "water_hammer_arrestor": "plumbing",
    "ro_stub": "plumbing", "penetration_seal": "plumbing",
    # Cast-in block-outs: a pre-pour operation graded by the plumbing rough-in rules, kept
    # on one toggle so the pour-day list is visible at once.
    "pipe_sleeve": "plumbing",
    # Raceways, split by the NEC 800.133/725 power-vs-comms line for colour, not trade.
    "conduit_power": "electrical", "conduit_data": "electrical",
    # Vent runs and routed air, one category per ``DuctSystem`` for colour.
    "vent": "mechanical",
    "duct_supply": "mechanical", "duct_return": "mechanical", "duct_exhaust": "mechanical",
    "duct_dryer": "mechanical", "duct_transfer": "mechanical",
    "duct_outdoor_air": "mechanical",
    # Fenestration: the glazing and the extrusions holding it, even in a roof plane.
    "glazing": "openings", "glazing_trim": "openings",
    # Roof edge trim (``resolve/roof_trim.py``, ``resolve/accessories.py``). ``flashing``
    # collapses drip and counterflashing; the BOM's ``edge_trim`` rows keep the real kind
    # and split siding from roofing there.
    "flashing": "roofing",
    "ridge_cap": "roofing",
    # Fastened INTO the standing-seam skin, whatever the clamp holds.
    "snow_guard": "roofing", "seam_clamp": "roofing", "panel_strap": "roofing",
    # The siding contractor's trim: fascia, the vented eave soffit panel, wall corner
    # closures, the aluminium cap over an exposed beam, the rainscreen base strip and
    # breezeway slat infill. ``beam_cap`` split off ``flashing`` so the sunken-garden caps
    # stop showing under Roof; ``takeoff/cost_codes._SIDING_EDGE_TRIM`` already billed it here.
    "fascia": "siding", "eave_soffit": "siding", "wall_corner": "siding",
    "beam_cap": "siding", "bug_screen": "siding", "screen_slat": "siding",
    "movement_joint": "masonry",  # a brick wythe's sealant end joint
    # Stormwater: one run from the gutter to daylight, one toggle. The IFC emitter groups
    # exactly these into ``IfcDistributionSystem/STORMWATER``.
    "gutter": "drainage", "downspout": "drainage", "sump": "drainage",
    "drain_tile": "drainage", "french_drain": "drainage", "drywell": "drainage",
    "rain_garden_media": "drainage", "rain_garden_stone": "drainage",
    "leader_extension": "drainage", "area_drain": "drainage", "area_drain_riser": "drainage",
    # Illustrative planting and the espalier frame (resolve/landscape.py): derived, unpriced.
    "plant": "landscaping", "trellis": "landscaping",
    # A dropped soffit box and a room's ceiling plane are the drywaller's overhead surfaces.
    "soffit": "drywall", "ceiling": "drywall",
    # Pours, and what is cast into them. Equal to the fallback; named so the parity test's
    # "unclassified" list stays meaningful.
    "slab": "concrete", "footing": "concrete", "pad": "concrete",
    "dowel": "concrete", "thermal_break": "concrete",
    # Guards and handrails, frame and infill. ``Canvas2D.tsx`` gates the plan's railing
    # outlines on the same trade.
    "railing": "stairs", "railing_infill": "stairs", "railing_glass": "stairs",
    # Structural hardware rides with the members it joins.
    "connector": "framing",
    # Both carved-off connector families stay FRAMING here, deliberately. This table decides
    # the viewer's CONTAINER and nothing else; who is *quoted* a cast-in anchor is decided by
    # its cost code (``takeoff/cost_codes.py``), which is where the concrete sub's scope
    # actually lives. Flipping this to "concrete" would move only the container — and would
    # BREAK the Connectors toggle, whose facet machinery is keyed to framing.
    "connector_embedded": "framing",
    "connector_hanger": "framing",
}


#: Stormwater, derived from the table so the two can never disagree (``emit/ifc/mep.py``).
DRAINAGE_CATEGORIES = frozenset(
    category for category, trade in SOLID_CATEGORY_TRADE.items() if trade == "drainage")

#: In-line supply devices, derived from the enum. The IFC emitter skips these in its generic
#: solid loop; ``_emit_pipe_accessories`` owns them.
PIPE_ACCESSORY_CATEGORIES = frozenset(kind.value for kind in PipeAccessoryKind)

#: The one swept solid a routed run gives (``resolve/mep.py::_emit_run_solids``). The IFC
#: emitter skips these too: a run already exports as real segments, and a second copy would
#: land on the ``IfcFooting`` fallback. glTF and ``model.json`` are the other way round.
ROUTED_RUN_CATEGORIES = (frozenset(f"pipe_{system.value}" for system in PipeSystem)
                         | frozenset(f"duct_{system.value}" for system in DuctSystem)
                         | frozenset({"conduit_power", "conduit_data"}))


def solid_trade(category: str | None) -> str:
    """The trade a solid's *category* names, before any material override."""
    if not category:
        return FALLBACK_TRADE
    return SOLID_CATEGORY_TRADE.get(category.strip().lower(), FALLBACK_TRADE)


# --- construction sequence ------------------------------------------------------------
#
# Deliberately coarse: the order trades come to site in, not a critical path. Durations,
# crew sizes and dates are not in the model (→ takeoff/tasks.py).

#: Every trade, in the order work happens. Ties break toward the trade harder to redo.
CONSTRUCTION_SEQUENCE: tuple[str, ...] = (
    "general", "earth", "concrete", "drainage", "framing", "masonry", "roofing",
    "openings", "siding", "plumbing", "electrical", "mechanical", "insulation", "drywall",
    "paint", "millwork", "tile", "flooring", "stairs", "furniture", "landscaping",
)

#: What must be substantially complete before a trade starts. A map rather than the linear
#: order alone: the three rough-ins genuinely run in parallel. House-specific order (catlin's
#: exterior foam before siding) is a ``depends_on`` in ``tasks.toml``, not a rule here.
TRADE_PREDECESSORS: dict[str, tuple[str, ...]] = {
    "general": (),
    "earth": ("general",),
    "concrete": ("earth",),
    "drainage": ("concrete",),
    "framing": ("concrete",),
    "masonry": ("framing",),
    "roofing": ("framing",),
    "openings": ("framing",),
    "siding": ("roofing", "openings"),
    "plumbing": ("framing", "roofing"),
    "electrical": ("framing", "roofing"),
    "mechanical": ("framing", "roofing"),
    "insulation": ("plumbing", "electrical", "mechanical"),
    "drywall": ("insulation",),
    "paint": ("drywall",),
    "millwork": ("paint",),
    "tile": ("drywall",),
    "flooring": ("paint",),
    "stairs": ("drywall",),
    "furniture": ("paint", "flooring", "millwork", "plumbing", "electrical", "mechanical"),
    "landscaping": ("drainage", "siding"),
}


def sequence_rank(trade: str) -> int:
    """Position in :data:`CONSTRUCTION_SEQUENCE`; unknown trades sort last."""
    return _RANK.get(trade, len(CONSTRUCTION_SEQUENCE))


_RANK = {trade: i for i, trade in enumerate(CONSTRUCTION_SEQUENCE)}


def _validate() -> None:
    """Import-time guard: groups, sequence and predecessors cover exactly TRADES; labels
    exist; no trade depends on one after it."""
    if len(TRADE_GROUP) != sum(len(trades) for _g, _l, trades in TRADE_GROUPS):
        raise ValueError("TRADE_GROUPS lists a trade twice")
    if set(TRADE_LABELS) != TRADES:
        raise ValueError(f"TRADE_LABELS must cover TRADES exactly: "
                         f"{sorted(set(TRADE_LABELS) ^ TRADES)}")
    if set(SOLID_CATEGORY_TRADE.values()) - TRADES or FALLBACK_TRADE not in TRADES:
        raise ValueError("SOLID_CATEGORY_TRADE names a trade that does not exist")
    if set(CONSTRUCTION_SEQUENCE) != TRADES or len(set(CONSTRUCTION_SEQUENCE)) != len(
            CONSTRUCTION_SEQUENCE):
        raise ValueError("CONSTRUCTION_SEQUENCE must list every trade exactly once")
    if set(TRADE_PREDECESSORS) != TRADES:
        raise ValueError("TRADE_PREDECESSORS must have one entry per trade")
    for trade, predecessors in TRADE_PREDECESSORS.items():
        for predecessor in predecessors:
            if _RANK[predecessor] >= _RANK[trade]:
                raise ValueError(f"{trade!r} depends on {predecessor!r}, which does not "
                                 "precede it in CONSTRUCTION_SEQUENCE")


_validate()
