"""The planting list: plants by type, trellis posts by the piece, wire by the foot.

Deliberately UNPRICED: no plan in ``cli/prices.ESTIMATE_PLANS`` reads it and it is not an
``UNPRICED_VIEWS`` entry, so every row surfaces in the estimate's ``unpriced`` list — which
is what an illustrative planting plan should say about itself.
"""

from __future__ import annotations

import math

from typehaus.model.landscape import Trellis
from typehaus.resolve.landscape import trellis_post_stations
from typehaus.resolve.model import ResolvedModel

_M_TO_FT = 3.280839895


def planting_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per plant type (``ea``), then trellis posts (``ea``) and wire (``LF``)."""
    types = {t.tag: t for t in model.plan.library.plant_types}
    counts: dict[str, list[str]] = {}
    for plant in model.plants:
        counts.setdefault(plant.type_ref, []).append(plant.source_ref)
    rows: list[dict[str, object]] = []
    for tag, sources in sorted(counts.items()):
        ptype = types[tag]
        rows.append({"item": tag, "kind": "plant", "unit": "ea", "count": len(sources),
                     "quantity": len(sources),
                     "name": " ".join(filter(None, (ptype.botanical_name,
                                                   f"'{ptype.cultivar}'" if ptype.cultivar
                                                   else ""))),
                     "form": ptype.form, "tags": sorted(set(sources))})
    posts: dict[str, list[str]] = {}
    wire_m: dict[str, float] = {}
    wire_tags: dict[str, list[str]] = {}
    for element in model.plan.all_elements():
        if not isinstance(element, Trellis):
            continue
        key = f"{element.post}:{element.post_material}"
        posts.setdefault(key, []).extend([element.tag] * len(trellis_post_stations(element)))
        path = [p.xy_m for p in element.path]
        run = sum(math.dist(a, b) for a, b in zip(path[:-1], path[1:], strict=True))
        wire_m[element.wire] = wire_m.get(element.wire, 0.0) + run * len(element.wire_heights)
        wire_tags.setdefault(element.wire, []).append(element.tag)
    for key, tags in sorted(posts.items()):
        rows.append({"item": f"trellis-post:{key}", "kind": "trellis_post", "unit": "ea",
                     "count": len(tags), "quantity": len(tags), "tags": sorted(set(tags))})
    for wire, length in sorted(wire_m.items()):
        feet = round(length * _M_TO_FT, 1)
        rows.append({"item": f"trellis-wire:{wire}", "kind": "trellis_wire", "unit": "LF",
                     "count": len(wire_tags[wire]), "quantity": feet, "length_ft": feet,
                     "tags": sorted(wire_tags[wire])})
    return rows
