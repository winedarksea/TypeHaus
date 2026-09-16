"""``derived_joints`` — every joint this engine derives, in one list, sorted by key.

This is the function the four readers share. Each locator below already answers "where does
this family of connection occur"; here each answer is turned into the one shape, given its
catalog part and its identity, and returned in a stable order.

**Coverage is declared, not assumed.** :data:`COVERED_ROLES` names exactly the roles this
function accounts for, and ``tests/test_connector_markers.py`` asserts that the joints of
each covered role, the BOM rows of that role, and the marker solids of that role are the
same number. A role absent from the set is a role whose derivation is still a run rather
than a joint — the stud plate ties, the coil strap, the knee braces, the resolver's own
hanger members — and the test knows it is out of scope rather than silently missing.
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    EXPOSURE_DRY,
    EXPOSURE_TREATED,
    ROLE_BEAM_HOLD_DOWN,
    ROLE_EMBEDDED_STRAP_HOLDOWN,
    ROLE_FACE_MOUNT_JOIST_HANGER,
    ROLE_GABLE_END_TIE,
    ROLE_GABLE_TRUSS_ANCHOR,
    ROLE_HURRICANE_TIE,
    ROLE_IJOIST_FACE_MOUNT_HANGER,
    ROLE_LATERAL_TIE_PLATE,
    ROLE_MUDSILL_ANCHOR,
    ROLE_POST_BASE,
    ROLE_POST_BASE_ANCHOR,
    ROLE_RIDGE_TIE_STRAP,
    ROLE_SLOPED_JOIST_HANGER,
    hardware_for_role,
    hardware_for_role_and_nominal,
)
from typehaus.hardware.config import (
    DEFAULT_HARDWARE_TAKEOFF_CONFIG,
    HardwareTakeoffConfig,
)
from typehaus.joints.authored import hanger_part, hanger_specs
from typehaus.joints.bearing import bearing_connections, continuous_bearing_members
from typehaus.joints.gable import gable_end_ties
from typehaus.joints.hosts import member_storeys
from typehaus.joints.hung import hung_connections, point_along, ridge_strap_pairs
from typehaus.joints.model import Joint, axis_of, joint_key
from typehaus.joints.posts import (
    bears_on_concrete,
    post_base_anchor_joints,
    post_base_joints,
    post_beam_strap_joints,
)
from typehaus.joints.sills import (
    mudsill_anchor_stations,
    strap_holdown_stations,
    tie_plate_stations,
)
from typehaus.quantities import M_PER_IN

#: Every role :func:`derived_joints` accounts for. See the module docstring.
COVERED_ROLES = frozenset({
    ROLE_GABLE_END_TIE,
    ROLE_GABLE_TRUSS_ANCHOR,
    ROLE_HURRICANE_TIE,
    ROLE_MUDSILL_ANCHOR,
    ROLE_SLOPED_JOIST_HANGER,
    ROLE_FACE_MOUNT_JOIST_HANGER,
    ROLE_IJOIST_FACE_MOUNT_HANGER,
    ROLE_RIDGE_TIE_STRAP,
    ROLE_EMBEDDED_STRAP_HOLDOWN,
    ROLE_LATERAL_TIE_PLATE,
    ROLE_POST_BASE,
    ROLE_POST_BASE_ANCHOR,
    ROLE_BEAM_HOLD_DOWN,
})


def derived_joints(model, config: HardwareTakeoffConfig = DEFAULT_HARDWARE_TAKEOFF_CONFIG
                   ) -> list[Joint]:
    """Every derived structural connection in the building, sorted by :attr:`Joint.key`.

    Sorted *always*, and by the key rather than by discovery order: ``shell_json`` sorts
    solids by uid and a marker list that reshuffled when an unrelated element moved would
    turn a one-line edit into a whole-file diff.
    """
    grid_m = max(config.uplift.coincident_bearing_tolerance_in, 1e-6) * M_PER_IN
    out: list[Joint] = []
    out.extend(_bearing_tie_joints(model, config, grid_m))
    out.extend(_continuous_tie_joints(model, config, grid_m))
    out.extend(_gable_tie_joints(model, config, grid_m))
    out.extend(_hanger_joints(model, config, grid_m))
    out.extend(_ridge_strap_joints(model, config, grid_m))
    out.extend(_sill_joints(model, config, grid_m))
    out.extend(_post_joints(model, config, grid_m))
    return sorted(out, key=lambda joint: joint.key)


def _joint(role: str, part: str, storey: str, point, z_m: float, axis: str,
           embedded: bool, members, anchor_tag: str, grid_m: float,
           height_m: float | None = None) -> Joint:
    point = (float(point[0]), float(point[1]))
    return Joint(role=role, part=part, storey=storey, point=point, z_m=float(z_m),
                 axis=axis, embedded=embedded, members=tuple(members),
                 key=joint_key(role, anchor_tag, point, float(z_m), grid_m),
                 height_m=height_m)


def _bearing_tie_joints(model, config: HardwareTakeoffConfig, grid_m: float) -> list[Joint]:
    """One tie per bearing joint. The coating follows the SUPPORT's wood, per IRC R317.3.1.

    Deliberately not "indoors or out": the rafter heels on catlin's weather walls sit on dry
    SPF plates under a roof, and sweeping those onto a ZMAX part would be a house-wide price
    rise bought with no code requirement behind it.
    """
    ties = config.uplift.ties_per_bearing
    out: list[Joint] = []
    for connection in bearing_connections(model, config.uplift):
        exposure = EXPOSURE_TREATED if connection.support_treated else EXPOSURE_DRY
        item = hardware_for_role(ROLE_HURRICANE_TIE, exposure=exposure)
        for _ in range(ties):
            out.append(_joint(
                ROLE_HURRICANE_TIE, item.model, connection.storey, connection.point_m,
                connection.z_m, connection.axis, embedded=False,
                members=(connection.support_tag, connection.assembly_tag),
                anchor_tag=connection.support_tag, grid_m=grid_m))
    return out


def _continuous_tie_joints(model, config: HardwareTakeoffConfig,
                           grid_m: float) -> list[Joint]:
    """Ties along a member bedded on its support for its whole length — catlin's ridge.

    Always DRY: ``continuously_supported`` is set on a beam bedded along a wall, which in
    this house is the interior ridge on a dry SPF plate. A member carries no material ref of
    its own, so there is nothing here to ask with yet, and an invented answer would be worse
    than a stated assumption.
    """
    item = hardware_for_role(ROLE_HURRICANE_TIE, exposure=EXPOSURE_DRY)
    out: list[Joint] = []
    for run in continuous_bearing_members(model, config.uplift):
        axis = axis_of(run.p0, run.p1)
        for station_m in run.stations_m:
            out.append(_joint(
                ROLE_HURRICANE_TIE, item.model, run.storey,
                point_along(run.p0, run.p1, station_m), run.z_m, axis, embedded=False,
                members=(run.profile,), anchor_tag=f"{run.category}:{run.profile}",
                grid_m=grid_m))
    return out


def _carrier_storeys(model) -> dict:
    """``carrier tag -> storey`` for every thing a member can hang off."""
    out = {solid.tag: solid.storey for solid in model.solids}
    for parent_uid, storey in member_storeys(model).items():
        out.setdefault(parent_uid, storey)
    for hosts in (model.walls, model.stairs, model.floors, model.roofs,
                  model.braces, model.soffits):
        for host in hosts:
            for member in host.members:
                out[f"{member.parent_uid}:{member.child_key}"] = host.storey
    return out


def _gable_tie_joints(model, config: HardwareTakeoffConfig, grid_m: float) -> list[Joint]:
    """A tie at every station along every gable-end wall's top plate.

    The leg no bearing rule can see, because no rafter bears on a gable end. See
    :mod:`typehaus.joints.gable` for how one is told from an eave wall.
    """
    out: list[Joint] = []
    for end in gable_end_ties(model, config.gable_end_ties):
        item = hardware_for_role(end.role)
        # ``station_z_m``, never the scalar ``end.z_m``: a gable wall RAKES, and its
        # ``z1_m`` is the bounding prism's ridge height rather than the plate the tie is
        # nailed to. Zipped strict — the two tuples are built together and a length
        # mismatch would silently drop or mislocate ties.
        for station_m, station_z in zip(end.stations_m, end.station_z_m, strict=True):
            out.append(_joint(
                end.role, item.model, end.storey,
                point_along(end.p0, end.p1, station_m), station_z, end.axis, embedded=False,
                members=(end.wall_tag, end.roof_tag), anchor_tag=end.wall_tag,
                grid_m=grid_m))
    return out


def _hanger_joints(model, config: HardwareTakeoffConfig, grid_m: float) -> list[Joint]:
    """A hanger at every hung end, sloped and level being two different parts."""
    storeys = _carrier_storeys(model)
    specs = hanger_specs(model)
    out: list[Joint] = []
    for connection in hung_connections(model, config.hanger_detection):
        role, _item, part = hanger_part(connection, specs)
        out.append(_joint(
            role, part, storeys.get(connection.carrier_tag, ""),
            connection.point_m, connection.carrier_soffit_m, connection.axis,
            embedded=False, members=(connection.carrier_tag, connection.member_profile),
            anchor_tag=connection.carrier_tag, grid_m=grid_m,
            height_m=connection.member_depth_m))
    return out


def _ridge_strap_joints(model, config: HardwareTakeoffConfig, grid_m: float) -> list[Joint]:
    item = hardware_for_role(ROLE_RIDGE_TIE_STRAP)
    storeys = _carrier_storeys(model)
    out: list[Joint] = []
    for straps in ridge_strap_pairs(model, config.hanger_detection):
        storey = storeys.get(straps.carrier_tag, "")
        for station_m in straps.stations_m:
            out.append(_joint(
                ROLE_RIDGE_TIE_STRAP, item.model, storey,
                point_along(straps.p0, straps.p1, station_m), straps.z_m, straps.axis,
                embedded=False, members=(straps.carrier_tag,),
                anchor_tag=straps.carrier_tag, grid_m=grid_m))
    return out


def _sill_joints(model, config: HardwareTakeoffConfig, grid_m: float) -> list[Joint]:
    rules, category = config.sill_plate_anchors, config.sill_plate_takeoff_category
    masa = hardware_for_role(ROLE_MUDSILL_ANCHOR)
    sthd = hardware_for_role(ROLE_EMBEDDED_STRAP_HOLDOWN)
    ltp = hardware_for_role(ROLE_LATERAL_TIE_PLATE)
    out: list[Joint] = []
    for station in mudsill_anchor_stations(model, rules, category):
        out.append(_joint(ROLE_MUDSILL_ANCHOR, masa.model, station.storey, station.point_m,
                          station.z_m, station.axis, embedded=True,
                          members=(station.run_tag,), anchor_tag=station.run_tag,
                          grid_m=grid_m))
    for station in strap_holdown_stations(model, rules, category):
        out.append(_joint(ROLE_EMBEDDED_STRAP_HOLDOWN, sthd.model, station.storey,
                          station.point_m, station.z_m, station.axis, embedded=True,
                          members=(station.run_tag,), anchor_tag=station.run_tag,
                          grid_m=grid_m))
    for station in tie_plate_stations(model, config.uplift):
        out.append(_joint(ROLE_LATERAL_TIE_PLATE, ltp.model, station.storey, station.point_m,
                          station.z_m, station.axis, embedded=False,
                          members=(station.run_tag,), anchor_tag=station.run_tag,
                          grid_m=grid_m))
    return out


def _post_joints(model, config: HardwareTakeoffConfig, grid_m: float) -> list[Joint]:
    """Post bases, their cast-in anchors, and the straps at beam ends landing on posts.

    ``embedded`` is answered here rather than in the marker table, from what is actually
    under the joint: a post base that moves from a pier to a deck re-files itself honestly,
    and its part leaves the concrete sub's RFQ without anyone editing a list.
    """
    out: list[Joint] = []
    for storey, post in post_base_joints(model, config.uplift):
        item = hardware_for_role_and_nominal(ROLE_POST_BASE, post.size)
        point, axis = _post_point(model, post)
        out.append(_joint(ROLE_POST_BASE, item.model, storey, point,
                          _post_base_z(model, post), axis,
                          embedded=bears_on_concrete(model, post),
                          members=(post.tag, post.supported_by or ""),
                          anchor_tag=post.tag, grid_m=grid_m))
    anchor = hardware_for_role(ROLE_POST_BASE_ANCHOR)
    for storey, post in post_base_anchor_joints(model, config.uplift):
        point, axis = _post_point(model, post)
        out.append(_joint(ROLE_POST_BASE_ANCHOR, anchor.model, storey, point,
                          _post_base_z(model, post), axis, embedded=True,
                          members=(post.tag, post.supported_by or ""),
                          anchor_tag=post.tag, grid_m=grid_m))
    strap = hardware_for_role(ROLE_BEAM_HOLD_DOWN)
    per_joint = config.uplift.straps_per_post_beam_joint
    for storey, beam, post in post_beam_strap_joints(model, config.uplift):
        point, axis = _post_point(model, post)
        for _ in range(per_joint):
            out.append(_joint(ROLE_BEAM_HOLD_DOWN, strap.model, storey, point,
                              _post_top_z(model, post), axis, embedded=False,
                              members=(beam.tag, post.tag),
                              anchor_tag=f"{beam.tag}->{post.tag}", grid_m=grid_m))
    return out


def _post_solid(model, post):
    for solid in model.solids:
        if solid.tag == post.tag:
            return solid
    return None


def _post_point(model, post) -> tuple[tuple[float, float], str]:
    """A post's plan centroid and its orientation, read off the resolved solid.

    Off the *resolved* solid rather than the authored position, because the authored one is
    a node reference plus an offset and the resolver is what turns those into a place.
    """
    solid = _post_solid(model, post)
    if solid is None or not solid.outline:
        return (0.0, 0.0), "x"
    xs = [point[0] for point in solid.outline]
    ys = [point[1] for point in solid.outline]
    centre = (sum(xs) / len(xs), sum(ys) / len(ys))
    axis = "x" if (max(xs) - min(xs)) >= (max(ys) - min(ys)) else "y"
    return centre, axis


def _post_base_z(model, post) -> float:
    solid = _post_solid(model, post)
    return solid.z0_m if solid is not None else 0.0


def _post_top_z(model, post) -> float:
    solid = _post_solid(model, post)
    return solid.z1_m if solid is not None else 0.0
