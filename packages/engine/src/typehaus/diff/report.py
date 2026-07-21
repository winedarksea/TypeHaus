"""Diff classification → change list + diff.json + human table (→ 20 §Diff step 4)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path

from typehaus.diff.matcher import Match, match_elements
from typehaus.diff.model import DiffElem
from typehaus.quantities.length import Length

_MOVE_TOL_M = 0.02   # ~3/4"
_SIZE_TOL_M = 0.01
_REPLACE_BBOX_TOL_M = 0.15


class ChangeKind(str, Enum):
    UNCHANGED = "unchanged"
    ADDED = "added"
    DELETED = "deleted"
    REPLACED = "replaced"
    MOVED = "moved"
    ROTATED = "rotated"
    REHOSTED = "rehosted"
    RESIZED = "resized"
    ATTR_CHANGED = "attr-changed"


@dataclass
class Change:
    kind: ChangeKind
    tag: str
    ifc_class: str
    delta: str
    confidence: float = 1.0
    was_tag: str | None = None  # replaced (was W-101)


@dataclass
class DiffReport:
    changes: list[Change] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for c in self.changes:
            out[c.kind.value] = out.get(c.kind.value, 0) + 1
        return out

    def substantive(self) -> list[Change]:
        return [c for c in self.changes if c.kind is not ChangeKind.UNCHANGED]

    def to_json(self) -> str:
        return json.dumps(
            {"counts": self.counts(),
             "changes": [asdict(c) | {"kind": c.kind.value} for c in self.substantive()]},
            indent=2, sort_keys=True,
        )

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())
        return path


def build_report(baseline: list[DiffElem], external: list[DiffElem]) -> DiffReport:
    matches = match_elements(baseline, external)
    report = DiffReport()
    deleted: list[DiffElem] = []
    added: list[DiffElem] = []

    for m in matches:
        if m.baseline is not None and m.external is not None:
            report.changes.append(_classify_pair(m))
        elif m.baseline is not None:
            deleted.append(m.baseline)
        elif m.external is not None:
            added.append(m.external)

    _detect_replacements(report, deleted, added)
    return report


def _classify_pair(m: Match) -> Change:
    b, e = m.baseline, m.external
    assert b is not None and e is not None
    conf = 1.0 if m.keyed else max(0.5, 1.0 - m.cost / 10.0)
    move = b.centroid_distance(e)
    size = b.bbox_distance(e)
    # An unkeyed geometric match in a near-identical bbox is a regenerated element (a tool
    # dropped the GUID): report it as replaced (was TAG), not a coincidental attr change.
    if not m.keyed and move <= _MOVE_TOL_M and size <= _SIZE_TOL_M:
        return Change(ChangeKind.REPLACED, e.tag or b.tag, b.ifc_class,
                      _attr_delta(b, e) or "regenerated (new GUID)", conf, was_tag=b.tag)
    if move > _MOVE_TOL_M:
        return Change(ChangeKind.MOVED, b.tag or e.tag, b.ifc_class,
                      _move_delta(b, e), conf)
    if size > _SIZE_TOL_M:
        return Change(ChangeKind.RESIZED, b.tag or e.tag, b.ifc_class,
                      _size_delta(b, e), conf)
    if b.attrs.get("host_wall") != e.attrs.get("host_wall"):
        return Change(ChangeKind.REHOSTED, b.tag or e.tag, b.ifc_class, _attr_delta(b, e), conf)
    if b.attrs.get("rotation_degrees") != e.attrs.get("rotation_degrees"):
        return Change(ChangeKind.ROTATED, b.tag or e.tag, b.ifc_class, _attr_delta(b, e), conf)
    attr_delta = _attr_delta(b, e)
    if attr_delta:
        return Change(ChangeKind.ATTR_CHANGED, b.tag or e.tag, b.ifc_class, attr_delta, conf)
    return Change(ChangeKind.UNCHANGED, b.tag or e.tag, b.ifc_class, "", conf)


def _detect_replacements(
    report: DiffReport, deleted: list[DiffElem], added: list[DiffElem]
) -> None:
    """Same-class delete+add in a near-identical bbox reports as replaced (was TAG)."""
    used_add: set[int] = set()
    for d in deleted:
        best: tuple[float, DiffElem] | None = None
        for a in added:
            if id(a) in used_add or a.ifc_class != d.ifc_class:
                continue
            dist = d.bbox_distance(a) + d.centroid_distance(a)
            if dist <= _REPLACE_BBOX_TOL_M and (best is None or dist < best[0]):
                best = (dist, a)
        if best is not None:
            a = best[1]
            used_add.add(id(a))
            report.changes.append(Change(
                ChangeKind.REPLACED, a.tag or d.tag, d.ifc_class,
                _attr_delta(d, a) or "regenerated", confidence=0.7, was_tag=d.tag,
            ))
        else:
            report.changes.append(Change(ChangeKind.DELETED, d.tag, d.ifc_class, ""))
    for a in added:
        if id(a) not in used_add:
            report.changes.append(Change(ChangeKind.ADDED, a.tag or "?", a.ifc_class, ""))


def _bearing(dx: float, dy: float) -> str:
    if abs(dy) >= abs(dx):
        return "north" if dy > 0 else "south"
    return "east" if dx > 0 else "west"


def _move_delta(b: DiffElem, e: DiffElem) -> str:
    dx = e.centroid[0] - b.centroid[0]
    dy = e.centroid[1] - b.centroid[1]
    dist = (dx * dx + dy * dy) ** 0.5
    return f"moved {Length(dist, *_ft_args(dist)).fmt()} {_bearing(dx, dy)}"


def _size_delta(b: DiffElem, e: DiffElem) -> str:
    changed = max(range(3), key=lambda i: abs(e.bbox[i] - b.bbox[i]))
    to = e.bbox[changed]
    axis = "width" if changed == 0 else ("depth" if changed == 1 else "height")
    return f"{axis} changed to {Length(to, *_ft_args(to)).fmt()}"


def _attr_delta(b: DiffElem, e: DiffElem) -> str:
    parts = []
    for k in sorted(set(b.attrs) | set(e.attrs)):
        if b.attrs.get(k) != e.attrs.get(k):
            parts.append(f"{k}: {b.attrs.get(k, '∅')} → {e.attrs.get(k, '∅')}")
    return "; ".join(parts)


def _ft_args(meters: float) -> tuple:
    from typehaus.quantities.length import AuthoredUnit

    feet = meters / 0.3048
    return (AuthoredUnit.FT_IN, (int(feet), 0.0))
