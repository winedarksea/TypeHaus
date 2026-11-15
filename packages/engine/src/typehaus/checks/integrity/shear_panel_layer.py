"""A shear panel's schedule names a layer that exists (``ShearPanelSpec.sheathing_layer``).

The spec's SDPWS row is read for one sheathing layer by name. Re-layer the assembly and the
row says nothing about the wall any more, while ``lateral_system`` keeps grading it. This is
the drift guard the field's own docstring promises.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, failed, not_applicable, passed
from typehaus.model.enums import LayerFunction

_CHECK_ID = "integrity.shear_panel_layer"


@check(Tier.INTEGRITY, _CHECK_ID)
def shear_panel_layer(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    graded = 0
    for wall in ctx.plan.all_elements():
        spec = getattr(wall, "shear_panel", None)
        if spec is None:
            continue
        graded += 1
        assembly = ctx.plan.library.resolve_assembly(wall.assembly)
        layers = assembly.layers if assembly is not None else ()
        layer = next((ly for ly in layers if ly.name == spec.sheathing_layer), None)
        if layer is None:
            problem = f"names layer {spec.sheathing_layer!r}, which {wall.assembly} does not have"
        elif layer.function is not LayerFunction.SHEATHING:
            problem = f"names {spec.sheathing_layer!r}, which is not a SHEATHING layer"
        elif layer.nailing is None:
            problem = (f"reads its row for {spec.sheathing_layer!r}, which authors no "
                       f"`SheathingNailing`: the schedule is graded and never billed")
        else:
            continue
        out.append(failed(_CHECK_ID, f"{wall.tag}'s shear_panel {problem}", (wall.tag,),
                          fix="point `sheathing_layer` at the nailed sheathing layer the "
                              "SDPWS row was read for"))
    if not graded:
        return [not_applicable(_CHECK_ID, "no wall declares a shear panel")]
    if not out:
        out.append(passed(_CHECK_ID, f"{graded} shear panel schedule(s) name a nailed "
                                     f"sheathing layer of their own wall"))
    return out
