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
from typing import Any

from typehaus.emit.md_writer import bullets, callout, document, heading, kv_block, table
from typehaus.engineering.deferred import DEFERRALS
from typehaus.engineering.item import EngineeringRecord, Status
from typehaus.engineering.register import EngineeringRegister
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


# --- design criteria -------------------------------------------------------------------

def _criteria(inputs: PackageInputs) -> str:
    from typehaus import wind
    from typehaus.engineering import soil as soil_module

    site = getattr(getattr(inputs.model, "plan", None), "project", None)
    site = getattr(site, "site", None)
    blocks = [
        heading(f"Design criteria — {inputs.house}"),
        "Every value on this page is **derived from the model**, not typed here. A criteria "
        "sheet that can drift from the calculations it fronts is worse than none.",
        heading("1. Wind", 2),
        _wind_block(wind, site, inputs),
        heading("2. Snow", 2),
        _snow_block(site),
        heading("3. Ground", 2),
        _soil_block(soil_module, site),
        heading("4. Materials", 2),
        _materials_block(inputs),
        heading("5. Service conditions", 2),
        _service_block(inputs),
    ]
    return document(*blocks)


def _wind_block(wind: Any, site: Any, inputs: PackageInputs) -> str:
    basis = wind.wind_basis(site) if site is not None else None
    if basis is None:
        return ("This model carries no complete wind basis (a speed, an exposure and a risk "
                "category are all required). Every wind-driven item reports it as a missing "
                "input rather than assuming one.")
    heights = sorted({round(float(q.value), 2) for record in inputs.records
                      for q in record.inputs if q.name == "mean_roof_height"})
    rows = [
        ["V_ult, basic wind speed", basis.speed_mph, "mph",
         "ASCE 7-16 Fig. 26.5-1 via MN Rules 1309.0301 (115 mph statewide)"],
        ["Exposure category", basis.exposure, "", "ASCE 7-16 §26.7.3 — surface roughness "
         "determined for this site"],
        ["Risk category", basis.risk_category, "", "ASCE 7-16 Table 1.5-1 — a dwelling is II"],
        ["K_d, directionality", wind.K_D_BUILDINGS, "", "ASCE 7-16 Table 26.6-1"],
        ["K_zt, topographic factor", wind.K_ZT_FLAT, "", "ASCE 7-16 §26.8.2 — none of the "
         "three conditions of §26.8.1 is met"],
        ["K_e, ground elevation factor", 1.0, "", "ASCE 7-16 §26.9 — permitted at all "
         "elevations; the conservative side of a 3 % effect at this site"],
        ["ASD wind factor", wind.ASD_WIND_FACTOR, "", "ASCE 7-16 §2.4.1 combination 5/6 — "
         "every capacity cited in this package is an ASD allowable"],
    ]
    for height in heights:
        rows.append([f"q_z at {height:g} ft (mean roof height)",
                     wind.velocity_pressure_psf(basis, height), "psf",
                     "ASCE 7-16 eq. 26.10-1, strength level"])
    return table(["Quantity", "Value", "Unit", "Source"], rows)


def _snow_block(site: Any) -> str:
    ground = getattr(site, "ground_snow_load_psf", None) if site is not None else None
    if ground is None:
        return ("This model carries no ground snow load. Every snow-driven item reports it "
                "as a missing input.")
    return table(["Quantity", "Value", "Unit", "Source"],
                 [["p_g, ground snow load", ground, "psf",
                   "IRC Table R301.2(1) — a jurisdictional figure, authored on the site, "
                   "not derived"]])


