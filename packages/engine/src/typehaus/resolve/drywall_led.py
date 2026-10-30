"""Plaster-in LED wall-washers: which runs are set into the board, and the slot they cut.

A run is plaster-in when the house's ``DrywallStandard`` names a ``led_profile`` and the run
sits in a gypsum board overhead: its soffit's underside (``soffit_ref``), or a flat room
ceiling whose board holds the run's height. Derived from the host face, never authored
(decision #103). Each leg must wash a face on its ``emission_side`` within the profile's
offset range, else ``integrity.light_run_host``.

A ceiling host loses the slot from its ``ceiling`` solid (split into simple pieces, the
first keeping its uid). A soffit's slot is cut with its board in ``resolve/soffits.py``.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from shapely.geometry import LineString, Polygon

from typehaus.findings import Finding, element_error
from typehaus.model.drywall import DrywallStandard, PlasterInProfile
from typehaus.resolve.ceiling_over import split_holes
from typehaus.resolve.geometry import length, normal, sub, unit
from typehaus.resolve.interior_trim_scope import face_is_gypsum
from typehaus.resolve.model import ResolvedLightRun, ResolvedModel, ResolvedSolid
from typehaus.resolve.soffits import SOFFIT_LINING_THICKNESS
from typehaus.resolve.trim_bands import plaster_in_washer_parts

_CID = "integrity.light_run_host"
# A run "in" a board: its height within the board, to this.
_BOARD_TOL_M = 0.0016
# A face is parallel to a leg within this sine, and reaches it if it overlaps this much.
_PARALLEL = 1e-3
_MIN_OVERLAP = 0.5
# How far below the ceiling the washed face's material is probed.
_WASH_PROBE_M = (0.05, 0.3)
_IN = 0.0254


def host_plaster_in_runs(model: ResolvedModel, standard: DrywallStandard | None) -> list[Finding]:
    """Make each gypsum-hosted run ``plaster_in`` and cut its slot from a ceiling host."""
    profile = standard.led_profile if standard is not None else None
    if profile is None:
        return []
    materials = {m.tag: m for m in model.plan.library.materials}
    parts = plaster_in_washer_parts(profile.aperture.meters, profile.depth.meters,
                                    profile.flange.meters, profile.tilt.radians)
    findings: list[Finding] = []
    for index, run in enumerate(model.light_runs):
        if run.z_path_m and len(set(run.z_path_m)) > 1:
            continue  # a raked run is never set into a flat board
        host = _host(model, run, materials)
        if host is None:
            continue
        host_ref, face_z, candidates = host
        error = _washed_faces(model, run, profile, candidates, face_z, materials)
        if error is not None:
            findings.append(error)
            continue
        model.light_runs[index] = dataclasses.replace(
            run, z_m=face_z, z_path_m=(), profile="plaster_in", section=parts,
            host_ref=host_ref, aperture_m=profile.aperture.meters)
        if run.soffit_ref is None:
            _cut_ceiling(model, host_ref, run.path, profile.aperture.meters / 2.0, face_z)
    return findings


def _host(model: ResolvedModel, run: ResolvedLightRun, materials: dict):
    """``(host ref, board face z, wash candidates)`` or None for a surface run.

    Candidates are ``(segment, wall or None)``: the room's clear-face edges with their wall,
    and a soffit host's own outline edges (its bulkhead, which the light spills past).
    """
    path_line = LineString(run.path)
    room = next((r for r in model.rooms if r.tag == run.room), None)
    if run.soffit_ref is not None:
        soffit = next((s for s in model.soffits if s.tag == run.soffit_ref), None)
        if soffit is None or not _in_board(run.z_m, soffit.z0_m, SOFFIT_LINING_THICKNESS.meters):
            return None
        ring = list(soffit.outline)
        edges = [((ring[i], ring[(i + 1) % len(ring)]), None) for i in range(len(ring))]
        return soffit.tag, soffit.z0_m, edges + _room_edges(model, room)
    for ceiling in model.ceilings:
        if (ceiling.z0_m is None or ceiling.z1_m is None or ceiling.storey != run.storey
                or len(ceiling.outline) < 3
                or not _in_board(run.z_m, ceiling.z0_m, ceiling.z1_m - ceiling.z0_m)
                or not Polygon(ceiling.outline).buffer(1e-6).covers(path_line)):
            continue
        board = next((layer for layer in ceiling.layers
                      if not getattr(materials.get(layer.material_ref), "coating", False)), None)
        if board is None or getattr(materials.get(board.material_ref), "gypsum_type",
                                    None) is None:
            return None
        owner = next((r for r in model.rooms if r.tag == ceiling.room_ref), room)
        return ceiling.uid, ceiling.z0_m, _room_edges(model, owner)
    return None


def _in_board(z: float, face: float, thickness: float) -> bool:
    return face - _BOARD_TOL_M <= z <= face + thickness + _BOARD_TOL_M


def _room_edges(model: ResolvedModel, room) -> list:
    """The room's clear-face edges, each with the wall whose body it lies on (or None)."""
    from typehaus.resolve.room_walls import _TOUCH_M
    from typehaus.resolve.wall_faces import wall_body

    if room is None or len(room.clear_face) < 3:
        return []
    ring = list(room.clear_face)
    walls = [w for w in model.walls if w.storey == room.storey and w.layers]
    out = []
    for i in range(len(ring)):
        segment = (ring[i], ring[(i + 1) % len(ring)])
        line = LineString(segment)
        if line.length < 1e-6:
            continue
        mid = line.interpolate(0.5, normalized=True)
        wall = next((w for w in walls
                     if wall_body(w, w.z0_m, w.z1_m).distance(mid) <= _TOUCH_M), None)
        out.append((segment, wall))
    return out


