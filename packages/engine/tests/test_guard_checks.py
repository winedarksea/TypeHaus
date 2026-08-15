"""The three guard rules a drawn infill made possible.

* ``structural.masonry_guard_bearing`` — a masonry parapet is a guard that is also a wall,
  and the load path that buys it (its own weight, on whatever is under it) had no rule.
* ``advisory.cable_guard_deflection`` — R312.1.3 reads 4"; a tensioned cable at 4" fails the
  inspection, because it deflects about a quarter of its spacing under load.
* ``code.R308_4_4_glass_guard`` — glass used *as* the guard, which R308.4's location test
  never reaches.

The porch guard is three ``FoundationWall``s rather than three ``Railing``s, and that is the
right call: it keeps its four-layer stucco/CMU/air/brick stack, the grouted cores that hold
the balcony pillar bases, and its cubic-yard take-off. What it costs is a load path nobody
was asking about — a 42" grouted-CMU-and-brick parapet runs about 420 plf, and a wood deck
rim designed to R507's 40 psf live + 10 psf dead cannot carry that. The load is derived from
the guard's own assembly, so these tests check the arithmetic against the catalog rather than
against a magic number, and check that a stack the catalog cannot weigh reports UNKNOWN
rather than a comfortable pass.
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

#: The porch parapet at the 3'-6" the plan set draws it, rather than at its resolved
#: 3'-6 15/16" (the railing top sits a shade over the porch top).
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


def _guard_wall(catlin_ctx, tag="W-SG-RAIL-F"):
    return next(w for w in catlin_ctx.model.walls if w.tag == tag)


def test_the_porch_parapet_weighs_what_its_own_layers_weigh(catlin_ctx):
    """~120 psf of face x 3'-6" = ~420 plf. Every term comes from the catalog: 7-5/8" of
    2000 kg/m3 grouted CMU, 3-5/8" of 1920 kg/m3 white brick, 1/2" of 1900 kg/m3 stucco —
    and the 1" air gap, which weighs nothing and is skipped rather than treated as a
    material whose density nobody stated."""
    load = _dead_load_plf(catlin_ctx, _guard_wall(catlin_ctx), GUARD_HEIGHT_M)
    assert load == pytest.approx(420.0, rel=0.05)


def test_all_three_porch_parapets_pass_on_the_concrete_under_them(catlin_ctx):
    """They land on the sunken-garden walls and the arch — concrete the whole run. This is
    the finding that makes the FAIL below meaningful: the rule is not simply failing every
    masonry guard it sees."""
    findings = [f for f in masonry_guard_bearing(catlin_ctx)]
    assert sorted(f.element_tags[0] for f in findings) == [
        "W-SG-RAIL-E", "W-SG-RAIL-F", "W-SG-RAIL-W"]
    assert {f.result for f in findings} == {Result.PASS}
    for finding in findings:
        assert "[advisory, not engineering]" in finding.message, (
            "a prescriptive load lookup is not an engineered design and must say so")


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


def test_a_house_with_no_guard_wall_reports_unknown():
    ctx = SimpleNamespace(
        plan=SimpleNamespace(all_elements=lambda: [],
                             library=SimpleNamespace(materials=_MATERIALS)),
        model=SimpleNamespace(walls=[], floors=[], solids=[]),
        preferences=Preferences(),
    )
    findings = masonry_guard_bearing(ctx)
    assert [f.result for f in findings] == [Result.UNKNOWN]


def test_the_deck_guard_rule_counts_a_masonry_parapet_as_a_guard(catlin_ctx):
    """``structural.deck_guard`` used to look only for a ``Railing`` at the deck elevation,
    so a deck guarded by a masonry parapet failed for having no element of the one class it
    knew about."""
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


def test_a_house_with_no_cable_guard_reports_unknown(catlin_ctx):
    """Never a pass by absence: this rule has nothing to say about a picket guard, and
    saying "fine" about a thing it never looked at is how an advisory stops being read."""
    from typehaus.checks.advisory.guards import cable_guard_deflection

    findings = cable_guard_deflection(catlin_ctx)
    assert [f.result for f in findings] == [Result.UNKNOWN]


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
    assert [f.result for f in findings] == [Result.UNKNOWN]
    assert "no guard in the plan is filled with a glass panel" in findings[0].message
