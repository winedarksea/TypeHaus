"""The register, open-items and scope pages of the calculation package (``02``, ``03``, ``05``).

Split out of :mod:`typehaus.takeoff.calc_package` (500-line ceiling). All three read the
records and the seal register; none computes anything.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typehaus.emit.md_writer import bullets, callout, document, heading, table
from typehaus.engineering.deferred import DEFERRALS
from typehaus.engineering.item import Status
from typehaus.takeoff.calc_summary import STATE_NAME, ratio_cell, trigger_note

if TYPE_CHECKING:  # pragma: no cover — typing only
    from typehaus.takeoff.calc_package import PackageInputs


def presumed_inputs(record) -> list[str]:  # type: ignore[no-untyped-def]
    """Names of the ``<x>_presumed`` flags a record raised (``base_rotation``'s n_h,
    ``thermal_break``'s k_v): a published table row standing in for a measurement."""
    return [q.name.removesuffix("_presumed") for q in record.inputs
            if q.name.endswith("_presumed") and q.value >= 0.5]


def _locations(inputs: PackageInputs) -> dict:
    """``item id -> Location`` on the key plan's grid; empty when the model cannot place it."""
    from typehaus.takeoff.handoff_drawings import item_locations

    try:
        return item_locations(inputs.model, list(inputs.records))
    except (AttributeError, TypeError):
        return {}


def register_page(inputs: PackageInputs) -> str:
    """02 — every item, highest d/c first, with where it is and how many states were graded."""
    where = _locations(inputs)

    def order(record) -> tuple:  # type: ignore[no-untyped-def]
        ratio = record.ratio
        return (0 if ratio is not None else 1, -(ratio or 0.0), record.item_id)

    rows = []
    for record in sorted(inputs.records, key=order):
        governing = record.governing
        state, signoff = inputs.register.freshness(record)
        place = where.get(record.item_id)
        graded = sum(1 for s in record.limit_states if not s.is_detailing)
        rows.append([
            f"`{record.item_id}`",
            f"{place.level} ({place.x_ft:g}, {place.y_ft:g} ft)" if place else "—",
            ", ".join(record.element_tags) or record.key,
            STATE_NAME[record.status],
            governing.name if governing else "—",
            ratio_cell(governing.ratio if governing else None),
            graded or "—",
            state.value + (f" ({signoff.id})" if signoff else ""),
            ", ".join(str(o) for o in record.oracle) or "**none**",
        ])
    return document(
        heading(f"Item register — {inputs.house}"),
        f"{len(rows)} engineered item(s), highest d/c first. One row per element: identity is "
        "per element and never per group, so moving one wall stales that wall's seal and "
        "leaves its neighbours alone.",
        table(["Item", "Where", "Elements", "Status", "Governing", "d/c", "States", "Seal",
               "Independently checked by"], rows),
        heading("Reading the table", 2),
        bullets([
            trigger_note(),
            "**Where** is the item's level and the plan position of its key element in feet "
            "(x, y), on the 10 ft grid of the key plan (`drawings/key_plan.pdf` in a handoff "
            "bundle).",
            "**States** is how many limit states were graded to give the d/c. A low d/c "
            "beside one state is not a margin on the item, only on that state.",
            "`unsealed` — no signoff in `engineering.toml` covers this item.",
            "`unpinned` — a signoff covers it but recorded no fingerprint. It cannot go "
            "stale, so it satisfies no gate.",
            "`fresh` — sealed, and the pinned fingerprint still matches this model.",
            "`stale` — sealed once, and the model or the calculation has moved since. This "
            "is the only state that reads as done and is not.",
        ]),
    )


def open_items_page(inputs: PackageInputs) -> str:
    """03 — everything not finished, and who owns it. Sections A to D always print."""
    records = inputs.records
    open_records = [r for r in records
                    if r.status in (Status.INCOMPLETE, Status.NO_CALC, Status.OVER)]
    blocks = [
        heading(f"Open items — {inputs.house}"),
        f"{len(open_records)} of {len(records)} items are open. Each row below names an input "
        "that is missing or a design that someone else owns, so it can be assigned.",
    ]
    deferred = [r for r in open_records if r.status is Status.NO_CALC]
    blocks.append(heading("A. Deferred to a designer of record", 2))
    if deferred:
        # Items that share one deferral share one row: two trussed roofs are one ask.
        grouped: dict[tuple[str, str, str], list[str]] = {}
        for record in deferred:
            deferral = DEFERRALS.get(record.kind)
            key = (deferral.designer if deferral else "not assigned",
                   deferral.deliverable if deferral else record.summary,
                   deferral.unblocks if deferral else "—")
            grouped.setdefault(key, []).append(f"`{record.item_id}`")
        rows = [[", ".join(items), *key] for key, items in grouped.items()]
        blocks += [
            "A fabricator's or supplier's sealed design governs these; nothing in this "
            "package computes them.",
            table(["Item", "Designer of record", "What they must produce", "Unblocks"], rows),
        ]
    else:
        blocks.append("None.")
    incomplete = [r for r in open_records if r.status is Status.INCOMPLETE]
    blocks.append(heading("B. Incomplete — the calculation exists, an input does not", 2))
    if incomplete:
        blocks += [
            "Each has a computed part and an uncomputed part. The ratio shown is real and is "
            "**not** the whole answer.",
            table(["Item", "Governing (of what was computed)", "d/c", "What is missing"],
                  [[f"`{r.item_id}`", r.governing.name if r.governing else "—",
                    ratio_cell(r.governing.ratio if r.governing else None),
                    "; ".join(r.missing)] for r in incomplete]),
        ]
    else:
        blocks.append("None.")
    over = [r for r in open_records if r.status is Status.OVER]
    blocks.append(heading("C. Over capacity", 2))
    if over:
        blocks += [
            callout("These items were computed in full and do not check. They are design "
                    "failures, not gaps.", marker="**Action required**"),
            table(["Item", "Governing", "d/c", "Citation"],
                  [[f"`{r.item_id}`", r.governing.name, f"{r.governing.ratio:.3f}",
                    r.governing.citation] for r in over if r.governing]),
        ]
    else:
        blocks.append("None.")
    presumed = [r for r in records if r.status not in (Status.INCOMPLETE, Status.NO_CALC,
                                                       Status.OVER) and presumed_inputs(r)]
    if presumed:
        blocks += [
            heading("D. Graded on a presumed input — computed, not closed", 2),
            "Each checks out on a PUBLISHED table value for the presumed soil, not a "
            "measurement on this parcel. A geotechnical report confirms or replaces the "
            "value; until then the row stays here.",
            table(["Item", "Presumed input", "Governing", "d/c"],
                  [[f"`{r.item_id}`", ", ".join(presumed_inputs(r)),
                    r.governing.name if r.governing else "—",
                    ratio_cell(r.governing.ratio if r.governing else None)]
                   for r in presumed]),
        ]
    if not open_records and not presumed:
        blocks.append("**Nothing is outstanding.** Every item is computed.")
    return document(*blocks)


def scope_page(inputs: PackageInputs) -> str:
    """05 — what a seal over this package would and would not cover. One page."""
    records = inputs.records
    computed = [r for r in records if r.status is Status.OK]
    incomplete = [r for r in records if r.status is Status.INCOMPLETE]
    over = [r for r in records if r.status is Status.OVER]
    deferred = [r for r in records if r.status is Status.NO_CALC]
    sealed = [r for r in records if inputs.register.freshness(r)[0].value == "fresh"]
    return document(
        heading(f"Scope of review — {inputs.house}"),
        "What a professional seal over this package covers, and what it does not. "
        f"{len(records)} engineered item(s) in four states.",
        table(["State", "Items", "What a seal over it would mean"], [
            [f"**{STATE_NAME[Status.OK]}**", len(computed),
             "A demand and a capacity were computed and every limit state on the sheet is "
             "within capacity. A seal here is a review of THIS arithmetic against THIS "
             "model: the reviewer is adopting the calculation, not re-deriving it."],
            [f"**{STATE_NAME[Status.INCOMPLETE]}**", len(incomplete),
             "A demand or a capacity is missing an input. Nothing may be sealed here until "
             "the input is authored; see `03-open-items.md` for what each one needs."],
            [f"**{STATE_NAME[Status.OVER]}**", len(over),
             "Computed in full and not within capacity: a design failure to resolve before "
             "any seal."],
            [f"**{STATE_NAME[Status.NO_CALC]}**", len(deferred),
             "Not computed here: a component manufacturer's or another engineer's sealed "
             "design governs. A seal on this package does NOT reach these; each names its "
             "own responsible designer."],
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
        f"{len(sealed)} of {len(records)} item(s) carry a fresh seal in `engineering.toml`. "
        "The seal register is read from that file and never written: a seal is a human "
        "act, and this package records it rather than performing it.",
    )
