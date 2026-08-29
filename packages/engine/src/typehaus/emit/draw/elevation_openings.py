"""Window and door elevation glyphs, driven by the product type (→ 30 §Elevations).

The projector already draws every opening's *geometry* — frame, glass, exterior casing, leaf,
mullion, sliding stile — because ``resolve/geometry_openings.py`` builds all of it. What
geometry cannot say is how the thing **works**, and that is the whole content of an elevation
window: a fixed unit and a casement of identical size project to the same rectangle. The
operation lives on the type (``model/types.py``: :class:`DoorType.operation`,
:class:`WindowType.operation`, ``glazed``, ``tempered``), so this module reads the type and
adds the conventional overlay on top of the projected linework.

Conventions used here
---------------------
* **The operation symbol is a dashed triangle whose apex is the hinge**, drawn on
  ``A-GLAZ-SASH``. Casement: apex on the hinge jamb, base on the opposite stile. Awning:
  hinged at the head, so the apex is at the top. Hopper is the same figure inverted, and a
  tilt-turn — which is both — gets both.
* **Which jamb is the hinge is not modelled**, and a house is entitled to hang its casements
  either way. The convention taken is *the jamb further from the middle of the host wall*,
  because that is the one that makes a mirrored pair of units draw as a mirrored pair of
  symbols, which is what a symmetric facade wants. Say so on the schedule if it matters.
* A **double-hung** shows its meeting rail, a **slider** its mullion; neither takes a triangle,
  because neither swings.
* A **door** gets a recessed panel line and a hardware mark at :data:`_HARDWARE_HEIGHT_M`, the
  ANSI lever height. A sectional overhead door gets its panel joints instead — that *is* what
  reads as a garage door in elevation.

Everything is clipped to the opening's own visible region, which the occlusion pass has
already worked out, so a window behind the garage adds no lines to the sheet.
"""

from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import LineString, Polygon, box
from shapely.geometry.base import BaseGeometry

from typehaus.emit.draw.elevation_project import ElevationView, VisiblePiece
from typehaus.emit.draw.scene import Polyline, SceneBuilder
from typehaus.model.enums import DoorOperation, WindowOperation
from typehaus.model.types import DoorType, WindowType
from typehaus.quantities import M_PER_IN
from typehaus.resolve import overlay
from typehaus.resolve.model import ResolvedModel, ResolvedOpening, ResolvedWall

#: Lever/lockset height above the door's own threshold. ANSI A117.1 puts operable hardware at
#: 34"-48"; 36" is the middle of that band and what a door schedule draws.
_HARDWARE_HEIGHT_M = 0.9144

#: Length of the hardware mark, and its inset from the latch stile.
_HARDWARE_MARK_M = 0.1016  # 4"
_HARDWARE_INSET_M = 0.0762  # 3"

#: A sectional overhead door's panel height — the joint that makes a garage door read as one.
_SECTIONAL_PANEL_M = 0.5334  # 21"

#: Inset of a door's recessed panel line from the leaf edge.
_DOOR_PANEL_INSET_M = 0.1016  # 4"

#: A glyph is skipped below this width or height: at a 14" x 24" unit the triangle, the rail
#: and the panel line all land inside the frame's own linework and only thicken it.
_MIN_GLYPH_M = 0.3048  # 12"

#: An opening whose in-plane width collapses to less than this fraction of its true width is
#: being seen edge-on — its host wall is perpendicular to this elevation — and has no glyph.
_IN_PLANE_FRACTION = 0.9

_GLYPH_WEIGHT = 0.18
_SASH_LAYER = "A-GLAZ-SASH"
_DOOR_LAYER = "A-DOOR"


@dataclass(frozen=True)
class _Panel:
    """One opening resolved into the elevation's own (u, z) rectangle, plus its clip region."""

    opening: ResolvedOpening
    u0: float
    z0: float
    u1: float
    z1: float
    hinge_u: float  # the jamb an operation symbol hinges on
    visible: BaseGeometry

    @property
    def width(self) -> float:
        return self.u1 - self.u0

    @property
    def height(self) -> float:
        return self.z1 - self.z0


