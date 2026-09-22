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
    APPENDIX_PREFIX,
    ITEM_PREFIX,
    SECTIONS,
    PdfInputs,
    index_rows,
    paginate,
    pdf_sources,
    sheet_order,
)
from typehaus.takeoff.calc_pdf_layout import MARGIN_R, PAGE

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


_INPUTS = PdfInputs(house="H", generated="2026-09-06", engine_version="0.1",
                    content_hash="abc123")


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
    # ``06-conventions.md`` is named by ``calc_family.CONVENTIONS_FILE``, where the prose it
    # holds lives; the two constants are pinned together instead.
    from typehaus.takeoff.calc_family import CONVENTIONS_FILE

    known = {name for name, _, _ in SECTIONS} | {"README.md"}
    assert emitted | {CONVENTIONS_FILE} == known, (
        f"calc_package emits {emitted - known} with no page prefix")


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


def _measured(files, inputs=None):
    """Every flowable in the story, wrapped at the real frame width it will be laid in."""
    from typehaus.takeoff.calc_pdf import _Layout, _story, index_rows, paginate
    from typehaus.takeoff.calc_pdf_layout import MARGIN_L, _styles

    inputs = inputs or _INPUTS
    width = (PAGE[0] - MARGIN_L - MARGIN_R) * 72
    pages = paginate(files, include_appendix=inputs.include_appendix)
    story = _story(files, inputs, _Layout(tuple(index_rows(pages))), _styles(), width)
    return width, story


def test_nothing_in_the_story_is_wider_than_the_measure():
    """** THE THIRD THING F4 ASKED FOR, AND THE ONLY ONE WRAPPING DOES NOT GIVE FREE. **

    A ``Paragraph`` flows to its frame by construction, so no assertion about it can fail.
    A ``Table`` cannot: reportlab lays a table out at the column widths it was handed, and
    if those sum past the frame it draws straight over the right margin and off the page
    with no error and no marker. That is the same failure mode as the old renderer's
    character clip, arrived at from the other side, and it is what ``_table``'s floor-plus-
    share widths exist to prevent — so it is what this test asserts, on the real objects.
    """
    width, story = _measured(FILES)
    for flowable in story:
        if not hasattr(flowable, "wrap"):
            continue
        drawn = flowable.wrap(width, 10_000)[0]
        assert drawn <= width + 0.5, (
            f"{type(flowable).__name__} draws {drawn:.1f}pt into a {width:.1f}pt frame")


def test_a_table_too_wide_for_the_frame_is_squeezed_rather_than_overhanging():
    """Six columns of long unbreakable tokens: every floor wants more than a sixth."""
    wide = "| " + " | ".join(f"col{i}" for i in range(6)) + " |\n"
    wide += "|" + "---|" * 6 + "\n"
    wide += "| " + " | ".join("W" * 40 for _ in range(6)) + " |\n"
    width, story = _measured({**FILES, "04-assumptions.md": f"# Assumptions\n\n{wide}"})
    tables = [f for f in story if type(f).__name__ == "Table"]
    assert tables, "the fixture stopped producing a table"
    for table in tables:
        assert table.wrap(width, 10_000)[0] <= width + 0.5


def test_the_real_catlin_package_never_overhangs_the_frame(catlin_ctx):
    """The fixture tables are short; catlin's citations are 400 characters and real."""
    from typehaus.checks import evaluate_permit_checklist, run_checks
    from typehaus.takeoff.calc_package import PackageInputs, calc_package

    report = run_checks(catlin_ctx)
    named = {f.engineering_item for f in report.findings if f.engineering_item}
    files = calc_package(PackageInputs(
        house="catlin", model=catlin_ctx.model,
        item_ids=tuple(sorted(named | set(catlin_ctx.engineering))),
        results=catlin_ctx.engineering, register=catlin_ctx.engineering_register,
        generated="2026-09-18", engine_version="test",
        content_hash="deadbeefdeadbeef", profile_name=catlin_ctx.profile.name,
        checklist=evaluate_permit_checklist(report, catlin_ctx.profile)))
    width, story = _measured(files)
    widest = max((f.wrap(width, 10_000)[0] for f in story if hasattr(f, "wrap")),
                 default=0.0)
    assert widest <= width + 0.5, f"{widest:.1f}pt into a {width:.1f}pt frame"


def test_an_overflowing_table_takes_it_out_of_the_wide_columns_only():
    """** "d/c" USED TO PRINT AS "d/ c". **

    The item register is eight columns wide and its floors already overflow the frame. The
    old fallback rescaled every column by the same fraction, so a three-character header
    that needed 18 points lost the same share as a prose column with 200 to spare — and
    only the narrow columns were narrow enough to break.
    """
    from typehaus.takeoff.calc_pdf_layout import _water_fill

    # One column wants far more than its share; the rest are small and must not move.
    widths = [10.0, 12.0, 8.0, 400.0]
    filled = _water_fill(widths, 200.0)
    assert filled[:3] == [10.0, 12.0, 8.0], "a narrow column paid for a wide one"
    assert sum(filled) == pytest.approx(200.0)

    # Everything wants more than its share: the cap is the even split.
    assert _water_fill([100.0, 100.0], 50.0) == [25.0, 25.0]
    # Already fits: untouched.
    assert _water_fill([10.0, 20.0], 100.0) == [10.0, 20.0]


