"""The ratings table's schema, and reading a capacity out of it.

``EquipmentType`` carried two scalars — ``heating_capacity_btuh`` and
``heating_capacity_at_design_btuh`` — and the catalog's own preamble said the quiet part:
*"the engine does no curve interpolation itself, so whatever is authored here IS the machine
as far as every check is concerned."* Two defects hid behind that, and neither is visible in
a scalar:

* a modulating unit's **minimum** output, which is what decides whether it short-cycles;
* **staleness**, because *at design* depends on ``Site.design_temp_heating`` and a type has
  never known the site.

This file holds the validator (transcription errors are refused at load time, the way
``_check_fan_curve`` refuses a bad fan curve) and ``takeoff/hvac.capacity_at`` (the read,
which refuses to extrapolate at either end).
"""

from __future__ import annotations

import pytest

from typehaus.model import EquipmentType, HeatPumpRating, RatingBasis, inch
from typehaus.takeoff.hvac import capacity_at


def _rating(**kwargs) -> HeatPumpRating:
    kwargs.setdefault("citation", "test fixture")
    return HeatPumpRating(**kwargs)


def _type(rows, tag: str = "EQ-T-TEST") -> EquipmentType:
    return EquipmentType(tag=tag, name="Test heat pump",
                         footprint=(inch(30), inch(15)), height=inch(30),
                         heating_ratings=tuple(rows))


# --- the validator ---------------------------------------------------------------------------

def test_a_single_row_is_a_rating_not_a_table() -> None:
    """One point cannot be read between, so it cannot answer "at design" at any other
    temperature — which is the entire reason the scalars were replaced."""
    with pytest.raises(ValueError, match="at least two rows"):
        _type([_rating(outdoor_db_f=47.0, rated_btuh=24000)])


def test_temperature_must_strictly_increase() -> None:
    """Rows out of order interpolate backwards and return a plausible number that means
    nothing — a fact about the TYPING, not about the building, so it is refused rather than
    reported as a finding."""
    with pytest.raises(ValueError, match="strictly increase"):
        _type([_rating(outdoor_db_f=47.0, rated_btuh=24000),
               _rating(outdoor_db_f=5.0, rated_btuh=18000)])


def test_a_repeated_temperature_is_refused_which_is_what_forbids_a_blend() -> None:
    """"One row, one basis" is enforced here and nowhere else. Two sources that disagree at
    one temperature cannot both be authored; the row the house sizes against is authored and
    the other goes in its ``citation`` prose."""
    with pytest.raises(ValueError, match="strictly increase"):
        _type([_rating(outdoor_db_f=5.0, rated_btuh=18000, basis=RatingBasis.NEEP),
               _rating(outdoor_db_f=5.0, rated_btuh=19000,
                       basis=RatingBasis.MANUFACTURER)])


def test_a_row_must_state_at_least_one_capacity() -> None:
    with pytest.raises(ValueError, match="states no capacity at all"):
        _type([_rating(outdoor_db_f=5.0), _rating(outdoor_db_f=47.0, rated_btuh=24000)])


def test_minimum_may_not_exceed_rated_or_maximum() -> None:
    with pytest.raises(ValueError, match="minimum <= rated <= maximum"):
        _type([_rating(outdoor_db_f=5.0, minimum_btuh=20000, maximum_btuh=18000),
               _rating(outdoor_db_f=47.0, rated_btuh=24000)])
    with pytest.raises(ValueError, match="minimum <= rated <= maximum"):
        _type([_rating(outdoor_db_f=5.0, rated_btuh=20000, maximum_btuh=18000),
               _rating(outdoor_db_f=47.0, rated_btuh=24000)])


def test_a_cop_without_its_capacity_is_refused() -> None:
    """A COP describes an OPERATING POINT. Stating one for a level the row does not claim
    exists is a transcription error — most often a minimum COP copied onto a row whose
    minimum column was blank."""
    with pytest.raises(ValueError, match="but no minimum capacity"):
        _type([_rating(outdoor_db_f=5.0, maximum_btuh=18000, cop_at_minimum=2.5),
               _rating(outdoor_db_f=47.0, rated_btuh=24000)])


def test_a_non_positive_capacity_or_cop_is_refused() -> None:
    with pytest.raises(ValueError, match="non-positive capacity"):
        _type([_rating(outdoor_db_f=5.0, rated_btuh=0.0),
               _rating(outdoor_db_f=47.0, rated_btuh=24000)])
    with pytest.raises(ValueError, match="COP at rated must be > 0"):
        _type([_rating(outdoor_db_f=5.0, rated_btuh=18000, cop_at_rated=0.0),
               _rating(outdoor_db_f=47.0, rated_btuh=24000)])


