"""A bedding's flood course: the stone below its drained section that may fill with water.

``FootingBedding.soakaway_depth`` hangs a course of the same stone under the drained ASCE 32
section. It stores water while the soil takes it, so it is never frost section; the fields
that describe it (inlets, overflow, the ``"soakaway"`` tile keyword) mean nothing without it
— except on a pipeless bed whose stone drains into a course (``discharge_ref``).
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
    if bedding.discharge_ref is not None:
        return _pipeless_findings(bedding, depth)
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


def _pipeless_findings(bedding: FootingBedding, depth) -> list[Finding]:
    """``discharge_ref`` is a pipeless bed's outlet: never beside a tile, a course or a keyword.

    Such a bed's stone is part of the body it drains into, so it may carry that body's inlets
    and overflow lip itself (the court's relief is at the bed its overflow run starts in).
    """
    ref = bedding.discharge_ref.strip()
    if bedding.drain_tile:
        why = "it runs a drain tile, which names its own outlet"
    elif depth is not None:
        why = "it has its own soakaway course"
    elif ref.lower() == SOAKAWAY_KEYWORD:
        why = f"{SOAKAWAY_KEYWORD!r} names a course, not a bed"
    elif not ref:
        why = "it is empty"
    else:
        return []
    return [element_error(_CID, f"{bedding.tag} states discharge_ref={ref!r}, but {why}",
                          bedding.tag)]
