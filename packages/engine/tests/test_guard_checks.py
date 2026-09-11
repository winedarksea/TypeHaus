"""The three guard rules a drawn infill made possible.

* ``structural.masonry_guard_bearing`` — a masonry parapet is a guard that is also a wall,
  and the load path that buys it (its own weight, on whatever is under it) had no rule.
* ``advisory.cable_guard_deflection`` — R312.1.3 reads 4"; a tensioned cable at 4" fails the
  inspection, because it deflects about a quarter of its spacing under load.
* ``code.R308_4_4_glass_guard`` — glass used *as* the guard, which R308.4's location test
  never reaches.

The motivating case: a masonry-parapet guard is a load path nobody was asking about — a
42" grouted-CMU-and-brick parapet runs about 420 plf, and a wood deck rim designed to R507's
40 psf live + 10 psf dead cannot carry it. Catlin's own porch guard is now RL-SG-PORCH, a
metal fascia-mount railing, so the house has no ``Wall.guard`` and the rule reports one
UNKNOWN saying so. The arithmetic it was written for is exercised against synthetic walls
below, where the catalog densities can be stated and varied — a stack the catalog cannot
weigh must report UNKNOWN rather than a comfortable pass.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.checks.registry import Preferences, StructuralPreferences
from typehaus.checks.structural.guards import (
    _dead_load_plf,
    masonry_guard_bearing,
)
from typehaus.findings import Result
from typehaus.quantities import inch
from _helpers import CATLIN as CATLIN_DIR

#: A 3'-6" guard — the height R312.1.2's 36" minimum is cleared by, and the height the
#: retired porch parapet was drawn at.
GUARD_HEIGHT_M = inch(42).meters


@pytest.fixture(scope="module")
def catlin_ctx():
    """The real house, with its preferences — the allowance this rule grades against is
    authored in ``houses/catlin/preferences.toml``, so a bare ``Preferences()`` would be
    checking a different number than the one the house states."""
    from typehaus.checks import build_context
    from typehaus.source import load_plan

    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    return ctx


def test_catlin_grades_one_guard_wall_and_it_is_not_masonry(catlin_ctx):
    """The house gained its first ``Wall.guard`` on 2026-09-10, and it is a light one.

    ``W-BW-SCREEN`` is the north entry's west panel: KDAT 2x4 at 16" o.c. under 5/8" CDX and
    7/8" corrugated on both faces, closing the passage from the deck to +4'-0" and doing
    three jobs at once — the canopy's north-south shear panel, the guard, and the closure
    over the deck framing.

    It weighs about 33 plf, which is what makes this test worth having. The same wall read
    **402 plf** before two derivations were fixed in this module on the same day: a profiled
    sheet was weighed as 7/8" of solid steel, and a framed layer as 3 1/2" of solid wood over
    the whole wall face. Either one alone sent a screen panel looking for a masonry bearing
    line. The assertion is on the ORDER of magnitude, not the digits — a framed screen wall
    is tens of plf and a grouted-CMU parapet is hundreds, and this check only means anything
    while it can tell them apart.
    """
    findings = masonry_guard_bearing(catlin_ctx)
    assert len(findings) == 1, [f.message for f in findings]
    finding = findings[0]
    assert finding.result is Result.PASS
    assert "W-BW-SCREEN" in finding.message
    assert "does not have to be hard" in finding.message
    plf = float(finding.message.split("weighs ")[1].split(" plf")[0])
    assert 20 <= plf <= 50, finding.message
    assert [w.tag for w in catlin_ctx.plan.all_elements()
            if getattr(w, "guard", False)] == ["W-BW-SCREEN"]


# --- synthetic supports --------------------------------------------------------------------

class _Layer:
    def __init__(self, function, material_ref, thickness_m) -> None:
        self.function = function
        self.material_ref = material_ref
        self.thickness_m = thickness_m


class _Wall:
    def __init__(self, tag, layers, axis, z0_m, z1_m, thickness_m=0.3) -> None:
        self.tag = tag
        self.axis = axis
        self.z0_m, self.z1_m = z0_m, z1_m
        self.thickness_m = thickness_m
        self._layers = layers

    def depth_layers(self):
        return list(self._layers)


def _masonry_layers():
    return [_Layer("finish", "stucco", inch(0.5).meters),
            _Layer("structure", "cmu", inch(7.625).meters),
            _Layer("airgap", "air-barrier", inch(1.0).meters),
            _Layer("cladding", "white-brick", inch(3.625).meters)]


_MATERIALS = [SimpleNamespace(tag="stucco", density=1900.0, hatch="concrete"),
              SimpleNamespace(tag="cmu", density=2000.0, hatch="concrete"),
              SimpleNamespace(tag="air-barrier", density=None, hatch="membrane"),
              SimpleNamespace(tag="white-brick", density=1920.0, hatch="concrete"),
              SimpleNamespace(tag="spf", density=500.0, hatch="lumber")]


def _ctx(guard_layers, *, floor_outline=None, support_wall=None, allowance=50.0):
    """A guard standing at z=0 over a 20' x 20' patch, on whatever is passed under it."""
    from typehaus.model.elements import Wall as _WallElement

    guard = _Wall("W-GUARD", guard_layers, ((0.0, 0.0), (6.0, 0.0)), 0.0, GUARD_HEIGHT_M)
    walls = [guard] + ([support_wall] if support_wall is not None else [])
    floors = []
    if floor_outline is not None:
        floors.append(SimpleNamespace(tag="FS-DECK", deck_outline=floor_outline,
                                      deck_z1_m=0.0))
    # ``masonry_guard_bearing`` censuses ``isinstance(e, Wall) and e.guard``, so the element
    # side has to be a real Wall — the marker is what makes this rule apply at all.
    element = _WallElement(uid="WG00000001", tag="W-GUARD", start_node="N-A", end_node="N-B",
                           assembly="A", guard=True)
    return SimpleNamespace(
        plan=SimpleNamespace(all_elements=lambda: [element],
                             library=SimpleNamespace(materials=_MATERIALS)),
        model=SimpleNamespace(walls=walls, floors=floors, solids=[]),
        preferences=Preferences(structural=StructuralPreferences(
            max_guard_dead_load_on_wood_plf=allowance)),
    )


def test_a_masonry_guard_on_a_wood_framed_deck_fails():
    """The whole point of deriving the load: 420 plf against the ~50 plf a deck rim was
    drawn for. The fix hint names the two real ways out — a hard bearing line, or a lighter
    guard — rather than telling the author to make the number smaller."""
    deck = [(-1.0, -1.0), (10.0, -1.0), (10.0, 1.0), (-1.0, 1.0)]
    findings = masonry_guard_bearing(_ctx(_masonry_layers(), floor_outline=deck))
    assert [f.result for f in findings] == [Result.FAIL]
    assert "FS-DECK" in findings[0].message
    assert "lighter guard" in (findings[0].fix_hint or "")


def test_a_light_guard_on_the_same_deck_passes():
    """The allowance is a load, not a material list: a guard under it may stand on wood.
    Without this the rule would be "masonry guards fail", which is not what it measures."""
    deck = [(-1.0, -1.0), (10.0, -1.0), (10.0, 1.0), (-1.0, 1.0)]
    light = [_Layer("structure", "spf", inch(1.5).meters)]
    findings = masonry_guard_bearing(_ctx(light, floor_outline=deck))
    assert [f.result for f in findings] == [Result.PASS]


def test_a_layer_with_no_density_reports_unknown_rather_than_passing():
    """A load computed from a partial stack is not a load. An AIRGAP is skipped because a
    cavity holds no material; a *solid* layer whose material states no density stops the
    derivation dead."""
    layers = _masonry_layers() + [_Layer("cladding", "mystery-stone", inch(4).meters)]
    deck = [(-1.0, -1.0), (10.0, -1.0), (10.0, 1.0), (-1.0, 1.0)]
    findings = masonry_guard_bearing(_ctx(layers, floor_outline=deck))
    assert [f.result for f in findings] == [Result.UNKNOWN]
    assert "density" in findings[0].message


def test_nothing_under_the_guard_reports_unknown():
    """Never a pass by absence: a guard with nothing modeled under it has an unidentified
    support, which is a different statement from a support that is known to be adequate."""
    findings = masonry_guard_bearing(_ctx(_masonry_layers()))
    assert [f.result for f in findings] == [Result.UNKNOWN]
    assert "nothing modeled under it" in findings[0].message


def test_a_house_with_no_guard_wall_reports_not_applicable():
    ctx = SimpleNamespace(
        plan=SimpleNamespace(all_elements=lambda: [],
                             library=SimpleNamespace(materials=_MATERIALS)),
        model=SimpleNamespace(walls=[], floors=[], solids=[]),
        preferences=Preferences(),
    )
    findings = masonry_guard_bearing(ctx)
    assert [f.result for f in findings] == [Result.NOT_APPLICABLE]


def test_the_deck_guard_rule_counts_a_masonry_parapet_as_a_guard(catlin_ctx):
    """``structural.deck_guard`` must count a masonry parapet as a guard, not just a
    ``Railing`` at the deck elevation."""
    from typehaus.checks.structural.deck import deck_guard

    findings = deck_guard(catlin_ctx)
    assert findings
    assert Result.FAIL not in {f.result for f in findings}, [
        f.message for f in findings if f.result is Result.FAIL]


# --- advisory.cable_guard_deflection --------------------------------------------------------

def _cable_ctx(gap_in, span_in=60):
    from _railing_fixtures import railing, resolve_railings

    guard = railing("RL-CABLE", infill="cable", baluster_spacing=inch(gap_in),
                    post_spacing=inch(span_in))
    model = resolve_railings([guard])
    return SimpleNamespace(plan=SimpleNamespace(all_elements=lambda: [guard]), model=model,
                           preferences=Preferences())


def test_a_four_inch_cable_gap_clears_the_code_and_fails_the_trade_rule():
    """The whole reason this advisory exists: 4" satisfies R312.1.3 on paper and spreads
    under a knee. The finding has to say the code number out loud so a reader does not read
    it as a code failure."""
    from typehaus.checks.advisory.guards import cable_guard_deflection

    findings = cable_guard_deflection(_cable_ctx(4.0))
    assert [f.result for f in findings] == [Result.FAIL]
    assert "4\"" in findings[0].message and "R312.1.3" in findings[0].message
    assert findings[0].severity.value == "warn", "an advisory never blocks the permit gate"


def test_a_three_inch_cable_gap_passes():
    from typehaus.checks.advisory.guards import cable_guard_deflection

    assert [f.result for f in cable_guard_deflection(_cable_ctx(3.0, span_in=48))] == [
        Result.PASS]


def test_the_allowance_tightens_a_quarter_inch_per_foot_of_span_over_four_feet():
    """Deflection scales with the unsupported run, so the rule is a function of the post
    span rather than one number — and it stops tightening before it reaches a cable count
    nobody builds."""
    from typehaus.checks.advisory.guards import max_cable_spacing_in

    assert max_cable_spacing_in(4.0) == pytest.approx(3.25)
    assert max_cable_spacing_in(3.0) == pytest.approx(3.25), "under the reference span"
    assert max_cable_spacing_in(6.0) == pytest.approx(2.75)
    assert max_cable_spacing_in(40.0) == pytest.approx(2.0), "floors out"


def test_a_house_with_no_cable_guard_reports_not_applicable(catlin_ctx):
    """Never a pass by absence: this rule has nothing to say about a picket guard, and
    saying "fine" about a thing it never looked at is how an advisory stops being read.

    N/A rather than UNKNOWN, and the distinction is not cosmetic: the
    check *did* look. It read every Railing in the plan and found none cable-filled, which
    is a verdict about the building, not a confession that an input is missing. A PASS
    would still be the wrong answer, and still is not what this returns.
    """
    from typehaus.checks.advisory.guards import cable_guard_deflection

    findings = cable_guard_deflection(catlin_ctx)
    assert [f.result for f in findings] == [Result.NOT_APPLICABLE]


# --- code.R308_4_4_glass_guard ---------------------------------------------------------------

def _glass_ctx(glazing=None, rail_count=2, path_ft=10.0, materials=None):
    from typehaus.quantities import ft, pt
    from _railing_fixtures import railing, railing_type, resolve_railings

    product = railing_type("RT-GLASS", glazing=glazing)
    guard = railing("RL-GLASS", path=(pt(ft(0), ft(0)), pt(ft(path_ft), ft(0))),
                    infill="panel", type_ref="RT-GLASS", rail_count=rail_count,
                    infill_material="lite")
    model = resolve_railings([guard], types=[product],
                             materials=materials or {"lite": "#8fb7c97a"})
    return SimpleNamespace(
        plan=SimpleNamespace(all_elements=lambda: [guard],
                             library=SimpleNamespace(railing_types=[product])),
        model=model, preferences=Preferences())


def test_laminated_glass_satisfies_the_exception_with_no_top_rail_argument():
    """Two equal plies of the same type hold the broken lite in place, so the guard is still
    a guard — which is exactly why R308.4.4 lets that stand in for the rail."""
    from typehaus.checks.code.mn_residential.glazing import structural_glass_guard

    for glazing in ("laminated", "laminated-tempered"):
        findings = structural_glass_guard(_glass_ctx(glazing, rail_count=0))
        assert [f.result for f in findings] == [Result.PASS], glazing


def test_single_ply_tempered_glass_needs_a_rail_over_three_panels():
    from typehaus.checks.code.mn_residential.glazing import structural_glass_guard

    # 20' at 5'-0" o.c. is four bays, so the top rail spans four lites.
    wide = structural_glass_guard(_glass_ctx("tempered", path_ft=20.0))
    assert [f.result for f in wide] == [Result.PASS], [f.message for f in wide]
    # One 4' bay: the rail spans a single lite, so losing it drops the rail.
    short = structural_glass_guard(_glass_ctx("tempered", path_ft=4.0))
    assert [f.result for f in short] == [Result.FAIL]
    assert "at least 3" in short[0].message
    railless = structural_glass_guard(_glass_ctx("tempered", rail_count=0))
    assert [f.result for f in railless] == [Result.FAIL]


def test_a_product_that_states_no_glazing_reports_unknown():
    """Nothing about a lite's geometry can tell you whether it arrived laminated."""
    from typehaus.checks.code.mn_residential.glazing import structural_glass_guard

    findings = structural_glass_guard(_glass_ctx(None))
    assert [f.result for f in findings] == [Result.UNKNOWN]


