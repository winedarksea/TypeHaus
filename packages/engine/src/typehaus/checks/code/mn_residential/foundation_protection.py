"""R403.1.6 sill anchorage, R405.1 foundation drainage, R406.1 dampproofing.

Three rules a plan reviewer reads off the foundation sheet and nothing in this engine
graded, even though the house models all three conditions: the sill-plate anchor schedule
(a takeoff derivation), the drain tile in every footing bedding, and the damp-proof
membrane in the basement wall assembly. They live in one module because they are one
drawing's worth of review — "how is the wood held down, and how does water get away from
the concrete" — and because they share the same applicability question: which foundation
walls actually retain earth against a space people use.

The anchorage rule grades the *derivation rule*, not a count of authored bolts. Nothing in
this model authors an anchor: ``takeoff/anchors.py`` develops MASA mudsill anchors along
every resolved sill-plate construction return at a configured pitch. That configuration is
the thing that can be wrong against R403.1.6, and it is what prints on the schedule.
"""

from __future__ import annotations

from typehaus.checks.soil import site_soil_class
from typehaus.checks.code.mn_residential._common import (
    _fail,
    _pass,
    _storey_is_below_grade,
    _unknown,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.assembly import Layer
from typehaus.model.enums import ControlLayer, LayerFunction
from typehaus.model.structure import Footing, FootingBedding, FoundationWall
from typehaus.quantities import ft

# R403.1.6: 1/2" bolts at 6 ft o.c. maximum, 7" embedment, within 12" of each end of a plate
# piece, and never fewer than two bolts per piece. "Approved anchors or anchor straps" are an
# explicit alternative to the cast bolt, which is what a MASA is.
_MAX_ANCHOR_PITCH_FT = 6.0
_MIN_ANCHORS_PER_PIECE = 2

# R405.1's exception: no drainage system is required on Group I well-drained soils. Group I
# is the 30 psf/ft equivalent-fluid column of IRC Table R405.1 — the clean gravels and sands
# — so the set is read off the shared copy of that table rather than restated here.
# Restating it is how two rules end up disagreeing about what is under the same house.
def _group_one_soils() -> frozenset:
    from typehaus.checks.structural._r404_table import SOIL_LATERAL_PSF_PER_FT

    return frozenset(name for name, psf in SOIL_LATERAL_PSF_PER_FT.items() if psf == 30)


# R406.1 dampproofs "from the top of the footing to the finished grade". A wall retaining
# less than this is a curb, not a below-grade enclosure, and the same 2 ft margin the
# storey-classification helper uses keeps a slab-on-grade stem out of the rule.
_MIN_RETAINED_FILL = ft(2)
# How far past a foundation wall's own face to probe for a room on its inboard side.
_WALL_SIDE_PROBE_M = 0.15


def _retaining_walls(ctx: CheckContext) -> list[FoundationWall]:
    """Foundation walls that retain earth *and enclose interior space below grade*.

    Both rules are scoped by their own text to walls that "retain earth and enclose
    habitable or usable spaces located below grade" (R405.1) / "enclose interior spaces and
    floors below grade" (R406.1). Retaining fill is therefore only half the test, and the
    half that over-reaches on its own: this house's sunken-garden walls, its yard retaining
    blocks and its garage ICF stem all hold back soil, and not one of them has a below-grade
    room behind it. Screening on fill alone reported four FAILs against walls neither
    section is addressed to.

    So the second half is geometric: some room on a storey classified below grade has to
    stand against the wall's inboard face. ``unbalanced_fill`` is the authored answer for
    the first half where it exists; otherwise the wall's own height below grade stands in,
    exactly as the unbalanced-fill check derives it.
    """
    from shapely.geometry import Point, Polygon

    grade = ctx.plan.project.site.grade
    if grade is None:
        return []
    below_storeys = {s.tag for s in ctx.plan.storeys
                     if _storey_is_below_grade(ctx, s) is True}
    rooms = [(room, Polygon(room.clear_face)) for room in ctx.model.rooms
             if room.storey in below_storeys and len(room.clear_face) >= 3]
    out = []
    for wall in ctx.plan.all_elements():
        if not isinstance(wall, FoundationWall):
            continue
        if wall.unbalanced_fill is not None:
            retained = wall.unbalanced_fill.meters
        elif wall.top_elevation is not None and wall.bottom_elevation is not None:
            retained = max(0.0, min(grade.meters, wall.top_elevation.meters)
                           - wall.bottom_elevation.meters)
        else:
            continue
        if retained < _MIN_RETAINED_FILL.meters:
            continue
        resolved = ctx.model.wall(wall.tag)
        if resolved is None:
            continue
        (sx, sy), (ex, ey) = resolved.axis
        run = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
        if run <= 1e-9:
            continue
        nx, ny = -(ey - sy) / run, (ex - sx) / run
        reach = resolved.thickness_m / 2.0 + _WALL_SIDE_PROBE_M
        encloses = False
        for t in (0.25, 0.5, 0.75):
            mx, my = sx + (ex - sx) * t, sy + (ey - sy) * t
            for sign in (1.0, -1.0):
                probe = Point(mx + nx * reach * sign, my + ny * reach * sign)
                if any(poly.covers(probe) for _room, poly in rooms):
                    encloses = True
                    break
            if encloses:
                break
        if encloses:
            out.append(wall)
    return out


@check(Tier.CODE, "code.R403_1_6_foundation_anchorage")
def foundation_anchorage(ctx: CheckContext) -> list[Finding]:
    """R403.1.6 — the sill plate is held to the concrete at 6 ft o.c. or tighter.

    Two things can be wrong and they fail differently. The *rule* can exceed the code
    maximum, which is a schedule error a reviewer catches on the sheet; or the model can
    resolve no sill-plate returns at all, in which case the schedule is empty and the rule
    has nothing to grade — UNKNOWN, not a pass, because "no anchors were derived" is not
    "no anchors are needed".
    """
    from typehaus.takeoff.hardware_config import HardwareTakeoffConfig

    cid, code = "code.R403_1_6_foundation_anchorage", "R403.1.6"
    rules = HardwareTakeoffConfig().sill_plate_anchors
    category = HardwareTakeoffConfig().sill_plate_takeoff_category
    returns = [r for r in ctx.model.construction_returns
               if r.takeoff_category == category]
    out: list[Finding] = []
    if rules.mudsill_anchor_pitch_ft > _MAX_ANCHOR_PITCH_FT + 1e-9:
        out.append(_fail(cid, f"the sill-anchor schedule spaces anchors at "
                              f"{rules.mudsill_anchor_pitch_ft:g} ft o.c.; R403.1.6 allows "
                              f"{_MAX_ANCHOR_PITCH_FT:g} ft maximum", (), code))
    if rules.minimum_anchors_per_run < _MIN_ANCHORS_PER_PIECE:
        out.append(_fail(cid, f"the schedule allows {rules.minimum_anchors_per_run} anchor(s) "
                              "per plate run; R403.1.6 requires two bolts per plate piece",
                         (), code))
    if not returns:
        out.append(_unknown(cid, "no sill-plate construction return resolves, so no anchorage "
                                 "is derived for the framed walls bearing on concrete",
                            (), code))
        return out
    if not out:
        length_ft = sum(r.length_m for r in returns) * 3.280839895013123
        out.append(_pass(cid, f"{len(returns)} sill-plate run(s) totalling {length_ft:.0f} LF "
                              f"are anchored at {rules.mudsill_anchor_pitch_ft:g} ft o.c. "
                              f"(min {rules.minimum_anchors_per_run} per run) with an approved "
                              "cast-in anchor — inside R403.1.6's 6 ft maximum", code))
    return out


@check(Tier.CODE, "code.R405_1_foundation_drainage")
def foundation_drainage(ctx: CheckContext) -> list[Finding]:
    """R405.1 — drains around every foundation retaining earth against usable space.

    Scoped by soil group, because R405.1's own exception is: Group I well-drained soils need
    no drainage system. The soil class is the site's own where it states one and the
    profile's presumption otherwise (``checks/soil.py``) — the same presumptive value the
    unbalanced-fill table is read at, so the two rules cannot disagree about what is under
    this house.
    """
    cid, code = "code.R405_1_foundation_drainage", "R405.1"
    grade = ctx.plan.project.site.grade
    if grade is None:
        return [_unknown(cid, "the site states no grade datum, so no wall can be classified "
                              "as retaining earth", (), code)]
    walls = _retaining_walls(ctx)
    if not walls:
        return [_pass(cid, "no foundation wall retains earth against a below-grade space",
                      code)]
    soil = (site_soil_class(ctx.plan, ctx.profile) or "").upper()
    footings = [e for e in ctx.plan.all_elements() if isinstance(e, Footing)]
    beddings = [e for e in ctx.plan.all_elements() if isinstance(e, FootingBedding)]
    tiled_footings = {b.host_ref for b in beddings
                      if b.drain_tile or b.drain_tile_spec is not None}
    tiled_walls = {f.under for f in footings if f.tag in tiled_footings}

    undrained = sorted(w.tag for w in walls if w.tag not in tiled_walls)
    drained = sorted(w.tag for w in walls if w.tag in tiled_walls)
    out: list[Finding] = []
    if drained:
        discharges = sorted({b.drain_tile_spec.discharge for b in beddings
                             if b.drain_tile_spec is not None and b.drain_tile_spec.discharge})
        out.append(_pass(cid, f"{len(drained)} retaining foundation wall(s) drain through "
                              f"footing tile discharging to "
                              f"{', '.join(discharges) or 'an authored outlet'}", code))
    if undrained:
        if soil in _group_one_soils():
            out.append(_pass(cid, f"{len(undrained)} retaining wall(s) run no footing tile, "
                                  f"and R405.1's exception exempts {soil} (Group I "
                                  "well-drained) soils: " + ", ".join(undrained), code))
        else:
            named = soil or "an unstated"
            out.append(_fail(cid, f"{len(undrained)} wall(s) retain earth on {named} soil "
                                  "with no drain tile in the footing bedding under them: "
                                  + ", ".join(undrained),
                             tuple(undrained), code))
    return out


@check(Tier.CODE, "code.R406_1_dampproofing")
def foundation_dampproofing(ctx: CheckContext) -> list[Finding]:
    """R406.1 — a damp-proof layer from the top of the footing to finished grade.

    Read off the assembly rather than off a wall flag: dampproofing is a *layer* on the
    earth side of the concrete, and the assembly is where this model says what a wall is
    made of. A layer qualifies when it carries the WATER control layer — which is the same
    property the envelope's water-control continuity checks read, so a wall cannot satisfy
    one and fail the other for a naming reason.

    R406.1 asks for the layer "from the top of the footing to finished grade", and until
    ``Layer.extent`` existed only *presence* could be tested: a layer had one vertical
    extent, the wall's, so there was nothing to compare against grade. A layer that now
    states a band has to reach that far, and a band that stops short of grade is graded
    exactly as a missing layer is — it is missing over the height that matters.
    """
    cid, code = "code.R406_1_dampproofing", "R406.1"
    grade = ctx.plan.project.site.grade
    if grade is None:
        return [_unknown(cid, "the site states no grade datum, so no wall can be classified "
                              "as below grade", (), code)]
    walls = _retaining_walls(ctx)
    if not walls:
        return [_pass(cid, "no foundation wall encloses interior space below grade", code)]
    assemblies = {a.tag: a for a in ctx.plan.library.assemblies}
    by_assembly: dict[str, list[str]] = {}
    for wall in walls:
        by_assembly.setdefault(wall.assembly, []).append(wall.tag)

    out: list[Finding] = []
    for assembly_tag, tags in sorted(by_assembly.items()):
        assembly = assemblies.get(assembly_tag)
        tags = sorted(tags)
        if assembly is None:
            out.append(_unknown(cid, f"{len(tags)} wall(s) name assembly {assembly_tag}, "
                                     "which the library does not define",
                                tuple(tags), code))
            continue
        proofed = [layer for layer in assembly.layers
                   if ControlLayer.WATER in (layer.control or set())
                   and layer.function in (LayerFunction.MEMBRANE, LayerFunction.SHEATHING,
                                          LayerFunction.CLADDING)]
        if proofed:
            short = _bands_short_of_grade(proofed)
            if short:
                out.append(_fail(
                    cid, f"{assembly_tag} ({len(tags)} wall(s)) dampproofs the earth side "
                         f"with '{proofed[0].name}', but its authored extent stops "
                         f"{short}; R406.1 wants it from the top of the footing to "
                         "finished grade: " + ", ".join(tags), tuple(tags), code))
            else:
                out.append(_pass(cid, f"{assembly_tag} ({len(tags)} wall(s)) dampproofs the "
                                      f"earth side with '{proofed[0].name}'", code))
        else:
            out.append(_fail(cid, f"{assembly_tag} ({len(tags)} wall(s) retaining earth "
                                  "against interior space) carries no water-control layer; "
                                  "R406.1 requires dampproofing from the top of the footing "
                                  "to finished grade: " + ", ".join(tags),
                             tuple(tags), code))
    return out


def _bands_short_of_grade(proofed: list[Layer]) -> str | None:
    """Why the first water-control layer's authored band fails to reach finished grade.

    ``None`` — the ordinary answer — when no band is authored at all (the layer runs the
    wall's full height, which is from the footing to the top of the wall and so past grade
    by definition), or when the band does reach. The two ways it can fall short are a
    bottom that starts above the footing and a top that dies below grade; both are stated
    against a datum, so both are answerable without a wall.
    """
    from typehaus.model.enums import LayerDatum

    extent = getattr(proofed[0], "extent", None)
    if extent is None:
        return None
    top, bottom = extent.top, extent.bottom
    if top is not None:
        if top.datum is LayerDatum.GRADE and top.offset.meters < -1e-9:
            return f'{-top.offset.inches:.1f}" below grade'
        if top.datum is LayerDatum.WALL_BASE:
            return "at the wall base"
    if bottom is not None and bottom.datum is LayerDatum.GRADE \
            and bottom.offset.meters > 1e-9:
        return f'{bottom.offset.inches:.1f}" above grade at its bottom'
    return None


__all__ = ["foundation_anchorage", "foundation_dampproofing", "foundation_drainage"]
