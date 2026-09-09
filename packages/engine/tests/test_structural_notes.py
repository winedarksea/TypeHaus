"""S-001 — general structural notes (→ 30 §Sheets).

The sheet replaces S-002, whose gate was "any specification section exists". On catlin
that printed one bullet; on a house with nothing authored it printed no sheet at all —
precisely the house that most needs one saying what is and is not known. So the first
thing these tests assert is that it is unconditional.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pytest

from typehaus.checks.code.mn_residential.profile import get_profile
from typehaus.emit.draw.schedules.structural_notes import (
    NOT_STATED,
    _write_structural_notes,
    anchorage_block,
    concrete_block,
    design_criteria_block,
    limits_block,
    structural_specification_block,
    wood_framing_block,
)
from typehaus.emit.draw.sheets import build_sheet_index


@pytest.fixture(scope="module")
def profile():
    return get_profile("mn-2024")


def test_s001_is_in_the_set_unconditionally(catlin_model_ro):
    sheets = {s.number: s.title for s in build_sheet_index(catlin_model_ro)}
    assert sheets["S-001"] == "General structural notes"


def test_the_starter_house_gets_the_sheet_too(starter_dir):
    """The gate S-002 had is the bug: a bare house needs the sheet MORE, not less."""
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    model, _ = resolve(load_plan(starter_dir).plan)
    assert "S-001" in {s.number for s in build_sheet_index(model)}


def test_every_block_renders_and_none_is_empty(catlin_model_ro, profile):
    blocks = {
        "criteria": design_criteria_block(catlin_model_ro, profile),
        "concrete": concrete_block(catlin_model_ro),
        "framing": wood_framing_block(catlin_model_ro),
        "anchorage": anchorage_block(catlin_model_ro),
        "specs": structural_specification_block(catlin_model_ro),
        "limits": limits_block(catlin_model_ro, None),
    }
    for name, lines in blocks.items():
        assert lines, f"{name} block is empty"


def test_the_criteria_block_prints_the_wind_basis_the_calcs_used(catlin_model_ro, profile):
    """Through ``wind.wind_basis``, not off the site directly.

    A speed with no exposure produces no pressure and no calc reads it; a sheet that
    printed the half-authored speed would print a number nothing used.
    """
    text = "\n".join(design_criteria_block(catlin_model_ro, profile))
    assert "115 mph" in text and "EXPOSURE B" in text and "RISK CATEGORY II" in text
    assert "50.0 psf" in text, "the ground snow load"
    assert "42.0 in" in text, "the profile's frost depth"


def test_a_silent_model_prints_not_stated_and_never_a_default(catlin_model, profile):
    """Decision #32. A missing value is a missing value, not zero and not a guess."""
    site = catlin_model.plan.project.site
    bare = site.model_copy(update={"ground_snow_load_psf": None,
                                   "design_wind_speed_mph": None})
    project = catlin_model.plan.project.model_copy(update={"site": bare})
    plan = catlin_model.plan.model_copy(update={"project": project})
    stripped = catlin_model.model_copy(update={"plan": plan})
    rows = design_criteria_block(stripped, profile)
    snow = next(line for line in rows if line.startswith("GROUND SNOW LOAD"))
    wind = next(line for line in rows if line.startswith("DESIGN WIND"))
    assert NOT_STATED in snow and "0" not in snow.split()[-1]
    assert NOT_STATED in wind


def test_the_concrete_block_groups_on_the_mix_not_the_assembly(catlin_model_ro):
    """Nineteen concrete assemblies, four mixes. A note that repeats one mix nineteen
    times is a note a reader stops reading at the third repeat."""
    lines = concrete_block(catlin_model_ro)
    mixes = [line for line in lines if line.startswith("MIX C")]
    assert 1 <= len(mixes) < 10
    assert any("5,000 psi" in line for line in mixes)
    assert any("hdg-a767" in line for line in lines), "the house's bar coating"


def test_the_framing_block_admits_that_species_and_grade_are_not_modelled(catlin_model_ro):
    text = "\n".join(wood_framing_block(catlin_model_ro))
    assert "SPECIES AND GRADE ARE NOT MODELLED" in text
    assert "out/calcs/" in text
    assert "DEFERRED SUBMITTAL" in text, "trusses are a deferred submittal"


def test_the_anchorage_block_states_the_rule_and_leaves_the_parts_on_s602(catlin_model_ro):
    lines = anchorage_block(catlin_model_ro)
    assert any("MUDSILL ANCHOR" in line for line in lines)
    assert lines[-1] == "PARTS, PART NUMBERS AND COUNTS: SEE S-602."


def test_divisions_03_and_05_are_on_s001_and_not_on_a002(catlin_model_ro):
    """Say it once. A-002 takes the remainder rather than a second allow-list, so the
    two sheets still partition the sections between them."""
    from typehaus.emit.draw.schedules.architectural import specification_sections

    on_s001 = structural_specification_block(catlin_model_ro)
    numbers = {number for number, _title, _lines in specification_sections(catlin_model_ro)}
    structural = {n for n in numbers if n[:2] in ("03", "05")}
    assert structural, "catlin authors at least one 03/05 section"
    for number in structural:
        assert any(line.startswith(number) for line in on_s001)


def test_every_line_fits_the_column_it_is_laid_into(catlin_model_ro, profile):
    """``_lay_out_blocks`` does not wrap — a long line runs into the next column."""
    from typehaus.emit.draw.schedules.structural_notes import _MAX_LINE_CHARS, _clip

    everything = (design_criteria_block(catlin_model_ro, profile)
                  + concrete_block(catlin_model_ro)
                  + wood_framing_block(catlin_model_ro)
                  + anchorage_block(catlin_model_ro)
                  + structural_specification_block(catlin_model_ro)
                  + limits_block(catlin_model_ro, None))
    assert all(len(_clip(line)) <= _MAX_LINE_CHARS for line in everything)


def test_the_sheet_composes_with_nothing_dropped(catlin_model_ro, profile, tmp_path):
    from matplotlib.backends.backend_pdf import PdfPages

    out = tmp_path / "s001.pdf"
    with PdfPages(out) as pdf:
        _write_structural_notes(pdf, catlin_model_ro, "S-001", "General structural notes",
                                profile=profile)
    assert out.stat().st_size > 0
    plt.close("all")
