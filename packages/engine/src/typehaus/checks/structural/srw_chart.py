"""A segmental gravity wall read off its maker's published chart — and the sheet it stands on.

``structural.srw_gravity_chart``: one finding per wall that authors ``SegmentalWallSpec.chart``
and ``published`` (AB Table 1.3). IRC R404.4 does not engage at <= 48" of unbalanced fill with
no added load, so the chart row is a prescriptive read, not an engineered item
(``tiered_retaining`` is retired entirely, 2026-11-23; the ``wall_panel`` precedent). The
finding prints every applicability condition beside what the model draws. A footingless
wall retaining fill with no chart row is UNKNOWN here, since no register item catches it now.
Any condition off the row is a FAIL — the chart is true for the section, not the height;
one the model cannot answer is UNKNOWN.

**Oracle.** ``houses/catlin/notes/raised_garden_srw.md`` §10; ``tests/test_srw_chart.py``.
"""

from __future__ import annotations

from typehaus.checks._authoring import structural_advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural._engineering import engineering_context
from typehaus.engineering.segmental_wall import segmental_walls
from typehaus.engineering.srw_chart import applicability
from typehaus.engineering.srw_scope import on_chart_path
from typehaus.engineering.srw_tiers import lower_tiers
from typehaus.findings import Finding, Result, not_applicable

_ID = "structural.srw_gravity_chart"
_CODE = "IRC R404.4; Allan Block Commercial Installation Manual Table 1.3"


def graded_wall(ectx, wall) -> Finding:  # type: ignore[no-untyped-def]
    row = wall.srw.published
    conds = applicability(ectx, wall, lower_tiers(ectx, wall))
    sheet = "; ".join(f"{c.name}: {c.drawn} (row: {c.row}) "
                      f"[{'ok' if c.ok else 'OFF ROW' if c.ok is False else '?'}]"
                      for c in conds)
    off = [c.name for c in conds if c.ok is False]
    unknown = [c.name for c in conds if c.ok is None]
    tags = (wall.tag,)
    if off:
        return structural_advisory(
            _ID, f"{wall.tag}: the chart row ({row.table}) does not describe this wall — off "
                 f"the row: {', '.join(off)}. Applicability sheet: {sheet}", tags, Result.FAIL,
            fix_hint="change the section to the row (lower, cap, drain, move the water), or "
                     "give the wall an engineered design", code=_CODE)
    if unknown:
        return structural_advisory(
            _ID, f"{wall.tag}: the model cannot answer {', '.join(unknown)} for the chart "
                 f"row. Applicability sheet: {sheet}", tags, Result.UNKNOWN, code=_CODE)
    return structural_advisory(
        _ID, f"{wall.tag}: a prescriptive read of a published table — {row.table}, every "
             f"condition answered. Applicability sheet: {sheet}. Conditions the engine does "
             f"not check: {row.condition} ({row.source})", tags, Result.PASS, code=_CODE)


def _unclaimed(wall) -> Finding:  # type: ignore[no-untyped-def]
    """A footingless fill-retaining wall with no chart row: no register item catches it now."""
    fill_in = wall.unbalanced_fill.inches
    why = ("R404.4 is engaged (over 48\" of unbalanced fill): it needs an engineered design"
           if fill_in > 48.0 + 1e-9 else
           "no published gravity-chart row and section are authored on its SegmentalWallSpec")
    return structural_advisory(
        _ID, f"{wall.tag}: a segmental wall retaining {fill_in:.0f}\" — {why}",
        (wall.tag,), Result.UNKNOWN, code=_CODE,
        fix_hint="author SegmentalWallSpec.published and .chart from the maker's table, or "
                 "have the wall designed")


@check(Tier.STRUCTURAL, _ID)
def srw_gravity_chart(ctx: CheckContext) -> list[Finding]:
    ectx = engineering_context(ctx)
    walls = segmental_walls(ectx)
    if not walls:
        return [not_applicable(
            _ID, "no footingless wall in this plan retains fill", (), code=_CODE)]
    return [graded_wall(ectx, w) if on_chart_path(w) else _unclaimed(w) for w in walls]
