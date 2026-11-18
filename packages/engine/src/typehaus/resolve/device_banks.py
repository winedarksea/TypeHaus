"""Gang banks and wall plates, derived from the house ``BoxStandard`` (decision #93).

Flush devices on one wall face, at one height, within ``bank_reach`` of a neighbour, share
one N-gang box and one plate. The bank centres on the midpoint of its outermost authored
centres and its members sit at ``gang_pitch`` slots about it; the source is untouched. A
lone device is a one-member bank. A flush device takes a plate (instance,
then type, then ``default_plate`` family) and its members stand off the face by the plate
thickness. Surface covers, luminaires, in-use covers and ``plate_included`` boxes take none.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from shapely.geometry import MultiPoint
from shapely.geometry.polygon import orient

from typehaus.findings import Finding, Result, Severity
from typehaus.model.electrical import BoxStandard, PlateRow
from typehaus.resolve.device_box_mesh import Opening, box_mesh
from typehaus.resolve.device_boxes import (
    BoxPlan,
    ResolvedDeviceBox,
    _derive_block,
    _house,
    gang_count,
)
from typehaus.resolve.model import ResolvedCanvasObject, ResolvedModel, ResolvedSolid
from typehaus.resolve.wall_hosting import Band, face_frame

_Z_TOLERANCE_M = 0.0127  # box centres within 1/2"
_BANKED = frozenset({"flush", "flush_raceway"})

Point = tuple[float, float]


@dataclass(frozen=True)
class PendingBox:
    """A boxed device, placed but not yet banked; ``index`` is its object's slot."""

    index: int
    item: Any
    product_type: Any | None
    plan: BoxPlan
    storey: str
    room: str | None
    band: Band


@dataclass
class _Member:
    pending: PendingBox
    point: Point
    tangent: Point
    normal: Point
    station: float  # along the tangent, absolute
    middle: float  # box-centre z
    gangs: int

    @property
    def item(self) -> Any:
        return self.pending.item


def place_banks(model: ResolvedModel, pending: list[PendingBox],
                objects: list[ResolvedCanvasObject]) -> list[Finding]:
    """Group, snap and record every boxed device; rewrite each member's object in place."""
    standard, _ = _house(model.plan)
    if standard is None or not pending:
        return []
    findings: list[Finding] = []
    members = [_member(model, p) for p in pending]
    for bank in _group(members, standard):
        row = standard.row_for(bank[0].pending.plan.mounting, sum(m.gangs for m in bank))
        if len(bank) > 1 and row is None:
            tags = tuple(m.item.tag for m in bank)
            findings.append(Finding(
                severity=Severity.ERROR, check_id="integrity.box_standard", result=Result.FAIL,
                message=f"{', '.join(tags)} form a {sum(m.gangs for m in bank)}-gang "
                        f"{bank[0].pending.plan.mounting} bank but {standard.tag} has no such "
                        "row; each keeps its own box", element_tags=tags))
            for member in bank:
                _place(model, [member], member.pending.plan, standard, objects, findings)
            continue
        plan = bank[0].pending.plan
        if len(bank) > 1:
            plan = replace(plan, row=row, gangs=sum(m.gangs for m in bank))
        _place(model, bank, plan, standard, objects, findings)
    return findings


def _member(model: ResolvedModel, pending: PendingBox) -> _Member:
    attachment = pending.item.location.attachment
    wall = model.wall(attachment.wall_ref)
    point, tangent, normal = face_frame(wall, attachment, pending.band)
    recess = pending.plan.recess_m  # a pocket box sits on the recess plane, not the face
    point = (point[0] - normal[0] * recess, point[1] - normal[1] * recess)
    return _Member(pending, point, tangent, normal, point[0] * tangent[0] + point[1] * tangent[1],
                   (pending.band[0] + pending.band[1]) / 2, gang_count(pending.product_type))


def _plated(member: _Member) -> bool:
    """Flush, not a light (its canopy covers the box), not under an in-use cover."""
    return (member.pending.plan.mounting in _BANKED and member.item.kind.value != "light"
            and not getattr(member.pending.product_type, "in_use_cover", None))


def _bankable(member: _Member) -> bool:
    return _plated(member) and member.pending.plan.row.use is None


