"""The general-notes, specification and legend table pages.

The cover is in ``cover.py``, the opening/finish schedules in ``openings.py`` and the two
energy sheets in ``energy.py``; those three names are re-exported here because
``schedules/__init__`` and a handful of tests already import them from this module.
"""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

from typehaus.emit.draw.schedules.blocks import _lay_out_blocks
from typehaus.emit.draw.schedules.cover import (  # noqa: F401 — re-exported
    _code_summary_rows,
    _gate_statement,
    _project_data_rows,
    _write_cover,
)
from typehaus.emit.draw.schedules.energy import (  # noqa: F401 — re-exported
    _write_energy_sheet,
    _write_ventilation_sheet,
)
from typehaus.emit.draw.schedules.openings import (  # noqa: F401 — re-exported
    _write_opening_schedule,
    _write_room_finish_schedule,
)
from typehaus.emit.draw.schedules.tables import _add_table
from typehaus.emit.draw.sheet_writer import schedule_sheet, section
from typehaus.resolve.model import ResolvedModel

if TYPE_CHECKING:  # pragma: no cover — annotations only
    from typehaus.checks.jurisdiction import JurisdictionProfile


def _write_general_notes(pdf, model: ResolvedModel, number: str, name: str,
                         profile: JurisdictionProfile | None = None) -> None:
    """G-002 — the general notes, and an index of where every sheet note is.

    What this replaced silently truncated. It collected the whole of every
    ``Transition.notes`` markdown file — 637 lines on catlin — laid them into four columns
    and ``break``ed out of both loops when it ran out of column, dropping the rest with no
    marker. A permit sheet that drops construction notes and says nothing about it is worse
    than a permit sheet with fewer notes on it.

    Two things fix that, and the first is the one that matters: **the content is bounded by
    construction now.** A fixed list of derived blocks plus one line per notes file cannot
    outgrow the sheet, where a transitions loop over unbounded prose always could. The
    second is that :func:`_lay_out_blocks` reports what it could not fit instead of
    dropping it — a belt for a condition that should no longer arise.

    The note text itself is on the A-5xx details, keyed. Reprinting it here was the
    duplication *say it once* exists to stop; what G-002 owes a reader is a way to FIND it,
    which is the index at the foot of the sheet.
    """
    with schedule_sheet(pdf, model, number, name, heading_xy=(0.03, 0.945)) as fig:
        blocks = _general_note_blocks(model, profile)
        overflow = _lay_out_blocks(fig, blocks)
        if overflow:
            # Never silent. If this ever prints, the fix is to shorten a block, not to
            # widen the tolerance.
            fig.text(0.03, 0.06,
                     f"NOTE: {overflow} block(s) did not fit and are NOT printed on this "
                     f"sheet — see the A-5xx details.", fontsize=7, family="monospace",
                     color="#8a1c1c")


def _general_note_blocks(model: ResolvedModel,
                         profile: JurisdictionProfile | None) -> list[tuple[str, list[str]]]:
    """The five derived blocks, then the sheet-note index. All bounded by construction."""
    edition = profile.edition if profile else "see cover"
    checklist = profile.name if profile else "see cover"
    blocks: list[tuple[str, list[str]]] = [
        ("CODE & JURISDICTION", [
            f"• Code: {edition}; declared checklist {checklist}.",
            "• Verify local amendments with the authority having jurisdiction.",
            "• Climate zone 6. See G-004 for the envelope summary.",
        ]),
        ("DIMENSIONS", [
            "• Written dimensions govern; do not scale the drawings.",
            "• Exterior strings are struck to the sheathing face.",
            "• Openings dimension to centreline.",
            "• Report a discrepancy before proceeding.",
        ]),
        ("SCOPE", [
            "• This set encodes a declared subset only.",
            "• Verify engineering, MEP and energy compliance",
            "  before construction.",
            "• Quantities shown are derived from the model and are",
            "  the contractor's to confirm in the field.",
        ]),
        ("ENVELOPE", _envelope_block(model)),
        ("SUBSTITUTIONS", [
            "• A named product is a performance specification.",
            "• Submit an equal for review before ordering.",
            "• Where a report number is cited, the substitute",
            "  carries an equivalent listing for the same use.",
        ]),
    ]
    index = _sheet_note_index(model)
    if index:
        blocks.append(("SHEET NOTE INDEX", index))
    return blocks


def _envelope_block(model: ResolvedModel) -> list[str]:
    """The envelope assemblies actually used, named once each with their R-value.

    Derived, and bounded by the number of DISTINCT exterior assemblies rather than by the
    number of walls — catlin has five, not 241.
    """
    from typehaus.checks.building_science.energy_load import _assembly_r_value

    seen: dict[str, float | None] = {}
    unknown: list[str] = []
    for wall in model.walls:
        ref = getattr(wall, "assembly", None) or ""
        # "INT" in the tag is how this house takes an interior assembly out of the envelope
        # (→ memory: INT token keeps walls out of the envelope), and it is the same test
        # ``mn_energy`` applies. One rule, not two.
        if not ref or ref in seen or "INT" in ref:
            continue
        with suppress(Exception):
            seen[ref] = _assembly_r_value(model, ref, unknown)
    out = ["• Exterior assemblies in this set:"]
    for ref, r_value in sorted(seen.items())[:8]:
        out.append(f"  {ref}" + (f"  R-{r_value:.0f}" if r_value else ""))
    out.append("• See the A-5xx details for each junction.")
    return out


