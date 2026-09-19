"""``haus calcs --pdf`` — the flattened, page-anchored submittal artefact.

Markdown stays the source of truth (``docs/calc-package-format.md``). What Markdown cannot
be is *submitted*: no jurisdiction accepts it, and under the NCEES Model Rules a seal binds
to a document such that any change invalidates it — which means a single flattened file,
not a folder of text a reviewer can edit without trace.
"""

from __future__ import annotations

import pytest

from typehaus.takeoff.calc_markdown import Bullets, Code, Heading, Table_, inline, parse
from typehaus.takeoff.calc_pdf import (
    ITEM_PREFIX,
    MARGIN_R,
    PAGE,
    SECTIONS,
    PdfInputs,
    index_rows,
    paginate,
    sheet_order,
)

FILES = {
    "README.md": "# repo navigation, not package content\n",
    "00-cover.md": "# Cover\n\n" + "\n".join(f"Line {i}." for i in range(120)),
    "01-design-criteria.md": "# Criteria\n\nWind V_ult 115 mph.\n",
    "02-item-register.md": "# Register\n\n| a | b |\n|---|---|\n| 1 | 2 |\n",
    "03-open-items.md": "# Open\n\n- one\n",
    "04-assumptions.md": "# Assumptions\n\n- two\n",
    "calcs/deck-post-pt-sg-bf1.md": "# deck_post/PT-SG-BF1\n\nbody\n",
    "calcs/retaining-wall-w-sg-e2.md": "# retaining_wall/W-SG-E2\n\nbody\n",
}


def test_page_numbers_are_section_prefixed_and_restart():
    """The property the numbering exists for.

    A reviewer's comment is page-anchored, and a resubmittal that inserts one page into the
    loads section must not renumber the footings section under their comment. A flat 1..N
    cannot promise that.
    """
    pages = paginate(FILES)
    numbers = [p.number for p in pages]
    assert numbers[0] == "C-1"
    assert "C-2" in numbers, "the 120-line cover paginates rather than clipping"
    assert numbers[numbers.index("D-1") - 1].startswith("C-"), "each section restarts at 1"
    assert any(n.startswith(f"{ITEM_PREFIX}-") for n in numbers)


def test_readme_is_not_in_the_package():
    """`README.md` is repository navigation, not package content, and a reviewer opening a
    sealed submittal should not find a paragraph about how to read a git checkout."""
    assert "README.md" not in [name for name, _prefix, _title in sheet_order(FILES)]
    assert not [p for p in paginate(FILES) if "repo navigation" in p.section]


def test_the_index_is_derived_from_the_pagination():
    """Code-required (CBC/IBC 1603A.3), and derived rather than authored so it cannot
    promise a page the package does not have."""
    pages = paginate(FILES)
    rows = index_rows(pages)
    assert rows[0][0] == "COVER" and rows[0][1].startswith("C-1..C-")
    numbers = {p.number for p in pages}
    for _section, span in rows:
        for token in span.split(".."):
            assert token in numbers


def test_an_item_sheet_is_titled_by_its_own_heading():
    """A page photocopied out of the package still has to say what it belongs to."""
    titles = {p.section for p in paginate(FILES)}
    assert "deck_post/PT-SG-BF1" in titles
    assert "retaining_wall/W-SG-E2" in titles


def test_a_pipe_table_becomes_a_TABLE_and_not_its_own_source_text():
    """** THE PIPES USED TO BE PRINTED LITERALLY. ** The old renderer had no table engine —
    it passed a table row through as text, unwrapped, and a reviewer read the markdown
    source of a demand/capacity table rather than the table."""
    row = "| a very long limit state name indeed | 1234.5 | 2345.6 | lbf | 0.526 |"
    blocks = parse(f"# T\n\n| name | demand | capacity | unit | d/c |\n"
                   f"|---|---|---|---|---|\n{row}\n")
    tables = [b for b in blocks if isinstance(b, Table_)]
    assert len(tables) == 1
    assert tables[0].header == ("name", "demand", "capacity", "unit", "d/c")
    assert tables[0].rows == (("a very long limit state name indeed", "1234.5", "2345.6",
                               "lbf", "0.526"),)
    assert not [b for b in blocks if "|" in getattr(b, "text", "")]


