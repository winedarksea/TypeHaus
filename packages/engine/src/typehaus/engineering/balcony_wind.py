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

from typehaus.model.structure import Post
from typehaus.wind import ASD_WIND_FACTOR
from typehaus.wind_tables import GUST_EFFECT_RIGID

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


def deck_edge_band(deck: Any, axis: str) -> Band | None:
    """A deck's OWN edge, where no fascia wraps it: joist depth plus the decking, over the
    sheet's run across the wind. A fascia belonging to some other deck is not this edge —
    catlin's landing read ``TR-SG-FASCIA`` (21.5' x 0.75') until 2026-09-21."""
    from typehaus.resolve.framing.profiles import cross_section

    outline = deck.subfloor_outline or deck.outline
    try:
        joist = float(cross_section(deck.joists.member).depth_m) / _FT
    except (KeyError, ValueError):
        return None
    board = ft(deck.subfloor.thickness) if getattr(deck, "subfloor", None) else 0.0
    xs = [p.xy_m[0] / _FT for p in outline]
    ys = [p.xy_m[1] / _FT for p in outline]
    run = (max(xs) - min(xs)) if axis == "y" else (max(ys) - min(ys))
    return Band("deck edge (joist + decking)", joist + board, run, deck.tag)


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


#: Points a candidate's ``path`` needs before :func:`nearest` will consider it, by element
#: kind. The default of 3 rejects a two-point run as a drip/flashing edge; a ``Railing`` is
#: exempt because a guard is routinely one straight leg (see :func:`nearest`).
_MIN_PATH_POINTS = {"Railing": 2}


def nearest(plan: PlanModel, anchors: Any, kind: type, storey: str | None = None) -> Any:
    """The element of ``kind`` whose plan path actually belongs to this structure.

    A whole-plan ``next(... isinstance(e, kind) ...)`` is wrong and quietly so: catlin has
    thirteen ``Railing`` elements, and the first one found is a stair-head guard on the main
    floor. Reading its base elevation as the balcony's top put the appurtenance height at
    12.8' instead of 23.0' and understated q_h by 12 %. Nothing about the finding text would
    have looked wrong. So the element is chosen by proximity to the ``anchors`` it is
    supposed to describe, which is the only relationship that holds when the plan grows.

    **``storey`` is what stops proximity from being the only relationship**, and it is not a
    refinement — it is a correctness fix. Plan-centroid distance cannot tell a guard one
    storey up from a guard directly under it, and on 2026-09-03 it stopped trying: opening a
    3'-0" doorway in ``RL-SG-PORCH``'s east leg for the porch stair moved that guard's path
    centroid 9" south, close enough to the balcony's cast columns to beat ``RL-SG-BALCONY``
    by 8". The porch guard's base is +0'-1" and the balcony's is +10'-0", so q_h fell 11 %
    and every corner column's base moment with it — a change of *demand* caused by shortening
    an unrelated railing. Filed on the structure's own storey, the two cannot be confused.

    The filter is not applied when it would return nothing: a house that files its guards on
    a storey other than its deck's still gets the historical proximity answer rather than a
    silent ``None`` that reads as "no guard here".

    ** A GUARD MAY BE ONE STRAIGHT LEG, AND THE THREE-POINT GATE USED TO DENY IT. ** The
    ``len(path) < 3`` rule below is written for a ``Fascia`` — a two-point run there really is
    a drip or a flashing edge rather than the outline of a structure. A ``Railing`` is not
    that: eleven of catlin's thirteen guards are single straight runs, and only
    ``RL-SG-PORCH`` and ``RL-SG-BALCONY`` turn a corner.
    #
    Applying the gate to a Railing had a consequence that stayed hidden while every structure
    shared the house's storey keys: the north entry's landing piers took their base moment
    from ``RL-SG-PORCH``, the court porch guard forty feet away, because it was the
    ONLY railing filed on ``main`` that cleared three points. Its base is +0'-1" where the
    entry's is -2'-10", so the demand those four piers were graded on described a different
    structure at a different elevation. Giving the entry its own building made the borrowing
    visible — the entry's own guards are two-point runs, so the gate left it with no guard at
    all and the piers silently published axial-only, dropping the state that governed them.
    Neither answer was right; the gate is what was wrong.
    """
    xs = [a.position.xy_m[0] for a in anchors]
    ys = [a.position.xy_m[1] for a in anchors]
    cx, cy = (sum(xs) / len(xs), sum(ys) / len(ys))
    on_storey = ({id(e) for e in plan.storey_elements(storey) if isinstance(e, kind)}
                 if storey is not None else set())
    best, best_d = None, None
    for element in plan.all_elements():
        if not isinstance(element, kind):
            continue
        if on_storey and id(element) not in on_storey:
            continue
        # A two-point run is a drip or a flashing edge rather than a plan outline — for a
        # Fascia. For a Railing it is the ordinary case, and a guard is still a guard when it
        # does not turn a corner. See the block in the docstring.
        path = getattr(element, "path", ())
        if len(path) < _MIN_PATH_POINTS.get(kind.__name__, 3):
            continue
        px = sum(p.xy_m[0] for p in path) / len(path)
        py = sum(p.xy_m[1] for p in path) / len(path)
        distance = math.dist((px, py), (cx, cy))
        if best_d is None or distance < best_d:
            best, best_d = element, distance
    return best

# --- what stands on the deck and was left out of the bands above (review B-06) ------------

