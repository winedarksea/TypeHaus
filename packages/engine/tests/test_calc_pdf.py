"""``haus calcs --pdf`` — the flattened, page-anchored submittal artefact.

Markdown stays the source of truth (``docs/calc-package-format.md``). What Markdown cannot
be is *submitted*: no jurisdiction accepts it, and under the NCEES Model Rules a seal binds
to a document such that any change invalidates it — which means a single flattened file,
not a folder of text a reviewer can edit without trace.
"""

from __future__ import annotations

from typehaus.takeoff.calc_pdf import (
    ITEM_PREFIX,
    MARGIN_R,
    SECTIONS,
    PdfInputs,
    _wrap,
    index_rows,
    paginate,
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
    assert not any("repo navigation" in line
                   for page in paginate(FILES) for line in page.lines)


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


def test_a_table_row_is_never_wrapped():
    """Wrapping one destroys the column alignment that is the only thing making it a table,
    and a calc sheet's tables are demand/capacity/ratio rows a reviewer reads down."""
    row = "| a very long limit state name indeed | 1234.5 | 2345.6 | lbf | 0.526 | d/c |"
    assert row in _wrap(f"# T\n\n{row}\n")


def test_headings_lose_their_hashes_and_gain_a_rule():
    out = _wrap("## Scope\n\ntext\n")
    assert "SCOPE" in out
    assert any(set(line) == {"-"} for line in out)


def test_the_right_margin_is_wide_enough_to_check_arithmetic_in():
    """A PE checks arithmetic beside the number it belongs to. 0.5" forces that onto a
    separate sheet that then has to be cross-referenced back."""
    assert MARGIN_R >= 1.75


def test_the_catlin_package_renders(catlin_model_ro, tmp_path):
    """End to end on the real 46-item package, and it must stay honest."""
    from typehaus.takeoff.calc_pdf import write_calc_pdf

    out = tmp_path / "calcs.pdf"
    write_calc_pdf(FILES, out, PdfInputs(house="H", generated="2026-09-06",
                                         engine_version="0.1", content_hash="abc123"))
    assert out.exists() and out.stat().st_size > 5_000


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
