"""G-001 — the cover: project data, the code summary, the sheet index, the gate statement.

Split out of ``architectural.py`` when the project-data block landed. The cover is the one
page in the set that is *about the set*, and it now carries the three things a Saint Paul
DSI intake clerk looks for before opening anything else: what property this is, what code
it was drawn to, and what is still outstanding.

Decision #32 governs the project-data block absolutely. A permit drawing that prints a
plausible-looking address, PIN or legal description the model does not carry is worse than
one that prints nothing — and a parcel ring that came from nowhere must SAY so, in the same
red the issue stamp uses, rather than sit quietly under a "LOT AREA" number.
"""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, Any

from typehaus.checks.soil import site_soil_bearing_psf, site_soil_class
from typehaus.emit.draw.sheet_writer import schedule_sheet, section
from typehaus.emit.draw.typography import wrap_columns_for
from typehaus.findings import Result
from typehaus.resolve.model import ResolvedModel

if TYPE_CHECKING:  # pragma: no cover — annotations only
    from typehaus.checks.jurisdiction import JurisdictionProfile
    from typehaus.checks.permit import PermitChecklist
    from typehaus.checks.registry import Preferences

#: Lettering pitch for the sheet index, inches per row. 8pt monospace on a 0.135" pitch is
#: the density a real index prints at.
_INDEX_PITCH_IN = 0.135

#: Narrowest index column, inches — the width the *column count* is decided against, so that
#: 11x17 still gets five columns rather than three luxurious ones and an overflow note.
_INDEX_COLUMN_IN = 2.95

#: Widest index column, inches. A derived detail's title carries the assembly pair that
#: distinguishes it ("TR-CATLIN-RIM-BAND · EXT_2X6 / ROOF"), which is what a
#: column this wide is for; past it the eye stops associating a number with its title.
_INDEX_COLUMN_MAX_IN = 6.2

#: Clear space between one index column's text and the next column's number, inches.
_INDEX_GUTTER_IN = 0.20

#: Index lettering. The number field is 9 characters plus its separating space, which is
#: where the ``- 10`` in the title's character budget comes from.
_INDEX_PT = 8.0

#: Longest index column worth printing, rows. Nothing but the paper stops a 24x36 cover
#: putting all 98 of catlin's sheets in one 13"-tall column — which fits, and is a worse
#: index than three short ones: the eye tracks a column top-to-bottom, and past about this
#: many rows it is scanning a wall of numbers. Above the cap the list balances across as
#: many columns as the sheet is wide enough to hold.
_INDEX_MAX_ROWS = 48


#: Widest the PROJECT DATA column gets, inches. Past this the label and its value stop
#: reading as a pair on a 24x36 sheet.
_DATA_COLUMN_MAX_IN = 6.6

#: The ink a parcel that came from nowhere is printed in — the same red as the issue stamp,
#: because it says the same kind of thing: this sheet may not be relied on for that.
_PLACEHOLDER_INK = "#8a1c1c"

#: What a project-data field the model does not carry prints as. Never a guess, and never
#: silence: a blank line beside "PIN" reads as a PIN nobody typed, which is exactly what it
#: is, and a reviewer needs to see that it is missing rather than not see the row.
NOT_STATED = "not stated"

#: Footer lettering and its line pitch, inches. The gate statement and the certification are
#: laid out as wrapped lines rather than handed to matplotlib's ``wrap=True``, which wraps to
#: the FIGURE and so ran the draft gate's list of unsealed items off the right edge.
_FOOTER_PT = 8.0
_FOOTER_STEP_IN = 0.145

#: Roof trusses are designed and sealed by the fabricator, so their drawings cannot be in
#: this set and Saint Paul DSI does not ask them to be — it asks that they be listed as a
#: deferred submittal and handed to the inspector on site.
DEFERRED_SUBMITTALS = (
    "DEFERRED SUBMITTALS — ROOF TRUSSES. Truss design drawings are prepared and sealed by\n"
    "the truss fabricator's engineer and are not part of this set. The manufacturer's\n"
    "drawings, including permanent bracing, are to be provided to the building inspector\n"
    "on site before the trusses are set.")


