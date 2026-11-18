"""Where a floor's bearing refs stand in plan: a resolved wall or an authored ``Beam``."""

from __future__ import annotations

from typehaus.model.structure import Beam
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedModel


def _bearing_axis(model: ResolvedModel, tag: str):
    """The plan axis (p0, p1) of a joist bearing ref — a resolved wall, or an authored
    standalone Beam (looked up through its per-storey nodes)."""
    wall = model.wall(tag)
    if wall is not None:
        return wall.axis
    beam = model.plan.by_tag(tag)
    if isinstance(beam, Beam):
        for storey in model.plan.storeys:
            nodes = {e.tag: e.position.xy_m for e in model.plan.storey_elements(storey.tag)
                     if e.element_kind == "Node"}
            p0, p1 = nodes.get(beam.start_node), nodes.get(beam.end_node)
            if p0 is not None and p1 is not None:
                return (p0, p1)
    return None


def _wall_footprint_span(wall, across: int) -> tuple[float, float] | None:
    """The wall's plan extent along axis ``across`` (0=x, 1=y), from its layer polygons.

    Read off the resolved polygons rather than ``axis`` +/- half ``thickness_m`` because an
    ``alignment=face(...)`` wall's axis is not its centreline.
    """
    values = [point[across] for layer in wall.layers for point in layer.polygon]
    return (min(values), max(values)) if values else None


def _bearing_footprint_span(model: ResolvedModel, tag: str,
                            across: int) -> tuple[float, float] | None:
    """The plan extent across the member's axis, for a wall *or* a standalone ``Beam``.

    A wall reads its resolved layer polygons (``alignment=face(...)`` means the axis is not
    the centreline). A ``Beam`` has no layers — it is not a resolved wall at all — so its
    width comes off ``Beam.size`` and straddles the axis, which is how the resolver places
    it. Without this, a beam named in ``FloorOpening.bearing_refs`` was skipped outright and
    the edge read as unsupported, putting a header under a beam that plainly carries it.
    """
    wall = model.wall(tag)
    if wall is not None:
        return _wall_footprint_span(wall, across)
    beam = model.plan.by_tag(tag)
    if not isinstance(beam, Beam):
        return None
    axis = _bearing_axis(model, tag)
    if axis is None:
        return None
    half = cross_section(beam.size).width_m / 2.0
    centre = axis[0][across]
    return (centre - half, centre + half)