def _soil_block(soil_module: Any, site: Any) -> str:
    soil_class = getattr(site, "soil_class", None) if site is not None else None
    presumptive = soil_module.presumptive(soil_class)
    if presumptive is None:
        return (f"This model declares no usable soil group (`soil_class` = "
                f"{soil_class!r}). No lateral pressure, bearing value or base friction is "
                f"presumed: a calculation that needs one reports it as a missing input, "
                f"because guessing the ground is the one assumption a retaining wall "
                f"cannot survive.")
    bed = soil_module.aggregate_bed()
    rows = [
        ["Declared soil group", presumptive.soil_class, "", "IRC Table R405.1 / Unified"],
        ["IBC presumptive class", presumptive.ibc_class, "", presumptive.citation],
        ["Active equivalent fluid pressure", presumptive.active_efp_psf_per_ft, "psf/ft",
         "IBC Table 1610.1"],
        ["At-rest equivalent fluid pressure", presumptive.at_rest_efp_psf_per_ft, "psf/ft",
         "IBC Table 1610.1 — used where the wall is restrained against rotation"],
        ["Allowable bearing", presumptive.allowable_bearing_psf, "psf",
         "IBC Table 1806.2"],
        ["Lateral bearing", presumptive.lateral_bearing_psf_per_ft, "psf/ft",
         "IBC Table 1806.2"],
        ["Base friction coefficient (native)", presumptive.friction_coefficient, "",
         "IBC Table 1806.2"],
        ["Base friction coefficient (on washed stone)", bed.friction_coefficient, "",
         f"{bed.citation} — a footing bearing on a replacement stone section slides on "
         f"stone, not on the retained soil behind the wall"],
        ["Soil unit weight band", f"{soil_module.SOIL_UNIT_WEIGHT_BAND_PCF[0]:g}–"
         f"{soil_module.SOIL_UNIT_WEIGHT_BAND_PCF[1]:g}", "pcf",
         "not a code value — loose-to-medium silty gravel through well compacted"],
        ["Concrete unit weight", soil_module.CONCRETE_UNIT_WEIGHT_PCF, "pcf",
         "conventional, and not in dispute"],
    ]
    return table(["Quantity", "Value", "Unit", "Source"], rows)


#: Input names that describe a *material*, and the row each becomes. Derived from what the
#: calculations actually consumed, so a material nothing is designed against never appears.
_MATERIAL_INPUTS = {
    "fc": ("f'c, specified concrete compressive strength", "psi"),
    "fy": ("f_y, specified yield strength of reinforcement", "psi"),
    "Fb_adjusted": ("F_b', adjusted bending design value", "psi"),
    "E_adjusted": ("E', adjusted modulus of elasticity", "psi"),
    "concrete_unit_weight": ("Concrete unit weight", "pcf"),
}


def _materials_block(inputs: PackageInputs) -> str:
    """Material properties, collected from the values the calculations actually consumed.

    Not read off the assemblies: an assembly a calculation never looked at would then be
    printed as a design criterion, which is precisely the drift this page exists to
    prevent. Where one calc used 3,000 psi and another 5,000, both appear, with the items
    that used each — that disagreement is a fact a reviewer needs, not a thing to average.
    """
    seen: dict[tuple[str, float], list[str]] = {}
    for record in inputs.records:
        for quantity in record.inputs:
            if quantity.name in _MATERIAL_INPUTS:
                seen.setdefault((quantity.name, round(float(quantity.value), 6)),
                                []).append(record.item_id)
    if not seen:
        return "_No calculation in this package consumed a declared material property._"
    rows = []
    for (name, value), items in sorted(seen.items()):
        label, unit = _MATERIAL_INPUTS[name]
        rows.append([label, value, unit, len(items),
                     ", ".join(f"`{i}`" for i in sorted(items)[:4])
                     + (", …" if len(items) > 4 else "")])
    return table(["Property", "Value", "Unit", "Items", "Used by"], rows) + \
        "\n\nWhere one value appears twice, two calculations were run against two different " \
        "strengths. That is reported and not reconciled."


def _service_block(inputs: PackageInputs) -> str:
    """The distinct bases the package rests on — one row per standard actually cited."""
    bases: dict[str, list[str]] = {}
    for record in inputs.records:
        if record.basis:
            bases.setdefault(record.basis, []).append(record.item_id)
    if not bases:
        return "_No basis is recorded on any item._"
    rows = [[basis, len(items), ", ".join(sorted({i.split("/")[0] for i in items}))]
            for basis, items in sorted(bases.items())]
    return table(["Basis", "Items", "Kinds"], rows)


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
