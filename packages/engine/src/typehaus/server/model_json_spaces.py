"""Rooms and everything derived *from* rooms rather than from construction.

Areas, the space and building-height summaries, the boundary conditions the junction solver
found, the transitions authored against them, and the stack edges between storeys. The
common thread is that none of it is geometry the viewer draws — it is the reading of the
house the inspectors and the code sheets work from, so it moves when the *interpretation*
changes, not when a wall does.
"""

from __future__ import annotations

from typing import Any

from typehaus.resolve.model import ResolvedModel
from typehaus.server.model_json_shared import _provenance
from typehaus.source.provenance import Provenance


def spaces_json(model: ResolvedModel, provenance: Provenance | None) -> dict[str, Any]:
    """Rooms, the two summaries over them, and the conditions/transitions/stack edges."""
    # Imported inside the call, as the monolith did: both summaries reach back into the
    # server package, and the payload must not need them at import time.
    from typehaus.server.building_height_summary import build_building_height_summary
    from typehaus.server.space_summary import build_space_summary

    return {
        "rooms": [
            {"uid": r.uid, "tag": r.tag, "storey": r.storey, "occupancy": r.occupancy,
             "provenance": _provenance(provenance, r.tag),
             "conditioned": r.conditioned, "area_m2": r.area_m2,
             "clear_face": [list(p) for p in r.clear_face], "floor_finish": r.floor_finish}
            for r in model.rooms
        ],
        "space_summary": build_space_summary(model),
        "building_height_summary": build_building_height_summary(model),
        "conditions": [
            {"kind": c.kind.value, "key": c.key, "elements": list(c.element_tags)}
            for c in model.conditions
        ],
        "transitions": [
            {"tag": t.tag, "pattern": t.condition_pattern, "overlay": t.overlay,
             "notes": t.notes,
             "continuity": [{"control": c.control, "from_face": c.from_face,
                             "to_face": c.to_face} for c in t.continuity],
             "joins": [{"layer": j.layer, "side": j.side,
                        "termination_m": j.termination.meters, "treatment": j.treatment}
                       for j in t.joins]}
            for t in model.plan.library.transitions
        ],
        "stack_edges": [
            {"lower": e.lower_wall, "upper": e.upper_wall, "overlap_m": e.overlap_m,
             "width_change": e.width_change}
            for e in model.stack_edges
        ],
    }
