"""Derived 24 V leads: driver to controller, controller to the tape's feed (decision #137).

One ``ResolvedLedLead`` per leg, sized off the house's ``LedStandard``. The route is
functional, not exact: up from the gear to the cavity plane over it (the finished ceiling,
else the higher end), orthogonally there (x, then y, or along an authored
``LightRun.lead_path``), and down to the feed. Its length, plus the standard's ``slack``,
is what is billed and what the drop is graded on. No cable is swept.

Gauge is the smallest stocked cable keeping the leg's drop in budget: a driver-to-controller
leg gets half of ``max_drop_pct``, and the feed leg what that leg left. Resistance is copper's,
NEC Chapter 9 Table 8 (stranded, uncoated, 75 C): physics, not product data. A strip whose
product ships its own cords (``LedStrip.system_cords``) takes no derived lead.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from typing import Any

#: Ohms per 1000 ft, one conductor (NEC Chapter 9 Table 8, stranded uncoated copper, 75 C).
OHMS_PER_KFT = {18: 7.95, 16: 4.99, 14: 3.14, 12: 1.98, 10: 1.24}
DC_V = 24.0
_FT = 0.3048
_CAVITY_M = 0.05  # a lead rides this far above the plane it crosses


@dataclass(frozen=True)
class ResolvedLedLead:
    tag: str
    storey: str
    leg: str  # "driver": driver to controller; "feed": controller (or driver) to the tape
    run_ref: str | None  # the run a feed leg lands on; None for a shared driver leg
    type_ref: str  # the tape type it bills under
    from_ref: str
    to_ref: str
    path: tuple[tuple[float, float, float], ...]
    length_m: float  # routed length plus slack
    current_a: float
    awg: int | None  # None: no stocked cable keeps the drop in budget
    cable_ref: str | None
    drop_pct: float | None
    feed: str | None = None  # "start" | "end" on a feed leg


def wire_drop_pct(current_a: float, length_m: float, awg: int) -> float:
    """Out-and-back resistive drop of a two-wire DC lead, % of 24 V."""
    ohms = 2.0 * OHMS_PER_KFT[awg] * (length_m / _FT) / 1000.0
    return 100.0 * current_a * ohms / DC_V


def _gauge(standard, current_a: float, length_m: float, budget_pct: float):
    rows = sorted((c for c in standard.cables if c.awg in OHMS_PER_KFT),
                  key=lambda c: -c.awg)  # thinnest first
    for cable in rows:
        drop = wire_drop_pct(current_a, length_m, cable.awg)
        if drop <= budget_pct + 1e-9:
            return cable.awg, cable.product_ref, drop
    thickest = rows[-1] if rows else None
    if thickest is None:
        return None, None, None
    return None, None, wire_drop_pct(current_a, length_m, thickest.awg)


def _route(a, b, cavity_z: float, via: tuple = ()) -> tuple[tuple[float, float, float], ...]:
    """Up from ``a`` to the cavity plane, across (x then y, or ``via``), down to ``b``."""
    plan = [a[:2], *via] if via else [a[:2], (b[0], a[1])]
    plan.append(b[:2])
    pts = [(a[0], a[1], a[2])] + [(x, y, cavity_z) for x, y in plan] + [(b[0], b[1], b[2])]
    out = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, out[-1]) > 1e-6:
            out.append(p)
    return tuple(out)


def _length(path) -> float:
    return sum(math.dist(p, q) for p, q in zip(path, path[1:], strict=False))


def derive_led_leads(model: Any) -> None:
    from typehaus.model.led import LedStandard
    from typehaus.resolve.ceilings import ceiling_faces, finished_ceiling_at

    standard = next((el for el in model.plan.all_elements()
                     if isinstance(el, LedStandard)), None)
    if standard is None:
        return
    types = {t.tag: t for t in model.plan.library.electrical_device_types}
    objects = {o.tag: o for o in model.canvas_objects}
    faces = ceiling_faces(model)

    def anchor(tag: str | None):
        o = objects.get(tag or "")
        if o is None or o.body_z0_m is None:
            return None
        top = o.body_z1_m if o.body_z1_m is not None else o.body_z0_m
        return (o.position[0], o.position[1], top), o

    def cavity(a, b, obj) -> float:
        plane = finished_ceiling_at(faces, obj.storey, None, obj.position)
        return max(plane if plane is not None else max(a[2], b[2]), a[2], b[2]) + _CAVITY_M

    # Pass 1: each fed run's source, feed end and route; its controller's load.
    fed: list[tuple] = []
    loads: dict[str, list] = {}  # controller -> [watts, type_ref, controller anchor, obj]
    for run in list(model.light_runs):
        product = types.get(run.type_ref)
        strip = getattr(product, "strip", None)
        if run.psu_ref is None or strip is None or strip.system_cords or len(run.path) < 2:
            continue
        via_ctrl = anchor(run.controller_ref)
        source = via_ctrl or anchor(run.psu_ref)
        if source is None:
            continue
        gear, obj = source
        watts = (getattr(product, "watts_per_ft", None) or 0.0) * run.length_m / _FT
        ends = {"start": (*run.path[0], run.vertex_z()[0]),
                "end": (*run.path[-1], run.vertex_z()[-1])}
        element = model.plan.by_tag(run.tag)
        feed = getattr(element, "feed", None) or min(
            ends, key=lambda k: math.dist(ends[k][:2], gear[:2]))
        via = tuple(p.xy_m for p in getattr(element, "lead_path", ()) or ())
        path = _route(gear, ends[feed], cavity(gear, ends[feed], obj), via)
        fed.append((run, obj, path, watts, feed, via_ctrl is not None))
        if via_ctrl is not None:
            load = loads.setdefault(run.controller_ref, [0.0, run.type_ref, gear, obj])
            load[0] += watts
    # Pass 2: the short driver-to-controller legs, sized first on half the budget; direct
    # where the pair sits within the standard's pairing distance.
    spent: dict[str, float] = {}
    for tag, (watts, type_ref, gear, _obj) in sorted(loads.items()):
        found = anchor(getattr(model.plan.by_tag(tag), "psu_ref", None))
        if found is None:
            continue
        driver, dobj = found
        if math.dist(driver[:2], gear[:2]) <= standard.max_controller_distance.meters:
            path = (driver, gear)
        else:
            path = _route(driver, gear, cavity(driver, gear, dobj))
        length = _length(path) * (1.0 + standard.slack)
        current = watts / DC_V
        awg, cable, drop = _gauge(standard, current, length, standard.max_drop_pct / 2)
        spent[tag] = drop if drop is not None else standard.max_drop_pct
        model.led_leads.append(ResolvedLedLead(
            tag=f"{tag}-LEAD", storey=dobj.storey, leg="driver", run_ref=None,
            type_ref=type_ref, from_ref=dobj.tag, to_ref=tag, path=path, length_m=length,
            current_a=current, awg=awg, cable_ref=cable, drop_pct=drop))
    # Pass 3: each feed leg on what its driver leg left of the budget.
    for run, src, path, watts, feed, via_ctrl in fed:
        length = _length(path) * (1.0 + standard.slack)
        current = watts / DC_V
        budget = standard.max_drop_pct - (spent.get(run.controller_ref, 0.0) if via_ctrl
                                          else 0.0)
        awg, cable, drop = _gauge(standard, current, length, budget)
        index = model.light_runs.index(run)
        model.light_runs[index] = dataclasses.replace(run, feed=feed)
        model.led_leads.append(ResolvedLedLead(
            tag=f"{run.tag}-LEAD", storey=src.storey, leg="feed", run_ref=run.tag,
            type_ref=run.type_ref, from_ref=src.tag, to_ref=run.tag, path=path,
            length_m=length, current_a=current, awg=awg, cable_ref=cable, drop_pct=drop,
            feed=feed))


def lead_drop_pct(model: Any, run_tag: str) -> float | None:
    """The run's total lead drop: its feed leg plus its controller's driver leg."""
    feed = next((le for le in model.led_leads if le.run_ref == run_tag), None)
    if feed is None or feed.drop_pct is None:
        return None
    driver = next((le for le in model.led_leads
                   if le.leg == "driver" and le.to_ref == feed.from_ref), None)
    if driver is not None and driver.drop_pct is None:
        return None
    return feed.drop_pct + (driver.drop_pct if driver else 0.0)
