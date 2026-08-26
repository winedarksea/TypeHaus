"""Resolve ``WallPaneling`` bands onto their room's bounding walls (→ model/paneling.py).

Each authored paneling becomes one :class:`ResolvedPaneling` per covered wall, its area
already net of the openings that punch the band, so downstream consumers sum rather than
re-intersect. Refs that resolve to nothing are ERROR findings, never a silent zero — a
typo'd room tag must not make a wainscot vanish from the order (#32).
"""

from __future__ import annotations

from typehaus.findings import Finding, failed
from typehaus.model.plan import PlanModel
from typehaus.resolve.model import ResolvedModel, ResolvedPaneling
from typehaus.resolve.room_walls import bounding_walls


def resolve_paneling(plan: PlanModel, model: ResolvedModel) -> list[Finding]:
    findings: list[Finding] = []
    materials = {material.tag for material in plan.library.materials}
    rooms = {room.tag: room for room in model.rooms}
    lines = {line.tag: line for line in model.layout_lines}
    for storey in plan.storeys:
        for el in plan.storey_elements(storey.tag):
            if el.element_kind != "WallPaneling":
                continue
            line_ref = getattr(el, "layout_line", None)
            # Exactly one scope. Naming both would need a precedence rule nobody could
            # guess from the source, and naming neither is a band with no walls.
            if bool(el.room) == bool(line_ref):
                findings.append(_error(
                    el, f"paneling {el.tag} must name exactly one of room / layout_line "
                        f"(room={el.room!r}, layout_line={line_ref!r})"))
                continue
            room = rooms.get(el.room) if el.room else None
            line = lines.get(line_ref) if line_ref else None
            if el.room and room is None:
                findings.append(_error(el, f"paneling {el.tag} names no room {el.room!r}"))
                continue
            if line_ref and line is None:
                findings.append(_error(
                    el, f"paneling {el.tag} names no layout line {line_ref!r}"))
                continue
            if el.material_ref not in materials:
                findings.append(_error(
                    el, f"paneling {el.tag} names no material {el.material_ref!r}"))
                continue
            walls = (_line_walls(model, line) if line is not None
                     else bounding_walls(model, room))
            if el.walls:
                known = {wall.tag for wall, _ in walls}
                scope = f"bound room {room.tag}" if room is not None \
                    else f"belong to layout line {line.tag}"
                for ref in el.walls:
                    if ref not in known:
                        findings.append(_error(
                            el, f"paneling {el.tag} restricts to {ref!r}, which does not "
                                f"{scope}"))
                walls = [(wall, span) for wall, span in walls if wall.tag in el.walls]
            spans_by_wall: dict[str, list] = {}
            for span in el.spans:
                spans_by_wall.setdefault(span.wall_ref, []).append(span)
            for ref in spans_by_wall:
                if ref not in {wall.tag for wall, _ in walls}:
                    scope = f"bound room {room.tag}" if room is not None \
                        else f"belong to layout line {line.tag}"
                    findings.append(_error(
                        el, f"paneling {el.tag} spans wall {ref!r}, which does not "
                            f"{scope} (or is excluded by walls=)"))
            offset = el.offset.meters if el.offset is not None else 0.0
            thickness_m = _band_thickness_m(plan, el.material_ref)
            # Which side of its walls the band is on. A room-scoped band faces into its room,
            # and a point guaranteed to be *inside* the face answers that for an L-shaped room
            # too, where the centroid can fall outside. A line-scoped band has no room to
            # face, and which side of a facade line its band lands on is not derivable from
            # anything the model carries today — so those still resolve area-only, exactly as
            # every band did before this. Better no geometry than a band on the wrong face.
            toward = _interior_point(room) if room is not None else None
            for wall, (u0, u1) in walls:
                intervals = [(u0, u1)]
                if spans_by_wall:
                    if wall.tag not in spans_by_wall:
                        continue  # spans authored => only the named walls carry the band
                    intervals = [
                        (max(u0, span.start.meters),
                         min(u1, span.start.meters + span.length.meters))
                        for span in spans_by_wall[wall.tag]
                    ]
                # Band in wall-local z, up from the wall base (== the room floor), clamped
                # to the wall's own mean top so a 7'-6" sauna wall never bills 8' of band.
                # ``base_ref_z_m`` is what "the room floor" means once a wall is extended
                # down over the rim: the band and the opening subtraction below both live in
                # that frame, and mixing it with ``z0_m`` would offset one against the other.
                mean_top = ((wall.top_z0_m or wall.z1_m)
                            + (wall.top_z1_m or wall.z1_m)) / 2.0
                wall_height = mean_top - wall.base_ref_z_m
                # A line-scoped band measures from the LINE's base, so the same authored
                # offset means the same elevation on every storey it crosses; the record
                # itself stays wall-local, which is what every consumer already reads.
                datum = 0.0 if line is None else line.base_z_m - wall.base_ref_z_m
                band_z0 = min(max(datum + offset, 0.0), wall_height)
                band_z1 = (wall_height if el.height is None
                           else min(datum + offset + el.height.meters, wall_height))
                if band_z1 - band_z0 <= 0.0:
                    continue
                openings = [o for o in model.openings if o.host_wall == wall.tag]
                for lo, hi in intervals:
                    if hi - lo <= 1e-6:
                        continue
                    area = (hi - lo) * (band_z1 - band_z0)
                    for o in openings:
                        du = (min(hi, o.center_along_m + o.width_m / 2.0)
                              - max(lo, o.center_along_m - o.width_m / 2.0))
                        dz = (min(band_z1, o.sill_m + o.height_m)
                              - max(band_z0, o.sill_m))
                        if du > 0.0 and dz > 0.0:
                            area -= du * dz
                    if area <= 0.0:
                        continue
                    outline = ([] if toward is None else
                               _band_outline(wall, lo, hi, toward, thickness_m,
                                             el.replaces_wall_finish))
                    model.panelings.append(ResolvedPaneling(
                        uid=el.uid, tag=el.tag, storey=wall.storey,
                        room=room.tag if room is not None else None,
                        wall_tag=wall.tag, material_ref=el.material_ref,
                        area_m2=area, band_z0_m=band_z0, band_z1_m=band_z1,
                        run_m=hi - lo, replaces_wall_finish=el.replaces_wall_finish,
                        layout_line=line.tag if line is not None else None,
                        outline=outline,
                        # The record's own band is wall-local, measured up from
                        # ``base_ref_z_m``; geometry wants it absolute.
                        z0_m=None if not outline else wall.base_ref_z_m + band_z0,
                        z1_m=None if not outline else wall.base_ref_z_m + band_z1,
                        thickness_m=thickness_m,
                    ))
    return findings



