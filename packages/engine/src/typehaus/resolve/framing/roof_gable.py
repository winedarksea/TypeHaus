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
# Below this the gable end is flush (zero rake overhang, #29) — no outlookers, no barge
# rafter, and no drop, because there is nothing cantilevering past the gable wall.
_FLUSH_RAKE_TOLERANCE_M = inch(0.5).meters
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

    @property
    def span_mid(self) -> float:
        return (self.foot_lo + self.foot_hi) / 2.0

    def plan_pt(self, along: float, span: float) -> tuple[float, float]:
        return (along, span) if self.ridge_direction == "x" else (span, along)

    def plane_z(self, span: float) -> float:
        """Top of the deck plane at a span coordinate."""
        half = (self.foot_hi - self.foot_lo) / 2.0 or 1.0
        return self.ridge_z_m - (self.ridge_z_m - self.eave_z_m) * abs(span - self.span_mid) / half


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
    )


def is_gable_end_position(layout: TrussLayout, index: int) -> bool:
    """The first and last truss stations sit on the gable walls."""
    return index in (0, len(layout.positions) - 1)


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
