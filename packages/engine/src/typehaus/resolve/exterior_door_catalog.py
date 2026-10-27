"""Coordinate catalog sections and evidence; clearance is not assembly certification."""

from dataclasses import replace
from math import sqrt

from typehaus.engineering.exterior_door_support import cantilever_support_report
from typehaus.resolve.exterior_door_catalog_layout import catalog_installation_layout
from typehaus.resolve.exterior_door_catalog_parts import catalog_sill_sections

_IN = 0.0254


def add_catalog_installation(model, wall, opening, assembly, clad):
    placement = assembly.exterior_placement
    installation = placement.specification
    spec = installation.catalog_installation
    layout = catalog_installation_layout(model, wall, opening, assembly, clad)
    sections = catalog_sill_sections(spec, installation, placement, opening, layout)
    unknown, conflicts = (list(assembly.unknown), list(assembly.conflicts))
    support = cantilever_support_report(spec, layout.projection, layout.spacing)
    if not any(item.tag == spec.support_ref for item in (*model.walls, *model.floors)):
        conflicts.append(f"approach support reference {spec.support_ref} does not resolve")
    if support["member_status"] == "FAIL":
        conflicts.append("catalog approach support member exceeds strength or deflection limit")
    if support["connection_status"] == "UNKNOWN":
        unknown.append(
            "approach root connection capacity/development is undocumented; "
            "member calculations do not verify the load path"
        )
    elif support["connection_status"] == "FAIL":
        conflicts.append("approach support connection exceeds its documented capacity")
    if layout.end >= layout.outlet:
        conflicts.append("catalog sill leaves no exterior approach")
    if layout.approach_front - layout.thickness <= layout.pan_front + layout.membrane:
        conflicts.append("catalog approach blocks the membrane drainage path")
    if layout.crest - spec.receiver_depth.meters < layout.seat + spec.receiver_pan_clearance.meters:
        conflicts.append(
            "FLA receiver drilling reaches the pan; coordinate cap setting or receiver"
        )
    report = _installation_report(assembly, placement, spec, layout, support)
    if layout.landing_gap is not None and layout.landing_gap <= spec.movement_horizontal.meters:
        conflicts.append("house/deck movement closes the approach gap")
    if spec.flashing_overlap.meters <= spec.movement_vertical.meters:
        conflicts.append("house/deck movement exhausts flashing overlap")
    unknown.extend(
        (
            "AridDek approach is an outer envelope; board/rib and cross-bearer drainage "
            "detailing needs installed sections",
            "catalog outline does not establish installed sweep compression or hinge datum",
            "SureSill installed section, compatible apron bond and pan-to-sill sealant "
            "remain unconfirmed",
        )
    )
    conflicts.extend(
        _opening_coordination_conflicts(model, opening, installation, spec, layout, report)
    )
    boards = tuple(
        replace(
            b,
            height_m=b.height_m + b.z_m - b.height_m / 2 - layout.seat,
            z_m=(b.z_m + b.height_m / 2 + layout.seat) / 2,
        )
        if "jamb" in b.name
        else b
        for b in placement.boards
    )
    placement = replace(
        placement,
        boards=boards,
        sections=tuple(sections),
        sill_design_status="CATALOG_DESIGN",
        threshold_crest_z_m=layout.crest,
        threshold_upper_z_m=layout.crest + spec.height_tolerance.meters,
        installation_report=report,
    )
    from typehaus.resolve.exterior_door_catalog_flashing import catalog_flashing_sections

    placement = replace(
        placement,
        sections=(
            *placement.sections,
            *catalog_flashing_sections(placement, opening, assembly, clad),
        ),
    )
    from typehaus.resolve.exterior_door_catalog_fit import (
        catalog_drainage_conflicts,
        catalog_seat_conflicts,
    )

    conflicts.extend(catalog_drainage_conflicts(placement))
    seat_conflicts = catalog_seat_conflicts(model, wall, opening, placement)
    report["seat_interference_status"] = "FAIL" if seat_conflicts else "PASS"
    report["seat_interference_conflicts"] = seat_conflicts
    conflicts.extend(seat_conflicts)
    unknown.append(
        "stock HeadFlash and silicone end-transition outlines require "
        "installed sections/bond evidence"
    )
    return replace(
        assembly,
        exterior_placement=placement,
        unknown=tuple(unknown),
        conflicts=tuple(conflicts),
        leaf_bottom_z_m=layout.crest + 0.125 * _IN,
        jamb_bottom_z_m=layout.seat,
    )


