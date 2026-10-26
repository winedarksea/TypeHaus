"""One immutable doorway-bottom answer for rendering, checks and purchasing.

No operation chooses a floor-spanning product. Unspecified exterior sills and hardware
remain UNKNOWN, while identical known interior finishes can continue without a trim.
"""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from itertools import pairwise
from typing import TYPE_CHECKING

from typehaus.model.base import HausModel
from typehaus.model.doorway import DoorwayProductSpec, DoorwayTreatment
from typehaus.resolve.geometry import opening_center, wall_frame
from typehaus.resolve.geometry_door_products import finish_faces
from typehaus.resolve.room_floor import SLAB_MATCH_TOLERANCE_M
from typehaus.resolve.walking_surface import FloorSurface, surfaces_at

if TYPE_CHECKING:
    from typehaus.resolve.exterior_door import ExteriorDoorPlacement


@dataclass(frozen=True)
class DoorwayConfig:
    floor_probe_m: float = 0.015
    height_tolerance_m: float = 0.001
    leaf_undercut_m: float = 0.010
    leaf_thickness_m: float = 0.045


DOORWAY = DoorwayConfig()


@dataclass(frozen=True)
class DoorwayComponent:
    specification: DoorwayProductSpec
    base_z_m: float
    normal_m: float
    span_m: float
    along_m: float

    @property
    def top_z_m(self):
        return self.base_z_m + max(z for p in self.specification.parts for _, z in p.polygon_m)

    @property
    def normal_extent_m(self):
        s = self.specification
        values = [self.normal_m + s.positive_normal_sign * x
                  for p in s.parts for x, _ in p.polygon_m]
        return min(values), max(values)


    @property
    def finish_extent_m(self):
        edges = self.specification.floor_finish_edges_m
        if edges is None:
            return self.normal_extent_m
        values = [self.normal_m + self.specification.positive_normal_sign * x for x in edges]
        return min(values), max(values)


@dataclass(frozen=True)
class DoorwayAssembly:
    rough_opening_z_m: float
    adjacent_floors: tuple[FloorSurface | None, FloorSurface | None]
    floor_treatment: str
    joint_normal_m: float
    components: tuple[DoorwayComponent, ...] = ()
    unknown: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    leaf_bottom_z_m: float | None = None
    selected_products: tuple[DoorwayProductSpec, ...] = ()
    jamb_bottom_z_m: float | None = None
    exterior_placement: ExteriorDoorPlacement | None = None

    @property
    def section_status(self):
        return "DOCUMENTED" if self.selected_products and all(
            s.verified or s.section_documented for s in self.selected_products) else "UNKNOWN"

    @property
    def supplier_status(self):
        return "CONFIRMED" if self.selected_products and all(
            s.supplier_confirmed for s in self.selected_products) else "PENDING"

    @property
    def fit_status(self):
        return "FAIL" if self.conflicts else "UNKNOWN" if self.unknown else "VERIFIED"

    @property
    def status(self):
        return "FAIL" if self.conflicts else "UNKNOWN" if self.unknown else "VERIFIED"


def doorway_json(value):
    """Serialize frozen authoring contracts alongside derived metre dimensions."""
    if isinstance(value, HausModel):
        return value.model_dump(mode="json")
    if is_dataclass(value):
        result = {f.name: doorway_json(getattr(value, f.name)) for f in fields(value)}
        if isinstance(value, DoorwayAssembly):
            result["status"] = value.status
            result["section_status"] = value.section_status
            result["supplier_status"] = value.supplier_status
            result["fit_status"] = value.fit_status
        return result
    if isinstance(value, (tuple, list)):
        return [doorway_json(v) for v in value]
    return value


def adjacent_floor(model, wall, point):
    candidates = [s for s in surfaces_at(model, point)
                  if abs(s.deck_top_m - wall.base_ref_z_m) < SLAB_MATCH_TOLERANCE_M]
    return min(candidates, key=lambda s: abs(s.deck_top_m - wall.base_ref_z_m), default=None)


def _floor_sample_stations(model, wall, opening, center, tangent, normal, offset):
    """Sample every finish-zone interval, including small zones close to a jamb."""
    from shapely.geometry import LineString, Polygon

    half = max(0, opening.width_m / 2 - DOORWAY.height_tolerance_m)
    def point(along):
        return (center[0] + normal[0] * offset + tangent[0] * along,
                center[1] + normal[1] * offset + tangent[1] * along)
    line = LineString((point(-half), point(half)))
    stations = {-half, half, 0.0}
    for room in model.rooms:
        if room.storey != wall.storey:
            continue
        for zone in room.finish_zones:
            if len(zone.outline) < 3:
                continue
            crossing = Polygon(zone.outline).boundary.intersection(line)
            for piece in getattr(crossing, "geoms", (crossing,)):
                for x, y in getattr(piece, "coords", ()):
                    stations.add((x - center[0]) * tangent[0] + (y - center[1]) * tangent[1])
    stations = sorted(stations)
    return [point((a + b) / 2) for a, b in pairwise(stations) if b - a > 1e-9]


