"""Sill ties on closely spaced joist ends: one pack, tied on its outer faces.

``joints/bearing`` gives each end on a concrete wall ``JoistSpec.sill_tie``s; this pass reads
the slot each tie needs (``resolve/connector_geometry/sill_tie_pack``) across every floor, so
ends of two fields at a seam pack together. An end inside a pack owns no tie; the pack's two
outer ends own one each. A tie with framing over its leaf keeps its ``blocked_by``, which
``code.MN_1309_0404_wall_top`` grades UNKNOWN.
"""

from __future__ import annotations

from dataclasses import replace


def pack_sill_ties(model, connections: list, tied=frozenset({"joist"})) -> list:
    """``connections`` with each sill-tied end's tie count, pack and blocked slots."""
    from typehaus.resolve.connector_geometry.plate_angle import plate_angle_dims
    from typehaus.resolve.connector_geometry.sill_tie_pack import sill_pack

    members = {f"{m.parent_uid}:{m.child_key}": (m, floor)
               for floor in model.floors for m in floor.members}
    out = []
    for c in connections:
        found = members.get(c.member_key or "") if c.sill_tie else None
        dims = plate_angle_dims(c.sill_tie) if found else None
        if dims is None:
            out.append(c)
            continue
        member, floor = found
        pack = sill_pack(member, c.point_m, floor, model.floors, dims, tied)
        count = len(pack.ties) if pack.members > 1 else c.sill_ties
        out.append(replace(c, sill_ties=count, pack_extent_m=pack.extent_m,
                           pack_members=pack.members,
                           blocked_by=tuple(sorted({k for t in pack.ties for k in t.blocked_by}))))
    return out
