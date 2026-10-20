"""Installed return finish area and three-sided bead lengths, never solid volume."""

from collections import defaultdict

from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.derived_paint import PAINT

_M2_TO_FT2 = 10.7639104167
_M_TO_FT = 3.280839895013123
BEAD_MATERIALS = ("drywall-corner-bead", "drywall-frame-termination-bead")


def window_return_finish_rows(model: ResolvedModel) -> list[dict[str, object]]:
    areas: dict[tuple[str, float], float] = defaultdict(float)
    for reveal in model.window_returns:
        for layer in reveal.layers:
            areas[(layer.material_ref, layer.thickness_m)] += layer.area_m2
        if reveal.derived_paint:
            areas[(PAINT, 0.0)] += reveal.exposed_area_m2
    return [{"scope": "window return", "function": "finish", "material": material,
             "thickness_in": round(thickness / 0.0254, 3),
             "net_area_sqft": round(area * _M2_TO_FT2, 1), "also_in_sheet_goods": False}
            for (material, thickness), area in sorted(areas.items())]


def window_return_bead_rows(model: ResolvedModel) -> list[dict[str, object]]:
    length = sum(reveal.bead_length_m for reveal in model.window_returns)
    if length <= 0:
        return []
    return [{"material": material, "length_ft": round(length * _M_TO_FT, 1),
             "tags": sorted(reveal.window_ref for reveal in model.window_returns)}
            for material in BEAD_MATERIALS]