def _washed_faces(model: ResolvedModel, run: ResolvedLightRun, profile: PlasterInProfile,
                  candidates: list, face_z: float, materials: dict) -> Finding | None:
    """None when every leg has a face to wash within range; else the finding naming the fix."""
    lo, hi = profile.wall_offset_min.meters, profile.wall_offset_max.meters
    sign = 1.0 if run.emission_side == "left" else -1.0
    for p0, p1 in zip(run.path, run.path[1:], strict=False):
        leg = sub(p1, p0)
        if length(leg) < 1e-6:
            continue
        d = unit(leg)
        n = normal(d)
        toward = (n[0] * sign, n[1] * sign)
        best = None
        for (a, b), wall in candidates:
            e = sub(b, a)
            if length(e) < 1e-6 or abs(d[0] * e[1] - d[1] * e[0]) / length(e) > _PARALLEL:
                continue
            offset = (a[0] - p0[0]) * toward[0] + (a[1] - p0[1]) * toward[1]
            if offset <= 1e-6:
                continue
            ta = (a[0] - p0[0]) * d[0] + (a[1] - p0[1]) * d[1]
            tb = (b[0] - p0[0]) * d[0] + (b[1] - p0[1]) * d[1]
            overlap = min(max(ta, tb), length(leg)) - max(min(ta, tb), 0.0)
            if overlap < _MIN_OVERLAP * min(length(leg), length(e)):
                continue
            if best is None or offset < best[0]:
                best = (offset, a, b, wall)
        if best is not None and best[3] is not None:
            offset, a, b, wall = best
            mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
            z0, z1 = face_z - _WASH_PROBE_M[1], face_z - _WASH_PROBE_M[0]
            if not face_is_gypsum(wall, mid, toward, z0, z1, materials):
                best = None
        if best is None:
            return element_error(_CID, (
                f"plaster-in run {run.tag} has no gypsum face to wash on its "
                f"{run.emission_side} side: set emission_side toward the washed wall"),
                run.tag)
        if not lo - 1e-6 <= best[0] <= hi + 1e-6:
            what = best[3].tag if best[3] is not None else "its soffit's edge"
            return element_error(_CID, (
                f"plaster-in run {run.tag} sits {best[0] / _IN:.2f}\" from {what}, outside "
                f"its profile's {lo / _IN:g}-{hi / _IN:g}\" slot-to-wall range: move the run"),
                run.tag)
    return None


def _cut_ceiling(model: ResolvedModel, host_uid: str, path, half_width: float,
                 face_z: float) -> None:
    """Take the slot out of every ``ceiling`` solid piece of ``host_uid`` it crosses."""
    slot = LineString(path).buffer(half_width, cap_style=2, join_style=2)
    taken = {solid.uid for solid in model.solids}
    out: list[ResolvedSolid] = []
    for solid in model.solids:
        if (solid.category != "ceiling" or not solid.uid.startswith(host_uid)
                or abs(solid.z0_m - face_z) > _BOARD_TOL_M
                or not Polygon(solid.outline).intersects(slot)):
            out.append(solid)
            continue
        cut = Polygon(solid.outline).difference(slot)
        pieces = [simple for part in getattr(cut, "geoms", (cut,)) if not part.is_empty
                  for simple in split_holes(part)]
        pieces.sort(key=lambda part: part.area, reverse=True)
        for number, piece in enumerate(pieces):
            uid, tag = solid.uid, solid.tag
            if number:
                k = 1
                while f"{solid.uid}-slot{k}" in taken:
                    k += 1
                uid, tag = f"{solid.uid}-slot{k}", f"{solid.tag}-SLOT{k}"
                taken.add(uid)
            ring = tuple((float(x), float(y)) for x, y in piece.exterior.coords[:-1])
            out.append(dataclasses.replace(solid, uid=uid, tag=tag, outline=ring))
    model.solids[:] = out


def drywall_standard(plan: Any) -> tuple[DrywallStandard | None, list[Finding]]:
    """The house's one ``DrywallStandard`` (or None), with ``integrity.drywall_standard``."""
    found = [el for el in plan.all_elements() if isinstance(el, DrywallStandard)]
    if not found:
        return None, []
    if len(found) > 1:
        tags = ", ".join(sorted(el.tag for el in found))
        return None, [element_error("integrity.drywall_standard",
                                    f"a house declares at most one DrywallStandard; found "
                                    f"{len(found)}: {tags}", found[0].tag)]
    standard = found[0]
    materials = {m.tag for m in plan.library.materials}
    missing = [ref for ref in standard.material_refs() if ref not in materials]
    if missing:
        return None, [element_error("integrity.drywall_standard",
                                    f"drywall standard {standard.tag} names no material "
                                    f"{missing[0]!r}", standard.tag)]
    profile = standard.led_profile
    if profile is not None:
        bed = profile.aperture.meters / 2.0 + profile.flange.meters
        if profile.wall_offset_min.meters < bed - 1e-6:
            return None, [element_error("integrity.drywall_standard", (
                f"drywall standard {standard.tag}'s LED profile puts its wall-side flange "
                f"past the wall below {bed / _IN:.2f}\": raise wall_offset_min"),
                standard.tag)]
    return standard, []
