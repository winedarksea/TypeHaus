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


def pan_rise_profile(dam, outlet, ro_face=None, slope=FLASHING.drainage_slope):
    """``(depth, rise)`` breakpoints of a sill pan's top above its seat, dam to outlet.

    Sloped to the outlet by default; with ``ro_face`` (``pan_across_ro``) sloped only to
    the RO's outer face and level beyond it.
    """
    if ro_face is None or not dam < ro_face < outlet:
        return ((dam, (outlet - dam) * slope), (outlet, 0.0))
    return ((dam, (ro_face - dam) * slope), (ro_face, 0.0), (outlet, 0.0))


def pan_rise_at(profile, depth):
    """The pan's rise at ``depth`` on a ``pan_rise_profile``; flat past either end."""
    (d0, r0), *rest = profile
    if depth <= d0:
        return r0
    for d1, r1 in rest:
        if depth <= d1:
            return r0 + (r1 - r0) * (depth - d0) / (d1 - d0)
        d0, r0 = d1, r1
    return r0


def door_pan_ro_face(placement):
    """The RO's outer face a ``pan_across_ro`` pan stops sloping at, else None."""
    design = placement.specification.sill_design if placement else None
    if design is None or not design.pan_across_ro:
        return None
    return placement.outward_sign * placement.frame_outer_m


