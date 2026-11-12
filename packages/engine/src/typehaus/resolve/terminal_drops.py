"""A run's end over a ceiling terminal's plain neck drops onto it on a derived elbow.

A disc valve's collar, or a return grille's rectangular filter-rack neck, stands up from the
ceiling face (``terminal_necks.ceiling_collar``) and takes the duct from above. An author
draws the run level to a point over the terminal; the resolver appends the vertical drop to
the neck top, and ``mep_fittings`` derives (and bills) the 90 there: the stock elbow for a
round run, E1's shop-made r/W row (``resolve/rect_elbows``) for a rectangular one. It never
snaps plan or reroutes: an end that is not over its terminal, or is below the neck top, is
left for ``mep.duct_connectivity`` to FAIL.

A rectangular neck is a drop only once a run end sits on it (``engaged``); until then it is
a boot, as before. **The arriving section must be the neck's**: a round run's diameter, or a
rectangular run's W x D in either orientation. A mismatch is a ``collar_seat_problem``, never
accepted; the transition is its own run. A neck with components or a dimensioned ``inlet``
(a wall or side inlet, a damper assembly) is not plain: ``end_terminal_ref`` reaches it.

Such runs resolve after placeables (``collar_fed_runs``), because the collar's height is
the placed register's face plus its neck.
"""

from __future__ import annotations

import math
from typing import NamedTuple

from typehaus.model.ducts import duct_size_text
from typehaus.model.placeables import MountKind
from typehaus.quantities import M_PER_IN

#: An end this close in plan to its valve is over it.
OVER_COLLAR_M = M_PER_IN / 16.0
#: A last leg whose ends differ less than this in z is level.
_LEVEL_M = 1e-4
#: A drop ending this close to the collar top is seated on it.
_SEAT_M = M_PER_IN / 16.0
#: A section side this close to the neck's is the neck's.
_SECTION_M = 1e-4


class Collar(NamedTuple):
    """A placed ceiling neck: plan centre, top z, and its section (round: ``width`` is the
    diameter and ``depth`` equals it)."""

    x: float
    y: float
    z_top: float
    width: float
    depth: float
    is_round: bool


def plain_collar(register_type) -> str | None:
    """``"round"`` or ``"rect"`` for a neck a duct drops onto from above, else None.

    A neck states its ``section``; an unstated one is round when square, rectangular when not.
    """
    neck = getattr(register_type, "neck", None)
    if neck is None or neck.components or neck.inlet is not None:
        return None
    if neck.section is None:
        return "round" if abs(neck.width.meters - neck.height.meters) <= 1e-6 else "rect"
    return "round" if neck.section == "round" else "rect"


def collar_fed_runs(plan) -> set[str]:
    """Runs a ceiling-neck register names: they wait for the placed register.

    A rectangular neck only waits for a run with an authored end over it (the drop is
    derived there); any other run to it is a boot and resolves in order.
    """
    types = {t.tag: t for t in plan.library.register_types}
    out: set[str] = set()
    for el in plan.all_elements():
        if (el.element_kind != "Register" or not el.duct_ref
                or el.mount.kind is not MountKind.CEILING):
            continue
        kind = plain_collar(types.get(el.type_ref))
        if kind == "rect":
            run = plan.by_tag(el.duct_ref)
            path = getattr(run, "path", None) or ()
            neck = types[el.type_ref].neck
            section = tuple(getattr(getattr(run, name, None), "meters", None)
                            for name in ("diameter", "width", "depth"))
            if not any(math.dist(path[i].xy_m, el.position.xy_m) <= OVER_COLLAR_M
                       for i in (0, -1) if path) or not same_section(
                    *section, neck.width.meters, neck.height.meters, False):
                continue
        if kind is not None:
            out.add(el.duct_ref)
    return out


def collars_by_run(model) -> dict[str, list[tuple[str, Collar]]]:
    """``{run tag: [(register tag, Collar)]}`` for placed ceiling necks."""
    from typehaus.resolve.terminal_necks import ceiling_collar

    runs = {el.tag: el.duct_ref for el in model.plan.all_elements()
            if el.element_kind == "Register" and el.duct_ref}
    out: dict[str, list] = {}
    for obj in model.canvas_objects:
        if obj.tag in runs:
            collar = ceiling_collar(model, obj)
            if collar is not None:
                out.setdefault(runs[obj.tag], []).append((obj.tag, collar))
    return out


