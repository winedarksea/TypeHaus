"""``advisory.door_undercut`` — every hung leaf's gap to the finished floor, against the
house's ``DoorUndercut`` range.

The leaf is a stock slab cut on site to its hung undercut over the higher finished floor
(``resolve/door_sizing``); this reads the gap that came out (``resolve/door_undercut``), so
a type authored past the range, a threshold that lifts the leaf, or a step to a lower floor
with nothing under the leaf to close it is reported. ADVISORY: the range is the house's rule,
not code, and it never blocks the permit gate.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, advisory, not_applicable, passed, unknown
from typehaus.model.enums import DoorOperation
from typehaus.resolve.door_product_spec import house_trim_standard
from typehaus.resolve.door_undercut import realized_undercut

_CID = "advisory.door_undercut"
_IN = 0.0254
_TOLERANCE_M = 0.0005
_LEAF_OPERATIONS = (DoorOperation.SWING, DoorOperation.DOUBLE_SWING, DoorOperation.POCKET)


def _in(value_m: float) -> str:
    return f'{value_m / _IN:.2f}"'


def _graded_doors(ctx: CheckContext):
    types = {t.tag: t for t in ctx.model.plan.library.door_types}
    for opening in sorted(ctx.model.openings, key=lambda o: o.tag):
        door_type = types.get(opening.type_ref or "")
        if (opening.kind == "door" and door_type is not None and not door_type.exterior
                and door_type.bookcase_door is None and door_type.operation in _LEAF_OPERATIONS):
            yield opening, door_type


@check(Tier.ADVISORY, _CID)
def door_undercut(ctx: CheckContext) -> list[Finding]:
    """Each interior leaf's realized undercut over the floor under it."""
    doors = list(_graded_doors(ctx))
    if not doors:
        return [not_applicable(_CID, "this plan hangs no interior leaf")]
    standard = house_trim_standard(ctx.model.plan)
    rule = getattr(standard, "door_undercut", None)
    if rule is None:
        return [unknown(_CID, "the TrimStandard states no door_undercut range to grade "
                              f"{len(doors)} interior leaves against")]
    low, high = rule.minimum.meters, rule.maximum.meters
    span = f"{_in(low)}-{_in(high)}"
    out: list[Finding] = []
    for opening, door_type in doors:
        gap = realized_undercut(opening)
        if gap is None:
            out.append(unknown(_CID, f"{opening.tag}: an adjacent finished floor or the leaf "
                                     "bottom is not resolved", (opening.tag,)))
            continue
        cut = opening.sizing.leaf_cut_m if opening.sizing is not None else 0.0
        hung = (f"{opening.tag} ({door_type.tag}) hangs {_in(gap.higher_m)} over "
                f"{gap.higher_finish or 'the bare deck'}"
                + (f", slab cut {_in(cut)}" if cut > _TOLERANCE_M else ""))
        stepped = gap.lower_m - gap.higher_m > _TOLERANCE_M
        lower = (f"; {_in(gap.lower_m)} over {gap.lower_finish or 'the bare deck'}"
                 f"{' in ' + gap.lower_room if gap.lower_room else ''}" if stepped else "")
        if not low - _TOLERANCE_M <= gap.higher_m <= high + _TOLERANCE_M:
            out.append(advisory(_CID, f"ADVISORY — {hung}, outside the house's {span}{lower}",
                                (opening.tag,), Result.ADVISORY,
                                fix=f"hang the leaf within {span} (DoorType.undercut)"))
        elif stepped and gap.lower_m > high + _TOLERANCE_M and not gap.bridged:
            out.append(advisory(
                _CID, f"ADVISORY — {hung}{lower}, past {_in(high)} with no threshold or "
                      "reducer under the leaf", (opening.tag,), Result.ADVISORY,
                fix="document the transition under the leaf (DoorwayTreatment)"))
        else:
            bridge = ", closed by the transition under the leaf" if stepped and gap.bridged else ""
            out.append(passed(_CID, f"{hung}, within {span}{lower}{bridge}", (opening.tag,)))
    return out
