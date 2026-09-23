"""Can the unit turn DOWN to the load — against ``notes/heat_pump_turndown.md``.

``mep.heating_capacity`` asks whether a unit can make enough heat at the design hour, which
is one hour of the year. This asks the other question, and it is the one that decides whether
the house is comfortable in October.

Section by section:

* **§1** — the decomposition. A zone's load at any outdoor temperature, read off the report
  it already has, with the design point reproduced exactly.
* **§2** — Manual S's 0.80 minimum-compressor sizing factor, evaluated across the published
  rows and not only at design.
* **§3** — the crossover temperature: where ``minimum(T) = load(T)``.
* **§4** — the tri-state, including the NOT_APPLICABLE that must be *earned*. Note that
  FAIL is not among the states this check can return at all (note §7).
"""

from __future__ import annotations

import pytest

from typehaus.checks.mep.hvac_sizing import (
    _MAX_MINIMUM_SIZING_FACTOR,
    _crossover_temp_f,
    heat_pump_turndown,
)
from typehaus.findings import Result
from typehaus.model import EquipmentType, HeatPumpRating, RatingBasis, inch
from typehaus.takeoff.hvac import heating_zones

# §2's table, from the note: ``(design load, largest published minimum, the row it is on,
# the Manual S sizing factor that follows, the crossover, the verdict)``.
#
# The factor's denominator is the DESIGN load, because that is what a Manual S sizing factor
# is; walking the whole table is what finds the largest MINIMUM, which is rarely on the
# design row. System 2 passes the cap at 0.60 and still cycles above 27 °F — the rule catches
# gross over-size, the crossover describes the year, and they are not the same statement.
# **Every verdict is PASS**: over the cap the message leads with ``ADVISORY —`` and the
# result does not gate. Owner decision, 2026-09-18 — short-cycling costs efficiency, comfort
# and compressor life, and is not a defect any permit authority grades. The last column is
# whether the advisory fires, not whether the check failed.
_ADVISED = True
_CATLIN = {
    # HP1 was 15,410 / -5.9 °F before WIN-A-S2/-S3 went WT-1436 -> WT-1424 (c3c46cff).
    "EQ-M-HP1-OD": (15_365, 14_000, 5.0, 0.91, -6.1, _ADVISED),
    "EQ-M-HP2-OD": (14_668, 8_800, 5.0, 0.60, 27.1, not _ADVISED),
    "EQ-M-HP3-OD": (1_043, 2_800, 17.0, 2.69, None, _ADVISED),
}


def _findings(ctx):
    return {f.element_tags[0]: f for f in heat_pump_turndown(ctx) if f.element_tags}


def _rating(**kwargs) -> HeatPumpRating:
    kwargs.setdefault("citation", "test fixture")
    kwargs.setdefault("basis", RatingBasis.NEEP)
    return HeatPumpRating(**kwargs)


# --- §1. the load decomposition ---------------------------------------------------------------

def test_the_design_point_is_reproduced_EXACTLY(catlin_ctx) -> None:
    """§1's pinned invariant, and it has to be exact rather than close.

    ``heating_load_at_outdoor_f(design)`` is the same arithmetic the turndown check solves
    the crossover with, so any drift between it and the load ``mep.heating_capacity``
    reports would make the two checks disagree about the same zone at the same hour.
    """
    zones, _ = heating_zones(catlin_ctx.model, catlin_ctx.preferences)
    assert zones
    for zone in zones:
        if not zone.rooms or zone.design_temp_f is None:
            continue
        assert zone.heating_load_at_outdoor_f(zone.design_temp_f) == pytest.approx(
            zone.heating_load_btu_per_hour, abs=1e-6), zone.equipment_tag


def test_the_load_falls_as_it_warms_and_the_ground_term_does_not_move(catlin_ctx) -> None:
    """The decomposition's shape: a ground-coupled component's ΔT is to the soil, which does
    not know what the air is doing. System 2's zone carries 2,412 Btu/h of it (a basement);
    System 1's carries none (second storey and attic), so its load is pure air."""
    zones = {z.equipment_tag: z for z in heating_zones(
        catlin_ctx.model, catlin_ctx.preferences)[0]}
    upstairs = zones["EQ-M-HP1-OD"]
    basement = zones["EQ-M-HP2-OD"]
    assert upstairs.ground_coupled_btuh == pytest.approx(0.0)
    assert basement.ground_coupled_btuh == pytest.approx(2_412, rel=0.01)
    for zone in (upstairs, basement):
        assert (zone.heating_load_at_outdoor_f(47.0)
                < zone.heating_load_at_outdoor_f(5.0)
                < zone.heating_load_at_outdoor_f(-22.0))
    # And the ground term is the floor the air term sits on: at the interior setpoint the
    # air ΔT is zero and only the ground remains.
    setpoint = basement.design_temp_f + basement._air_delta_at_design
    assert basement.heating_load_at_outdoor_f(setpoint) == pytest.approx(
        basement.ground_coupled_btuh)


