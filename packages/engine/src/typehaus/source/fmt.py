"""``haus fmt`` — merge-friendly canonical style + missing-uid auto-fix (→ 20 §libcst).

M2 scope (WP2.2): assign a fresh ``uid=`` to every element constructor call that lacks one
(the auto-fix the dialect linter flags), preserving all other formatting and comments by
construction. The fuller canonical normalizer (one declaration per statement, stable
ordering) builds on this same CST pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import libcst as cst

from typehaus.model.ids import new_uid
from typehaus.model.registry import is_registered_element
from typehaus.source.loader import editable_files


@dataclass
class FmtResult:
    source: str
    uids_added: int


class _UidInserter(cst.CSTTransformer):
    def __init__(self) -> None:
        self.added = 0

    def leave_Call(self, original: cst.Call, updated: cst.Call) -> cst.BaseExpression:
        if not (isinstance(original.func, cst.Name)
                and is_registered_element(original.func.value)):
            return updated
        has_uid = any(a.keyword is not None and a.keyword.value == "uid"
                      for a in original.args)
        if has_uid:
            return updated
        self.added += 1
        uid_arg = cst.Arg(
            keyword=cst.Name("uid"),
            value=cst.SimpleString(f'"{new_uid()}"'),
            equal=cst.AssignEqual(
                whitespace_before=cst.SimpleWhitespace(""),
                whitespace_after=cst.SimpleWhitespace(""),
            ),
            comma=cst.Comma(whitespace_after=cst.SimpleWhitespace(" ")),
        )
        return updated.with_changes(args=[uid_arg, *updated.args])


def fmt_source(source: str) -> FmtResult:
    """Return ``source`` with a fresh uid on every element call that lacks one."""
    module = cst.parse_module(source)
    inserter = _UidInserter()
    module = module.visit(inserter)
    return FmtResult(source=module.code, uids_added=inserter.added)


def fmt_house(house_dir: Path) -> dict[str, int]:
    """Format every editable file in place; return {relpath: uids_added}."""
    report: dict[str, int] = {}
    for path in editable_files(house_dir):
        result = fmt_source(path.read_text())
        rel = path.relative_to(house_dir).as_posix()
        report[rel] = result.uids_added
        if result.uids_added:
            path.write_text(result.source)
    return report
