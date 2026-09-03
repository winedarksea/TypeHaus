"""The one reduction from an element to the :class:`~typehaus.model.assembly.ConcreteSpec`
that governs its pour.

A ``ConcreteSpec`` is authored on the STRUCTURE layer of an ``Assembly``, which is where
``material_ref="concrete"`` already lives and where ``assembly_material.py::
assembly_structure_material`` already says "this is a concrete pour". Every consumer —
``engineering/retaining_basis``, ``engineering/deck_post``, the durability check, the
reinforcement takeoff — asks *here* and never walks the layer stack itself. Two spellings of
one lookup is how the section detail and the calc come to disagree about what was poured.

Deliberately **no element-level ``concrete`` field**. A pour's mix belongs to its assembly:
that is what makes "these four piers are the F3+C2 mix" a single authored fact instead of
four that can drift apart, and it is why an assembly-less pour has to be given an assembly
rather than a spec of its own.
"""

from __future__ import annotations

from typing import Any

from typehaus.model.assembly import ConcreteSpec


def concrete_spec_for(plan: Any, element: Any) -> ConcreteSpec | None:
    """The ``ConcreteSpec`` governing ``element``'s pour, or ``None``.

    ``None`` means one of three genuinely different things, and the caller must not collapse
    them into a default: the element names no assembly, the assembly it names has no
    concrete layer, or that layer states no spec. All three are "this model does not say",
    which is an UNKNOWN to report and never a mix to assume.
    """
    return concrete_spec_of(plan, getattr(element, "assembly", None))


def concrete_spec_of(plan: Any, assembly_tag: str | None) -> ConcreteSpec | None:
    """``concrete_spec_for`` by assembly tag, for a caller that has the tag and not the element."""
    if not assembly_tag:
        return None
    assembly = plan.library.resolve_assembly(assembly_tag)
    if assembly is None or not assembly.layers:
        return None
    index = assembly.structure_index()
    layers = assembly.layers
    ordered = ([layers[index]] + [ly for i, ly in enumerate(layers) if i != index]
               if index is not None else list(layers))
    for layer in ordered:
        spec: ConcreteSpec | None = layer.concrete
        if spec is not None:
            return spec
    return None


def cover_in(spec: ConcreteSpec | None) -> float | None:
    """``spec``'s specified cover in inches, or ``None`` where it states none."""
    if spec is None or spec.cover is None:
        return None
    return float(spec.cover.inches)


def fc_psi(spec: ConcreteSpec | None) -> float | None:
    """``spec``'s specified f'c, or ``None`` where there is no spec at all."""
    return None if spec is None else float(spec.fc_psi)


def cover_for(plan: Any, element: Any) -> tuple[float | None, str | None]:
    """The clear cover governing ``element``'s bar, in inches, and where it was authored.

    **The element's own schedule wins over its mix**, and that order is the whole point of
    this function. Cover is a property of a *face*: a footing cast against soil wants 3",
    the formed face of the wall standing on it wants 2", and both are poured from the same
    ticket. A ``ConcreteSpec`` is that ticket — one mix serving many elements — so a cover
    written on it can only ever be the house default, and the ``ReinforcementSpec`` on the
    element is the one place a per-face figure can be stated at all.

    Before this existed the precedence ran the other way by accident: every calc read
    ``ConcreteSpec.cover`` and nothing read ``ReinforcementSpec.cover``, so the 2" authored
    on catlin's retaining stems was inert (the ACI table fallback happened to return 2" as
    well, which is how it went unnoticed) and the basement walls silently took the buried
    mix's cast-against-earth 3" on a formed face.

    Returns ``(None, None)`` where neither states one — the caller falls back to the ACI
    Table 20.5.1.3.1 minimum for the bar, and says so in its citation.
    """
    schedule = getattr(element, "reinforcement", None)
    authored = getattr(schedule, "cover", None) if schedule is not None else None
    if authored is not None:
        return float(authored.inches), "its reinforcement schedule"
    mix = cover_in(concrete_spec_for(plan, element))
    return (mix, "its mix") if mix is not None else (None, None)
