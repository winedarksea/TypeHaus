"""Phases 3 and 4: honest space and connections, and diagnostics with a cause.

These are the claims the two phases make that are not already pinned by an oracle note.
Each test names the defect it would catch, because a test whose failure nobody can read is
a test somebody deletes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.quantities import M_PER_IN, inch

# --- Phase 3a: duct sizing, the one derivation ---------------------------------------


def test_the_friction_physics_has_exactly_one_home():
    """``erv_static`` must READ ``resolve/duct_sizing``, not hold its own copy.

    The whole point of moving it is that a router sizing a duct and a check grading one
    use the same arithmetic. Two copies drift, and the drift is invisible because both
    answers look plausible.
    """
    from typehaus.checks.mep import erv_static
    from typehaus.resolve import duct_sizing

    assert erv_static._friction_factor is duct_sizing.friction_factor
    assert erv_static._NU_FT2_S == duct_sizing.NU_FT2_S


def test_laminar_and_turbulent_regimes_are_both_exact_at_their_own_rule():
    """Hagen-Poiseuille below 2,300 is exact, not a correlation — assert it as such."""
    from typehaus.resolve.duct_sizing import friction_factor

    assert friction_factor(1950.0, 0.0001) == pytest.approx(64.0 / 1950.0)
    # Colebrook is implicit; the fixed point must satisfy its own equation.
    import math
    factor = friction_factor(50_000.0, 0.001)
    residual = (-2.0 * math.log10(0.001 / 3.7 + 2.51 / (50_000.0 * math.sqrt(factor)))) ** -2
    assert factor == pytest.approx(residual, rel=1e-9)


def test_a_cfm_no_published_row_carries_is_a_refusal_not_the_largest_row(catlin_model):
    """The Phase 0 rule, applied to air: an unknown size is a sentence, never a guess."""
    from typehaus.resolve.duct_sizing import size_for_cfm

    size, reason = size_for_cfm(catlin_model.plan.library, 5000.0, material="galvanized")
    assert size is None
    assert "largest published row" in reason
    assert "0.080" in reason  # the design rate it was measured against


def test_sizing_picks_the_smallest_row_that_clears_the_design_rate(catlin_model):
    library = catlin_model.plan.library
    from typehaus.resolve.duct_sizing import size_for_cfm

    size, basis = size_for_cfm(library, 18.0, material="galvanized")
    assert size is not None
    assert size.nominal_m == pytest.approx(inch(4).meters)
    assert size.rate_in_wg_per_100ft <= 0.08
    assert "in. w.g./100 ft" in basis


def test_the_catlin_erv_trunk_is_undersized_and_the_engine_now_says_so(catlin_model):
    """The house's own ``erv_static_budget.md`` argument, reached from the sizing end.

    210 cfm in 6" galvanized runs far past the 0.08 design rate. This is not a FAIL — an
    authored size is a decision — but it must be *sayable*, because "210 at 0.2 or 206 at
    0.4" is that same fact stated as a fan curve and it took a fortnight of prose.
    """
    from typehaus.resolve.duct_sizing import friction_rate_in_wg_per_100ft

    row = next(r for r in catlin_model.plan.library.duct_product_types
               if r.material == "galvanized"
               and r.nominal_diameter.meters == pytest.approx(inch(6).meters))
    rate = friction_rate_in_wg_per_100ft(210.0, row.bore_diameter.meters, row.roughness_m)
    assert rate > 0.08 * 3


def test_the_house_states_its_own_design_rate():
    from typehaus.checks import load_preferences
    from typehaus.resolve.duct_sizing import friction_rate_from_preferences

    table = load_preferences(Path("houses/catlin")).mep.routing
    assert "duct_friction_in_wg_per_100ft" in table
    assert friction_rate_from_preferences(table) == pytest.approx(0.08)


# --- Phase 3b: packing, the tier reading ----------------------------------------------


def test_two_runs_that_stack_do_not_share_the_bay_width():
    """**The defect this replaces.** Summing every occupant's width made an 11 7/8" floor
    full of two 3" radials that never share an elevation."""
    from typehaus.resolve.mep_packing import Occupant, pack

    low = Occupant("A", 3 * M_PER_IN, 0.0, 3 * M_PER_IN)
    high = Occupant("B", 3 * M_PER_IN, 5 * M_PER_IN, 8 * M_PER_IN)
    stacked = pack(12.5 * M_PER_IN, [low, high])
    assert stacked.taken_m == pytest.approx(3 * M_PER_IN)  # not 6: they do not share
    assert stacked.tier in (("A",), ("B",))

    beside = pack(12.5 * M_PER_IN, [low, Occupant("C", 3 * M_PER_IN, 0.0, 3 * M_PER_IN)])
    assert beside.taken_m == pytest.approx(6 * M_PER_IN)
    assert beside.tier == ("A", "C")