def test_an_opaque_sheet_guard_is_not_glazing_and_gets_no_finding():
    """Applicability is the model's own statement that the panel is glass — the infill
    resolving to ``railing_glass`` because its material authored an alpha byte. A steel
    sheet guard is not glazing and R308.4.4 has nothing to say about it."""
    from typehaus.checks.code.mn_residential.glazing import structural_glass_guard

    findings = structural_glass_guard(_glass_ctx("tempered", materials={"lite": "#8fb7c9"}))
    assert [f.result for f in findings] == [Result.NOT_APPLICABLE]
    assert "no guard in the plan is filled with a glass panel" in findings[0].message


# --- edge coverage: the shared helper, and the three findings it opened -----------------


def test_the_shared_helper_projects_onto_a_skew_segment():
    """A 45-degree edge is measured on its own axis, not on x or y.

    The predecessor of this helper indexed ``across``/``along`` as 0/1, so an edge that ran
    diagonally could not be graded at all. Two railing sub-segments covering the middle
    third of a skew edge have to read as the middle third.
    """
    from typehaus.checks.code.mn_residential.fall_protection import _uncovered_runs

    rail = SimpleNamespace(
        tag="RL-X",
        path=(SimpleNamespace(xy_m=(1.0, 1.0)), SimpleNamespace(xy_m=(2.0, 2.0))))
    runs, short, used = _uncovered_runs(
        (0.0, 0.0), (3.0, 3.0), [], [(rail, True)], [],
        gap_tol_m=0.05, plane_tol_m=0.20, wall_face_tol_m=0.05)
    assert used == {"RL-X"} and not short
    assert len(runs) == 2
    assert runs[0] == pytest.approx((0.0, 2.0 ** 0.5), abs=1e-6)
    assert runs[1] == pytest.approx((2.0 * 2.0 ** 0.5, 3.0 * 2.0 ** 0.5), abs=1e-6)


