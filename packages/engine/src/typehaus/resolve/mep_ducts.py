"""Resolving a duct run: its section, its elevations, its solid, its developed length.

Split out of :mod:`typehaus.resolve.mep` when ``DuctRun`` gained the pipe stack, for the
reason AGENTS.md gives — that module was already at its page budget, and this is the same
seam ``mep_slope`` and ``mep_sleeves`` were cut along.

**What changed and why it mattered.** A ``DuctRun`` had no elevation field at all, so a
four-storey ERV existed only as plan polylines that teleported between floors: no vertical
leg was drawn anywhere, ducts emitted no 3D solids, and the take-off billed plan length —
a riser measured as the zero length it projects to. The one z anybody derived lived inside
the IFC emitter, which is why no other consumer could draw a duct.

Everything here is the pipe machinery, reused rather than re-written: the same elevation
solver (``mep_slope``, now with the check-id prefix as a parameter), the same mitred sweep
kernel (``sweep.py`` — whose ``rect_profile`` had been sitting unused since it was written),
the same one-swept-solid-per-run emitter. A vertical riser needs no new concept: it is a
repeated plan point at two elevations, exactly as a drain drop is.
"""

from __future__ import annotations

import math

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import DuctRouting
from typehaus.model.mep import DuctRun
from typehaus.quantities import inch
from typehaus.resolve.framing.soffit import soffit_clear_section
from typehaus.resolve.geometry import bbox, length, sub
from typehaus.resolve.mep_queries import duct_bay_occupancy
from typehaus.resolve.mep_slope import _pipe_vertex_z
from typehaus.resolve.model import ResolvedDuct, ResolvedModel
from typehaus.resolve.round_solids import PIPE_FACETS
from typehaus.resolve.sweep import rect_profile, round_profile

_DEFAULT_SPACING_M = inch(16).meters


def _duct_section(duct: DuctRun) -> tuple[tuple[float, float, float | None] | None,
                                          list[Finding]]:
    """``(width_m, depth_m, diameter_m | None)`` for the run, or a finding saying why not.

    A round duct reports its diameter as *both* plan dimensions. Every consumer that
    measures a duct against something — a joist bay, a soffit cavity, a sheet-metal
    schedule — is asking how much room it takes up, and a 6" round takes 6" either way; the
    diameter rides alongside for the two consumers that need to know it is round (the sweep
    profile and the take-off key, because 6" spiral and 6x6 rectangular are two orders).
    """
    has_rect = duct.width is not None and duct.depth is not None
    if duct.diameter is not None and (duct.width is not None or duct.depth is not None):
        return None, [Finding(
            severity=Severity.ERROR, check_id="integrity.duct_run_section",
            message=(f"duct run {duct.tag} states both a diameter and a rectangular "
                     "section — a duct is round or it is rectangular, not both"),
            element_tags=(duct.tag,), result=Result.FAIL)]
    if duct.diameter is not None:
        d = duct.diameter.meters
        return (d, d, d), []
    if has_rect:
        assert duct.width is not None and duct.depth is not None  # narrowed by has_rect
        return (duct.width.meters, duct.depth.meters, None), []
    return None, [Finding(
        severity=Severity.ERROR, check_id="integrity.duct_run_section",
        message=(f"duct run {duct.tag} states no section — give it a diameter (round) or "
                 "a width and depth (rectangular)"),
        element_tags=(duct.tag,), result=Result.FAIL)]


def _derived_base_z(model: ResolvedModel, duct: DuctRun, storey, floor) -> float:
    """The underside a run with no authored elevation sits on.

    Three cavities, in the order a reader would look: the soffit it names, the joist bay it
    names, then the storey datum. The last is the fallback the IFC emitter has always used
    and is kept exactly so every duct authored before elevations existed resolves where it
    already resolved — the difference is that now *every* consumer sees that z, not only
    the IFC file.
    """
    if duct.soffit_ref:
        soffit = next((s for s in model.soffits if s.tag == duct.soffit_ref), None)
        if soffit is not None:
            section = soffit_clear_section(soffit)
            if section is not None:
                return section.z[0]
            return soffit.z0_m
    if duct.routing is DuctRouting.JOIST_BAY and floor is not None and floor.members:
        return floor.members[0].z0_m
    return storey.elevation.meters


def _duct_vertex_z(model: ResolvedModel, duct: DuctRun, path: list[tuple[float, float]],
                   storey, floor, depth_m: float) -> tuple[list[float], list[Finding]]:
    """Absolute centreline z per path vertex — authored where authored, derived otherwise."""
    authored = (duct.elevations is not None or duct.start_elevation is not None
                or duct.end_elevation is not None)
    if authored:
        z, findings = _pipe_vertex_z(duct, path, storey.elevation.meters, prefix="duct")
        if z is not None:
            return z, findings
        return [], findings
    base = _derived_base_z(model, duct, storey, floor)
    return [base + depth_m / 2.0] * len(path), []


