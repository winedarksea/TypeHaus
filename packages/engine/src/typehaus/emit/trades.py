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

# The visibility trades the UI honours (``ui/src/state/vocabulary.ts::Trade``). Spelled out here
# so a typo in the table below fails a test rather than shipping a node the UI drops.
TRADES = frozenset({
    "walls", "openings", "framing", "floors", "concrete", "roof", "stairs", "furniture",
    "plumbing", "electrical", "mechanical", "earth",
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

    # Routed plumbing (``resolve/mep.py::_emit_pipe_solids``, one category per ``PipeSystem``).
    "pipe_drain": "plumbing",
    "pipe_vent": "plumbing",
    "pipe_water_hot": "plumbing",
    "pipe_water_cold": "plumbing",
    # No instances in the Catlin house yet; listed because both palettes already carry them,
    # and a gas line appearing under "concrete" is exactly the bug this table exists to fix.
    "pipe_gas": "plumbing",
    "pipe_radon": "plumbing",

    # Vent runs — bath/dryer exhaust and the radon riser (``resolve/accessories.py``).
    "vent": "mechanical",

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
    "gutter": "roof",
    "flashing": "roof",

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

    # Deliberately left on the fallback, not oversights:
    #
    # "sump"      — the pit is a pour; the pump that makes it plumbing is a Fixture, and
    #               fixtures already route by their own domain.
    # "railing"   — guards are built framing, but ``ui/src/components/Canvas2D.tsx`` gates the
    #               2D railing outlines on ``visibleTrades.concrete``. Moving the category here
    #               alone would split a railing's 2D and 3D toggles; it wants the plan gate
    #               changed in the same breath, and the "stairs" trade is the likelier home.
    # "connector" — too coarse to route. The 86 in the Catlin house are a mix of PV rail clamps
    #               (electrical), knee-brace straps and column base plates (framing), and vent
    #               clamps (mechanical). One category cannot be all three; this wants routing by
    #               *host* rather than by category, which is a larger change than a table.
}


def solid_trade(category: str | None) -> str:
    """The visibility trade a :class:`~typehaus.resolve.model.ResolvedSolid` belongs to."""
    if not category:
        return FALLBACK_TRADE
    return SOLID_CATEGORY_TRADE.get(category.strip().lower(), FALLBACK_TRADE)