def test_an_oversubscribed_channel_is_reported_as_negative_room():
    from typehaus.resolve.mep_packing import Occupant, pack

    packed = pack(6 * M_PER_IN, [Occupant("A", 4 * M_PER_IN, 0.0, 0.1),
                                 Occupant("B", 4 * M_PER_IN, 0.0, 0.1)])
    assert packed.oversubscribed()
    assert not packed.admits(0.0)


def test_packing_declines_unresolved_occupants_rather_than_raising():
    from typehaus.resolve.mep_packing import Occupant, pack

    packed = pack(0.3, [Occupant("A", 0.0, 0.0, 0.1)])
    assert packed.tier == ()
    assert packed.remaining_m == pytest.approx(0.3)


# --- Phase 3c: ports ------------------------------------------------------------------


def test_a_port_is_approximate_until_it_says_otherwise():
    """The default is the whole point: four ports at one point must not read as exact."""
    from typehaus.model.enums import Service
    from typehaus.model.placeables import PortCertainty, ServicePort

    port = ServicePort(tag="P", service=Service.SUPPLY_AIR,
                       position=(inch(0), inch(0), inch(21.6)), connection_size=inch(6))
    assert port.certainty is PortCertainty.APPROXIMATE
    assert not port.is_exact()
    assert port.section_m() == pytest.approx((inch(6).meters, inch(6).meters))


def test_an_exact_port_states_a_rectangular_section_and_a_direction():
    from typehaus.model.enums import Service
    from typehaus.model.placeables import PortCertainty, ServicePort

    port = ServicePort(tag="P", service=Service.RETURN_AIR,
                       position=(inch(0), inch(0), inch(12)),
                       width=inch(10), depth=inch(8), direction=(0.0, 0.0, 1.0),
                       certainty=PortCertainty.EXACT)
    assert port.is_exact()
    assert port.section_m() == pytest.approx((inch(10).meters, inch(8).meters))


def test_catlin_ports_are_approximate_EXCEPT_the_shop_drawn_collars(catlin_model):
    """The ERV's datasheet gives a FACE, not coordinates, and the model says so: every port
    on a catalog machine is approximate and reports itself that way.

    **The exception is a box THIS house has a shop drawing for** (2026-09-19). The two
    level-2 plenums and the two basement ones are fabricated for catlin and dimension their
    collars, so those ten are EXACT — which is what lets `mep.erv_manifold_ports` grade each
    radial against the collar it lands on instead of against a tally. Nothing in
    `library/hvac.py` dimensions one, and that is deliberate: a collar layout is a shop
    drawing and a reusable part has none.

    The basement pair (D3) states three 4" collars each and two SIX-inch ports — the trunk
    from the machine and the riser from upstairs — and the 6" pair is deliberately NOT in
    this list. A collar is an exact port whose section equals the type's `port_diameter`;
    those two carry no `connection_size` at all, so `mep.equipment_port_service` grades them
    at service level the way it grades the machine's own. The assertion below says the same
    thing a second way: every exact port here is a branch collar.

    ** AND THEN THE WATER HEATER STOPPED BEING ONE (2026-09-20). ** `EQ-B-WH`'s cold and hot
    taps are EXACT and are not collars, which widens the rule rather than breaking it: what
    makes a port exact is that somebody has dimensioned it for THIS house, and a tap this
    house cuts in the field qualifies the same way a fabricated plenum's collar does. The
    PROPH80's sheet publishes the face ("top connections", 3/4" NPT) and no station, so the
    8" spread is the house's own and the ports say so in their notes. The collar assertion
    is therefore now scoped to the ERV boxes, where it is still the thing worth pinning."""
    from typehaus.resolve.mep_ports import placed_ports

    ports = placed_ports(catlin_model)
    assert ports, "catlin places equipment declaring ServicePorts"
    exact = sorted(f"{p.equipment_tag}.{p.port_tag}" for p in ports if p.exact)
    assert exact == ["EQ-B-ERV-MAN-EXH.collar-bath",
                     "EQ-B-ERV-MAN-EXH.collar-bench",
                     "EQ-B-ERV-MAN-EXH.collar-sauna",
                     "EQ-B-ERV-MAN-SUP.collar-gym",
                     "EQ-B-ERV-MAN-SUP.collar-play",
                     "EQ-B-ERV-MAN-SUP.collar-sauna",
                     "EQ-B-WH.cold",
                     "EQ-B-WH.hot",
                     "EQ-M-ERV-MAN-EXH.collar-trunk",
                     "EQ-M-ERV-MAN-SUP.collar-bed",
                     "EQ-M-ERV-MAN-SUP.collar-living",
                     "EQ-M-ERV-MAN-SUP.collar-study"]
    assert all(p.collar for p in ports if p.exact and p.equipment_tag.startswith("EQ-")
               and "ERV" in p.equipment_tag), "an exact ERV port IS a branch collar"
    assert all("approximate" in p.describe() for p in ports if not p.exact)
    assert all("exact" in p.describe() for p in ports if p.exact)


