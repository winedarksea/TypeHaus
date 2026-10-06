"""The canopy's delivery to the garage, against ``notes/canopy_garage_diaphragm.md`` §2-§4.

The note is hand-worked in a separate pass with plain arithmetic and no engine import; this
module reproduces its rows on the landed house (``kdat``, on the glulam headers) and pins the two
behaviours a delivery must have when a part is missing: an unresolved reference makes the
record INCOMPLETE by name, and a PINNED post mints no ``column_base`` of its own.
"""

from __future__ import annotations

import pytest

from typehaus.engineering.item import Status

_ITEM = "lateral_system/RF-BW-CANOPY"

#: §2 — the ASD pressure on any band, and the deck-level shears with pinned 6x6 posts.
_PRESSURE_PSF = 16.8315
_DELIVERED = {"x": 694.6, "y": 1045.1}

#: §3-§4, the kdat column of every table: ``row name -> (demand, capacity)``. The panel and
#: everything under it moved to ``canopy_west_band.md`` (``test_canopy_west_band_calcs``).
_ROWS = {
    "open front, L'": (6.000, 25.0),
    "open front, L'/W'": (0.2250, 1.0),
    "joint boundary nailing, along": (28.94, 190.0),
    "LSTA24 joint straps, across": (149.29, 823.3333333333334),
    "LSTA24 joint straps, rotation couple": (56.10, 823.3333333333334),
    "LTP4 plate clips, frame into wall": (99.23, 450.0),
    "RF-GARAGE unit-shear increment": (22.76, 167.5),
    "W-G-S delivered shear on the surplus": (43.03, 182.5),
    "W-G-E delivered shear on the surplus": (27.70, 182.5),
    "W-G-W delivered shear on the surplus": (28.67, 182.5),
    "W-G-S overturning, delivered increment": (283.5, 3065.0),
    "diaphragm unit shear at W-BW-SCREEN": (174.18, 190.0),
}


@pytest.fixture(scope="module")
def record(catlin_ctx):
    return catlin_ctx.engineering[_ITEM]


def test_the_pinned_posts_split_their_drag_half_to_each_end(catlin_ctx) -> None:
    """§2: 16.8315 psf x 5.5/12 x 6.1771' = 47.65 lb, 23.83 lb to each end."""
    from typehaus.engineering.roof_lateral import roof_winds

    wind = roof_winds(catlin_ctx.engineering.context)["RF-BW-CANOPY"]
    assert wind.pressure_psf == pytest.approx(_PRESSURE_PSF, abs=5e-4)
    posts = {p.tag: p for p in wind.pinned}
    assert set(posts) == {"PT-BW-RE", "PT-BW-RNE"}, "a within_wall post is the wall's face"
    for post in posts.values():
        assert post.drag_lb == pytest.approx(47.65, abs=0.02)
        assert post.head_lb == pytest.approx(post.base_lb) == pytest.approx(23.83, abs=0.01)
    for axis, lb in _DELIVERED.items():
        assert wind.delivered_lb(axis) == pytest.approx(lb, abs=0.1)
    # §3b: the E-W resultant 3.016' off the joint.
    assert wind.resultant_ft("x") == pytest.approx(40.203, abs=0.002)


def test_the_record_reproduces_sections_3_and_4(record) -> None:
    assert record.status is Status.OK, record.summary
    assert not record.missing
    states = {s.name: s for s in record.limit_states}
    for name, (demand, capacity) in _ROWS.items():
        assert name in states, f"{name} is not on the record"
        assert states[name].demand == pytest.approx(demand, rel=2e-3, abs=0.01), name
        assert states[name].capacity == pytest.approx(capacity, rel=1e-6), name


def test_the_screen_boundary_governs(record) -> None:
    """§4d: the envelope row over the envelope share — 0.917, and nothing else is closer."""
    worst = max(record.limit_states, key=lambda s: s.demand / s.capacity)
    assert worst.name == "diaphragm unit shear at W-BW-SCREEN"
    assert worst.demand / worst.capacity == pytest.approx(0.917, abs=0.001)


def test_the_old_four_to_one_row_is_gone_with_the_second_line(record) -> None:
    """§3a: with pinned east posts the deck does not span between two N-S lines."""
    assert "diaphragm span-to-depth" not in {s.name for s in record.limit_states}


def test_the_receivers_are_on_the_record_and_graded_by_nobody_else(catlin_ctx) -> None:
    record = catlin_ctx.engineering[_ITEM]
    for tag in ("RF-GARAGE", "W-G-S", "W-G-E", "W-G-W", "CN-G-BWHD-S-DR"):
        assert tag in record.element_tags
    assert "lateral_system/RF-GARAGE" not in catlin_ctx.engineering, (
        "a roof that only RECEIVES is graded on the delivering roof's item")


def test_the_landing_tie_reads_the_envelope_share(catlin_ctx) -> None:
    """§4e: the tie's N-S panel load is the whole 1,045.1 lb; its E-W row still governs."""
    record = catlin_ctx.engineering["deck_tie/FS-BW-FLOOR"]
    loads = {q.name: q.value for q in record.inputs}
    assert loads["y:W-BW-SCREEN panel share of RF-BW-CANOPY"] == pytest.approx(1045.1, abs=0.1)
    assert record.status is Status.OK
    worst = max(record.limit_states, key=lambda s: s.demand / s.capacity)
    assert "E-W" in worst.name


