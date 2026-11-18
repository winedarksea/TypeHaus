"""A door approach that rests at both ends: on the truss wall's girt sill course, and on the
landing's own member (``ApproachBearing``). Nothing cantilevers and nothing is fixed across
the house/landing joint.

Depths here are the installation's layout frame: outward-positive, ``layout = sign * local``,
where ``local`` is the wall normal from the opening's centre (the sections' own frame).
"""

from dataclasses import dataclass
from math import ceil

from shapely.geometry import LineString, Polygon

from typehaus.resolve.exterior_door_sections import DoorSectionBuilder
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import opening_center, wall_frame

_IN = 0.0254
_TOL = _IN / 32
_LANDING_MEMBERS = ("joist", "sister_joist", "rim", "band", "blocking", "ledger")
#: How far out from the sheathing a landing member is looked for.
_LANDING_REACH = 18 * _IN
#: The share of the approach's width a landing member must run under; past its ends the
#: landing's own decking (which oversails its end joists) carries the rest.
_MIN_COVER = 0.75
#: A pan wrapped down a sill beam's face ends in a short drip, clear of a cover seat below.
_DRIP_LEG = 0.5 * _IN


@dataclass(frozen=True)
class BridgeSupport:
    sheathing: float
    girt_key: str | None = None
    girt_inner: float | None = None
    girt_face: float | None = None
    girt_bottom: float | None = None
    girt_top: float | None = None
    buck_top: float | None = None
    member: str | None = None
    member_inner: float | None = None
    member_outer: float | None = None
    member_top: float | None = None
    member_cover: float | None = None
    deck_edge: float | None = None
    deck_top: float | None = None
    conflicts: tuple[str, ...] = ()


def bridge_support(model, wall, opening, placement, base, half_width):
    """Locate the girt sill course, the buck sill and the landing member under a door."""
    bearing = placement.specification.approach_bearing
    sign = placement.outward_sign
    center = opening_center(wall, opening)
    _, tangent, normal, _ = wall_frame(wall)

    def local(point):
        delta = (point[0] - center[0], point[1] - center[1])
        return (sign * (delta[0] * normal[0] + delta[1] * normal[1]),
                delta[0] * tangent[0] + delta[1] * tangent[1])

    conflicts = []
    support = dict(sheathing=sign * placement.frame_outer_m)
    girt = _covering(wall.members, local, ("ladder-sill-",), -half_width, half_width)
    if girt is not None:
        depth, across = _across_faces(girt, local)
        support.update(girt_key=girt.child_key, girt_inner=depth - across,
                       girt_face=depth + across, girt_bottom=girt.z0_m, girt_top=girt.z1_m)
    elif bearing.girt_course:
        conflicts.append("no girt sill course under the approach")
    buck = _covering(wall.members, local, ("buck-sill-",), -half_width, half_width)
    if buck is not None:
        support["buck_top"] = buck.z1_m
        if buck.z1_m > base + _TOL:
            conflicts.append("buck sill stands above the rough sill and dams the pan")
    floor = next((f for f in model.floors if f.tag == bearing.landing_ref), None)
    if floor is None:
        conflicts.append(f"approach landing {bearing.landing_ref} does not resolve")
        return BridgeSupport(**support, conflicts=tuple(conflicts))
    start = support.get("girt_face", support["sheathing"])
    candidates = []
    for member in floor.members:
        if member.category not in _LANDING_MEMBERS:
            continue
        (d0, a0), (d1, a1) = local(member.p0), local(member.p1)
        cover = min(max(a0, a1), half_width) - max(min(a0, a1), -half_width)
        if abs(d0 - d1) > _TOL or cover < _MIN_COVER * 2 * half_width:
            continue
        half = cross_section(member.profile).width_m / 2
        if start - _TOL <= d0 - half <= start + _LANDING_REACH:
            candidates.append((d0 - half, d0 + half, member, cover / (2 * half_width)))
    if not candidates:
        conflicts.append(f"no member of {floor.tag} runs under the approach's outer end")
    else:
        inner, outer, member, cover = min(candidates, key=lambda c: c[0])
        support.update(member=member.child_key, member_inner=inner, member_outer=outer,
                       member_top=member.z1_m, member_cover=min(cover, 1.0))
    ray = LineString([_plan(center, normal, tangent, sign * d, 0.0)
                      for d in (support["sheathing"], support["sheathing"] + _LANDING_REACH)])
    crossing = Polygon(floor.deck_outline, holes=list(floor.deck_voids)).intersection(ray)
    depths = [local(p)[0] for line in getattr(crossing, "geoms", (crossing,))
              for p in getattr(line, "coords", ())]
    if depths:
        support["deck_edge"] = min(depths)
    support["deck_top"] = floor.deck_z1_m
    return BridgeSupport(**support, conflicts=tuple(conflicts))