def resolve_doorway(model, wall, opening, door_type, treatment=None):
    treatment = treatment or DoorwayTreatment()
    center = opening_center(wall, opening)
    _, tangent, normal, _ = wall_frame(wall)
    faces = finish_faces(wall)
    unknown, conflicts = [], []
    floors = []
    installation = treatment.exterior_installation
    from typehaus.resolve.exterior_door_boundary import (
        ExteriorDoorBoundaryError,
        exterior_door_boundary,
    )

    try:
        exterior = (exterior_door_boundary(model, wall, opening, installation)
                    if installation else None)
    except ExteriorDoorBoundaryError as error:
        exterior = None
        unknown.append(str(error))
    for side, face in zip((-1, 1), faces or (0, 0), strict=True):
        samples = []
        boundary_face = exterior[0] if exterior and side == exterior[1] else face
        offset = boundary_face + side * DOORWAY.floor_probe_m
        for point in _floor_sample_stations(model, wall, opening, center, tangent, normal, offset):
            if exterior and side == exterior[1]:
                from typehaus.resolve.exterior_door import exterior_landing

                samples.append(exterior_landing(model, wall, point,
                    tuple(side * n for n in normal), installation))
            else:
                samples.append(adjacent_floor(model, wall, point))
        signatures = {(s.finish_ref, s.room_tag, s.surface_m is None) if s else None
                      for s in samples}
        elevations = [s.surface_m for s in samples if s is not None and s.surface_m is not None]
        varies = elevations and max(elevations) - min(elevations) > DOORWAY.height_tolerance_m
        if len(signatures) != 1 or varies:
            unknown.append(f"floor varies across doorway side {side}; split finish layout required")
            floors.append(None)
        else:
            floors.append(max(samples, key=lambda s: s.surface_m if s.surface_m is not None
                              else s.deck_top_m) if samples and samples[0] is not None else None)
    known = all(f is not None and f.surface_m is not None for f in floors)
    if not known:
        unknown.append("adjacent walking surface or finish thickness is missing")
    base = wall.base_ref_z_m + opening.sill_m
    joint = opening.cased_product.leaf_normal_m if opening.cased_product else 0.0
    # Concealed leaves close on their flush face; avoid using swing direction as sill orientation.
    if door_type.trimless and faces:
        from typehaus.resolve.geometry_door_products import concealed_leaf, handing
        _, _, _, flush, back = concealed_leaf(faces, handing(opening)[1], opening.width_m,
                                             base, opening.height_m, door_type.leaf_set)
        joint = (flush + back) / 2
    same = known and (floors[0].finish_ref == floors[1].finish_ref
                     and abs(floors[0].surface_m - floors[1].surface_m)
                     <= DOORWAY.height_tolerance_m)
    mode = treatment.floor_treatment
    if mode == "auto":
        mode = ("continuous" if same and not door_type.exterior
                and treatment.transition is None else "transition")
    if mode == "continuous" and known and not same:
        conflicts.append("continuous floor requires matching finishes and walking elevations")
    selected = [treatment.threshold, treatment.transition]
    if door_type.exterior and treatment.threshold is None:
        unknown.append("exact exterior sill/track or leaf-mounted bottom-seal section "
                       "is unspecified")
    if door_type.operation.value in ("slide", "pocket", "bifold") and treatment.threshold is None:
        unknown.append("documented guide/track installation is unspecified; "
                       "no bottom track inferred")
    if mode == "transition" and treatment.transition is None and not door_type.exterior:
        unknown.append("compatible flooring trim or documented transition is unspecified")
    components = []
    for spec in selected:
        if spec is None:
            continue
        if not (spec.verified or spec.section_documented):
            unknown.append(f"{spec.product_ref}: section/installation variant is unverified")
            continue
        if spec.role in ("sill", "track", "transition") and spec.maximum_floor_difference_m is None:
            unknown.append(f"{spec.product_ref}: supported floor-height range is unspecified")
            continue
        if spec.role in ("sill", "track", "transition") and spec.floor_finish_edges_m is None:
            unknown.append(f"{spec.product_ref}: documented finish-stop positions "
                           "are unspecified")
            continue
        if spec.role == "transition":
            if spec.floor_contact_heights_m is None:
                unknown.append(f"{spec.product_ref}: installed floor contact planes "
                               "are unspecified")
                continue
            if not known:
                continue
            pair = (floors[0].finish_ref, floors[1].finish_ref)
            difference = floors[1].surface_m - floors[0].surface_m
            if abs(difference) > DOORWAY.height_tolerance_m:
                if spec.higher_floor_side is None:
                    unknown.append(f"{spec.product_ref}: reducer high-side orientation "
                                   "is unverified")
                    continue
                expected_sign = spec.higher_floor_side * spec.positive_normal_sign
                if difference * expected_sign < 0:
                    conflicts.append(f"{spec.product_ref}: reducer high side faces the lower floor")
            if (pair not in spec.compatible_finish_pairs
                    and pair[::-1] not in spec.compatible_finish_pairs):
                unknown.append(f"{spec.product_ref}: compatibility with adjacent finishes "
                               "is unverified")
                continue
        if known and spec.maximum_floor_difference_m is not None:
            difference = abs(floors[1].surface_m - floors[0].surface_m)
            if not (spec.minimum_floor_difference_m - DOORWAY.height_tolerance_m <= difference
                    <= spec.maximum_floor_difference_m + DOORWAY.height_tolerance_m):
                conflicts.append(f"{spec.product_ref}: adjacent floor-height difference "
                                 "outside supported range")
        if spec.datum != "rough_opening" and not known:
            unknown.append(f"{spec.product_ref}: installation datum needs adjacent finished floors")
            continue
        datum = base if spec.datum == "rough_opening" else (
            min if spec.datum == "lower_floor" else max)(f.surface_m for f in floors)
        normal = spec.normal_offset_m + (joint if spec.role == "transition" else 0)
        component = DoorwayComponent(spec, datum + spec.elevation_offset_m,
                                     normal,
                                     spec.span_m or opening.width_m, spec.along_offset_m)
        if spec.role == "transition" and known:
            expected = spec.floor_contact_heights_m
            if spec.positive_normal_sign < 0:
                expected = expected[::-1]
            if any(abs(component.base_z_m + height - floor.surface_m)
                   > DOORWAY.height_tolerance_m
                   for height, floor in zip(expected, floors, strict=True)):
                conflicts.append(f"{spec.product_ref}: section floor contacts "
                                 "do not meet walking planes")
        if abs(component.along_m) + component.span_m / 2 > opening.width_m / 2 + 1e-9:
            conflicts.append(f"{spec.product_ref}: span extends outside rough opening")
        components.append(component)
    leaf = None
    jamb = None
    known_surfaces = [f.surface_m for f in floors if f is not None and f.surface_m is not None]
    if known or installation and known_surfaces:
        jamb = max(base, min(known_surfaces))
        leaf = max(base, *known_surfaces) + DOORWAY.leaf_undercut_m
        for component in components:
            if component.specification.role != "bottom_seal":
                leaf = max(leaf, component.top_z_m + component.specification.leaf_clearance_m)
        for component in components:
            spec = component.specification
            if spec.leaf_bottom_m is not None:
                published_bottom = component.base_z_m + spec.leaf_bottom_m
                if published_bottom < leaf - DOORWAY.height_tolerance_m:
                    conflicts.append(f"{spec.product_ref}: published leaf bottom conflicts "
                                     "with floor/profile clearance")
                leaf = published_bottom
            if (door_type.exterior and spec.role in ("sill", "track")
                    and spec.leaf_bottom_m is None):
                unknown.append(f"{spec.product_ref}: published leaf termination is missing")
            if spec.jamb_bottom_m is not None:
                jamb = component.base_z_m + spec.jamb_bottom_m
            elif door_type.exterior and spec.role in ("sill", "track"):
                unknown.append(f"{spec.product_ref}: published jamb termination is missing")
        if leaf >= base + opening.height_m:
            conflicts.append("walking surface/product leaves no clear leaf height")
    return DoorwayAssembly(base, tuple(floors), mode, joint, tuple(components),
                           tuple(unknown), tuple(conflicts), leaf,
                           tuple(s for s in selected if s is not None), jamb)


