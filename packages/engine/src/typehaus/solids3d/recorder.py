"""Placeables as true solids, through the glTF emitter's own drawing code.

``SolidRecorder`` takes the five ``_MeshBuilder`` calls ``emit/gltf/canvas_objects.py``
makes, so a placeable converts with no second copy of its symbol logic. Each call is kept
as one IR solid with its colour and its explicit dimensions: the smallest dimension is the
feature a printer has to resolve, read exactly rather than measured off a mesh.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from shapely.geometry import Polygon

from typehaus.emit.gltf.canvas_objects import CanvasDrawContext, draw_canvas_object
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.resolve.geometry_ir import GMesh, GPrism, GSolid
from typehaus.resolve.model import ResolvedCanvasObject, ResolvedModel

Color = tuple[float, float, float, float]


@dataclass(frozen=True)
class Primitive:
    solid: GSolid
    color: Color
    #: The primitive's own extents (plan width, plan length, height), smallest first.
    dims_m: tuple[float, float, float]

    @property
    def min_feature_m(self) -> float:
        return self.dims_m[0]


class SolidRecorder:
    """A ``_MeshBuilder`` stand-in that keeps solids instead of triangles."""

    def __init__(self) -> None:
        self.primitives: list[Primitive] = []

    def is_empty(self) -> bool:
        return not self.primitives

    def add_prism(self, ring, z0: float, z1: float, color: Color) -> None:
        self.add_prism_with_rectangular_voids(ring, (), z0, z1, color)

    def add_prism_with_rectangular_voids(self, ring, voids: Sequence, z0: float, z1: float,
                                         color: Color) -> None:
        ring = tuple((float(x), float(y)) for x, y in ring)
        if len(ring) < 3 or z1 <= z0:
            return
        solid = GPrism(ring=ring, z0_m=z0, z1_m=z1,
                       voids=tuple(tuple((float(x), float(y)) for x, y in void)
                                   for void in voids))
        self.primitives.append(Primitive(solid, color, _sorted((*_plan_extents(ring),
                                                                z1 - z0))))

    def add_mesh(self, mesh: GMesh, color: Color) -> None:
        if mesh.triangles:
            self.primitives.append(Primitive(mesh, color, _sorted(_bbox_extents(mesh.positions))))

    def add_triangles(self, triangles, color: Color) -> None:
        """Triangles arrive in glTF's (x, z, -y) frame; they go back to plan (x, y, z)."""
        index: dict[tuple[float, float, float], int] = {}
        faces = []
        for triangle in triangles:
            face = []
            for gx, gy, gz in triangle:
                point = (gx, -gz, gy)
                face.append(index.setdefault(point, len(index)))
            faces.append(tuple(face))
        if faces:
            self.add_mesh(GMesh(positions=tuple(index), triangles=tuple(faces)), color)

    def add_plan_depth_cylinder(self, center, radius: float, length: float, axis, color: Color,
                                segments: int | None = None) -> None:
        # The emitter's own cylinder, which reaches the recorder through add_triangles.
        extra = {} if segments is None else {"segments": segments}
        _MeshBuilder.add_plan_depth_cylinder(self, center, radius, length, axis, color, **extra)


def placeable_primitives(item: ResolvedCanvasObject, context: CanvasDrawContext,
                         ) -> list[Primitive]:
    recorder = SolidRecorder()
    draw_canvas_object(recorder, item, context)
    return recorder.primitives


def drawn_placeables(model: ResolvedModel) -> list[tuple[ResolvedCanvasObject, list[Primitive]]]:
    """Every canvas object the glTF emitter draws, with its primitives."""
    context = CanvasDrawContext.of(model)
    return [(item, placeable_primitives(item, context))
            for item in sorted(model.canvas_objects, key=lambda co: co.uid)
            if item.domain != "opening"]


def _plan_extents(ring) -> tuple[float, float]:
    with np.errstate(divide="ignore", invalid="ignore"):  # a ring with a repeated vertex
        rectangle = Polygon(ring).minimum_rotated_rectangle
    if rectangle.geom_type != "Polygon":
        return (0.0, 0.0)
    (ax, ay), (bx, by), (cx, cy) = list(rectangle.exterior.coords)[:3]
    return (((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5, ((cx - bx) ** 2 + (cy - by) ** 2) ** 0.5)


def _bbox_extents(points) -> tuple[float, float, float]:
    return tuple(max(p[i] for p in points) - min(p[i] for p in points) for i in range(3))


def _sorted(values) -> tuple[float, float, float]:
    return tuple(sorted(float(value) for value in values))