def _sheet_note_index(model: ResolvedModel) -> list[str]:
    """``note title -> the sheet numbers it prints on``.

    This is what makes G-002 useful without reprinting a word of the notes: a reader who
    knows there is guidance about the eave can find which sheet carries it. One line per
    notes file, so it is bounded by the six files rather than by their 637 lines.
    """
    from typehaus.emit.draw.callouts import detail_sheet_numbers
    from typehaus.emit.draw.details import derive_detail_slices

    sheets = detail_sheet_numbers(model)
    where: dict[str, list[str]] = {}
    for derived in derive_detail_slices(model):
        rel = getattr(derived.transition, "notes", None) if derived.transition else None
        sheet = sheets.get(derived.key)
        if not rel or not sheet:
            continue
        where.setdefault(Path(rel).stem.replace("_", " ").upper(), []).append(sheet)
    out: list[str] = []
    for title, numbers in sorted(where.items()):
        ordered = sorted(set(numbers))
        # A note bound to a whole assembly pattern reaches a dozen sheets; printing all
        # twelve numbers is a wall of text where a range says the same thing.
        shown = (f"{ordered[0]}..{ordered[-1]} ({len(ordered)} sheets)"
                 if len(ordered) > 3 else ", ".join(ordered))
        out.append(f"• {title}")
        out.append(f"  {shown}")
    return out



#: MasterFormat divisions, in order, with the titles a spec sheet prints. Only the
#: divisions this engine's houses actually reach — a full MasterFormat listing on a
#: residential set is a table of contents for a book nobody wrote.
MASTERFORMAT_DIVISIONS = {
    "03": "CONCRETE",
    "04": "MASONRY",
    "05": "METALS",
    "06": "WOOD, PLASTICS AND COMPOSITES",
    "07": "THERMAL AND MOISTURE PROTECTION",
    "08": "OPENINGS",
    "09": "FINISHES",
    "22": "PLUMBING",
    "23": "HEATING, VENTILATING AND AIR CONDITIONING",
    "26": "ELECTRICAL",
    "31": "EARTHWORK",
    "32": "EXTERIOR IMPROVEMENTS",
}


def specification_sections(model: ResolvedModel) -> list[tuple[str, str, list[str]]]:
    """``(section number, division title, requirements)`` from every bound notes file.

    The ``### Spec <section>`` blocks of ``emit/draw/sheet_notes.py``. CSI's split is that
    **drawings carry quantity, location and dimension; specifications carry quality,
    performance and procedure** — "bucks before foam" is not a dimension and printing it on
    six detail sheets is the duplication *say it once* exists to stop. A residential set
    without a project manual has nowhere to put it; this sheet is that somewhere, which is
    what sets like this one actually do.

    Requirements are de-duplicated across files, because two details of the same wall
    legitimately name the same procedure and a reader should meet it once.
    """
    from typehaus.emit.draw.details import derive_detail_slices
    from typehaus.emit.draw.sheet_notes import parse_sheet_notes

    root = model.plan.source_root
    by_section: dict[str, list[str]] = {}
    seen_files: set[str] = set()
    for derived in derive_detail_slices(model):
        rel = getattr(derived.transition, "notes", None) if derived.transition else None
        if not rel or rel in seen_files or not root:
            continue
        seen_files.add(rel)
        path = Path(root) / rel
        if not path.exists():
            continue
        for note in parse_sheet_notes(path.read_text(encoding="utf-8"),
                                      source=path.name).spec:
            bucket = by_section.setdefault(note.spec_section or "01 00 00", [])
            if note.text not in bucket:
                bucket.append(note.text)
    out = []
    for number in sorted(by_section):
        division = MASTERFORMAT_DIVISIONS.get(number[:2], "GENERAL REQUIREMENTS")
        out.append((number, division, by_section[number]))
    return out


def _write_specifications(pdf, model: ResolvedModel, number: str, name: str,
                          disciplines: tuple[str, ...] = ()) -> None:
    """A-002 / S-002 — the specification sheet, MasterFormat-ordered.

    ``disciplines`` filters by leading division so the architectural and structural sheets
    do not print each other's sections: 03 and 05 are structural, everything else is
    architectural. A section that reaches neither list would vanish, so the architectural
    sheet takes the remainder rather than a second allow-list.

    IBC 1603.1 forces one exception to *say it once*: the design loads and criteria stay
    printed on the drawings as well. That is G-004 and S-603's business, not this sheet's.
    """
    sections = [s for s in specification_sections(model)
                if not disciplines or s[0][:2] in disciplines]
    if not disciplines:
        structural = {"03", "05"}
        sections = [s for s in specification_sections(model) if s[0][:2] not in structural]
    with schedule_sheet(pdf, model, number, name, heading_xy=(0.03, 0.945)) as fig:
        blocks = [(f"{num}  {title}", [f"• {line}" for line in lines])
                  for num, title, lines in sections]
        if not blocks:
            fig.text(0.03, 0.90,
                     "No specification content is authored for this discipline.",
                     fontsize=7, family="monospace", va="top")
            return
        overflow = _lay_out_blocks(fig, blocks)
        if overflow:
            fig.text(0.03, 0.06,
                     f"NOTE: {overflow} section(s) did not fit and are NOT printed.",
                     fontsize=7, family="monospace", color="#8a1c1c")