def test_port_at_never_offers_an_approximate_port_to_the_router(catlin_model):
    """Snapping a terminal to a port the datasheet never dimensioned would move the run to
    a coordinate nobody authored — worse than leaving it where its author put it."""
    from typehaus.resolve.mep_ports import placed_ports, port_at

    port = next(p for p in placed_ports(catlin_model) if not p.exact)
    assert port_at(catlin_model, (port.x_m, port.y_m), port.z_m,
                   duct_system=None, tolerance_m=1.0) is None


def test_the_port_verdict_says_it_is_service_level(catlin_model):
    """A reader must be able to tell a machine properly connected from one merely fed."""
    from typehaus.checks import run_from_model
    from typehaus.checks.registry import Preferences

    report = run_from_model(catlin_model, [], preferences=Preferences(),
                            only="mep.equipment_port_service")
    mine = [f for f in report.findings if f.check_id == "mep.equipment_port_service"]
    assert mine
    assert any("service-level verdict" in f.message for f in mine)


def test_connectivity_reports_a_dimensioned_landing_and_never_re_fails_it(catlin_model):
    """``duct_connectivity`` REPORTS how exact a landing is; it never re-FAILs what
    ``mep.equipment_port_service`` already grades.

    It was silent on every machine in catlin until the level-2 plenums were given their
    collars, because there was nothing dimensioned to be near or far from. Now four runs
    land on a stated station and the note appears for them — and for nobody else."""
    from typehaus.checks import run_from_model
    from typehaus.checks.registry import Preferences

    report = run_from_model(catlin_model, [], preferences=Preferences(),
                            only="mep.duct_connectivity")
    mine = [f for f in report.findings if f.check_id == "mep.duct_connectivity"]
    assert mine
    noted = [f for f in mine if "dimensioned port" in f.message]
    assert noted, "the four shop-drawn collars are landed on and the note says so"
    assert all(f.result.value != "fail" for f in noted), (
        "mep.equipment_port_service owns the verdict; this one only reports")


def test_the_port_note_distinguishes_the_spigot_from_the_case():
    """The distinction the note exists for, exercised directly: an end ON the collar and an
    end merely inside the same case both PASS connectivity, and an installer needs to know
    which. Built as a stub rather than by authoring an exact port into catlin, because the
    house's own ports really are approximate and making one exact to test the message would
    be changing the building to suit the test."""
    from typehaus.checks.mep.duct_connectivity import _port_note
    from typehaus.resolve.mep_ports import PlacedPort

    port = PlacedPort("EQ-1", "P-SUP", "supply_air", "supply", 1.0, 2.0, 3.0, exact=True)

    class _Model:
        pass

    class _Ctx:
        model = _Model()

    class _Duct:
        system = "supply"

    # ``_port_note`` imports ``placed_ports`` inside the function, so patching the owning
    # module is what the call actually resolves through.
    import typehaus.resolve.mep_ports as ports_module
    saved = ports_module.placed_ports
    ports_module.placed_ports = lambda _m: [port]
    try:
        on = _port_note(_Ctx(), _Duct(), (1.0, 2.0), 3.0, "EQ-1")
        off = _port_note(_Ctx(), _Duct(), (1.3, 2.0), 3.0, "EQ-1")
        elsewhere = _port_note(_Ctx(), _Duct(), (1.0, 2.0), 3.0, "EQ-2")
    finally:
        ports_module.placed_ports = saved

    assert "an exact connection" in on
    assert "off its dimensioned port" in off and "not to the spigot" in off
    assert elsewhere == "", "a port on a different machine is not this end's business"


