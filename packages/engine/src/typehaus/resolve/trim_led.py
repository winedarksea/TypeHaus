"""Exterior LED runs hosted on the corrugated Sill to Soffit's flange (decision #143).

A surface, aperture-down run on no soffit host whose legs lie along a Sill to Soffit edge
(``exposed_wall_top_edges``, the inventory the trim is swept from) moves onto the flange's
underside: its inside edge on the cladding face, ``z`` on the flange at every vertex (raked
up a rake), ends within ``EDGE_SNAP_M`` of the edge's ends clamped to them. ``host_ref``
names the trim. No run, no hosting: the trim is the same either way.
"""

from __future__ import annotations

import dataclasses
import math

from typehaus.findings import Finding, Result, Severity
from typehaus.library.trim.metal_sales import PROFILES
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.wall_tops import exposed_wall_top_edges, wall_top_tag
from typehaus.resolve.led_sections import modules_for, section_extent
from typehaus.resolve.mep import EDGE_SNAP_M, GENERIC_WIDTH_M
from typehaus.resolve.model import ResolvedModel

_CID = "integrity.light_run_host"
_RECEIVER = "CORRUGATED_SILL_TO_SOFFIT"
# A leg is on an edge within this, in plan off the cladding face and in z off the flange.
_REACH_M = 6 * M_PER_IN
_PARALLEL = 1e-3
_MIN_OVERLAP = 0.5


def _flange_clear_m(edge) -> float:
    """The flange's underside from the cladding face to its outboard end (its y=0 leg)."""
    profile = PROFILES[_RECEIVER]
    reach = profile.receiver_throat_in - min(x for x, y in profile.section_in if y == 0)
    return reach * M_PER_IN - edge.face.layer.thickness_m


def _outside(edge) -> float:
    return edge.face.back + edge.face.layer.thickness_m


def _station(edge, point) -> float:
    return point[0] * edge.face.d[0] + point[1] * edge.face.d[1]


def _z_at(edge, station: float) -> float:
    span = edge.end - edge.start
    return edge.z_start + (edge.z_end - edge.z_start) * (station - edge.start) / span


def _leg_edge(a, b, za, zb, edges):
    """The receiver edge a leg runs along, nearest in plan, or None."""
    leg = math.dist(a, b)
    if leg < 1e-9:
        return None
    ux, uy = (b[0] - a[0]) / leg, (b[1] - a[1]) / leg
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    best = None
    for edge in edges:
        d, n = edge.face.d, edge.face.n
        if abs(ux * d[1] - uy * d[0]) > _PARALLEL:
            continue
        off = abs(mid[0] * n[0] + mid[1] * n[1] - _outside(edge))
        lo, hi = sorted((_station(edge, a), _station(edge, b)))
        overlap = min(hi, edge.end) - max(lo, edge.start)
        middle = (lo + hi) / 2
        if (off > _REACH_M or overlap < _MIN_OVERLAP * leg
                or abs((za + zb) / 2 - _z_at(edge, middle)) > _REACH_M):
            continue
        if best is None or off < best[0]:
            best = (off, edge)
    return None if best is None else best[1]


def _line_point(edge, station: float, centre: float):
    d, n = edge.face.d, edge.face.n
    return (d[0] * station + n[0] * centre, d[1] * station + n[1] * centre)


def _corner(e0, c0, e1, c1, point):
    """Where two hosted lines meet; the projection onto the first where they are parallel."""
    n0, n1 = e0.face.n, e1.face.n
    det = n0[0] * n1[1] - n0[1] * n1[0]
    if abs(det) < 1e-9:
        return _line_point(e0, _station(e0, point), c0)
    return ((c0 * n1[1] - c1 * n0[1]) / det, (n0[0] * c1 - n1[0] * c0) / det)


