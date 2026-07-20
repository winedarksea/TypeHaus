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
    elif view == "3d":
        # 3D is the offscreen glTF artifact (#51): emit a self-contained .glb the UI panel
        # and a glTF viewer both read. A raster snapshot needs an offscreen GL context (M3);
        # the .glb is the durable artifact the agent-eyes loop and UI share.
        from typehaus.emit.gltf import emit_glb

        lod = "framed" if any(w.members for w in model.walls) else "core"
        written.append(emit_glb(model, out_dir / "model.glb", lod=lod))
    elif view == "section":
        from typehaus.emit.draw.pdf_writer import write_raster
        from typehaus.emit.draw.section import build_center_section

        written.append(write_raster(build_center_section(model), out_dir / f"section_house.{fmt}",
                                    title="section · house center"))
    elif view == "details":
        from typehaus.emit.draw.details import build_detail, derive_detail_slices
        from typehaus.emit.draw.pdf_writer import write_raster

        for derived in derive_detail_slices(model):
            scene, _findings = build_detail(model, derived)
            slug = derived.view.tag.replace("/", "_")
            written.append(write_raster(scene, out_dir / f"detail_{slug}.{fmt}",
                                        title=f"detail · {derived.key}"))
    else:
        raise ValueError(f"unknown view {view!r} (plan|section|3d|details)")
    return written
