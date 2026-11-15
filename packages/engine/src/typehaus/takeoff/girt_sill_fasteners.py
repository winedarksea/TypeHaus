"""Screws in a door's girt sill course blocks (``FramingSpec.sill_course``).

Each block names its count (``resolve/framing/girt_sill_course.py``); the part is the
authored ``SillCourseFastening.fastener_part``, which crosses the floor edge's backer pair.
"""

from __future__ import annotations

from collections import Counter

from typehaus.hardware.catalog import screw_by_part_number
from typehaus.resolve.framing.girt_sill_course import sill_block_screws
from typehaus.resolve.framing.truss_girts import truss_girt_bands
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_row import hardware_row

SCOPE = "girt door sill course blocks"


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
            basis=(f"per block as resolved: {spec.end_screws} in each end block, 1 in each "
                   f"interior block at {round(spec.block_spacing.inches, 4):g} in max, "
                   "through girt + block + sheathing + the edge joist's SPF backer pair "
                   f"({thread_in:g} in thread in the inner backer); "
                   "notes/exterior_door_structural_mount.md")))
    return rows
