"""A framing angle nailed member-to-plate: one leaf up a member face, one flat on the sill.

The A35 as a joist-to-sill or block-to-sill tie (C-C-2026 A35 installation "joist to sill"):
the strip's width runs along the face, and its length folds half up the face and half
across the sill top. ``ties._angle_tie`` keeps the upright post-to-beam frame the authored
angles use. Heights come from the sill return under the tie, never from authored values.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.hardware.catalog import ROLE_SILL_TIE, ROLE_WALL_TOP_TIE
from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import box_mesh, combine_meshes, transform_mesh
from typehaus.resolve.geometry_ir import GMesh

_ALIASES = {"A35Z": "A35", "A35SS": "A35"}


@dataclass(frozen=True)
class PlateAngle:
    width_m: float  # along the face
    leg_m: float  # each leaf, off the heel
    thickness_m: float


def plate_angle_dims(part: str) -> PlateAngle | None:
    from typehaus.resolve.connector_geometry.ties import ANGLES, STEEL_THICKNESS_IN

    name = _ALIASES.get(part.strip().upper(), part.strip().upper())
    if name != "A35":
        return None
    d = ANGLES[name]
    return PlateAngle(d.leaf_width_in * M_PER_IN, d.height_in / 2.0 * M_PER_IN,
                      STEEL_THICKNESS_IN[d.gauge] * M_PER_IN)


def is_plate_angle(joint, part: str) -> bool:
    return joint.role in (ROLE_WALL_TOP_TIE, ROLE_SILL_TIE) and plate_angle_dims(part) is not None


def plate_angle_mesh(dims: PlateAngle, centre, inward, z_m: float) -> GMesh:
    """The L with its heel centred on ``centre`` (on the face, at ``z_m``), flat leaf inward."""
    w, leg, t = (v / M_PER_IN for v in (dims.width_m, dims.leg_m, dims.thickness_m))
    body = combine_meshes(box_mesh((-w / 2, 0.0, 0.0), (w / 2, leg, t)),
                          box_mesh((-w / 2, 0.0, t), (w / 2, t, leg)))
    nx, ny = inward
    return transform_mesh(body, origin_m=(centre[0], centre[1], z_m),
                          x_axis=(ny, -nx, 0.0), y_axis=(nx, ny, 0.0), z_axis=(0.0, 0.0, 1.0))


def footprint(centre, inward, dims):
    """The flat leaf's plan rectangle on the sill."""
    from shapely.geometry import Polygon

    h, (nx, ny) = dims.width_m / 2.0, inward
    heel = (ny, -nx)
    return Polygon([(centre[0] + heel[0] * s + nx * d, centre[1] + heel[1] * s + ny * d)
                    for s, d in ((-h, 0.0), (h, 0.0), (h, dims.leg_m), (-h, dims.leg_m))])


def _sill_tie_face(index, joint, floor, dims):
    """``(centre, inward)`` for a joist-end tie: the pack's faces this member owns, in order
    (``sill_tie_pack``); ``#n`` on the joint's member key is the nth."""
    from typehaus.resolve.connector_geometry.sill_tie_pack import sill_pack

    key, _, ply = (joint.carried_member_key or "").partition("#")
    member = index.members.get(key)
    if member is None:
        return None
    ties = sill_pack(member, joint.point, floor, index.model.floors, dims).ties
    if not ties:
        return None
    tie = ties[min(int(ply or 0), len(ties) - 1)]
    return tie.centre, tie.inward


def plate_angle_body(index, joint) -> GMesh | None:
    """The tie at a wall-top station or a joist end, on its face and the sill top."""
    from typehaus.joints.wall_top import edge_face, sill_returns, sill_top_z

    dims = plate_angle_dims(joint.part)
    wall = index.model.wall(joint.members[0]) if joint.members else None
    floor = index.hosts.get(joint.members[1]) if len(joint.members) > 1 else None
    if dims is None or wall is None or floor is None:
        return None
    if joint.role == ROLE_WALL_TOP_TIE:
        face = edge_face(floor, wall)
        if face is None:
            return None
        placed = (joint.point, face[1])
    else:
        placed = _sill_tie_face(index, joint, floor, dims)
        if placed is None:
            return None
    centre, inward = placed
    top = wall.plate_top_z_m if wall.plate_top_z_m is not None else wall.z1_m
    probe = (centre[0] + inward[0] * dims.leg_m / 2, centre[1] + inward[1] * dims.leg_m / 2)
    returns = index.__dict__.get("_plate_angle_returns")
    if returns is None:
        returns = index.__dict__["_plate_angle_returns"] = sill_returns(index.model)
    z_m = sill_top_z(index.model, probe, top, returns)
    return plate_angle_mesh(dims, centre, inward, joint.z_m if z_m is None else z_m)
