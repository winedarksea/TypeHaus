"""Resolved doorway provenance and installation conflicts, without guessed products."""
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Result, advisory, failed, passed
from typehaus.resolve.doorway import DOORWAY
from typehaus.resolve.geometry import wall_frame

_ID = "integrity.doorway_assembly"


@check(Tier.INTEGRITY, _ID)
def doorway_assembly(ctx: CheckContext) -> list:
    findings = []
    materials = {m.tag for m in ctx.plan.library.materials}
    for opening in ctx.model.openings:
        if opening.kind != "door":
            continue
        before = len(findings)
        assembly = opening.doorway
        if assembly is None:
            findings.append(advisory(_ID, "doorway assembly has not been resolved",
                                     (opening.tag,), Result.UNKNOWN))
            continue
        for message in assembly.unknown:
            findings.append(advisory(_ID, message, (opening.tag,), Result.UNKNOWN))
        for message in assembly.conflicts:
            findings.append(failed(_ID, message, (opening.tag,)))
        wall = ctx.model.wall(opening.host_wall)
        floors = assembly.adjacent_floors
        if wall is not None and all(f is not None and f.surface_m is not None for f in floors):
            walking = min(f.surface_m for f in floors)
            origin, tangent, _, _ = wall_frame(wall)
            for member in wall.members:
                if (not member.child_key.startswith("plate-bottom")
                        or member.z0_m < wall.base_ref_z_m - DOORWAY.height_tolerance_m
                        or member.z1_m <= walking + DOORWAY.height_tolerance_m
                        or assembly.rough_opening_z_m > member.z1_m + DOORWAY.height_tolerance_m):
                    continue
                stations = [sum((p[i] - origin[i]) * tangent[i] for i in (0, 1))
                            for p in (member.p0, member.p1)]
                lo = max(min(stations), opening.center_along_m - opening.width_m / 2)
                hi = min(max(stations), opening.center_along_m + opening.width_m / 2)
                supported = any(c.specification.role in ("sill", "track")
                                and c.base_z_m >= member.z1_m - DOORWAY.height_tolerance_m
                                for c in assembly.components)
                if hi - lo > DOORWAY.height_tolerance_m and not supported:
                    findings.append(failed(_ID, "sole plate obstructs known doorway "
                                           "walking surface",
                                           (opening.tag, wall.tag)))
        for component in assembly.components:
            for part in component.specification.parts:
                if part.material_ref not in materials:
                    findings.append(failed(_ID, f"unknown section material {part.material_ref}",
                                           (opening.tag,)))
        if len(findings) == before:
            findings.append(passed(_ID, "resolved continuous floor or sourced doorway components",
                                   (opening.tag,)))
    return findings
