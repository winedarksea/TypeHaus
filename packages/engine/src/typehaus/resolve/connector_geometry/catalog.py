"""Part-number dispatch for simplified manufacturer-dimensioned connector meshes."""

from __future__ import annotations

from functools import lru_cache

from typehaus.resolve.geometry_ir import GMesh


@lru_cache(maxsize=512)
def connector_mesh(part: str, *, member_width_in: float | None = None,
                   member_depth_in: float | None = None, slope_radians: float = 0.0,
                   support_width_in: float | None = None,
                   strap_length_in: float | None = None) -> GMesh | None:
    """Catalog bodies in local metres. Unknown products have no invented dimension record."""
    from typehaus.resolve.connector_geometry.bases_caps import base_cap_mesh
    from typehaus.resolve.connector_geometry.fasteners import fastener_mesh
    from typehaus.resolve.connector_geometry.hangers import hanger_mesh
    from typehaus.resolve.connector_geometry.ties import tie_mesh

    body = hanger_mesh(part, member_width_in=member_width_in, member_depth_in=member_depth_in,
                       slope_radians=slope_radians, support_width_in=support_width_in)
    if body is not None:
        return body
    body = base_cap_mesh(part, member_width_in=member_width_in, member_depth_in=member_depth_in)
    if body is not None:
        return body
    body = tie_mesh(part, member_width_in=member_width_in, member_depth_in=member_depth_in,
                   slope_radians=slope_radians, strap_length_in=strap_length_in)
    return body if body is not None else fastener_mesh(part)