def _project_data_rows(project, site) -> list[tuple[str, str, bool]]:
    """The PROJECT DATA block: ``(label, value, is a warning)``.

    The third element is what makes the parcel row honest. A lot area computed off a
    placeholder ring is a real number about a fictional parcel, and printing it in the same
    ink as the code edition invites a reviewer to scale off it. ``parcel_basis`` therefore
    earns a verdict of its own, in the issue stamp's red until a licensed surveyor's
    document replaces the ring.

    Decision #32 everywhere else: a field the model does not carry prints
    :data:`NOT_STATED`, never a plausible placeholder.
    """
    from typehaus.emit.draw.site_metrics import lot_area_ft2

    def stated(holder, field: str) -> str:
        value = getattr(holder, field, None)
        return str(value) if value else NOT_STATED

    area = lot_area_ft2(site) if site is not None else None
    address = getattr(site, "address", None) or getattr(project, "address", None)
    rows: list[tuple[str, str, bool]] = [
        ("Address", " ".join(str(address).split()) if address else NOT_STATED, False),
        ("Parcel ID (PIN)", stated(site, "pin"), False),
        ("Legal description", stated(site, "legal_description"), False),
        ("Zoning district", stated(site, "zoning_district"), False),
        ("Lot area", f"{area:,.0f} sf" if area else NOT_STATED, False),
        ("Owner", stated(project, "owner"), False),
        ("Project number", stated(project, "number"), False),
        ("Prepared by", stated(project, "preparer"), False),
    ]
    rows.append(_survey_basis_row(site))
    return rows


def _survey_basis_row(site) -> tuple[str, str, bool]:
    """What the parcel geometry on C-101 and the lot area above it actually rest on."""
    basis = getattr(site, "parcel_basis", None)
    if basis == "survey":
        by = getattr(site, "survey_by", None) or NOT_STATED
        when = getattr(site, "survey_date", None)
        return ("Survey basis", f"{by}" + (f", {when}" if when else ""), False)
    if basis == "placeholder":
        return ("Survey basis", "PLACEHOLDER — NOT A SURVEY", True)
    return ("Survey basis", "PARCEL NOT SURVEYED", True)