class _Swapped:
    """A plan with one element replaced — the ``_PlanWithTheBells`` idiom, by tag."""

    def __init__(self, plan, replacement):
        self._plan = plan
        self._new = replacement

    def all_elements(self):
        return [self._new if getattr(e, "tag", None) == self._new.tag else e
                for e in self._plan.all_elements()]

    def by_tag(self, tag):
        return self._new if tag == self._new.tag else self._plan.by_tag(tag)

    def __getattr__(self, name):
        return getattr(self._plan, name)


def _canopy_with(catlin_ctx, **delivery):
    from dataclasses import replace

    from typehaus.engineering.lateral_system import compute

    roof = catlin_ctx.plan.by_tag("RF-BW-CANOPY")
    spec = roof.diaphragm
    changed = spec.model_copy(update={
        "delivers_to": spec.delivers_to.model_copy(update=delivery)})
    plan = _Swapped(catlin_ctx.plan, roof.model_copy(update={"diaphragm": changed}))
    ctx = replace(catlin_ctx.engineering.context, plan=plan)
    return next(r for r in compute(ctx) if r.item_id == _ITEM)


def test_an_unresolved_joint_part_is_incomplete_by_name(catlin_ctx) -> None:
    record = _canopy_with(catlin_ctx, joint_refs=("CN-BW-JOINT-1", "CN-NOWHERE-9"))
    assert record.status is Status.INCOMPLETE
    assert any("CN-NOWHERE-9" in text for text in record.missing)


def test_joint_attachment_gap_is_explicit_despite_passing_nominal_capacity(catlin_ctx):
    record = _canopy_with(catlin_ctx, joint_attachment_missing="end nailing not detailed")
    assert record.status is Status.INCOMPLETE
    assert any("end nailing not detailed" in missing for missing in record.missing)
    assert all(state.ok for state in record.limit_states)
    # The resolved framing now completes both independently checked attachments.
    detailed_record = _canopy_with(catlin_ctx, joint_attachment_missing=None)
    assert not any("joint attachment" in text for text in detailed_record.missing)
    assert detailed_record.status is Status.OK
    assert not detailed_record.missing


def test_an_axial_strap_rating_cannot_replace_continuous_deck_shear(catlin_ctx):
    delivery = catlin_ctx.plan.by_tag("RF-BW-CANOPY").diaphragm.delivers_to
    recipe = delivery.joint_nailing.model_copy(update={"continuous_deck": False})
    record = _canopy_with(catlin_ctx, joint_nailing=recipe)
    assert record.status is Status.INCOMPLETE
    assert any("no transverse shear capacity" in text for text in record.missing)
    assert "LSTA24 joint straps, along" not in {state.name for state in record.limit_states}


def test_an_unresolved_receiving_roof_is_incomplete_by_name(catlin_ctx) -> None:
    record = _canopy_with(catlin_ctx, roof="RF-NOWHERE")
    assert record.status is Status.INCOMPLETE
    assert any("RF-NOWHERE" in text for text in record.missing)


def test_a_receiving_wall_the_geometry_disagrees_with_is_refused(catlin_ctx) -> None:
    from typehaus import ReceivingLine

    stray = ReceivingLine(wall="W-M-N2", unit_shear_asd_plf=182.5,
                          apparent_stiffness_kips_per_in=11.0, source="a house wall")
    record = _canopy_with(catlin_ctx, lines=(stray,))
    assert record.status is Status.INCOMPLETE
    assert any("W-M-N2" in text and "geometry" in text for text in record.missing)


def test_a_pinned_post_mints_no_column_base(catlin_ctx) -> None:
    """The pier under it is graded as a short pole; the post itself is not a column base."""
    keys = set(catlin_ctx.engineering)
    assert "column_base/PT-BW-RE" not in keys and "column_base/PT-BW-RNE" not in keys
    assert {"column_base/PT-BW-PE", "column_base/PT-BW-PNE"} <= keys
    for tag in ("PT-BW-PE", "PT-BW-PNE"):
        assert f"column_head_joint/{tag}" not in keys, "the head is the post's base plate"
        assert f"base_rotation/{tag}" not in keys, "a short pole has no P-delta to magnify"


@pytest.mark.parametrize(("tag", "shaft"), [("PT-BW-PE", 6.120), ("PT-BW-PNE", 3.500)])
def test_the_pier_is_a_short_pole(catlin_ctx, tag, shaft) -> None:
    """§6: 82.74 lb at 1.932' above grade on the 14" pier; 2.48' of shaft needed, the pad
    credited below."""
    record = catlin_ctx.engineering[f"column_base/{tag}"]
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["lateral_shear_asd"] == pytest.approx(82.74, abs=0.05)
    assert inputs["shear_height_above_grade"] == pytest.approx(1.932, abs=0.002)
    assert inputs["shaft_embedment"] == pytest.approx(shaft, abs=0.002)
    embedment = record.limit_states[0]
    assert embedment.demand <= 2.478 + 1e-3, "basis 4's pad credit only ever reads lower"
    assert record.status is Status.OK
