"""Grade a generic Z drip head over a non-metal rainscreen opening, off its resolved pieces.

R703.4.1 asks the head flashing to reach the surface of the wall finish and shed water there;
James Hardie asks the siding to stand 1/4" clear of it, uncaulked. Read here: the Z runs past
the casing at both ends, each end is dammed, the drip clears the face it protects, the WRB
strip-in laps over its upstand, and the strip closing the cavity's foot stands the clearance
off the flashing (``resolve/opening_head_drip.py``).
"""

from __future__ import annotations

from typehaus.checks.integrity.cladding_trim_runs import spans_cover
from typehaus.findings import failed
from typehaus.library.trim.generic import HEAD_FLASHING_CLADDING_CLEARANCE_IN
from typehaus.quantities import M_PER_IN
from typehaus.resolve.flashing_config import FLASHING
from typehaus.resolve.opening_head_drip import DRIP_HEAD_PRODUCT

CITE = "IRC R703.4 item 1, R703.4.1; James Hardie HS0920-P1/4 Fig. 7"
_TOL = 1e-4
_STRIP_PRODUCT = "PANEL_END_STRIP"


def grade_drip_head(model, wall, opening, frame, cavity_id) -> list:
    """FAIL findings for one generic drip head; empty when every requirement is met."""
    from typehaus.resolve.opening_flashing import _drip_face, head_flashing_section

    tag, d, n = opening.tag, frame.along, frame.outward
    pieces = [s for s in model.solids if s.host_ref == tag and s.product == DRIP_HEAD_PRODUCT
              and s.body_mesh is not None]
    points = [(x * d[0] + y * d[1], x * n[0] + y * n[1], z)
              for piece in pieces for x, y, z in piece.body_mesh.positions]
    head = head_flashing_section(wall, opening, frame)
    (water, bend), (front, seat) = head.points[1], head.points[2]
    station0 = frame.origin[0] * d[0] + frame.origin[1] * d[1]
    depth0 = frame.origin[0] * n[0] + frame.origin[1] * n[1]
    lap = FLASHING.head_end_lap_m
    lo, hi = station0 + head.start + lap, station0 + head.start + head.span - lap
    out = []

    def fail(message):
        out.append(failed(cavity_id, f"{tag}: {message}", (tag,), code=CITE))

    spans = []
    for piece in pieces:
        stations = [x * d[0] + y * d[1] for x, y, _z in piece.body_mesh.positions]
        spans.append((min(stations), max(stations)))
    if not spans_cover(spans, lo, hi):
        fail("the head flashing does not run past the casing at both ends")
        return out
    ends = (min(s for s, _o, _z in points), max(s for s, _o, _z in points))
    middle = depth0 + (water + front) / 2
    dam_top = seat + 0.9 * FLASHING.head_end_dam_m
    if not all(any(abs(s - end) < 2 * FLASHING.sheet_m and o > middle and z > dam_top
                   for s, o, z in points) for end in ends):
        fail("the head flashing has no end dam, so water runs off its ends into the wall")
    face = depth0 + _drip_face(opening, frame, FLASHING) - FLASHING.head_projection_m
    if max(o for _s, o, _z in points) <= face + _TOL:
        fail("the head flashing's drip does not clear the face of the trim or cladding")
    top = max(z for _s, _o, z in points)
    tape = [s for s in model.solids if s.host_ref == tag
            and s.category == "opening_flashing_membrane"]
    if not tape or max(s.z1_m for s in tape) <= top + _TOL:
        fail("the head flashing's upstand is not lapped under the WRB strip-in above it")
    strips = [s for s in model.solids if s.host_ref == tag and s.product == _STRIP_PRODUCT
              and s.body_mesh is not None]
    if strips:
        def line(v):
            return bend + (seat - bend) * (v - water) / (front - water)

        gap = min(z - line(o - depth0) for strip in strips
                  for o, z in ((x * n[0] + y * n[1], z)
                               for x, y, z in strip.body_mesh.positions))
        if gap + _TOL < HEAD_FLASHING_CLADDING_CLEARANCE_IN * M_PER_IN:
            fail(f"the cladding over the head stands {gap / M_PER_IN:.2f} in off the flashing, "
                 f"under the {HEAD_FLASHING_CLADDING_CLEARANCE_IN} in its maker asks")
    return out
