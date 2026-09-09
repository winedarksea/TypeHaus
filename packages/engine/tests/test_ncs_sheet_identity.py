"""Sheet identity under the National CAD Standard (→ 30 §Sheets).

A sheet number is not a label. NCS makes it a *statement*: the letter is the discipline,
the second digit is the drawing TYPE, and a reviewer who has seen one set can find the
window schedule in another without opening it. This set used to say four things that were
not true — the cover was architectural, the details were large-scale views, the structural
schedules were plans, and the energy sheet had a discipline designator that does not exist.
"""

from __future__ import annotations

import re

from typehaus.emit.draw.sheets import build_sheet_index

#: Every sheet number in a conforming set. ``A-301.1`` is the authored-section variant and
#: is deliberately admitted — a decimal suffix is how NCS numbers a sheet inserted into an
#: existing sequence.
_NUMBER = re.compile(r"^[A-Z]{1,2}-[0-9]{3}(\.[0-9]+)?$")

#: Which type digit each series is allowed to use, and what the digit means.
_TYPE_MEANING = {
    "0": "general", "1": "plans", "2": "elevations", "3": "sections",
    "4": "large-scale views", "5": "details", "6": "schedules",
    "7": "user-defined", "8": "user-defined", "9": "3D",
}

#: NCS discipline order. A set that emits E before A is not wrong sheet by sheet and is
#: unreadable as a pile.
_DISCIPLINE_ORDER = ["G", "C", "S", "A", "P", "M", "E"]


def _numbers(model):
    return [sheet.number for sheet in build_sheet_index(model)]


def test_every_sheet_number_is_well_formed(catlin_model_ro):
    bad = [n for n in _numbers(catlin_model_ro) if not _NUMBER.match(n)]
    assert not bad, f"not NCS sheet numbers: {bad}"


def test_the_type_digit_agrees_with_the_content(catlin_model_ro):
    """The digit is the claim; this is the claim being checked against the sheet."""
    expect = {
        # cover, notes, symbols legend, energy — all general information
        "G-001": "0", "G-002": "0", "G-003": "0", "G-004": "0",
        "S-001": "0",                                # general structural notes
        "C-101": "1", "S-100": "1",                  # site and foundation are plans
        "A-201": "2", "A-202": "2", "A-203": "2", "A-204": "2",
        "A-301": "3",
        "A-601": "6", "A-602": "6", "A-603": "6",
        "S-601": "6", "S-602": "6", "S-603": "6",
        "E-601": "6", "E-602": "6",
    }
    numbers = set(_numbers(catlin_model_ro))
    for number, digit in expect.items():
        assert number in numbers, f"{number} ({_TYPE_MEANING[digit]}) is not in the set"
        assert number[2] == digit


def test_details_are_the_five_series_not_the_four(catlin_model_ro):
    """Type 4 is a large-scale VIEW — an enlarged plan. A junction cut is type 5."""
    numbers = _numbers(catlin_model_ro)
    assert any(n.startswith("A-5") for n in numbers)
    assert not [n for n in numbers if n.startswith("A-4")], \
        "this set has no large-scale views, so the 4 series must be empty"


def test_elevations_come_before_sections(catlin_model_ro):
    numbers = _numbers(catlin_model_ro)
    assert numbers.index("A-201") < numbers.index("A-301")


def test_disciplines_are_emitted_in_order(catlin_model_ro):
    """G, C, S, A, P, M, E — each discipline contiguous and in NCS order."""
    seen: list[str] = []
    for number in _numbers(catlin_model_ro):
        letter = number.split("-")[0]
        if not seen or seen[-1] != letter:
            assert letter not in seen, f"{letter} sheets are not contiguous"
            seen.append(letter)
    assert seen == [d for d in _DISCIPLINE_ORDER if d in seen]


def test_the_three_schedules_are_three_sheets(catlin_model_ro):
    """Doors, windows and room finishes have three readers and three sheets."""
    titles = {s.number: s.title for s in build_sheet_index(catlin_model_ro)}
    assert titles["A-601"] == "Door schedule"
    assert titles["A-602"] == "Window schedule"
    assert titles["A-603"] == "Room finish schedule"


def test_the_symbols_legend_explains_what_the_set_draws(catlin_model_ro):
    """NCS asks for G-003 and the set had none, which made every bubble on it a convention
    a reader had to already know."""
    from typehaus.emit.draw.schedules.architectural import ABBREVIATIONS, SYMBOLS

    titles = {s.number: s.title for s in build_sheet_index(catlin_model_ro)}
    assert "Symbols" in titles["G-003"]
    drawn = " ".join(meaning for _symbol, meaning in SYMBOLS)
    for expected in ("keyed note", "detail callout", "braced wall line"):
        assert expected in drawn, f"G-003 does not explain the {expected}"
    keys = [key for key, _ in ABBREVIATIONS]
    assert keys == sorted(keys, key=str.casefold)


def test_no_sheet_number_is_used_twice(catlin_model_ro):
    numbers = _numbers(catlin_model_ro)
    assert len(numbers) == len(set(numbers))


def test_s002_is_gone_and_s001_replaces_it(catlin_model_ro):
    """The spec sheet's gate was "any section exists", so it vanished on a bare house.

    S-001 is unconditional and carries divisions 03/05 as one of its six blocks.
    """
    numbers = _numbers(catlin_model_ro)
    assert "S-002" not in numbers
    assert numbers.index("S-001") < numbers.index("S-100")


def test_sheet_numbers_ascend_within_a_discipline(catlin_model_ro):
    """NCS numbering is only navigable if the pile is in it.

    The braced-wall loop used to run before the roof-framing loop, so the set emitted
    every S-103.n and *then* the S-102.n behind them. Every existing test checked the
    discipline letter and none checked the number, so the set read out of order for a
    reviewer flipping through it and nothing said so.
    """
    for letter in _DISCIPLINE_ORDER:
        series = [n for n in _numbers(catlin_model_ro) if n.startswith(f"{letter}-")]
        keys = [tuple(int(part) for part in n.split("-")[1].split(".")) for n in series]
        assert keys == sorted(keys), f"{letter} sheets are out of order: {series}"
