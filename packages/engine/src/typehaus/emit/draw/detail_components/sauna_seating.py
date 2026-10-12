"""Cut placed sauna furniture using the same parts that the viewer and glTF receive.

Bench boxes and recliner ribbons are convex. Intersecting their vertex chords with
the plane and taking the convex hull therefore gives their exact section, including
slat gaps; it does not substitute a bounding box for the inclined back or mattress.
"""

from __future__ import annotations

from itertools import combinations, product

from shapely.geometry import MultiPoint, Polygon

from typehaus.emit.draw.detail_components.config import LAYER
from typehaus.emit.draw.detail_components.geometry import closed_region, rect_points, rect_region
from typehaus.emit.draw.lineweights import PROFILE
from typehaus.emit.draw.scene import IRNode, Polyline
from typehaus.model.placeable_symbols import place_local, symbol_geometry
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_slice import CutPlane, ring_intervals

SECTION_TOLERANCE_M = 1e-9
SEATING_SYMBOLS = frozenset(
    {
        "sauna-bench",
        "sauna-bench-tiered",
        "sauna-open-bench",
        "sauna-recliner",
        "sauna-recliner-mattress",
    }
)


def _part_vertices(part):
    if "mesh" in part:
        # Flat normals split triangle vertices; sectioning needs each corner only once.
        return tuple(dict.fromkeys(part["mesh"]["positions"]))
    center, size = part["center"], part["size"]
    return tuple(
        tuple(center[i] + sign[i] * size[i] / 2 for i in range(3))
        for sign in product((-1, 1), repeat=3)
    )


def _cut_part(part, obj, direction, station):
    vertices = _part_vertices(part)
    xy = place_local([(x, y) for x, y, _ in vertices], obj.position, obj.rotation_degrees)
    world = [(x, y, vertex[2] + obj.body_z0_m) for (x, y), vertex in zip(xy, vertices, strict=True)]
    fixed, along = (1, 0) if direction == "x" else (0, 1)
    hits = [(p[along], p[2]) for p in world if abs(p[fixed] - station) < SECTION_TOLERANCE_M]
    for a, b in combinations(world, 2):
        da, db = a[fixed] - station, b[fixed] - station
        if da * db >= 0:
            continue
        t = da / (da - db)
        hits.append((a[along] + t * (b[along] - a[along]), a[2] + t * (b[2] - a[2])))
    if not hits:
        return ()
    section = MultiPoint(hits).convex_hull
    if not isinstance(section, Polygon) or section.area <= SECTION_TOLERANCE_M**2:
        return ()
    return tuple((u / M_PER_IN, z / M_PER_IN) for u, z in section.exterior.coords[:-1])


def sauna_benches(model, direction: str, station: float) -> list[IRNode]:
    """Actual bench, step, reclining back and bent mattress parts crossing the cut."""
    types = {t.tag: t for t in model.plan.library.furniture_types}
    plane = CutPlane(axis=direction, station_m=station)
    nodes: list[IRNode] = []
    for obj in model.canvas_objects:
        furniture_type = types.get(obj.type_ref)
        if (
            furniture_type is None
            or furniture_type.plan_symbol not in SEATING_SYMBOLS
            or "sauna" not in (obj.room or "").lower()
            or not ring_intervals(obj.footprint, plane)
        ):
            continue
        width, depth = (length.meters for length in furniture_type.footprint)
        _, parts = symbol_geometry(
            furniture_type.plan_symbol, width, depth, obj.body_z1_m - obj.body_z0_m
        )
        for part in parts:
            ring = _cut_part(part, obj, direction, station)
            if not ring:
                continue
            tag = "sauna-bench"
            material, pattern = "sauna-shiplap", "lumber"
            if furniture_type.plan_symbol == "sauna-recliner":
                tag = "sauna-recliner"
            elif furniture_type.plan_symbol == "sauna-recliner-mattress":
                tag, material, pattern = "sauna-mattress", None, None
            elif part["color"] == "sauna-wood-dark":
                tag = "sauna-bench-leg"
            for node in closed_region(ring, tag, material, pattern, PROFILE):
                nodes.append(node.model_copy(update={"uid": obj.uid}))
    return nodes


def sauna_heaters_in_cut(model, direction: str, station: float) -> list[IRNode]:
    """Dashed body outlines locate the real heater; clearance comes from its listing."""
    types = {t.tag: t for t in model.plan.library.equipment_types}
    plane = CutPlane(axis=direction, station_m=station)
    nodes = []
    for obj in model.canvas_objects:
        equipment_type = types.get(obj.type_ref)
        if equipment_type is None or equipment_type.plan_symbol != "sauna-heater":
            continue
        for lo, hi in ring_intervals(obj.footprint, plane):
            nodes.append(
                Polyline(
                    points=rect_points(
                        lo / M_PER_IN,
                        obj.body_z0_m / M_PER_IN,
                        hi / M_PER_IN,
                        obj.body_z1_m / M_PER_IN,
                    ),
                    layer=LAYER,
                    closed=True,
                    lineweight=PROFILE,
                    linetype="DASHED",
                    uid=obj.uid,
                    tag="detail-component:sauna-heater",
                )
            )
    return nodes


def sauna_finished_ceilings_in_cut(model, direction: str, station: float) -> list[IRNode]:
    """Room-authored finished planes, including the full actual insulation/service stack."""
    plane = CutPlane(axis=direction, station_m=station)
    nodes = []
    for ceiling in model.ceilings:
        if "sauna" not in ceiling.room_ref.lower() or ceiling.z0_m is None:
            continue
        for lo, hi in ring_intervals(ceiling.outline, plane):
            z = ceiling.z0_m
            for layer in ceiling.layers:
                top = z + layer.thickness.meters
                nodes += rect_region(
                    lo / M_PER_IN,
                    z / M_PER_IN,
                    hi / M_PER_IN,
                    top / M_PER_IN,
                    "sauna-drop-ceiling",
                    layer.material_ref,
                    "lumber" if layer.framing else None,
                    lineweight=PROFILE,
                )
                z = top
    return nodes
