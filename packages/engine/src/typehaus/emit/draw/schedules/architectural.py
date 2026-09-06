"""The A-series and EN-1 table pages: cover, general notes, openings, energy summary."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any

from typehaus.checks.soil import site_soil_bearing_psf, site_soil_class
from typehaus.emit.draw.schedules.tables import _add_table
from typehaus.emit.draw.sheet_writer import schedule_sheet, section
from typehaus.emit.draw.typography import wrap_columns_for
from typehaus.findings import Result
from typehaus.quantities import M_PER_IN
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
#: distinguishes it ("TR-CATLIN-RIM-BAND · CATLIN_EXT_2X6 / CATLIN_ROOF"), which is what a
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
    with schedule_sheet(pdf, model, "A-000", "Cover / code summary", heading="") as fig:
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

        cursor = y1 - 2.70
        section(fig, _x(x0), _y(cursor), "CODE SUMMARY", fontsize=12)
        cursor -= 0.42
        for label, value in _code_summary_rows(profile, model.plan):
            fig.text(_x(x0 + 0.1), _y(cursor), f"{label:<26}{value}", fontsize=8,
                     family="monospace")
            cursor -= _INDEX_PITCH_IN

        cursor -= 0.45
        section(fig, _x(x0), _y(cursor), "SHEET INDEX", fontsize=12)
        cursor -= 0.42
        # Rows are whatever fits between here and the statement above the title block; the
        # column count then follows from the sheet count, not from a guess about the paper.
        per_column, columns = _index_shape(
            len(index),
            rows=max(1, int((cursor - (y0 + 0.75)) / _INDEX_PITCH_IN)),
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
            fig.text(_x(x0), _y(y0 + 0.52),
                     f"Index continues: {len(dropped)} further sheet(s) "
                     f"{dropped[0][0]}–{dropped[-1][0]} are in the set and not listed above.",
                     fontsize=8, family="monospace", weight="bold")

        fig.text(_x(x0), _y(y0 + 0.20), _gate_statement(profile, checklist),
                 fontsize=8, family="sans-serif", wrap=True)


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
            f"PASS — DRAFT, NOT FOR CONSTRUCTION. {len(unsealed)} requirement(s) rest on "
            f"engineered design computed by this engine and NOT SEALED by a licensed "
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


#: The four columns G-002 lays out into, as figure-fraction left edges, and the band they
#: run between. Measured off the composed sheet, which is why they are here and not guessed.
_NOTE_COLUMNS_X = (0.03, 0.275, 0.52, 0.765)
_NOTE_BAND = (0.90, 0.115)
_NOTE_STEP = 0.011


def _lay_out_blocks(fig, blocks: list[tuple[str, list[str]]]) -> int:
    """Lay blocks into four columns; return how many did NOT fit.

    The old loop ``break``ed out of both levels when it ran out of column and dropped
    everything after, including the remainder of the block it was mid-way through. This one
    never splits a block across a column boundary and never drops one silently — it counts
    what it could not place and hands the count back to be printed on the sheet.
    """
    top, bottom = _NOTE_BAND
    column, y = 0, top
    dropped = 0
    for title, lines in blocks:
        needed = (len(lines) + 2) * _NOTE_STEP
        if y - needed < bottom and y < top:
            column, y = column + 1, top
        if column >= len(_NOTE_COLUMNS_X):
            dropped += 1
            continue
        x = _NOTE_COLUMNS_X[column]
        section(fig, x, y, title, fontsize=7, va="top")
        y -= _NOTE_STEP * 1.6
        for line in lines:
            fig.text(x, y, line, fontsize=6, family="monospace", va="top")
            y -= _NOTE_STEP
        y -= _NOTE_STEP
    return dropped


def _write_opening_schedule(pdf, model: ResolvedModel, number: str, name: str,
                            kinds: str = "all") -> None:
    """A-601 (doors) / A-602 (windows), keyed to the plan.

    The Mark column is what makes the floor plan's bubbled ``D1``/``W3`` mean something: the
    plan stopped printing raw opening tags because a field of ``WIN-M-EAST-MID``-class text
    over the room plan is not an annotation of it, and a mark with no column to land in is
    only half of that trade. Marks come from ``plan_marks.opening_type_marks``, so the two
    cannot drift — the plan and the schedule read one mapping.

    ``kinds`` splits what used to be one sheet. Doors, windows and plumbing fixtures were
    scheduled together and they have three different readers; a door supplier reading down a
    Mark column past nine windows and a bathtub is reading the wrong sheet. Fixtures leave
    the opening schedules entirely — they are not openings, carry no plan bubble, and were
    only ever here because they had nowhere else to go. They are on A-603 now, with the
    rooms they stand in.
    """
    from typehaus.emit.draw.plan_marks import opening_type_marks

    want_doors = kinds in ("all", "door")
    want_windows = kinds in ("all", "window")
    with schedule_sheet(pdf, model, number, name) as fig:
        marks = opening_type_marks(model)
        rows = [(marks.get(opening.type_ref or "", "—"), opening.tag,
                 "Door" if opening.is_door else "Window", opening.type_ref or "RO",
                 f"{opening.width_m / M_PER_IN:.0f}\" × {opening.height_m / M_PER_IN:.0f}\"")
                for opening in sorted(model.openings, key=lambda item: item.tag)
                if (opening.is_door and want_doors) or (not opening.is_door and want_windows)]
        _add_table(fig, rows, ("Mark", "Tag", "Kind", "Type", "Nominal footprint"),
                   bbox=(0.04, 0.11, 0.92, 0.80))


def _write_room_finish_schedule(pdf, model: ResolvedModel, number: str, name: str) -> None:
    """A-603 — the room finish schedule, and the fixtures that stand in each room.

    A finish schedule is one of the two or three things a residential plan check looks for
    and this set had none: floor, base, walls and ceiling per room, which is where a builder
    reads what to order and an inspector reads what was promised. Every column is DERIVED —
    ``Room.floor_finish``, the ceiling the resolver worked out per deck region, and the
    bounding walls' own assemblies — so it cannot disagree with the model that priced it.

    ``—`` is printed where a room states nothing, never a guess. An unstated floor finish on
    catlin's guest studio is a real decision (bare sanded deck) and a schedule that filled it
    in with a plausible default would be inventing scope.
    """
    rooms = sorted(model.rooms, key=lambda r: (r.storey or "", r.tag))
    types = {item.tag: item for item in (*model.plan.library.fixture_types,
                                         *model.plan.library.appliance_types)}
    with schedule_sheet(pdf, model, number, name) as fig:
        section(fig, 0.04, 0.93, "ROOM FINISH SCHEDULE")
        rows = [(room.tag, (room.storey or "—"), _finish(room, "floor_finish"),
                 _finish(room, "base_finish"), _finish(room, "wall_finish"),
                 _ceiling_finish(model, room), f"{room.area_m2 * 10.7639:,.0f}")
                for room in rooms]
        _add_table(fig, rows,
                   ("Room", "Storey", "Floor", "Base", "Walls", "Ceiling", "Area (ft2)"),
                   bbox=(0.04, 0.50, 0.92, 0.41))

        section(fig, 0.04, 0.46, "FIXTURES AND APPLIANCES")
        fixture_rows = [
            (fixture.tag, getattr(fixture, "room", None) or "—", fixture.element_kind,
             fixture.type_ref,
             f"{types[fixture.type_ref].footprint[0].inches:.0f}\" × "
             f"{types[fixture.type_ref].footprint[1].inches:.0f}\"")
            for storey in model.plan.storeys
            for fixture in model.plan.storey_elements(storey.tag)
            if fixture.element_kind in {"Fixture", "Appliance"} and fixture.type_ref in types
        ]
        _add_table(fig, fixture_rows, ("Tag", "Room", "Kind", "Type", "Nominal footprint"),
                   bbox=(0.04, 0.11, 0.92, 0.32))


def _finish(room, field: str) -> str:
    """A room's stated finish, or ``—``. Never a default — see the schedule's docstring."""
    value = getattr(room, field, None)
    return str(value) if value else "—"


def _ceiling_finish(model, room) -> str:
    """The ceiling a room actually resolved, named by its ROOM-SIDE layer's material.

    ``ResolvedCeiling`` carries a layer stack, not a finish string — it is derived (a room
    override, else the covering deck's ``ceiling_below``, else the roof's default lining),
    which is exactly why this schedule can be trusted: the board named here is the board the
    take-off ordered.

    A room may resolve MORE THAN ONE, because ``resolve/ceilings.py`` derives a ceiling per
    DECK REGION rather than per room — catlin's gym has two, 234 sf under the I-joists and
    90 sf under the cast deck, 1 9/16" apart. Both are named. A vaulted room resolves a
    stack with no flat plane and still names its board.
    """
    names = sorted({_room_side_material(c) for c in model.ceilings
                    if c.room_ref == room.tag or c.room_ref == room.uid} - {""})
    return " / ".join(names) if names else "—"


def _room_side_material(ceiling) -> str:
    """The material of the layer a person standing in the room can touch.

    Layers run interior-first, so it is ``layers[0]`` — and it is a *material* ref rather
    than the layer's function name, because "FINISH" tells a builder nothing and
    ``gwb-x`` tells them which board to buy.
    """
    for layer in ceiling.layers:
        ref = getattr(layer, "material_ref", "") or ""
        if ref:
            return ref
    return ""


def _write_energy_sheet(pdf, model: ResolvedModel, number: str, name: str,
                        preferences: Preferences | None = None) -> None:
    """Three honest tables: prescriptive envelope, WWR, and a declared-not-Manual-J
    block load — the EN-1 rewrite (→ Permit-ready plan set Phase 7)."""

    from typehaus.checks.building_science.wwr import wwr_summary
    from typehaus.checks.code.mn_energy import evaluate_envelope
    from typehaus.checks.registry import Preferences
    from typehaus.energy import estimate_block_load

    prefs = preferences if preferences is not None else Preferences()
    with schedule_sheet(pdf, model, number, name) as fig:
        section(fig, 0.04, 0.90, "PRESCRIPTIVE ENVELOPE — MN 2024, CLIMATE ZONE 6")
        prescriptive_rows = [
            (row.component, row.role, row.required, row.provided, row.verdict.upper())
            for row in evaluate_envelope(model, model.plan)
        ]
        _add_table(fig, prescriptive_rows,
                  ("Component", "Use", "Required", "Provided", "Verdict"),
                  bbox=(0.04, 0.62, 0.92, 0.26))

        section(fig, 0.04, 0.575, "WINDOW-TO-WALL RATIO")
        wwr = wwr_summary(model)
        wwr_rows = [("OVERALL", f"{wwr['overall']:.1%}")]
        wwr_rows.extend((item.facade, f"{item.ratio:.1%}") for item in wwr["per_facade"])
        _add_table(fig, wwr_rows, ("Facade", "Glazing / gross wall"), bbox=(0.04, 0.40, 0.4, 0.16))

        section(fig, 0.04, 0.36, "BLOCK LOAD — NOT A MANUAL J")
        load = estimate_block_load(model, prefs)
        load_rows = [(component.kind, f"{component.area_ft2:,.0f}",
                     f"{component.ua_btu_per_hour_f:,.1f}") for component in load.components]
        load_rows.append(("TOTAL HEATING", "", f"{load.heating_load_btu_per_hour:,.0f} BTU/h"))
        load_rows.append(("TOTAL COOLING", "", f"{load.cooling_load_btu_per_hour:,.0f} BTU/h "
                                                f"({load.cooling_tons:.1f} tons)"))
        _add_table(fig, load_rows, ("Component", "Area (ft2)", "UA / total"),
                  bbox=(0.04, 0.15, 0.5, 0.20))
        if load.unknown_inputs:
            fig.text(0.04, 0.115, "NOT A MANUAL J — unknown inputs: "
                     + ", ".join(load.unknown_inputs), fontsize=7, family="sans-serif", wrap=True)
        else:
            fig.text(0.04, 0.115, "NOT A MANUAL J — a transparent block-load estimate only.",
                     fontsize=7, family="sans-serif")


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
