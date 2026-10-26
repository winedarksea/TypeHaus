"""Catalog head cap and independently attached flashing-end coordination envelopes.

Membrane bonds and moving-joint application are evidence holds, not implied approvals.
"""

from typehaus.resolve.flashing_config import FLASHING

_IN = 0.0254


def catalog_flashing_sections(placement, opening, assembly, clad, section, rectangle):
    installation = placement.specification
    spec = installation.catalog_installation
    sign = placement.outward_sign
    head = assembly.rough_opening_z_m + opening.height_m
    casing = installation.casing_width.meters
    face = sign * clad
    sheet = installation.wrap_isolation_thickness.meters
    top = head + casing
    span = opening.width_m + 2 * (casing + FLASHING.head_end_lap_m)
    # SureSill HeadFlash 1-3/8 x 84 complete pack; cross-section remains a coordination
    # envelope until a dimensioned drawing establishes its upstand, gauge and downstand.
    rectangle(
        "stock-headflash-cap-envelope",
        face,
        face + 1.375 * _IN,
        top,
        top + sheet,
        spec.head_material_ref,
        "membrane",
        span=span,
    )
    rectangle(
        "stock-headflash-upstand-envelope",
        face,
        face + sheet,
        top,
        top + 1.5 * _IN,
        spec.head_material_ref,
        "membrane",
        span=span,
    )
    for side in (-1, 1):
        along = side * (span / 2 - sheet / 2)
        rectangle(
            f"stock-headflash-end-dam-envelope-{side}",
            face,
            face + 1.375 * _IN,
            top,
            top + 0.5 * _IN,
            spec.head_material_ref,
            "membrane",
            span=sheet,
            along=along,
        )
    if spec.support_kind != "timber_outriggers":
        return
    # These terminate the two existing rear flashing runs without fastening across the
    # independent house/deck joint. They are design envelopes for standard ETA parts.
    report = placement.installation_report
    deck_top = report["exterior_surface_z_m"]
    if deck_top is None:
        return
    overlap = spec.flashing_overlap.meters
    deck_edge = report.get("landing_edge_depth_m")
    if deck_edge is None:
        return
    gap = deck_edge - face
    for side in (-1, 1):
        along = side * (opening.width_m / 2 + casing + installation.drainage_gap.meters)
        rectangle(
            f"flashing-end-house-adapter-{side}",
            face,
            face + sheet,
            deck_top,
            deck_top + overlap + spec.movement_vertical.meters,
            "aluminum-extrusion",
            "door_hardware",
            span=0.375 * _IN,
            along=along,
        )
        rectangle(
            f"flashing-end-deck-adapter-{side}",
            deck_edge,
            deck_edge + sheet,
            deck_top,
            deck_top + overlap,
            "aluminum-extrusion",
            "door_hardware",
            span=0.375 * _IN,
            along=along,
        )
        # Unbonded slack between attachments, with lap continuing down toward the pan.
        section(
            f"flashing-end-silicone-corner-envelope-{side}",
            (
                (face, deck_top + overlap),
                (face + gap / 2, deck_top + overlap - gap / 2),
                (face + gap, deck_top + overlap),
                (face + gap, deck_top + overlap + sheet),
                (face + gap / 2, deck_top + overlap - gap / 2 + sheet),
                (face, deck_top + overlap + sheet),
            ),
            spec.transition_material_ref,
            "membrane",
            span=6 * _IN,
            along=along,
        )