def engaged(duct, collars) -> list[tuple[str, Collar]]:
    """The necks among ``collars`` that ``duct`` is graded against.

    A round collar always (the run must seat on it). A rectangular neck only once a run end
    sits on its top (plan and z): the drop is drawn, by the author or by ``drop_onto_collars``
    from a level end over it. Until then it is a boot, with the plan reach and the 3D
    ``mep.register_reach`` every boot has had.
    """
    ends = ((duct.path[0], duct.z_m[0]), (duct.path[-1], duct.z_m[-1]))
    return [(tag, c) for tag, c in collars
            if c.is_round or any(math.dist(p, (c.x, c.y)) <= OVER_COLLAR_M
                                 and abs(z - c.z_top) <= _SEAT_M for p, z in ends)]


def same_section(diameter, width, depth, neck_width: float, neck_depth: float,
                 is_round: bool) -> bool:
    """A round run on a round neck's diameter, or a rectangular run on the neck's W x D in
    either orientation."""
    if diameter is not None:
        return is_round and abs(diameter - neck_width) <= _SECTION_M
    return not is_round and any(
        abs(width - w) <= _SECTION_M and abs(depth - d) <= _SECTION_M
        for w, d in ((neck_width, neck_depth), (neck_depth, neck_width)))


def section_problem(duct, register: str, collar: Collar) -> str | None:
    """Why ``duct``'s section is not ``register``'s neck, or None if it is."""
    if duct is None or same_section(duct.diameter_m, duct.width_m, duct.depth_m,
                                    collar.width, collar.depth, collar.is_round):
        return None
    have = duct_size_text(duct.diameter_m, duct.width_m, duct.depth_m)
    want = (duct_size_text(collar.width) if collar.is_round
            else duct_size_text(None, collar.width, collar.depth))
    return (f"arrives as {have} but {register}'s neck is {want}; match the run to the neck, "
            "or author the transition as its own run")


def arrival(path, z, at_end: bool) -> tuple[bool, bool]:
    """``(level, from above)`` for the leg that ends the run at that end."""
    end, prior = (-1, -2) if at_end else (0, 1)
    plan = math.dist(path[end], path[prior]) > OVER_COLLAR_M
    return (plan and abs(z[end] - z[prior]) <= _LEVEL_M,
            not plan and z[prior] > z[end] + _LEVEL_M)


def drop_onto_collars(model, duct_tag: str, path: list, z: list, section=None) -> None:
    """Append (or prepend) the drop to the neck top at a level end over a terminal, in place.

    ``section`` is the run's ``(diameter, width, depth)``: a rectangular neck of another
    section gets no drop (it is a boot transition, not a connection); a round one always does
    and ``collar_seat_problem`` reports the mismatch.
    """
    collars = [c for _, c in collars_by_run(model).get(duct_tag, ())
               if c.is_round or section is None or same_section(
                   *section, c.width, c.depth, False)]
    for at_end in (True, False):
        end = -1 if at_end else 0
        if len(path) < 2 or not arrival(path, z, at_end)[0]:
            continue  # a vertical (or sloped) arrival is the author's own
        for c in collars:
            if math.dist(path[end], (c.x, c.y)) <= OVER_COLLAR_M and z[end] > c.z_top + _LEVEL_M:
                index = len(path) if at_end else 0
                path.insert(index, (c.x, c.y))
                z.insert(index, c.z_top)
                break


def collar_seat_problem(path, z, at_end: bool, register: str, collar: Collar,
                        duct=None) -> str | None:
    """Why this run end does not sit on ``register``'s neck top, or None if it does; given
    the ``duct``, also why its section is not the neck's."""
    end = -1 if at_end else 0
    x, y, top = collar.x, collar.y, collar.z_top
    off = math.dist(path[end], (x, y))
    if off > OVER_COLLAR_M:
        return (f"ends {off / M_PER_IN:.1f}\" off {register}'s ceiling collar in plan; "
                "end the run over the valve")
    dz = z[end] - top
    if dz < -_SEAT_M:
        return (f"ends {-dz / M_PER_IN:.1f}\" below {register}'s collar top; "
                "the collar takes the duct from above")
    if abs(dz) > _SEAT_M or not arrival(path, z, at_end)[1]:
        return (f"does not drop onto {register}'s collar top; end the run level at least "
                "2\" over the valve")
    return section_problem(duct, register, collar)
