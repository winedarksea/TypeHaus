"""A deck ledger bolted to a wall face — IRC R507.9 / AWC DCA6 (→ 12 §checks/structural).

``Beam.ledger_on`` names the wall. What is graded, per ledger:

- the wall exists and the ledger lies against its face (DCA6 Table 5 fn 2: no more than a
  1/2" gap, and it may not run into the wall);
- the ledger is preservative-treated and at least a 2x8 (DCA6 Table 5 fn 5, IRC R507.9.1.1);
- fasteners are authored on it (``Connector.connects`` naming the ledger), and their
  spacing is graded where a prescriptive row exists.

**On concrete or solid masonry there is no row.** IRC R507.9.1.3 tabulates lags and bolts
into a wood band joist only, and DCA6 ("Expansion and Adhesive Anchors") requires 1/2"
anchors with washers and leaves "minimum spacing and embedment length ... per the
manufacturer's recommendations". So a ledger on concrete with its anchors authored reports
UNKNOWN naming that gap; it is never graded against a number the code does not publish.
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, not_applicable, unknown
from typehaus.model.elements import Wall
from typehaus.model.enums import ConnectorKind
from typehaus.model.floors import FloorSystem
from typehaus.model.structure import Beam, Connector, FoundationWall
from typehaus.quantities import M_PER_IN
from typehaus.resolve.assembly_material import assembly_structure_material
from typehaus.resolve.framing.profiles import cross_section

_CID = "structural.deck_ledger"
#: DCA6 Table 5 footnote 2: the ledger face within 1/2" of the wall it bolts to.
MAX_GAP_IN = 0.5
#: DCA6 Table 5 footnote 5 / IRC R507.9.1.1: a deck ledger is at least a 2x8.
MIN_DEPTH_IN = 7.25
#: DCA6 Table 5 (= IRC Table R507.9.1.3(1)), 2x lumber band, 1/2" fasteners, o.c. inches by
#: joist span (ft). Wood substrate only.
_JOIST_SPANS_FT = (6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0)
LAG_SPACING_IN = (30.0, 23.0, 18.0, 15.0, 13.0, 11.0, 10.0)
THROUGH_BOLT_SPACING_IN = (36.0, 36.0, 34.0, 29.0, 24.0, 21.0, 19.0)
_FASTENER_KINDS = (ConnectorKind.ANCHOR_BOLT,)
_CAST = ("concrete", "cmu", "masonry", "block")


def _ledgers(ctx: CheckContext) -> list[Beam]:
    return [e for e in ctx.plan.all_elements() if isinstance(e, Beam) and e.ledger_on]


def _treated(ctx: CheckContext, beam: Beam) -> bool:
    refs = [assembly_structure_material(ctx.plan, beam.assembly)]
    if ":" in beam.size:
        refs.append(beam.size.split(":", 1)[1].strip())
    for ref in refs:
        material = ctx.plan.library.material(ref) if ref else None
        if material is not None and material.preservative_treated:
            return True
    return False


def _cast(ctx: CheckContext, wall: Wall) -> bool:
    ref = (assembly_structure_material(ctx.plan, wall.assembly) or "").lower()
    return isinstance(wall, FoundationWall) or any(word in ref for word in _CAST)


def _face_gap_in(ctx: CheckContext, beam: Beam, wall_tag: str) -> tuple[float, float] | None:
    """``(gap, overlap)`` in inches between the ledger's section and the wall's body.

    The gap is the WORSE end's, so a ledger skewed off the face is caught; the overlap is a
    depth (area over length), so a ledger half-buried in the pour is too.
    """
    from shapely.geometry import Point, Polygon

    from typehaus.resolve.overlay import intersection, union_all

    solid = next((s for s in ctx.model.solids if s.tag == beam.tag), None)
    wall = ctx.model.wall(wall_tag)
    if solid is None or wall is None or len(solid.outline) < 4:
        return None
    rings = [layer.polygon for layer in wall.layers if layer.polygon and len(layer.polygon) >= 3]
    if not rings:
        return None
    body = union_all([Polygon(ring) for ring in rings])
    ring = list(solid.outline)[:4]
    length = math.dist(ring[0], ring[1])
    # corners 0/3 are the start end, 1/2 the far end (resolve/envelope._resolve_beam)
    gap = max(min(Point(p).distance(body) for p in pair)
              for pair in ((ring[0], ring[3]), (ring[1], ring[2])))
    depth = intersection(Polygon(ring), body).area / length if length > 0 else 0.0
    return gap / M_PER_IN, depth / M_PER_IN


def _stations_in(ctx: CheckContext, beam: Beam, connectors: list[Connector]) -> list[float]:
    start, end = ctx.plan.by_tag(beam.start_node), ctx.plan.by_tag(beam.end_node)
    (x0, y0), (x1, y1) = start.position.xy_m, end.position.xy_m
    length = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    out = sorted(((c.position.xy_m[0] - x0) * ux + (c.position.xy_m[1] - y0) * uy)
                 for c in connectors)
    return [0.0, *out, length] if out else []


def _carried_span_ft(ctx: CheckContext, beam: Beam) -> float | None:
    """Longest joist hung on this ledger, tip to tip, in feet."""
    spans = []
    for deck in ctx.plan.all_elements():
        if not isinstance(deck, FloorSystem) or beam.tag not in (deck.joists.bearing_refs or ()):
            continue
        resolved = next((f for f in ctx.model.floors if f.tag == deck.tag), None)
        if resolved is not None:
            spans += [m.length_m / 0.3048 for m in resolved.members if m.category == "joist"]
    return max(spans) if spans else None


def _wood_limit_in(size: str, span_ft: float) -> tuple[float, str] | None:
    row, label = ((THROUGH_BOLT_SPACING_IN, "through-bolt") if "bolt" in size.lower()
                  else (LAG_SPACING_IN, "lag screw"))
    for tabulated, spacing in zip(_JOIST_SPANS_FT, row, strict=True):
        if span_ft <= tabulated + 1e-6:
            return spacing, f"the {label} row at a {tabulated:.0f}' joist span"
    return None


@check(Tier.STRUCTURAL, _CID)
def deck_ledger(ctx: CheckContext) -> list[Finding]:
    """Each ``Beam.ledger_on``: against its wall, treated, and fastened."""
    ledgers = _ledgers(ctx)
    if not ledgers:
        return [not_applicable(_CID, "no Beam in this plan names a ledger_on wall, so no "
                               "deck hangs on a ledger")]
    return [_one(ctx, beam) for beam in ledgers]


def _one(ctx: CheckContext, beam: Beam) -> Finding:
    tags = (beam.tag, beam.ledger_on)
    wall = ctx.plan.by_tag(beam.ledger_on)
    if not isinstance(wall, Wall):
        return _advisory(_CID, f"ledger {beam.tag} names {beam.ledger_on!r}, which is not a "
                         f"wall", tags, Result.FAIL, code="IRC R507.9")
    problems: list[str] = []
    measured = _face_gap_in(ctx, beam, wall.tag)
    if measured is None:
        return unknown(_CID, f"ledger {beam.tag} or wall {wall.tag} did not resolve a plan "
                       f"section, so the face cannot be measured", tags)
    gap_in, into_in = measured
    if into_in > 1.0 / 16.0:
        problems.append(f"runs {into_in:.2f}\" into {wall.tag}")
    elif gap_in > MAX_GAP_IN + 1e-6:
        problems.append(f"stands {gap_in:.2f}\" off {wall.tag}'s face, past DCA6's "
                        f"{MAX_GAP_IN:g}\"")
    if not _treated(ctx, beam):
        problems.append("is not preservative-treated (DCA6 Table 5 fn 5)")
    depth_in = cross_section(beam.size).depth_m / M_PER_IN
    if depth_in < MIN_DEPTH_IN - 1e-6:
        problems.append(f"is {depth_in:.2f}\" deep, under the 2x8 minimum (R507.9.1.1)")
    fasteners = [c for c in ctx.plan.all_elements()
                 if isinstance(c, Connector) and c.kind in _FASTENER_KINDS
                 and beam.tag in c.connects]
    if not fasteners:
        problems.append("has no anchors authored (a Connector connecting it)")
    if problems:
        return _advisory(_CID, f"ledger {beam.tag} on {wall.tag} " + "; ".join(problems),
                         tags, Result.FAIL, code="IRC R507.9",
                         fix_hint="set it against the wall face, in treated stock, and "
                                  "author its anchors")
    stations = _stations_in(ctx, beam, fasteners)
    widest_in = max(b - a for a, b in zip(stations, stations[1:], strict=False)) / M_PER_IN
    what = (f"ledger {beam.tag} ({beam.size}) sits {gap_in:.2f}\" off {wall.tag} with "
            f"{len(fasteners)} anchors, widest gap {widest_in:.1f}\"")
    if _cast(ctx, wall):
        return unknown(_CID, f"{what}. On concrete DCA6 requires 1/2\" expansion or adhesive "
                       f"anchors with washers and sets spacing and embedment by the anchor "
                       f"manufacturer's recommendations; no prescriptive row covers it",
                       tags, code="AWC DCA6 (Expansion and Adhesive Anchors)")
    span_ft = _carried_span_ft(ctx, beam)
    limit = None if span_ft is None else _wood_limit_in(fasteners[0].size, span_ft)
    if limit is None:
        return unknown(_CID, f"{what}; no DCA6 Table 5 row for the joist span it carries",
                       tags, code="IRC Table R507.9.1.3(1)")
    allowed_in, row = limit
    ok = widest_in <= allowed_in + 1e-6
    return _advisory(_CID, f"{what}, {'within' if ok else 'past'} {allowed_in:g}\" o.c. "
                     f"(DCA6 Table 5, {row})", tags, Result.PASS if ok else Result.FAIL,
                     code="IRC Table R507.9.1.3(1)",
                     fix_hint=None if ok else "add anchors to close the widest gap")
