"""resolve/ownership: derived solids belong to their parent by uid, never by tag prefix."""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.resolve.ownership import children_of, parent_uid
from typehaus.resolve.railings.parts import RAILING_INFILL_CATEGORY
from typehaus.takeoff.railings import _infill_solids


def _solid(uid: str, tag: str, category: str = RAILING_INFILL_CATEGORY):
    return SimpleNamespace(uid=uid, tag=tag, category=category)


def _model():
    # RL-FOO and RL-FOO-NE both exist: a tag prefix would hand RL-FOO the NE stub's parts.
    return SimpleNamespace(solids=[
        _solid("AAAA1-i000", "RL-FOO-BAL1"),
        _solid("AAAA1-i001", "RL-FOO-BAL2"),
        _solid("BBBB2-i000", "RL-FOO-NE-BAL1"),
        _solid("BBBB2-i001", "RL-FOO-NE-BAL2"),
        _solid("BBBB2-i002", "RL-FOO-NE-BAL3"),
        _solid("AAAA1-p00", "RL-FOO-POST1", "railing_post"),
        _solid("CCCC3", "SL-FOO"),
    ])


def test_parent_uid_reads_the_head_of_a_derived_uid():
    assert parent_uid("AAAA1-i000") == "AAAA1"
    assert parent_uid("AAAA1") is None


def test_children_of_does_not_take_a_longer_tags_parts():
    model = _model()
    foo = SimpleNamespace(uid="AAAA1", tag="RL-FOO")
    ne = SimpleNamespace(uid="BBBB2", tag="RL-FOO-NE")
    assert [s.tag for s in children_of(model, foo, (RAILING_INFILL_CATEGORY,))] == [
        "RL-FOO-BAL1", "RL-FOO-BAL2"]
    assert len(children_of(model, ne)) == 3
    assert len(children_of(model, foo)) == 3  # the post too, with no category filter


def test_railing_takeoff_counts_only_its_own_balusters():
    model = _model()
    assert len(_infill_solids(model, SimpleNamespace(uid="AAAA1", tag="RL-FOO"))) == 2
    assert len(_infill_solids(model, SimpleNamespace(uid="BBBB2", tag="RL-FOO-NE"))) == 3
