"""Which visibility trade a resolved solid belongs to.

The 3D UI groups the building by *trade* — the toggles in ``ui/src/components/ViewsPanel.tsx``
— and every other record family already routes itself: a wall's layers are "walls" and its
members are "framing" (``emit/gltf/emitter.py``), a floor's joists are "framing" while its deck
is "floors", a roof's sticks are "framing" and its shell is "roof". :class:`ResolvedSolid` was
the exception: every solid, whatever its category, was handed to "concrete" by all three
consumers (the glTF emitter, the geometry IR, and the viewer's three.js builders).

That is wrong for most of them. A standalone ``Beam`` and a ``Post`` are the same sticks of
structure as the studs and rafters they carry — an authored ridge beam already appears under
framing, because ``resolve/framing/roof.py`` re-types it as a ``FramedMember``, so the two hall
beams and the ridge beam were the same authored element kind filed under two different toggles.
A routed pipe run is plumbing; ``resolve/mep.py`` gives each run a per-system category expressly
"so the viewer and the glTF export color-code trades the way a riser diagram does", and the
colours did while the grouping did not. Roof edge trim is roof. Glazing is fenestration.

This module is that mapping, named once so the three consumers share one verdict instead of
three literals. It sits beside :mod:`typehaus.emit.finishes` for the same reason: that module
owns the shared *material-key* vocabulary keyed by the very same category strings, and both the
resolve-stage IR builder and the emitters already import from it.

``ui/src/three/solidMaterials.ts`` mirrors the table for the live viewer, whose render path is
deliberately not on the IR (→ ``WHOLE_HOUSE_GLB_PRIMARY``). ``tests/test_solid_trade_parity.py``
is the link between the two, in both directions.
"""

from __future__ import annotations

from typehaus.model.enums import DuctSystem, PipeAccessoryKind, PipeSystem

# The visibility trades the UI honours (``ui/src/state/vocabulary.ts::Trade``). Spelled out here
# so a typo in the table below fails a test rather than shipping a node the UI drops.
TRADES = frozenset({
    "walls", "openings", "framing", "floors", "concrete", "roof", "stairs", "furniture",
    "plumbing", "electrical", "mechanical", "earth", "drainage",
})

# What a solid whose category is not in the table resolves to. Named rather than implicit,
# following ``finishes.FALLBACK_KEY``: concrete is the right answer for a pour, and a category
# that lands here should be visible as "we have not classified this" rather than as a claim.
FALLBACK_TRADE = "concrete"

