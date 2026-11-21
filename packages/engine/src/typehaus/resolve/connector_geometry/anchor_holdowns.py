"""A bolted hold-down and its cast-in anchor, drawn from the catalog rows they are read at.

Local frame, inches: the anchor rod's centre is the origin; the member face the hold-down
nails to is the plane y = -CL. The hold-down's z = 0 is its seat bottom (on the sill), the
anchor's is its embedment line (the pour top).
"""

from __future__ import annotations

from typehaus.hardware.anchor_holdowns import HOLDOWNS, SSTB_STEM
from typehaus.resolve.connector_geometry.mesh import box_mesh, combine_meshes
from typehaus.resolve.geometry_ir import GMesh

_GAUGE_11_IN = 0.120
_SEAT_DEPTH_IN = 1.0       # seat past the rod centre: a drawing allowance, not a catalog row
_SEAT_HEIGHT_IN = 1.375
_ROD_ABOVE_LINE_IN = 5.0   # 17-5/8 length less 12-5/8 embedment


def anchor_holdown_mesh(part: str) -> GMesh | None:
    if part in HOLDOWNS:
        row = HOLDOWNS[part]
        half, face = row.width_in / 2.0, -row.cl_in
        back = box_mesh((-half, face, 0.0), (half, face + _GAUGE_11_IN, row.height_in))
        seat = box_mesh((-half, face, _SEAT_HEIGHT_IN - _GAUGE_11_IN),
                        (half, _SEAT_DEPTH_IN, _SEAT_HEIGHT_IN))
        return combine_meshes(back, seat)
    if part in SSTB_STEM:
        row = SSTB_STEM[part]
        r = row.diameter_in / 2.0
        return box_mesh((-r, -r, -row.le_in), (r, r, _ROD_ABOVE_LINE_IN))
    return None
