"""The window & exterior door schedule and the interior door schedule, as subs read them.

One row per opening, keyed by the plan's mark (``opening_type_marks``), with hand and jamb
read through A-601's own ``door_hand`` / ``jamb_text`` so the bid and the sheet cannot
disagree. Safety glazing and egress are what the R308.4 / R310 checks derive from the
geometry, not the type's ``tempered`` flag: that column says what was ordered.
"""

from __future__ import annotations

from typehaus.quantities import M_PER_IN
from typehaus.takeoff.bid_summaries import SummaryInputs, SummaryTable
from typehaus.takeoff.labels import _fraction_in

_EXTERIOR = ("Mark", "Tag", "Storey", "Location", "Kind", "Operation", "Hand", "Unit W x H",
             "RO W x H", "Wall", "Jamb", "Safety glazing", "Tempered ordered", "Egress",
             "U-factor", "SHGC", "Product", "Spec sheet")
_INTERIOR = ("Mark", "Tag", "Storey", "Location", "Size", "Operation", "Hand", "Core",
             "Function", "Jamb", "Safety glazing", "Fire rating", "Closer", "HW set", "Product")


def openings_summary(inputs: SummaryInputs) -> list[SummaryTable]:
    return [exterior_schedule(inputs), interior_door_schedule(inputs), hardware_sets(inputs)]


def exterior_schedule(inputs: SummaryInputs) -> SummaryTable:
    from typehaus.emit.draw.schedules.openings import door_hand, energy_columns, jamb_text
    from typehaus.resolve.model_window_seat import window_frame_dimensions

    model = inputs.model
    library = model.plan.library
    doors = {t.tag: t for t in library.door_types}
    windows = {t.tag: t for t in library.window_types}
    marks, names = _marks(model), _room_names(model)
    rows = []
    for opening in _ordered(model, marks):
        spec = doors.get(opening.type_ref) if opening.is_door else windows.get(opening.type_ref)
        if spec is None or (opening.is_door and not spec.exterior):
            continue
        u_text, shgc, _vt, operation, tempered = energy_columns(spec, opening.is_door)
        sizing = opening.sizing
        if opening.is_door:
            unit = sizing.installed_unit if sizing is not None else None
            hand, jamb = door_hand(model, opening, spec), _inches(jamb_text(sizing))
        else:
            frame = window_frame_dimensions(opening)
            unit = frame[:2] if frame is not None else None
            depth = getattr(spec, "frame_depth", None)
            hand, jamb = "—", (f"frame {_fraction_in(depth.inches)}" if depth else "—")
        product = library.product(spec.product_ref or "")
        rows.append((
            marks.get(opening.tag, "—"), opening.tag, _storey(model, opening),
            _location(model, opening, names), "door" if opening.is_door else "window",
            operation.lower().replace("_", " "), hand, _size(*(unit or (None, None))),
            _size(opening.width_m, opening.height_m), _wall(model, opening), jamb,
            f"required ({inputs.glazing[opening.tag]})" if opening.tag in inputs.glazing
            else "—", "yes" if tempered == "YES" else "—",
            f"yes ({inputs.egress[opening.tag]})" if opening.tag in inputs.egress else "—",
            u_text, shgc, _product_label(product), (product.url or "") if product else ""))
    return SummaryTable(
        "windows-exterior-doors", "Windows and exterior doors", _EXTERIOR, tuple(rows),
        ("Hand per ANSI/DHI A115.1G from the secure (outside) side: LH/RH swing away, LHR/RHR "
         "toward; casement handing is not modelled.",
         "Safety glazing is where R308.4 requires tempered or laminated glass by location; "
         "Tempered ordered is what the type specifies.",
         "Wall is finish face to finish face; Jamb is the door jamb as hung, or the "
         "window's stated frame depth. Grille, colour and finish are as the product names "
         "them."))


