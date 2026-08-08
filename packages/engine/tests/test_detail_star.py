"""Transition.star — authored curation of the primary detail set (2026-07-31).

`star` marks the derived details a builder actually opens: `detail_index` serves it to
the UI, `build_sheet_index(details="primary")` composes only starred (plus authored)
detail sheets, and the flag round-trips to `houses/<house>/plan/transitions.py` through
the ordinary PatchOp writeback — which is why that file is `# haus: editable` now.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from typehaus.emit.draw.details import derive_detail_slices, detail_index
from typehaus.emit.draw.sheets import build_sheet_index
from typehaus.resolve import resolve
from typehaus.source import load_plan
from typehaus.source.coordinator import ProjectCoordinator
from typehaus.source.ops import PatchOp

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"
_DETAIL_NUMBER = re.compile(r"A-4\d\d$")


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    assert result.plan is not None
    model, _ = resolve(result.plan)
    return model


def test_star_reaches_the_detail_index(catlin_model):
    rows = detail_index(catlin_model)
    starred = {r["key"] for r in rows if r["star"]}
    unstarred = {r["key"] for r in rows if not r["star"]}
    # The eave transition is authored star=True; the interior-opening one is not.
    assert any(k.startswith("wall_roof:") for k in starred)
    assert any("INT_" in k for k in unstarred)


def test_primary_sheet_set_keeps_only_starred_derived_details(catlin_model):
    everything = build_sheet_index(catlin_model)
    primary = build_sheet_index(catlin_model, details="primary")
    det_all = [s for s in everything if _DETAIL_NUMBER.match(s.number)]
    det_primary = [s for s in primary if _DETAIL_NUMBER.match(s.number)]
    # The filter drops exactly the unstarred derived sheets; everything it keeps is
    # flagged primary, and non-detail sheets are untouched.
    assert len(det_primary) < len(det_all)
    assert all(s.primary for s in det_primary)
    assert len(det_all) - len(det_primary) == sum(1 for s in det_all if not s.primary)
    non_detail = lambda sheets: [s.number for s in sheets  # noqa: E731
                                 if not _DETAIL_NUMBER.match(s.number)]
    assert non_detail(everything) == non_detail(primary)


def test_haus_print_composes_the_primary_set_by_default():
    """`haus print` defaults to the curated primary set; `--details all` stays available.

    The library defaults (``build_sheet_index`` / ``write_permit_set``) deliberately stay
    ``"all"`` — the flip is a CLI decision about what a builder gets by default, not a
    change to what the composers do.
    """
    import inspect

    from typehaus.cli.app import print_sheets

    option = inspect.signature(print_sheets).parameters["details"].default
    assert getattr(option, "default", option) == "primary"


def test_star_writes_back_to_the_real_transitions_source(tmp_path):
    house = tmp_path / "catlin"
    shutil.copytree(CATLIN_DIR, house,
                    ignore=shutil.ignore_patterns("out", "__pycache__", ".claude"))
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


def test_per_condition_overrides_curate_the_primary_sheet_set(catlin_model):
    """The interior rim/foundation keys are unstarred while their siblings stay primary."""
    rows = {r["key"]: r for r in detail_index(catlin_model)}
    interior = "storey_stack:rim:INT_2X4_PARTITION"
    exterior = "storey_stack:rim:CATLIN_EXT_2X6"
    # Same transition, same pattern-wide star, opposite effective answers.
    assert rows[interior]["transition"] == rows[exterior]["transition"]
    assert rows[interior]["transition_star"] is rows[exterior]["transition_star"] is True
    assert rows[interior]["star"] is False and rows[exterior]["star"] is True
    assert interior in rows[interior]["unstarred_conditions"]

    derived = derive_detail_slices(catlin_model)
    starred = {d.key for d in derived if d.transition.stars(d.key)}
    assert exterior in starred and interior not in starred
    # Every rim condition carries the same pattern-wide star, yet only some are primary —
    # which is the whole point: one binding, individually curated details.
    rim = [d for d in derived if d.transition.tag == rows[interior]["transition"]]
    assert all(d.transition.star for d in rim)
    assert 0 < len({d.key for d in rim} & starred) < len(rim)
    # The primary sheet set drops exactly the details ``stars()`` says are not primary.
    det_all = [s for s in build_sheet_index(catlin_model) if _DETAIL_NUMBER.match(s.number)]
    det_primary = [s for s in build_sheet_index(catlin_model, details="primary")
                   if _DETAIL_NUMBER.match(s.number)]
    assert len(det_all) - len(det_primary) == len(derived) - len(starred)


def test_stale_override_keys_are_reported(catlin_model):
    from typehaus.checks.code.mn_residential.profile import MN_2024
    from typehaus.checks.integrity.checks import condition_star_override
    from typehaus.checks.registry import CheckContext, Preferences

    ctx = CheckContext(plan=catlin_model.plan, model=catlin_model,
                       preferences=Preferences(), profile=MN_2024)
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
                        unstarred_conditions=("wall_foundation:GARAGE_ICF_8|GARAGE_WALL_2X6",))
    said = messages(inert)
    assert len(said) == 1 and "does not match" in said[0]
    # A live, matching key is what an override is supposed to look like: silence.
    assert messages(_transition(unstarred_conditions=("storey_stack:rim:INT_2X4_PARTITION",))) == []


def test_per_condition_override_writes_back_to_source(tmp_path):
    """The UI's one-PatchOp star toggle round-trips as a list field, like any other."""
    house = tmp_path / "catlin"
    shutil.copytree(CATLIN_DIR, house,
                    ignore=shutil.ignore_patterns("out", "__pycache__", ".claude"))
    coordinator = ProjectCoordinator(house)
    key = "wall_roof:GARAGE_ROOF|GARAGE_WALL_2X6"
    coordinator.apply_patch(
        [PatchOp("update", "Transition", "TR-CATLIN-EAVE",
                 {"starred_conditions": [], "unstarred_conditions": [key]})],
        coordinator.revision())
    result = load_plan(house)
    assert result.plan is not None, [f.message for f in result.findings]
    eave = next(t for t in result.plan.library.transitions if t.tag == "TR-CATLIN-EAVE")
    assert eave.unstarred_conditions == (key,)
    assert eave.star is True and eave.stars(key) is False
    assert eave.stars("wall_roof:CATLIN_EXT_2X6|CATLIN_ROOF") is True