def test_a_guard_covering_only_the_middle_no_longer_passes_the_whole_edge():
    """The bug the old ``_railing_runs_edge`` was: distance to the WHOLE segment.

    A guard sitting on the middle of a 10 m edge is 0 m from it, so the retired boolean
    reported the entire edge guarded. Coverage reports the two ends, which is what a builder
    would see standing there.
    """
    from typehaus.checks.code.mn_residential.fall_protection import _uncovered_runs

    rail = SimpleNamespace(
        tag="RL-MID",
        path=(SimpleNamespace(xy_m=(0.0, 4.0)), SimpleNamespace(xy_m=(0.0, 6.0))))
    runs, _short, _used = _uncovered_runs(
        (0.0, 0.0), (0.0, 10.0), [], [(rail, True)], [],
        gap_tol_m=0.30, plane_tol_m=0.20, wall_face_tol_m=0.05)
    assert runs == [(0.0, 4.0), (6.0, 10.0)]


def test_the_porch_guards_doorway_is_the_stair_throat_and_not_an_open_side(catlin_ctx):
    """``RL-SG-PORCH``'s east leg carries a 3'-0" hole and the check has to see it as one.

    The two pieces of the split guard cover 0'..5.2' and 8.2'..8.7' of the porch deck's east
    edge; the 3'-0" between them is exactly ``ST-SG-PORCH``'s throat, which is the stairway
    rather than an open side. The assertion that matters is the *derivation*: with the
    flight's throat removed the same edge reports the doorway as unguarded, so the PASS is
    earned by the stair being there and not by the old midpoint accident.
    """
    from typehaus.checks.code.mn_residential import edge_coverage as ec
    from typehaus.checks.code.mn_residential import fall_protection as fp
    from typehaus.model.structure import Railing
    from typehaus.quantities import inch as _inch

    deck = next(f for f in catlin_ctx.model.floors if f.tag == "FS-SG-PORCH")
    surface = deck.deck_z1_m
    ring = list(deck.deck_outline)
    east = next((a, b) for a, b in zip(ring, ring[1:] + ring[:1], strict=True)
                if a[0] == b[0] and a[0] == max(p[0] for p in ring))
    closures = ec._closures_at(catlin_ctx, surface)
    rails = [(r, r.height.meters + 1e-9 >= _inch(36).meters)
             for r in catlin_ctx.plan.all_elements()
             if isinstance(r, Railing) and abs(r.base_elevation.meters - surface) < 0.15]
    kwargs = dict(gap_tol_m=fp._EDGE_GAP_TOL_M, plane_tol_m=fp._EDGE_RAILING_PLANE_TOL_M,
                  wall_face_tol_m=fp._EDGE_WALL_FACE_TOL_M)
    quads = ec._stair_throat_quads(catlin_ctx, surface)
    with_stair, _s, _u = ec._uncovered_runs(*east, closures, rails, quads, **kwargs)
    assert with_stair == []
    without_stair, _s, _u = ec._uncovered_runs(*east, closures, rails, [], **kwargs)
    opening = max(hi - lo for lo, hi in without_stair)
    assert opening == pytest.approx(inch(36).meters, abs=0.02)