def _write_cover(pdf, model: ResolvedModel, index: list[tuple[str, str]],
                 profile: JurisdictionProfile,
                 preferences: Preferences | None = None) -> None:
    """A-000 — the identity of the set, the code data behind it, and the sheet index.

    The checklist is evaluated with the actual ``preferences`` (from the set writer): without
    them ``[envelope].ach50`` is unreadable and the air-leakage item reads UNKNOWN even on a
    house that passes it, and ``haus print`` gates on that same evaluation being clean.

    The index layout is in paper inches and takes its row count from :func:`content_box`, so
    the column count follows the paper; if a set ever outgrows even that, the overflow is
    *stated on the sheet* rather than silently clipped.
    """
    from typehaus.checks import evaluate_permit_checklist, run_from_model
    from typehaus.emit.draw.sheet_writer import content_box

    site = model.plan.project.site
    checklist = evaluate_permit_checklist(
        run_from_model(model, [], profile=profile.name, preferences=preferences), profile)
    # G-001, not A-000. The sheet index, the manifest and every cross-reference in the set
    # call this page G-001 (a cover is general information, not architectural); the title
    # block was still lettering the pre-NCS number, so the one page whose job is to be the
    # map disagreed with itself.
    with schedule_sheet(pdf, model, "G-001", "Cover / code summary", heading="") as fig:
        width, height = fig.get_size_inches()
        x0, y0, x1, y1 = content_box((width, height))

        def _x(inches: float) -> float:
            return inches / width

        def _y(inches: float) -> float:
            return inches / height

        fig.text(_x(x0), _y(y1 - 0.55), model.plan.project.name, fontsize=28,
                 family="monospace")
        fig.text(_x(x0), _y(y1 - 1.15), f"{profile.edition.upper()} PERMIT SET",
                 fontsize=13, family="monospace")
        fig.text(_x(x0), _y(y1 - 1.70),
                 f"Site: {site.lat:.5f}, {site.lon:.5f}\n"
                 f"Climate zone 6 · framed model derived from Type:Haus",
                 fontsize=10, family="monospace", va="top")

        # PROJECT DATA and CODE SUMMARY sit side by side: both are short label/value lists
        # and stacking them cost the sheet index a whole column of rows.
        top = y1 - 2.70
        column_2 = x0 + min(_DATA_COLUMN_MAX_IN, (x1 - x0) / 2.0)
        section(fig, _x(x0), _y(top), "PROJECT DATA", fontsize=12)
        section(fig, _x(column_2), _y(top), "CODE SUMMARY", fontsize=12)
        rows = 0
        for column_x, entries in ((x0, _project_data_rows(model.plan.project, site)),
                                  (column_2, [(label, value, False) for label, value
                                              in _code_summary_rows(profile, model.plan)])):
            cursor = top - 0.42
            for label, value, warn in entries:
                fig.text(_x(column_x + 0.1), _y(cursor), f"{label:<22}{value}", fontsize=8,
                         family="monospace",
                         color=_PLACEHOLDER_INK if warn else "#1a1a1a",
                         weight="bold" if warn else "normal")
                cursor -= _INDEX_PITCH_IN
            rows = max(rows, len(entries))

        cursor = top - 0.42 - rows * _INDEX_PITCH_IN - 0.34
        for deferred_line in DEFERRED_SUBMITTALS.splitlines():
            fig.text(_x(x0), _y(cursor), deferred_line, fontsize=8, family="monospace")
            cursor -= _INDEX_PITCH_IN
        cursor -= 0.32
        section(fig, _x(x0), _y(cursor), "SHEET INDEX", fontsize=12)
        cursor -= 0.42
        # The footer is laid out first, in lines, because the index gets whatever height is
        # left above it — a statement that grew (the draft gate now names every unsealed
        # requirement) used to run off the bottom of the sheet and through the title block.
        footer_lines = _footer_paragraphs(profile, checklist, wrap_columns_for(x1 - x0, 9.0))
        footer_in = 0.10 + _FOOTER_STEP_IN * (sum(len(p) for p in footer_lines)
                                              + 0.4 * len(footer_lines) + 1)
        # Rows are whatever fits between here and the statement above the title block; the
        # column count then follows from the sheet count, not from a guess about the paper.
        per_column, columns = _index_shape(
            len(index),
            rows=max(1, int((cursor - (y0 + footer_in)) / _INDEX_PITCH_IN)),
            columns=max(1, int((x1 - x0) / _INDEX_COLUMN_IN)))
        shown, dropped = index[:per_column * columns], index[per_column * columns:]
        # Having settled how many columns there are, spend the leftover width on them. Three
        # columns on 24x36 leave 34.8" to fill, and a title clipped to the 11x17 column
        # width on a sheet with that much room to spare is a clip for no reason.
        pitch_in = min(_INDEX_COLUMN_MAX_IN, (x1 - x0) / columns)
        # The column is the width the entry has, so it is the width the entry is fitted to.
        # Catlin's longest titles ("Framing schedule / bill of materials", "Framing plan —
        # main · FS-SG-PORCH") are wider than one 11x17 column and ran straight through the
        # next column's sheet number — two overlapping strings, both unreadable, on the page
        # that is meant to be the map.
        room = wrap_columns_for(pitch_in - _INDEX_GUTTER_IN, _INDEX_PT) - 10
        for row, (number, name) in enumerate(shown):
            column, line = divmod(row, per_column)
            fig.text(_x(x0 + 0.1 + column * pitch_in),
                     _y(cursor - line * _INDEX_PITCH_IN),
                     f"{number:9} {_fit(name, room)}",
                     fontsize=_INDEX_PT, family="monospace")
        if dropped:
            footer_lines.insert(0, [
                f"Index continues: {len(dropped)} further sheet(s) "
                f"{dropped[0][0]}–{dropped[-1][0]} are in the set and not listed above."])
        cursor = y0 + 0.10 + _FOOTER_STEP_IN * sum(len(p) for p in footer_lines)
        for paragraph in footer_lines:
            for footer_line in paragraph:
                fig.text(_x(x0), _y(cursor), footer_line, fontsize=_FOOTER_PT,
                         family="sans-serif")
                cursor -= _FOOTER_STEP_IN
            cursor -= _FOOTER_STEP_IN * 0.4


