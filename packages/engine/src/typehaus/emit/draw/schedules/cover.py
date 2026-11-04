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
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from typehaus.checks.soil import site_soil_bearing_psf, site_soil_class
from typehaus.emit.draw.schedules.cover_index import (
    HEADING_GAP_IN,
    INDEX_PITCH_IN,
    INDEX_PT,
    draw_index,
)
from typehaus.emit.draw.sheet_writer import schedule_sheet, section
from typehaus.emit.draw.typography import CHAR_ASPECT, wrap_columns_for
from typehaus.findings import Result
from typehaus.resolve.model import ResolvedModel

if TYPE_CHECKING:  # pragma: no cover — annotations only
    from typehaus.checks.jurisdiction import JurisdictionProfile
    from typehaus.checks.permit import PermitChecklist
    from typehaus.emit.draw.cover_sheets import CoverPlan

#: Narrowest the deferred-submittal statement may print beside the data blocks, inches.
#: Narrower and it stacks under them, as it did before ledger ran out of index rows.
_DEFERRED_MIN_IN = 3.0


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
    if basis == "plat":
        # Dimensions stated off a record, nobody's seal on them. Still a warning row: the
        # reviewer must not scale off it either.
        return ("Survey basis", "PLAT / RECORD DIMENSIONS — NOT A SURVEY", True)
    return ("Survey basis", "PARCEL NOT SURVEYED", True)


@dataclass(frozen=True)
class CoverHeader:
    """The cover's data blocks and where the sheet index starts below them (paper inches)."""
    top: float
    column_2: float
    data_rows: list[tuple[str, str, bool]]
    code_rows: list[tuple[str, str, bool]]
    deferred_x: float | None     # beside the blocks when the paper has the width, else None
    deferred_heading: str
    deferred_lines: list[str]
    index_top: float             # the "SHEET INDEX" heading's baseline


def cover_header(model: ResolvedModel, profile: JurisdictionProfile,
                 box: tuple[float, float, float, float]) -> CoverHeader:
    """Lay out everything above the index. Pure, so the plan and the page agree on its height."""
    x0, _, x1, y1 = box
    top = y1 - 2.70
    column_2 = x0 + min(_DATA_COLUMN_MAX_IN, (x1 - x0) / 2.0)
    data_rows = _project_data_rows(model.plan.project, model.plan.project.site)
    code_rows = [(label, value, False) for label, value
                 in _code_summary_rows(profile, model.plan)]
    cursor = top - 0.42 - max(len(data_rows), len(code_rows)) * INDEX_PITCH_IN
    # Beside the data blocks where the paper has the width: stacked under them it cost
    # ledger's index eight rows, and the index is the one list that must be whole.
    widest = max(len(f"{label:<22}{value}") for label, value, _ in code_rows)
    deferred_x = column_2 + 0.1 + widest * INDEX_PT * CHAR_ASPECT / 72.0 + 0.4
    heading, _, body = " ".join(DEFERRED_SUBMITTALS.split()).partition(" — ")
    if x1 - deferred_x >= _DEFERRED_MIN_IN:
        lines = textwrap.wrap(
            body, wrap_columns_for(min(x1 - deferred_x, _DATA_COLUMN_MAX_IN), INDEX_PT))
        side = top - 0.42 - len(lines) * INDEX_PITCH_IN
        return CoverHeader(top, column_2, data_rows, code_rows, deferred_x, heading, lines,
                           min(cursor, side) - 0.34)
    lines = DEFERRED_SUBMITTALS.splitlines()
    return CoverHeader(top, column_2, data_rows, code_rows, None, heading, lines,
                       cursor - 0.34 - len(lines) * INDEX_PITCH_IN - 0.32)


def footer_height_in(footer: tuple[tuple[str, ...], ...]) -> float:
    """Height the gate statement and certification take above the title strip."""
    return 0.10 + _FOOTER_STEP_IN * (sum(len(p) for p in footer) + 0.4 * len(footer) + 1)


