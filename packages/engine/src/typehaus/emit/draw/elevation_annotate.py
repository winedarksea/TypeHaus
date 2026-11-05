"""The elevation sheet's ground line and right-hand annotation margin (→ 30 §Elevations).

Split out of :mod:`elevation` when that module went past the 500-line ceiling
(``AGENTS.md`` §1.1). Everything here is *sheet* work rather than *building* work: where the
ground goes, what the facade is made of, and what the horizontal datums are called.

The layout rule these three share is that nothing places itself blind: a fixed stagger from
each wall top piles material callouts on this house, and GRADE, GARAGE FLOOR and MAIN
FLOOR — inches apart here — would print on top of one another at their raw elevations. They
are one column instead, lettered in points at the sheet's scale, boxed with air, and run through
:func:`annotate.dodge` against each other. A label that has been dodged off its own datum
keeps a leader back to the marker, which is why these are ``Leader`` nodes and not bare
``Text``.

Two halves of this are **not** elevation-specific and are public for that reason: the
grade profile's sampled points (:func:`grade_profile_points`, :func:`emit_grade_hatch`)
and the level datum ladder (:class:`Level`, :func:`merged_levels`, :func:`label_at`,
:func:`emit_level_markers`, :func:`emit_level_dimensions`). A building section cuts the
same ground and stands against the same datums, and
:mod:`typehaus.emit.draw.section_annotate` draws them by calling these rather than by
keeping a second copy that would drift.
"""

from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry
from shapely.ops import nearest_points

from typehaus.emit.draw.annotate import LabelSpec, PlacedLabel, dodge, label_box
from typehaus.emit.draw.elevation_project import (
    ElevationView,
    VisiblePiece,
    split_at_grade,
)
from typehaus.emit.draw.lineweights import CUT_HEAVY, LIGHT
from typehaus.emit.draw.scene import (
    ArchDimension,
    Leader,
    NamedPoint,
    Polyline,
    SceneBuilder,
    Symbol,
    Text,
)
from typehaus.emit.draw.typography import TEXT_PT, feet_inches_8th, model_in_per_pt
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel

#: The symmetric band a **section** captures spot elevations in, either side of the cut
#: line. A cut has soil on both sides of it, so 10' each way is the right reach there.
_CAPTURE_BAND_M = 3.048  # 10'

#: How far *outboard* of a facade a spot elevation still describes that facade's ground
#: line. R401.3 authors a second ring ~9' out, perpendicular to the wall and 6" lower — a
#: station about the fall away from the building, not a station along it. Projected onto the
#: wall line it drew a 4" V in the middle of the south elevation. 4' keeps the near ring and
#: drops the far one.
_FACADE_GRADE_BAND_M = 1.2192  # 4'

#: ...and how far *inboard* (behind the facade plane, into the building). Only the slop
#: between the cladding face and a station authored a foot or two off the wall, never
#: enough to reach a courtyard floor or the far side of the house.
_INBOARD_SLACK_M = 0.3048  # 12"

#: How far past the building the ground line runs on, and the air before the first
#: annotation column.
_EXTEND_M = 0.6096  # 24"

#: The scale elevation lettering is reserved at when no sheet scale is given: the set's
#: ledger scale (C7-E5). ``framed_elevations`` lays the four sheets out at the one scale
#: they all fit, so a sheet reserves exactly what it prints.
ELEVATION_SCALE = 0.09375  # 3/32" = 1'-0"

#: Printed size of every annotation label, points. Same pattern as ``section_annotate``:
#: lettering is paper, and model-inch lettering printed at ``MIN_PT`` past its reservation.
ANNO_PT = TEXT_PT


def anno_in(scale: float) -> float:
    """``ANNO_PT`` as model inches at ``scale`` — what the dodge boxes and bounds measure."""
    return ANNO_PT * model_in_per_pt(scale)


#: The lettering as model inches at :data:`ELEVATION_SCALE` (frameless renders and tests).
ANNO_HEIGHT_IN = anno_in(ELEVATION_SCALE)

#: Air reserved above and below a label at that scale: ``dodge`` separates boxes that
#: overlap, and two labels a hair apart print as one smear.
LABEL_PAD_IN = ANNO_HEIGHT_IN * 0.7

#: Air between the three right-hand columns (callouts, dimension string, datum labels),
#: paper inches. Column positions derive from what lands in each; this is the slack.
_COLUMN_GAP_PAPER_IN = 0.15

#: Paper the dimension string's rotated 9.5 pt text takes left of its line.
_DIM_TEXT_PAPER_IN = 0.18