def host_trim_runs(model: ResolvedModel) -> list[Finding]:
    """Put each exterior surface run along a Sill to Soffit edge on its flange."""
    runs = [i for i, r in enumerate(model.light_runs)
            if r.profile == "surface" and r.soffit_ref is None and r.aperture == "down"]
    if not runs:
        return []
    edges = [e for e in exposed_wall_top_edges(model) if e.product == _RECEIVER]
    types = {t.tag: t for t in model.plan.library.electrical_device_types}
    findings: list[Finding] = []
    for index in runs:
        run = model.light_runs[index]
        path = list(run.path)
        zs = list(run.z_path_m) or [run.z_m] * len(path)
        legs = [_leg_edge(path[k], path[k + 1], zs[k], zs[k + 1], edges)
                for k in range(len(path) - 1)]
        if not all(legs):
            if run.room is None and _ceiling_mount(model, run):
                missing = "finds no soffit receiver" if not any(legs) else (
                    f"leaves the soffit receiver on leg {legs.index(None) + 1}")
                findings.append(_finding(
                    run, Severity.WARN, Result.UNKNOWN,
                    f"exterior ceiling-mount run {run.tag} {missing} within "
                    f"{_REACH_M / M_PER_IN:.0f}\", so nothing hosts or grades it",
                    "set the run under a soffit edge, or give it a soffit_ref"))
            continue
        width = section_extent(run.section)[0] if run.section else GENERIC_WIDTH_M
        centres = [_outside(e) + width / 2 for e in legs]
        new_path, new_z = [], []
        for k, point in enumerate(path):
            before, after = (k - 1 if k else None), (k if k < len(legs) else None)
            edge = legs[after if after is not None else before]
            centre = centres[after if after is not None else before]
            station = _station(edge, point)
            if before is None or after is None:  # a run end clamps to its edge's end
                near = [s for s in (edge.start, edge.end) if abs(s - station) <= EDGE_SNAP_M]
                station = min(near, key=lambda s: abs(s - station)) if near else station
                xy = _line_point(edge, station, centre)
            else:
                xy = _corner(legs[before], centres[before], edge, centre, point)
                station = _station(edge, xy)
            new_path.append(xy)
            new_z.append(_z_at(edge, station))
        past = [e for k, e in enumerate(legs)
                if max(_overrun(e, new_path[k]), _overrun(e, new_path[k + 1])) > EDGE_SNAP_M]
        if past:
            findings.append(_finding(
                run, Severity.ERROR, Result.FAIL,
                f"run {run.tag} runs past the end of {wall_top_tag(past[0])} by more than "
                f"{EDGE_SNAP_M / M_PER_IN:.0f}\", off the flange it is hosted on",
                "stop the run at the soffit edge's end"))
        clear = min(_flange_clear_m(e) for e in legs)
        if width > clear + 1e-9:
            findings.append(_finding(
                run, Severity.ERROR, Result.FAIL,
                f"run {run.tag}'s {width / M_PER_IN:.2f}\" channel is wider than the "
                f"{clear / M_PER_IN:.2f}\" of Sill to Soffit flange clear of the cladding",
                "pick a narrower channel"))
        developed = sum(math.hypot(math.dist(new_path[k], new_path[k + 1]),
                                   new_z[k + 1] - new_z[k]) for k in range(len(new_path) - 1))
        level = max(new_z) - min(new_z) < 1e-9
        # ``z_m`` stays the mount the vertex heights rise from, as ``resolve/mep.py`` sets it.
        model.light_runs[index] = dataclasses.replace(
            run, path=new_path, z_m=run.z_m + new_z[0] - zs[0],
            z_path_m=() if level else tuple(new_z),
            length_m=developed, host_ref=wall_top_tag(legs[0]),
            **modules_for(types.get(run.type_ref), developed))
    return findings


def _overrun(edge, point) -> float:
    station = _station(edge, point)
    return max(edge.start - station, station - edge.end, 0.0)


def _ceiling_mount(model: ResolvedModel, run) -> bool:
    mount = getattr(model.plan.by_tag(run.tag), "mount", None)
    return mount is not None and mount.kind.value == "ceiling"


def _finding(run, severity, result, message, hint) -> Finding:
    return Finding(severity=severity, check_id=_CID, result=result,
                   element_tags=(run.tag,), message=message, fix_hint=hint)
