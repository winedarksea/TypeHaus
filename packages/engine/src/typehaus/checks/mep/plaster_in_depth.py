"""``mep.plaster_in_depth`` — a plaster-in LED channel needs room above its board.

A plaster-in run (``resolve/drywall_led.py``) sets an aluminium channel into a slot cut
through the ceiling or soffit board, and the channel stands ``PlasterInProfile.depth`` above
the board's room face: more than a 5/8" board, so it rises into whatever the board is
fastened to. Nothing else grades that volume: the slot is cut from the board only.

Each leg's occupied volume is its swept section's parts that rise above the face (the mudded
wings lie on it), over the face-to-top band. It is graded against every framed member and
column or beam (``_interference_geom.framing_candidates``, the framing checks' own reading)
and every placed pipe, duct and raceway envelope (``resolve/mep_envelopes``, the router's).
A schematic raceway is not placed, so it is not graded (as ``mep.run_interference``).

``Tier.STRUCTURAL`` with no permit item, like ``mep.run_interference``: a buildability
clash, not a code section.
"""

from __future__ import annotations

from shapely import STRtree
from shapely.geometry import Polygon

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.resolve.geometry import length, rect_between, sub

CID = "mep.plaster_in_depth"
#: Overlap under a sixteenth (the authoring grid) is two things drawn to touch.
TOUCH_M = 0.0015875
#: Shared plan area under this is an abutment, not a clash (the framing checks' figure).
MIN_AREA_M2 = 1e-4
_IN = 0.0254


def _legs(run) -> list[tuple[Polygon, float]]:
    """``(plan footprint, top z)`` per leg: the parts above the face, swept along it."""
    sign = 1.0 if run.emission_side == "left" else -1.0
    raised = [quad for _key, quad in run.section if min(d for _a, d in quad) < -TOUCH_M]
    if not raised:
        return []
    across = [sign * a for quad in raised for a, _d in quad]
    rise = -min(d for quad in raised for _a, d in quad)
    out = []
    for p0, p1 in zip(run.path, run.path[1:], strict=False):
        if length(sub(p1, p0)) < 1e-6:
            continue
        out.append((Polygon(rect_between(p0, p1, min(across), max(across))), run.z_m + rise))
    return out


def _obstacles(ctx: CheckContext) -> list[tuple[str, Polygon, object]]:
    """``(label, plan footprint, z band at a plan point)`` for framing and placed runs."""
    from typehaus.checks.structural._interference_geom import framing_candidates
    from typehaus.resolve.mep_envelopes import envelopes
    from typehaus.resolve.mep_queries import schematic_conduits

    out: list[tuple[str, Polygon, object]] = [
        (f"{c.kind} {c.label}", c.poly, c.zband_at) for c in framing_candidates(ctx.model)]
    schematic = schematic_conduits(ctx.model)
    for envelope in envelopes(ctx.model):
        if envelope.tag in schematic:
            continue
        for prism in envelope.prisms:
            out.append((f"{envelope.kind} {envelope.tag}", prism.footprint,
                        lambda _point, z=(prism.z0_m, prism.z1_m): z))
    return out


@check(Tier.STRUCTURAL, CID)
def plaster_in_depth(ctx: CheckContext) -> list[Finding]:
    """Every plaster-in channel clears the framing and runs above its board."""
    runs = [run for run in ctx.model.light_runs if run.profile == "plaster_in"]
    if not runs:
        return [_na(CID, "no light run is set into a gypsum board in this building")]
    obstacles = _obstacles(ctx)
    index = STRtree([poly for _label, poly, _band in obstacles])
    out: list[Finding] = []
    for run in runs:
        clashes: dict[str, float] = {}
        legs = _legs(run)
        top = max((leg_top for _footprint, leg_top in legs), default=run.z_m)
        for footprint, leg_top in legs:
            for position in index.query(footprint):
                label, poly, band = obstacles[int(position)]
                shared = poly.intersection(footprint)
                if shared.area < MIN_AREA_M2:
                    continue
                z_lo, z_hi = band(shared.representative_point().coords[0])
                if z_lo < leg_top - TOUCH_M and z_hi > run.z_m + TOUCH_M:
                    clashes[label] = max(clashes.get(label, 0.0),
                                         leg_top - max(z_lo, run.z_m))
        host = run.soffit_ref or f"{run.room} ceiling"
        rise = f'{(top - run.z_m) / _IN:.2f}"'
        if not clashes:
            out.append(_pass(CID, f"{run.tag}: its channel's {rise} above the {host} board "
                                  "face is clear", (run.tag,)))
            continue
        worst = sorted(clashes, key=lambda label: (-clashes[label], label))
        named = ", ".join(f'{label} ({clashes[label] / _IN:.2f}")' for label in worst[:3])
        more = f" and {len(worst) - 3} more" if len(worst) > 3 else ""
        out.append(_fail(CID, (
            f"{run.tag}: its plaster-in channel stands {rise} above the {host} board face "
            f"and runs into {len(worst)} element(s): {named}{more}"), (run.tag,),
            fix="fur the board down clear of the channel, re-route what crosses it, or "
                "choose a shallower profile"))
    return out
