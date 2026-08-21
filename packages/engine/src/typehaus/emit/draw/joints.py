"""Joint resolution — per-layer terminations + treatment geometry at a transition (→ 11b).

A junction detail is a live section cut. Where a wall's skin stops is **not** decided here —
``resolve/roof_edge.py`` has already built the answer as real per-layer closure members,
positioned by ``roof_edge_geometry.mating_faces`` and ``roof_height_at``, and the section
slices them like any other geometry. This module used to invent a second answer (a
``_WEDGE_GAP_M`` of 0.05 m, a ``_DRIP_M`` of 0.04, and its own transcription of the roof
plane), and the drawing believed the wrong one: the wall's continuous insulation was
terminated below its own plate and the spray-foam wedge landed inside the wall.

So the default joint plan is **empty**. ``terminations`` survives for ``_apply_authored_join``
alone, because an authored ``LayerJoin`` on a matched ``Transition`` is a genuine
drawing-only override of what the model says. What remains derived is the treatment fill —
the spray-foam wedge — and its three bounds are read off the geometry rather than off a
convention.

Engine-internal IR (plain dataclasses, never serialized as source), consumed by the cutter.
Section coordinates: ``u`` = world x (cut_direction "x") or world y ("y"); ``z`` = world z.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from typehaus.emit.draw.scene import Hatch, IRNode, Polyline
from typehaus.model.patterns import matches
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_slice import CutPlane, ring_cut_intervals, slice_part
from typehaus.resolve.model import ResolvedModel, ResolvedRoof, ResolvedWall
from typehaus.resolve.roof_geometry import roof_height_at


@dataclass(frozen=True)
class TerminationPlane:
    """A layer's termination (top) elevation in section (u, z): ``z0 + slope*(u - u0)``."""

    u0: float
    z0: float
    slope: float = 0.0

    def z(self, u: float) -> float:
        return self.z0 + self.slope * (u - self.u0)


@dataclass
class JointPlan:
    """Per (element uid, layer name) termination planes + treatment scene nodes."""

    terminations: dict[tuple[str, str], TerminationPlane] = field(default_factory=dict)
    treatments: list[IRNode] = field(default_factory=list)

    def termination(self, uid: str, layer: str) -> TerminationPlane | None:
        return self.terminations.get((uid, layer))


def build_joint_plan(model: ResolvedModel, condition, transition,
                     direction: str, station: float) -> JointPlan:
    """Derive the joint plan for one bound (condition, transition) at a section cut.

    Default joins by layer function/control at a wall↔roof junction; authored ``LayerJoin``
    entries override by glob. Other junction kinds currently contribute authored joins only.
    """
    plan = JointPlan()
    wall = _representative_wall(model, condition)
    roof = _representative_roof(model, condition)

    if wall is not None and roof is not None:
        _spray_foam_wedge(plan, model, wall, roof, direction, station)

    # Authored overrides (LayerJoin) — glob over layer name/function on the wall's side.
    if wall is not None and transition is not None:
        for join in getattr(transition, "joins", ()):
            _apply_authored_join(plan, wall, join, direction, station)
    return plan


def _representative_wall(model, condition) -> ResolvedWall | None:
    for tag in getattr(condition, "element_tags", ()):
        w = model.wall(tag)
        if w is not None:
            return w
    return None


def _representative_roof(model, condition) -> ResolvedRoof | None:
    tags = set(getattr(condition, "element_tags", ()))
    return next((r for r in model.roofs if r.tag in tags), None)


def _spray_foam_wedge(plan: JointPlan, model, wall: ResolvedWall, roof: ResolvedRoof,
                      direction: str, station: float) -> None:
    """Fill the angled mismatch between the roof's foam and the wall's.

    Catlin's eave note asks for exactly this: *"leave the angled mismatch between roof foam
    and wall foam; fill with closed-cell spray polyurethane foam."* Sprayed foam is the one
    thing at this junction with no solid anywhere in the model, so it is genuinely 2D-only
    linework — but its bounds are not, and they are what the old version got wrong.

    ``roof_edge`` carries each wall skin layer up to *its own* face in the roof stack, at
    that layer's own plan offset. The roof plane falls as it runs outboard, so the closure
    bands' tops step down while the plane between them slopes: the void is the sawtooth
    between the two. That is the mismatch, and it is a consequence of the resolver's own
    geometry rather than of a convention.

    The old version invented a 2" gap under a "roof underside" it computed by summing the
    *whole* assembly, which on catlin's 19.86"-deep nailbase roof put that plane 8" below
    the top plate — and the wedge with it, inside the wall, under the plate.
    """
    bands = _closure_band_tops(model, roof, wall,
                               CutPlane(axis=direction, station_m=station), "insulation")
    foam_plane = _roof_foam_underside(model, roof, direction, station)
    if not bands or foam_plane is None:
        return
    for index, polygon in enumerate(_mismatch_polygons(sorted(bands), foam_plane)):
        points = tuple((u / M_PER_IN, z / M_PER_IN) for (u, z) in polygon)
        plan.treatments.append(
            Hatch(boundary=points, pattern="spray-foam", layer="A-DETL-TRMT",
                  uid=f"trmt:{wall.uid}:wedge-{index}"))
        plan.treatments.append(
            Polyline(points=points, layer="A-DETL-TRMT", closed=True, lineweight=0.18,
                     tag="spray-foam-wedge"))


