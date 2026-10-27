"""Catalog head cap and independently attached flashing-end coordination envelopes.

Membrane bonds and moving-joint application are evidence holds, not implied approvals.
"""

from typehaus.resolve.exterior_door_sections import DoorSectionBuilder
from typehaus.resolve.flashing_config import FLASHING


def catalog_flashing_sections(placement, opening, assembly, clad):
    """Return head and optional independent-landing sections without mutating placement."""
    builder = DoorSectionBuilder(placement.outward_sign, opening.width_m)
    section, rectangle = builder.section, builder.rectangle
    installation = placement.specification
    spec = installation.catalog_installation
    sign = placement.outward_sign
    head = assembly.rough_opening_z_m + opening.height_m
    casing = installation.casing_width.meters
    face = sign * clad
    sheet = spec.head_profile_thickness.meters
    top = head + casing
    span = opening.width_m + 2 * (casing + FLASHING.head_end_lap_m)
    # SureSill HeadFlash 1-3/8 x 84 complete pack; cross-section remains a coordination
    # envelope until a dimensioned drawing establishes its upstand, gauge and downstand.
    rectangle(
        "stock-headflash-cap-envelope",
        face,
        face + spec.head_cap_depth.meters,
        top,
        top + sheet,
        spec.head_material_ref,
        "membrane",
        source_url=spec.head_source_url,
        span=span,
    )
    rectangle(
        "stock-headflash-upstand-envelope",
        face,
        face + sheet,
        top,
        top + spec.head_upstand_height.meters,
        spec.head_material_ref,
        "membrane",
        source_url=spec.head_source_url,
        span=span,
    )
    for side in (-1, 1):
        along = side * (span / 2 - sheet / 2)
        rectangle(
            f"stock-headflash-end-dam-envelope-{side}",
            face,
            face + spec.head_cap_depth.meters,
            top,
            top + spec.head_end_dam_height.meters,
            spec.head_material_ref,
            "membrane",
            source_url=spec.head_source_url,
            span=sheet,
            along=along,
        )
    if not spec.independent_landing_flashing:
        return tuple(builder.sections)
    # These terminate the two existing rear flashing runs without fastening across the
    # independent house/deck joint. They are design envelopes for standard ETA parts.
    report = placement.installation_report
    deck_top = report["exterior_surface_z_m"]
    if deck_top is None:
        return tuple(builder.sections)
    overlap = spec.flashing_overlap.meters
    deck_edge = report.get("landing_edge_depth_m")
    if deck_edge is None:
        return tuple(builder.sections)
    sheet = spec.transition_adapter_thickness.meters
    silicone = spec.transition_sheet_thickness.meters
    gap = deck_edge - face
    for side in (-1, 1):
        along = side * (opening.width_m / 2 + casing + installation.drainage_gap.meters)
        rectangle(
            f"flashing-end-house-adapter-{side}",
            face,
            face + sheet,
            deck_top,
            deck_top + overlap + spec.movement_vertical.meters,
            spec.transition_adapter_material_ref,
            "door_hardware",
            source_url=spec.transition_source_url,
            span=spec.transition_adapter_width.meters,
            along=along,
        )
        rectangle(
            f"flashing-end-deck-adapter-{side}",
            deck_edge,
            deck_edge + sheet,
            deck_top,
            deck_top + overlap,
            spec.transition_adapter_material_ref,
            "door_hardware",
            source_url=spec.transition_source_url,
            span=spec.transition_adapter_width.meters,
            along=along,
        )
        # Unbonded slack between attachments, with lap continuing down toward the pan.
        section(
            f"flashing-end-silicone-corner-envelope-{side}",
            (
                (face, deck_top + overlap),
                (face + gap / 2, deck_top + overlap - gap / 2),
                (face + gap, deck_top + overlap),
                (face + gap, deck_top + overlap + silicone),
                (face + gap / 2, deck_top + overlap - gap / 2 + silicone),
                (face, deck_top + overlap + silicone),
            ),
            spec.transition_material_ref,
            "membrane",
            source_url=spec.transition_source_url,
            span=spec.transition_strip_width.meters,
            along=along,
        )
    return tuple(builder.sections)
