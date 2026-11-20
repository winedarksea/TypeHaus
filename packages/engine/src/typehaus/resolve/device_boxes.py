"""Device boxes, derived from the house's ``BoxStandard`` and the face a device is on (#93).

Declare once, derive everywhere — the ``TrimStandard`` pattern. The mounting comes from the
host face over the device's own band, read outermost layer first:

* bare concrete or masonry (a thin finish over it changes nothing) → ``surface``: a box on
  the face, the device on its cover, ``projection_m`` proud;
* a framed or furred cavity behind the finish → ``flush``, the box in the cavity; the box
  may be no deeper than the cavity (``electrical.box_fill`` grades it);
* a flush box an authored raceway reaches (``ConduitRun.to_ref``/``from_ref``, or a floor
  heat's ``thermostat_ref``) → ``flush_raceway``;
* cladding outermost (an exterior face) → no box: the type carries its own weatherproof one;
* a ``recessed_into_host_surface`` device inside a blind ``RoughOpening`` (a pocket) →
  ``surface`` on the recess plane (finish face + the attachment's ``normal_gap``): the box
  screws to the pocket's back and the device stands on its cover.

A row may name a ``use``: a light takes the ``"luminaire"`` row, and a type may ask for its
own (``box_use="recessed"``); with none, the general row serves. A flush box whose host stack
crosses an air-control membrane takes the ``"air-sealed"`` row (flange taped to the
membrane) ahead of any other; ``electrical.box_fill`` reports one the standard lacks.

Wall-hosted receptacles, switches and wall lights take one; data outlets, enclosures,
panels, disconnects, meters and junction boxes do not unless their type says
``device_box=True``. The box is a solid (``electrical_box``) and, where surface, part of
the device's footprint, so collision and ``integrity.wall_mount_on_face`` read both.
A row with a ``block_profile`` also derives a flat block behind each box, butting the bay's
studs (``box-block-<tag>``, billed as framing); ``advisory.box_on_stud`` reports one that
does not fit.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from typehaus.findings import Finding, Result, Severity
from typehaus.model.electrical import BoxRow, BoxStandard
from typehaus.model.nec import NEC
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry_members import member_box
from typehaus.resolve.model import FramedMember, ResolvedModel
from typehaus.resolve.wall_hosting import Band, face_frame

_BOXED_KINDS = frozenset({"receptacle", "gfci", "receptacle_240", "switch", "light"})
_TWO_GANG_SYMBOLS = frozenset({"receptacle-combined", "receptacle-quad"})
_MASONRY_HATCHES = frozenset({"concrete", "masonry"})
_SKIN_FUNCTIONS = frozenset({"finish", "membrane"})
_CID = "integrity.box_standard"
AIR_SEALED = "air-sealed"


@dataclass(frozen=True)
class BoxPlan:
    """What the host face asks for, before the device is placed."""

    mounting: str
    gangs: int
    row: BoxRow
    projection_m: float  # surface: box depth + cover rise; flush: 0
    cavity_m: float | None  # flush: depth of the cavity behind the finish
    host_layer: str
    air_barrier: bool = False  # the box breaches an air-control membrane
    recess_m: float = 0.0  # a pocket box: how far behind the finish face its back sits


@dataclass(frozen=True)
class ResolvedDeviceBox:
    device_tag: str
    device_uid: str
    storey: str
    room: str | None
    device_kind: str
    circuit: str | None
    mounting: str
    gangs: int
    box_product: str
    cover_product: str | None
    volume_in3: float | None
    width_m: float
    height_m: float
    depth_m: float
    projection_m: float
    cavity_m: float | None
    wall_tag: str | None  # None on a ceiling box
    host_layer: str
    footprint: tuple[tuple[float, float], ...]
    z0_m: float
    z1_m: float
    #: Finish-face point at the device's station and the unit normal into the room.
    face_point: tuple[float, float]
    normal: tuple[float, float]
    #: The device's own plan footprint; its canvas footprint and body band also hold a
    #: surface box (collision), so IFC and the diff read this and the mount ``z_m``.
    device_footprint: tuple[tuple[float, float], ...] = ()
    #: ``<device uid>-box``: a stable key for the record (its solid carries the same uid).
    uid: str = ""
    #: The derived block's child key on ``wall_tag``, or None (no row block, or none fits).
    block_key: str | None = None
    shape: str = "rectangular"
    #: The box breaches an air-control membrane; ``box_use`` is the row it took.
    air_barrier: bool = False
    box_use: str | None = None
    #: The row's 314.16(B)(2)/(3) facts: clamps (None = not stated) and support fittings.
    internal_clamps: bool | None = None
    support_fittings: int = 0
    terminal_blocks: int = 0
    # --- the bank (resolve/device_banks.py): every box is one; a lone device is a 1-member
    # bank. The scalar ``device_*``/``circuit`` fields above are the LEAD's (lowest uid).
    device_tags: tuple[str, ...] = ()
    device_uids: tuple[str, ...] = ()
    device_kinds: tuple[str, ...] = ()
    circuits: tuple[str | None, ...] = ()
    #: Each member's own plan footprint after the snap, aligned with ``device_tags``.
    member_footprints: tuple[tuple[tuple[float, float], ...], ...] = ()
    #: How far the snap moved each member along the wall (m, + = face tangent).
    snap_shifts_m: tuple[float, ...] = ()
    member_gangs: tuple[int, ...] = ()
    #: The derived wall plate, or None (surface cover, in-use cover, luminaire, plate_included).
    plate_product: str | None = None
    plate_family: str | None = None
    plate_openings: tuple[str, ...] = ()
    plate_size_m: tuple[float, float] | None = None  # (width, height)
    plate_thickness_m: float = 0.0
    plate_footprint: tuple[tuple[float, float], ...] = ()
    #: A pocket box (``BoxPlan.recess_m``): fed from the framing beside it, so no NM drop.
    recess_m: float = 0.0
    #: ``"ceiling"`` for a ceiling box (resolve/ceiling_boxes.py, #140): no wall, never banked;
    #: ``axis`` is its face's 3D unit normal into the room (down, or down-slope).
    host: str = "wall"
    axis: tuple[float, float, float] | None = None


def boxes_by_device(model: ResolvedModel) -> dict[str, ResolvedDeviceBox]:
    """Each boxed device's tag -> the bank box it sits in."""
    out: dict[str, ResolvedDeviceBox] = {}
    for box in model.device_boxes:
        for tag in box.device_tags or (box.device_tag,):
            out[tag] = box
    return out


