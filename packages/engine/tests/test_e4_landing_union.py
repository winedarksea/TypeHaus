"""E4 — a landing made of two abutting surfaces, and the cladding datum under the court.

``code.R311_3_exterior_landing`` asks whether a *landing* covers the 36" patch outside a
door. It used to ask whether one authored element did, which is a different question: a
stoop that abuts a deck is one walking surface and failed the check however it was built.
``_landing_surfaces(ctx, union=True)`` now merges the surfaces sharing one plane.

The second half pins the datum the sunken garden is laid out from. ``house_ext_layers_in``
was a frozen 5.0" against a cladding face that had moved to 7.25"; it is derived now, and
the porch's north line — which the whole structure reads — did not move.
"""

from __future__ import annotations

import pytest
from shapely.geometry import box

from typehaus.checks.code.mn_residential.egress import (
    _landing_surfaces,
    _merged_landing_surfaces,
    _plane_buckets,
)

INCH = 0.0254
FT = 0.3048


def test_two_abutting_coplanar_surfaces_merge_into_one():
    stoop = ("SL-STOOP", box(0, 0, 1, 1), 0.0)
    deck = ("FS-DECK", box(1, 0, 3, 1), 0.0)
    merged = _merged_landing_surfaces([stoop, deck])
    assert len(merged) == 1
    name, poly, top = merged[0]
    assert name == "FS-DECK + SL-STOOP"
    assert poly.area == pytest.approx(3.0, abs=1e-6)
    assert top == pytest.approx(0.0)


def test_the_lowest_top_governs_the_merged_entry():
    """A landing is only as high as its lowest board: the honest step down is the big one."""
    low = ("SL-STOOP", box(0, 0, 1, 1), 0.0)
    high = ("FS-DECK", box(1, 0, 3, 1), 0.4 * INCH)
    (_name, _poly, top), = _merged_landing_surfaces([low, high])
    assert top == pytest.approx(0.0)


def test_surfaces_a_riser_apart_are_not_one_plane():
    lower = ("SL-WALK", box(0, 0, 1, 1), 0.0)
    upper = ("FS-DECK", box(1, 0, 3, 1), 7.0 * INCH)
    assert _merged_landing_surfaces([lower, upper]) == []


def test_disjoint_coplanar_surfaces_are_never_bridged():
    """Two islands with a gap between them are two landings, not one."""
    west = ("SL-W", box(0, 0, 1, 1), 0.0)
    east = ("SL-E", box(5, 0, 6, 1), 0.0)
    assert _merged_landing_surfaces([west, east]) == []


def test_a_plane_bucket_cannot_chain_its_way_uphill():
    """Each member is compared to the bucket's seed, so a ramp of near-coplanar surfaces
    does not walk a whole staircase into one plane."""
    steps = [(f"S{i}", box(i, 0, i + 1, 1), i * 0.4 * INCH) for i in range(6)]
    buckets = _plane_buckets(steps)
    assert len(buckets) > 1
    for bucket in buckets:
        assert bucket[-1][2] - bucket[0][2] <= 0.5 * INCH + 1e-9


def test_union_is_opt_in_and_keeps_every_individual_surface():
    """``flood_step`` reads the un-merged list on purpose — water stands to the level of the
    HIGHEST surface, and a merged entry is published at its lowest top."""
    import inspect

    signature = inspect.signature(_landing_surfaces)
    assert signature.parameters["union"].default is False


def test_catlin_porch_north_line_did_not_move(catlin_model):
    """The sunken garden's north edge is -0'-10" off the house's sheathing line, and the
    whole porch — deck, back beams, column line, veneer grade beam — is laid out from it.
    Deriving ``house_ext_layers_in`` from the live 7.25" cladding stand-off re-split that
    10" (7.25" of wall + 2.75" of air) and must not have re-cut it: widening the gap back
    to a nominal 5" pushes the court 2.25" south and off D-B-PATIO's landing patch.
    """
    porch = catlin_model.plan.by_tag("FS-SG-PORCH")
    north = max(p.xy_m[1] for p in (porch.subfloor_outline or porch.outline))
    assert north == pytest.approx(-10 * INCH, abs=1e-6)


def test_catlin_patio_door_still_lands_on_the_court(catlin_check_report):
    from typehaus.findings import Result

    landings = [f for f in catlin_check_report().findings
                if f.check_id == "code.R311_3_exterior_landing" and "D-B-PATIO" in f.message]
    assert landings and all(f.result is Result.PASS for f in landings), landings
