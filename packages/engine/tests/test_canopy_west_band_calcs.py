"""The canopy's west band, heads, bases and open front, against ``notes/canopy_west_band.md``.

The note is hand-worked with plain arithmetic and no engine import; this module reproduces its
rows on the landed house (``kdat``), the band being ``SB-BW-BAND``'s 45° slats, and pins the two
refusals: a band nothing bridges makes the record INCOMPLETE by name, and the drift limit's N/A
is earned only from SDC A.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from typehaus.engineering.item import Status

_ITEM = "lateral_system/RF-BW-CANOPY"

#: §3, §4 and §6: ``row name -> (demand, capacity)``. §3's slat band since 2026-10-04.
_ROWS = {
    "W-BW-SCREEN unit shear": (190.96, 265.0),
    "W-BW-SCREEN aspect ratio": (0.751, 3.5),
    "SB-BW-BAND slat end, KBS1Z": (183.56, 540.0),
    "SB-BW-BAND slat buckling": (183.56, 4901.2),
    "SB-BW-BAND centre post bending": (88.20, 1360.0),
    "SB-BW-BAND centre post end ties": (389.38, 1390.0),
    "SB-BW-BAND top plate screws into BM-BW-RW": (162.24, 659.17),
    "SB-BW-BAND sill screws into W-BW-SCREEN's top plate": (162.24, 659.17),
    "W-BW-SCREEN top plate end bearing on a chord": (98.89, 251.25),
    "W-BW-SCREEN base plate and sill end bearing on a chord": (64.39, 251.25),
    "BM-BW-RW eave collector clips": (173.06, 450.0),
    "W-BW-SCREEN chord hold-down, full height": (2227.6, 3060.0),
    "W-BW-SCREEN chord base shear, one base": (1038.35, 1270.0),
    "diaphragm unit shear at W-BW-SCREEN": (173.06, 190.0),
    "LSTA24 end straps, chord force + across share": (259.78, 823.3333333333334),
    "BM-BW-RW chord into CN-BW-JOINT-1's block": (216.42, 450.0),
    "BM-BW-RE chord into CN-BW-JOINT-7's block": (86.72, 450.0),
    "W-G-W joint couple, E-W case": (4.64, 182.5),
    "W-G-E joint couple, E-W case": (4.13, 182.5),
}


@pytest.fixture(scope="module")
def record(catlin_ctx):
    return catlin_ctx.engineering[_ITEM]


def test_the_band_rows_reproduce_the_note(record) -> None:
    assert record.status is Status.OK, record.summary
    assert not record.missing
    states = {s.name: s for s in record.limit_states}
    for name, (demand, capacity) in _ROWS.items():
        assert name in states, f"{name} is not on the record"
        assert states[name].demand == pytest.approx(demand, rel=2e-3, abs=0.01), name
        assert states[name].capacity == pytest.approx(capacity, rel=1e-3), name
    assert "NOMINAL ONLY" not in states["BM-BW-RW eave collector clips"].citation


def test_the_band_inputs_reproduce_section_1_and_4b(record) -> None:
    values = {q.name: q.value for q in record.inputs}
    assert values["band_height_W-BW-SCREEN"] == pytest.approx(2.34375, abs=1e-4)
    assert values["overturning_height_W-BW-SCREEN"] == pytest.approx(8.625, abs=1e-3)
    assert values["joint_couple_lb_ft"] == pytest.approx(2081.3, abs=1.0)
    assert values["chord_force_open_front_lb"] == pytest.approx(86.7, abs=0.1)


def test_the_slat_band_reproduces_section_3a_and_3b(record) -> None:
    """§3a-b: 24.375" x 25.125" bays, four braced slats across mid-band, 183.56 lb a slat."""
    values = {q.name: q.value for q in record.inputs}
    assert values["slat_bay_width_SB-BW-BAND"] == pytest.approx(24.375, abs=1e-3)
    assert values["slat_bay_height_SB-BW-BAND"] == pytest.approx(25.125, abs=1e-3)
    assert values["slats_crossing_mid_SB-BW-BAND"] == 4
    assert values["slat_force_SB-BW-BAND"] == pytest.approx(183.56, abs=0.01)
    assert not any("band strap tension" in s.name for s in record.limit_states)


def test_the_old_anchor_rows_are_gone_with_the_bolt(record) -> None:
    """§4b: the CBSQ's cracked row is measured through the concrete; no ACI Ch. 17 row."""
    assert not any("anchor tension" in s.name for s in record.limit_states)
    assert any("CBSQ66-SDS2 is cast in" in note for note in record.notes)


def test_the_drift_limit_is_not_applicable_on_evidence(record) -> None:
    assert any("DRIFT LIMIT — NOT APPLICABLE, earned" in note for note in record.notes)