def test_capacity_RISING_as_it_gets_colder_is_ACCEPTED() -> None:
    """**The positive test, and the one someone will try to delete.**

    ``EQ-T-GREE-SAPPHIRE-9-OD`` publishes 12,000 Btu/h at 17 °F and 10,600 at 47 °F — more
    capacity when it is colder. That is not a transcription error: it is a real boosted
    low-ambient map, the compressor is allowed to overspeed below a threshold, and several
    cold-climate units publish one. A monotonicity rule would refuse the machine this house
    actually bought, which is why ``_check_heating_ratings`` deliberately does not have one.
    """
    product = _type([
        _rating(outdoor_db_f=-22.0, minimum_btuh=2600, maximum_btuh=7400),
        _rating(outdoor_db_f=5.0, minimum_btuh=2600, rated_btuh=11500, maximum_btuh=11500),
        _rating(outdoor_db_f=17.0, minimum_btuh=2800, rated_btuh=12000, maximum_btuh=13000),
        _rating(outdoor_db_f=47.0, minimum_btuh=2700, rated_btuh=10600, maximum_btuh=16000),
    ])
    assert len(product.heating_ratings) == 4
    rated = [row.rated_btuh for row in product.heating_ratings]
    assert rated[2] > rated[3], "17 °F really is above 47 °F on this machine"


def test_a_ragged_table_is_accepted_because_published_tables_are_ragged() -> None:
    """NEEP states a rated column at three temperatures and not at the fourth; Gree's
    extended ratings state a maximum everywhere and a minimum nowhere. Requiring all three
    columns on every row would make most real documents unauthorable."""
    product = _type([
        _rating(outdoor_db_f=-22.0, minimum_btuh=13400, maximum_btuh=18000),
        _rating(outdoor_db_f=-15.0, rated_btuh=21000, basis=RatingBasis.MANUFACTURER),
        _rating(outdoor_db_f=47.0, minimum_btuh=10800, rated_btuh=25000,
                maximum_btuh=25400),
    ])
    assert product.heating_ratings[1].minimum_btuh is None


def test_a_citation_is_required_not_optional() -> None:
    """A capacity with no provenance is the defect this class exists to close, so the field
    has no default. There is nowhere to author a number without saying where it came from."""
    with pytest.raises(ValueError, match="citation"):
        HeatPumpRating(outdoor_db_f=47.0, rated_btuh=24000)


# --- capacity_at -----------------------------------------------------------------------------

_CATLIN_FLEXX = (
    HeatPumpRating(outdoor_db_f=-22.0, minimum_btuh=13400, maximum_btuh=18000,
                   basis=RatingBasis.NEEP, citation="NEEP 504980"),
    HeatPumpRating(outdoor_db_f=5.0, minimum_btuh=14000, rated_btuh=25000,
                   maximum_btuh=25000, basis=RatingBasis.NEEP, citation="NEEP 504980"),
    HeatPumpRating(outdoor_db_f=17.0, minimum_btuh=7100, rated_btuh=20600,
                   maximum_btuh=21600, basis=RatingBasis.NEEP, citation="NEEP 504980"),
    HeatPumpRating(outdoor_db_f=47.0, minimum_btuh=10800, rated_btuh=25000,
                   maximum_btuh=25400, basis=RatingBasis.NEEP, citation="NEEP 504980"),
)


def test_an_exact_row_is_READ_and_says_so() -> None:
    """The basis string is not decoration: a finding prints it, so a reader can tell a read
    from an interpolation without opening the catalog."""
    capacity = capacity_at(_CATLIN_FLEXX, 47.0)
    assert capacity is not None
    assert (capacity.minimum_btuh, capacity.rated_btuh) == (10800, 25000)
    assert capacity.basis == "read at 47 °F (neep)"


def test_between_two_rows_is_interpolated_per_COLUMN() -> None:
    """Per column, because published tables are ragged: the maximum interpolates across the
    −22/5 pair while the rated does NOT, because −22 states no rated. Interpolating a rated
    from one endpoint would invent it."""
    capacity = capacity_at(_CATLIN_FLEXX, -15.0)
    assert capacity is not None
    assert capacity.rated_btuh is None
    assert capacity.maximum_btuh == pytest.approx(18000 + 7000 * 7 / 27)
    assert capacity.minimum_btuh == pytest.approx(13400 + 600 * 7 / 27)
    assert capacity.basis == "interpolated between -22 °F and 5 °F (neep)"


