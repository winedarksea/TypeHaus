"""Door plan-symbol vocabulary: one geometry source for every writer (→ 20 §Drawing IR).

A ``Symbol`` node carries only name/insert/rotation/params; deriving the leaf and arc math
independently per writer risks drift the moment a non-swing operation is added. This module
owns both halves of the contract:

* :func:`door_symbol` — what the plan builder emits for a :class:`DoorOperation`, with
  every geometric parameter resolved into ``Symbol.params`` (never re-derived downstream).
* :func:`door_symbol_geometry` — the resolved strokes/arcs a writer draws, in model-space
  inches, so the PDF and DXF writers agree by construction.

The TypeScript canvas mirrors this file in ``ui/src/model/doorSymbols.ts``; the constants
below are the shared definition of each glyph and must move together.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.emit.draw.scene import Symbol
from typehaus.model.enums import DoorOperation

Pt = tuple[float, float]

DOOR_SWING = "door-swing"
DOOR_SWING_DOUBLE = "door-swing-double"
DOOR_OVERHEAD = "door-overhead"
DOOR_BIFOLD = "door-bifold"
DOOR_SLIDING = "door-sliding"
DOOR_POCKET = "door-pocket"

DOOR_SYMBOL_NAMES = frozenset({DOOR_SWING, DOOR_SWING_DOUBLE, DOOR_OVERHEAD, DOOR_BIFOLD,
                               DOOR_SLIDING, DOOR_POCKET})

# A sectional door parks its panels on horizontal track running back into the garage by
# roughly the door height. Drawing that band tells the reader the swept volume is ceiling
# space (dashed = above the cut plane), which a swing arc actively mis-states.
OVERHEAD_TRACK_DEPTH_PER_DOOR_HEIGHT = 1.0

# The bifold glyph draws the leaves part-open, otherwise the pair reads as a plain panel
# line. Each half of a pair carries two leaves of a quarter-opening each and folds
# symmetrically, so fixing the leading edge at this fraction of the half-opening makes the
# knuckle offset exact rather than a drawn approximation (see ``_bifold_fold_offset``).
BIFOLD_LEADING_EDGE_FRACTION = 0.6

# A surface-mounted bypass leaf hangs clear of the wall face on rollers instead of filling
# the opening, so its panel is drawn *outside* the wall depth — half the host thickness plus
# this hardware clearance. Drawn any nearer the axis it would land inside the wall and
# read as a fixed panel rather than a bypassing leaf.
SLIDING_PANEL_CLEARANCE_IN = 2.0

# The far leaf of a bypass pair rides its own roller track, set slightly deeper off the
# wall than the near leaf's — that depth split is what lets the plan read as two distinct
# panels instead of one line traced twice.
BYPASS_TRACK_SPACING_IN = 1.5

# Real bypass leaves lap each other past centre rather than meeting edge to edge, or the
# drawn panels would leave a sliver at the middle with no leaf covering it.
BYPASS_OVERLAP_IN = 2.0

# Every operation now has a dedicated glyph; a door authored with none falls back to the
# hinged leaf, which is the only operation a bare ``DoorType`` can mean.
_SYMBOL_BY_OPERATION = {
    DoorOperation.DOUBLE_SWING: DOOR_SWING_DOUBLE,
    DoorOperation.OVERHEAD: DOOR_OVERHEAD,
    DoorOperation.BIFOLD: DOOR_BIFOLD,
    DoorOperation.SLIDE: DOOR_SLIDING,
    DoorOperation.POCKET: DOOR_POCKET,
}

# Symbols anchored at the opening centre rather than at the hinge jamb. A sliding or
# pocket panel spans the whole opening and only its travel is handed, so it anchors at the
# centre like the other non-hinged glyphs.
_CENTRE_ANCHORED = frozenset({DOOR_SWING_DOUBLE, DOOR_OVERHEAD, DOOR_BIFOLD, DOOR_SLIDING,
                              DOOR_POCKET})


@dataclass(frozen=True)
class SymbolStroke:
    """An open polyline of a symbol, in model-space inches."""

    points: tuple[Pt, ...]
    dashed: bool = False


@dataclass(frozen=True)
class SymbolArc:
    """A circular arc of a symbol; angles are degrees CCW from +X, as DXF expects."""

    center: Pt
    radius: float
    start_angle_deg: float
    end_angle_deg: float


@dataclass(frozen=True)
class DoorSymbolGeometry:
    strokes: tuple[SymbolStroke, ...] = ()
    arcs: tuple[SymbolArc, ...] = ()


def symbol_name_for_operation(operation: DoorOperation) -> str:
    return _SYMBOL_BY_OPERATION.get(operation, DOOR_SWING)


def symbol_is_centre_anchored(name: str) -> bool:
    """True when the insert point is the opening centre, not the hinge jamb."""
    return name in _CENTRE_ANCHORED


def door_symbol_params(name: str, width_in: float, height_in: float, swing_sign: float, *,
                       hinge_jamb_sign: float,
                       host_wall_thickness_in: float) -> dict[str, float]:
    """Resolve every parameter the glyph needs, so no writer computes geometry constants.

    ``swing_sign`` is the handed operating side (+1/-1 along the wall normal) — the side a
    leaf swings toward, or for an overhead door the side the track runs into.
    ``hinge_jamb_sign`` is the handed jamb (+1/-1 along the wall) the leaf is fixed at:
    the hinge for a swinging leaf, and the jamb a sliding or pocket panel parks against.
    ``host_wall_thickness_in`` places the panels that live with the wall depth rather than
    with the opening — a slider hangs outside it, a pocket panel disappears into it — and
    the symbol is inserted on the wall axis, so both are measured from its half depth.
    """
    params: dict[str, float] = {"width_in": width_in, "swing_sign": swing_sign}
    if name == DOOR_SWING:
        # A leaf shuts *away* from its hinge, and the arc has to sweep that quadrant.
        params["closed_leaf_sign"] = -hinge_jamb_sign
    elif name == DOOR_OVERHEAD:
        params["track_depth_in"] = height_in * OVERHEAD_TRACK_DEPTH_PER_DOOR_HEIGHT
    elif name == DOOR_BIFOLD:
        leaf_run_in = (width_in / 2.0) * BIFOLD_LEADING_EDGE_FRACTION
        params["leaf_run_in"] = leaf_run_in
        params["fold_offset_in"] = _bifold_fold_offset(width_in, leaf_run_in)
    elif name == DOOR_SLIDING:
        # A bypass pair has no hinge jamb — both leaves are symmetric about the opening
        # centre, so hinge_jamb_sign plays no part here.
        near_standoff_in = host_wall_thickness_in / 2.0 + SLIDING_PANEL_CLEARANCE_IN
        params["near_standoff_in"] = near_standoff_in
        params["far_standoff_in"] = near_standoff_in + BYPASS_TRACK_SPACING_IN
        params["overlap_in"] = min(BYPASS_OVERLAP_IN, width_in / 2.0)
    elif name == DOOR_POCKET:
        params["park_jamb_sign"] = hinge_jamb_sign
        params["pocket_run_in"] = width_in
        # The stop spans the wall it hides in, which is what makes it read as the stud
        # closing the cavity rather than as a stray tick.
        params["pocket_stop_half_length_in"] = host_wall_thickness_in / 2.0
    return params


def _bifold_fold_offset(width_in: float, leaf_run_in: float) -> float:
    """Perpendicular projection of the folded knuckle, from rigid-leaf geometry.

    Each half of a bifold pair is two leaves of ``width/4``; folded symmetrically with the
    leading edge ``leaf_run`` along the wall, the knuckle is the apex of an isoceles
    triangle. Solving it here (rather than eyeballing a chevron depth) keeps the drawn
    leaves the length the real leaves are.
    """
    leaf_length_in = width_in / 4.0
    half_run_in = leaf_run_in / 2.0
    return math.sqrt(max(leaf_length_in ** 2 - half_run_in ** 2, 0.0))


def door_symbol_geometry(node: Symbol) -> DoorSymbolGeometry:
    """Resolve one door ``Symbol`` into strokes + arcs in model space."""
    width_in = float(node.params.get("width_in", node.scale) or node.scale)
    swing_sign = float(node.params.get("swing_sign", 1.0))
    frame = _SymbolFrame(node.insert, node.rotation, swing_sign)
    if node.name == DOOR_SWING:
        return _swing_leaf(node.insert, node.rotation, swing_sign, width_in,
                           float(node.params["closed_leaf_sign"]))
    if node.name == DOOR_SWING_DOUBLE:
        return _double_swing(frame, node.rotation, swing_sign, width_in)
    if node.name == DOOR_OVERHEAD:
        return _overhead(frame, width_in, float(node.params.get("track_depth_in", width_in)))
    if node.name == DOOR_BIFOLD:
        return _bifold(frame, width_in, float(node.params["leaf_run_in"]),
                       float(node.params["fold_offset_in"]))
    if node.name == DOOR_SLIDING:
        return _sliding(frame, width_in, float(node.params["near_standoff_in"]),
                        float(node.params["far_standoff_in"]),
                        float(node.params["overlap_in"]))
    if node.name == DOOR_POCKET:
        return _pocket(frame, width_in, float(node.params["park_jamb_sign"]),
                       float(node.params["pocket_run_in"]),
                       float(node.params["pocket_stop_half_length_in"]))
    raise KeyError(f"not a door symbol: {node.name}")


@dataclass(frozen=True)
class _SymbolFrame:
    """Local symbol axes: ``u`` runs along the wall, ``v`` is the handed operating side."""

    origin: Pt
    rotation_deg: float
    swing_sign: float

    def at(self, u: float, v: float) -> Pt:
        angle = math.radians(self.rotation_deg)
        along = (math.cos(angle), math.sin(angle))
        across = (-math.sin(angle) * self.swing_sign, math.cos(angle) * self.swing_sign)
        return (self.origin[0] + along[0] * u + across[0] * v,
                self.origin[1] + along[1] * u + across[1] * v)


def _swing_leaf(hinge: Pt, rotation_deg: float, swing_sign: float, leaf_length_in: float,
                closed_leaf_sign: float) -> DoorSymbolGeometry:
    """One hinged leaf standing open at 90° plus its swing arc, pivoting on ``hinge``.

    ``closed_leaf_sign`` is the direction along the wall (+1 = the frame's ``u``) the shut
    leaf lies in, i.e. toward the strike jamb. The arc has to sweep from the shut leaf to
    the open one, so a leaf hinged at the other jamb sweeps the *other* quadrant: assuming
    a single handing drew the arc over the wall beside the door rather than across the
    opening, which is what read as a convex swing.
    """
    open_end = _SymbolFrame(hinge, rotation_deg, swing_sign).at(0.0, leaf_length_in)
    closed_angle = rotation_deg if closed_leaf_sign > 0 else rotation_deg + 180.0
    return DoorSymbolGeometry(
        strokes=(SymbolStroke(points=(hinge, open_end)),),
        arcs=(_quarter_swing_arc(hinge, leaf_length_in, closed_angle,
                                 rotation_deg + 90.0 * swing_sign),),
    )


def _quarter_swing_arc(hinge: Pt, radius_in: float, closed_angle_deg: float,
                       open_angle_deg: float) -> SymbolArc:
    """The 90° sweep between the shut and open leaf, ordered as both writers expect.

    ezdxf and matplotlib each draw an arc counter-clockwise from ``start_angle`` to
    ``end_angle``, so the two leaf directions cannot simply be emitted in leaf order: for
    every leaf that opens clockwise that draws the 270° complement — an arc bowing away
    from the hinge instead of hugging it.
    """
    opens_counter_clockwise = (open_angle_deg - closed_angle_deg) % 360.0 < 180.0
    start_deg, end_deg = ((closed_angle_deg, open_angle_deg) if opens_counter_clockwise
                          else (open_angle_deg, closed_angle_deg))
    return SymbolArc(center=hinge, radius=radius_in, start_angle_deg=start_deg % 360.0,
                     end_angle_deg=end_deg % 360.0)


def _double_swing(frame: _SymbolFrame, rotation_deg: float, swing_sign: float,
                  width_in: float) -> DoorSymbolGeometry:
    """A French pair: half-width leaves hinged at both jambs, opening to the same side.

    The second leaf reuses the single-leaf math with its rotation flipped 180° and its
    sign negated, which is what keeps both leaves on one physical side of the wall. Both
    shut toward the mullion — the frame's ``+u`` in each leaf's own rotated frame — so the
    pair is a mirror image of itself rather than one concave leaf beside one convex one.
    """
    half = width_in / 2.0
    left = _swing_leaf(frame.at(-half, 0.0), rotation_deg, swing_sign, half,
                       closed_leaf_sign=1.0)
    right = _swing_leaf(frame.at(half, 0.0), rotation_deg + 180.0, -swing_sign, half,
                        closed_leaf_sign=1.0)
    return DoorSymbolGeometry(strokes=left.strokes + right.strokes,
                              arcs=left.arcs + right.arcs)


def _overhead(frame: _SymbolFrame, width_in: float, track_depth_in: float) -> DoorSymbolGeometry:
    """Sectional overhead door: jamb/track lines plus the parked panel band — no arc.

    The closed panel is solid in the opening; the track legs and the panel in its stored
    position are dashed because they are above the plan cut, exactly like a header.
    """
    half = width_in / 2.0
    return DoorSymbolGeometry(strokes=(
        SymbolStroke(points=(frame.at(-half, 0.0), frame.at(half, 0.0))),
        SymbolStroke(points=(frame.at(-half, 0.0), frame.at(-half, track_depth_in)),
                     dashed=True),
        SymbolStroke(points=(frame.at(half, 0.0), frame.at(half, track_depth_in)),
                     dashed=True),
        SymbolStroke(points=(frame.at(-half, track_depth_in), frame.at(half, track_depth_in)),
                     dashed=True),
    ))


def _sliding(frame: _SymbolFrame, width_in: float, near_standoff_in: float,
             far_standoff_in: float, overlap_in: float) -> DoorSymbolGeometry:
    """A bypass pair: two overlapping leaves on parallel tracks, both solid — no arc.

    Each leaf runs from its own jamb to just past centre, so the two panels lap each other
    where they cross rather than meeting edge to edge with a gap. The far leaf sits at a
    slightly greater standoff than the near one — the two rollers' actual track depths —
    which is what reads as two independent panels instead of one line traced twice. Unlike
    a pocket door (or a single barn-door slider), neither leaf ever travels past a jamb, so
    there is nothing to draw dashed.
    """
    half = width_in / 2.0
    half_overlap = overlap_in / 2.0
    return DoorSymbolGeometry(strokes=(
        SymbolStroke(points=(frame.at(-half, near_standoff_in),
                             frame.at(half_overlap, near_standoff_in))),
        SymbolStroke(points=(frame.at(-half_overlap, far_standoff_in),
                             frame.at(half, far_standoff_in))),
    ))


def _pocket(frame: _SymbolFrame, width_in: float, park_jamb_sign: float,
            pocket_run_in: float, stop_half_length_in: float) -> DoorSymbolGeometry:
    """A pocket door: the panel receding along the wall axis into its cavity — no arc.

    The concealed run and the stud that stops it are dashed (they are inside the wall);
    only the panel standing in the opening is drawn solid. Nothing stands off the wall,
    which is exactly what distinguishes this glyph from the surface slider.
    """
    half = width_in / 2.0
    pocket_end = park_jamb_sign * (half + pocket_run_in)
    return DoorSymbolGeometry(strokes=(
        SymbolStroke(points=(frame.at(-half, 0.0), frame.at(half, 0.0))),
        SymbolStroke(points=(frame.at(park_jamb_sign * half, 0.0),
                             frame.at(pocket_end, 0.0)), dashed=True),
        SymbolStroke(points=(frame.at(pocket_end, -stop_half_length_in),
                             frame.at(pocket_end, stop_half_length_in)), dashed=True),
    ))


def _bifold(frame: _SymbolFrame, width_in: float, leaf_run_in: float,
            fold_offset_in: float) -> DoorSymbolGeometry:
    """A bifold pair: two folded leaf runs meeting the jambs, chevroned — no swing arc."""
    half = width_in / 2.0
    return DoorSymbolGeometry(strokes=tuple(
        SymbolStroke(points=(
            frame.at(side * half, 0.0),
            frame.at(side * (half - leaf_run_in / 2.0), fold_offset_in),
            frame.at(side * (half - leaf_run_in), 0.0),
        ))
        for side in (-1.0, 1.0)
    ))
