#!/usr/bin/env python3
"""Rebuild the dimensioned seating review from Catlin's resolved furniture and sections."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PatchPolygon
from matplotlib.patches import Rectangle

from typehaus.emit.draw.detail_components.sauna_seating import (
    sauna_benches,
    sauna_finished_ceilings_in_cut,
    sauna_heaters_in_cut,
)
from typehaus.model.placeable_symbols import place_local, symbol_geometry
from typehaus.quantities import M_PER_IN
from typehaus.resolve import resolve
from typehaus.source import load_plan

matplotlib.rcParams["svg.hashsalt"] = "catlin-sauna-seating-review"
HOUSE = Path(__file__).resolve().parents[1] / "houses" / "catlin"
COLORS = {
    "UPPER": "#d1a66f",
    "LOWER": "#edd5ac",
    "STEP": "#c2ab8a",
    "RECLINER": "#ad8051",
    "MATTRESS": "#eee9dc",
}


def dimension(ax, start, end, label, *, vertical=False):
    ax.annotate("", end, start, arrowprops={"arrowstyle": "|-|", "color": "#333", "lw": 0.8})
    x, y = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
    ax.text(
        x - 1 if vertical else x,
        y if vertical else y + 1.5,
        label,
        ha="right" if vertical else "center",
        va="center" if vertical else "bottom",
        rotation=90 if vertical else 0,
        fontsize=8,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 1},
    )


def occupied(ax, x, y, width, depth, label):
    ax.add_patch(
        Rectangle(
            (x, y),
            width,
            depth,
            facecolor="#539db0",
            edgecolor="#17657a",
            alpha=0.35,
            linestyle="--",
        )
    )
    ax.text(x + width / 2, y + depth / 2, label, fontsize=8, ha="center", va="center")


def plan(ax, model, *, group):
    room = next(r for r in model.rooms if r.tag == "RM-B-SAUNA")
    ax.add_patch(
        PatchPolygon(
            [(x / M_PER_IN, y / M_PER_IN) for x, y in room.clear_face],
            closed=True,
            fill=False,
            edgecolor="#333",
            lw=2,
        )
    )
    types = {t.tag: t for t in model.plan.library.furniture_types}
    for obj in model.canvas_objects:
        # FURN-B-SAUNA-BATH-TOWEL is the bath's towel bar, not seating.
        if obj.tag.removeprefix("FURN-B-SAUNA-") in COLORS and obj.tag.startswith("FURN-B-SAUNA-"):
            suffix = obj.tag.removeprefix("FURN-B-SAUNA-")
            if group and suffix in {"RECLINER", "MATTRESS"}:
                continue
            ring = [(x / M_PER_IN, y / M_PER_IN) for x, y in obj.footprint]
            ax.add_patch(
                PatchPolygon(
                    ring,
                    closed=True,
                    facecolor=COLORS[suffix],
                    edgecolor="#78613f",
                    lw=0.7,
                    alpha=0.8,
                )
            )
            if suffix in {"RECLINER", "MATTRESS"}:
                catalog = types[obj.type_ref]
                strokes, _ = symbol_geometry(
                    catalog.plan_symbol,
                    *(d.meters for d in catalog.footprint),
                    obj.body_z1_m - obj.body_z0_m,
                )
                for stroke in strokes:
                    points = place_local(stroke["points"], obj.position, obj.rotation_degrees)
                    ax.plot(
                        [x / M_PER_IN for x, _ in points],
                        [y / M_PER_IN for _, y in points],
                        color="#78613f",
                        lw=0.7,
                    )
        elif obj.tag in {"EQ-B-SAUNA-HTR", "ED-B-SAUNA-JB"}:
            ring = [(x / M_PER_IN, y / M_PER_IN) for x, y in obj.footprint]
            ax.add_patch(PatchPolygon(ring, closed=True, facecolor="#ddd", edgecolor="#555"))
            ax.text(
                sum(x for x, _ in ring) / len(ring),
                sum(y for _, y in ring) / len(ring),
                {"EQ-B-SAUNA-HTR": "Heater", "ED-B-SAUNA-JB": "JB"}[obj.tag],
                ha="center",
                va="center",
                fontsize=7,
            )
    ax.text(
        126 if group else 137.25,
        50,
        'Upper: 42" AFF / 80 9/16 × 28' if group else 'Upper: 42" AFF\n80 9/16 × 28\n26 × 68" lying envelope',
        ha="center",
        va="center",
        rotation=90 if group else 0,
        fontsize=8,
        bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
    )
    ax.text(165.25, 79, 'Lower deck\n24" AFF', ha="center", va="center", fontsize=7)
    ax.text(186.25, 73, '12"\nstep', ha="center", va="center", fontsize=7)
    ax.plot([161, 175], [9.5, 9.5], color="#549cce", lw=5)
    ax.text(168, 5, "Window", ha="center", fontsize=8)
    ax.plot([209.75, 209.75], [51, 75], color="white", lw=5)
    ax.text(212.5, 63, "Door → gym", rotation=90, fontsize=8, ha="center", va="center")
    drain = next(o for o in model.canvas_objects if o.tag == "FX-B-SAUNA-FD")
    ax.add_patch(
        PatchPolygon(
            [(x / M_PER_IN, y / M_PER_IN) for x, y in drain.footprint],
            fill=False,
            edgecolor="#246c87",
            linestyle=":",
        )
    )
    # The condensate air gap ends over the drain, so one dot marks both.
    for run in model.pipe_runs:
        if run.tag == "PR-B-COND":
            x, y = (coordinate / M_PER_IN for coordinate in run.path[-1])
            ax.plot(x, y, "o", color="#246c87", markersize=3)
    if not group:
        x, y = (coordinate / M_PER_IN for coordinate in drain.position)
        ax.text(x, y + 9, "Drain + air gap", ha="center", fontsize=7, color="#246c87")
    if group:
        # Recliner and pad lifted off; three seats on 26" runs, feet on the lower deck.
        for number, south in enumerate((11.28, 37.28, 63.28), 1):
            occupied(ax, 133.25, south, 18, 26, str(number))
            occupied(ax, 151.25, south, 20, 26, "Feet")
        ax.text(168, -5, "Recliner/pad removed; 3 seated on the upper bench", ha="center", fontsize=8)
    else:
        occupied(ax, 124.25, 16.28, 26, 68, "")
        ax.text(
            165.25,
            40,
            "Reader ↑\n105 / 110 / 112° locks",
            ha="center",
            fontsize=8,
            bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
        )
        ax.text(168, -5, "Separate lying and reading places", ha="center", fontsize=8)
    dimension(ax, (116, 10), (116, 90.5625), '80 9/16"', vertical=True)
    dimension(ax, (123.25, 95), (151.25, 95), '28" usable')
    dimension(ax, (151.25, 95), (179.25, 95), '28" deck')
    dimension(ax, (179.25, 45), (210, 45), '30 3/4" aisle')
    dimension(ax, (179.25, 36), (192.25, 36), '13" to heater')
    ax.set_title("Three seated adults" if group else "Lounging / reading", loc="left", fontsize=13)
    ax.set_xlim(109, 218)
    ax.set_ylim(-10, 103)
    ax.set_aspect("equal")
    ax.axis("off")


def section(ax, model, *, group):
    # Group: across the benches at y=72 (u = x). Reading: along the recliner at x=165.25 (u = y).
    direction, station_in = ("x", 72) if group else ("y", 165.25)
    station = station_in * M_PER_IN
    nodes = (
        sauna_benches(model, direction, station)
        + sauna_finished_ceilings_in_cut(model, direction, station)
        + sauna_heaters_in_cut(model, direction, station)
    )
    floor = next(s.z1_m for s in model.solids if s.tag == "SL-B-FLOOR") / M_PER_IN
    for node in nodes:
        if node.node != "polyline":
            continue
        points = [(x, z - floor) for x, z in node.points]
        tag = getattr(node, "tag", "")
        color = "#eee9dc" if tag.endswith("mattress") else "#d1a66f"
        if tag.endswith("heater"):
            ax.add_patch(
                PatchPolygon(points, closed=True, fill=False, edgecolor="#666", linestyle="--")
            )
        else:
            ax.add_patch(
                PatchPolygon(points, closed=True, facecolor=color, edgecolor="#78613f", lw=0.5)
            )
    lo, hi = (122.5, 210) if group else (9.25, 90.75)
    ceiling = 84.0625
    ax.plot([lo, hi], [0, 0], color="#333", lw=2)
    ax.plot([lo, hi], [ceiling, ceiling], color="#333", lw=1)
    ax.text(hi - 2, ceiling + 2, '84 1/16"\nfinished ceiling', ha="right", fontsize=8)
    if group:
        dimension(ax, (116, 0), (116, 42), '42"', vertical=True)
        dimension(ax, (183, 0), (183, 24), '24"', vertical=True)
        dimension(ax, (127, 42), (127, ceiling), '42 1/16" headroom', vertical=True)
        occupied(ax, 133.25, 42, 18, 32, "Bather")
        occupied(ax, 151.25, 24, 20, 4, "Feet")
        ax.text(186, 14, '12" step', fontsize=8)
        ax.set_xlim(109, 218)
    else:
        dimension(ax, (3, 0), (3, 24), '24"', vertical=True)
        ax.text(52, 48, '110° back\n4" segmented pad', fontsize=8)
        ax.text(22, 40, '22" seat + 22" legs', fontsize=8)
        ax.text(76, 28, "Head north", fontsize=8)
        ax.set_xlim(-2, 98)
    ax.set_title(
        'Occupied upper / lower deck cut, y=72"'
        if group
        else 'Reading position cut, x=165 1/4" (south to north)',
        loc="left",
        fontsize=11,
    )
    ax.set_ylim(-4, 102)
    ax.set_aspect("equal")
    ax.axis("off")


def main():
    result = load_plan(HOUSE)
    assert result.plan is not None, result.findings
    model, findings = resolve(result.plan)
    assert not [f for f in findings if f.severity.value == "error"]
    fig, axes = plt.subplots(2, 2, figsize=(13, 16), gridspec_kw={"height_ratios": [1.25, 1]})
    for column, group in enumerate((False, True)):
        plan(axes[0, column], model, group=group)
        section(axes[1, column], model, group=group)
    fig.suptitle("Catlin sauna • seating coordination • inches / AFF", fontsize=16)
    fig.text(
        0.5,
        0.02,
        "Heat qualification and full-size comfort trial required before fabrication.\n"
        "Heater fence and installed junction-box access: see sauna_seating.md.",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.96))
    target = HOUSE / "notes" / "assets"
    target.mkdir(exist_ok=True)
    for extension in ("svg", "png"):
        path = target / f"sauna_seating_review.{extension}"
        fig.savefig(path, dpi=140, metadata={"Date": None} if extension == "svg" else None)
        print(path)


if __name__ == "__main__":
    main()
