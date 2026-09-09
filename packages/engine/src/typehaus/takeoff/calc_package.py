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

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from typehaus.emit.md_writer import bullets, callout, document, heading, kv_block, table
from typehaus.engineering.deferred import DEFERRALS
from typehaus.engineering.item import EngineeringRecord, Status
from typehaus.engineering.register import EngineeringRegister
from typehaus.takeoff.calc_criteria import _criteria
from typehaus.takeoff.calc_sheet import STATUS_LABEL, render_sheet, sheet_filename

#: Printed on the cover, and meant to be read. A draft package is a working document; a set
#: that leaves this repo without saying so can be mistaken for one somebody sealed.
NOT_FOR_CONSTRUCTION = (
    "NOT FOR CONSTRUCTION. This package is generated from a model by the Type:Haus engine. "
    "Every result in it is a **draft** calculation: it is this engine's own first-principles "
    "arithmetic, checked against an independently hand-worked note, and it is not a "
    "professional engineer's seal. Nothing here may be built from until a licensed engineer "
    "has reviewed it and stamped the items on the register."
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
    records: tuple[EngineeringRecord, ...] = field(default_factory=tuple)

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
        "01-design-criteria.md": _criteria(inputs),
        "02-item-register.md": _register_page(inputs),
        "03-open-items.md": _open_items(inputs),
        "04-assumptions.md": _assumptions(inputs),
        "05-scope-of-review.md": _scope_of_review(inputs),
    }
    for record in inputs.records:
        if only is not None and record.item_id != only:
            continue
        files[f"calcs/{sheet_filename(record.item_id)}"] = render_sheet(
            record, inputs.register, generated=inputs.generated, house=inputs.house)
    return dict(sorted(files.items()))


# --- front matter ----------------------------------------------------------------------

def _readme(inputs: PackageInputs) -> str:
    sheets = [f"`calcs/{sheet_filename(r.item_id)}`" for r in inputs.records]
    return document(
        heading(f"Calculation package — {inputs.house}"),
        NOT_FOR_CONSTRUCTION,
        heading("How to read this package", 2),
        bullets([
            "`00-cover.md` — what this is a calculation for, against which model, and "
            "where the permit gate stands.",
            "`01-design-criteria.md` — the loads, the ground and the materials every sheet "
            "behind it assumes. Derived from the model, not typed: if a sheet disagrees "
            "with this page, the package is broken and should be regenerated.",
            "`02-item-register.md` — every engineered item on one table, with its governing "
            "limit state, its seal status and the note that independently checks it.",
            "`03-open-items.md` — what is **not** finished, and who owns each one.",
            "`04-assumptions.md` — every assumption any calculation made, deduped.",
            f"`calcs/` — one sheet per item, {len(inputs.records)} of them, in the standard "
            f"nine-section order.",
        ]),
        heading("Regenerating it", 2),
        "This package is generated, not maintained. Re-run `haus calcs "
        f"houses/{inputs.house}` and it is rebuilt from the model; the output is "
        "byte-deterministic, so a diff between two runs is a real change in the model or "
        "the calculations and nothing else. Do not edit these files — an edit is lost on "
        "the next run, and worse, it makes the package disagree with the model it claims to "
        "describe.",
        heading("The sheets", 2),
        bullets(sheets) if sheets else "_No engineered item in this house._",
    )


