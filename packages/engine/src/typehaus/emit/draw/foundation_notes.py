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

from typing import TYPE_CHECKING, Any

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
    notes.extend(_dampproofing_notes(model))
    notes.extend(radon_control_notes(model))
    notes.append("FOOTING, PAD, WALL AND SLAB GEOMETRY IS RESOLVED FROM THE PLAN SOURCE; "
                 "SIZES ARE AUTHORED, NOT ENGINEERED.")
    return notes


def _water_control_layers(assembly: Any) -> list[Any]:
    """Layers that dampproof the earth face, by the criterion ``code.R406_1_dampproofing``
    uses — one definition, so the sheet and the verdict cannot disagree about one wall."""
    return [layer for layer in assembly.layers
            if ControlLayer.WATER in (layer.control or set())
            and layer.function in (LayerFunction.MEMBRANE, LayerFunction.SHEATHING,
                                   LayerFunction.CLADDING)]


def _dampproofing_notes(model: ResolvedModel) -> list[str]:
    """R406.1 — what actually dampproofs each foundation-wall assembly, named.

    Assembly by assembly rather than wall by wall: dampproofing is a layer, and a house
    with thirteen basement walls has two or three answers, not thirteen. Walls whose
    assembly carries no water-control layer are listed but not judged — whether R406.1
    reaches a given wall is ``code.R406_1_dampproofing``'s question (it also asks whether
    the wall encloses space below grade, which this sheet does not re-derive).
    """
    from typehaus.emit.draw.foundation_schedule import foundation_walls

    by_assembly: dict[str, list[str]] = {}
    for wall in foundation_walls(model):
        by_assembly.setdefault(wall.assembly, []).append(wall.tag)
    notes, bare = [], []
    for assembly_tag, tags in sorted(by_assembly.items()):
        assembly = model.plan.library.resolve_assembly(assembly_tag)
        proofed = _water_control_layers(assembly) if assembly is not None else []
        if proofed:
            notes.append(f"DAMPPROOFING (IRC R406.1): {assembly_tag} "
                         f"({len(tags)} WALL(S)) CARRIES '{proofed[0].name.upper()}' — "
                         f"{_layer_thickness(proofed[0])} "
                         f"{proofed[0].material_ref.upper()} — ON THE EARTH FACE, FROM THE "
                         "TOP OF FOOTING TO FINISHED GRADE.")
        else:
            bare.append(assembly_tag)
    if bare:
        notes.append("NO WATER-CONTROL LAYER IS MODELLED IN " + ", ".join(bare)
                     + "; SEE code.R406_1_dampproofing FOR WHICH OF THESE R406.1 REACHES.")
    return notes


def radon_control_notes(model: ResolvedModel) -> list[str]:
    """MN 1303.2400-.2402 passive soil-gas control, item by item off the model.

    The rule has eight field items and this model carries five of them. Each line is
    derived or says "NOT MODELLED" against its own subpart — never a plausible default,
    which on a radon system would be a sheet telling an installer something nobody decided.
    """
    from typehaus.model.enums import DeviceKind, PipeSystem
    from typehaus.model.mep import Sump, VentRun

    notes = ["RADON CONTROL — MN 1303.2400 (PASSIVE SOIL-GAS SYSTEM). THE ITEMS BELOW ARE "
             "READ OFF THIS MODEL; ANYTHING MARKED NOT MODELLED IS A FIELD ITEM."]
    notes.extend(_soil_gas_course_notes(model))
    sumps = [e for e in model.plan.all_elements()
             if isinstance(e, Sump) and e.radon_vent]
    risers = [e for e in model.plan.all_elements()
              if isinstance(e, VentRun) and PipeSystem.RADON in e.systems]
    if sumps:
        notes.append("SUBP. 3-4: COLLECTION POINT " + ", ".join(
            f"{sump.tag} ({sump.diameter.inches:.0f}\" PIT, "
            f"{'SEALED' if sump.sealed_cover else 'UNSEALED'} COVER, VENT "
            f"{sump.vent_ref or 'NOT NAMED'})" for sump in sorted(sumps, key=lambda s: s.tag))
            + ". THE 10 FT OF PERFORATED PIPE UNDER THE MEMBRANE IS NOT MODELLED.")
    else:
        notes.append("SUBP. 3: NO SEALED COLLECTION POINT IS MODELLED.")
    notes.extend(_radon_riser_notes(model, risers))
    notes.append("SUBP. 5: \"RADON GAS VENT SYSTEM\" LABELLING AT EACH STOREY AND THE 24\" "
                 "CLEAR FOR A FUTURE FAN ARE NOT MODELLED — FIELD ITEMS.")
    notes.extend(_fan_power_notes(model, risers, DeviceKind))
    return notes


def _soil_gas_course_notes(model: ResolvedModel) -> list[str]:
    """Subpart 2's gas-permeable course and the membrane over it, per interior slab.

    Read as "the stack the slab assembly puts below its structure", which is the same
    reading ``_under_slab_note`` prints in the slab schedule. The model states a material
    and a thickness; it states no aggregate gradation and no membrane lap, and the note
    says so rather than printing the code minimum as though someone had authored it.
    """
    from typehaus.emit.draw.foundation_schedule import slabs_on_grade

    lines = []
    for slab in slabs_on_grade(model):
        if not _within_the_building(model, slab):
            continue
        stack = _under_slab_note(model, slab)
        if not stack:
            lines.append(f"SUBP. 2: {slab.tag} HAS NO UNDER-SLAB STACK MODELLED — NO "
                         "GAS-PERMEABLE COURSE AND NO SOIL-GAS MEMBRANE.")
            continue
        lines.append(f"SUBP. 2: {slab.tag} — {stack} (OUTBOARD OF THE POUR). AGGREGATE "
                     "GRADATION AND THE 12\" MEMBRANE LAP ARE NOT MODELLED.")
    return lines


