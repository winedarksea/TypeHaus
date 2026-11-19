"""A leafless through opening's return strips by installed area, as window returns bill theirs.

The wall's own finish rows stop at the rough opening; the beads bill in ``drywall_trims``
(→ resolve/drywall_passage_wraps.py). Like the beads, nothing bills without a DrywallStandard.
"""

from collections import defaultdict

from typehaus.resolve.drywall_led import drywall_standard
from typehaus.resolve.model import ResolvedModel

_M2_TO_FT2 = 10.7639104167


def passage_return_finish_rows(model: ResolvedModel) -> list[dict[str, object]]:
    if drywall_standard(model.plan)[0] is None:
        return []
    areas: dict[tuple[str, float], float] = defaultdict(float)
    for face in model.passage_wraps:
        for material, thickness in face.finish:
            areas[(material, thickness)] += face.return_area_m2
    return [{"scope": "passage return", "function": "finish", "material": material,
             "thickness_in": round(thickness / 0.0254, 3),
             "net_area_sqft": round(area * _M2_TO_FT2, 1), "also_in_sheet_goods": False}
            for (material, thickness), area in sorted(areas.items())]
