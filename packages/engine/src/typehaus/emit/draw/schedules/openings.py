"""A-601 / A-602 / A-603 — the opening and room-finish schedules.

A-601 and A-602 carry the energy columns a plan reviewer looks for first: every column is
read off the *type*, and a type that states nothing prints ``—``. An assumed U-factor or a
defaulted SHGC on a schedule is a compliance claim nobody made.

Lengths print through ``feet_inches_8th`` (jamb and frame to 1/16"), and the tables flow at
one legible size across continuation sheets (``paged_tables``) rather than shrinking to fit.
"""

from __future__ import annotations

from typehaus.emit.draw.schedules.paged_tables import (
    PagedTable,
    continuation_number,
    draw_page,
    wrap_cells,
)
from typehaus.emit.draw.schedules.tables import _add_table
from typehaus.emit.draw.sheet_writer import schedule_sheet, section
from typehaus.emit.draw.typography import feet_inches_8th
from typehaus.model.enums import DoorOperation
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.model_window_seat import window_frame_dimensions

_DOOR_COLUMNS = ("Mark", "Tag", "Type", "Operation", "Hand", "Nominal", "Unit", "RO", "Jamb",
                 "RO sill", "Net clear", "U-factor", "SHGC", "VT", "Tempered", "HW set",
                 "Doorway")
_WINDOW_COLUMNS = ("Mark", "Tag", "Kind", "Type", "Operation", "RO", "Modeled frame",
                   "RO sill", "Net clear", "U-factor", "SHGC", "VT", "Tempered")
_DOORWAY_WRAP = 46
#: Secure-side rank (A115.1G "outside"): outdoors, then a garage or unconditioned space,
#: then circulation. Lower is outside; a tie goes to the larger room.
_OUTSIDE_RANK = {"garage": 1, "unconditioned": 1, "hallway": 2, "stair": 2}


#: G-003's key to the A-601/A-602 columns, kept beside ``_hand`` so the two cannot drift.
HAND_LEGEND = (
    ("Hand: viewed from",
     "the secure (outside) side, ANSI/DHI A115.1G: outdoors, else a garage or unconditioned "
     "space, else the hall or stair, else the larger room"),
    ("LH / RH", "hinges on the viewer's left / right; the door swings away from the viewer"),
    ("LHR / RHR", "hinges on the viewer's left / right; the door swings toward the viewer"),
    ("PAIR / PAIR R", "a pair swinging away from / toward the viewer; active leaf per HW set"),
    ("—", "does not swing: pocket, bypass, bifold, overhead"),
    ("RO sill", "rough-opening bottom above the storey datum (top of joists or slab)"),
    ("Jamb", "stock set as-is, ripped from a stock depth, extended, or a milled flat jamb"),
    ("Net clear", "door: clear passage; window: the maker's published net clear opening"),
)


def opening_tables(model: ResolvedModel, kinds: str = "all") -> list[PagedTable]:
    """A-601 (``door``: the door schedule, then the hardware sets) / A-602 (``window``).

    The Mark column is what makes the plan's bubbled ``D13a``/``W3`` mean something, and it
    comes from ``plan_marks.opening_type_marks`` so the plan and schedule read one mapping.
    Rows sort by mark, so one bubble's openings stand together. Fixtures are on A-603.
    """
    from typehaus.emit.draw.plan_marks import opening_type_marks
    from typehaus.emit.draw.schedules.door_hardware import hardware_set_marks, hardware_tables

    marks = opening_type_marks(model)
    doors = {item.tag: item for item in model.plan.library.door_types}
    windows = {item.tag: item for item in model.plan.library.window_types}
    hardware = hardware_set_marks(model)
    ordered = sorted(model.openings, key=lambda o: (_mark_key(marks.get(o.tag)), o.tag))
    tables: list[PagedTable] = []
    if kinds in ("all", "door"):
        rows = [_door_row(model, o, doors.get(o.type_ref or ""), marks, hardware)
                for o in ordered if o.is_door]
        tables.append(PagedTable(
            "DOOR SCHEDULE — HAND PER ANSI/DHI A115.1G FROM THE SECURE SIDE (G-003)",
            _DOOR_COLUMNS, wrap_cells(rows, {len(_DOOR_COLUMNS) - 1: _DOORWAY_WRAP})))
        tables.extend(hardware_tables(model))
    if kinds in ("all", "window"):
        rows = [_window_row(o, windows.get(o.type_ref or ""), marks)
                for o in ordered if not o.is_door]
        tables.append(PagedTable("WINDOW AND ROUGH OPENING SCHEDULE", _WINDOW_COLUMNS,
                                 tuple(rows)))
    return tables


