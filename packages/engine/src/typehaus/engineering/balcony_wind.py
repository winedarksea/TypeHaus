"""The wind demand on a freestanding deck, as an area and a storey shear.

Hoisted out of ``checks/structural/lateral_racking.py`` on 2026-09-03, when the balcony's
lateral system stopped being eight knee braces and became four fixed concrete columns. The
two consumers ask the same question — *how much wind does this thing catch, and how much
shear does that put at the storey* — and answer it against the same ASCE 7-16 §29.3
inversion; deriving the area twice is how the two would start disagreeing about the same
structure.

**This module must not move lateral_racking's numbers**, and the check imports every name
back so that it cannot: ``tests/test_lateral_racking.py`` pins the band areas and the
critical coefficients on the landed house, and those tests are the contract.

**Why the engineering package and not ``checks``.** ``engineering/`` is a leaf that may not
import ``checks`` (see ``engineering/__init__``), so the shared code has to live on this
side of the line. The check importing *down* into it is the same direction
``engineering/pier_basis`` already runs relative to its two consumers.

**What it deliberately does NOT do.** It does not pick ``C_f``. ASCE 7-16 Fig. 29.3-1 is a
copyrighted table this repository holds three verified cells of, so both consumers invert
instead — reporting the coefficient at which a joint reaches capacity — and that inversion
stays with whoever is grading a capacity. This module hands over ``area_sf`` and
``storey_shear_lb(c_f)`` and stops.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from typehaus.checks.structural._asce_29_3_table import GUST_EFFECT_RIGID
from typehaus.model.structure import Post
from typehaus.wind import ASD_WIND_FACTOR

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.model.plan import PlanModel

_FT = 0.3048

#: Deck plank thickness contributes to the solid edge band. Read off the fascia's own top
#: elevation vs. the deck it faces would be better; the fascia's `depth` already covers the
#: joist ends and the plank edge, so nothing is added for the plank here — it would be
#: double counting. Recorded as a constant of zero so the decision is visible, not implied.
PLANK_BAND_FT = 0.0


@dataclass(frozen=True)
class Band:
    """One horizontal strip of solid area the wind sees, and where it came from."""

    label: str
    depth_ft: float       # vertical dimension of the strip
    length_ft: float      # its plan run, perpendicular to the wind
    source: str           # the element tag it was derived from

    @property
    def area_sf(self) -> float:
        return self.depth_ft * self.length_ft


@dataclass(frozen=True)
class Demand:
    """The wind demand on one freestanding structure in one plan direction.

    ``members`` is what the shear is eventually divided among — knee braces for the braced
    case, cast columns for the braceless one — and this module holds it only so the two
    consumers can carry one object instead of two. Nothing here reads it.
    """

    axis: str             # "x" (E-W wind) | "y" (N-S wind)
    q_h_psf: float
    height_ft: float      # top of the appurtenance above the ground beneath it
    bands: tuple[Band, ...]
    members: tuple[Any, ...] = ()

    @property
    def area_sf(self) -> float:
        return sum(b.area_sf for b in self.bands)

    def storey_shear_lb(self, c_f: float) -> float:
        """ASD storey shear at a given force coefficient: 0.6 · q_h · G · C_f · A_s."""
        return ASD_WIND_FACTOR * self.q_h_psf * GUST_EFFECT_RIGID * c_f * self.area_sf


def ft(length: Any) -> float:
    return float(length.meters) / _FT


def solid_bands(plan: PlanModel, axis: str, member_tags: Any,
                fascia: Any) -> tuple[Band, ...]:
    """The solid strips this deck presents to wind blowing along ``axis``.

    Derived, never authored. The fascia gives its own depth and the extent of the deck it
    wraps; ``member_tags`` names the beams and rails standing in the same band, and each
    one's section depth is another strip. A reader who deepens the fascia or retypes a beam
    moves the demand, which is the whole point of deriving rather than authoring an area.

    **Callers pass the tags gathered from EVERY brace, not from this direction's braces.**
    That reads backwards and is the correction to the obvious version: what presents a face
    to wind along ``x`` is the members running along ``y``, and those are exactly the ones
    the *other* direction's braces rise into. Scoping the search to this axis's own braces
    finds only members running along the wind, whose ends present nothing, and silently
    drops every rail and beam from the area — leaving the fascia to carry a demand it is not
    alone in. The braceless caller passes the deck's own bearing beams, which has the same
    property for the same reason.
    """
    bands: list[Band] = []

    if fascia is not None:
        xs = [p.xy_m[0] / _FT for p in fascia.path]
        ys = [p.xy_m[1] / _FT for p in fascia.path]
        # Wind along y meets the deck's E-W run; wind along x meets its N-S run.
        run = (max(xs) - min(xs)) if axis == "y" else (max(ys) - min(ys))
        bands.append(Band("fascia + deck edge", ft(fascia.depth) + PLANK_BAND_FT,
                          run, fascia.tag))

    # The rail or beam each member names. Counted once per distinct member, at the member's
    # own length, because two braces on one continuous rail do not present the strip twice.
    seen: set[str] = set()
    for tag in sorted(member_tags):
        element = plan.by_tag(tag)
        if element is None or tag in seen or isinstance(element, Post):
            continue
        depth = member_depth_ft(plan, tag)
        length = member_length_ft(plan, element)
        if depth is None or length is None:
            continue
        # Only members running perpendicular to the wind present their face to it.
        if runs_along(plan, element) == axis:
            continue
        seen.add(tag)
        bands.append(Band(f"{tag} section depth", depth, length, tag))
    return tuple(bands)


def _node_xy(plan: PlanModel, tag: str) -> tuple[float, float] | None:
    element = plan.by_tag(tag) if tag else None
    position = getattr(element, "position", None)
    return position.xy_m if position is not None else None


def member_length_ft(plan: PlanModel, element: Any) -> float | None:
    start = _node_xy(plan, getattr(element, "start_node", "") or "")
    end = _node_xy(plan, getattr(element, "end_node", "") or "")
    if start is None or end is None:
        return None
    return math.dist(start, end) / _FT


def runs_along(plan: PlanModel, element: Any) -> str | None:
    start = _node_xy(plan, getattr(element, "start_node", "") or "")
    end = _node_xy(plan, getattr(element, "end_node", "") or "")
    if start is None or end is None:
        return None
    return "x" if abs(end[0] - start[0]) >= abs(end[1] - start[1]) else "y"


def member_depth_ft(plan: PlanModel, tag: str) -> float | None:
    """A beam's section depth, from its authored nominal size.

    The dressed depth, not the nominal one: a "2x8" rail presents 7.25 inches to the wind,
    not 8. ``cross_section`` is the same resolver the framing solver uses, so this cannot
    drift from the member that actually gets built.
    """
    size = getattr(plan.by_tag(tag), "size", None)
    if not size:
        return None
    from typehaus.resolve.framing.profiles import cross_section

    try:
        return float(cross_section(size).depth_m) / _FT
    except (KeyError, ValueError):
        return None


def ground_below_ft(plan: PlanModel) -> float:
    """The elevation of the ground under this structure, in the project frame.

    The sunken garden floor, not the site grade: this deck stands over an excavation, and
    z in ASCE 7's K_z is height above the ground *there*. Taking the site grade would shorten
    z by six feet and understate q_h, which is the wrong direction to be wrong in.
    """
    site = plan.project.site
    candidates = [ft(spot.elevation) for spot in site.spot_elevations]
    if site.grade is not None:
        candidates.append(ft(site.grade))
    return min(candidates) if candidates else 0.0


def nearest(plan: PlanModel, anchors: Any, kind: type) -> Any:
    """The element of ``kind`` whose plan path actually belongs to this structure.

    A whole-plan ``next(... isinstance(e, kind) ...)`` is wrong and quietly so: catlin has
    thirteen ``Railing`` elements, and the first one found is a stair-head guard on the main
    floor. Reading its base elevation as the balcony's top put the appurtenance height at
    12.8' instead of 23.0' and understated q_h by 12 %. Nothing about the finding text would
    have looked wrong. So the element is chosen by proximity to the ``anchors`` it is
    supposed to describe, which is the only relationship that holds when the plan grows.
    """
    xs = [a.position.xy_m[0] for a in anchors]
    ys = [a.position.xy_m[1] for a in anchors]
    cx, cy = (sum(xs) / len(xs), sum(ys) / len(ys))
    best, best_d = None, None
    for element in plan.all_elements():
        if not isinstance(element, kind):
            continue
        # >= 3 points: a two-point run is a drip or a flashing edge, not the plan outline
        # of a thing this structure is bounded by.
        path = getattr(element, "path", ())
        if len(path) < 3:
            continue
        px = sum(p.xy_m[0] for p in path) / len(path)
        py = sum(p.xy_m[1] for p in path) / len(path)
        distance = math.dist((px, py), (cx, cy))
        if best_d is None or distance < best_d:
            best, best_d = element, distance
    return best
