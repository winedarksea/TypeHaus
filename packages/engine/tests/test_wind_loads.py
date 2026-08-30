"""``typehaus.wind`` — the site's design-wind basis, and ASCE 7-16 §26.10 velocity pressure.

**The oracle for the arithmetic is `houses/catlin/notes/catlin_truss_engineering.md` §2**,
which hand-worked K_z and q_h for this exact site months before this module existed and for
both exposures. Those numbers were computed by hand from the standard, not by this code, so
reproducing them is a real independent check rather than a snapshot of whatever the code
happens to do. Any change here that moves them is a bug in here until proven otherwise.
"""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from typehaus import Site, degF, ft
from typehaus.wind import (
    ASD_WIND_FACTOR,
    K_D_BUILDINGS,
    capacity_caveat,
    velocity_pressure_coefficient,
    velocity_pressure_psf,
    wind_basis,
)

#: The catlin basis: MN Rules 1309.0301's amendment to IRC Table R301.2(1).
_V_ULT = 115.0


def _site(**overrides) -> Site:
    """A minimal Site in the shape of ``houses/catlin/plan/site.py``'s."""
    fields = dict(lat=44.9778, lon=-93.2650, elevation=ft(830),
                  design_temp_heating=degF(-15), design_temp_cooling=degF(90))
    fields.update(overrides)
    return Site(**fields)


# --- the three fields on Site -----------------------------------------------------------


def test_a_silent_site_carries_no_wind_basis():
    """The starter house authors none of the three, and that must stay a legal Site.

    Every consumer degrades to UNKNOWN off this. If the fields were required, adding them
    would have been a breaking change to every house in the world that is not catlin.
    """
    site = _site()
    assert site.design_wind_speed_mph is None
    assert site.wind_exposure is None
    assert site.risk_category is None
    assert wind_basis(site) is None


def test_an_authored_site_round_trips_all_three():
    site = _site(design_wind_speed_mph=_V_ULT, wind_exposure="B", risk_category="II")
    assert site.design_wind_speed_mph == _V_ULT
    assert site.wind_exposure == "B"
    assert site.risk_category == "II"
    basis = wind_basis(site)
    assert basis is not None
    assert basis.describe() == "V_ult = 115 mph, Exposure B, Risk Category II"


@pytest.mark.parametrize("exposure", ["A", "b", "", "E"])
def test_an_exposure_outside_the_asce_set_is_rejected_at_construction(exposure):
    """``Literal["B","C","D"]`` is the whole point: Exposure A was deleted in ASCE 7-10."""
    with pytest.raises(ValidationError):
        _site(design_wind_speed_mph=_V_ULT, wind_exposure=exposure, risk_category="II")


@pytest.mark.parametrize("kwargs", [
    {"design_wind_speed_mph": _V_ULT},
    {"design_wind_speed_mph": _V_ULT, "wind_exposure": "B"},
    {"wind_exposure": "B", "risk_category": "II"},
])
def test_a_partial_basis_is_no_basis(kwargs):
    """Half a basis cannot make a pressure, and must not be completed by a default.

    Defaulting the missing half — C "because it is conservative", II "because most things
    are" — would put an assumed number into a calculation that a reader would then take as
    sourced. Absent is the honest answer.
    """
    assert wind_basis(_site(**kwargs)) is None


# --- the caveat the coverage checks share ------------------------------------------------


def test_the_caveat_names_the_absence_when_there_is_one():
    assert "no design wind speed" in capacity_caveat(_site())


def test_the_caveat_quotes_the_basis_and_still_refuses_to_claim_capacity():
    """The narrowing this whole change is about: a different reason, not a different verdict."""
    text = capacity_caveat(_site(design_wind_speed_mph=_V_ULT, wind_exposure="B",
                                 risk_category="II"))
    assert "no design wind speed" not in text
    assert "V_ult = 115 mph, Exposure B, Risk Category II" in text
    assert "capacity of the connection is not evaluated" in text


