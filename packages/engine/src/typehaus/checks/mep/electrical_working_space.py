"""NEC 110.26(D) working-space lighting and the (E)(2) outdoor rules.

``electrical.working_space_lighting`` (D): each indoor panel's room holds a luminaire, and not
every one of them answers only to automatic control. A light on a plain switch, a dimmer, a
smart relay (it keeps its paddle), an integral switch or no switch at all is manual enough; one
whose only controls are occupancy sensors or timers is automatic. No luminaire in the room is
UNKNOWN, since an adjacent source may light the space (the (D) allowance).

``electrical.outdoor_working_space`` (E)(2), for service equipment and panels standing in no
room: the equipment's footprint from grade to 6 ft above its top holds no pipe, duct or
``Equipment`` body (structural overhangs are the exception and are not bodies), and the (A)
zone in front, 36" x 30" (or its width) from grade to 6'-6", holds no other body or run,
conduit excepted. Grade is the site's authored grade. The protection of the enclosure from
contact, vehicles and spillage is a listing and siting judgement, not graded.
"""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.checks._authoring import by_result
from typehaus.checks.mep.electrical_panel_space import _hits, _wall_prisms, _windows
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import DeviceKind
from typehaus.model.nec import NEC, cite

_LIGHT_CID = "electrical.working_space_lighting"
_OUT_CID = "electrical.outdoor_working_space"
_IN = 0.0254
_ABOVE_M = 72 * _IN
_HEIGHT_M = 78 * _IN
_SHRINK_M = 0.001
AUTOMATIC_ONLY_CONTROLS = frozenset({"occupancy", "timer"})


def _room_tag(ctx: CheckContext, obj) -> str | None:
    from typehaus.resolve.room_lookup import room_owning

    room = room_owning(ctx.model, obj.storey, obj.position)
    return None if room is None else room.tag


@check(Tier.CODE, _LIGHT_CID)
def working_space_lighting(ctx: CheckContext) -> list[Finding]:
    """110.26(D): an indoor panel's working space is lit, not by automatic control alone."""
    code = cite(NEC.WORKING_ILLUMINATION)
    objects = {o.tag: o for o in ctx.model.canvas_objects}
    devices = [e for e in ctx.plan.all_elements() if e.element_kind == "ElectricalDevice"]
    by_tag = {e.tag: e for e in devices}
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    panels = sorted((e for e in devices if e.kind is DeviceKind.PANEL and e.tag in objects),
                    key=lambda e: e.tag)
    indoor = [(p, _room_tag(ctx, objects[p.tag])) for p in panels]
    indoor = [(p, room) for p, room in indoor if room is not None]
    if not indoor:
        return [by_result(_LIGHT_CID, Result.NOT_APPLICABLE, "no panel stands indoors", (),
                          code)]
    lights: dict[str, list] = {}
    for light in devices:
        if light.kind is DeviceKind.LIGHT and light.tag in objects:
            room = _room_tag(ctx, objects[light.tag])
            if room is not None:
                lights.setdefault(room, []).append(light)

    def manual(light) -> bool:
        if getattr(types.get(light.type_ref or ""), "integral_switch", False):
            return True
        controls = [getattr(types.get(getattr(by_tag.get(s), "type_ref", None) or ""),
                            "control", None) for s in light.controlled_by]
        return not controls or any(c not in AUTOMATIC_ONLY_CONTROLS for c in controls)

    out: list[Finding] = []
    for panel, room in indoor:
        here = sorted(lights.get(room, ()), key=lambda e: e.tag)
        if not here:
            out.append(by_result(_LIGHT_CID, Result.UNKNOWN, f"{panel.tag}: {room} holds no "
                                 "luminaire; an adjacent source may light the working space",
                                 (panel.tag, room), code, "add a luminaire in the room"))
            continue
        hand = [e.tag for e in here if manual(e)]
        if hand:
            out.append(by_result(_LIGHT_CID, Result.PASS, f"{panel.tag}: {room} is lit by "
                                 f"{len(here)} luminaire(s), {len(hand)} under manual control "
                                 f"({', '.join(hand[:4])})", (panel.tag, room), code))
        else:
            out.append(by_result(_LIGHT_CID, Result.UNKNOWN, f"{panel.tag}: every luminaire in "
                                 f"{room} answers only to an occupancy sensor or timer; (D) bars "
                                 "automatic control alone unless the sensor has a manual "
                                 "override", (panel.tag, room, *(e.tag for e in here)), code,
                                 "put one luminaire on a wall switch"))
    return out


