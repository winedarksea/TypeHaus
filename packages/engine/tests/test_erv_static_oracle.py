"""``mep.erv_static_budget`` against its hand-worked oracle.

``houses/catlin/notes/erv_static_budget.md`` is the independent pass: Darcy-Weisbach with a
Colebrook friction factor, worked term by term from the resolved geometry and from ASHRAE
Fundamentals Ch. 21, before the check was encoded. A calculation that only agrees with
itself is not verified, so the numbers below are read off that note and not off the code.

Three groups:

* the *arithmetic*, on a synthetic model small enough to redo by hand in a line;
* the *schema*, which refuses a mistranscribed fan curve at load time;
* the *live house*, whose worst path and delivered flow are the note's §6.
"""

from __future__ import annotations

import math

import pytest
from _helpers import check_context

from typehaus.checks.mep.erv_static import (
    PA_PER_IN_WG,
    _delivered,
    _friction_factor,
    _interpolate,
    erv_static_budget,
)
from typehaus.findings import Result

# --- the curve the whole note reads ------------------------------------------------------
#: The Broan B210E75RT's published curve, note §Sources. Duplicated here deliberately: a
#: test that read it off the house would agree with the house however wrong the house is.
_BROAN_CURVE = ((0.1, 214.0), (0.2, 210.0), (0.3, 208.0), (0.4, 206.0), (0.5, 201.0),
                (0.6, 199.0), (0.7, 195.0), (0.8, 191.0), (1.0, 184.0), (1.2, 176.0))


# --- 1. the arithmetic, by hand ----------------------------------------------------------

def test_the_friction_factor_matches_the_notes_colebrook_solution() -> None:
    """Note §3's f column: 0.0324 for the 25 cfm PLANT radial, 0.0225 for a 210 cfm trunk."""
    # 4" galvanized at 25 cfm: V = 286.5 fpm, D = 0.3333 ft, nu = 1.63e-4 ft2/s
    reynolds = (286.5 / 60.0) * 0.33333 / 1.63e-4
    assert reynolds == pytest.approx(9764, rel=1e-3)
    assert _friction_factor(reynolds, 0.0003 / 0.33333) == pytest.approx(0.0324, abs=5e-4)
    # 6" galvanized at 210 cfm: V = 1069.5 fpm, D = 0.5 ft
    reynolds = (1069.5 / 60.0) * 0.5 / 1.63e-4
    assert reynolds == pytest.approx(54679, rel=1e-3)
    assert _friction_factor(reynolds, 0.0003 / 0.5) == pytest.approx(0.0225, abs=5e-4)


def test_a_laminar_branch_uses_hagen_poiseuille_and_not_colebrook() -> None:
    """Note §3: six of the 23 radials run below Re 4,000 and ``DU-A-ERV-R-BED3`` at 5 cfm is
    outright laminar at Re ~1,950. f = 64/Re is exact there; Colebrook is not valid at all,
    and reporting the regime as a gap in the MODEL would be reporting the correlation's
    limitation as the building's."""
    assert _friction_factor(1953.0, 0.0009) == pytest.approx(64.0 / 1953.0)
    # And in the transitional band the turbulent value at the band's top is used, so a run
    # at Re 3,000 resolves rather than reporting nothing.
    assert _friction_factor(3000.0, 0.0009) == pytest.approx(
        _friction_factor(4000.0, 0.0009))


def test_the_plant_branch_reproduces_the_notes_worst_radial() -> None:
    """Note §6's first two rows, redone from §2's formula alone.

    25 cfm, 4" bore, 53.00 ft developed, 3 elbows at the 2'-6" equivalent length §2 derives.
    """
    bore = 4.0 / 12.0
    area = math.pi * bore * bore / 4.0
    velocity = 25.0 / area
    velocity_pressure = (velocity / 4005.0) ** 2
    reynolds = (velocity / 60.0) * bore / 1.63e-4
    factor = _friction_factor(reynolds, 0.0003 / bore)
    effective = 53.00 + 3 * 2.5
    assert factor * (effective / bore) * velocity_pressure == pytest.approx(0.0301, abs=5e-4)


