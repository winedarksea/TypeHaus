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
