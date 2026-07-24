"""Door plan-symbol vocabulary: one geometry source for every writer (→ 20 §Drawing IR).

A ``Symbol`` node carries only name/insert/rotation/params, so each writer used to
re-derive the leaf and arc math from scratch — three copies that drifted the moment a
non-swing operation was added. This module owns both halves of the contract:

* :func:`door_symbol` — what the plan builder emits for a :class:`DoorOperation`, with
  every geometric parameter resolved into ``Symbol.params`` (never re-derived downstream).
* :func:`door_symbol_geometry` — the resolved strokes/arcs a writer draws, in model-space
  inches, so the PDF and DXF writers agree by construction.

The TypeScript canvas mirrors this file in ``ui/src/plan/doorSymbols.ts``; the constants
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

DOOR_SYMBOL_NAMES = frozenset({DOOR_SWING, DOOR_SWING_DOUBLE, DOOR_OVERHEAD, DOOR_BIFOLD})

# A sectional door parks its panels on horizontal track running back into the garage by
# roughly the door height. Drawing that band tells the reader the swept volume is ceiling
# space (dashed = above the cut plane), which a swing arc actively mis-states.
OVERHEAD_TRACK_DEPTH_PER_DOOR_HEIGHT = 1.0

# The bifold glyph draws the leaves part-open, otherwise the pair reads as a plain panel
# line. Each half of a pair carries two leaves of a quarter-opening each and folds
# symmetrically, so fixing the leading edge at this fraction of the half-opening makes the
# knuckle offset exact rather than a drawn approximation (see ``_bifold_fold_offset``).
BIFOLD_LEADING_EDGE_FRACTION = 0.6

# Operations with no dedicated glyph yet still read as a hinged leaf; sliding and pocket
# doors are tracked in TODO but deliberately keep the swing symbol for now.
_SYMBOL_BY_OPERATION = {
    DoorOperation.DOUBLE_SWING: DOOR_SWING_DOUBLE,
    DoorOperation.OVERHEAD: DOOR_OVERHEAD,
    DoorOperation.BIFOLD: DOOR_BIFOLD,
}

# Symbols anchored at the opening centre rather than at the hinge jamb.
_CENTRE_ANCHORED = frozenset({DOOR_SWING_DOUBLE, DOOR_OVERHEAD, DOOR_BIFOLD})


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


def door_symbol_params(name: str, width_in: float, height_in: float,
                       swing_sign: float) -> dict[str, float]:
    """Resolve every parameter the glyph needs, so no writer computes geometry constants.

    ``swing_sign`` is the handed operating side (+1/-1 along the wall normal) — the side a
    leaf swings toward, or for an overhead door the side the track runs into.
    """
    params: dict[str, float] = {"width_in": width_in, "swing_sign": swing_sign}
    if name == DOOR_OVERHEAD:
        params["track_depth_in"] = height_in * OVERHEAD_TRACK_DEPTH_PER_DOOR_HEIGHT
    elif name == DOOR_BIFOLD:
        leaf_run_in = (width_in / 2.0) * BIFOLD_LEADING_EDGE_FRACTION
        params["leaf_run_in"] = leaf_run_in
        params["fold_offset_in"] = _bifold_fold_offset(width_in, leaf_run_in)
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
        return _swing_leaf(node.insert, node.rotation, swing_sign, width_in)
    if node.name == DOOR_SWING_DOUBLE:
        return _double_swing(frame, node.rotation, swing_sign, width_in)
    if node.name == DOOR_OVERHEAD:
        return _overhead(frame, width_in, float(node.params.get("track_depth_in", width_in)))
    if node.name == DOOR_BIFOLD:
        return _bifold(frame, width_in, float(node.params["leaf_run_in"]),
                       float(node.params["fold_offset_in"]))
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


def _swing_leaf(hinge: Pt, rotation_deg: float, swing_sign: float,
                leaf_length_in: float) -> DoorSymbolGeometry:
    """One hinged leaf standing open at 90° plus its swing arc, pivoting on ``hinge``."""
    end = _SymbolFrame(hinge, rotation_deg, swing_sign).at(0.0, leaf_length_in)
    start_angle = rotation_deg if swing_sign > 0 else rotation_deg - 90.0
    end_angle = rotation_deg + 90.0 if swing_sign > 0 else rotation_deg
    return DoorSymbolGeometry(
        strokes=(SymbolStroke(points=(hinge, end)),),
        arcs=(SymbolArc(center=hinge, radius=leaf_length_in,
                        start_angle_deg=start_angle, end_angle_deg=end_angle),),
    )


def _double_swing(frame: _SymbolFrame, rotation_deg: float, swing_sign: float,
                  width_in: float) -> DoorSymbolGeometry:
    """A French pair: half-width leaves hinged at both jambs, opening to the same side.

    The second leaf reuses the single-leaf math with its rotation flipped 180° and its
    sign negated, which is what keeps both leaves on one physical side of the wall.
    """
    half = width_in / 2.0
    left = _swing_leaf(frame.at(-half, 0.0), rotation_deg, swing_sign, half)
    right = _swing_leaf(frame.at(half, 0.0), rotation_deg + 180.0, -swing_sign, half)
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
