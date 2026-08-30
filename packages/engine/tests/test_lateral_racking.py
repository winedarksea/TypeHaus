"""``structural.lateral_racking`` — the first check in this model that computes a wind load.

Two kinds of test here and they answer different questions.

The synthetic fixtures below follow ``test_foundation_unbalanced.py``'s pattern: a minimal
plan, one variable moved at a time, asserting the *contract* — silent site to UNKNOWN,
unrated connector to UNKNOWN naming the report, authored ``engineering_spec`` to PASS.

The catlin fixtures at the foot pin the **landed verdicts on all eight real braces**, because
a check that computes a load can regress silently in a way a coverage check cannot: pick the
wrong ``Railing`` out of thirteen and the appurtenance height drops from 23' to 12.8', q_h
falls 12 %, and every finding still reads perfectly. That bug happened during development and
the height assertion here is what would have caught it.
"""

from types import SimpleNamespace

import pytest

from typehaus.checks.structural.lateral_racking import (
    _brace_axial_per_unit_shear,
    lateral_racking,
)
from typehaus.findings import Result
from typehaus.model.enums import TrimKind
from typehaus.model.structure import KneeBrace, Post
from typehaus.model.trim import Fascia
from typehaus.quantities import ft, inch, pt

_SILENT_SITE = SimpleNamespace(design_wind_speed_mph=None, wind_exposure=None,
                               risk_category=None, grade=ft(-2, -10), spot_elevations=())
_CATLIN_SITE = SimpleNamespace(design_wind_speed_mph=115.0, wind_exposure="B",
                               risk_category="II", grade=ft(-2, -10),
                               spot_elevations=(SimpleNamespace(elevation=ft(-9, -4)),))


def _brace(tag="KB-T-1", axis="y", connector="KBS1Z", spec=None) -> KneeBrace:
    return KneeBrace(uid=f"TSTKB{tag[-1]}AAAA", tag=tag, position=pt(ft(8), ft(-2.5)),
                     soffit_elevation=ft(8, 5.5), leg=ft(3), axis=axis, member="2x6",
                     post_size="6x6", connector=connector, connects=("PT-T-1", "BM-T-1"),
                     engineering_spec=spec)


def _post() -> Post:
    return Post(uid="TSTPT01AAAA", tag="PT-T-1", position=pt(ft(8), ft(-2.5)),
                size="6x6", height=ft(9, 3))


def _fascia() -> Fascia:
    return Fascia(uid="TSTFC01AAAA", tag="TR-T-FASCIA", kind=TrimKind.FASCIA,
                  path=(pt(ft(7.5), ft(-0.83)), pt(ft(7.5), ft(-10.5)),
                        pt(ft(28.5), ft(-10.5)), pt(ft(28.5), ft(-0.83))),
                  top_elevation=ft(10), depth=inch(9), thickness=inch(1),
                  material="PVC", host_ref="FS-T-DECK")


def _ctx(elements, site=_CATLIN_SITE) -> SimpleNamespace:
    by_tag = {e.tag: e for e in elements}
    return SimpleNamespace(
        plan=SimpleNamespace(
            project=SimpleNamespace(site=site),
            all_elements=lambda: iter(elements),
            by_tag=by_tag.get),
        model=SimpleNamespace())


def _of(findings, tag):
    return [f for f in findings if tag in f.element_tags]


# --- the free body -----------------------------------------------------------------------


def test_the_brace_carries_more_than_the_shear_it_resists():
    """P = V·h·sqrt(2)/(h-a). Always > sqrt(2), because the brace is short of the load point.

    Worth its own test because the intuition runs the other way: a brace is often imagined as
    "taking its share", and it in fact amplifies. On catlin's 9.23' post with a 3' leg the
    factor is 2.10 — the connector sees more than double the storey shear delivered above it.
    """
    assert _brace_axial_per_unit_shear(9.23, 3.0) == pytest.approx(2.098, abs=0.01)
    assert _brace_axial_per_unit_shear(9.06, 3.0) == pytest.approx(2.114, abs=0.01)


def test_a_longer_leg_on_the_same_post_costs_capacity_not_buys_it():
    """The lever shortens as the brace grows, so a bigger brace is a worse one, structurally."""
    short = _brace_axial_per_unit_shear(9.0, 2.0)
    long_ = _brace_axial_per_unit_shear(9.0, 5.0)
    assert long_ > short


def test_a_brace_as_long_as_its_post_is_not_gradeable():
    """No lever, no finite force. Returning a huge number instead would look like an answer."""
    assert _brace_axial_per_unit_shear(3.0, 3.0) is None
    assert _brace_axial_per_unit_shear(3.0, 4.0) is None


# --- the contract ------------------------------------------------------------------------


def test_a_plan_with_no_knee_braces_says_nothing():
    """This check is about a specific lateral system. Silence, not a finding, where none is."""
    assert lateral_racking(_ctx([_post(), _fascia()])) == []


def test_a_silent_site_yields_one_unknown_naming_the_missing_field():
    findings = lateral_racking(_ctx([_brace(), _post(), _fascia()], site=_SILENT_SITE))
    assert len(findings) == 1
    assert findings[0].result is Result.UNKNOWN
    assert "no complete design wind basis" in findings[0].message
    assert "design_wind_speed_mph" in (findings[0].fix_hint or "")


def test_an_unrated_connector_is_unknown_and_quotes_the_report():
    """The APVKB case: a demand is computable, a ratio is not, and the message must say why."""
    findings = _of(lateral_racking(_ctx([_brace(connector="APVKB45-6"), _post(), _fascia()])),
                   "KB-T-1")
    assert len(findings) == 1
    assert findings[0].result is Result.UNKNOWN
    assert "no published lateral capacity" in findings[0].message
    assert "ER-280" in findings[0].message
    assert "KBS1Z" in (findings[0].fix_hint or "")


