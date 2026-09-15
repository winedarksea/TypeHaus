"""``integrity.member_profile_parses`` — a nominal nobody can read is a guessed member.

``cross_section`` has a silent rectangular fallback, and two of its branches reach that
fallback one level down while *reporting success*: a well-formed nominal that
``LUMBER_ACTUAL`` does not publish matches the pattern, misses the table, and comes back
indistinguishable from a real parse. ``"3.5x3.5 STEEL"``, ``"L3-1/2x3-1/2x1/4"`` and
``"16x16"`` all draw, cut, clash-check and bill as a 2x6, with nothing anywhere saying a
guess was made.

The silence stays — ``cross_section`` is called from 31 modules inside ``resolve()``, where
a raise aborts the build instead of reporting a defect. These tests pin the four things
that make the guard right rather than merely loud: that ``parses()`` agrees with
``cross_section``'s *actual* behaviour, that no pattern can be added to ``profiles.py``
without the predicate being told, that the check is registered, and that catlin — whose one
real hit, the resilient channel, is now read by a named-product literal — comes back clean
without ever having been turned red.
"""

from __future__ import annotations

import pytest

from typehaus.checks.registry import (
    CheckContext,
    JurisdictionProfile,
    Preferences,
    Tier,
    registered,
)
from typehaus.findings import Result
from typehaus.quantities import inch
from typehaus.resolve.framing import profiles
from typehaus.resolve.framing.profiles import (
    _FALLBACK_ACTUAL_IN,
    _PARSED_LITERALS,
    _PARSED_PATTERNS,
    cross_section,
    parses,
)

_CHECK_ID = "integrity.member_profile_parses"


# --- the predicate ----------------------------------------------------------------------

#: Every spelling the catalog really reads, one per branch of ``cross_section``.
_READABLE = (
    "2x4", "2x12", "6x6", "3-2x4", "2x4:kdat", "2-1.75x14 LVL", "1.75x11.875 LVL",
    "1.75x11.875 LSL", "1.5x11.875 rim", "deck 42x1.5", "11.875 I-joist", "11.875 TJI 230",
    "11.875 floor truss", "24 roof truss", "24 gable roof truss", "6.125x6.125", "12 round",
    "48x0.75 panel", "48x0.75 corner panel", "engineered-LVL", "hanger", "tapered tread",
    "25 ga. resilient channel",
)
#: The trap. Every one of these resolves to the 1 1/2" x 5 1/2" fallback today.
_UNREADABLE = (
    "3.5x3.5 STEEL", "L3-1/2x3-1/2x1/4", "16x16", "3-16x16",
    "HSS4x4x1/4", "W8x10", "", "   ", "2x", "x6",
)


@pytest.mark.parametrize("profile", _READABLE)
def test_a_readable_profile_parses(profile: str) -> None:
    assert parses(profile), profile


@pytest.mark.parametrize("profile", _UNREADABLE)
def test_an_unreadable_profile_does_not(profile: str) -> None:
    assert not parses(profile), profile


@pytest.mark.parametrize("profile", _UNREADABLE)
def test_unreadable_is_exactly_the_fallback(profile: str) -> None:
    """The predicate's whole claim: ``not parses(p)`` means the section is the guess.

    Asserted against ``cross_section`` itself rather than restated, so the two cannot
    drift: if a future pattern starts reading one of these strings for real, this fails
    and ``parses`` has to be told about it.

    A multi-ply spelling ("3-16x16") guesses the same 1 1/2" x 5 1/2" stick and then lays
    the authored number of them up, so the guess is divided back out by ``plies``: the
    fabricated dimension is the ply, not the built-up width.
    """
    section = cross_section(profile)
    assert section.shape == "rect"
    assert section.width_m / section.plies == pytest.approx(inch(_FALLBACK_ACTUAL_IN[0]).meters)
    assert section.depth_m == pytest.approx(inch(_FALLBACK_ACTUAL_IN[1]).meters)


