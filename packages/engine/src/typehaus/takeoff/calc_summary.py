"""``00-summary.md`` — the one page a reviewer reads to decide whether to read the rest.

Criteria, the ten highest ratios, counts, every presumed or authored input, what changed since
the last issue, what is open, and a pointer to what each family does not cover. Everything is
derived from the records; the previous issue arrives as two markdown files read by the caller
(:func:`read_previous`), so :func:`render_summary` stays pure.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from typehaus.emit.md_writer import bullets, document, heading, table
from typehaus.engineering.deferred import DEFERRALS
from typehaus.engineering.item import EngineeringRecord, Scope, Status
from typehaus.takeoff.calc_criteria_loads import consumed, input_name
from typehaus.takeoff.calc_criteria_materials import material_rows

if TYPE_CHECKING:  # pragma: no cover — typing only
    from typehaus.takeoff.calc_package import PackageInputs

#: Owner cost-review trigger (decision 30). NOT an acceptance limit: the limit is 1.000.
COST_REVIEW_TRIGGER = 0.85
ACCEPTANCE_LIMIT = 1.0

#: The one name per state used on every front-matter page (cover, summary, register, open
#: items, scope), so the same three items are not "NO LOCAL CALC", "not finished" and "Deferred".
STATE_NAME = {Status.OK: "Computed", Status.INCOMPLETE: "Incomplete",
              Status.NO_CALC: "Deferred", Status.OVER: "Over capacity"}
_OLD_NAME = {"draft": "Computed", "NO LOCAL CALC": "Deferred", "INCOMPLETE": "Incomplete",
             "OVER": "Over capacity"}
_STATE_ORDER = (Status.OK, Status.INCOMPLETE, Status.NO_CALC, Status.OVER)
_SCOPE_NAME = {Scope.COMPLETE: "complete", Scope.SCREENING: "screening",
               Scope.EXTERNAL: "external"}


def state_line(records: Sequence[EngineeringRecord]) -> str:
    """``"29 computed, 2 incomplete, 3 deferred"`` — only the states that occur."""
    counts = {s: sum(1 for r in records if r.status is s) for s in _STATE_ORDER}
    return ", ".join(f"{n} {STATE_NAME[s].lower()}" for s, n in counts.items() if n)


def scope_sentence(records: Sequence[EngineeringRecord]) -> str:
    """``"Computed: 29 screening. Deferred: 3 external."`` — how much each state answers."""
    parts = []
    for state in _STATE_ORDER:
        by_scope = [f"{n} {_SCOPE_NAME[sc]}" for sc in Scope
                    if (n := sum(1 for r in records if r.status is state and r.scope is sc))]
        if by_scope:
            parts.append(f"{STATE_NAME[state]}: {', '.join(by_scope)}.")
    return (" ".join(parts) + " A **screening** item grades the limit states listed on its "
            "sheet, and nothing else is implied to pass.")


def trigger_note() -> str:
    return (f"**Bold d/c** is at or above {COST_REVIEW_TRIGGER:g}, the owner's cost-review "
            f"trigger. It is not an acceptance limit: the limit is {ACCEPTANCE_LIMIT:.3f}.")


def ratio_cell(ratio: float | None) -> str:
    """A d/c to three places, bold at the cost-review trigger."""
    if ratio is None:
        return "—"
    text = f"{ratio:.3f}"
    return f"**{text}**" if ratio >= COST_REVIEW_TRIGGER else text


# --- the previous issue --------------------------------------------------------------------

@dataclass(frozen=True)
class PreviousIssue:
    generated: str
    content_hash: str
    #: item id -> (state name, governing text, d/c or None)
    rows: Mapping[str, tuple[str, str, float | None]]


def read_previous(root: Path) -> dict[str, str] | None:
    """The cover and register of an earlier package at ``root`` (or ``root/calcs``).

    ``None`` when there is none. This is the package's only disk read, and the caller makes it.
    """
    for base in (root, root / "calcs"):
        cover, register = base / "00-cover.md", base / "02-item-register.md"
        if cover.is_file() and register.is_file():
            return {"00-cover.md": cover.read_text(encoding="utf-8"),
                    "02-item-register.md": register.read_text(encoding="utf-8")}
    return None


def parse_previous(files: Mapping[str, str] | None) -> PreviousIssue | None:
    if not files or "02-item-register.md" not in files:
        return None
    cover = files.get("00-cover.md", "")
    generated = re.search(r"\*\*Generated:\*\*\s*(\S+)", cover)
    digest = re.search(r"\*\*Model content hash:\*\*\s*`?([0-9a-f]+)", cover)
    rows: dict[str, tuple[str, str, float | None]] = {}
    header: list[str] = []
    for line in files["02-item-register.md"].splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == "Item":
            header = cells
            continue
        if not header or set(cells[0]) <= {"-", ":"}:
            continue
        row = dict(zip(header, cells, strict=False))
        item = row.get("Item", "").strip("`")
        state = row.get("Status") or row.get("Local", "")
        ratio = row.get("d/c", "").strip("*")
        try:
            value: float | None = float(ratio)
        except ValueError:
            value = None
        rows[item] = (_OLD_NAME.get(state, state), row.get("Governing", ""), value)
    return PreviousIssue(generated.group(1) if generated else "",
                         digest.group(1) if digest else "", rows)


def changes_since(previous: PreviousIssue | None, records: Sequence[EngineeringRecord],
                  content_hash: str) -> str:
    """The "what changed" block: items added or removed, state moves, ratio moves."""
    if previous is None:
        return ("**First issue.** No earlier package was supplied to compare against "
                "(`haus calcs --since <earlier package folder>` compares to one).")
    now = {r.item_id: r for r in records}
    lines: list[str] = []
    for item in sorted(set(now) - set(previous.rows)):
        lines.append(f"`{item}` added.")
    for item in sorted(set(previous.rows) - set(now)):
        lines.append(f"`{item}` removed.")
    for item in sorted(set(now) & set(previous.rows)):
        record, (state, governing, ratio) = now[item], previous.rows[item]
        name = STATE_NAME[record.status]
        gov = record.governing
        moved = []
        if name != state:
            moved.append(f"{state} to {name}")
        new_ratio = None if gov is None else gov.ratio
        if (ratio is None) != (new_ratio is None) or (
                ratio is not None and new_ratio is not None and abs(ratio - new_ratio) >= 0.0005):
            before = "none" if ratio is None else f"{ratio:.3f}"
            after = "none" if new_ratio is None else f"{new_ratio:.3f}"
            moved.append(f"d/c {before} to {after}")
        if gov is not None and governing and gov.name != governing:
            moved.append(f"governing state now {gov.name}")
        if moved:
            lines.append(f"`{item}`: " + "; ".join(moved) + ".")
    same_model = bool(previous.content_hash) and content_hash.startswith(previous.content_hash)
    head = (f"Compared with the package generated {previous.generated or 'earlier'} "
            f"(model `{previous.content_hash[:12] or 'unknown'}`); the model is "
            + ("unchanged." if same_model else "changed."))
    if not lines:
        return head + " **No item changed state, ratio or governing limit state.**"
    shown = lines[:25]
    if len(lines) > len(shown):
        shown.append(f"and {len(lines) - len(shown)} more.")
    return head + "\n\n" + bullets(shown)


# --- the page ------------------------------------------------------------------------------

def _criteria_rows(inputs: PackageInputs) -> list[list[str]]:
    from typehaus import wind
    from typehaus.engineering import soil as soil_module

    site = getattr(getattr(inputs.model, "plan", None), "project", None)
    site = getattr(site, "site", None)
    rows: list[list[str]] = []
    basis = wind.wind_basis(site) if site is not None else None
    if basis is not None:
        rows.append(["Wind", f"V_ult {basis.speed_mph:g} mph, Exposure {basis.exposure}, "
                             f"Risk Category {basis.risk_category}"])
    ground = getattr(site, "ground_snow_load_psf", None)
    design = sorted({round(float(q.value), 1) for r in inputs.records for q in r.inputs
                     if q.name in ("roof_snow", "design_snow")})
    if ground is not None:
        extra = f"; roof design snow {', '.join(f'{v:g}' for v in design)} psf (authored)" \
            if design else ""
        rows.append(["Snow", f"p_g {float(ground):g} psf{extra}"])
    for label, names, unit in (("Live load", {"floor_live", "live_load"}, "psf"),
                               ("Dead load", {"floor_dead", "dead_load"}, "psf")):
        found = consumed(inputs, names, unit)
        if found:
            rows.append([label, ", ".join(f"{v:g}" for v in sorted(found)) + f" {unit}"])
    guard = consumed(inputs, {"head_lateral_guard"}, "lb")
    if guard:
        rows.append(["Guard", ", ".join(f"{v:g}" for v in sorted(guard)) + " lb concentrated"])
    category = getattr(getattr(inputs, "profile", None), "seismic_design_category", None)
    rows.append(["Seismic", f"Category {category}; no seismic demand computed here"
                 if category else "no category stated; no seismic demand computed here"])
    soil_class = getattr(site, "soil_class", None)
    presumptive = soil_module.presumptive(soil_class, basis=getattr(site, "soil_basis", None))
    if presumptive is not None:
        rows.append(["Ground", f"soil group {presumptive.soil_class} (presumed, not measured): "
                               f"active EFP {presumptive.active_efp_psf_per_ft:g} psf/ft, "
                               f"bearing {presumptive.allowable_bearing_psf:g} psf"])
    mats = material_rows(inputs)
    for key, label in (("f'c", "Concrete f'c"), ("f_y", "Reinforcement f_y")):
        vals = sorted({v for p, v, *_ in mats if p.startswith(key)})
        if vals:
            rows.append([label, ", ".join(f"{v:,.0f}" for v in vals) + " psi"])
    asce = getattr(getattr(inputs, "profile", None), "asce_edition", "")
    if asce:
        rows.append(["Loads standard", asce])
    return rows


def _top(records: Sequence[EngineeringRecord], n: int = 10) -> list[EngineeringRecord]:
    rated = [r for r in records if r.governing is not None]
    return sorted(rated, key=lambda r: (-r.governing.ratio, r.item_id))[:n]  # type: ignore[union-attr]


def _input_rows(inputs: PackageInputs) -> list[list[str]]:
    """Presumed flags, ESTIMATED notes and authored snow; items with the same input share a row."""
    grouped: dict[tuple[str, str], list[str]] = {}
    for record in inputs.records:
        flags = sorted({input_name(q.name.removesuffix("_presumed")) for q in record.inputs
                        if q.name.endswith("_presumed") and q.value >= 0.5})
        if flags:
            grouped.setdefault((", ".join(flags), "presumed from a published table row, not "
                                "measured on this parcel"), []).append(f"`{record.item_id}`")
        estimated = next((part.strip() for note in record.notes
                          for part in re.split(r"(?<=[.;])\s+", note) if "ESTIMATED" in part),
                         None)
        if estimated:
            grouped.setdefault(("estimated value", estimated[:200].rstrip(" ;,")),
                               []).append(f"`{record.item_id}`")
    rows = [[", ".join(items), *key] for key, items in grouped.items()]
    site = getattr(getattr(getattr(inputs.model, "plan", None), "project", None), "site", None)
    ground = getattr(site, "ground_snow_load_psf", None)
    design = sorted({round(float(q.value), 2) for r in inputs.records for q in r.inputs
                     if q.name in ("roof_snow", "design_snow")})
    for value in design:
        if ground is not None and abs(value - float(ground)) > 0.01:
            rows.append(["roof beams and piers under the drift", f"design snow {value:g} psf",
                         f"authored (drift case), not derived from p_g {float(ground):g} psf"])
    return rows


def _short(text: str, limit: int = 110) -> str:
    """The first clause of a long owner string, cut at a word."""
    first = re.split(r" — |; ", text)[0]
    if len(first) <= limit:
        return first
    return first[:limit].rsplit(" ", 1)[0] + " …"


def _family_rows(records: Sequence[EngineeringRecord]) -> list[list[Any]]:
    """Screening families share one row; each external family has its own owner."""
    from typehaus.takeoff.calc_family import families, family_filename

    screening: list[str] = []
    rows: list[list[Any]] = []
    for kind, group in families(list(records)).items():
        deferral = DEFERRALS.get(kind)
        if deferral is None:
            screening.append(f"`{kind}`")
            continue
        rows.append([f"`{kind}` ({len(group)})", f"`calcs/{family_filename(kind)}` section 9",
                     _short(deferral.designer)])
    if screening:
        rows.insert(0, [", ".join(screening), "section 9 of each calculation, `calcs/<family>.md`",
                        "the sealing engineer, unless section 9 names another party"])
    return rows


def render_summary(inputs: PackageInputs, previous: PreviousIssue | None) -> str:
    records = inputs.records
    families_n = len({r.kind for r in records})
    top = _top(records)
    rated = [r for r in records if r.ratio is not None]
    high = sum(1 for r in rated if r.ratio >= COST_REVIEW_TRIGGER)  # type: ignore[operator]
    open_rows = [r for r in records if r.status in (Status.INCOMPLETE, Status.NO_CALC,
                                                    Status.OVER)]
    blocks = [
        heading(f"Reviewer's summary — {inputs.house}"),
        f"**Draft, unsealed.** {len(records)} engineered item(s) in {families_n} "
        f"famil{'y' if families_n == 1 else 'ies'}: {state_line(records) or 'none'}. "
        "Read this page to decide whether to read the rest.",
        "**In this package:** the cover (`00-cover.md`), the criteria (`01-...`), the item "
        "register with locations (`02-...`), open items (`03-...`), assumptions (`04-...`), "
        "one calculation per design family (`calcs/`) and the per-member data behind each "
        "schedule (`appendix/`).",
        heading("Criteria", 2),
        table(["Criterion", "Value"], _criteria_rows(inputs)),
        heading("Governing items", 2),
        f"{high} of {len(rated)} items with a ratio are at or above "
        f"{COST_REVIEW_TRIGGER:g}; the ten highest are below. d/c is demand over capacity "
        "(required over achieved for a factor of safety), so over 1.000 is over capacity. "
        + trigger_note(),
        table(["Item", "Governing limit state", "d/c", "Status"],
              [[f"`{r.item_id}`", r.governing.name, ratio_cell(r.governing.ratio),  # type: ignore[union-attr]
                STATE_NAME[r.status]] for r in top]),
        heading("Counts", 2),
        scope_sentence(records),
    ]
    presumed = _input_rows(inputs)
    if presumed:
        blocks += [heading("Presumed, authored and estimated inputs", 2),
                   table(["Item", "Input", "Basis"], presumed)]
    blocks += [heading("What changed since the last issue", 2),
               changes_since(previous, records, inputs.content_hash),
               heading("Open items", 2)]
    if open_rows:
        blocks.append(f"{len(open_rows)} of {len(records)} item(s) are open: "
                      f"`03-open-items.md` names what each needs and who owns it.")
        grouped: dict[str, list[str]] = {}
        for r in open_rows:
            grouped.setdefault(STATE_NAME[r.status], []).append(f"`{r.item_id}`")
        blocks.append(bullets([f"**{state}** — {', '.join(items)}"
                               for state, items in grouped.items()]))
    else:
        blocks.append("None. Every item is computed.")
    blocks += [heading("Not covered, and who owns it", 2),
               "Per family: where its calculation lists what it does not grade.",
               table(["Family", "Where it lists what it does not grade", "Owner"],
                     _family_rows(records))]
    if _owner_snow(inputs):
        blocks += [heading("Not covered — owner", 2), bullets([
            "**Balcony snow.** The decks carry the Minnesota deck basis (40 live + 10 dead, "
            "no snow, no drift). The reason is the owner's: elevated and wind-swept. The "
            "comparison is on `01-design-criteria.md`, section 2."])]
    return document(*blocks)


def _owner_snow(inputs: PackageInputs) -> bool:
    structural = getattr(getattr(inputs, "preferences", None), "structural", None)
    return getattr(structural, "deck_snow_psf", None) is not None
