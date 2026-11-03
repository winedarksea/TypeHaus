"""Minnesota UPC 707.4 sanitary cleanout locations and 707.9 access."""

from __future__ import annotations

import math

from shapely.geometry import Point, Polygon

from typehaus.checks._authoring import failed, not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cleanout_rules import (  # noqa: F401 - re-exported for the tests
    _INSIDE_WALL_REACH_M,
    _LOCATION_TOLERANCE_M,
    _TERMINAL_TOLERANCE_M,
    CleanoutRequirement,
    _distance_to_axis,
    required_cleanout_locations,
)
from typehaus.resolve.mep_queries import pipe_elevations_at

_CODE_LOCATION = "MN Plumbing Code (ch. 4714) 707.4"
_CODE_CLEARANCE = "2020 MN Plumbing Code (2018 UPC) 707.9"


def _at_sewer_connection(cleanout, building) -> bool:
    """707.4 exception 4: a two-way fitting outside at the drain's lower end, extended to
    grade, or inside the building wall near the building drain/sewer connection."""
    distance = math.dist(cleanout.position, building.path[-1])
    if cleanout.access == "grade":
        return distance <= _LOCATION_TOLERANCE_M + 1e-6
    return cleanout.access in {"floor", "wall"} and distance <= _INSIDE_WALL_REACH_M + 1e-6


@check(Tier.CODE, "mep.drain_cleanouts")
def drain_cleanouts(ctx: CheckContext):
    requirements = required_cleanout_locations(ctx.model)
    cleanouts = ctx.model.drain_cleanouts
    if not requirements and not cleanouts:
        return [not_applicable("mep.drain_cleanouts", "no sanitary horizontal drains",
                               code=_CODE_LOCATION)]
    findings = []
    building = next((r for r in ctx.model.pipe_runs if r.tag.endswith("MAIN-DRAIN")
                     and r.system == "drain" and r.sanitary), None)
    for requirement in requirements:
        # The required fitting may move a few feet down a buried branch when the fixture
        # occupies the terminal's floor footprint; its cap still has to be exposed.
        tolerance = (_TERMINAL_TOLERANCE_M if requirement.reason == "upper terminal"
                     else _LOCATION_TOLERANCE_M)
        direct = [c for c in cleanouts if c.pipe_ref == requirement.pipe_ref
                  and math.dist(c.position, requirement.point) <= tolerance + 1e-6
                  and (requirement.z_m is None
                       or abs(c.fitting_z_m - requirement.z_m) <= 6 * M_PER_IN)]
        substitute = [c for c in cleanouts if building is not None
                      and requirement.pipe_ref == building.tag
                      and requirement.reason == "upper terminal"
                      and c.pipe_ref == building.tag and c.direction == "two_way"
                      and _at_sewer_connection(c, building)]
        matched = direct or substitute
        if matched:
            findings.append(passed("mep.drain_cleanouts",
                                   f"{requirement.pipe_ref} {requirement.reason}: "
                                   f"{matched[0].tag}",
                                   (requirement.pipe_ref, matched[0].tag),
                                   code=_CODE_LOCATION))
        else:
            findings.append(failed("mep.drain_cleanouts",
                                   f"{requirement.pipe_ref} missing {requirement.reason} "
                                   f"cleanout at {requirement.point}",
                                   (requirement.pipe_ref,), code=_CODE_LOCATION))
    for cleanout in cleanouts:
        host = next((r for r in ctx.model.pipe_runs if r.tag == cleanout.pipe_ref), None)
        if (host is None or host.system != "drain" or not host.sanitary
            or not any(abs(z - cleanout.fitting_z_m) <= host.diameter_m / 2
                       for z in pipe_elevations_at(host, cleanout.position))):
            findings.append(failed("mep.drain_cleanouts",
                                   f"{cleanout.tag} fitting is not connected to its sanitary "
                                   f"host {cleanout.pipe_ref}", (cleanout.tag,),
                                   code=_CODE_LOCATION))
        if hasattr(ctx.model, "solids"):
            parts = {s.category for s in ctx.model.solids if s.tag == cleanout.tag
                     or s.tag in {cleanout.tag + "-EXT", cleanout.tag + "-CAP"}}
            if parts != {"cleanout_fitting", "cleanout_extension", "cleanout_cap"}:
                findings.append(failed("mep.drain_cleanouts",
                                       f"{cleanout.tag} lacks fitting, extension, or cap geometry",
                                       (cleanout.tag,), code=_CODE_LOCATION))
        if cleanout.access == "grade":
            site_grade = ctx.model.plan.project.site.grade
            if (site_grade is None
                or abs(cleanout.cap_z_m - site_grade.meters) > M_PER_IN):
                findings.append(failed("mep.drain_cleanouts",
                                       f"{cleanout.tag} cap does not terminate at grade",
                                       (cleanout.tag,), code=_CODE_LOCATION))
        elif cleanout.access == "floor":
            floor = next((s for s in ctx.model.plan.storeys
                          if getattr(s, "tag", cleanout.storey) == cleanout.storey), None)
            if floor is not None and abs(cleanout.cap_z_m - floor.elevation.meters) > M_PER_IN:
                findings.append(failed("mep.drain_cleanouts",
                                       f"{cleanout.tag} cap is not flush with its floor",
                                       (cleanout.tag,), code=_CODE_LOCATION))
            for item in getattr(ctx.model, "canvas_objects", ()):
                if (item.storey != cleanout.storey
                    or item.domain not in {"plumbing", "appliance", "furniture"}
                    or not item.footprint or item.body_z1_m < cleanout.cap_z_m):
                    continue
                if Polygon(item.footprint).covers(Point(cleanout.cap_position)):
                    findings.append(failed("mep.drain_cleanouts",
                                           f"{cleanout.tag} floor cap is hidden by {item.tag}",
                                           (cleanout.tag, item.tag), code=_CODE_LOCATION))
        elif cleanout.access == "wall":
            wall = next((w for w in getattr(ctx.model, "walls", ())
                         if w.tag == cleanout.wall_ref), None)
            if (wall is None
                or _distance_to_axis(cleanout.cap_position, wall.axis) > 6 * M_PER_IN
                or not wall.z0_m - M_PER_IN <= cleanout.cap_z_m <= wall.z1_m + M_PER_IN):
                findings.append(failed("mep.drain_cleanouts",
                                       f"{cleanout.tag} wall cap does not reach its "
                                       f"accessible host {cleanout.wall_ref}",
                                       (cleanout.tag,), code=_CODE_LOCATION))
        required_in = 18 if cleanout.diameter_m <= 2 * M_PER_IN else 24
        if not cleanout.accessible:
            findings.append(failed("mep.drain_cleanouts", f"{cleanout.tag} cap is inaccessible",
                                   (cleanout.tag,), code=_CODE_CLEARANCE))
        elif (cleanout.clear_width_m < required_in * M_PER_IN
              or cleanout.clear_depth_m < required_in * M_PER_IN):
            findings.append(failed("mep.drain_cleanouts",
                                   f"{cleanout.tag} needs {required_in} in by {required_in} in "
                                   "clear at its cap", (cleanout.tag,), code=_CODE_CLEARANCE))
        else:
            findings.append(passed("mep.drain_cleanouts",
                                   f"{cleanout.tag} accessible cap has {required_in} in clearance",
                                   (cleanout.tag,), code=_CODE_CLEARANCE))
    return findings