SOLID_CATEGORY_TRADE: dict[str, str] = {
    # Standalone structure. ``resolve/envelope.py::resolve_columns_and_beams`` turns authored
    # ``Beam``/``Post`` elements into solids so the slab consumers can draw them, but they are
    # framing: same lumber, same profiles, same load path as the members around them.
    "beam": "framing",
    "column": "framing",

    # Routed plumbing (``resolve/mep.py::_emit_run_solids``, one category per ``PipeSystem``).
    "pipe_drain": "plumbing",
    "pipe_vent": "plumbing",
    "pipe_water_hot": "plumbing",
    "pipe_water_cold": "plumbing",
    # No instances in the Catlin house yet; listed because both palettes already carry them,
    # and a gas line appearing under "concrete" is exactly the bug this table exists to fix.
    "pipe_gas": "plumbing",
    "pipe_radon": "plumbing",
    # In-line supply devices (``resolve/mep.py::_resolve_pipe_accessory``). One category per
    # ``PipeAccessoryKind`` rather than one "pipe_accessory" for the lot: a solid's category
    # is what the 3D inspector and the solids rollup *label* it with, and a family name tells
    # a reader nothing — a shutoff, a backflow preventer and a sealed penetration are three
    # different things to find in a model. ``PIPE_ACCESSORY_CATEGORIES`` below keeps the
    # family available for the consumers that do want them treated alike.
    "main_shutoff": "plumbing",
    "shutoff": "plumbing",
    "backflow_preventer": "plumbing",
    "vacuum_breaker": "plumbing",
    "water_hammer_arrestor": "plumbing",
    "ro_stub": "plumbing",
    "penetration_seal": "plumbing",
    # The cast-in block-outs (``resolve/mep.py::_emit_sleeve_solid``). Plumbing, even for the
    # dozen that carry raceways: a sleeve is a pre-pour operation graded by the plumbing
    # rough-in rules (``checks/mep/plumbing.py`` sleeve_coverage / footing_clearance), and
    # splitting the family by what eventually threads it would hide half the pour-day list
    # behind the Electrical toggle on the one walk where you want to see all of it at once.
    "pipe_sleeve": "plumbing",

    # Raceways (``resolve/mep.py::_resolve_conduit_run``), one category per side of the
    # NEC 800.133/725 power-vs-comms line. Both are the electrician's work, so both ride the
    # electrical toggle; the split exists for the colour and the inspector heading, not for
    # the grouping.
    "conduit_power": "electrical",
    "conduit_data": "electrical",

    # Vent runs — bath/dryer exhaust and the radon riser (``resolve/accessories.py``).
    "vent": "mechanical",

    # Routed air (``resolve/mep_ducts.py``, one category per ``DuctSystem``). Every one of
    # them is the HVAC contractor's work, so the split is for the colour and the inspector
    # heading, exactly as the raceway pair above is: what a reader wants to tell apart in a
    # duct box is fresh air from stale, not sheet metal from sheet metal.
    "duct_supply": "mechanical",
    "duct_return": "mechanical",
    "duct_exhaust": "mechanical",
    "duct_dryer": "mechanical",
    "duct_transfer": "mechanical",
    "duct_outdoor_air": "mechanical",

    # Fenestration: the glazing panels and the aluminium extrusions that hold them. They read
    # as openings even where the panel is set in a roof plane, because what a viewer wants to
    # hide with the roof is the shell, not the glass in it.
    "glazing": "openings",
    "glazing_trim": "openings",
    # The rainscreen base closure strip, hosted per wall — an envelope detail on the cladding
    # plane, hidden with the openings/trim rather than with the concrete.
    "bug_screen": "openings",

    # Roof edge trim (``resolve/accessories.py::_TRIM_CATEGORY``, ``resolve/roof_trim.py``).
    "fascia": "roof",
    "flashing": "roof",

    # Stormwater. A gutter is roof-edge trim by where it hangs, but what it *is* is the head
    # of a drainage run that continues down a leader, through the perimeter tile and out to
    # daylight — the same family IFC files under ``IfcDistributionSystem/STORMWATER``. Filing
    # the run's head under "roof" and its tail under "concrete" is what made drainage the
    # least legible family in the model, so the whole run rides one toggle.
    "gutter": "drainage",
    "downspout": "drainage",
    "sump": "drainage",
    # No instances yet — declared here like ``pipe_gas`` above so the first one authored is
    # routed rather than poured into concrete. Geometry arrives in later phases.
    "drain_tile": "drainage",
    "french_drain": "drainage",
    "drywell": "drainage",

    # A dropped soffit is framed and finished like the ceiling it hangs under, so it rides the
    # floors trade instead of appearing in a concrete take-off it has no business in. This was
    # the geometry IR's one pre-existing exception; the glTF emitter disagreed and sent it to
    # concrete with everything else. The table settles it.
    "soffit": "floors",

    # Below explicit for the record, though they equal the fallback: naming them documents that
    # they were considered, so the parity test's "unclassified" list stays meaningful.
    "slab": "concrete",
    "footing": "concrete",
    "pad": "concrete",
    "dowel": "concrete",          # GFRP rebar doweled into a pour
    "thermal_break": "concrete",  # XPS block in the concrete stack

    # Guards and handrails, frame and infill together. "stairs" rather than "framing": a guard
    # is the safety fitting of the circulation it protects, and six of the Catlin house's seven
    # are stair-well guards or stair handrails. The one deck guard (RL-SG-BALCONY) rides along,
    # which is the accepted cost of one toggle per guard.
    #
    # These were on the concrete fallback for a long time, with the fallback holding the 2D and
    # 3D toggles in agreement: ``ui/src/components/Canvas2D.tsx`` gated the plan's railing
    # outlines on ``visibleTrades.concrete`` *because* that is where the 3D viewer put them.
    # That gate moved to ``stairs`` in the same change as these rows — the two have to move
    # together or a railing appears in one viewer and not the other.
    "railing": "stairs",
    "railing_infill": "stairs",
    "railing_glass": "stairs",

    # Connection hardware, routed by *what kind of connection it is* rather than by the one
    # "connector" category it used to share. Structural hardware — the hangers, ties, post
    # bases, hold-downs and knee-brace straps — is the carpenter's work and rides with the
    # members it joins. A post base is anchored into a pour and is still framing hardware:
    # what makes a solid concrete is being a pour, not touching one.
    "connector": "framing",
    # The two roof/skin families, split out because they are genuinely different products and
    # a category is what the 3D inspector *labels* a solid with. A snow-retention rail and an
    # S-5!-style seam clamp both live on the standing-seam skin: the clamp is a fastener into
    # the seam, whatever it happens to be holding — a PV rail, a leader, a vent riser — so it
    # rides the roof it penetrates rather than following its payload into four trades.
    "snow_guard": "roof",
    "seam_clamp": "roof",
}


# The stormwater family, derived from the table so the two can never disagree. The IFC emitter
# groups exactly these solids into one ``IfcDistributionSystem`` with ``PredefinedType=STORMWATER``
# (``emit/ifc/mep.py``), which is what Revit and Bonsai read as a real system rather than as
# loose proxies.
DRAINAGE_CATEGORIES = frozenset(
    category for category, trade in SOLID_CATEGORY_TRADE.items() if trade == "drainage")

# The in-line supply devices, derived from the enum so the two can never disagree. The IFC
# emitter skips exactly these in its generic solid loop, because ``_emit_pipe_accessories``
# owns them and knows which ``IfcValve`` PredefinedType each one is; a device that fell
# through the generic path would export as the ``IfcFooting`` fallback.
PIPE_ACCESSORY_CATEGORIES = frozenset(kind.value for kind in PipeAccessoryKind)

