"""Trim and door paint off the derived trim and doors (decision #113, ``PaintStandard``).

``trim_paint_rows`` bills ``standard.trim`` by the LF of painted base and casing — the
``interior_trim`` rows whose stock is ``wood_surface="painted"``; oiled hardwood and a base the
floor trade makes stay out. Stair skirts and paneling are left out because their own rates
already include priming and painting. ``door_leaf_paint_rows`` bills ``standard.doors`` by the
face area of every interior leaf and frame (both faces), in ``envelope_layers`` beside the
exterior doors' ``field_finish``. A door type with a ``field_finish`` or a factory-finished
leaf is never billed again here.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.room_paint import paint_standard
from typehaus.takeoff.door_hardening import door_face_area_m2

_FT = 0.3048
_SQFT = 0.09290304
#: The ``interior_trim`` kinds a painter coats; skirts and paneling carry paint in their rate.
PAINTED_TRIM_KINDS = ("baseboard", "door casing")


def trim_paint_rows(model: ResolvedModel) -> list[dict[str, object]]:
    from typehaus.takeoff.interior_trim import interior_trim_takeoff

    standard = paint_standard(model.plan)[0]
    if standard is None or standard.trim is None:
        return []
    materials = {m.tag: m for m in model.plan.library.materials}
    length: dict[str, float] = defaultdict(float)
    tags: dict[str, set] = defaultdict(set)
    for row in interior_trim_takeoff(model):
        material = materials.get(str(row["material"]))
        if row["kind"] not in PAINTED_TRIM_KINDS or material is None \
                or material.wood_surface != "painted":
            continue
        length[str(row["kind"])] += float(row["length_ft"])
        tags[str(row["kind"])].update(row["tags"])
    name = materials[standard.trim].name if standard.trim in materials else standard.trim
    return [{"kind": kind, "material": standard.trim,
             "description": f"{name} — {kind}",
             "length_ft": round(length[kind], 2), "tags": sorted(tags[kind])}
            for kind in sorted(length)]


def door_leaf_paint_rows(model: ResolvedModel) -> list[dict[str, object]]:
    standard = paint_standard(model.plan)[0]
    if standard is None or standard.doors is None:
        return []
    types = {item.tag: item for item in model.plan.library.door_types}
    area = 0.0
    for opening in model.openings:
        spec = types.get(opening.type_ref) if opening.is_door else None
        if (spec is None or spec.exterior or spec.field_finish is not None
                or spec.leaf_material_ref is not None or spec.bookcase_door is not None):
            continue
        area += 2.0 * door_face_area_m2(model, opening)
    if area <= 0.0:
        return []
    return [dict(scope="door leaf paint", function="finish", material=standard.doors,
                 thickness_in=0.0, net_area_sqft=round(area / _SQFT, 1),
                 also_in_sheet_goods=False)]
