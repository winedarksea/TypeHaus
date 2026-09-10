"""Transition.star — authored curation of the primary detail set.

`star` marks the derived details a builder actually opens: `detail_index` serves it to
the UI, `build_sheet_index(details="primary")` composes only starred (plus authored)
detail sheets, and the flag round-trips to `houses/<house>/plan/transitions.py` through
the ordinary PatchOp writeback — which is why that file is `# haus: editable` now.
"""

from __future__ import annotations

import re
from types import SimpleNamespace


from typehaus.emit.draw.details import derive_detail_slices, detail_index
from typehaus.emit.draw.sheets import build_sheet_index
from typehaus.source import load_plan
from typehaus.source.coordinator import ProjectCoordinator
from typehaus.source.ops import PatchOp
from _helpers import CATLIN as CATLIN_DIR, copy_house

_DETAIL_NUMBER = re.compile(r"A-5\d\d$")


def test_star_reaches_the_detail_index(catlin_model):
    rows = detail_index(catlin_model)
    starred = {r["key"] for r in rows if r["star"]}
    unstarred = {r["key"] for r in rows if not r["star"]}
    # The eave transition is authored star=True; the interior-opening one is not.
    assert any(k.startswith("wall_roof:") for k in starred)
    assert any("INT_" in k for k in unstarred)


def test_permit_sheet_set_keeps_only_starred_derived_details(catlin_model):
    everything = build_sheet_index(catlin_model, sets="full")
    permit = build_sheet_index(catlin_model, sets="permit")
    det_all = [s for s in everything if _DETAIL_NUMBER.match(s.number)]
    det_permit = [s for s in permit if _DETAIL_NUMBER.match(s.number)]
    # The filter drops exactly the unstarred derived sheets, and every one it keeps is in
    # the permit set. (Non-detail sheets are NOT untouched any more — the permit set also
    # drops the E-1xx/P-1xx/BOM/finish sheets — but it is still a subset, in order.)
    assert len(det_permit) < len(det_all)
    assert all("permit" in s.sets for s in det_permit)
    assert len(det_all) - len(det_permit) == sum(1 for s in det_all
                                                 if "permit" not in s.sets)
    assert [s.number for s in permit] == [s.number for s in everything
                                          if s.number in {p.number for p in permit}]


def test_details_primary_is_still_an_alias_for_the_permit_set(catlin_model):
    """One test on the deprecated name. ``primary`` -> ``permit``, ``all`` -> ``full``."""
    assert ([s.number for s in build_sheet_index(catlin_model, details="primary")]
            == [s.number for s in build_sheet_index(catlin_model, sets="permit")])
    assert ([s.number for s in build_sheet_index(catlin_model, details="all")]
            == [s.number for s in build_sheet_index(catlin_model, sets="full")])


def test_haus_print_composes_the_permit_set_by_default():
    """`haus print` defaults to the submittal; `--set full` stays available.

    The library defaults (``build_sheet_index`` / ``write_permit_set``) deliberately stay
    ``"full"`` — the flip is a CLI decision about what a person handing a set in gets by
    default, not a change to what the composers do.
    """
    import inspect

    from typehaus.cli.app import print_sheets

    option = inspect.signature(print_sheets).parameters["set_"].default
    assert getattr(option, "default", option) == "permit"


def test_star_writes_back_to_the_real_transitions_source(tmp_path):
    house = tmp_path / "catlin"
    copy_house(CATLIN_DIR, house)
    source = house / "plan" / "transitions.py"
    assert 'tag="TR-CATLIN-EAVE"' in source.read_text()
    coordinator = ProjectCoordinator(house)
    coordinator.apply_patch(
        [PatchOp("update", "Transition", "TR-CATLIN-EAVE", {"star": False})],
        coordinator.revision())
    text = source.read_text()
    block = text[text.index('tag="TR-CATLIN-EAVE"'):text.index("TR-CATLIN-FOUNDATION")]
    assert "star=False" in block
    result = load_plan(house)
    assert result.plan is not None, [f.message for f in result.findings]
    eave = next(t for t in result.plan.library.transitions if t.tag == "TR-CATLIN-EAVE")
    assert eave.star is False


def _transition(**kwargs):
    from typehaus.model.views import Transition

    return Transition(tag="TR-T", condition_pattern="storey_stack:rim:*", **kwargs)


def test_stars_precedence_unstar_wins_and_star_is_the_default():
    """``stars(key)`` is the whole per-condition rule: unstar > star > pattern default."""
    key = "storey_stack:rim:INT_2X4_PARTITION"
    # Neither list: the pattern-wide flag answers, exactly as before overrides existed.
    assert _transition(star=True).stars(key) is True
    assert _transition(star=False).stars(key) is False
    # An override flips its own key and nothing else.
    assert _transition(star=False, starred_conditions=(key,)).stars(key) is True
    assert _transition(star=False, starred_conditions=(key,)).stars("other") is False
    assert _transition(star=True, unstarred_conditions=(key,)).stars(key) is False
    assert _transition(star=True, unstarred_conditions=(key,)).stars("other") is True
    # Contradictory authoring resolves one way, deterministically: the unstar wins.
    both = _transition(star=True, starred_conditions=(key,), unstarred_conditions=(key,))
    assert both.stars(key) is False
    assert _transition(star=False, starred_conditions=(key,),
                       unstarred_conditions=(key,)).stars(key) is False