#: Abbreviations this set actually prints, and what each expands to. Kept short and
#: honest — a legend listing forty abbreviations a set never uses trains a reader to skip
#: it, and the one they needed is then in a list they have learned to ignore.
ABBREVIATIONS = (
    ("AFF", "above finished floor"),
    ("ccSPF", "closed-cell spray polyurethane foam"),
    ("CDX", "exterior-glue plywood sheathing"),
    ("CI", "continuous insulation"),
    ("CLG", "ceiling"),
    ("EPS / XPS", "expanded / extruded polystyrene"),
    ("ERV", "energy recovery ventilator"),
    ("FS", "factor of safety"),
    ("ICF", "insulating concrete form"),
    ("KDAT", "kiln-dried after treatment"),
    ("LVL / LSL", "laminated veneer / laminated strand lumber"),
    ("o.c.", "on centre"),
    ("PT", "preservative-treated"),
    ("PVDF", "polyvinylidene fluoride coating"),
    ("R.O.", "rough opening"),
    ("SF / LF / CY", "square foot / lineal foot / cubic yard"),
    ("TJI", "wood I-joist"),
    ("WRB", "water-resistive barrier"),
    ("WSP", "wood structural panel (IRC R602.10.4)"),
)

#: What each symbol on the sheets means. Every row names a real drawn thing — the modules
#: are cited so a reader who wants the geometry can find it, and so a symbol that stops
#: being drawn stops being explained here in the same edit.
SYMBOLS = (
    ("D1, W3 in a bubble", "door / window mark, keyed to A-601 and A-602 (plan_marks.py)"),
    ("K1 in a circle", "keyed note, listed in the notes band on that sheet (keyed_notes.py)"),
    ("Split circle, 2 over A-502",
     "detail callout: detail 2, drawn on sheet A-502 (callouts.py)"),
    ("Heavy red line on S-103", "braced wall line (bracedwallplan.py)"),
    ("Triangle with a level name", "storey datum, on sections and elevations"),
    ("Hatched band in a wall cut", "material, named in that sheet's own legend"),
)

#: The lineweight hierarchy, said once for a reader who is about to trust it. Sourced from
#: ``emit/draw/lineweights.py`` rather than restated, so the sheet cannot drift from the pen.
_WEIGHT_ROWS = (
    ("CUT", "material the cut plane passes through"),
    ("PROFILE", "material seen beyond the cut; anything drawn in elevation"),
    ("LIGHT", "surfaces, hatches, layer boundaries, furniture"),
    ("REFERENCE", "dimensions, leaders, grids, bubbles"),
    ("FAINT", "construction lines, underlay, centrelines"),
)


def _write_symbols_legend(pdf, model: ResolvedModel, number: str, name: str) -> None:
    """G-003 — symbols, abbreviations and the lineweight hierarchy.

    NCS asks for this sheet and the set had none, which means every bubble on it was a
    convention a reader had to already know. The abbreviations are the ones this set prints
    and no more: a legend listing forty a set never uses trains a reader to skip it, and the
    one they needed is then in a list they have learned to ignore.
    """
    from typehaus.emit.draw import lineweights

    with schedule_sheet(pdf, model, number, name, heading_xy=(0.03, 0.945)) as fig:
        section(fig, 0.03, 0.90, "SYMBOLS", fontsize=8, va="top")
        _add_table(fig, [list(row) for row in SYMBOLS], ("Symbol", "Meaning"),
                   bbox=(0.03, 0.62, 0.55, 0.25))

        section(fig, 0.62, 0.90, "LINE WEIGHTS", fontsize=8, va="top")
        weights = [[name_, f"{getattr(lineweights, name_):.2f} mm", meaning]
                   for name_, meaning in _WEIGHT_ROWS]
        _add_table(fig, weights, ("Name", "Width", "What it draws"),
                   bbox=(0.62, 0.62, 0.35, 0.25))

        section(fig, 0.03, 0.57, "ABBREVIATIONS", fontsize=8, va="top")
        half = (len(ABBREVIATIONS) + 1) // 2
        _add_table(fig, [list(row) for row in ABBREVIATIONS[:half]], ("", ""),
                   bbox=(0.03, 0.13, 0.45, 0.41))
        _add_table(fig, [list(row) for row in ABBREVIATIONS[half:]], ("", ""),
                   bbox=(0.52, 0.13, 0.45, 0.41))
