"""Small reference / marker value types used across the schema.

These are the union arms and selector helpers the dialect exposes as constructors:
``FaceRef``/``face``, ``ToRoof``, ``FollowRoof``, ``Arch``, layer-span selectors
(``outside_of``/``inside_of``/``layers``), and opening position specs
(``from_node``/``centered``).
"""

from __future__ import annotations

from typehaus.model.base import HausModel
from typehaus.quantities import Length


class FaceRef(HausModel):
    """Names an assembly face role (datum, alignment, drainage plane) — semantic, not
    a layer index (#44). e.g. ``face("sheathing-ext")``, ``face("stud-int")``,
    ``face("center")``."""

    role: str
    offset: Length | None = None


def face(role: str, offset: Length | None = None) -> FaceRef:
    return FaceRef(role=role, offset=offset)


class LayerMaterial(HausModel):
    """Swaps the material of ONE named layer on ONE wall, leaving the assembly alone.

    An assembly states the whole stack, materials included, so a wall that wants a
    different cladding *colour* without this — the same panel in a second coil colour, the
    same brick in a second body — needs a duplicate Assembly tag differing in one
    ``material_ref``. That duplicate is not free: it is a new key in every table keyed by
    assembly (``prices.toml``, the condition gates, the section goldens), all to say
    "same wall, different paint".

    Deliberately NOT a mapping: ``Wall`` is a movable element and must live in a
    ``# haus: editable`` file, and the dialect has no mapping literal
    (``source/dialect.py``). A tuple of these is dialect-legal and reads the same.

    It substitutes a material and nothing else — thickness, function, framing, banding and
    every derived geometry stay the assembly's. Use it for appearance; a layer that needs a
    different *thickness* or *function* is a different wall and wants its own assembly.
    """

    layer: str      # Layer.name within the wall's assembly
    material: str   # Material.tag to use instead of that layer's material_ref


class ToRoof(HausModel):
    """Wall top constraint terminating against a roof plane (#43; resolves in M3)."""

    roof_ref: str


class FollowRoof(HausModel):
    """Room ceiling follows the interior finish face of a Roof system (#29; M3)."""

    roof_ref: str


class Arch(HausModel):
    """Arched opening head — masonry/concrete walls only in M1 (#, → 10)."""

    rise: Length


# --- layer-span selectors for assembly variants (#35) ------------------------
class LayerSpan(HausModel):
    """Selects a contiguous layer span in the base assembly for substitution."""

    mode: str  # "outside_of" | "inside_of" | "between"
    anchor: str
    anchor_b: str | None = None


def outside_of(layer_name: str) -> LayerSpan:
    return LayerSpan(mode="outside_of", anchor=layer_name)


def inside_of(layer_name: str) -> LayerSpan:
    return LayerSpan(mode="inside_of", anchor=layer_name)


def layers(a: str, b: str) -> LayerSpan:
    return LayerSpan(mode="between", anchor=a, anchor_b=b)


# --- opening position along a wall -------------------------------------------
class OpeningPosition(HausModel):
    """Where an opening sits along its host wall."""

    mode: str  # "from_node" | "centered"
    node: str | None = None
    offset: Length | None = None


def from_node(node_tag: str, offset: Length) -> OpeningPosition:
    return OpeningPosition(mode="from_node", node=node_tag, offset=offset)


def centered() -> OpeningPosition:
    return OpeningPosition(mode="centered")


# --- embed spec for radiant floor heat (#39) ---------------------------------
class Embed(HausModel):
    mode: str  # "in_slab" | "under_subfloor"
    depth: Length | None = None


def in_slab(depth: Length) -> Embed:
    return Embed(mode="in_slab", depth=depth)


def under_subfloor() -> Embed:
    return Embed(mode="under_subfloor")