def resolve_doorways(model):
    types = {t.tag: t for t in model.plan.library.door_types}
    walls = {w.tag: w for w in model.walls}
    resolved = []
    for opening in model.openings:
        product = types.get(opening.type_ref)
        if opening.kind != "door" or product is None:
            resolved.append(opening)
            continue
        authored = model.plan.by_tag(opening.tag)
        treatment = getattr(authored, "doorway", None) or product.doorway
        installation = getattr(authored, "exterior_installation", None)
        if installation:
            treatment = (treatment or DoorwayTreatment()).model_copy(
                update={"exterior_installation": installation})
        assembly = resolve_doorway(model, walls[opening.host_wall], opening, product, treatment)
        if treatment and treatment.exterior_installation:
            from typehaus.resolve.exterior_door import place_exterior_door

            assembly = place_exterior_door(model, walls[opening.host_wall], opening, assembly,
                                          treatment.exterior_installation)
        if assembly.exterior_placement:
            previous = opening.doorway.exterior_placement if opening.doorway else None
            offset = assembly.exterior_placement.leaf_normal_m
            delta = offset - (previous.leaf_normal_m if previous else 0.0)
            _, _, normal, _ = wall_frame(walls[opening.host_wall])
            opening = replace(opening, swing_clearance=[
                (x + normal[0] * delta, y + normal[1] * delta)
                for x, y in opening.swing_clearance])
        cased = opening.cased_product
        if cased and assembly.leaf_bottom_z_m is not None:
            cased = replace(cased, leaf_bottom_z_m=assembly.leaf_bottom_z_m,
                            base_z_m=assembly.jamb_bottom_z_m,
                            finished_floor_z_m=tuple(f.surface_m if f else None
                                                    for f in assembly.adjacent_floors))
        resolved.append(replace(opening, doorway=assembly, cased_product=cased))
    model.openings = resolved