#: Shortest rung the vertical dimension string draws, paper inches (C7-E5). A rung is read
#: through its own 9.5 pt string between two arrowheads; "2'-10"" is ~0.5" of paper, so
#: under this the string overprints its neighbour. Merging keeps the chain summing.
MIN_RUNG_PAPER_IN = 0.6

#: The model-inch floor for a frameless caller: under 2'-0" no scale makes a rung legible.
_MIN_DIM_IN = 24.0

#: Smallest visible surface worth a material callout. A wall whose cladding is occluded can
#: still leak a 1" strip of its stud layer past its neighbour, and a leader reading "SPF"
#: pointing at a sliver says something false about what the building is finished in.
_MIN_CALLOUT_AREA_M2 = 1.0


def grade_datum(model: ResolvedModel) -> float:
    """The flat ``Site.grade`` datum — what "below grade" is measured against."""
    site = model.plan.project.site
    return site.grade.meters if site.grade is not None else 0.0


def grade_profile_points(model: ResolvedModel, view: ElevationView, plane_depth: float,
                         lo_u: float, hi_u: float, *,
                         band_m: float = _CAPTURE_BAND_M,
                         inboard_slack_m: float = _CAPTURE_BAND_M,
                         ) -> list[tuple[float, float]]:
    """The (u, z) ground profile in **metres**, sampled for one viewing direction.

    ``plane_depth`` is the depth of the plane the ground is being drawn against — a
    facade's dominant cladding plane, or a section's cut station. A spot elevation counts
    when it lies between ``band_m`` *outboard* of that plane and ``inboard_slack_m``
    *behind* it, and when it reads ``kind == "grade"``: the top of a sunken-court floor is
    an elevation of a structure, not of the soil, and a ground line drawn through it dives
    into a courtyard that is nowhere near the wall.

    The two reaches are separate because the two callers are. A **section** cuts earth on
    both sides of the line and takes the symmetric default. An **elevation** looks at a
    wall: ground outboard of it is the ground being drawn, ground far behind it is the far
    side of the house, so :func:`emit_grade_profile` passes the tighter facade pair.

    Fewer than two captured spots is not a failure — it is a flat ground line, at the one
    spot's own elevation, or at ``Site.grade`` when there is none at all (decision 2).
    Extended flat 24" past the building either way.
    """
    site = model.plan.project.site

    captured: list[tuple[float, float, float]] = []
    for spot in site.spot_elevations:
        if spot.kind != "grade":
            continue
        x, y = spot.position.xy_m
        offset = view.depth_of(x, y) - plane_depth
        if -band_m <= offset <= inboard_slack_m:
            captured.append((view.u_of(x, y), spot.elevation.meters, abs(offset)))
    # Two stations at the same u is a tie the drawing has to break, and it must not break it
    # by authoring order: sorting on |offset| makes the one nearest the plane win, which is
    # the one describing this ground.
    captured.sort(key=lambda item: (item[0], item[2]))
    deduped: list[tuple[float, float]] = []
    for u, z, _offset in captured:
        if deduped and abs(u - deduped[-1][0]) < 1e-6:
            continue
        deduped.append((u, z))

    if len(deduped) < 2:
        grade_z = deduped[0][1] if deduped else grade_datum(model)
        points = [(lo_u - _EXTEND_M, grade_z), (hi_u + _EXTEND_M, grade_z)]
    else:
        sample_us = sorted({lo_u - _EXTEND_M, hi_u + _EXTEND_M,
                            *(u for u, _ in deduped if lo_u - _EXTEND_M <= u <= hi_u + _EXTEND_M)})
        points = [(u, interpolate_profile(deduped, u)) for u in sample_us]
    return points


def emit_grade_profile(b: SceneBuilder, model: ResolvedModel, view: ElevationView,
                        facade_depth: float, lo_u: float, hi_u: float,
                        scale: float = ELEVATION_SCALE) -> None:
    """The elevation's ground line, its hatch and its "GRADE" caption.

    Sampled against the *facade* band rather than the symmetric section one: an elevation
    draws the ground in front of one wall, and a station 9' out or 20' behind describes
    other ground.
    """
    points = grade_profile_points(model, view, facade_depth, lo_u, hi_u,
                                  band_m=_FACADE_GRADE_BAND_M,
                                  inboard_slack_m=_INBOARD_SLACK_M)
    poly = tuple((u / M_PER_IN, z / M_PER_IN) for u, z in points)
    b.add(Polyline(points=poly, layer="L-SITE-GRAD", lineweight=CUT_HEAVY))
    emit_grade_hatch(b, points)
    height = anno_in(scale)
    b.add(Text(anchor=(poly[0][0], poly[0][1] - height), content="GRADE",
               height=height, height_pt=ANNO_PT, layer="L-SITE-GRAD"))


