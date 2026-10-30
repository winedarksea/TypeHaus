"""Shared authored door parts for the live viewer's product path."""
from typehaus.resolve.geometry_ir import GPrism

_PRODUCT_KEYS = {"leaf", "frame", "mullion", "glass", "hardware", "stop", "jamb_liner"}


def authored_product_parts(model, opening):
    spec = next((spec for spec in model.plan.library.door_types
                 if spec.tag == opening.type_ref), None)
    if not opening.is_door or spec is None or not (spec.hardware or spec.field_finish):
        return None
    return [dict(key=part.key, material_key=part.material_key,
                 material_ref=part.catalog.material_ref if part.catalog else None,
                 role=part.catalog.role if part.catalog else None,
                 name=part.catalog.name if part.catalog else None,
                 solids=[dict(ring=solid.ring, z0_m=solid.z0_m, z1_m=solid.z1_m)
                         for solid in part.solids if isinstance(solid, GPrism)])
            for part in model.geometry.by_uid(opening.uid).parts
            if part.key.split(":")[0] in _PRODUCT_KEYS]


def sizing_json(sizing):
    """``resolve/door_sizing.DoorSizing`` for the viewer, which never re-derives it."""
    if sizing is None:
        return None
    from dataclasses import asdict

    out = asdict(sizing)
    out["basis"] = dict(sizing.basis)
    out["pocket_run_m"] = sizing.pocket_run_m
    return out