def _footer_paragraphs(profile, checklist, columns: int) -> list[list[str]]:
    """The gate statement, then the jurisdiction's certification sentence — both wrapped.

    Minn. R. 1800.4200 subp. 4, verbatim and once: the ruled NAME / LICENSE NO. / DATE /
    SIGNATURE lines in every certified sheet's title block are the instrument, and this is
    the sentence they refer back to. A profile that states no certification prints none —
    another state's set must never carry Minnesota's.
    """
    paragraphs = [textwrap.wrap(_gate_statement(profile, checklist), width=columns)]
    if profile.seal_certification:
        paragraphs.append(textwrap.wrap(
            "PROFESSIONAL CERTIFICATION — " + profile.seal_certification
            + "  Signature, typed or printed name, date and licence number are ruled in "
              "the title block of each sheet the licensee is responsible for.",
            width=columns))
    return paragraphs


def _fit(text: str, room: int) -> str:
    """``text`` clipped to ``room`` characters, ellipsised so the clip is visible.

    A silently truncated title reads as the real title. The ellipsis is the difference
    between "this sheet is called that" and "this sheet's name is longer than the column".
    """
    if room <= 1 or len(text) <= room:
        return text
    return text[:room - 1].rstrip() + "…"


def _index_shape(entries: int, *, rows: int, columns: int) -> tuple[int, int]:
    """(rows per column, columns) for ``entries`` index lines in a ``rows`` x ``columns`` grid.

    Two rules, in order. Cap a column at :data:`_INDEX_MAX_ROWS` so a tall sheet does not
    print one enormous column, then **balance**: having decided three columns are needed,
    print 33/33/32 rather than 48/48/2. An unbalanced index looks like the list was
    truncated and continues somewhere else, which is the exact thing this page must not
    suggest.

    The grid is a hard bound, not a target — a set too big for the paper returns the
    largest whole grid that fits and the caller says on the sheet what did not make it.
    """
    if entries <= 0:
        return (1, 1)
    per_column = min(rows, _INDEX_MAX_ROWS)
    needed = -(-entries // per_column)  # ceil
    columns = max(1, min(needed, columns))
    return (min(rows, -(-entries // columns)), columns)


def _code_summary_rows(profile: JurisdictionProfile, plan: Any = None) -> list[tuple[str, str]]:
    """The profile's own data, which A-000 has claimed to summarise since it was written.

    Every value here is authored on :class:`JurisdictionProfile` and was already deciding
    findings; none of it reached paper. A reviewer reading "42\" MIN BELOW THE LOWEST
    ADJACENT FINISHED GRADE" on S-100 could not see, anywhere in the set, which profile
    that 42 came from. A row is omitted rather than printed as "—" when the profile states
    nothing: a blank is a fact about the profile, and inventing a dash for it is not.
    """
    rows = [("Jurisdiction profile", profile.name),
            ("Code edition", profile.edition),
            ("Effective", profile.effective_date),
            ("IRC base", profile.irc_base)]
    if profile.frost_depth_in is not None:
        rows.append(("Frost depth", f"{profile.frost_depth_in:.0f}\" below lowest "
                                    f"adjacent finished grade (IRC R403.1.4.1)"))
    # The site's own soil where it states one, the profile's presumption otherwise, and the
    # row SAYS WHICH — a reviewer reading "GM" needs to know whether that is this parcel's
    # soils report or a regional default (→ checks/soil.py).
    site = getattr(getattr(plan, "project", None), "site", None)
    bearing = site_soil_bearing_psf(plan, profile)
    if bearing is not None:
        basis = ("this site" if getattr(site, "soil_bearing_psf", None) is not None
                 else "presumptive, IRC Table R401.4.1")
        rows.append(("Soil bearing", f"{bearing:.0f} psf ({basis})"))
    soil_class = site_soil_class(plan, profile)
    if soil_class is not None:
        basis = ("this site" if getattr(site, "soil_class", None) is not None
                 else "presumptive")
        rows.append(("Backfill soil class", f"{soil_class} ({basis}, "
                                            f"IRC Table R405.1 / R404.1.2)"))
    gating = sum(1 for item in profile.permit_items if item.blocking)
    rows.append(("Checklist items", f"{gating} gating, "
                                    f"{len(profile.permit_items) - gating} under review"))
    return rows


#: A permit line with nothing left outstanding. N/A belongs here beside PASS: a requirement
#: whose governed condition does not exist in this building is resolved, not unresolved, and
#: lettering "NOT READY" over one would be a false statement on a drawing.
_RESOLVED = frozenset({Result.PASS, Result.NOT_APPLICABLE})


def _gate_statement(profile: JurisdictionProfile, checklist: PermitChecklist) -> str:
    """The verdict line, which now names what is unresolved instead of only that something is.

    "NOT READY" on its own sends a reader back to the CLI to find out why. Since this page
    is also written into the architect handoff — a path that does *not* go through the
    ``haus print`` gate — that branch is reachable with a real set attached to it, and the
    labels are the least it can say.
    """
    unresolved = [item.label for item in checklist.items
                  if item.blocking and item.result not in _RESOLVED]
    if not checklist.ok:
        verdict = "NOT READY — unresolved: " + ", ".join(unresolved)
        return _gate_sentence(profile, verdict)

    stale = checklist.stale_seals
    if stale:
        # A seal that no longer describes the model is worse than no seal: it reads as
        # done. This is the one PASSING checklist that still letters NOT READY.
        names = ", ".join(sorted({tag for item in stale for tag in item.engineering_items}))
        who = next((item.signoff.id for item in stale if item.signoff), "a signoff")
        return _gate_sentence(
            profile, f"NOT READY — engineering seal stale: the model changed after {who} "
                     f"was sealed ({names})")

    engineered = checklist.engineered
    if not engineered:
        return _gate_sentence(profile, "PASS")

    unsealed = checklist.unsealed
    if unsealed:
        # Draft. The set prints, and says out loud what it is: a requirement this engine
        # computed, and no licensed professional has signed — spelled out as a count rather
        # than folded into the generic disclaimer below.
        return _gate_sentence(
            profile,
            f"PASS — DRAFT. {len(unsealed)} requirement(s) NOT SEALED. They rest on "
            f"engineered design computed by this engine and reviewed by no licensed "
            f"professional engineer: " + ", ".join(item.label for item in unsealed))
    credits = sorted({item.signoff.credit() for item in engineered if item.signoff})
    return _gate_sentence(
        profile, f"PASS. Engineered items sealed by {'; '.join(credits)} — see S-105")


def _gate_sentence(profile: JurisdictionProfile, verdict: str) -> str:
    """The verdict plus the standing scope disclaimer, in one place.

    "engineering" stays in the disclaimer because the *scope* caveat is still true — this
    engine computes four limit-state families, not a building's whole structural design.
    """
    return (f"Declared {profile.name} checklist: {verdict}. This set encodes a declared "
            "subset only; verify local amendments, engineering, MEP, and energy before "
            "construction.")


