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
                    model.panelings.append(ResolvedPaneling(
                        uid=el.uid, tag=el.tag, storey=wall.storey,
                        room=room.tag if room is not None else None,
                        wall_tag=wall.tag, material_ref=el.material_ref,
                        area_m2=area, band_z0_m=band_z0, band_z1_m=band_z1,
                        run_m=hi - lo, replaces_wall_finish=el.replaces_wall_finish,
                        layout_line=line.tag if line is not None else None,
                    ))
    return findings


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