# What a band stands proud of the wall by, where its material states no stock thickness. Half
# an inch — a tile-and-thinset bed, a panel — and visual only: nothing in the takeoff reads it.
# A band's *area* is what gets ordered, and that is measured on the face, not through it.

def _interior_point(room) -> tuple[float, float]:
    """A point guaranteed to lie inside a room's clear face — its side of its walls."""
    from shapely.geometry import Polygon

    point = Polygon(room.clear_face).representative_point()
    return (point.x, point.y)


_DEFAULT_BAND_THICKNESS_M = 0.0127


def _band_thickness_m(plan: PlanModel, material_ref: str) -> float:
    """How thick to draw a band, from its material's nominal board stock where it has one.

    ``stock_bf_per_sqft`` is board feet per square foot on NOMINAL thickness — 1.0 is 4/4,
    1.25 is 5/4 — so it doubles as the nominal thickness in inches. Stock under 2" dresses
    1/4" thinner (4/4 surfaces to 3/4", 5/4 to 1"), which is the figure a board actually
    stands proud by and the figure ``_SAUNA_LINER`` authors for its 5/4 liner.
    """
    material = next((m for m in plan.library.materials if m.tag == material_ref), None)
    nominal = getattr(material, "stock_bf_per_sqft", None) if material is not None else None
    if not nominal:
        return _DEFAULT_BAND_THICKNESS_M
    return max(0.003, (float(nominal) - 0.25) * 0.0254)



