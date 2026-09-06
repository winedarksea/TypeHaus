"""The note sanitizer and the ``## Sheet notes`` parser.

Every string in the sanitization table is a real line from a ``houses/catlin/notes/*.md``
file that reached a drawing, so a regression here is a regression on a sheet.
"""

from __future__ import annotations

import pytest

from typehaus.emit.draw import note_text
from typehaus.emit.draw.sheet_notes import (
    MAX_BULLET_CHARS,
    legacy_notes,
    parse_sheet_notes,
    wrapped_line_count,
)


@pytest.mark.parametrize(("raw", "want"), [
    # A house-relative markdown link printed its brackets and its path onto A-402.
    ("(Same pipe — see [basement_to_framed_wall_detail.md](notes/x.md) for the run.)",
     '(Same pipe -- see basement_to_framed_wall_detail.md for the run.)'),
    # A backticked path or pytest id is dropped whole, with the preposition it governed.
    ("and breaks `test_garage_overhead_door_opens_from_the_slab_at_grade`.",
     "and breaks."),
    ("Read `emit/draw/detail_components/sauna.py::ceiling_underside_over` now.",
     "Read now."),
    # A backticked identifier a builder can still use keeps its text.
    ("The `GARAGE_STEM_REVEAL` is the garage storey datum.",
     "The GARAGE_STEM_REVEAL is the garage storey datum."),
    # Emphasis is a footnote marker to a builder.
    ("**BOTH HALVES ARE NOW BUILT** and *neither* is optional.",
     "BOTH HALVES ARE NOW BUILT and neither is optional."),
    # DXF cannot set these.
    ("42″ below grade; ≥ 3,500 psi; 20″×8″ footing — confirm.",
     '42" below grade; >= 3,500 psi; 20"x8" footing -- confirm.'),
    ("show two-tier bench (≈18″ + ≈36″ heights)",
     'show two-tier bench (~18" + ~36" heights)'),
])
def test_sanitizer_table(raw: str, want: str) -> None:
    assert note_text.clean(raw) == want


def test_no_auto_uppercasing() -> None:
    """Uppercasing destroys the units a structural note is made of."""
    assert note_text.clean("2.4 ksi at MC 19%, R-30C over 45 psf/ft") == (
        "2.4 ksi at MC 19%, R-30C over 45 psf/ft")


def test_ascii_only_except_the_bullet() -> None:
    """Both writers indent continuation rows off the bullet, so it is load-bearing."""
    out = note_text.fold_ascii("• café — ½″")
    assert out.startswith("•")
    assert all(ch == "•" or ord(ch) < 128 for ch in out)


def test_hard_wraps_rejoin_into_one_bullet() -> None:
    """The source wraps at column 100; the old loader made each physical line a note."""
    src = [
        "- Interior sauna liner (walls + ceiling): 2\" foil-faced polyiso",
        "  (taped seams). Polyiso is held with 1/2\" plywood furring strips.",
        "",
        "- Wall/ceiling junction: detail as continuous layers.",
    ]
    got = note_text.logical_bullets(src)
    assert len(got) == 2
    assert got[0].endswith("furring strips.")


def test_tables_quotes_and_fences_drop() -> None:
    src = ["| a | b |", "|---|---|", "| 1 | 2 |", "> quoted", "```py", "x = 1", "```",
           "- a real note"]
    assert note_text.logical_bullets(src) == ["a real note"]


def test_banned_words_are_reported_not_rewritten() -> None:
    assert note_text.banned_terms("Fasten as required; workmanlike result") == [
        "as required", "workmanlike"]


SAMPLE = """---
title: "x"
applied_to:
  - detail: y
---

## Sheet notes

### General
- Structural ridge beam; not a rafter-tie roof. Do not omit the LSSR hangers.

### Keyed
- `[K1 @ W-M-N-EXT#layer:sheathing:out]` 5" closed-cell foam to deck underside;
  1-1/2" min first lift.
- [K2 @ W-M-N-EXT] Vented standoff, 1/4"; **do not** lay the sheet on the foam.

### Spec 07 21 00
- Install window bucks before spraying foam. Fillet against block sides.

# Notes

- All the rationale, unchanged, below this line.
"""


def test_parse_splits_three_ways() -> None:
    got = parse_sheet_notes(SAMPLE, source="x.md")
    assert got.problems == ()
    assert got.authored
    assert len(got.general) == 1
    assert [n.key for n in got.keyed] == ["K1", "K2"]
    assert got.keyed[0].anchor_uid == "W-M-N-EXT"
    assert got.keyed[0].anchor_face == "layer:sheathing:out"
    assert got.keyed[1].anchor_face == ""
    assert got.spec[0].spec_section == "07 21 00"


def test_keyed_note_rejoins_and_sanitizes() -> None:
    keyed = parse_sheet_notes(SAMPLE).keyed
    assert keyed[0].text == '5" closed-cell foam to deck underside; 1-1/2" min first lift.'
    assert "**" not in keyed[1].text


def test_specs_never_print_on_the_sheet() -> None:
    """Say it once: a specification belongs on A-002, not in the detail's notes band."""
    lines = parse_sheet_notes(SAMPLE).sheet_lines()
    assert not any("window bucks" in line for line in lines)
    assert any("ridge beam" in line for line in lines)
    assert "KEYED NOTES:" in lines


@pytest.mark.parametrize(("body", "fragment"), [
    ("## Sheet notes\n### Wharrgarbl\n- x\n", "unknown '### Wharrgarbl'"),
    ("## Sheet notes\n- loose note\n### General\n- x\n", "before any"),
    ("## Sheet notes\n### Keyed\n- unkeyed text\n", "no [K#] prefix"),
    ("## Sheet notes\n### Keyed\n- [K1] a\n- [K1] b\n", "duplicate keyed-note key K1"),
    ("## Sheet notes\n### General\n- [K9] a\n", "on a non-keyed note"),
    ("## Sheet notes\n### General\n- Fasten as required.\n", "banned term"),
])
def test_parse_problems_are_never_swallowed(body: str, fragment: str) -> None:
    problems = parse_sheet_notes(body).problems
    assert any(fragment in p for p in problems), problems


def test_over_long_bullet_is_a_problem() -> None:
    long = "x" * (MAX_BULLET_CHARS + 1)
    problems = parse_sheet_notes(f"## Sheet notes\n### General\n- {long}\n").problems
    assert any("max" in p and "chars" in p for p in problems)


def test_legacy_fallback_for_an_unmigrated_file() -> None:
    got = parse_sheet_notes("---\ntitle: x\n---\n\n# Notes\n\n- A note with `a/b.py` in it.")
    assert not got.authored
    assert got.legacy[0] == "NOTES:"
    assert got.legacy[1] == "• A note with in it."


def test_legacy_keeps_the_bullet_marker() -> None:
    assert legacy_notes("# Notes\n- one\n- two")[1:] == ["• one", "• two"]


def test_wrapped_line_count_is_ceiling_division() -> None:
    assert wrapped_line_count(["x" * 43, "x" * 44, "", "y"], columns=43) == 5
