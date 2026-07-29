"""JSON → macro dispatch for ``POST /macro`` (→ 20 §FastAPI server, → 21b §Room macros).

Turns the UI's screen-intent payload into a :class:`~typehaus.model.remap.MutationResult` by
calling the geometry-aware builders in :mod:`typehaus.source.macros`. The server then feeds the
resulting ops through the ordinary coordinator patch path, so a macro is journaled, undoable,
and revision-hash-guarded exactly like a hand op — no separate write path.
"""

from __future__ import annotations

from typing import Any

from typehaus.model.materials import Material
from typehaus.model.plan import PlanModel
from typehaus.model.remap import MutationResult
from typehaus.source import assembly_ops, detail_ops, macros


class MacroRequestError(ValueError):
    """The macro request was malformed (unknown macro, missing arg, bad geometry)."""


def build_macro_ops(plan: PlanModel, body: dict[str, Any]) -> MutationResult:
    name = body.get("macro")
    if not name:
        raise MacroRequestError("missing 'macro'")
    if name not in _LIBRARY_MACROS and not body.get("storey"):
        raise MacroRequestError("missing 'storey'")
    try:
        handler = _DISPATCH[name]
    except KeyError:
        raise MacroRequestError(
            f"unknown macro {name!r} ({', '.join(sorted(_DISPATCH))})"
        ) from None
    try:
        return handler(plan, body.get("storey", ""), body)
    except macros.MacroError as exc:
        raise MacroRequestError(str(exc)) from exc
    except (KeyError, TypeError) as exc:
        raise MacroRequestError(f"bad arguments for {name!r}: {exc}") from exc


def _xy(raw: Any) -> tuple[Any, Any]:
    if not isinstance(raw, (list, tuple)) or len(raw) != 2:
        raise MacroRequestError(f"expected an [x, y] point, got {raw!r}")
    return (raw[0], raw[1])


