"""IFC tessellation from the same rail/head meshes used by the canvas and GLB."""

from typehaus.emit.ifc.placeable_parts import parts_representation
from typehaus.model.placeable_symbols._track_lighting import track_geometry


def track_representation(f, body, spec, center, rotation, z_base):
    _, parts = track_geometry(spec)
    return parts_representation(f, body, parts, center, rotation, z_base)
