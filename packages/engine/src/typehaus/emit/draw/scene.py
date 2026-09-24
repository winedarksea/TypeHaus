"""The 2D drawing IR — one scenegraph, two writers (ezdxf + matplotlib-PDF) (→ 20 §Drawing IR).

Pure data: frozen pydantic records, no matplotlib objects, no ezdxf handles. That purity is
what lets golden tests snapshot the IR as JSON *before* any writer runs, and guarantees the
DXF and PDF agree — all placement math happens IR-side, once. Coordinates are model-space
**inches** (INSUNITS=1), matching the DXF convention (→ 20 §DXF conventions).

Node vocabulary (resolved, → 20): Polyline | Hatch | Text | ArchDimension | Leader |
Symbol | Viewport. ``AnchorRef`` is either an element face reference ``(uid, face_role)``
or a free ``NamedPoint`` — the → 21b dimension scheme, reused by overlay anchors.

Model space, paper space, and lettering
---------------------------------------
Every node carries ``space``. ``"model"`` is the building, in the inches above. ``"paper"``
is the printed page, in paper inches measured from the sheet's lower-left corner — where a
title block, a legend and a notes column live, and where nothing may move because the
drawing's scale changed.

Text is the one thing that crosses, so the rule is stated once, here:

    **``height_pt`` wins when it is set. Otherwise ``height`` is model-space inches and
    scales with the drawing.**

A ``space="model"`` node *with* ``height_pt`` is **annotative**: it rides the geometry — it
points at a 1/2" layer and has to stay on it — but letters at a fixed printed size. That is
AutoCAD's contract and it is what the layer ladder, the seed callouts and every dimension
string want. ``space="paper"`` requires ``height_pt``, because a paper node has no scale to
be relative to.

``Leader`` crosses on purpose: ``at`` (the label end) is in the node's own space, ``to`` (the
arrow) is **always model space**, because it points at geometry. A paper-space leader is
therefore a leader from the margin into the drawing, and the writer maps ``to`` through
:class:`Frame`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field, model_serializer

from typehaus.emit.draw.palette import library_fill
from typehaus.emit.draw.typography import DIM_STRING_PT

if TYPE_CHECKING:
    from typehaus.model.plan import Library

Pt = tuple[float, float]


class _IRBase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class _Node(_IRBase):
    """Base of everything that is *drawn*. Anchors are not — see ``FaceAnchor`` below."""

    space: Literal["model", "paper"] = "model"


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


AnchorRef = FaceAnchor | NamedPoint


# --- primitives --------------------------------------------------------------
class Polyline(_Node):
    node: Literal["polyline"] = "polyline"
    points: tuple[Pt, ...]
    layer: str
    lineweight: float = 0.25  # mm
    linetype: str = "CONTINUOUS"
    closed: bool = False
    uid: str | None = None  # element provenance → XDATA
    tag: str | None = None


class Hatch(_Node):
    node: Literal["hatch"] = "hatch"
    boundary: tuple[Pt, ...]
    pattern: str  # "batt" | "rigid" | "concrete" | "lumber" | "SOLID" …
    scale: float = 1.0
    angle: float = 0.0
    layer: str = "A-WALL-PATT"
    uid: str | None = None  # hit-testing / annotation provenance (→ detail editor)
    # Material tag this fill represents. A detail reads by material, not layer function —
    # concrete, XPS, EPS and polyiso must be distinguishable at a glance — so the writers
    # resolve fill colour through ``palette.detail_fill`` rather than the pattern alone.
    material: str | None = None
    # The fill a house material authors for itself, resolved where the library is in hand
    # (``SceneBuilder(library=...)``); a writer reads it before the tag table. Serialized
    # only when set, so a library-tag hatch's JSON is unchanged.
    fill: str | None = None

    @model_serializer(mode="wrap")
    def _omit_unset_fill(self, handler):  # noqa: ANN001, ANN202
        data = handler(self)
        if isinstance(data, dict) and data.get("fill") is None:
            data.pop("fill", None)
        return data


class Text(_Node):
    node: Literal["text"] = "text"
    anchor: Pt
    content: str
    height: float = 3.0  # inches (model space); ignored when height_pt is set
    height_pt: float | None = None  # printed size, points — wins over `height`
    rotation: float = 0.0
    style: str = "ARCH"
    layer: str = "A-ANNO-TEXT"
    align: Literal["left", "center", "right"] = "left"
    uid: str | None = None  # DetailAnnotation uid for hit-testing (→ detail editor)


class ArchDimension(_Node):
    node: Literal["dimension"] = "dimension"
    kind: Literal["linear", "aligned"] = "linear"
    ends: tuple[AnchorRef, AnchorRef]
    p0: Pt  # resolved measure points (writers never re-measure)
    p1: Pt
    offset: float  # perpendicular offset of the dimension line, inches
    # A dimension is always annotative: p0/p1 are *measured* points and must stay on the
    # geometry, but the string reads at one printed size whatever the drawing's scale is.
    # 3/32" caps, the NCS minimum plotted text height.
    height_pt: float = DIM_STRING_PT
    layer: str = "A-ANNO-DIMS"
    text: str | None = None  # override; None → writer formats the measured distance
    # Label shift along the line from the segment midpoint, model inches. Non-zero only when
    # no stagger row had room: the string sits outside its extension lines on a leader.
    text_along: float = 0.0
    uid: str | None = None  # DetailAnnotation uid for hit-testing (→ detail editor)


class Leader(_Node):
    node: Literal["leader"] = "leader"
    anchor: AnchorRef
    at: Pt
    to: Pt
    text: str
    height: float = 1.6  # inches (model space), like Text.height — both writers honor it
    height_pt: float | None = None  # printed size, points — wins over `height`
    layer: str = "A-ANNO-TEXT"
    uid: str | None = None  # DetailAnnotation uid for hit-testing (→ detail editor)


class Symbol(_Node):
    node: Literal["symbol"] = "symbol"
    name: str  # "door-swing" | "north-arrow" | "fixture-*" …
    insert: Pt
    rotation: float = 0.0
    scale: float = 1.0
    layer: str = "A-ANNO-SYMB"
    params: dict[str, float] = Field(default_factory=dict)
    uid: str | None = None  # DetailAnnotation uid for hit-testing (→ detail editor)


class Viewport(_Node):
    node: Literal["viewport"] = "viewport"
    sheet: str
    window: tuple[Pt, Pt]  # model-space (min, max)
    scale: float  # e.g. 0.25 for 1/4" = 1'
    target_slice: str


IRNode = Polyline | Hatch | Text | ArchDimension | Leader | Symbol | Viewport


class Frame(_IRBase):
    """The paper the drawing is laid out on — the thing that makes a scale *chosen*.

    ``None`` on a :class:`Scene` means "no paper decided yet": the writer fits the content
    to whatever figure it likes, and the drawn scale is a consequence of how much there
    happened to be to draw. With a frame, the sheet is the independent variable and the
    drawing is placed into it.

    * ``paper`` — sheet size, paper inches (w, h).
    * ``viewport`` — (x, y, w, h) of the drawing window on that sheet, paper inches.
    * ``center`` — the model-space point that lands at the viewport's centre.
    * ``scale`` — ``sheet_writer.ARCH_SCALES``' number: paper inches per model foot.
    * ``scale_label`` — how to print it ("1-1/2\" = 1'-0\"", or ``NTS_LABEL``).
    * ``bands`` — named paper-inch rectangles reserved for chrome (notes, legend, title),
      so a paper-space node can be placed into one by name rather than by magic number.
    """

    paper: Pt
    viewport: tuple[float, float, float, float]
    center: Pt
    scale: float
    scale_label: str
    bands: dict[str, tuple[float, float, float, float]] = Field(default_factory=dict)


class Scene(_IRBase):
    """A whole 2D drawing: an ordered list of IR nodes plus a name and unit declaration."""

    name: str
    units: Literal["in", "mm"] = "in"
    nodes: tuple[IRNode, ...] = ()
    # Pre-wrapped construction-note lines that accompany the drawing but live *outside*
    # its coordinate space: bounds functions must ignore them, and each writer lays them
    # out in its own margin/panel. Putting them in ``nodes`` couples the drawing's scale
    # to the length of its prose — a 60-line note column dwarfs a 40" junction cut.
    notes: tuple[str, ...] = ()
    # The paper this drawing is laid out on. ``None`` preserves the frameless behaviour
    # exactly: the writer fits the figure to the content.
    frame: Frame | None = None
    # Internal layout intents are deliberately excluded from the serialized drawing IR.
    # They exist only between scene construction and the scale-aware sheet layout pass.
    annotation_requests: tuple[object, ...] = Field(default=(), exclude=True)
    annotation_diagnostics: tuple[object, ...] = Field(default=(), exclude=True)

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

    def __init__(self, name: str, units: Literal["in", "mm"] = "in",
                 library: Library | None = None) -> None:
        self.name = name
        self.units = units
        self._library = library
        self._nodes: list[IRNode] = []
        self._annotation_requests: list[object] = []

    def _resolved(self, node: IRNode) -> IRNode:
        """Stamp a hatch's house-authored fill: a tag the detail table does not know."""
        if not isinstance(node, Hatch) or node.fill is not None:
            return node
        fill = library_fill(self._library, node.material)
        return node.model_copy(update={"fill": fill}) if fill else node

    def add(self, node: IRNode) -> IRNode:
        node = self._resolved(node)
        self._nodes.append(node)
        return node

    def extend(self, nodes: list[IRNode]) -> None:
        self._nodes.extend(self._resolved(n) for n in nodes)

    def add_annotation_request(self, request: object) -> None:
        self._annotation_requests.append(request)

    def build(self) -> Scene:
        return Scene(name=self.name, units=self.units, nodes=tuple(self._nodes),
                     annotation_requests=tuple(self._annotation_requests))