def test_the_ea_trunk_is_the_single_largest_term_in_the_budget() -> None:
    """Note §6: ``DU-ERV-EA`` alone is 0.1666 in. w.g., a third of the whole path, and §6's
    flex comparison is why the material is rigid pipe."""
    bore = 0.5
    area = math.pi * bore * bore / 4.0
    velocity_pressure = ((210.0 / area) / 4005.0) ** 2
    reynolds = ((210.0 / area) / 60.0) * bore / 1.63e-4
    rigid = _friction_factor(reynolds, 0.0003 / bore) * ((29.32 + 5 * 4.5) / bore) \
        * velocity_pressure
    flex = _friction_factor(reynolds, 0.003 / bore) * ((29.32 + 5 * 7.0) / bore) \
        * velocity_pressure
    assert rigid == pytest.approx(0.1666, abs=1e-3)
    assert flex == pytest.approx(0.3082, abs=2e-3)
    # Note §6: flex costs about three times the static of rigid pipe in the same wrap, and
    # on this one run alone it would take the delivered flow under MN's 205 cfm.
    assert flex / rigid > 1.8


def test_a_component_curve_is_read_linearly_between_its_authored_points() -> None:
    """Note §5's addendum: a chord across a Q^2 curve sits above it, which is the
    conservative direction and is why §6's terminal reads 10.55 Pa where Q^2 gives 10.16."""
    terminal = ((10.0, 1.6), (20.0, 6.5), (30.0, 14.6))
    assert _interpolate(terminal, 25.0) == pytest.approx(10.55)
    assert 10.55 > 6.5 * (25.0 / 20.0) ** 2
    plenum = ((60.0, 0.5), (120.0, 1.8), (210.0, 5.5))
    assert _interpolate(plenum, 146.0) == pytest.approx(2.869, abs=1e-3)


def test_the_unit_bridge_is_the_one_the_note_uses() -> None:
    assert pytest.approx(249.089) == PA_PER_IN_WG


# --- 2. the curve, and the refusal to extrapolate -----------------------------------------

def test_the_curve_is_read_by_interpolation_at_the_notes_governing_static() -> None:
    """Note §6: 0.4593 in. w.g. lands between (0.4, 206) and (0.5, 201) at 203.0 cfm."""
    assert _delivered(_BROAN_CURVE, 0.4593) == pytest.approx(203.0, abs=0.1)
    assert _delivered(_BROAN_CURVE, 0.4) == pytest.approx(206.0)
    assert _delivered(_BROAN_CURVE, 0.05) == pytest.approx(214.0), \
        "below the first point the curve is clamped, not extrapolated upward"


def test_past_the_last_point_it_refuses_to_extrapolate() -> None:
    """A curve stops where the manufacturer stopped measuring. A straight-line continuation
    past 1.2 in. w.g. would be the check's invention, not the machine's behaviour."""
    assert _delivered(_BROAN_CURVE, 1.25) is None


def test_the_validator_refuses_a_mistranscribed_fan_curve() -> None:
    """A curve is a table and the two ways it goes wrong are not facts about a building that
    a Finding could report — they are facts about the typing, so they are a load-time error."""
    from typehaus.model.types import EquipmentType
    from typehaus.quantities import inch

    def build(curve):
        return EquipmentType(tag="EQ-T-X", name="x", footprint=(inch(1), inch(1)),
                             height=inch(1), fan_curve=curve)

    build(((0.1, 214.0), (0.2, 210.0)))  # the minimum valid curve
    with pytest.raises(ValueError, match="at least two points"):
        build(((0.4, 206.0),))
    with pytest.raises(ValueError, match="strictly increase"):
        build(((0.2, 210.0), (0.2, 208.0)))
    with pytest.raises(ValueError, match="strictly increase"):
        build(((0.4, 206.0), (0.2, 210.0)))
    with pytest.raises(ValueError, match="must not rise with static"):
        build(((0.2, 206.0), (0.4, 210.0)))


# --- 3. the live house --------------------------------------------------------------------

def _findings(catlin_model_ro):
    return erv_static_budget(check_context(model=catlin_model_ro))


