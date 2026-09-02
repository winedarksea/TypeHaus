"""Plumbing specialties: the in-line devices, and the kits that come with them.

``pipe_run_takeoff`` bills pipe by the foot and ``sleeve_takeoff`` bills sleeves by the
piece; neither can see a valve — that is :class:`~typehaus.model.mep.PipeAccessory`. A
supply system's whole protection budget — the main shutoff, the backflow preventers, the
hose-bib vacuum breakers, the washer arrestors, the capped RO tee — lives here, on order
and in schedule.

Two sections, because they are two orders placed with two different suppliers:

``accessories`` is devices by the piece, grouped on (kind, model, system, size) — the four
things that change the price. A 3/4" hose-bib vacuum breaker and a 1 1/4" double-check
assembly are not interchangeable and must never roll up into one "backflow preventer: 2".

``install_parts`` is the loose kit each installation carries — a silicone gasket, a plastic
mounting bracket, a can of closed-cell foam. Nobody stocks these as "hydrant"; they are
bought individually from three aisles. They ride ``PipeAccessory.install_parts`` rather than
a catalog type because they are properties of *this* penetration: the same hydrant through
a different wall takes a different kit.

``Appliance.install_parts`` feeds the same section for the same reason. A disposer's 24V
control loop — transformer, contactor, enclosure, buttons, low-voltage cable — is an order,
not a route: nobody has decided where the cable runs, and inventing conduit for it would put
geometry in the model that no drawing supports. Counting the parts is what is actually
known, and it lands in the section that already exists for exactly this shape of order.
"""

from __future__ import annotations

from typehaus.model.spatial import Appliance
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel


def plumbing_specialties_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """In-line supply devices by the piece."""
    rows: dict[tuple[str, str, str, float], dict[str, object]] = {}
    for acc in model.pipe_accessories:
        size = round((acc.diameter_m or 0.0) / M_PER_IN, 2)
        key = (acc.kind, acc.model, acc.system or "", size)
        entry = rows.setdefault(key, {"count": 0, "tags": []})
        entry["count"] = int(entry["count"]) + 1
        tags = entry["tags"]
        assert isinstance(tags, list)
        tags.append(acc.tag)
    return [
        {"kind": kind, "model": model_no, "system": system, "size_in": size,
         "count": int(entry["count"]), "tags": sorted(entry["tags"])}
        for (kind, model_no, system, size), entry in sorted(rows.items())
    ]


def _install_part_carriers(model: ResolvedModel) -> list:
    """Everything in the model that carries an ``install_parts`` kit.

    Two spellings, one order. Accessories come off the resolved run; appliances come off
    the plan, because an ``Appliance``'s kit is a property of the authored installation and
    survives whether or not the product resolves to anything with a service connection.
    """
    return [*model.pipe_accessories,
            *(element
              for storey in model.plan.storeys
              for element in model.plan.storey_elements(storey.tag)
              if isinstance(element, Appliance))]


def install_parts_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """The sealing/mounting consumables, one row per distinct part, billed each."""
    rows: dict[str, dict[str, object]] = {}
    for carrier in _install_part_carriers(model):
        for part in carrier.install_parts:
            entry = rows.setdefault(part, {"count": 0, "tags": []})
            entry["count"] = int(entry["count"]) + 1
            tags = entry["tags"]
            assert isinstance(tags, list)
            tags.append(carrier.tag)
    return [
        {"part": part, "count": int(entry["count"]), "tags": sorted(entry["tags"])}
        for part, entry in sorted(rows.items())
    ]