def _draw_wall(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.draw_wall(
        plan, storey, _xy(body["start"]), _xy(body["end"]), body["assembly"],
        hint_file=body.get("hint_file"), tag=body.get("tag"),
    )


def _move_nodes(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.move_nodes(plan, storey, list(body["nodes"]), body["dx"], body["dy"])


def _split_wall(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.split_wall(plan, storey, body["wall"], _xy(body["at"]))


def _heal_walls(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.heal_walls(plan, storey, body["node"])


def _place_opening(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.place_opening(
        plan, storey, host=body["host"], type_ref=body["type_ref"], along=body["along"],
        is_door=bool(body.get("is_door")), sill=body.get("sill"),
        hint_file=body.get("hint_file"), tag=body.get("tag"),
    )


def _place_rough_opening(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.place_rough_opening(
        plan, storey, host=body["host"], width=body["width"], height=body["height"],
        along=body["along"], sill=body.get("sill"), hint_file=body.get("hint_file"), tag=body.get("tag"),
    )


def _move_opening(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.move_opening(plan, storey, tag=body["tag"], along=body["along"])


def _rehost_opening(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.rehost_opening(plan, storey, tag=body["tag"], host=body["host"], along=body["along"])


def _place_room(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.place_room(
        plan, storey, seed=_xy(body["seed"]), occupancy=body["occupancy"],
        floor_finish=body.get("floor_finish"), hint_file=body.get("hint_file"),
        tag=body.get("tag"),
    )


def _place_stair(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.place_stair(
        plan, storey, seed=_xy(body["seed"]), to_storey=body.get("to_storey"),
        hint_file=body.get("hint_file"), tag=body.get("tag"),
    )


def _move_placeable(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.move_placeable(plan, storey, tag=body["tag"], position=_xy(body["position"]))


def _rotate_placeable(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.rotate_placeable(plan, storey, tag=body["tag"], degrees=float(body["degrees"]),
                                   free_rotation=bool(body.get("free_rotation")))


def _attach_placeable(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.attach_placeable(plan, storey, tag=body["tag"], wall=body["wall"],
                                   face=body["face"], distance=body["distance"],
                                   gap=body.get("gap", 0), rotation_offset=float(body.get("rotation_offset", 0)))


def _set_placeable_mount(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.set_placeable_mount(plan, storey, tag=body["tag"], elevation=body["elevation"])


def _detach_placeable(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.detach_placeable(plan, storey, tag=body["tag"],
                                   position=_xy(body["position"]) if body.get("position") is not None else None)


def _place_placeable(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.place_placeable(plan, storey, type_ref=body["type_ref"], position=_xy(body["position"]),
                                  hint_file=body.get("hint_file"), tag=body.get("tag"))


def _assign_placeable_room(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.assign_placeable_room(plan, storey, tag=body["tag"], room=body.get("room"))


def _duplicate_canvas_object(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.duplicate_canvas_object(plan, storey, tag=body["tag"])


def _duplicate_assembly(plan: PlanModel, _s: str, body: dict[str, Any]) -> MutationResult:
    return assembly_ops.duplicate_assembly(plan, body["source"], body["tag"])


def _blank_assembly(plan: PlanModel, _s: str, body: dict[str, Any]) -> MutationResult:
    return assembly_ops.blank_assembly(plan, body["tag"])


def _edit_assembly_layers(plan: PlanModel, _s: str, body: dict[str, Any]) -> MutationResult:
    layers = body.get("layers")
    if not isinstance(layers, list):
        raise MacroRequestError("edit_assembly_layers needs a 'layers' list")
    return assembly_ops.edit_assembly_layers(plan, body["tag"], layers)


def _seed_detail_annotations(plan: PlanModel, _s: str, body: dict[str, Any]) -> MutationResult:
    annotations = body.get("annotations")
    if not isinstance(annotations, list):
        raise MacroRequestError("seed_detail_annotations needs an 'annotations' list")
    try:
        return detail_ops.seed_detail_annotations(plan, body.get("condition_key", ""),
                                                  annotations)
    except detail_ops.MacroError as exc:
        raise MacroRequestError(str(exc)) from exc


def _add_material(plan: PlanModel, _s: str, body: dict[str, Any]) -> MutationResult:
    spec = dict(body.get("material") or {})
    if "tag" not in spec or "name" not in spec:
        raise MacroRequestError("material needs 'tag' and 'name'")
    try:
        material = Material(**spec)
    except Exception as exc:  # noqa: BLE001 - surface pydantic validation as a 400
        raise MacroRequestError(f"invalid material: {exc}") from exc
    return assembly_ops.add_material(plan, material)


_DISPATCH = {
    "draw_wall": _draw_wall,
    "move_nodes": _move_nodes,
    "split_wall": _split_wall,
    "heal_walls": _heal_walls,
    "place_opening": _place_opening,
    "place_rough_opening": _place_rough_opening,
    "move_opening": _move_opening,
    "rehost_opening": _rehost_opening,
    "place_room": _place_room,
    "place_stair": _place_stair,
    "move_placeable": _move_placeable,
    "rotate_placeable": _rotate_placeable,
    "attach_placeable": _attach_placeable,
    "set_placeable_mount": _set_placeable_mount,
    "detach_placeable": _detach_placeable,
    "place_placeable": _place_placeable,
    "assign_placeable_room": _assign_placeable_room,
    "duplicate_canvas_object": _duplicate_canvas_object,
    "duplicate_assembly": _duplicate_assembly,
    "blank_assembly": _blank_assembly,
    "edit_assembly_layers": _edit_assembly_layers,
    "add_material": _add_material,
    "seed_detail_annotations": _seed_detail_annotations,
}

# Macros that operate on the project library rather than a storey (no 'storey' required).
_LIBRARY_MACROS = frozenset({
    "duplicate_assembly", "blank_assembly", "edit_assembly_layers", "add_material",
    "seed_detail_annotations",
})