def _machine_finding(catlin_model_ro):
    return next(f for f in _findings(catlin_model_ro) if "worst path" in f.message)


def test_the_broan_carries_the_whole_published_curve(catlin_plan) -> None:
    broan = next(t for t in catlin_plan.library.equipment_types
                 if t.tag == "EQ-T-BROAN-B210E75RT")
    assert broan.fan_curve == _BROAN_CURVE
    assert broan.fan_curve_max_static_in_wg == pytest.approx(1.3)


def test_the_governing_side_is_extract_again(catlin_model_ro) -> None:
    """Note §6, and the governing SIDE swapped THREE times on 2026-09-15.

    The machine's curve is an external static PER SIDE, so what governs is the worse of two
    paths and never their sum. In order:

    * extract governed at 0.4169 after the 265 -> 210 cfm rebalance took the worst radial off
      ``DU-M-ERV-R-PLANT`` (a 5x cut in flow is a 25x cut in friction);
    * ``DU-ERV-EA`` 6" -> 8" took the discharge term from 0.1666 to 0.0490 and the column to
      0.3548, handing the lead to SUPPLY at 0.4064 — of which only the first 0.0086 in. ever
      reached the delivered figure, exactly as §6 had predicted before the change was bought;
    * both hoods then moved to the NORTH face, which let ``DU-ERV-OA`` go 6" -> 8" as well
      (0.1318 -> 0.0315) and handed the lead **back to extract** at 0.3495 against supply's
      0.3061.

    The assertion is written this way round because what matters is the LEVER, not the
    number. With extract in front by 0.0434 in., the two extract levers that were worth
    nothing after the second swap — the elbow audit and riser segmentation — are worth
    something again, up to that gap. §6 says so.
    """
    message = _machine_finding(catlin_model_ro).message
    assert "extract side via DU-B-ERV-R-SAUNA-EXH" in message
    assert "supply side" not in message


def test_the_static_and_the_delivered_flow_are_the_notes(catlin_model_ro) -> None:
    """Note §6: 0.3495 in. w.g. and 207.0 cfm, on the EXTRACT side.

    Hand-worked in the note before this assertion was changed, which is the order that makes
    it an oracle. Extract column, term by term: ``DU-B-ERV-R-SAUNA-EXH`` 0.0135 + terminal
    6.50/249.089 + plenum 0.50/249.089 + ``DU-ERV-RISER-EXH`` 0.2028 + ``DU-B-ERV-RET-TRUNK``
    0.0614 + ``DU-ERV-EA`` 0.0437 = **0.3495**. Delivered off the curve between (0.3, 208)
    and (0.4, 206): 208 - 0.495 x 2 = 207.0.

    Supply, for the comparison that decides which side governs: 0.0134 + 0.0361 + 0.0020 +
    ``DU-ERV-OA`` 0.0315 + ``DU-B-ERV-SUP-TRUNK`` 0.0234 + ``DU-ERV-RISER-SUP`` 0.1367 +
    ``DU-S-ERV-HP-FEED`` 0.0630 = 0.3061. Extract leads by 0.0434.

    ** THE CODE MARGIN IS 2.0 cfm. ** 207.0 against MN 1322 R403.5's 205. It was 203.0 —
    BELOW the rate — at the start of the day, then 205.7, and the hoods' move to the north
    face is what bought the rest. It is still thin enough that §8's "measure it at
    commissioning with a low-flow hood" is the operative sentence, and it is the EXTRACT side
    to hood again.
    """
    message = _machine_finding(catlin_model_ro).message
    assert "0.350 in. w.g." in message
    assert "delivering 207 cfm" in message


def test_the_shortfall_against_the_design_rate_is_unknown_and_never_a_fail(
        catlin_model_ro) -> None:
    """``ventilation_cfm`` is 210, which is the curve's value at 0.2 in. w.g. — a design
    intent no real duct system reaches. Whether 203 is ENOUGH is MN 1322 R403.5's question,
    graded by ``code.N1103_6_whole_house_ventilation`` against 205."""
    finding = _machine_finding(catlin_model_ro)
    assert finding.result is Result.UNKNOWN
    assert "210 cfm design rate" in finding.message


