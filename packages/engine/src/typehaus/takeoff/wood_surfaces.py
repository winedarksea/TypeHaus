"""Wood surfaces by species — the estimator's lumberyard order, cut across sections.

Wood a house wears arrives from four places that bill in four different sections: a
T&G liner authored as an assembly FINISH layer (``envelope_layers``), a wainscot authored
as a ``WallPaneling``, a species floor (``floor_finishes``), and a timber post
(``structural_solids`` — by the cubic foot, which nobody orders elm in). This section is
the species rollup across all four, in the units wood is bought in: square feet and board
feet. Rows that mirror another section say so — ``also_in_envelope_layers`` /
``also_in_floor_finishes`` / ``also_in_structural_solids`` — so a caller summing sections
knows exactly where the overlaps are; the primary billing never moves here.

Admission is ``Material.species``: authored species is what makes a material a wood
product this section orders, and ``stock_bf_per_sqft`` (1.0 = 4/4 stock) is what turns
its square feet into board feet. Neither is ever guessed from a tag substring.

Known approximation, inherited for reconcilability: a FINISH liner on a foundation wall
bills at the wall's full height (the same gross ``envelope_layers`` uses), though the
physical liner may stop at a drop ceiling — the sauna's east wall carries ~20 sf of that.
"""

from __future__ import annotations

import math
from collections import defaultdict

from typehaus.model.enums import LayerFunction
from typehaus.model.structure import Post
from typehaus.resolve.geometry import length, sub
from typehaus.resolve.model import ResolvedModel

_M2_TO_FT2 = 10.7639104
_M_TO_FT = 3.280839895

# Ordering allowances, matching ``finishes.py``: T&G and boards cut to a wall waste like
# plank cut to a floor; tile carries breakage.
_WASTE: dict[str, float] = {
    "tile": 0.15,
}
_DEFAULT_WASTE = 0.10


def _order_area(net_ft2: float, waste: float) -> float:
    return float(math.ceil(net_ft2 * (1.0 + waste) - 1e-9))


