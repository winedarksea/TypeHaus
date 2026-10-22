#!/usr/bin/env python3
"""Render the selected Bath2 tub hardware from resolved geometry (in inches)."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

from typehaus.model.placeable_symbols import model_parts, place_local, plan_symbol_strokes
from typehaus.model.placeable_symbols._kohler_underscore_rect import (
    BASIN_TOP_DEPTH_IN,
    BASIN_TOP_WIDTH_IN,
)
from typehaus.model.placeable_symbols._roman_tub_filler import (
    HANDLE_CENTRES_IN,
    SPOUT_BASE_DIAMETER_IN,
)
from typehaus.quantities import M_PER_IN as IN
from typehaus.resolve import resolve
from typehaus.resolve.room_floor import room_finished_floor_elevation
from typehaus.source import load_plan

HOUSE = Path(__file__).resolve().parents[1] / "houses" / "catlin"
INK, BLUE, SILVER = "#29444b", "#457b94", "#d9e1e5"
matplotlib.rcParams.update({"svg.hashsalt": "catlin-bath2-tub-hardware", "font.size": 10})


def dimension(ax, a, b, label, *, vertical=False):
    ax.annotate("", b, a, arrowprops={"arrowstyle": "|-|", "color": BLUE, "lw": 0.8})
    x, y = ((a[i] + b[i]) / 2 for i in (0, 1))
    ax.text(x - 0.8 if vertical else x, y if vertical else y + 0.8, label,
            ha="right" if vertical else "center", va="center" if vertical else "bottom",
            rotation=90 if vertical else 0, fontsize=9, color=INK,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})


def bounds(obj):
    xs, ys = zip(*obj.footprint, strict=True)
    return min(xs) / IN, min(ys) / IN, max(xs) / IN, max(ys) / IN


def glyph(ax, obj, catalog):
    for stroke in plan_symbol_strokes(catalog.plan_symbol, *(d.meters for d in catalog.footprint)):
        points = place_local(stroke["points"], obj.position, obj.rotation_degrees)
        if stroke["closed"]:
            points.append(points[0])
        ax.plot([x / IN for x, _ in points], [y / IN for _, y in points], color=INK, lw=1)


def plan_view(ax, model, tub, filler, bars, types):
    slab = model.plan.by_tag("SL-M-TUBDK")
    ax.add_patch(Polygon([(p.x.inches, p.y.inches) for p in slab.outline],
                         fc="#f1eee7", ec="#adab9e"))
    for wall in model.walls:
        if wall.tag in {"W-M-BA2E", "W-M-BA2E2", "W-M-HS2", "W-M-TUBDK-W", "W-M-TUBDK-S"}:
            for layer in wall.layers:
                ax.add_patch(Polygon([(x / IN, y / IN) for x, y in layer.polygon],
                                     fc="#e0dfd9", ec="#b6b5ae", lw=0.3))
    x0, y0, x1, y1 = bounds(tub)
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="white", ec=INK, lw=1.3))
    cx, cy = (v / IN for v in tub.position)
    ax.add_patch(Rectangle((cx - BASIN_TOP_DEPTH_IN / 2, cy - BASIN_TOP_WIDTH_IN / 2),
                           BASIN_TOP_DEPTH_IN, BASIN_TOP_WIDTH_IN, fc="#edf5f7", ec=BLUE))
    # Service: the heater-end leaf and Bask outlet (north), the foot leaf (south).
    for tag in ("FURN-M-BATH2-TUBDK-AP-N", "FURN-M-BATH2-TUBDK-AP", "ED-M-BATH2-TUB-RC"):
        part = next(c for c in model.canvas_objects if c.tag == tag)
        px0, py0, px1, py1 = bounds(part)
        ax.add_patch(Rectangle((px0, py0), px1 - px0, py1 - py0, fc=BLUE, ec=BLUE))
    ax.text(cx, cy + 24, "heater end", color=BLUE, ha="center", fontsize=8)
    ax.plot([tub.position[0] / IN] * 2, [197, 267], color=BLUE, lw=0.7, ls="--")
    for bar in bars:
        bx0, by0, bx1, by1 = bounds(bar)
        ax.add_patch(Rectangle((bx1 - 4.5, by0), 4.5, by1 - by0,
                               fc="#cce4ee", ec=BLUE, ls="--", alpha=0.65))
        glyph(ax, bar, types[bar.type_ref])
    glyph(ax, filler, types[filler.type_ref])
    filler_type = types[filler.type_ref]
    hole_y = filler_type.footprint[1].inches / 2 - SPOUT_BASE_DIAMETER_IN / 2
    holes = place_local([(x * IN, hole_y * IN) for x in (-HANDLE_CENTRES_IN / 2, 0,
                                                                      HANDLE_CENTRES_IN / 2)],
                        filler.position, filler.rotation_degrees)
    ax.scatter([x / IN for x, y in holes], [y / IN for x, y in holes], s=14, color=BLUE)
    ax.text(68, 235, "Kohler Underscore\nK-1130-W1-0", color=INK, ha="center", fontsize=9,
            rotation=90)
    ax.annotate('Hole line y = 200.41"\n10" handle centres', (holes[1][0] / IN, holes[1][1] / IN),
                (55, 190), color=INK, fontsize=9, arrowprops={"arrowstyle": "-", "color": BLUE})
    dimension(ax, (x0, 272), (x1, 272), f'{x1 - x0:g}" rim')
    dimension(ax, (49, y0), (49, y1), f'{y1 - y0:g}" rim', vertical=True)
    ax.text(95.8, 234, "EAST WALL", rotation=90, color=INK, ha="center")
    ax.text(79, 265, f'CL x = {tub.position[0] / IN:g}"', color=BLUE, fontsize=9)
    ax.set(xlim=(44, 102), ylim=(185, 278), xlabel="House x (inches)", ylabel="House y (inches)")
    ax.set_title("PLAN · north up", loc="left", fontweight="bold", color=INK)


def east_elevation(ax, model, tub, filler, bars, types, floor):
    _, south, _, north = bounds(tub)
    rim = (tub.body_z1_m - floor) / IN
    ax.add_patch(Rectangle((south - 5.05, 0), north - south + 7.05, rim,
                           fc="#f1eee7", ec="#adab9e"))
    ax.add_patch(Rectangle((south, rim - 0.375), north - south, 0.375,
                           fc="white", ec=INK, lw=1.2))
    ax.plot([195, 266], [0, 0], color=INK, lw=1)
    ax.plot([tub.position[1] / IN] * 2, [0, 60], color=BLUE, lw=0.7, ls="--")
    for bar in bars:
        _, lo, _, hi = bounds(bar)
        center = (bar.z_m + 0.67 * IN - floor) / IN
        ax.add_patch(Rectangle((lo + 1.67, center - 28), hi - lo - 3.34, 28,
                               fc="#cce4ee", ec=BLUE, lw=0.8))
        ax.add_patch(Rectangle((lo, center - 0.67), hi - lo, 1.34, fc=SILVER, ec=INK, lw=0.8))
        for y in (bar.position[1] / IN - 12, bar.position[1] / IN + 12):
            ax.plot(y, center, "o", ms=3, color=INK)
        ax.text(bar.position[1] / IN, 57, "24\" Align", ha="center", color=INK, fontsize=9)
    trim = types[filler.type_ref]
    for part in model_parts(trim.plan_symbol, *(d.meters for d in trim.footprint), trim.height.meters):
        cx, cy, cz = part["center"]
        dx, dy, dz = part["size"]
        corners = place_local([(cx - dx / 2, cy - dy / 2), (cx + dx / 2, cy + dy / 2)],
                              filler.position, filler.rotation_degrees)
        lo, hi = sorted(p[1] / IN for p in corners)
        z = (filler.z_m + cz - dz / 2 - floor) / IN
        ax.add_patch(Rectangle((lo, z), hi - lo, dz / IN, fc=SILVER, ec=INK, lw=0.7))
    dimension(ax, (269, 0), (269, 54), '54" bar centres AFF', vertical=True)
    dimension(ax, (274, rim), (274, 26), f'{26 - rim:g}" towel / rim gap', vertical=True)
    dimension(ax, (south, -5), (north, -5), f'{north - south:g}" tub')
    south_edge, north_edge = bounds(bars[0])[3], bounds(bars[1])[1]
    dimension(ax, (south_edge, 62), (north_edge, 62), f'{north_edge - south_edge:.2f}" gap')
    ax.text(210, 10, "Existing tub enclosure", color=INK, fontsize=10)
    ax.text(199, 31, "T393", color=INK, fontsize=9)
    ax.set(xlim=(193, 279), ylim=(-8, 67), xlabel="House y (inches) · south → north",
           ylabel="Above finished floor (inches)")
    ax.set_title("EAST WALL · viewed from aisle", loc="left", fontweight="bold", color=INK)


def main():
    model, _ = resolve(load_plan(HOUSE).plan)
    objects = {o.tag: o for o in model.canvas_objects}
    types = {t.tag: t for catalog in (model.plan.library.fixture_types,
                                     model.plan.library.furniture_types) for t in catalog}
    tub, filler = (objects[tag] for tag in ("FX-M-BATH2-TUB", "FX-M-BATH2-FILLER"))
    bars = [objects["FURN-M-BATH2-TUB-TOWEL-" + end] for end in ("S", "N")]
    room = next(r for r in model.rooms if r.tag == tub.room)
    floor = room_finished_floor_elevation(model, room)
    fig, axes = plt.subplots(1, 2, figsize=(14, 8), gridspec_kw={"width_ratios": [1, 1.5]})
    plan_view(axes[0], model, tub, filler, bars, types)
    east_elevation(axes[1], model, tub, filler, bars, types, floor)
    for ax in axes:
        ax.set_aspect("equal")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=8)
    fig.suptitle("BATH2 · centered Moen Align filler + twin chrome towel bars",
                 fontsize=17, fontweight="bold", color=INK, x=0.07, ha="left")
    fig.text(0.07, 0.08, 'Blue: towels with 28" hanging drop / 4½" projection. Silver: chrome hardware. '
             'All dimensions follow the resolved model.', fontsize=10, color=INK)
    fig.text(0.07, 0.045, 'Drilling: delivered Moen trim + Kohler template govern. '
             'Retain service access and an ASSE 1070 temperature-limiting device.', fontsize=10, color=INK)
    fig.subplots_adjust(left=0.07, right=0.97, bottom=0.18, top=0.88, wspace=0.30)
    target = HOUSE / "notes/assets/bath2_tub_hardware_review"
    fig.savefig(target.with_suffix(".svg"), metadata={"Date": None})
    fig.savefig(target.with_suffix(".png"), dpi=160)
    plt.close(fig)
    print(target.with_suffix(".svg"))


if __name__ == "__main__":
    main()