def _write_opening_schedule(pdf, model: ResolvedModel, number: str, name: str,
                            kinds: str = "all", *, page: int = 0) -> None:
    """One page of A-601 / A-602; ``number`` is this page's own (``A-601.1``)."""
    base = number if page == 0 else number.rsplit(".", 1)[0]
    with schedule_sheet(pdf, model, number, name) as fig:
        size = tuple(fig.get_size_inches())
        draw_page(fig, opening_tables(model, kinds), size, page,
                  continuation_number(base, page + 1))


def _mark_key(mark: str | None) -> tuple:
    """``D2`` < ``D10`` < ``D13a``; unmarked openings last."""
    if not mark:
        return ("~", 0, "")
    digits = "".join(c for c in mark[1:] if c.isdigit())
    return (mark[0], int(digits or 0), mark[1 + len(digits):])


def _fi(length_m: float | None, denominator: int = 8) -> str:
    return "—" if length_m is None else feet_inches_8th(length_m / M_PER_IN, denominator)


def _pair(width_m: float | None, height_m: float | None, denominator: int = 8) -> str:
    if width_m is None or height_m is None:
        return _fi(width_m, denominator) if width_m is not None else "—"
    return f"{_fi(width_m, denominator)} × {_fi(height_m, denominator)}"


def _door_row(model, opening, spec, marks, hardware) -> tuple[str, ...]:
    sizing = opening.sizing
    u_text, shgc, vt, operation, tempered = _energy_columns(spec, True)
    if sizing is None:
        nominal, unit, rough = "—", "—", _pair(opening.width_m, opening.height_m)
    else:
        nominal = _pair(sizing.nominal_w_m, sizing.nominal_h_m)
        unit = _pair(*(sizing.installed_unit or (None, None)))
        rough = _pair(sizing.rough_w_m, sizing.rough_h_m)
    clear = (_pair(sizing.clear_w_m, sizing.clear_h_m)
             if sizing is not None and sizing.clear_w_m is not None else "—")
    return (marks.get(opening.tag, "—"), opening.tag, opening.type_ref or "RO", operation,
            _hand(model, opening, spec), nominal, unit, rough, _jamb_text(sizing),
            _fi(opening.sill_m), clear, u_text, shgc, vt, tempered,
            hardware.get(opening.type_ref, "—"), _doorway_text(opening))


def _window_row(opening, spec, marks) -> tuple[str, ...]:
    u_text, shgc, vt, operation, tempered = _energy_columns(spec, False)
    is_ro = opening.kind == "rough_opening"
    return (marks.get(opening.tag, "—"), opening.tag, "Rough opening" if is_ro else "Window",
            opening.type_ref or "RO", operation, _pair(opening.width_m, opening.height_m),
            _frame_size_text(window_frame_dimensions(opening), is_ro), _fi(opening.sill_m),
            _window_clear_text(opening, spec), u_text, shgc, vt, tempered)


def _hand(model: ResolvedModel, opening, spec) -> str:
    """ANSI/DHI A115.1G hand, seen from the secure ("outside") side; ``—`` if it does not swing.

    The outside is outdoors, else a garage or unconditioned space, else circulation, else the
    larger room; with nothing either side, the side the leaf swings away from. Hinges on the
    viewer's right read RH; a leaf swinging toward the viewer adds R (reverse). A pair is
    named ``PAIR`` because no active leaf is modelled. Unflipped, the leaf hangs on the
    END-node jamb and swings toward the wall's left normal (``ResolvedOpening``).
    """
    from typehaus.resolve.geometry import wall_frame
    from typehaus.resolve.geometry_door_products import finish_faces
    from typehaus.resolve.room_lookup import room_owning

    operation = getattr(spec, "operation", DoorOperation.SWING)
    wall = model.wall(opening.host_wall)
    if operation not in (DoorOperation.SWING, DoorOperation.DOUBLE_SWING) or wall is None:
        return "—"
    origin, tangent, normal, _ = wall_frame(wall)
    faces = finish_faces(wall) or (-wall.thickness_m / 2, wall.thickness_m / 2)
    swing_left = not opening.flip_swing

    def rank(side: int) -> tuple:
        face = faces[1] if side > 0 else faces[0]
        reach = face + side * 0.15
        point = tuple(origin[i] + tangent[i] * opening.center_along_m + normal[i] * reach
                      for i in (0, 1))
        room = room_owning(model, wall.storey, point)
        if room is None:
            return (0, 0.0, 0)
        return (_OUTSIDE_RANK.get(room.occupancy, 3), -room.area_m2, 0)

    left, right = rank(1), rank(-1)
    # A tie: stand where the leaf swings away (the hinges are not seen from there).
    viewer_left = left < right or (left == right and not swing_left)
    reverse = viewer_left == swing_left
    if operation == DoorOperation.DOUBLE_SWING:
        return "PAIR R" if reverse else "PAIR"
    hinge_right = viewer_left == opening.flip_hinge
    return ("RH" if hinge_right else "LH") + ("R" if reverse else "")


