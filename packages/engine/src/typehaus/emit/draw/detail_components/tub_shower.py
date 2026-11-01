"""An integral tub-shower insert in section (C7-E4, I2-005): tub, apron, surround, valve.

A ``tub-shower`` fixture is a one-piece insert, not a tiled shower: no recess, no backer,
no tile and no glass. What the cut shows is the type's own 3D massing
(``placeable_symbols.tub_shower``) sliced at the station — tub floor, apron, back rim and
the surround carried up to the type's height — so the drawing is the model. Beyond it: the
surround's nailing flange lapped onto the stud face of the wall it backs against, and the
valve at its port height, read from the type's ``VALVE-*`` ports.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.geometry import (
    layer_intervals,
    outboard_is_high,
    outermost_with_function,
    rect_region,
)
from typehaus.emit.draw.detail_components.stack_dimensions import dim, dim_text
from typehaus.emit.draw.lineweights import PROFILE, REFERENCE
from typehaus.emit.draw.scene import IRNode, Polyline, Text
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_slice import CutPlane, ring_intervals

#: The surround's nailing flange: sheet thickness and how far it laps up the stud face. A
#: drawing convention for the product class (the insert publishes no flange drawing).
FLANGE_T_IN = 0.125
FLANGE_LAP_IN = 1.0


def _cut_parts(obj, ftype, direction: str, station: float) -> list[tuple]:
    """``(u0, u1, z0, z1, color)`` inches for every massing box the plane crosses."""
    from typehaus.model.placeable_symbols import model_parts, place_local

    w, d = ftype.footprint[0].meters, ftype.footprint[1].meters
    plane = CutPlane(axis=direction, station_m=station)
    out = []
    for part in model_parts("tub-shower", w, d, ftype.height.meters):
        if part["shape"] != "box" or part["color"] == "metal":
            continue  # the riser is drawn as the valve beyond, from the type's ports
        (cx, cy, cz), (sx, sy, sz) = part["center"], part["size"]
        ring = place_local([(cx - sx / 2, cy - sy / 2), (cx + sx / 2, cy - sy / 2),
                            (cx + sx / 2, cy + sy / 2), (cx - sx / 2, cy + sy / 2)],
                           obj.position, obj.rotation_degrees)
        z0 = (obj.z_m + cz - sz / 2) / M_PER_IN
        for a, b in ring_intervals(ring, plane):
            out.append((min(a, b) / M_PER_IN, max(a, b) / M_PER_IN, z0, z0 + sz / M_PER_IN,
                        part["color"]))
    return out


def _backing_wall(model, u_edge_m: float, z_m: float, direction: str, station: float):
    """The wall whose cut face is nearest the surround's back edge, with its stud face."""
    best = None
    for wall in model.walls:
        top = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
        if not wall.z0_m <= z_m <= top:
            continue
        intervals = layer_intervals(wall, direction, station)
        stud = outermost_with_function(intervals, "structure")
        high = outboard_is_high(wall, direction, station)
        if stud is None or high is None:
            continue
        face = stud[0] if high else stud[1]  # the stud face toward the room
        gap = abs(face - u_edge_m / M_PER_IN)
        if gap < 4.0 and (best is None or gap < best[1]):
            best = (wall, gap, face)
    return best


def tub_shower_components(model, obj, ftype, direction: str, station: float) -> list[IRNode]:
    """The insert cut, its flange to the studs, the valve beyond and its strings."""
    parts = _cut_parts(obj, ftype, direction, station)
    if not parts:
        return []
    nodes: list[IRNode] = []
    for u0, u1, z0, z1, _color in parts:
        nodes += rect_region(u0, z0, u1, z1, "tub-shower-insert", "fiber-cement", None,
                             lineweight=PROFILE)
    base = obj.z_m / M_PER_IN
    lo = min(p[0] for p in parts)
    hi = max(p[1] for p in parts)
    rim = max(p[3] for p in parts if p[3] - base < ftype.height.meters / M_PER_IN * 0.5)
    top = max(p[3] for p in parts)
    # The surround's back is the side whose part runs full height.
    back_hi = any(p[1] >= hi - 1e-6 and p[3] >= top - 1e-6 for p in parts)
    edge = hi if back_hi else lo
    backing = _backing_wall(model, edge * M_PER_IN, (base + 48.0) * M_PER_IN, direction, station)
    if backing is not None:
        face = backing[2]
        sign = 1.0 if face > edge else -1.0
        nodes += rect_region(edge, top - FLANGE_T_IN, face, top, "tub-shower-flange",
                             "fiber-cement", None, lineweight=PROFILE)
        nodes += rect_region(face - sign * FLANGE_T_IN, top, face, top + FLANGE_LAP_IN,
                             "tub-shower-flange", "fiber-cement", None, lineweight=PROFILE)
        nodes.append(Text(anchor=(edge - sign * 2.0, top - 4.0), content=(
            "INTEGRAL SURROUND: NAILING FLANGE TO STUDS, GWB LAPS FLANGE"), height_pt=6.5,
            align="right" if sign > 0 else "left", layer="A-ANNO-TEXT"))
    nodes += _valve(obj, ftype, base, direction)
    nodes.append(dim((lo - 3.0, base), (lo - 3.0, rim), 0.0, f"{dim_text(rim - base)} tub"))
    nodes.append(dim((lo - 3.0, rim), (lo - 3.0, top), 0.0,
                     f"{dim_text(top - rim)} surround"))
    return nodes


def _valve(obj, ftype, base: float, direction: str) -> list[IRNode]:
    """The valve body beyond the cut, at its ports' height, dimensioned off the tub base."""
    from typehaus.model.placeable_symbols import place_local

    ports = [p for p in ftype.ports if p.tag.startswith("VALVE")]
    if not ports:
        return []
    z = base + sum(p.position[2].meters for p in ports) / len(ports) / M_PER_IN
    world = place_local([(p.position[0].meters, p.position[1].meters) for p in ports],
                        obj.position, obj.rotation_degrees)
    across = [(y if direction == "y" else x) / M_PER_IN for x, y in world]
    centre = sum(across) / len(across)
    half = max(2.0, (max(across) - min(across)) / 2.0 + 1.0)
    body = ((centre - half, z - half), (centre + half, z - half),
            (centre + half, z + half), (centre - half, z + half))
    return [Polyline(points=body, layer="A-DETL-CMPT", closed=True, lineweight=REFERENCE,
                     linetype="DASHED", tag="detail-component:tub-shower-valve"),
            Text(anchor=(centre + half + 1.0, z), content="VALVE (BEYOND)", height_pt=6.5,
                 layer="A-ANNO-TEXT"),
            dim((centre, base), (centre, z), 0.0, f"{dim_text(z - base)} valve")]
