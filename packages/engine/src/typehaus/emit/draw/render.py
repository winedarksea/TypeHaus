"""``haus render`` backend — headless plan/section snapshots for the agent eyes loop (#52).

The loop is edit → build → check → *look* → fix. This module turns a ``ResolvedModel`` into
PNG/SVG snapshots Claude reads natively (→ 20 §Agent eyes). Plan and section come straight
from the drawing IR; 3D is the offscreen glTF path (M-later) and degrades gracefully here.
"""

from __future__ import annotations

from pathlib import Path

from typehaus.emit.draw.floorplan import build_floorplan
from typehaus.emit.draw.pdf_writer import write_raster
from typehaus.resolve.model import ResolvedModel


def render_plan(model: ResolvedModel, storey: str, path: Path, dpi: int = 110) -> Path:
    scene = build_floorplan(model, storey)
    return write_raster(scene, path, title=f"plan · {storey}", dpi=dpi)


def render_views(
    model: ResolvedModel, out_dir: Path, view: str = "plan", fmt: str = "png"
) -> list[Path]:
    """Render one view for every storey; returns the written snapshot paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    storeys = [s.tag for s in sorted(model.plan.storeys, key=lambda x: x.elevation.meters)]
    if view == "plan":
        for storey in storeys:
            if not any(w.storey == storey for w in model.walls):
                continue
            written.append(render_plan(model, storey, out_dir / f"plan_{storey}.{fmt}"))
    elif view in ("section", "3d"):
        # Section/3D snapshots build on the M3 sheet + glTF artifact; emit a placeholder
        # marker file so the skills loop degrades without crashing.
        marker = out_dir / f"{view}_unavailable.txt"
        marker.write_text(f"{view} render not available in M2 (needs → 30/#51)\n")
        written.append(marker)
    else:
        raise ValueError(f"unknown view {view!r} (plan|section|3d)")
    return written