def _cover(inputs: PackageInputs) -> str:
    gate = _gate_lines(inputs)
    return document(
        heading(f"{inputs.house} — structural calculation package"),
        callout(NOT_FOR_CONSTRUCTION, marker="**Status: DRAFT**"),
        heading("This package", 2),
        kv_block([
            ("House", inputs.house),
            ("Jurisdiction profile", inputs.profile_name or "not declared"),
            ("Generated", inputs.generated),
            ("Engine version", inputs.engine_version or "unknown"),
            ("Model content hash", f"`{inputs.content_hash}`" if inputs.content_hash else ""),
            ("Engineered items", len(inputs.records)),
        ]),
        heading("Where the gates stand", 2),
        gate,
        heading("The two gates", 2),
        bullets([
            "**draft** — this engine computed the item and every ratio is within capacity. "
            "That is what a permit-ready printoff is for, and what `haus print` gates on.",
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
    rows = [[STATUS_LABEL[status].split(" —")[0], counts.get(status, 0)]
            for status in (Status.OK, Status.OVER, Status.INCOMPLETE, Status.NO_CALC)]
    rows.append(["items covered by a signoff in engineering.toml", sealed])
    block = table(["Local calculation status", "Items"], rows)
    checklist = inputs.checklist
    if checklist is None:
        return block + "\n\nThe permit checklist was not evaluated for this package."
    verdict = ("the **draft** gate is OPEN" if getattr(checklist, "ok", False)
               else "the **draft** gate is SHUT")
    final = ("and the **sealed** gate is OPEN" if getattr(checklist, "sealed", False)
             else "and the **sealed** gate is SHUT")
    return block + f"\n\nAgainst the declared permit checklist, {verdict} {final}."


def _status_counts(records: Sequence[EngineeringRecord]) -> dict[Status, int]:
    counts: dict[Status, int] = {}
    for record in records:
        counts[record.status] = counts.get(record.status, 0) + 1
    return counts


def _scope_of_review(inputs: PackageInputs) -> str:
    """05 — what a seal over this package would and would not cover. One page.

    The register says what each item *is*; this says what signing it *means*. It is the
    page a reviewer asked for a scope letter reads, and the reason it is generated rather
    than written is the same as everywhere else here: a scope that can drift from the items
    it scopes is worse than none.
    """
    computed = [r for r in inputs.records if r.status is Status.OK]
    incomplete = [r for r in inputs.records if r.status is Status.INCOMPLETE]
    deferred = [r for r in inputs.records if r.status is Status.NO_CALC]
    sealed = [r for r in inputs.records
              if inputs.register.freshness(r)[0].value == "fresh"]
    return document(
        heading(f"Scope of review — {inputs.house}"),
        "What a professional seal over this package covers, and what it does not. "
        f"{len(inputs.records)} engineered item(s) in three states.",
        table(["State", "Items", "What a seal over it would mean"], [
            ["**Computed**", len(computed),
             "This engine derived a demand and a capacity and the item checks out. A seal "
             "here is a review of THIS arithmetic against THIS model — the reviewer is "
             "adopting the calculation, not re-deriving it."],
            ["**Incomplete**", len(incomplete),
             "A demand or a capacity is missing an input. Nothing may be sealed here until "
             "the input is authored; see `03-open-items.md` for what each one needs."],
            ["**Deferred**", len(deferred),
             "This engine computes nothing and never will — a component manufacturer's or "
             "another engineer's sealed design governs. A seal on this package does NOT "
             "reach these; each names its own responsible designer."],
        ]),
        heading("What a seal does not cover, in any state", 2),
        bullets([
            "**The model.** A seal is pinned to a fingerprint of the elements it covers "
            "(`02-item-register.md`). Move one of them and the seal goes stale, by design.",
            "**Anything outside these item ids.** Every requirement met from a "
            "prescriptive table is graded by `haus check` and is not in this package.",
            "**Means and methods, MEP, energy, and the architectural set.** This package "
            "is structural calculation only.",
            "**Quantities.** The bill of materials is derived from the same model and is "
            "the contractor's to confirm.",
        ]),
        heading("Where it stands now", 2),
        f"{len(sealed)} of {len(inputs.records)} item(s) carry a fresh seal in "
        "`engineering.toml`. The engine reads that file and never writes it: a seal is a "
        "human act, and this package records it rather than performing it.",
    )



# --- register and gap pages --------------------------------------------------------------

def _register_page(inputs: PackageInputs) -> str:
    rows = []
    for record in inputs.records:
        governing = record.governing
        state, signoff = inputs.register.freshness(record)
        rows.append([
            f"`{record.item_id}`",
            ", ".join(record.element_tags) or record.key,
            STATUS_LABEL[record.status].split(" —")[0],
            governing.name if governing else "—",
            f"{governing.ratio:.2f}" if governing else "—",
            state.value + (f" ({signoff.id})" if signoff else ""),
            ", ".join(str(o) for o in record.oracle) or "**none**",
        ])
    return document(
        heading(f"Item register — {inputs.house}"),
        f"{len(rows)} engineered item(s). One row per element: identity is per element and "
        "never per group, so moving one wall stales that wall's seal and leaves its "
        "neighbours alone.",
        table(["Item", "Elements", "Local", "Governing", "d/c", "Seal",
               "Independently checked by"], rows),
        heading("Reading the seal column", 2),
        bullets([
            "`unsealed` — no signoff in `engineering.toml` covers this item.",
            "`unpinned` — a signoff covers it but recorded no fingerprint. It cannot go "
            "stale, so it satisfies no gate.",
            "`fresh` — sealed, and the pinned fingerprint still matches this model.",
            "`stale` — sealed once, and the model or the calculation has moved since. This "
            "is the only state that reads as done and is not.",
        ]),
    )


def _open_items(inputs: PackageInputs) -> str:
    """The gap register — everything not finished, and who owns it.

    Separated from the item register on purpose. Twenty-nine open rows scattered through a
    forty-six-row table is a list nobody reads to the end; a page whose only content is
    what is outstanding is one somebody works through.
    """
    open_records = [r for r in inputs.records
                    if r.status in (Status.INCOMPLETE, Status.NO_CALC, Status.OVER)]
    blocks = [
        heading(f"Open items — {inputs.house}"),
        (f"{len(open_records)} of {len(inputs.records)} items are not finished. Nothing on "
         "this page is a guess that failed: each row is an input this engine does not have "
         "or a design it does not do, named so that it can be assigned."),
    ]
    deferred = [r for r in open_records if r.status is Status.NO_CALC]
    if deferred:
        rows = []
        for record in deferred:
            deferral = DEFERRALS.get(record.kind)
            rows.append([
                f"`{record.item_id}`",
                deferral.designer if deferral else "not assigned",
                deferral.deliverable if deferral else record.summary,
                deferral.unblocks if deferral else "—",
            ])
        blocks += [
            heading("A. Deferred to a designer of record", 2),
            "This engine computes nothing for these, by decision — a fabricator's or a "
            "supplier's sealed design governs. They are exactly as blocking as they were "
            "before they had names.",
            table(["Item", "Designer of record", "What they must produce", "Unblocks"], rows),
        ]
    incomplete = [r for r in open_records if r.status is Status.INCOMPLETE]
    if incomplete:
        blocks += [
            heading("B. Incomplete — the calculation exists, an input does not", 2),
            "Each of these has a computed part and an uncomputed part. The ratio on the "
            "sheet is real and is **not** the whole answer.",
            table(["Item", "Governing (of what was computed)", "d/c", "What is missing"],
                  [[f"`{r.item_id}`",
                    r.governing.name if r.governing else "—",
                    f"{r.governing.ratio:.2f}" if r.governing else "—",
                    " ".join(r.missing)] for r in incomplete]),
        ]
    over = [r for r in open_records if r.status is Status.OVER]
    if over:
        blocks += [
            heading("C. Over capacity", 2),
            callout("These items were computed in full and do not check. They are design "
                    "failures, not gaps.", marker="**Action required**"),
            table(["Item", "Governing", "d/c", "Citation"],
                  [[f"`{r.item_id}`", r.governing.name, f"{r.governing.ratio:.2f}",
                    r.governing.citation] for r in over if r.governing]),
        ]
    if not open_records:
        blocks.append("**Nothing is outstanding.** Every item reached draft.")
    return document(*blocks)


def _assumptions(inputs: PackageInputs) -> str:
    """Every distinct assumption any record made, deduped, grouped by the kind that made it.

    Deduped because twenty wall panels making the same five assumptions is five
    assumptions; grouped by kind because an assumption is a property of the calculation,
    and a reviewer disagreeing with one wants to know every item it reaches.
    """
    by_kind: dict[str, dict[str, list[str]]] = {}
    for record in inputs.records:
        for note in record.notes:
            by_kind.setdefault(record.kind, {}).setdefault(note, []).append(record.item_id)
    blocks = [
        heading(f"Assumptions and exclusions — {inputs.house}"),
        "Every assumption any calculation in this package made, verbatim, deduped, and "
        "grouped by the kind of calculation that made it. These are the statements a "
        "reviewer is entitled to disagree with; each one names the items it reaches.",
    ]
    if not by_kind:
        blocks.append("_No record carries an assumption._")
    for kind in sorted(by_kind):
        rows = [[note, len(items),
                 ", ".join(f"`{i}`" for i in sorted(items)[:3])
                 + (f", … ({len(items)} items)" if len(items) > 3 else "")]
                for note, items in sorted(by_kind[kind].items())]
        blocks += [heading(f"`{kind}`", 2), table(["Assumption", "Items", "Reaching"], rows)]
    return document(*blocks)
