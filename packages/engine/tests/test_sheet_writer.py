"""compose_sheet: fixed paper, border + title block, TRUE printed scale (→ sheet_writer)."""

from __future__ import annotations

from datetime import date

import pytest

from typehaus.emit.draw.floorplan import build_floorplan
from typehaus.emit.draw.pdf_writer import _scene_bounds
from typehaus.emit.draw.scene import Polyline, Scene
from typehaus.emit.draw.sheet_writer import (
    ARCH_D,
    LEDGER,
    NTS_LABEL,
    compose_sheet,
    select_scale,
    viewport_box,
)
from typehaus.emit.draw.sheets import SheetSpec, build_sheet_index


def _fig_texts(fig) -> str:
    parts = [t.get_text() for t in fig.texts]
    for ax in fig.axes:
        parts.extend(t.get_text() for t in ax.texts)
    return "\n".join(parts)


# --- scale selection ----------------------------------------------------------


def test_select_scale_picks_largest_that_fits():
    # 40' x 24' plan in a ledger-ish viewport: 3/8" needs 15"x9" (too tall for 8.7"),
    # so 1/4" = 1'-0" (10" x 6") is the largest fit.
    scale, label = select_scale(40 * 12.0, 24 * 12.0, 15.5, 8.7)
    assert scale == 0.25
    assert label == "1/4\" = 1'-0\""


def test_select_scale_lands_detail_spans_on_large_scales():
    # A 3' x 4' detail prints 9" x 12" at 3" = 1'-0" — too tall, so 1-1/2" fits (4.5x6).
    scale, label = select_scale(3 * 12.0, 4 * 12.0, 15.0, 9.0)
    assert scale == 1.5
    assert label == "1-1/2\" = 1'-0\""

    scale, _ = select_scale(2 * 12.0, 2 * 12.0, 15.0, 9.0)
    assert scale == 3.0


def test_select_scale_continues_into_engineering_scales_for_parcels():
    # The catlin site plan (~100' x 165') overflows 1/16" = 1'-0" vertically; the civil
    # ladder catches it at the residential-survey standard 1" = 20'.
    scale, label = select_scale(100 * 12.0, 165 * 12.0, 16.2, 9.45)
    assert scale == 0.05
    assert label == "1\" = 20'"


def test_select_scale_falls_back_to_nts():
    # A 2000' span cannot print on ledger even at 1" = 100' (needs 20").
    scale, label = select_scale(2000 * 12.0, 1200 * 12.0, 15.5, 8.7)
    assert scale is None
    assert label == NTS_LABEL


def test_select_scale_uses_both_axes():
    # Wide-but-short: width limits the scale, not height.
    scale, _ = select_scale(60 * 12.0, 4 * 12.0, 14.0, 9.0)
    assert scale == 0.1875  # 3/16": 60' -> 11.25" wide; 1/4" would need 15"


# --- composed sheet -----------------------------------------------------------


def _tiny_scene(span_ft: float = 30.0) -> Scene:
    span_in = span_ft * 12.0
    return Scene(name="tiny", nodes=(
        Polyline(points=((0.0, 0.0), (span_in, 0.0), (span_in, span_in / 2.0),
                         (0.0, span_in / 2.0)), layer="A-WALL", closed=True),
    ))


def test_compose_sheet_page_size_is_the_preset(catlin_model):
    fig = compose_sheet(_tiny_scene(), SheetSpec("A-900", "Test"), catlin_model)
    assert tuple(fig.get_size_inches()) == LEDGER
    fig = compose_sheet(_tiny_scene(), SheetSpec("A-900", "Test"), catlin_model,
                        size=ARCH_D)
    assert tuple(fig.get_size_inches()) == ARCH_D