def add_sill_design(assembly, opening, clad, model=None, wall=None):
    placement = assembly.exterior_placement
    installation = placement.specification
    design = installation.sill_design
    if design is None:
        return assembly
    bearing = installation.approach_bearing if model is not None else None
    if any(c.specification.role in ("sill", "track") for c in assembly.components):
        return replace(assembly, conflicts=(*assembly.conflicts,
            "remove schematic sill design when installing a documented factory section"))
    sign = placement.outward_sign
    inner = sign * placement.frame_inner_m
    # Keep the factory envelope outboard of the liquid back-dam face.
    start = inner + FLASHING.sill_membrane_m + design.drainage_clearance.meters
    end = start + design.threshold_depth.meters
    outlet = sill_outlet_depth(sign * clad, installation)
    pan_outlet = outlet
    base = assembly.rough_opening_z_m
    exterior_floor = assembly.adjacent_floors[0 if sign < 0 else 1]
    interior_floor = assembly.adjacent_floors[1 if sign < 0 else 0]
    raised_open_interior = (interior_floor is None and opening.sill_m > 0)
    missing_interior = interior_floor is None or interior_floor.surface_m is None
    if (exterior_floor is None or exterior_floor.surface_m is None
            or (not raised_open_interior and missing_interior)):
        return replace(assembly, unknown=(*assembly.unknown,
            "sill design needs known interior and exterior surfaces; no approach generated"))
    if end >= outlet - installation.drainage_gap.meters:
        return replace(assembly, conflicts=(*assembly.conflicts,
            "sill design leaves no room for the draining exterior approach"))
    support = None
    if bearing is not None:
        # No cantilever: the plate runs on to rest over the landing's member (slip pad).
        from typehaus.resolve.exterior_door_bridge import bridge_support

        support = bridge_support(model, wall, opening, placement, base, opening.width_m / 2)
        if support.member_outer is not None and bearing.landing == "slip_pad":
            outlet = max(outlet, support.member_outer)
    thickness = design.approach_plate_thickness.meters
    front_top = max(base + design.approach_minimum_height.meters,
                    exterior_floor.surface_m + design.approach_landing_step.meters)
    # Heights hang off the pan's outlet; a plate run on to its landing pad only falls further.
    back_top = front_top + (pan_outlet - end) * design.approach_slope
    front_top = back_top - (outlet - end) * design.approach_slope
    seat = max(base + design.seat_height.meters,
               back_top - design.threshold_nose_height.meters)
    crest = seat + design.threshold_height.meters
    if interior_floor is not None and interior_floor.surface_m >= crest - thickness:
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
    if interior_floor is not None:
        section("interior-back-dam-cover", ((cap_back, interior_floor.surface_m),
            (cap_back + thickness, interior_floor.surface_m),
            (cap_back + thickness, crest - thickness), (start, crest - thickness),
            (start, crest), (cap_back, crest)),
            design.approach_material_ref, "door_hardware")

    section("approach-walking-plate", ((end, back_top - thickness),
        (outlet, front_top - thickness), (outlet, front_top), (end, back_top)),
        design.approach_material_ref, "door_hardware")
    if support is None:
        # A skirt conceals the downturned pan from an oblique view, without a bottom return
        # that would dam it. The discharge gap is behind this skirt and open below it.
        skirt = outlet + design.drainage_clearance.meters
        section("approach-drip-nosing", ((outlet, front_top - thickness),
            (skirt, front_top - thickness), (skirt, base - FLASHING.pan_drop_m),
            (skirt + design.nosing_thickness.meters, base - FLASHING.pan_drop_m),
            (skirt + design.nosing_thickness.meters, front_top), (outlet, front_top)),
            design.approach_material_ref, "door_hardware", span=opening.width_m)

    def plate_bottom(depth):
        return back_top - thickness - (depth - end) * design.approach_slope

    # The strips run out to the girt sill course's face (or the frame, on a wall with none):
    # the plate rests on them there and on its landing pad, and spans between.
    reach = outlet
    if support is not None:
        # Never short of the threshold's own end: the strips carry it as well.
        reach = max(support.girt_face if support.girt_face is not None
                    else support.sheathing,
                    end + installation.wrap_isolation_thickness.meters + 0.25 * 0.0254)
    strip_width = design.bearing_strip_width.meters
    intervals = max(1, ceil((width - strip_width) / design.bearing_strip_spacing.meters))
    positions = [-(width - strip_width) / 2 + i * (width - strip_width) / intervals
                 for i in range(intervals + 1)]
    ro_face = door_pan_ro_face(placement)
    profile = pan_rise_profile(inner, pan_outlet, ro_face)

    def pan_top(depth):
        depth = min(depth, pan_outlet)
        rise = ((pan_outlet - depth) * FLASHING.drainage_slope if ro_face is None
                else pan_rise_at(profile, depth))
        return base + rise + FLASHING.sill_membrane_m
    strip_bottom_start = pan_top(start)
    strip_bottom_end = pan_top(reach)
    isolation = installation.wrap_isolation_thickness.meters
    if min(seat - isolation - strip_bottom_start,
           plate_bottom(reach) - isolation - strip_bottom_end,
           back_top - thickness - isolation - pan_top(end)) <= 0:
        return replace(assembly, conflicts=(*assembly.conflicts,
            "sill design bearing or walking plate intersects the drainage envelope"))
    for index, along in enumerate(positions):
        step_depth = end + isolation
        step_top = back_top - thickness - isolation * (1 + design.approach_slope)
        section(f"draining-bearing-strip-{index}", ((start, strip_bottom_start),
            (reach, strip_bottom_end), (reach, plate_bottom(reach) - isolation),
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
            (reach, plate_bottom(reach) - isolation),
            (reach, plate_bottom(reach)), (end, back_top - thickness)),
            installation.wrap_isolation_material_ref, "membrane", strip_width, along,
            purchase="allowance_included")
    unknown = (*assembly.unknown,
        "sill/leaf/jamb design envelopes are schematic; "
        "factory profiles and seals await supplier section")
    conflicts = list(assembly.conflicts)
    report = None
    if support is None:
        unknown = (*unknown, "approach plate and draining bearing strips need structural "
                   "support/anchorage design; exterior insulation and plywood buck provide "
                   "no bearing")
    else:
        from typehaus.resolve.exterior_door_bridge import (
            gap_landing_conflicts,
            slip_pad_bearing,
            slip_pad_seat,
        )

        conflicts.extend(support.conflicts)
        deck_top = exterior_floor.surface_m
        length = pad = None
        cut = None
        if bearing.landing == "slip_pad":
            # The deck stays clear of the pan's drip; the pad rests on what is left.
            lo, pad_base, cut = slip_pad_seat(support, bearing, deck_top,
                                              pan_outlet + design.drainage_clearance.meters)
            length, pad, pad_conflicts = slip_pad_bearing(support, bearing, plate_bottom(outlet),
                                                          pad_base, lo)
            conflicts.extend(pad_conflicts)
            if pad is not None and pad > 0:
                section("approach-slip-pad", ((lo, pad_base), (outlet, pad_base),
                        (outlet, plate_bottom(outlet)), (lo, plate_bottom(lo))),
                        bearing.slip_pad_material_ref, "rigid")
        else:
            conflicts.extend(gap_landing_conflicts(support, bearing, outlet,
                                                   installation.drainage_gap.meters / 2))
        if support.buck_top is not None and plate_bottom(reach) < support.buck_top - 1e-6:
            conflicts.append("approach plate sinks into the buck sill")
        from typehaus.resolve.exterior_door_bridge import girt_course_connection

        connection, connection_unknown, connection_conflicts = girt_course_connection(
            model, wall, opening, placement, support)
        conflicts.extend(connection_conflicts)
        unknown = (*unknown, "approach plate span and section are schematic; the plate's "
                   "published load awaits the supplier's section", *connection_unknown)
        report = dict(kind="approach_bearing", **connection, landing_member=support.member,
                      landing_member_cover=support.member_cover,
                      strip_reach_in=reach / 0.0254,
                      plate_span_in=(outlet - reach) / 0.0254,
                      pad_bearing_in=None if length is None else length / 0.0254,
                      pad_thickness_in=None if pad is None else pad / 0.0254,
                      exterior_surface_z_m=deck_top,
                      landing_edge_depth_m=support.deck_edge,
                      deck_cut_depth_m=cut)
    if raised_open_interior:
        unknown = (*unknown, "interior is open below the raised rough sill")
    # The generic door has no weather sweep contract. Its clearance is a visible design gap.
    leaf_bottom = crest + design.leaf_clearance.meters
    return replace(assembly, leaf_bottom_z_m=leaf_bottom, jamb_bottom_z_m=seat,
        exterior_placement=replace(placement, sections=tuple(sections),
                                  sill_design_status="SCHEMATIC",
                                  installation_report=report or placement.installation_report),
        unknown=unknown, conflicts=tuple(conflicts))
