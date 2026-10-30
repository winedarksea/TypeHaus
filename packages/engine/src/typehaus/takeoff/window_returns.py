"""Installed return finish area, never solid volume; the beads bill in ``drywall_trims``."""

from collections import defaultdict

from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.derived_paint import PAINT

_M2_TO_FT2 = 10.7639104167


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
