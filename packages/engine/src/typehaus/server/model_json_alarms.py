"""Each alarm head as served — the resolved record (``resolve/alarm_heads.py``) the GLB and IFC
also read, so the viewer derives neither the point nor the body."""

from __future__ import annotations

from typing import Any

from typehaus.resolve.model import ResolvedModel


def _r(value: float) -> float:
    return round(value, 6)


def alarm_points(model: ResolvedModel, alarm: Any, storey_tag: str) -> dict[str, Any]:
    """``x``/``y``/``z``/``mount``/``type`` and the body ``solid`` of one alarm."""
    head = next((h for h in model.alarm_heads if h.uid == alarm.uid), None)
    if head is None:
        return {"x": None, "y": None, "z": None, "mount": None, "type": None, "solid": None}
    solid = None
    if head.body is not None:
        prism = head.body.solids[0]
        solid = {"ring": [[_r(x), _r(y)] for x, y in prism.ring],
                 "z0_m": _r(prism.z0_m), "z1_m": _r(prism.z1_m)}
    return {"x": head.x, "y": head.y, "z": head.z, "mount": head.mount,
            "type": head.type_ref, "solid": solid}