@check(Tier.CODE, _OUT_CID)
def outdoor_working_space(ctx: CheckContext) -> list[Finding]:
    """110.26(E)(2): outdoor service equipment's dedicated space and (A) zone are clear."""
    from typehaus.checks.integrity.clear_zones import obstruction_prisms
    from typehaus.resolve.mep_envelopes import envelopes
    from typehaus.resolve.site_earth import site_grade_elevation_m

    code = cite(NEC.DEDICATED_SPACE_OUTDOOR, NEC.WORKING_SPACE)
    objects = {o.tag: o for o in ctx.model.canvas_objects}
    kinds = (DeviceKind.METER, DeviceKind.PANEL)
    outdoor = sorted((e for e in ctx.plan.all_elements() if e.element_kind == "ElectricalDevice"
                      and e.kind in kinds and e.tag in objects
                      and _room_tag(ctx, objects[e.tag]) is None), key=lambda e: e.tag)
    if not outdoor:
        return [by_result(_OUT_CID, Result.NOT_APPLICABLE, "no service equipment or panel "
                          "stands outdoors", (), code)]
    grade = site_grade_elevation_m(ctx.model)
    runs = envelopes(ctx.model)
    conduits = {env.tag for env in runs if env.kind == "conduit"}
    candidates = [p for p in obstruction_prisms(ctx.model, runs) + _wall_prisms(ctx)
                  if p.tag not in conduits]
    equipment = {e.tag for e in ctx.plan.all_elements() if e.element_kind == "Equipment"}
    foreign = [p for p in candidates if p.kind in ("pipe", "duct") or p.tag in equipment]
    out: list[Finding] = []
    for device in outdoor:
        body = objects[device.tag]
        if body.body_z1_m is None or len(body.footprint) < 3:
            out.append(by_result(_OUT_CID, Result.UNKNOWN, f"{device.tag}: no resolved body",
                                 (device.tag,), code))
            continue
        skip = {device.tag, body.attachment_wall}
        top = body.body_z1_m
        footprint = Polygon(body.footprint).buffer(-_SHRINK_M, join_style=2)
        dedicated = sorted({p.tag for p in foreign if p.tag not in skip
                            and _hits(footprint, grade + _SHRINK_M, top + _ABOVE_M, p)})
        z1 = max(grade + _HEIGHT_M, top)
        best: list[str] | None = None
        for zone in _windows(body):
            blocked = sorted({p.tag for p in candidates if p.tag not in skip
                              and _hits(zone, grade + _SHRINK_M, z1, p)})
            if best is None or len(blocked) < len(best):
                best = blocked
            if not blocked:
                break
        problems = []
        if dedicated:
            problems.append(f"{', '.join(dedicated)} in the dedicated space (grade to 6 ft "
                            "above the top)")
        if best:
            problems.append(f"no clear 36\" x 30\" working-space position; the best holds "
                            f"{', '.join(best)}")
        if problems:
            out.append(by_result(_OUT_CID, Result.FAIL, f"{device.tag}: " + "; ".join(problems),
                                 (device.tag, *dedicated, *(best or ())), code,
                                 "move the pipe, duct or equipment clear of the enclosure"))
        else:
            out.append(by_result(_OUT_CID, Result.PASS, f"{device.tag}: dedicated space clear "
                                 f"to {(top + _ABOVE_M - grade) / _IN:.0f}\" above grade, and a "
                                 "36\" x 30\" working space clear from grade", (device.tag,),
                                 code))
    return out