def test_a_missing_seismic_category_does_not_earn_the_na(catlin_ctx) -> None:
    from typehaus.engineering.lateral_system import compute

    ctx = replace(catlin_ctx.engineering.context, seismic_design_category=None)
    found = next(r for r in compute(ctx) if r.item_id == _ITEM)
    assert found.status is Status.INCOMPLETE
    assert any("seismic design category" in text for text in found.missing)


class _WithoutStraps:
    """The plan with every band brace (slat or strap) removed — the ``_Swapped`` idiom."""

    def __init__(self, plan):
        self._plan = plan

    def all_elements(self):
        from typehaus.model.braces import SlatBrace, StrapBrace

        return [e for e in self._plan.all_elements()
                if not isinstance(e, (SlatBrace, StrapBrace))]

    def __getattr__(self, name):
        return getattr(self._plan, name)


def test_an_unbridged_band_is_incomplete_by_name(catlin_ctx) -> None:
    """§2: a panel under the roof in PLAN that stops short of its collector is not reached."""
    from typehaus.engineering.lateral_system import compute

    ctx = replace(catlin_ctx.engineering.context, plan=_WithoutStraps(catlin_ctx.plan))
    found = next(r for r in compute(ctx) if r.item_id == _ITEM)
    assert found.status is Status.INCOMPLETE
    assert any("band between W-BW-SCREEN's top" in text for text in found.missing)


#: §5c, ``post -> {row: ratio}``; a chord's along rows and its column carry the band push.
_POSTS = {
    "PT-BW-CW": {"ACE6Z head, uplift + lateral along the beam": 0.530,
                 "A35Z head, across the beam": 0.163,
                 "A35Z panel top plate into the post": 0.175,
                 "CBSQ66-SDS2 base, uplift + lateral across the beam": 0.277,
                 "CBSQ66-SDS2 base, uplift + lateral along the beam": 0.210,
                 "NDS combined axial and bending": 0.386},
    "PT-BW-CNW": {"AC6Z head, uplift + lateral along the beam": 0.399,
                  "A35Z head, across the beam": 0.082,
                  "NDS combined axial and bending": 0.386},
    "PT-BW-RE": {"ACE6Z head, uplift + lateral along the beam": 0.233,
                 "CBSQ66-SDS2 base, uplift + lateral across the beam": 0.189,
                 "NDS combined axial and bending": 0.225},
    "PT-BW-RNE": {"AC6Z head, uplift + lateral along the beam": 0.164,
                  "CBSQ66-SDS2 base, uplift + lateral along the beam": 0.159},
}


@pytest.mark.parametrize("post", sorted(_POSTS))
def test_every_post_has_a_rated_head_and_base(catlin_ctx, post) -> None:
    found = catlin_ctx.engineering[f"wood_roof_post/{post}"]
    assert found.status is Status.OK, found.summary
    ratios = {s.name: s.demand / s.capacity for s in found.limit_states}
    for name, ratio in _POSTS[post].items():
        assert ratios[name] == pytest.approx(ratio, abs=0.002), (post, name)


def test_the_chord_heads_carry_the_band_couple(catlin_ctx) -> None:
    """§5b: 428.9 + max(206.4 header depth, 169.2 slat couple) = 635.3 lb at a chord's head,
    and the compression bay's 389.38 lb push across the band."""
    found = catlin_ctx.engineering["wood_roof_post/PT-BW-CW"]
    values = {q.name: q.value for q in found.inputs}
    assert values["head_uplift_lb"] == pytest.approx(635.3, abs=0.2)
    assert values["plate_load_lb"] == pytest.approx(121.48, abs=0.05)
    assert values["band_push_lb"] == pytest.approx(389.38, abs=0.05)


def test_the_glulam_header_reproduces_section_7(catlin_ctx) -> None:
    found = catlin_ctx.engineering["roof_beam/BM-BW-RW"]
    assert found.status is Status.OK
    states = {s.name: s for s in found.limit_states}
    assert states["bearing on the post"].demand == pytest.approx(122.2, abs=0.3)
    assert states["bearing on the post"].capacity == pytest.approx(344.5, abs=0.1)
    assert states["bending"].demand / states["bending"].capacity == pytest.approx(0.146,
                                                                                abs=0.002)


def test_the_cbsq_piers_are_14_inches_for_the_side_cover(catlin_plan) -> None:
    """§5e: a 12" round leaves the straps 2 3/4" of cover against ESR-3050's 3"."""
    for tag in ("PT-BW-W", "PT-BW-GW", "PT-BW-PE", "PT-BW-PNE"):
        assert catlin_plan.by_tag(tag).size == "14 round", tag
