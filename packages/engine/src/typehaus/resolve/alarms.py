"""Where an alarm head mounts in plan — one rule for the plan sheet, the checks and the viewer."""

from __future__ import annotations

from typing import Any


def alarm_xy(alarm: Any, room: Any | None) -> tuple[float, float] | None:
    """The authored ``Alarm.position``, else the hosting room's seed; ``None`` with neither."""
    if alarm.position is not None:
        return alarm.position.xy_m
    return room.seed.xy_m if room is not None else None
