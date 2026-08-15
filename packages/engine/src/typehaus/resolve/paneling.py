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
    for storey in plan.storeys:
        for el in plan.storey_elements(storey.tag):
            if el.element_kind != "WallPaneling":
                continue
            room = rooms.get(el.room)
            if room is None:
                findings.append(_error(el, f"paneling {el.tag} names no room {el.room!r}"))
                continue
            if el.material_ref not in materials:
                findings.append(_error(
                    el, f"paneling {el.tag} names no material {el.material_ref!r}"))
                continue
            walls = bounding_walls(model, room)
            if el.walls:
                known = {wall.tag for wall, _ in walls}
                for ref in el.walls:
                    if ref not in known:
                        findings.append(_error(
                            el, f"paneling {el.tag} restricts to {ref!r}, which does not "
                                f"bound room {room.tag}"))
                walls = [(wall, span) for wall, span in walls if wall.tag in el.walls]
            spans_by_wall: dict[str, list] = {}
            for span in el.spans:
                spans_by_wall.setdefault(span.wall_ref, []).append(span)
            for ref in spans_by_wall:
                if ref not in {wall.tag for wall, _ in walls}:
                    findings.append(_error(
                        el, f"paneling {el.tag} spans wall {ref!r}, which does not bound "
                            f"room {room.tag} (or is excluded by walls=)"))
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
                mean_top = ((wall.top_z0_m or wall.z1_m)
                            + (wall.top_z1_m or wall.z1_m)) / 2.0
                wall_height = mean_top - wall.z0_m
                band_z0 = min(offset, wall_height)
                band_z1 = (wall_height if el.height is None
                           else min(offset + el.height.meters, wall_height))
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
                        uid=el.uid, tag=el.tag, storey=storey.tag, room=room.tag,
                        wall_tag=wall.tag, material_ref=el.material_ref,
                        area_m2=area, band_z0_m=band_z0, band_z1_m=band_z1,
                        run_m=hi - lo, replaces_wall_finish=el.replaces_wall_finish,
                    ))
    return findings


def _error(el, message: str) -> Finding:
    return failed("integrity.paneling_ref", message, (el.tag,))
