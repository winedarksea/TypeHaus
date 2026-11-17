"""Check the drawn FLEXX installation, without certifying schematic product stations."""

import math

from shapely.geometry import Polygon

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import Tier, check
from typehaus.model.placeable_symbols import model_parts, place_local
from typehaus.model.placeable_symbols._gree_flexx import CABINET_IN, FRONT_CONNECTIONS_IN
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_ports import placed_ports
from typehaus.resolve.walking_surface import surfaces_at

CHECK_ID = "mep.air_handler_installation"
SYMBOL = "gree-flexx-ultra-24-horizontal"
GEOMETRY_TOLERANCE_M = 0.001 * M_PER_IN
MINIMUM_TRAP_DROP_IN = 2.0
MINIMUM_SEAL_DEPTH_IN = 3.0
MINIMUM_VENT_RISE_IN = 2.0
MINIMUM_CABINET_SLOPE_IN_PER_FT = 0.125
MINIMUM_PAN_EXTRA_IN = 3.0


def _part_outline(part, obj):
    x, y, _ = part["center"]
    w, d, _ = part["size"]
    return Polygon(place_local(((x - w / 2, y - d / 2), (x + w / 2, y - d / 2),
                                (x + w / 2, y + d / 2), (x - w / 2, y + d / 2)),
                               obj.position, obj.rotation_degrees))