_CACHE: dict[int, tuple[Any, BoxStandard | None, frozenset[str]]] = {}


def _house(plan: Any) -> tuple[BoxStandard | None, frozenset[str]]:
    """(the standard or None, device tags a raceway reaches), memoised per plan."""
    cached = _CACHE.get(id(plan))
    if cached is not None and cached[0] is plan:
        return cached[1], cached[2]
    standards, reached = [], set()
    for element in plan.all_elements():
        kind = element.element_kind
        if kind == "BoxStandard":
            standards.append(element)
        elif kind == "ConduitRun":
            reached.update(ref for ref in (element.to_ref, element.from_ref) if ref)
        elif kind == "FloorHeat" and element.thermostat_ref:
            reached.add(element.thermostat_ref)
    standard = standards[0] if len(standards) == 1 else None
    if len(_CACHE) > 8:
        _CACHE.clear()
    _CACHE[id(plan)] = (plan, standard, frozenset(reached))
    return standard, frozenset(reached)


def standard_findings(plan: Any) -> list[Finding]:
    """``integrity.box_standard``: one standard, its products real, every row a volume."""
    found = [el for el in plan.all_elements() if el.element_kind == "BoxStandard"]
    if not found:
        return []
    if len(found) > 1:
        tags = tuple(sorted(el.tag for el in found))
        return [Finding(severity=Severity.ERROR, check_id=_CID, result=Result.FAIL,
                        message=f"a house declares at most one BoxStandard; found "
                                f"{len(found)}: {', '.join(tags)}", element_tags=tags)]
    standard = found[0]
    out: list[Finding] = []
    for ref in standard.product_refs():
        if plan.library.product(ref) is None:
            out.append(_error(standard.tag, f"box standard {standard.tag} names no product "
                                            f"{ref!r}"))
    for row in standard.rows:
        if row.volume_in3 is None:
            out.append(_error(standard.tag, (
                f"box standard {standard.tag}'s {row.mounting} {row.gangs}-gang row has no "
                f"volume: name a {NEC.BOX_VOLUME_TABLE} designation or author the marked "
                "volume")))
        width, height, _depth = row.box_size
        if row.shape == "round" and abs(width.meters - height.meters) > 1e-6:
            out.append(_error(standard.tag, f"box standard {standard.tag}'s round "
                                            f"{row.box_product_ref} row needs one diameter: "
                                            "its width and height differ"))
    return out


def _error(tag: str, message: str) -> Finding:
    return Finding(severity=Severity.ERROR, check_id=_CID, message=message,
                   element_tags=(tag,), result=Result.FAIL)


