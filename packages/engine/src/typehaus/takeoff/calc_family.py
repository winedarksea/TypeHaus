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

from collections.abc import Mapping, Sequence

from typehaus.emit.md_writer import bullets, callout, document, heading, kv_block, table
from typehaus.engineering.fingerprint import fingerprint
from typehaus.engineering.item import EngineeringRecord, Status
from typehaus.engineering.register import EngineeringRegister
from typehaus.takeoff.calc_collapse import collapse
from typehaus.takeoff.calc_sheet import (
    SCOPE_LABEL,
    SEAL_LABEL,
    STATUS_LABEL,
)

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


def governing_member(records: Sequence[EngineeringRecord]) -> EngineeringRecord:
    """The member a reviewer would open first: worst status, then worst ratio.

    Not simply the worst ratio. An INCOMPLETE member has no ratio to lose with and is a
    bigger fact about the family than an OK member at 0.98; and a NO_CALC member has no
    arithmetic at all. Status orders first for the same reason the CLI does.
    """
    def key(record: EngineeringRecord) -> tuple[int, float, str]:
        governing = record.governing
        return (_STATUS_RANK.get(record.status, 4),
                -(governing.ratio if governing is not None else 0.0),
                record.item_id)
    return min(records, key=key)


def _deduped(values: Sequence[str]) -> list[str]:
    """First-appearance order, not sorted — an argument scattered alphabetically is lost."""
    seen: list[str] = []
    for text in values:
        if text and text not in seen:
            seen.append(text)
    return seen


def references(records: Sequence[EngineeringRecord]) -> list[str]:
    """Every citation the family rests on, deduped in first-appearance order.

    Numbered R1, R2 … on the sheet and cited by number from the appendix's limit-state
    tables, which is how a per-member state keeps its citation without printing 400
    characters of it in every column.
    """
    return _deduped([record.basis for record in records]
                    + [state.citation for record in records
                       for state in record.limit_states])


def _schedule(records: Sequence[EngineeringRecord],
              register: EngineeringRegister) -> str:
    """The table that replaces the repetition: one row per member, and what governs it."""
    rows = []
    for record in records:
        governing = record.governing
        freshness, _signoff = register.freshness(record)
        if governing is None:
            demand = capacity = unit = ratio = "—"
            state = "no load-carrying state computed"
        else:
            demand = f"{governing.demand:,.1f}"
            capacity = f"{governing.capacity:,.1f}"
            unit = governing.unit
            ratio = f"{governing.ratio:.2f}"
            state = governing.name
        rows.append([
            f"`{record.item_id.split('/', 1)[1]}`",
            ", ".join(record.element_tags) or record.key,
            state, demand, capacity, unit, ratio,
            STATUS_LABEL[record.status].split(" — ")[0],
            SCOPE_LABEL[record.scope].split(" — ")[0],
            SEAL_LABEL[freshness].split(" — ")[0],
        ])
    kind = records[0].kind
    return table(["Member", "Elements", "Governing limit state", "Demand", "Capacity",
                  "Unit", "d/c", "Status", "Coverage", "Seal"], rows) + (
        f"\n\nPer-member data: `{appendix_filename(kind)}`.")


def _worked(record: EngineeringRecord) -> str:
    """The governing member's arithmetic, with the substitutions and units beside it.

    ** THE SUBSTITUTIONS ARE THE POINT. ** A limit-state row saying "9,461 / 7,150 = 1.32"
    is checkable only by somebody who already knows what went into the 9,461. The inputs
    are printed as ``name = value unit`` immediately above the states that consumed them,
    which is how a hand calculation is laid out and why a hand calculation can be marked up.
    """
    blocks = [f"Worked at **`{record.item_id}`**, the member the verdict comes from."]
    if record.inputs:
        blocks.append(table(
            ["Symbol", "Value", "Unit"],
            [[f"`{q.name}`", f"{q.value:,.4g}", q.unit or "—"] for q in record.inputs]))
    else:
        blocks.append("_This member consumed no input — the engine computes nothing here._")

    if not record.limit_states:
        blocks.append("_No limit state is computed. What governs is named under "
                      "**Result**._")
        return "\n\n".join(blocks)

    rows = []
    for state in record.limit_states:
        if state.is_safety_factor:
            form = f"{state.demand:,.4g} required / {state.capacity:,.4g} achieved"
        elif state.is_detailing:
            form = f"{state.demand:,.4g} required / {state.capacity:,.4g} provided"
        else:
            form = f"{state.demand:,.4g} demand / {state.capacity:,.4g} capacity"
        name = f"**{state.name}**" if state is record.governing else state.name
        rows.append([name, f"{form} {state.unit}".strip(), f"{state.ratio:.3f}",
                     state.combination or "—", state.citation])
    blocks.append(table(["Limit state", "Substitution", "= d/c", "Load combination",
                         "Citation"], rows))
    return "\n\n".join(blocks)