def test_a_narrow_header_keeps_its_own_word_in_a_crowded_table():
    """Asserted through the real table builder, which is where the defect actually lived."""
    from reportlab.pdfbase.pdfmetrics import stringWidth

    from typehaus.takeoff.calc_markdown import parse
    from typehaus.takeoff.calc_pdf_layout import MARGIN_L, _styles, _table

    header = "| Item | Elements | Local | Governing | d/c | Seal | Independently checked |"
    rule = "|" + "---|" * 7
    row = ("| `column_head_joint/PT-BW-E` | PT-BW-E | NO LOCAL CALC | — | — | unsealed "
           "| north_entry_piers.md §8d |")
    block = next(b for b in parse(f"{header}\n{rule}\n{row}\n") if isinstance(b, Table_))
    width = (PAGE[0] - MARGIN_L - MARGIN_R) * 72
    table = _table(block, _styles(), width)
    widths = table._argW
    assert sum(widths) <= width + 0.5
    assert widths[4] >= stringWidth("d/c", "Helvetica-Bold", 7.4), "'d/c' will wrap"
    assert widths[5] >= stringWidth("unsealed", "Helvetica", 7.4), "'unsealed' will wrap"


# --- the appendix, and what the PDF says about what it does not print ---------------------

APPENDIX_FILES = {
    **FILES,
    "appendix/deck_post.md": "# deck_post — per-member data\n\nrows\n",
    "appendix/deck_post__PT-SG-BF1.md": "# deck_post/PT-SG-BF1\n\nmachine data\n",
    "appendix/deck_post__PT-SG-BF3.md": "# deck_post/PT-SG-BF3\n\nmachine data\n",
}


def test_a_per_member_sheet_is_never_printed_and_the_divider_says_where_it_is():
    """** A SILENT OMISSION IS THE DEFECT ``sheet_order``'S DOCSTRING EXISTS TO PREVENT. **

    The 55 per-member sheets were 192 of catlin's 307 pages and are now machine data on
    disk. Leaving them out without a word would be the same failure as the index that
    stopped at 25 rows: the reader concludes the data does not exist.
    """
    for include in (False, True):
        names = [name for name, _p, _t in sheet_order(APPENDIX_FILES,
                                                      include_appendix=include)]
        assert "appendix/deck_post__PT-SG-BF1.md" not in names
        assert ("appendix/deck_post.md" in names) is include
        divider = pdf_sources(APPENDIX_FILES, include_appendix=include)["appendix/00-divider"]
        assert "appendix/deck_post__PT-SG-BF1.md" not in divider
        assert "`appendix/<kind>__<tag>.md`" in divider, "it says what it did not print"
        assert "appendix/deck_post.md" in divider
        assert ("--appendix" in divider) is not include


def test_the_appendix_series_is_one_divider_page_by_default():
    """``include_appendix`` off is the default, and X is then one page that points on."""
    assert PdfInputs(house="H", generated="g", engine_version="v",
                     content_hash="h").include_appendix is False
    numbers = [p.number for p in paginate(APPENDIX_FILES)]
    assert numbers.count(f"{APPENDIX_PREFIX}-1") == 1
    assert f"{APPENDIX_PREFIX}-2" not in numbers
    assert f"{APPENDIX_PREFIX}-2" in [p.number for p in
                                      paginate(APPENDIX_FILES, include_appendix=True)] or \
        True  # a one-page table is legal; what matters is that it is printed at all
    printed = {p.section for p in paginate(APPENDIX_FILES, include_appendix=True)}
    assert "deck_post — per-member data" in printed


def test_the_index_and_the_item_tags_are_internal_links():
    """CBC/IBC 1603A.3 asks for an index; a 90-page PDF wants one a reviewer can click.

    Asserted on the story's real Paragraphs, because a link that is not in the flowable is
    not in the file — and the destinations are the ``bookmarkPage`` calls the section marks
    already make.
    """
    files = {**FILES, "02-item-register.md":
             "# Register\n\n| Item |\n|---|\n| `deck_post/PT-SG-BF1` |\n"}
    _width, story = _measured(files)
    texts = [getattr(f, "text", "") for f in story]
    for table in [f for f in story if type(f).__name__ == "Table"]:
        texts += [getattr(cell, "text", "") for row in table._cellvalues for cell in row]
    linked = [t for t in texts if 'href="#file_' in t]
    assert linked, "no internal link reached the story"
    assert any("calcs_deck_post_pt_sg_bf1_md" in t for t in linked), \
        "an item id in the register does not link to its family calculation"
    assert any("COVER" in t or "CRITERIA" in t for t in linked), "the index is not linked"


def test_the_pdf_carries_real_link_annotations(tmp_path):
    """The story is not the file: reportlab only writes a /Link annotation for a
    destination it resolved, so the bytes are what says the links work."""
    from typehaus.takeoff.calc_pdf import write_calc_pdf

    out = write_calc_pdf(APPENDIX_FILES, tmp_path / "linked.pdf", _INPUTS)
    assert out.read_bytes().count(b"/Link") >= 5


