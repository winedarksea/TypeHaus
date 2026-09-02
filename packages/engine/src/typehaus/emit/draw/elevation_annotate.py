"""The elevation sheet's ground line and right-hand annotation margin (→ 30 §Elevations).

Split out of :mod:`elevation` when that module went past the 500-line ceiling
(``AGENTS.md`` §1.1). Everything here is *sheet* work rather than *building* work: where the
ground goes, what the facade is made of, and what the horizontal datums are called.

The layout rule these three share is that nothing places itself blind: a fixed stagger from
each wall top piles material callouts on this house, and GRADE, GARAGE FLOOR and MAIN
FLOOR — inches apart here — would print on top of one another at their raw elevations. They
are one column instead, sized in model inches, boxed with air, and run through
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

from typehaus.emit.draw import annotate
from typehaus.emit.draw.annotate import LabelSpec, PlacedLabel, dodge, label_box
from typehaus.emit.draw.elevation_project import (
    ElevationView,
    VisiblePiece,
    split_at_grade,
)
from typehaus.emit.draw.scene import (
    ArchDimension,
    Leader,
    NamedPoint,
    Polyline,
    SceneBuilder,
    Symbol,
    Text,
)
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel

#: How far to either side of the facade a spot elevation still describes this ground line.
_CAPTURE_BAND_M = 3.048  # 10'

#: How far past the building the ground line runs on, and the air before the first
#: annotation column.
_EXTEND_M = 0.6096  # 24"

#: Annotation lettering, model inches. An elevation is the largest drawing in the set —
#: forty feet across — so a smaller size (2.5") rasterises to about three pixels in
#: ``haus render``. Sized here rather than inherited so the dodge boxes and the
#: printed glyphs are the same number.
ANNO_HEIGHT_IN = 4.0

#: Air reserved above and below every annotation label, model inches. ``dodge`` separates
#: boxes that *overlap*, and two labels a hair apart do not overlap — they print as one
#: smear at elevation scale. Padding the reservation is how the gap becomes part of what is
#: reserved, and it is what makes four datums within 3'-4" of each other come out as four
#: readable lines.
LABEL_PAD_IN = ANNO_HEIGHT_IN * 0.7

#: Air between the three right-hand columns — material callouts, the vertical dimension
#: string, then the datum labels — model inches. The columns' *positions* are derived from
#: the width of what lands in each, so a long material name pushes the string over instead
#: of printing through it; this is the slack on top of that width.
#:
#: 3'-0" of it, which is more than an estimate needs, because the reservation and the print
#: are not always the same size here: ``text_extent`` reserves at the authored height, while
#: ``pdf_writer`` floors annotation at ``typography.MIN_PT`` so a raster of a forty-foot
#: elevation prints the smallest labels *larger* than they were reserved. The slack is what
#: absorbs that, and "FOUNDATION-PROTECTION-PANEL" printing through "GRADE EL. -2'-10"" is
#: what it looks like when there is none.
_COLUMN_GAP_IN = 36.0

#: Shortest rung the vertical dimension string will draw. Under 2'-0" the string's own text
#: prints between two arrowheads that are already touching; see
#: :func:`emit_level_dimensions` for why skipping the rung keeps the chain summing.
_MIN_DIM_IN = 24.0

#: Smallest visible surface worth a material callout. A wall whose cladding is occluded can
#: still leak a 1" strip of its stud layer past its neighbour, and a leader reading "SPF"
#: pointing at a sliver says something false about what the building is finished in.
_MIN_CALLOUT_AREA_M2 = 1.0


def grade_datum(model: ResolvedModel) -> float:
    """The flat ``Site.grade`` datum — what "below grade" is measured against."""
    site = model.plan.project.site
    return site.grade.meters if site.grade is not None else 0.0


def grade_profile_points(model: ResolvedModel, view: ElevationView, facade_depth: float,
                         lo_u: float, hi_u: float) -> list[tuple[float, float]]:
    """The (u, z) ground profile in **metres**, sampled for one viewing direction.

    Spot elevations within a 10' capture band of ``facade_depth``, extended flat 24" past
    the building; flat ``Site.grade`` when fewer than two spots are in band (decision 2).
    Split out of :func:`emit_grade_profile` so a section — which cuts the same ground along
    the same kind of (u, depth) frame — can draw the profile at its own lettering size.
    """
    site = model.plan.project.site

    captured: list[tuple[float, float]] = []
    for spot in site.spot_elevations:
        x, y = spot.position.xy_m
        if abs(view.depth_of(x, y) - facade_depth) <= _CAPTURE_BAND_M:
            captured.append((view.u_of(x, y), spot.elevation.meters))
    captured.sort(key=lambda item: item[0])
    deduped: list[tuple[float, float]] = []
    for u, z in captured:
        if deduped and abs(u - deduped[-1][0]) < 1e-6:
            continue  # nearest-in-band point already kept (sorted by u, first wins)
        deduped.append((u, z))

    if len(deduped) < 2:
        grade_z = grade_datum(model)
        points = [(lo_u - _EXTEND_M, grade_z), (hi_u + _EXTEND_M, grade_z)]
    else:
        sample_us = sorted({lo_u - _EXTEND_M, hi_u + _EXTEND_M,
                            *(u for u, _ in deduped if lo_u - _EXTEND_M <= u <= hi_u + _EXTEND_M)})
        points = [(u, interpolate_profile(deduped, u)) for u in sample_us]
    return points


def emit_grade_profile(b: SceneBuilder, model: ResolvedModel, view: ElevationView,
                        facade_depth: float, lo_u: float, hi_u: float) -> None:
    """The elevation's ground line, its hatch and its "GRADE" caption.

    Kept from the wireframe elevation term for term — it reads real spot elevations and it
    works; only the projection of a spot into (u, z) moved, so a mirrored view now puts the
    profile the same way round as the building it belongs to."""
    points = grade_profile_points(model, view, facade_depth, lo_u, hi_u)
    poly = tuple((u / M_PER_IN, z / M_PER_IN) for u, z in points)
    b.add(Polyline(points=poly, layer="L-SITE-GRAD", lineweight=0.7))
    emit_grade_hatch(b, points)
    b.add(Text(anchor=(poly[0][0], poly[0][1] - ANNO_HEIGHT_IN), content="GRADE",
               height=ANNO_HEIGHT_IN, layer="L-SITE-GRAD"))


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
                       layer="L-SITE-GRAD", lineweight=0.25))
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
                           facade_pieces: list[VisiblePiece], edge_u: float) -> None:
    """Material callouts and the level datum string, laid out once and dodged together.

    Placed blind — a fixed stagger for callouts, raw elevation for level labels — GRADE,
    MAIN FLOOR and GARAGE FLOOR print on top of one another on this house. One column
    instead: merged, stacked, and run through :func:`annotate.dodge` against each other.
    """
    height_pt = ANNO_HEIGHT_IN / annotate.model_in_per_pt(None)
    levels = merged_levels(model)
    gap = _COLUMN_GAP_IN * M_PER_IN

    callout_u = edge_u + gap
    callouts = _material_callouts(facade_pieces, callout_u, grade_datum(model))
    callout_labels = [label_at(callout_u, target[1], spec.text, height_pt,
                                target=target, key=spec.key)
                      for spec, target in ((spec, spec.target or (callout_u, 0.0))
                                           for spec in callouts)]

    widest = max((item.box[2] - item.box[0] for item in callout_labels), default=0.0)
    dim_u = callout_u + widest * M_PER_IN + gap
    # Three gaps, not one: the level marker and the dimension string's own text both sit at
    # ``dim_u``, and a datum label starting a foot away printed through both of them.
    label_u = dim_u + 3.0 * gap
    level_labels = [
        label_at(label_u, level.z_m, level_text(level), height_pt,
                  target=(dim_u, level.z_m), key=("level", index))
        for index, level in enumerate(levels)]

    # Level labels settle first and the callouts dodge around them: a datum label has to stay
    # on its own line to mean anything, and a material note does not.
    placed_levels = dodge(level_labels)
    placed_callouts = dodge(callout_labels, fixed=tuple(item.box for item in placed_levels))

    emit_level_markers(b, levels, placed_levels, dim_u)
    emit_level_dimensions(b, levels, dim_u)

    for placed in placed_callouts:
        anchor_u, anchor_z = placed.spec.target or placed.at
        b.add(Leader(
            anchor=NamedPoint(xy=(anchor_u / M_PER_IN, anchor_z / M_PER_IN),
                              name=str(placed.spec.key)),
            at=placed.at, to=(anchor_u / M_PER_IN, anchor_z / M_PER_IN),
            text=placed.spec.text, height=ANNO_HEIGHT_IN, layer="A-ANNO-TEXT"))


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
    for storey in sorted(model.plan.storeys, key=lambda item: item.elevation.meters):
        named.append((f"{storey.tag.upper()} FLOOR", storey.elevation.meters))
        storey_walls = [wall for wall in model.walls if wall.storey == storey.tag]
        if storey_walls:
            named.append((f"{storey.tag.upper()} T.O. PLATE",
                          max(wall.z1_m for wall in storey_walls)))
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


def level_text(level: Level) -> str:
    return " / ".join(level.labels) + f"  EL. {feet_inches_signed(level.z_m)}"


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


def emit_level_dimensions(b: SceneBuilder, levels: list[Level], dim_u: float) -> None:
    """The stacked vertical string, chained past datums too close together to dimension.

    ``SECOND T.O. PLATE`` stands 1" above ``ATTIC FLOOR`` here, and a 1" dimension printed
    between two arrowheads that overlap each other is illegible and worthless. Skipping the
    rung rather than dropping the level keeps the chain summing: the next dimension is
    measured from the last one that was drawn, so bottom to top still adds up to the inch.
    """
    if not levels:
        return
    minimum = _MIN_DIM_IN * M_PER_IN
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
        out.append(LabelSpec(text=material.upper(), target=(anchor.x, anchor.y), key=material))
    return out


def feet_inches_signed(z_m: float) -> str:
    total_in = round(z_m / M_PER_IN)
    sign = "-" if total_in < 0 else ""
    total_in = abs(total_in)
    return f"{sign}{total_in // 12}'-{total_in % 12}\""
