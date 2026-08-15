"""Structural screws holding furring/battens through continuous exterior insulation.

Walls and the roof are billed as two separate line items on purpose: they share the same
16 in x 24 in fastener grid, but a roof carries far more exterior foam, so its screws are a
different (longer) part. Both counts are derived from the resolved assembly stack — a wall
type is never named here, so adding a second furred-and-foamed wall type bills itself.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry import length, sub
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_catalog import (
    ROLE_EXTERIOR_INSULATION_SCREW,
    hardware_row,
    screw_for_required_length,
)
from typehaus.takeoff.hardware_config import ExteriorInsulationFastenerRules

# Float slack when a run divides evenly into its spacing (an 18 ft wall at 16 in o.c.).
_GRID_EPSILON = 1e-9


@dataclass(frozen=True)
class ExteriorInsulationFastening:
    """The screwed-strip condition found in one assembly's layer stack."""

    fastened_layer: str          # the furring/batten layer the screw head bears on
    through_thickness_m: float   # everything the screw passes through before the framing
    insulation_thickness_m: float

    def required_screw_length_in(self, rules: ExteriorInsulationFastenerRules) -> float:
        return (self.through_thickness_m / M_PER_IN) + rules.minimum_structural_embedment_in


def exterior_insulation_fastening(
    layer_stack: list, rules: ExteriorInsulationFastenerRules,
) -> "ExteriorInsulationFastening | None":
    """Find the screwed furring condition in an interior→exterior ``(function, thickness_m,
    name)`` stack, or ``None`` when the assembly has none.

    A strip only takes *structural* screws when continuous insulation holds it off the
    framing; a rainscreen batten straight over sheathing takes ordinary siding nails and is
    deliberately not billed here.
    """
    structure_indices = [index for index, (function, _, _) in enumerate(layer_stack)
                         if function in rules.structure_layer_functions]
    if not structure_indices:
        return None
    structure_index = structure_indices[-1]  # outermost structural layer carries the screw
    outboard = list(enumerate(layer_stack))[structure_index + 1:]
    fastened = [index for index, (function, _, _) in outboard
                if function in rules.fastened_layer_functions]
    if not fastened:
        return None
    fastened_index = fastened[-1]  # the outermost strip layer is the one screwed through
    between = layer_stack[structure_index + 1:fastened_index + 1]
    insulation_m = sum(thickness for function, thickness, _ in between
                       if function in rules.insulation_layer_functions)
    if insulation_m <= 0.0:
        return None
    return ExteriorInsulationFastening(
        fastened_layer=layer_stack[fastened_index][2],
        through_thickness_m=sum(thickness for _, thickness, _ in between),
        insulation_thickness_m=insulation_m,
    )


def fastener_grid_count(run_m: float, rise_m: float, strip_spacing_m: float,
                        pitch_m: float) -> int:
    """Screws on a rectangular field: strips at ``strip_spacing_m`` o.c. across ``run_m``,
    fasteners at ``pitch_m`` along each strip up ``rise_m``. Both ends of both axes are
    fastened, hence the ``+ 1`` on each — a 16 ft wall at 16 in o.c. carries 13 strips."""
    if run_m <= 0.0 or rise_m <= 0.0:
        return 0
    strips = int(math.floor(run_m / strip_spacing_m + _GRID_EPSILON)) + 1
    per_strip = int(math.floor(rise_m / pitch_m + _GRID_EPSILON)) + 1
    return strips * per_strip


def _wall_layer_stack(wall) -> list:
    """Interior→exterior ``(function, thickness_m, name)`` for a resolved wall's real
    depth layers (cavity fill shares its host layer's depth and is not a band)."""
    return [(layer.function, layer.thickness_m, layer.name) for layer in wall.depth_layers()]


def _wall_height_m(wall) -> float:
    """Cladding/furring height: exterior walls span floor-to-floor, and a raked top wall
    averages its two end elevations (the strips run the full raked face)."""
    top = ((wall.top_z0_m or wall.z1_m) + (wall.top_z1_m or wall.z1_m)) / 2.0
    return top - wall.z0_m


def exterior_insulation_screw_rows(model: ResolvedModel,
                                   rules: ExteriorInsulationFastenerRules) -> list:
    """Wall-furring and roof-batten screw lines, one row per (scope, screw length).

    Openings are not deducted: the strips do stop at a rough opening, but the added jamb,
    head, and sill furring around it takes those fasteners back, so the gross grid is the
    estimate a framer orders against.
    """
    strip_spacing_m = rules.strip_spacing_in * M_PER_IN
    pitch_m = rules.fastener_pitch_along_strip_in * M_PER_IN

    Group = dict
    groups: dict = {}

    def add(scope: str, storey: str, fastening: ExteriorInsulationFastening,
            count: int) -> None:
        if count <= 0:
            return
        required_in = fastening.required_screw_length_in(rules)
        item, length_in, part_number = screw_for_required_length(
            ROLE_EXTERIOR_INSULATION_SCREW, required_in)
        key = (scope, part_number)
        group: Group = groups.setdefault(key, {
            "item": item, "length_in": length_in, "part_number": part_number,
            "count": 0, "by_storey": Counter(), "required_in": required_in,
            "fastening": fastening,
        })
        group["count"] += count
        group["by_storey"][storey] += count
        # The governing (thickest) condition sets the screw length for the whole line.
        if required_in > group["required_in"]:
            group["required_in"], group["fastening"] = required_in, fastening

    for wall in model.walls:
        fastening = exterior_insulation_fastening(_wall_layer_stack(wall), rules)
        if fastening is None:
            continue
        run_m = length(sub(wall.axis[1], wall.axis[0]))
        add("exterior wall furring", wall.storey, fastening,
            fastener_grid_count(run_m, _wall_height_m(wall), strip_spacing_m, pitch_m))

    for roof in model.roofs:
        assembly = model.plan.library.resolve_assembly(roof.assembly)
        if assembly is None:
            continue
        stack = [(layer.function.value, layer.thickness.meters, layer.name)
                 for layer in assembly.layers]
        fastening = exterior_insulation_fastening(stack, rules)
        if fastening is None:
            continue
        # A roof plane is billed by grid density: the resolved roof carries its true sloped
        # surface area, but not a per-plane run/rise to walk a grid across.
        cell_m2 = strip_spacing_m * pitch_m
        add("roof battens", roof.storey, fastening,
            int(math.ceil(roof.surface_area_m2 / cell_m2)))

    rows = []
    for (scope, part_number), group in sorted(groups.items()):
        fastening = group["fastening"]
        rows.append(hardware_row(
            group["item"], scope=scope, count=int(group["count"]), part_number=part_number,
            size=f"{group['length_in']:g} in",
            by_storey=dict(sorted(group["by_storey"].items())),
            basis=(f"{rules.strip_spacing_in:g} in o.c. strips x "
                   f"{rules.fastener_pitch_along_strip_in:g} in o.c. fasteners through "
                   f"{fastening.insulation_thickness_m / M_PER_IN:.2f} in exterior insulation "
                   f"({fastening.through_thickness_m / M_PER_IN:.2f} in total penetration + "
                   f"{rules.minimum_structural_embedment_in:g} in embedment = "
                   f"{group['required_in']:.2f} in required)"),
        ))
    return rows
