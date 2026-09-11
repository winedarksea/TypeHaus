"""The rules a site-state file must satisfy, run at load and by every write.

``haus site validate`` is the agent interface: the plan for this phase is that the agent
editing ``tasks.toml`` and ``inspections.toml`` is Claude Code editing TOML directly, that
``git diff`` is the change review, and that this module is what tells either of us the edit
does not hold together. So an error here names the file, the key and the reason, and never
the fix — the fix is a judgement.

Two severities, and the split is the plan's soft-gate decision. An **error** is a file that
does not describe a buildable sequence: a dependency loop, a verified visit with an open
hold, two visits silently billing the same BOM row. A **warning** is a thing worth seeing
that must not stop anybody: a missing certificate of insurance, a package whose split leaves
rows unassigned, a gate the engine declined to imply. Great subs without digital paperwork
have to stay bookable.
"""

from __future__ import annotations

from typing import Any

from typehaus.schedule.graph import INSPECTION_PREFIX


def _known_refs(board: Any) -> set[str]:
    refs = {visit.slug for visit in board.visits}
    refs |= {f"{visit.slug}#{point['id']}"
             for visit in board.visits for point in visit.checkpoints}
    refs |= {f"{INSPECTION_PREFIX}{record.id}" for record in board.inspections}
    return refs


def dangling_dependencies(board: Any) -> list[str]:
    known = _known_refs(board)
    out: list[str] = []
    for visit in board.visits:
        for dependency in visit.depends_on:
            if dependency not in known:
                out.append(f"[visits.\"{visit.slug}\"] depends_on {dependency!r}, which "
                           "names no visit, checkpoint or inspection in this model")
        for point in visit.checkpoints:
            for dependency in point.get("after") or ():
                if dependency not in known:
                    out.append(f"[visits.\"{visit.slug}\"] checkpoint "
                               f"{point['id']!r} waits on {dependency!r}, which names "
                               "nothing in this model")
    return out


def shared_rows(board: Any) -> list[str]:
    """Two visits billing one BOM row double-counts the estimate unless both say so."""
    claims: dict[tuple[str, str], list[Any]] = {}
    for visit in board.visits:
        for row in visit.rows:
            claims.setdefault(row, []).append(visit)
    out: list[str] = []
    for (section, key), visits in sorted(claims.items()):
        if len(visits) < 2 or all(v.shared_rows for v in visits):
            continue
        named = ", ".join(sorted(v.slug for v in visits))
        out.append(f"BOM row {section}:{key} is claimed by {len(visits)} visits ({named}) "
                   "and at least one does not declare shared_rows = true — the estimate "
                   "counts it once per visit")
    return out


def unassigned_scope(board: Any) -> list[str]:
    """A split package whose rows or tags no visit covers: work nobody is arriving for."""
    by_package: dict[str, list[Any]] = {}
    for visit in board.visits:
        if not visit.implicit and not visit.standalone:
            by_package.setdefault(visit.package, []).append(visit)
    out: list[str] = []
    for package, visits in sorted(by_package.items()):
        covered_rows = {row for visit in visits for row in visit.rows}
        covered_tags = {tag for visit in visits for tag in visit.element_tags}
        whole = next((v for v in visits if not v.rows and not v.element_tags), None)
        if whole is not None:
            continue
        missing_rows = sorted(set(_package_rows(board, package)) - covered_rows)
        missing_tags = sorted(set(_package_tags(board, package)) - covered_tags)
        if missing_rows:
            shown = ", ".join(f"{s}:{k}" for s, k in missing_rows[:4])
            out.append(f"{package}: {len(missing_rows)} BOM row(s) fall to no visit in the "
                       f"split ({shown})")
        if missing_tags:
            out.append(f"{package}: {len(missing_tags)} element tag(s) fall to no visit in "
                       f"the split ({', '.join(missing_tags[:4])})")
    return out


def _package_rows(board: Any, package: str) -> tuple[tuple[str, str], ...]:
    return getattr(board, "package_rows", {}).get(package, ())


def _package_tags(board: Any, package: str) -> tuple[str, ...]:
    return getattr(board, "package_tags", {}).get(package, ())


def verification_errors(board: Any, model: Any = None) -> list[str]:
    """``verified`` is the owner's own walk, and this is the whole of what it claims.

    Every hold cleared, every handoff item ticked or skipped *with a reason*, and every
    inspection this visit depends on resolved. The first of those is enforced entry-locally
    in ``takeoff/visit_toml.py``; the other two need the board and live here.
    """
    from typehaus.schedule.handoff import handoff_items

    by_inspection = {record.id: record for record in board.inspections}
    out: list[str] = []
    for visit in board.visits:
        if visit.status != "verified":
            continue
        settled = set(visit.checked) | {item["id"] for item in visit.skipped}
        if model is not None:
            outstanding = [item.id for item in handoff_items(model, visit)
                           if item.id not in settled]
            if outstanding:
                out.append(f"[visits.\"{visit.slug}\"] is verified with "
                           f"{len(outstanding)} handoff item(s) neither ticked nor "
                           f"skipped: {outstanding[0]!r}")
        for dependency in visit.depends_on:
            if not dependency.startswith(INSPECTION_PREFIX):
                continue
            record = by_inspection.get(dependency[len(INSPECTION_PREFIX):])
            if record is None or not record.resolved:
                out.append(f"[visits.\"{visit.slug}\"] is verified while {dependency} is "
                           f"{record.state if record else 'unknown'}")
    return out


def exception_warnings(board: Any) -> list[str]:
    out: list[str] = []
    for visit in board.visits:
        recorded = {item["hold"] for item in visit.exceptions}
        if visit.status not in ("done", "verified"):
            continue
        for hold in visit.constraints:
            if hold.kind == "authored" and hold.severity == "blocking" and not hold.met \
                    and hold.label not in recorded:
                out.append(f"[visits.\"{visit.slug}\"] is {visit.status} with the hold "
                           f"{hold.label!r} still open and no exception recorded")
    return out


def rewalk_warnings(board: Any) -> list[str]:
    out: list[str] = []
    for visit in board.visits:
        if visit.orphan_ticks:
            out.append(f"[visits.\"{visit.slug}\"] has {len(visit.orphan_ticks)} tick(s) "
                       f"naming no derived handoff item: {visit.orphan_ticks[0]!r}")
        elif visit.needs_rewalk:
            out.append(f"[visits.\"{visit.slug}\"]: the handoff set changed under existing "
                       "ticks — needs re-walk")
    return out


def validate(board: Any, model: Any = None) -> tuple[list[str], list[str]]:
    """``(errors, warnings)``. ``haus site validate`` exits 1 on any error."""
    errors = list(board.errors)
    errors += dangling_dependencies(board)
    errors += shared_rows(board)
    errors += verification_errors(board, model)
    warnings = unassigned_scope(board)
    warnings += exception_warnings(board)
    warnings += rewalk_warnings(board)
    warnings += [f"{slug}: authored state that no longer derives from the model"
                 for slug in board.stale]
    warnings += [f"{trade}: the gate {ref} is not implied on the unsplit package — it "
                 "follows another gate on the same trade, so applying both is a loop"
                 for trade, ref in board.dropped_gates]
    return errors, warnings