def _radon_riser_notes(model: ResolvedModel, risers: list[Any]) -> list[str]:
    """Subpart 5's vent: which run, how big, and where its derived terminus is."""
    from typehaus.resolve.vent_termination import derived_termination_elevation

    if not risers:
        return ["SUBP. 5: NO VENT RUN CARRIES THE RADON SYSTEM."]
    lines = []
    for riser in sorted(risers, key=lambda r: r.tag):
        top = derived_termination_elevation(model, riser)
        terminus = (f"TERMINATING {elevation_feet(top)} (DERIVED, 12\" ABOVE THE ROOF "
                    "SURFACE)" if top is not None else
                    "WITH NO DERIVABLE ROOF TERMINATION")
        lines.append(f"SUBP. 5: VENT {riser.tag}, {riser.diameter.inches:.0f}\" DIA., "
                     f"{terminus}. THE 12\" AND THE 10 FT TO AN OPENING ARE GRADED BY "
                     "code.MN_1303_2402_radon AND mep.vent_termination_height.")
    return lines


def _fan_power_notes(model: ResolvedModel, risers: list[Any],
                     device_kind: Any) -> list[str]:
    """Subpart 6 — an approved box at the anticipated fan location.

    Reach and riser point come from the check that grades this, so the sheet names the
    same box the verdict does rather than a second nearest-box rule.
    """
    from typehaus.checks.code.mn_residential.radon import _FAN_BOX_REACH
    from typehaus.resolve.vent_termination import exterior_riser_point

    if not risers:
        return []
    boxes: list[Any] = [e for e in model.plan.all_elements()
                        if getattr(e, "element_kind", None) == "ElectricalDevice"
                        and getattr(e, "kind", None) is device_kind.JUNCTION_BOX]
    # A box that declares a ROOM is skipped, and that is the conservative half of the
    # check's own rule rather than a second one: the reach test is plan-only in a
    # four-storey house, so a lighting supply two floors up falls inside the radius, and
    # subpart 6 forbids the fan's box in conditioned space anyway. A box with no room is
    # outside the building, which is where the rule wants this one.
    named = []
    for riser in sorted(risers, key=lambda r: r.tag):
        rx, ry = exterior_riser_point(riser)
        for box in boxes:
            if getattr(box, "room", None):
                continue
            bx, by = box.position.xy_m
            if ((bx - rx) ** 2 + (by - ry) ** 2) ** 0.5 <= _FAN_BOX_REACH.meters:
                named.append(box.tag)
    if named:
        return [f"SUBP. 6: POWER FOR A FUTURE FAN AT {', '.join(sorted(set(named)))}, "
                f"WITHIN {_FAN_BOX_REACH.inches / 12:.0f} FT OF THE RISER."]
    return ["SUBP. 6: NO JUNCTION BOX IS MODELLED WITHIN "
            f"{_FAN_BOX_REACH.inches / 12:.0f} FT OF THE RISER FOR A FUTURE FAN."]


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
    """What S-100 cannot say about sill anchorage — which is now only the empty case.

    ``ConnectorKind.ANCHOR_BOLT`` lets a house author cast-in bolts, and the take-off
    separately derives strap anchors off the sill runs at a stated pitch. Either is real
    anchorage and both now SCHEDULE (``anchorage_schedule``); what used to be a WARN over a
    hundred and thirty-seven derived anchors was the sheet declining to print a number it
    was already holding. The finding survives for the house that models neither.
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
        return []  # derived anchors, scheduled by mark on the sheet
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
    # ``Slab.reinforcement`` exists now, so this reports the pours that state none rather
    # than the schema that could not hold one. A plain slab is legal; a plain slab the
    # sheet is silent about is not, which is why it is still named here.
    unreinforced = [slab.tag for slab in slabs
                    if getattr(model.plan.by_tag(slab.tag), "reinforcement", None) is None]
    if unreinforced:
        findings.append(Finding(
            severity=Severity.WARN, check_id="sheet.foundation.slab_reinforcement",
            message="no slab on grade carries a ReinforcementSpec, so S-100 shows no slab "
                    "reinforcement callout: " + ", ".join(unreinforced),
            element_tags=tuple(unreinforced), result=Result.UNKNOWN,
            fix_hint="author reinforcement=ReinforcementSpec(bars=(BarSpec(...),)) on the "
                     "Slab, or record the decision to pour it plain",
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
    walls = foundation_walls(model)
    if walls:
        findings.extend(_sill_anchorage_findings(model))
    # Presence only. WHICH walls R406.1 reaches is code.R406_1_dampproofing's question and
    # it asks a second one this sheet does not re-derive (does the wall enclose space below
    # grade); a house with no water-control layer anywhere has nothing for either to print.
    if walls and not any(
            _water_control_layers(assembly)
            for assembly in {model.plan.library.resolve_assembly(wall.assembly)
                             for wall in walls} if assembly is not None):
        findings.append(Finding(
            severity=Severity.WARN, check_id="sheet.foundation.dampproofing",
            message="no foundation-wall assembly carries a water-control layer, so S-100 "
                    "shows no dampproofing callout (IRC R406.1)",
            element_tags=tuple(wall.tag for wall in walls)[:1], result=Result.UNKNOWN,
            fix_hint="add a MEMBRANE layer with control={WATER} outboard of the STRUCTURE "
                     "layer in the foundation wall assembly",
        ))
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
