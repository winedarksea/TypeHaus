"""24 V LED gear: reachable, paired, and wired to what it feeds (decision #137).

``electrical.led_gear_access``: a driver's splice box is a junction box (NEC 314.29: no
building finish removed to reach it) and every driver and controller sheet says keep it
accessible. A body above a finished ceiling or soffit plane, or recessed into a wall,
is concealed and PASSes only with a framed opening (a ``SoffitOpening``, or a placeable
whose type is an ``access_opening``) within arm's reach. Exposed gear PASSes. A controller
must also sit within the ``LedStandard``'s ``max_controller_distance`` of its driver.

``electrical.led_wiring``: a run's ``controller_ref`` names an LED_CONTROLLER on the run's
own driver, with the channels its ``color_mode`` needs and the current its tape draws.
"""

from __future__ import annotations

import math

from shapely.geometry import Point, Polygon

from typehaus.checks._authoring import advisory, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.led import COLOR_MODE_CHANNELS, LedStandard
from typehaus.model.nec import NEC
from typehaus.resolve.placeables import placed_xy

_ACCESS = "electrical.led_gear_access"
_WIRING = "electrical.led_wiring"
_GEAR = ("led_driver", "led_controller")
# A hand through an opening reaches this far past its edge, to the nearest point of the body.
REACH_M = 0.6
_TOL_M = 0.005
_IN = 0.0254
_DC_V = 24.0


def led_standard(plan) -> LedStandard | None:
    return next((el for el in plan.all_elements() if isinstance(el, LedStandard)), None)


def gear_devices(plan) -> dict[str, object]:
    return {el.tag: el for s in plan.storeys for el in plan.storey_elements(s.tag)
            if el.element_kind == "ElectricalDevice"
            and getattr(el.kind, "value", "") in _GEAR}


def concealment(model, obj, faces) -> tuple[str | None, float | None]:
    """(what hides the body, that plane's z), or (None, None) for an exposed body."""
    from typehaus.resolve.ceilings import finished_ceiling_at

    mount = getattr(obj, "mount", None)
    if obj.attachment_wall and getattr(mount, "recessed_into_host_surface", False):
        return f"recessed in {obj.attachment_wall}", None
    if obj.body_z0_m is None:
        return None, None
    plane = finished_ceiling_at(faces, obj.storey, None, obj.position)
    if plane is not None and obj.body_z0_m >= plane - _TOL_M:
        return "the finished ceiling", plane
    point = Point(obj.position)
    for soffit in model.soffits:
        if soffit.storey == obj.storey and Polygon(soffit.outline).covers(point) \
                and soffit.z0_m - _TOL_M <= obj.body_z0_m <= soffit.z1_m:
            return f"soffit {soffit.tag}", soffit.z0_m
    return None, None


def _openings(model, storey: str) -> list[tuple[str, Polygon]]:
    found = [(tag, Polygon(outline)) for soffit in model.soffits if soffit.storey == storey
             for tag, outline in soffit.openings]
    furniture = {t.tag for t in model.plan.library.furniture_types
                 if getattr(t, "access_opening", False)}
    found += [(o.tag, Polygon(o.footprint)) for o in model.canvas_objects
              if o.storey == storey and o.type_ref in furniture and len(o.footprint) >= 3]
    return found


@check(Tier.ADVISORY, _ACCESS)
def led_gear_access(ctx: CheckContext) -> list[Finding]:
    from typehaus.resolve.ceilings import ceiling_faces

    gear = gear_devices(ctx.plan)
    if not gear:
        return [unknown(_ACCESS, "no LED drivers or controllers modeled")]
    objects = {o.tag: o for o in ctx.model.canvas_objects if o.tag in gear}
    faces = ceiling_faces(ctx.model)
    standard = led_standard(ctx.plan)
    out: list[Finding] = []
    for tag in sorted(gear):
        obj = objects.get(tag)
        if obj is None or obj.body_z0_m is None:
            out.append(unknown(_ACCESS, f"{tag} has no resolved body to grade", (tag,)))
            continue
        hidden, _plane = concealment(ctx.model, obj, faces)
        if hidden is None:
            out.append(passed(_ACCESS, f"{tag} is exposed, reachable without opening a finish",
                              (tag,)))
        else:
            body = Polygon(obj.footprint) if len(obj.footprint) >= 3 else Point(obj.position)
            near = [(name, hole.distance(body)) for name, hole in _openings(ctx.model,
                                                                            obj.storey)]
            near = [(name, d) for name, d in near if d <= REACH_M]
            if near:
                name, d = min(near, key=lambda item: item[1])
                out.append(passed(_ACCESS, f"{tag} above {hidden} is reached through {name} "
                                           f"({d / _IN:.0f}\" off its edge)", (tag, name)))
            else:
                out.append(advisory(_ACCESS, (
                    f"{tag} is concealed by {hidden} with no access opening within "
                    f"{REACH_M / _IN:.0f}\": its splice box must be reachable without removing "
                    f"building finish ({NEC.EDITION} 314.29), and the sheet says keep it "
                    "accessible"), (tag,), Result.FAIL))
        out.extend(_pairing(ctx, gear, gear[tag], standard))
    return out


