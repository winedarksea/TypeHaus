"""A face-mount hanger's seat fits the member it carries, in width (→ 12 §checks/structural).

Nothing validated a hanger designation against its member until 2026-10-31 (geometry review
C3-E11): catlin's single 2x8 `BM-BW-SCSILL` sat in a double-2x8 `HU28-2Z`, 1 5/8" of slop,
at 0 FAIL. Simpson's face-mount tables are by joist size, and a seat is that size's own
W: a member it cannot take, or one with room to roll, is the wrong part.

**Width only, both ways.** FAIL when the seat's clear W is narrower than the member less
1/32" (the member does not go in) or wider than the member plus 1/8" (the catalog's own
step: a 1 1/2" joist takes a 1 9/16" seat, a 4 1/2" triple a 4 5/8"). LUS26-2Z on a 3",
HU28-2Z on a 3" and LUS210-3Z on a 4 1/2" sit EXACTLY on the 1/8" bound, so it carries a
float tolerance. Height and seat depth are not graded here.

Two populations, one rule: authored hangers (the carried beam named first in ``connects``,
measured off its resolved solid) and derived hanger joints (their own member width). A
designation with no dimensioned catalog row is UNKNOWN, never passed.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity, not_applicable
from typehaus.quantities import M_PER_IN

_CHECK_ID = "structural.hanger_seat_fit"
#: A seat may be this much narrower than its member before the member will not go in.
TIGHT_IN = 1 / 32
#: ... and this much wider before the member is loose in it.
LOOSE_IN = 1 / 8
#: Float slack on both bounds: three catalog pairings land exactly on 1/8".
_FLOAT_IN = 1e-6


_Hanger = tuple[str, str, float | None, float | None, tuple[str, ...]]


def _authored(model) -> list[_Hanger]:
    """``(label, part, member width in, member depth in, tags)`` per authored hanger."""
    from typehaus.model.enums import ConnectorKind
    from typehaus.model.structure import Connector
    from typehaus.resolve.connector_geometry.placement import (
        ConnectorPlacementIndex,
        authored_hanger_section,
    )

    index = None
    out = []
    for el in model.plan.all_elements():
        if not (isinstance(el, Connector) and el.kind is ConnectorKind.JOIST_HANGER):
            continue
        if el.hanger_spec_pair(model.plan) is not None:
            continue  # a spec for a floor's hung ends: its derived joints are graded below
        index = index or ConnectorPlacementIndex(model)
        section = authored_hanger_section(index, el)
        width, depth = (s / M_PER_IN for s in section) if section else (None, None)
        out.append((el.tag, el.size, width, depth, (el.tag, *el.connects)))
    return out


def _derived(model) -> list[_Hanger]:
    from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG
    from typehaus.joints import derived_joints
    from typehaus.resolve.connector_geometry.placement import HANGER_PREFIXES

    return [(f"{joint.part} at {'/'.join(joint.members)}", joint.part,
             joint.member_width_m / M_PER_IN if joint.member_width_m else None,
             joint.height_m / M_PER_IN if joint.height_m else None, tuple(joint.members))
            for joint in derived_joints(model, DEFAULT_HARDWARE_TAKEOFF_CONFIG)
            if joint.part.upper().startswith(HANGER_PREFIXES)
            and joint.outward_xy is not None]


@check(Tier.STRUCTURAL, _CHECK_ID)
def hanger_seat_fit(ctx: CheckContext) -> list[Finding]:
    """Every face-mount hanger's seat width fits its carried member (−1/32" / +1/8")."""
    from typehaus.resolve.connector_geometry.hangers import hanger_dimensions

    if getattr(ctx.model, "plan", None) is None:
        return []
    hangers = _authored(ctx.model) + _derived(ctx.model)
    if not hangers:
        return [not_applicable(_CHECK_ID, "no face-mount hanger is authored or derived in "
                               "this plan")]
    out: list[Finding] = []
    fit: list[str] = []
    unknown: list[str] = []
    for label, part, width, depth, tags in hangers:
        row = hanger_dimensions(part, member_width_in=width, member_depth_in=depth)
        if row is None or width is None:
            unknown.append(f"{label} ({part})")
            continue
        slop = row.clear_width_in - width
        if -TIGHT_IN - _FLOAT_IN <= slop <= LOOSE_IN + _FLOAT_IN:
            fit.append(tags[0] if label == tags[0] else label)
            continue
        verdict = ("is narrower than" if slop < 0 else "is wider than")
        out.append(Finding(
            severity=Severity.ERROR, check_id=_CHECK_ID, result=Result.FAIL,
            message=(f"{label}: the {part} seat (W {row.clear_width_in:.4g}\") {verdict} the "
                     f"{width:.4g}\" member it carries by {abs(slop):.4g}\" (allowed "
                     f"-{TIGHT_IN:.4g}\" / +{LOOSE_IN:.4g}\")"),
            element_tags=tags,
            fix_hint="name the hanger sized for the member's own width (the catalog's "
                     "joist-size row), or change the member"))
    if fit:
        out.append(Finding(
            severity=Severity.WARN, check_id=_CHECK_ID, result=Result.PASS,
            message=f"{len(fit)} face-mount hanger seat(s) fit their members' width",
            element_tags=tuple(sorted(t for t in fit if " at " not in t))))
    if unknown:
        out.append(Finding(
            severity=Severity.WARN, check_id=_CHECK_ID, result=Result.UNKNOWN,
            message=(f"{len(unknown)} hanger(s) have no dimensioned catalog row or no "
                     f"measured member: {', '.join(sorted(unknown)[:6])}"),
            fix_hint="add the part's W/H/B to resolve/connector_geometry/hangers.py"))
    return out
