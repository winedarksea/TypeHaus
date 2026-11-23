"""The rated head and base of a pinned wood roof post, both directions — for ``wood_roof_post``.

Every end of a pinned post returns a lateral reaction, and until 2026-09-30 none had a rated
path: a CCQ and an ABU publish no lateral row. What is graded now, each against the catalog
row of the part the plan AUTHORS at that joint:

* **head, along the beam** — the AC/ACE cap's lateral row (ESR-2604 Table 3 fn. 6: parallel to
  the beam only), linear with the cap's uplift where the post carries both;
* **head, across the beam** — the A35 angles on the post's free faces up to the beam soffit
  (ESR-3096 Table 5), each at the lower of F1/F2;
* **base** — the cast-in CBSTQ's uplift with its lateral in each direction, F2 along
  ``Connector.axis`` and F1 across it, summed linearly (Simpson's own unity rule);
* **the plate end** — for a post a panel is framed into, the A35 carrying the panel's top-plate
  reaction into the post side face.

**Oracle.** ``houses/catlin/notes/canopy_west_band.md`` §5.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typehaus.engineering.canopy_service import OUTSIDE_REPORT, WET_CM, WET_RULE
from typehaus.engineering.item import LimitState


@dataclass(frozen=True)
class EndDemands:
    """ASD lb at each end of one post. ``along`` is parallel to the beam it carries."""

    head_along: float
    head_across: float
    base_along: float
    base_across: float
    head_uplift: float
    base_uplift: float
    plate_lb: float = 0.0


def _parts(ctx: Any, post_tag: str) -> list[Any]:
    return [e for e in ctx.plan.all_elements()
            if getattr(e, "connects", ()) and post_tag in e.connects
            and getattr(e, "size", None)]


def joint_rows(ctx: Any, post_tag: str, beam_axis: str, demands: EndDemands,
               missing: list[str]) -> list[LimitState]:
    from typehaus.hardware.catalog import allowable_for_model
    from typehaus.model.enums import ConnectorKind

    parts = _parts(ctx, post_tag)
    cap = next((p for p in parts if p.kind is ConnectorKind.POST_CAP), None)
    base = next((p for p in parts if p.kind is ConnectorKind.POST_BASE), None)
    angles = [p for p in parts if p.kind is ConnectorKind.TENSION_TIE and p.size == "A35Z"]
    states: list[LimitState] = []
    cap_allow = allowable_for_model(cap.size) if cap else None
    if cap_allow is None or cap_allow.uplift_lb is None:
        missing.append(f"a post cap with published uplift on {post_tag}")
    else:
        cap_up = cap_allow.uplift_lb * WET_CM
        up = demands.head_uplift / cap_up
        states.append(LimitState(f"{cap.size} head uplift", demands.head_uplift, cap_up, "lb",
                                 f"{cap_allow.citation.split(':')[0]}; {WET_RULE}; "
                                 f"{OUTSIDE_REPORT}"))
        if cap_allow.lateral_f1_lb:
            cap_lat = cap_allow.lateral_f1_lb * WET_CM
            lat = demands.head_along / cap_lat
            states.append(LimitState(
                f"{cap.size} head, uplift + lateral along the beam", up + lat, 1.0, "",
                f"linear: {demands.head_uplift:,.1f} / {cap_up:,.0f} + "
                f"{demands.head_along:,.1f} / {cap_lat:,.0f} (ESR-2604 Table 3 fn. 6, lateral "
                f"parallel to the beam; x C_M {WET_CM:g}, wet, outside the report)"))
        else:
            missing.append(f"a lateral row along the beam for {cap.size} on {post_tag}")
    from typehaus.model.elements import Wall

    # An angle naming a WALL ties that panel's plate into the post; one naming the beam is
    # the head's across-beam path.
    plate_angles = [a for a in angles
                    if any(isinstance(ctx.plan.by_tag(t), Wall) for t in a.connects)]
    head_angles = [a for a in angles if a not in plate_angles]
    _angle_row(states, head_angles, demands.head_across, "head, across the beam", post_tag,
               missing, required=demands.head_across > 0.0)
    if demands.plate_lb > 0.0:
        _angle_row(states, plate_angles, demands.plate_lb, "panel top plate into the post",
                   post_tag, missing, required=True)
    base_allow = allowable_for_model(base.size) if base else None
    if base_allow is None or base_allow.uplift_lb is None:
        missing.append(f"a post base with published uplift on {post_tag}")
        return states
    f2_along_beam = getattr(base, "axis", None) == beam_axis
    along_cap = base_allow.lateral_f2_lb if f2_along_beam else base_allow.lateral_f1_lb
    across_cap = base_allow.lateral_f1_lb if f2_along_beam else base_allow.lateral_f2_lb
    if not along_cap or not across_cap:
        missing.append(f"lateral rows for {base.size} on {post_tag}")
        return states
    base_up = base_allow.uplift_lb * WET_CM
    up = demands.base_uplift / base_up
    for label, lateral, allow in (("along the beam", demands.base_along, along_cap * WET_CM),
                                  ("across the beam", demands.base_across, across_cap * WET_CM)):
        states.append(LimitState(
            f"{base.size} base, uplift + lateral {label}", up + lateral / allow, 1.0, "",
            f"wet, x C_M {WET_CM:g} on every term, outside the report; "
            f"linear unity: {demands.base_uplift:,.1f} / {base_up:,.0f} (cracked) "
            f"+ {lateral:,.1f} / {allow:,.0f}; F2 along Connector.axis "
            f"{getattr(base, 'axis', None) or 'unset'}. {base_allow.citation.split(';')[0]}"))
    return states


def _angle_row(states, angles, demand, label, post_tag, missing, required) -> None:
    from typehaus.hardware.catalog import allowable_for_model

    if not angles:
        if required:
            missing.append(f"an A35Z for the {label} on {post_tag}")
        return
    allow = allowable_for_model(angles[0].size)
    values = [v for v in (allow.lateral_f1_lb, allow.lateral_f2_lb) if v] if allow else []
    if not values:
        missing.append(f"a lateral row for {angles[0].size}")
        return
    states.append(LimitState(
        f"{angles[0].size} {label}", demand / len(angles), min(values) * WET_CM, "lb",
        f"{demand:,.1f} lb over {len(angles)} angle(s) at the lower of F1/F2 x C_M "
        f"{WET_CM:g} (wet, outside the report) — {allow.citation.split(':')[0]}"))
