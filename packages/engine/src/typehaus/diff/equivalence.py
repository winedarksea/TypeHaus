"""Semantic equivalence between two IFC models of the same building (→ 30 WP3.7).

Migration equivalence asks a different question than ``haus diff``: not "what did the
architect change in my file" but "does this rebuilt model still mean what the old one meant".
Identity cannot carry the answer — the two files were written by different tools, with
different GlobalIds, names and modelling conventions — so equivalence is established the only
way it honestly can be: lift both into the neutral semantic vocabulary
(:mod:`typehaus.diff.semantic`), pair occurrences geometrically with the same Hungarian
matcher ``haus diff`` uses, and report *per entity* how far apart the pair is.

Nothing here decides what an acceptable divergence is. A migrated design legitimately moves
on from its reference, so this module measures and the caller (a test, the CLI) declares which
divergences are intended.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from typehaus.diff.matcher import match_elements
from typehaus.diff.model import DiffElem
from typehaus.diff.semantic import COMPARED_CATEGORIES, SemanticEntity, SemanticModel

# Status vocabulary shared by storeys and entities.
STATUS_EQUIVALENT = "equivalent"
STATUS_DIVERGENT = "divergent"
STATUS_ONLY_REFERENCE = "only_in_reference"
STATUS_ONLY_CURRENT = "only_in_current"


@dataclass(frozen=True)
class EquivalenceTolerance:
    """How far apart two occurrences may sit and still mean the same thing.

    Construction-scale, not modelling noise: 2" of placement is a detail decision, a foot is
    a different design. ``framing_fraction`` is relative because framing counts scale with
    the element, so an absolute stud tolerance would be meaningless on a 36' wall.
    """

    placement_m: float = 0.05
    size_m: float = 0.05
    framing_fraction: float = 0.10
    # Pairing cost ceiling for the Hungarian matcher. Far looser than a diff against our own
    # export: across tools the same wall line is expected to have moved and changed depth, and
    # naming it as the corresponding wall is more informative than an add + a delete.
    match_threshold: float = 10.0


@dataclass(frozen=True)
class StoreyEquivalence:
    key: str
    reference_name: str | None
    current_name: str | None
    reference_elevation_m: float | None
    current_elevation_m: float | None
    status: str

    @property
    def elevation_delta_m(self) -> float | None:
        if self.reference_elevation_m is None or self.current_elevation_m is None:
            return None
        return round(self.current_elevation_m - self.reference_elevation_m, 4)

    def as_dict(self) -> dict:
        return {"storey": self.key, "status": self.status,
                "reference_name": self.reference_name, "current_name": self.current_name,
                "reference_elevation_m": self.reference_elevation_m,
                "current_elevation_m": self.current_elevation_m,
                "elevation_delta_m": self.elevation_delta_m}


@dataclass(frozen=True)
class CensusRow:
    """How many runs of one category each side puts on one storey."""

    storey: str
    category: str
    reference: int
    current: int

    @property
    def delta(self) -> int:
        return self.current - self.reference

    def as_dict(self) -> dict:
        return {"storey": self.storey, "category": self.category,
                "reference": self.reference, "current": self.current, "delta": self.delta}


@dataclass(frozen=True)
class EntityEquivalence:
    """One reference occurrence and the current occurrence it means, or the lack of one."""

    category: str
    storey: str
    reference_name: str | None
    current_name: str | None
    status: str
    placement_delta_m: float | None = None
    size_delta_m: tuple[float, float, float] | None = None
    reference_layer_count: int | None = None
    current_layer_count: int | None = None
    reference_framing_count: int | None = None
    current_framing_count: int | None = None
    reasons: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "category": self.category, "storey": self.storey, "status": self.status,
            "reference": self.reference_name, "current": self.current_name,
            "placement_delta_m": (round(self.placement_delta_m, 4)
                                  if self.placement_delta_m is not None else None),
            "size_delta_m": ([round(v, 4) for v in self.size_delta_m]
                             if self.size_delta_m is not None else None),
            "layer_count": [self.reference_layer_count, self.current_layer_count],
            "framing_member_count": [self.reference_framing_count, self.current_framing_count],
            "reasons": list(self.reasons),
        }


@dataclass
class EquivalenceReport:
    """The whole comparison: hierarchy, census, per-entity equivalence, class totals."""

    reference_label: str
    current_label: str
    storeys: list[StoreyEquivalence] = field(default_factory=list)
    census: list[CensusRow] = field(default_factory=list)
    entities: list[EntityEquivalence] = field(default_factory=list)
    class_census: dict[str, tuple[int, int]] = field(default_factory=dict)

    def by_status(self, status: str) -> list[EntityEquivalence]:
        return [item for item in self.entities if item.status == status]

    def status_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self.entities:
            counts[item.status] = counts.get(item.status, 0) + 1
        return counts

    def matched(self) -> list[EntityEquivalence]:
        """Pairs the matcher paired, equivalent or not — the denominator of "how close"."""
        return [item for item in self.entities
                if item.status in (STATUS_EQUIVALENT, STATUS_DIVERGENT)]

    def equivalent_fraction(self, category: str | None = None) -> float:
        rows = [item for item in self.entities
                if category is None or item.category == category]
        if not rows:
            return 0.0
        equivalent = sum(1 for item in rows if item.status == STATUS_EQUIVALENT)
        return equivalent / len(rows)

    def census_row(self, storey: str, category: str) -> CensusRow | None:
        return next((row for row in self.census
                     if row.storey == storey and row.category == category), None)

    def as_dict(self) -> dict:
        return {
            "models": {"reference": self.reference_label, "current": self.current_label},
            "status_counts": self.status_counts(),
            "storeys": [item.as_dict() for item in self.storeys],
            "census": [item.as_dict() for item in self.census],
            "entities": [item.as_dict() for item in self.entities],
            "class_census": {name: list(pair) for name, pair in sorted(self.class_census.items())},
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True)

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())
        return path


def _as_diff_elem(entity: SemanticEntity) -> DiffElem:
    # global_id is deliberately dropped: two tools' GUIDs for the same wall are unrelated, and
    # a keyed match on them would be a coincidence, not evidence.
    return DiffElem(global_id=None, tag=entity.name, ifc_class=entity.category,
                    storey=entity.storey_key, centroid=entity.centroid_m,
                    bbox=entity.size_m, axis_dir=(0.0, 0.0))


def _classify(reference: SemanticEntity, current: SemanticEntity,
              tolerance: EquivalenceTolerance) -> EntityEquivalence:
    placement = sum((a - b) ** 2 for a, b in zip(reference.centroid_m, current.centroid_m)) ** 0.5
    size = tuple(current.size_m[axis] - reference.size_m[axis] for axis in range(3))
    reasons: list[str] = []
    if placement > tolerance.placement_m:
        reasons.append(f"placement {placement:.3f} m apart")
    worst_axis = max(range(3), key=lambda axis: abs(size[axis]))
    if abs(size[worst_axis]) > tolerance.size_m:
        axis_name = ("x", "y", "z")[worst_axis]
        reasons.append(f"{axis_name} extent {size[worst_axis]:+.3f} m")
    if reference.layer_count != current.layer_count:
        reasons.append(f"layers {reference.layer_count} → {current.layer_count}")
    reference_framing = reference.framing_member_count
    current_framing = current.framing_member_count
    if reference_framing or current_framing:
        allowance = max(1.0, tolerance.framing_fraction * max(reference_framing, current_framing))
        if abs(current_framing - reference_framing) > allowance:
            reasons.append(f"framing members {reference_framing} → {current_framing}")
    return EntityEquivalence(
        category=reference.category, storey=reference.storey_key,
        reference_name=reference.name, current_name=current.name,
        status=STATUS_DIVERGENT if reasons else STATUS_EQUIVALENT,
        placement_delta_m=placement, size_delta_m=size,
        reference_layer_count=reference.layer_count,
        current_layer_count=current.layer_count,
        reference_framing_count=reference_framing, current_framing_count=current_framing,
        reasons=tuple(reasons),
    )


def _unpaired(entity: SemanticEntity, status: str) -> EntityEquivalence:
    reference_side = status == STATUS_ONLY_REFERENCE
    return EntityEquivalence(
        category=entity.category, storey=entity.storey_key,
        reference_name=entity.name if reference_side else None,
        current_name=None if reference_side else entity.name,
        status=status,
        reference_layer_count=entity.layer_count if reference_side else None,
        current_layer_count=None if reference_side else entity.layer_count,
        reference_framing_count=entity.framing_member_count if reference_side else None,
        current_framing_count=None if reference_side else entity.framing_member_count,
    )


def compare_semantic_models(reference: SemanticModel, current: SemanticModel,
                            tolerance: EquivalenceTolerance | None = None
                            ) -> EquivalenceReport:
    """Diff two semantic models: spatial hierarchy, census, and per-entity equivalence."""
    tolerance = tolerance or EquivalenceTolerance()
    report = EquivalenceReport(reference_label=reference.label, current_label=current.label)

    reference_storeys = {item.key: item for item in reference.storeys}
    current_storeys = {item.key: item for item in current.storeys}
    for key in sorted(set(reference_storeys) | set(current_storeys)):
        left, right = reference_storeys.get(key), current_storeys.get(key)
        status = (STATUS_ONLY_REFERENCE if right is None else
                  STATUS_ONLY_CURRENT if left is None else STATUS_EQUIVALENT)
        report.storeys.append(StoreyEquivalence(
            key=key,
            reference_name=left.name if left else None,
            current_name=right.name if right else None,
            reference_elevation_m=left.elevation_m if left else None,
            current_elevation_m=right.elevation_m if right else None,
            status=status,
        ))

    reference_census = reference.category_census()
    current_census = current.category_census()
    for key in sorted(set(reference_census) | set(current_census)):
        storey, category = key
        report.census.append(CensusRow(storey=storey, category=category,
                                       reference=reference_census.get(key, 0),
                                       current=current_census.get(key, 0)))

    for category in COMPARED_CATEGORIES:
        left_entities = reference.in_category(category)
        right_entities = current.in_category(category)
        left_elems = [_as_diff_elem(item) for item in left_entities]
        right_elems = [_as_diff_elem(item) for item in right_entities]
        left_by_elem = dict(zip((id(elem) for elem in left_elems), left_entities))
        right_by_elem = dict(zip((id(elem) for elem in right_elems), right_entities))
        for match in match_elements(left_elems, right_elems, tolerance.match_threshold):
            if match.baseline is not None and match.external is not None:
                report.entities.append(_classify(left_by_elem[id(match.baseline)],
                                                 right_by_elem[id(match.external)], tolerance))
            elif match.baseline is not None:
                report.entities.append(_unpaired(left_by_elem[id(match.baseline)],
                                                 STATUS_ONLY_REFERENCE))
            elif match.external is not None:
                report.entities.append(_unpaired(right_by_elem[id(match.external)],
                                                 STATUS_ONLY_CURRENT))

    for name in sorted(set(reference.class_census) | set(current.class_census)):
        report.class_census[name] = (reference.class_census.get(name, 0),
                                     current.class_census.get(name, 0))
    return report
