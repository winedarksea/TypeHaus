"""Exterior opening metal and concealed liquid flashing, resolved after framing.

The geometry documents the already-purchased opening system. It never creates a second
membrane or trim allowance. The water and mount planes come from the host's resolved stack.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.resolve.flashing_config import FLASHING, FlashingConfig
from typehaus.resolve.flashing_solids import flashing_solid
from typehaus.resolve.framing.truss_wall import truss_kind
from typehaus.resolve.geometry_ir import GMesh
from typehaus.resolve.geometry_openings import (
    _WINDOW_TRIM_FACE_WIDTH_M,
    _WINDOW_TRIM_PROUD_DEPTH_M,
    _exterior_face,
)
from typehaus.resolve.model import ResolvedModel, ResolvedOpening, ResolvedWall
from typehaus.resolve.rainscreen_closures import rainscreen_band
from typehaus.resolve.sheet_geometry import combine_sheets, extruded_quad, sheet_between

_HEAD_COURSE_TOLERANCE_M = 1e-5


@dataclass(frozen=True)
class OpeningFlashingFrame:
    origin: tuple[float, float]
    along: tuple[float, float]
    outward: tuple[float, float]
    back: float
    water: float
    mount: float
    clad: float
    outie: bool

    def point(self, station: float, depth: float, z: float) -> tuple[float, float, float]:
        return (self.origin[0] + self.along[0] * station + self.outward[0] * depth,
                self.origin[1] + self.along[1] * station + self.outward[1] * depth, z)

    def leg(self, station: float, width: float, a, b, thickness: float) -> GMesh:
        return sheet_between(self.point(station, *a), self.point(station, *b),
                             (*[value * width for value in self.along], 0.0), thickness,
                             normal_hint=(*self.outward, 1.0))


def opening_flashing_frame(model: ResolvedModel, wall: ResolvedWall) \
        -> OpeningFlashingFrame | None:
    exterior = _exterior_face(wall)
    if exterior is None:
        return None
    (x0, y0), (x1, y1) = wall.axis
    span = math.hypot(x1 - x0, y1 - y0)
    along = ((x1 - x0) / span, (y1 - y0) / span)
    outward = (-along[1] * exterior[1], along[0] * exterior[1])

    def extent(layer):
        return tuple((x - x0) * outward[0] + (y - y0) * outward[1]
                     for x, y in layer.polygon)

    bodies = [layer for layer in wall.depth_layers() if layer.polygon]
    sheaths = [layer for layer in bodies if layer.function == "sheathing"]
    structures = [layer for layer in bodies if layer.function == "structure"]
    if not sheaths and not structures:
        return None
    substrate = sheaths[-1] if sheaths else structures[-1]
    sheath_out = max(extent(substrate))
    clad = max(extent(bodies[-1]))
    kind = truss_kind(model.plan, wall.assembly)
    cavity = rainscreen_band(wall.layers)
    outie = kind is not None and cavity is not None
    if outie:
        band, gap = cavity
        mount = max(extent(band))
        water = mount - gap
        back = sheath_out
    else:
        mount = sheath_out
        water_layers = [layer for layer in bodies if "water" in layer.control
                        and layer.function != "cladding"]
        water = max(extent(water_layers[-1])) if water_layers else sheath_out
        back = min(extent(structures[-1])) if structures else min(extent(substrate))
    return OpeningFlashingFrame((x0, y0), along, outward, back, water, mount, clad, outie)


def resolve_opening_flashing(model: ResolvedModel, cfg: FlashingConfig = FLASHING) -> None:
    walls = {wall.tag: wall for wall in model.walls}
    for opening in model.openings:
        if opening.kind not in ("window", "door"):
            continue
        wall = walls[opening.host_wall]
        frame = opening_flashing_frame(model, wall)
        if frame is None:
            continue
        element = model.plan.by_tag(opening.tag)
        product = next((p for p in model.plan.library.door_types
                        if p.tag == opening.type_ref), None) if opening.is_door else None
        operation = getattr(getattr(product, "operation", None), "value", "")
        if not operation:
            operation = getattr(getattr(element, "operation", None), "value", "")
        meshes = opening_flashing_meshes(wall, opening, frame, cfg,
                                         pan=operation != "overhead")
        for key, category, material, mesh in meshes:
            model.solids.append(flashing_solid(
                uid=f"{opening.uid}-flashing-{key}", tag=f"{opening.tag}-FLASH-{key.upper()}",
                storey=wall.storey, category=category, mesh=mesh, material=material,
                host_ref=opening.tag))


def opening_flashing_meshes(wall: ResolvedWall, opening: ResolvedOpening,
                            frame: OpeningFlashingFrame, cfg: FlashingConfig = FLASHING,
                            *, pan: bool = True) -> list[tuple[str, str, str, GMesh]]:
    lo = opening.center_along_m - opening.width_m / 2
    hi = lo + opening.width_m
    sill = wall.base_ref_z_m + opening.sill_m
    head = sill + opening.height_m
    # Read the actual head course, including a girt's flat 2x4 rather than guessing its height.
    courses = [m for m in wall.members if m.category == "truss_blocking"
               and abs(m.z0_m - head) < _HEAD_COURSE_TOLERANCE_M]
    casing_top = head + (_WINDOW_TRIM_FACE_WIDTH_M if opening.kind == "window" else 0.0)
    head_seat = max(casing_top, max((m.z1_m for m in courses), default=head))
    rise = cfg.outie_head_rise_m if frame.outie else cfg.head_rise_m
    margin = max((m.z1_m - m.z0_m for m in courses), default=cfg.head_projection_m)
    # The existing opening product finishes proud of the cladding. The drip must clear
    # that face too, or its downstand is buried in the very trim it is meant to protect.
    front = frame.clad + _WINDOW_TRIM_PROUD_DEPTH_M + cfg.head_projection_m
    fall = max(0.0, front - frame.water) * cfg.drainage_slope
    # Raise the inboard bend so the fall clears the head course at every depth.
    bend_z = head_seat + fall
    metal = [frame.leg(lo - margin, opening.width_m + 2 * margin, a, b, cfg.sheet_m)
             for a, b in (
                 ((frame.water, bend_z + rise), (frame.water, bend_z)),
                 ((frame.water, bend_z), (front, head_seat)),
                 ((front, head_seat), (front, head_seat - cfg.head_drop_m)),
                 ((front, head_seat - cfg.head_drop_m),
                  (front - cfg.hem_m, head_seat - cfg.head_drop_m)),
             )]
    result = [("head", "opening_head_flashing", cfg.metal_material, combine_sheets(metal))]

    membrane = []
    thickness = cfg.perimeter_membrane_m
    lap = cfg.perimeter_lap_m
    for station, sign in ((lo, 1.0), (hi, -1.0)):
        jamb_top = head - opening.arch_rise_m
        # Reveal and outward return form one continuous liquid application at each jamb.
        points = tuple(frame.point(station, depth, z) for depth, z in
                       ((frame.back, sill), (frame.mount, sill),
                        (frame.mount, jamb_top), (frame.back, jamb_top)))
        membrane.append(extruded_quad(points, (*[sign * v * thickness for v in frame.along], 0)))
        membrane.append(frame.leg(station - lap if sign > 0 else station, lap,
                                 (frame.water, sill), (frame.water, jamb_top), thickness))
    if opening.arch_rise_m > 0:
        from typehaus.resolve.geometry_prims import (
            _arch_soffit_sample,
            _arch_soffit_segment_count,
            arch_soffit_circle,
        )

        radius, angle, _spring = arch_soffit_circle(opening.width_m / 2, opening.arch_rise_m)
        count = _arch_soffit_segment_count(radius, angle)
        contour = [(opening.center_along_m + x, head - opening.arch_rise_m + z)
                   for x, z in (_arch_soffit_sample(i, count, radius, angle)
                                for i in range(count + 1))]
    else:
        contour = [(lo, head), (hi, head)]
    for (s0, z0), (s1, z1) in zip(contour[:-1], contour[1:], strict=True):
        membrane.append(extruded_quad(tuple(frame.point(s, depth, z) for s, depth, z in
            ((s0, frame.back, z0), (s1, frame.back, z1),
             (s1, frame.mount, z1), (s0, frame.mount, z0))), (0, 0, -thickness)))
        membrane.append(extruded_quad(tuple(frame.point(s, frame.water, z) for s, z in
            ((s0, z0), (s1, z1), (s1, z1 + lap), (s0, z0 + lap))),
            (*[v * thickness for v in frame.outward], 0)))
    for station in (lo - lap, hi):
        jamb_head = head - opening.arch_rise_m
        membrane.append(frame.leg(station, lap, (frame.water, jamb_head),
                                 (frame.water, jamb_head + lap), thickness))
    result.append(("perimeter", "opening_flashing_membrane", "fluid-applied-flashing",
                   combine_sheets(membrane)))
    if pan:
        outlet = frame.mount if frame.outie else front
        fall = (outlet - frame.back) * cfg.drainage_slope
        pan_meshes = [frame.leg(lo, opening.width_m, a, b, cfg.sill_membrane_m)
                      for a, b in (
                          ((frame.back, sill + cfg.back_dam_m), (frame.back, sill + fall)),
                          ((frame.back, sill + fall), (outlet, sill)),
                          ((outlet, sill), (outlet, sill - cfg.pan_drop_m)))]
        for station, sign in ((lo, 1.0), (hi, -1.0)):
            pan_meshes.append(extruded_quad(tuple(frame.point(station, depth, z) for depth, z in
                ((frame.back, sill + fall), (outlet, sill),
                 (outlet, sill + cfg.end_dam_m), (frame.back, sill + cfg.end_dam_m))),
                (*[sign * v * cfg.sill_membrane_m for v in frame.along], 0)))
        result.append(("sill", "opening_sill_pan", "fluid-applied-flashing",
                       combine_sheets(pan_meshes)))
    return result