def interior_door_schedule(inputs: SummaryInputs) -> SummaryTable:
    from typehaus.emit.draw.schedules.door_hardware import hardware_set_marks
    from typehaus.emit.draw.schedules.openings import door_hand, jamb_text

    model = inputs.model
    library = model.plan.library
    doors = {t.tag: t for t in library.door_types}
    marks, names = _marks(model), _room_names(model)
    sets = hardware_set_marks(model)
    rows = []
    for opening in _ordered(model, marks):
        spec = doors.get(opening.type_ref) if opening.is_door else None
        if spec is None or spec.exterior:
            continue
        fire = spec.fire_rating_minutes
        rows.append((
            marks.get(opening.tag, "—"), opening.tag, _storey(model, opening),
            _location(model, opening, names), _door_size(spec.width.inches, spec.height.inches),
            spec.operation.value.replace("_", " "), door_hand(model, opening, spec),
            spec.core or "—", (spec.function or "—").replace("_", " "),
            _inches(jamb_text(opening.sizing)),
            f"required ({inputs.glazing[opening.tag]})" if opening.tag in inputs.glazing
            else "—", f"{fire} min" if fire else "—",
            "yes" if spec.self_closing else "—", sets.get(spec.tag, "—"),
            _product_label(library.product(spec.product_ref or ""))))
    return SummaryTable(
        "interior-doors", "Interior doors", _INTERIOR, tuple(rows),
        ("Size is feet/inches, 2/8 x 6/8 = 2'8\" x 6'8\". Hinge and lever finish are in the "
         "hardware sets.",))


def hardware_sets(inputs: SummaryInputs) -> SummaryTable:
    from typehaus.emit.draw.schedules.door_hardware import hardware_schedule_rows

    rows = tuple((mark, role, product, int(qty), height, installation)
                 for mark, role, product, qty, height, installation
                 in hardware_schedule_rows(inputs.model))
    return SummaryTable("hardware-sets", "Door hardware sets, per opening",
                        ("HW set", "Role", "Product", "Qty", "Height", "Installation"), rows)


def _marks(model) -> dict[str, str]:
    from typehaus.emit.draw.plan_marks import opening_type_marks

    return opening_type_marks(model)


def _ordered(model, marks: dict[str, str]) -> list:
    from typehaus.emit.draw.schedules.openings import mark_key

    return sorted(model.openings, key=lambda o: (mark_key(marks.get(o.tag)), o.tag))


def _room_names(model) -> dict[str, str]:
    return {e.tag: getattr(e, "name", None) or e.tag for e in model.plan.all_elements()
            if e.element_kind == "Room"}


def _location(model, opening, names: dict[str, str]) -> str:
    """The room either side, ``A ↔ B``; one name where the other side is outdoors."""
    from typehaus.resolve.room_lookup import opening_rooms

    sides = [names.get(room.tag, room.tag) for room in opening_rooms(model, opening) if room]
    return " ↔ ".join(sorted(set(sides))) or "—"


def _storey(model, opening) -> str:
    wall = model.wall(opening.host_wall)
    return wall.storey if wall is not None else "—"


def _wall(model, opening) -> str:
    wall = model.wall(opening.host_wall)
    return _fraction_in(wall.thickness_m / M_PER_IN) if wall is not None else "—"


def _size(width_m: float | None, height_m: float | None) -> str:
    if width_m is None or height_m is None:
        return "—"
    return f"{_fraction_in(width_m / M_PER_IN)} x {_fraction_in(height_m / M_PER_IN)}"


def _inches(text: str) -> str:
    """A-601 prints jambs in feet-inches (``0'-4 9/16"``); a door shop reads inches."""
    return text.replace("0'-", "")


def _door_size(width_in: float, height_in: float) -> str:
    """``32, 80`` -> ``2/8 x 6/8``; a fractional inch keeps inches, as the trade writes it."""
    def one(inches: float) -> str:
        if abs(inches - round(inches)) > 1e-6:
            return _fraction_in(inches)
        feet, rest = divmod(round(inches), 12)
        return f"{feet}/{rest}"

    return f"{one(width_in)} x {one(height_in)}"


def _product_label(product) -> str:
    from typehaus.takeoff.product_labels import product_label

    return product_label(product) if product is not None else "—"