def guard_band(plan: PlanModel, axis: str, guard: Any) -> Band | None:
    """The guard's solid share across the wind: balusters at the authored gap, the two rails
    (1-1/2" deep each, taken) and the posts, over the plan run presented to ``axis``. A bound,
    at the same C_f ceiling as every other band; the guard's centroid is the lever."""
    if guard is None or len(guard.path) < 2:
        return None
    index = 0 if axis == "y" else 1     # wind along y meets a leg's E-W extent
    legs = [(a, b) for a, b in zip(guard.path, guard.path[1:], strict=False)
            if abs(b.xy_m[index] - a.xy_m[index]) > 1e-6]
    run = sum(abs(b.xy_m[index] - a.xy_m[index]) for a, b in legs) / _FT
    rtype = next((t for t in plan.library.railing_types if t.tag == getattr(guard, "type_ref", "")),
                 None)
    width = ft(rtype.baluster_width) if rtype is not None and rtype.baluster_width else 0.0
    gap = ft(guard.baluster_spacing) if guard.baluster_spacing is not None else 0.0
    solidity = min(1.0, width / (width + gap)) if width + gap > 0.0 else 1.0
    height = ft(guard.height)
    # The posts stand in the same legs, one every ``post_spacing`` and one at each end.
    post_ft = _nominal_in(getattr(guard, "post_size", "")) / 12.0
    spacing = ft(guard.post_spacing) if getattr(guard, "post_spacing", None) else 0.0
    posts = sum(math.ceil(math.dist(a.xy_m, b.xy_m) / _FT / spacing) + 1
                for a, b in legs) if spacing > 0.0 else 0
    area_sf = run * (solidity * height + 2.0 * 0.125) + posts * post_ft * height
    return Band(f"{guard.tag} balusters (solidity {solidity:.2f}), rails and {posts} posts",
                height, area_sf / height, guard.tag)


def _nominal_in(size: str) -> float:
    """``"3x3"`` -> 3.0, the post's face in inches (nominal, the product's tube)."""
    try:
        return float(str(size).lower().split("x")[0])
    except ValueError:
        return 0.0


def column_bands(columns: Any) -> tuple[Band, ...]:
    """Each cast column's own face: its diameter by the height of its SHAFT (the resolved
    solid, which ends under the beam). ``columns`` are ``(tag, diameter_ft, shaft_ft)``."""
    return tuple(Band(f"{tag} shaft", height, diameter, tag) for tag, diameter, height in columns)


def plank_edge_band(deck: Any, axis: str) -> Band | None:
    """The 1-1/2" plank edge above the fascia, over the deck's run across the wind."""
    outline = deck.subfloor_outline or deck.outline
    if not getattr(deck, "subfloor", None):
        return None
    xs = [p.xy_m[0] / _FT for p in outline]
    ys = [p.xy_m[1] / _FT for p in outline]
    run = (max(xs) - min(xs)) if axis == "y" else (max(ys) - min(ys))
    return Band("plank edge above the fascia", ft(deck.subfloor.thickness), run, deck.tag)


def curtain_bands(plan: PlanModel, axis: str) -> tuple[Band, ...]:
    """The porch's closed enclosure curtains, hung on the balcony joists. HALF a panel's load
    reaches the top track (the other half goes to the floor), so the band carries half the
    drop. The face across the wind is the whole enclosure's extent — the straight runs AND the
    corner curves that join them, which project past the straight track. A closed enclosure's
    windward and leeward panels are one net C_f, so one face counts. Closed is the design case:
    the enclosure is in use in spring and autumn (``notes/porch_enclosure.md``)."""
    from typehaus.model.spatial import Furniture

    types = {t.tag: t for t in plan.library.furniture_types}
    low, high, drop = math.inf, -math.inf, 0.0
    index = 0 if axis == "y" else 1          # wind along y meets the enclosure's x extent
    found = []
    for element in plan.all_elements():
        if not isinstance(element, Furniture) or element.position is None:
            continue
        ftype = types.get(element.type_ref)
        track = getattr(ftype, "curtain_track", None)
        if track is None or not track.outdoor_hardware:
            continue
        turn = element.rotation.radians if element.rotation is not None else 0.0
        half = ft(ftype.footprint[0]) / 2.0
        centre = element.position.xy_m[index] / _FT
        reach = half * abs(math.cos(turn) if index == 0 else math.sin(turn))
        low, high = min(low, centre - reach), max(high, centre + reach)
        drop = max(drop, ft(element.mount.elevation) if element.mount.elevation is not None
                   else 0.0)
        found.append(element.tag)
    if not found:
        return ()
    # The curves each stand in for about 8" of both legs (porch_enclosure.md): the face reaches
    # the flank tracks' lines, which the straight run stops short of.
    return (Band("porch curtains, top-track half (straight runs and corner curves)",
                 drop / 2.0, _enclosure_face_ft(plan, axis, (low, high)), ",".join(found)),)


def _enclosure_face_ft(plan: PlanModel, axis: str, straight: tuple[float, float]) -> float:
    """The enclosure's extent across the wind: the straight runs' span, widened to the lines
    of the tracks that run the other way (the flanks), which the corner curves join."""
    from typehaus.model.spatial import Furniture

    types = {t.tag: t for t in plan.library.furniture_types}
    low, high = straight
    index = 0 if axis == "y" else 1
    for element in plan.all_elements():
        if not isinstance(element, Furniture) or element.position is None:
            continue
        track = getattr(types.get(element.type_ref), "curtain_track", None)
        if track is None or not track.outdoor_hardware:
            continue
        at = element.position.xy_m[index] / _FT
        low, high = min(low, at), max(high, at)
    return high - low
