"""MN residential code rules — a few high-value ones (R305/R310/R311.7/R311.6, → 12).

Every rule is tri-state (#32): a rule that cannot evaluate reports UNKNOWN with the reason
and is counted separately, never as a pass.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import SLEEPING_OCCUPANCIES, Occupancy
from typehaus.quantities import ft, inch

_MIN_CEILING = ft(7)
_MIN_EGRESS_WIDTH = inch(20)
_MIN_EGRESS_HEIGHT = inch(24)
_MAX_EGRESS_SILL = inch(44)
_MIN_EGRESS_AREA_SF = 5.7  # grade-floor 5.0; upper 5.7 (R310.2.1)
_MIN_DOOR_CLEAR = inch(31.75)  # 32" nominal clear (R311.2)


def _pass(cid: str, msg: str, code: str) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, code_ref=code,
                   result=Result.PASS)


def _fail(cid: str, msg: str, tags: tuple[str, ...], code: str) -> Finding:
    return Finding(severity=Severity.ERROR, check_id=cid, message=msg, element_tags=tags,
                   code_ref=code, result=Result.FAIL)


def _unknown(cid: str, reason: str, tags: tuple[str, ...], code: str) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=f"UNKNOWN — {reason}",
                   element_tags=tags, code_ref=code, result=Result.UNKNOWN)


@check(Tier.CODE, "code.R305_ceiling_height")
def ceiling_height(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for room in ctx.plan.all_elements():
        if room.element_kind != "Room" or room.occupancy is Occupancy.UNCONDITIONED:
            continue
        if room.ceiling is None:
            storey = _room_storey(ctx, room.tag)
            h = storey.default_ceiling_height if storey else None
        elif hasattr(room.ceiling, "meters"):
            h = room.ceiling
        else:
            out.append(_unknown("code.R305_ceiling_height",
                                "ceiling follows roof (resolves in M3)", (room.tag,), "R305.1"))
            continue
        if h is None:
            out.append(_unknown("code.R305_ceiling_height", "no ceiling height",
                                (room.tag,), "R305.1"))
        elif h < _MIN_CEILING:
            out.append(_fail("code.R305_ceiling_height",
                             f"{room.tag} ceiling {h.fmt()} < 7'-0\" minimum", (room.tag,),
                             "R305.1"))
        else:
            out.append(_pass("code.R305_ceiling_height", f"{room.tag} ceiling ok", "R305.1"))
    return out


@check(Tier.CODE, "code.R310_egress")
def egress_windows(ctx: CheckContext) -> list[Finding]:
    """Every sleeping room needs a compliant emergency escape opening (R310)."""
    out: list[Finding] = []
    windows = {op.host_wall: op for op in ctx.model.openings if not op.is_door}
    for room in ctx.plan.all_elements():
        if room.element_kind != "Room" or room.occupancy not in SLEEPING_OCCUPANCIES:
            continue
        wins = [op for op in ctx.model.openings if not op.is_door]
        best = None
        for op in wins:
            area = op.width_m * op.height_m * 10.7639
            if (op.width_m >= _MIN_EGRESS_WIDTH.meters
                    and op.height_m >= _MIN_EGRESS_HEIGHT.meters
                    and area >= _MIN_EGRESS_AREA_SF
                    and op.sill_m <= _MAX_EGRESS_SILL.meters):
                best = op
                break
        if best is not None:
            out.append(_pass("code.R310_egress",
                             f"{room.tag} has egress window {best.tag}", "R310.1"))
        elif not wins:
            out.append(_fail("code.R310_egress",
                             f"sleeping room {room.tag} has no egress window", (room.tag,),
                             "R310.1"))
        else:
            out.append(_fail("code.R310_egress",
                             f"sleeping room {room.tag} window fails egress dimensions",
                             (room.tag,), "R310.2"))
    return out


@check(Tier.CODE, "code.R311_door_width")
def egress_door_width(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for door in (e for e in ctx.plan.all_elements() if e.element_kind == "Door"):
        dt = next((t for t in ctx.plan.library.door_types if t.tag == door.type_ref), None)
        if dt is None:
            out.append(_unknown("code.R311_door_width", "unknown door type",
                                (door.tag,), "R311.2"))
            continue
        if dt.exterior and dt.width < _MIN_DOOR_CLEAR:
            out.append(_fail("code.R311_door_width",
                             f"egress door {door.tag} width {dt.width.fmt()} < 32\" clear",
                             (door.tag,), "R311.2"))
        else:
            out.append(_pass("code.R311_door_width", f"door {door.tag} width ok", "R311.2"))
    return out


def _room_storey(ctx: CheckContext, room_tag: str):
    for storey in ctx.plan.storeys:
        if any(e.tag == room_tag for e in ctx.plan.storey_elements(storey.tag)):
            return storey
    return None