def _verdict(records: Sequence[EngineeringRecord]) -> str:
    counts: dict[Status, int] = {}
    for record in records:
        counts[record.status] = counts.get(record.status, 0) + 1
    parts = [f"{counts[status]} {STATUS_LABEL[status].split(' — ')[0]}"
             for status in sorted(counts, key=lambda s: _STATUS_RANK.get(s, 4))]
    worst = governing_member(records)
    governing = worst.governing
    line = f"**{len(records)} member(s): " + ", ".join(parts) + ".**"
    if governing is not None:
        verdict = "PASS" if governing.ok else "**OVER CAPACITY**"
        line += (f"\n\nThe family is governed by `{worst.item_id}` at d/c "
                 f"{governing.ratio:.2f} on {governing.name} "
                 f"({governing.citation}) — {verdict}.")
    else:
        line += f"\n\n`{worst.item_id}` leads it; no load-bearing state — see §7."
    return line


def _open_inputs(records: Sequence[EngineeringRecord]) -> str:
    rows = [[f"`{record.item_id}`", "\n\n".join(record.missing)]
            for record in records if record.missing]
    if not rows:
        return "_None._"
    return callout(
        table(["Member", "What is missing"], rows),
        marker=f"**{len(rows)} of {len(records)} members are not finished**")


def _oracle(records: Sequence[EngineeringRecord]) -> str:
    oracles = _deduped([str(oracle) for record in records for oracle in record.oracle])
    if not oracles:
        return callout(
            "No independently hand-worked note is registered for this family. Nothing "
            "below has been reproduced outside the code that produced it — treat every "
            "number in this calculation as unverified.",
            marker="**Unverified**")
    rows = []
    for record in records:
        for oracle in record.oracle:
            row = [oracle.note, oracle.section or "whole note", oracle.test or "—"]
            if row not in rows:
                rows.append(row)
    return table(["Note (houses/<house>/notes/)", "Section", "Test that reproduces it"],
                 rows)


def _coverage(records: Sequence[EngineeringRecord]) -> str:
    """The family's one coverage word, or ``mixed`` — the header prints it, §9 points on."""
    scopes = sorted({SCOPE_LABEL[record.scope].split(" — ")[0] for record in records})
    return scopes[0] if len(scopes) == 1 else "mixed (see the schedule)"


def _exclusions(records: Sequence[EngineeringRecord]) -> str:
    """One line. The standing exclusions are said once, in :data:`CONVENTIONS_FILE`."""
    return f"**{_coverage(records)}** — §4's states only; see `{CONVENTIONS_FILE}`."


