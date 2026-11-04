"""The cover's sheet index paginates onto G-001.n instead of dropping entries."""

from __future__ import annotations

import pytest

from typehaus.emit.draw.cover_sheets import COVER, converge
from typehaus.emit.draw.schedules.cover_index import (
    INDEX_COLUMN_IN,
    INDEX_PT,
    INDEX_TIGHT_PITCH_IN,
    INDEX_TIGHT_PT,
    expand_numbers,
)
from typehaus.emit.draw.sheet_writer import ARCH_D, LEDGER, set_paper

# Tight lettering, 3 columns of 10 rows on the first page and of 20 on each later one.
_WIDTH = 3.2 * INDEX_COLUMN_IN * INDEX_TIGHT_PT / INDEX_PT
_FIRST, _LATER = 10.5 * INDEX_TIGHT_PITCH_IN, 20.5 * INDEX_TIGHT_PITCH_IN


def _rest(count: int) -> list[tuple[str, str]]:
    return [(f"A-{n:03d}", f"Sheet {n}") for n in range(count)]


def _pages(count: int):
    return converge(_rest(count), first_height_in=_FIRST, later_height_in=_LATER,
                    width_in=_WIDTH)


def test_an_index_that_fits_stays_on_the_cover():
    assert len(_pages(10)) == 1


def test_the_continuation_page_is_itself_an_entry():
    """G-001 holds 30; 30 sheets plus the cover is 31, so G-001.1 exists, and as an entry
    it is the 32nd. Both fit on two pages."""
    pages = _pages(30)
    printed = expand_numbers([e for page in pages for e in page.entries])
    assert len(pages) == 2
    assert printed[:2] == [COVER, f"{COVER}.1"]


def test_a_continuation_that_pushes_the_index_over_a_page_adds_another():
    """Two pages hold 30 + 60 = 90 lines. 88 sheets plus the cover and G-001.1 fills them
    exactly; one more sheet needs G-001.2, which is one more line again."""
    assert len(_pages(88)) == 2
    pages = _pages(89)
    assert len(pages) == 3
    printed = expand_numbers([e for page in pages for e in page.entries])
    assert printed[:3] == [COVER, f"{COVER}.1", f"{COVER}.2"]
    assert len(printed) == 89 + 3


@pytest.mark.parametrize("sets", ["permit", "full"])
@pytest.mark.parametrize("paper", [LEDGER, ARCH_D])
def test_every_emitted_sheet_is_printed_on_the_index(catlin_sheet_index, sets, paper):
    sheets = catlin_sheet_index(sets=sets, paper=paper)
    numbers = [sheet.number for sheet in sheets]
    assert len(numbers) == len(set(numbers))
    cover = [n for n in numbers if n == COVER or n.startswith(f"{COVER}.")]
    assert numbers[:len(cover)] == cover
    assert cover == [COVER, *(f"{COVER}.{i}" for i in range(1, len(cover)))]
    plan = sheets[0].page.keywords["plan"]
    assert len(plan.pages) == len(cover)
    printed = expand_numbers([e for page in plan.pages for e in page.entries])
    assert printed == numbers


def test_ledger_full_set_continues_on_g001_1(catlin_sheet_index, catlin_model_ro, tmp_path):
    """The full set outgrows even the tight, grouped G-001; each spec renders one page."""
    from matplotlib.backends.backend_pdf import PdfPages

    sheets = catlin_sheet_index(sets="full", paper=LEDGER)
    cover = [s for s in sheets if s.number.startswith(COVER)]
    assert [s.number for s in cover][:2] == [COVER, f"{COVER}.1"]
    with PdfPages(tmp_path / "cover.pdf") as pdf, set_paper(LEDGER):
        for spec in cover:
            spec.page(pdf, catlin_model_ro, spec.number, spec.title)
        assert pdf.get_pagecount() == len(cover)
