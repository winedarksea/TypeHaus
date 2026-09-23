"""Where a drainage run lets go, in geometry: receiver footprints and bodies of stone.

Split out of ``drainage_network.py``. Everything here reads the RESOLVED model — the solid a
receiver resolved to, the stone a bed resolved to — never a re-derivation of either.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext
from typehaus.model.mep import Sump
from typehaus.model.structure import Drywell, FrenchDrain


def _elements(ctx: CheckContext):
    for storey in ctx.model.plan.storeys:
        yield from ctx.model.plan.storey_elements(storey.tag)

#: How far above a receiver's own inlet a discharging invert may sit and still be read as
#: arriving in it. Two inches — a pipe let into the top course of stone, and a survey
#: tolerance. Anything more and the run ends in undisturbed ground: catlin's field lateral
#: hung **28 inches** over the well it fed, and five wall-bed tiles hung 9 inches over the
#: same well before the well was moved onto their plane.
ARRIVAL_TOLERANCE_M = 2.0 * 0.0254

#: How far outside a receiver's own footprint a run's last vertex may land. The receiver's
#: radius plus this: a run drawn to the edge of a cylinder reads in section as a pipe that
#: does not arrive, so the house authors them to the CENTRE, and this is the slack around
#: that convention. Six inches.
PLAN_ARRIVAL_SLACK_M = 6.0 * 0.0254



def receiver_footprints(ctx: CheckContext) -> dict[str, tuple[object, float, float]]:
    """``tag -> (plan polygon, z bottom, z top)`` for every drywell, sump and soakaway bed.

    Read off the **resolved solid**, not re-derived from the authored position and depth.
    The resolver already places both — a soakaway from its top of stone down, a pit from the
    slab it is cast into down — and a second derivation here would be a second opinion about
    the same elevation, which is how a receiver ends up at a level nothing else agrees with.

    ** IT ALSO HAS TO BE PRESENT. ** The first cut of this walked ``Sump.host_ref`` to the
    slab, found it in neither ``model.floors`` nor ``model.solids`` under that name, returned
    ``None``, and every rule downstream skipped the pit — so nineteen perimeter rings
    "passed" by never being asked. A receiver whose solid does not resolve gets no footprint
    and the rules that need one report it, rather than falling silently through.
    """
    from shapely.geometry import Polygon

    wanted = {e.tag for e in _elements(ctx) if isinstance(e, (Drywell, Sump))}
    out: dict[str, tuple[object, float, float]] = {}
    for solid in ctx.model.solids:
        if solid.tag in wanted and solid.tag not in out and len(solid.outline) >= 3:
            out[solid.tag] = (Polygon(solid.outline), solid.z0_m, solid.z1_m)
    # A soakaway bed's footprint is its whole stone, flood course included.
    for bed in ctx.model.footing_beddings:
        if bed.soakaway_z0_m is not None and len(bed.outline) >= 3:
            out[bed.tag] = (Polygon(bed.outline), bed.stone_z0_m, bed.z1_m)
    return out


def body_touches(ctx: CheckContext, body: frozenset, footprint, tolerance_m: float) -> bool:
    from shapely.geometry import Polygon

    shape, bottom, top = footprint
    for bed in ctx.model.footing_beddings:
        if bed.tag not in body or len(bed.outline) < 3:
            continue
        if bed.stone_z0_m >= top + tolerance_m or bottom >= bed.z1_m + tolerance_m:
            continue
        if Polygon(bed.outline).distance(shape) <= tolerance_m:
            return True
    return False


def run_starts_in(run: FrenchDrain, ctx: CheckContext, body: frozenset) -> bool:
    """Does this run pick water up from that body of stone?

    Any vertex inside a bed of the body, not only the first: a lead authored from the
    strips' court face to a well's centre passes THROUGH the stone it drains, and which end
    of the path was written first is an authoring habit rather than a hydraulic fact.
    """
    from shapely.geometry import Point as ShapelyPoint
    from shapely.geometry import Polygon

    points = [ShapelyPoint(p.x.meters, p.y.meters) for p in run.path]
    for bed in ctx.model.footing_beddings:
        if bed.tag not in body or len(bed.outline) < 3:
            continue
        shape = Polygon(bed.outline)
        if any(shape.distance(point) <= 0.3048 for point in points):
            return True
    return False


def reaches_through_stone(ctx: CheckContext, run: FrenchDrain, target: str) -> bool:
    """Does this run's trench end in a body of stone that reaches ``target``?

    The connection a trench makes to a receiver it does not touch: it ends in a bedding, the
    bedding's body is continuous with the receiver, and water is in the receiver. Both halves
    are geometric — touching in plan, overlapping in section — so this claims nothing the
    model cannot show.
    """
    from typehaus.resolve.drainage_network import BODY_TOUCH_TOLERANCE_M, stone_bodies

    footprints = receiver_footprints(ctx)
    if target not in footprints:
        return False
    bodies = stone_bodies(ctx.model)
    for bed in ctx.model.footing_beddings:
        if bed.tag not in bodies:
            continue
        body = bodies[bed.tag]
        if not run_starts_in(run, ctx, frozenset({bed.tag})):
            continue
        if body_touches(ctx, body, footprints[target], BODY_TOUCH_TOLERANCE_M):
            return True
    return False


def soakaway_arrival(ctx: CheckContext, target: str, end_xy: tuple[float, float],
                     invert_m: float | None) -> str | None:
    """``None`` when an outlet lands in ``target``'s body of stone, else why it does not.

    A soakaway bed has no single inlet level: water arrives anywhere in its stone. So the
    outlet invert must sit within ``[stone bottom, top]`` of SOME bed of the body, with the
    outlet's plan point inside that bed's outline (plus the plan slack).
    """
    from shapely.geometry import Point as ShapelyPoint
    from shapely.geometry import Polygon

    from typehaus.resolve.drainage_network import stone_bodies

    body = stone_bodies(ctx.model).get(target, frozenset({target}))
    beds = [b for b in ctx.model.footing_beddings if b.tag in body and len(b.outline) >= 3]
    if not beds:
        return f"{target}'s stone does not resolve"
    end = ShapelyPoint(*end_xy)
    near = [b for b in beds if Polygon(b.outline).distance(end) <= PLAN_ARRIVAL_SLACK_M]
    if not near:
        return f"it ends outside every bed of {target}'s stone body"
    if invert_m is None:
        return None
    for bed in near:
        if bed.stone_z0_m - ARRIVAL_TOLERANCE_M <= invert_m <= bed.z1_m + ARRIVAL_TOLERANCE_M:
            return None
    bed = near[0]
    return (f"it lets go at {invert_m / 0.0254:.0f}\", outside {bed.tag}'s stone "
            f"({bed.stone_z0_m / 0.0254:.0f}\" to {bed.z1_m / 0.0254:.0f}\")")