def emit_opening_glyphs(b: SceneBuilder, model: ResolvedModel, pieces: list[VisiblePiece],
                        view: ElevationView) -> None:
    """Add the type-driven overlay to every opening the elevation can actually see."""
    visible = _visible_by_uid(pieces)
    doors = {door.tag: door for door in model.plan.library.door_types}
    windows = {window.tag: window for window in model.plan.library.window_types}
    for opening in model.openings:
        region = visible.get(opening.uid)
        if region is None or region.is_empty:
            continue
        wall = model.wall(opening.host_wall)
        if wall is None:
            continue
        panel = _panel_for(opening, wall, region, view)
        if panel is None:
            continue
        if opening.is_door:
            _emit_door_glyph(b, panel, doors.get(opening.type_ref or ""))
        else:
            _emit_window_glyph(b, panel, windows.get(opening.type_ref or ""))


def _visible_by_uid(pieces: list[VisiblePiece]) -> dict[str, BaseGeometry]:
    """uid -> everything of that opening that survived occlusion, as one region."""
    grouped: dict[str, list[BaseGeometry]] = {}
    for piece in pieces:
        if piece.candidate.family in {"glaz", "sash", "door"}:
            grouped.setdefault(piece.candidate.uid, []).append(piece.geometry)
    return {uid: overlay.union_all(parts) for uid, parts in grouped.items()}


def _panel_for(opening: ResolvedOpening, wall: ResolvedWall, region: BaseGeometry,
               view: ElevationView) -> _Panel | None:
    (start_x, start_y), (end_x, end_y) = wall.axis
    length = ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5
    if length < 1e-9:
        return None
    tx, ty = (end_x - start_x) / length, (end_y - start_y) / length
    center_x = start_x + tx * opening.center_along_m
    center_y = start_y + ty * opening.center_along_m
    half = opening.width_m / 2.0
    u_a = view.u_of(center_x - tx * half, center_y - ty * half)
    u_b = view.u_of(center_x + tx * half, center_y + ty * half)
    if abs(u_b - u_a) < opening.width_m * _IN_PLANE_FRACTION:
        return None  # seen edge-on; this opening belongs to a different elevation
    sill = wall.base_ref_z_m + opening.sill_m
    wall_mid_u = (view.u_of(start_x, start_y) + view.u_of(end_x, end_y)) / 2.0
    u0, u1 = min(u_a, u_b), max(u_a, u_b)
    hinge_u = u0 if abs(u0 - wall_mid_u) > abs(u1 - wall_mid_u) else u1
    return _Panel(opening=opening, u0=u0, z0=sill, u1=u1, z1=sill + opening.height_m,
                  hinge_u=hinge_u, visible=region)


# --- windows -----------------------------------------------------------------------------
def _emit_window_glyph(b: SceneBuilder, panel: _Panel,
                       window_type: WindowType | None) -> None:
    if panel.width < _MIN_GLYPH_M or panel.height < _MIN_GLYPH_M:
        return
    operation = getattr(window_type, "operation", WindowOperation.FIXED)
    if operation in (WindowOperation.CASEMENT, WindowOperation.TILT_TURN):
        _emit_swing_triangle(b, panel, hinge="jamb")
    if operation in (WindowOperation.AWNING, WindowOperation.TILT_TURN):
        _emit_swing_triangle(b, panel, hinge="head")
    if operation == WindowOperation.DOUBLE_HUNG:
        _emit_line(b, panel, ((panel.u0, _mid(panel.z0, panel.z1)),
                              (panel.u1, _mid(panel.z0, panel.z1))), _SASH_LAYER)
    if operation == WindowOperation.SLIDER:
        _emit_line(b, panel, ((_mid(panel.u0, panel.u1), panel.z0),
                              (_mid(panel.u0, panel.u1), panel.z1)), _SASH_LAYER)


def _emit_swing_triangle(b: SceneBuilder, panel: _Panel, hinge: str) -> None:
    """The dashed operation triangle: apex on the hinge, base on the opposite edge."""
    if hinge == "jamb":
        far_u = panel.u1 if panel.hinge_u == panel.u0 else panel.u0
        points = ((far_u, panel.z0), (panel.hinge_u, _mid(panel.z0, panel.z1)),
                  (far_u, panel.z1))
    else:  # hinged at the head — an awning opens out at the sill
        points = ((panel.u0, panel.z0), (_mid(panel.u0, panel.u1), panel.z1),
                  (panel.u1, panel.z0))
    _emit_line(b, panel, points, _SASH_LAYER, linetype="DASHED")