def test_the_replacement_garage_landing_is_in_the_guard_census(catlin_ctx):
    from typehaus.checks.code.mn_residential.fall_protection import raised_surface_guard_height

    findings = {f.message.split(":")[0]: f for f in raised_surface_guard_height(catlin_ctx)}
    assert "SL-G-STEP-0" not in findings
    assert findings["FS-BW-GARAGE"].result is Result.PASS


def test_an_interior_seam_between_two_floor_systems_is_not_an_open_side(catlin_ctx):
    """Two decks of one storey abut across the wall between them and never touch.

    Probed on the edge line, every interior floor boundary in the house reads as a fall to
    grade. The drop is asked *outboard* of the run for exactly this reason, and the main
    floor's four systems have to come back clean.
    """
    from typehaus.checks.code.mn_residential.fall_protection import (
        raised_surface_guard_height,
    )

    findings = {f.message.split(":")[0]: f for f in raised_surface_guard_height(catlin_ctx)}
    for tag in ("FS-M-WEST", "FS-M-MECH", "FS-M-STAIR", "FS-M-EAST", "FS-S-WEST"):
        assert findings[tag].result is Result.PASS, findings[tag].message


# --- R311.7.1 at a stair head that lands on a wall top ---------------------------------


def test_the_porch_stair_head_is_graded_against_its_wall_top(catlin_ctx):
    """``ST-SG-PORCH`` springs from ``W-SG-E1``'s top, which no element models."""
    from typehaus.checks.code.mn_residential.stair_guards import wall_top_landing_width

    findings = wall_top_landing_width(catlin_ctx)
    assert len(findings) == 1, [f.message for f in findings]
    assert findings[0].result is Result.PASS
    assert "W-SG-E1" in findings[0].message and "36.0\"" in findings[0].message