def _group(members: list[_Member], standard: BoxStandard) -> list[list[_Member]]:
    """Chains of bankable neighbours on one face; everything else stands alone."""
    reach = standard.bank_reach.meters
    keyed: dict[tuple, list[_Member]] = {}
    banks: list[list[_Member]] = []
    for member in members:
        if not _bankable(member):
            banks.append([member])
            continue
        attachment = member.item.location.attachment
        key = (member.pending.storey, attachment.wall_ref, attachment.face,
               member.pending.plan.mounting)
        keyed.setdefault(key, []).append(member)
    for group in keyed.values():
        # Chain by station within each height cluster.
        for level in _clusters(sorted(group, key=lambda m: m.middle), lambda m: m.middle,
                               _Z_TOLERANCE_M):
            banks.extend(_clusters(sorted(level, key=lambda m: m.station),
                                   lambda m: m.station, reach))
    return banks


def _clusters(items: list[_Member], value, gap: float) -> list[list[_Member]]:
    out: list[list[_Member]] = []
    for item in items:
        if out and value(item) - value(out[-1][-1]) <= gap + 1e-9:
            out[-1].append(item)
        else:
            out.append([item])
    return out


def _plate(bank: list[_Member], plan: BoxPlan, standard: BoxStandard,
           findings: list[Finding]) -> PlateRow | None:
    if (plan.row.plate_included or not standard.plates
            or not all(_plated(m) for m in bank)):
        return None
    families = [getattr(m.item, "plate", None)
                or getattr(m.pending.product_type, "plate", None)
                or standard.default_plate for m in bank]
    if len(set(families)) > 1:
        findings.append(Finding(
            severity=Severity.WARN, check_id="integrity.device_plate", result=Result.ADVISORY,
            message=f"bank {', '.join(m.item.tag for m in bank)} names plate families "
                    f"{', '.join(sorted({str(f) for f in families}))}; one plate covers it, "
                    f"so {families[0]!r} (the first) is used",
            element_tags=tuple(m.item.tag for m in bank)))
    family = families[0]
    if family == "integral":  # the device's own strap is its plate (a 1450R)
        return None
    openings = tuple(o for m in bank for o in (
        getattr(m.pending.product_type, "plate_openings", None) or ("decora",) * m.gangs))
    row = standard.plate_for(family, openings) if family else None
    if row is None:
        findings.append(Finding(
            severity=Severity.WARN, check_id="integrity.device_plate", result=Result.UNKNOWN,
            message=f"{standard.tag} has no {family!r} plate for {'/'.join(openings)} "
                    f"({', '.join(m.item.tag for m in bank)}): no plate is drawn or billed",
            element_tags=tuple(m.item.tag for m in bank)))
    return row


