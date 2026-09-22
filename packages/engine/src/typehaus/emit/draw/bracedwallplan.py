"""S-103 — the braced wall plan, per floor (→ 30 §Structural).

MNSPECT's most-cited residential omission, and this set had none. A braced wall plan states
four things per floor: where the braced wall **lines** are, where the **panels** on each
line are, how **wide** each panel is, and which IRC R602.10.4 **method** each is built to. A
discrete braced-wall inspection is run against it, and the inspector's own questions are the
per-line REQ / PROV block this sheet prints.

The lines and the panels are read from ``resolve/braced_walls.py`` and graded by
``checks/structural/bracing_eval.py`` — the same reading the findings are written from, so
the drawing and the verdict cannot disagree.

**``structural_role`` is not the input, and the plan for this work assumed it was.** Every
one of catlin's walls carries ``structural_role=None``. Lines are identified by what is
actually known: a chain carrying a light-frame wall on the building's exterior envelope.
"""

from __future__ import annotations

from typehaus.checks.structural.bracing_eval import LineEvaluation, evaluate_line
from typehaus.emit.draw._shared import emit_ghost_walls, to_in
from typehaus.emit.draw.lineweights import CUT, CUT_HEAVY
from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder, Text
from typehaus.emit.draw.typography import DIM_TEXT_PT
from typehaus.quantities import M_PER_IN
from typehaus.resolve.braced_walls import (
    KIND_BRACED,
    KIND_ENGINEERED,
    KIND_FOUNDATION,
    KIND_GABLE_END,
    KIND_INFILL,
    KIND_INTERIOR,
    KIND_PLATE,
    BracedWallLine,
    braced_wall_lines,
    resolved_braced_wall_panels,
)

BWL_LAYER = "S-WALL-BRCE"

#: How far off the line a panel is drawn, so the heavy panel run reads beside the line
#: rather than on top of it.
_PANEL_OFFSET_IN = 6.0

#: What a line's label says about why it is not graded. One phrase per measured kind.
_KIND_LABEL = {
    KIND_ENGINEERED: "ENGINEERED — lateral_system/RF-BW-CANOPY",
    KIND_PLATE: "RAFTER PLATE — NOT A BRACED WALL LINE",
    KIND_GABLE_END: "GABLE END — BRACED BY ROOF ASSEMBLY",
    KIND_FOUNDATION: "FOUNDATION — R404",
    KIND_INTERIOR: "INTERIOR PARTITION — NOT DESIGNATED",
    KIND_INFILL: "FRAMED INFILL IN AN R404 BOX",
}


def has_braced_wall_content(model, storey: str) -> bool:
    return bool(braced_wall_lines(model, storey))


def build_braced_wall_plan(model, storey: str) -> Scene:
    """Ghosted walls, the lines heavy, the panels heavier, and a REQ/PROV block per line."""
    b = SceneBuilder(name=f"braced-wall-{storey}", units="in")
    emit_ghost_walls(b, model, storey)
    lines = braced_wall_lines(model, storey)
    panels, unplaced = resolved_braced_wall_panels(model, storey, lines)
    notes: list[str] = []
    for line in lines:
        b.add(Polyline(points=(to_in(line.p0), to_in(line.p1)),
                       layer=BWL_LAYER, lineweight=CUT, tag=line.tag))
        mid = ((line.p0[0] + line.p1[0]) / 2.0, (line.p0[1] + line.p1[1]) / 2.0)
        label = _KIND_LABEL.get(line.kind, line.method)
        b.add(Text(anchor=to_in(mid),
                   content=f"{line.tag}  {line.length_ft:.1f}'  {label}",
                   height_pt=DIM_TEXT_PT, layer=BWL_LAYER, align="center"))
        if line.kind != KIND_BRACED:
            continue
        evaluation = evaluate_line(model, line, lines, panels)
        notes.append(_req_prov(evaluation))
        for grade in evaluation.panels:
            _draw_panel(b, line, grade)
    for panel in unplaced:
        notes.append(f"{panel.tag}: {panel.reason} (wall_ref {panel.wall_ref})")
    y = -48.0
    for note in (*notes, _CONDITIONS):
        b.add(Text(anchor=(0.0, y), content=note, height_pt=DIM_TEXT_PT, layer=BWL_LAYER,
                   align="left"))
        y -= 12.0
    return b.build()