# --- §2. the sizing factor, across the rows ---------------------------------------------------

def test_the_manual_s_verdict_on_all_three_catlin_systems(catlin_ctx) -> None:
    """§2's table. **The check that the audit was written to produce**, and the answer it
    gives is the one a scalar structurally could not: System 1 PASSes
    ``mep.heating_capacity`` with a +6,743 Btu/h margin and short-cycles anyway.

    **Nothing here FAILs**, and that is the owner's call recorded in the note's §7: an
    over-sized unit is not ideal and it is not a reason to call a whole house failing. The
    arithmetic is reported in full; it just does not gate.
    """
    rows = _findings(catlin_ctx)
    assert set(rows) == set(_CATLIN)
    for tag, (load, minimum, at_f, factor, _crossover, advised) in _CATLIN.items():
        finding = rows[tag]
        assert finding.result is Result.PASS, tag
        assert f"minimum output {minimum:,.0f} Btu/h (at {at_f:g} °F)" in finding.message, tag
        assert f"sizing factor of {factor:.2f}" in finding.message, tag
        assert f"{load:,.0f} Btu/h design load" in finding.message, tag
        assert finding.message.startswith("ADVISORY — ") is advised, tag
        assert ("SHORT-CYCLING" in finding.message) is advised, tag


def test_the_binding_row_is_NOT_the_design_row(catlin_ctx) -> None:
    """**The reason the check walks the whole table.** An inverter's floor moves with
    outdoor temperature and is rarely highest at the design row: Systems 1 and 2 have their
    largest published minimum at 5 °F and System 3 at 17 °F, and none of the three designs
    there.

    A check that read only the design row would report System 1 at 13,556 Btu/h interpolated
    (factor 0.88) instead of the 14,000 it will actually be asked to sit at.
    """
    rows = _findings(catlin_ctx)
    for tag, (_load, _minimum, at_f, *_rest) in _CATLIN.items():
        assert f"(at {at_f:g} °F)" in rows[tag].message, tag
        assert "(at -15 °F)" not in rows[tag].message, tag


def test_the_cap_is_manual_s_and_is_stated_in_btu_per_hour_too(catlin_ctx) -> None:
    """0.80 as a ratio is a number nobody can act on; ``12,292 Btu/h against this zone's
    15,365`` is one an equipment selector can shop against."""
    assert _MAX_MINIMUM_SIZING_FACTOR == 0.80
    finding = _findings(catlin_ctx)["EQ-M-HP1-OD"]
    assert "Manual S caps it at 0.80" in finding.message
    assert f"{0.80 * 15_365:,.0f} Btu/h".replace(",", ",") in finding.message


# --- §3. the crossover ------------------------------------------------------------------------

def test_the_crossover_is_the_sentence_an_owner_can_act_on(catlin_ctx) -> None:
    """§3. "It modulates down to the load only below −6.1 °F" is a fact about this
    building's year; "minimum sizing factor 0.91" is one nobody can act on.

    **Reported on a PASS as well**, and System 2 is why: it passes the Manual S cap at 0.60
    and still cycles above 27.1 °F, which is most of a Minnesota heating season. The rule
    catches gross over-size; the crossover describes the year.
    """
    zones = {z.equipment_tag: z for z in heating_zones(
        catlin_ctx.model, catlin_ctx.preferences)[0]}
    rows = _findings(catlin_ctx)
    for tag, (*_rest, crossover, _advised) in _CATLIN.items():
        if crossover is None:
            assert "never meets the load anywhere" in rows[tag].message, tag
            continue
        assert f"below {crossover:.1f} °F" in rows[tag].message, tag
        zone = zones[tag]
        with_minimum = [r for r in zone.heating_ratings if r.minimum_btuh is not None]
        assert _crossover_temp_f(zone, with_minimum) == pytest.approx(crossover, abs=0.05)


def test_a_unit_whose_minimum_never_reaches_the_load_reports_no_crossover(
        catlin_ctx) -> None:
    """System 3: a 2,700 Btu/h floor against a zone that peaks at 932 Btu/h. There is no
    temperature in the published range at which it settles, and the check says so rather
    than extrapolating one out of the table."""
    zones = {z.equipment_tag: z for z in heating_zones(
        catlin_ctx.model, catlin_ctx.preferences)[0]}
    zone = zones["EQ-M-HP3-OD"]
    with_minimum = [r for r in zone.heating_ratings if r.minimum_btuh is not None]
    assert _crossover_temp_f(zone, with_minimum) is None