def _jamb_text(sizing) -> str:
    """The jamb as hung: stock set as-is, ripped from a stock, extended, or a milled flat."""
    if sizing is None or sizing.jamb_depth_m is None:
        return "—"
    depth = _fi(sizing.jamb_depth_m, 16)
    if sizing.jamb_material_ref:
        return f"{depth} flat, {sizing.jamb_material_ref}"
    stock = _fi(sizing.jamb_stock_m, 16)
    if sizing.jamb_rip_m > 0:
        return f"{depth} rip of {stock}"
    if sizing.jamb_extension_m > 0:
        return f"{depth} = {stock} + ext."
    return f"{stock} stock"


def _window_clear_text(opening, spec) -> str:
    """The maker's published net clear opening (R310.2.1), never a nominal estimate."""
    frame = window_frame_dimensions(opening)
    sizes = []
    for index, axis in enumerate(("width", "height")):
        exact = getattr(spec, f"net_clear_{axis}", None)
        deduction = getattr(spec, f"net_clear_{axis}_deduction", None)
        if exact is not None:
            sizes.append(exact.meters)
        elif deduction is not None and frame is not None:
            sizes.append(frame[index] - deduction.meters)
        else:
            return "—"
    return _pair(*sizes)


def _eighths(length_m: float) -> str:
    """Inches to the nearest 1/8": a 27 1/2" RO must not print as 28"."""
    return f"{round(length_m / M_PER_IN * 8) / 8:g}"


def _frame_size_text(frame: tuple[float, float, float] | None, is_ro: bool = False) -> str:
    if frame is None:
        return "—" if is_ro else "UNRESOLVED"  # a rough opening has no frame by definition
    width, height, _sill = frame
    return _pair(width, height, 16)


def _energy_columns(spec, is_door: bool) -> tuple[str, ...]:
    """The columns a plan reviewer opens A-601/A-602 for, and never a default.

    U-factor is what N1102.1.2 grades a fenestration unit on, and this set carried the
    number in the library and printed it nowhere. SHGC, VT, operation and tempered glazing
    are the other four a Minnesota reviewer reads off the schedule — SHGC because the
    energy certificate has a line for the area-weighted average, tempered because R308.4
    derives the *locations* from geometry and can never know what was ordered.

    ``—`` is a type that states nothing, and it is never filled in: a defaulted SHGC on a
    permit schedule is a compliance claim nobody made. An UNGLAZED door has no SHGC and no
    VT to state — not a missing number but an absent property — and prints ``—`` for both
    however the product is spelled.

    **Operation joins the door table.** It is the one column here that is not a performance
    claim: ``DoorOperation`` is a closed vocabulary that drives the plan symbol and the
    framing pattern, so what prints is what the model built, and swing / slide / pocket /
    overhead is the first thing a door supplier reads off a schedule. Its default (SWING)
    is a product configuration the rest of the set already acts on, not an invented number
    of the kind the ``—`` rule exists to forbid — the same call A-602 already made.
    """
    u_factor = getattr(spec, "u_factor", None)
    u_text = f"{u_factor.u_us:.2f}" if u_factor is not None else "—"
    shgc, vt = getattr(spec, "shgc", None), getattr(spec, "vt", None)
    if is_door and not getattr(spec, "glazed", False):
        shgc = vt = None  # a solid leaf has no glazing to state these of
    operation = getattr(spec, "operation", None)
    return (u_text,
            f"{shgc:.2f}" if shgc is not None else "—",
            f"{vt:.2f}" if vt is not None else "—",
            str(getattr(operation, "value", operation or "—")).upper(),
            "YES" if getattr(spec, "tempered", False) else "—")


