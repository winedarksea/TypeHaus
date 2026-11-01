"""The rake (a gable wall under the roof's edge): leaders only, over what the cut draws.

The stock rake metal, the BBD75 wall head and the raked top plate are all resolved
geometry, so the section already cuts them; this overlay names them (C7-E7). A piece the cut
does not pass through gets no leader.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.eave import eave_frame
from typehaus.emit.draw.detail_components.eave_labels import (
    Anchor,
    eave_labels,
    member_anchor,
    roof_labels,
)
from typehaus.emit.draw.detail_components.geometry import layer_intervals
from typehaus.emit.draw.scene import IRNode
from typehaus.emit.draw.typography import TEXT_PT
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_members import member_solid
from typehaus.resolve.geometry_slice import CutPlane, slice_solid

#: The rake piece's child-key suffix (``roof_image_ii``); ``-rake-foot`` is the eave corner.
_RAKE_LEG = "-image-ii-rake"


def rake(model, wall, crop, direction, station, scale=None) -> list[IRNode]:
    """Name the rake metal and its leg, the closure, the raked plate and the head foam."""
    frame = eave_frame(model, wall, direction, station) if crop is not None else None
    if frame is None:
        return []
    roof, clad_out, junction_z, out_sign, slope = frame
    at = (roof, direction, station, clad_out, junction_z)
    entries = roof_labels(model, roof, clad_out, junction_z, out_sign, slope) + [
        (member_anchor(*at, "drip_edge", _RAKE_LEG),
         "K1 stock rake 52126XX over the membrane at the deck edge"),
        (_rake_leg_foot(roof, direction, station, clad_out, junction_z),
         "K2 rake leg 1\" below the wall head, over the closure"),
        (_band_head(wall, direction, station, junction_z, "cladding", 2.0),
         "K3 BBD75 slope-cut, Universal Closure taped to it"),
        (_wall_member_anchor(wall, direction, station, "raked_plate"),
         "K5 rake nailer on the raked top plate"),
        (_band_head(wall, direction, station, junction_z, "insulation", 3.0),
         "K6 wall foam tight to the deck underside"),
    ]
    entries = [(target, text) for target, text in entries
               if target is not None and _in_crop(target, crop)]
    entries.sort(key=lambda entry: -entry[0][1])
    return eave_labels(entries, clad_out, junction_z, out_sign, scale, step_pt=1.5 * TEXT_PT)


def _cut_points(solids, direction: str, station: float) -> list[Anchor]:
    plane = CutPlane(axis=direction, station_m=station)
    points: list[Anchor] = []
    for solid in solids:
        for profile in slice_solid(solid, plane):
            points += [(u / M_PER_IN, z / M_PER_IN) for u, z in profile.outline]
    return points


def _rake_leg_foot(roof, direction, station, clad_out, junction_z) -> Anchor | None:
    """The lowest point of the rake piece the cut passes through: its leg's drip."""
    if roof is None:
        return None
    solids = [member_solid(m) for m in roof.members
              if m.category == "drip_edge" and m.child_key.endswith(_RAKE_LEG)]
    points = [p for p in _cut_points([s for s in solids if s is not None], direction, station)
              if abs(p[0] - clad_out) <= 6.0 and abs(p[1] - junction_z) <= 12.0]
    return min(points, key=lambda p: p[1]) if points else None


def _wall_member_anchor(wall, direction, station, category: str) -> Anchor | None:
    solids = [member_solid(m) for m in getattr(wall, "members", ()) if m.category == category]
    points = _cut_points([s for s in solids if s is not None], direction, station)
    if not points:
        return None
    us = [u for u, _ in points]
    zs = [z for _, z in points]
    return ((min(us) + max(us)) / 2.0, (min(zs) + max(zs)) / 2.0)


def _band_head(wall, direction, station, junction_z, function: str,
               drop_in: float) -> Anchor | None:
    """The wall's outermost ``function`` layer, ``drop_in`` under the roof at the wall."""
    bands = [iv for iv in layer_intervals(wall, direction, station).values()
             if iv[2] == function]
    if not bands:
        return None
    lo, hi, _function = bands[-1]
    return ((lo + hi) / 2.0, junction_z - drop_in)


def _in_crop(point, crop) -> bool:
    (cu0, cz0), (cu1, cz1) = crop
    u, z = point[0] * M_PER_IN, point[1] * M_PER_IN
    return min(cu0, cu1) <= u <= max(cu0, cu1) and min(cz0, cz1) <= z <= max(cz0, cz1)
