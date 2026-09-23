"""A bedding's flood course: the stone below its drained section that may fill with water.

``FootingBedding.soakaway_depth`` hangs a course of the same stone under the drained ASCE 32
section. It stores water while the soil takes it, so it is never frost section; the fields
that describe it (inlets, overflow, the ``"soakaway"`` tile keyword) mean nothing without it.
"""

from __future__ import annotations

from typehaus.findings import Finding, element_error
from typehaus.model.structure import FootingBedding
from typehaus.resolve.drainage_network import SOAKAWAY_KEYWORD

_CID = "integrity.footing_bedding_soakaway"


def soakaway_findings(bedding: FootingBedding) -> list[Finding]:
    """Hard errors for a flood course that is not one, or course fields with no course."""
    spec = bedding.drain_tile_spec
    discharge = ((spec.discharge if spec is not None else None) or "").strip()
    keyword = discharge.lower() == SOAKAWAY_KEYWORD
    depth = bedding.soakaway_depth
    if depth is None:
        stray = [name for name, value in (
            ("inlet_refs", bedding.inlet_refs), ("overflow_ref", bedding.overflow_ref),
            ("overflow_invert", bedding.overflow_invert)) if value]
        out = []
        if stray:
            out.append(element_error(_CID, f"{bedding.tag} states {', '.join(stray)} but has "
                                           f"no soakaway_depth — there is no course to feed "
                                           f"or spill", bedding.tag))
        if keyword:
            out.append(element_error(_CID, f"{bedding.tag}'s tile discharges to "
                                           f"{SOAKAWAY_KEYWORD!r}, but the bed has no "
                                           f"soakaway course", bedding.tag))
        return out
    if depth.meters <= 0:
        return [element_error(_CID, f"{bedding.tag} soakaway_depth must be > 0", bedding.tag)]
    if bedding.drain_tile and discharge and not keyword:
        return [element_error(_CID, f"{bedding.tag} is a soakaway bed, so its tile lets go "
                                    f"into its own course ({SOAKAWAY_KEYWORD!r}), not "
                                    f"{discharge!r}", bedding.tag)]
    return []
