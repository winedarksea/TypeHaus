"""``appendix/<kind>.md`` — one family's per-member data as tables, one column per member.

** 55 PER-MEMBER SHEETS WERE 192 OF A 307-PAGE PDF (2026-09-22). ** Each repeated its
kind's references, exclusions and table keys, and eleven of twelve cast columns added an
element tag and a few numbers to the first. The numbers are what an appendix is for, so
this prints them side by side: the inputs and limit states as rows, the members as
columns, and every per-member string (summary, citation, result, open input) once, with
the numbers that vary collapsed through :mod:`typehaus.takeoff.calc_collapse`.

The per-member nine-section sheets (:mod:`typehaus.takeoff.calc_sheet`) are still written
as diffable machine data; they stopped being printed. Every field they hold is here or on
the family calculation (fingerprints, oracle notes, assumptions).
"""

from __future__ import annotations

from collections.abc import Sequence

from typehaus.emit.md_writer import document, heading, table
from typehaus.engineering.item import EngineeringRecord, LimitState
from typehaus.takeoff.calc_collapse import collapse, collapsed_tables
from typehaus.takeoff.calc_family import family_filename, references

#: Members per value table. Five columns of "4,947 / 285,893 = 0.017" is what a 5.5"
#: measure holds beside the row labels without wrapping every cell.
MEMBERS_PER_TABLE = 4


def _tag(record: EngineeringRecord) -> str:
    return record.item_id.split("/", 1)[1]


def _chunks(records: Sequence[EngineeringRecord]) -> list[Sequence[EngineeringRecord]]:
    """Balanced groups of at most :data:`MEMBERS_PER_TABLE` — 5 is 3 + 2, never 4 + 1."""
    count = -(-len(records) // MEMBERS_PER_TABLE)
    size, extra = divmod(len(records), count)
    out, start = [], 0
    for i in range(count):
        end = start + size + (1 if i < extra else 0)
        out.append(records[start:end])
        start = end
    return out


def _ratio_basis(state: LimitState) -> str:
    if state.is_safety_factor:
        return "FS (required / achieved)"
    if state.is_detailing:
        return "detailing (required / provided)"
    return "demand / capacity"


def _given(records: Sequence[EngineeringRecord]) -> str:
    """Inputs as rows keyed by (name, unit, quantum), first-appearance order."""
    keys: list[tuple[str, str, str]] = []
    for record in records:
        for q in record.inputs:
            key = (q.name, q.unit, "exact" if q.quantum is None else f"{q.quantum:g}")
            if key not in keys:
                keys.append(key)
    if not keys:
        return "_No member consumed an input — this engine computes nothing here._"
    blocks = []
    for chunk in _chunks(records):
        values = [{(q.name, q.unit, "exact" if q.quantum is None else f"{q.quantum:g}"):
                   q.value for q in record.inputs} for record in chunk]
        rows = [[f"`{name}`", unit or "—", quantum,
                 *[by_key.get((name, unit, quantum), "—") for by_key in values]]
                for name, unit, quantum in keys
                if any((name, unit, quantum) in by_key for by_key in values)]
        blocks.append(table(["Quantity", "Unit", "Quantum",
                             *[f"`{_tag(r)}`" for r in chunk]], rows))
    return "\n\n".join(blocks)


def _state_key(state: LimitState) -> tuple[str, str, str]:
    return (state.name, state.unit, _ratio_basis(state))


def _states(records: Sequence[EngineeringRecord]) -> str:
    """``demand / capacity = ratio (R4)`` per member; the governing cell bold.

    ``R4`` is the citation's number in the family calculation's §2, so every member's own
    citation is recoverable without printing 400 characters of it in each column.
    """
    refs = references(records)
    keys: list[tuple[str, str, str]] = []
    for record in records:
        for state in record.limit_states:
            if _state_key(state) not in keys:
                keys.append(_state_key(state))
    if not keys:
        return "_No limit state is computed for any member._"
    blocks = []
    for chunk in _chunks(records):
        cells: list[dict[tuple[str, str, str], str]] = []
        for record in chunk:
            by_key = {}
            for state in record.limit_states:
                cite = (f" (R{refs.index(state.citation) + 1})"
                        if state.citation in refs else "")
                text = (f"{state.demand:,.4g} / {state.capacity:,.4g} "
                        f"= {state.ratio:.3f}{cite}")
                by_key[_state_key(state)] = (f"**{text}**" if state is record.governing
                                             else text)
            cells.append(by_key)
        rows = [[name, unit or "—", basis, *[by_key.get((name, unit, basis), "—")
                                              for by_key in cells]]
                for name, unit, basis in keys
                if any((name, unit, basis) in by_key for by_key in cells)]
        blocks.append(table(["Limit state", "Unit", "Ratio", *[f"`{_tag(r)}`" for r in chunk]],
                            rows))
    return "\n\n".join(blocks)


def render_appendix(kind: str, records: Sequence[EngineeringRecord], *,
                    house: str) -> str:
    """One family's per-member data. ``records`` share ``kind``, in item-id order."""
    assert records and all(record.kind == kind for record in records)
    summaries = collapse((record.item_id, record.summary) for record in records
                         if record.summary)
    return document(
        heading(f"{kind} — per-member data"),
        f"{len(records)} member(s) — `calcs/{family_filename(kind)}`, {house}.",
        heading("Scope, by member", 2),
        collapsed_tables(summaries, label="Summary", prefix="M") if summaries else
        "_The records carry no summary._",
        heading("Given", 2),
        _given(records),
        heading("Limit states", 2),
        _states(records),
    )
