"""Gable-end truss + rake framing for a truss roof (→ B2).

The end positions sitting on the gable walls are not the same truss as the field:

* A gable end is not a Fink truss. It is a **drop truss**: its top chords are set down by the
  outlooker depth and the web pattern is replaced by vertical **gable studs** at stud
  spacing, so the gable end can be sheathed like a wall.
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
from typehaus.resolve.framing.profiles import cross_section, truss_chord_depth_m
from typehaus.resolve.framing.tables import DEFAULT_SPACING
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedRoof

# Vertical gable studs infill the end truss at ordinary stud spacing so the gable end
# sheathes like a wall rather than reading as an exposed truss.
GABLE_STUD_SPACING = inch(16)
GABLE_STUD_PROFILE = "2x4"
# 2x4 outlookers on edge at 24" o.c. carry the rake overhang; the gable truss drops by
# their depth so they pass over it and the deck stays planar.
OUTLOOKER_PROFILE = "2x4"
OUTLOOKER_SPACING = inch(24)
# Outlookers bear on the first interior truss, so the back-span is one truss bay.
BARGE_RAFTER_PROFILE = "2x6"
# Below this the gable end is flush (zero rake overhang, #29) — no outlookers, no barge
# rafter, and no drop, because there is nothing cantilevering past the gable wall.
_FLUSH_RAKE_TOLERANCE_M = inch(0.5).meters
_MIN_GABLE_STUD_M = inch(1.5).meters


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
    web: str
    chord_depth_m: float
    web_depth_m: float
    positions: tuple[float, ...]

    @property
    def span_mid(self) -> float:
        return (self.foot_lo + self.foot_hi) / 2.0

    @property
    def truss_orient(self) -> tuple[float, float]:
        """Plan axis a truss-plane vertical member (heel block, king post) follows."""
        return (1.0, 0.0) if self.ridge_direction == "x" else (0.0, 1.0)

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
    for tag in element.bearing_refs:
        wall = model.wall(tag)
        if wall is None:
            continue
        (ax, ay), (bx, by) = wall.axis
        span_coord = ay if span_ax == 1 else ax
        r0, r1 = (ay, by) if ridge_ax == 1 else (ax, bx)
        along_lo = min(r0, r1) if along_lo is None else min(along_lo, r0, r1)
        along_hi = max(r0, r1) if along_hi is None else max(along_hi, r0, r1)
        bearings.append((span_coord, wall.z1_m))
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
        web_depth_m=cross_section(web).depth_m,
        positions=tuple(positions),
    )


def is_gable_end_position(layout: TrussLayout, index: int) -> bool:
    """The first and last truss stations sit on the gable walls."""
    return index in (0, len(layout.positions) - 1)


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
    members = list(_drop_truss(layout, pos, key, drop))
    members.extend(_gable_studs(layout, pos, key, drop))
    if overhang > _FLUSH_RAKE_TOLERANCE_M:
        members.extend(_outlookers(layout, pos, key, rake_edge, drop, outward))
        members.extend(_barge_rafters(layout, key, rake_edge))
    return tuple(members)


def _drop_truss(
    layout: TrussLayout, pos: float, key: str, drop: float
) -> tuple[FramedMember, ...]:
    """Bottom chord + the two dropped top chords of a gable-end truss."""
    cd = layout.chord_depth_m
    apex = layout.plan_pt(pos, layout.span_mid)
    ridge_top = layout.ridge_z_m - drop
    eave_top = layout.eave_z_m - drop
    rise = layout.ridge_z_m - layout.eave_z_m
    chords = [FramedMember(
        layout.roof_uid, f"{key}-bc", "bottom_chord", layout.chord,
        layout.plan_pt(pos, layout.bear_lo), layout.plan_pt(pos, layout.bear_hi),
        layout.plate_top_m, layout.plate_top_m + cd, abs(layout.bear_hi - layout.bear_lo),
    )]
    for side, foot in (("lo", layout.foot_lo), ("hi", layout.foot_hi)):
        chords.append(FramedMember(
            layout.roof_uid, f"{key}-tc-{side}", "top_chord", layout.chord,
            layout.plan_pt(pos, foot), apex, eave_top - cd, eave_top,
            math.hypot(layout.span_mid - foot, rise),
            z0_end_m=ridge_top - cd, z1_end_m=ridge_top,
        ))
    return tuple(chords)


def _gable_studs(
    layout: TrussLayout, pos: float, key: str, drop: float
) -> tuple[FramedMember, ...]:
    """Vertical studs infilling the end truss, bottom chord → dropped top chord."""
    spacing = GABLE_STUD_SPACING.meters
    base = layout.plate_top_m + layout.chord_depth_m
    count = int((layout.bear_hi - layout.bear_lo) / spacing)
    studs: list[FramedMember] = []
    for step in range(count + 1):
        span = layout.bear_lo + step * spacing
        top = layout.plane_z(span) - drop - layout.chord_depth_m
        if top - base < _MIN_GABLE_STUD_M:
            continue  # the chords already meet here; a sliver stud is not a member
        point = layout.plan_pt(pos, span)
        studs.append(FramedMember(
            layout.roof_uid, f"{key}-gable-stud-{step:03d}", "stud", GABLE_STUD_PROFILE,
            point, point, base, top, top - base, orient=layout.truss_orient,
        ))
    return tuple(studs)


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
