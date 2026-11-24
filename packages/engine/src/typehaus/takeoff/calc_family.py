"""One calculation per design family, with a member schedule — the sheet a reviewer reads.

** SIXTY-FIVE SHEETS, EACH REPEATING THE SAME REFERENCES AND THE SAME EXCLUSIONS. ** That
is what finding 8 of the 2026-09-18 gap review meant by a package nobody can review: twelve
`deck_post` items produced twelve nine-section sheets, and eleven of them added nothing to
the first but an element tag and four numbers. A reviewer checking a cast column does not
want twelve copies of ACI 318-19 §22.4.2.1; they want the clause once, the arithmetic once,
and a **schedule** saying which member is which and which one governs.

So the package now leads with one of these per ``kind``: the family's shared basis and
references printed once, a member schedule, the calculation worked term by term at the
governing member with its substitutions and units beside it, and the family's exclusions
said once instead of sixty-five times. The per-item sheets keep every field they had and
move to ``appendix/`` — nothing is lost, and the machine data stops being the document.

**Said once, not once per family** (2026-09-22): the standing exclusions, the ratio
conventions and the "bold row governs" key repeated 52-55 times in a 307-page PDF. They
live in :func:`render_conventions` (``06-conventions.md``) and a family sheet points there.

**It invents nothing.** Every number, citation and assumption here is read off the same
``EngineeringRecord`` the per-item sheet reads; this module chooses a grouping.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from typehaus.emit.md_writer import bullets, callout, document, heading, table
from typehaus.engineering.deferred import DEFERRALS
from typehaus.engineering.fingerprint import fingerprint, pinnable
from typehaus.engineering.item import (
    EngineeringRecord,
    NotCovered,
    StatedBasis,
    Status,
    sheet_spec,
)
from typehaus.engineering.register import EngineeringRegister
from typehaus.takeoff.calc_collapse import (
    Collapsed,
    RefIndex,
    collapse,
    reference_index,
    values_line,
)
from typehaus.takeoff.calc_numfmt import num, ratio_text
from typehaus.takeoff.calc_sheet import SCOPE_LABEL, SEAL_LABEL, STATE_NAME
from typehaus.takeoff.calc_worked import render_worked

#: Worst first, so a family's verdict is the first row of its own schedule.
_STATUS_RANK: Mapping[Status, int] = {
    Status.OVER: 0, Status.INCOMPLETE: 1, Status.NO_CALC: 2, Status.OK: 3,
}


#: The one page the hoisted boilerplate lives on; front matter, printed just before S-2.
CONVENTIONS_FILE = "06-conventions.md"

#: Where every record's assumptions are printed, grouped by kind and collapsed.
ASSUMPTIONS_FILE = "04-assumptions.md"


def appendix_filename(kind: str) -> str:
    """``deck_post`` -> ``appendix/deck_post.md``: the family's per-member data table."""
    return f"appendix/{kind}.md"


def family_filename(kind: str) -> str:
    """``deck_post`` -> ``deck_post.md``. The kind IS the family, and it is filename-safe."""
    return f"{kind}.md"


def families(records: Sequence[EngineeringRecord]) -> dict[str, list[EngineeringRecord]]:
    """``kind -> its records``, each family in item-id order, the families sorted."""
    grouped: dict[str, list[EngineeringRecord]] = {}
    for record in records:
        grouped.setdefault(record.kind, []).append(record)
    return {kind: sorted(grouped[kind], key=lambda r: r.item_id)
            for kind in sorted(grouped)}


def _member_key(record: EngineeringRecord) -> tuple[int, float, str]:
    governing = record.governing
    return (_STATUS_RANK.get(record.status, 4),
            -(governing.ratio if governing is not None else 0.0), record.item_id)


def governing_member(records: Sequence[EngineeringRecord]) -> EngineeringRecord:
    """The member a reviewer would open first: worst status, then worst ratio.

    Not simply the worst ratio. An INCOMPLETE member has no ratio to lose with and is a
    bigger fact about the family than an OK member at 0.98; and a NO_CALC member has no
    arithmetic at all. Status orders first for the same reason the CLI does.
    """
    return min(records, key=_member_key)


def _deduped(values: Sequence[str]) -> list[str]:
    """First-appearance order, not sorted — an argument scattered alphabetically is lost."""
    seen: list[str] = []
    for text in values:
        if text and text not in seen:
            seen.append(text)
    return seen


def references(records: Sequence[EngineeringRecord]) -> list[str]:
    """Every citation the family rests on, deduped in first-appearance order."""
    return _deduped([record.basis for record in records]
                    + [state.citation for record in records
                       for state in record.limit_states])