def _containing_floor(model: ResolvedModel, storey_tag: str, direction: str,
                      point: tuple[float, float], fallback):
    """Whichever FloorSystem on this storey shares ``direction`` and contains ``point``.

    Siblings from the same x-spanning deck split share a joist ``direction``; a duct that
    crosses the split boundary needs the floor under each segment, not the one named by
    ``floor_ref`` alone. Falls back to ``fallback`` (the named ``floor_ref``'s floor) when
    no sibling's deck outline contains the point — e.g. a duct that briefly runs outside
    any deck footprint."""
    for f in model.floors:
        if f.storey != storey_tag or f.direction != direction or not f.deck_outline:
            continue
        (x0, y0), (x1, y1) = bbox(list(f.deck_outline))
        if x0 - 1e-6 <= point[0] <= x1 + 1e-6 and y0 - 1e-6 <= point[1] <= y1 + 1e-6:
            return f
    return fallback


def _bay_occupancy(model: ResolvedModel, duct: DuctRun, storey_tag: str,
                   path: list[tuple[float, float]], floor, width_m: float, depth_m: float
                   ) -> tuple[tuple[str, ...], tuple[tuple[float, float], ...], bool]:
    conflicts: list[str] = []
    crossings: list[tuple[float, float]] = []
    depth_ok = True
    if floor is None:
        return (), (), True
    # Each segment validates against whichever sibling FloorSystem (same storey, same joist
    # direction) contains its midpoint, so a duct spanning a split deck resolves against
    # both halves instead of reporting UNKNOWN past the named floor_ref's edge.
    for a, b in zip(path, path[1:], strict=False):
        midpoint = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        seg_floor = _containing_floor(model, storey_tag, floor.direction, midpoint, floor)
        system = model.plan.by_tag(seg_floor.tag)
        bearing_walls = [model.wall(tag)
                         for tag in getattr(system.joists, "bearing_refs", ())]
        bearing_walls = [w for w in bearing_walls if w is not None]
        spacing_m = (system.joists.spacing.meters if system.joists.spacing is not None
                     else _DEFAULT_SPACING_M)
        seg_conflicts, seg_crossings, seg_depth_ok = duct_bay_occupancy(
            [a, b], width_m, depth_m, duct.routing, seg_floor, bearing_walls, spacing_m,
        )
        conflicts.extend(seg_conflicts)
        crossings.extend(seg_crossings)
        depth_ok = depth_ok and seg_depth_ok
    return tuple(conflicts), tuple(crossings), depth_ok


def resolve_duct_run(model: ResolvedModel, duct: DuctRun, storey,
                     emit_solids) -> list[Finding]:
    """Validate one run, give it elevations and a swept solid, and record it.

    ``emit_solids`` is ``resolve.mep._emit_run_solids`` passed in rather than imported:
    ``mep.py`` is the module every call site already imports and it owns that emitter, so
    taking it as an argument keeps the dependency running one way (mep -> mep_ducts) and
    the import cycle unwritten.
    """
    path = [p.xy_m for p in duct.path]
    if len(path) < 2:
        return [Finding(
            severity=Severity.ERROR, check_id="integrity.duct_run_path",
            message=f"duct run {duct.tag} needs >= 2 path points", element_tags=(duct.tag,),
            result=Result.FAIL,
        )]
    section, findings = _duct_section(duct)
    if section is None:
        return findings
    width_m, depth_m, diameter_m = section
    floor = (next((f for f in model.floors if f.tag == duct.floor_ref), None)
             if duct.floor_ref else None)
    conflicts, crossings, depth_ok = _bay_occupancy(
        model, duct, storey.tag, path, floor, width_m, depth_m)
    z, z_findings = _duct_vertex_z(model, duct, path, storey, floor, depth_m)
    findings.extend(z_findings)
    if not z:
        return findings
    developed = sum(
        math.hypot(length(sub(path[i], path[i + 1])), z[i + 1] - z[i])
        for i in range(len(path) - 1))
    profile = (round_profile(diameter_m / 2.0, PIPE_FACETS) if diameter_m is not None
               else rect_profile(width_m, depth_m))
    emit_solids(model, duct.uid or duct.tag, duct.tag, storey.tag, path, z, profile,
                f"duct_{duct.system.value}")
    model.ducts.append(ResolvedDuct(
        uid=duct.uid, tag=duct.tag, storey=storey.tag, system=duct.system.value,
        path=path, width_m=width_m, depth_m=depth_m, routing=duct.routing.value,
        floor_ref=duct.floor_ref, crossings=crossings, conflicts=conflicts,
        depth_ok=depth_ok, design_cfm=duct.design_cfm, diameter_m=diameter_m,
        z_m=tuple(z), length_m=developed, material=duct.material,
        insulation=duct.insulation, soffit_ref=duct.soffit_ref,
    ))
    return findings
