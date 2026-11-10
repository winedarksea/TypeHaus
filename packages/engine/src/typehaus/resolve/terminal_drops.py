"""A round run's end over a ceiling valve drops onto its collar on a derived stock elbow.

A disc valve's collar stands up from the ceiling face (``terminal_necks.ceiling_collar``)
and takes the duct from above. An author draws the run level to a point over the valve; the
resolver appends the vertical drop to the collar top, and ``mep_fittings`` derives (and
bills) the 90 there. It never snaps plan or reroutes: an end that is not over its valve, or
is below the collar top, is left for ``mep.duct_connectivity`` to FAIL.

Such runs resolve after placeables (``collar_fed_runs``), because the collar's height is
the placed register's face plus its neck.
"""

from __future__ import annotations

import math

from typehaus.model.placeables import MountKind
from typehaus.quantities import M_PER_IN

#: An end this close in plan to its valve is over it.
OVER_COLLAR_M = M_PER_IN / 16.0
#: A last leg whose ends differ less than this in z is level.
_LEVEL_M = 1e-4
#: A drop ending this close to the collar top is seated on it.
_SEAT_M = M_PER_IN / 16.0


def plain_round_collar(register_type) -> bool:
    """A square neck with no components and no inlet: a collar a round run drops onto."""
    neck = getattr(register_type, "neck", None)
    return (neck is not None and not neck.components and neck.inlet is None
            and abs(neck.width.meters - neck.height.meters) <= 1e-6)


def collar_fed_runs(plan) -> set[str]:
    """Runs a ceiling-collar register names: they wait for the placed register."""
    types = {t.tag: t for t in plan.library.register_types}
    return {el.duct_ref for el in plan.all_elements()
            if el.element_kind == "Register" and el.duct_ref
            and el.mount.kind is MountKind.CEILING
            and plain_round_collar(types.get(el.type_ref))}


def collars_by_run(model) -> dict[str, list[tuple[str, tuple[float, float, float, float]]]]:
    """``{run tag: [(register tag, (x, y, z_top, diameter))]}`` for placed ceiling collars."""
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


def arrival(path, z, at_end: bool) -> tuple[bool, bool]:
    """``(level, from above)`` for the leg that ends the run at that end."""
    end, prior = (-1, -2) if at_end else (0, 1)
    plan = math.dist(path[end], path[prior]) > OVER_COLLAR_M
    return (plan and abs(z[end] - z[prior]) <= _LEVEL_M,
            not plan and z[prior] > z[end] + _LEVEL_M)


def drop_onto_collars(model, duct_tag: str, path: list, z: list) -> None:
    """Append (or prepend) the drop to the collar top at a level end over a valve, in place."""
    collars = [c for _, c in collars_by_run(model).get(duct_tag, ())]
    for at_end in (True, False):
        end = -1 if at_end else 0
        if len(path) < 2 or not arrival(path, z, at_end)[0]:
            continue  # a vertical (or sloped) arrival is the author's own
        for x, y, top, _ in collars:
            if math.dist(path[end], (x, y)) <= OVER_COLLAR_M and z[end] > top + _LEVEL_M:
                index = len(path) if at_end else 0
                path.insert(index, (x, y))
                z.insert(index, top)
                break


def collar_seat_problem(path, z, at_end: bool, register: str,
                        collar: tuple[float, float, float, float]) -> str | None:
    """Why this run end does not sit on ``register``'s collar top, or None if it does."""
    end = -1 if at_end else 0
    x, y, top, _ = collar
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
    return None