def reference_entries(records: Sequence[EngineeringRecord]) -> list[tuple[str, str]]:
    """``(member, citation)`` in reasoning order, basis first — what :func:`ref_index` reads."""
    return ([(r.key, r.basis) for r in records if r.basis]
            + [(f"{r.key}: {s.name}", s.citation) for r in records for s in r.limit_states
               if s.citation])


def ref_index(records: Sequence[EngineeringRecord]) -> RefIndex:
    """The family's references with near-duplicates collapsed (review E-11)."""
    return reference_index(reference_entries(records))


def _references_block(refs: RefIndex) -> str:
    if not refs.rows:
        return "_No citation is recorded._"
    blocks = [bullets(f"**R{n}** — {row.template}" for n, row in enumerate(refs.rows, 1))]
    for n, row in enumerate(refs.rows, start=1):
        if row.values:
            blocks.append(f"**R{n}**, the values in [ ] by member:\n\n" + table(
                ["Member: limit state", "Values"], [[m, values_line(tokens)]
                                       for m, tokens in row.values]))
    return "\n\n".join(blocks)


#: A factor of safety has no unit; say what the two columns are instead of leaving a blank.
_FS_UNIT = "FS (required / achieved)"


def _first_word(text: str) -> str:
    return text.split(" — ")[0]


def _uniform(values: Sequence[str]) -> str | None:
    return values[0] if len(set(values)) == 1 else None


def _schedule(records: Sequence[EngineeringRecord], register: EngineeringRegister,
              refs: RefIndex) -> str:
    """One row per member and what governs it. Status, coverage and seal print here only
    when they differ between members; otherwise once, in the header (review 6A-3c)."""
    worst = governing_member(records)
    status = [STATE_NAME[r.status] for r in records]
    coverage = [_first_word(SCOPE_LABEL[r.scope]) for r in records]
    seal = [_first_word(SEAL_LABEL[register.freshness(r)[0]]) for r in records]
    extra = [(name, col) for name, col in (("Status", status), ("Coverage", coverage),
                                           ("Seal", seal)) if _uniform(col) is None]
    rows = []
    for i, record in enumerate(records):
        governing = record.governing
        if governing is None:
            demand = capacity = unit = ratio = "—"
            state = "no load-carrying state computed"
        else:
            demand, capacity = num(governing.demand), num(governing.capacity)
            unit = _FS_UNIT if governing.is_safety_factor else governing.unit or "—"
            ratio = ratio_text(governing.ratio)
            state = f"{governing.name} ({refs.cite(governing.citation)})"
        tag = f"`{record.key}`"
        rows.append([f"**{tag}**" if record is worst and len(records) > 1 else tag,
                     ", ".join(t for t in record.element_tags if t != record.key) or "—",
                     state, demand, capacity, unit, ratio, *[col[i] for _n, col in extra]])
    return table(["Member", "With", "Governing limit state", "Demand", "Capacity",
                  "Unit", "d/c", *[n for n, _c in extra]], rows) + (
        f"\n\nPer-member data: `{appendix_filename(records[0].kind)}`.")


def _verdict(records: Sequence[EngineeringRecord], refs: RefIndex) -> str:
    counts: dict[Status, int] = {}
    for record in records:
        counts[record.status] = counts.get(record.status, 0) + 1
    parts = [f"{counts[status]} {STATE_NAME[status].lower()}"
             for status in sorted(counts, key=lambda s: _STATUS_RANK.get(s, 4))]
    worst = governing_member(records)
    governing = worst.governing
    line = f"**{len(records)} member(s): " + ", ".join(parts) + ".**"
    if governing is not None:
        verdict = "PASS" if governing.ok else "**OVER CAPACITY**"
        line += (f"\n\nThe family is governed by `{worst.item_id}` at d/c "
                 f"{ratio_text(governing.ratio)} on {governing.name} "
                 f"({refs.cite(governing.citation)}) — {verdict}. The limit is 1.000.")
    else:
        line += f"\n\n`{worst.item_id}` leads it; no load-bearing state — see §8."
    return line


def _open_inputs(records: Sequence[EngineeringRecord]) -> str:
    rows = [[f"`{record.item_id}`", "\n\n".join(record.missing)]
            for record in records if record.missing]
    deferral = DEFERRALS.get(records[0].kind)
    if deferral is not None:
        rows.append([", ".join(f"`{r.item_id}`" for r in records),
                     f"{deferral.deliverable} — from {deferral.designer}"])
    if not rows:
        return "_None._"
    return callout(
        table(["Member", "What is missing"], rows),
        marker=f"**{len(rows)} open input(s)**")


def _oracle(records: Sequence[EngineeringRecord]) -> str:
    """The notes only: the tests that re-derive them are not in the bundle (review E-17)."""
    rows = []
    for record in records:
        for oracle in record.oracle:
            row = [oracle.note, oracle.section or "whole note"]
            if row not in rows:
                rows.append(row)
    if not rows:
        return callout(
            "No independently hand-worked note is registered for this family. Nothing "
            "below has been reproduced outside the code that produced it — treat every "
            "number in this calculation as unverified.",
            marker="**Unverified**")
    return table(["Note (in `notes/`)", "Section"], rows)