def wood_surfaces_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per (species, material, kind): the species-split wood order."""
    from typehaus.takeoff.framing import _board_feet_per_ft, _order_length_ft

    materials = {material.tag: material for material in model.plan.library.materials}
    rows: list[dict[str, object]] = []

    # --- assembly FINISH layers with a species (the sauna liner) --------------------
    # The same wall walk ``envelope_layer_takeoff`` makes — run x mean top, net of
    # openings — filtered to species-bearing FINISH layers, then net of any
    # ``replaces_wall_finish`` paneling band on the wall (the tile splash).
    openings_by_wall: dict[str, float] = defaultdict(float)
    for opening in model.openings:
        openings_by_wall[opening.host_wall] += opening.width_m * opening.height_m
    override_by_wall: dict[str, float] = defaultdict(float)
    for paneling in model.panelings:
        if paneling.replaces_wall_finish:
            override_by_wall[paneling.wall_tag] += paneling.area_m2

    liner_area: dict[str, float] = defaultdict(float)
    liner_tags: dict[str, list[str]] = defaultdict(list)
    for wall in model.walls:
        run = length(sub(wall.axis[1], wall.axis[0]))
        mean_top = ((wall.top_z0_m or wall.z1_m) + (wall.top_z1_m or wall.z1_m)) / 2.0
        net = max(0.0, run * (mean_top - wall.z0_m) - openings_by_wall[wall.tag])
        for layer in wall.layers:
            if getattr(layer, "is_cavity", False):
                continue
            material = materials.get(layer.material_ref)
            if (layer.function != LayerFunction.FINISH.value or material is None
                    or material.species is None):
                continue
            liner_area[layer.material_ref] += max(
                0.0, net - override_by_wall[wall.tag])
            liner_tags[layer.material_ref].append(wall.tag)
    for ref in sorted(liner_area):
        rows.append(_area_row(materials, ref, liner_area[ref],
                              kind="wall-assembly-finish", where=liner_tags[ref],
                              also={"also_in_envelope_layers": True}))

    # --- WallPaneling bands (wainscot; overrides like the tile splash) --------------
    paneling_area: dict[tuple[str, bool], float] = defaultdict(float)
    paneling_rooms: dict[tuple[str, bool], list[str]] = defaultdict(list)
    for paneling in model.panelings:
        key = (paneling.material_ref, paneling.replaces_wall_finish)
        paneling_area[key] += paneling.area_m2
        paneling_rooms[key].append(paneling.room)
    for ref, is_override in sorted(paneling_area):
        rows.append(_area_row(
            materials, ref, paneling_area[(ref, is_override)],
            kind="override" if is_override else "paneling",
            where=paneling_rooms[(ref, is_override)]))

    # --- species timber posts (the suite's elm tudor posts) -------------------------
    # Species comes off the post's finish assembly's STRUCTURE layer material; length off
    # its resolved solid; board feet off the profile's actual section over the *ordered*
    # length, since custom-milled stock is what the sawyer charges for.
    solids = {solid.tag: solid for solid in model.solids}
    timber: dict[tuple[str, str], dict[str, object]] = {}
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if not isinstance(element, Post) or element.assembly is None:
                continue
            assembly = model.plan.library.resolve_assembly(element.assembly)
            if assembly is None:
                continue
            ref = next((ly.material_ref for ly in assembly.layers
                        if ly.function == LayerFunction.STRUCTURE), None)
            material = materials.get(ref) if ref else None
            if material is None or material.species is None:
                continue
            solid = solids.get(element.tag)
            if solid is None:
                continue
            cut_ft = (solid.z1_m - solid.z0_m) * _M_TO_FT
            key = (material.tag, element.size)
            group = timber.setdefault(key, {
                "species": material.species, "material": material.tag,
                "kind": "timber", "known": True, "profile": element.size,
                "count": 0, "cut_length_ft": 0.0, "order_length_ft": 0,
                "board_feet": None, "tags": [],
                "also_in_structural_solids": True,
            })
            group["count"] = int(group["count"]) + 1
            group["cut_length_ft"] = round(float(group["cut_length_ft"]) + cut_ft, 1)
            group["order_length_ft"] = (int(group["order_length_ft"])
                                        + _order_length_ft(cut_ft))
            tags = group["tags"]
            assert isinstance(tags, list)
            tags.append(element.tag)
    for key in sorted(timber):
        group = timber[key]
        bf_per_ft = _board_feet_per_ft(str(group["profile"]))
        if bf_per_ft is not None:
            group["board_feet"] = round(bf_per_ft * float(group["order_length_ft"]), 1)
        group["tags"] = sorted(group["tags"])  # type: ignore[index]
        rows.append(group)

    # --- species floors (the oak studies) -------------------------------------------
    # Mirror of the ``floor_finishes`` field-area math for finishes whose material has a
    # species, so the two sections reconcile to the digit.
    floor_area: dict[str, float] = defaultdict(float)
    floor_rooms: dict[str, list[str]] = defaultdict(list)
    for room in model.rooms:
        material = materials.get(room.floor_finish) if room.floor_finish else None
        if material is None or material.species is None:
            continue
        zone_area = sum(zone.area_m2 for zone in room.finish_zones)
        floor_area[material.tag] += max(room.area_m2 - zone_area, 0.0)
        floor_rooms[material.tag].append(room.tag)
    for ref in sorted(floor_area):
        rows.append(_area_row(materials, ref, floor_area[ref], kind="floor",
                              where=floor_rooms[ref],
                              also={"also_in_floor_finishes": True}))

    return rows


def _area_row(materials: dict, ref: str, area_m2: float, kind: str,
              where: list[str], also: dict[str, object] | None = None) -> dict[str, object]:
    """A square-foot row; board feet added when the material states its stock."""
    material = materials.get(ref)
    net_ft2 = area_m2 * _M2_TO_FT2
    waste = _WASTE.get(ref, _DEFAULT_WASTE)
    order = _order_area(net_ft2, waste)
    bf = (round(order * material.stock_bf_per_sqft, 1)
          if material is not None and material.stock_bf_per_sqft is not None else None)
    row: dict[str, object] = {
        "species": material.species if material is not None else None,
        "material": ref if material is not None else "UNKNOWN",
        "kind": kind,
        "known": material is not None,
        "net_area_sqft": round(net_ft2, 1),
        "waste_pct": round(waste * 100.0, 1),
        "order_area_sqft": order,
        "board_feet": bf,
        "tags": sorted(set(where)),
    }
    row.update(also or {})
    return row
