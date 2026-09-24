"""``mep.run_member_crossing`` — does the service crossing this floor fit between its members.

The rule nobody had: the 8 7/8" window that sets every starting invert on catlin's second
floor was prose and a router invariant, and the drain note's §6 conceded it outright.
"""

from __future__ import annotations

import pytest
from _helpers import check_context

from typehaus.checks.mep.routing_members import run_member_crossing
from typehaus.findings import Result
from typehaus.quantities import M_PER_IN

_CID = "mep.run_member_crossing"


def _findings(plan, model):
    return run_member_crossing(check_context(plan=plan, model=model))


def _for(findings, tag, floor):
    return next(f for f in findings
                if tag in f.element_tags and floor in f.element_tags)


def _crown_in(message: str) -> float:
    """The crown number out of a PASS message, so the test reads the check's own words."""
    token = message.split("crown ")[1].split('"')[0]
    return float(token)


def test_every_catlin_crossing_clears_its_z_WINDOW(catlin_plan, catlin_model_ro) -> None:
    """The 0-FAIL gate this check has always held: nothing in the reference house has its
    crown or its invert inside a member.

    **It is the z window's gate and no longer the whole check's** (2026-09-19). Since
    FS-S-WEST states its fabricator's panel layout, this check asks a second question —
    is the crossing in an OPENING, or on a web — and seventeen of catlin's are on a web.
    Those are E8's finding and `preferences.toml` itemises every one of them; conflating
    the two here would have let a real z-window regression hide behind them."""
    findings = _findings(catlin_plan, catlin_model_ro)
    fails = [f for f in findings if f.result is Result.FAIL
             and "ON A WEB" not in f.message]
    assert not fails, [f.message for f in fails]
    assert findings, "catlin routes services across framed members; something should grade"


def test_the_web_verdict_is_a_SECOND_finding_and_not_a_changed_one(
        catlin_plan, catlin_model_ro) -> None:
    """A run on a web still gets its z-window verdict. The two are different questions —
    "does it fit between the chords" and "is there a slot here at all" — and a run that
    answers one well and the other badly has to be told both."""
    findings = _findings(catlin_plan, catlin_model_ro)
    web = [f for f in findings if "ON A WEB" in f.message]
    # Seventeen when the panel datum landed; nine since D1 took level 2's ducts off the
    # webs; six since the 2026-09-24 vent re-lane. Every one left is a PIPE — the plumbing
    # campaign's, not the air's.
    assert len(web) == 6, [f.message for f in web]
    assert all(tag.startswith("PR-") for f in web for tag in f.element_tags
               if not tag.startswith("FS-"))
    for finding in web:
        assert finding.result is Result.FAIL
        tag = finding.element_tags[0]
        window = [f for f in findings if tag in f.element_tags
                  and "FS-S-WEST" in f.element_tags and "ON A WEB" not in f.message]
        assert window, f"{tag} lost its z-window verdict"


def test_per_crossing_beats_the_envelope_on_the_bld05_run(
        catlin_plan, catlin_model_ro) -> None:
    """**The assertion that pins this decision shut.**

    ``PR-M-S-SUITE-WC-DRAIN``'s south leg reads crown **+0.250"** on the whole-leg envelope
    and **+0.944"** per-crossing. The 0.694" between them is exactly the clear bay its high
    end sits in — there is no truss there. BLD-05's "half an inch of crown clearance" is the
    envelope number at the nominal size; this is the number the pipe actually has.

    If anyone ever "simplifies" this check to band a whole leg, this fails.

    +1.209" since 0db0c103 re-laned the suite stack out of the master closet.
    """
    findings = _findings(catlin_plan, catlin_model_ro)
    finding = _for(findings, "PR-M-S-SUITE-WC-DRAIN", "FS-S-WEST")
    assert finding.result is Result.PASS
    assert _crown_in(finding.message) == pytest.approx(1.209, abs=0.001)
    assert "joist-0-015-0" in finding.message


