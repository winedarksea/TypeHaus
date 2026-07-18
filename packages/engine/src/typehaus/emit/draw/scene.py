"""The 2D drawing IR — one scenegraph, two writers (ezdxf + matplotlib-PDF) (→ 20 §Drawing IR).

Pure data: frozen pydantic records, no matplotlib objects, no ezdxf handles. That purity is
what lets golden tests snapshot the IR as JSON *before* any writer runs, and guarantees the
DXF and PDF agree — all placement math happens IR-side, once. Coordinates are model-space
**inches** (INSUNITS=1), matching the DXF convention (→ 20 §DXF conventions).

Node vocabulary (resolved, → 20): Polyline | Hatch | Text | ArchDimension | Leader |
Symbol | Viewport. ``AnchorRef`` is either an element face reference ``(uid, face_role)``
or a free ``NamedPoint`` — the → 21b dimension scheme, reused by overlay anchors.
"""

from __future__ import annotations

from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, Field

Pt = tuple[float, float]


class _IRBase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


# --- anchors -----------------------------------------------------------------
class FaceAnchor(_IRBase):
    """A reference to a resolved element face — survives geometry edits (→ 21b)."""

    kind: Literal["face"] = "face"
    uid: str
    face_role: str  # e.g. "start", "end", "center", "opening-center"


class NamedPoint(_IRBase):
    kind: Literal["point"] = "point"
    xy: Pt
    name: str = ""


AnchorRef = Union[FaceAnchor, NamedPoint]


# --- primitives --------------------------------------------------------------
class Polyline(_IRBase):
    node: Literal["polyline"] = "polyline"
    points: tuple[Pt, ...]
    layer: str
    lineweight: float = 0.25  # mm
    linetype: str = "CONTINUOUS"
    closed: bool = False
    uid: str | None = None  # element provenance → XDATA
    tag: str | None = None


class Hatch(_IRBase):
    node: Literal["hatch"] = "hatch"
    boundary: tuple[Pt, ...]
    pattern: str  # "batt" | "rigid" | "concrete" | "lumber" | "SOLID" …
    scale: float = 1.0
    angle: float = 0.0
    layer: str = "A-WALL-PATT"


class Text(_IRBase):
    node: Literal["text"] = "text"
    anchor: Pt
    content: str
    height: float = 3.0  # inches (model space)
    rotation: float = 0.0
    style: str = "ARCH"
    layer: str = "A-ANNO-TEXT"
    align: Literal["left", "center", "right"] = "left"


class ArchDimension(_IRBase):
    node: Literal["dimension"] = "dimension"
    kind: Literal["linear", "aligned"] = "linear"
    ends: tuple[AnchorRef, AnchorRef]
    p0: Pt  # resolved measure points (writers never re-measure)
    p1: Pt
    offset: float  # perpendicular offset of the dimension line, inches
    layer: str = "A-ANNO-DIMS"
    text: str | None = None  # override; None → writer formats the measured distance


class Leader(_IRBase):
    node: Literal["leader"] = "leader"
    anchor: AnchorRef
    at: Pt
    to: Pt
    text: str
    layer: str = "A-ANNO-TEXT"


class Symbol(_IRBase):
    node: Literal["symbol"] = "symbol"
    name: str  # "door-swing" | "north-arrow" | "fixture-*" …
    insert: Pt
    rotation: float = 0.0
    scale: float = 1.0
    layer: str = "A-ANNO-SYMB"
    params: dict[str, float] = Field(default_factory=dict)


class Viewport(_IRBase):
    node: Literal["viewport"] = "viewport"
    sheet: str
    window: tuple[Pt, Pt]  # model-space (min, max)
    scale: float  # e.g. 0.25 for 1/4" = 1'
    target_slice: str


IRNode = Union[Polyline, Hatch, Text, ArchDimension, Leader, Symbol, Viewport]


class Scene(_IRBase):
    """A whole 2D drawing: an ordered list of IR nodes plus a name and unit declaration."""

    name: str
    units: Literal["in", "mm"] = "in"
    nodes: tuple[IRNode, ...] = ()

    def to_json(self) -> str:
        """Deterministic JSON snapshot for golden tests (→ 20 §Drawing IR pure-data)."""
        return self.model_dump_json(indent=2)

    def by_layer(self) -> dict[str, list[IRNode]]:
        out: dict[str, list[IRNode]] = {}
        for n in self.nodes:
            out.setdefault(getattr(n, "layer", "0"), []).append(n)
        return out


class SceneBuilder:
    """Mutable accumulator that freezes into a :class:`Scene`."""

    def __init__(self, name: str, units: Literal["in", "mm"] = "in") -> None:
        self.name = name
        self.units = units
        self._nodes: list[IRNode] = []

    def add(self, node: IRNode) -> IRNode:
        self._nodes.append(node)
        return node

    def extend(self, nodes: list[IRNode]) -> None:
        self._nodes.extend(nodes)

    def build(self) -> Scene:
        return Scene(name=self.name, units=self.units, nodes=tuple(self._nodes))