def _draw_panel(b: SceneBuilder, line: BracedWallLine, grade) -> None:
    """One merged panel, offset off the line, tagged with its width and method.

    A panel contributing ZERO length is still drawn — it is on the wall and an inspector
    will ask about it — but drawn light, and its label says what it does not do.
    """
    panel = grade.panel
    ux, uy = ((line.p1[0] - line.p0[0]) / line.length_m,
              (line.p1[1] - line.p0[1]) / line.length_m)
    nx, ny = -uy * _PANEL_OFFSET_IN * M_PER_IN, ux * _PANEL_OFFSET_IN * M_PER_IN
    p0 = (line.p0[0] + ux * panel.u0_m + nx, line.p0[1] + uy * panel.u0_m + ny)
    p1 = (line.p0[0] + ux * panel.u1_m + nx, line.p0[1] + uy * panel.u1_m + ny)
    counts = grade.contributes_in > 0.0
    b.add(Polyline(points=(to_in(p0), to_in(p1)), layer=BWL_LAYER,
                   lineweight=CUT_HEAVY if counts else CUT,
                   tag=f"BWP-{panel.line_tag}-{panel.u0_ft:.0f}"))
    mid = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0)
    words = (f"{panel.length_in:.0f}\" {panel.method}" if counts
             else f"{panel.length_in:.0f}\" — CONTRIBUTES 0: {grade.reason}")
    if panel.hold_down_refs:
        words += f"  HD {'/'.join(panel.hold_down_refs)}"
    b.add(Text(anchor=to_in(mid), content=words, height_pt=DIM_TEXT_PT, layer=BWL_LAYER,
               align="center"))


def _req_prov(evaluation: LineEvaluation) -> str:
    """The block an MNSPECT braced-wall inspection asks for, with the rows read."""
    required = evaluation.required_ft
    if required is None:
        return f"{evaluation.line.tag}: REQ NOT DETERMINED — {'; '.join(evaluation.gaps)}"
    rows = " | ".join(factor.row for factor in evaluation.factors)
    base = evaluation.base.row if evaluation.base else ""
    return (f"{evaluation.line.tag}: REQ {required:.2f}' / PROV {evaluation.provided_ft:.2f}'"
            f" — {base} | {rows}")


#: The R602.10.8 conditions a PASS on this sheet rests on and this model does not carry.
#: It replaced a disclaimer saying the panels were not modelled at all; they are now.
_CONDITIONS = (
    "PANELS SHOWN ARE THE DESIGNATED BRACED WALL PANELS (IRC R602.10). THE PASS ON THIS "
    "SHEET RESTS ON R602.10.8, WHICH IS NOT MODELLED: A RIM JOIST, BAND JOIST OR BLOCKING "
    "OVER THE FULL LENGTH OF EACH PANEL WHERE JOISTS ARE PERPENDICULAR; A PARALLEL FRAMING "
    "MEMBER OR FULL-DEPTH BLOCKING AT 16 IN O.C. WHERE THEY ARE PARALLEL; PLATE FASTENING "
    "PER TABLE R602.3(1); CONNECTIONS TO CONCRETE PER R403.1.6."
)


def braced_wall_summary(model, storey: str) -> tuple[int, int, float, float]:
    """``(graded lines, panels, required ft, provided ft)`` for one storey.

    The sheet's own arithmetic, exported for ``schedule/handoff.py`` so the framer's list
    and S-103 quote one number. Lines that owe no length (a gable end, a foundation) are not
    counted; a line whose requirement cannot be determined contributes 0 to both totals.
    """
    lines = braced_wall_lines(model, storey)
    panels, _unplaced = resolved_braced_wall_panels(model, storey, lines)
    graded = required = provided = 0.0
    counted = 0
    for line in lines:
        if line.kind != KIND_BRACED:
            continue
        counted += 1
        evaluation = evaluate_line(model, line, lines, panels)
        if evaluation.required_ft is not None:
            required += evaluation.required_ft
            provided += evaluation.provided_ft
        graded += 1
    return counted, len(panels), required, provided