def test_a_column_on_the_wall_top_splits_the_threshold():
    """The north-strip drawing this rule exists for: a 12" round on a 12" wall.

    It filled the top edge to edge, leaving 10" of passage one side and 14" the other, and
    every check in the engine passed it. The clear width is the WIDER passage, not their
    sum — you walk through one of them.
    """
    from shapely.geometry import Polygon

    from typehaus.checks.code.mn_residential.stair_guards import _clear_across

    foot = 0.3048
    a, b, travel = (28.5 * foot, -3.5 * foot), (28.5 * foot, -0.5 * foot), (-1.0, 0.0)
    landing = Polygon([a, b, (27.5 * foot, -0.5 * foot), (27.5 * foot, -3.5 * foot)])
    column = Polygon([(27.5 * foot, -3.0 * foot), (28.5 * foot, -3.0 * foot),
                      (28.5 * foot, -2.0 * foot), (27.5 * foot, -2.0 * foot)])
    assert _clear_across(landing, a, b, travel) == pytest.approx(inch(36).meters, abs=1e-4)
    assert (_clear_across(landing.difference(column), a, b, travel)
            == pytest.approx(inch(18).meters, abs=1e-4))


def test_the_open_connector_has_real_guards_instead_of_glazing_credit(catlin_ctx):
    from typehaus.checks.code.mn_residential import fall_protection as fp

    findings = {f.message.split(":")[0]: f for f in fp.raised_surface_guard_height(catlin_ctx)}
    assert findings["FS-BW-FLOOR"].result is Result.PASS
    assert catlin_ctx.plan.by_tag("GL-BW-WALL-W") is None
    # `RL-BW-SCREEN` went on 2026-09-10 with the metal guard it named: the west edge is
    # closed by `W-BW-SCREEN`, a solid sheathed panel, and a Railing standing 1 1/2" off it
    # was two elements doing one job. The edge is still guarded and still graded — by the
    # wall's own 4'-0" of height, which is what this now reads.
    assert catlin_ctx.plan.by_tag("RL-BW-SCREEN") is None
    panel = catlin_ctx.plan.by_tag("W-BW-SCREEN")
    assert panel is not None and panel.guard
    assert panel.top.inches >= 36


