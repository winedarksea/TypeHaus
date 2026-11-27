"""An SRW wall's drain pipe and capstone adhesive, billed into the drainage section.

``SrwChartSection.drain`` is the pipe at the back of the base trench: one run along each
wall's axis, plus ONE stub per outlet bedding (the walls naming one drain as a connected
network) from the nearest wall to that bedding's stone column. The cap adhesive is the
walls' capstone run over ``SrwChartSection.cap_adhesive_coverage`` (the house's tube label),
rounded up to whole tubes on the total, since a tube is not split across walls.
"""

from __future__ import annotations

import math
from collections import defaultdict

from shapely.geometry import LineString, Polygon

from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.ownership import children_of


def _stub_m(model: ResolvedModel, outlet_ref: str, axes: list[LineString]) -> float:
    """Shortest reach from any wall's axis to the outlet bedding's wall column (stone)."""
    from typehaus.model.structure import FootingBedding

    bed = next((e for e in model.plan.all_elements()
                if isinstance(e, FootingBedding) and e.tag == outlet_ref), None)
    cols = [Polygon(s.outline) for s in children_of(model, bed, ["drain_column"])] if bed else []
    cols = [c for c in cols if c.is_valid and not c.is_empty]
    return min((a.distance(c) for a in axes for c in cols), default=0.0)


def add_srw_accessories(model: ResolvedModel, rows) -> None:  # type: ignore[no-untyped-def]
    """Add ``srw_drain`` (LF) and ``srw_cap_adhesive`` (tubes) rows to the drainage ``_Rows``."""
    from typehaus.model.structure import FoundationWall

    resolved = {w.tag: w for w in model.walls}
    pipes: dict[tuple[str, str, float], list] = defaultdict(list)
    caps: dict[tuple[str, float], list] = defaultdict(list)
    for el in model.plan.all_elements():
        srw = el.srw if isinstance(el, FoundationWall) else None
        chart = srw.chart if srw is not None else None
        wall = resolved.get(el.tag) if chart is not None else None
        if wall is None:
            continue
        axis = LineString(wall.axis)
        if chart.drain is not None and chart.drain.diameter is not None:
            product = chart.drain.pipe.split(",")[0].strip()
            pipes[(chart.drain.outlet_ref, product, chart.drain.diameter.meters)].append(
                (el.tag, axis))
        if srw.cap and chart.cap_adhesive_coverage is not None:
            caps[(srw.cap, chart.cap_adhesive_coverage.meters)].append((el.tag, axis.length))

    for (outlet, product, dia_m), legs in sorted(pipes.items()):
        for tag, axis in legs:
            rows.add("srw_drain", product, dia_m / M_PER_IN, tag=tag, length_m=axis.length)
        stub = _stub_m(model, outlet, [axis for _, axis in legs])
        if stub > 1e-6:
            rows.add("srw_drain", product, dia_m / M_PER_IN, tag=legs[0][0], length_m=stub)
    for (cap, coverage_m), runs in sorted(caps.items()):
        tubes = math.ceil(sum(length for _, length in runs) / coverage_m - 1e-9)
        for i, (tag, _) in enumerate(runs):
            rows.add("srw_cap_adhesive", cap, 0.0, tag=tag, count=tubes if i == 0 else 0)