# --- Phase 4: diagnostics with a cause -------------------------------------------------


def test_mobility_is_read_off_the_prism_kind_never_guessed_from_a_tag():
    from typehaus.routing.diagnostics import Mobility, mobility_of

    assert mobility_of("run") is Mobility.MOVABLE
    assert mobility_of("opening") is Mobility.FIXED
    assert mobility_of("concrete") is Mobility.FIXED
    assert mobility_of("void") is Mobility.FIXED
    # ``--avoid`` is the caller's own instruction, held apart from "it is concrete".
    assert mobility_of("avoid") is Mobility.UNKNOWN
    assert mobility_of("something new") is Mobility.UNKNOWN


def test_a_refusal_distinguishes_this_search_from_impossibility():
    """The claim Phase 4 exists to make. A router that reports both the same way teaches a
    caller to distrust both."""
    from typehaus.routing.diagnostics import Blocker, Mobility, Refusal

    movable = Refusal("PR-X", "drain", "origin", 3, 30_000,
                      blockers=[Blocker("PR-M-WC-VENT", "run", Mobility.MOVABLE,
                                        1.0, 2.0, 3.0)])
    assert "not a proof of impossibility" in movable.render()
    assert "--counterfactual" in movable.render()
    assert movable.movable()

    sealed = Refusal("PR-X", "drain", "origin", 3, 30_000,
                     blockers=[Blocker("RO-1", "opening", Mobility.FIXED, 1.0, 2.0, 3.0)],
                     established=True)
    assert "established from the geometry" in sealed.render()
    assert not sealed.movable()


def test_a_refusal_carries_its_shortage_and_what_was_tried():
    """A gravity refusal's number and the geometric blocker used to be mutually exclusive;
    both are wanted."""
    from typehaus.routing.diagnostics import Refusal

    refused = Refusal("FX-1", "drain", "root", 400, 900,
                      shortages=("0.25\" under the web 14 ft in",),
                      attempts=("3 alternative(s) asked for", "margin 8 ft"))
    text = refused.render()
    assert "Short by: 0.25\" under the web 14 ft in." in text
    assert "Tried: 3 alternative(s) asked for; margin 8 ft." in text
    assert refused.payload()["shortages"] == ["0.25\" under the web 14 ft in"]


def test_a_blocker_payload_carries_the_conflict_location():
    """Contract 3 wants the exact location and z, not merely a tag."""
    from typehaus.routing.diagnostics import Blocker, Mobility

    payload = Blocker("DU-1", "run", Mobility.MOVABLE, 1.5, 2.5, 3.5).payload()
    assert payload == {"tag": "DU-1", "kind": "run", "mobility": "movable",
                       "x_m": 1.5, "y_m": 2.5, "z_m": 3.5}


def test_a_counterfactual_relaxes_only_movable_blockers_and_says_what_it_is():
    from typehaus.routing.counterfactual import counterfactuals, render
    from typehaus.routing.diagnostics import Blocker, Mobility

    asked: list[frozenset[str]] = []

    def build(extra):
        asked.append(extra)
        return object()

    items = counterfactuals(
        None,
        [Blocker("RO-1", "opening", Mobility.FIXED, 0, 0, 0),
         Blocker("PR-VENT", "run", Mobility.MOVABLE, 0, 0, 0)],
        build=build, search=lambda _space: 340.0, baseline_in=326.0)

    assert asked == [frozenset({"PR-VENT"})], "a fixed prism must never be relaxed"
    assert len(items) == 1
    assert items[0].cost_in == 340.0
    assert items[0].delta_in == pytest.approx(14.0)
    text = " ".join(render(items))
    assert "a route exists if PR-VENT were re-routed" in text
    assert "not a proposal" in text
    assert "still has to go somewhere" in text


def test_a_counterfactual_that_opens_nothing_says_so():
    from typehaus.routing.counterfactual import counterfactuals
    from typehaus.routing.diagnostics import Blocker, Mobility

    items = counterfactuals(None, [Blocker("PR-V", "run", Mobility.MOVABLE, 0, 0, 0)],
                            build=lambda _e: object(), search=lambda _s: None)
    assert items[0].cost_in is None
    assert "does NOT open a lane" in items[0].render()


