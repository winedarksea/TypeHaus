"""Views & transitions: Slice, Transition, condition keys (#36/#37, → 11b)."""

from __future__ import annotations

from typehaus.model.base import Element, HausModel
from typehaus.model.enums import ConditionKind, SliceKind
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Point2D


class ExaggerationSpec(HausModel):
    """Thin-layer exaggeration with true-dimension labels (#36)."""

    min_draw_thickness: Length
    label_true: bool = True


@register_element
class Slice(Element):
    """One view mechanism for plans/sections/details over the resolved model (#36).

    Plan slices are auto-scaffolded per storey; sections/details are authored."""

    kind: SliceKind
    storey: str | None = None  # for plan slices
    cut_origin: Point2D | None = None  # section/detail cut plane origin
    cut_direction: str | None = None  # "x" | "y" for section
    crop: tuple[Point2D, Point2D] | None = None
    scale: str = "1/4\"=1'"
    exaggeration: ExaggerationSpec | None = None
    simplified_poche: bool = False  # conventional gray-box plan for jurisdictions
    title: str | None = None  # sheet name override (→ Permit-ready plan set Phase 6)
    condition_key: str | None = None  # authored DETAIL claims this condition, suppressing
    # its auto-scaffold (→ 11b transition details)


class ConditionKey(HausModel):
    """A derived boundary-condition key: junction kind + participating assemblies (#37).

    Produced by the resolver, matched by Transition condition patterns."""

    kind: ConditionKind
    assemblies: tuple[str, ...]  # participating assembly tags, sorted
    detail: str = ""  # extra discriminator (e.g. "rim", "width-change")


class Continuity(HausModel):
    """A declared control-layer continuity claim a Transition makes (→ 11b)."""

    control: str  # "air" | "water" | "vapor" | "thermal"
    from_face: str
    to_face: str


class LayerJoin(HausModel):
    """A per-layer termination at a junction — Revit layer extension distance (→ 11b).

    ``layer`` is a name/function glob (fnmatch) over the participating assembly's layers;
    ``side`` names which participant ("from"|"to", matching :class:`Continuity`); a signed
    ``termination`` offset from the interface plane (+ extends past it, - stops short);
    an optional ``treatment`` id (e.g. "spray-foam", "sealant", "tape", "flashing")."""

    layer: str  # fnmatch glob over layer name / function
    side: str  # "from" | "to"
    termination: Length  # signed offset from interface plane; + extends past
    treatment: str | None = None


@register_element
class Transition(Element):
    """Binds a condition pattern to an anchored overlay recipe + continuity claims (#37).

    Post-resolve only: documents/validates; never alters geometry (#45)."""

    condition_pattern: str  # wildcard pattern over condition keys
    notes: str | None = None
    continuity: tuple[Continuity, ...] = ()
    documents_rules: tuple[str, ...] = ()  # ConstructionRule tags
    overlay: str | None = None  # default-annotation seed-set id (→ 11b transition details)
    joins: tuple[LayerJoin, ...] = ()  # per-layer terminations (Revit extension distances)


@register_element
class DetailAnnotation(Element):
    """An authored 2D annotation on a transition detail — note/leader/dimension (→ 11b).

    Anchored to a resolved element face ``(anchor_uid, anchor_face)`` plus a 2D slice-frame
    ``offset`` relative to the anchor point, so it rides the anchor when geometry changes.
    Unresolvable anchor → ``detail.anchor_unresolved`` finding, never a silently stale note.
    Edited via ordinary PatchOps (generic over any registered element kind)."""

    condition_key: str
    kind: str  # "note" | "leader" | "dimension"
    anchor_uid: str
    anchor_face: str
    offset: Point2D | None = None  # slice-frame offset from anchor point
    text: str = ""


for _name, _obj in (
    ("Slice", Slice),
    ("Transition", Transition),
    ("DetailAnnotation", DetailAnnotation),
    ("ExaggerationSpec", ExaggerationSpec),
    ("Continuity", Continuity),
    ("LayerJoin", LayerJoin),
):
    register_constructor(_name, _obj)
