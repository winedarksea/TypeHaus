"""Opening marks and an R.O. height key on an exterior elevation (O4-010, O3-011).

The mark is the plan's (``plan_marks.opening_type_marks``), in the same circle (window) or
hexagon (door), so a bubble on A-201 reads the same A-601/A-602 row as its twin on A-101.
A mark keys (type, RO, frame), not height, so the heights go on the sheet: a key under the
drawing, one row per storey and (sill, head), in the schedules' own "RO sill" terms.

A leadered datum per head and sill was tried first: eleven of them on the south facade
cascaded off the bottom of a left-hand column, and the column pushed all four sheets down a
scale rung (A-204 has no slack). The key fits in the white space every elevation already has.

A bubble goes on a door's leaf, under a sill, beside a jamb or over a head: whichever lands
least on the openings, guards and trim the projection drew, the earlier spot winning a near
tie (a mark over a head reads as the window above's). :func:`annotate.dodge` then settles
any two left touching. A cladding line may run behind a bubble; a guard's pickets may not.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import Point, box
from shapely.geometry.base import BaseGeometry

from typehaus.emit.draw.annotate import LabelSpec, PlacedLabel, dodge
from typehaus.emit.draw.elevation_openings import _panel_for, _visible_by_uid
from typehaus.emit.draw.elevation_project import ElevationView, VisiblePiece
from typehaus.emit.draw.lineweights import REFERENCE
from typehaus.emit.draw.plan_marks import MARK_LAYER, opening_type_marks
from typehaus.emit.draw.scene import Polyline, SceneBuilder, Text
from typehaus.emit.draw.typography import CHAR_ASPECT, feet_inches_8th, model_in_per_pt
from typehaus.quantities import M_PER_IN
from typehaus.resolve import overlay
from typehaus.resolve.model import ResolvedModel

#: An opening less visible than this share of its R.O. (behind the garage) takes no tag:
#: the bubble would name a window a reader cannot find.
_MIN_VISIBLE = 0.3

#: Air between a bubble and its opening's trim, paper inches.
_TAG_GAP_PAPER_IN = 0.03

_SEGMENTS = 16
_KEY_LAYER = "A-ANNO-TEXT"


@dataclass(frozen=True)
class OpeningTarget:
    """One visible opening in the elevation's (u, z), metres, and its schedule heights."""

    tag: str
    uid: str
    mark: str
    is_door: bool
    storey: str
    u0: float
    z0: float
    u1: float
    z1: float
    #: The R.O. and everything of the opening drawn around it (casing, cap, pan).
    bounds: tuple[float, float, float, float]
    sill_m: float  # the schedules' "RO sill": above the storey datum
    head_m: float
    datum_m: float  # the storey datum, for ordering the key


@dataclass(frozen=True)
class OpeningMarks:
    """What the annotation pass needs: the targets, and what a bubble may not cover."""

    targets: tuple[OpeningTarget, ...] = ()
    #: A guard's pickets hide a mark; a fascia or belt is avoided where it can be; a
    #: cladding line through one only crosses it.
    rails: BaseGeometry | None = None
    trim: BaseGeometry | None = None