def test_catlin_reports_no_fail_from_this_check(catlin_model_ro) -> None:
    """Every FAIL branch is demonstrated synthetically; the reference house stays clean."""
    assert [f.message for f in _findings(catlin_model_ro) if f.result is Result.FAIL] == []


def test_every_branch_clears_the_products_own_flow_limit(catlin_model_ro) -> None:
    """23 radials all inside ``DUCT-T-GALV-4``'s 50 cfm — a 600 fpm QUIET limit for a branch
    running continuously beside a bed, not the pipe's capacity. The highest is
    ``DU-B-ERV-R-PLAY`` at 30 cfm.

    **24 since D1**, and the extra is ``DU-M-ERV-EXH-TRUNK``: level 2 went trunk-and-branch
    on 2026-09-19 and the trunk is a run like any other, 114 cfm in 8". The ten takeoffs off
    it are still here — ``radial_landings`` follows one hop through a trunk, which it did
    not do the day the trunk was drawn, and ten runs left this budget silently until it
    did."""
    rows = [f for f in _findings(catlin_model_ro) if " carries " in f.message]
    assert len(rows) == 24
    assert all(f.result is Result.PASS for f in rows)
    assert any("DU-M-ERV-EXH-TRUNK carries 114 cfm" in f.message for f in rows)
    for tag in ("DU-M-ERV-R-PLANT", "DU-M-ERV-R-BATH1", "DU-M-ERV-R-KITCH"):
        assert any(f.message.startswith(f"{tag} carries ") for f in rows), tag


def test_the_system_1_trunks_are_not_pulled_into_the_ventilators_budget(
        catlin_model_ro) -> None:
    """Catlin's ducted heat pump shares ``EQ-S-ERV-MIX`` with this machine and its trunks are
    fabricated rectangular sheet metal — not a typed round product, with no roughness anybody
    read. Grading them here would report a gap in a system this check has no business
    grading. A run that DOES state a material and matches no product row stays in."""
    messages = " ".join(f.message for f in _findings(catlin_model_ro))
    for tag in ("DU-S-HP-SUP", "DU-S-HP-RET", "DU-S-HP-SOUTH", "DU-S-HP-SUITE"):
        assert tag not in messages


def test_an_unauthored_duct_product_is_named_by_its_pair_not_defaulted(
        catlin_plan) -> None:
    """A run whose (material, nominal diameter) pair names no ``DuctProductType`` is UNKNOWN
    by that pair. A plausible drop computed from an invented roughness is worse than none,
    because nobody can tell it was invented."""
    stripped = catlin_plan.library.model_copy(update={"duct_product_types": ()})
    plan = catlin_plan.model_copy(update={"library": stripped})
    findings = erv_static_budget(check_context(plan=plan))
    gaps = [f for f in findings if "no DuctProductType for" in f.message]
    assert gaps, "with the catalog emptied every run must report its pair"
    assert all(f.result is Result.UNKNOWN for f in gaps)
    assert any("galvanized, 4.0\"" in f.message for f in gaps)


def test_a_plan_with_no_ventilator_earns_not_applicable(catlin_plan) -> None:
    """N/A is earned from positive evidence of absence — every canvas object inspected and
    none a balanced ventilator — never returned as an empty list."""
    from typehaus.model.enums import EquipmentKind

    elements = [e for e in catlin_plan.all_elements()
                if getattr(e, "kind", None) is EquipmentKind.ERV]
    assert elements, "catlin must have an ERV for this test to mean anything"
    findings = erv_static_budget(check_context(model=_without(catlin_plan, elements)))
    assert [f.result for f in findings] == [Result.NOT_APPLICABLE]


def _without(plan, drop):
    """``plan`` with the named elements removed from every storey."""
    from typehaus.resolve import resolve

    dropped = {e.uid for e in drop}
    elements = {tag: tuple(e for e in group if e.uid not in dropped)
                for tag, group in plan.elements.items()}
    model, _findings = resolve(plan.model_copy(update={"elements": elements}))
    return model
