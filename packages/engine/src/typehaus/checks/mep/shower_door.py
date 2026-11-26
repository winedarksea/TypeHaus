"""UPC 408.5 shower door opening, and the advisories around a door's swing (decision #152).

Minn. R. 1309.0010 subp. 3.D strikes IRC ch. 25-33 (so P2708.1 does not apply) and 4714.0050
adopts the 2018 UPC; 4714.0408 amends only 408.7, so 408.5 stands: shower doors open to leave
at least 22 in. unobstructed. No outward-swing sentence was found in the UPC (the IRC's),
and no clear space in front of a shower: UPC 402.5 names water closets and bidets only. So
the opening is graded (FAIL) and the front zone is a recommendation. Notes:
``docs/local-code-notes/mn-upc-shower-door-paraphrase.md``.

The opening a leaf gives at ``a`` degrees is ``leaf_width * (1 - cos a)``: its lateral gap to
the fixed edge. ``ResolvedShowerEnclosure.free_angle_degrees`` is how far it opens before it
meets a room face or a body below its head.
"""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.checks._authoring import advisory, failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.placeable_symbols._shower_door import degrees_for_passage, passage_at
from typehaus.quantities import inch

CODE_ID = "code.MN_4714_0408_shower_door"
ADVISORY_ID = "advisory.shower_door_swing"
CODE_REF = "MN Plumbing Code (ch. 4714) 408.5"
MIN_OPENING = inch(22)  # UPC 408.5
# Scan and bisection resolution; an angle within this of the need counts as reaching it.
_ANGLE_TOLERANCE_DEGREES = 0.1
_OVERLAP_M2 = 1e-6
_SHOWER_SYMBOLS = {"shower", "shower-neo-angle", "tub-shower", "swanstone-flex-3636"}


def _showers(ctx: CheckContext):
    """``(fixture, type)`` for every placed shower, tub-showers included."""
    types = {t.tag: t for t in ctx.plan.library.fixture_types}
    for fixture in ctx.plan.elements_of_kind("Fixture"):
        product = types.get(fixture.type_ref)
        if product is not None and (product.shower_assembly is not None
                                    or product.shower_enclosure is not None
                                    or product.plan_symbol in _SHOWER_SYMBOLS):
            yield fixture, product


@check(Tier.CODE, CODE_ID)
def shower_door_opening(ctx: CheckContext) -> list[Finding]:
    """UPC 408.5: the door opens to 22 in. clear before it meets anything."""
    records = {r.tag: r for r in ctx.model.shower_enclosures}
    minimum, out = MIN_OPENING.meters, []
    for fixture, product in _showers(ctx):
        spec, tags = product.shower_enclosure, (fixture.tag,)
        if spec is None:
            out.append(unknown(CODE_ID, f"{fixture.tag} ({product.tag}) names no "
                               "shower_enclosure, so its door opening is not modelled", tags,
                               CODE_REF, "author FixtureType.shower_enclosure"))
        elif spec.kind == "curtain":
            out.append(not_applicable(CODE_ID, f"{fixture.tag} has a curtain, not a door", tags,
                                      CODE_REF))
        elif spec.clear_opening.meters < minimum - 1e-9:
            out.append(failed(CODE_ID, f"{fixture.tag}: clear opening "
                              f'{spec.clear_opening.inches:.2f}" is under the '
                              f'{MIN_OPENING.inches:g}" UPC 408.5 asks', tags, CODE_REF))
        elif not spec.swings:
            out.append(passed(CODE_ID, f'{fixture.tag}: sliding door, clear opening '
                              f'{spec.clear_opening.inches:.2f}" (no swing to obstruct)', tags,
                              CODE_REF))
        else:
            out.append(_swing_finding(fixture.tag, spec, records.get(fixture.tag), minimum))
    return out or [not_applicable(CODE_ID, "no showers", (), CODE_REF)]


def _swing_finding(tag: str, spec, record, minimum: float) -> Finding:
    tags = (tag,)
    if record is None or record.entry is None or record.free_angle_degrees is None:
        return unknown(CODE_ID, f"{tag}: its entry edge {spec.entry_edge!r} resolves to no "
                       "footprint edge, so the door cannot be swept", tags, CODE_REF)
    leaf = spec.leaf_width.meters
    needed = degrees_for_passage(leaf, minimum)
    if needed is None:
        return failed(CODE_ID, f'{tag}: a {spec.leaf_width.inches:.2f}" leaf cannot open '
                      f'{MIN_OPENING.inches:g}" clear at any angle', tags, CODE_REF)
    free, limit = record.free_angle_degrees, spec.max_opening_degrees
    if needed > limit + _ANGLE_TOLERANCE_DEGREES:
        return failed(CODE_ID, f"{tag}: the door stops at {limit:g} degrees, which opens "
                      f'{passage_at(leaf, limit) / 0.0254:.1f}", under {MIN_OPENING.inches:g}"',
                      tags, CODE_REF)
    detail = (f'{spec.leaf_width.inches:.2f}" leaf needs {needed:.1f} degrees for '
              f'{MIN_OPENING.inches:g}"')
    if free + _ANGLE_TOLERANCE_DEGREES < needed:
        return failed(CODE_ID, f"{tag}: the door opens {free:.1f} degrees before it meets "
                      f"{record.blocker}; the {detail}", tags, CODE_REF,
                      "turn the entry toward open floor, or move what the leaf meets")
    return passed(CODE_ID, f"{tag}: the door opens {free:.1f} degrees clear of obstruction; "
                  f"the {detail}", tags, CODE_REF)


@check(Tier.ADVISORY, ADVISORY_ID)
def shower_door_swing(ctx: CheckContext) -> list[Finding]:
    """The swing against room doors and its own maximum; the recommended zone in front."""
    records = [r for r in ctx.model.shower_enclosures if r.entry is not None]
    doors = [(o, Polygon(o.swing_clearance)) for o in ctx.model.openings
             if len(o.swing_clearance) >= 3]
    storeys = {w.tag: w.storey for w in ctx.model.walls}
    out = []
    for r in records:
        tags, notes = (r.tag,), []
        if r.sector:
            sector = Polygon(r.sector)
            notes += [f"its swing overlaps {o.tag}'s" for o, shape in doors
                      if storeys.get(o.host_wall) == r.storey
                      and sector.intersection(shape).area > _OVERLAP_M2]
            if (r.free_angle_degrees is not None
                    and r.free_angle_degrees + _ANGLE_TOLERANCE_DEGREES < r.max_opening_degrees):
                notes.append(f"the door reaches {r.free_angle_degrees:.1f} of its "
                             f"{r.max_opening_degrees:g} degrees (meets {r.blocker})")
        if r.front_blockers:
            notes.append("the recommended zone in front of the entry holds "
                         + ", ".join(r.front_blockers))
        if notes:
            out.append(advisory(ADVISORY_ID, f"{r.tag}: " + "; ".join(notes), tags,
                                Result.ADVISORY, fix=None))
        else:
            out.append(passed(ADVISORY_ID, f"{r.tag}: swing and front zone are clear", tags))
    return out or [not_applicable(ADVISORY_ID, "no shower enclosures", ())]
