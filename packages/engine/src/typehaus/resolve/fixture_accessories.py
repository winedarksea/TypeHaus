"""Attach purchased hose devices after their host fixtures have physical placements."""

from typehaus.findings import Finding, element_error
from typehaus.model.enums import PipeAccessoryKind
from typehaus.model.mep import PipeAccessory
from typehaus.model.placeable_symbols import place_local
from typehaus.model.placeable_symbols._yard_hydrant import hose_outlet, vacuum_breaker_parts
from typehaus.model.placeable_symbols._yard_hydrant_config import (
    VACUUM_BREAKER_PRODUCT,
    YARD_HYDRANT_SYMBOL,
)
from typehaus.resolve.geometry_ir import GMesh
from typehaus.resolve.model import ResolvedModel, ResolvedPipeAccessory, ResolvedSolid


def resolve_fixture_accessories(model: ResolvedModel) -> list[Finding]:
    findings: list[Finding] = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if isinstance(element, PipeAccessory) and element.fixture_ref is not None:
                findings.extend(resolve_fixture_accessory(model, element, storey.tag))
    return findings


def resolve_fixture_accessory(model: ResolvedModel, accessory: PipeAccessory,
                              storey_tag: str) -> list[Finding]:
    def error(reason):
        return [element_error("integrity.pipe_accessory_attachment",
                              f"{accessory.tag}: {reason}", accessory.tag)]

    if accessory.position is not None or accessory.elevation is not None:
        return error("fixture_ref replaces authored position/elevation")
    if (accessory.kind != PipeAccessoryKind.VACUUM_BREAKER
            or accessory.product_ref != VACUUM_BREAKER_PRODUCT):
        return error(f"hose_outlet attachment requires vacuum_breaker / {VACUUM_BREAKER_PRODUCT}")
    host_pipe = next((p for p in model.pipe_runs if p.tag == accessory.pipe_ref), None)
    if host_pipe is None:
        return error(f"pipe_ref={accessory.pipe_ref!r} is not a resolved supply run")
    fixture = next((o for o in model.canvas_objects if o.tag == accessory.fixture_ref
                    and o.kind == "Fixture"), None)
    if fixture is None:
        return error(f"fixture_ref={accessory.fixture_ref!r} is not a resolved fixture")
    product = next((p for p in model.plan.library.fixture_types if p.tag == fixture.type_ref), None)
    if product is None or product.plan_symbol != YARD_HYDRANT_SYMBOL:
        return error(f"fixture {fixture.tag} has no supported hose_outlet")
    if fixture.tag not in host_pipe.serves:
        return error(f"pipe_ref={host_pipe.tag!r} does not serve fixture {fixture.tag}")
    origin, direction = hose_outlet(product.height.meters)
    (cx, cy), = place_local([origin[:2]], fixture.position, fixture.rotation_degrees)
    z = fixture.body_z0_m + origin[2]
    positions, triangles, normals = [], [], []
    for part in vacuum_breaker_parts():
        mesh = part["mesh"]
        offset = len(positions)
        xy = place_local([(x, y) for x, y, _ in mesh["positions"]], (cx, cy),
                         fixture.rotation_degrees)
        positions.extend((x, y, z + p[2]) for (x, y), p in zip(xy, mesh["positions"], strict=True))
        normal_xy = place_local([(x, y) for x, y, _ in mesh["normals"]], (0, 0),
                                fixture.rotation_degrees)
        normals.extend((x, y, n[2]) for (x, y), n in zip(normal_xy, mesh["normals"], strict=True))
        triangles.extend(tuple(i + offset for i in triangle) for triangle in mesh["triangles"])
    minimum = tuple(min(p[i] for p in positions) for i in range(3))
    maximum = tuple(max(p[i] for p in positions) for i in range(3))
    x0, y0, z0 = minimum
    x1, y1, z1 = maximum
    model.pipe_accessories.append(ResolvedPipeAccessory(
        uid=accessory.uid, tag=accessory.tag, storey=storey_tag, kind=accessory.kind.value,
        position=(cx, cy), z_m=z, pipe_ref=host_pipe.tag, system=host_pipe.system,
        diameter_m=host_pipe.diameter_m, serves=tuple(accessory.serves),
        accessible=accessory.accessible, room=accessory.room or fixture.room,
        wall_ref=accessory.wall_ref, model=accessory.model,
        install_parts=tuple(accessory.install_parts),
        fixture_ref=fixture.tag, product_ref=accessory.product_ref, direction=direction))
    model.solids.append(ResolvedSolid(
        uid=accessory.uid, tag=accessory.tag, storey=storey_tag, category=accessory.kind.value,
        outline=((x0, y0), (x1, y0), (x1, y1), (x0, y1)), z0_m=z0, z1_m=z1,
        product=accessory.product_ref, host_ref=fixture.tag,
        body_mesh=GMesh(positions=tuple(positions), triangles=tuple(triangles),
                        normals=tuple(normals), curved_vertices=frozenset(range(len(positions))))))
    return []
