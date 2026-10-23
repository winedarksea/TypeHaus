"""Exterior opening metal and concealed liquid flashing, resolved after framing.

The geometry documents the already-purchased opening system. It never creates a second
membrane or trim allowance. The water and mount planes come from the host's resolved stack.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from typehaus.model.project import Project
from typehaus.model.types import WindowType
from typehaus.quantities import inch
from typehaus.resolve.flashing_config import FLASHING, FlashingConfig
from typehaus.resolve.flashing_solids import flashing_solid
from typehaus.resolve.framing.truss_common import BUCK_THICKNESS_IN
from typehaus.resolve.framing.truss_wall import truss_kind
from typehaus.resolve.geometry_ir import GMesh
from typehaus.resolve.geometry_openings import (
    _WINDOW_TRIM_FACE_WIDTH_M,
    _WINDOW_TRIM_PROUD_DEPTH_M,
    _exterior_face,
)
from typehaus.resolve.model import ResolvedModel, ResolvedOpening, ResolvedWall
from typehaus.resolve.model_window_seat import WindowSeat, orderable_size
from typehaus.resolve.rainscreen_closures import rainscreen_band
from typehaus.resolve.sheet_geometry import combine_sheets, extruded_quad, sheet_between

_HEAD_COURSE_TOLERANCE_M = 1e-5
_DEFAULT_METAL = Project.model_fields["opening_flashing_material"].default


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
    #: The plywood buck lining the RO; every reveal membrane lies on its exposed face.
    buck: float = 0.0

    def point(self, station: float, depth: float, z: float) -> tuple[float, float, float]:
        return (self.origin[0] + self.along[0] * station + self.outward[0] * depth,
                self.origin[1] + self.along[1] * station + self.outward[1] * depth, z)

    def leg(self, station: float, width: float, a, b, thickness: float) -> GMesh:
        return sheet_between(self.point(station, *a), self.point(station, *b),
                             (*[value * width for value in self.along], 0.0), thickness,
                             normal_hint=(*self.outward, 1.0))

    def section(self, station: float, profile, thickness: float, sign: float) -> GMesh:
        """A planar (depth, z) profile at ``station``, thickened ``sign`` along the wall."""
        return extruded_quad(tuple(self.point(station, d, z) for d, z in profile),
                             (*[sign * v * thickness for v in self.along], 0.0))


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
    buck = 0.0
    if outie:
        band, gap = cavity
        mount = max(extent(band))
        water = mount - gap
        back = sheath_out
        buck = inch(BUCK_THICKNESS_IN).meters
    else:
        mount = sheath_out
        water_layers = [layer for layer in bodies if "water" in layer.control
                        and layer.function != "cladding"]
        water = max(extent(water_layers[-1])) if water_layers else sheath_out
        back = min(extent(structures[-1])) if structures else min(extent(substrate))
    return OpeningFlashingFrame((x0, y0), along, outward, back, water, mount, clad, outie,
                                buck)


def resolve_window_seats(model: ResolvedModel, cfg: FlashingConfig = FLASHING) -> None:
    """Seat every flashed window before anything reads its product frame (returns, stool)."""
    walls = {wall.tag: wall for wall in model.walls}
    seated = []
    for opening in model.openings:
        frame = opening_flashing_frame(model, walls[opening.host_wall]) \
            if opening.kind == "window" else None
        product = next((t for t in model.plan.library.window_types
                        if t.tag == opening.type_ref), None) if frame is not None else None
        seated.append(opening if frame is None else replace(
            opening, window_seat=window_seat(opening, frame, cfg, product)))
    model.openings = seated


def is_overhead(model: ResolvedModel, opening: ResolvedOpening) -> bool:
    """An overhead door runs to the slab and takes no sill pan."""
    product = next((p for p in model.plan.library.door_types
                    if p.tag == opening.type_ref), None) if opening.is_door else None
    operation = getattr(getattr(product, "operation", None), "value", "")
    if not operation:
        element = model.plan.by_tag(opening.tag)
        operation = getattr(getattr(element, "operation", None), "value", "")
    return operation == "overhead"


def resolve_opening_flashing(model: ResolvedModel, cfg: FlashingConfig = FLASHING) -> None:
    walls = {wall.tag: wall for wall in model.walls}
    metal = model.plan.project.opening_flashing_material
    for opening in model.openings:
        if opening.kind not in ("window", "door"):
            continue
        wall = walls[opening.host_wall]
        frame = opening_flashing_frame(model, wall)
        if frame is None:
            continue
        meshes = opening_flashing_meshes(wall, opening, frame, cfg,
                                         pan=not is_overhead(model, opening), metal=metal)
        for key, category, material, mesh in meshes:
            model.solids.append(flashing_solid(
                uid=f"{opening.uid}-flashing-{key}", tag=f"{opening.tag}-FLASH-{key.upper()}",
                storey=wall.storey, category=category, mesh=mesh, material=material,
                host_ref=opening.tag))


def opening_flashing_meshes(wall: ResolvedWall, opening: ResolvedOpening,
                            frame: OpeningFlashingFrame, cfg: FlashingConfig = FLASHING,
                            *, pan: bool = True, metal: str = _DEFAULT_METAL) \
        -> list[tuple[str, str, str, GMesh]]:
    lo = opening.center_along_m - opening.width_m / 2
    hi = lo + opening.width_m
    sill = wall.base_ref_z_m + opening.sill_m
    head = sill + opening.height_m
    buck = frame.buck
    # A membrane is applied to the wall it seals: below the wall's base (an overhead door
    # down to the slab) there is only the stem end, which is not this wall's opening.
    base = max(sill, wall.z0_m)
    # Read the actual head course, including a girt's flat 2x4 rather than guessing its height.
    courses = [m for m in wall.members if m.category == "truss_blocking"
               and abs(m.z0_m - head) < _HEAD_COURSE_TOLERANCE_M]
    window = opening.kind == "window"
    casing = _WINDOW_TRIM_FACE_WIDTH_M if window else 0.0
    head_seat = max(head + casing, max((m.z1_m for m in courses), default=head))
    rise = cfg.outie_head_rise_m if frame.outie else cfg.head_rise_m
    # The drip must clear the casing face where there is one, or its downstand is buried
    # in the very trim it protects; a door has none and clears the cladding.
    front = _drip_face(opening, frame, cfg)
    fall = max(0.0, front - frame.water) * cfg.drainage_slope
    # Raise the inboard bend so the fall clears the head course at every depth.
    bend_z = head_seat + fall
    start = lo - casing - cfg.head_end_lap_m
    span = hi - lo + 2 * (casing + cfg.head_end_lap_m)
    top = bend_z + rise
    sheets = [frame.leg(start, span, a, b, cfg.sheet_m)
              for a, b in (
                  ((frame.water, top), (frame.water, bend_z)),
                  ((frame.water, bend_z), (front, head_seat)),
                  ((front, head_seat), (front, head_seat - cfg.head_drop_m)),
                  ((front, head_seat - cfg.head_drop_m),
                   (front - cfg.hem_m, head_seat - cfg.head_drop_m)),
              )]
    for station, sign in ((start, 1.0), (start + span, -1.0)):
        dam = cfg.head_end_dam_m
        sheets.append(frame.section(station, ((frame.water, bend_z), (front, head_seat),
                                              (front, head_seat + dam),
                                              (frame.water, bend_z + dam)), cfg.sheet_m, sign))
    result = [("head", "opening_head_flashing", metal, combine_sheets(sheets))]

    membrane = []
    thickness = cfg.perimeter_membrane_m
    lap = cfg.perimeter_lap_m
    jamb_top = head - opening.arch_rise_m
    for station, sign in ((lo, 1.0), (hi, -1.0)):
        # Reveal and outward return form one continuous liquid application at each jamb,
        # on the buck's face and wrapped round its edge onto the water plane.
        membrane.append(frame.section(station + sign * buck, (
            (frame.back, max(base, sill + buck)), (frame.mount, max(base, sill + buck)),
            (frame.mount, jamb_top - buck), (frame.back, jamb_top - buck)), thickness, sign))
        membrane.append(frame.leg(station - lap if sign > 0 else station - buck, lap + buck,
                                  (frame.water, base), (frame.water, jamb_top), thickness))
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
        r0, r1 = (min(max(s, lo + buck), hi - buck) for s in (s0, s1))
        if r1 - r0 > 1e-9:
            membrane.append(extruded_quad(tuple(frame.point(s, depth, z - buck)
                for s, depth, z in ((r0, frame.back, z0), (r1, frame.back, z1),
                                    (r1, frame.mount, z1), (r0, frame.mount, z0))),
                (0, 0, -thickness)))
        membrane.append(extruded_quad(tuple(frame.point(s, frame.water, z) for s, z in
            ((s0, z0 - buck), (s1, z1 - buck), (s1, z1 + lap), (s0, z0 + lap))),
            (*[v * thickness for v in frame.outward], 0)))
    for station in (lo - lap, hi):
        membrane.append(frame.leg(station, lap, (frame.water, jamb_top),
                                  (frame.water, jamb_top + lap), thickness))
    # The head course's top under the metal: steel never bears on treated wood bare.
    if courses:
        membrane.append(frame.leg(start, span, (frame.water, head_seat),
                                  (frame.mount, head_seat), thickness))
    # Strip-in over the upstand's top edge, or water on the water plane runs behind it.
    strip, metal_face = cfg.head_strip_lap_m, frame.water + cfg.sheet_m
    membrane += [frame.leg(start, span, a, b, thickness) for a, b in (
        ((metal_face, top - strip), (metal_face, top)),
        ((frame.water, top), (metal_face + thickness, top)),
        ((frame.water, top), (frame.water, top + strip)))]
    result.append(("perimeter", "opening_flashing_membrane", cfg.membrane_material,
                   combine_sheets(membrane)))
    if pan:
        result += _sill_pan(frame, _pan_outlet(opening, frame, cfg), lo + buck,
                            hi - lo - 2 * buck, sill + buck, cfg)
    return result


def _drip_face(opening: ResolvedOpening, frame: OpeningFlashingFrame,
               cfg: FlashingConfig) -> float:
    """The drip must clear the casing face where there is one, else the cladding."""
    casing = _WINDOW_TRIM_PROUD_DEPTH_M if opening.kind == "window" else 0.0
    return frame.clad + casing + cfg.head_projection_m


def _pan_outlet(opening: ResolvedOpening, frame: OpeningFlashingFrame,
                cfg: FlashingConfig) -> float:
    """An outie window's pan discharges at the mount plane; every other pan at the drip."""
    return frame.mount if frame.outie and not opening.is_door \
        else _drip_face(opening, frame, cfg)


