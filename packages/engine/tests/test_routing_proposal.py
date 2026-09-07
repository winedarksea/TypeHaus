"""A proposal has to be dialect source somebody can paste, and this is what says so.

Two halves, and the second is the stronger one:

* the printed literal **round-trips through the loader** — it parses, the dialect accepts
  it, and the quantities come back within a sixteenth of what was proposed;
* a run built from a proposal, resolved, and put through the routing checks **passes them**.
  A router graded only by its own cost function is a router that agrees with itself.
"""

from __future__ import annotations

import pathlib

import pytest
from _helpers import CATLIN, copy_house

from typehaus.quantities import M_PER_IN
from typehaus.routing.proposal import RouteProposal, length_source, render, snap

pytestmark = pytest.mark.slow

_IN = M_PER_IN


def _proposal(points, **kwargs) -> RouteProposal:
    return RouteProposal(
        tag=kwargs.pop("tag", "PR-TEST-PROPOSED"), kind="pipe",
        points=[(x * _IN, y * _IN, z * _IN) for x, y, z in points],
        diameter_m=kwargs.pop("diameter_in", 2.0) * _IN,
        serves=kwargs.pop("serves", ("FX-S-SUITEBATH-WC",)), **kwargs).snapped()


def test_a_negative_elevation_is_printed_in_inches_not_feet_and_inches() -> None:
    """``ft(f, i)`` is ``f * 12 + i``, so a negative elevation cannot be written that way at
    all — ``ft(-7, 10)`` raises and ``ft(-0, 8)`` is caught by ``dialect.mixed_sign_ft``. A
    basement invert is negative, and printing one as a feet-inches pair is how a proposal
    becomes an un-loadable file."""
    assert length_source(-18.6 * _IN).to_source().startswith("inch(")
    assert length_source(3.0 * _IN).to_source() == "inch(3)"
    assert length_source(115.5 * _IN).to_source() == "ft(9, 7.5)"


def test_a_one_tuple_keeps_its_trailing_comma() -> None:
    """The editable dialect needs it and ``build --inspect`` is what says so."""
    source = _proposal([(0, 0, 120), (0, 0, 118)]).source()
    assert 'serves=("FX-S-SUITEBATH-WC",)' in source


def test_the_source_carries_no_operator_and_no_uid() -> None:
    """The dialect is a constrained declarative subset: literals and constructors, nothing
    computed. And a uid is minted by ``haus fmt``, never handed out — a hand-written one is
    the thing this repo forbids outright."""
    source = _proposal([(0, 0, 120), (60, 0, 119), (60, 60, 118)]).source()
    for banned in ("+", "*", "/", "uid=", "frozenset"):
        assert banned not in source, banned


def test_the_printed_literal_round_trips_through_the_loader(tmp_path) -> None:
    """The whole promise: what is printed can be pasted.

    Written into a copy of the house rather than the house itself — the source under test
    is a proposal, and the one thing ``haus route`` must never do is edit a plan file.
    """
    from typehaus.source import load_plan

    house = copy_house(CATLIN, tmp_path / "house")
    proposal = _proposal(
        [(134.81, 250.625, 120.75), (134.81, 250.625, 116.5),
         (134.81, 202.8, 113.375), (156.0, 202.8, 112.0)],
        diameter_in=3.0, tag="PR-TEST-ROUNDTRIP")

    target = pathlib.Path(house) / "plan" / "mep_drainage.py"
    text = target.read_text()
    body = proposal.source(storey_datum_m=0.0)
    text = text.replace("SECOND_DRAINS = [",
                        f"SECOND_DRAINS = [\n    {body}\n", 1)
    target.write_text(text)

    loaded = load_plan(pathlib.Path(house))
    errors = [f for f in loaded.findings if f.severity.value == "error"]
    assert loaded.plan is not None, [f.message for f in loaded.findings]
    # A missing uid is the ONE expected complaint: `haus fmt` mints it, and a proposal that
    # handed one out would be doing the thing the non-negotiables forbid.
    assert all("uid" in f.message for f in errors), [f.message for f in errors]

    run = next(e for storey in loaded.plan.storeys
               for e in loaded.plan.storey_elements(storey.tag)
               if getattr(e, "tag", None) == "PR-TEST-ROUNDTRIP")
    for point, (x, y, _z) in zip(run.path, proposal.points, strict=True):
        assert point.xy_m[0] == pytest.approx(x, abs=1 / 32 * _IN)
        assert point.xy_m[1] == pytest.approx(y, abs=1 / 32 * _IN)
    for length, (_x, _y, z) in zip(run.elevations, proposal.points, strict=True):
        assert length.meters == pytest.approx(z, abs=1 / 32 * _IN)


def test_snapping_happens_before_the_numbers_are_printed() -> None:
    """"What is printed is what was verified" is only true if the snap comes first. A
    coordinate 1/100" off the grid comes back on it, and a vertex that snapping collapses
    onto its neighbour is dropped — two points at one place are one point."""
    raw = RouteProposal(tag="T", kind="pipe", diameter_m=2 * _IN,
                        points=[(0.0, 0.0, 0.0), (0.001 * _IN, 0.0, 0.0),
                                (12.0 * _IN, 0.0, 0.0)])
    snapped = raw.snapped()
    assert len(snapped.points) == 2
    assert all(v == snap(v) for point in snapped.points for v in point)


def test_the_banner_cannot_be_mistaken_for_a_file() -> None:
    """A block of dialect source in a terminal looks exactly like a file, and the one thing
    a reader must not conclude is that it has been written anywhere."""
    text = render([_proposal([(0, 0, 120), (60, 0, 119)])])
    assert "PROPOSED, NOT WRITTEN" in text
    assert "Nothing on disk changed" in text