def _on_ceiling(item: Any) -> bool:
    return getattr(getattr(getattr(item, "mount", None), "kind", None), "value", None) == "ceiling"


def takes_box(item: Any, product_type: Any | None) -> bool:
    """The type's ``device_box`` wins; an alarm head with a circuit takes one (NEC 300.15);
    a ceiling housing or wafer owns its j-box and a PSU-fed fitting is low voltage (#140)."""
    flag = getattr(product_type, "device_box", None)
    if flag is not None:
        return bool(flag)
    if getattr(item, "element_kind", None) == "Alarm":
        return bool(item.circuit)
    if _on_ceiling(item) and (item.mount.recessed_into_host_surface
                              or getattr(item, "psu_ref", None)):
        return False
    return getattr(getattr(item, "kind", None), "value", None) in _BOXED_KINDS


def box_use(item: Any, product_type: Any | None) -> str | None:
    """The BoxStandard row ``use`` a device asks for: its own, its type's, else by mount:
    a ceiling fan ``"fan"``, other ceiling lights ``"ceiling"``, an alarm head ``"alarm"``,
    a wall light ``"luminaire"``."""
    use = getattr(item, "box_use", None) or getattr(product_type, "box_use", None)
    if use is not None:
        return use
    if getattr(item, "element_kind", None) == "Alarm":
        return "alarm"
    if getattr(getattr(item, "kind", None), "value", None) != "light":
        return None
    if not _on_ceiling(item):
        return "luminaire"
    form = getattr(getattr(product_type, "form", None), "value", None)
    return "fan" if form == "ceiling_fan_light" else "ceiling"


def gang_count(product_type: Any | None) -> int:
    symbol = getattr(getattr(product_type, "model_representation", None), "symbol", None)
    return max(int(getattr(product_type, "gangs", 1) or 1),
               2 if symbol in _TWO_GANG_SYMBOLS else 1)


def _face_layers(wall: Any, frame: tuple, band: Band) -> list[Any]:
    """Layers present over ``band``, outermost (into the room) first."""
    point, _tangent, normal = frame

    def reach(layer: Any) -> float:
        return max((p[0] - point[0]) * normal[0] + (p[1] - point[1]) * normal[1]
                   for p in layer.polygon)

    z0, z1 = band
    present = [layer for layer in wall.layers if not layer.is_cavity and layer.polygon
               and (layer.z0_m is None or layer.z0_m < z1 + 1e-6)
               and (layer.z1_m is None or layer.z1_m > z0 - 1e-6)]
    out, seen = [], set()
    for layer in sorted(present, key=reach, reverse=True):
        if layer.source_layer_name:  # a cut layer's pieces (tee, pocket) are one layer
            if layer.source_layer_name in seen:
                continue
            seen.add(layer.source_layer_name)
        out.append(layer)
    return out


def _host(model: ResolvedModel,
          layers: list[Any]) -> tuple[str, float | None, str, bool] | None:
    """(``surface``|``flush``, cavity depth, host layer, air barrier crossed), or None.

    A flush box reaches through any furring or channel behind the finish, and through a
    membrane (sealed to an airtight box's flange), into the first framed layer, so its
    cavity is all of them together.
    """
    found = _host_layers(model, layers)
    if found is None:
        return None
    mounting, cavity, host, crossed = found
    air = mounting != "surface" and any(
        layer.function == "membrane" and "air" in layer.control for layer in crossed)
    return mounting, cavity, host, air


def _host_layers(model: ResolvedModel, layers: list[Any]):
    materials = {material.tag: material for material in model.plan.library.materials}
    cavity, host, crossed = 0.0, None, []
    for layer in layers:
        crossed.append(layer)
        hatch = getattr(materials.get(layer.material_ref), "hatch", None)
        if hatch in _MASONRY_HATCHES:
            return (("flush", cavity, host, crossed) if host
                    else ("surface", None, layer.name, crossed))
        if layer.function in _SKIN_FUNCTIONS and not host:
            continue
        # Behind furring, a second finish (the plant liner's gypsum) is cut through too.
        if layer.function in ("furring", "airgap", "membrane") or (
                host and layer.function == "finish"):
            cavity, host = cavity + layer.thickness_m, layer.name
            continue
        if layer.function == "structure":
            return "flush", cavity + layer.thickness_m, layer.name, crossed
        if host or layer.function == "insulation":
            return ((("flush", cavity, host) if host
                     else ("flush", layer.thickness_m, layer.name)) + (crossed,))
        return None  # cladding: an exterior face
    return ("flush", cavity, host, crossed) if host else None


