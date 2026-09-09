"""C-101 annotation: what a zoning reviewer reads, in the order they read it.

Saint Paul DSI reads a site plan as a fixed sequence — lot lines with dimensions and
bearings, setback dimensions to each line, lot coverage against the district maximum, the
driveway, grading and drainage, erosion control, height — and the sheet is returned when
any one of them is missing. ``siteplan.py`` draws the *geometry* (footprints, footings,
contours, grading arrows, drainage); this module draws the *statements about the parcel*
that turn that geometry into a zoning submittal.

Every number printed here comes from ``site_metrics``, which the cover sheet also reads,
so C-101 and G-001 cannot disagree about lot area or coverage. Nothing here fabricates:
an absent street, easement, benchmark or driveway prints nothing at all, and a parcel that
is not a certified survey says so on the face of the sheet.
"""

from __future__ import annotations

import math

from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.lineweights import CUT, LIGHT, PROFILE
from typehaus.emit.draw.scene import (
    ArchDimension,
    NamedPoint,
    Polyline,
    SceneBuilder,
    Text,
)
from typehaus.emit.draw.schedule_block import (
    CHARACTER_WIDTH_RATIO,
    SCHEDULE_TEXT_HEIGHT_IN,
    BlockMetrics,
    ScheduleTable,
    block_origin_right_of,
    metrics_for,
)
from typehaus.emit.draw.site_metrics import (
    FT_PER_M,
    coverage_table,
    lot_line_dimensions,
)
from typehaus.emit.draw.structural_common import feet_inches
from typehaus.model.project import Site
from typehaus.resolve.model import ResolvedModel

# AIA civil layers for the annotation this module adds. The parcel ring, setbacks and
# topography already have theirs in ``siteplan.py``.
EASEMENT_LAYER = "C-PROP-EASE"
EROSION_LAYER = "C-EROS"
TABLE_LAYER = "C-ANNO-TABL"
BENCHMARK_LAYER = "C-ANNO-BMRK"

# Lettering for the field annotation, in model inches at ``REFERENCE_PLAN_EXTENT_IN``. A
# lot is an order of magnitude bigger than a floor plan and prints an order of magnitude
# smaller, so these are scaled by the parcel's own extent (``BlockMetrics``, the same
# factor the coverage table is drawn at) rather than fixed like the spot-elevation
# callouts — an unscaled lot-line dimension is a smudge at 3/32" = 1'-0".
_LOT_LINE_TEXT_IN = 2.0
_LABEL_TEXT_IN = 1.8
_SETBACK_TEXT_IN = 2.0
_STREET_TEXT_IN = 2.4
_LOT_LINE_OFFSET_IN = 3.0  # lettering sits outboard of the line it measures, per text height
_ENTRANCE_MARK_IN = 4.0  # half-diagonal of a point-located mark, in text heights


def emit_site_annotations(builder: SceneBuilder, model: ResolvedModel, site: Site) -> None:
    """Draw everything C-101 says *about* the parcel, on top of the drawn geometry."""
    metrics = metrics_for([_in(p.xy_m) for p in site.parcel])
    _emit_parcel_and_setbacks(builder, model, site, metrics)
    _emit_lot_line_dimensions(builder, site, metrics)
    _emit_streets(builder, site, metrics)
    _emit_easements(builder, site, metrics)
    _emit_erosion_controls(builder, site, metrics)
    _emit_benchmark(builder, site, metrics)
    _emit_coverage_table(builder, model, site, metrics)


def _reading_angle(dx: float, dy: float) -> float:
    """Text rotation that runs along a line and is never read upside down."""
    angle = math.degrees(math.atan2(dy, dx))
    return angle + 180.0 if angle > 90.0 or angle <= -90.0 else angle


def _scaled(metrics: BlockMetrics, height_in: float) -> float:
    """One of the constants above, at the parcel's drawing scale."""
    return height_in * metrics.text_height / SCHEDULE_TEXT_HEIGHT_IN