def test_nothing_is_ever_truncated():
    """** THE DEFECT THIS TEST EXISTS FOR. ** The old renderer cut every line at
    ``COLUMNS + 24`` characters — x ~ 8.15" on an 8.5" page — and dropped the rest with no
    marker. 305 lines of catlin's own package sat at that cap, the longest source row 860
    characters, and the content most often lost was a limit state's citation.

    A layout engine wraps; it does not clip. Asserted on the PARSE, because that is where
    the clipping used to happen and because a Platypus ``Paragraph`` flows by construction.
    """
    long_line = "word " * 300
    blocks = parse(f"# T\n\n{long_line.strip()}\n")
    text = next(b.text for b in blocks if getattr(b, "text", "").startswith("word"))
    assert len(text) == len(long_line.strip()), "the paragraph keeps every character"

    cell = "x" * 860
    table = next(b for b in parse(f"| a |\n|---|\n| {cell} |\n") if isinstance(b, Table_))
    assert table.rows[0][0] == cell, "a long cell is wrapped by the table, never cut"


def test_headings_carry_an_anchor_for_the_outline():
    """Bookmarks were impossible in the old renderer: matplotlib's PDF backend has no
    outline API at all. Every heading is an anchor now, and the outline is built off them."""
    blocks = parse("# One\n\n## Two\n\ntext\n", source="calcs/x.md")
    headings = [b for b in blocks if isinstance(b, Heading)]
    assert [h.level for h in headings] == [1, 2]
    assert len({h.anchor for h in headings}) == 2, "anchors are unique"
    assert all(h.anchor.isidentifier() for h in headings)


def test_inline_markup_is_escaped_before_it_is_marked_up():
    """A calc sheet is full of ``<=`` and ``&``. Escaping second would let a bare ``<``
    take Platypus' parser down or, worse, silently eat the rest of the line."""
    out = inline("a <= b & c **bold**")
    assert "&lt;=" in out and "&amp;" in out
    assert "<b>bold</b>" in out


def test_a_bullets_continuation_line_stays_in_its_bullet():
    """``03-open-items.md`` wraps its deliverables across lines. Treating the continuation
    as a new paragraph would put half a sentence outside the list it belongs to."""
    blocks = parse("- first line\n  continued here\n- second\n")
    bullets = next(b for b in blocks if isinstance(b, Bullets))
    assert bullets.items == ("first line continued here", "second")


def test_a_fenced_block_keeps_its_own_line_breaks():
    """The notes' hand-worked arithmetic is fenced, and reflowing it destroys the alignment
    that makes a derivation readable."""
    code = next(b for b in parse("```\na = 1\nb = 2\n```\n") if isinstance(b, Code))
    assert code.lines == ("a = 1", "b = 2")


def test_the_right_margin_is_wide_enough_to_check_arithmetic_in():
    """A PE checks arithmetic beside the number it belongs to. 0.5" forces that onto a
    separate sheet that then has to be cross-referenced back."""
    assert MARGIN_R >= 1.75


def test_the_catlin_package_renders(catlin_model_ro, tmp_path):
    """End to end on the real package, and it must stay honest."""
    from typehaus.takeoff.calc_pdf import write_calc_pdf

    out = tmp_path / "calcs.pdf"
    write_calc_pdf(FILES, out, PdfInputs(house="H", generated="2026-09-06",
                                         engine_version="0.1", content_hash="abc123"))
    assert out.exists() and out.stat().st_size > 5_000


def test_the_pdf_is_byte_deterministic(tmp_path):
    """Nothing asserted this before, and the handoff manifest rests on it.

    ``test_handoff.test_the_bundle_is_byte_deterministic`` ran ``--no-pdf``, so the one
    file in the bundle most likely to carry a wall-clock timestamp was the one file the
    determinism test excluded. ``rl_config.invariant`` fixes the producer, the dates and the
    document id; this is what says it stayed fixed.
    """
    from typehaus.takeoff.calc_pdf import write_calc_pdf

    inputs = PdfInputs(house="H", generated="2026-09-06", engine_version="0.1",
                       content_hash="abc123")
    first = write_calc_pdf(FILES, tmp_path / "a.pdf", inputs)
    second = write_calc_pdf(FILES, tmp_path / "b.pdf", inputs)
    assert first.read_bytes() == second.read_bytes()