def test_compose_sheet_title_block_contents(catlin_model):
    spec = SheetSpec("A-901", "Chrome test sheet", north_arrow=True)
    fig = compose_sheet(_tiny_scene(), spec, catlin_model)
    text = _fig_texts(fig)
    assert "A-901" in text
    assert "Chrome test sheet" in text
    assert catlin_model.plan.project.name in text
    assert f"{catlin_model.plan.project.site.lat:.5f}" in text
    assert date.today().isoformat() in text
    assert "TYPE:HAUS" in text
    assert "REV" in text
    assert "N" in [t.get_text() for ax in fig.axes for t in ax.texts]  # north arrow


def test_compose_sheet_scale_is_exact_data_per_inch(catlin_model):
    """The printed scale is the truth: model inches per figure inch == 12 / scale_in."""
    scene = build_floorplan(catlin_model, "basement")
    spec = SheetSpec("A-101", "Basement floor plan")
    fig = compose_sheet(scene, spec, catlin_model)
    ax = fig.axes[0]

    u0, z0, u1, z1 = _scene_bounds(scene)
    view = viewport_box(LEDGER)
    scale_in, label = select_scale(u1 - u0, z1 - z0, view[2], view[3])
    assert scale_in is not None, "the catlin floor plan must land on a real scale"

    width_in = ax.get_position().width * fig.get_size_inches()[0]
    x0, x1 = ax.get_xlim()
    assert (x1 - x0) / width_in == pytest.approx(12.0 / scale_in)
    # and the title block prints that same scale
    assert label in _fig_texts(fig)
    # a known model dimension prints at exactly span * scale / 12 sheet inches
    printed = (u1 - u0) * scale_in / 12.0
    assert printed <= view[2]


def test_compose_sheet_nts_fallback_labels_honestly(catlin_model):
    fig = compose_sheet(_tiny_scene(span_ft=2000.0), SheetSpec("C-900", "Huge"),
                        catlin_model)
    assert NTS_LABEL in _fig_texts(fig)


def test_compose_sheet_draws_scale_bar_on_scaled_sheets(catlin_model):
    fig = compose_sheet(_tiny_scene(), SheetSpec("A-902", "Bar"), catlin_model)
    text = _fig_texts(fig)
    assert "SCALE" in text
    assert "0" in text  # bar origin label


# --- index integration --------------------------------------------------------


def test_index_gains_general_notes_after_cover(catlin_model):
    sheets = build_sheet_index(catlin_model)
    numbers = [s.number for s in sheets]
    assert numbers[0] == "A-000"
    assert numbers[1] == "G-002"
    assert sheets[1].page is not None


def test_plan_sheets_carry_north_arrows(catlin_model):
    sheets = {s.number: s for s in build_sheet_index(catlin_model)}
    assert sheets["C-101"].north_arrow
    assert sheets["S-100"].north_arrow
    assert sheets["S-101.1"].north_arrow
    assert sheets["S-102.1"].north_arrow
    assert sheets["A-101"].north_arrow
    assert not sheets["A-301"].north_arrow  # a section has no plan north
    assert not sheets["A-201"].north_arrow


def test_authored_sections_join_the_a301_series(catlin_model, monkeypatch):
    from typehaus.model.enums import SliceKind
    from typehaus.model.plan import PlanModel
    from typehaus.model.views import Slice
    from typehaus.quantities import ft, pt

    extra = Slice(uid="TESTSEC001", tag="SL-S-TEST", kind=SliceKind.SECTION,
                  title="Test cross section", cut_origin=pt(ft(0), ft(18)),
                  cut_direction="x")
    original = PlanModel.elements_of_kind

    def patched(self, kind):
        items = list(original(self, kind))
        if kind == "Slice":
            items.append(extra)
        return items

    monkeypatch.setattr(PlanModel, "elements_of_kind", patched)
    sheets = build_sheet_index(catlin_model)
    numbers = [s.number for s in sheets]
    assert "A-301.1" in numbers
    assert numbers.index("A-301.1") == numbers.index("A-301") + 1
    spec = next(s for s in sheets if s.number == "A-301.1")
    assert spec.title == "Test cross section"
    assert spec.scene is not None


def test_every_sheet_has_the_same_paper_size(catlin_model):
    assert all(s.size == LEDGER for s in build_sheet_index(catlin_model))
