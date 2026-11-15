"""A hung machine's trapeze against the runs it hangs among (``resolve/equipment_hangers.py``).

Every seated rod (a riser), each bridge and strut (1 5/8" strut section) against every placed
run's envelope, insulation wrap included (``resolve/equipment_hanger_clearance``). Contact
within 1/16" is drawn to touch; deeper is a FAIL naming the part, the run and the depth.
No pardons: a rod through a duct is a clash whatever drew it.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed
from typehaus.checks.mep._format import feet_inches
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN

CID = "structural.equipment_hanger_clearance"


@check(Tier.STRUCTURAL, CID)
def equipment_hanger_clearance(ctx: CheckContext) -> list[Finding]:
    from typehaus.resolve.equipment_hanger_clearance import RunEnvelopes, hanger_segments

    rods = list(getattr(ctx.model, "equipment_hangers", ()))
    if not rods:
        return [not_applicable(CID, "no Equipment authors hangers")]
    runs = RunEnvelopes(ctx.model)
    by_unit: dict[str, list] = {}
    for rod in rods:
        by_unit.setdefault(rod.equipment_tag, []).append(rod)
    out: list[Finding] = []
    for tag, unit in sorted(by_unit.items()):
        parts = hanger_segments(unit)
        clashes = [(label, run, c) for label, seg in parts
                   for run, c in sorted(runs.clashes(seg).items())]
        out.extend(failed(
            CID, f"{tag} {label} is {c.score_m / M_PER_IN:.2f}\" inside {run}'s envelope at "
                 f"({feet_inches(c.point[0])}, {feet_inches(c.point[1])}): "
                 f"{c.plan_depth_m / M_PER_IN:.2f}\" in plan, "
                 f"{c.z_depth_m / M_PER_IN:.2f}\" in elevation",
            (tag, run),
            fix=f"re-route {run} clear of the trapeze, or move {tag}")
            for label, run, c in clashes)
        if not clashes:
            out.append(passed(CID, f"{tag}: {len(parts)} trapeze parts (rods, struts, "
                                   "bridges) clear every run envelope", (tag,)))
    return out
