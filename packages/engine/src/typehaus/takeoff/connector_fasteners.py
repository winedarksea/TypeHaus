"""The nails and screws a coated or stainless connector is installed with (decision #105).

A pass over the hardware rows already derived: every row whose part number has a schedule
(``library/hardware/connector_schedules.py``) contributes count x schedule, and the result
is one row per fastener model — the part a contractor quotes, so a ZMAX tie is not driven
with electro-galv nails and a stainless one with whatever is on the truck.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from typehaus.hardware.catalog import hardware_by_model
from typehaus.hardware.connector_fastening import connector_fastening
from typehaus.takeoff.hardware_row import hardware_row


def _catalogued(model: str):
    item = hardware_by_model(model)
    if item is None or item.model != model:
        raise LookupError(f"connector schedule names {model!r}, which is not catalogued")
    return item


def connector_fastener_rows(rows: list) -> list:
    """Fastener rows for the connector ``rows``; storeys merged where every source has one."""
    totals: Counter = Counter()
    by_storey: dict[str, Counter] = defaultdict(Counter)
    storey_known: dict[str, bool] = defaultdict(lambda: True)
    terms: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        part = row.get("part_number")
        schedule = connector_fastening(part) if part else None
        if schedule is None:
            continue
        connectors = int(row["count"])
        for per, fastener, into in schedule.fasteners:
            totals[fastener] += connectors * per
            terms[fastener][(part, per, into)] += connectors
            if row.get("by_storey"):
                for storey, n in row["by_storey"].items():
                    by_storey[fastener][storey] += n * per
            else:
                storey_known[fastener] = False

    out = []
    for fastener, count in sorted(totals.items()):
        if count <= 0:
            continue
        basis = "; ".join(f"{part} x{n} x {per} into {into}"
                          for (part, per, into), n in sorted(terms[fastener].items()))
        out.append(hardware_row(
            _catalogued(fastener), scope="connector fasteners", count=count,
            part_number=fastener,
            by_storey=dict(sorted(by_storey[fastener].items()))
            if storey_known[fastener] else None,
            basis=f"connector count x schedule (C-C-2026 / the catalog record): {basis}"))
    return out
