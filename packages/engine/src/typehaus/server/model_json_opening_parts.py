"""Resolved opening parts for the live viewer, which extrudes these rings and derives none."""
from typehaus.resolve.door_plan_dimensions import door_plan_dimensions
from typehaus.resolve.geometry_ir import GPrism

# The viewer draws these from the opening's ``doorway`` record (sections, installation boards).
_DOORWAY_KEYS = {"doorway", "installation"}


def _r(value: float) -> float:
    return round(value, 6)


def opening_parts_json(model, opening):
    """Every product part of ``opening``: frame, leaf, glass, casing, stops and hardware."""
    element = model.geometry.by_uid(opening.uid) if model.geometry is not None else None
    if element is None:
        return None
    parts = []
    for part in element.parts:
        if part.key.split(":")[0] in _DOORWAY_KEYS:
            continue
        solids = [dict(ring=[[_r(x), _r(y)] for x, y in solid.ring],
                       z0_m=_r(solid.z0_m), z1_m=_r(solid.z1_m))
                  for solid in part.solids if isinstance(solid, GPrism)]
        if not solids:
            continue
        entry = dict(key=part.key, material_key=part.material_key, solids=solids)
        if part.catalog is not None:
            # Catalog role (hinge, passage, ...) and product name feed the inspector.
            entry.update({name: value for name, value in (
                ("material_ref", part.catalog.material_ref), ("role", part.catalog.role),
                ("name", part.catalog.name)) if value is not None})
        parts.append(entry)
    return parts or None


def sizing_json(sizing):
    """``resolve/door_sizing.DoorSizing`` for the viewer, which never re-derives it."""
    if sizing is None:
        return None
    from dataclasses import asdict

    out = asdict(sizing)
    out["basis"] = dict(sizing.basis)
    out["pocket_run_m"] = sizing.pocket_run_m
    return out


def door_plan_dimensions_json(model, opening):
    """Physical glyph dimensions; the canvas only projects these resolved measurements."""
    from dataclasses import asdict

    wall = model.wall(opening.host_wall)
    if not opening.is_door or wall is None:
        return None
    return asdict(door_plan_dimensions(opening, wall))