def opening_marks(model: ResolvedModel, pieces: list[VisiblePiece],
                  view: ElevationView) -> OpeningMarks:
    """Every marked opening this elevation sees face-on, left to right, plus the guards
    and trim a bubble must stay off."""
    from typehaus.emit.draw.schedules.openings import ro_sill_m

    marks = opening_type_marks(model)
    visible = _visible_by_uid(pieces)
    # An opening's own casing and cap (``cladding_trim`` tagged with it) are part of it.
    own_trim: dict[str, list[BaseGeometry]] = {}
    for piece in pieces:
        if piece.candidate.family == "trim":
            own_trim.setdefault(piece.candidate.tag, []).append(piece.geometry)
    out: list[OpeningTarget] = []
    for opening in model.openings:
        mark, region = marks.get(opening.tag), visible.get(opening.uid)
        wall = model.wall(opening.host_wall)
        if mark is None or region is None or region.is_empty or wall is None:
            continue
        panel = _panel_for(opening, wall, region, view)
        if panel is None or region.area < _MIN_VISIBLE * panel.width * panel.height:
            continue
        sill = ro_sill_m(model, opening) or 0.0
        storey = model.plan.storey(wall.storey)
        rb = overlay.union_all([region, *own_trim.get(opening.tag, [])]).bounds
        out.append(OpeningTarget(
            tag=opening.tag, uid=opening.uid, mark=mark, is_door=opening.is_door,
            storey=wall.storey, u0=panel.u0, z0=panel.z0, u1=panel.u1, z1=panel.z1,
            bounds=(min(rb[0], panel.u0), min(rb[1], panel.z0),
                    max(rb[2], panel.u1), max(rb[3], panel.z1)),
            sill_m=sill, head_m=sill + opening.height_m,
            datum_m=storey.elevation.meters if storey is not None else panel.z0))
    tagged = {target.tag for target in out}
    rails = [p.geometry for p in pieces if p.candidate.family == "rail"]
    trim = [p.geometry for p in pieces
            if p.candidate.family == "trim" and p.candidate.tag not in tagged]
    return OpeningMarks(targets=tuple(sorted(out, key=lambda t: (t.u0, t.z0))),
                        rails=overlay.union_all(rails) if rails else None,
                        trim=overlay.union_all(trim) if trim else None)


def emit_opening_tags(b: SceneBuilder, marks: OpeningMarks, scale: float,
                      height_pt: float, grade_z: float) -> None:
    """A bubbled mark on each opening, in the first clear spot, dodged."""
    targets = marks.targets
    if not targets:
        return
    per_pt = model_in_per_pt(scale)
    longest = max(3, *(len(t.mark) for t in targets))
    radius = (longest * CHAR_ASPECT * height_pt / 2.0 + 0.25 * height_pt) * per_pt
    gap = _TAG_GAP_PAPER_IN * 12.0 / scale
    rects = [tuple(v / M_PER_IN for v in t.bounds) for t in targets]
    taken = [box(*rect) for rect in rects]
    if marks.rails is not None and not marks.rails.is_empty:
        taken.append(_inches(marks.rails))
    soft = ([_inches(marks.trim)] if marks.trim is not None and not marks.trim.is_empty
            else [])
    ground = grade_z / M_PER_IN
    labels: list[PlacedLabel] = []
    for index, (target, (u0, z0, u1, z1)) in enumerate(zip(targets, rects, strict=True)):
        uc, zc = (u0 + u1) / 2.0, (z0 + z1) / 2.0
        # Under the sill, then beside a jamb, and over the head last: a mark over a head
        # stacks under the sill of the window above and reads as that window's.
        spots = [(uc, z0 - gap - radius), (u1 + gap + radius, zc),
                 (u0 - gap - radius, zc), (uc, z1 + gap + radius)]
        if target.is_door and u1 - u0 > 2.5 * radius:
            # A door's mark goes on its leaf, above the hardware: nothing else is there.
            spots.insert(0, (uc, z0 + 0.7 * (z1 - z0)))
        spots = [spot for spot in spots if spot[1] - radius > ground] or spots[-1:]
        others = [shape for i, shape in enumerate(taken) if i != index]
        # The least covered spot, an opening, guard or placed mark weighing ten times a
        # trim, and each step down the preference a tenth of a bubble.
        step = 0.1 * math.pi * radius * radius
        at = min(spots, key=lambda spot: (10.0 * _covered(spot, radius, others)
                                          + _covered(spot, radius, soft)
                                          + step * spots.index(spot)))
        taken.append(Point(at).buffer(radius))
        labels.append(PlacedLabel(
            spec=LabelSpec(text=target.mark, target=(uc, z0), key=target.tag), at=at,
            align="center", height_pt=height_pt,
            box=(at[0] - radius, at[1] - radius, at[0] + radius, at[1] + radius)))
    for target, placed in zip(targets, dodge(labels, scale=scale),
                              strict=True):
        ux, uz = placed.at
        sides, phase = (6, math.pi / 2) if target.is_door else (_SEGMENTS, 0.0)
        ring = tuple((ux + radius * math.cos(phase + 2 * math.pi * i / sides),
                      uz + radius * math.sin(phase + 2 * math.pi * i / sides))
                     for i in range(sides))
        b.add(Polyline(points=ring, layer=MARK_LAYER, closed=True, lineweight=REFERENCE,
                       uid=target.uid, tag=target.tag))
        b.add(Text(anchor=(ux, uz), content=target.mark, height=height_pt * per_pt,
                   height_pt=height_pt, layer=MARK_LAYER, align="center"))


