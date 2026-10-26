"""Bounds of placeables and openings as the IFC emitter places them (the baseline side)."""

from __future__ import annotations

from typehaus.resolve.geometry_ir import GSweep
from typehaus.resolve.model import ResolvedModel


def _bounds(
    points: list[tuple[float, float]], z0: float, z1: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if not points:
        return ((0.0, 0.0, (z0 + z1) / 2), (0.0, 0.0, z1 - z0))
    # ``points`` is a list of 2-tuples by annotation and by every caller, so the transpose
    # is square; strict= turns a stray 3-tuple into a loud error instead of a dropped axis.
    xs, ys = zip(*points, strict=True)
    minimum, maximum = (min(xs), min(ys), z0), (max(xs), max(ys), z1)
    return (tuple((minimum[index] + maximum[index]) / 2 for index in range(3)),
            tuple(maximum[index] - minimum[index] for index in range(3)))  # type: ignore[return-value]


def _emitted_parts_bounds(model: ResolvedModel, item, hosted_countertops, base_z_m: float):
    """Bounds of a furniture or fixture the emitter draws from generated parts, else None."""
    from typehaus.emit.ifc.architectural import is_parts_fixture, is_parts_furniture
    from typehaus.model.canvas import model_symbol_for
    from typehaus.model.placeable_symbols import model_parts

    furniture = next((t for t in model.plan.library.furniture_types if t.tag == item.type_ref),
                     None)
    if (furniture is not None and getattr(furniture, "built_in_bench", None) is None
            and is_parts_furniture(furniture)):
        # Hosted countertops drop their counter-coloured parts (emit/ifc/architectural).
        parts = [part for part in model_parts(
            model_symbol_for(furniture), *(d.meters for d in furniture.footprint),
            furniture.height.meters)
            if item.tag not in hosted_countertops or part.get("color") != "counter"]
        return _parts_bounds(parts, item.position, item.rotation_degrees, base_z_m)
    fixture = next((t for t in model.plan.library.fixture_types if t.tag == item.type_ref), None)
    symbol = model_symbol_for(fixture) if fixture is not None else None
    if is_parts_fixture(symbol):
        parts = model_parts(symbol, fixture.footprint[0].meters, fixture.footprint[1].meters,
                            fixture.height.meters)
        return _parts_bounds(parts, item.position, item.rotation_degrees, base_z_m)
    return None


def _parts_bounds(parts, position, rotation_degrees: float, base_z_m: float):
    """Bounds of generated placeable parts, placed as the emitter places them."""
    from typehaus.model.placeable_symbols import place_local

    local_vertices: list[tuple[float, float, float]] = []
    for part in parts:
        mesh = part.get("mesh")
        if mesh is not None:
            local_vertices.extend(mesh["positions"])
            continue
        center_x, center_y, center_z = part["center"]
        size_x, size_y, size_z = part["size"]
        local_vertices.extend(
            (center_x + x * size_x / 2, center_y + y * size_y / 2,
             center_z + z * size_z / 2)
            for x, y, z in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))
        )
    if not local_vertices:
        return _bounds([], base_z_m, base_z_m)
    world_xy = place_local([(x, y) for x, y, _z in local_vertices], position,
                           rotation_degrees)
    z_values = [base_z_m + z for _x, _y, z in local_vertices]
    return _bounds(world_xy, min(z_values), max(z_values))


def _cased_filling(opening, door_type) -> bool:
    """Whether the emitter sweeps this door's own solids (``emit/ifc/architectural``)."""
    product = door_type.bookcase_door if door_type is not None else None
    return (opening.doorway is not None or opening.cased_product is not None
            or bool(door_type and (door_type.hardware or door_type.field_finish))
            or (product is None and bool(opening.effective_frame_material_ref
                                         or opening.effective_leaf_material_ref)))


def _cased_door_bounds(model: ResolvedModel, opening):
    """Bounds of a cased or doorway door's solids, as ``cased_door_representation`` sweeps them."""
    points: list[tuple[float, float]] = []
    zs: list[float] = []
    for part in model.geometry.by_uid(opening.uid).parts:
        if part.key.startswith("hardware:"):
            continue  # emitted as its own IfcDiscreteAccessory
        for solid in part.solids:
            if isinstance(solid, GSweep):
                ex, ey, _ = solid.extrude
                for x, y, z in solid.profile:
                    points += [(x, y), (x + ex, y + ey)]
                    zs.append(z)
            else:
                points += [tuple(point) for point in solid.ring]
                zs += [solid.z0_m, solid.z1_m]
    return _bounds(points, min(zs), max(zs))