def girt_course_connection(model, wall, opening, placement, support):
    """``(report fields, unknown, conflicts)`` of the girt sill course's screws."""
    course = next((m for m in wall.members if m.child_key == support.girt_key), None)
    if course is None:
        return dict(connection_status="NOT_APPLICABLE", connection_demand_lb=0.0,
                    connection_capacity_lb=None, connection_dcr=None), [], []
    from typehaus.resolve.girt_sill_connection import girt_sill_connection

    return girt_sill_connection(model, wall, opening, placement, course)


def gap_landing_conflicts(support, bearing, nose, movement):
    """The approach stops short: the landing's plank ends bear on its member, and the open
    gap to the nose survives the reserved movement."""
    conflicts = []
    if support.member_inner is None or support.deck_edge is None:
        return conflicts
    if not (support.member_inner - _TOL <= support.deck_edge
            <= support.member_outer - bearing.plank_bearing.meters + _TOL):
        conflicts.append("landing plank ends at the door stand off their member")
    gap = min(support.deck_edge, support.member_inner) - nose
    if gap <= movement + _TOL:
        conflicts.append("house/landing movement closes the gap at the approach nose")
    return conflicts


def slip_pad_seat(support, bearing, deck_top, cut):
    """``(pad start, pad base, deck cut line)``: on the deck over the member where the deck
    left past the pan's drip (``cut``) still covers it by the minimum, else on the member
    itself with the deck cut back over it."""
    if support.member_inner is None or deck_top is None:
        return None, None, None
    edge = max(support.deck_edge if support.deck_edge is not None else cut, cut)
    lo = max(support.member_inner, edge)
    if support.member_outer - lo >= bearing.minimum_bearing.meters - _TOL:
        return lo, deck_top, (cut if support.deck_edge is None or cut > support.deck_edge
                              else None)
    return support.member_inner, support.member_top, support.member_outer


def slip_pad_bearing(support, bearing, plate_bottom, deck_top, lo=None):
    """``(bearing length, pad thickness, conflicts)`` of an approach resting on the landing."""
    if support.member_inner is None or support.deck_edge is None or deck_top is None:
        return None, None, []
    if lo is None:
        lo = max(support.member_inner, support.deck_edge)
    length = support.member_outer - lo
    pad = plate_bottom - deck_top
    conflicts = []
    if length < bearing.minimum_bearing.meters - _TOL:
        conflicts.append("approach bears on less of the landing member than its minimum")
    if not 0 <= pad <= bearing.maximum_pad_thickness.meters + _TOL:
        conflicts.append(f"approach slip pad would be {pad / _IN:.3f}\" thick")
    return length, pad, conflicts


def add_bridge_sections(builder: DoorSectionBuilder, spec, installation, layout, support,
                        pan_outlet, fall=0.0):
    """Pan over the buck to its drip; draining strips on it out to the girt course's face
    carry the sill's overhang and the extender. A sill beam standing proud of the cladding
    takes the pan over its top, falling ``fall`` across it, and down its face to a drip."""
    membrane = layout.membrane
    face = support.sheathing
    wrap = support.girt_face is not None and pan_outlet <= support.girt_face + _TOL
    back = support.girt_inner if wrap else pan_outlet
    builder.section("impermeable-pan-apron", ((face, layout.base), (back, layout.base),
                                              (pan_outlet, layout.base - fall),
                                              (pan_outlet, layout.base - fall + membrane),
                                              (back, layout.base + membrane),
                                              (face, layout.base + membrane)),
                    spec.pan_material_ref, "membrane")
    drip = _DRIP_LEG if wrap else 3 * _IN
    builder.rectangle("pan-outlet-drop", pan_outlet, pan_outlet + membrane,
                      layout.base - fall - drip, layout.base - fall + membrane,
                      spec.pan_material_ref, "membrane")
    reach = support.girt_face if support.girt_face is not None else face
    if reach - face <= _TOL:
        return 0
    width, spacing = 1.5 * _IN, 8 * _IN
    intervals = max(1, ceil((layout.width - width) / spacing))
    isolation = installation.wrap_isolation_thickness.meters
    for index in range(intervals + 1):
        along = -(layout.width - width) / 2 + index * (layout.width - width) / intervals
        builder.rectangle(f"bridge-bearing-strip-{index}", face, reach,
                          layout.base + membrane, layout.seat - isolation, "kdat", "lumber",
                          span=width, along=along)
        builder.rectangle(f"bridge-bearing-isolation-{index}", face, reach,
                          layout.seat - isolation, layout.seat,
                          installation.wrap_isolation_material_ref, "membrane", span=width,
                          along=along, purchase="allowance_included")
    return intervals + 1