def _write_room_finish_schedule(pdf, model: ResolvedModel, number: str, name: str) -> None:
    """A-603 — the room finish schedule, and the fixtures that stand in each room.

    A finish schedule is one of the two or three things a residential plan check looks for
    and this set had none: floor, base, walls and ceiling per room, which is where a builder
    reads what to order and an inspector reads what was promised. Every column is DERIVED —
    ``Room.floor_finish``, the ceiling the resolver worked out per deck region, and the
    bounding walls' own assemblies — so it cannot disagree with the model that priced it.

    ``—`` is printed where a room states nothing, never a guess. An unstated floor finish on
    catlin's two unfinished attic lofts is a real decision (bulk storage walks on the deck)
    and a schedule that filled it in with a plausible default would be inventing scope.
    """
    rooms = sorted(model.rooms, key=lambda r: (r.storey or "", r.tag))
    types = {item.tag: item for item in (*model.plan.library.fixture_types,
                                         *model.plan.library.appliance_types)}
    with schedule_sheet(pdf, model, number, name) as fig:
        section(fig, 0.04, 0.93, "ROOM FINISH SCHEDULE")
        rows = [(room.tag, (room.storey or "—"), _finish(room, "floor_finish"),
                 _base_finish(model, room), _wall_finish(model, room),
                 _ceiling_finish(model, room), f"{room.area_m2 * 10.7639:,.0f}")
                for room in rooms]
        _add_table(fig, rows,
                   ("Room", "Storey", "Floor", "Base", "Walls", "Ceiling", "Area (ft2)"),
                   bbox=(0.04, 0.50, 0.92, 0.41))

        section(fig, 0.04, 0.46, "FIXTURES AND APPLIANCES")
        fixture_rows = [
            (fixture.tag, getattr(fixture, "room", None) or "—", fixture.element_kind,
             fixture.type_ref,
             f"{_eighths(types[fixture.type_ref].footprint[0].inches * M_PER_IN)}\" × "
             f"{_eighths(types[fixture.type_ref].footprint[1].inches * M_PER_IN)}\"")
            for storey in model.plan.storeys
            for fixture in model.plan.storey_elements(storey.tag)
            if fixture.element_kind in {"Fixture", "Appliance"} and fixture.type_ref in types
        ]
        _add_table(fig, fixture_rows, ("Tag", "Room", "Kind", "Type", "Footprint (envelope)"),
                   bbox=(0.04, 0.11, 0.92, 0.32))


def _finish(room, field: str) -> str:
    """A room's stated finish, or ``—``. Never a default — see the schedule's docstring."""
    value = getattr(room, field, None)
    return str(value) if value else "—"


def _base_finish(model, room) -> str:
    """Base material and height from the room's derived ``base_runs``, or ``—``."""
    names = sorted({f'{run.material_ref} {_eighths(run.height_m)}"'
                    for run in model.base_runs if run.room in (room.tag, room.uid)})
    return " / ".join(names) if names else "—"


def _wall_finish(model, room) -> str:
    """The room-side board of each bounding wall: the thick layer standing furthest
    toward the room (a coating has no depth, so it never wins)."""
    from typehaus.resolve.geometry import normal, sub, unit
    from typehaus.resolve.paneling import _room_side_sign
    from typehaus.resolve.room_walls import bounding_walls

    cx = sum(p[0] for p in room.clear_face) / max(len(room.clear_face), 1)
    cy = sum(p[1] for p in room.clear_face) / max(len(room.clear_face), 1)
    names: set[str] = set()
    for wall, _span in bounding_walls(model, room):
        n = normal(unit(sub(wall.axis[1], wall.axis[0])))
        sign = _room_side_sign(wall, (cx, cy))
        best, ref = float("-inf"), ""
        for layer in wall.layers:
            if layer.thickness_m <= 0 or not layer.material_ref or not layer.polygon:
                continue
            reach = max(((x - wall.axis[0][0]) * n[0] + (y - wall.axis[0][1]) * n[1]) * sign
                        for x, y in layer.polygon)
            if reach > best + 1e-6:
                best, ref = reach, layer.material_ref
        if ref:
            names.add(ref)
    return " / ".join(sorted(names)) if names else "—"


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
    names = sorted({_room_side_material(c, model.plan.library) for c in model.ceilings
                    if c.room_ref == room.tag or c.room_ref == room.uid} - {""})
    return " / ".join(names) if names else "—"


def _room_side_material(ceiling, library) -> str:
    """The material of the layer a person standing in the room can touch.

    Layers run interior-first, so it is ``layers[0]`` — and it is a *material* ref rather
    than the layer's function name, because "FINISH" tells a builder nothing and
    ``gwb-x`` tells them which board to buy.
    """
    from typehaus.resolve.coatings import is_coating

    coat = ""
    for layer in ceiling.layers:
        ref = getattr(layer, "material_ref", "") or ""
        if not ref:
            continue
        if is_coating(library, ref):  # a coating takes no depth; name the board, then the coat
            coat = coat or ref
            continue
        return f"{ref} + {coat}" if coat else ref
    return coat




def _doorway_text(opening):
    assembly = opening.doorway
    if assembly is None:
        return "UNKNOWN"
    identities = ", ".join(s.product_ref + " (" + s.purchase.removesuffix("_included") + ")"
                           for s in assembly.selected_products)
    suffix = (f"; section {assembly.section_status}; supplier {assembly.supplier_status}"
              if assembly.exterior_placement else "")
    return f"{assembly.status}: {identities or assembly.floor_treatment}{suffix}"