# The categories a *routed run* — a pipe or a raceway — gives its one swept solid
# (``resolve/mep.py::_emit_run_solids``). Derived from the enum for pipes and named for
# raceways, whose two categories are a service split rather than an enum
# (``resolve/mep.py::_conduit_category``); ``test_mep_geometry`` asserts the reference house
# mints nothing outside this set, so the two cannot drift apart in silence.
#
# The IFC emitter skips exactly these in its generic solid loop, for the same reason it skips
# the accessories above and with a worse symptom: a run already exports as real
# ``IfcPipeSegment``s (``emit/ifc/mep.py``) or ``IfcCableCarrierSegment``s
# (``emit/ifc/electrical.py``), so emitting its solid too put a **second** copy of every run
# in the file — and, with no ``_SOLID_IFC_CLASS`` row to land on, that copy was an
# ``IfcFooting``. 68 of catlin's 239 footings were pipe. glTF and ``model.json`` are the
# other way round: there the solid *is* the run, and no second element exists.
ROUTED_RUN_CATEGORIES = (frozenset(f"pipe_{system.value}" for system in PipeSystem)
                         | frozenset(f"duct_{system.value}" for system in DuctSystem)
                         | frozenset({"conduit_power", "conduit_data"}))


def solid_trade(category: str | None) -> str:
    """The visibility trade a :class:`~typehaus.resolve.model.ResolvedSolid` belongs to."""
    if not category:
        return FALLBACK_TRADE
    return SOLID_CATEGORY_TRADE.get(category.strip().lower(), FALLBACK_TRADE)


# --- construction sequence ------------------------------------------------------------
#
# ``TRADES`` above is a *visibility* axis — which toggles the 3D viewer offers — and carries
# no ordering at all. A schedule needs one, and it is the one thing on this page that cannot
# be derived from the model: nothing in the geometry says footings precede framing. It is
# judgment, authored once, here beside the vocabulary it orders.
#
# Deliberately coarse. This is the order the trades come to site in, not a critical path:
# durations, crew sizes and calendar dates are not in the model and a fabricated duration is
# worse than an absent one (→ takeoff/tasks.py).

#: Every trade in ``TRADES``, in the order work happens. Ties are broken toward the trade
#: that is harder to redo.
CONSTRUCTION_SEQUENCE: tuple[str, ...] = (
    "earth",        # excavation, backfill, drain tile bedding
    "concrete",     # footings, walls, slabs — everything cast
    "drainage",     # perimeter drainage and the site work that has to precede backfill
    "framing",      # sticks: studs, joists, rafters, beams, posts
    "floors",       # decks and subfloor over the framing that carries them
    "roof",         # dry-in: sheathing, underlayment, roofing, edge metal
    "walls",        # sheathing, WRB, insulation, cladding — the envelope layers
    "openings",     # windows and doors, after the rough openings and before finishes
    "plumbing",     # rough-in runs while the walls are open ...
    "electrical",   # ... and the three rough-ins share that window, in trade order
    "mechanical",
    "stairs",       # stairs and guards, once the floors they land on are down
    "furniture",    # casework, appliances, fixtures set at the end
)

#: What must be substantially complete before a trade starts. A predecessor map rather than
#: only the linear order above, because the three rough-ins genuinely run in parallel and a
#: schedule that serializes them is one no builder will use.
TRADE_PREDECESSORS: dict[str, tuple[str, ...]] = {
    "earth": (),
    "concrete": ("earth",),
    "drainage": ("concrete",),
    "framing": ("concrete",),
    "floors": ("framing",),
    "roof": ("framing",),
    "walls": ("framing", "roof"),
    "openings": ("walls",),
    "plumbing": ("framing", "floors"),
    "electrical": ("framing", "floors"),
    "mechanical": ("framing", "floors"),
    "stairs": ("floors",),
    "furniture": ("walls", "openings", "plumbing", "electrical", "mechanical"),
}


def _validate_sequence() -> None:
    """Import-time guard: the sequence and the predecessor map must cover exactly TRADES,
    and no trade may depend on one that comes after it."""
    if set(CONSTRUCTION_SEQUENCE) != TRADES:
        missing = sorted(TRADES - set(CONSTRUCTION_SEQUENCE))
        extra = sorted(set(CONSTRUCTION_SEQUENCE) - TRADES)
        raise ValueError(f"CONSTRUCTION_SEQUENCE must cover TRADES exactly; "
                         f"missing {missing}, unknown {extra}")
    if set(TRADE_PREDECESSORS) != TRADES:
        raise ValueError("TRADE_PREDECESSORS must have one entry per trade")
    rank = {trade: i for i, trade in enumerate(CONSTRUCTION_SEQUENCE)}
    for trade, predecessors in TRADE_PREDECESSORS.items():
        for predecessor in predecessors:
            if rank[predecessor] >= rank[trade]:
                raise ValueError(f"{trade!r} depends on {predecessor!r}, which does not "
                                 f"precede it in CONSTRUCTION_SEQUENCE")


_validate_sequence()
