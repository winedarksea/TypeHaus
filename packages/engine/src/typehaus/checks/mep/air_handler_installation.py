"""Check the drawn FLEXX installation, without certifying schematic product stations."""

import math

from shapely.geometry import Polygon

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import Tier, check
from typehaus.model.placeable_symbols import model_parts, place_local
from typehaus.model.placeable_symbols._flexx_installation import TRAP_ROLES, primary_port_in
from typehaus.model.placeable_symbols._gree_flexx import CABINET_IN
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_ports import placed_ports
from typehaus.resolve.mep_slope import CONDENSATE_FLOOR_IN_PER_FT
from typehaus.resolve.overlay import union_all
from typehaus.resolve.placeable_bodies import part_outline
from typehaus.resolve.walking_surface import surfaces_at

CHECK_ID = "mep.air_handler_installation"
SYMBOL = "gree-flexx-ultra-24-horizontal"
GEOMETRY_TOLERANCE_M = 0.001 * M_PER_IN
# Gree indoor IOM 4.4 figure, measured from the unit's drain connection.
MINIMUM_TRAP_DROP_IN = 2.0
MINIMUM_SEAL_DEPTH_IN = 3.0
MINIMUM_VENT_RISE_IN = 2.0
MINIMUM_CABINET_SLOPE_IN_PER_FT = 0.125
MINIMUM_PAN_EXTRA_IN = 3.0


def _fit_problems(spec):
    """Hubs that would overlap: a leg shorter than its two fittings cannot be made up."""
    fit = spec.fittings
    elbow, tee = fit.elbow_center_to_hub.inches, fit.tee_center_to_hub.inches
    s = spec.drain_setout(primary_port_in(spec))
    legs = (
        ("adapter to first 90", spec.primary_elbow_offset.inches,
         fit.adapter_projection.inches + elbow),
        ("feeder 90 to union to inlet tee", s.inlet_tee[0] - s.elbow[0],
         elbow + fit.union_length.inches + tee),
        ("trap inlet leg", s.inlet_tee[2] - s.upper_bend[2], tee + elbow),
        ("trap bottom nipple", spec.trap_leg_spacing.inches, 2 * elbow),
        ("trap outlet leg", s.outlet_tee[2] - s.lower_bend[2], elbow + tee),
        ("cleanout riser", s.cleanout_top[2] - s.inlet_tee[2],
         tee + fit.cap_socket_depth.inches),
        ("vent riser", s.vent_top[2] - s.outlet_tee[2], tee),
    )
    return [f"{label} is {length:.3g} in, shorter than its fittings' {needed:.3g} in"
            for label, length, needed in legs if length < needed - 1e-9]


def _code_problems(spec, product):
    s = spec.drain_setout(primary_port_in(spec))
    port_z = s.port[2]
    problems = []
    for value, minimum, label in (
        (port_z - s.outlet_tee[2], MINIMUM_TRAP_DROP_IN, "trap inlet/outlet drop"),
        (spec.trap_seal_depth.inches, MINIMUM_SEAL_DEPTH_IN, "trap seal"),
        (s.vent_top[2] - port_z, MINIMUM_VENT_RISE_IN, "downstream vent rise"),
        (spec.cabinet_slope_in_per_ft, MINIMUM_CABINET_SLOPE_IN_PER_FT, "cabinet pitch"),
        (spec.feeder_slope_in_per_ft, CONDENSATE_FLOOR_IN_PER_FT,
         "feeder slope (IMC 307.2.1)"),
    ):
        if value < minimum - 1e-9:
            problems.append(f"{label} {value:.3g} is below {minimum:g}")
    if (spec.pan_width.inches < product.footprint[0].inches + MINIMUM_PAN_EXTRA_IN
            or spec.pan_depth.inches < product.footprint[1].inches + MINIMUM_PAN_EXTRA_IN):
        problems.append("pan does not extend at least 3 inches beyond cabinet overall sizes")
    if spec.float_trip_depth.meters + spec.pan_sheet.meters >= spec.pan_height.meters:
        problems.append("float trip level reaches or exceeds the pan rim")
    if (len(spec.rail_centers) < 2 or any(
            abs(center.inches) + spec.rail_width.inches / 2 > product.footprint[0].inches / 2
            for center in spec.rail_centers)):
        problems.append("support rails do not bear beneath both cabinet ends")
    return problems


def _bottom(parts, obj):
    return obj.z_m + min(p["center"][2] - p["size"][2] / 2 for p in parts)


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
        problems = _code_problems(spec, product) + _fit_problems(spec)
        if not unit.secondary_drain_pan or not unit.float_switch_ref or unit.overflow_drain_ref:
            problems.append("drawn undrained pan requires the declared pan and float shutdown")
        if unit.install_parts.count(spec.float_switch_product_ref) != 1:
            problems.append("modeled float switch must be selected once in install_parts")
        parts = model_parts(SYMBOL, *(v.meters for v in (*product.footprint, product.height)),
                            air_handler_installation=spec)
        pan, = [p for p in parts if p.get("role") == "flexx:emergency-pan-floor"]
        pan_bottom = _bottom([pan], obj)
        pan_outline = part_outline(pan, obj)
        supports = [s for s in ctx.model.solids
                    if Polygon(s.outline).buffer(GEOMETRY_TOLERANCE_M).covers(pan_outline)
                    and abs(s.z1_m - pan_bottom) <= GEOMETRY_TOLERANCE_M]
        if not supports:
            problems.append("pan bottom is not seated on a modeled continuous platform")
        trap_parts = [p for p in parts if p.get("role") in TRAP_ROLES]
        trap_bottom = _bottom(trap_parts, obj)
        trap_outline = union_all([part_outline(p, obj) for p in trap_parts])
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
        if not all(pan_outline.covers(part_outline(p, obj)) for p in float_parts):
            problems.append("float travel envelope is outside the emergency pan")
        port = ports.get((obj.tag, "condensate_trap_outlet"))
        pipe = pipes.get(unit.pan_drain_ref)
        local_outlet = tuple(v * dimension.inches / reference for v, dimension, reference in zip(
            spec.drain_setout(primary_port_in(spec)).outlet_tee,
            (*product.footprint, product.height), CABINET_IN, strict=True))
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
                                   "cabinet and fitting-built primary make up and connect; "
                                   f"feeder falls {spec.feeder_slope_in_per_ft:g} in/ft; trap "
                                   f"exterior is {gap:.2f} inches above the deck, outside the "
                                   "service zone.", tags))
        findings.append(unknown(CHECK_ID, f"{obj.tag}: drain station and SS3 body/bracket "
                                "allowance remain provisional. Verify rail bearing, pan seams, "
                                "pitched duct transitions and float travel; wet-test shutdown "
                                "before overflow while retaining Gree's blower delay and R32 "
                                "controls. These dimensions do not release fabrication.", tags))
    return findings or [not_applicable(CHECK_ID, "No horizontal FLEXX air handler is placed.")]
