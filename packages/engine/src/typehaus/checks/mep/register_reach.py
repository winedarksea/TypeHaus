"""Does a register's boot actually reach the run it names? (3D)

``mep.duct_connectivity`` grades run ENDS, and only in plan for a boot. A floor register in
the attic over a second-storey trunk sits in plan within a hand's width of the run it names
and 9-20" above it, and draws like a connection. This reads the register's neck box against
the named run's section in plan *and* z.

* **Plan:** the register is within ``BOOT_REACH_M`` (36") of some segment of the run: the
  same reach ``_boot`` and ``resolve/duct_terminations`` use, to the PATH not just an end.
* **Z:** the neck box (``terminal_necks.neck_boxes``) is within ``BOOT_DROP_M`` of the
  segment's section (its z span widened by half the section height). A boot IS the neck: a
  stamped boot a round take-off collar tall (4") stands between neck face and duct. Catlin's
  authored boots top out at 3.1" (floor boots over an ERV radial); the attic floor boots
  are 5.4"-14.7" short.

Not graded here (another check owns them): a plain round ceiling COLLAR (``_collar_end``
and ``terminal_drops`` already demand it be seated on top of the run), and a register the
run names in ``end_terminal_ref`` (``inlet_connection_error``). A register with no neck box
has only its face: within the drop, PASS; farther, UNKNOWN (the boot is unmodelled).
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import failed, passed, unknown
from typehaus.checks.mep.duct_connectivity import BOOT_REACH_M, _collar_tags
from typehaus.checks.registry import CheckContext, Tier, check, shared
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.mep_soffit import plan_distance_to_segment

_CID = "mep.register_reach"

#: The most z a boot spans between its neck face and the run's section: a 4" round
#: take-off collar. Sits between the largest authored gap (3.1") and the smallest red (5.4").
BOOT_DROP_M = inch(4).meters


def _neck_z(ctx: CheckContext, obj) -> tuple[float, float, bool] | None:
    """``(z0, z1, has_neck)`` of the neck box, else the face body, else None."""
    from typehaus.resolve.terminal_necks import neck_boxes

    boxes = shared(ctx, "register_reach.necks", lambda: _necks(neck_boxes(ctx.model)))
    spans = boxes.get(obj.tag)
    if spans:
        return min(s[0] for s in spans), max(s[1] for s in spans), True
    if obj.body_z0_m is None or obj.body_z1_m is None:
        return None
    return obj.body_z0_m, obj.body_z1_m, False


def _necks(rows) -> dict[str, list[tuple[float, float]]]:
    out: dict[str, list[tuple[float, float]]] = {}
    for tag, ring, z0, z1, _part in rows:
        if ring:  # an empty ring is a wall neck whose back was not found
            out.setdefault(tag, []).append((z0, z1))
    return out


def _inches(metres: float) -> str:
    return f'{metres / M_PER_IN:.1f}"'


@check(Tier.INTEGRITY, _CID)
def register_reach(ctx: CheckContext) -> list[Finding]:
    """Each register's neck face meets the section of the run it names, in plan and z."""
    ducts = {d.tag: d for d in ctx.model.ducts if len(d.path) >= 2}
    objects = {o.tag: o for o in ctx.model.canvas_objects}
    out: list[Finding] = []
    for el in ctx.plan.all_elements():
        duct = ducts.get(getattr(el, "duct_ref", None) or "") if (
            el.element_kind == "Register") else None
        obj = objects.get(el.tag)
        if duct is None or obj is None:
            continue  # no run to reach, or no placed register: other checks say so
        authored = ctx.plan.by_tag(duct.tag)
        if (el.tag in _collar_tags(ctx, duct)
                or getattr(authored, "end_terminal_ref", None) == el.tag):
            continue
        out.append(_grade(ctx, el.tag, obj, duct))
    return out


def _grade(ctx: CheckContext, tag: str, obj, duct) -> Finding:
    if len(duct.z_m) != len(duct.path):
        return unknown(_CID, f"{duct.tag} has no elevation per vertex, so {tag}'s boot "
                             "cannot be compared in z", (tag, duct.tag))
    neck = _neck_z(ctx, obj)
    if neck is None:
        return unknown(_CID, f"{tag} resolves no body elevation, so its boot cannot be "
                             f"compared with {duct.tag} in z", (tag, duct.tag))
    z0, z1, has_neck = neck
    half = (duct.diameter_m or duct.depth_m) / 2.0
    reach = []  # (gap, plan, lo, hi) for each segment within a boot's plan reach
    near = float("inf")
    for i in range(len(duct.path) - 1):
        span, t = plan_distance_to_segment(obj.position, duct.path[i], duct.path[i + 1])
        near = min(near, span)
        if span > BOOT_REACH_M:
            continue
        za, zb = duct.z_m[i], duct.z_m[i + 1]
        if math.dist(duct.path[i], duct.path[i + 1]) > 1e-6:
            za = zb = za + t * (zb - za)  # a sloped leg: its elevation where the boot meets it
        lo, hi = min(za, zb) - half, max(za, zb) + half  # a riser spans its whole length
        reach.append((max(z0 - hi, lo - z1, 0.0), span, lo, hi))
    if not reach:
        return failed(_CID, f"{tag} names {duct.tag} but no part of the run is within "
                            f"{_inches(BOOT_REACH_M)} of it in plan (nearest {_inches(near)}): "
                            "no drawn connection", (tag, duct.tag),
                      fix=f"draw {duct.tag} to the register, or name the run that serves it")
    gap, span, lo, hi = min(reach)
    face = "neck" if has_neck else "face"
    if gap <= BOOT_DROP_M:
        return passed(_CID, f"{tag}'s {face} meets {duct.tag}'s section within "
                            f"{_inches(span)} in plan and {_inches(gap)} in z (boot drop "
                            f"{_inches(BOOT_DROP_M)})", (tag, duct.tag))
    side = "above" if z0 > hi else "below"
    if not has_neck:
        return unknown(_CID, f"{tag} has no neck box, and its face stands {_inches(gap)} "
                             f"{side} {duct.tag} (boot drop {_inches(BOOT_DROP_M)}): the "
                             "boot that spans it is not modelled", (tag, duct.tag),
                       fix="give the register type a neck, or draw the drop")
    return failed(_CID, f"{tag}'s neck stands {_inches(gap)} {side} {duct.tag}'s section "
                        f"({_inches(span)} off in plan), past a boot's {_inches(BOOT_DROP_M)} "
                        "drop: no drawn connection", (tag, duct.tag),
                  fix=f"draw the boot or drop from {duct.tag} to {tag} "
                      "(a run ending on the neck, or end_terminal_ref)")
