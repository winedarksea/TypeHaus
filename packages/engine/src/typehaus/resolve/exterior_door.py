"""Structural-wall door placement and independently measured reveal boards.

Factory sections remain product data. These records locate them and describe site-built
trim; a thin window buck is never promoted into a door sill bearing.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from typehaus.model.exterior_door import ExteriorDoorInstallation
from typehaus.resolve.geometry import opening_center, wall_frame
from typehaus.resolve.geometry_door_products import finish_faces
from typehaus.resolve.geometry_ir import GPart, GPrism, PartCatalogRef
from typehaus.resolve.walking_surface import surfaces_at


@dataclass(frozen=True)
class DoorInstallationBoard:
    name: str
    width_m: float
    height_m: float
    depth_m: float
    along_m: float
    z_m: float
    normal_m: float
    material_ref: str
    material_key: str = "window_trim"

    @property
    def cut_dimensions_m(self):
        """Stock thickness, face width, cut length in the board's own orientation."""
        if "casing" in self.name:
            return ((self.depth_m, self.width_m, self.height_m) if "jamb" in self.name
                    else (self.depth_m, self.height_m, self.width_m))
        return ((self.width_m, self.depth_m, self.height_m) if "jamb" in self.name
                else (self.height_m, self.depth_m, self.width_m))


@dataclass(frozen=True)
class ExteriorDoorPlacement:
    specification: ExteriorDoorInstallation
    outward_sign: float
    frame_inner_m: float
    frame_outer_m: float
    leaf_normal_m: float
    interior_finish_stop_m: float
    exterior_finish_stop_m: float
    boards: tuple[DoorInstallationBoard, ...]
    factory_depth_documented: bool


def exterior_landing(model, wall, point, outward, installation):
    """Find actual surfaces across a bounded drainage gap, including dropped landings."""
    from typehaus.resolve.doorway import DOORWAY

    distance = 0.0
    while distance <= installation.landing_search.meters + DOORWAY.height_tolerance_m:
        probe = tuple(point[i] + outward[i] * distance for i in (0, 1))
        candidates = [s for s in surfaces_at(model, probe)
                      if s.room_tag is None and abs(s.deck_top_m - wall.base_ref_z_m)
                      <= installation.maximum_landing_drop.meters]
        if candidates:
            return min(candidates, key=lambda s: abs(s.deck_top_m - wall.base_ref_z_m))
        distance += installation.drainage_gap.meters
    return None


def place_exterior_door(model, wall, opening, assembly, specification):
    from typehaus.resolve.doorway import DOORWAY
    from typehaus.resolve.geometry_openings import _exterior_face

    exterior = _exterior_face(wall)
    faces = finish_faces(wall)
    if exterior is None or faces is None:
        return replace(assembly, unknown=(*assembly.unknown,
                       "structural-wall door requires resolved exterior and interior faces"))
    clad, sign = exterior
    origin, _, normal, _ = wall_frame(wall)
    def offsets(layer):
        return [sum((p[i] - origin[i]) * normal[i] for i in (0, 1)) for p in layer.polygon]
    structures = [layer for layer in wall.depth_layers() if layer.function == "structure"]
    if not structures:
        return replace(assembly, unknown=(*assembly.unknown, "door anchorage substrate is missing"))
    structural_offsets = offsets(structures[0])
    outer = max(sign * n for n in structural_offsets)
    inner = min(sign * n for n in structural_offsets)
    factory = specification.factory_frame_depth
    # Until documented, retain an explicitly schematic frame within its anchorage substrate.
    depth = factory.meters if factory else outer - inner
    frame_outer, frame_inner = sign * outer, sign * (outer - depth)
    leaf = frame_inner + sign * DOORWAY.leaf_thickness_m / 2
    head = assembly.rough_opening_z_m + opening.height_m
    base = assembly.jamb_bottom_z_m
    if base is None:
        base = assembly.rough_opening_z_m
    thickness = specification.return_thickness.meters
    half = opening.width_m / 2
    boards = []
    def reveal(prefix, a, b, material, key):
        if abs(a - b) <= DOORWAY.height_tolerance_m:
            return
        mid, length = (a + b) / 2, abs(a - b)
        for side in (-1, 1):
            boards.append(DoorInstallationBoard(f"{prefix}-jamb-{side}", thickness,
                head - base - thickness, length, side * (half - thickness / 2),
                (base + head - thickness) / 2, mid, material, key))
        boards.append(DoorInstallationBoard(f"{prefix}-head", opening.width_m, thickness,
            length, 0, head - thickness / 2, mid, material, key))
    reveal("exterior-return", frame_outer, clad, specification.exterior_material_ref, "window_trim")
    interior_face = faces[0] if sign > 0 else faces[1]
    reveal("interior-extension", interior_face, frame_inner,
           specification.interior_material_ref, "door_frame")
    casing = specification.casing_width.meters
    casing_depth = specification.casing_thickness.meters
    for side in (-1, 1):
        boards.append(DoorInstallationBoard(f"exterior-casing-jamb-{side}", casing,
            head - base, casing_depth, side * (half + casing / 2),
            (base + head) / 2, clad + sign * casing_depth / 2,
            specification.exterior_material_ref))
    boards.append(DoorInstallationBoard("exterior-casing-head", opening.width_m + 2 * casing,
        casing, casing_depth, 0, head + casing / 2, clad + sign * casing_depth / 2,
        specification.exterior_material_ref))
    placement = ExteriorDoorPlacement(specification, sign, frame_inner, frame_outer, leaf,
        frame_inner, frame_outer, tuple(boards), factory is not None)
    unknown = list(assembly.unknown)
    if factory is None:
        unknown.append("factory jamb depth/hinge datum is undocumented; frame remains schematic")
    if not any(c.specification.role == "sill" for c in assembly.components):
        unknown.append("exact sill bearing, finish stops and exterior approach support "
                       "await section")
    # Section offsets on this installation are measured from the factory frame's
    # inside face; leaf-mounted seals instead follow the leaf. Transition offsets
    # were already located at the former floor joint by resolve_doorway.
    components = tuple(replace(c, normal_m=c.normal_m + (
        frame_inner - assembly.joint_normal_m if c.specification.role == "transition"
        else leaf if c.specification.role == "bottom_seal" else frame_inner))
        for c in assembly.components)
    # Finish extension must stop at the frame until a documented sill supplies its own edge.
    return replace(assembly, exterior_placement=placement, joint_normal_m=frame_inner,
                   components=components, unknown=tuple(unknown))


def installation_parts(wall, opening):
    placement = opening.doorway.exterior_placement if opening.doorway else None
    if placement is None:
        return ()
    center = opening_center(wall, opening)
    _, tangent, normal, _ = wall_frame(wall)
    parts = []
    for board in placement.boards:
        ring = tuple((center[0] + tangent[0] * (board.along_m + along)
                      + normal[0] * (board.normal_m + offset),
                      center[1] + tangent[1] * (board.along_m + along)
                      + normal[1] * (board.normal_m + offset))
                     for along, offset in ((-board.width_m / 2, -board.depth_m / 2),
                                           (board.width_m / 2, -board.depth_m / 2),
                                           (board.width_m / 2, board.depth_m / 2),
                                           (-board.width_m / 2, board.depth_m / 2)))
        parts.append(GPart(key=f"installation:{board.name}", material_key=board.material_key,
            solids=(GPrism(ring, board.z_m - board.height_m / 2,
                           board.z_m + board.height_m / 2),),
            catalog=PartCatalogRef(material_ref=board.material_ref,
                                   role="door_installation", name=board.name)))
    return tuple(parts)