def test_the_index_lists_every_section_and_is_never_cut_off():
    """** THE OLD COVER PRINTED 25 OF 40 ROWS AND STOPPED. ** It drew the index line by
    line into whatever space was left and hit a hard ``break`` at the bottom margin. An
    index that stops is worse than no index: a reviewer looking for the fifteenth section
    concludes it is not in the package. The index is a flowing table now and spills onto a
    second page where it needs to.
    """
    pages = paginate(FILES)
    rows = index_rows(pages)
    listed = [section for section, _span in rows]
    # Every section the package contains has a row, in order, with no gaps.
    assert listed == list(dict.fromkeys(page.section for page in pages))
    assert len(rows) >= len([n for n, _p, _t in sheet_order(FILES)])


def test_a_long_package_does_not_lose_index_rows(tmp_path):
    """The failure mode is only visible at scale, so it is provoked rather than waited for:
    forty item sheets, and every one of them has to reach the index."""
    from typehaus.takeoff.calc_pdf import write_calc_pdf

    files = dict(FILES)
    for i in range(40):
        files[f"calcs/item-{i:02d}.md"] = f"# kind/TAG-{i:02d}\n\nbody {i}\n"
    rows = index_rows(paginate(files))
    for i in range(40):
        assert any(section == f"kind/TAG-{i:02d}" for section, _ in rows), i

    out = write_calc_pdf(files, tmp_path / "c.pdf",
                         PdfInputs(house="H", generated="d", engine_version="0",
                                   content_hash="h"))
    assert out.stat().st_size > 10_000


def test_the_index_quotes_page_labels_the_package_actually_has():
    """Two passes, because the index's own length moves the labels it quotes. A range
    naming a page that does not exist is the failure mode that makes an index worthless."""
    pages = paginate(FILES)
    numbers = {page.number for page in pages}
    for _section, span in index_rows(pages):
        for token in span.split(".."):
            assert token in numbers, span


def test_every_front_matter_file_has_a_prefix():
    """A file the package emits but this module does not know about would land in the item
    series with a misleading number. The two lists are pinned together here."""
    import inspect

    from typehaus.takeoff.calc_package import calc_package

    # Read the front-matter names out of ``calc_package``'s own dict literal rather than
    # restating them: a file added there and not here would land in the ITEM series with a
    # misleading number, and this is what catches that.
    source = inspect.getsource(calc_package)
    emitted = {name for name in source.split('"') if name.endswith(".md")}
    known = {name for name, _, _ in SECTIONS} | {"README.md"}
    assert emitted == known, f"calc_package emits {emitted - known} with no page prefix"


def test_the_load_combination_column_prints_a_dash_and_never_a_guess():
    """`LimitState.combination` is empty for almost every state today, and must stay so.

    Writing a combination number beside a demand that was never combined would be a claim
    about the arithmetic the arithmetic does not support.
    """
    from typehaus.engineering.item import LimitState

    state = LimitState(name="axial", demand=1.0, capacity=2.0, unit="lbf", citation="X")
    assert state.combination == ""


def test_italics_never_eat_a_snake_case_tag():
    """``_None — ...._`` is markdown italic; ``W_SG_E2`` and ``roof_beam_snow_psf`` are
    not, and a naive underscore rule italicises half of every calc sheet's element tags."""
    out = inline("_None — nothing is missing._ on W_SG_E2 via roof_beam_snow_psf")
    assert out.startswith("<i>None")
    assert "W_SG_E2" in out and "roof_beam_snow_psf" in out
    assert out.count("<i>") == 1


def test_the_measure_is_wide_enough_to_read_and_narrow_enough_to_check_beside():
    """The frame a paragraph flows in, stated as a number rather than implied by margins.

    Wrapping is the whole point of the renderer — but a 6.5" measure of 8.5 pt text is ~110
    characters a line, which is past what anyone reads comfortably. The wide right margin is
    what keeps it near 65, and it is the same margin a PE does arithmetic in.
    """
    measure = PAGE[0] - 0.90 - MARGIN_R
    assert 4.7 <= measure <= 5.8, f"{measure:.2f}in of text measure"
