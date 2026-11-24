"""``out/calcs/`` — the calculation package you hand a professional engineer.

The register already holds everything a reviewer needs: inputs with units, limit states
with demand, capacity, ratio and citation, assumptions as free text, a basis version and a
fingerprint. What did not exist was **the artefact** — the register renders as a rich
console table, a JSON blob, or one summary sheet in the drawing set, and none of those is a
document somebody marks up and sends back.

This module is pure data in, ``{relative path: markdown}`` out. No file I/O at all, which
is what makes the whole package testable without a temp directory, and what lets
``haus calcs --out`` write it anywhere. ``cli/cmd_calcs.py`` is the only thing that touches
a disk.

**The criteria page is derived, never typed.** Wind comes through :mod:`typehaus.wind`,
soil through :mod:`typehaus.engineering.soil`, and everything else off the records
themselves. A design-criteria sheet that can drift from the calculations it fronts is worse
than none: it is the page a reviewer trusts to place every number behind it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from typehaus.emit.md_writer import bullets, callout, document, heading, kv_block, table
from typehaus.engineering.item import EngineeringRecord, Status
from typehaus.engineering.register import EngineeringRegister
from typehaus.takeoff.calc_appendix import render_appendix
from typehaus.takeoff.calc_collapse import collapse, collapsed_tables
from typehaus.takeoff.calc_criteria import _criteria, design_method
from typehaus.takeoff.calc_family import (
    CONVENTIONS_FILE,
    appendix_filename,
    families,
    family_filename,
    render_conventions,
    render_family,
)
from typehaus.takeoff.calc_register import open_items_page, register_page, scope_page
from typehaus.takeoff.calc_sheet import render_sheet, sheet_filename
from typehaus.takeoff.calc_summary import (
    STATE_NAME,
    parse_previous,
    render_summary,
    state_line,
)

#: Printed on the cover, and meant to be read. A draft package is a working document; a set
#: that leaves this repo without saying so can be mistaken for one somebody sealed.
NOT_FOR_CONSTRUCTION = (
    "NOT FOR CONSTRUCTION. This package is generated from a model by Type:Haus. Every "
    "result in it is a **draft** calculation: first-principles arithmetic, checked against an "
    "independently hand-worked note, and it is not a professional engineer's seal. Nothing "
    "here may be built from until a licensed engineer has reviewed it and stamped the items "
    "on the register."
)


@dataclass(frozen=True)
class PackageInputs:
    """Everything the package is generated from — nothing is read from disk.

    ``item_ids`` is passed in rather than enumerated here on purpose: which requirements in
    a house are outside the prescriptive path is a conclusion the *checks* reach (7 feet of
    unbalanced fill here, 3 feet next door), and a second enumeration living in the emitter
    would be that judgement written twice, free to drift. ``cli/cmd_engineering.py::_load``
    is the one place that decides it.
    """

    house: str
    model: object
    item_ids: tuple[str, ...]
    results: Mapping[str, EngineeringRecord]
    register: EngineeringRegister
    generated: str
    engine_version: str = ""
    content_hash: str = ""
    profile_name: str = ""
    #: The permit gate as it stands, when the caller ran it. ``None`` is honest — the cover
    #: then says the gate was not evaluated rather than implying it opened.
    checklist: object = None
    notes_dir: str = "notes/"
    model_revision: str = ""
    records: tuple[EngineeringRecord, ...] = field(default_factory=tuple)
    #: The ``JurisdictionProfile`` (code and loads editions, seismic category) and the house's
    #: ``Preferences`` (the deck snow input). Either may be ``None``; the pages then omit them.
    profile: object = None
    preferences: object = None
    #: An earlier package's ``00-cover.md`` and ``02-item-register.md`` for "what changed"
    #: (:func:`typehaus.takeoff.calc_summary.read_previous`); ``None`` reads "first issue".
    previous: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        if not self.records:
            object.__setattr__(self, "records",
                               tuple(self.results[key] for key in self.item_ids))


def calc_package(inputs: PackageInputs, *, only: str | None = None) -> dict[str, str]:
    """The whole package: ``{relative path: markdown}``, in a stable order.

    ``only`` narrows the per-item sheets to one item — the front matter is still generated,
    because a single sheet with no criteria page behind it is not checkable.
    """
    files: dict[str, str] = {
        "README.md": _readme(inputs),
        "00-cover.md": _cover(inputs),
        "00-summary.md": render_summary(inputs, parse_previous(inputs.previous)),
        "01-design-criteria.md": _criteria(inputs),
        "02-item-register.md": register_page(inputs),
        "03-open-items.md": open_items_page(inputs),
        "04-assumptions.md": _assumptions(inputs),
        "05-scope-of-review.md": scope_page(inputs),
        CONVENTIONS_FILE: render_conventions(house=inputs.house),
    }
    kept = [record for record in inputs.records
            if only is None or record.item_id == only]
    # ** THE CALCULATIONS ARE PER FAMILY; THE PER-ITEM DATA IS AN APPENDIX. **
    # One sheet per item meant twelve copies of ACI 318-19 §22.4.2.1 for twelve cast
    # columns, and eleven of them added an element tag and four numbers to the first. A
    # reviewer wants the clause once, the arithmetic once, and a schedule saying which
    # member governs. Nothing is dropped: every field the per-item sheet ever carried is
    # still on it, in `appendix/`, behind the calculation that reads it. The PDF prints
    # the per-KIND tables and not the per-member sheets (2026-09-22: those were 192 pages).
    for kind, records in families(kept).items():
        files[f"calcs/{family_filename(kind)}"] = render_family(
            kind, records, inputs.register, generated=inputs.generated,
            house=inputs.house, design_method=design_method(kind, records))
        files[appendix_filename(kind)] = render_appendix(
            kind, records, house=inputs.house)
    for record in kept:
        files[f"appendix/{sheet_filename(record.item_id)}"] = render_sheet(
            record, inputs.register, generated=inputs.generated, house=inputs.house)
    return dict(sorted(files.items()))


# --- front matter ----------------------------------------------------------------------

def _readme(inputs: PackageInputs) -> str:
    sheets = [f"`calcs/{family_filename(kind)}` — {len(group)} member(s)"
              for kind, group in families(list(inputs.records)).items()]
    return document(
        heading(f"Calculation package — {inputs.house}"),
        NOT_FOR_CONSTRUCTION,
        heading("How to read this package", 2),
        bullets([
            "`00-summary.md` — one page: criteria, the ten highest ratios, what changed "
            "since the last issue, what is open, and what is not covered.",
            "`00-cover.md` — what this is a calculation for, against which model, and "
            "where the permit gate stands.",
            "`01-design-criteria.md` — the loads, the ground and the materials every sheet "
            "behind it assumes. Derived from the model, not typed: if a sheet disagrees "
            "with this page, the package is broken and should be regenerated.",
            "`02-item-register.md` — every engineered item on one table, with its governing "
            "limit state, its seal status and the note that independently checks it.",
            "`03-open-items.md` — what is **not** finished, and who owns each one.",
            "`04-assumptions.md` — every assumption any calculation made, deduped.",
            f"`calcs/` — **the calculations**, one per design family with a member "
            f"schedule: {len(families(list(inputs.records)))} of them, each in the same "
            f"ten-section order.",
            f"`{CONVENTIONS_FILE}` — how every calculation reads, and what none of them "
            f"covers, said once.",
            f"`appendix/<kind>.md` — the per-member data behind those schedules, one table "
            f"per family with a column per member. Beside it, one nine-section sheet per "
            f"item (`appendix/<kind>__<tag>.md`, {len(inputs.records)} of them) as diffable "
            f"machine data, which the PDF does not print. The per-family tables are in the "
            f"PDF of a `haus handoff` bundle, and in `haus calcs --pdf` only with "
            f"`--appendix`. Nothing in it is a second calculation; it is what the schedule "
            f"rows are read off.",
        ]),
        heading("Regenerating it", 2),
        "This package is generated, not maintained. Re-run `haus calcs "
        f"houses/{inputs.house}` and it is rebuilt from the model; the output is "
        "byte-deterministic, so a diff between two runs is a real change in the model or "
        "the calculations and nothing else. Do not edit these files — an edit is lost on "
        "the next run, and worse, it makes the package disagree with the model it claims to "
        "describe.",
        heading("The calculations", 2),
        bullets(sheets) if sheets else "_No engineered item in this house._",
    )


def _cover(inputs: PackageInputs) -> str:
    gate = _gate_lines(inputs)
    profile = inputs.profile
    edition = getattr(profile, "edition", "")
    jurisdiction = (f"{inputs.profile_name} — {edition}" if inputs.profile_name and edition
                    else inputs.profile_name or "not declared")
    revision = ([("Live model revision", f"`{inputs.model_revision}`")]
                if inputs.model_revision else [])
    asce = getattr(profile, "asce_edition", "")
    return document(
        heading(f"{inputs.house} — structural calculation package"),
        callout(NOT_FOR_CONSTRUCTION, marker="**Status: DRAFT**"),
        heading("This package", 2),
        kv_block([
            ("House", inputs.house),
            ("Jurisdiction", jurisdiction),
            ("Loads standard", asce or "see the design criteria"),
            ("Generated", inputs.generated),
            ("Software version", inputs.engine_version or "unknown"),
            ("Model content hash", f"`{inputs.content_hash}`" if inputs.content_hash else ""),
            ("Engineered items", len(inputs.records)),
        ] + revision),
        heading("Where the gates stand", 2),
        gate,
        heading("The two gates", 2),
        bullets([
            "**draft** — the item has been computed and every limit state listed on its sheet "
            "is within capacity. A limit state the sheet does not list is not evaluated and is "
            "not implied to pass (section 10 of each calculation). `haus print` gates here.",
            "**sealed** — a licensed professional stamped the item *and* the fingerprint "
            "pinned in `engineering.toml` still matches the model in front of you. "
            "`haus print --sealed` gates here.",
        ]),
        "A stamp that pins no fingerprint cannot go stale, and so says nothing about this "
        "model. It never satisfies the sealed gate.",
    )


def _gate_lines(inputs: PackageInputs) -> str:
    counts = _status_counts(inputs.records)
    sealed = sum(1 for record in inputs.records
                 if inputs.register.covering(record.item_id) is not None)
    rows = [[STATE_NAME[status], counts.get(status, 0)]
            for status in (Status.OK, Status.INCOMPLETE, Status.NO_CALC, Status.OVER)]
    rows.append(["items covered by a signoff in engineering.toml", sealed])
    block = (f"{len(inputs.records)} item(s): {state_line(inputs.records)}. A computed item "
             "is not a complete one; the others are open.\n\n"
             + table(["Local calculation status", "Items"], rows))
    checklist = inputs.checklist
    if checklist is None:
        return block + "\n\nThe permit checklist was not evaluated for this package."
    verdict = ("the **draft** gate is OPEN" if getattr(checklist, "ok", False)
               else "the **draft** gate is SHUT")
    final = ("and the **sealed** gate is OPEN" if getattr(checklist, "sealed", False)
             else "and the **sealed** gate is SHUT")
    return block + f"\n\nAgainst the declared permit checklist, {verdict} {final}."


def _status_counts(records) -> dict[Status, int]:
    counts: dict[Status, int] = {}
    for record in records:
        counts[record.status] = counts.get(record.status, 0) + 1
    return counts


def _assumptions(inputs: PackageInputs) -> str:
    """Every distinct assumption any record made, grouped by the kind that made it.

    Collapsed rather than merely deduped: twelve columns stating one sentence with their
    own numbers is one assumption and a table of numbers (2026-09-22: this page was 22 of
    them). :mod:`typehaus.takeoff.calc_collapse` drops nothing — every original expands
    back out of its template and values.
    """
    by_kind: dict[str, list[tuple[str, str]]] = {}
    for record in inputs.records:
        for note in record.notes:
            by_kind.setdefault(record.kind, []).append((record.item_id, note))
    blocks = [
        heading(f"Assumptions and exclusions — {inputs.house}"),
        "Every assumption any calculation in this package made, verbatim, grouped by the "
        "kind of calculation that made it. These are the statements a reviewer is "
        "entitled to disagree with; each one names the items it reaches. Where members "
        "state one sentence with their own numbers, it is printed once with the numbers "
        "as [1], [2] … and a table of what each member put there.",
    ]
    if not by_kind:
        blocks.append("_No record carries an assumption._")
    for kind in sorted(by_kind):
        blocks += [heading(f"`{kind}`", 2),
                   collapsed_tables(collapse(by_kind[kind]), label="Assumption")]
    return document(*blocks)