def _place(model: ResolvedModel, bank: list[_Member], plan: BoxPlan, standard: BoxStandard,
           objects: list[ResolvedCanvasObject], findings: list[Finding]) -> None:
    lead = min(bank, key=lambda m: m.item.uid)
    tangent, normal = lead.tangent, lead.normal
    pitch = standard.gang_pitch.meters
    centre = (bank[0].station + bank[-1].station) / 2 if len(bank) > 1 else lead.station
    middle = sum(m.middle for m in bank) / len(bank)
    origin = (lead.point[0] + tangent[0] * (centre - lead.station),
              lead.point[1] + tangent[1] * (centre - lead.station))
    plate = _plate(bank, plan, standard, findings)
    thick = plate.thickness.meters if plate is not None else 0.0
    total, slot = sum(m.gangs for m in bank), 0
    shifts, footprints = [], []
    openings: list[Opening | None] = []
    for member in bank:
        target = (centre + (slot + (member.gangs - 1) / 2 - (total - 1) / 2) * pitch
                  if len(bank) > 1 else member.station)
        slot += member.gangs
        shift, dz = target - member.station, middle - member.middle
        dx, dy = tangent[0] * shift + normal[0] * thick, tangent[1] * shift + normal[1] * thick
        obj = objects[member.pending.index]
        moved = [(x + dx, y + dy) for x, y in obj.footprint]
        shifts.append(shift)
        footprints.append(tuple(moved))
        objects[member.pending.index] = obj = replace(
            obj, position=(obj.position[0] + dx, obj.position[1] + dy), footprint=moved,
            z_m=obj.z_m + dz,
            body_z0_m=None if obj.body_z0_m is None else obj.body_z0_m + dz,
            body_z1_m=None if obj.body_z1_m is None else obj.body_z1_m + dz)
        openings.append(_opening(obj, origin, tangent, middle))
    wall = model.wall(lead.item.location.attachment.wall_ref)
    width, height, depth = (part.meters for part in plan.row.box_size)
    near, far = (0.0, plan.projection_m) if plan.mounting == "surface" else (-depth, 0.0)
    ring = _ring(origin, tangent, normal, width, near, far)
    z0, z1 = middle - height / 2, middle + height / 2
    block_key = (_derive_block(model, wall, lead.item.tag, plan.row.block_profile, origin,
                               tangent, normal, width, depth, middle)
                 if plan.row.block_profile and plan.mounting != "surface" else None)
    plate_ring: tuple[Point, ...] = ()
    if plate is not None:
        plate_w, plate_h = (part.meters for part in plate.size)
        plate_ring = tuple(_ring(origin, tangent, normal, plate_w, 0.0, thick))
        model.solids.append(ResolvedSolid(
            uid=f"{lead.item.uid}-plate", tag=f"{lead.item.tag}-PLATE", storey=lead.pending.storey,
            category="wall_plate", outline=list(plate_ring), z0_m=middle - plate_h / 2,
            z1_m=middle + plate_h / 2, material=plate.material_ref, product=plate.product_ref,
            derived=True))  # billed in [electrical_boxes]
    item = lead.item
    model.device_boxes.append(ResolvedDeviceBox(
        device_tag=item.tag, device_uid=item.uid, storey=lead.pending.storey,
        room=lead.pending.room, device_kind=item.kind.value,
        circuit=getattr(item, "circuit", None), mounting=plan.mounting, gangs=plan.gangs,
        box_product=plan.row.box_product_ref, cover_product=plan.row.cover_product_ref,
        volume_in3=plan.row.volume_in3, width_m=width, height_m=height, depth_m=depth,
        projection_m=plan.projection_m, cavity_m=plan.cavity_m, wall_tag=wall.tag,
        host_layer=plan.host_layer, footprint=tuple(ring), z0_m=z0, z1_m=z1,
        face_point=origin, normal=normal,
        device_footprint=footprints[bank.index(lead)], uid=f"{item.uid}-box",
        block_key=block_key, shape=plan.row.shape, air_barrier=plan.air_barrier,
        box_use=plan.row.use, internal_clamps=plan.row.internal_clamps,
        support_fittings=plan.row.support_fittings, terminal_blocks=plan.row.terminal_blocks,
        device_tags=tuple(m.item.tag for m in bank), device_uids=tuple(m.item.uid for m in bank),
        device_kinds=tuple(m.item.kind.value for m in bank),
        circuits=tuple(getattr(m.item, "circuit", None) for m in bank),
        member_footprints=tuple(footprints), snap_shifts_m=tuple(shifts),
        member_gangs=tuple(m.gangs for m in bank),
        plate_openings=plate.openings if plate else (),
        plate_product=plate.product_ref if plate else None,
        plate_family=plate.family if plate else None,
        plate_size_m=tuple(p.meters for p in plate.size) if plate else None,
        plate_thickness_m=thick, plate_footprint=plate_ring, recess_m=plan.recess_m))
    model.solids.append(ResolvedSolid(
        uid=f"{item.uid}-box", tag=f"{item.tag}-BOX", storey=lead.pending.storey,
        category="electrical_box", outline=list(ring), z0_m=z0, z1_m=z1,
        product=plan.row.box_product_ref, material=plan.row.material_ref,
        body_mesh=box_mesh(origin, tangent, normal, middle, width=width, height=height,
                           depth=depth, shape=plan.row.shape, mounting=plan.mounting,
                           cover_rise=plan.row.cover_rise.meters,
                           openings=tuple(o for o in openings if o is not None)),
        derived=True))  # billed in [electrical_boxes]
    if plan.mounting == "surface":  # the device and its box collide as one
        index = bank[0].pending.index
        obj = objects[index]
        hull = orient(MultiPoint([*obj.footprint, *ring]).convex_hull, 1.0)
        objects[index] = replace(
            obj, footprint=[tuple(p) for p in list(hull.exterior.coords)[:-1]],
            body_z0_m=min(obj.body_z0_m if obj.body_z0_m is not None else z0, z0),
            body_z1_m=max(obj.body_z1_m if obj.body_z1_m is not None else z1, z1))


def _opening(obj: ResolvedCanvasObject, origin: Point, tangent: Point,
             middle: float) -> Opening | None:
    """A placed device's face in the box frame: its tangent span and z band about the centre."""
    if obj.body_z0_m is None or obj.body_z1_m is None or not obj.footprint:
        return None
    stations = [(x - origin[0]) * tangent[0] + (y - origin[1]) * tangent[1]
                for x, y in obj.footprint]
    return (min(stations), max(stations), obj.body_z0_m - middle, obj.body_z1_m - middle)


def _ring(origin: Point, tangent: Point, normal: Point, width: float, near: float,
          far: float) -> list[Point]:
    return [(origin[0] + tangent[0] * s + normal[0] * n, origin[1] + tangent[1] * s + normal[1] * n)
            for s, n in ((-width / 2, near), (width / 2, near), (width / 2, far),
                         (-width / 2, far))]
