"""Catalog-profile door coordination, separate from ordered-assembly certification."""

from dataclasses import replace
from math import ceil

from typehaus.engineering.exterior_door_support import cantilever_support_report
from typehaus.resolve.exterior_door_sill import DoorInstallationSection

_IN = 0.0254


def add_catalog_installation(model, wall, opening, assembly, clad):
    placement = assembly.exterior_placement
    installation = placement.specification
    spec = installation.catalog_installation
    sign = placement.outward_sign
    inner = sign * placement.frame_inner_m
    # Keep the back of the factory sill clear of the pan's upstand.
    start = inner + installation.wrap_isolation_thickness.meters
    base = assembly.rough_opening_z_m
    seat = base + spec.pan_height.meters
    end = start + max(x for x, _ in spec.sill_outline_m)
    outlet = sign * clad + installation.casing_thickness.meters
    outlet += installation.drainage_gap.meters / 4
    exterior = assembly.adjacent_floors[0 if sign < 0 else 1]
    landing_gap = None
    landing_edge = None
    floor = next((f for f in model.floors if exterior and f.tag == exterior.deck_tag), None)
    if floor is not None:
        from shapely.geometry import LineString, Polygon

        from typehaus.resolve.geometry import opening_center, wall_frame

        center = opening_center(wall, opening)
        _, _, normal, _ = wall_frame(wall)
        ray = LineString(
            [
                (center[0] + normal[0] * sign * d, center[1] + normal[1] * sign * d)
                for d in (outlet, outlet + installation.landing_search.meters)
            ]
        )
        crossing = Polygon(floor.deck_outline, holes=list(floor.deck_voids)).intersection(ray)
        if not crossing.is_empty:
            depths = [
                sign * sum((p[i] - center[i]) * normal[i] for i in (0, 1))
                for line in getattr(crossing, "geoms", (crossing,))
                for p in getattr(line, "coords", ())
            ]
            if depths:
                edge = min(depths)
                landing_edge = edge
                outlet = max(outlet, edge - installation.drainage_gap.meters)
                landing_gap = edge - outlet
    crest = seat + max(z for _, z in spec.sill_outline_m)
    width = opening.width_m - 2 * installation.return_thickness.meters
    product = next(t for t in model.plan.library.door_types if t.tag == opening.type_ref)
    unit_width = (
        product.catalog_dimensions.unit_width.meters if product.catalog_dimensions else width
    )
    membrane = installation.wrap_isolation_thickness.meters
    sections = []
    unknown, conflicts = list(assembly.unknown), list(assembly.conflicts)

    def section(name, profile, material, key, span=width, along=0, purchase="site"):
        sections.append(
            DoorInstallationSection(
                name, tuple((sign * x, z) for x, z in profile), span, along, material, key, purchase
            )
        )

    def rectangle(name, x0, x1, z0, z1, material, key, **kwargs):
        if x1 <= x0 or z1 <= z0:
            raise ValueError(f"nonpositive catalog installation part {name}")
        section(name, ((x0, z0), (x1, z0), (x1, z1), (x0, z1)), material, key, **kwargs)

    section(
        "catalog-sill-outline",
        ((start + x, seat + z) for x, z in spec.sill_outline_m),
        spec.sill_material_ref,
        "door_hardware",
        span=unit_width,
        purchase="factory_included",
    )
    # AridDek runs in the drainage direction. Its standard profile trim covers the front ends.
    nose = (
        max(z for x, z in spec.sill_outline_m if x > 0.95 * max(x for x, _ in spec.sill_outline_m))
        + seat
    )
    slope = 1 / 48
    approach_back = max(seat + 0.5 * _IN, nose)
    approach_front = approach_back - (outlet - end) * slope
    thickness = spec.approach_thickness.meters
    board_count = ceil(width / spec.approach_board_width.meters)
    for index in range(board_count):
        board_width = min(
            spec.approach_board_width.meters, width - index * spec.approach_board_width.meters
        )
        along = -width / 2 + index * spec.approach_board_width.meters + board_width / 2
        section(
            f"ariddek-approach-board-envelope-{index}",
            (
                (end, approach_back - thickness),
                (outlet, approach_front - thickness),
                (outlet, approach_front),
                (end, approach_back),
            ),
            spec.approach_material_ref,
            "floor",
            span=board_width,
            along=along,
        )
    rectangle(
        "ariddek-stock-profile-trim",
        outlet,
        outlet + membrane,
        approach_front - thickness,
        approach_front,
        spec.approach_material_ref,
        "floor",
    )
    membrane = installation.wrap_isolation_thickness.meters
    slope = 1 / 48
    # The stock pan drains down the curb face into a lower apron beneath the approach.
    # This drop avoids burying a thick deck profile in the factory sill's level bearing.
    apron_back = (
        approach_front
        - thickness
        - spec.cross_bearer_depth.meters
        - spec.minimum_drainage_clearance.meters
        - membrane
    )
    pan_front = apron_back - (outlet - end) * slope
    pan_back = base + spec.pan_height.meters - membrane
    section(
        "impermeable-pan-apron",
        (
            (end, apron_back),
            (outlet, pan_front),
            (outlet, pan_front + membrane),
            (end, apron_back + membrane),
        ),
        spec.pan_material_ref,
        "membrane",
    )
    section(
        "pan-outlet-drop",
        (
            (end, pan_back),
            (end + membrane, pan_back),
            (end + membrane, apron_back),
            (end, apron_back),
        ),
        spec.pan_material_ref,
        "membrane",
    )
    rectangle(
        "pan-back-dam",
        start - membrane,
        start,
        pan_back,
        seat + 1.5 * _IN,
        spec.pan_material_ref,
        "membrane",
    )
    rectangle(
        "stock-pan-coordination-envelope",
        start,
        end,
        base,
        seat,
        spec.frame_material_ref,
        "door_frame",
        span=opening.width_m - 2 * membrane,
        purchase="kit_included",
    )
    for side in (-1, 1):
        rectangle(
            f"pan-jamb-end-dam-{side}",
            start,
            end,
            pan_back,
            seat + 6 * _IN,
            spec.pan_material_ref,
            "membrane",
            span=membrane,
            along=side * (width / 2 + membrane / 2),
        )
    count = max(2, ceil(width / spec.support_spacing.meters) + 1)
    spacing = (width - spec.support_width.meters) / (count - 1)
    projection = outlet - sign * placement.frame_outer_m
    support_top = pan_front - membrane
    for index in range(1 if spec.support_kind == "concrete_cantilever" else count):
        along = -(width - spec.support_width.meters) / 2 + index * spacing
        back = (
            sign * placement.frame_outer_m - spec.support_backspan.meters
            if spec.support_kind == "timber_outriggers"
            else sign * placement.frame_outer_m
        )
        rectangle(
            f"approach-support-{index}",
            back,
            outlet,
            support_top - spec.support_depth.meters,
            support_top,
            spec.support_material_ref,
            "stud" if spec.support_kind == "timber_outriggers" else "slab",
            span=(
                width if spec.support_kind == "concrete_cantilever" else spec.support_width.meters
            ),
            along=0 if spec.support_kind == "concrete_cantilever" else along,
        )
    for station in (end, outlet - spec.cross_bearer_width.meters):
        rectangle(
            f"approach-cross-bearer-{station:.4f}",
            station,
            station + spec.cross_bearer_width.meters,
            approach_front - thickness - spec.cross_bearer_depth.meters,
            approach_front - thickness,
            spec.support_material_ref,
            "stud",
        )
    # A complete supporting section is modeled, but root anchorage is not inferred from contact.
    support = cantilever_support_report(spec, projection, spacing)
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
    if end >= outlet:
        conflicts.append("catalog sill leaves no exterior approach")
    if approach_front - thickness <= pan_front + membrane:
        conflicts.append("catalog approach blocks the membrane drainage path")
    if crest - spec.receiver_depth.meters < seat + spec.receiver_pan_clearance.meters:
        conflicts.append(
            "FLA receiver drilling reaches the pan; coordinate cap setting or receiver"
        )
    exterior = assembly.adjacent_floors[0 if sign < 0 else 1]
    interior = assembly.adjacent_floors[1 if sign < 0 else 0]
    floor_report = {}
    for name, floor in (("interior", interior), ("exterior", exterior)):
        floor_report[f"{name}_surface_z_m"] = floor.surface_m if floor else None
        floor_report[f"crest_above_{name}_in"] = (
            (crest - floor.surface_m) / _IN if floor and floor.surface_m is not None else None
        )
    receiver_clearance = crest - spec.receiver_depth.meters - seat
    report = dict(
        **floor_report,
        source_url=spec.source_url,
        source_drawing=spec.source_drawing,
        profile_status="DIGITIZED_OUTLINE",
        approach_outlet_depth_m=outlet,
        landing_edge_depth_m=landing_edge,
        pan_product=spec.pan_product,
        pan_height_basis="maximum published allowance; installed pan section pending",
        support=support,
        installation_complete=False,
        approach_board_count=board_count,
        approach_board_cut_length_in=(outlet - end) / _IN,
        support_count=count,
        support_spacing_in=spacing / _IN,
        nominal_crest_z_m=crest,
        conservative_crest_z_m=crest + spec.height_tolerance.meters,
        approach_back_z_m=approach_back,
        approach_front_z_m=approach_front,
        approach_slope=slope,
        drainage_clearance_in=(approach_front - thickness - pan_front - membrane) / _IN,
        receiver_pan_clearance_in=receiver_clearance / _IN,
        movement_gap_in=landing_gap / _IN if landing_gap is not None else None,
        minimum_movement_gap_in=(
            (landing_gap - spec.movement_horizontal.meters) / _IN
            if landing_gap is not None
            else None
        ),
        minimum_flashing_overlap_in=(spec.flashing_overlap.meters - spec.movement_vertical.meters)
        / _IN,
    )
    if landing_gap is not None and landing_gap <= spec.movement_horizontal.meters:
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
    if installation.exterior_opening_ref:
        from math import sqrt

        reveal = next(o for o in model.openings if o.tag == installation.exterior_opening_ref)
        veneer = model.wall(reveal.host_wall)
        clear_half = unit_width / 2 - installation.return_thickness.meters
        rise = reveal.arch_rise_m
        head_z = veneer.base_ref_z_m + reveal.sill_m + reveal.height_m
        if rise:
            radius = ((reveal.width_m / 2) ** 2 + rise**2) / (2 * rise)
            head_z += sqrt(max(0, radius**2 - clear_half**2)) - radius
        report["minimum_reveal_clear_height_in"] = (
            head_z - crest - spec.height_tolerance.meters
        ) / _IN
        if report["minimum_reveal_clear_height_in"] < 78:
            conflicts.append("brick reveal leaves less than the 78 inch project clear headroom")
    if installation.seat_opening_ref:
        notch = next((o for o in model.openings if o.tag == installation.seat_opening_ref), None)
        curb = model.wall(notch.host_wall) if notch else None
        if (
            curb is None
            or abs(curb.base_ref_z_m + notch.sill_m - base) > 0.001
            or notch.width_m + 0.001 < opening.width_m
        ):
            conflicts.append("concrete seat opening does not match the door elevation/width")
    boards = tuple(
        replace(
            b,
            height_m=b.height_m + b.z_m - b.height_m / 2 - seat,
            z_m=(b.z_m + b.height_m / 2 + seat) / 2,
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
        threshold_crest_z_m=crest,
        threshold_upper_z_m=crest + spec.height_tolerance.meters,
        installation_report=report,
    )
    from typehaus.resolve.exterior_door_catalog_flashing import catalog_flashing_sections

    catalog_flashing_sections(placement, opening, assembly, clad, section, rectangle)
    sources = {
        "catalog-sill": spec.source_url,
        "ariddek": "https://wahoobuildingproducts.com/ariddek-installation-guide/",
        "stock-pan": "https://www.suresill.com/faq",
        "stock-headflash": "https://www.suresill.com/product/headflash",
        "flashing-end": "https://www.tremcosealants.com/resource/download/Proglaze_ETA_System_1_AI.pdf",
    }
    sections = [
        replace(
            s,
            source_url=next(
                (url for prefix, url in sources.items() if s.name.startswith(prefix)), None
            ),
            geometry_status="DIGITIZED_OUTLINE"
            if s.name == "catalog-sill-outline"
            else "COORDINATION_ENVELOPE",
        )
        for s in sections
    ]
    placement = replace(placement, sections=tuple(sections))
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
        leaf_bottom_z_m=crest + 0.125 * _IN,
        jamb_bottom_z_m=seat,
    )
