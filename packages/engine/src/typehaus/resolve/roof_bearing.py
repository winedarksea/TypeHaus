"""A roof bearing ref that resolves to a wall **or** to a standalone ``Beam``.

``Roof.bearing_refs`` used to mean "wall tags", and every consumer said so by calling
``model.wall(tag)`` and dropping whatever did not come back. That is right for a roof
over a room and wrong for a canopy: the north entry passage is three trusses spanning
between two headers on columns, and there is no wall under it to name.

**What a bearing actually has to supply is small**, and a Beam supplies all of it:

* ``axis`` — the plan centreline, ``(p0, p1)`` in metres. Every footprint, truss station
  and rake extent is built from these and nothing else.
* ``z1_m`` — the top, which is the plate top for a wall and the beam top for a beam.
* ``assembly`` — read only to cut the birdsmouth, and only on a rafter-framed roof.

The precedent is ``resolve/floors.py::_bearing_axis``, which already falls back from a
wall to a Beam for a joist bearing; this is the same move one element up.

**Read off the AUTHORED beam, never off a resolved solid.** Standalone beams become
``ResolvedSolid``s in ``resolve_columns_and_beams``, which runs *after* the envelope
stage that resolves roofs (``resolve/pipeline.py``) — and ``index_by_tag`` runs later
still. A beam's geometry therefore has to come from the ``Beam`` element and its per-storey
``Node``s, exactly as the floors precedent does it.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.model.structure import Beam
from typehaus.resolve.model import ResolvedModel, ResolvedWall

Axis = tuple[tuple[float, float], tuple[float, float]]


@dataclass(frozen=True)
class RoofBearing:
    """One resolved entry of ``Roof.bearing_refs``."""

    tag: str
    axis: Axis
    z1_m: float
    assembly: str | None
    #: The resolved wall, where the bearing IS one. ``None`` for a beam — and the one
    #: consumer that needs a wall's *polygons* rather than its axis (the cladding lap in
    #: ``_resolve_roof``, and ``_eave_plumb_cuts``' stud face) must branch on this rather
    #: than assume. A beam has no cladding to lap and no stud face to cut to.
    wall: ResolvedWall | None = None


def _beam_axis(model: ResolvedModel, beam: Beam) -> Axis | None:
    for storey in model.plan.storeys:
        nodes = {e.tag: e.position.xy_m for e in model.plan.storey_elements(storey.tag)
                 if e.element_kind == "Node"}
        p0, p1 = nodes.get(beam.start_node), nodes.get(beam.end_node)
        if p0 is not None and p1 is not None:
            return (p0, p1)
    return None


def roof_bearing(model: ResolvedModel, tag: str) -> RoofBearing | None:
    """One bearing ref, or ``None`` where it resolves to neither a wall nor a beam."""
    wall = model.wall(tag)
    if wall is not None:
        return RoofBearing(tag, wall.axis, wall.z1_m, wall.assembly, wall)
    beam = model.plan.by_tag(tag)
    if not isinstance(beam, Beam):
        return None
    axis = _beam_axis(model, beam)
    if axis is None:
        return None
    # ``Beam.top_elevation`` is ABSOLUTE, not storey-relative — ``_resolve_beam`` reads it
    # against the storey datum, not added to it. A beam carrying a roof has no joist field
    # to derive a drop from, so an unauthored top is not defaultable: say so instead.
    if beam.top_elevation is None:
        return None
    return RoofBearing(tag, axis, beam.top_elevation.meters, beam.assembly, None)


def roof_bearings(model: ResolvedModel, refs: tuple[str, ...]) -> list[RoofBearing | None]:
    """Every ref in order, ``None`` where one does not resolve — so a caller can name it."""
    return [roof_bearing(model, tag) for tag in refs]


def resolved_bearings(model: ResolvedModel, refs: tuple[str, ...]) -> tuple[RoofBearing, ...]:
    """Only the refs that resolved. The shape every downstream consumer wants."""
    return tuple(b for b in roof_bearings(model, refs) if b is not None)
