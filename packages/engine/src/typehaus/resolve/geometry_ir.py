"""The derived-geometry IR: one description of what the building *is*, shaped for emitters.

Four pipelines used to re-derive the same solids from :class:`ResolvedModel` — the IFC
emitter, the glTF emitter, the three.js builders in the UI, and the 2D section cuts — and
they had drifted: the glTF member box ignored ``orient``/``depth_m`` (IFC did not), IFC's
roof layers skipped the eave-drift compensation glTF and the viewer both applied, glTF drew
no earth and no subfloor deck. So what the user saw was not provably what Revit received.

This module is the shared answer. Geometry math happens once, in ``resolve/``, and the
emitters become serializers: IFC still owns entity classes, psets and containment; glTF still
owns buffers and materials; neither owns the shape of a stud.

Conventions
-----------
* **Metres, plan frame**: x/y in plan, z up. glTF's ``(x, z, -y)`` swizzle is an emitter
  detail and does not appear here.
* **Orientation-neutral**: rings and corners are final 3D coordinates. No compass keys, no
  ``"x"``/``"y"`` ridge tokens — the producer *applies* roof edge setbacks and rake, so
  rotating a building later touches ``resolve/`` alone.
* **Stdlib only.** The whole engine runs in Pyodide in the browser, which is exactly how the
  in-browser viewer can emit its own GLB; a dependency here would break that.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union

# A 2D plan-frame ring (x, y), and a true 3D ring — both closed implicitly (no repeated
# first point).
Vec2 = tuple[float, float]
Vec3 = tuple[float, float, float]
Ring = tuple[Vec2, ...]
Ring3 = tuple[Vec3, ...]


@dataclass(frozen=True)
class GPrism:
    """A plan ring extruded from ``z0_m`` to ``z1_m``.

    ``top`` gives per-vertex top elevations for a raked prism (a wall under a sloped
    ceiling, a floor deck following a ramp); ``None`` means a flat top at ``z1_m``. ``voids``
    are plan rings subtracted through the full height — the opening holes in a wall layer.
    """

    ring: Ring
    z0_m: float
    z1_m: float
    top: tuple[float, ...] | None = None
    voids: tuple[Ring, ...] = ()

    def __post_init__(self) -> None:
        if self.top is not None and len(self.top) != len(self.ring):
            raise ValueError(
                f"GPrism.top has {len(self.top)} elevations for {len(self.ring)} vertices"
            )


@dataclass(frozen=True)
class GBox:
    """An eight-corner hexahedron: matching bottom and top rings, vertex for vertex.

    Generalized from :class:`ResolvedSolarPanel`, which already carried exactly this pair.
    One shape covers what used to need three code paths — an upright member with an
    ``orient``ed section, a raked member whose ends sit at different elevations, and a
    tapered band that grows from heel to ridge — because all three are just different
    corners.
    """

    corners_bottom: Ring3
    corners_top: Ring3

    def __post_init__(self) -> None:
        if len(self.corners_bottom) != len(self.corners_top):
            raise ValueError("GBox rings must correspond vertex for vertex")
        if len(self.corners_bottom) < 3:
            raise ValueError("GBox needs at least three corners per ring")


@dataclass(frozen=True)
class GMesh:
    """Pre-tessellated geometry, for shapes no prism or box describes.

    Arch spandrels and curved soffits live here. ``normals`` are carried when they are
    *analytic* rather than facet-derived — an arch soffit reads as a smooth curve only if
    the normals come from the curve, not from the triangles approximating it. ``uvs`` are
    carried for the seam families (standing seam, lap siding) whose material needs to know
    where along the surface it is.
    """

    positions: tuple[Vec3, ...]
    triangles: tuple[tuple[int, int, int], ...]
    normals: tuple[Vec3, ...] | None = None
    uvs: tuple[tuple[float, float], ...] | None = None

    def __post_init__(self) -> None:
        count = len(self.positions)
        if self.normals is not None and len(self.normals) != count:
            raise ValueError("GMesh.normals must be per-position")
        if self.uvs is not None and len(self.uvs) != count:
            raise ValueError("GMesh.uvs must be per-position")
        for tri in self.triangles:
            if any(index >= count for index in tri):
                raise ValueError(f"GMesh triangle {tri} indexes past {count} positions")


# `Union` rather than `X | Y`: this alias is evaluated at import time, and the engine still
# runs on the interpreters the test venv uses.
GSolid = Union[GPrism, GBox, GMesh]


@dataclass(frozen=True)
class GPart:
    """One addressable piece of an element: a layer band, a member, a leaf, a deck.

    The key is what the part *is* within its element (``"layer:gypsum"``, ``"member:stud-007"``,
    ``"leaf"``, ``"glass"``, ``"deck"``) and is stable across builds, so a viewer selection or
    an IFC GUID can hang off it.
    """

    key: str
    solids: tuple[GSolid, ...]
    # A semantic finish key from the shared vocabulary (`emit/finishes.py`, mirrored in
    # `ui/src/three/finishKeys.ts`) — never an RGBA. Python maps it to a flat colour for
    # export; the viewer maps it to a procedural material.
    material_key: str
    # Which band of the assembly this part belongs to, from ALL_LAYER_VISIBILITY_GROUPS.
    # Per-layer visibility rides this.
    layer_group: str | None = None
    # ``"<ownerUid>::<childKey>"`` for framing, so a merged member mesh can resolve a pick
    # back to one stick.
    member_uid: str | None = None


@dataclass(frozen=True)
class ElementGeometry:
    """Every solid one resolved element contributes, grouped into addressable parts."""

    uid: str
    kind: str
    trade: str
    parts: tuple[GPart, ...] = ()


@dataclass(frozen=True)
class GeometryModel:
    """The whole building's derived geometry."""

    elements: tuple[ElementGeometry, ...] = field(default_factory=tuple)

    def by_uid(self, uid: str) -> ElementGeometry | None:
        return next((el for el in self.elements if el.uid == uid), None)

    def of_kind(self, kind: str) -> tuple[ElementGeometry, ...]:
        return tuple(el for el in self.elements if el.kind == kind)
