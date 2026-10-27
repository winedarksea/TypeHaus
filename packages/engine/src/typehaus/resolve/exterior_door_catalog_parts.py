"""Catalog sill, pan and approach sections with explicit product provenance."""

from math import radians, tan

from typehaus.resolve.exterior_door_sections import DoorSectionBuilder

_IN = 0.0254


def catalog_sill_sections(spec, installation, placement, opening, layout):
    builder = DoorSectionBuilder(placement.outward_sign, layout.width)
    _add_factory_sill(builder, spec, layout)
    _add_approach_boards(builder, spec, layout)
    _add_pan_and_apron(builder, spec, opening, layout)
    _add_approach_supports(builder, spec, placement, layout)
    return tuple(builder.sections)


def _add_factory_sill(builder, spec, layout):
    section = builder.section
    section(
        "catalog-sill-outline",
        ((layout.start + x, layout.seat + z) for x, z in spec.sill_outline_m),
        spec.sill_material_ref,
        "door_hardware",
        span=layout.unit_width,
        purchase="factory_included",
        source_url=spec.source_url,
        geometry_status="DIGITIZED_OUTLINE",
    )
    if spec.sill_extender_ref:
        extension_drop = spec.sill_extender_depth.meters * tan(
            radians(spec.sill_extender_slope_degrees)
        )
        extension_top = spec.sill_extender_height.meters - extension_drop
        section(
            f"catalog-sill-extender-{spec.sill_extender_ref}",
            (
                (layout.sill_end, layout.seat),
                (layout.sill_end + spec.sill_extender_depth.meters, layout.seat),
                (layout.sill_end + spec.sill_extender_depth.meters, layout.seat + extension_top),
                (layout.sill_end, layout.seat + spec.sill_extender_height.meters),
            ),
            spec.sill_material_ref,
            "door_hardware",
            span=layout.unit_width,
            purchase="separate",
            source_url=spec.sill_extender_source_url,
        )


def _add_approach_boards(builder, spec, layout):
    section = builder.section
    rectangle = builder.rectangle
    for index in range(layout.board_count):
        board_width = min(
            spec.approach_board_width.meters,
            layout.width - index * spec.approach_board_width.meters,
        )
        along = -layout.width / 2 + index * spec.approach_board_width.meters + board_width / 2
        section(
            f"ariddek-approach-board-envelope-{index}",
            (
                (layout.end, layout.approach_back - layout.thickness),
                (layout.outlet, layout.approach_front - layout.thickness),
                (layout.outlet, layout.approach_front),
                (layout.end, layout.approach_back),
            ),
            spec.approach_material_ref,
            "floor",
            span=board_width,
            along=along,
            source_url=spec.approach_source_url,
        )
    rectangle(
        "ariddek-stock-profile-trim",
        layout.outlet,
        layout.outlet + layout.membrane,
        layout.approach_front - layout.thickness,
        layout.approach_front,
        spec.approach_material_ref,
        "floor",
        source_url=spec.approach_source_url,
    )


def _add_pan_and_apron(builder, spec, opening, layout):
    section = builder.section
    rectangle = builder.rectangle
    section(
        "impermeable-pan-apron",
        (
            (layout.end, layout.apron_back),
            (layout.outlet, layout.pan_front),
            (layout.outlet, layout.pan_front + layout.membrane),
            (layout.end, layout.apron_back + layout.membrane),
        ),
        spec.pan_material_ref,
        "membrane",
    )
    section(
        "pan-outlet-drop",
        (
            (layout.end, layout.pan_back),
            (layout.end + layout.membrane, layout.pan_back),
            (layout.end + layout.membrane, layout.apron_back),
            (layout.end, layout.apron_back),
        ),
        spec.pan_material_ref,
        "membrane",
    )
    rectangle(
        "pan-back-dam",
        layout.start - layout.membrane,
        layout.start,
        layout.pan_back,
        layout.seat + 1.5 * _IN,
        spec.pan_material_ref,
        "membrane",
    )
    rectangle(
        "stock-pan-coordination-envelope",
        layout.start,
        layout.end,
        layout.base,
        layout.seat,
        spec.frame_material_ref,
        "door_frame",
        span=opening.width_m - 2 * layout.membrane,
        purchase="kit_included",
        source_url=spec.pan_source_url,
    )
    for side in (-1, 1):
        rectangle(
            f"pan-jamb-end-dam-{side}",
            layout.start,
            layout.end,
            layout.pan_back,
            layout.seat + 6 * _IN,
            spec.pan_material_ref,
            "membrane",
            span=layout.membrane,
            along=side * (layout.width / 2 + layout.membrane / 2),
        )


def _add_approach_supports(builder, spec, placement, layout):
    sign = placement.outward_sign
    rectangle = builder.rectangle
    for index in range(1 if spec.support_kind == "concrete_cantilever" else layout.count):
        along = -(layout.width - spec.support_width.meters) / 2 + index * layout.spacing
        back = (
            sign * placement.frame_outer_m - spec.support_backspan.meters
            if spec.support_kind == "timber_outriggers"
            else sign * placement.frame_outer_m
        )
        rectangle(
            f"approach-support-{index}",
            back,
            layout.outlet,
            layout.support_top - spec.support_depth.meters,
            layout.support_top,
            spec.support_material_ref,
            "stud" if spec.support_kind == "timber_outriggers" else "slab",
            span=layout.width
            if spec.support_kind == "concrete_cantilever"
            else spec.support_width.meters,
            along=0 if spec.support_kind == "concrete_cantilever" else along,
        )
    for station in (layout.end, layout.outlet - spec.cross_bearer_width.meters):
        rectangle(
            f"approach-cross-bearer-{station:.4f}",
            station,
            station + spec.cross_bearer_width.meters,
            layout.approach_front - layout.thickness - spec.cross_bearer_depth.meters,
            layout.approach_front - layout.thickness,
            spec.support_material_ref,
            "stud",
        )