def height_key_rows(targets: tuple[OpeningTarget, ...]) -> list[tuple[str, ...]]:
    """``(storey, its datum EL., marks, RO sill, RO head)``, top storey first, one row per
    distinct pair. The datum ties a row to the level ladder (the garage's is its own); the
    sill is printed with the schedules' formatter so it reads as it does on A-601/A-602."""
    from typehaus.emit.draw.schedules.openings import _fi

    groups: dict[tuple[str, str, str], tuple[float, float, list[str]]] = {}
    for target in targets:
        key = (target.storey, _fi(target.sill_m), _fi(target.head_m))
        datum, u, found = groups.get(key, (target.datum_m, target.u0, []))
        if target.mark not in found:
            found.append(target.mark)
        groups[key] = (datum, min(u, target.u0), found)
    ordered = sorted(groups.items(), key=lambda item: (-item[1][0], item[1][1]))
    return [(storey.upper(), feet_inches_8th(datum / M_PER_IN, 16), " ".join(found), sill,
             head) for (storey, sill, head), (datum, _u, found) in ordered]


def emit_height_key(b: SceneBuilder, targets: tuple[OpeningTarget, ...], left_u: float,
                    top_z: float, scale: float, height_pt: float) -> None:
    """The R.O. height key, a small table hung from ``top_z`` (metres) at ``left_u``."""
    rows = height_key_rows(targets)
    if not rows:
        return
    per_pt = model_in_per_pt(scale)
    header = ("STOREY", "DATUM EL.", "MARK", "RO SILL", "RO HEAD")
    widths = [max(len(row[i]) for row in (header, *rows)) for i in range(len(header))]
    char = CHAR_ASPECT * height_pt * per_pt
    step = 1.6 * height_pt * per_pt
    columns = [left_u / M_PER_IN]
    for width in widths[:-1]:
        columns.append(columns[-1] + (width + 2) * char)
    z = top_z / M_PER_IN - step
    b.add(Text(anchor=(columns[0], z), content="OPENING R.O. HEIGHTS ABOVE STOREY DATUM",
               height=height_pt * per_pt, height_pt=height_pt, layer=_KEY_LAYER))
    for row in (header, *rows):
        z -= step
        for u, cell in zip(columns, row, strict=True):
            b.add(Text(anchor=(u, z), content=cell, height=height_pt * per_pt,
                       height_pt=height_pt, layer=_KEY_LAYER))


def _covered(at: tuple[float, float], radius: float, shapes: list[BaseGeometry]) -> float:
    """How much of a bubble at ``at`` lands on ``shapes``, model square inches."""
    bubble = Point(at).buffer(radius)
    return sum(shape.intersection(bubble).area for shape in shapes)


def _inches(geometry: BaseGeometry) -> BaseGeometry:
    from shapely import affinity

    return affinity.scale(geometry, 1.0 / M_PER_IN, 1.0 / M_PER_IN, origin=(0.0, 0.0))
