#!/usr/bin/env python3
"""Render BATH2's centred shower drain and its FS-M-WEST joist bay from resolved geometry.

Plan (x, y) and a section on the drain's x looking east (y, z). Inches, main-storey datum.
"""

from itertools import pairwise
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle
from shapely.geometry import Point, box
from shapely.geometry import Polygon as Area

from typehaus.quantities import M_PER_IN as IN
from typehaus.resolve import resolve
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section
from typehaus.source import load_plan

HOUSE = Path(__file__).resolve().parents[1] / "houses" / "catlin"
INK, BLUE, RED, WOOD, GREY = "#29444b", "#457b94", "#b4473a", "#e9d8b8", "#d9dcde"
GREEN = "#7fb39f"
COLOURS = {"drain": "#6b4f2a", "vent": "#8a7a5a", "water_hot": RED, "water_cold": BLUE}
PLAN_X, PLAN_Y, SECTION_Z = (58, 112), (150, 202), (-27, 4)
matplotlib.rcParams.update({"svg.hashsalt": "catlin-bath2-shower-drain", "font.size": 9})


def _in(points):
    return [(x / IN, y / IN) for x, y in points]


def _colour(run):
    return COLOURS.get(str(getattr(run.system, "value", run.system)), GREY)


def plan_view(ax, floor, joists, fixture, opening, runs, cleanout):
    ax.add_patch(Polygon(_in(fixture.footprint), fc="#f4f7f8", ec=INK, lw=1.2))
    for joist in joists:
        ring, _, _ = member_footprint(joist)
        ax.add_patch(Polygon(_in(ring), fc=WOOD, ec="#a08a5f", lw=0.6))
        ax.text(PLAN_X[0] + 1, joist.p0[1] / IN + 1.4, f'y = {joist.p0[1] / IN:g}"',
                fontsize=8, color="#7a6440")
    ax.add_patch(Polygon(_in(p.xy_m for p in opening.outline), fc="white", ec=INK,
                         ls="--", lw=1, label="6x6 subfloor clearance"))
    under = floor.deck_z1_m - 11.875 * IN - 1 * IN
    for run in runs:
        for (a, za), (b, zb) in pairwise(zip(run.path, run.z_m, strict=True)):
            dashed = max(za, zb) < under  # below the joists: drawn dashed
            ax.plot(*zip(*_in((a, b)), strict=True), color=_colour(run),
                    lw=2.2 if "DRAIN" in run.tag else 1.4, ls="--" if dashed else "-")
    drain = next(r for r in runs if r.tag == "PR-B-SH2-DRAIN")
    x, y = (v / IN for v in drain.path[0])
    ax.add_patch(Circle((x, y), 2.375 / 2, fc="white", ec=COLOURS["drain"], lw=1.6))
    ax.annotate(f'molded drain ({x:.3f}", {y:.2f}")', (x, y), (x - 15, y - 12),
                fontsize=8, color=INK, arrowprops={"arrowstyle": "-", "color": INK, "lw": 0.6})
    cx, cy = (v.inches for v in (cleanout.position.x, cleanout.position.y))
    ax.plot(cx, cy, "s", ms=5, mfc="white", mec=INK)
    ax.annotate(cleanout.tag, (cx, cy), (cx + 2, cy - 9), fontsize=8, color=INK,
                arrowprops={"arrowstyle": "-", "color": INK, "lw": 0.6})
    tee = drain.path[3]
    ax.annotate("vent tee + wall drop", (tee[0] / IN, tee[1] / IN), (tee[0] / IN + 1, 194),
                fontsize=8, color=INK, arrowprops={"arrowstyle": "-", "color": INK, "lw": 0.6})
    ax.set(xlim=PLAN_X, ylim=PLAN_Y, xlabel="House x (inches)", ylabel="House y (inches)")
    ax.set_title("PLAN · FS-M-WEST bay, north up", loc="left", fontweight="bold", color=INK)


