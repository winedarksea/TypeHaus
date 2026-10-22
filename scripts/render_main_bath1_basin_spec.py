#!/usr/bin/env python3
"""Render the powder-room layout and basin support from the resolved Catlin model."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

from typehaus.model.placeable_symbols import place_local, symbol_geometry
from typehaus.quantities import M_PER_IN as IN
from typehaus.resolve import resolve
from typehaus.source import load_plan

HOUSE = Path(__file__).resolve().parents[1] / "houses" / "catlin"
matplotlib.rcParams["svg.hashsalt"] = "catlin-powder-basin"


def dimension(ax, start, end, label, *, vertical=False):
    ax.annotate("", end, start, arrowprops={"arrowstyle": "|-|", "color": "#42616a"})
    x, y = ((a + b) / 2 for a, b in zip(start, end, strict=True))
    ax.text(x - 1 if vertical else x, y if vertical else y + 1, label,
            rotation=90 if vertical else 0, ha="right" if vertical else "center",
            va="center" if vertical else "bottom", fontsize=9,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})


def bounds(obj):
    xs, ys = zip(*[(x / IN, y / IN) for x, y in obj.footprint], strict=True)
    return min(xs), max(xs), min(ys), max(ys)


def plan_view(ax, model, basin, toilet):
    room = next(r for r in model.rooms if r.tag == "RM-M-BATH1")
    for wall in model.walls:
        if wall.tag in {"W-M-HS1", "W-M-W2", "W-M-STOS", "W-M-BAE"}:
            for layer in wall.layers:
                ax.add_patch(Polygon([(x / IN, y / IN) for x, y in layer.polygon],
                                     facecolor="#dddcd6", edgecolor="#888", lw=0.4))
    door = next(o for o in model.openings if o.tag == "D-M-BATH1")
    south = min(y for _, y in door.swing_clearance) / IN
    north = max(y for _, y in door.swing_clearance) / IN
    ax.add_patch(Rectangle((69.6, south), 4.8, north - south, color="white"))
    swing = [(x / IN, y / IN) for x, y in door.swing_clearance]
    ax.plot(*zip(*swing, strict=True), color="#486275", lw=1)
    ax.plot([72, 104], [south, south], color="#486275", lw=2)
    types = {t.tag: t for t in model.plan.library.fixture_types}
    for obj in (basin, toilet):
        catalog = types[obj.type_ref]
        ax.add_patch(Polygon([(x / IN, y / IN) for x, y in obj.footprint],
                             facecolor="#edf4f5", edgecolor="#9cbbbf", lw=0.7))
        strokes, _ = symbol_geometry(catalog.plan_symbol,
                                     *(d.meters for d in catalog.footprint),
                                     obj.body_z1_m - obj.body_z0_m)
        for stroke in strokes:
            points = place_local(stroke["points"], obj.position, obj.rotation_degrees)
            ax.plot([x / IN for x, _ in points], [y / IN for _, y in points],
                    color="#35565b", lw=0.8)
    x0, x1, y0, y1 = bounds(basin)
    tx0, tx1, _, ty1 = bounds(toilet)
    room_north = max(y for _, y in room.clear_face) / IN
    dimension(ax, (65, y1), (65, room_north), f'{room_north - y1:.2f}" aisle', vertical=True)
    dimension(ax, (17, ty1), (17, room_north), f'{room_north - ty1:.2f}"', vertical=True)
    dimension(ax, ((tx0 + tx1) / 2, 267), ((x0 + x1) / 2, 267), '30.125" centers')
    ax.text(27, 288, "TOTO AP", ha="center", fontsize=8)
    ax.text((x0 + x1) / 2, 278, "D-Code", ha="center", fontsize=8)
    ax.text(88, 304, 'INT32\noutswing\n32" modeled RO', ha="center", fontsize=9)
    ax.text(8, 322, "N ↑", fontsize=10)
    ax.text(43, 260, "Shared wet wall W-M-HS1", ha="center", fontsize=9)
    # An occupied position illustrates scale, not a swept-path or transfer validation.
    ax.add_patch(Rectangle((14, 292.9), 48, 24, fill=False, linestyle="--",
                           edgecolor="#aa864c", lw=0.9))
    ax.text(38, 307, '24 × 48" chair outline\nillustrative parked position',
            fontsize=8, ha="center", color="#87672f")
    ax.set(xlim=(2, 108), ylim=(256, 328), aspect="equal")
    ax.set_title("South-wall layout · north is up", fontsize=12, loc="left")
    ax.axis("off")


def support_view(ax, model, basin):
    wall = next(w for w in model.walls if w.tag == "W-M-HS1")
    block = next(m for m in wall.members
                 if m.child_key.startswith("backing-") and m.profile == "2x10")
    for stud in wall.members:
        x = stud.p0[0] / IN
        if stud.category == "stud" and 44 < x < 67:
            north = stud.p0[1] > 268 * IN
            ax.add_patch(Rectangle((x - 0.75, 15), 1.5, 33, facecolor="#f2e3c8",
                                   edgecolor="#b4976a", linestyle="-" if north else "--"))
    x = min(block.p0[0], block.p1[0]) / IN
    ax.add_patch(Rectangle((x, block.z0_m / IN), block.length_m / IN,
                           (block.z1_m - block.z0_m) / IN,
                           facecolor="#dec393", edgecolor="#775c2e"))
    x0, x1, _, _ = bounds(basin)
    center = (x0 + x1) / 2
    height = (basin.body_z0_m + 0.145 - 0.055) / IN
    for fixing in (center - 120 / 25.4, center + 120 / 25.4):
        ax.add_patch(Rectangle((fixing - 1, height - 1), 2, 2,
                               facecolor="#d4d9dc", edgecolor="#555"))
        ax.plot(fixing, height, "+", color="#222")
    dimension(ax, (center - 120 / 25.4, 40), (center + 120 / 25.4, 40), "240 mm fixings")
    ax.add_patch(Rectangle((x0, basin.body_z0_m / IN), x1 - x0, 145 / 25.4,
                           fill=False, edgecolor="#35565b", linestyle="--"))
    ax.text(center, 30, '2 × 10 solid block\n1½" deep × 9¼" high',
            ha="center", fontsize=8)
    ax.text(45, 45, 'North stud row: x=48 / 64"\nDashed stud: opposing row at x=56"',
            fontsize=8)
    ax.text(45, 21, 'Services run behind block.\nNo fixing or service bore crosses it.\n'
            'Heights shown above main storey datum.',
            fontsize=8)
    ax.set(xlim=(44, 68), ylim=(15, 49), aspect="equal")
    ax.set_title("Basin fixing support · view south", fontsize=12, loc="left")
    ax.set_xlabel("x, inches from west wall axis")
    ax.set_ylabel("Inches above main datum")
    ax.spines[["top", "right"]].set_visible(False)


def main():
    result = load_plan(HOUSE)
    assert result.plan is not None, result.findings
    model, _ = resolve(result.plan)
    objects = {o.tag: o for o in model.canvas_objects}
    basin, toilet = (objects[f"FX-M-BATH1-{suffix}"] for suffix in ("LAV", "WC"))
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6), gridspec_kw={"width_ratios": [2.1, 1]})
    plan_view(axes[0], model, basin, toilet)
    support_view(axes[1], model, basin)
    fig.suptitle("RM-M-BATH1 · roomier basin on shared south plumbing wall", fontsize=15)
    fig.text(0.04, 0.02, 'INT32 is a framed opening, not 32" finished clear. '
             'No wheelchair turning or transfer claim. '
             'Fixture symbols are schematic; use manufacturer drawings for installation.',
             fontsize=8)
    fig.tight_layout(rect=(0.01, 0.06, 0.99, 0.94))
    for extension in ("svg", "png"):
        path = HOUSE / "notes" / "assets" / f"main_bath1_basin_spec.{extension}"
        fig.savefig(path, dpi=160, metadata={"Date": None} if extension == "svg" else None)
        print(path)


if __name__ == "__main__":
    main()
