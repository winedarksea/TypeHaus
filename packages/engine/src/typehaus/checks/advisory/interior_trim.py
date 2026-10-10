"""What the derived interior trim ran into (→ resolve/interior_trim.py).

ADVISORY, and deliberately not FAIL yet: no code governs a casing, and whether a clash
should block is the owner's call on review, so nothing new lands on a clean gate
unannounced.

* ``advisory.casing_clipped`` — one finding per casing leg the resolver scribed short or
  left off, naming what it ran into. A PASS that says so: the resolver already did what a
  carpenter would, and the finding is the record of it, never a silent trim.
* ``advisory.trim_device_clash`` — a wall-hosted placeable (a receptacle or switch plate, a
  register, a rail) whose body overlaps a casing or base board. UNKNOWN: someone has to move
  one of them, and which is a judgement.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, not_applicable
from typehaus.resolve.geometry_millwork import base_run_prisms, door_casing_prisms

_CLIPPED = "advisory.casing_clipped"
_CLASH = "advisory.trim_device_clash"
_M_TO_IN = 39.37007874
# Overlap smaller than this (plan area, m²) is a plate kissing a board edge, not a clash.
_TOUCH_M2 = 1e-6
_ADVISORY = "ADVISORY — "


@check(Tier.ADVISORY, _CLIPPED)
def casing_clipped(ctx: CheckContext) -> list[Finding]:
    """Every casing leg scribed or dropped, and what it ran into."""
    casings = sorted(ctx.model.door_casings, key=lambda c: c.tag)
    if not casings:
        return [not_applicable(_CLIPPED, "this plan derives no door casing")]
    out: list[Finding] = []
    for casing in casings:
        for clip in casing.clips:
            side = clip.piece.replace("leg_", "")
            what = ("left off" if clip.dropped else
                    f'scribed to {clip.remaining_m * _M_TO_IN:.2f}"')
            out.append(advisory(
                _CLIPPED,
                f"{_ADVISORY}{casing.opening_ref} ({casing.room} face): the {side} casing leg "
                f"runs into {clip.obstruction} and is {what}",
                (casing.opening_ref, casing.room), Result.PASS))
    if not out:
        out.append(advisory(_CLIPPED, "every derived casing leg is full width",
                            (), Result.PASS))
    return out


@check(Tier.ADVISORY, _CLASH)
def trim_device_clash(ctx: CheckContext) -> list[Finding]:
    """No wall-hosted body overlaps a casing or base board."""
    from shapely.geometry import Polygon

    boards = []
    for run in ctx.model.base_runs:
        boards.extend((run.room, run.storey, prism) for prism in base_run_prisms(run))
    for casing in ctx.model.door_casings:
        boards.extend((casing.opening_ref, casing.storey, prism)
                      for prism in door_casing_prisms(casing))
    if not boards:
        return [not_applicable(_CLASH, "this plan derives no base or casing")]
    hosted = [item for item in ctx.model.canvas_objects
              if item.attachment_wall and len(item.footprint) >= 3
              and item.body_z0_m is not None and item.body_z1_m is not None]
    if not hosted:
        return [not_applicable(_CLASH, "no placeable in this plan is hosted on a wall")]
    out: list[Finding] = []
    for item in sorted(hosted, key=lambda i: i.tag):
        body = Polygon(item.footprint)
        if not body.is_valid:
            continue
        hits = sorted({owner for owner, storey, prism in boards
                       if storey == item.storey
                       and min(item.body_z1_m, prism.z1_m) > max(item.body_z0_m, prism.z0_m)
                       and body.intersection(Polygon(prism.ring)).area > _TOUCH_M2})
        if hits:
            out.append(advisory(
                _CLASH,
                f"{_ADVISORY}{item.tag} on {item.attachment_wall} overlaps the trim at "
                f"{', '.join(hits)}: move the {item.kind.lower()} or scribe the trim",
                (item.tag, *hits), Result.UNKNOWN,
                fix="move the device clear of the casing or base, or clip the trim by hand"))
    if not out:
        out.append(advisory(_CLASH, f"no wall-hosted body of {len(hosted)} overlaps the trim",
                            (), Result.PASS))
    return out