def _write_cover(pdf, model: ResolvedModel, number: str, title: str, *,
                 plan: CoverPlan, page: int, profile: JurisdictionProfile) -> None:
    """G-001 (``page`` 0) or a continuation G-001.n: one page of the planned cover.

    G-001 carries the identity of the set, the code data, the first part of the index and
    the gate statement; a continuation carries index alone. Everything about the layout
    was decided in ``cover_sheets.plan_cover`` -- the checklist is not re-evaluated here --
    so the index this letters is the one the page count was computed from.
    """
    from typehaus.emit.draw.sheet_writer import content_box

    index_page = plan.pages[page]
    with schedule_sheet(pdf, model, number, title, heading="") as fig:
        width, height = fig.get_size_inches()
        x0, y0, x1, y1 = content_box((width, height))

        def _x(inches: float) -> float:
            return inches / width

        def _y(inches: float) -> float:
            return inches / height

        if page:
            section(fig, _x(x0), _y(y1 - 0.35), "SHEET INDEX (CONT.)", fontsize=12)
            draw_index(fig, index_page, x0=x0, x1=x1, top=y1 - 0.35 - HEADING_GAP_IN)
            return
        site = model.plan.project.site
        head = cover_header(model, profile, (x0, y0, x1, y1))
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
        section(fig, _x(x0), _y(head.top), "PROJECT DATA", fontsize=12)
        section(fig, _x(head.column_2), _y(head.top), "CODE SUMMARY", fontsize=12)
        for column_x, entries in ((x0, head.data_rows), (head.column_2, head.code_rows)):
            cursor = head.top - 0.42
            for label, value, warn in entries:
                fig.text(_x(column_x + 0.1), _y(cursor), f"{label:<22}{value}", fontsize=8,
                         family="monospace",
                         color=_PLACEHOLDER_INK if warn else "#1a1a1a",
                         weight="bold" if warn else "normal")
                cursor -= INDEX_PITCH_IN
        if head.deferred_x is not None:
            section(fig, _x(head.deferred_x), _y(head.top), head.deferred_heading,
                    fontsize=12)
            side = head.top - 0.42
            for deferred_line in head.deferred_lines:
                fig.text(_x(head.deferred_x), _y(side), deferred_line, fontsize=8,
                         family="monospace")
                side -= INDEX_PITCH_IN
        else:
            side = head.top - 0.42 - max(len(head.data_rows),
                                         len(head.code_rows)) * INDEX_PITCH_IN - 0.34
            for deferred_line in head.deferred_lines:
                fig.text(_x(x0), _y(side), deferred_line, fontsize=8, family="monospace")
                side -= INDEX_PITCH_IN
        section(fig, _x(x0), _y(head.index_top), "SHEET INDEX", fontsize=12)
        draw_index(fig, index_page, x0=x0, x1=x1, top=head.index_top - HEADING_GAP_IN)
        cursor = y0 + 0.10 + _FOOTER_STEP_IN * sum(len(p) for p in plan.footer)
        for paragraph in plan.footer:
            for footer_line in paragraph:
                fig.text(_x(x0), _y(cursor), footer_line, fontsize=_FOOTER_PT,
                         family="sans-serif")
                cursor -= _FOOTER_STEP_IN
            cursor -= _FOOTER_STEP_IN * 0.4


def _footer_paragraphs(profile, checklist, columns: int,
                       register: str | None = None) -> list[list[str]]:
    """The gate statement, then the jurisdiction's certification sentence — both wrapped.

    Minn. R. 1800.4200 subp. 4, verbatim and once: the ruled NAME / LICENSE NO. / DATE /
    SIGNATURE lines in every certified sheet's title block are the instrument, and this is
    the sentence they refer back to. A profile that states no certification prints none —
    another state's set must never carry Minnesota's.
    """
    paragraphs = [textwrap.wrap(_gate_statement(profile, checklist, register),
                                width=columns)]
    if profile.seal_certification:
        paragraphs.append(textwrap.wrap(
            "PROFESSIONAL CERTIFICATION — " + profile.seal_certification
            + "  Signature, typed or printed name, date and licence number are ruled in "
              "the title block of each sheet the licensee is responsible for.",
            width=columns))
    return paragraphs


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
    # The electrical cycle runs separately from the residential one and can be AHEAD of it,
    # so a reader who takes the profile name as the edition for everything reads the
    # electrical sheets against the wrong code. Omitted where the profile claims nothing.
    if profile.nec_base:
        rows.append(("NEC base", profile.nec_base))
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


def _gate_statement(profile: JurisdictionProfile, checklist: PermitChecklist,
                    register: str | None = None) -> str:
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
    # The register's number comes from the index (it was "S-105" long after S-603 took it).
    where = f" — see {register}" if register else ""
    return _gate_sentence(
        profile, f"PASS. Engineered items sealed by {'; '.join(credits)}{where}")


def _gate_sentence(profile: JurisdictionProfile, verdict: str) -> str:
    """The verdict plus the standing scope disclaimer, in one place.

    "engineering" stays in the disclaimer because the *scope* caveat is still true — this
    engine computes four limit-state families, not a building's whole structural design.
    """
    return (f"Declared {profile.name} checklist: {verdict}. This set encodes a declared "
            "subset only; verify local amendments, engineering, MEP, and energy before "
            "construction.")


