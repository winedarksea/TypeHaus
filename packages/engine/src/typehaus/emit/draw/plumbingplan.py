"""Plumbing plan → drawing IR (→ 20 §Drawing IR, Permit-ready plan set Phase 2).

One sheet per storey that owns plumbing content: authored ``PipeRun``/``SleevePenetration``
elements on that storey, plus sleeves that penetrate the slab immediately above (shown
"from below" — a basement ceiling plan needs the sleeve layout to coordinate mechanical
rough-in against the cast-in-place pour above it, → 2.5).
"""

from __future__ import annotations

from typehaus.emit.draw._shared import emit_fixtures, emit_ghost_walls
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.scene import Leader, NamedPoint, Polyline, Scene, SceneBuilder, Symbol, Text
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel

_DRAIN_VENT = {"drain", "vent"}


def storey_above(model: ResolvedModel, storey_tag: str) -> str | None:
    storeys = sorted(model.plan.storeys, key=lambda s: s.elevation.meters)
    tags = [s.tag for s in storeys]
    if storey_tag not in tags:
        return None
    index = tags.index(storey_tag)
    return tags[index + 1] if index + 1 < len(tags) else None


def _sleeves_for(model: ResolvedModel, storey_tag: str):
    above = storey_above(model, storey_tag)
    return [s for s in model.sleeves if s.storey in {storey_tag, above}]


def has_plumbing_content(model: ResolvedModel, storey_tag: str) -> bool:
    pipes = [p for p in model.pipe_runs if p.storey == storey_tag]
    return bool(pipes or _sleeves_for(model, storey_tag))


def build_plumbing_plan(model: ResolvedModel, storey: str) -> Scene:
    b = SceneBuilder(name=f"plumbing-{storey}", units="in")
    emit_ghost_walls(b, model, storey)
    emit_fixtures(b, model, storey, frozenset({"plumbing", "appliance"}))

    for run in model.pipe_runs:
        if run.storey != storey:
            continue
        layer = "P-SANR-PIPE" if run.system in _DRAIN_VENT else "P-DOMW-PIPE"
        linetype = "DASHED" if run.system in _DRAIN_VENT else "CONTINUOUS"
        b.add(Polyline(points=tuple(_in(p) for p in run.path), layer=layer,
                       lineweight=0.35, linetype=linetype, uid=run.uid, tag=run.tag))
        mid = run.path[len(run.path) // 2]
        diameter_in = run.diameter_m / M_PER_IN
        if run.z_start_m is not None and run.z_end_m is not None and run.length_m > 1e-9:
            slope = (run.z_start_m - run.z_end_m) / M_PER_IN / (run.length_m * 3.280839895)
            text = f'{diameter_in:.0f}" {run.system.upper()} @ {slope:.2f}"/FT'
        else:
            text = f'{diameter_in:.0f}" {run.system.upper()}'
        b.add(Leader(anchor=NamedPoint(xy=_in(mid), name=run.tag), at=_in(mid),
                     to=_in((mid[0], mid[1] + 1.0)), text=text, layer=layer))

    for sleeve in _sleeves_for(model, storey):
        b.add(Symbol(name="sleeve", insert=_in(sleeve.center), layer="P-SANR-PIPE",
                     scale=sleeve.sleeve_d_m / M_PER_IN))
        b.add(Text(anchor=_in((sleeve.center[0], sleeve.center[1] + 0.3)), content=sleeve.tag,
                   height=2.0, layer="A-ANNO-TEXT", align="center"))
    return b.build()
