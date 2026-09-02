"""S-100 content derivation: what the foundation sheet knows, and what it does not.

Splits the *reading* of the resolved model (which solids are foundation scope, what mark
each carries, what the schedule rows say, which required datum the model simply does not
have) away from the *drawing* in ``foundationplan``. Everything here is derived from
``ResolvedModel`` and the authored plan; nothing is invented. Where a permit-set datum is
missing — slab reinforcement, under-slab vapour retarder, sill anchorage — this module
returns a :class:`Finding` naming the missing input instead of printing a plausible value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

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
from typehaus.findings import Finding, Result, Severity
from typehaus.model.assembly import Layer
from typehaus.model.enums import ControlLayer, LayerFunction

if TYPE_CHECKING:
    from typehaus.checks.jurisdiction import JurisdictionProfile

from typehaus.resolve.model import ResolvedModel, ResolvedSolid, ResolvedWall

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
    """The keyed S-100 schedules: footings/pads, foundation walls, slabs on grade."""
    marks = foundation_marks(model)
    tables = [_bearing_schedule(model, marks), _wall_schedule(model, marks),
              _slab_schedule(model, marks)]
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


def _under_slab_note(model: ResolvedModel, slab: ResolvedSolid) -> str:
    """Everything the slab assembly stacks below its structural layer, outboard-first."""
    assembly = model.plan.library.resolve_assembly(slab.assembly) if slab.assembly else None
    if assembly is None:
        return ""
    structure_index = assembly.structure_index()
    if structure_index is None:
        return ""
    below = assembly.layers[structure_index + 1:]
    return ", ".join(f"{_layer_thickness(layer)} {layer.material_ref.upper()}"
                     for layer in below)


def _layer_thickness(layer: Layer) -> str:
    """A layer's thickness the way its own trade states it.

    A sheet membrane is specified in mils and is 0.010" thick, which the schedule's ``.0f``
    inches printed as ``0"`` — a callout for a layer of nothing. Anything under half an inch
    is a sheet good; say mils.
    """
    inches: float = layer.thickness.inches
    if inches < 0.5:
        return f"{inches * 1000.0:.0f} MIL"
    return f"{inches:.0f}\""


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


def foundation_general_notes(model: ResolvedModel,
                             profile: JurisdictionProfile | None = None) -> list[str]:
    """Sheet notes derived from the code profile and the resolved bedding/drainage records.

    The profile is passed in by the sheet that prints these notes, so the frost depth on
    S-100 is stated by the same jurisdiction the cover sheet and the checklist name.
    """
    from typehaus.checks.code.mn_residential.profile import DEFAULT_PROFILE_NAME, get_profile

    if profile is None:
        profile = get_profile(DEFAULT_PROFILE_NAME)
    notes: list[str] = []
    if profile.frost_depth_in is not None:
        notes.append(f"ALL FOOTINGS TO BEAR {profile.frost_depth_in:.0f}\" MIN BELOW THE "
                     f"LOWEST ADJACENT FINISHED GRADE (IRC R403.1.4.1) PER "
                     f"{profile.name.upper()} ({profile.edition}).")
        notes.extend(_lowest_adjacent_grade_notes(model, profile.frost_depth_in))
    notes.extend(_bearing_tier_notes(model))
    drainage = _drainage_note(model)
    if drainage:
        notes.append(drainage)
    notes.append("FOOTING, PAD, WALL AND SLAB GEOMETRY IS RESOLVED FROM THE PLAN SOURCE; "
                 "SIZES ARE AUTHORED, NOT ENGINEERED.")
    return notes


def _lowest_adjacent_grade_notes(model: ResolvedModel, frost_depth_in: float) -> list[str]:
    """Name the footings whose lowest adjacent grade is not the site grade plane.

    "ALL FOOTINGS TO BEAR 42\" MIN BELOW FINISHED GRADE" printed on this sheet for as long
    as it has existed, and on a site with an open sunken court beside the house it was
    simply false: the strips along that court bear 8" below the court floor, and the note
    told a reader — and an inspector — otherwise. The blanket claim is the thing that was
    wrong, not the number, so the note keeps the number and states the exceptions the
    geometry actually contains. Silent where there are none, which is most houses.
    """
    from typehaus.resolve.site_earth import (
        heated_floor_footprint,
        local_grade_elevation_m,
        open_excavation_floors,
    )

    reach_m = frost_depth_in * 0.0254
    floors = open_excavation_floors(model)
    if not floors:
        return []
    sheltered_by = heated_floor_footprint(model)
    shallow: list[tuple[str, float, str]] = []
    for solid in sorted(bearing_solids(model), key=lambda item: item.tag):
        grade_m, source = local_grade_elevation_m(
            model, solid.outline, reach_m, floors, sheltered_by)
        if source is None:
            continue
        cover_in = (grade_m - solid.z0_m) / 0.0254
        if cover_in < frost_depth_in - 1e-6:
            shallow.append((solid.tag, cover_in, source))
    if not shallow:
        return []
    sections = _declared_sections(model, frost_depth_in)
    replaced = [row for row in shallow if row[0] in sections]
    insulated = [row for row in shallow if row[0] not in sections]
    notes = ["THE LOWEST ADJACENT GRADE FOR " + ", ".join(
                f"{tag} ({cover:.0f}\" COVER)" for tag, cover, _ in shallow)
             + " IS THE FLOOR OF "
             + ", ".join(sorted({source for _, _, source in shallow}))
             + ", NOT THE SITE GRADE PLANE."]
    # Two different frost measures answer this condition and they carry different citations:
    # R403.3 for the house strips' wing insulation, but the garden's protection is the graded
    # stone section beneath it, not R403.3 — a blanket citation is wrong on the sheet an
    # inspector reads off.
    if insulated:
        notes.append("FROST PROTECTION FOR "
                     + ", ".join(tag for tag, _c, _s in insulated)
                     + " IS PER IRC R403.3 AND THE FOUNDATION DETAILS, NOT BY DEPTH.")
    if replaced:
        notes.append("FROST PROTECTION FOR "
                     + ", ".join(tag for tag, _c, _s in replaced)
                     + " IS BY SOIL REPLACEMENT: EACH BEARS ON A DRAINED "
                     "NON-FROST-SUSCEPTIBLE SECTION REACHING "
                     f"{frost_depth_in:.0f}\" MIN BELOW THAT GRADE (ASCE 32, "
                     "PER IRC R403.1.4.1). SECTION GRADATION PER THE FOUNDATION DETAILS.")
    return notes


def _declared_sections(model: ResolvedModel, frost_depth_in: float) -> set[str]:
    """Footing tags protected by a declared, drained aggregate section reaching frost depth.

    The three conditions are ``structural.frost_depth``'s, and that check is the authority —
    this exists so the sheet can *name the right citation per footing*, which needs the same
    split the check makes. Kept deliberately literal rather than clever so that a reader
    comparing the two can see they ask the same question; if the check's rule changes, this
    is the second place to change.
    """
    return {bed.host for bed in model.footing_beddings
            if bed.non_frost_susceptible is True and bed.drain_tile
            and (bed.z1_m - bed.z0_m) >= frost_depth_in * 0.0254 - 1e-9}


def _bearing_tier_notes(model: ResolvedModel) -> list[str]:
    """Name each distinct footing bearing plane, then each measured step between two runs."""
    elevations = sorted({round(solid.z0_m, 3) for solid in bearing_solids(model)})
    if len(elevations) < 2:
        return []
    notes = [f"FOOTINGS BEAR AT {len(elevations)} ELEVATIONS: "
             + ", ".join(elevation_feet(z) for z in elevations) + "."]
    for lower, upper, _at in footing_steps(model):
        notes.append(f"STEP FOOTING {feet_inches(upper.z0_m - lower.z0_m)} FROM "
                     f"{lower.tag} {elevation_feet(lower.z0_m)} UP TO "
                     f"{upper.tag} {elevation_feet(upper.z0_m)}.")
    return notes


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


def _drainage_note(model: ResolvedModel) -> str:
    """Where the perimeter tile discharges, read off the tile.

    A sheet note is a statement about the building, so it reads the field that makes the
    statement, and says so plainly when the tile does not.
    """
    beddings = [bedding for bedding in model.footing_beddings if bedding.drain_tile]
    if not beddings:
        return ""
    discharges = sorted({bedding.drain_tile_spec.discharge.strip().upper()
                         for bedding in beddings
                         if bedding.drain_tile_spec is not None
                         and bedding.drain_tile_spec.discharge})
    if not discharges:
        destination = "TO AN APPROVED OUTLET (NOT MODELLED)"
    else:
        destination = f"TO {', '.join(discharges)}"
    return (f"PERIMETER DRAIN TILE IN THE FOOTING BEDDING AT {len(beddings)} FOOTINGS,"
            f" DRAINING {destination}.")


def _sill_anchorage_findings(model: ResolvedModel) -> list[Finding]:
    """What S-100 can say about sill anchorage, which depends on what the model carries.

    ``ConnectorKind.ANCHOR_BOLT`` lets a house author cast-in bolts with a diameter and an
    embedment, and the take-off separately derives MASA mudsill anchors off the sill runs at
    a stated pitch — which IS modelled anchorage even though it is not a bolt. A flat "not
    modelled" would misreport a hundred and twenty-five derived anchors.
    """
    from typehaus.model.enums import ConnectorKind
    from typehaus.takeoff.anchors import mudsill_anchor_rows
    from typehaus.takeoff.hardware_config import DEFAULT_HARDWARE_TAKEOFF_CONFIG

    walls = tuple(wall.tag for wall in foundation_walls(model))[:1]
    if [e for e in model.plan.all_elements()
            if e.element_kind == "Connector" and e.kind is ConnectorKind.ANCHOR_BOLT]:
        return []  # a modelled bolt carries its own diameter/embedment; the schedule reads it

    config = DEFAULT_HARDWARE_TAKEOFF_CONFIG
    rows = mudsill_anchor_rows(model, config.sill_plate_anchors,
                               config.sill_plate_takeoff_category)
    if rows:
        pitch = config.sill_plate_anchors.mudsill_anchor_pitch_ft
        return [Finding(
            severity=Severity.WARN, check_id="sheet.foundation.sill_anchorage",
            message=(f"sill-plate anchorage is {rows[0]['count']} {rows[0]['part_number']} "
                     f"mudsill anchors at {pitch:g} ft o.c.; a cast strap has no bolt "
                     "diameter or embedment to schedule, so S-100 shows the pitch and not a "
                     "bolt spacing"),
            element_tags=walls, result=Result.UNKNOWN,
            fix_hint=("author Connector elements of kind ANCHOR_BOLT where a cast-in bolt is "
                      "wanted instead of, or beside, the strap"))]
    return [Finding(
        severity=Severity.WARN, check_id="sheet.foundation.sill_anchorage",
        message="sill-plate anchorage is not modelled — no sill-plate construction return "
                "reaches the anchor rule and no anchor-bolt Connector is authored, so S-100 "
                "shows no anchor spacing",
        element_tags=walls, result=Result.UNKNOWN,
        fix_hint="give the wall a sill-plate ConstructionRule, or author ANCHOR_BOLT "
                 "Connector elements with a diameter and an embedment")]


def foundation_sheet_findings(model: ResolvedModel) -> list[Finding]:
    """Permit-set datums S-100 must show that the model does not carry.

    Reported rather than drawn: a foundation sheet that prints "#4 @ 16" O.C. E.W." nobody
    authored is worse than one that says the input is missing.
    """
    findings: list[Finding] = []
    slabs = slabs_on_grade(model)
    if slabs:
        findings.append(Finding(
            severity=Severity.WARN, check_id="sheet.foundation.slab_reinforcement",
            message="slab reinforcement is not an authored input — Slab carries thickness and "
                    "assembly only, so S-100 shows no reinforcement callout",
            element_tags=tuple(slab.tag for slab in slabs), result=Result.UNKNOWN,
            fix_hint="add a reinforcement field to model.floors.Slab (bar size, spacing, "
                     "cover) and schedule it here",
        ))
    unretarded = [slab.tag for slab in slabs
                  if _within_the_building(model, slab)
                  and not _has_vapour_retarder(model, slab)]
    if unretarded:
        findings.append(Finding(
            severity=Severity.WARN, check_id="sheet.foundation.vapour_retarder",
            message="no under-slab vapour retarder in the slab assembly — no layer declares "
                    "the VAPOR control layer below the slab structure",
            element_tags=tuple(unretarded), result=Result.UNKNOWN,
            fix_hint="add a MEMBRANE layer with control={VAPOR} below the slab's STRUCTURE "
                     "layer in the slab assembly",
        ))
    if foundation_walls(model):
        findings.extend(_sill_anchorage_findings(model))
    unscheduled = [solid.tag for solid in bearing_solids(model)
                   if solid.category == "footing" and model.plan.by_tag(solid.tag) is None]
    if unscheduled:
        findings.append(Finding(
            severity=Severity.WARN, check_id="sheet.foundation.footing_size",
            message="footing solid has no authored Footing element, so its width/depth "
                    "cannot be scheduled", element_tags=tuple(unscheduled),
            result=Result.UNKNOWN))
    return findings


def _within_the_building(model: ResolvedModel, slab: ResolvedSolid) -> bool:
    """Is this a slab IRC R506.2.3 is talking about?

    R506.2.3 requires the retarder under a slab "in contact with the ground" *within the
    building*, and its exception names what is outside that: garages, utility buildings,
    unheated accessory structures, and flatwork not likely to be enclosed and heated later.
    Asked of every slab bearing on grade, this reported the garden's own floor and a garage
    step-down as missing a retarder they must not have — one under an exterior slab protects
    nothing, and traps water in a pour with weather on both sides of it.

    "Within the building" is read as "under a conditioned room", and deliberately NOT as "has
    a room over it": a garage slab has one, and R506.2.3 names garages in its exception.
    """
    from shapely.geometry import Polygon

    if len(slab.outline) < 3:
        return False
    footprint = Polygon(slab.outline)
    if not footprint.is_valid or footprint.area <= 0.0:
        return False
    covered = 0.0
    for room in model.rooms:
        if not room.conditioned or len(room.clear_face) < 3:
            continue
        face = Polygon(room.clear_face)
        if face.is_valid and face.area > 0.0:
            covered += footprint.intersection(face).area
    return bool(covered > 0.5 * footprint.area)


def _has_vapour_retarder(model: ResolvedModel, slab: ResolvedSolid) -> bool:
    assembly = model.plan.library.resolve_assembly(slab.assembly) if slab.assembly else None
    if assembly is None:
        return False
    structure_index = assembly.structure_index()
    below = assembly.layers[structure_index + 1:] if structure_index is not None else ()
    return any(ControlLayer.VAPOR in layer.control
               or layer.function is LayerFunction.MEMBRANE for layer in below)