def test_per_condition_overrides_curate_the_permit_sheet_set(catlin_model):
    """The interior rim/foundation keys are unstarred while their siblings stay primary."""
    rows = {r["key"]: r for r in detail_index(catlin_model)}
    # TR-CATLIN-EAVE is the live case since the 2026-09-08 star reduction: `star=False`
    # with two `starred_conditions` named. The house eave and the garage eave are two
    # different drawings; an interior partition dying into the roof deck is not an eave at
    # all and is drawn on the framing plan.
    interior = "wall_roof:INT_2X6_BRG|ROOF"
    exterior = "wall_roof:EXT_2X6|ROOF"
    # Same transition, same pattern-wide star, opposite effective answers.
    assert rows[interior]["transition"] == rows[exterior]["transition"]
    assert rows[interior]["transition_star"] is rows[exterior]["transition_star"] is False
    assert rows[interior]["star"] is False and rows[exterior]["star"] is True
    assert exterior in rows[exterior]["starred_conditions"]

    derived = derive_detail_slices(catlin_model)
    starred = {d.key for d in derived if d.transition.stars(d.key)}
    assert exterior in starred and interior not in starred
    # Every eave condition carries the same pattern-wide star, yet only some are in the
    # permit set — which is the whole point: one binding, individually curated details.
    eaves = [d for d in derived if d.transition.tag == rows[interior]["transition"]]
    assert not any(d.transition.star for d in eaves)
    assert 0 < len({d.key for d in eaves} & starred) < len(eaves)
    # The primary sheet set drops exactly the details ``stars()`` says are not primary.
    det_all = [s for s in build_sheet_index(catlin_model, sets="full")
               if _DETAIL_NUMBER.match(s.number)]
    det_permit = [s for s in build_sheet_index(catlin_model, sets="permit")
                  if _DETAIL_NUMBER.match(s.number)]
    assert len(det_all) - len(det_permit) == len(derived) - len(starred)


def test_stale_override_keys_are_reported(catlin_model):
    from typehaus.checks.code.mn_residential.profile import MN_2020
    from typehaus.checks.integrity.checks import condition_star_override
    from typehaus.checks.registry import CheckContext, Preferences

    ctx = CheckContext(plan=catlin_model.plan, model=catlin_model,
                       preferences=Preferences(), profile=MN_2020)
    assert condition_star_override(ctx) == []
    # A renamed assembly leaves an override addressing a key nothing derives any more —
    # that has to surface, or the primary set silently re-curates itself.
    def messages(*overrides):
        library = SimpleNamespace(transitions=overrides)
        stub = SimpleNamespace(plan=SimpleNamespace(library=library), model=ctx.model)
        return [f.message for f in condition_star_override(stub)]

    stale = _transition(star=True, unstarred_conditions=("storey_stack:rim:RENAMED",))
    said = messages(stale)
    assert len(said) == 1 and "RENAMED" in said[0]
    # A live key the transition's own pattern cannot match is inert, and says so.
    inert = _transition(star=True,
                        unstarred_conditions=("wall_foundation:GARAGE_ICF_6|GARAGE_WALL_2X6",))
    said = messages(inert)
    assert len(said) == 1 and "does not match" in said[0]
    # A live, matching key is what an override is supposed to look like: silence.
    live = "storey_stack:rim:INT_2X4_PARTITION|INT_2X4_STAGGERED_GWB"
    assert messages(_transition(unstarred_conditions=(live,))) == []


def test_per_condition_override_writes_back_to_source(tmp_path):
    """The UI's one-PatchOp star toggle round-trips as a list field, like any other."""
    house = tmp_path / "catlin"
    copy_house(CATLIN_DIR, house)
    coordinator = ProjectCoordinator(house)
    # TR-CATLIN-EAVE is `star=False` with two named `starred_conditions` — catlin curates
    # by key, not by pattern (the four interior-partition-to-roof keys are not drawings).
    # The toggle under test is therefore the other direction: unstar one of the two.
    key = "wall_roof:GARAGE_ROOF|GARAGE_WALL_2X6"
    coordinator.apply_patch(
        [PatchOp("update", "Transition", "TR-CATLIN-EAVE",
                 {"starred_conditions": [], "unstarred_conditions": [key]})],
        coordinator.revision())
    result = load_plan(house)
    assert result.plan is not None, [f.message for f in result.findings]
    eave = next(t for t in result.plan.library.transitions if t.tag == "TR-CATLIN-EAVE")
    assert eave.unstarred_conditions == (key,)
    assert eave.starred_conditions == ()
    assert eave.star is False and eave.stars(key) is False
    # The other key was starred BY NAME, and the patch cleared that list, so it goes too —
    # which is the round trip working: both list fields wrote back.
    assert eave.stars("wall_roof:EXT_2X6|ROOF") is False