def plan_box(model: ResolvedModel, item: Any, product_type: Any | None,
             band: Band) -> BoxPlan | None:
    """The box a wall-hosted device takes, or None (no standard, not boxed, no host)."""
    if item.element_kind != "ElectricalDevice" or not takes_box(item, product_type):
        return None
    attachment = getattr(getattr(item, "location", None), "attachment", None)
    if attachment is None or getattr(item.mount.kind, "value", None) != "wall":
        return None
    standard, reached = _house(model.plan)
    wall = model.wall(attachment.wall_ref)
    if standard is None or wall is None:
        return None
    gangs = gang_count(product_type)
    use = box_use(item, product_type)
    pocket = _pocket(model, wall, item, attachment, band)
    if pocket is not None:
        row = standard.row_for("surface", gangs, use)
        if row is None:
            return None
        projection = row.box_size[2].meters + row.cover_rise.meters
        return BoxPlan("surface", gangs, row, projection, None, pocket,
                       recess_m=-attachment.normal_gap.meters)
    host = _host(model, _face_layers(wall, face_frame(wall, attachment, band), band))
    if host is None:
        return None
    mounting, cavity, layer, air = host
    if mounting == "flush" and item.tag in reached:
        mounting = "flush_raceway"
    # An air-sealed row for the device's own use ("air-sealed-luminaire-round"), else the plain one.
    sealed = air and next((r for want in (f"{AIR_SEALED}-{use}" if use else None, AIR_SEALED)
                           for r in standard.rows if want and r.mounting == mounting
                           and r.gangs == gangs and r.use == want), None)
    row = sealed or standard.row_for(mounting, gangs, use)
    if row is None:
        return None
    width, _height, depth = (part.meters for part in row.box_size)
    projection = depth + row.cover_rise.meters if mounting == "surface" else 0.0
    return BoxPlan(mounting, gangs, row, projection, cavity, layer, air)


def _pocket(model: ResolvedModel, wall: Any, item: Any, attachment: Any,
            band: Band) -> str | None:
    """The blind rough opening a recessed device stands in, by tag, or None."""
    if not item.mount.recessed_into_host_surface or attachment.normal_gap.meters >= 0:
        return None
    station = attachment.distance_from_start.meters
    for opening in model.openings:
        if (opening.host_wall != wall.tag or opening.kind != "rough_opening"
                or not opening.depth_m):
            continue
        z0 = wall.base_ref_z_m + opening.sill_m
        if (abs(station - opening.center_along_m) <= opening.width_m / 2
                and z0 <= band[0] and band[1] <= z0 + opening.height_m):
            return opening.tag
    return None


def _derive_block(model: ResolvedModel, wall: Any, tag: str, profile: str,
                  point: tuple[float, float], tangent: tuple[float, float],
                  normal: tuple[float, float], width: float, depth: float,
                  middle: float) -> str | None:
    """A flat block behind the box, stud face to stud face; its child key, or None."""
    section = cross_section(profile)
    thick, face = section.width_m, section.depth_m
    z0, z1 = middle - face / 2, middle + face / 2
    back = -depth - thick  # the block's far face, into the wall from the finish face
    left = right = None
    for member in wall.members:
        if member.p0 != member.p1 or member.z0_m > z0 or member.z1_m < z1:
            continue
        solid = member_box(member)
        if solid is None:
            continue
        ring = [(x - point[0], y - point[1]) for x, y, _z in solid.corners_bottom]
        along = [x * tangent[0] + y * tangent[1] for x, y in ring]
        into = [x * normal[0] + y * normal[1] for x, y in ring]
        if min(into) > back + 1e-6 or max(into) < -depth:
            continue  # too shallow to hold the block, or the other face's stud
        if max(along) <= -width / 2 + 1e-6 and (left is None or max(along) > left):
            left = max(along)
        elif min(along) >= width / 2 - 1e-6 and (right is None or min(along) < right):
            right = min(along)
    if left is None or right is None:
        return None
    offset = -depth - thick / 2
    ends = [(point[0] + tangent[0] * s + normal[0] * offset,
             point[1] + tangent[1] * s + normal[1] * offset) for s in (left, right)]
    key = f"box-block-{tag}"
    block = FramedMember(wall.uid, key, "blocking", profile, ends[0], ends[1], z0, z1,
                         right - left)
    index = next(i for i, w in enumerate(model.walls) if w is wall)
    model.walls[index] = replace(wall, members=(*wall.members, block))
    return key