# --- §4. the tri-state ------------------------------------------------------------------------

def _single_stage() -> EquipmentType:
    return EquipmentType(
        tag="EQ-T-SINGLE", name="Single-stage heat pump",
        footprint=(inch(30), inch(15)), height=inch(30),
        heating_ratings=(
            _rating(outdoor_db_f=5.0, minimum_btuh=18000, rated_btuh=18000,
                    maximum_btuh=18000),
            _rating(outdoor_db_f=47.0, minimum_btuh=24000, rated_btuh=24000,
                    maximum_btuh=24000),
        ))


def _no_minimum() -> EquipmentType:
    return EquipmentType(
        tag="EQ-T-NOMIN", name="Heat pump with no published minimum",
        footprint=(inch(30), inch(15)), height=inch(30),
        heating_ratings=(
            _rating(outdoor_db_f=5.0, maximum_btuh=18000,
                    basis=RatingBasis.MANUFACTURER),
            _rating(outdoor_db_f=47.0, maximum_btuh=24000,
                    basis=RatingBasis.MANUFACTURER),
        ))


def _swap_type(ctx, equipment_tag: str, product: EquipmentType):
    """``ctx`` with one unit's type replaced — the zone geometry is catlin's, the machine
    is the fixture's."""
    import dataclasses

    library = ctx.plan.library
    types = tuple(product if item.tag == _type_of(ctx, equipment_tag) else item
                  for item in library.equipment_types)
    # Retag the fixture to the tag the equipment actually references.
    types = tuple(item.model_copy(update={"tag": _type_of(ctx, equipment_tag)})
                  if item is product else item for item in types)
    plan = ctx.plan.model_copy(update={
        "library": library.model_copy(update={"equipment_types": types})})
    model = dataclasses.replace(ctx.model, plan=plan)
    return dataclasses.replace(ctx, plan=plan, model=model)


def _type_of(ctx, equipment_tag: str) -> str:
    from typehaus.takeoff.hvac import hvac_units

    return next(u.type_ref for u in hvac_units(ctx.model) if u.tag == equipment_tag)


def test_a_single_stage_unit_is_NOT_APPLICABLE_and_it_is_EARNED(catlin_ctx) -> None:
    """§4. N/A is a *verdict*, not a gap, and the fourth-verdict rule says it must come from
    positive evidence of absence. "Every published row states the same minimum and maximum"
    is that evidence: the machine has told us it is on-or-off, and Manual S's
    minimum-compressor factor governs modulating equipment.

    The wrong answer here would be UNKNOWN — which would read as "we could not tell", when
    in fact the document answered.
    """
    ctx = _swap_type(catlin_ctx, "EQ-M-HP3-OD", _single_stage())
    finding = _findings(ctx)["EQ-M-HP3-OD"]
    assert finding.result is Result.NOT_APPLICABLE
    assert "single-stage" in finding.message
    assert "no turndown to grade" in finding.message


def test_a_table_with_no_minimum_column_is_UNKNOWN_not_an_assumed_ratio(
        catlin_ctx) -> None:
    """§4. Most manufacturer documents publish no minimum at all; NEEP's ccASHP database is
    the one public source that does. A turndown ratio assumed from the maximum would be
    exactly the invented input this package refuses, and the message says where to look."""
    ctx = _swap_type(catlin_ctx, "EQ-M-HP3-OD", _no_minimum())
    finding = _findings(ctx)["EQ-M-HP3-OD"]
    assert finding.result is Result.UNKNOWN
    assert "states no minimum_btuh at any temperature" in finding.message
    assert "ashp.neep.org" in finding.message


def test_a_design_temperature_outside_the_table_is_UNKNOWN(catlin_ctx) -> None:
    """The same refusal ``capacity_at`` makes: a table that stops at 5 °F says nothing about
    a −15 °F design hour, and reading the endpoint would turn a gap in the document into a
    verdict."""
    warm_only = EquipmentType(
        tag="EQ-T-WARM", name="Heat pump rated to 5 F only",
        footprint=(inch(30), inch(15)), height=inch(30),
        heating_ratings=(
            _rating(outdoor_db_f=5.0, minimum_btuh=3000, rated_btuh=18000),
            _rating(outdoor_db_f=47.0, minimum_btuh=3000, rated_btuh=24000),
        ))
    ctx = _swap_type(catlin_ctx, "EQ-M-HP3-OD", warm_only)
    finding = _findings(ctx)["EQ-M-HP3-OD"]
    assert finding.result is Result.UNKNOWN
    assert "outside it and nothing is read by extrapolation" in finding.message
