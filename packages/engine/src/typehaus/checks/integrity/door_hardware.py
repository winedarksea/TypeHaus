"""Authored hardware references, leaf limits and local jamb specifications."""
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.door_hardware import HARDWARE_BLOCKING_ANCHOR_ROLES


@check(Tier.INTEGRITY, "integrity.door_hardware")
def door_hardware(ctx: CheckContext) -> list[Finding]:
    products = {item.tag for item in ctx.plan.library.products}
    materials = {item.tag for item in ctx.plan.library.materials}
    findings = []
    for spec in ctx.plan.library.door_types:
        errors = []
        for item in spec.hardware:
            if item.product_ref not in products:
                errors.append(f"unknown hardware product {item.product_ref!r}")
            if item.height is not None and item.height.meters >= spec.height.meters:
                errors.append(f"{item.role} height must be inside the leaf")
        framing = spec.jamb_framing
        if framing and framing.blocking and not any(item.height is not None and item.role in
                HARDWARE_BLOCKING_ANCHOR_ROLES
                for item in spec.hardware):
            errors.append("blocking requires hardware anchor heights")
        if framing and framing.bay_fill_ref and framing.bay_fill_ref not in materials:
            errors.append(f"unknown jamb fill material {framing.bay_fill_ref!r}")
        for ref in spec.field_finish or ():
            if ref not in materials:
                errors.append(f"unknown field finish material {ref!r}")
        roles = {item.role for item in spec.hardware}
        if "strike_reinforcement" in roles and not roles & {"passage", "deadbolt"}:
            errors.append("strike reinforcement requires a passage latch or deadbolt")
        for error in errors:
            findings.append(Finding(check_id="integrity.door_hardware", severity=Severity.ERROR,
                                    result=Result.FAIL, element_tags=(spec.tag,),
                                    message=f"{spec.tag}: {error}"))
    types = {spec.tag: spec for spec in ctx.plan.library.door_types}
    for opening in ctx.model.openings:
        spec = types.get(opening.type_ref) if opening.is_door else None
        if spec is None or spec.jamb_framing is None:
            continue
        wall = ctx.model.wall(opening.host_wall)
        if wall is None or not any(member.category in {"king", "jack", "stud"}
                                   for member in wall.members):
            findings.append(Finding(check_id="integrity.door_hardware", severity=Severity.ERROR,
                result=Result.FAIL, element_tags=(opening.tag,),
                message=f"{opening.tag}: jamb framing requires a stud-framed host"))
        elif spec.jamb_framing.bay_fill_ref and not any(layer.is_cavity for layer in wall.layers):
            findings.append(Finding(check_id="integrity.door_hardware", severity=Severity.ERROR,
                result=Result.FAIL, element_tags=(opening.tag,),
                message=f"{opening.tag}: jamb fill requires a host cavity layer to replace"))
    return findings
