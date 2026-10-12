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
    "READING": "#edd5ac",
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
        if obj.tag.startswith("FURN-B-SAUNA-"):
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
        elif obj.tag in {"FX-B-SAUNA-SH", "EQ-B-SAUNA-HTR", "ED-B-SAUNA-JB"}:
            ring = [(x / M_PER_IN, y / M_PER_IN) for x, y in obj.footprint]
            ax.add_patch(PatchPolygon(ring, closed=True, facecolor="#ddd", edgecolor="#555"))
            ax.text(
                sum(x for x, _ in ring) / len(ring),
                sum(y for _, y in ring) / len(ring),
                {"FX-B-SAUNA-SH": '36" shower', "EQ-B-SAUNA-HTR": "Heater", "ED-B-SAUNA-JB": "JB"}[
                    obj.tag
                ],
                ha="center",
                va="center",
                fontsize=7,
            )
    ax.text(
        126 if group else 137.25,
        78,
        'Upper: 42" AFF / 78 × 28' if group else 'Upper: 42" AFF\n78 × 28\n26 × 68" lying envelope',
        ha="center",
        rotation=90 if group else 0,
        fontsize=8,
        bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
    )
    ax.text(161.25, 111, 'Foot deck\n24" AFF', ha="center", fontsize=7)
    ax.text(178.25, 75, '12"\nstep', ha="center", fontsize=7)
    ax.plot([161, 175], [9.5, 9.5], color="#549cce", lw=5)
    ax.text(168, 6, "Window", ha="center", fontsize=8)
    ax.plot([209.75, 209.75], [37.6875, 61.6875], color="white", lw=5)
    ax.text(212, 49, "Door → gym", rotation=90, fontsize=8, ha="center", va="center")
    cleanout = next(c for c in model.drain_cleanouts if c.tag == "CO-B-SAUNA-HEAD")
    x, y = (p / M_PER_IN for p in cleanout.cap_position)
    ax.add_patch(Rectangle((x - 9, y - 9), 18, 18, fill=False, edgecolor="#577b57", linestyle=":"))
    ax.plot(x, y, "o", color="#577b57", markersize=3)
    ax.text(x + 1, y + 1, '18" cap access', fontsize=6)
    drain = next(o for o in model.canvas_objects if o.tag == "FX-B-SAUNA-FD")
    ax.add_patch(
        PatchPolygon(
            [(x / M_PER_IN, y / M_PER_IN) for x, y in drain.footprint],
            fill=False,
            edgecolor="#246c87",
            linestyle=":",
        )
    )
    for run in model.pipe_runs:
        if run.tag in {"PR-B-COND", "PR-B-ERV-COND"}:
            x, y = (coordinate / M_PER_IN for coordinate in run.path[-1])
            ax.plot(x, y, "o", color="#246c87", markersize=3)
    if not group:
        x, y = (coordinate / M_PER_IN for coordinate in drain.position)
        ax.text(
            x,
            y - 8,
            "Lift north deck:\ndrain + 2 air gaps",
            ha="center",
            fontsize=7,
            color="#246c87",
        )
    if group:
        for number, south in enumerate((38.1875, 64.1875, 90.1875), 1):
            occupied(ax, 133.25, south, 18, 26, str(number))
            occupied(ax, 151.25, south, 20, 26, "Feet")
        occupied(ax, 123.75, 11, 22, 26, "4: seat")
        occupied(ax, 145.75, 11, 22, 26, "Legs")
        ax.text(168, -5, "Recliner/pad removed; 3 upper + 1 south lower", ha="center", fontsize=8)
    else:
        occupied(ax, 124.25, 43.1875, 26, 68, "")
        ax.text(
            152.5,
            24,
            "Reader →\n105 / 110 / 112° locks",
            ha="center",
            fontsize=8,
            bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
        )
        ax.text(168, -5, "Separate lying and reading places", ha="center", fontsize=8)
    dimension(ax, (116, 38.1875), (116, 116.1875), '78"', vertical=True)
    dimension(ax, (123.25, 120), (151.25, 120), '28" usable')
    dimension(ax, (123.25, 1), (181.75, 1), '58½"')
    dimension(ax, (185.25, 83), (209.75, 83), '24½" aisle')
    dimension(ax, (181.75, 41), (209.75, 41), '28" aisle')
    ax.set_title("Four seated adults" if group else "Lounging / reading", loc="left", fontsize=13)
    ax.set_xlim(109, 218)
    ax.set_ylim(-10, 127)
    ax.set_aspect("equal")
    ax.axis("off")


def section(ax, model, *, group):
    station = (72 if group else 24) * M_PER_IN
    nodes = (
        sauna_benches(model, "x", station)
        + sauna_finished_ceilings_in_cut(model, "x", station)
        + sauna_heaters_in_cut(model, "x", station)
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
    ax.plot([122.8125, 209.75], [0, 0], color="#333", lw=2)
    ax.plot([122.8125, 209.75], [82.8125, 82.8125], color="#333", lw=1)
    ax.text(200, 85, '82 13/16"\nfinished ceiling', ha="right", fontsize=8)
    if group:
        dimension(ax, (116, 0), (116, 42), '42"', vertical=True)
        dimension(ax, (176, 0), (176, 24), '24"', vertical=True)
        dimension(ax, (127, 42), (127, 82.8125), '40 13/16" headroom', vertical=True)
        occupied(ax, 133.25, 42, 18, 32, "Bather")
        occupied(ax, 151.25, 24, 20, 4, "Feet")
        ax.text(184, 14, '12" step', fontsize=8)
    else:
        dimension(ax, (116, 0), (116, 24), '24"', vertical=True)
        ax.text(145, 47, '110° back\n4" segmented pad', fontsize=8)
        ax.text(156, 34, '22" seat + 22" legs', fontsize=8)
        dimension(ax, (181.75, 5), (192.25, 5), '10½"')
        ax.text(199, 48, '45" heater', ha="center", fontsize=8)
    ax.set_title(
        'Occupied upper / foot deck cut, y=72"' if group else 'Reading position cut, y=24"',
        loc="left",
        fontsize=11,
    )
    ax.set_xlim(109, 218)
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
