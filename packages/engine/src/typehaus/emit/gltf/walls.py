"""Wall bodies: the glTF serialization of the wall solids the IR produces.

The geometry itself — layer prisms, jamb splitting around openings, the raked top, the arched
head — moved to ``resolve/geometry_walls.py``, because this module was one of four places that
computed it. What is left here is the emitter's own job: pick the colour, hand the solids to
the mesh builder.
"""

from __future__ import annotations

from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.palette import _layer_color
from typehaus.resolve.geometry_ir import GMesh, GPrism
# `_wall_top_at` keeps its old name here: openings.py and emitter.py import it from this
# module, and the rake it answers for is the same one the wall solids are built with.
from typehaus.resolve.geometry_walls import layer_solids
from typehaus.resolve.geometry_walls import wall_top_at as _wall_top_at  # noqa: F401
from typehaus.resolve.model import ResolvedWall


def _add_solid(mb: _MeshBuilder, solid, color) -> None:
    if isinstance(solid, GPrism):
        if solid.top is None:
            mb.add_prism(list(solid.ring), solid.z0_m, solid.z1_m, color)
        else:
            tops = dict(zip(solid.ring, solid.top))
            mb.add_raked_prism(list(solid.ring), solid.z0_m,
                               lambda x, y: tops[(x, y)], color)
    elif isinstance(solid, GMesh):
        mb.add_mesh(solid, color)


def _add_wall_body(mb: _MeshBuilder, wall: ResolvedWall, lod: str, openings=(),
                   authored: dict | None = None) -> None:
    """Draw a wall's selectable body (its depth-layer prisms). Framing members are emitted as a
    separate ``framing`` node by the caller, so the framed LOD leaves the body empty and lets the
    stud model stand on its own. ``authored`` is the catalog's authored-colour map
    (``palette.authored_colors``), so a layer whose material states a colour — a paint film,
    a wood liner — reads with it instead of a family guess."""
    if lod == "framed" and wall.members:
        return
    for layer in wall.depth_layers():
        if not layer.polygon:
            continue
        color = _layer_color(layer, authored)
        band = layer.band(wall) if layer.is_banded else None
        for solid in layer_solids(wall, layer.polygon, openings, band=band):
            _add_solid(mb, solid, color)
