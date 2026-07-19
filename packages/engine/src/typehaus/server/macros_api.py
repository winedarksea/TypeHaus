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
from typehaus.source import assembly_ops, macros


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


def _place_room(plan: PlanModel, storey: str, body: dict[str, Any]) -> MutationResult:
    return macros.place_room(
        plan, storey, seed=_xy(body["seed"]), occupancy=body["occupancy"],
        floor_finish=body.get("floor_finish"), hint_file=body.get("hint_file"),
        tag=body.get("tag"),
    )


def _duplicate_assembly(plan: PlanModel, _s: str, body: dict[str, Any]) -> MutationResult:
    return assembly_ops.duplicate_assembly(plan, body["source"], body["tag"])


def _blank_assembly(plan: PlanModel, _s: str, body: dict[str, Any]) -> MutationResult:
    return assembly_ops.blank_assembly(plan, body["tag"])


def _edit_assembly_layers(plan: PlanModel, _s: str, body: dict[str, Any]) -> MutationResult:
    layers = body.get("layers")
    if not isinstance(layers, list):
        raise MacroRequestError("edit_assembly_layers needs a 'layers' list")
    return assembly_ops.edit_assembly_layers(plan, body["tag"], layers)


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
    "place_room": _place_room,
    "duplicate_assembly": _duplicate_assembly,
    "blank_assembly": _blank_assembly,
    "edit_assembly_layers": _edit_assembly_layers,
    "add_material": _add_material,
}

# Macros that operate on the project library rather than a storey (no 'storey' required).
_LIBRARY_MACROS = frozenset({
    "duplicate_assembly", "blank_assembly", "edit_assembly_layers", "add_material",
})