def test_the_caveat_works_off_a_duck_typed_site():
    """``wind_basis`` reads with ``getattr`` so synthetic check fixtures need no real Site."""
    assert "no design wind speed" in capacity_caveat(SimpleNamespace())


# --- ASCE 7-16 Table 26.10-1 / eq. 26.10-1 -----------------------------------------------


def test_kz_reproduces_the_truss_notes_exposure_c_value():
    """§2 of the note: "mean roof height h = 30 ft; K_z = 0.98"."""
    assert velocity_pressure_coefficient(30.0, "C") == pytest.approx(0.98, abs=0.005)


def test_kz_reproduces_the_truss_notes_exposure_b_value():
    """§2 of the note: "Exposure B reference: K_z = 0.70"."""
    assert velocity_pressure_coefficient(30.0, "B") == pytest.approx(0.70, abs=0.005)


def test_qh_reproduces_the_truss_notes_exposure_c_pressure():
    """§2: ``q_h = 0.00256 · 0.98 · 0.85 · 115² = 28.2 psf``."""
    basis = wind_basis(_site(design_wind_speed_mph=_V_ULT, wind_exposure="C",
                             risk_category="II"))
    assert velocity_pressure_psf(basis, 30.0) == pytest.approx(28.2, abs=0.15)


def test_qh_reproduces_the_truss_notes_exposure_b_pressure():
    """§2: "Exposure B reference: K_z = 0.70 → q_h = 20.1 psf"."""
    basis = wind_basis(_site(design_wind_speed_mph=_V_ULT, wind_exposure="B",
                             risk_category="II"))
    assert velocity_pressure_psf(basis, 30.0) == pytest.approx(20.1, abs=0.15)


def test_the_exposure_c_pressure_is_the_40_percent_margin_the_note_claims():
    """The note says the design "carries the Exposure C number, 40 % higher". Check it.

    This is the one number that justifies leaving `catlin_truss_engineering.md` on Exposure C
    while `plan/site.py` states B for everything else. If the ratio were small the note's
    rationale would be wrong, and nobody would notice from the note alone.
    """
    b = wind_basis(_site(design_wind_speed_mph=_V_ULT, wind_exposure="B", risk_category="II"))
    c = wind_basis(_site(design_wind_speed_mph=_V_ULT, wind_exposure="C", risk_category="II"))
    ratio = velocity_pressure_psf(c, 30.0) / velocity_pressure_psf(b, 30.0)
    assert ratio == pytest.approx(1.40, abs=0.02)


def test_kz_is_floored_at_the_tables_minimum_height():
    """Table 26.10-1's rows start at 0-15 ft; below that the 15-ft value is held.

    The balcony's own elements sit around 10-12 ft, so this floor is not academic here —
    without it the power law would keep falling and under-report the demand on exactly the
    structure ``checks/structural/lateral_racking.py`` grades.
    """
    at_15 = velocity_pressure_coefficient(15.0, "B")
    assert velocity_pressure_coefficient(4.0, "B") == pytest.approx(at_15)
    assert velocity_pressure_coefficient(0.0, "B") == pytest.approx(at_15)


def test_an_unknown_exposure_raises_rather_than_defaulting():
    basis = wind_basis(_site(design_wind_speed_mph=_V_ULT, wind_exposure="B",
                             risk_category="II"))
    bad = type(basis)(speed_mph=_V_ULT, exposure="X", risk_category="II")
    with pytest.raises(ValueError, match="exposure"):
        velocity_pressure_psf(bad, 30.0)


def test_the_asd_and_directionality_constants_are_the_standards():
    """Pinned so a "tuning" edit to either has to argue with a citation, not a diff."""
    assert K_D_BUILDINGS == 0.85     # Table 26.6-1
    assert ASD_WIND_FACTOR == 0.6    # §2.4.1 combinations 5 and 6
