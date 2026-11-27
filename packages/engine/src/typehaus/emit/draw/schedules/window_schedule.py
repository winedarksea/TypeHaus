"""A-602 — the window schedule, then the rough openings that take no unit.

A window row says which supplier and frame it is ordered as (``WindowType.product_ref``,
``frame_depth``) and which jamb an operable sash hinges on (``Window.hinge``). A rough
opening (a doorless passage, a service penetration, a niche) has no unit, so it gets its
own short table rather than a row of ``—`` in the window columns.
"""

from __future__ import annotations

from typehaus.emit.draw.schedules.paged_tables import PagedTable
from typehaus.model.enums import WindowOperation
from typehaus.resolve import compass
from typehaus.resolve.model_window_seat import window_frame_dimensions

WINDOW_COLUMNS = ("Mark", "Tag", "Type", "Product", "Operation", "RO", "Modeled frame",
                  "Frame depth", "Hinge", "RO sill", "Net clear", "U-factor", "SHGC", "VT",
                  "Tempered")
ROUGH_COLUMNS = ("Tag", "Wall", "RO", "RO sill", "Depth", "Serves")


def window_tables(model, ordered, windows, marks) -> list[PagedTable]:
    from typehaus.emit.draw.schedules.openings import ro_sill_m

    rows, rough = [], []
    for opening in ordered:
        if opening.is_door:
            continue
        if opening.kind == "rough_opening":
            rough.append(_rough_row(model, opening, ro_sill_m(model, opening)))
        else:
            rows.append(_window_row(model, opening, windows.get(opening.type_ref or ""),
                                    marks, ro_sill_m(model, opening)))
    tables = [PagedTable("WINDOW SCHEDULE", WINDOW_COLUMNS, tuple(rows))]
    if rough:
        tables.append(PagedTable("ROUGH OPENINGS — NO UNIT (PASSAGES, PENETRATIONS, NICHES)",
                                 ROUGH_COLUMNS, tuple(rough)))
    return tables


def _window_row(model, opening, spec, marks, sill_m) -> tuple[str, ...]:
    from typehaus.emit.draw.schedules.openings import _fi, energy_columns, size_pair
    from typehaus.takeoff.product_labels import product_label

    u_text, shgc, vt, operation, tempered = energy_columns(spec, False)
    product = model.plan.library.product(getattr(spec, "product_ref", None) or "")
    depth = getattr(spec, "frame_depth", None)
    return (marks.get(opening.tag, "—"), opening.tag, opening.type_ref or "—",
            product_label(product) if product is not None else "—", operation,
            size_pair(opening.width_m, opening.height_m, 16),
            _frame_size_text(window_frame_dimensions(opening)),
            _depth_text(opening, depth),
            _hinge_text(model, opening, spec), _fi(sill_m),
            _window_clear_text(opening, spec), u_text, shgc, vt, tempered)


def _depth_text(opening, depth) -> str:
    """The frame depth, and how far the seat leaves the unit proud of its mount plane."""
    from typehaus.emit.draw.detail_components.stack_dimensions import dim_text
    from typehaus.emit.draw.schedules.openings import _fi
    from typehaus.quantities import M_PER_IN

    if depth is None:
        return "—"
    proud = getattr(opening.window_seat, "proud_m", 0.0)
    note = f" ({dim_text(proud / M_PER_IN)} proud, confirm)" if proud > 1e-4 else ""
    return _fi(depth.meters, 16) + note


def _rough_row(model, opening, sill_m) -> tuple[str, ...]:
    from typehaus.emit.draw.schedules.openings import _fi, size_pair

    return (opening.tag, opening.host_wall, size_pair(opening.width_m, opening.height_m, 16),
            _fi(sill_m), "through" if opening.depth_m is None else _fi(opening.depth_m, 16),
            ", ".join(opening.penetration_for) or "—")


def _hinge_text(model, opening, spec) -> str:
    """The hinge jamb as a true-compass side (``W jamb``), from ``Window.hinge``."""
    element = model.plan.by_tag(opening.tag)
    side = getattr(element, "hinge", None)
    wall = model.wall(opening.host_wall)
    if side is None or wall is None or getattr(spec, "operation", None) == WindowOperation.FIXED:
        return "—"
    (sx, sy), (ex, ey) = wall.axis[0], wall.axis[1]
    dx, dy = (sx - ex, sy - ey) if side == "start" else (ex - sx, ey - sy)
    return f"{compass.facade_name((dx, dy), model.plan.project.site)} jamb"


def _window_clear_text(opening, spec) -> str:
    """The maker's published net clear opening (R310.2.1), never a nominal estimate."""
    from typehaus.emit.draw.schedules.openings import size_pair

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
    return size_pair(*sizes)


def _frame_size_text(frame: tuple[float, float, float] | None) -> str:
    from typehaus.emit.draw.schedules.openings import size_pair

    if frame is None:
        return "UNRESOLVED"
    width, height, _sill = frame
    return size_pair(width, height, 16)
