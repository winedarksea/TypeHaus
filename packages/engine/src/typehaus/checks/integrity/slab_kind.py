"""An authored ``Slab.kind`` agrees with what its assembly and support derive.

``kind`` decides whether a slab is billed as a pour, drawn on the foundation sheet and
reinforced. An authored value that contradicts the derivation (``resolve/slab_kind.py``)
would move a plywood cap into the concrete yards, or a pour out of them, silently.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.floors import Slab
from typehaus.resolve.slab_kind import derive_slab_kind

_CHECK_ID = "integrity.slab_kind_matches_assembly"


@check(Tier.INTEGRITY, _CHECK_ID)
def slab_kind_matches_assembly(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    authored = 0
    for solid in ctx.model.solids:
        element = ctx.plan.by_tag(solid.tag) if solid.tag and not solid.derived else None
        if not isinstance(element, Slab) or element.kind is None:
            continue
        authored += 1
        derived = derive_slab_kind(ctx.model, element, solid.storey, solid.z0_m)
        if derived != element.kind:
            out.append(failed(
                _CHECK_ID,
                f"{element.tag} authors kind=\"{element.kind}\" but its assembly and "
                f"support derive \"{derived}\"", tags=(element.tag,),
                fix=f"set kind=\"{derived}\" on {element.tag}, or change its assembly"))
    if not authored:
        return [not_applicable(_CHECK_ID, "no Slab authors a kind")]
    if not out:
        return [passed(_CHECK_ID, f"all {authored} authored slab kinds match the derivation")]
    return out