def test_a_failing_relaxation_never_takes_the_refusal_down_with_it():
    """A counterfactual is a courtesy on top of a diagnosis that already stands."""
    from typehaus.routing.counterfactual import counterfactuals
    from typehaus.routing.diagnostics import Blocker, Mobility

    def explode(_extra):
        raise RuntimeError("lattice too large")

    items = counterfactuals(None, [Blocker("PR-V", "run", Mobility.MOVABLE, 0, 0, 0)],
                            build=explode, search=lambda _s: 1.0)
    assert items[0].cost_in is None
    assert "did not complete" in items[0].note


def test_the_relaxation_budget_is_bounded():
    from typehaus.routing.counterfactual import counterfactuals
    from typehaus.routing.diagnostics import Blocker, Mobility

    many = [Blocker(f"PR-{i}", "run", Mobility.MOVABLE, 0, 0, 0) for i in range(20)]
    items = counterfactuals(None, many, build=lambda _e: object(),
                            search=lambda _s: 1.0, limit=3)
    assert len(items) == 3


# --- Phase 4: the station sweep --------------------------------------------------------


def test_the_sweep_clamps_along_the_wall_and_not_across_it(catlin_model):
    """**The defect this test exists for.** A derived drain point stands off the wall face
    — a WC's flange is over a foot into the room — so clamping the POINT to the wall's plan
    box refuses every station including the drawn one, and the sweep reports "no legal
    station" about a fixture that sweeps perfectly well."""
    from typehaus.cli.cmd_route_sweep import stations
    from typehaus.resolve.mep import _expected_drain_point

    point = _expected_drain_point(catlin_model, "FX-S-SUITEBATH-WC")
    assert point is not None
    found = stations(catlin_model, "FX-S-SUITEBATH-WC", (point[0], point[1], 0.0), 8.0)
    assert len(found) > 1
    offsets = [offset for offset, _p in found]
    assert 0.0 in offsets, "the drawn station must be among the candidates"
    assert max(offsets) <= 8.0 and min(offsets) >= -8.0


def test_the_sweep_walks_its_wall_axis_only(catlin_model):
    """Every station shares the drawn point's across-wall coordinate: a sweep that drifted
    off the wall would be offering positions in the middle of the room."""
    from typehaus.cli.cmd_route_sweep import stations, wall_axis
    from typehaus.resolve.mep import _expected_drain_point

    point = _expected_drain_point(catlin_model, "FX-S-SUITEBATH-WC")
    axis = wall_axis(catlin_model, "W-S-SN3")
    assert axis is not None
    (ux, _uy), _lo, _hi = axis
    found = stations(catlin_model, "FX-S-SUITEBATH-WC", (point[0], point[1], 0.0), 8.0)
    across = [p[1] if abs(ux) > 0.5 else p[0] for _o, p in found]
    assert across == pytest.approx([across[0]] * len(across))


def test_the_sweep_prints_a_fixture_not_a_pipe(catlin_model):
    """The whole point of the sweep is that the ANSWER is a fixture move, so the thing to
    paste is a ``Fixture(...)`` with ``drain_position`` — never a PipeRun."""
    from typehaus.cli.cmd_route_sweep import Station, render

    out = " ".join(render("FX-S-SUITEBATH-WC", [
        Station(0.0, 1.0, 2.0, True, 900.0, 3),
        Station(4.0, 1.1, 2.0, True, 400.0, 1)], catlin_model))
    assert "Fixture(" in out
    assert "drain_position=pt(" in out
    assert "PROPOSED, NOT WRITTEN" in out
    assert "NOT a graded position" in out
    assert "moves the DRAIN POINT, not the fixture" in out
    assert "PipeRun(" not in out


def test_a_sweep_where_nothing_routes_says_the_fixture_is_not_the_problem(catlin_model):
    from typehaus.cli.cmd_route_sweep import Station, render

    out = " ".join(render("FX-X", [Station(0.0, 1.0, 2.0, False, note="blocked"),
                                   Station(2.0, 1.1, 2.0, False, note="blocked")],
                          catlin_model))
    assert "NO station on this wall routes" in out
    assert "the obstruction is not where the fixture stands" in out


def test_the_sweep_does_not_claim_the_drawn_station_is_wrong_when_it_is_best(catlin_model):
    from typehaus.cli.cmd_route_sweep import Station, render

    out = " ".join(render("FX-X", [Station(0.0, 1.0, 2.0, True, 100.0, 0),
                                   Station(2.0, 1.1, 2.0, True, 400.0, 2)], catlin_model))
    assert "already the cheapest" in out
    assert "Fixture(" not in out