def _mismatch_polygons(bands, foam_plane):
    """The void over each closure band: where the sloping foam plane runs above its flat top.

    Each band was carried up to the plane evaluated at *its own* plan offset, so its square
    top sits on the plane at its midpoint and the plane runs above it over one half and below
    it over the other. The half below is where the wall foam is trimmed; the half above is
    the void, and it is what gets sprayed. A band that already meets the plane along its
    whole width contributes nothing.
    """
    for (u0, u1, z) in bands:
        z0, z1 = foam_plane(u0), foam_plane(u1)
        above0, above1 = z0 > z + 1e-9, z1 > z + 1e-9
        if not above0 and not above1:
            continue
        if above0 and above1:
            yield ((u0, z), (u1, z), (u1, z1), (u0, z0))
            continue
        crossing = u0 + (z - z0) / (z1 - z0) * (u1 - u0)
        yield (((u0, z), (crossing, z), (u0, z0)) if above0
               else ((crossing, z), (u1, z), (u1, z1)))


def _roof_foam_underside(model, roof: ResolvedRoof, direction: str, station: float):
    """``u -> z`` of the plane the wall's insulation dies into: the roof foam's underside.

    The same ``mating_faces`` offset ``roof_edge`` positioned the closure bands against, so
    the wedge's top edge and the bands' tops are answers to one question rather than two.
    """
    from typehaus.resolve.roof_edge_geometry import mating_faces, roof_slope
    from typehaus.resolve.roof_layer_setbacks import above_structure_layers

    assembly = model.plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    layers = above_structure_layers(assembly)
    if not layers:
        return None
    faces = mating_faces(layers)
    if faces.foam_under is None:
        return None
    perpendicular = faces.foam_under * math.hypot(1.0, roof_slope(roof))

    def at(u: float) -> float:
        point = (u, station) if direction == "x" else (station, u)
        return roof_height_at(roof, point) + perpendicular

    return at


def _named_layer(wall: ResolvedWall, function: str):
    """The outermost layer of ``wall`` with this function, or ``None``."""
    return next((layer for layer in reversed(wall.layers)
                 if layer.function == function and not layer.is_cavity), None)


def _closure_band_tops(model, roof: ResolvedRoof, wall: ResolvedWall, plane: CutPlane,
                       role: str) -> list[tuple[float, float, float]]:
    """``(u0, u1, z_top)`` per closure band carrying this wall layer up to its roof face.

    ``roof_edge._closure_members`` emits one per skin layer at that layer's own plan offset,
    so the band's sliced top *is* the elevation the wall's insulation actually reaches. The
    bands hang off the **roof** (they are emitted during the roof-edge stage) while naming
    the wall they continue, which is why the lookup goes through the roof's framing element
    and matches on the wall's tag.
    """
    element = model.geometry.by_uid(f"{roof.uid}::framing")
    if element is None:
        return []
    prefix = f"{wall.tag}-closure-"
    bands: list[tuple[float, float, float]] = []
    for part in element.parts:
        catalog = part.catalog
        if catalog is None or catalog.role != role:
            continue
        if not (catalog.name or "").startswith(prefix):
            continue
        for profile in slice_part(part, plane):
            us = [u for (u, _z) in profile.outline]
            bands.append((min(us), max(us), max(z for (_u, z) in profile.outline)))
    return bands


def _apply_authored_join(plan: JointPlan, wall: ResolvedWall, join, direction, station) -> None:
    interface_z = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
    term = interface_z + join.termination.meters
    for layer in wall.layers:
        if matches(join.layer, layer.name) or matches(join.layer, layer.function):
            u_iv = _layer_u_interval(layer, direction, station)
            u0 = station if u_iv is None else sum(u_iv) / 2.0
            plan.terminations[(wall.uid, layer.name)] = TerminationPlane(u0=u0, z0=term)


def _layer_u_interval(layer, direction: str, station: float) -> tuple[float, float] | None:
    if layer is None:
        return None
    ivs = ring_cut_intervals(layer.polygon, direction, station)
    return ivs[0] if ivs else None
