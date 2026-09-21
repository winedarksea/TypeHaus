"""The exported analytical model, solved in an independent solver, reproduces the notes.

``houses/catlin/notes/analytical_model_basis.md`` states the boundary conditions and load
cases as claims and hand-solves the balcony bent. This test builds the graph, solves it in
PyNite and checks the reactions against the numbers the engineering records already carry —
the same rule as every other calculation here (a model that only agrees with itself is not
verified), applied to a model instead of a number.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from typehaus.analytical.build import build_analytical_model
from typehaus.analytical.graph import Fixity, LoadCaseKind
from typehaus.analytical.solve import solve
from typehaus.cli.engineering_load import load_engineering
from typehaus.engineering.pier_basis import cast_piers

HOUSE = Path(__file__).resolve().parents[3] / "houses" / "catlin"
N_TO_LB = 1 / 4.4482216152605
NM_TO_LB_FT = N_TO_LB / 0.3048
PLF_TO_N_M = 4.4482216152605 / 0.3048

#: The four balcony moment columns the note hand-solves (§3a–3c).
BALCONY = ("PT-SG-BF1", "PT-SG-BF3", "PT-SG-BR1", "PT-SG-BR3")


@pytest.fixture(scope="module")
def solved():
    load = load_engineering(HOUSE)
    model = build_analytical_model(load.ctx)
    result = solve(model)
    piers = {p.tag: p for p in cast_piers(load.ctx)}
    return load, model, result, piers


def _support(model, tag):
    hits = [s for s in model.supports if s.element_tag == tag]
    assert hits, f"no support on {tag}"
    return hits[0]


def _moment_lb_ft(reaction) -> float:
    return max(abs(reaction.mx_nm), abs(reaction.my_nm)) * NM_TO_LB_FT


def test_the_catlin_graph_is_stable(solved):
    _, _, result, _ = solved
    assert result.stable, result.warnings


def test_every_lateral_system_column_is_fixed_and_nothing_else_is(solved):
    _, model, _, piers = solved
    for tag, pier in piers.items():
        support = _support(model, tag)
        expected = Fixity.FIXED if pier.lateral_system else Fixity.PINNED
        assert support.fixity is expected, (tag, support.basis)
        if pier.lateral_system:
            assert "wind" in support.basis.lower()


#: The record's lever is the AUTHORED post height; the model's column runs base to beam
#: centreline, which on catlin is 1.0-1.1 % shorter (8.92' vs 9.01', 9.08' vs 9.18'). Note §3a.
LEVER_TOLERANCE = 0.03


@pytest.mark.parametrize("tag", BALCONY)
def test_balcony_wind_base_moment_matches_the_note(solved, tag):
    """§3a: 153.4 lb at the deck plane x the column = 1,385 lb-ft (front), 1,410 (rear)."""
    _, model, result, piers = solved
    reaction = result.reactions[(_support(model, tag).node, LoadCaseKind.WIND.value)]
    assert _moment_lb_ft(reaction) == pytest.approx(piers[tag].wind_base_moment_lb_ft,
                                                    rel=LEVER_TOLERANCE)
    assert piers[tag].wind_base_moment_lb_ft == pytest.approx(
        1385 if tag.startswith("PT-SG-BF") else 1410, abs=5)


@pytest.mark.parametrize("tag", BALCONY)
def test_balcony_guard_base_moment_matches_the_note(solved, tag):
    """§3b: 200 lb x (9.01' + 3.5') = 2,502 lb-ft at a front column."""
    _, model, result, piers = solved
    reaction = result.reactions[(_support(model, tag).node, LoadCaseKind.GUARD.value)]
    assert _moment_lb_ft(reaction) == pytest.approx(piers[tag].guard_base_moment_lb_ft,
                                                    rel=LEVER_TOLERANCE)


@pytest.mark.parametrize("front,rear", (("PT-SG-BF1", "PT-SG-BR1"), ("PT-SG-BF3", "PT-SG-BR3")))
def test_balcony_gravity_reactions_match_the_records(solved, front, rear):
    """§3c: the PAIR carries what the records say (statics, 1 %); the frame redistributes it.

    The beam is continuous over both columns with a longer rear cantilever, so the solve
    hands the rear column ~10 % more than the record's equal split. That is a finding about
    the record, not a solver error, and the note carries it; here each column is bounded at
    15 % and the pair at 1 %.
    """
    load, model, result, piers = solved
    pair_model = {"dead": 0.0, "live": 0.0}
    pair_record = {"dead": 0.0, "live": 0.0}
    for tag in (front, rear):
        node = _support(model, tag).node
        inputs = {q.name: q.value for q in load.results[f"deck_post/{tag}"].inputs}
        pier = piers[tag]
        self_weight = pier.gross_area_in2 / 144 * pier.height_in / 12 * 150.0
        dead = result.reactions[(node, LoadCaseKind.DEAD.value)].fz_n * N_TO_LB + self_weight
        live = result.reactions[(node, LoadCaseKind.LIVE.value)].fz_n * N_TO_LB
        assert dead == pytest.approx(inputs["dead_load"], rel=0.15)
        assert live == pytest.approx(inputs["live_load"], rel=0.15)
        pair_model["dead"] += dead
        pair_model["live"] += live
        pair_record["dead"] += inputs["dead_load"]
        pair_record["live"] += inputs["live_load"]
    for case in ("dead", "live"):
        assert pair_model[case] == pytest.approx(pair_record[case], rel=0.01)


def test_roof_beam_line_loads_sum_to_the_records_uniform_load(solved):
    """§3d: dead + snow on BM-BW-RE/RW equals `uniform_load` 1,170.9 plf, exactly."""
    load, model, _, _ = solved
    roof_items = [i for i in load.item_ids if i.startswith("roof_beam/")]
    assert roof_items
    for item in roof_items:
        record = load.results[item]
        plf = next(q.value for q in record.inputs if q.name == "uniform_load")
        tag = item.split("/", 1)[1]
        total = sum(abs(load_.w0_n_m) for m in model.members if m.tag == tag
                    for load_ in model.loads_on(m.id)
                    if load_.case in (LoadCaseKind.DEAD, LoadCaseKind.SNOW))
        # A beam split at a seat carries its load on every piece; sum per unit length once.
        pieces = {m.id for m in model.members if m.tag == tag}
        assert total / max(len(pieces), 1) == pytest.approx(plf * PLF_TO_N_M, rel=1e-6)


def test_the_gaps_name_what_the_note_says_is_not_modelled(solved):
    _, model, _, _ = solved
    joined = "\n".join(model.gaps)
    # ``lateral_uplift/RF-HOUSE`` was the fourth of these until 2026-09-14, when the kind
    # retired: RF-HOUSE's uplift is a published read now and raises no item, so there is no
    # id left for a gap line to name. ``rafter/RF-GARAGE`` takes its place — the trussed
    # roof the uplift question folded INTO, which the graph still cannot draw.
    for item in ("retaining_system/W-SG-ARCH", "wall_panel/W-A-N1", "girt_screw/W-A-N1",
                 "rafter/RF-GARAGE"):
        assert item in joined
    assert "lateral_uplift/" not in joined


def test_the_landing_ties_are_springs_on_their_members(solved):
    """§1 / §3e: each deck_tie joint is a DX+DY spring on the member it ties, at NDS
    §11.3.6's slip modulus x 2 bolts, equal — the stiffness the record distributes by."""
    load, model, _, _ = solved
    from typehaus.engineering.deck_tie_basis import wall_ties

    ectx = load.ctx.engineering.context
    joints = wall_ties(ectx, ectx.plan.by_tag("FS-BW-FLOOR"))
    springs = [s for s in model.support_springs if "deck_tie/FS-BW-FLOOR" in s.basis]
    assert len(springs) == 2 * len(joints) == 6
    assert {s.dof for s in springs} == {"DX", "DY"}
    lb_per_in = {round(s.stiffness_n_m * N_TO_LB * 0.0254) for s in springs}
    assert lb_per_in == {190_919}  # 2 x 270,000 x 0.5^1.5
    nodes = {s.node for s in springs}
    assert any("BM-BW-FC:tie" in n for n in nodes) and any("BM-BW-FE:tie" in n for n in nodes)
    # The screen's tie lands on the sill it stands on, at the sill's north end.
    assert any("BM-BW-SCSILL" in n and "tie:W-G-W" in n for n in nodes)
    assert not [g for g in model.gaps if "lands on no member" in g]


def test_the_ties_carry_no_gravity_but_the_graph_hands_them_a_thrust(solved):
    """§3e: the block stands 1/4" off the stem, so no VERTICAL reaction reaches a tie. The
    graph does hand them a horizontal one under gravity — the seat beams' end pieces rise
    0.6' to the carriers over 1.125' (the work-point convention), a thrust the building
    does not have. A finding, pinned so it cannot grow unseen: ~95 lb live at a stem tie (~110
    before the stem ties moved 1 1/4" north with their angles, §3e)."""
    _, model, result, _ = solved
    nodes = {s.node for s in model.support_springs if "deck_tie/" in s.basis}
    assert nodes
    worst = 0.0
    for node in nodes:
        for case in (LoadCaseKind.DEAD.value, LoadCaseKind.LIVE.value):
            reaction = result.reactions[(node, case)]
            assert abs(reaction.fz_n) * N_TO_LB < 1e-6
            worst = max(worst, math.hypot(reaction.fx_n, reaction.fy_n) * N_TO_LB)
    assert worst == pytest.approx(95.2, abs=5.0)