def _plan(center, normal, tangent, depth, along):
    return (center[0] + normal[0] * depth + tangent[0] * along,
            center[1] + normal[1] * depth + tangent[1] * along)


def _covering(members, local, prefixes, lo, hi):
    """The member whose child key starts with ``prefixes`` and runs the whole span."""
    for member in members:
        if not member.child_key.startswith(prefixes):
            continue
        a0, a1 = sorted((local(member.p0)[1], local(member.p1)[1]))
        if a0 <= lo + 2 * _IN and a1 >= hi - 2 * _IN:
            return member
    return None


def _across_faces(member, local):
    """``(centre depth, half thickness across the wall)`` of a flat-laid member."""
    section = cross_section(member.profile)
    height = member.z1_m - member.z0_m
    across = section.width_m if abs(height - section.depth_m) < _TOL else section.depth_m
    return local(member.p0)[0], across / 2


def bridge_installation(model, wall, opening, placement, layout, clad):
    """A catalog ``girt_bridge`` door: ``(support report, sections, conflicts, unknown)``."""
    from typehaus.resolve.exterior_door_cover import add_cover

    installation = placement.specification
    spec = installation.catalog_installation
    bearing = installation.approach_bearing
    support = bridge_support(model, wall, opening, placement, layout.base, layout.width / 2)
    conflicts = list(support.conflicts)
    builder = DoorSectionBuilder(placement.outward_sign, layout.width)
    pan_outlet = placement.outward_sign * clad + installation.drainage_gap.meters
    fall = 0.0
    # A sill beam proud of the cladding: the pan wraps its face, falling across its top.
    if support.girt_face is not None and support.girt_face > placement.outward_sign * clad:
        pan_outlet = support.girt_face
        sill = _sill_course_spec(model, wall)
        if sill is not None:
            fall = ((support.girt_face - support.girt_inner)
                    * sill.course_fall_per_ft.meters / 0.3048)
    strips = add_bridge_sections(builder, spec, installation, layout, support, pan_outlet, fall)
    if bearing.landing == "slip_pad":
        conflicts.append("a catalog extender stops short of its landing: use a gap or a cover")
    house_face = max(layout.end, support.girt_face if support.girt_face is not None
                     else layout.end)
    conflicts.extend(gap_landing_conflicts(support, bearing, house_face,
                                           spec.movement_horizontal.meters))
    overhang = None
    if support.girt_face is not None:
        overhang = layout.end - support.girt_face
        if layout.end < support.girt_inner - _TOL:
            conflicts.append("the extender stops short of the girt sill course")
        if pan_outlet > layout.end + _TOL and pan_outlet > support.girt_face + _TOL:
            conflicts.append("the pan's drip stands past the extender's nose")
    gap = (min(support.deck_edge, support.member_inner) - house_face
           if support.deck_edge is not None and support.member_inner is not None else None)
    connection, unknown, connection_conflicts = girt_course_connection(
        model, wall, opening, placement, support)
    conflicts.extend(connection_conflicts)
    if overhang is not None and overhang > _TOL:
        unknown.append(f"{spec.sill_extender_ref}: its nose runs {overhang / _IN:.2f}\" past "
                       "the girt sill course; its support there is a supplier hold")
    unknown.append(f"{spec.sill_extender_ref}: the prehung assembly on this sill is a "
                   "supplier hold")
    cover = {}
    if bearing.landing == "cover":
        cover, cover_conflicts, cover_unknown = add_cover(
            model, builder, bearing, support, house_face, layout,
            spec.movement_horizontal.meters)
        conflicts.extend(cover_conflicts)
        unknown.extend(cover_unknown)
    report = dict(
        member_status=connection.pop("member_status", "NOT_APPLICABLE"), **connection,
        kind="girt_bridge", girt_face_in=_inch(support.girt_face),
        buck_top_z_m=support.buck_top, extender_overhang_in=_inch(overhang),
        landing=bearing.landing, landing_member=support.member,
        landing_member_cover=support.member_cover,
        landing_member_inner_in=_inch(support.member_inner),
        landing_deck_edge_in=_inch(support.deck_edge), nose_gap_in=_inch(gap),
        pan_outlet_in=pan_outlet / _IN, pan_fall_in=fall / _IN, bearing_strips=strips,
        **cover)
    return report, tuple(builder.sections), conflicts, unknown


def _sill_course_spec(model, wall):
    from typehaus.resolve.framing.truss_girts import truss_girt_bands

    bands = truss_girt_bands(model.plan, wall.assembly)
    return bands[1].framing.sill_course if bands and bands[1].framing else None


def _inch(value):
    return None if value is None else value / _IN
