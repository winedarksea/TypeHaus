"""One permit line per engineering kind that no other check names.

``haus engineering`` listed 26 items — base rotation, column heads, the veneer beam, the
thermal breaks and the tiered apron — that no ``@check`` delegated to, so none of them
produced a finding and none reached the permit checklist. A deferral nobody can see on the
checklist reads exactly like a design with nothing outstanding. These checks close that:
each walks its kind's keys through ``registry.keys_of`` (the register's own list, never a
re-walked predicate) and reports each item through ``engineered()``.

**One check id per kind**, never a catch-all. ``_item_from_findings`` folds by check id, so
a shared id would send one kind's UNKNOWN red on another kind's line (the 2026-09-20
``structural.column_base`` incident, ``profile.py``).

The rows live in ``checks/engineered_rows.py``, which also derives each kind's permit line:
registering a calculation flips that line to blocking with no profile edit.
"""

from __future__ import annotations

from typehaus.checks._authoring import engineered as _engineered
from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks.engineered_rows import ROWS, ItemRow
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural._engineering import engineering_context
from typehaus.engineering import item_id, keys_of
from typehaus.findings import Finding, Result


def _items(ctx: CheckContext, row: ItemRow) -> list[Finding]:
    cid, kind = row.check_id, row.kind
    keys = keys_of(kind, engineering_context(ctx))
    if not keys:
        # Earned: the kind's own enumeration ran and found nothing in this plan.
        return [_advisory(cid, row.absent, (), Result.NOT_APPLICABLE)]
    return [_engineered(ctx, cid, item_id(kind, key), f"{key}: {row.subject}", (key,),
                        code=row.code, fix=f"seal `{item_id(kind, key)}` in engineering.toml")
            for key in keys]


def _register(row: ItemRow) -> None:
    def fn(ctx: CheckContext) -> list[Finding]:
        return _items(ctx, row)

    fn.__name__ = fn.__qualname__ = row.name
    fn.__doc__ = row.doc
    globals()[row.name] = check(Tier.STRUCTURAL, row.check_id)(fn)


for _row in ROWS:
    _register(_row)
