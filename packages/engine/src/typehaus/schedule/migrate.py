"""``haus site migrate`` — the old spellings folded into the current ones, in place.

Four jobs, and each of them refuses to invent.

**One status ladder.** ``[entries]."task/x/y".status`` used to be invisible to the board,
which built an implicit visit from a blank entry. The board now *reads* that row, so the two
ladders meet without a rewrite — what this reports instead is the case a rewrite could only
have guessed at: a package marked ``done`` in ``[entries]`` that somebody has since split
into visits with mixed status. Listed for review, never resolved.

**Attempts.** An inspection's single ``result`` / ``result_date`` / ``history`` slot becomes
one entry in ``attempts``, keeping the date, the inspector and the note. A second attempt
used to overwrite the first.

**Waivers.** ``waived = "some string"`` becomes a table with ``by``/``date``/``ref``, with
the old string kept as the note, because a waiver that outranks model evidence has to say
who granted it.

**Retired trade tokens.** ``roof`` became ``roofing`` and ``floors`` became ``flooring``
when the vocabulary widened (2026-09-12). Those two are one-to-one and are renamed
TEXTUALLY — in ``task/<trade>/`` slugs, ``trade = "..."``, ``gates`` and ``trades`` — so
the file's comments survive (``task_state.write_tasks`` regenerates from scratch and would
erase them). ``walls`` split into siding / insulation / drywall / paint and ``furniture``
casework moved to ``millwork``; those are one-to-many, so every place that names one is
listed for review, never resolved.

Nothing here promotes ``done`` to ``verified``. ``verified`` is the owner's own walk and no
migration can have done it for them.
"""

from __future__ import annotations

import re
from pathlib import Path

#: Old token -> new token, for the renames that are one-to-one.
RENAMED_TRADES: dict[str, str] = {"roof": "roofing", "floors": "flooring"}

#: Old tokens with no single successor. Printed, never rewritten.
SPLIT_TRADES: dict[str, str] = {
    "walls": "siding / insulation / drywall / paint — pick per visit",
    "furniture": "furniture (loose) or millwork (casework) — pick per visit",
}


def _rename_tokens(text: str) -> tuple[str, list[str]]:
    """Apply :data:`RENAMED_TRADES` to the spellings a site file carries a trade in."""
    changes: list[str] = []
    for old, new in RENAMED_TRADES.items():
        patterns = (
            (rf'(task/){old}(/)', rf'\g<1>{new}\g<2>'),
            (rf'(trade\s*=\s*"){old}(")', rf'\g<1>{new}\g<2>'),
            (rf'(gates\s*=\s*\[[^\]]*"){old}(")', rf'\g<1>{new}\g<2>'),
            (rf'(trades\s*=\s*\[[^\]]*"){old}(")', rf'\g<1>{new}\g<2>'),
        )
        for pattern, replacement in patterns:
            text, count = re.subn(pattern, replacement, text)
            if count:
                changes.append(f"{count} × {old!r} -> {new!r} ({pattern.split('(')[1]})")
    return text, changes


def _split_review(text: str, filename: str) -> list[str]:
    out: list[str] = []
    for old, advice in SPLIT_TRADES.items():
        for line_no, line in enumerate(text.splitlines(), 1):
            if re.search(rf'(task/{old}/|trade\s*=\s*"{old}"|"{old}")', line):
                out.append(f"{filename}:{line_no} names {old!r}, which has no single "
                           f"successor: {advice}")
    return out


def migrate(house_dir: Path, *, write: bool = False) -> tuple[list[str], list[str]]:
    """``(what moved, what needs a person)``. Writes only when ``write`` is true."""
    from typehaus.schedule.inspection_state import (
        INSPECTIONS_FILENAME,
        migrate_entries,
        write_inspections,
    )
    from typehaus.takeoff.task_state import TASKS_FILENAME, load_tasks

    directory = Path(house_dir)
    changes: list[str] = []
    review: list[str] = []

    # Textual renames first, so the reload below sees the new tokens.
    for filename in (TASKS_FILENAME, INSPECTIONS_FILENAME):
        path = directory / filename
        if not path.exists():
            continue
        text = path.read_text()
        renamed, moved = _rename_tokens(text)
        changes.extend(f"{filename}: {line}" for line in moved)
        review.extend(_split_review(renamed, filename))
        if write and renamed != text:
            path.write_text(renamed)

    tasks = load_tasks(directory)
    for slug, entry in sorted(tasks.entries.items()):
        split = tasks.visits.for_package(slug)
        if not split or entry.status == "todo":
            continue
        statuses = {visit.derived_status for visit in split.values()}
        if statuses != {entry.status}:
            review.append(
                f"[entries.\"{slug}\"] says {entry.status!r} while its {len(split)} visit(s) "
                f"say {sorted(statuses)} — the split is the finer fact and only you know "
                "which arrival the package status was about")

    migrated, moved = migrate_entries(directory / INSPECTIONS_FILENAME)
    changes.extend(moved)
    if write and moved:
        write_inspections(directory, migrated)
    return changes, review