def window_seat(opening: ResolvedOpening, frame: OpeningFlashingFrame,
                cfg: FlashingConfig = FLASHING, product: WindowType | None = None) -> WindowSeat:
    """The unit inside its flashed RO: shimmed off the jambs and head, on the pan's high
    point at the back dam (a level unit bears there on a sloped pan), outboard of the dam.

    A product with an orderable size is rounded down inside that envelope, centred between
    the jambs; the head takes the rest of the vertical slack.
    """
    dam = frame.back + cfg.back_dam_strip_m
    fall = (_pan_outlet(opening, frame, cfg) - dam) * cfg.drainage_slope
    lining = frame.buck + cfg.perimeter_membrane_m
    sill_rise = frame.buck + fall + cfg.sill_membrane_m
    side = head = lining + cfg.install_gap_m
    allowance = getattr(product, "minimum_rough_opening_allowance", None)
    step = getattr(product, "frame_size_increment", None)
    if allowance is not None or step is not None:
        extra = allowance.meters if allowance is not None else 0.0
        flashed_w = opening.width_m - 2 * lining
        flashed_h = opening.height_m - sill_rise - lining
        unit_w = orderable_size(flashed_w - max(2 * cfg.install_gap_m, extra), step)
        unit_h = orderable_size(flashed_h - max(cfg.install_gap_m, extra), step)
        side = (opening.width_m - unit_w) / 2
        head = opening.height_m - sill_rise - unit_h
    sign = frame.outward[0] * -frame.along[1] + frame.outward[1] * frame.along[0]
    return WindowSeat(jamb_inset_m=side, sill_rise_m=sill_rise, head_drop_m=head,
                      inner_m=(dam + cfg.sill_membrane_m) * sign)


