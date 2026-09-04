"""One engineering item as a calculation sheet — the nine sections, in the usual order.

The order is not this repo's invention: header, scope, references, given, analysis, result,
assumptions, open inputs, independent check is the shape a US structural calculation has
arrived on a reviewer's desk in for decades, and a package that reorders it makes a
reviewer hunt for the one thing they always look at first.

**Every field printed here already exists on the record.** That is the property that keeps
the package regenerable rather than a document somebody maintains beside the model: this
module chooses a layout and a rounding, and invents no number, no citation and no
assumption. Where an input is genuinely absent the sheet prints the record's ``missing``
text verbatim, because "we do not know this yet, and here is exactly what it is" is a
better deliverable than a plausible figure.
"""

from __future__ import annotations

from collections.abc import Mapping

from typehaus.emit.md_writer import bullets, callout, document, heading, kv_block, table
from typehaus.engineering.fingerprint import Freshness, fingerprint
from typehaus.engineering.item import EngineeringRecord, Status
from typehaus.engineering.register import EngineeringRegister, Signoff

#: How each local status letters on a sheet. Deliberately the same four words the CLI uses
#: (``cli/cmd_engineering.py::_LOCAL``), so a reader moving between the terminal and the
#: package is not learning a second vocabulary.
STATUS_LABEL: Mapping[Status, str] = {
    Status.OK: "draft — this engine's calculation checks out",
    Status.OVER: "OVER — a limit state exceeds its capacity",
    Status.INCOMPLETE: "INCOMPLETE — the calculation exists and an input it needs is absent",
    Status.NO_CALC: "NO LOCAL CALC — a designer of record owns this",
}

SEAL_LABEL: Mapping[Freshness, str] = {
    Freshness.FRESH: "sealed, and the seal still matches this model",
    Freshness.STALE: "STALE — sealed once, and the model or the calculation has moved since",
    Freshness.UNPINNED: "stamped, not pinned — no fingerprint was recorded, so it can never "
                        "go stale and satisfies no gate",
    Freshness.UNSEALED: "unsealed",
}


def sheet_filename(item_id: str) -> str:
    """``retaining_wall/W-SG-E2`` -> ``retaining_wall__W-SG-E2.md``.

    A double underscore for the ``/`` so the item id is recoverable from the filename, and
    nothing else is rewritten: element tags are already filename-safe by the tag rules, and
    silently transliterating one would break the link back to the model.
    """
    return item_id.replace("/", "__") + ".md"


def _seal_line(record: EngineeringRecord,
               register: EngineeringRegister) -> tuple[str, Signoff | None]:
    state, signoff = register.freshness(record)
    label = SEAL_LABEL[state]
    if signoff is not None:
        label = f"{label} — {signoff.scope} ({signoff.credit()})"
    return label, signoff


def _references(record: EngineeringRecord) -> list[str]:
    """Every citation this record rests on, deduped, basis first.

    Deduped *in first-appearance order* rather than sorted: the limit states are already in
    the order the calculation reasoned about them, and alphabetising a reference list by
    "ACI" versus "IRC" would scatter one argument across the page.
    """
    seen: list[str] = []
    for text in ([record.basis] if record.basis else []) + \
            [state.citation for state in record.limit_states]:
        if text and text not in seen:
            seen.append(text)
    return seen


def _given(record: EngineeringRecord) -> str:
    if not record.inputs:
        return "_No inputs were consumed — this engine computes nothing for this item._"
    return table(
        ["Quantity", "Value", "Unit", "Fingerprint quantum"],
        [[q.name, q.value, q.unit, "exact" if q.quantum is None else q.quantum]
         for q in record.inputs])


def _analysis(record: EngineeringRecord) -> str:
    if not record.limit_states:
        return ("_No limit state is computed here._ What governs is named under "
                "**Result** and under **Open inputs** below.")
    governing = record.governing
    rows = []
    for state in record.limit_states:
        # A safety factor is stored as required/achieved so that every row of this table is
        # "over 1.0 is bad" — see ``LimitState``. The column headers say which convention a
        # row is in rather than letting a reader assume the wrong one.
        if state.is_safety_factor:
            kind = "FS (required / achieved)"
        elif state.is_detailing:
            kind = "detailing rule (required / provided)"
        else:
            kind = "demand / capacity"
        rows.append([
            ("**" + state.name + "**") if state is governing else state.name,
            state.demand, state.capacity, state.unit,
            f"{state.ratio:.3f}", kind, state.citation,
        ])
    body = table(["Limit state", "Demand", "Capacity", "Unit", "Ratio", "Basis of ratio",
                  "Citation"], rows)
    if governing is not None:
        body += ("\n\nThe **bold** row governs — it is the worst ratio among the states "
                 "that carry load, and the one an engineer would name if asked what "
                 "controls this item.")
    else:
        body += ("\n\n**No row is bold, because no load-carrying limit state could be "
                 "computed here.** Every row above is a detailing rule, and detailing "
                 "rules are graded against the section and the cage alone. What the "
                 "section can carry is unresolved — see **Open inputs**.")
    if any(state.is_detailing for state in record.limit_states):
        body += ("\n\nA row marked *detailing rule* reads 1.000 when the design sits "
                 "exactly on the code minimum, which is compliant. Such a row is graded "
                 "and would fail the item if it went over 1.0, but it is never named as "
                 "governing — a bar count at its minimum does not control a column.")
    return body