def _emit_parcel_and_setbacks(builder: SceneBuilder, model: ResolvedModel, site: Site,
                              metrics: BlockMetrics) -> None:
    """The parcel ring, each required setback line, and the distance actually provided.

    The label carries both numbers — ``FRONT SETBACK 30'-0" REQ / 34'-2" PROVIDED`` —
    because a setback line drawn without the provided dimension makes the reviewer measure
    the sheet. "Provided" is the same quantity ``code.site_setback`` grades: the shortest
    distance from any wall axis endpoint to that parcel edge *segment*.
    """
    parcel = [p.xy_m for p in site.parcel]
    if len(parcel) < 3:
        return
    builder.add(Polyline(points=tuple(_in(p) for p in parcel), closed=True, layer="C-PROP",
                         lineweight=CUT, linetype="PHANTOM"))
    n = len(parcel)
    footprint_pts = [p for wall in model.walls for p in (wall.axis[0], wall.axis[1])]
    for spec in site.setbacks:
        a, b = parcel[spec.edge % n], parcel[(spec.edge + 1) % n]
        offset_a, offset_b = _offset_edge(a, b, spec.distance.meters)
        builder.add(Polyline(points=(_in(offset_a), _in(offset_b)), layer="C-PROP-SETB",
                             lineweight=PROFILE, linetype="DASHED"))
        nearest = _nearest_point_to_edge(footprint_pts, a, b)
        name = spec.label or f"EDGE {spec.edge}"
        label = f"{name} SETBACK {feet_inches(spec.distance.meters)} REQ"
        if nearest is not None:
            provided_m = math.dist(nearest, _project_onto_segment(nearest, a, b))
            label += f" / {feet_inches(provided_m)} PROVIDED"
        # Read along the setback line, clear of it: a horizontal label on a vertical side
        # setback crosses the lot line it is measured from and becomes unreadable.
        height = _scaled(metrics, _SETBACK_TEXT_IN)
        mid = _in(((offset_a[0] + offset_b[0]) / 2, (offset_a[1] + offset_b[1]) / 2))
        ax, ay = _in(a)
        bx, by = _in(b)
        run = math.hypot(bx - ax, by - ay) or 1.0
        inward = (-(by - ay) / run, (bx - ax) / run)
        builder.add(Text(anchor=(mid[0] + inward[0] * height, mid[1] + inward[1] * height),
                         content=label, height=height, rotation=_reading_angle(bx - ax, by - ay),
                         layer="C-PROP-SETB", align="center"))
        if nearest is not None:
            foot = _project_onto_segment(nearest, a, b)
            builder.add(ArchDimension(
                kind="linear", ends=(NamedPoint(xy=_in(foot), name="setback-edge"),
                                     NamedPoint(xy=_in(nearest), name="setback-pt")),
                p0=_in(foot), p1=_in(nearest), offset=0.0,
            ))


