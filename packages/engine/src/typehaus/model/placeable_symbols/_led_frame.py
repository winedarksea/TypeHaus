"""A product drawn in its datasheet's own units, scaled into the caller's W×D×H.

``u`` runs along the length (local x), ``t`` is thickness measured off the mounting surface
(back at +y, so ``t`` grows toward -y), ``z`` is up. Every feature stays inside the envelope
because every coordinate is a fraction of the sheet's overall size.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, Part, Stroke, box, polygon
from typehaus.model.placeable_symbols._round_hardware import round_cylinder


@dataclass(frozen=True)
class ProductFrame:
    length: float
    thickness: float
    height: float
    width_m: float
    depth_m: float
    height_m: float

    def x(self, u: float) -> float:
        return (u - self.length / 2) * self.width_m / self.length

    def y(self, t: float) -> float:
        return self.depth_m / 2 - t * self.depth_m / self.thickness

    def z(self, z: float) -> float:
        return z * self.height_m / self.height

    def slab(self, u0, u1, t0, t1, z0, z1, color) -> Part:
        x0, x1, y0, y1 = self.x(u0), self.x(u1), self.y(t0), self.y(t1)
        return box((x0 + x1) / 2, (y0 + y1) / 2, self.z(z0), self.z(z1),
                   x1 - x0, y0 - y1, color)

    def cylinder(self, u, t, z, radius, length, axis, color) -> Part:
        """``axis`` 0/1/2 = along u/t/z; ``radius`` takes the tighter of its two scales."""
        scales = (self.width_m / self.length, self.depth_m / self.thickness,
                  self.height_m / self.height)
        radial = min(scale for index, scale in enumerate(scales) if index != axis)
        return round_cylinder((self.x(u), self.y(t), self.z(z)), radius * radial,
                              length * scales[axis], axis=axis, color=color)

    def outline(self, u0, u1, t0, t1, *, fill=None, weight=DETAIL_WEIGHT) -> Stroke:
        x0, x1, y0, y1 = self.x(u0), self.x(u1), self.y(t0), self.y(t1)
        return polygon(((x0, y0), (x1, y0), (x1, y1), (x0, y1)), fill=fill, weight=weight)