def test_it_refuses_to_extrapolate_at_BOTH_ends() -> None:
    """One more than ``erv_static._delivered``, which clamps at its low end and is right to:
    a fan cannot beat its free-air flow, so the clamp is a physical bound. There is no such
    bound here. A compressor below the coldest published row is not "at least that much" —
    it is a machine the manufacturer declined to characterise, and quite possibly one that
    has locked out. Returning the endpoint would turn a gap in the document into a number
    the sizing check then passes on."""
    assert capacity_at(_CATLIN_FLEXX, -30.0) is None
    assert capacity_at(_CATLIN_FLEXX, 60.0) is None
    assert capacity_at((), -15.0) is None


def test_the_basis_names_both_sources_when_an_interpolation_spans_them() -> None:
    rows = (
        HeatPumpRating(outdoor_db_f=-22.0, maximum_btuh=18000,
                       basis=RatingBasis.NEEP, citation="NEEP"),
        HeatPumpRating(outdoor_db_f=5.0, maximum_btuh=25000,
                       basis=RatingBasis.MANUFACTURER, citation="Gree"),
    )
    capacity = capacity_at(rows, -10.0)
    assert capacity is not None
    assert "neep/manufacturer" in capacity.basis


# --- the house -------------------------------------------------------------------------------

def test_catlins_three_systems_all_carry_a_table_with_a_minimum(catlin_plan) -> None:
    """The Phase 3 data-gathering risk, closed. The plan that asked for these tables rated
    the Multi's minimum column as "may not exist publicly" — the highest risk of the three.
    NEEP publishes it for all three units, at all four of its temperatures.
    """
    types = {item.tag: item for item in catlin_plan.library.equipment_types}
    for tag in ("EQ-T-GREE-FLEXX-ULTRA-24-OD", "EQ-T-GREE-MULTI-U30",
                "EQ-T-GREE-SAPPHIRE-9-OD"):
        rows = types[tag].heating_ratings
        assert rows, tag
        with_minimum = [row for row in rows if row.minimum_btuh is not None]
        assert len(with_minimum) >= 4, tag
        assert all(row.citation for row in rows), tag
        assert all(row.return_db_f == 70.0 for row in rows), tag


def test_the_two_manufacturer_rows_are_the_two_at_the_design_temperature(
        catlin_plan) -> None:
    """Every row is NEEP's except where the site designs: NEEP publishes −22, 5, 17 and 47
    and this site designs at −15, so Systems 1 and 2 carry a manufacturer row there rather
    than an interpolation of two NEEP rows. System 3's zone is 932 Btu/h and takes the
    interpolation, because nothing turns on it."""
    types = {item.tag: item for item in catlin_plan.library.equipment_types}
    manufacturer = [(tag, row.outdoor_db_f)
                    for tag in ("EQ-T-GREE-FLEXX-ULTRA-24-OD", "EQ-T-GREE-MULTI-U30",
                                "EQ-T-GREE-SAPPHIRE-9-OD")
                    for row in types[tag].heating_ratings
                    if row.basis is RatingBasis.MANUFACTURER]
    assert manufacturer == [("EQ-T-GREE-FLEXX-ULTRA-24-OD", -15.0),
                            ("EQ-T-GREE-MULTI-U30", -15.0)]


def test_the_heat_kits_zero_at_design_is_DERIVED_from_its_lockout(catlin_plan) -> None:
    """It was authored as ``heating_capacity_at_design_btuh=0`` with prose explaining that
    the control locks the elements out above −22 °F and the site designs at −15. A correct
    reading, and a conclusion rather than an input: move the site to −30 °F and the kit
    really would contribute, and the authored zero would have been silently wrong.
    """
    from typehaus.takeoff.hvac import HvacUnit, _resistance_at_design

    kit = {item.tag: item for item in catlin_plan.library.equipment_types}[
        "EQ-T-GREE-FLEXX-HEATKIT-46KW"]
    assert kit.resistance_heating_btuh == 15695
    assert kit.aux_lockout_above_f == -22.0
    unit = HvacUnit(
        tag="EQ-S-HP1-STRIP", uid="x", storey="second", kind="heater", name=None,
        type_ref=kit.tag, room="RM-S-HALL", zone_rooms=(), outdoor_ref=None, circuit=None,
        heating_ratings=(), resistance_heating_btuh=kit.resistance_heating_btuh,
        aux_lockout_above_f=kit.aux_lockout_above_f, cooling_capacity_btuh=None,
        min_operating_temp_f=None, ventilation_cfm=None,
        sensible_recovery_effectiveness=None, supplemental_heat=True)
    assert _resistance_at_design(unit, -15.0) == 0.0   # this site: locked out
    assert _resistance_at_design(unit, -30.0) == 15695  # a colder one: it runs
    assert _resistance_at_design(unit, None) == 15695   # no site stated: nothing to gate on