def _emit_lot_line_dimensions(builder: SceneBuilder, site: Site, metrics: BlockMetrics) -> None:
    """Length and quadrant bearing of every parcel edge, read along the line it measures.

    Decimal feet, not feet-and-inches: a lot line is a surveyor's dimension and the
    certified survey it will be replaced by states it that way.
    """
    parcel = [p.xy_m for p in site.parcel]
    for edge, length_ft, bearing in lot_line_dimensions(site):
        a, b = parcel[edge], parcel[(edge + 1) % len(parcel)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        run = math.hypot(dx, dy) or 1.0
        # Outward normal of a CCW ring is the right-hand normal — the mirror of the inward
        # offset the setback lines use, so the dimension never lands inside the lot.
        ox, oy = dy / run, -dx / run
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        anchor = _in(mid)
        height = _scaled(metrics, _LOT_LINE_TEXT_IN)
        gap = height * _LOT_LINE_OFFSET_IN
        anchor = (anchor[0] + ox * gap, anchor[1] + oy * gap)
        builder.add(Text(anchor=anchor, content=f"{length_ft:.2f}'  {bearing}",
                         height=height, rotation=_reading_angle(dx, dy), layer="C-PROP",
                         align="center"))


def _emit_streets(builder: SceneBuilder, site: Site, metrics: BlockMetrics) -> None:
    """Name each abutting street and show the right-of-way it occupies.

    The parcel edge *is* the right-of-way line, so what the sheet adds is the street's
    centreline, half the stated ROW outboard of it. A frontage with no stated ROW is named
    and not dimensioned — the width is a plat fact, and inventing one would put a
    fabricated centreline on a permit drawing.
    """
    parcel = [p.xy_m for p in site.parcel]
    if len(parcel) < 3:
        return
    n = len(parcel)
    for street in site.streets:
        a, b = parcel[street.edge % n], parcel[(street.edge + 1) % n]
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        label = street.name.upper()
        if street.right_of_way_ft is not None:
            label += f" — {street.right_of_way_ft:.0f}' R.O.W."
            half_m = street.right_of_way_ft / 2.0 / FT_PER_M
            centre_a, centre_b = _offset_edge(a, b, -half_m)
            builder.add(Polyline(points=(_in(centre_a), _in(centre_b)), layer="C-PROP",
                                 lineweight=LIGHT, linetype="CENTER"))
            mid = ((centre_a[0] + centre_b[0]) / 2, (centre_a[1] + centre_b[1]) / 2)
        builder.add(Text(anchor=_in(mid), content=label,
                         height=_scaled(metrics, _STREET_TEXT_IN),
                         rotation=_reading_angle(b[0] - a[0], b[1] - a[1]),
                         layer="C-PROP", align="center"))


def _emit_easements(builder: SceneBuilder, site: Site, metrics: BlockMetrics) -> None:
    """Hatch-free dashed ring per recorded easement, labelled with its instrument.

    An easement is the one area on a site plan nothing may be built over, so it is drawn
    from its recorded outline rather than reconstructed from a centreline and a width; the
    stated width is printed beside the kind when the instrument gives one.
    """
    for easement in site.easements:
        ring = [p.xy_m for p in easement.outline]
        if len(ring) < 3:
            continue
        builder.add(Polyline(points=tuple(_in(p) for p in ring), closed=True,
                             layer=EASEMENT_LAYER, lineweight=PROFILE, linetype="DASHED"))
        label = f"{easement.kind.upper()} EASEMENT"
        if easement.width is not None:
            label = f"{feet_inches(easement.width.meters)} {label}"
        if easement.description:
            label += f" ({easement.description})"
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        builder.add(Text(anchor=_in((cx, cy)), content=label,
                         height=_scaled(metrics, _LABEL_TEXT_IN),
                         layer=EASEMENT_LAYER, align="center"))


#: How each erosion-control measure reads on the sheet. A silt fence is a run, an entrance
#: and an inlet protector are places — the model does not pretend the three share a
#: geometry, and neither does the drawing.
_EROSION_LABELS = {
    "silt_fence": "SILT FENCE",
    "construction_entrance": "ROCK CONSTRUCTION ENTRANCE",
    "inlet_protection": "INLET PROTECTION",
}


def _emit_erosion_controls(builder: SceneBuilder, site: Site, metrics: BlockMetrics) -> None:
    """Silt fence, rock entrance and inlet protection, each drawn as what it is."""
    height = _scaled(metrics, _LABEL_TEXT_IN)
    for control in site.erosion_controls:
        path = [p.xy_m for p in control.path]
        if not path:
            continue
        label = _EROSION_LABELS.get(control.kind, control.kind.upper().replace("_", " "))
        if control.description:
            label += f" — {control.description}"
        if len(path) >= 2:
            builder.add(Polyline(points=tuple(_in(p) for p in path), layer=EROSION_LAYER,
                                 lineweight=PROFILE, linetype="DASHED"))
            anchor = _in(path[len(path) // 2])
        else:
            # A point-located measure: an X on the spot. Drawn rather than symbolised —
            # the symbol vocabulary the writers carry has no erosion-control glyph, and an
            # unlisted name draws as window glazing.
            (x, y) = _in(path[0])
            d = height * _ENTRANCE_MARK_IN
            builder.add(Polyline(points=((x - d, y - d), (x + d, y + d)),
                                 layer=EROSION_LAYER, lineweight=PROFILE))
            builder.add(Polyline(points=((x - d, y + d), (x + d, y - d)),
                                 layer=EROSION_LAYER, lineweight=PROFILE))
            anchor = (x, y + d)
        builder.add(Text(anchor=(anchor[0], anchor[1] + height), content=label,
                         height=height, layer=EROSION_LAYER, align="center"))


def _emit_benchmark(builder: SceneBuilder, site: Site, metrics: BlockMetrics) -> None:
    """The physical point every elevation on the set is recovered from."""
    benchmark = site.benchmark
    if benchmark is None:
        return
    x, y = _in(benchmark.position.xy_m)
    height = _scaled(metrics, _LABEL_TEXT_IN)
    d = height * _ENTRANCE_MARK_IN / 2.0
    builder.add(Polyline(points=((x - d, y - d), (x + d, y - d), (x, y + d)), closed=True,
                         layer=BENCHMARK_LAYER, lineweight=PROFILE))
    elevation_ft = benchmark.elevation.meters * FT_PER_M
    label = f"BENCHMARK EL. {elevation_ft:+.2f}'"
    if benchmark.description:
        label += f" — {benchmark.description.upper()}"
    builder.add(Text(anchor=(x + d + height, y), content=label, height=height,
                     layer=BENCHMARK_LAYER))


def _survey_notes(site: Site) -> list[str]:
    """What this sheet's parcel geometry rests on, said in the reviewer's own terms."""
    basis = site.parcel_basis
    if basis == "survey":
        who = site.survey_by or "THE SURVEYOR OF RECORD"
        dated = f", DATED {site.survey_date}" if site.survey_date else ""
        first = (f"PARCEL, LOT LINES AND SETBACKS PER CERTIFIED SURVEY BY {who.upper()}"
                 f"{dated}. THE CERTIFIED SURVEY IS THE DOCUMENT OF RECORD AND GOVERNS "
                 "OVER THIS SHEET.")
    elif basis == "placeholder":
        first = ("THIS SHEET IS DRAWN FROM A PLACEHOLDER PARCEL — NOT A SURVEY. LOT LINES, "
                 "BEARINGS, LOT AREA, COVERAGE AND SETBACK DIMENSIONS SHOWN ARE NOT "
                 "MEASURED. A CERTIFIED SURVEY BY A LICENSED LAND SURVEYOR IS THE DOCUMENT "
                 "OF RECORD AND GOVERNS OVER THIS SHEET.")
    else:
        first = ("THE PARCEL SHOWN STATES NO BASIS: NOBODY HAS CERTIFIED THE RING THESE "
                 "LOT LINES, SETBACKS AND COVERAGE FIGURES ARE MEASURED ON. A CERTIFIED "
                 "SURVEY BY A LICENSED LAND SURVEYOR IS THE DOCUMENT OF RECORD.")
    notes = [first,
             "EXISTING AND PROPOSED TOPOGRAPHY, TOP OF BLOCK / FIRST FLOOR ELEVATIONS AND "
             "TREE INVENTORY ARE SURVEY DELIVERABLES AND ARE NOT SHOWN ON THIS SHEET."]
    if site.erosion_controls:
        notes.append("EROSION AND SEDIMENT CONTROL MEASURES TO BE IN PLACE BEFORE ANY "
                     "SOIL DISTURBANCE AND MAINTAINED UNTIL THE SITE IS STABILIZED.")
    return notes


def _emit_coverage_table(builder: SceneBuilder, model: ResolvedModel, site: Site,
                         metrics: BlockMetrics) -> None:
    """Zoning arithmetic beside the drawing: coverage, paving, height, and the survey note.

    Placed off the parcel's right edge, so the table can never land on the lot it
    describes however the sheet is later fitted.
    """
    parcel = [_in(p.xy_m) for p in site.parcel]
    if len(parcel) < 3:
        return
    x0, y0 = block_origin_right_of(parcel, metrics)
    rows = tuple(tuple(cell for cell in row) for row in coverage_table(model, site))
    table = ScheduleTable(title="SITE / ZONING DATA",
                          columns=("ITEM", "PROVIDED", "ALLOWED"), rows=rows)
    y = _emit_table(builder, table, (x0, y0), metrics)
    _emit_notes(builder, "SITE PLAN NOTES", _survey_notes(site),
                (x0, y - metrics.block_gap), metrics)


# ``schedule_block`` owns the same rhythm on A-sheets, but its emitters hard-code the
# architectural annotation layers; a civil sheet's table rules belong on C-ANNO-TABL. The
# metrics and the monospace padding convention are shared, so only the two draw loops and
# the layer names live here.
def _emit_table(builder: SceneBuilder, table: ScheduleTable, origin: tuple[float, float],
                metrics: BlockMetrics) -> float:
    x0, y0 = origin
    if not table.rows:
        return y0
    widths = [max([len(column)] + [len(row[i]) for row in table.rows if i < len(row)])
              for i, column in enumerate(table.columns)]
    lines = [_pad(table.columns, widths)] + [_pad(row, widths) for row in table.rows]
    rule_width = max(len(line) for line in lines) * metrics.text_height * CHARACTER_WIDTH_RATIO

    builder.add(Text(anchor=(x0, y0), content=table.title, height=metrics.title_height,
                     layer=TABLE_LAYER))
    row_y = y0 - metrics.title_pitch
    builder.add(Text(anchor=(x0, row_y), content=lines[0], height=metrics.text_height,
                     layer=TABLE_LAYER))
    row_y -= metrics.row_pitch / 2.0
    _rule(builder, x0, row_y, rule_width)
    for line in lines[1:]:
        row_y -= metrics.row_pitch
        builder.add(Text(anchor=(x0, row_y), content=line, height=metrics.text_height,
                         layer=TABLE_LAYER))
    bottom = row_y - metrics.row_pitch / 2.0
    _rule(builder, x0, bottom, rule_width)
    return bottom


_NOTE_WRAP_COLUMNS = 72


def _emit_notes(builder: SceneBuilder, title: str, notes: list[str],
                origin: tuple[float, float], metrics: BlockMetrics) -> float:
    import textwrap

    x0, y0 = origin
    if not notes:
        return y0
    builder.add(Text(anchor=(x0, y0), content=title, height=metrics.title_height,
                     layer=TABLE_LAYER))
    row_y = y0 - metrics.title_pitch
    for index, note in enumerate(notes, start=1):
        lead = f"{index}. "
        for line in textwrap.wrap(note, _NOTE_WRAP_COLUMNS) or [""]:
            builder.add(Text(anchor=(x0, row_y), content=lead + line,
                             height=metrics.text_height, layer=TABLE_LAYER))
            lead = " " * len(lead)
            row_y -= metrics.row_pitch
    return row_y


def _pad(cells: tuple[str, ...], widths: list[int]) -> str:
    padded = [cell.ljust(width) for cell, width in zip(cells, widths, strict=False)]
    return "  ".join(padded).rstrip()


def _rule(builder: SceneBuilder, x0: float, y: float, width: float) -> None:
    builder.add(Polyline(points=((x0, y), (x0 + width, y)), layer=TABLE_LAYER,
                         lineweight=LIGHT))


def _offset_edge(a: tuple[float, float], b: tuple[float, float],
                 distance: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """Offset a CCW parcel edge inward by ``distance`` (left-hand normal of CCW = inward)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length  # rotate -90° (CCW ring -> inward normal)
    return ((a[0] + nx * distance, a[1] + ny * distance),
            (b[0] + nx * distance, b[1] + ny * distance))


def _nearest_point_to_edge(points: list[tuple[float, float]], a: tuple[float, float],
                           b: tuple[float, float]) -> tuple[float, float] | None:
    """The authored point closest to the parcel *segment* — what the setback check grades."""
    if not points:
        return None
    best, best_dist = None, float("inf")
    for p in points:
        dist = math.dist(p, _project_onto_segment(p, a, b))
        if dist < best_dist:
            best_dist, best = dist, p
    return best


def _project_onto_segment(point: tuple[float, float], a: tuple[float, float],
                          b: tuple[float, float]) -> tuple[float, float]:
    """Foot of ``point`` on the finite segment a-b, clamped to its ends.

    Clamped because ``code.site_setback`` measures to a ``LineString``: a wall past the end
    of an edge is that far from the *lot line*, not from its infinite extension.
    """
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy or 1.0
    t = ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / length2
    t = min(1.0, max(0.0, t))
    return (a[0] + t * dx, a[1] + t * dy)
