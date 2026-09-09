"""S-100's prose half: the notes it prints, and the findings it prints instead of a value.

Split out of ``foundation_schedule`` (which keeps the marks and the keyed tables) when both
outgrew one file. Everything here answers "what does this sheet SAY", and the rule is the
same as next door: a note states what the model carries, and where the model is silent the
sheet reports the gap rather than printing a plausible default.

Imports of the selectors (``bearing_solids``, ``foundation_walls``, ``footing_steps``) are
function-local on purpose: ``foundation_schedule`` imports this module at the top to
re-export these names for its existing callers, so the module-level edge runs one way only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typehaus.findings import Finding, Result, Severity
from typehaus.model.assembly import Layer
from typehaus.model.enums import ControlLayer, LayerFunction
from typehaus.resolve.model import ResolvedModel, ResolvedSolid

if TYPE_CHECKING:
    from typehaus.checks.jurisdiction import JurisdictionProfile

from typehaus.emit.draw.structural_common import elevation_feet, feet_inches


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
    from typehaus.emit.draw.foundation_schedule import bearing_solids
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
    from typehaus.emit.draw.foundation_schedule import bearing_solids, footing_steps

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
    from typehaus.emit.draw.foundation_schedule import foundation_walls
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
    from typehaus.emit.draw.foundation_schedule import (
        bearing_solids,
        foundation_walls,
        slabs_on_grade,
    )

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