# --- doors -------------------------------------------------------------------------------
def _emit_door_glyph(b: SceneBuilder, panel: _Panel, door_type: DoorType | None) -> None:
    if panel.width < _MIN_GLYPH_M or panel.height < _MIN_GLYPH_M:
        return
    operation = getattr(door_type, "operation", DoorOperation.SWING)
    if operation == DoorOperation.OVERHEAD:
        _emit_sectional_joints(b, panel)
        return
    leaves = _leaf_stations(panel, operation)
    for leaf_u0, leaf_u1 in leaves:
        inset = min(_DOOR_PANEL_INSET_M, (leaf_u1 - leaf_u0) / 4.0, panel.height / 8.0)
        _emit_closed(b, panel, ((leaf_u0 + inset, panel.z0 + inset),
                                (leaf_u1 - inset, panel.z0 + inset),
                                (leaf_u1 - inset, panel.z1 - inset),
                                (leaf_u0 + inset, panel.z1 - inset)), _DOOR_LAYER)
    _emit_hardware(b, panel, operation)


def _leaf_stations(panel: _Panel, operation: DoorOperation) -> list[tuple[float, float]]:
    """Where each leaf's edges fall — a pair swings from the two jambs, a slider bypasses."""
    if operation in (DoorOperation.DOUBLE_SWING, DoorOperation.SLIDE, DoorOperation.BIFOLD):
        middle = _mid(panel.u0, panel.u1)
        return [(panel.u0, middle), (middle, panel.u1)]
    return [(panel.u0, panel.u1)]


def _emit_sectional_joints(b: SceneBuilder, panel: _Panel) -> None:
    station = panel.z0 + _SECTIONAL_PANEL_M
    while station < panel.z1 - 1e-6:
        _emit_line(b, panel, ((panel.u0, station), (panel.u1, station)), _DOOR_LAYER)
        station += _SECTIONAL_PANEL_M


def _emit_hardware(b: SceneBuilder, panel: _Panel, operation: DoorOperation) -> None:
    """A short mark on the latch stile — the one thing that tells a door from a panel."""
    z = panel.z0 + _HARDWARE_HEIGHT_M
    if z >= panel.z1:
        return
    latch_u = panel.u1 if panel.hinge_u == panel.u0 else panel.u0
    inward = -1.0 if latch_u == panel.u1 else 1.0
    if operation in (DoorOperation.DOUBLE_SWING, DoorOperation.SLIDE, DoorOperation.BIFOLD):
        # Both leaves meet in the middle, so the hardware does too.
        middle = _mid(panel.u0, panel.u1)
        _emit_line(b, panel, ((middle - _HARDWARE_MARK_M, z),
                              (middle + _HARDWARE_MARK_M, z)), _DOOR_LAYER)
        return
    start = latch_u + inward * _HARDWARE_INSET_M
    _emit_line(b, panel, ((start, z), (start + inward * _HARDWARE_MARK_M, z)), _DOOR_LAYER)


# --- clipping ----------------------------------------------------------------------------
def _mid(a: float, b: float) -> float:
    return (a + b) / 2.0


def _emit_line(b: SceneBuilder, panel: _Panel, points: tuple[tuple[float, float], ...],
               layer: str, linetype: str = "CONTINUOUS") -> None:
    """Draw a glyph polyline clipped to what of this opening is actually visible."""
    clipped = overlay.intersection(LineString(points), _clip(panel))
    for segment in getattr(clipped, "geoms", (clipped,)):
        coords = list(getattr(segment, "coords", ()))
        if len(coords) < 2:
            continue
        b.add(Polyline(points=tuple((u / M_PER_IN, z / M_PER_IN) for u, z in coords),
                       layer=layer, lineweight=_GLYPH_WEIGHT, linetype=linetype,
                       uid=panel.opening.uid, tag=panel.opening.tag))


def _emit_closed(b: SceneBuilder, panel: _Panel, points: tuple[tuple[float, float], ...],
                 layer: str) -> None:
    _emit_line(b, panel, points + (points[0],), layer)


def _clip(panel: _Panel) -> BaseGeometry:
    """The opening's visible region with its holes filled, cropped to the panel rectangle.

    A projected frame is a *ring* — the glass sits in the hole — so intersecting a glyph with
    the frame alone would leave only the two ends of every triangle. Filling the rings (rather
    than dilating the region) keeps the outer edge exactly where occlusion put it, so a window
    half-hidden behind the garage still loses exactly the half it should.
    """
    filled = [Polygon(part.exterior)
              for part in getattr(panel.visible, "geoms", (panel.visible,))
              if getattr(part, "exterior", None) is not None]
    if not filled:
        return panel.visible
    return overlay.intersection(box(panel.u0, panel.z0, panel.u1, panel.z1),
                                overlay.union_all(filled))
