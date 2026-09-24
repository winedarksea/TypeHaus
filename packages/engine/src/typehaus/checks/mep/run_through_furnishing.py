"""``mep.run_through_furnishing`` — a run standing in a closet's shelving or a wardrobe.

The column a storage furnishing claims is :mod:`typehaus.resolve.mep_furnishings`' reading,
and the router refuses the same volume (``routing/obstacles``), so a check and a proposal
cannot disagree about the closet. A run is graded against it envelope for envelope — real
outside diameter plus lagging — because a riser grazing the shelf's edge is in the shelf.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed
from typehaus.checks.mep._format import feet_inches
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN

_CID = "mep.run_through_furnishing"


@check(Tier.ADVISORY, _CID)
def run_through_furnishing(ctx: CheckContext) -> list[Finding]:
    """Every run envelope against every storage furnishing's column."""
    from shapely import STRtree

    from typehaus.resolve.mep_envelopes import envelopes
    from typehaus.resolve.mep_furnishings import furnishing_columns

    columns = furnishing_columns(ctx.model)
    if not columns:
        return [not_applicable(_CID, "no storage furnishing (shelving, a rod, a wardrobe) "
                                     "is placed in a room with a known ceiling", ())]
    # A run in the ceiling cavity may graze the plane, as ``run_in_finished_volume`` allows.
    graze = ctx.preferences.mep.ceiling_intrusion_in * M_PER_IN
    index = STRtree([c.footprint for c in columns])
    hits: dict[tuple[str, str], tuple[float, float]] = {}
    for shell in envelopes(ctx.model):
        for prism in shell.prisms:
            for i in index.query(prism.footprint):
                column = columns[int(i)]
                low, high = max(prism.z0_m, column.z0_m), min(prism.z1_m, column.z1_m)
                if low >= column.z1_m - graze or high <= low:
                    continue
                if not prism.footprint.intersects(column.footprint):
                    continue
                if prism.footprint.intersection(column.footprint).area <= 1e-6:
                    continue
                key = (shell.tag, column.tag)
                was = hits.get(key)
                hits[key] = (low, high) if was is None else (min(was[0], low),
                                                             max(was[1], high))
    rooms = {c.tag: c.room for c in columns}
    out = [failed(_CID, f"{run} stands in {furniture}'s column in {rooms[furniture]} from "
                        f"{feet_inches(low)} to {feet_inches(high)}: shelving and hanging "
                        "space are in use floor to ceiling, so a run there is in the open "
                        "through the furnishing",
                  (run, furniture),
                  fix="route it inside a wall or the floor above — `haus route --run "
                      f"{run}` refuses this volume")
           for (run, furniture), (low, high) in sorted(hits.items())]
    return out or [passed(_CID, f"no run stands in any of {len(columns)} storage "
                                "furnishings' columns", ())]
