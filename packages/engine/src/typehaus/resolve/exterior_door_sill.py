"""Explicit schematic sill option for doors without selected catalog geometry.

Never invoked as an automatic fallback after catalog failure.

The plate carries foot traffic; trim coil does not. Drainage strips run outward,
and bracket sizing/anchorage stays UNKNOWN until structurally specified.
"""
from dataclasses import replace
from math import ceil

from typehaus.resolve.exterior_door_sections import DoorInstallationSection
from typehaus.resolve.flashing_config import FLASHING


def sill_outlet_depth(clad, installation):
    """Door outlet in the landing gap; the head drip's larger throw is a separate part."""
    outlet = (clad + installation.casing_thickness.meters
              + installation.sill_design.pan_projection.meters)
    if installation.exterior_wrap_material_ref:
        outlet += (installation.exterior_wrap_thickness.meters
                   + installation.wrap_isolation_thickness.meters)
    return outlet


def add_sill_design(assembly, opening, clad):
    placement = assembly.exterior_placement
    installation = placement.specification
    design = installation.sill_design
    if design is None:
        return assembly
    if any(c.specification.role in ("sill", "track") for c in assembly.components):
        return replace(assembly, conflicts=(*assembly.conflicts,
            "remove schematic sill design when installing a documented factory section"))
    sign = placement.outward_sign
    inner = sign * placement.frame_inner_m
    # Keep the factory envelope outboard of the liquid back-dam face.
    start = inner + FLASHING.sill_membrane_m + design.drainage_clearance.meters
    end = start + design.threshold_depth.meters
    outlet = sill_outlet_depth(sign * clad, installation)
    base = assembly.rough_opening_z_m
    exterior_floor = assembly.adjacent_floors[0 if sign < 0 else 1]
    interior_floor = assembly.adjacent_floors[1 if sign < 0 else 0]
    if (exterior_floor is None or exterior_floor.surface_m is None
            or interior_floor is None or interior_floor.surface_m is None):
        return replace(assembly, unknown=(*assembly.unknown,
            "sill design needs known interior and exterior surfaces; no approach generated"))
    if end >= outlet - installation.drainage_gap.meters:
        return replace(assembly, conflicts=(*assembly.conflicts,
            "sill design leaves no room for the draining exterior approach"))
    thickness = design.approach_plate_thickness.meters
    front_top = max(base + design.approach_minimum_height.meters,
                    exterior_floor.surface_m + design.approach_landing_step.meters)
    back_top = front_top + (outlet - end) * design.approach_slope
    seat = max(base + design.seat_height.meters,
               back_top - design.threshold_nose_height.meters)
    crest = seat + design.threshold_height.meters
    if interior_floor.surface_m >= crest - thickness:
        return replace(assembly, conflicts=(*assembly.conflicts,
            "interior finish rises into the sill design back-dam cover"))
    cap_end = start + design.cap_depth.meters
    lining = installation.return_thickness.meters + design.side_clearance.meters
    if installation.exterior_wrap_material_ref:
        lining += (installation.exterior_wrap_thickness.meters
                   + installation.wrap_isolation_thickness.meters)
    width = opening.width_m - 2 * lining
    if width <= design.bearing_strip_width.meters:
        return replace(assembly, conflicts=(*assembly.conflicts,
            "sill design is too narrow for separated draining bearing strips"))
    sections = []

    def section(name, profile, material, key, span=width, along=0, purchase="site"):
        sections.append(DoorInstallationSection(name,
            tuple((sign * n, z) for n, z in profile), span, along, material, key, purchase))

    # These simplified solids deliberately do not claim hollow extrusion or seal geometry.
    nose = seat + design.threshold_nose_height.meters
    section("threshold-design-envelope", ((start, seat), (end, seat), (end, nose),
        (cap_end, crest - design.cap_height.meters),
        (start, crest - design.cap_height.meters)),
        design.approach_material_ref, "door_hardware", purchase="factory_included")
    section("threshold-cap-design-envelope", (
        (start, crest - design.cap_height.meters),
        (cap_end, crest - design.cap_height.meters), (cap_end, crest),
        (start, crest)), "composite-deck", "window_trim", purchase="factory_included")
    cap_back = inner - FLASHING.back_dam_strip_m - thickness - design.drainage_clearance.meters
    section("interior-back-dam-cover", ((cap_back, interior_floor.surface_m),
        (cap_back + thickness, interior_floor.surface_m),
        (cap_back + thickness, crest - thickness), (start, crest - thickness),
        (start, crest), (cap_back, crest)),
        design.approach_material_ref, "door_hardware")

    section("approach-walking-plate", ((end, back_top - thickness),
        (outlet, front_top - thickness), (outlet, front_top), (end, back_top)),
        design.approach_material_ref, "door_hardware")
    # A skirt conceals the downturned pan from an oblique view, without a bottom return
    # that would dam it. The discharge gap is behind this skirt and open below it.
    skirt = outlet + design.drainage_clearance.meters
    section("approach-drip-nosing", ((outlet, front_top - thickness),
        (skirt, front_top - thickness), (skirt, base - FLASHING.pan_drop_m),
        (skirt + design.nosing_thickness.meters, base - FLASHING.pan_drop_m),
        (skirt + design.nosing_thickness.meters, front_top), (outlet, front_top)),
        design.approach_material_ref, "door_hardware", span=opening.width_m)
    strip_width = design.bearing_strip_width.meters
    intervals = max(1, ceil((width - strip_width) / design.bearing_strip_spacing.meters))
    positions = [-(width - strip_width) / 2 + i * (width - strip_width) / intervals
                 for i in range(intervals + 1)]
    def pan_top(depth):
        return base + (outlet - depth) * FLASHING.drainage_slope + FLASHING.sill_membrane_m
    strip_bottom_start = pan_top(start)
    strip_bottom_end = pan_top(outlet)
    isolation = installation.wrap_isolation_thickness.meters
    if min(seat - isolation - strip_bottom_start,
           front_top - thickness - isolation - strip_bottom_end,
           back_top - thickness - isolation - pan_top(end)) <= 0:
        return replace(assembly, conflicts=(*assembly.conflicts,
            "sill design bearing or walking plate intersects the drainage envelope"))
    for index, along in enumerate(positions):
        step_depth = end + isolation
        step_top = back_top - thickness - isolation * (1 + design.approach_slope)
        section(f"draining-bearing-strip-{index}", ((start, strip_bottom_start),
            (outlet, strip_bottom_end), (outlet, front_top - thickness - isolation),
            (step_depth, step_top),
            (step_depth, seat - isolation), (start, seat - isolation)),
            design.bearing_material_ref, "lumber", strip_width, along)
        section(f"bearing-isolation-sill-{index}", ((start, seat - isolation),
            (end, seat - isolation), (end, seat), (start, seat)),
            installation.wrap_isolation_material_ref, "membrane", strip_width, along,
            purchase="allowance_included")
        if step_top > seat - isolation:
            section(f"bearing-isolation-step-{index}", ((end, seat - isolation),
                (step_depth, seat - isolation), (step_depth, step_top), (end, step_top)),
                installation.wrap_isolation_material_ref, "membrane", strip_width, along,
                purchase="allowance_included")
        section(f"bearing-isolation-approach-{index}", (
            (end, back_top - thickness - isolation),
            (outlet, front_top - thickness - isolation),
            (outlet, front_top - thickness), (end, back_top - thickness)),
            installation.wrap_isolation_material_ref, "membrane", strip_width, along,
            purchase="allowance_included")
    unknown = (*assembly.unknown,
        "sill/leaf/jamb design envelopes are schematic; "
        "factory profiles and seals await supplier section",
        "approach plate and draining bearing strips need structural support/anchorage design; "
        "exterior insulation and plywood buck provide no bearing")
    # The generic door has no weather sweep contract. Its clearance is a visible design gap.
    leaf_bottom = crest + design.leaf_clearance.meters
    return replace(assembly, leaf_bottom_z_m=leaf_bottom, jamb_bottom_z_m=seat,
        exterior_placement=replace(placement, sections=tuple(sections),
                                  sill_design_status="SCHEMATIC"), unknown=unknown)