def test_the_envelope_would_have_failed_three_real_runs(
        catlin_plan, catlin_model_ro) -> None:
    """Two more that flip FAIL -> PASS for the same reason, so the choice is not a one-off.

    ``PR-M-S-BATH1-TUB-DRAIN`` reads -0.200" on the envelope and +0.148" per-crossing;
    ``PR-M-S-SUITE-LAV-DRAIN`` -0.013" and +0.294". The tub drain reads +0.465" since its
    2026-09-24 re-lane west of the ERV trunk.
    """
    findings = _findings(catlin_plan, catlin_model_ro)
    for tag, crown in (("PR-M-S-BATH1-TUB-DRAIN", 0.465),
                       ("PR-M-S-SUITE-LAV-DRAIN", 0.294)):
        finding = _for(findings, tag, "FS-S-WEST")
        assert finding.result is Result.PASS, finding.message
        assert _crown_in(finding.message) == pytest.approx(crown, abs=0.001), tag


def test_a_diagonal_raceway_crosses_what_it_crosses(catlin_plan, catlin_model_ro) -> None:
    """``CD-B-ATTIC-RISER`` "crosses" twelve members on a station-only reading of its band
    and exactly **one** when the crossing is interpolated. One finding per (run, floor)."""
    findings = _findings(catlin_plan, catlin_model_ro)
    riser = [f for f in findings if "CD-B-ATTIC-RISER" in f.element_tags]
    floors = {t for f in riser for t in f.element_tags if t.startswith("FS-")}
    assert len(riser) == len(floors), [f.message for f in riser]


def test_the_surfaces_are_real_not_nominal(catlin_plan, catlin_model_ro) -> None:
    """A 3" drain is graded at 3.500" and 3/4" EMT at 0.922", and the message says so."""
    findings = _findings(catlin_plan, catlin_model_ro)
    assert '3.500" outside' in _for(findings, "PR-M-S-SUITE-WC-DRAIN", "FS-S-WEST").message
    kitch = _for(findings, "CD-M-DATA-KITCH", "FS-S-WEST")
    assert '0.922" outside' in kitch.message


def test_the_two_raceway_defects_are_fixed_and_stay_fixed(
        catlin_plan, catlin_model_ro) -> None:
    """``plan/electrical.py`` claimed 3/4" EMT "passes between the 8 7/8" chords without a
    hole in anything". At +9'-2" the real 0.922" OD put the invert 0.086" INTO the bottom
    chord; ``CD-M-DATA-PORCH``'s drop leg was 1.115" in. Both are +9'-2 1/4" now, and the
    porch run holds that elevation through the rim before it turns down.

    2026-09-24: both re-laned around the ERV trunk. KITCH crosses at +9'-2 1/2" (invert
    +0.414"); PORCH's north-south leg rides the top chord (crown +0.039")."""
    findings = _findings(catlin_plan, catlin_model_ro)
    for tag, side, gap in (("CD-M-DATA-KITCH", "invert", 0.414),
                           ("CD-M-DATA-PORCH", "crown", 0.039)):
        finding = _for(findings, tag, "FS-S-WEST")
        assert finding.result is Result.PASS, finding.message
        measured = float(finding.message.split(f"{side} ")[1].split('"')[0])
        assert measured == pytest.approx(gap, abs=0.001), tag