def test_a_rated_connector_reports_a_critical_force_coefficient():
    findings = _of(lateral_racking(_ctx([_brace(), _post(), _fascia()])), "KB-T-1")
    assert len(findings) == 1
    assert findings[0].result is Result.UNKNOWN
    assert "540 lbf" in findings[0].message
    assert "C_f" in findings[0].message


def test_an_authored_engineering_spec_is_the_one_thing_that_passes():
    """Verbatim ``FoundationWall.engineering_spec``'s contract, and the only route to PASS."""
    spec = "Lateral design by J. Doe PE, MN #12345, sheet S2.1, 2026-09-15"
    findings = _of(lateral_racking(
        _ctx([_brace(spec=spec), _post(), _fascia()])), "KB-T-1")
    assert len(findings) == 1
    assert findings[0].result is Result.PASS
    assert spec in findings[0].message


def test_the_check_never_returns_a_fail():
    """verify.sh holds catlin to zero FAIL, and a screening calc has no standing to break it.

    Every branch, including the worst one this fixture can produce, must stay off FAIL.
    """
    for connector in ("KBS1Z", "APVKB45-6", "NOT-A-PART"):
        findings = lateral_racking(_ctx([_brace(connector=connector), _post(), _fascia()]))
        assert all(f.result is not Result.FAIL for f in findings), connector


def test_a_brace_naming_no_resolvable_post_is_unknown_not_silent():
    findings = _of(lateral_racking(_ctx([_brace(), _fascia()])), "KB-T-1")
    assert len(findings) == 1
    assert findings[0].result is Result.UNKNOWN
    assert "names no Post" in findings[0].message


# --- the real house ----------------------------------------------------------------------


@pytest.fixture(scope="module")
def catlin_findings(catlin_model):
    from typehaus.checks.registry import CheckContext, FramingPreferences, Preferences

    del FramingPreferences, Preferences
    ctx = CheckContext(plan=catlin_model.plan, model=catlin_model,
                       preferences=_catlin_preferences(), profile=_catlin_profile())
    return lateral_racking(ctx)


def _catlin_preferences():
    from typehaus.checks.registry import Preferences

    return Preferences()


def _catlin_profile():
    from typehaus.checks.code.mn_residential.profile import MN_2024

    return MN_2024


def test_catlin_grades_all_eight_braces_plus_the_unbraced_posts(catlin_findings):
    brace_findings = [f for f in catlin_findings
                      if any(t.startswith("KB-SG-") for t in f.element_tags)]
    assert len(brace_findings) == 8


def test_catlin_has_no_fail_here(catlin_findings):
    assert all(f.result is not Result.FAIL for f in catlin_findings)
    assert all(f.result is Result.UNKNOWN for f in catlin_findings)


def test_catlin_measures_the_appurtenance_from_the_sunken_garden_floor(catlin_findings):
    """23.0', not 12.8'.

    The balcony's guard tops out at +13'-1 1/2" and the garden floor it stands over is at
    -9'-4". Reading any other Railing in the plan — a stair-head guard on the main floor,
    say — gives 12.8' and understates q_h by 12 % while every word of the finding still looks
    right. This is the assertion that catches it.
    """
    message = catlin_findings[0].message
    assert "23.0' above the ground beneath" in message
    assert "q_h 18.7 psf" in message


def test_catlin_derives_the_beams_into_the_projected_area_not_just_the_fascia(catlin_findings):
    """The bands must include the members the braces rise into, not only the fascia.

    Scoping the member search to one direction's own braces finds only members running
    *along* the wind, which present their ends and nothing else — dropping every beam and
    rail from A_s and understating the demand by roughly two thirds.
    """
    ew = next(f for f in catlin_findings if "E-W wind" in f.message)
    ns = next(f for f in catlin_findings if "N-S wind" in f.message)
    assert "BM-SG-BLW section depth" in ew.message and "25.4 sf" in ew.message
    assert "BM-SG-RAIL-R section depth" in ns.message
    # N-S sees the 21' face, E-W the 9.7' one, so the N-S demand must be the larger.
    assert "39.9 sf" in ns.message


def test_every_catlin_brace_clears_the_whole_force_coefficient_table(catlin_findings):
    """The landed engineering result, pinned.

    All eight braces reach their KBS1Z allowable only above C_f 2.69, and the largest
    coefficient ASCE 7-16 Fig. 29.3-1 Cases A and B are known to produce is 1.80. So the
    bracing is adequate for *every* value the table can hold, and the one input this
    repository could not source cannot change the answer. If a geometry change makes this
    test fail, the balcony's lateral system got worse and somebody needs to know.
    """
    brace_findings = [f for f in catlin_findings
                      if any(t.startswith("KB-SG-") for t in f.element_tags)]
    assert len(brace_findings) == 8
    for finding in brace_findings:
        assert "clears for every value" in finding.message, finding.message
        assert "reaches its allowable" not in finding.message


def test_catlin_names_the_two_centre_pillars_and_not_the_heat_pump_legs(catlin_findings):
    """The unbraced-post finding is about columns, and the stand legs are not columns.

    Twelve ``PT-SG-HP*`` aluminium legs sit inside the balcony footprint at 12" tall. Listing
    them buries the two pillars the finding exists to raise in ten that are irrelevant to it.
    """
    lonely = next(f for f in catlin_findings if "carry no knee brace" in f.message)
    assert "PT-SG-BR2" in f"{lonely.element_tags}"
    assert "PT-SG-BF2" in f"{lonely.element_tags}"
    assert not any(t.startswith("PT-SG-HP") for t in lonely.element_tags)
