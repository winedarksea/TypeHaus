"""``Wall.layer_materials`` must name a layer the assembly has and a material the catalog has.

The override is applied by name in ``resolve/topology.py`` with a plain dict lookup, so a
typo in either half is silent: the wall resolves exactly as if nothing had been authored,
and the only symptom is a colour that did not change. That is the failure mode this check
exists for — the override's whole purpose is appearance, so its whole failure mode is
invisible.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity


@check(Tier.INTEGRITY, "integrity.wall_layer_material")
def wall_layer_material(ctx: CheckContext) -> list[Finding]:
    findings: list[Finding] = []
    library = ctx.plan.library
    materials = {m.tag for m in library.materials or ()}

    for wall in ctx.plan.all_elements():
        overrides = getattr(wall, "layer_materials", ()) or ()
        if not overrides:
            continue
        # Resolved, not raw: an assembly composed off a library base states its full stack
        # only after resolution, and the override is matched against that same full stack.
        assembly = ctx.plan.library.resolve_assembly(wall.assembly)
        # An unknown assembly is already `integrity.wall_assembly`; do not report it twice.
        if assembly is None:
            continue
        names = {layer.name for layer in assembly.layers}
        names.update(layer.name for layer in (assembly.default_lining or ()))
        for override in overrides:
            if override.layer not in names:
                findings.append(Finding(
                    severity=Severity.ERROR,
                    check_id="integrity.wall_layer_material",
                    message=(f"wall {wall.tag} overrides layer {override.layer!r}, which "
                             f"{wall.assembly} does not have"),
                    element_tags=(wall.tag,),
                    fix_hint=(f"{wall.assembly}'s layers are "
                              f"{', '.join(sorted(names))}"),
                    result=Result.FAIL,
                ))
            if override.material not in materials:
                findings.append(Finding(
                    severity=Severity.ERROR,
                    check_id="integrity.wall_layer_material",
                    message=(f"wall {wall.tag} overrides layer {override.layer!r} with "
                             f"material {override.material!r}, which the catalog has no "
                             "entry for"),
                    element_tags=(wall.tag,),
                    fix_hint="add the Material to the library, or fix the spelling",
                    result=Result.FAIL,
                ))
    return findings