def emit_grade_hatch(b: SceneBuilder, points: list[tuple[float, float]]) -> None:
    """45° tick hatching below the grade line (the standard grade-hatch convention)."""
    if len(points) < 2:
        return
    tick_spacing_m = 0.6096  # 24"
    u = points[0][0]
    while u <= points[-1][0]:
        z = interpolate_profile(points, u)
        b.add(Polyline(points=((u / M_PER_IN, z / M_PER_IN),
                               ((u - 0.15) / M_PER_IN, (z - 0.15) / M_PER_IN)),
                       layer="L-SITE-GRAD", lineweight=LIGHT))
        u += tick_spacing_m


def interpolate_profile(points: list[tuple[float, float]], u: float) -> float:
    """Linear interpolation along a (u, z) profile, flat outside its ends."""
    if u <= points[0][0]:
        return points[0][1]
    for (u0, z0), (u1, z1) in zip(points, points[1:], strict=False):
        if u0 <= u <= u1:
            t = 0.0 if abs(u1 - u0) < 1e-9 else (u - u0) / (u1 - u0)
            return z0 + t * (z1 - z0)
    return points[-1][1]


# --- the right-hand annotation margin ----------------------------------------------------
@dataclass(frozen=True)
class Level:
    """One horizontal datum, after coincident lines have been merged into one marker."""

    z_m: float
    labels: tuple[str, ...]


def emit_sheet_annotations(b: SceneBuilder, model: ResolvedModel,
                           facade_pieces: list[VisiblePiece], edge_u: float,
                           scale: float = ELEVATION_SCALE) -> None:
    """Material callouts and the level datum string, laid out once and dodged together.

    Placed blind — a fixed stagger for callouts, raw elevation for level labels — GRADE,
    MAIN FLOOR and GARAGE FLOOR print on top of one another on this house. One column
    instead: merged, stacked, and run through :func:`annotate.dodge` against each other.
    Lettering is ``ANNO_PT`` reserved at ``scale``, the scale the sheet prints at.
    """
    height_in = anno_in(scale)
    pad_in = height_in * 0.7
    levels = merged_levels(model)
    gap = _COLUMN_GAP_PAPER_IN * 12.0 / scale * M_PER_IN

    callout_u = edge_u + gap
    callouts = _material_callouts(facade_pieces, callout_u, grade_datum(model))
    callout_labels = [label_at(callout_u, target[1], spec.text, ANNO_PT,
                                target=target, key=spec.key, scale=scale, pad_in=pad_in)
                      for spec, target in ((spec, spec.target or (callout_u, 0.0))
                                           for spec in callouts)]

    widest = max((item.box[2] - item.box[0] for item in callout_labels), default=0.0)
    # The string's own rotated text prints LEFT of its line, so the line stands that far on.
    dim_u = callout_u + widest * M_PER_IN + gap + _DIM_TEXT_PAPER_IN * 12.0 / scale * M_PER_IN
    # Three gaps, not one: the level marker and the dimension string's own text both sit at
    # ``dim_u``, and a datum label starting a foot away printed through both of them.
    label_u = dim_u + gap
    level_labels = [
        label_at(label_u, level.z_m, level_text(level, stacked=True), ANNO_PT,
                  target=(dim_u, level.z_m), key=("level", index), scale=scale,
                  pad_in=pad_in)
        for index, level in enumerate(levels)]

    # Level labels settle first and the callouts dodge around them: a datum label has to stay
    # on its own line to mean anything, and a material note does not.
    placed_levels = dodge(level_labels)
    placed_callouts = dodge(callout_labels, fixed=tuple(item.box for item in placed_levels))

    emit_level_markers(b, levels, placed_levels, dim_u, height=height_in, height_pt=ANNO_PT)
    emit_level_dimensions(b, levels, dim_u, min_paper_in=MIN_RUNG_PAPER_IN, scale=scale)

    for placed in placed_callouts:
        anchor_u, anchor_z = placed.spec.target or placed.at
        b.add(Leader(
            anchor=NamedPoint(xy=(anchor_u / M_PER_IN, anchor_z / M_PER_IN),
                              name=str(placed.spec.key)),
            at=placed.at, to=(anchor_u / M_PER_IN, anchor_z / M_PER_IN),
            text=placed.spec.text, height=height_in, height_pt=ANNO_PT,
            layer="A-ANNO-TEXT"))