def _installation_report(assembly, placement, spec, layout, support):
    sign = placement.outward_sign
    exterior = assembly.adjacent_floors[0 if sign < 0 else 1]
    interior = assembly.adjacent_floors[1 if sign < 0 else 0]
    floor_report = {}
    for name, floor in (("interior", interior), ("exterior", exterior)):
        floor_report[f"{name}_surface_z_m"] = floor.surface_m if floor else None
        floor_report[f"crest_above_{name}_in"] = (
            (layout.crest - floor.surface_m) / _IN
            if floor and floor.surface_m is not None
            else None
        )
    receiver_clearance = layout.crest - spec.receiver_depth.meters - layout.seat
    return dict(
        **floor_report,
        source_url=spec.source_url,
        source_drawing=spec.source_drawing,
        sill_extender_ref=spec.sill_extender_ref,
        sill_extender_source_url=spec.sill_extender_source_url,
        sill_extender_depth_in=spec.sill_extender_depth.meters / _IN,
        profile_status="DIGITIZED_OUTLINE",
        approach_outlet_depth_m=layout.outlet,
        landing_edge_depth_m=layout.landing_edge,
        pan_product=spec.pan_product,
        pan_height_basis="maximum published allowance; installed pan section pending",
        support=support,
        installation_complete=False,
        approach_board_count=layout.board_count,
        approach_board_cut_length_in=(layout.outlet - layout.end) / _IN,
        support_count=layout.count,
        support_spacing_in=layout.spacing / _IN,
        nominal_crest_z_m=layout.crest,
        conservative_crest_z_m=layout.crest + spec.height_tolerance.meters,
        approach_back_z_m=layout.approach_back,
        approach_front_z_m=layout.approach_front,
        approach_slope=layout.slope,
        drainage_clearance_in=(
            layout.approach_front - layout.thickness - layout.pan_front - layout.membrane
        )
        / _IN,
        receiver_pan_clearance_in=receiver_clearance / _IN,
        movement_gap_in=layout.landing_gap / _IN if layout.landing_gap is not None else None,
        minimum_movement_gap_in=(layout.landing_gap - spec.movement_horizontal.meters) / _IN
        if layout.landing_gap is not None
        else None,
        minimum_flashing_overlap_in=(spec.flashing_overlap.meters - spec.movement_vertical.meters)
        / _IN,
    )


def _opening_coordination_conflicts(model, opening, installation, spec, layout, report):
    conflicts = []
    if installation.exterior_opening_ref:
        reveal = next(o for o in model.openings if o.tag == installation.exterior_opening_ref)
        veneer = model.wall(reveal.host_wall)
        clear_half = layout.unit_width / 2 - installation.return_thickness.meters
        rise = reveal.arch_rise_m
        head_z = veneer.base_ref_z_m + reveal.sill_m + reveal.height_m
        if rise:
            radius = ((reveal.width_m / 2) ** 2 + rise**2) / (2 * rise)
            head_z += sqrt(max(0, radius**2 - clear_half**2)) - radius
        report["minimum_reveal_clear_height_in"] = (
            head_z - layout.crest - spec.height_tolerance.meters
        ) / _IN
        if report["minimum_reveal_clear_height_in"] < 78:
            conflicts.append("brick reveal leaves less than the 78 inch project clear headroom")
    if installation.seat_opening_ref:
        notch = next((o for o in model.openings if o.tag == installation.seat_opening_ref), None)
        curb = model.wall(notch.host_wall) if notch else None
        if (
            curb is None
            or abs(curb.base_ref_z_m + notch.sill_m - layout.base) > 0.001
            or notch.width_m + 0.001 < opening.width_m
        ):
            conflicts.append("concrete seat opening does not match the door elevation/width")
    return conflicts