def _closing_tags(ctx, surface):
    from typehaus.checks.code.mn_residential import edge_coverage as ec

    return {solid.tag for solid in ctx.model.solids
            if solid.category in ec._ENCLOSING_SOLID_CATEGORIES
            and solid.z0_m <= surface + 0.1
            and solid.z1_m >= surface + inch(36).meters - 0.02}


# --- a slat screen that declares itself the guard ----------------------------------------

def test_a_slat_screen_can_be_the_guard_and_is_graded_on_its_own_gap():
    """``SlatScreen.role="guard"`` puts a screen into every R312 population.

    Catlin does not use this today — its west screen sits ABOVE a solid guard wall and stays
    `role="screen"` — and that is exactly why the capability needs its own test rather than
    riding on the reference house. A screen of on-edge slats at a clear gap under 4",
    standing at a raised edge, satisfies R312.1 on its own terms; before this existed the
    only way to model one was to stand a redundant Railing an inch away from it.

    The two halves both matter: the screen must appear in ``guard_lines`` (so the coverage
    derivations can close an edge with it) and it must carry its ``clear_gap`` through as the
    sphere dimension (so it is graded on a number it already states, not on the claim).
    """
    from typehaus.checks.guard_lines import guard_lines
    from typehaus.model.screens import SlatScreen
    from typehaus.quantities import ft, inch, pt

    def screen(role):
        return SlatScreen(uid="SC00000001", tag="SC-TEST", start=pt(ft(0), ft(0)),
                          end=pt(ft(0), ft(8)), base_elevation=ft(0), height=inch(42),
                          slat_face=inch(1.5), slat_depth=inch(3.5), clear_gap=inch(1.5),
                          assembly="POST_KDAT", supported_by="BM-TEST", role=role)

    plan = SimpleNamespace(all_elements=lambda: [screen("screen")])
    assert guard_lines(plan) == []

    plan = SimpleNamespace(all_elements=lambda: [screen("guard")])
    lines = guard_lines(plan)
    assert [line.tag for line in lines] == ["SC-TEST"]
    assert lines[0].height.inches == pytest.approx(42)
    assert lines[0].baluster_spacing.inches == pytest.approx(1.5)
    assert lines[0].infill == "balusters"
    assert len(lines[0].path) == 2
