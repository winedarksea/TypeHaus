"""Grade geometric alignment independently of the manufacturer's port certainty."""

from math import cos, dist, hypot, radians, sin

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import Tier, check
from typehaus.model.placeable_symbols import place_local
from typehaus.model.placeable_symbols._shower_hardware import shower_hardware_parts
from typehaus.resolve.ceilings import ceiling_faces, finished_ceiling_at
from typehaus.resolve.mep_sleeves import placed_port_point

CHECK_ID = "mep.shower_assembly_alignment"
AXIS_COSINE_TOLERANCE = 0.999


def endpoint_meets_hub(endpoint, neighbor, hub, direction, tolerance):
    """Neighbor lies outboard on the outward hub axis, for either path orientation."""
    delta = tuple(a - b for a, b in zip(neighbor, endpoint, strict=True))
    length = hypot(*delta)
    return (dist(endpoint, hub) <= tolerance and length > tolerance
            and sum(a * b for a, b in zip(delta, direction, strict=True)) / length
            >= AXIS_COSINE_TOLERANCE)


@check(Tier.INTEGRITY, CHECK_ID)
def shower_assembly_alignment(ctx):
    types = {entry.tag: entry for entry in ctx.plan.library.fixture_types}
    fixtures = {item.tag: item for item in ctx.model.canvas_objects if item.kind == "Fixture"}
    storeys = {item.tag: storey for storey in ctx.plan.storeys
               for item in ctx.plan.storey_elements(storey.tag)}
    faces = ceiling_faces(ctx.model)
    tolerance = ctx.preferences.plumbing.fixture_port_exact_tolerance_in * 0.0254
    findings = []
    for authored in ctx.plan.elements_of_kind("Fixture"):
        product = types.get(authored.type_ref)
        spec = product.shower_assembly if product else None
        fixture = fixtures.get(authored.tag)
        if spec is None or fixture is None:
            continue
        angle = radians(fixture.rotation_degrees)
        for port in spec.inlet_ports():
            local_point = placed_port_point(ctx.model, fixture.tag, port)
            hub = (*local_point[:2], local_point[2] + storeys[fixture.tag].elevation.meters)
            dx, dy, dz = port.direction
            direction = (dx * cos(angle) - dy * sin(angle),
                         dx * sin(angle) + dy * cos(angle), dz)
            arrivals = [(run.tag, (*run.path[i], run.z_m[i]), (*run.path[j], run.z_m[j]))
                        for run in ctx.model.pipe_runs if fixture.tag in run.serves
                        and run.system == port.service.value and len(run.path) == len(run.z_m)
                        and len(run.path) >= 2
                        for i, j in ((0, 1), (-1, -2))]
            aligned = next((tag for tag, end, neighbor in arrivals
                            if endpoint_meets_hub(end, neighbor, hub, direction, tolerance)), None)
            result = passed if aligned else failed
            alignment = "aligned by " + aligned if aligned else "endpoint/axis mismatch"
            findings.append(result(CHECK_ID,
                f"{fixture.tag} {port.tag}: {alignment}; "
                f"manufacturer station remains {port.certainty.value}", (fixture.tag, port.tag)))
            declared = next((p for p in product.ports if p.tag == port.tag), None)
            if declared != port:
                findings.append(failed(CHECK_ID, "fixture port differs from shower assembly",
                                       (fixture.tag, port.tag)))
        # Sample every corner of the complete head/arm envelope, rather than its centre only.
        clearances = []
        for part in shower_hardware_parts(spec):
            if not part.get("role", "").startswith("shower:head") or "riser" in part["role"]:
                continue
            (x, y, z), (w, d, h) = part["center"], part["size"]
            for xy in place_local([(x + sx * w / 2, y + sy * d / 2)
                                   for sx in (-1, 1) for sy in (-1, 1)],
                                  fixture.position, fixture.rotation_degrees):
                ceiling = finished_ceiling_at(faces, fixture.storey, authored.room, xy)
                if ceiling is None:
                    from typehaus.resolve.roof_geometry import (
                        roof_height_at,
                        roof_underside_depth_m,
                    )

                    room = ctx.plan.by_tag(authored.room)
                    roof_ref = getattr(getattr(room, "ceiling", None), "roof_ref", None)
                    roof = next((r for r in ctx.model.roofs if r.tag == roof_ref), None)
                    depth = (roof_underside_depth_m(ctx.model, roof, authored.room)
                             if roof else None)
                    if depth is not None:
                        ceiling = roof_height_at(roof, xy) - depth
                if ceiling is not None:
                    clearances.append(ceiling - (fixture.z_m + z + h / 2))
        if clearances:
            result = passed if min(clearances) >= -tolerance else failed
            findings.append(result(CHECK_ID, f"head/arm ceiling clearance {min(clearances):.4f} m",
                                   (fixture.tag,)))
        else:
            findings.append(unknown(CHECK_ID, "head/arm ceiling envelope is unresolved",
                                    (fixture.tag,)))
    return findings or [not_applicable(CHECK_ID, "no shower assemblies", ())]
