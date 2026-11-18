"""Screws in a door's girt sill beam seats (``FramingSpec.sill_course``).

Each seat names its count (``resolve/framing/girt_sill_course.py``); the part is
the authored ``SillCourseFastening.fastener_part``, into the floor edge's backer pair.
"""

from __future__ import annotations

from collections import Counter

from typehaus.hardware.catalog import screw_by_part_number
from typehaus.resolve.framing.girt_sill_course import sill_block_screws
from typehaus.resolve.framing.truss_girts import truss_girt_bands
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_row import hardware_row

SCOPE = "girt door sill beam seats"


def girt_sill_screw_rows(model: ResolvedModel) -> list:
    groups: dict[str, Counter] = {}
    specs = {}
    for wall in model.walls:
        counts = [n for n in map(sill_block_screws, wall.members) if n is not None]
        if not counts:
            continue
        bands = truss_girt_bands(model.plan, wall.assembly)
        spec = bands[1].framing.sill_course
        part = spec.fastener_part
        specs[part] = spec
        groups.setdefault(part, Counter())[wall.storey] += sum(counts)
    rows = []
    for part, by_storey in sorted(groups.items()):
        item, length_in, thread_in = screw_by_part_number(part)
        spec = specs[part]
        rows.append(hardware_row(
            item, scope=SCOPE, count=sum(by_storey.values()), part_number=part,
            size=f"{length_in:g} in", by_storey=dict(sorted(by_storey.items())),
            basis=_basis(spec, thread_in)))
    return rows


def _basis(spec, thread_in):
    return (f"per end seat as resolved: {spec.seat_rows} staggered rows of "
            f"{spec.screws_per_row}, through the {spec.course_stock} sill beam + seat stack "
            f"+ sheathing into the edge joist's SPF backer pair ({thread_in:g} in thread); "
            "notes/exterior_door_sill_beam.md")
