"""A-601 / A-602 / A-603 — the opening and room-finish schedules.

A-601 and A-602 carry the energy columns a plan reviewer looks for first: every column is
read off the *type*, and a type that states nothing prints ``—``. An assumed U-factor or a
defaulted SHGC on a schedule is a compliance claim nobody made.
"""

from __future__ import annotations

from typehaus.emit.draw.schedules.tables import _add_table
from typehaus.emit.draw.sheet_writer import schedule_sheet, section
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel


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
    windows = {item.tag: item for item in model.plan.library.window_types}
    doors = {item.tag: item for item in model.plan.library.door_types}
    with schedule_sheet(pdf, model, number, name) as fig:
        marks = opening_type_marks(model)
        rows = []
        for opening in sorted(model.openings, key=lambda item: item.tag):
            if opening.is_door and not want_doors:
                continue
            if not opening.is_door and not want_windows:
                continue
            spec = (doors if opening.is_door else windows).get(opening.type_ref or "")
            rows.append((
                marks.get(opening.type_ref or "", "—"), opening.tag,
                "Door" if opening.is_door else "Window", opening.type_ref or "RO",
                f"{opening.width_m / M_PER_IN:.0f}\" × {opening.height_m / M_PER_IN:.0f}\"",
                *_energy_columns(spec, opening.is_door)))
        headers: tuple[str, ...] = ("Mark", "Tag", "Kind", "Type",
                                    "Nominal footprint", "U-factor")
        if want_windows:
            headers = (*headers, "SHGC", "VT", "Operation", "Tempered")
        _add_table(fig, rows, headers, bbox=(0.04, 0.11, 0.92, 0.80))


def _energy_columns(spec, is_door: bool) -> tuple[str, ...]:
    """The columns a plan reviewer opens A-601/A-602 for, and never a default.

    U-factor is what N1102.1.2 grades a fenestration unit on, and this set carried the
    number in the library and printed it nowhere. SHGC, VT, operation and tempered glazing
    are the other four a Minnesota reviewer reads off the schedule — SHGC because the
    energy certificate has a line for the area-weighted average, tempered because R308.4
    derives the *locations* from geometry and can never know what was ordered.

    ``—`` is a type that states nothing, and it is never filled in: a defaulted SHGC on a
    permit schedule is a compliance claim nobody made.
    """
    u_factor = getattr(spec, "u_factor", None)
    u_text = f"{u_factor.u_us:.2f}" if u_factor is not None else "—"
    if is_door:
        return (u_text,)
    shgc, vt = getattr(spec, "shgc", None), getattr(spec, "vt", None)
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


