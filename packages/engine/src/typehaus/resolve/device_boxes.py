"""Device boxes, derived from the house's ``BoxStandard`` and the face a device is on (#93).

Declare once, derive everywhere — the ``TrimStandard`` pattern. The mounting comes from the
host face over the device's own band, read outermost layer first:

* bare concrete or masonry (a thin finish over it changes nothing) → ``surface``: a box on
  the face, the device on its cover, ``projection_m`` proud;
* a framed or furred cavity behind the finish → ``flush``, the box in the cavity; the box
  may be no deeper than the cavity (``electrical.box_fill`` grades it);
* a flush box an authored raceway reaches (``ConduitRun.to_ref``/``from_ref``, or a floor
  heat's ``thermostat_ref``) → ``flush_raceway``;
* cladding outermost (an exterior face) → no box: the type carries its own weatherproof one.

Wall-hosted receptacles, switches and wall lights take one; data outlets, enclosures,
panels, disconnects, meters and junction boxes do not unless their type says
``device_box=True``. The box is a solid (``electrical_box``) and, where surface, part of
the device's footprint, so collision and ``integrity.wall_mount_on_face`` read both.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shapely.geometry import MultiPoint
from shapely.geometry.polygon import orient

from typehaus.findings import Finding, Result, Severity
from typehaus.model.electrical import BoxRow, BoxStandard
from typehaus.resolve.model import ResolvedModel, ResolvedSolid
from typehaus.resolve.wall_hosting import Band, face_frame

_BOXED_KINDS = frozenset({"receptacle", "gfci", "receptacle_240", "switch", "light"})
_TWO_GANG_SYMBOLS = frozenset({"receptacle-combined", "receptacle-quad"})
_MASONRY_HATCHES = frozenset({"concrete", "masonry"})
_SKIN_FUNCTIONS = frozenset({"finish", "membrane"})
_CID = "integrity.box_standard"


@dataclass(frozen=True)
class BoxPlan:
    """What the host face asks for, before the device is placed."""

    mounting: str
    gangs: int
    row: BoxRow
    projection_m: float  # surface: box depth + cover rise; flush: 0
    cavity_m: float | None  # flush: depth of the cavity behind the finish
    host_layer: str


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
    wall_tag: str
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
                f"volume: name a Table 314.16(A) designation or author the marked volume")))
    return out


def _error(tag: str, message: str) -> Finding:
    return Finding(severity=Severity.ERROR, check_id=_CID, message=message,
                   element_tags=(tag,), result=Result.FAIL)


def takes_box(item: Any, product_type: Any | None) -> bool:
    flag = getattr(product_type, "device_box", None)
    if flag is not None:
        return bool(flag)
    return getattr(getattr(item, "kind", None), "value", None) in _BOXED_KINDS


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
    return sorted(present, key=reach, reverse=True)


def _host(model: ResolvedModel, layers: list[Any]) -> tuple[str, float | None, str] | None:
    """(``surface``|``flush``, cavity depth, host layer) off the face, or None for no box.

    A flush box reaches through any furring or channel behind the finish, and through a
    membrane (sealed to an airtight box's flange), into the first framed layer, so its
    cavity is all of them together.
    """
    materials = {material.tag: material for material in model.plan.library.materials}
    cavity, host = 0.0, None
    for layer in layers:
        hatch = getattr(materials.get(layer.material_ref), "hatch", None)
        if hatch in _MASONRY_HATCHES:
            return ("flush", cavity, host) if host else ("surface", None, layer.name)
        if layer.function in _SKIN_FUNCTIONS and not host:
            continue
        if layer.function in ("furring", "airgap", "membrane"):
            cavity, host = cavity + layer.thickness_m, layer.name
            continue
        if layer.function == "structure":
            return "flush", cavity + layer.thickness_m, layer.name
        if host or layer.function == "insulation":
            return ("flush", cavity, host) if host else ("flush", layer.thickness_m, layer.name)
        return None  # cladding: an exterior face
    return ("flush", cavity, host) if host else None


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
    host = _host(model, _face_layers(wall, face_frame(wall, attachment, band), band))
    if host is None:
        return None
    mounting, cavity, layer = host
    if mounting == "flush" and item.tag in reached:
        mounting = "flush_raceway"
    gangs = gang_count(product_type)
    row = standard.row_for(mounting, gangs)
    if row is None:
        return None
    width, _height, depth = (part.meters for part in row.box_size)
    projection = depth + row.cover_rise.meters if mounting == "surface" else 0.0
    return BoxPlan(mounting, gangs, row, projection, cavity, layer)


def place_box(model: ResolvedModel, item: Any, plan: BoxPlan, storey: str, room: str | None,
              device_footprint: list[tuple[float, float]], body: Band) -> list[tuple[float, float]]:
    """Record the box and its solid; return the device footprint grown to include it."""
    attachment = item.location.attachment
    wall = model.wall(attachment.wall_ref)
    point, tangent, normal = face_frame(wall, attachment, body)
    width, height, depth = (part.meters for part in plan.row.box_size)
    near, far = (0.0, plan.projection_m) if plan.mounting == "surface" else (-depth, 0.0)
    ring = [(point[0] + tangent[0] * s + normal[0] * n, point[1] + tangent[1] * s + normal[1] * n)
            for s, n in ((-width / 2, near), (width / 2, near), (width / 2, far),
                         (-width / 2, far))]
    middle = (body[0] + body[1]) / 2
    z0, z1 = middle - height / 2, middle + height / 2
    model.device_boxes.append(ResolvedDeviceBox(
        device_tag=item.tag, device_uid=item.uid, storey=storey, room=room,
        device_kind=item.kind.value, circuit=getattr(item, "circuit", None),
        mounting=plan.mounting, gangs=plan.gangs, box_product=plan.row.box_product_ref,
        cover_product=plan.row.cover_product_ref, volume_in3=plan.row.volume_in3,
        width_m=width, height_m=height, depth_m=depth, projection_m=plan.projection_m,
        cavity_m=plan.cavity_m, wall_tag=wall.tag, host_layer=plan.host_layer,
        footprint=tuple(ring), z0_m=z0, z1_m=z1, face_point=point, normal=normal,
        device_footprint=tuple(device_footprint), uid=f"{item.uid}-box"))
    model.solids.append(ResolvedSolid(
        uid=f"{item.uid}-box", tag=f"{item.tag}-BOX", storey=storey, category="electrical_box",
        outline=list(ring), z0_m=z0, z1_m=z1, product=plan.row.box_product_ref,
        derived=True))  # billed in [electrical_boxes]; drawn and exported, not cut or measured
    if plan.mounting != "surface":
        return device_footprint
    hull = orient(MultiPoint([*device_footprint, *ring]).convex_hull, 1.0)
    return [tuple(p) for p in list(hull.exterior.coords)[:-1]]