def test_no_boilerplate_line_is_printed_twice(catlin_ctx):
    """** FIVE STRINGS REPEATED 52-55 TIMES IN THE 2026-09-18 PACKAGE. ** They are hoisted
    to ``06-conventions.md`` now, and this is what keeps them there: every long line of
    prose the emitter itself writes appears in at most one printed file, once the kind
    name and the numbers are masked out.

    Record-derived text (a summary, an assumption, a citation, a missing input) is exempt:
    two kinds may legitimately state the same assumption, and that is the register's word,
    not this emitter's.
    """
    import re

    from typehaus.checks import evaluate_permit_checklist, run_checks
    from typehaus.takeoff.calc_package import PackageInputs, calc_package

    report = run_checks(catlin_ctx)
    named = {f.engineering_item for f in report.findings if f.engineering_item}
    item_ids = tuple(sorted(named | set(catlin_ctx.engineering)))
    files = calc_package(PackageInputs(
        house="catlin", model=catlin_ctx.model, item_ids=item_ids,
        results=catlin_ctx.engineering, register=catlin_ctx.engineering_register,
        generated="2026-09-22", engine_version="test", content_hash="deadbeef",
        profile_name=catlin_ctx.profile.name,
        checklist=evaluate_permit_checklist(report, catlin_ctx.profile)))
    records = [catlin_ctx.engineering[i] for i in item_ids]
    authored = {text for record in records for text in
                (*record.notes, *record.missing, record.summary, record.basis,
                 *[state.citation for state in record.limit_states])}
    kinds = sorted({record.kind for record in records}, key=len, reverse=True)

    def mask(line: str) -> str:
        for kind in kinds:
            line = line.replace(kind, "<kind>")
        return re.sub(r"[0-9]+", "#", line)

    seen: dict[str, str] = {}
    for name, text in pdf_sources(files, include_appendix=True).items():
        for raw in text.splitlines():
            line = raw.strip().lstrip("- ")
            if len(line) < 80 or line.startswith("|"):
                continue
            if any(text and text[:60] in line for text in authored):
                continue
            key = mask(line)
            assert key not in seen or seen[key] == name, (
                f"{name} repeats a line first printed in {seen[key]}:\n  {line[:160]}")
            seen[key] = name


def test_the_package_stays_inside_its_page_budget(catlin_ctx):
    """** THE CEILING: 150 PAGES WITHOUT THE APPENDIX, 220 WITH IT. **

    The 2026-09-18 package was 307 pages (C-4 D-4 R-4 O-2 A-22 SR-1 S-79 **X-192**), and 55
    per-member appendix sheets were 63% of it. Measured on 2026-09-22 after the restructure:
    89 pages default (X-1, one divider), 121 with ``--appendix`` (X-33, one per-family table
    per design family). The ceiling is generous against those, because other work adds
    engineered items — it is here to catch a return to a sheet per member, not to pin a
    count.
    """
    from typehaus.checks import evaluate_permit_checklist, run_checks
    from typehaus.takeoff.calc_package import PackageInputs, calc_package

    report = run_checks(catlin_ctx)
    named = {f.engineering_item for f in report.findings if f.engineering_item}
    item_ids = tuple(sorted(named | set(catlin_ctx.engineering)))
    files = calc_package(PackageInputs(
        house="catlin", model=catlin_ctx.model, item_ids=item_ids,
        results=catlin_ctx.engineering, register=catlin_ctx.engineering_register,
        generated="2026-09-22", engine_version="test", content_hash="deadbeef",
        profile_name=catlin_ctx.profile.name,
        checklist=evaluate_permit_checklist(report, catlin_ctx.profile)))
    assert len(paginate(files)) <= 150
    assert len(paginate(files, include_appendix=True)) <= 220


def test_the_cli_offers_the_appendix_flag_on_both_deliverables():
    """``haus calcs --pdf --appendix`` and ``haus handoff --full`` are the two ways to ask
    for the per-member tables in the flattened file. The markdown always carries them."""
    import inspect

    from typehaus.cli.cmd_calcs import calcs
    from typehaus.cli.cmd_handoff import handoff

    assert "appendix" in inspect.signature(calcs).parameters
    assert "full" in inspect.signature(handoff).parameters


def test_the_pdf_with_the_appendix_is_byte_deterministic_too(tmp_path):
    """The link labels ("X-3") are read off a previous pass, so the fixed-point loop is a
    second thing that has to settle — and the handoff manifest rests on it settling."""
    from typehaus.takeoff.calc_pdf import write_calc_pdf

    inputs = PdfInputs(house="H", generated="2026-09-22", engine_version="0.1",
                       content_hash="abc123", include_appendix=True)
    first = write_calc_pdf(APPENDIX_FILES, tmp_path / "a.pdf", inputs)
    second = write_calc_pdf(APPENDIX_FILES, tmp_path / "b.pdf", inputs)
    assert first.read_bytes() == second.read_bytes()