def _coverage(records: Sequence[EngineeringRecord]) -> str:
    """The family's one coverage word, or ``mixed`` — the header prints it."""
    scopes = sorted({_first_word(SCOPE_LABEL[record.scope]) for record in records})
    return scopes[0] if len(scopes) == 1 else "mixed (see the schedule)"


#: How a record's note marks something it deliberately does not grade.
_NOT_GRADED = re.compile(r"not graded|not checked|\bscreening\b", re.IGNORECASE)


def not_covered(records: Sequence[EngineeringRecord]) -> list[NotCovered]:
    """The kind's declared rows, the members' own, and a deferral's — deduped, in order."""
    kind = records[0].kind
    rows = list(sheet_spec(kind).not_covered)
    rows += [row for record in records for row in record.not_covered]
    deferral = DEFERRALS.get(kind)
    if deferral is not None:
        rows.append(NotCovered(f"the whole design of `{kind}`", _clause(deferral.reason),
                               deferral.designer, deferral.deliverable))
    out: list[NotCovered] = []
    for row in rows:
        if row not in out:
            out.append(row)
    return out


def _clause(text: str, limit: int = 160) -> str:
    """The first sentence of a long reason, cut at a word."""
    first = re.split(r"(?<=[.;])\s", text, maxsplit=1)[0]
    return first if len(first) <= limit else first[:limit].rsplit(" ", 1)[0] + " …"


def stated_bases(records: Sequence[EngineeringRecord]) -> list[StatedBasis]:
    rows = list(sheet_spec(records[0].kind).bases)
    rows += [b for record in records for b in record.bases]
    out: list[StatedBasis] = []
    for row in rows:
        if row not in out:
            out.append(row)
    return out


def _bases(records: Sequence[EngineeringRecord]) -> str:
    rows = stated_bases(records)
    if not rows:
        return "_None: every input is a code or catalog row, a model dimension or authored._"
    return table(["Subject", "Kind", "Statement", "Reopens if / leaves out", "Recorded in"],
                 [[b.subject, b.kind.value, b.statement, b.reopens_if or "—",
                   b.reference or "—"] for b in rows])


def _exclusions(records: Sequence[EngineeringRecord],
                assumptions: Sequence[Collapsed] = ()) -> str:
    """The family's not-covered table (review E-01); the standing exclusions are in
    :data:`CONVENTIONS_FILE`."""
    lines = [f"**{_coverage(records)}**: §4's states only; the rest is in "
             f"`{CONVENTIONS_FILE}`."]
    rows = not_covered(records)
    if rows:
        lines.append(table(["Not graded here", "Why", "Owner", "Closes by"],
                           [[r.what, r.why, r.owner, r.closes_by or "—"] for r in rows]))
    else:
        lines.append("_Not yet itemised for this family._ Owner: the sealing engineer.")
    flagged = [str(n) for n, row in enumerate(assumptions, start=1)
               if _NOT_GRADED.search(row.template)]
    if flagged:
        lines.append(f"Also by name: `{ASSUMPTIONS_FILE}` rows {', '.join(flagged)}.")
    return "\n\n".join(lines)


def _ordered(records: Sequence[EngineeringRecord]) -> list[EngineeringRecord]:
    return sorted(records, key=_member_key)


def _header(kind: str, records: Sequence[EngineeringRecord], register: EngineeringRegister,
            design_method: str, generated: str, house: str) -> str:
    """One two-column table instead of nine stacked paragraphs (review E-17)."""
    worst = governing_member(records)
    bases = _deduped([record.basis for record in records])
    versions = _deduped([record.basis_version for record in records])
    status = _uniform([STATE_NAME[r.status] for r in records])
    seal = _uniform([_first_word(SEAL_LABEL[register.freshness(r)[0]]) for r in records])
    rows = [["Members", str(len(records))],
            ["Basis", "; ".join(bases) or "—"],
            ["Design method", design_method or "not declared"],
            ["Coverage", _coverage(records)],
            *([["Status", status]] if status else []),
            *([["Seal", seal]] if seal else []),
            ["Governed by", f"`{worst.item_id}`"],
            ["Basis version", ", ".join(versions)],
            ["House / generated", f"{house}, {generated}"]]
    return table(["Design family", f"`{kind}`"], rows)


