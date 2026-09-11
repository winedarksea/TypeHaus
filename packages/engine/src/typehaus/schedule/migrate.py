"""``haus site migrate`` — the old spellings folded into the current ones, in place.

Three jobs, and each of them refuses to invent.

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

Nothing here promotes ``done`` to ``verified``. ``verified`` is the owner's own walk and no
migration can have done it for them.
"""

from __future__ import annotations

from pathlib import Path


def migrate(house_dir: Path, *, write: bool = False) -> tuple[list[str], list[str]]:
    """``(what moved, what needs a person)``. Writes only when ``write`` is true."""
    from typehaus.schedule.inspection_state import (
        INSPECTIONS_FILENAME,
        migrate_entries,
        write_inspections,
    )
    from typehaus.takeoff.task_state import load_tasks

    directory = Path(house_dir)
    changes: list[str] = []
    review: list[str] = []

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
