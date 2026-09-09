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
from dataclasses import dataclass, field

from typehaus.emit.draw.foundation_notes import (
    _under_slab_note,
    foundation_general_notes,
    foundation_sheet_findings,
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
from typehaus.resolve.model import ResolvedModel, ResolvedSolid, ResolvedWall
from typehaus.takeoff.hardware_config import FT_TO_M

# ``foundation_general_notes`` and ``foundation_sheet_findings`` moved to
# ``foundation_notes`` and are re-exported here: S-100's builder and two test modules import
# them from this module, and the split is an internal one.
__all__ = [
    "FoundationMarks",
    "bearing_solids",
    "build_foundation_schedules",
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
    """Slabs that bear on grade, so they belong on the foundation sheet.

    A slab is excluded when the model shows something carrying it: a joisted deck at the
    same plane (composite porch decking over ``FS-SG-PORCH``), a room on a lower storey
    inside its footprint (the main deck over the basement), or WALLS whose plates top out at
    the slab's own underside (RM-M-BATH2's tub-deck cap on its knee walls). All three are
    structural decks and are drawn on the framing sheets instead.

    All three clauses share one argument: ``Slab`` is the model's only horizontal-sheet
    element that can leave its storey datum, so it carries laid decking and framed
    platforms as well as flatwork, and this sheet must
    print only what actually bears on the ground. Elevation alone will not separate them —
    SL-G-STEP-0 is a real 6" pour 6" above its datum — so the test is "does the model show
    something under it", which is what the other two clauses already ask.
    """
    storey_elevation = {storey.tag: storey.elevation.meters for storey in model.plan.storeys}
    out: list[ResolvedSolid] = []
    for solid in model.solids:
        if solid.category != "slab":
            continue
        if (_carried_by_deck(model, solid) or _carried_by_walls(model, solid)
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


def _carried_by_walls(model: ResolvedModel, slab: ResolvedSolid) -> bool:
    """Whether walls on the slab's own storey top out at its underside and stand under it.

    The framed-platform case: a knee-wall box with a sheet capping it. Every clause is load
    bearing here, and the first two exist because SL-B-FLOOR flunked the naive version.

      * NOT a foundation wall. A slab-on-grade meets the stems around it at its own
        underside all day long; that is abutment, not support.
      * The wall's plate is ABOVE its storey datum. A platform stands on the floor and
        carries something over it. Anything topping out at or below the datum is part of
        the substructure the slab is poured against.
      * Plates at the slab's underside AND a footprint under it. Plenty of walls top out at
        20" somewhere in a house and plenty stand under a given outline at some other
        height; only a wall doing both is carrying anything.
    """
    slab_box = outline_bbox(slab.outline)
    datum = next((storey.elevation.meters for storey in model.plan.storeys
                  if storey.tag == slab.storey), 0.0)
    for wall in model.walls:
        if wall.storey != slab.storey or wall.is_foundation:
            continue
        if wall.z1_m <= datum + DECK_COINCIDENCE_TOLERANCE_M:
            continue
        if abs(wall.z1_m - slab.z0_m) > DECK_COINCIDENCE_TOLERANCE_M:
            continue
        points = [point for layer in wall.layers for point in layer.polygon]
        if points and bboxes_overlap(slab_box, outline_bbox(points)):
            return True
    return False


def _room_below(model: ResolvedModel, slab: ResolvedSolid,
                storey_elevation: dict[str, float]) -> bool:
    slab_box = outline_bbox(slab.outline)
    for room in model.rooms:
        if storey_elevation.get(room.storey, 0.0) >= slab.z0_m:
            continue
        if len(room.clear_face) >= 3 and point_in_bbox(outline_center(room.clear_face), slab_box):
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
    sill anchorage, reinforcement. An empty table is dropped rather than printed as a
    heading over nothing."""
    marks = foundation_marks(model)
    tables = [_bearing_schedule(model, marks), _wall_schedule(model, marks),
              _slab_schedule(model, marks), anchorage_schedule(model),
              reinforcement_schedule(model)]
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


def _wall_schedule(model: ResolvedModel, marks: FoundationMarks) -> ScheduleTable:
    grouped: dict[str, list[ResolvedWall]] = {}
    for wall in foundation_walls(model):
        grouped.setdefault(marks.wall[wall.tag], []).append(wall)
    rows: list[tuple[str, ...]] = []
    for mark, walls in sorted(grouped.items(), key=lambda item: _mark_order(item[0])):
        sample = walls[0]
        run_ft = sum(wall_length_m(wall) for wall in walls) * M_TO_FT
        rows.append((mark, sample.assembly, inches(sample.thickness_m), f"{run_ft:,.0f} LF",
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
    """Authored cast-in bolts, grouped by product. ``Connector`` holds no diameter or
    embedment, so the schedule states the model number and says where the rest lives."""
    from typehaus.model.enums import ConnectorKind

    bolts = [e for e in model.plan.all_elements()
             if e.element_kind == "Connector" and e.kind is ConnectorKind.ANCHOR_BOLT]
    grouped: dict[str, list] = {}
    for bolt in sorted(bolts, key=lambda e: e.tag):
        grouped.setdefault(bolt.size or "", []).append(bolt)
    rows = []
    for index, (size, items) in enumerate(sorted(grouped.items()), start=1):
        walls = sorted({tag for bolt in items for tag in bolt.connects})
        rows.append((f"A{index}", "CAST-IN ANCHOR BOLT", size or "NOT STATED",
                     "AUTHORED PER BOLT — SEE PLAN", str(len(items)),
                     _abbreviate(", ".join(walls))))
    return rows


def _mudsill_anchor_schedule_rows(model: ResolvedModel) -> list[tuple[str, ...]]:
    """Strap anchors along the sill-plate construction returns.

    The per-run count repeats ``takeoff/anchors.mudsill_anchor_rows``'s rule rather than
    calling it: that function answers for the whole house, this table per condition.
    ``takeoff`` is the authority and the two must agree — asserted, not hoped for, in
    ``test_structural_sheets``.
    """
    from typehaus.takeoff.anchors import mudsill_anchor_rows
    from typehaus.takeoff.hardware_config import DEFAULT_HARDWARE_TAKEOFF_CONFIG

    config = DEFAULT_HARDWARE_TAKEOFF_CONFIG
    rules = config.sill_plate_anchors
    returns = [ret for ret in model.construction_returns
               if ret.takeoff_category == config.sill_plate_takeoff_category]
    if not returns:
        return []
    takeoff = mudsill_anchor_rows(model, rules, config.sill_plate_takeoff_category)
    part = str(takeoff[0]["part_number"]) if takeoff else "NOT STATED"
    wall_tags = {wall.tag for wall in model.walls}
    foundation_tags = {wall.tag for wall in foundation_walls(model)}
    grouped: dict[tuple[str, str], list] = {}
    for ret in returns:
        host = ret.element_tags[0] if ret.element_tags else ""
        kind = ("FOUNDATION WALL" if host in foundation_tags
                else "SLAB" if host in {solid.tag for solid in model.solids}
                else "CONCRETE")
        grouped.setdefault((ret.storey, kind), []).append(ret)
    rows = []
    for index, ((storey, kind), runs) in enumerate(sorted(grouped.items()), start=1):
        count = sum(max(rules.minimum_anchors_per_run,
                        int(math.floor(ret.length_m / (rules.mudsill_anchor_pitch_ft
                                                       * FT_TO_M) + 1e-9)) + 1)
                    for ret in runs)
        carried = sorted({tag for ret in runs for tag in ret.element_tags[1:]
                          if tag in wall_tags})
        rows.append((
            f"A{index}", f"SILL PLATE ON {kind} — {storey.upper()}", part,
            f"{feet_inches(rules.mudsill_anchor_pitch_ft / M_TO_FT)} O.C. "
            f"(MIN {rules.minimum_anchors_per_run} PER PLATE RUN)",
            str(count), _abbreviate(", ".join(carried)) or f"{len(runs)} SILL RUN(S)"))
    return rows


def reinforcement_schedule(model: ResolvedModel) -> ScheduleTable:
    """The steel in the foundation pours, one row per bar role.

    Reads ``ReinforcementSpec`` off the elements S-100 draws and prints nothing where a
    pour carries none: ACI 318-19 §14.1.4 permits plain concrete in a footing, so an absent
    spec is a legal condition, not a hole to fill with a plausible mat. ELEMENT keys back
    through the sheet's own marks (FW1, F2, S3), which the reader can find on the drawing.
    """
    from typehaus.resolve.concrete import concrete_spec_of

    marks = foundation_marks(model)
    mark_of = {**marks.wall, **marks.footing, **marks.pad, **marks.slab}
    grouped: dict[tuple, list[tuple[str, str]]] = {}
    specs: dict[tuple, object] = {}
    for element in _reinforced_elements(model):
        spec = element.reinforcement
        key = (element.element_kind, spec.model_dump_json()
               if hasattr(spec, "model_dump_json") else repr(spec),
               _cover_text(spec, concrete_spec_of(model.plan, getattr(element, "assembly",
                                                                     None))))
        grouped.setdefault(key, []).append(
            (mark_of.get(element.tag, element.tag), element.tag))
        specs[key] = spec
    rows: list[tuple[str, ...]] = []
    for index, (key, members) in enumerate(sorted(grouped.items(),
                                                  key=lambda item: item[0][0]), start=1):
        spec = specs[key]
        element_kind, _identity, cover = key
        keys = _abbreviate(", ".join(sorted({mark for mark, _tag in members})), 20)
        lap = f"CLASS {spec.lap_class}" if spec.lap_class else "NOT STATED"
        for bar in spec.bars:
            quantity = (f'{bar.spacing.inches:g}" O.C.' if bar.spacing is not None
                        else f"({bar.count})" if bar.count is not None else "NOT STATED")
            rows.append((f"R{index}", f"{keys} ({len(members)})",
                         bar.role.upper(), f"#{bar.bar}", quantity,
                         str(bar.layers), cover, lap))
    return ScheduleTable(
        title="FOUNDATION REINFORCEMENT SCHEDULE",
        columns=("MARK", "ELEMENT", "ROLE", "BAR", "SPACING/COUNT", "LAYERS", "COVER",
                 "LAP"),
        rows=tuple(rows),
    )


def _reinforced_elements(model: ResolvedModel) -> list:
    """Foundation-scope pours carrying an authored ``ReinforcementSpec``, in tag order.

    The four element kinds this sheet draws as foundation. A cast pier is a ``Post`` with a
    cage of its own and is scheduled with the column it is, not here.
    """
    kinds = {"FoundationWall", "Footing", "Pad", "Slab"}
    return sorted((element for element in model.plan.all_elements()
                   if element.element_kind in kinds
                   and getattr(element, "reinforcement", None) is not None),
                  key=lambda element: element.tag)


def _cover_text(spec, concrete) -> str:
    """The element's own cover, else the mix's, else the truth. The element outranks the
    mix by design: a stem cast against earth buys cover the plant ticket knows nothing
    about."""
    if spec.cover is not None:
        return f'{spec.cover.inches:.2g}"'
    if concrete is not None and concrete.cover is not None:
        return f'{concrete.cover.inches:.2g}" (MIX)'
    return "NOT STATED"
