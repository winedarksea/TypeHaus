"""One fabrication description for bench shop cuts, viewer meshes, GLB and IFC.

Local +y is the wall behind the sitter. Panels carry true thickness and blank sizes;
shaped panels additionally retain their actual profile rather than becoming blank boxes.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from typehaus.model.built_in_bench import BuiltInBenchSpec
from typehaus.model.placeable_symbols._mesh import mesh_part
from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import plate_mesh

CURVE_SEGMENTS = 12


@dataclass(frozen=True)
class BenchPart:
    name: str
    stock_kind: Literal["panel", "solid wood", "upholstery"]
    material_ref: str
    thickness_m: float
    width_m: float
    length_m: float
    grain_direction: str
    shape_note: str
    geometry: dict


def bench_parts(spec: BuiltInBenchSpec) -> tuple[BenchPart, ...]:
    width = spec.width.meters
    depth = spec.overall_depth_m
    front, rear = -depth / 2, depth / 2
    panel = spec.panel_thickness.meters
    deck = spec.deck_height.meters
    cap_z = spec.back_height.meters - spec.cap_thickness.meters
    cushion_top = deck + spec.seat_cushion_thickness.meters
    toe = spec.toe_height.meters
    pad_t = spec.back_pad_thickness.meters / math.cos(spec.recline_radians)
    parts: list[BenchPart] = []

    def back(z):
        return spec.back_front_y(z) + rear

    def add(name, kind, ref, x0, x1, profile, thickness, blank_width, blank_length,
            grain="along length", note="rectangular"):
        # The reusable plate extruder handles concave toe notches and lumbar profiles.
        mesh = plate_mesh(tuple((x0 / M_PER_IN, y / M_PER_IN, z / M_PER_IN) for y, z in profile),
                          ((x1 - x0) / M_PER_IN, 0, 0))
        geometry = mesh_part(list(mesh.positions), list(mesh.triangles), "wood")
        parts.append(BenchPart(name, kind, ref, thickness, blank_width, blank_length,
                               grain, note, geometry))

    def rectangle(y0, y1, z0, z1):
        return ((y0, z0), (y1, z0), (y1, z1), (y0, z1))

    supports = spec.internal_partition_count + 2
    support_x = [-width / 2 + index * (width - panel) / (supports - 1)
                 for index in range(supports)]
    for index, x0 in enumerate(support_x):
        profile = ((front + spec.toe_recess.meters, 0), (rear, 0),
                   (rear, deck - panel), (front + panel, deck - panel),
                   (front + panel, toe), (front + spec.toe_recess.meters, toe))
        add(f"support {index + 1}", "panel", spec.carcass_material_ref, x0, x0 + panel,
            profile, panel, depth - panel, deck - panel,
            "vertical", f"toe notch {spec.toe_height.inches:g} in high x "
            f"{(spec.toe_recess.meters - panel) / M_PER_IN:g} in from panel front edge")
        # Rear triangular webs transfer the reclined back load into the carcass.
        gusset_front = back(deck - panel) + panel / math.cos(spec.recline_radians)
        add(f"back gusset {index + 1}", "panel", spec.carcass_material_ref, x0, x0 + panel,
            ((gusset_front, deck - panel), (rear, deck - panel), (rear, cap_z)),
            panel, rear - gusset_front, cap_z - deck + panel,
            "vertical", "triangular; rake to back angle")

    deck_back = back(deck)
    add("seat deck", "panel", spec.carcass_material_ref, -width / 2, width / 2,
        rectangle(front + panel, deck_back, deck - panel, deck),
        panel, deck_back - front - panel, width,
        note=f"front edge R{spec.front_roundover_radius.inches:g} in; seal all faces")
    add("walnut front", "panel", spec.front_material_ref, -width / 2, width / 2,
        rectangle(front, front + panel, toe, deck - panel), panel, deck - panel - toe, width,
        "horizontal across bench", "solid walnut edging on exposed edges")
    add("toe closure", "panel", spec.carcass_material_ref, -width / 2 + panel, width / 2 - panel,
        rectangle(front + spec.toe_recess.meters, front + spec.toe_recess.meters + panel, 0, toe),
        panel, toe, width - 2 * panel)
    add("seat edge", "solid wood", spec.trim_material_ref, -width / 2, width / 2,
        rectangle(front, front + panel, deck - panel, deck), panel, panel, width,
        note=f"round over exposed front R{spec.front_roundover_radius.inches:g} in")
    add("back substrate", "panel", spec.carcass_material_ref, -width / 2, width / 2,
        ((back(deck), deck), (back(deck) + panel / math.cos(spec.recline_radians), deck),
         (rear, cap_z), (back(cap_z), cap_z)),
        panel, ((cap_z - deck) / math.cos(spec.recline_radians)
                + panel * math.tan(spec.recline_radians)), width,
        "horizontal across bench", "bevel ends to back angle; blank includes bevel allowance; "
        "no wall fasteners")
    cap_front = back(cap_z) - pad_t
    add("back cap", "solid wood", spec.trim_material_ref, -width / 2, width / 2,
        rectangle(cap_front, rear, cap_z, spec.back_height.meters),
        spec.cap_thickness.meters, rear - cap_front, width,
        note="eased edges; slotted fixings allow solid-wood movement")

    # A waterfall nose avoids a hard pressure ridge at the thigh; the rear follows the pad.
    radius = spec.cushion_front_radius.meters
    cushion_rear = back(cushion_top) - pad_t
    cushion = [(front + radius, deck), (cushion_rear, deck),
               (cushion_rear, cushion_top), (front + radius, cushion_top)]
    for index in range(1, CURVE_SEGMENTS + 1):
        angle = math.pi / 2 + index * math.pi / (2 * CURVE_SEGMENTS)
        cushion.append((front + radius + radius * math.cos(angle),
                        cushion_top - radius + radius * math.sin(angle)))
    cushion.append((front, deck + radius))
    for index in range(1, CURVE_SEGMENTS + 1):
        angle = math.pi + index * math.pi / (2 * CURVE_SEGMENTS)
        cushion.append((front + radius + radius * math.cos(angle),
                        deck + radius + radius * math.sin(angle)))
    # Omit the final duplicate closing point before tessellation.
    add("seat cushion", "upholstery", spec.upholstery_material_ref, -width / 2, width / 2,
        cushion[:-1], spec.seat_cushion_thickness.meters, cushion_rear - front, width,
        "fabric across bench", "waterfall nose; removable zipped cover; non-slip base")

    lower, upper = cushion_top, cap_z
    lumbar = spec.lumbar_elevation
    pad_profile = [(back(lower), lower), (back(upper), upper)]
    stations = {lower + (upper - lower) * index / CURVE_SEGMENTS
                for index in range(CURVE_SEGMENTS + 1)}
    for z in sorted(stations | {lumbar}, reverse=True):
        fraction = ((z - lower) / (lumbar - lower) if z <= lumbar
                    else (upper - z) / (upper - lumbar))
        bulge = spec.lumbar_projection.meters * math.sin(math.pi * fraction / 2) ** 2
        pad_profile.append((back(z) - pad_t - bulge, z))
    add("back pad", "upholstery", spec.upholstery_material_ref, -width / 2, width / 2,
        pad_profile, spec.back_pad_thickness.meters,
        (upper - lower) / math.cos(spec.recline_radians), width,
        "fabric across bench", "contoured removable lumbar insert; concealed height adjustment")
    return tuple(parts)


def bench_canvas_parts(spec: BuiltInBenchSpec, materials: dict) -> list[dict]:
    """Existing mesh wire format; no viewer-specific bench geometry is necessary."""
    return [{**part.geometry, "color": materials[part.material_ref].color,
             "material_ref": part.material_ref, "role": part.name,
             "grain_axis": (0, 0, 1) if part.grain_direction == "vertical" else (1, 0, 0)}
            for part in bench_parts(spec)]
