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
             "clear_face": [list(p) for p in r.clear_face], "floor_finish": r.floor_finish,
             # In-room finish overrides — a hearth pad authored on the room, or the band a
             # slab whose own top face is the finished floor claims back from it. Resolved
             # since the FinishZone work and carried into the .glb, but never exported here,
             # so the viewer painted the room's field finish over the whole clear face and
             # the Inspector could not say the floor changed. ``source_ref`` is the slab a
             # derived zone came from, null for an authored one.
             "finish_zones": [
                 {"outline": [list(p) for p in z.outline],
                  "material_ref": z.material_ref, "area_m2": z.area_m2,
                  "source_ref": z.source_ref}
                 for z in r.finish_zones
             ],
             # Derived head and glazing: facts about the room (read by
             # code.R305_ceiling_height and code.R303_1_light_and_ventilation), so they ride
             # on the room rather than living only inside a check's message string.
             #
             # ``clear_height_m`` is to the lowest thing overhead INCLUDING soffits, and
             # ``soffit_area_m2`` says how much of the room that low head actually covers —
             # the two are only useful together, since a duct box over 47 of 159 sf is not
             # the same building as a 7'-3" ceiling. ``glazed_area_m2`` and
             # ``operable_glazed_area_m2`` are raw areas, NOT R303.1's 8%/4% ratios and not
             # pre-halved: a reader totalling them against a floor area must apply the code
             # rule themselves, the same way the check does. null means a window type did
             # not resolve — not that the room has no glass.
             "clear_height_m": r.clear_height_m,
             "soffit_area_m2": r.soffit_area_m2,
             "glazed_area_m2": r.glazed_area_m2,
             "operable_glazed_area_m2": r.operable_glazed_area_m2}
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
        # The chain ``stack_edges`` only ever had pairs of. Not an element — nothing in the
        # viewer draws it — but it is what explains why two walls share a stud module or a
        # course line, so it ships beside the edges it generalizes.
        "layout_lines": [
            {"tag": line.tag, "origin": list(line.origin),
             "direction": list(line.direction),
             "base_z_m": line.base_z_m, "top_z_m": line.top_z_m,
             "members": [{"wall": m.wall_tag, "storey": m.storey,
                          "u_offset_m": m.u_offset_m,
                          "direction_sign": m.direction_sign,
                          "z0_m": m.z0_m, "z1_m": m.z1_m}
                         for m in line.members]}
            for line in model.layout_lines
        ],
    }
