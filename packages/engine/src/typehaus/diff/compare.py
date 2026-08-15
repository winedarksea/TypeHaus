"""Compare two variants of the same design (→ 20 §Diff, first-class variant compare).

``haus diff`` reconciles the deterministic baseline against an *external* IFC. This module
is the internal twin: it diffs two resolved TypeHaus models against each other — two named
plan variants (two house directories) or the same plan resolved with a different assembly
selection (an assembly swap). It reuses the very same matcher/report machinery; the only new
edge is projecting a second in-memory model onto :class:`DiffElem` (already provided by
``ifc_adapter.baseline_elems``) and rolling up a quantity delta from the framing takeoff.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from typehaus.diff._json_report import JsonReport
from typehaus.diff.ifc_adapter import baseline_elems
from typehaus.diff.report import DiffReport, build_report
from typehaus.diff.variants import LayerThicknessOverride, apply_layer_thickness

if TYPE_CHECKING:
    from typehaus.findings import Finding
    from typehaus.model.plan import PlanModel
    from typehaus.resolve.model import ResolvedModel


@dataclass(frozen=True)
class VariantSelection:
    """A vibe-code-friendly pointer to one resolvable variant of a design.

    The simplest selection is just a house directory. To compare the *same* plan under a
    different assembly selection, add ``swaps`` mapping an authored assembly tag to the tag
    that should replace it on every wall before resolve (e.g. ``{"CATLIN_EXT_2X6":
    "CATLIN_EXT_2X4"}``), and/or ``layer_thickness`` overrides retuning one layer of one
    assembly. Both are the override vocabulary a declared ``variants.toml`` entry carries
    (→ :mod:`typehaus.diff.variants`).
    """

    house: Path
    swaps: dict[str, str] = field(default_factory=dict)
    label: str | None = None
    layer_thickness: tuple[LayerThicknessOverride, ...] = ()

    def resolved_label(self) -> str:
        if self.label:
            return self.label
        base = Path(self.house).name or str(self.house)
        notes = [f"{old}->{new}" for old, new in sorted(self.swaps.items())]
        notes += [item.label() for item in self.layer_thickness]
        return f"{base} [{','.join(notes)}]" if notes else base


@dataclass
class QuantityDelta:
    """One changed framing-takeoff quantity between two variants (baseline → variant)."""

    profile: str            # lumber size, e.g. "2x6"
    metric: str             # "pieces" | "order_length_ft" | "board_feet"
    baseline: float
    variant: float

    @property
    def delta(self) -> float:
        return round(self.variant - self.baseline, 3)


@dataclass
class EnvelopeDelta:
    """One changed envelope metric of one assembly used by either variant's walls.

    ``None`` on a side is never a fabricated zero. ``note`` says which kind of None it is:
    the assembly is simply not used by that variant, or its R-value is UNKNOWN for want of a
    material number (#32).
    """

    assembly: str
    metric: str             # "r_value" | "thickness_in"
    baseline: float | None
    variant: float | None
    note: str = ""

    @property
    def delta(self) -> float | None:
        if self.baseline is None or self.variant is None:
            return None
        return round(self.variant - self.baseline, 3)


@dataclass
class CheckDelta:
    """One check whose result moved between the variants (absent on a side => None)."""

    check_id: str
    element_tags: str
    baseline: str | None    # "pass" | "fail" | "unknown" | None (no such finding)
    variant: str | None


@dataclass
class CompareReport(JsonReport):
    """Semantic element diff + quantity, envelope and check deltas between two variants."""

    label_a: str
    label_b: str
    diff: DiffReport
    quantity_deltas: list[QuantityDelta] = field(default_factory=list)
    envelope_deltas: list[EnvelopeDelta] = field(default_factory=list)
    check_deltas: list[CheckDelta] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True)

    def as_dict(self) -> dict:
        return {
            "variants": {"a": self.label_a, "b": self.label_b},
            "element_counts": self.diff.counts(),
            "element_changes": [asdict(c) | {"kind": c.kind.value}
                                for c in self.diff.substantive()],
            "quantity_deltas": [asdict(q) | {"delta": q.delta}
                                for q in self.quantity_deltas],
            "envelope_deltas": [asdict(e) | {"delta": e.delta}
                                for e in self.envelope_deltas],
            "check_deltas": [asdict(c) for c in self.check_deltas],
        }


def apply_assembly_swaps(plan: "PlanModel", swaps: dict[str, str]) -> "PlanModel":
    """Return a copy of ``plan`` with every element's assembly remapped per ``swaps``.

    Any element that references an assembly tag directly (walls, foundation walls, …) is a
    pure, localized rewrite target; unmatched elements are left untouched. Selecting a variant
    is therefore just naming the swap, e.g. ``{"CATLIN_EXT_2X6": "CATLIN_EXT_2X4"}``.

    The replacement must be an assembly the plan's library actually carries. Swapping to a tag
    the plan cannot resolve does not produce a thinner wall — it produces *no* wall, and a
    compare against that reads as "the variant deleted the whole envelope", which is exactly
    the silent nonsense a variant tool must never report.
    """
    if not swaps:
        return plan
    missing = sorted(tag for tag in set(swaps.values())
                     if plan.library.resolve_assembly(tag) is None)
    if missing:
        raise ValueError(
            "assembly swap names assemblies this plan's library does not carry: "
            f"{', '.join(missing)} — add them to plan/assemblies.py first")
    result = plan
    for storey in plan.storeys:
        elements = plan.storey_elements(storey.tag)
        changed = False
        rebuilt = []
        for element in elements:
            new_tag = swaps.get(getattr(element, "assembly", None))
            if new_tag is not None:
                rebuilt.append(element.model_copy(update={"assembly": new_tag}))
                changed = True
            else:
                rebuilt.append(element)
        if changed:
            result = result.with_elements(storey.tag, rebuilt)
    return result


def variant_plan(selection: VariantSelection) -> "PlanModel":
    """Load the base plan and apply this variant's overrides — the one build entry point."""
    from typehaus.source import load_plan

    loaded = load_plan(Path(selection.house))
    if loaded.plan is None:
        raise ValueError(
            f"cannot load plan for {selection.resolved_label()}: "
            + "; ".join(f.render() for f in loaded.findings)
        )
    plan = apply_assembly_swaps(loaded.plan, selection.swaps)
    return apply_layer_thickness(plan, selection.layer_thickness)


def resolve_variant(selection: VariantSelection) -> tuple["ResolvedModel", list["Finding"]]:
    """Load, apply this variant's overrides, and resolve it into a model."""
    from typehaus.resolve import resolve

    return resolve(variant_plan(selection))


def quantity_deltas(model_a: "ResolvedModel", model_b: "ResolvedModel") -> list[QuantityDelta]:
    """Roll the framing takeoff of both variants up by size and report every changed metric."""
    from typehaus.takeoff import framing_bom_by_size

    def _rows(model: "ResolvedModel") -> dict[str, dict]:
        return {str(row["profile"]): row for row in framing_bom_by_size(model)}

    rows_a, rows_b = _rows(model_a), _rows(model_b)
    deltas: list[QuantityDelta] = []
    for profile in sorted(set(rows_a) | set(rows_b)):
        ra, rb = rows_a.get(profile), rows_b.get(profile)
        for metric in ("pieces", "order_length_ft", "board_feet"):
            va = _num(ra.get(metric)) if ra else 0.0
            vb = _num(rb.get(metric)) if rb else 0.0
            if va != vb:
                deltas.append(QuantityDelta(profile, metric, va, vb))
    return deltas


def _num(value: object) -> float:
    return float(value) if isinstance(value, (int, float)) else 0.0


def envelope_deltas(model_a: "ResolvedModel", model_b: "ResolvedModel") -> list[EnvelopeDelta]:
    """Compare the R-value and built thickness of every wall assembly either variant uses.

    This is the "variant B: +R7, +1½″ of wall" row of the compare view (→ 21b). Each side is
    measured through its own library, so a layer-thickness override shows up as the same
    assembly tag with different numbers.
    """
    from typehaus.analysis import assembly_metrics

    def _metrics(model: "ResolvedModel") -> dict[str, object]:
        library = model.plan.library
        used = {wall.assembly for wall in model.walls if wall.assembly}
        resolved = {tag: library.resolve_assembly(tag) for tag in used}
        return {tag: assembly_metrics(asm, library)
                for tag, asm in resolved.items() if asm is not None}

    metrics_a, metrics_b = _metrics(model_a), _metrics(model_b)
    deltas: list[EnvelopeDelta] = []
    for tag in sorted(set(metrics_a) | set(metrics_b)):
        one, two = metrics_a.get(tag), metrics_b.get(tag)
        note = ("unused in A" if one is None else
                "unused in B" if two is None else "")
        for metric, reader in (
            ("r_value", lambda m: round(m.r_value.value.r_us, 3) if m.r_value.known else None),
            ("thickness_in", lambda m: round(m.thickness_in, 3)),
        ):
            left = reader(one) if one is not None else None
            right = reader(two) if two is not None else None
            if left != right:
                unknown = (one is not None and left is None) or (two is not None
                                                                 and right is None)
                deltas.append(EnvelopeDelta(
                    tag, metric, left, right,
                    note or ("UNKNOWN — missing material data" if unknown else "")))
    return deltas


def check_deltas(model_a: "ResolvedModel", findings_a: list["Finding"], house_a: Path,
                 model_b: "ResolvedModel", findings_b: list["Finding"],
                 house_b: Path) -> list[CheckDelta]:
    """Run each variant's checks and report every rule whose result moved.

    A variant is only worth promoting if it is at least as compliant as what it replaces, so
    the compare view answers that directly rather than making the user re-run ``haus check``
    on both. Findings are keyed by (check id, elements) — the same rule against the same
    elements — so a changed *number* inside one message is not reported as a new finding.
    """
    from typehaus.checks import run_from_model

    def _results(model, findings, house) -> dict[tuple[str, str], str]:
        report = run_from_model(model, findings, Path(house))
        return {(finding.check_id, ";".join(finding.element_tags)): finding.result.value
                for finding in report.findings}

    results_a = _results(model_a, findings_a, house_a)
    results_b = _results(model_b, findings_b, house_b)
    return [CheckDelta(check_id=key[0], element_tags=key[1],
                       baseline=results_a.get(key), variant=results_b.get(key))
            for key in sorted(set(results_a) | set(results_b))
            if results_a.get(key) != results_b.get(key)]


def compare_models(model_a: "ResolvedModel", model_b: "ResolvedModel",
                   label_a: str = "A", label_b: str = "B") -> CompareReport:
    """Diff two resolved models. Reuses the external-diff matcher via ``baseline_elems``.

    Both sides are projected onto the same neutral :class:`DiffElem` vocabulary the external
    IFC diff uses, so element changes (added/removed/moved/resized/attr-changed) come straight
    from ``build_report``; quantity deltas come from the framing takeoff rollup and envelope
    deltas from the assembly rollup. Check deltas need each variant's house directory (for its
    preferences and code profile) and are added by :func:`compare_variants`.
    """
    diff = build_report(baseline_elems(model_a), baseline_elems(model_b))
    return CompareReport(label_a, label_b, diff, quantity_deltas(model_a, model_b),
                         envelope_deltas(model_a, model_b))


def compare_variants(selection_a: VariantSelection, selection_b: VariantSelection,
                     include_checks: bool = True) -> CompareReport:
    """Resolve both variant selections and compare them (the one-call convenience entry)."""
    model_a, findings_a = resolve_variant(selection_a)
    model_b, findings_b = resolve_variant(selection_b)
    report = compare_models(model_a, model_b,
                            selection_a.resolved_label(), selection_b.resolved_label())
    if include_checks:
        report.check_deltas = check_deltas(model_a, findings_a, Path(selection_a.house),
                                           model_b, findings_b, Path(selection_b.house))
    return report