def _room_side_sign(wall, toward: tuple[float, float]) -> float:
    """+1 or -1: which way along the wall's plan normal the room lies.

    ``toward`` is a POINT inside the room, not a direction, so the test is against the vector
    from the wall's axis to it. Taking it as a direction (a bare dot with the point's
    coordinates) is the same arithmetic and silently right for a room north-east of the
    origin, which is why it wants saying: it flips for a wall whose room sits toward -x.
    """
    from typehaus.resolve.geometry import normal, sub, unit

    n = normal(unit(sub(wall.axis[1], wall.axis[0])))
    to_room = (toward[0] - wall.axis[0][0], toward[1] - wall.axis[0][1])
    return 1.0 if (n[0] * to_room[0] + n[1] * to_room[1]) >= 0.0 else -1.0


def _room_side_offset(wall, toward: tuple[float, float]) -> float:
    """How far the wall's face stands off its axis, on the side ``toward`` points to.

    Measured from the wall's own resolved layer polygons rather than from the room's clear
    face. That is deliberate: ``resolve/rooms.py::_lining_inset`` insets a claimed face by one
    uniform figure derived from ``Room.wall_lining`` rather than by each bounding wall's own
    resolved lining, so the clear face does *not* sit on the finish plane of a wall with an
    unusual liner — the sauna's 3 1/2" liner famously does not move its room polygon at all.
    Hanging a band off it would put the sauna's tile splash three inches inside the wall.

    The layer polygons have no such problem: they are where the wall's material actually is.
    """
    from typehaus.resolve.geometry import normal, sub, unit

    direction = unit(sub(wall.axis[1], wall.axis[0]))
    n = normal(direction)
    sign = _room_side_sign(wall, toward)
    x0, y0 = wall.axis[0]
    best = 0.0
    for layer in wall.layers:
        for (px, py) in layer.polygon:
            offset = ((px - x0) * n[0] + (py - y0) * n[1]) * sign
            best = max(best, offset)
    return best


def _band_outline(wall, lo: float, hi: float, toward: tuple[float, float],
                  thickness_m: float, replaces_finish: bool):
    """The band's plan rectangle: the ``lo``..``hi`` stretch of the wall's room-side face.

    A band that *replaces* the wall finish occupies the depth that finish had, so it lies
    between the face and ``thickness_m`` back into the wall. A band added over the finish — a
    wainscot — stands proud of it by the same amount. Getting this backwards is visible: the
    tile splash would float off the sauna wall, and the wainscot would be buried in it.
    """
    from typehaus.resolve.geometry import add, rect_between, scale, sub, unit

    direction = unit(sub(wall.axis[1], wall.axis[0]))
    sign = _room_side_sign(wall, toward)
    face = _room_side_offset(wall, toward)
    inner, outer = ((face - thickness_m, face) if replaces_finish
                    else (face, face + thickness_m))
    p0 = add(wall.axis[0], scale(direction, lo))
    p1 = add(wall.axis[0], scale(direction, hi))
    return [(float(x), float(y))
            for (x, y) in rect_between(p0, p1, inner * sign, outer * sign)]


def _line_walls(model: ResolvedModel, line) -> list:
    """``(wall, (u0, u1))`` for every member of ``line``, in the wall's own frame.

    The shape :func:`typehaus.resolve.room_walls.bounding_walls` returns, so the rest of
    this pass cannot tell the two scopes apart. The interval is the wall's whole run: a
    room shares only part of a wall's face and has to say which part, but a line's member
    *is* the run — that is what makes it a member.
    """
    from typehaus.resolve.geometry import length, sub

    out = []
    for member in line.members:
        wall = model.wall(member.wall_tag)
        if wall is None:
            continue
        out.append((wall, (0.0, length(sub(wall.axis[1], wall.axis[0])))))
    return out


def _error(el, message: str) -> Finding:
    return failed("integrity.paneling_ref", message, (el.tag,))
