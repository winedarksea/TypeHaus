"""Regenerate the service-door swing plan and authored x=99in longitudinal section."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PlotPolygon
from shapely.affinity import rotate, translate
from shapely.geometry import MultiPoint, box

from typehaus.emit.draw.details import build_authored_detail_scene
from typehaus.emit.draw.elevation_project import solid_faces
from typehaus.emit.draw.render import write_scene
from typehaus.resolve import resolve
from typehaus.resolve.door_swing_envelope import assembly_components, clearance_results
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
    wall = model.wall(door.host_wall)
    hinge, components = assembly_components(wall, door)
    hinge_inches = tuple(value / INCH for value in hinge)
    stop = model.plan.by_tag(door.tag).maximum_opening_degrees
    limit = stop + door.swing_assembly.stop_tolerance_degrees
    results = clearance_results(model, door, stop)
    for result in results:
        if result.clearance_m < door.swing_assembly.minimum_clearance.meters:
            print(f"CONFLICT {result.component} / {result.obstacle} / {result.part}: "
                  f"{result.clearance_m / INCH:.3f}in at {result.angle_interval_degrees}deg")
    if results:
        nearest = results[0]
        print(f"MINIMUM {nearest.component} / {nearest.obstacle} / {nearest.part}: "
              f"{nearest.clearance_m / INCH:.3f}in at {nearest.angle_interval_degrees}deg")
    print("SUPPLIER CONFIRMED:", door.swing_assembly.supplier_confirmed)
    fig, ax = plt.subplots(figsize=(10, 9))
    crop = box(65, 480, 126, 529)
    hold_down = model.plan.by_tag("CN-G-BWHD-S-DR")
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
                    if element.uid == hold_down.uid:
                        study = translate(shape, xoff=1.5)
                        ax.add_patch(PlotPolygon(study.exterior.coords, fill=False,
                                                 edgecolor="#c13030", linestyle="--",
                                                 linewidth=2))
    for angle, color, alpha in [(a, "#d1e4ed", 0.08) for a in range(int(limit) + 1)] + [
        (0, "#147b92", 0.6), (stop, "#147b92", 0.8), (limit, "#c46934", 0.6),
    ]:
        for component in components:
            pose = rotate(component.closed, -angle, origin=hinge)
            polygons = list(pose.geoms) if pose.geom_type == "MultiPolygon" else [pose]
            for polygon in polygons:
                coords = [(x / INCH, y / INCH) for x, y in polygon.exterior.coords]
                ax.add_patch(PlotPolygon(coords, facecolor=color, edgecolor=color, alpha=alpha))
    ax.plot(*hinge_inches, "ko")
    ax.text(84, 522, f"SCHEMATIC hinge x={hinge_inches[0]:.2f}in; supplier section pending",
            fontsize=9)
    ax.text(85, 482, "90° stop-only (blue), 91° tolerance (orange)\n"
            "Leaf bottom ≥1in above rough sill required; factory dimensions pending", fontsize=10)
    ax.annotate("Dashed: +1.5in strap study only\nFraming and anchorage unapproved",
                xy=(117.25, 521.5), xytext=(94, 526), fontsize=8,
                arrowprops={"arrowstyle": "->", "color": "#c13030"})
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
