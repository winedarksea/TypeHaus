"""Semantic diff / architect round-trip (→ 20 §Diff).

``haus diff <external.ifc>`` compares an architect-modified IFC against the deterministic
baseline rebuilt from source: GlobalId match, Hungarian fallback for unkeyed elements,
replace detection, and classification into added/deleted/replaced/moved/resized/attr-changed
with deltas in authoring units. The matcher works on plain :class:`DiffElem` records so it is
testable without ifcopenshell; the IFC adapter is the thin, optional edge.
"""

from __future__ import annotations

from typehaus.diff.assembly_compare import AssemblyComparison, MetricDelta, compare_assemblies
from typehaus.diff.compare import (
                                            CheckDelta,
                                            CompareReport,
                                            EnvelopeDelta,
                                            QuantityDelta,
                                            VariantSelection,
                                            apply_assembly_swaps,
                                            check_deltas,
                                            compare_models,
                                            compare_variants,
                                            envelope_deltas,
                                            quantity_deltas,
                                            resolve_variant,
                                            variant_plan,
)
from typehaus.diff.equivalence import EntityEquivalence, EquivalenceReport, compare_semantic_models
from typehaus.diff.matcher import Match, match_elements
from typehaus.diff.model import DiffElem
from typehaus.diff.report import ChangeKind, DiffReport, build_report
from typehaus.diff.semantic import (
                                            AmbiguousStoreyDatum,
                                            SemanticEntity,
                                            SemanticModel,
                                            SemanticStorey,
                                            pick_datum_storey,
                                            semantic_model_from_ifc,
)
from typehaus.diff.variants import (
                                            LayerThicknessOverride,
                                            VariantSpec,
                                            apply_layer_thickness,
                                            find_variant,
                                            load_variants,
)

__all__ = [
    "DiffElem", "Match", "match_elements",
    "ChangeKind", "DiffReport", "build_report",
    "CheckDelta", "CompareReport", "EnvelopeDelta", "QuantityDelta", "VariantSelection",
    "apply_assembly_swaps", "check_deltas", "compare_models", "compare_variants",
    "envelope_deltas", "quantity_deltas", "resolve_variant", "variant_plan",
    "AssemblyComparison", "MetricDelta", "compare_assemblies",
    "LayerThicknessOverride", "VariantSpec", "apply_layer_thickness", "find_variant",
    "load_variants",
    "AmbiguousStoreyDatum", "SemanticEntity", "SemanticModel", "SemanticStorey",
    "pick_datum_storey", "semantic_model_from_ifc",
    "EquivalenceReport", "EntityEquivalence", "compare_semantic_models",
]
