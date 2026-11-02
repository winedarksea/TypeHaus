"""Recalculate the direct-mounted MDO screen through normal house load consumers."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "houses/catlin"))
from plan.entry_screen_finish_spec import (  # noqa: E402
    HARDWARE_AND_PAINT_RESERVE_LB,
    PANEL_RUNS_IN,
    SUPPORT_WEIGHT_LB,
)

from typehaus.checks.run import build_context  # noqa: E402
from typehaus.engineering.pier_basis import wall_line_loads  # noqa: E402
from typehaus.resolve.assembly_weight import dead_load_plf, wall_line_plf  # noqa: E402
from typehaus.source import load_plan  # noqa: E402

house = ROOT / "houses/catlin"
loaded = load_plan(house)
if loaded.plan is None:
    raise RuntimeError(loaded.findings)
context, _ = build_context(loaded.plan, house)
wall = context.model.wall("W-BW-SCREEN")
report = {
    "panel_cuts_in": [{"width": b - a, "height": 45.5, "quantity": 1} for a, b in PANEL_RUNS_IN],
    "support_weight_lb": SUPPORT_WEIGHT_LB,
    "hardware_and_paint_reserve_lb": HARDWARE_AND_PAINT_RESERVE_LB,
    "wall_dead_load_plf": dead_load_plf(context, wall, wall.z1_m - wall.z0_m),
    "wall_and_upper_band_plf": wall_line_plf(context, wall)[0],
    "wall_reaction_lb": wall_line_loads(context.engineering.context)[0],
    "structural_records": [
        {
            "key": f"{r.kind}/{r.key}",
            "status": r.status.value,
            "ratio": r.governing.ratio if r.governing else None,
        }
        for r in context.engineering.values()
        if any("BW" in tag for tag in r.element_tags)
    ],
}
print(json.dumps(report, indent=2))
