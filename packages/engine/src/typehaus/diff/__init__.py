"""Semantic diff / architect round-trip (→ 20 §Diff).

``haus diff <external.ifc>`` compares an architect-modified IFC against the deterministic
baseline rebuilt from source: GlobalId match, Hungarian fallback for unkeyed elements,
replace detection, and classification into added/deleted/replaced/moved/resized/attr-changed
with deltas in authoring units. The matcher works on plain :class:`DiffElem` records so it is
testable without ifcopenshell; the IFC adapter is the thin, optional edge.
"""

from __future__ import annotations

from typehaus.diff.compare import (CompareReport, QuantityDelta, VariantSelection,
                                   apply_assembly_swaps, compare_models, compare_variants,
                                   quantity_deltas, resolve_variant)
from typehaus.diff.matcher import Match, match_elements
from typehaus.diff.model import DiffElem
from typehaus.diff.report import ChangeKind, DiffReport, build_report

__all__ = [
    "DiffElem", "Match", "match_elements",
    "ChangeKind", "DiffReport", "build_report",
    "CompareReport", "QuantityDelta", "VariantSelection",
    "apply_assembly_swaps", "compare_models", "compare_variants",
    "quantity_deltas", "resolve_variant",
]
