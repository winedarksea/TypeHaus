"""A ``VentRun`` is a run, and until now it was in no collision system whatsoever.

It is a parametric chase riser rather than an authored polyline, so it resolved to
``ResolvedSolid``s alone: no envelope, nothing ``mep.run_interference`` could grade, and —
since ``routing/obstacles`` iterates ``envelopes()`` — not a router obstacle either. A
campaign would lane a duct straight through catlin's radon riser and call the lane clear.

These pin the fix and, more importantly, pin that there is exactly ONE derivation of the
riser's route with two readers. A second copy is how the authored 33' riser drifted 6 ft
above its own roof, and the same failure here would put the viewer's pipe somewhere the
collision checker's pipe is not.
"""

from __future__ import annotations

import pytest

from typehaus.model.mep import VentRun
from typehaus.resolve.vent_termination import RISER_LEGS, riser_polylines

pytestmark = pytest.mark.slow


def _vents(ctx):
    return [el for el in ctx.model.plan.all_elements() if isinstance(el, VentRun)]


def test_the_solids_and_the_polyline_are_ONE_derivation(catlin_ctx) -> None:
    """Every ``ResolvedSolid`` the vent emits sits on the polyline, riser for riser."""
    solids = {s.tag: s for s in catlin_ctx.model.solids if s.category == "vent"}
    assert solids, "catlin authors a VentRun"

    for vent in _vents(catlin_ctx):
        for tag, path, z in riser_polylines(catlin_ctx.model, vent):
            system = tag.rsplit("-", 1)[-1]
            for leg, (_uid, tag_part, horizontal) in enumerate(RISER_LEGS):
                a, b, za, zb = path[leg], path[leg + 1], z[leg], z[leg + 1]
                if horizontal:
                    continue  # swept into bands; its ends are pinned by the risers either side
                if za == zb:
                    continue  # a leg this vent does not have
                solid = solids.get(f"{vent.tag}-{system}-{tag_part}")
                assert solid is not None, f"{tag_part} of {tag} resolves a solid"
                assert solid.z0_m == pytest.approx(min(za, zb))
                assert solid.z1_m == pytest.approx(max(za, zb))
                centre = solid.outline
                xs = [p[0] for p in centre]
                ys = [p[1] for p in centre]
                assert (min(xs) + max(xs)) / 2.0 == pytest.approx(a[0], abs=1e-6)
                assert (min(ys) + max(ys)) / 2.0 == pytest.approx(a[1], abs=1e-6)


def test_a_vent_riser_now_has_an_envelope(catlin_ctx) -> None:
    """``mep.run_interference`` and ``routing/obstacles`` read the same ``envelopes()``, so
    both pick this up with no edit of their own — which is the point of a shared reading."""
    from typehaus.resolve.mep_envelopes import envelopes

    shells = {e.tag: e for e in envelopes(catlin_ctx.model)}
    risers = [tag for vent in _vents(catlin_ctx)
              for tag, _path, _z in riser_polylines(catlin_ctx.model, vent)]
    assert risers, "catlin's VentRun bundles at least one system"
    for tag in risers:
        assert tag in shells, f"{tag} resolves an envelope"
        assert shells[tag].prisms, f"{tag}'s envelope is not empty"


def test_the_chase_is_a_hard_prism_for_the_router(catlin_ctx) -> None:
    """The reason this matters: an obstacle the router cannot see is a lane it will take."""
    from typehaus.routing.obstacles import hard_prisms

    blocked = {p.tag for p in hard_prisms(catlin_ctx.model, 0.0381)}
    risers = [tag for vent in _vents(catlin_ctx)
              for tag, _path, _z in riser_polylines(catlin_ctx.model, vent)]
    assert any(tag in blocked for tag in risers)


def test_a_riser_with_no_derivable_top_is_not_placed_at_all(catlin_ctx) -> None:
    """A riser whose termination is unknown is not a placed run. Guessing one would put a
    solid — and an obstacle — where the building has none."""

    for vent in _vents(catlin_ctx):
        stripped = vent.model_copy(update={"wall_ref": None,
                                           "roof_termination_elevation": None})
        model = catlin_ctx.model
        roofs, model.roofs = model.roofs, []
        try:
            assert riser_polylines(model, stripped) == []
        finally:
            model.roofs = roofs
