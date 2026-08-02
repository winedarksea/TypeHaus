"""Plumbing specialties: the in-line devices, and the kits that come with them.

``pipe_run_takeoff`` bills pipe by the foot and ``sleeve_takeoff`` bills sleeves by the
piece; neither can see a valve, because until :class:`~typehaus.model.mep.PipeAccessory`
existed there was nothing to see. A supply system's whole protection budget — the main
shutoff, the backflow preventers, the hose-bib vacuum breakers, the washer arrestors, the
capped RO tee — was prose in a notes file, so it appeared on no order and in no schedule.

Two sections, because they are two orders placed with two different suppliers:

``accessories`` is devices by the piece, grouped on (kind, model, system, size) — the four
things that change the price. A 3/4" hose-bib vacuum breaker and a 1 1/4" double-check
assembly are not interchangeable and must never roll up into one "backflow preventer: 2".

``install_parts`` is the loose kit each installation carries — a silicone gasket, a plastic
mounting bracket, a can of closed-cell foam. Nobody stocks these as "hydrant"; they are
bought individually from three aisles. They ride ``PipeAccessory.install_parts`` rather than
a catalog type because they are properties of *this* penetration: the same hydrant through
a different wall takes a different kit.
"""

from __future__ import annotations

from typehaus.resolve.model import ResolvedModel

_M_TO_IN = 39.37007874015748


def plumbing_specialties_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """In-line supply devices by the piece."""
    rows: dict[tuple[str, str, str, float], dict[str, object]] = {}
    for acc in model.pipe_accessories:
        size = round((acc.diameter_m or 0.0) * _M_TO_IN, 2)
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


def install_parts_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """The sealing/mounting consumables, one row per distinct part, billed each."""
    rows: dict[str, dict[str, object]] = {}
    for acc in model.pipe_accessories:
        for part in acc.install_parts:
            entry = rows.setdefault(part, {"count": 0, "tags": []})
            entry["count"] = int(entry["count"]) + 1
            tags = entry["tags"]
            assert isinstance(tags, list)
            tags.append(acc.tag)
    return [
        {"part": part, "count": int(entry["count"]), "tags": sorted(entry["tags"])}
        for part, entry in sorted(rows.items())
    ]
