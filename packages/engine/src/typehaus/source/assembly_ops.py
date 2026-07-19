"""Assembly-editor write flows (WP2.4d/e, → 21b feature 7).

The assembly inspector's editor mode is *clone-and-tweak*: duplicate a picker entry — a
``library/`` preset or a project-owned assembly — into ``plan/assemblies.py`` as an inline
``Assembly(...)``, then edit it with ordinary ``assembly|layer|material`` PATCH ops through the
standard journal. The one genuinely new engine capability is the duplicate itself: it reads a
resolved preset (which may live only in ``library/``, not editable source) and serializes it
into project source via :mod:`typehaus.source.serialize`. Everything after — layer add/remove/
reorder, thickness bumps, material swaps — is a plain ``update`` op on the emitted declaration.

The blank-builder + inline-material affordances (WP2.4e) share this path: a new ``Material(...)``
is one ``add`` op to the project materials list; a blank assembly is a duplicate of an empty
stack. No schema change — the model already carries every authored field (→ 10).
"""

from __future__ import annotations

from typing import Any

from typehaus.model.assembly import Assembly, Layer
from typehaus.model.enums import LayerFunction
from typehaus.model.materials import Material
from typehaus.model.plan import PlanModel
from typehaus.model.remap import MutationResult
from typehaus.quantities.length import Length
from typehaus.source.macros import MacroError
from typehaus.source.ops import PatchOp, RawExpr
from typehaus.source.serialize import element_add_op, value_source

# Project source files the editor writes to (never ``library/``, → 21b feature 7).
ASSEMBLIES_FILE = "plan/assemblies.py"
ASSEMBLIES_LIST = "ASSEMBLIES"
MATERIALS_LIST = "MATERIALS"


def duplicate_assembly(plan: PlanModel, source_tag: str, new_tag: str) -> MutationResult:
    """Copy assembly ``source_tag`` (library or project) into project source as ``new_tag``.

    Variants are flattened against their base first, so the duplicate is a self-contained
    declaration the editor can tweak without chasing ``variant_of`` (→ 11 §Wall variation).
    """
    if new_tag == source_tag:
        raise MacroError("duplicate needs a new tag distinct from the source")
    if plan.library.assembly(new_tag) is not None:
        raise MacroError(f"assembly {new_tag!r} already exists")
    asm = plan.library.resolve_assembly(source_tag)
    if asm is None:
        raise MacroError(f"no assembly {source_tag!r} to duplicate")
    # The duplicate is a fresh base declaration — drop variant provenance.
    clone = asm.model_copy(update={"tag": new_tag, "variant_of": None, "substitute": ()})
    op = element_add_op(clone, tag=new_tag, hint_list=ASSEMBLIES_LIST,
                        hint_file=ASSEMBLIES_FILE)
    return MutationResult(ops=[op])


def add_material(plan: PlanModel, material: Material) -> MutationResult:
    """Write a new ``Material(...)`` to project materials source (WP2.4e inline material)."""
    if plan.library.material(material.tag) is not None:
        raise MacroError(f"material {material.tag!r} already exists")
    op = element_add_op(material, tag=material.tag, hint_list=MATERIALS_LIST,
                        hint_file=ASSEMBLIES_FILE)
    return MutationResult(ops=[op])


def _layer_thickness(raw: Any) -> Length:
    if isinstance(raw, str):
        return Length.parse(raw)
    from typehaus.quantities.length import m

    return m(float(raw))


def edit_assembly_layers(
    plan: PlanModel, tag: str, layers: list[dict[str, Any]]
) -> MutationResult:
    """Rewrite a project assembly's layer stack (WP2.4e layer add/remove/reorder/swap).

    The client sends the full ordered layer list — each ``{name, material, function,
    thickness}`` a plain scalar/authored-unit spec, no source syntax. Framing and control-layer
    metadata are inherited by layer *name* from the current stack, so bumping a thickness or
    reordering never silently drops a structural stud layout. Emits one ``update Assembly``
    op carrying the serialized ``Layer(...)`` tuple, riding the standard journal.
    """
    current = plan.library.assembly(tag)
    if current is None:
        raise MacroError(f"no assembly {tag!r} to edit")
    if current.variant_of is not None:
        raise MacroError(f"{tag!r} is a variant; duplicate it before editing layers")
    resolved = plan.library.resolve_assembly(tag) or current
    prior = {ly.name: ly for ly in resolved.layers}
    built: list[Layer] = []
    seen: set[str] = set()
    for spec in layers:
        try:
            name = str(spec["name"])
            material = str(spec["material"])
            function = LayerFunction(str(spec["function"]))
        except (KeyError, ValueError) as exc:
            raise MacroError(f"bad layer spec {spec!r}: {exc}") from exc
        if name in seen:
            raise MacroError(f"duplicate layer name {name!r}")
        seen.add(name)
        if plan.library.material(material) is None:
            raise MacroError(f"unknown material {material!r}")
        base = prior.get(name)
        built.append(Layer(
            name=name,
            material_ref=material,
            thickness=_layer_thickness(spec["thickness"]),
            function=function,
            framing=base.framing if base is not None else None,
            masonry=base.masonry if base is not None else None,
            control=base.control if base is not None else frozenset(),
        ))
    op = PatchOp("update", "Assembly", tag, {"layers": RawExpr(value_source(tuple(built)))})
    return MutationResult(ops=[op])


def blank_assembly(plan: PlanModel, new_tag: str) -> MutationResult:
    """Start a new assembly from an empty stack (WP2.4e).

    The no-STRUCTURE-layer state is intentionally authored — it surfaces as a visible
    integrity finding on the next resolve, never a silent invalid (→ 21b WP2.4e), so the
    editor can guide the user to add layers rather than blocking the create.
    """
    if plan.library.assembly(new_tag) is not None:
        raise MacroError(f"assembly {new_tag!r} already exists")
    empty = Assembly(tag=new_tag, layers=())
    op = element_add_op(empty, tag=new_tag, hint_list=ASSEMBLIES_LIST,
                        hint_file=ASSEMBLIES_FILE)
    return MutationResult(ops=[op])
