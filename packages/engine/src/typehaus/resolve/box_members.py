"""A device box's members, read through the scalar fallback (→ resolve/device_banks.py)."""

from __future__ import annotations

from typing import Any, NamedTuple


class BoxMember(NamedTuple):
    tag: str
    uid: str
    kind: str
    circuit: str | None
    footprint: tuple[tuple[float, float], ...]
    shift_m: float


def box_members(box: Any) -> list[BoxMember]:
    """Members left to right; an old record without the tuples is its lead alone."""
    tags = box.device_tags or (box.device_tag,)
    n = len(tags)

    def aligned(values: tuple, fallback: Any) -> tuple:
        return tuple(values) if len(values) == n else (fallback,) + (None,) * (n - 1)

    uids = aligned(box.device_uids, box.device_uid)
    kinds = aligned(box.device_kinds, box.device_kind)
    circuits = aligned(box.circuits, box.circuit)
    feet = aligned(box.member_footprints, box.device_footprint)
    shifts = aligned(box.snap_shifts_m, 0.0)
    return [BoxMember(t, u, k or box.device_kind, c, f if f else box.device_footprint,
                      s or 0.0)
            for t, u, k, c, f, s in zip(tags, uids, kinds, circuits, feet, shifts, strict=True)]


def member_footprint(box: Any, tag: str) -> tuple[tuple[float, float], ...]:
    """The member's own plan footprint, else the lead's ``device_footprint``."""
    for member in box_members(box):
        if member.tag == tag:
            return member.footprint
    return box.device_footprint