def test_every_level_two_duct_rests_on_a_chord_and_none_is_inside_one(
        catlin_plan, catlin_model_ro) -> None:
    """``_BAY_Z`` meant "a 4" duct sitting on FS-S-WEST's bottom chord" and was derived
    against 108 1/8", the bottom of that chord rather than its top — 1 1/2" low, on every
    radial's south leg. Resting ON a chord is 0.000" of clearance and a PASS: the duct is
    supported by the thing it is touching.

    **Since D1 there are TWO tiers and a duct rests on whichever chord its tier names**, so
    the assertion is that one of the two gaps is zero rather than that the invert is. A
    south leg rides the upper tier (crown +0.000") and a bay leg the lower (invert +0.000");
    the 8" trunk is centred and clears both by 0.437"."""
    findings = _findings(catlin_plan, catlin_model_ro)
    ducts = [f for f in findings
             if any(t.startswith("DU-M-ERV") for t in f.element_tags)
             and "FS-S-WEST" in f.element_tags]
    # **SIX of the fourteen, and the other eight are the design.** Because the trunk runs
    # south, most extract takeoffs are pure BAY legs and cross no truss; what is left to
    # grade is the trunk itself, the three supply radials, LAUNDRY's turn south to the
    # standpipe boot, and SUITEBATH's turn north to its grille (2026-09-24).
    assert sorted(tag for f in ducts for tag in f.element_tags
                  if tag.startswith("DU-M-ERV")) == [
        "DU-M-ERV-EXH-TRUNK", "DU-M-ERV-R-BED", "DU-M-ERV-R-LAUNDRY",
        "DU-M-ERV-R-LIVING", "DU-M-ERV-R-STUDY", "DU-M-ERV-R-SUITEBATH"]
    for finding in ducts:
        assert finding.result is Result.PASS, finding.message
        crown = float(finding.message.split("crown ")[1].split('"')[0])
        invert = float(finding.message.split("invert ")[1].split('"')[0])
        assert crown >= -1e-9 and invert >= -1e-9, finding.message
        if "DU-M-ERV-EXH-TRUNK" in finding.element_tags:
            assert crown == pytest.approx(0.437, abs=0.001)
        else:
            assert min(crown, invert) == pytest.approx(0.0, abs=1e-6), finding.message


def test_an_i_joist_pass_is_qualified(catlin_plan, catlin_model_ro) -> None:
    """Clearing both flanges is necessary and not sufficient — the hole's diameter and its
    zone along the span come off a chart this engine does not hold, and the finding says so
    rather than implying the question is closed."""
    findings = _findings(catlin_plan, catlin_model_ro)
    i_joist = [f for f in findings if "fabricator's chart" in f.message]
    assert i_joist
    assert all("flange" in f.message for f in i_joist)


def test_no_floors_is_unknown_and_no_crossings_is_not_applicable(
        catlin_plan, catlin_model_ro) -> None:
    """N/A is earned from positive evidence of absence; UNKNOWN is the honest gap."""
    import copy

    stripped = copy.copy(catlin_model_ro)
    object.__setattr__(stripped, "floors", ())
    verdict = run_member_crossing(check_context(plan=catlin_plan, model=stripped))
    assert len(verdict) == 1 and verdict[0].result is Result.UNKNOWN

    no_runs = copy.copy(catlin_model_ro)
    for field in ("pipe_runs", "ducts", "conduits"):
        object.__setattr__(no_runs, field, ())
    verdict = run_member_crossing(check_context(plan=catlin_plan, model=no_runs))
    assert len(verdict) == 1 and verdict[0].result is Result.NOT_APPLICABLE


def test_it_is_registered_and_on_the_rough_plumbing_inspection() -> None:
    """The trap ``test_drain_offset_geometry.py`` exists to catch: a check module that is
    never imported registers nothing and grades nothing."""
    from typehaus.checks.code.mn_residential.inspections import MN_INSPECTIONS
    from typehaus.checks.registry import Tier, registered

    assert _CID in {cid for cid, _ in registered(Tier.STRUCTURAL)}
    rough = next(i for i in MN_INSPECTIONS if i.id == "rough_plumbing")
    assert _CID in rough.check_ids


def test_it_carries_no_permit_item() -> None:
    """``Tier.STRUCTURAL`` and no ``PermitItemSpec``, ever — the ``mep.run_over_void``
    precedent. No IRC section says "put the duct in the middle of the web", so a CODE tier
    would trip the coverage test and the ``code_ref`` requirement dishonestly."""
    from typehaus.checks.code.mn_residential.profile import get_profile

    for item in get_profile("mn-2020").permit_items:
        assert _CID not in item.check_ids, item.label


def test_the_window_units_are_inches_not_metres(catlin_plan, catlin_model_ro) -> None:
    """A station a builder can find with a tape, not a float in metres."""
    findings = _findings(catlin_plan, catlin_model_ro)
    assert all("'-" in f.message for f in findings if f.result is not Result.UNKNOWN)
    assert M_PER_IN > 0
