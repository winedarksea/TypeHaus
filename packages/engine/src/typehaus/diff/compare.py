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

from typehaus.diff.ifc_adapter import baseline_elems
from typehaus.diff.report import DiffReport, build_report

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
    "CATLIN_EXT_2X4"}``).
    """

    house: Path
    swaps: dict[str, str] = field(default_factory=dict)
    label: str | None = None

    def resolved_label(self) -> str:
        if self.label:
            return self.label
        base = Path(self.house).name or str(self.house)
        if self.swaps:
            swap_note = ",".join(f"{old}->{new}" for old, new in sorted(self.swaps.items()))
            return f"{base} [{swap_note}]"
        return base


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
class CompareReport:
    """Semantic element diff + quantity delta between two variants of one design."""

    label_a: str
    label_b: str
    diff: DiffReport
    quantity_deltas: list[QuantityDelta] = field(default_factory=list)

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
        }

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())
        return path


def apply_assembly_swaps(plan: "PlanModel", swaps: dict[str, str]) -> "PlanModel":
    """Return a copy of ``plan`` with every element's assembly remapped per ``swaps``.

    Any element that references an assembly tag directly (walls, foundation walls, …) is a
    pure, localized rewrite target; unmatched elements are left untouched. Selecting a variant
    is therefore just naming the swap, e.g. ``{"CATLIN_EXT_2X6": "CATLIN_EXT_2X4"}``.
    """
    if not swaps:
        return plan
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


def resolve_variant(selection: VariantSelection) -> tuple["ResolvedModel", list["Finding"]]:
    """Load, optionally swap assemblies, and resolve one variant into a model."""
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    loaded = load_plan(Path(selection.house))
    if loaded.plan is None:
        raise ValueError(
            f"cannot load plan for {selection.resolved_label()}: "
            + "; ".join(f.render() for f in loaded.findings)
        )
    plan = apply_assembly_swaps(loaded.plan, selection.swaps)
    return resolve(plan)


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


def compare_models(model_a: "ResolvedModel", model_b: "ResolvedModel",
                   label_a: str = "A", label_b: str = "B") -> CompareReport:
    """Diff two resolved models. Reuses the external-diff matcher via ``baseline_elems``.

    Both sides are projected onto the same neutral :class:`DiffElem` vocabulary the external
    IFC diff uses, so element changes (added/removed/moved/resized/attr-changed) come straight
    from ``build_report``; quantity deltas come from the framing takeoff rollup.
    """
    diff = build_report(baseline_elems(model_a), baseline_elems(model_b))
    return CompareReport(label_a, label_b, diff, quantity_deltas(model_a, model_b))


def compare_variants(selection_a: VariantSelection,
                     selection_b: VariantSelection) -> CompareReport:
    """Resolve both variant selections and compare them (the one-call convenience entry)."""
    model_a, _ = resolve_variant(selection_a)
    model_b, _ = resolve_variant(selection_b)
    return compare_models(model_a, model_b,
                          selection_a.resolved_label(), selection_b.resolved_label())
