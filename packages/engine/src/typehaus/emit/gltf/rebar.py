"""Reinforcing bars in the glTF: one tube per piece, one node per host (decision #75 D13).

Each bar is a four-facet tube swept along its laid-out ``path`` through the same mitring
``resolve/sweep.py`` gives a handrail, a closed hoop repeating its first point. Export
weight is the constraint, not fidelity: ~1,200 bars at six facets added 7.6 MB to catlin's
GLB, so bars are square in section and a circular tie keeps every third vertex. The viewer
draws its own rounder bars from ``/model/rebar``. The
node carries the host's own kind + uid, trade ``concrete``, and ``extras.facet =
"concrete:rebar"`` — the facet the viewer's Concrete › Rebar chip toggles, off by default.
"""

from __future__ import annotations

from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.resolve.geometry_ir import GBox
from typehaus.resolve.model import ResolvedModel, SolidSweep
from typehaus.resolve.sweep import round_profile, sweep_legs

REBAR_FACET = "concrete:rebar"

#: Reinforcing bar by its coating (decision #75): galvanized reads zinc grey, black bar mill-scale
#: brown, epoxy green. Mirrored in ui/src/three/rebar.ts — keep the two in step.
_REBAR_COATING = {
    "hdg-a767": (0.70, 0.72, 0.74, 1.0),
    "hdg-a1094": (0.70, 0.72, 0.74, 1.0),
    "black": (0.33, 0.25, 0.21, 1.0),
    "epoxy": (0.30, 0.52, 0.30, 1.0),
    "stainless": (0.80, 0.81, 0.82, 1.0),
    "gfrp": (0.78, 0.70, 0.36, 1.0),
}


def rebar_color(coating: str) -> tuple[float, float, float, float]:
    return _REBAR_COATING.get(coating, _REBAR_COATING["black"])


_FACETS = 4
_CIRCLE_STRIDE = 3


def add_rebar(scene, model: ResolvedModel) -> None:
    for rebar_set in sorted(model.rebar, key=lambda s: s.host_uid):
        mb = _MeshBuilder()
        for bar in rebar_set.bars:
            points = tuple(bar.path)
            if bar.closed and len(points) > 8:
                points = points[::_CIRCLE_STRIDE]
            path = points + ((points[0],) if bar.closed else ())
            sweep = SolidSweep(path=path, profile=round_profile(bar.diameter_m / 2.0, _FACETS))
            color = rebar_color(bar.coating)
            for start, end in sweep_legs(sweep):
                mb.add_gbox(GBox(corners_bottom=start, corners_top=end), color)
        kind = "wall" if model.wall(rebar_set.host_tag) is not None else "solid"
        scene.add_object(mb, ("concrete",), kind=kind, uid=rebar_set.host_uid,
                         facet=REBAR_FACET)