def _result(record: EngineeringRecord) -> str:
    governing = record.governing
    if governing is None:
        return f"**{STATUS_LABEL[record.status]}.** {record.summary}"
    verdict = "PASS" if governing.ok else "**OVER CAPACITY**"
    line = (f"**d/c = {governing.ratio:.2f}, governed by {governing.name} "
            f"({governing.citation}) — {verdict}.**")
    if record.status is Status.INCOMPLETE:
        line += ("\n\nThis ratio is **not the whole answer**: the item is INCOMPLETE, and "
                 "the limit states it could not reach are listed under **Open inputs**.")
    return line


def _independent_check(record: EngineeringRecord) -> str:
    """Who checked this arithmetic other than the code that produced it.

    The rule from the root ``CLAUDE.md`` — "a calc that only agrees with itself is not
    verified" — has an answer for every kind in this engine, and until now it was reachable
    only from a Python module docstring. A sheet with an empty section here is a sheet a
    reviewer should refuse.
    """
    if not record.oracle:
        return callout(
            "No independently hand-worked note is registered for this item's kind. Nothing "
            "below has been reproduced outside the code that produced it — treat every "
            "number on this sheet as unverified.",
            marker="**Unverified**")
    rows = [[oracle.note, oracle.section or "whole note", oracle.test or "—"]
            for oracle in record.oracle]
    return table(["Note (houses/<house>/notes/)", "Section", "Test that reproduces it"],
                 rows) + \
        "\n\nEach note is an independent hand pass, worked without reference to this " \
        "engine's code. Where a test is named, it re-derives the note's own numbers, so a " \
        "change to the calculation that drifts from the note fails the suite."


def render_sheet(record: EngineeringRecord, register: EngineeringRegister, *,
                 generated: str, house: str) -> str:
    """The whole sheet for one item."""
    seal, _signoff = _seal_line(record, register)
    print_fingerprint = (fingerprint(record) if record.status is not Status.NO_CALC
                         else "— (no inputs to fingerprint; a seal over this item can be "
                              "recorded but never pinned)")
    header = kv_block([
        ("Item", f"`{record.item_id}`"),
        ("Elements covered", ", ".join(record.element_tags) or record.key),
        ("Basis", record.basis or "—"),
        ("Basis version", record.basis_version),
        ("Local status", STATUS_LABEL[record.status]),
        ("Professional seal", seal),
        ("Fingerprint", f"`{print_fingerprint}`"),
        ("House", house),
        ("Generated", generated),
    ])
    blocks = [
        heading(record.item_id),
        header,
        heading("1. Scope", 2),
        record.summary or "_The record carries no summary._",
        heading("2. References", 2),
        bullets(_references(record)) or "_No citation is recorded._",
        heading("3. Given", 2),
        _given(record),
        heading("4. Analysis", 2),
        _analysis(record),
        heading("5. Result", 2),
        _result(record),
        heading("6. Assumptions and exclusions", 2),
        (bullets(record.notes) if record.notes else
         "_The record records no assumption beyond the citations above._"),
    ]
    if record.missing:
        blocks += [
            heading("7. Open inputs", 2),
            callout("\n\n".join(record.missing),
                    marker="**This item is not finished**"),
        ]
    else:
        blocks += [heading("7. Open inputs", 2), "_None — every input the calculation "
                   "needs was available in the model._"]
    blocks += [heading("8. Independent check", 2), _independent_check(record)]
    blocks += [heading("9. What this sheet does not cover", 2), _exclusions(record)]
    return document(*blocks)


def _exclusions(record: EngineeringRecord) -> str:
    """The standing boundary of every sheet in this package, in the item's own terms.

    Written once, here, rather than left implicit. A calculation package that does not say
    what it excludes invites a reviewer to assume it covered the thing it did not, and the
    two exclusions below are true of every record this engine produces: the limit states
    are the ones the calc module enumerated, and the seal is a separate act.
    """
    return bullets([
        f"Only the limit states listed in §4 are graded. A failure mode this engine does "
        f"not enumerate for `{record.kind}` is not evaluated here and is not implied to "
        f"pass.",
        "Load cases are those the record's inputs state. No combination beyond them is "
        "searched.",
        "This engine computing a PASS is the **draft** gate. It is not a professional "
        "seal, and it does not become one by being printed.",
    ])
