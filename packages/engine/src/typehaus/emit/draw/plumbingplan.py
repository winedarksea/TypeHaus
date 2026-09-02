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


#: How far a candidate storey may sit *below* this storey's own ceiling plane and still be
#: called the floor above it. Slack for a raised-heel lift or a sloped deck, not for a
#: different structure standing beside the house.
_CEILING_SLACK_M = 0.05


def storey_above(model: ResolvedModel, storey_tag: str) -> str | None:
    """The storey whose floor is this storey's ceiling, or ``None``.

    Not simply the next storey by elevation. A freestanding structure files its own storey
    in the same table as the house's, and once it stops sharing the house's datum it lands
    *between* two house storeys: catlin's garage sits at -0'-8" — above the basement at -9'
    but 8" below the main floor. Taking it as "the storey above the basement" put a garage
    yard-hydrant sleeve on the basement's ceiling plan and dropped the 42 sleeves cast in
    the deck actually overhead.

    So the candidate must reach this storey's own ceiling. A floor that sits below the
    ceiling of the storey under it is not that storey's ceiling; it is something standing
    next to it.
    """
    storeys = sorted(model.plan.storeys, key=lambda s: s.elevation.meters)
    tags = [s.tag for s in storeys]
    if storey_tag not in tags:
        return None
    here = storeys[tags.index(storey_tag)]
    ceiling = here.elevation.meters + here.default_ceiling_height.meters - _CEILING_SLACK_M
    return next((s.tag for s in storeys
                 if s.elevation.meters > here.elevation.meters
                 and s.elevation.meters >= ceiling), None)


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