def render_family(kind: str, records: Sequence[EngineeringRecord],
                  register: EngineeringRegister, *, generated: str, house: str,
                  design_method: str = "") -> str:
    """One design family as one calculation. ``records`` must all share ``kind``."""
    assert records and all(record.kind == kind for record in records)
    worst = governing_member(records)
    refs = ref_index(records)
    summaries = _deduped([record.summary for record in records])
    scope = (summaries[0] if len(summaries) == 1
             else f"{worst.summary}\n\nThe other members' summaries: "
                  f"`{appendix_filename(kind)}`.")
    assumptions = collapse((record.item_id, note) for record in records
                           for note in record.notes)
    assumption_pointer = (
        f"`{ASSUMPTIONS_FILE}`, under `{kind}` — {len(assumptions)} distinct."
        if assumptions else "_None beyond the citations above._")
    return document(
        heading(f"{kind} — {len(records)} member(s)"),
        _header(kind, records, register, design_method, generated, house),
        heading("1. Scope", 2),
        scope or "_The records carry no summary._",
        heading("2. References", 2),
        _references_block(refs),
        heading("3. Member schedule", 2),
        _schedule(records, register, refs),
        heading("4. The calculation, worked at the governing member", 2),
        render_worked(records, _ordered(records), refs),
        heading("5. Result", 2),
        _verdict(records, refs),
        heading("6. Stated bases and owner acceptances", 2),
        _bases(records),
        heading("7. Assumptions", 2),
        assumption_pointer,
        heading("8. Open inputs", 2),
        _open_inputs(records),
        heading("9. Independent check", 2),
        _oracle(records),
        heading("10. What this calculation does not cover", 2),
        _exclusions(records, assumptions),
        _fingerprints(records),
    )


def _fingerprints(records: Sequence[EngineeringRecord]) -> str:
    """One line for the seal form; the full column is in the appendix sheets."""
    parts = [f"`{r.key}` `{fingerprint(r)}`" for r in records if pinnable(r)]
    if not parts:
        return "_Not pinned to the model; the seal form records the designer's document._"
    return "_Fingerprints for the seal form:_ " + ", ".join(parts) + "."


def render_conventions(*, house: str) -> str:
    """How every family calculation reads, and what none of them covers — said once."""
    return document(
        heading(f"Reading the calculations — {house}"),
        "Each calculation that follows is one design family: the family's references "
        "once, a member schedule, the arithmetic worked at the governing member, and the "
        "family's assumptions. Everything on this page holds for every one of them and is "
        "not repeated on each.",
        heading("Layout", 2),
        bullets([
            "**The governing member** is picked by status first and ratio second: an "
            "incomplete member has no ratio to lose with and is a bigger fact about the "
            "family than a computed member at 0.98.",
            "**Section 4 shows the working.** Each symbol is named in plain words, each "
            "limit state lists its steps as equation = numbers = result with the clause or "
            "table row, and the load combination is named beside it. Where the members of "
            "one family run different limit states, each such calculation is worked once.",
            "**Every other member** in a schedule is the same calculation at its own "
            "dimensions. Its own inputs and limit states are in the family's appendix "
            "table, `appendix/<kind>.md`, one column per member.",
            "**A schedule is the whole family.** A member not in it was not analysed; it "
            "is not a member that passed.",
            "**Stated bases** (section 6) are inputs that rest on an owner's decision or a "
            "specified value rather than a code row or a measurement.",
            "**Assumptions** that differ only in their numbers are printed once, with the "
            "numbers that vary as [1], [2] … and a table of what each member put there. "
            "References are collapsed the same way.",
        ]),
        heading("Reading a limit-state table", 2),
        bullets([
            "The **bold** row governs: the worst ratio among the states that carry load, "
            "and the one an engineer would name if asked what controls the member.",
            "A ratio is `demand / capacity`, or `required / achieved` for a factor of "
            "safety, so that over 1.000 is always over capacity.",
            "0.85 is the owner's cost-review trigger, not an acceptance limit. The limit "
            "is 1.000.",
            "A _detailing_ row (`required / provided`) reads 1.000 when the design sits on "
            "the code minimum, which is compliant. It is graded and would fail the member "
            "over 1.0, but it is never named as governing.",
        ]),
        heading("What no calculation here covers", 2),
        bullets([
            "**Coverage.** Each calculation's header says SCREENING, COMPLETE or EXTERNAL. "
            "SCREENING means only the limit states in its section 4 are graded; its "
            "section 10 lists what is not, and who owns it. Nothing else is implied to "
            "pass.",
            "Load cases are those the records' inputs state. No combination beyond them "
            "is searched.",
            "A computed PASS is the **draft** gate. It is not a professional seal, and it "
            "does not become one by being printed.",
        ]),
        heading("Independent checks", 2),
        "Each note a calculation's section 9 names is a hand pass, worked by hand from the "
        "drawings and the published sources. A note cites the program's code only to name "
        "what it oracles; its arithmetic does not come from the code. A test re-derives the "
        "note's numbers, so a calculation drifting from its note is caught.",
    )
