"""DiffElem — the neutral element record both sides of a diff are projected onto (→ 20)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DiffElem:
    """One comparable element: identity + coarse geometry + attributes.

    Both the deterministic baseline (from ``ResolvedModel``) and the external IFC are mapped
    to this shape, so the matcher never touches ifcopenshell or the resolver directly.
    """

    global_id: str | None       # IFC GlobalId (uid-derived on our side); None if unkeyed
    tag: str                    # human tag (baseline only; "" for unknown external elements)
    ifc_class: str              # "IfcWall", "IfcWindow", "IfcDoor", …
    storey: str
    centroid: tuple[float, float, float]  # meters
    bbox: tuple[float, float, float]      # oriented bbox dims (dx, dy, dz), meters
    axis_dir: tuple[float, float]         # unit plan direction, (0,0) if n/a
    attrs: dict[str, str] = field(default_factory=dict)  # authoring-unit attribute strings

    def bbox_distance(self, other: DiffElem) -> float:
        return sum(abs(a - b) for a, b in zip(self.bbox, other.bbox))

    def centroid_distance(self, other: DiffElem) -> float:
        return sum((a - b) ** 2 for a, b in zip(self.centroid, other.centroid)) ** 0.5
