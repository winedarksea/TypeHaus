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


@register_element
class Transition(Element):
    """Binds a condition pattern to an anchored overlay recipe + continuity claims (#37).

    Post-resolve only: documents/validates; never alters geometry (#45)."""

    condition_pattern: str  # wildcard pattern over condition keys
    notes: str | None = None
    continuity: tuple[Continuity, ...] = ()
    documents_rules: tuple[str, ...] = ()  # ConstructionRule tags
    overlay: str | None = None  # overlay recipe id (2D-only, → 11b)


for _name, _obj in (
    ("Slice", Slice),
    ("Transition", Transition),
    ("ExaggerationSpec", ExaggerationSpec),
    ("Continuity", Continuity),
):
    register_constructor(_name, _obj)
