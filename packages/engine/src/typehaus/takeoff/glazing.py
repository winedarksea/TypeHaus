"""The glazing section of the bill of materials — sheets, extrusions, and their fixings.

A glazing panel is bought as a *sheet*, its trim by the *lineal foot*, and its fixings by
the *piece*, so none of the three fits the existing sections: ``framing_takeoff`` bills
sticks of lumber, ``structural_solids_takeoff`` bills concrete by the yard, and
``sheet_goods_takeoff`` only ever looked at SHEATHING layers — which meant the panels that
are the entire enclosure of a breezeway were counted by nothing at all.

Sheet economy is the point of the rows here. A 4'x8' panel that has to be cut in half is
still a whole panel on the order, so the count is what you buy, not what you install.
"""

from __future__ import annotations

import math

from typehaus.resolve.geometry import polygon_area
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_catalog import (
    ROLE_GLAZING_PANEL_FASTENER,
    hardware_for_role,
    hardware_row,
)

_M2_TO_FT2 = 10.7639104167
_M_TO_FT = 3.280839895013123
_SHEET_AREA_FT2 = 32.0  # 4'x8', the stock multiwall/sheet-good size

# Fixing spacing along a panel's perimeter. Multiwall polycarbonate is fixed through
# oversize holes at a close, even pitch so the sheet can expand without the fastener
# clamping it; 24" is the common published maximum for the perimeter of a 16mm sheet.
GLAZING_FASTENER_SPACING_IN = 24.0


def _panel_area_m2(solid) -> float:
    """The panel's face area — its plan footprint if it lies flat, its elevation if it stands."""
    if solid.category != "glazing":
        return 0.0
    plan_area = abs(polygon_area(list(solid.outline)))
    ring = list(solid.outline)
    run = max(((ring[i][0] - ring[i - 1][0]) ** 2 + (ring[i][1] - ring[i - 1][1]) ** 2) ** 0.5
              for i in range(len(ring))) if len(ring) >= 2 else 0.0
    height = solid.z1_m - solid.z0_m
    # A standing sheet is a thin prism: its footprint is the sheet's *thickness* times its
    # run, which is not the sheet. Its face is the run times the height it stands.
    return run * height if run * height > plan_area else plan_area


def _panel_perimeter_m(solid) -> float:
    ring = list(solid.outline)
    if len(ring) < 3:
        return 0.0
    plan_perimeter = sum(
        ((ring[i][0] - ring[i - 1][0]) ** 2 + (ring[i][1] - ring[i - 1][1]) ** 2) ** 0.5
        for i in range(len(ring)))
    run = max(((ring[i][0] - ring[i - 1][0]) ** 2 + (ring[i][1] - ring[i - 1][1]) ** 2) ** 0.5
              for i in range(len(ring)))
    height = solid.z1_m - solid.z0_m
    if run * height > abs(polygon_area(ring)):  # standing sheet
        return 2.0 * (run + height)
    return plan_perimeter


def glazing_panel_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per glazing assembly: face area and the whole 4x8 sheets it is cut from."""
    groups: dict[str, dict[str, object]] = {}
    for solid in model.solids:
        if solid.category != "glazing":
            continue
        key = solid.assembly or "(no assembly)"
        row = groups.get(key)
        if row is None:
            row = groups[key] = {"assembly": solid.assembly, "panels": 0,
                                 "area_m2": 0.0, "tags": []}
        row["panels"] = int(row["panels"]) + 1
        row["area_m2"] = float(row["area_m2"]) + _panel_area_m2(solid)
        tags = row["tags"]
        assert isinstance(tags, list)
        tags.append(solid.tag)
    rows: list[dict[str, object]] = []
    for key in sorted(groups):
        row = groups[key]
        area_ft2 = float(row["area_m2"]) * _M2_TO_FT2
        rows.append({
            "assembly": row["assembly"],
            "panels": int(row["panels"]),
            "net_area_sqft": round(area_ft2, 1),
            "sheets_4x8": math.ceil(area_ft2 / _SHEET_AREA_FT2 - 1e-9),
            "tags": sorted(row["tags"]),
        })
    return rows


def glazing_trim_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Lineal feet of glazing extrusion, grouped by profile and material.

    The engine had no lineal-foot section for trim at all — the fascia/gutter family was
    only ever billed as solids. This mirrors ``construction_returns_takeoff``'s row shape so
    an estimator reads both the same way.
    """
    from typehaus.model.trim import GlazingTrim

    runs: dict[tuple[str, str, bool], dict[str, object]] = {}
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if not isinstance(element, GlazingTrim):
                continue
            # A jamb channel runs up the sheet's edge, so its length is its depth; every
            # other run's length is the path it follows. Billing the path either way would
            # charge an 8'-0" jamb as 5/8" of aluminium.
            if element.vertical:
                length_m = element.depth.meters
            else:
                points = [p.xy_m for p in element.path]
                length_m = sum(
                    ((points[i][0] - points[i - 1][0]) ** 2
                     + (points[i][1] - points[i - 1][1]) ** 2) ** 0.5
                    for i in range(1, len(points)))
            key = (element.profile, element.material or "", element.weep_holes)
            row = runs.get(key)
            if row is None:
                row = runs[key] = {"category": "glazing trim", "profile": element.profile,
                                   "material": element.material, "count": 0,
                                   "length_m": 0.0, "weep_holes": element.weep_holes,
                                   "tags": []}
            row["count"] = int(row["count"]) + 1
            row["length_m"] = float(row["length_m"]) + length_m
            tags = row["tags"]
            assert isinstance(tags, list)
            tags.append(element.tag)
    return [
        {"category": row["category"], "profile": row["profile"], "material": row["material"],
         "count": int(row["count"]),
         "length_ft": round(float(row["length_m"]) * _M_TO_FT, 1),
         "weep_holes": row["weep_holes"], "tags": sorted(row["tags"])}
        for row in (runs[key] for key in sorted(runs, key=lambda k: (k[0], k[1], k[2])))
    ]


def glazing_fastener_rows(model: ResolvedModel) -> list:
    """Gasketed stainless panel screws, one every 24" around each sheet's perimeter."""
    panels = [solid for solid in model.solids if solid.category == "glazing"]
    if not panels:
        return []
    spacing_ft = GLAZING_FASTENER_SPACING_IN / 12.0
    count = sum(math.ceil(_panel_perimeter_m(panel) * _M_TO_FT / spacing_ft - 1e-9)
                for panel in panels)
    item = hardware_for_role(ROLE_GLAZING_PANEL_FASTENER)
    return [hardware_row(
        item, scope="glazing panel fixing", count=count,
        basis=(f"one every {GLAZING_FASTENER_SPACING_IN:.0f}\" around the perimeter of "
               f"{len(panels)} glazing panel(s)"))]
