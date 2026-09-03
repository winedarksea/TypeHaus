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
    return _findings_for(catlin_model)


def _catlin_preferences():
    from typehaus.checks.registry import Preferences

    return Preferences()


def _catlin_profile():
    from typehaus.checks.code.mn_residential.profile import MN_2024

    return MN_2024


def test_catlin_has_no_knee_brace_left_and_the_check_does_not_go_silent(catlin_findings):
    """The regression this file most needed guarding against, and it very nearly happened.

    catlin's balcony traded eight knee braces for four 12" cast concrete columns fixed at
    their bases on 2026-09-03 (``houses/catlin/notes/balcony_moment_columns.md``). The
    brace-shaped code at the top of ``lateral_racking`` returned ``[]`` for a plan with no
    ``KneeBrace`` in it — so the one check that exists because this deck has no shear walls
    would have gone completely quiet on the day its entire lateral system changed.

    It now names each corner column and delegates to ``deck_post/<tag>``: one design, one
    stamp, two checks, the same pattern ``structural.frost_depth`` shares with
    ``structural.foundation_unbalanced_fill`` on a retaining wall.
    """
    from typehaus.model.structure import KneeBrace

    assert not [f for f in catlin_findings
                if any(t.startswith("KB-SG-") for t in f.element_tags)]
    assert catlin_findings, "the check went silent on a braceless freestanding deck"
    columns = {t for f in catlin_findings for t in f.element_tags if t.startswith("PT-SG-B")}
    assert columns == {"PT-SG-BR1", "PT-SG-BR3", "PT-SG-BF1", "PT-SG-BF3"}
    assert all("deck_post/" in (f.engineering_item or "") for f in catlin_findings)
    del KneeBrace


def test_catlin_has_no_fail_here(catlin_findings):
    """PASS, not UNKNOWN, and that is a change worth reading twice.

    While the lateral system was eight knee braces every finding here was UNKNOWN: the
    connector allowables were published but ``C_f`` was not, so the check inverted and
    reported a critical coefficient rather than a verdict. The four columns are graded by
    ``engineering/deck_post.py`` instead, which spends ``C_f`` at the Fig. 29.3-1 Case A/B
    ceiling and produces a real d/c — so ``engineered()`` returns the calculation's own
    result. It is still a DRAFT and still unsealed; ``haus print --sealed`` is the gate that
    says so.
    """
    assert all(f.result is not Result.FAIL for f in catlin_findings)
    assert all(f.result is Result.PASS for f in catlin_findings)


def test_a_deck_hung_in_a_shear_wall_is_not_reported_as_column_braced(catlin_model):
    """FS-SG-PORCH lands its four beams in W-SG-W1/E1 — two 12" concrete retaining walls.

    It is braced by shear walls in both directions and has no lateral question at all.
    Without the gate, its two cast columns would each be reported as "the lateral system",
    which is a false claim about a real structure — and one that would read as a PASS the
    moment their axial record came back OK.
    """
    named = {t for f in _findings_for(catlin_model) for t in f.element_tags}
    assert "FS-SG-PORCH" not in named
    assert "PT-SG-COL" not in named and "PT-SG-FCOL" not in named
    assert "FS-SG-DECK" in named


def _findings_for(catlin_model):
    """The check, with the ENGINEERING SUITE wired in.

    A bare ``CheckContext`` leaves ``ctx.engineering`` empty, and ``engineered()`` then
    reports "no calc registered for the kind" — an UNKNOWN that looks exactly like a real
    one. Since every finding this check now produces is a delegation, a fixture without the
    suite would assert nothing about the arithmetic behind them.
    """
    from typehaus.checks.registry import CheckContext
    from typehaus.engineering import EngineeringContext, EngineeringResults

    engineering = EngineeringResults(EngineeringContext(
        plan=catlin_model.plan, model=catlin_model, soil_class="GM"))
    return lateral_racking(CheckContext(
        plan=catlin_model.plan, model=catlin_model,
        preferences=_catlin_preferences(), profile=_catlin_profile(),
        engineering=engineering))


def test_the_corner_columns_are_delegated_not_graded_here(catlin_findings):
    """The finding says what is engineered and names the item a seal can cover — it does not
    try to be the calculation. A base moment against a section's phi*Mn is
    ``engineering/deck_post.py``'s arithmetic, and duplicating it here would be two
    authorities on one number."""
    for finding in catlin_findings:
        assert "fixed at its base" in finding.message
        assert "no knee brace and no shear wall" in finding.message
        assert finding.engineering_item.startswith("deck_post/PT-SG-B")