def section_view(ax, floor, joists, opening, runs, ceiling, cut_x):
    section = cross_section(joists[0].profile)
    fw, ft, wt = (v / IN for v in (section.flange_width_m, section.flange_thickness_m,
                                   section.web_thickness_m))
    bottom, top = joists[0].z0_m / IN, joists[0].z1_m / IN
    ys = [p.y.inches for p in opening.outline]
    deck0, deck1 = floor.deck_z0_m / IN, floor.deck_z1_m / IN
    for lo, hi in ((PLAN_Y[0], min(ys)), (max(ys), PLAN_Y[1])):
        ax.add_patch(Rectangle((lo, deck0), hi - lo, deck1 - deck0, fc="#cdb98f", ec="#a08a5f"))
    for joist in joists:
        y = joist.p0[1] / IN
        for z in (bottom, top - ft):
            ax.add_patch(Rectangle((y - fw / 2, z), fw, ft, fc=WOOD, ec="#a08a5f", lw=0.6))
        ax.add_patch(Rectangle((y - wt / 2, bottom + ft), wt, top - bottom - 2 * ft,
                               fc=WOOD, ec="#a08a5f", lw=0.6))
    if ceiling is not None:
        ax.add_patch(Rectangle((PLAN_Y[0], ceiling.z0_m / IN), PLAN_Y[1] - PLAN_Y[0],
                               (ceiling.z1_m - ceiling.z0_m) / IN, fc=GREY, ec="#9aa0a4"))
        ax.text(PLAN_Y[0] + 1, ceiling.z0_m / IN - 1.6, "basement ceiling, closed",
                fontsize=8, color=INK)
    drain = next(r for r in runs if r.tag == "PR-B-SH2-DRAIN")
    y0, z_top, z_trap = drain.path[0][1] / IN, drain.z_m[0] / IN, drain.z_m[1] / IN
    od = 2.375
    ax.add_patch(Rectangle((y0 - od / 2, z_trap), od, z_top - z_trap,
                           fc="white", ec=COLOURS["drain"], lw=1.4))
    ax.annotate(f'pipe top {deck1 - z_top:g}" below subfloor top', (y0, z_top), (y0 + 6, 2.2),
                fontsize=8, color=INK, arrowprops={"arrowstyle": "-", "color": INK, "lw": 0.6})
    ax.annotate(f'trap weir {deck0 - z_trap:g}" below datum; arm runs east',
                (y0, z_trap), (y0 + 6, -16), fontsize=8, color=INK,
                arrowprops={"arrowstyle": "-", "color": INK, "lw": 0.6})
    for run in runs:  # every horizontal run crossing the cut plane, seen end-on
        for (a, za), (b, zb) in pairwise(zip(run.path, run.z_m, strict=True)):
            if (a[0] - cut_x) * (b[0] - cut_x) >= 0 or a[0] == b[0]:
                continue
            t = (cut_x - a[0]) / (b[0] - a[0])
            y, z = (a[1] + t * (b[1] - a[1])) / IN, (za + t * (zb - za)) / IN
            ax.add_patch(Circle((y, z), run.diameter_m / IN / 2 + 0.12, fc=_colour(run),
                                ec=INK, lw=0.4))
            right = y > PLAN_Y[1] - 14
            ax.text(y - 1.4 if right else y + 1.4, z, run.tag.removeprefix("PR-"), fontsize=7,
                    color=INK, va="center", ha="right" if right else "left")
    lo, hi = (joist.p0[1] / IN for joist in joists if 165 < joist.p0[1] / IN < 190)
    ax.annotate("", (hi, bottom - 3), (lo, bottom - 3),
                arrowprops={"arrowstyle": "|-|", "color": BLUE, "lw": 0.8})
    ax.text((lo + hi) / 2, bottom - 4.6, f'{hi - lo:g}" o.c.', ha="center", fontsize=8, color=INK)
    ax.set(xlim=PLAN_Y, ylim=SECTION_Z, xlabel="House y (inches) · south → north",
           ylabel="Main-storey datum (inches)")
    ax.set_title(f'SECTION · x = {cut_x / IN:.3f}", looking west', loc="left",
                 fontweight="bold", color=INK)


