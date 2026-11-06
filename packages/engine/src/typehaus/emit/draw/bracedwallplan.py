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

from os.path import commonprefix

from typehaus.checks.structural.bracing_eval import LineEvaluation, evaluate_line
from typehaus.checks.structural.sill_bearing import sill_anchor_notes
from typehaus.emit.draw._shared import emit_ghost_walls, to_in
from typehaus.emit.draw.annotation_requests import add_line_label
from typehaus.emit.draw.lineweights import CUT, CUT_HEAVY
from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder
from typehaus.emit.draw.structural_dimensions import (
    Tier,
    emit_structural_tiers,
    line_stations,
    overall_tier,
)
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

#: The scale S-103's dimension tiers are laid out for: the smallest it lands on (ledger).
#: A larger print only spaces them further apart.
_TIER_SCALE = 0.09375

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
    evaluations: list[LineEvaluation] = []
    for line in lines:
        b.add(Polyline(points=(to_in(line.p0), to_in(line.p1)),
                       layer=BWL_LAYER, lineweight=CUT, tag=line.tag))
        label = _KIND_LABEL.get(line.kind, line.method)
        # Placed at frame time against the panel labels (C7-E8, F1-008): the line's own
        # side is the one away from its panels.
        add_line_label(b, key=f"bwl-{line.tag}",
                       text=f"{line.tag}  {line.length_ft:.1f}'  {label}",
                       start=to_in(line.p0), end=to_in(line.p1), layer=BWL_LAYER,
                       height_pt=DIM_TEXT_PT, priority=60, preferred_side=-1)
        if line.kind != KIND_BRACED:
            continue
        evaluation = evaluate_line(model, line, lines, panels)
        evaluations.append(evaluation)
        for grade in evaluation.panels:
            _draw_panel(b, line, grade)
    notes = _req_prov_notes(evaluations)
    notes.extend(sill_anchor_notes(model, storey))
    for panel in unplaced:
        notes.append(f"{panel.tag}: {panel.reason} (wall_ref {panel.wall_ref})")
    walls = [wall for wall in model.walls if wall.storey == storey]
    line_xs, line_ys = line_stations((line.p0, line.p1) for line in lines)
    tiers = [Tier("BWL C/C", tuple(line_xs), tuple(line_ys)),
             overall_tier("O/A FACE WALL", walls)]
    emit_structural_tiers(b, tiers, _TIER_SCALE)
    # The notes print in the sheet's wrapped notes panel (F1-007: as model text they ran
    # off the border). The tiers stand outside the bounds a frame fits, so it reserves them.
    scene = b.build().model_copy(update={"notes": (*notes, _CONDITIONS)})
    return _framed(scene)


def _framed(scene: Scene) -> Scene:
    """``scene`` with a frame on the set's paper that leaves room for its tiers."""
    from typehaus.emit.draw.dimension_rows import dimension_reserve
    from typehaus.emit.draw.sheet_writer import current_paper, frame_for_scene

    frame = frame_for_scene(scene, current_paper(),
                            reserve=lambda scale: dimension_reserve(scene, scale))
    return scene if frame is None else scene.model_copy(update={"frame": frame})


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
    words = (f"{panel.length_in:.0f}\" {panel.method}" if counts
             else f"{panel.length_in:.0f}\" — CONTRIBUTES 0: {grade.reason}")
    if panel.hold_down_refs:
        words += f"  HD {'/'.join(panel.hold_down_refs)}"
    add_line_label(b, key=f"bwp-{panel.line_tag}-{panel.u0_ft:.1f}", text=words,
                   start=to_in(p0), end=to_in(p1), layer=BWL_LAYER, height_pt=DIM_TEXT_PT,
                   priority=50, preferred_side=1)


def _req_prov_notes(evaluations: list[LineEvaluation]) -> list[str]:
    """The block an MNSPECT braced-wall inspection asks for, with the rows read.

    A row every graded line read (and the leading words of the base row they share) prints
    once; the lines that read the same remaining rows then share one note, each with its
    own REQ / PROV.
    """
    graded = [e for e in evaluations if e.required_ft is not None]
    bases = {id(e): e.base.row.split(", ") if e.base else [] for e in graded}
    common = len(commonprefix(list(bases.values()))) if graded else 0
    shared = [f.row for f in graded[0].factors
              if all(f.row in {g.row for g in e.factors} for e in graded)] if graded else []
    head = ", ".join(next(iter(bases.values()), [])[:common])
    notes = ([f"EVERY LINE READS: {' | '.join(r for r in (head, *shared) if r)}"]
             if head or shared else [])
    groups: dict[str, list[str]] = {}
    for e in evaluations:
        if e.required_ft is None:
            notes.append(f"{e.line.tag}: REQ NOT DETERMINED — {'; '.join(e.gaps)}")
            continue
        own = [", ".join(bases[id(e)][common:]),
               *(f.row for f in e.factors if f.row not in shared)]
        groups.setdefault(" | ".join(r for r in own if r), []).append(
            f"{e.line.tag}: REQ {e.required_ft:.2f}' / PROV {e.provided_ft:.2f}'")
    notes.extend((f"{rows} — " if rows else "") + "; ".join(results)
                 for rows, results in groups.items())
    return notes


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