@pytest.mark.parametrize("profile", _READABLE)
def test_readable_is_never_the_fallback_by_accident(profile: str) -> None:
    """A parse that lands on 1.5x5.5 anyway would make the predicate unfalsifiable.

    ``"2x6"`` is deliberately absent from ``_READABLE``: it IS 1 1/2" x 5 1/2", which is
    precisely why that section was chosen as the fallback and why it can never be the
    evidence either way.
    """
    section = cross_section(profile)
    fallback = (inch(_FALLBACK_ACTUAL_IN[0]).meters, inch(_FALLBACK_ACTUAL_IN[1]).meters)
    assert (section.width_m, section.depth_m) != fallback


def test_every_pattern_in_the_module_is_accounted_for() -> None:
    """A new ``_RE_*`` in ``profiles.py`` that nobody tells ``parses()`` about is the bug.

    It would report the new spelling as unreadable, and the check would file a finding
    against a member the parser handles perfectly. The two nominal patterns are the
    deliberate exclusions: they match on shape and then consult ``LUMBER_ACTUAL``, so
    ``parses`` grades them by table membership instead of by match.
    """
    graded_separately = {profiles._RE_MULTI_NOMINAL, profiles._RE_NOMINAL}
    declared = {*_PARSED_PATTERNS, *graded_separately}
    in_module = {v for name, v in vars(profiles).items() if name.startswith("_RE_")}
    assert in_module - declared == set()


def test_every_literal_branch_is_accounted_for() -> None:
    """``cross_section``'s ``text == "..."`` branches, which no pattern covers."""
    for literal in _PARSED_LITERALS:
        assert parses(literal)
    source = profiles.cross_section.__wrapped__.__code__.co_consts
    spelled = {c for c in source if isinstance(c, str) and c in {"hanger", "tapered tread",
                                                                 "engineered-LVL"}}
    assert spelled <= _PARSED_LITERALS


def test_parses_never_raises() -> None:
    """It is asked about authored strings, so it is asked about anything a person typed."""
    for junk in ("", ":", "::", "x", "2x6:", ":2x6", "  2x6  ", "2x6 " * 40, "\n", "é"):
        parses(junk)


# --- the check --------------------------------------------------------------------------


def test_the_check_is_registered() -> None:
    """A check module nothing imports registers nothing and every test still passes."""
    assert _CHECK_ID in [cid for cid, _ in registered(Tier.INTEGRITY)]


class _Layer:
    def __init__(self, name, framing=None):
        self.name = name
        self.framing = framing


class _Spec:
    def __init__(self, **kw):
        self.member = kw.get("member")
        self.plate_member = kw.get("plate_member")
        self.chord_member = kw.get("chord_member")
        self.web_member = kw.get("web_member")


class _Element:
    def __init__(self, kind, tag, **kw):
        self.element_kind = kind
        self.tag = tag
        for k, v in kw.items():
            setattr(self, k, v)


class _Member:
    def __init__(self, profile, key="stud-000"):
        self.profile = profile
        self.parent_uid = "UID"
        self.child_key = key


def _run(elements=(), assemblies=(), members=()):
    class _Library:
        pass

    library = _Library()
    library.assemblies = tuple(assemblies)

    class _Plan:
        def all_elements(self):
            return list(elements)

    plan = _Plan()
    plan.library = library

    class _Model:
        def all_members(self):
            return list(members)

    fn = next(fn for cid, fn in registered(Tier.INTEGRITY) if cid == _CHECK_ID)
    return fn(CheckContext(
        plan=plan, model=_Model(), preferences=Preferences(),
        profile=JurisdictionProfile(name="t", edition="t", effective_date="t",
                                    irc_base="t", coverage_statement="t")))


def test_a_steel_beam_size_is_flagged() -> None:
    """The case the guard was written for: a lintel spelled as the steel it is."""
    findings = _run(elements=[_Element("Beam", "BM-X", size="3.5x3.5 STEEL")])
    assert [f.result for f in findings] == [Result.UNKNOWN]
    assert "BM-X" in findings[0].element_tags
    assert "3.5x3.5 STEEL" in findings[0].message


