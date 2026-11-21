"""S-100 content derivation: what the foundation sheet knows, and what it does not.

Splits the *reading* of the resolved model (which solids are foundation scope, what mark
each carries, what the schedule rows say, which required datum the model simply does not
have) away from the *drawing* in ``foundationplan``. Everything here is derived from
``ResolvedModel`` and the authored plan; nothing is invented. Where a permit-set datum is
missing — slab reinforcement, under-slab vapour retarder, sill anchorage — this module
returns a :class:`Finding` naming the missing input instead of printing a plausible value.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from typehaus.emit.draw.foundation_notes import (
    _under_slab_note,
    foundation_general_notes,
    foundation_sheet_findings,
)
from typehaus.emit.draw.foundation_reinforcement import (
    _cover_text,
    column_reinforcement_schedule,
    reinforcement_schedule,
)
from typehaus.emit.draw.schedule_block import ScheduleTable
from typehaus.emit.draw.structural_common import (
    M_TO_FT,
    bboxes_overlap,
    elevation_feet,
    feet_inches,
    inches,
    inches_text,
    outline_area_m2,
    outline_bbox,
    outline_center,
    point_in_bbox,
    wall_length_m,
)
from typehaus.hardware.config import FT_TO_M
from typehaus.resolve.assembly_material import is_flatwork
from typehaus.resolve.model import ResolvedModel, ResolvedSolid, ResolvedWall
from typehaus.resolve.room_lookup import axis_ring
from typehaus.resolve.solid_categories import is_pour_slab

# The notes half moved to ``foundation_notes`` and the steel to ``foundation_reinforcement``;
# both are re-exported here, because S-100's builder and the tests import them from here.
__all__ = [
    "FoundationMarks",
    "_cover_text",
    "bearing_solids",
    "build_foundation_schedules",
    "column_reinforcement_schedule",
    "footing_steps",
    "foundation_general_notes",
    "foundation_marks",
    "foundation_sheet_findings",
    "anchorage_schedule",
    "foundation_walls",
    "reinforcement_schedule",
    "slabs_on_grade",
]

# A deck's top and the slab riding on it are the same plane to within a subfloor sheet;
# anything further apart is a different level, not decking.
DECK_COINCIDENCE_TOLERANCE_M = 0.3
SQ_M_TO_SQ_FT = 10.763910416709722
# Two footing runs whose plan outlines come this close are one continuous foundation, so a
# difference in bearing elevation between them is a step rather than two separate structures.
STEP_ADJACENCY_GAP_M = 0.6
# Bearing elevations within a stone-bed tolerance are the same plane, not a step.
STEP_ELEVATION_TOLERANCE_M = 0.02


@dataclass(frozen=True)
class FoundationMarks:
    """Schedule keys, by element tag — the plan and the schedule share one mark source."""

    footing: dict[str, str] = field(default_factory=dict)
    pad: dict[str, str] = field(default_factory=dict)
    wall: dict[str, str] = field(default_factory=dict)
    slab: dict[str, str] = field(default_factory=dict)


def foundation_walls(model: ResolvedModel) -> list[ResolvedWall]:
    """Every wall the resolver marked as foundation, in tag order."""
    return sorted((wall for wall in model.walls if wall.is_foundation), key=lambda w: w.tag)


def bearing_solids(model: ResolvedModel) -> list[ResolvedSolid]:
    """Footings and pads — foundation scope by definition, whatever storey they were
    authored on (catlin's breezeway pads live on ``main``, its house footings on
    ``basement``; both belong on S-100)."""
    return sorted((solid for solid in model.solids if solid.category in ("footing", "pad")),
                  key=lambda s: s.tag)


def slabs_on_grade(model: ResolvedModel) -> list[ResolvedSolid]:
    """Pours that bear on grade, so they belong on the foundation sheet.

    Only a ``pour`` kind qualifies (``resolve/slab_kind.py``): a deck, framed platform
    (RM-M-BATH2's tub-deck cap) or band is drawn elsewhere. A pour is still excluded when a
    joisted deck carries it at the same plane or a lower-storey room sits inside its
    footprint (the main deck over the basement). Elevation alone will not separate them.
    """
    storey_elevation = {storey.tag: storey.elevation.meters for storey in model.plan.storeys}
    out: list[ResolvedSolid] = []
    for solid in model.solids:
        if not is_pour_slab(solid.category) or is_flatwork(model.plan, solid):
            continue
        if (_carried_by_deck(model, solid)
                or _room_below(model, solid, storey_elevation)):
            continue
        out.append(solid)
    return sorted(out, key=lambda s: s.tag)


def _carried_by_deck(model: ResolvedModel, slab: ResolvedSolid) -> bool:
    slab_box = outline_bbox(slab.outline)
    for floor in model.floors:
        if not floor.members:
            continue
        points = [point for member in floor.members for point in (member.p0, member.p1)]
        deck_top = max(member.z1_m for member in floor.members)
        if abs(deck_top - slab.z0_m) > DECK_COINCIDENCE_TOLERANCE_M:
            continue
        if bboxes_overlap(slab_box, outline_bbox(points)):
            return True
    return False


def _room_below(model: ResolvedModel, slab: ResolvedSolid,
                storey_elevation: dict[str, float]) -> bool:
    slab_box = outline_bbox(slab.outline)
    for room in model.rooms:
        if storey_elevation.get(room.storey, 0.0) >= slab.z0_m:
            continue
        if len(axis_ring(room)) >= 3 and point_in_bbox(outline_center(axis_ring(room)), slab_box):
            return True
    return False


def foundation_marks(model: ResolvedModel) -> FoundationMarks:
    """Assign F#/P#/FW#/S# marks — one mark per distinct scheduled type, tag-ordered."""
    marks = FoundationMarks()
    footing_keys: dict[tuple, str] = {}
    pad_keys: dict[tuple, str] = {}
    for solid in bearing_solids(model):
        if solid.category == "footing":
            key = _footing_key(model, solid)
            marks.footing[solid.tag] = footing_keys.setdefault(key, f"F{len(footing_keys) + 1}")
        else:
            key = _pad_key(solid)
            marks.pad[solid.tag] = pad_keys.setdefault(key, f"P{len(pad_keys) + 1}")
    wall_keys: dict[tuple, str] = {}
    for wall in foundation_walls(model):
        key = _wall_key(wall)
        marks.wall[wall.tag] = wall_keys.setdefault(key, f"FW{len(wall_keys) + 1}")
    for index, slab in enumerate(slabs_on_grade(model), start=1):
        marks.slab[slab.tag] = f"S{index}"
    return marks


def _footing_key(model: ResolvedModel, solid: ResolvedSolid) -> tuple:
    authored = model.plan.by_tag(solid.tag)
    width = round(authored.width.inches, 1) if authored is not None else None
    depth = round(authored.depth.inches, 1) if authored is not None else None
    return ("footing", width, depth, round(solid.z0_m, 3))


def _pad_key(solid: ResolvedSolid) -> tuple:
    x0, y0, x1, y1 = outline_bbox(solid.outline)
    return ("pad", round(x1 - x0, 3), round(y1 - y0, 3),
            round(solid.z1_m - solid.z0_m, 3), round(solid.z0_m, 3))


def _wall_key(wall: ResolvedWall) -> tuple:
    return (wall.assembly, round(wall.thickness_m, 3), round(wall.z0_m, 3), round(wall.z1_m, 3))


def build_foundation_schedules(model: ResolvedModel) -> list[ScheduleTable]:
    """The keyed S-100 schedules: footings/pads, foundation walls, slabs on grade,
    sill anchorage, reinforcement, the cast columns' cages. An empty table is dropped rather
    than printed as a heading over nothing."""
    marks = foundation_marks(model)
    tables = [_bearing_schedule(model, marks), _wall_schedule(model, marks),
              _slab_schedule(model, marks), anchorage_schedule(model),
              reinforcement_schedule(model), column_reinforcement_schedule(model)]
    return [table for table in tables if table.rows]


def _bearing_schedule(model: ResolvedModel, marks: FoundationMarks) -> ScheduleTable:
    grouped: dict[str, list[ResolvedSolid]] = {}
    for solid in bearing_solids(model):
        mark = marks.footing.get(solid.tag) or marks.pad[solid.tag]
        grouped.setdefault(mark, []).append(solid)
    rows: list[tuple[str, ...]] = []
    for mark, solids in sorted(grouped.items(), key=lambda item: _mark_order(item[0])):
        sample = solids[0]
        authored = model.plan.by_tag(sample.tag)
        if sample.category == "footing" and authored is not None:
            kind = "CONT. STRIP FTG." if _is_under_wall(model, authored) else "SPREAD FTG."
            size = (f"{inches_text(authored.width.inches)} W × "
                    f"{inches_text(authored.depth.inches)} D")
        else:
            x0, y0, x1, y1 = outline_bbox(sample.outline)
            kind = "PAD"
            # The pad *solid* is extended down to its authored bottom elevation, so its z
            # extent is a pier depth, not the pad thickness the schedule owes the reader.
            thickness = (inches_text(authored.thickness.inches) if authored is not None
                         else inches(sample.z1_m - sample.z0_m))
            size = f"{feet_inches(x1 - x0)} × {feet_inches(y1 - y0)} × {thickness} THK"
        supports = ", ".join(sorted({_supported_element(model, s) for s in solids
                                     if _supported_element(model, s)}))
        rows.append((mark, kind, size, elevation_feet(sample.z0_m), str(len(solids)),
                     _abbreviate(supports)))
    return ScheduleTable(
        title="FOOTING / PAD SCHEDULE",
        columns=("MARK", "TYPE", "SIZE", "BEARING EL.", "QTY", "SUPPORTS"),
        rows=tuple(rows),
    )


def _structural_thickness_m(wall: ResolvedWall) -> float:
    """The THK an S-100 wall schedule owes the reader: the POUR, not the finished stack.

    ``ResolvedWall.thickness_m`` is every layer, which is the right number for a clash or a
    room's clear face and the wrong one on a structural sheet. catlin's sunken-garden court put a
    1/8" mineral silicate wash on the court face of its 12" retaining walls, and this column
    duly printed **12 1/8"** — a permit drawing telling a contractor to form a wall an eighth of
    an inch thicker than the one that is designed, reinforced and priced. Nothing would have
    caught it but a test that happened to pin the string.

    Summing the STRUCTURE layers says what a foundation wall schedule means. Falls back to the
    full thickness when an assembly declares no structure layer, so a wall shaped unlike this one
    reads exactly as it did before (``integrity.assembly_layers`` owns that case separately).
    """
    structural = [ly.thickness_m for ly in wall.layers if ly.function == "structure"]
    return sum(structural) if structural else wall.thickness_m


def _wall_schedule(model: ResolvedModel, marks: FoundationMarks) -> ScheduleTable:
    grouped: dict[str, list[ResolvedWall]] = {}
    for wall in foundation_walls(model):
        grouped.setdefault(marks.wall[wall.tag], []).append(wall)
    rows: list[tuple[str, ...]] = []
    for mark, walls in sorted(grouped.items(), key=lambda item: _mark_order(item[0])):
        sample = walls[0]
        run_ft = sum(wall_length_m(wall) for wall in walls) * M_TO_FT
        rows.append((mark, sample.assembly, inches(_structural_thickness_m(sample)),
                     f"{run_ft:,.0f} LF",
                     elevation_feet(sample.z1_m), elevation_feet(sample.z0_m), str(len(walls))))
    return ScheduleTable(
        title="FOUNDATION WALL SCHEDULE",
        columns=("MARK", "ASSEMBLY", "THK", "RUN", "T.O.W. EL.", "B.O.W. EL.", "QTY"),
        rows=tuple(rows),
    )


def _slab_schedule(model: ResolvedModel, marks: FoundationMarks) -> ScheduleTable:
    rows: list[tuple[str, ...]] = []
    for slab in slabs_on_grade(model):
        rows.append((
            marks.slab[slab.tag], slab.tag, inches(slab.z1_m - slab.z0_m),
            f"{outline_area_m2(slab.outline) * SQ_M_TO_SQ_FT:,.0f} SF",
            slab.assembly or "—",
            _under_slab_note(model, slab) or "NOT MODELLED",
            elevation_feet(slab.z1_m),
        ))
    return ScheduleTable(
        title="SLAB-ON-GRADE SCHEDULE",
        columns=("MARK", "TAG", "THK", "AREA", "ASSEMBLY", "UNDER-SLAB", "T.O.S. EL."),
        rows=tuple(rows),
    )




def _is_under_wall(model: ResolvedModel, authored) -> bool:
    hosted = model.plan.by_tag(getattr(authored, "under", "") or "")
    return hosted is not None and hosted.element_kind in ("Wall", "FoundationWall")


def _supported_element(model: ResolvedModel, solid: ResolvedSolid) -> str:
    authored = model.plan.by_tag(solid.tag)
    under = getattr(authored, "under", None) if authored is not None else None
    if under:
        return str(under)
    # A pad names no host; the post standing on it does, so read the load path backwards.
    for element in model.plan.all_elements():
        if element.element_kind == "Post" and getattr(element, "supported_by", None) == solid.tag:
            return element.tag
    return ""


def _abbreviate(text: str, limit: int = 46) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _mark_order(mark: str) -> tuple[str, int]:
    prefix = mark.rstrip("0123456789")
    return prefix, int(mark[len(prefix):] or 0)




def footing_steps(model: ResolvedModel
                  ) -> list[tuple[ResolvedSolid, ResolvedSolid, tuple[float, float]]]:
    """Where two *touching* footing runs bear at different elevations — a real step.

    Two footings at different elevations on opposite sides of the site are two structures,
    not a step, so adjacency in plan is the test. One callout per distinct elevation pair,
    placed at the first adjacency in tag order, keeps the plan readable and deterministic.
    """
    footings = [solid for solid in bearing_solids(model) if solid.category == "footing"]
    boxes = {solid.tag: outline_bbox(solid.outline) for solid in footings}
    seen: set[tuple[float, float]] = set()
    steps: list[tuple[ResolvedSolid, ResolvedSolid, tuple[float, float]]] = []
    for index, first in enumerate(footings):
        for second in footings[index + 1:]:
            if abs(first.z0_m - second.z0_m) <= STEP_ELEVATION_TOLERANCE_M:
                continue
            if not bboxes_overlap(boxes[first.tag], boxes[second.tag], STEP_ADJACENCY_GAP_M):
                continue
            lower, upper = sorted((first, second), key=lambda solid: solid.z0_m)
            key = (round(lower.z0_m, 3), round(upper.z0_m, 3))
            if key in seen:
                continue
            seen.add(key)
            low_at = outline_center(lower.outline)
            high_at = outline_center(upper.outline)
            steps.append((lower, upper, ((low_at[0] + high_at[0]) / 2.0,
                                         (low_at[1] + high_at[1]) / 2.0)))
    return steps


def anchorage_schedule(model: ResolvedModel) -> ScheduleTable:
    """How the wood above is fastened to the concrete below — MARK, part, pitch, count.

    Two shapes, and the sheet prints whichever the model carries. An authored
    ``ConnectorKind.ANCHOR_BOLT`` is placed one at a time, so it schedules by location and
    carries no pitch. The ordinary case is derived: a framed wall stacked on concrete makes
    a sill-plate construction return and ``takeoff/anchors`` counts a strap anchor along it
    at a pitch — a derivation S-100 was already running and throwing away as a WARN.
    Grouped by what the plate lands on and on which storey: a mudsill over a foundation
    wall and a partition plate on a slab are two conditions sharing one part number.
    """
    rows = _anchor_bolt_rows(model) or _mudsill_anchor_schedule_rows(model)
    return ScheduleTable(
        title="SILL ANCHORAGE SCHEDULE",
        columns=("MARK", "TYPE", "PART", "SPACING", "QTY", "WALLS"),
        rows=tuple(rows),
    )


def _anchor_bolt_rows(model: ResolvedModel) -> list[tuple[str, ...]]:
    """Authored cast-in bolts by product. ``Connector`` holds no diameter or embedment.

    A bolt that fastens a deck LEDGER (``Beam.ledger_on``) is not sill anchorage and is left
    out: it is the deck's attachment, graded by ``structural.deck_ledger``. Letting one in
    would also displace every derived mudsill anchor below. A hold-down's anchor (an SSTB
    under an HTT) is the hold-down's, not the plate's, and is left out for the same reason.
    """
    from typehaus.hardware.catalog import ROLE_HOLDOWN_ANCHOR_BOLT, hardware_by_model
    from typehaus.model.enums import ConnectorKind
    from typehaus.model.structure import is_ledger

    bolts = [e for e in model.plan.all_elements()
             if e.element_kind == "Connector"
             and getattr(e, "kind", None) is ConnectorKind.ANCHOR_BOLT
             and getattr(hardware_by_model(str(getattr(e, "size", "") or "")), "role",
                         None) != ROLE_HOLDOWN_ANCHOR_BOLT
             and not any(is_ledger(model.plan.by_tag(tag))
                         for tag in getattr(e, "connects", ()))]
    grouped: dict[str, list[Any]] = {}
    for bolt in sorted(bolts, key=lambda e: e.tag):
        grouped.setdefault(str(getattr(bolt, "size", "") or ""), []).append(bolt)
    rows: list[tuple[str, ...]] = []
    for index, (size, items) in enumerate(sorted(grouped.items()), start=1):
        walls = sorted({tag for bolt in items for tag in getattr(bolt, "connects", ())})
        rows.append((f"A{index}", "CAST-IN BOLT", size or "NOT STATED",
                     "PER PLAN", str(len(items)), _abbreviate(", ".join(walls), 20)))
    return rows


def _mudsill_anchor_schedule_rows(model: ResolvedModel) -> list[tuple[str, ...]]:
    """Strap anchors along the sill-plate construction returns.

    The per-run count repeats ``takeoff/anchors.mudsill_anchor_rows``'s rule rather than
    calling it: that function answers for the whole house, this table per condition.
    ``takeoff`` is the authority and the two must agree — asserted in
    ``test_structural_sheets``.
    """
    from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG
    from typehaus.joints.sills import anchored_sill_returns, mudsill_anchor_stations
    from typehaus.takeoff.anchors import mudsill_anchor_rows

    config = DEFAULT_HARDWARE_TAKEOFF_CONFIG
    rules = config.sill_plate_anchors
    returns = anchored_sill_returns(model, config.sill_plate_takeoff_category)
    if not returns:
        return []
    takeoff = mudsill_anchor_rows(model, rules, config.sill_plate_takeoff_category)
    from typehaus.hardware.catalog import hardware_for_role
    from typehaus.joints.sills import sill_anchor_role

    def part_of(ret) -> str:
        return hardware_for_role(sill_anchor_role(ret)).model if takeoff else "NOT STATED"
    wall_tags = {wall.tag for wall in model.walls}
    foundation_tags = {wall.tag for wall in foundation_walls(model)}
    grouped: dict[tuple[str, str], list[Any]] = {}
    for ret in returns:
        host = ret.element_tags[0] if ret.element_tags else ""
        kind = ("FDN WALL" if host in foundation_tags
                else "SLAB" if host in {solid.tag for solid in model.solids}
                else "CONCRETE")
        grouped.setdefault((ret.storey, kind, part_of(ret)), []).append(ret)
    pitch_m = rules.mudsill_anchor_pitch_ft * FT_TO_M
    counts = {key: sum(max(rules.minimum_anchors_per_run,
                           int(math.floor(ret.length_m / pitch_m + 1e-9)) + 1) for ret in runs)
              for key, runs in grouped.items()}
    # The anchors ``joints/sills`` adds at wall-top block stations are on foundation walls.
    located = Counter((st.storey, hardware_for_role(st.role).model) for st in
                      mudsill_anchor_stations(model, rules, config.sill_plate_takeoff_category))
    for (storey, part), n in located.items():
        if (storey, "FDN WALL", part) in counts:
            counts[(storey, "FDN WALL", part)] += n - sum(
                c for (s, _k, q), c in counts.items() if (s, q) == (storey, part))
    rows: list[tuple[str, ...]] = []
    for index, ((storey, kind, part), runs) in enumerate(sorted(grouped.items()), start=1):
        count = counts[(storey, kind, part)]
        carried = sorted({tag for ret in runs for tag in ret.element_tags[1:]
                          if tag in wall_tags})
        # Narrow on purpose: this column sits beside the plan and a wide table costs the
        # drawing a scale step. The per-run minimum rides in a sheet note; the walls
        # carried are named by the first tag and a count.
        walls = (f"{carried[0]} +{len(carried) - 1}" if len(carried) > 1
                 else carried[0] if carried else f"{len(runs)} RUNS")
        rows.append((
            f"A{index}", f"{kind} — {storey.upper()}", part,
            f"{feet_inches(rules.mudsill_anchor_pitch_ft / M_TO_FT)} O.C.",
            str(count), walls))
    return rows