def _pairing(ctx, gear: dict, device, standard) -> list[Finding]:
    if getattr(device.kind, "value", "") != "led_controller" or not device.psu_ref:
        return []
    driver = gear.get(device.psu_ref)
    a, b = placed_xy(ctx.model, device), placed_xy(ctx.model, driver) if driver else None
    if driver is None or a is None or b is None:
        return [advisory(_ACCESS, f"{device.tag} names driver {device.psu_ref}, which is no "
                                  "placed LED_DRIVER", (device.tag,), Result.FAIL)]
    if standard is None:
        return [unknown(_ACCESS, f"{device.tag}: no LedStandard states how far a controller "
                                 "may stand from its driver", (device.tag,))]
    d, limit = math.dist(a, b), standard.max_controller_distance.meters
    if d > limit + _TOL_M:
        return [advisory(_ACCESS, f"{device.tag} stands {d / _IN / 12:.1f}' from its driver "
                                  f"{driver.tag}, past the standard's {limit / _IN / 12:g}'",
                         (device.tag, driver.tag), Result.FAIL)]
    return []


@check(Tier.ADVISORY, _WIRING)
def led_wiring(ctx: CheckContext) -> list[Finding]:
    gear = gear_devices(ctx.plan)
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    out: list[Finding] = []
    load: dict[str, float] = {}
    graded = 0
    for run in ctx.model.light_runs:
        product = types.get(run.type_ref)
        mode = getattr(product, "color_mode", "fixed")
        if run.controller_ref is None:
            if mode != "fixed":
                out.append(unknown(_WIRING, f"{run.tag} is {mode} tape and names no "
                                            "controller", (run.tag,)))
            continue
        controller = gear.get(run.controller_ref)
        if controller is None or controller.kind.value != "led_controller":
            out.append(advisory(_WIRING, f"{run.tag} names controller {run.controller_ref}, "
                                         "which is no LED_CONTROLLER", (run.tag,), Result.FAIL))
            continue
        if controller.psu_ref != run.psu_ref:
            out.append(advisory(_WIRING, f"{run.tag} is on driver {run.psu_ref} but its "
                                         f"controller {controller.tag} is on "
                                         f"{controller.psu_ref}", (run.tag, controller.tag),
                                Result.FAIL))
            continue
        spec = getattr(types.get(controller.type_ref or ""), "led_controller", None)
        if spec is None:
            out.append(unknown(_WIRING, f"{controller.tag}'s type states no LedController",
                               (controller.tag,)))
            continue
        need = COLOR_MODE_CHANNELS.get(mode, 1)
        if spec.channels < need:
            out.append(advisory(_WIRING, f"{run.tag} is {mode} ({need} channels) on "
                                         f"{controller.tag}'s {spec.channels}",
                                (run.tag, controller.tag), Result.FAIL))
            continue
        watts = (getattr(product, "watts_per_ft", None) or 0.0) * run.length_m / 0.3048
        load[controller.tag] = load.get(controller.tag, 0.0) + watts
        graded += 1
    for tag, watts in sorted(load.items()):
        controller = gear[tag]
        spec = types[controller.type_ref].led_controller
        amps = watts / _DC_V
        if spec.max_current_a is None:
            out.append(unknown(_WIRING, f"{tag}'s sheet publishes no output current; its tape "
                                        f"draws {amps:.2f} A", (tag,)))
        elif amps > spec.max_current_a + 1e-6:
            out.append(advisory(_WIRING, f"{tag} drives {amps:.2f} A of tape against its "
                                         f"{spec.max_current_a:g} A rating", (tag,),
                                Result.FAIL))
    if graded and not any(f.result is Result.FAIL for f in out):
        out.append(passed(_WIRING, f"{graded} controller-fed runs are on their own driver's "
                                   "controller, with the channels and current they need"))
    if not out:
        out.append(unknown(_WIRING, "no controller-fed light runs modeled"))
    return out


__all__ = ["REACH_M", "concealment", "gear_devices", "led_standard"]