def test_the_bounding_box_spelling_is_not_flagged() -> None:
    """``size="3.5x3.5"`` is a stated section and parses; only the unreadable spelling goes.

    This is catlin's own ``BM-M-FIRE-LINTEL``, whose ``engineering_note`` says outright that
    the size is the angle's bounding box. A check that flagged it would be asking the house
    to stop describing a member it has already described honestly.
    """
    findings = _run(elements=[_Element("Beam", "BM-X", size="3.5x3.5")])
    assert [f.result for f in findings] == [Result.PASS]


def test_a_product_model_in_a_size_field_is_not_swept() -> None:
    """``Connector.size`` is "HUC212-3" — a product, never a section. Field names lie."""
    findings = _run(elements=[_Element("Connector", "CN-X", size="HUC212-3"),
                              _Element("Post", "PT-X", size="6x6")])
    assert [f.result for f in findings] == [Result.PASS]


def test_a_framing_spec_names_its_assembly_and_layer() -> None:
    """The fix goes where the string was authored, so that is what the finding points at."""
    assembly = _Element("Assembly", "PARTITION")
    assembly.layers = (_Layer("channel", _Spec(member="HSS4x4x1/4")),)
    findings = _run(assemblies=[assembly],
                    members=[_Member("HSS4x4x1/4", f"rc-{i:03d}")
                             for i in range(64)])
    assert len(findings) == 1
    assert findings[0].element_tags == ("PARTITION/channel",)
    assert "64 resolved member(s)" in findings[0].message


def test_one_finding_per_distinct_string_not_per_stick() -> None:
    """64 sticks off one typo are one defect. A finding each would bury it."""
    findings = _run(members=[_Member("16x16", f"post-{i}") for i in range(20)])
    assert len(findings) == 1


def test_nothing_to_grade_is_not_applicable_not_silence() -> None:
    """Per CLAUDE.md: a check with nothing to say returns ``not_applicable()``, not ``[]``."""
    findings = _run()
    assert [f.result for f in findings] == [Result.NOT_APPLICABLE]


# --- the reference house ----------------------------------------------------------------


@pytest.fixture(scope="module")
def catlin_findings(catlin_model_ro, catlin_plan):
    from typehaus.checks import run_from_model

    report = run_from_model(catlin_model_ro, [], tier=Tier.INTEGRITY)
    return [f for f in report.findings if f.check_id == _CHECK_ID]


def test_catlin_is_graded_and_stays_out_of_the_red(catlin_findings) -> None:
    """WARN/UNKNOWN, never FAIL: ``scripts/verify.sh`` holds catlin to 0 FAIL, and the
    engine genuinely does not know what section the string names — it is not a verdict
    that the member is wrong."""
    assert catlin_findings
    assert not [f for f in catlin_findings if f.result is Result.FAIL]
    assert {f.severity.value for f in catlin_findings} == {"warn"}


def test_catlin_reads_every_profile_it_authors(catlin_findings) -> None:
    """The house's last unreadable string is gone, so the check PASSes outright.

    It used to be ``INT_2X4_RC``'s FURRING layer: a 1/2" hat channel that every lumber
    pattern must miss, resolving 64 strapping members to the 1 1/2" x 5 1/2" fallback and
    drawing them as 2x6 — 1" proud of the finish gypsum, into the room. Now a named-product
    literal in ``profiles.cross_section``. A new UNKNOWN here is a real regression, not
    noise.
    """
    assert [f.result for f in catlin_findings] == [Result.PASS]


def test_the_resilient_channel_is_the_hat_and_not_the_fallback() -> None:
    """The point of the literal, pinned against the fallback it replaced.

    Laid flat, ``width_m`` is the standoff through the band and ``depth_m`` the screw
    face — so 1/2" x 2 1/2", not the lumber order. Asserted against ``cross_section``
    directly: this is the number the drawn solid, the clash graders and the cut list all
    read.
    """
    section = cross_section("25 ga. resilient channel")
    assert section.shape == "rect"
    assert section.width_m == pytest.approx(inch(0.5).meters)
    assert section.depth_m == pytest.approx(inch(2.5).meters)
    assert section != cross_section("2x6")