def render_family(kind: str, records: Sequence[EngineeringRecord],
                  register: EngineeringRegister, *, generated: str, house: str,
                  design_method: str = "") -> str:
    """One design family as one calculation. ``records`` must all share ``kind``."""
    assert records and all(record.kind == kind for record in records)
    worst = governing_member(records)
    bases = _deduped([record.basis for record in records])
    versions = _deduped([record.basis_version for record in records])
    header = kv_block([
        ("Design family", f"`{kind}`"),
        ("Members", str(len(records))),
        ("Basis", bases[0] if len(bases) == 1 else
         "; ".join(bases) or "—"),
        ("Basis version", ", ".join(versions)),
        ("Design method", design_method or "not declared"),
        ("Coverage", _coverage(records)),
        ("Governed by", f"`{worst.item_id}`"),
        ("House", house),
        ("Generated", generated),
    ])
    summaries = _deduped([record.summary for record in records])
    scope = (summaries[0] if len(summaries) == 1
             else f"{worst.summary}\n\nThe other members' summaries: "
                  f"`{appendix_filename(kind)}`.")
    assumptions = collapse((record.item_id, note) for record in records
                           for note in record.notes)
    # Said once, on the assumptions page, rather than here AND there: the same rows under
    # the same heading were 20 pages of a 108-page PDF.
    assumption_pointer = (
        f"`{ASSUMPTIONS_FILE}`, under `{kind}` — {len(assumptions)} distinct."
        if assumptions else "_None beyond the citations above._")
    return document(
        heading(f"{kind} — {len(records)} member(s)"),
        header,
        heading("1. Scope", 2),
        scope or "_The records carry no summary._",
        heading("2. References", 2),
        bullets(f"**R{n}** — {text}" for n, text in enumerate(references(records), start=1))
        or "_No citation is recorded._",
        heading("3. Member schedule", 2),
        _schedule(records, register),
        heading("4. The calculation, worked at the governing member", 2),
        _worked(worst),
        heading("5. Result", 2),
        _verdict(records),
        heading("6. Assumptions and exclusions", 2),
        assumption_pointer,
        heading("7. Open inputs", 2),
        _open_inputs(records),
        heading("8. Independent check", 2),
        _oracle(records),
        heading("9. What this calculation does not cover", 2),
        _exclusions(records),
        heading("10. Per-member fingerprints", 2),
        _fingerprints(records),
    )


def _fingerprints(records: Sequence[EngineeringRecord]) -> str:
    """What a seal on any one member would be pinned against — the machine half, last.

    On the family sheet rather than only in the appendix because a seal is applied per
    item, so a reviewer sealing this family needs the whole column in one place.
    """
    rows = []
    for record in records:
        value = (f"`{fingerprint(record)}`" if record.status is not Status.NO_CALC
                 else "— (no inputs to fingerprint; a seal can be recorded, never pinned)")
        rows.append([f"`{record.item_id}`", record.basis_version, value])
    return table(["Member", "Basis version", "Fingerprint"], rows)


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
            "INCOMPLETE member has no ratio to lose with and is a bigger fact about the "
            "family than an OK member at 0.98.",
            "**Every other member** in a schedule is the same calculation at its own "
            "dimensions. Its own inputs and limit states are in the family's appendix "
            "table, `appendix/<kind>.md`, one column per member; each member's full "
            "nine-section sheet is written beside it as `appendix/<kind>__<tag>.md`, "
            "machine data that is not printed.",
            "**A schedule is the whole family.** A member not in it is a member this "
            "engine does not know about, not a member that passed.",
            "**Assumptions** that differ only in their numbers are printed once, with the "
            "numbers that vary as [1], [2] … and a table of what each member put there. "
            "Nothing is dropped.",
        ]),
        heading("Reading a limit-state table", 2),
        bullets([
            "The **bold** row governs: the worst ratio among the states that carry load, "
            "and the one an engineer would name if asked what controls the member.",
            "A ratio is `demand / capacity`, or `required / achieved` for a factor of "
            "safety, so that over 1.0 is always bad.",
            "A _detailing_ row (`required / provided`) reads 1.000 when the design sits on "
            "the code minimum, which is compliant. It is graded and would fail the member "
            "over 1.0, but it is never named as governing.",
        ]),
        heading("What no calculation here covers", 2),
        bullets([
            "**Coverage.** Each calculation's header says SCREENING, COMPLETE or EXTERNAL. "
            "SCREENING means only the limit states in its §4 are graded: a failure mode "
            "this engine does not enumerate for that kind is not evaluated and is not "
            "implied to pass.",
            "Load cases are those the records' inputs state. No combination beyond them "
            "is searched.",
            "This engine computing a PASS is the **draft** gate. It is not a professional "
            "seal, and it does not become one by being printed.",
        ]),
        heading("Independent checks", 2),
        "Each note a calculation's §8 names is an independent hand pass, worked without "
        "reference to this engine's code. Where a test is named it re-derives the note's "
        "own numbers, so a change to the calculation that drifts from the note fails the "
        "suite.",
    )