def emit_level_markers(b: SceneBuilder, levels: list[Level],
                       placed: list[PlacedLabel], dim_u: float,
                       height: float = ANNO_HEIGHT_IN,
                       height_pt: float | None = None) -> None:
    """The datum tick and its leadered caption, one per level, at column ``dim_u``.

    A label dodged off its own datum has to keep a line back to the tick or it names the
    wrong elevation, which is why these are ``Leader`` nodes. Sizing is the caller's: the
    elevation letters in model inches (``height``), a section in points (``height_pt``),
    and the writers prefer ``height_pt`` when it is set.
    """
    for level, item in zip(levels, placed, strict=True):
        b.add(Symbol(name="level-marker", insert=(dim_u / M_PER_IN, level.z_m / M_PER_IN),
                     layer="A-ANNO-SYMB"))
        b.add(Leader(anchor=NamedPoint(xy=(dim_u / M_PER_IN, level.z_m / M_PER_IN),
                                       name=level.labels[0]),
                     at=item.at, to=(dim_u / M_PER_IN, level.z_m / M_PER_IN),
                     text=item.spec.text, height=height, height_pt=height_pt,
                     layer="A-ANNO-TEXT"))


def merged_levels(model: ResolvedModel) -> list[Level]:
    """Grade, each storey's floor and top-of-plate, and the ridge — coincident lines merged."""
    named: list[tuple[str, float]] = [("GRADE", grade_datum(model))]
    # One caption per LEVEL, not per storey. A storey is a datum within one building, so four
    # of catlin's stand on the basement's: naming each produced the caption "BASEMENT FLOOR /
    # G-FOUNDATION FLOOR / COURT-LOW FLOOR / YARD-LOW FLOOR", which says four times over what
    # a datum line exists to say once. The level is named for the floor a reader knows.
    #
    # The plate is the PRIMARY storey's: an accessory building's own plate is a real datum,
    # but one a section CUT THROUGH THAT BUILDING should caption (court walls topped at grade
    # printed "BASEMENT T.O. PLATE 0'-1"").
    for primary, _here in model.plan.levels():
        named.append((f"{primary.tag.upper()} FLOOR", primary.elevation.meters))
        own = [wall for wall in model.walls if wall.storey == primary.tag]
        platform = [w.plate_top_z_m for w in own if w.plate_top_z_m is not None]
        # Under a pitched roof no wall is platform-framed; the eave plate is then the LOWEST
        # flat top (the ridge-bearing wall's soffit is not the level's plate).
        flat = [w.z1_m for w in own if w.top_z0_m is None and w.top_z1_m is None]
        plate = max(platform) if platform else (min(flat) if flat else None)
        if plate is not None:
            named.append((f"{primary.tag.upper()} T.O. PLATE", plate))
    if model.roofs:
        named.append(("RIDGE", max(roof.ridge_z_m for roof in model.roofs)))

    out: list[Level] = []
    for label, z in sorted(named, key=lambda item: item[1]):
        # Merge only what prints as one elevation. Two datums an inch apart *are* two datums,
        # and folding them under one "EL." would state a number that is wrong for one of
        # them; the dodge below is what keeps their labels off each other.
        if out and feet_inches_signed(z) == feet_inches_signed(out[-1].z_m):
            previous = out.pop()
            out.append(Level(z_m=previous.z_m, labels=previous.labels + (label,)))
            continue
        out.append(Level(z_m=z, labels=(label,)))
    return out


def level_text(level: Level, *, stacked: bool = False) -> str:
    """The datum caption; ``stacked`` puts each name and the elevation on its own line."""
    elevation = f"EL. {feet_inches_signed(level.z_m)}"
    if stacked:
        return "\n".join((*level.labels, elevation))
    return " / ".join(level.labels) + f"  {elevation}"


def label_at(u: float, z: float, text: str, height_pt: float,
             target: tuple[float, float], key: object,
             scale: float | None = None, pad_in: float = LABEL_PAD_IN) -> PlacedLabel:
    """One annotation label, boxed with air above and below so :func:`dodge` keeps it clear.

    ``dodge`` separates boxes that *overlap*; two labels a hair apart do not overlap and
    print as one smear at elevation scale. Padding the reservation is how the gap becomes
    part of what is reserved.

    ``scale`` is the paper inches per model foot the box is *reserved* at — ``None`` keeps
    the frameless convention this module has always used. A section reserves at the smaller
    of the two papers it prints on, so its column cannot collide on the tighter sheet.
    """
    at = (u / M_PER_IN, z / M_PER_IN)
    u0, z0, u1, z1 = label_box(at, text, height_pt, "left", scale)
    return PlacedLabel(spec=LabelSpec(text=text, target=target, key=key), at=at,
                       align="left", height_pt=height_pt,
                       box=(u0, z0 - pad_in, u1, z1 + pad_in))


