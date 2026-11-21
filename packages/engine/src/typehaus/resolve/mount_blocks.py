"""Exterior mounts on a metal wall (decision #142): blocks, strut pairs and strap blocks.

A device on a profiled-metal cladding face never sits on the bare panel. Its type's
``exterior_mount`` picks a 3/4" cellular-PVC block (``MountBlockRow``, ``margin`` larger all
round, head sealed, bottom open: the feed hole hides behind it) or a vertical strut pair
(the meter-main and what rides it). ``plan_standoff`` is read once at placement, so the
device stands off by exactly what is derived here. A through-panel pipe strap stands on its
laminated block (``resolve/strap_blocks.py``), cut parallel to a rake it would reach.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.resolve.wall_hosting import Band, face_frame


@dataclass(frozen=True)
class StandoffPlan:
    kind: str  # "block" | "strut"
    depth_m: float


@dataclass(frozen=True)
class ResolvedMountBlock:
    uid: str
    tag: str
    kind: str  # "block" | "strut" | "strap_block"
    wall_tag: str
    storey: str
    #: What stands on it: devices, or the strap connector.
    holds: tuple[str, ...]
    station_lo_m: float
    station_hi_m: float
    z0_m: float
    z1_m: float
    #: Proud of the crowns (block thickness, strut depth, strap-block depth).
    depth_m: float
    #: Point on the cladding's outer face at station 0, the axis tangent, the outward normal.
    origin: tuple[float, float]
    tangent: tuple[float, float]
    normal: tuple[float, float]
    product: str | None = None
    material: str | None = None
    #: A raked top: z at ``station_lo_m`` and ``station_hi_m`` (strap block under a rake).
    top_z: tuple[float, float] | None = None
    #: Where its back bears, off the crown face (negative: on the pan, behind the crowns).
    back_n_m: float = 0.0
    #: Strut: each channel's centre station; the channel width.
    channels: tuple[float, ...] = ()
    channel_width_m: float = 0.0

    @property
    def width_m(self) -> float:
        return self.station_hi_m - self.station_lo_m

    @property
    def strut_lf_m(self) -> float:
        return len(self.channels) * (self.z1_m - self.z0_m)

    def point(self, station: float, out: float, z: float) -> tuple[float, float, float]:
        return (self.origin[0] + self.tangent[0] * station + self.normal[0] * out,
                self.origin[1] + self.tangent[1] * station + self.normal[1] * out, z)


def penetration_standard(plan: Any) -> Any | None:
    from typehaus.model.penetrations import PenetrationStandard

    return next((el for el in plan.all_elements() if isinstance(el, PenetrationStandard)), None)


def is_metal_face(model: Any, wall: Any, attachment: Any, band: Band) -> bool:
    """Whether the face a device mounts on is a profiled-metal cladding (outermost)."""
    from typehaus.resolve.device_boxes import _face_layers
    from typehaus.resolve.panel_flats import cladding_layer

    clad = cladding_layer(model, wall)
    if clad is None:
        return False
    layers = _face_layers(wall, face_frame(wall, attachment, band), band)
    return bool(layers) and (layers[0].source_layer_name or layers[0].name) == (
        clad.source_layer_name or clad.name)


def plan_standoff(model: Any, item: Any, product_type: Any | None,
                  band: Band) -> StandoffPlan | None:
    """How far an exterior device stands off its metal wall, or None (not one)."""
    from typehaus.resolve.equipment_hangers import STRUT_SECTION_M

    if item.element_kind != "ElectricalDevice" or product_type is None:
        return None
    attachment = getattr(getattr(item, "location", None), "attachment", None)
    wall = model.wall(attachment.wall_ref) if attachment is not None else None
    standard = penetration_standard(model.plan)
    if wall is None or standard is None or not is_metal_face(model, wall, attachment, band):
        return None
    if getattr(product_type, "exterior_mount", "block") == "strut":
        return None if standard.strut is None else StandoffPlan("strut", STRUT_SECTION_M)
    row = standard.mount_block
    return None if row is None else StandoffPlan("block", row.thickness.meters)


def wall_face_frame(wall: Any, outward_sign: int | None = None
                    ) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """(cladding outer face at station 0, axis tangent, outward unit normal)."""
    (x0, y0), (x1, y1) = wall.axis
    length = math.hypot(x1 - x0, y1 - y0) or 1.0
    tangent = ((x1 - x0) / length, (y1 - y0) / length)
    left = (-tangent[1], tangent[0])

    def across(layer: Any) -> list[float]:
        return [(p[0] - x0) * left[0] + (p[1] - y0) * left[1] for p in layer.polygon]

    clad = [ly for ly in wall.layers if ly.function == "cladding" and ly.polygon]
    inner = [ly for ly in wall.layers if ly.function == "structure" and ly.polygon]
    sign = outward_sign
    if sign is None:
        mean_clad = sum(sum(across(ly)) / len(ly.polygon) for ly in clad) / max(len(clad), 1)
        mean_in = sum(sum(across(ly)) / len(ly.polygon) for ly in inner) / max(len(inner), 1)
        sign = 1 if mean_clad >= mean_in else -1
    offsets = [v * sign for ly in clad[-1:] for v in across(ly)]
    face = max(offsets) if offsets else 0.0
    normal = (left[0] * sign, left[1] * sign)
    return (x0 + normal[0] * face, y0 + normal[1] * face), tangent, normal


def station_of(wall: Any, xy: tuple[float, float]) -> float:
    (x0, y0), (x1, y1) = wall.axis
    length = math.hypot(x1 - x0, y1 - y0) or 1.0
    return ((xy[0] - x0) * (x1 - x0) + (xy[1] - y0) * (y1 - y0)) / length


def derive_mount_blocks(model: Any) -> None:
    """Every exterior device's block or strut pair, and every strap's block."""
    standard = penetration_standard(model.plan)
    if standard is None:
        return
    els = {el.tag: el for el in model.plan.all_elements()
           if el.element_kind == "ElectricalDevice"}
    types = {t.tag: t for t in model.plan.library.electrical_device_types}
    blocks: list[tuple[Any, Any]] = []
    struts: dict[str, list[Any]] = {}
    for obj in model.canvas_objects:
        item = els.get(obj.tag)
        if item is None or obj.body_z1_m is None:
            continue
        plan = plan_standoff(model, item, types.get(item.type_ref), (obj.body_z0_m,
                                                                     obj.body_z1_m))
        if plan is None:
            continue
        wall = model.wall(item.location.attachment.wall_ref)
        if plan.kind == "strut":
            struts.setdefault(wall.tag, []).append(obj)
        else:
            blocks.append((wall, obj))
    model.mount_blocks.extend(_merged([_device_block(standard, wall, obj)
                                       for wall, obj in blocks]))
    for wall_tag, objs in struts.items():
        model.mount_blocks.extend(_strut_pairs(standard, model.wall(wall_tag), objs))
    from typehaus.resolve.strap_blocks import strap_blocks

    model.mount_blocks.extend(strap_blocks(model, standard))


def _span(wall: Any, obj: Any) -> tuple[float, float]:
    stations = [station_of(wall, p) for p in obj.footprint]
    return min(stations), max(stations)


def _device_block(standard: Any, wall: Any, obj: Any) -> ResolvedMountBlock:
    row = standard.mount_block
    margin = row.margin.meters
    lo, hi = _span(wall, obj)
    sign = 1 if obj.attachment_face == "left" else -1
    origin, tangent, normal = wall_face_frame(wall, sign)
    return ResolvedMountBlock(
        uid=f"{obj.uid}-block", tag=f"MB-{obj.tag}", kind="block", wall_tag=wall.tag,
        storey=wall.storey, holds=(obj.tag,), station_lo_m=lo - margin,
        station_hi_m=hi + margin, z0_m=obj.body_z0_m - margin, z1_m=obj.body_z1_m + margin,
        depth_m=row.thickness.meters, origin=origin, tangent=tangent, normal=normal,
        product=row.product_ref, material=row.material_ref)


def _merged(blocks: list[ResolvedMountBlock]) -> list[ResolvedMountBlock]:
    """Overlapping blocks on one wall are one block (a hung SPD shares its box's)."""
    from dataclasses import replace

    out: list[ResolvedMountBlock] = []
    for block in sorted(blocks, key=lambda b: b.uid):
        hit = next((i for i, o in enumerate(out) if o.wall_tag == block.wall_tag
                    and o.station_lo_m < block.station_hi_m and block.station_lo_m < o.station_hi_m
                    and o.z0_m < block.z1_m and block.z0_m < o.z1_m), None)
        if hit is None:
            out.append(block)
            continue
        o = out[hit]
        out[hit] = replace(o, holds=(*o.holds, *block.holds),
                           station_lo_m=min(o.station_lo_m, block.station_lo_m),
                           station_hi_m=max(o.station_hi_m, block.station_hi_m),
                           z0_m=min(o.z0_m, block.z0_m), z1_m=max(o.z1_m, block.z1_m))
    return out


def _strut_pairs(standard: Any, wall: Any, objs: list[Any]) -> list[ResolvedMountBlock]:
    """One pair per cluster of strut-mounted devices touching along the wall."""
    from typehaus.resolve.equipment_hangers import STRUT_SECTION_M

    row = standard.strut
    width = depth = STRUT_SECTION_M
    spans = sorted(((*_span(wall, o), o) for o in objs), key=lambda t: t[0])
    clusters: list[list[tuple[float, float, Any]]] = []
    for span in spans:
        if clusters and span[0] <= max(s[1] for s in clusters[-1]) + 6 * 0.0254:
            clusters[-1].append(span)
        else:
            clusters.append([span])
    out = []
    for cluster in clusters:
        lo, hi = min(s[0] for s in cluster), max(s[1] for s in cluster)
        lead = max(cluster, key=lambda s: (s[1] - s[0], s[2].uid))[2]  # the widest: the meter
        z0 = min(s[2].body_z0_m for s in cluster) - row.end_margin.meters
        z1 = max(s[2].body_z1_m for s in cluster) + row.end_margin.meters
        inset = row.side_inset.meters
        sign = 1 if lead.attachment_face == "left" else -1
        origin, tangent, normal = wall_face_frame(wall, sign)
        out.append(ResolvedMountBlock(
            uid=f"{lead.uid}-strut", tag=f"MS-{lead.tag}", kind="strut", wall_tag=wall.tag,
            storey=wall.storey, holds=tuple(s[2].tag for s in cluster), station_lo_m=lo,
            station_hi_m=hi, z0_m=z0, z1_m=z1, depth_m=depth, origin=origin,
            tangent=tangent, normal=normal, product=row.product_ref,
            material=row.material_ref, channels=(lo + inset, hi - inset),
            channel_width_m=width))
    return out


def _xy(origin: tuple[float, float], tangent: tuple[float, float],
        station: float) -> tuple[float, float]:
    return origin[0] + tangent[0] * station, origin[1] + tangent[1] * station
