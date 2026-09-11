"""Gable-end truss + rake framing for a truss roof (→ B2).

The end positions sitting on the gable walls are not the same truss as the field:

* A gable end is not a Fink truss. It is a **drop truss**: its top chords are set down by the
  outlooker depth and the web pattern is replaced by verticals at stud spacing, so the gable
  end can be sheathed like a wall. It ships plated that way, so it is one member and one
  price row of its own — the verticals are not loose studs to bill beside it.
* The rake overhang needs framing. **Outlookers** run over the dropped gable truss, back to
  the first interior truss, and cantilever out to a **barge rafter** at the rake edge, which
  is what the rake fascia and the deck edge land on.

The shared truss geometry lives in :class:`TrussLayout` so this module and ``roof.py`` read
the same plane, bearings, and truss stations rather than each deriving their own.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.model.assembly import FramingSpec
from typehaus.model.spatial import Roof
from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import (
    cross_section,
    roof_truss_profile,
    truss_chord_depth_m,
    truss_heel_height_m,
)
from typehaus.resolve.framing.tables import DEFAULT_SPACING
from typehaus.resolve.intervals import subtract as subtract_spans
from typehaus.resolve.model import (
    FramedMember,
    ResolvedModel,
    ResolvedRoof,
    TrussShape,
)
from typehaus.resolve.roof_bearing import resolved_bearings

# 2x4 outlookers on edge at 24" o.c. carry the rake overhang; the gable truss drops by
# their depth so they pass over it and the deck stays planar.
OUTLOOKER_PROFILE = "2x4"
OUTLOOKER_SPACING = inch(24)
# Outlookers bear on the first interior truss, so the back-span is one truss bay.
BARGE_RAFTER_PROFILE = "2x6"
# ** BELOW THIS A RAKE IS BUILT CLOSE, NOT LADDERED, AND 1/2" WAS THE WRONG LINE. **
# A gable end at or under this projection is flush (#29) — no outlookers, no barge rafter and
# no drop. The bound is not "zero": it is the point where the roof deck stops being able to
# carry its own edge. A close rake cantilevers the sheathing past the gable truss and hangs
# the fascia on it, which 7/16" panel spanning 24" o.c. does without help for about half a
# foot; only past that does anyone frame a ladder. At 1/2" the engine framed 15 2x4 lookouts
# and a 2x6 barge to carry a 1 9/16" trim projection at the catlin garage's south gable —
# where the roof does not even end, it runs on as RF-BW-CANOPY — and 15 more for the canopy's
# own 3 3/8" drip edge. Neither is a thing anyone builds.
_FLUSH_RAKE_TOLERANCE_M = inch(6.0).meters
# ** A GABLE END IS A WALL LINE, AND THE ENGINE USED TO TAKE IT ON FAITH. **
# The first and last truss stations were gable ends unconditionally, whatever was or was not
# under them. That is not what a gable end frame is: SBCA's own definition is a frame "where
# the bottom chord has continuous vertical support provided by the end wall or beam", plated
# with verticals at stud spacing and no engineered web joints. It does not span, and it is
# billed on its own row (`roof_truss_profile(..., gable=True)`) at a premium over a field
# truss. Handing that member to an end station standing over open air — catlin's north-entry
# canopy, whose south end hangs 24' between two headers with no wall at all — asks a truss
# plant to quote a frame that cannot carry its own bottom chord.
#: A wall may stop this far under the plate and still be read as carrying a gable end. A
#: gable wall is built to the plate its neighbours are built to; a knee wall or a parapet
#: stub is not, and must not buy a gable frame the fabricator would then have to span.
_GABLE_PLATE_TOLERANCE_M = inch(2.0).meters
#: How much of the bearing-to-bearing span the wall (or walls, where an opening split one)
#: has to run under before it counts as continuous support. "Continuous" means the whole
#: bottom chord; the slack is for the corner geometry at each end and nothing else.
_GABLE_COVERAGE_TOLERANCE_M = inch(12.0).meters
#: A hair, in metres. Separates "the grid divided evenly" from "the bearing ran on past the
#: grid", and "this wall runs along the ridge" from "it crosses it".
_TOL_M = 1e-6
#: One member per truss: the category both the field trusses (``roof.py``) and the gable-end
#: drop trusses here emit. Consumers that used to name ``top_chord``/``bottom_chord``/
#: ``truss_web``/``truss_heel`` name this instead.
ROOF_TRUSS_CATEGORY = "roof_truss"


@dataclass(frozen=True)
class TrussLayout:
    """Everything both the interior trusses and the gable ends need from one roof.

    ``along`` runs parallel to the ridge (truss stations); ``span`` runs perpendicular to it
    (bearing to bearing). All elevations are the *final* (heel-lifted) plane.
    """

    roof_uid: str
    ridge_direction: str
    plate_top_m: float
    bear_lo: float
    bear_hi: float
    foot_lo: float          # span extent of the roof footprint (eave edge to eave edge)
    foot_hi: float
    along_lo: float         # ridge-axis extent of the bearing walls == the gable wall lines
    along_hi: float
    rake_lo: float          # ridge-axis extent of the footprint (gable wall + rake overhang)
    rake_hi: float
    eave_z_m: float
    ridge_z_m: float
    chord: str
    #: The web stock the assembly names. Nothing frames a web stick any more — the truss is
    #: one member — but the plate layout it stands for is still what a fabricator prices, so
    #: the layout keeps stating what the assembly asked for.
    web: str
    chord_depth_m: float
    #: Raised heel: plate top to top-chord underside at the bearing. The deck plane arrives
    #: already lifted by it (``roof_geometry.apply_truss_heel_lift``), so nothing here does
    #: heel arithmetic — but the truss's own drawing needs the number back.
    heel_m: float
    positions: tuple[float, ...]
    #: ``(lo, hi)`` — whether each end station is a gable end, i.e. has a wall plate running
    #: under it that this roof is allowed to sit on. Derived (``_gable_ends``), narrowed by
    #: ``Roof.gable_ends``. A False end takes a field truss, and if its station is off the
    #: spacing module it takes no truss at all — see ``build_truss_layout``.
    gable_ends: tuple[bool, bool] = (True, True)

    @property
    def span_mid(self) -> float:
        return (self.foot_lo + self.foot_hi) / 2.0

    def plan_pt(self, along: float, span: float) -> tuple[float, float]:
        return (along, span) if self.ridge_direction == "x" else (span, along)

    def plane_z(self, span: float) -> float:
        """Top of the deck plane at a span coordinate."""
        half = (self.foot_hi - self.foot_lo) / 2.0 or 1.0
        return self.ridge_z_m - (self.ridge_z_m - self.eave_z_m) * abs(span - self.span_mid) / half


#: The compass name of each ridge-axis end, ``(lo, hi)``, keyed by ridge direction. The same
#: vocabulary ``Roof.edge_overhangs`` already uses, so one roof spells its edges one way.
_END_NAMES = {"x": ("west", "east"), "y": ("south", "north")}


def _wall_supports(model: ResolvedModel, ridge_direction: str, along: float,
                   span_lo: float, span_hi: float, plate_top_m: float) -> bool:
    """Is there a wall plate running under the whole of a truss station at ``along``?

    The gable-end test, and it is deliberately about the WALL rather than about the station's
    position in the list. Several walls may answer — an overhead door or a service door
    splits a gable wall into segments, and the bottom chord over them is supported just the
    same — so their span extents are accumulated and the shortfall is what is graded.

    A wall qualifies when it runs perpendicular to the ridge (a gable wall does; a bearing
    wall parallel to it does not), sits within its own thickness of the station, and reaches
    the plate. Reaching it, not matching it: a raked gable wall carried to the underside of
    the deck supports the chord exactly as a flat one at the plate does.
    """
    ridge_ax = 0 if ridge_direction == "x" else 1
    span_ax = 1 - ridge_ax
    cuts: list[tuple[float, float]] = []
    for wall in model.walls:
        (ax, ay), (bx, by) = wall.axis
        start, end = (ax, ay), (bx, by)
        if abs(start[ridge_ax] - end[ridge_ax]) > _TOL_M:
            continue  # runs along the ridge, so it is a bearing line and not a gable line
        half_thickness = (wall.thickness_m or 0.0) / 2.0
        if abs(start[ridge_ax] - along) > half_thickness + _TOL_M:
            continue
        tops = [z for z in (wall.z1_m, wall.top_z0_m, wall.top_z1_m) if z is not None]
        if not tops or max(tops) < plate_top_m - _GABLE_PLATE_TOLERANCE_M:
            continue
        cuts.append((min(start[span_ax], end[span_ax]), max(start[span_ax], end[span_ax])))
    if not cuts:
        return False
    gaps = subtract_spans(span_lo, span_hi, cuts)
    return sum(hi - lo for lo, hi in gaps) <= _GABLE_COVERAGE_TOLERANCE_M


def _gable_ends(model: ResolvedModel, element: Roof, ridge_direction: str,
                along_lo: float, along_hi: float, span_lo: float, span_hi: float,
                plate_top_m: float) -> tuple[bool, bool]:
    """Which ends are gable ends: derived from the walls, then narrowed by the author.

    The narrowing only ever subtracts, which is what makes the field safe to hand to a plan.
    Geometry can see that a plate runs under a station; it cannot see that the plate belongs
    to a different building, which is the one thing an author has to be able to say.
    """
    lo, hi = (_wall_supports(model, ridge_direction, along, span_lo, span_hi, plate_top_m)
              for along in (along_lo, along_hi))
    if element.gable_ends is None:
        return lo, hi
    allowed = {name.lower() for name in element.gable_ends}
    lo_name, hi_name = _END_NAMES.get(ridge_direction, _END_NAMES["y"])
    return lo and lo_name in allowed, hi and hi_name in allowed


def build_truss_layout(
    model: ResolvedModel, roof: ResolvedRoof, spec: FramingSpec
) -> TrussLayout | None:
    """Derive the shared truss geometry, or ``None`` if the bearing line is unresolvable."""
    element = model.plan.by_tag(roof.tag)
    if not isinstance(element, Roof):
        return None
    span_ax = 1 if roof.ridge_direction == "x" else 0
    ridge_ax = 1 - span_ax
    bearings: list[tuple[float, float]] = []  # (span coordinate, plate top z)
    along_lo = along_hi = None
    for bearing in resolved_bearings(model, element.bearing_refs):
        (ax, ay), (bx, by) = bearing.axis
        span_coord = ay if span_ax == 1 else ax
        r0, r1 = (ay, by) if ridge_ax == 1 else (ax, bx)
        along_lo = min(r0, r1) if along_lo is None else min(along_lo, r0, r1)
        along_hi = max(r0, r1) if along_hi is None else max(along_hi, r0, r1)
        bearings.append((span_coord, bearing.z1_m))
    if along_lo is None or along_hi is None or len(bearings) < 2:
        return None
    bearings.sort()

    span_vals = [point[span_ax] for point in roof.footprint]
    along_vals = [point[ridge_ax] for point in roof.footprint]
    spacing = (spec.spacing or DEFAULT_SPACING).meters
    count = int(round((along_hi - along_lo) / spacing))
    positions = [min(along_hi, along_lo + index * spacing) for index in range(count + 1)]
    if positions[-1] < along_hi - 1e-9:
        positions.append(along_hi)

    gable_ends = _gable_ends(model, element, roof.ridge_direction, along_lo, along_hi,
                             bearings[0][0], bearings[-1][0], max(z for _, z in bearings))
    # ** AN OFF-MODULE END STATION IS A GABLE LINE OR IT IS NOTHING. **
    # The last station is forced onto ``along_hi`` so a gable wall never ends up with the
    # truss field stopping short of it. Where that end is NOT a gable line, the tip is just
    # the end of a bearing that ran on past its truss field — catlin's canopy headers carry
    # 8" past their north columns so the deck reaches the garage wall — and standing a truss
    # out of module on it is an invention. Dropping it is safe by construction: ``count`` is
    # a ROUND, so the last on-module station is within one spacing of ``along_hi`` and the
    # bay left behind is never longer than an ordinary one.
    residue = (positions[-1] - along_lo) % spacing
    off_module = min(residue, spacing - residue) > _TOL_M
    if not gable_ends[1] and off_module and len(positions) > 1:
        positions.pop()

    chord = spec.chord_member or spec.member
    web = spec.web_member or "2x4"
    return TrussLayout(
        roof_uid=roof.uid, ridge_direction=roof.ridge_direction,
        plate_top_m=max(z for _, z in bearings),
        bear_lo=bearings[0][0], bear_hi=bearings[-1][0],
        foot_lo=min(span_vals), foot_hi=max(span_vals),
        along_lo=along_lo, along_hi=along_hi,
        rake_lo=min(along_vals), rake_hi=max(along_vals),
        eave_z_m=roof.eave_z_m, ridge_z_m=roof.ridge_z_m,
        chord=chord, web=web,
        chord_depth_m=truss_chord_depth_m(spec),
        heel_m=truss_heel_height_m(spec),
        positions=tuple(positions),
        gable_ends=gable_ends,
    )


def is_gable_end_position(layout: TrussLayout, index: int) -> bool:
    """Does this station take a gable-end frame rather than a field truss?

    Only the two end stations can, and only where ``_gable_ends`` found a plate under them.
    An end station over open air takes an ordinary field truss, which is the member that
    actually spans bearing to bearing.
    """
    if index == 0:
        return layout.gable_ends[0]
    return index == len(layout.positions) - 1 and layout.gable_ends[1]


def truss_member(layout: TrussLayout, pos: float, key: str,
                 drop: float = 0.0, gable: bool = False) -> FramedMember:
    """A whole shop-fabricated truss as **one** member — the floor-truss precedent.

    A truss is engineered, plated, delivered and set as one assembly, and that is what is
    ordered and priced, so it is one member here rather than the 8-10 chord/web/heel sticks
    this used to emit. Where those sticks went:

    * **quantities** — the BOM bills one ``"<span> roof truss"`` per truss at its span (the
      dimension a truss plant quotes on), not the sum of its lumber. ``prices.toml`` carries
      the matching per-lineal-foot-of-span rate.
    * **geometry** — the member's envelope is bearing to bearing in plan and plate top to
      ridge in elevation. The chords, webs and heel are the fabricator's plate layout, which
      no model here holds; the viewer draws a conventional fink inside this envelope
      (``ui/src/three/roofTruss.ts``), the way it already does for a floor truss.

    ``drop`` is the gable-end set-down that lets the outlookers pass over (``roof_gable``);
    a field truss takes 0.0. ``gable`` bills it as the drop truss it is — the plant plates
    the verticals in, so the gable end is one purchased assembly and not a truss plus a
    bundle of loose studs.

    The overhang TAILS are outside the member: they run past the bearing to the eave, and
    putting the member's ends out there would move the bearing ends the uplift take-off ties
    off the wall they land on. They travel on ``TrussShape`` instead, with the heel, so the
    viewer draws the truss the roof actually has.
    """
    span = abs(layout.bear_hi - layout.bear_lo)
    return FramedMember(
        layout.roof_uid, key, ROOF_TRUSS_CATEGORY, roof_truss_profile(span, gable=gable),
        layout.plan_pt(pos, layout.bear_lo), layout.plan_pt(pos, layout.bear_hi),
        layout.plate_top_m, layout.ridge_z_m - drop, span,
        truss=TrussShape(
            heel_m=layout.heel_m,
            tail_lo_m=max(0.0, layout.bear_lo - layout.foot_lo),
            tail_hi_m=max(0.0, layout.foot_hi - layout.bear_hi),
            gable=gable,
        ),
    )


def gable_end_members(layout: TrussLayout, index: int, key: str) -> tuple[FramedMember, ...]:
    """The full gable end at truss station ``index``: drop truss + rake framing."""
    station = layout.positions[index]
    outward = -1.0 if index == 0 else 1.0
    rake_edge = layout.rake_lo if index == 0 else layout.rake_hi
    overhang = abs(rake_edge - station)
    drop = cross_section(OUTLOOKER_PROFILE).depth_m if overhang > _FLUSH_RAKE_TOLERANCE_M else 0.0
    # Truss stations come from the bearing walls' axes, which lie on the sheathing plane.
    # An interior truss straddles its station, but the gable truss's *outboard face* is that
    # plane — it is what the gable sheathing lands on — so it sits half a chord inboard.
    pos = station - outward * cross_section(layout.chord).width_m / 2.0
    members: list[FramedMember] = [_drop_truss(layout, pos, key, drop)]
    if overhang > _FLUSH_RAKE_TOLERANCE_M:
        members.extend(_outlookers(layout, pos, key, rake_edge, drop, outward))
        members.extend(_barge_rafters(layout, key, rake_edge))
    return tuple(members)


def _drop_truss(layout: TrussLayout, pos: float, key: str, drop: float) -> FramedMember:
    """The gable-end drop truss, as one fabricated member (see :func:`truss_member`)."""
    return truss_member(layout, pos, key, drop=drop, gable=True)


def _outlookers(
    layout: TrussLayout, pos: float, key: str, rake_edge: float, drop: float, outward: float
) -> tuple[FramedMember, ...]:
    """Ladder framing over the dropped gable truss, cantilevering to the barge rafter.

    Each outlooker bears on the first interior truss (one bay back), passes over the gable
    truss, and lands on the barge rafter — the standard rake detail a lookout-less overhang
    cannot reproduce.
    """
    back_span = abs(layout.positions[1] - layout.positions[0]) if len(layout.positions) > 1 else 0.0
    inboard = pos - outward * back_span
    spacing = OUTLOOKER_SPACING.meters
    count = int((layout.foot_hi - layout.foot_lo) / spacing)
    spans = [layout.foot_lo + step * spacing for step in range(count + 1)]
    if spans[-1] < layout.foot_hi - 1e-9:
        spans.append(layout.foot_hi)
    members: list[FramedMember] = []
    for step, span in enumerate(spans):
        top = layout.plane_z(span)
        members.append(FramedMember(
            layout.roof_uid, f"{key}-outlooker-{step:03d}", "outlooker", OUTLOOKER_PROFILE,
            layout.plan_pt(inboard, span), layout.plan_pt(rake_edge, span),
            top - drop, top, abs(rake_edge - inboard),
            connection="rake:outlooker-over-drop-truss",
        ))
    return tuple(members)


def _barge_rafters(layout: TrussLayout, key: str, rake_edge: float) -> tuple[FramedMember, ...]:
    """The sloped rake member at the overhang edge that the rake fascia lands on."""
    depth = cross_section(BARGE_RAFTER_PROFILE).depth_m
    apex = layout.plan_pt(rake_edge, layout.span_mid)
    rise = layout.ridge_z_m - layout.eave_z_m
    return tuple(FramedMember(
        layout.roof_uid, f"{key}-barge-{side}", "barge_rafter", BARGE_RAFTER_PROFILE,
        layout.plan_pt(rake_edge, foot), apex,
        layout.eave_z_m - depth, layout.eave_z_m, math.hypot(layout.span_mid - foot, rise),
        z0_end_m=layout.ridge_z_m - depth, z1_end_m=layout.ridge_z_m,
    ) for side, foot in (("lo", layout.foot_lo), ("hi", layout.foot_hi)))