def emit_level_dimensions(b: SceneBuilder, levels: list[Level], dim_u: float, *,
                          min_paper_in: float | None = None,
                          scale: float | None = None) -> None:
    """The stacked vertical string, chained past datums too close together to dimension.

    ``SECOND T.O. PLATE`` stands 1" above ``ATTIC FLOOR`` here, and a 1" dimension printed
    between two arrowheads that overlap each other is illegible and worthless. Skipping the
    rung rather than dropping the level keeps the chain summing: the next dimension is
    measured from the last one that was drawn, so bottom to top still adds up to the inch.

    The shortest rung is ``min_paper_in`` of paper at ``scale`` when both are given (the
    string's size is points, so legibility is a paper length), never under 2'-0".
    """
    if not levels:
        return
    minimum_in = _MIN_DIM_IN
    if min_paper_in is not None and scale is not None:
        minimum_in = max(minimum_in, min_paper_in * 12.0 / scale)
    minimum = minimum_in * M_PER_IN
    lower = levels[0]
    for upper in levels[1:]:
        if upper.z_m - lower.z_m < minimum:
            continue
        b.add(ArchDimension(
            kind="linear",
            ends=(NamedPoint(xy=(dim_u / M_PER_IN, lower.z_m / M_PER_IN),
                             name=lower.labels[0]),
                  NamedPoint(xy=(dim_u / M_PER_IN, upper.z_m / M_PER_IN),
                             name=upper.labels[0])),
            p0=(dim_u / M_PER_IN, lower.z_m / M_PER_IN),
            p1=(dim_u / M_PER_IN, upper.z_m / M_PER_IN),
            offset=6.0,
        ))
        lower = upper


def _material_callouts(facade_pieces: list[VisiblePiece], column_u: float,
                       grade_z: float) -> list[LabelSpec]:
    """One callout per distinct visible exterior *surface* material.

    Restricted to walls and roofs, and the caller has already banded the pieces to the
    facade plane. Every other family names something
    that is not a finish — a deck's plywood, a soffit's spf, a beam's LVL — and a callout
    reading "STRUCT-1-PLYWOOD" beside a standing-seam wall says nothing about what the
    building is clad in. Each leader lands on the point of its own surface nearest the
    annotation column, so a note does not draw a rule across the whole facade to reach the
    middle of the thing it names.
    """
    best: dict[str, BaseGeometry] = {}
    for piece in facade_pieces:
        material = piece.candidate.material_ref
        if material is None or piece.candidate.kind not in {"wall", "roof"}:
            continue
        # Buried surface: an elevation calls out what a person standing there can see, and
        # the leader has to land on the part of it that is above grade, not on the middle of
        # a dashed foundation outline.
        exposed = split_at_grade(piece.geometry, grade_z)[0]
        if exposed.is_empty or exposed.area < _MIN_CALLOUT_AREA_M2:
            continue
        current = best.get(material)
        if current is None or exposed.area > current.area:
            best[material] = exposed
    out: list[LabelSpec] = []
    for material, exposed in sorted(best.items(), key=lambda item: -item[1].area):
        centre = exposed.representative_point()
        anchor = nearest_points(exposed, Point(column_u, centre.y))[0]
        out.append(LabelSpec(text=_two_lines(material.upper()), target=(anchor.x, anchor.y),
                             key=material))
    return out


def _two_lines(tag: str, longest: int = 16) -> str:
    """A long tag broken at the hyphen nearest its middle: "STANDING-SEAM-LINEN-WHITE" on
    one line pushed A-203/A-204 off 3/32" (the four share one scale)."""
    cuts = [i for i, ch in enumerate(tag) if ch == "-"]
    if len(tag) <= longest or not cuts:
        return tag
    cut = min(cuts, key=lambda i: abs(i - len(tag) / 2))
    return f"{tag[:cut + 1]}\n{tag[cut + 1:]}"


def feet_inches_signed(z_m: float) -> str:
    """A level to 1/16" (F3-106): the 108 1/8" plate prints 9'-0 1/8", the slab -9'-1 7/16"."""
    return feet_inches_8th(z_m / M_PER_IN, 16)
