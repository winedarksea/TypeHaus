"""CODE-tier electrical rule — the highest breaker handle of a panel, NEC 240.24(A) / 404.8(A).

NEC 240.24(A): overcurrent devices readily accessible, installed so the centre of the grip
of the operating handle, in its highest position, is not more than 2.0 m (6 ft 7 in.)
above the floor or working platform; 404.8(A) says the same of switches, including a
panel's main. https://www.ecmweb.com/national-electrical-code/code-basics/article/20897104/
and https://www.ecmweb.com/national-electrical-code/article/55125351/ (2017 NEC text).

A panel type rarely states where its top handle sits, so the body top is graded instead:
conservative, since every handle is below it. ``ElectricalDeviceType.top_handle_from_top``
(off the product sheet) refines it. Heights are the device's own ``Mount.elevation`` (the
floor-relative contract, ``resolve/placeables.py``) plus its resolved body height.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, by_result

_CID, _CODE = "electrical.panel_handle_height", "NEC 240.24(A) / 404.8(A)"
_IN = 0.0254
_MAX_HANDLE_M = 79 * _IN  # 2.0 m (6 ft 7 in.); the code's own inch figure governs


def _in(value_m: float) -> str:
    return f'{value_m / _IN:.1f}"'


@check(Tier.CODE, _CID)
def panel_handle_height(ctx: CheckContext) -> list[Finding]:
    """Each panel's highest handle (or, unstated, its body top) is at most 6'-7" AFF."""
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    bodies = {item.tag: item for item in ctx.model.canvas_objects}
    panels = sorted((e for e in ctx.plan.all_elements()
                     if e.element_kind == "ElectricalDevice" and e.kind.value == "panel"),
                    key=lambda e: e.tag)
    if not panels:
        return [by_result(_CID, Result.NOT_APPLICABLE, "no panel in the plan", (), _CODE)]
    out: list[Finding] = []
    for panel in panels:
        product = types.get(panel.type_ref or "")
        body = bodies.get(panel.tag)
        elevation = getattr(panel.mount, "elevation", None)
        if (product is None or body is None or elevation is None
                or body.body_z0_m is None or body.body_z1_m is None):
            out.append(by_result(_CID, Result.UNKNOWN,
                f"{panel.tag}: no floor-relative mount elevation or body height to grade",
                (panel.tag,), _CODE, fix="Mount it with a stated elevation and typed height."))
            continue
        top = elevation.meters + (body.body_z1_m - body.body_z0_m)
        offset = product.top_handle_from_top
        handle = top - offset.meters if offset is not None else top
        what = "top handle" if offset is not None else "body top (no handle offset stated)"
        result = Result.PASS if handle <= _MAX_HANDLE_M + 1e-6 else Result.FAIL
        out.append(by_result(_CID, result,
            f"{panel.tag}: {what} {_in(handle)} AFF against the 79\" maximum",
            (panel.tag,), _CODE,
            fix=None if result is Result.PASS else
            "Lower the mount so the highest handle is at or below 6'-7\" AFF."))
    return out
