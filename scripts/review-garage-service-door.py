"""Regenerate the service-door swing plan and authored x=99in longitudinal section."""

import runpy
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PlotPolygon
from shapely.affinity import rotate, translate
from shapely.geometry import MultiPoint, box
from shapely.ops import unary_union

from typehaus.emit.draw.details import build_authored_detail_scene
from typehaus.emit.draw.elevation_project import solid_faces
from typehaus.emit.draw.render import write_scene
from typehaus.resolve import resolve
from typehaus.source import load_plan

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "out/garage-service-door-review"
INCH = 0.0254


def main():
    loaded = load_plan(ROOT / "houses/catlin")
    if loaded.plan is None:
        raise RuntimeError(loaded.findings)
    model, findings = resolve(loaded.plan)
    if errors := [f for f in findings if f.severity.value == "error"]:
        raise RuntimeError(errors)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    door = next(o for o in model.openings if o.tag == "D-G-SERVICE")
    hinge = door.swing_clearance[0]
    budget = runpy.run_path(str(ROOT / "houses/catlin/plan/entry_screen_finish_spec.py"))
    half_leaf = budget["DOOR_LEAF_THICKNESS_IN"] / 2
    lever_depth = half_leaf + budget["LEVER_PROJECTION_BUDGET_IN"]
    spindle = door.width_m / INCH - budget["DOOR_BACKSET_IN"]
    closed = unary_union(
        [
            box(0, -half_leaf, door.width_m / INCH, half_leaf),
            box(spindle - budget["LEVER_HINGEWARD_EXTENT_IN"], -lever_depth, spindle, lever_depth),
        ]
    )
    fig, ax = plt.subplots(figsize=(10, 9))
    crop = box(65, 480, 126, 529)
    for element in model.geometry.elements:
        if element.uid.startswith(door.uid):
            continue
        for part in element.parts:
            for solid in part.solids:
                points = [p for face in solid_faces(solid) for p in face]
                if (
                    not points
                    or max(p[2] for p in points) <= 0
                    or min(p[2] for p in points) >= door.height_m
                ):
                    continue
                shape = MultiPoint([(p[0] / INCH, p[1] / INCH) for p in points]).convex_hull
                if shape.geom_type == "Polygon" and shape.intersects(crop):
                    ax.add_patch(
                        PlotPolygon(
                            shape.exterior.coords,
                            facecolor="#c3b7a6",
                            edgecolor="#706b63",
                            linewidth=0.5,
                        )
                    )
    stop = budget["DOOR_STOP_DEGREES"]
    limit = stop + budget["DOOR_STOP_TOLERANCE_DEGREES"]
    for angle, color, alpha in [(a, "#d1e4ed", 0.08) for a in range(int(limit) + 1)] + [
        (0, "#147b92", 0.6),
        (stop, "#147b92", 0.8),
        (limit, "#c46934", 0.6),
    ]:
        pose = translate(rotate(closed, -angle, origin=(0, 0)), hinge[0] / INCH, hinge[1] / INCH)
        ax.add_patch(
            PlotPolygon(pose.exterior.coords, facecolor=color, edgecolor=color, alpha=alpha)
        )
    ax.plot(hinge[0] / INCH, hinge[1] / INCH, "ko")
    ax.text(84, 522, "West hinge x=83in | east jamb x=115in", fontsize=10)
    ax.text(
        85,
        482,
        "90° stop-only (blue), 91° tolerance (orange)\n"
        "Leaf bottom ≥1in above rough sill required; factory dimensions pending",
        fontsize=10,
    )
    ax.annotate(
        "Guard head x=116.5in",
        xy=(116.5, 514.75),
        xytext=(99, 505),
        arrowprops={"arrowstyle": "->"},
        fontsize=10,
    )
    ax.set(
        xlim=(65, 126),
        ylim=(480, 529),
        aspect="equal",
        xlabel="Project x (in)",
        ylabel="Project y (in)",
        title="D-G-SERVICE — 32in Masonite outswing / retained brick screen",
    )
    ax.grid(alpha=0.2)
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        fig.savefig(OUTPUT / f"door-plan.{suffix}", dpi=180)
    plt.close(fig)
    section = model.plan.by_tag("SL-D-NORTH-BRIDGE")
    scene = build_authored_detail_scene(model, section)
    for suffix in ("png", "svg", "pdf"):
        write_scene(scene, OUTPUT / f"door-section.{suffix}", section.title, 160, long_edge=2400)
    print(OUTPUT)


if __name__ == "__main__":
    main()
