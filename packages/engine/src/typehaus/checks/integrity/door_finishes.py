"""Door surface references must resolve and have a visible owner."""
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.elements import Door


@check(Tier.INTEGRITY, "integrity.door_material_ref")
def door_material_ref(ctx: CheckContext) -> list[Finding]:
    materials = {item.tag for item in ctx.plan.library.materials}
    types = {item.tag: item for item in ctx.plan.library.door_types}
    findings = []
    entries = [*types.values(),
               *(item for item in ctx.plan.all_elements() if isinstance(item, Door))]
    for entry in entries:
        product = types.get(entry.type_ref) if isinstance(entry, Door) else entry
        for field in ("frame_material_ref", "leaf_material_ref"):
            ref = getattr(entry, field)
            if ref is None:
                continue
            problem = None
            if ref not in materials:
                problem = f"references unknown material {ref!r}"
            elif product and product.bookcase_door:
                problem = "has bookcase-owned surfaces; use bookcase_door.material_ref"
            elif (product and field == "leaf_material_ref"
                  and product.glazed and not product.trimless):
                problem = "has a glass-only leaf with no solid surface to finish"
            if problem:
                findings.append(Finding(
                    check_id="integrity.door_material_ref", severity=Severity.ERROR,
                    result=Result.FAIL, element_tags=(entry.tag,),
                    message=f"{entry.tag}.{field} {problem}",
                    fix_hint="choose a defined material for a supported surface, or reset to None"))
    return findings