def _sill_pan(frame: OpeningFlashingFrame, outlet: float, lo: float, width: float,
              seat: float, cfg: FlashingConfig) -> list[tuple[str, str, str, GMesh]]:
    """A sloped pan on a tapered shim, its back dam turned up a rigid strip.

    A window's outie pan discharges at the mount plane, behind the cladding; a door's, and
    every pan on a conventional wall, runs past the cladding to a drip.
    """
    dam = frame.back + cfg.back_dam_strip_m
    fall = (outlet - dam) * cfg.drainage_slope
    # The shim stands on what is there: the buck's front edge, or the sheathing face.
    support = min(outlet, frame.mount)
    rise = (outlet - support) * cfg.drainage_slope
    shim = ((dam, seat), (support, seat),
            *(((support, seat + rise),) if rise > 1e-9 else ()), (dam, seat + fall))
    support_meshes = [
        frame.section(lo, ((frame.back, seat), (dam, seat), (dam, seat + cfg.back_dam_m),
                           (frame.back, seat + cfg.back_dam_m)), width, 1.0),
        frame.section(lo, shim, width, 1.0),
    ]
    pan_meshes = [frame.leg(lo, width, a, b, cfg.sill_membrane_m)
                  for a, b in (
                      ((dam, seat + cfg.back_dam_m), (dam, seat + fall)),
                      ((dam, seat + fall), (outlet, seat)),
                      ((outlet, seat), (outlet, seat - cfg.pan_drop_m)))]
    for station, sign in ((lo, 1.0), (lo + width, -1.0)):
        pan_meshes.append(frame.section(station, (
            (dam, seat + fall), (outlet, seat),
            (outlet, seat + cfg.end_dam_m), (dam, seat + cfg.end_dam_m)),
            cfg.sill_membrane_m, sign))
    return [("sill", "opening_sill_pan", cfg.membrane_material, combine_sheets(pan_meshes)),
            ("sill-support", "opening_sill_pan", cfg.sill_shim_material,
             combine_sheets(support_meshes))]