def overview(ax, joists, module_in=16.0):
    """Whole span: off-module (moved/added) joists highlighted, the vacated module line dashed."""
    stations = [j.p0[1] / IN for j in joists]
    for joist, y in zip(joists, stations, strict=True):
        ring, _, _ = member_footprint(joist)
        moved = abs(y / module_in - round(y / module_in)) > 1e-6
        ax.add_patch(Polygon(_in(ring), fc=GREEN if moved else WOOD, ec="#a08a5f", lw=0.5))
        x0, x1 = sorted(v / IN for v in (joist.p0[0], joist.p1[0]))
        ax.text(x1 + 1.5, y, f'y {y:g}"  {x1 - x0:.1f}" uncut', va="center", fontsize=7,
                color=GREEN if moved else INK)
    lo, hi = min(stations), max(stations)
    for k in range(int(lo // module_in), int(hi // module_in) + 1):
        y = k * module_in
        if lo < y < hi and all(abs(y - s) > 0.5 for s in stations):
            ax.axhline(y, color=RED, ls="--", lw=0.8)
            ax.text(4, y + 0.8, f'former y = {y:g}" line', fontsize=7, color=RED)
    for a, b in pairwise(stations):
        ax.annotate("", (-4, b), (-4, a), arrowprops={"arrowstyle": "|-|", "color": BLUE,
                                                       "lw": 0.7}, annotation_clip=False)
        ax.text(-6, (a + b) / 2, f'{b - a:g}"', ha="right", va="center", fontsize=7, color=INK)
    ax.set(xlim=(-14, 250), ylim=(lo - 6, hi + 6), xlabel="House x (inches)")
    ax.set_title("FS-M-WEST · whole span, west sill to x = 18'", loc="left",
                 fontweight="bold", color=INK)


def main():
    model, findings = resolve(load_plan(HOUSE).plan)
    if errors := [f.message for f in findings if f.severity.value == "error"]:
        raise SystemExit(errors)
    floor = next(f for f in model.floors if f.tag == "FS-M-WEST")
    joists = sorted((m for m in floor.members if m.category == "joist"
                     and PLAN_Y[0] < m.p0[1] / IN < PLAN_Y[1]), key=lambda m: m.p0[1])
    fixture = next(o for o in model.canvas_objects if o.tag == "FX-M-BATH2-SH")
    opening = model.plan.by_tag("FO-M-BATH2-SH-DRAIN")
    cleanout = model.plan.by_tag("CO-M-SH2-HEAD")
    window = box(PLAN_X[0] * IN, PLAN_Y[0] * IN, PLAN_X[1] * IN, PLAN_Y[1] * IN)
    runs = [r for r in model.pipe_runs if len(r.path) > 1 and r.storey in ("basement", "main")
            and any(window.contains(Point(p)) for p in r.path)]
    cut_x = fixture.position[0]
    ceiling = next((c for c in model.ceilings if c.storey == "basement" and Area(
        c.outline).contains(Point(cut_x, fixture.position[1]))), None)
    fig = plt.figure(figsize=(15, 11))
    grid = fig.add_gridspec(2, 2, height_ratios=(0.5, 1), width_ratios=(1, 1.25))
    axes = [fig.add_subplot(grid[0, :]), fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1])]
    overview(axes[0], joists)
    plan_view(axes[1], floor, joists, fixture, opening, runs, cleanout)
    section_view(axes[2], floor, joists, opening, runs, ceiling, cut_x)
    for ax in axes:
        ax.set_aspect("equal")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=8)
    fig.suptitle("BATH2 · SS-3636 centred drain between full-span TJIs", fontsize=15,
                 fontweight="bold", color=INK, x=0.06, ha="left")
    fig.text(0.06, 0.035, "Solid: in the joist depth. Dashed: below the joists. "
             "Blue cold, red hot, brown drain. "
             "Dry-fit the delivered base before the 6\" round site cut.",
             fontsize=9, color=INK)
    fig.subplots_adjust(left=0.06, right=0.98, bottom=0.08, top=0.92, wspace=0.18, hspace=0.2)
    target = HOUSE / "notes/assets/bath2-shower-drain-framing"
    fig.savefig(target.with_suffix(".svg"), metadata={"Date": None})
    plt.close(fig)
    print(target.with_suffix(".svg"))


if __name__ == "__main__":
    main()