@check(Tier.INTEGRITY, CHECK_ID)
def air_handler_installation(ctx):
    products = {p.tag: p for p in ctx.plan.library.equipment_types
                if p.model_representation and p.model_representation.symbol == SYMBOL}
    equipment = {e.tag: e for e in ctx.plan.all_elements() if e.element_kind == "Equipment"}
    ports = {(p.equipment_tag, p.port_tag): p for p in placed_ports(ctx.model)}
    pipes = {p.tag: p for p in ctx.model.pipe_runs}
    findings = []
    for obj in ctx.model.canvas_objects:
        product = products.get(obj.type_ref)
        if product is None:
            continue
        unit = equipment[obj.tag]
        tags = (obj.tag,)
        spec = product.air_handler_installation
        if spec is None:
            findings.append(unknown(CHECK_ID, f"{obj.tag}: no dimensional pan, supports, "
                                    "primary trap or float-switch installation is modeled. "
                                    "A platform elevation alone proves no trap clearance.", tags))
            continue
        problems = []
        for value, minimum, label in (
            (spec.trap_outlet_drop.inches, MINIMUM_TRAP_DROP_IN, "trap inlet/outlet drop"),
            (spec.trap_seal_depth.inches, MINIMUM_SEAL_DEPTH_IN, "trap seal"),
            (spec.vent_rise_above_inlet.inches, MINIMUM_VENT_RISE_IN, "downstream vent rise"),
            (spec.cabinet_slope_in_per_ft, MINIMUM_CABINET_SLOPE_IN_PER_FT, "cabinet pitch"),
        ):
            if value < minimum - 1e-9:
                problems.append(f"{label} {value:g} is below {minimum:g}")
        if (spec.pan_width.inches < product.footprint[0].inches + MINIMUM_PAN_EXTRA_IN
                or spec.pan_depth.inches < product.footprint[1].inches + MINIMUM_PAN_EXTRA_IN):
            problems.append("pan does not extend at least 3 inches beyond cabinet overall sizes")
        if spec.float_trip_depth.meters + spec.pan_sheet.meters >= spec.pan_height.meters:
            problems.append("float trip level reaches or exceeds the pan rim")
        if not unit.secondary_drain_pan or not unit.float_switch_ref or unit.overflow_drain_ref:
            problems.append("drawn undrained pan requires the declared pan and float shutdown")
        if unit.install_parts.count(spec.float_switch_product_ref) != 1:
            problems.append("modeled float switch must be selected once in install_parts")
        if (len(spec.rail_centers) < 2 or any(
                abs(center.inches) + spec.rail_width.inches / 2 > product.footprint[0].inches / 2
                for center in spec.rail_centers)):
            problems.append("support rails do not bear beneath both cabinet ends")
        parts = model_parts(SYMBOL, *(v.meters for v in (*product.footprint, product.height)),
                            air_handler_installation=spec)
        pan, = [p for p in parts if p.get("role") == "flexx:emergency-pan-floor"]
        pan_bottom = obj.z_m + pan["center"][2] - pan["size"][2] / 2
        pan_outline = _part_outline(pan, obj)
        supports = [s for s in ctx.model.solids
                    if Polygon(s.outline).buffer(GEOMETRY_TOLERANCE_M).covers(pan_outline)
                    and abs(s.z1_m - pan_bottom) <= GEOMETRY_TOLERANCE_M]
        if not supports:
            problems.append("pan bottom is not seated on a modeled continuous platform")
        trap = next(p for p in parts if p.get("role") == "flexx:primary-trap")
        trap_bottom = obj.z_m + trap["center"][2] - trap["size"][2] / 2
        trap_outline = _part_outline(trap, obj)
        trap_point = trap_outline.centroid
        floors = [s.deck_top_m for s in surfaces_at(ctx.model, (trap_point.x, trap_point.y))
                  if s.deck_top_m <= obj.z_m + GEOMETRY_TOLERANCE_M]
        if not floors:
            problems.append("no deck surface establishes trap bottom clearance")
        elif trap_bottom <= max(floors) + GEOMETRY_TOLERANCE_M:
            problems.append("primary trap exterior touches or falls below the deck")
        for support in supports:
            if (Polygon(support.outline).intersects(trap_outline)
                    and trap_bottom < support.z1_m - GEOMETRY_TOLERANCE_M):
                problems.append(f"primary trap intersects {support.tag}")
        if any(trap_outline.intersection(Polygon(zone)).area > GEOMETRY_TOLERANCE_M ** 2
               for zone in obj.required_clearances):
            problems.append("primary trap occupies the front service rectangle")
        float_parts = [p for p in parts if p.get("role") == "flexx:float-switch"]
        if not all(pan_outline.covers(_part_outline(p, obj)) for p in float_parts):
            problems.append("float travel envelope is outside the emergency pan")
        port = ports.get((obj.tag, "condensate_trap_outlet"))
        pipe = pipes.get(unit.pan_drain_ref)
        primary_x, primary_z, _ = FRONT_CONNECTIONS_IN["condensate_primary"]
        primary_height = spec.pitched_point_in((primary_x, -CABINET_IN[1] / 2, primary_z))[2]
        local_outlet = tuple(v * dimension.inches / reference for v, dimension, reference in zip(
            spec.trap_outlet_in(primary_height), (*product.footprint, product.height),
            CABINET_IN, strict=True))
        outlet_xy, = place_local([(local_outlet[0] * M_PER_IN, local_outlet[1] * M_PER_IN)],
                                  obj.position, obj.rotation_degrees)
        drawn_outlet = (*outlet_xy, obj.z_m + local_outlet[2] * M_PER_IN)
        if port is None or math.dist(port.point, drawn_outlet) > GEOMETRY_TOLERANCE_M:
            problems.append("declared trap outlet disagrees with the drawn installation")
        if (port is None or pipe is None or pipe.z_m is None or not pipe.path
                or math.dist(drawn_outlet, (*pipe.path[0], pipe.z_m[0])) > GEOMETRY_TOLERANCE_M):
            problems.append("primary drain does not start at the drawn trap outlet")
        if problems:
            findings.append(failed(CHECK_ID, f"{obj.tag}: " + "; ".join(problems) + ".", tags))
        else:
            gap = (trap_bottom - max(floors)) / M_PER_IN
            findings.append(passed(CHECK_ID, f"{obj.tag}: modeled pan/support stack, pitched "
                                   f"cabinet and trapped primary connect; trap exterior is "
                                   f"{gap:.2f} inches above the deck, outside the service zone.",
                                   tags))
        findings.append(unknown(CHECK_ID, f"{obj.tag}: drain station and SS3 body/bracket "
                                "allowance remain provisional. Verify rail bearing, pan seams, "
                                "pitched duct transitions and float travel; wet-test shutdown "
                                "before overflow while retaining Gree's blower delay and R32 "
                                "controls. These dimensions do not release fabrication.", tags))
    return findings or [not_applicable(CHECK_ID, "No horizontal FLEXX air handler is placed.")]
