"""Screws at a blocked eave: the gutter girt into the blocking, and the blocking itself.

Counted off the resolved members (``resolve/roof_eave_girt.py``, ``resolve/framing/roof_eave.py``).
The counts are the hand calc's, ``houses/catlin/notes/eave_gutter_girt.md``:

* **girt standoffs** — two screws per standoff, girt + plies + sheathing + 1-1/2" into the
  block. The same length rule and the same authored screw as the wall girts'.
* **block ends** — two toe screws per end into the beveled web stiffener pair.
* **block to plate** — two toe screws down into the rafter plate.
"""

from __future__ import annotations

from collections import Counter

from typehaus.hardware.catalog import screw_by_part_number
from typehaus.hardware.config import ExteriorInsulationFastenerRules
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.roof_eave import EAVE_BLOCKING_CONNECTION
from typehaus.resolve.framing.truss_common import BLOCK_CATEGORY
from typehaus.resolve.framing.truss_wall import truss_girt_bands
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.roof_eave_girt import EAVE_GIRT_CONNECTION, EAVE_GIRT_MEMBER
from typehaus.takeoff.hardware_row import hardware_row

EAVE_GIRT_BLOCK_SCREWS = 2
EAVE_BLOCK_END_SCREWS = 4
EAVE_BLOCK_PLATE_SCREWS = 2
#: Toe screws, 0.220" SDWS: 3" at the ends (into a 1-7/16" stiffener pair), 4" down into the
#: plate (a 45-degree drive loses about half its length to the block).
_END_SCREW = "SDWS22300DB"
_PLATE_SCREW = "SDWS22400DB"


def eave_screw_rows(model: ResolvedModel, rules: ExteriorInsulationFastenerRules) -> list:
    from typehaus.takeoff.fasteners import _block_screw_choice

    walls = {wall.tag: wall for wall in model.walls}
    girt: dict = {}
    blocks: Counter = Counter()
    for roof in model.roofs:
        for member in roof.members:
            if member.connection == EAVE_BLOCKING_CONNECTION:
                blocks[roof.storey] += 1
            if member.connection != EAVE_GIRT_CONNECTION or member.category != BLOCK_CATEGORY:
                continue
            wall = walls.get(member.child_key.split("-eave-girt-")[0])
            if wall is None:
                continue
            sheathing_m = sum(layer.thickness_m for layer in wall.depth_layers()
                              if layer.function == "sheathing")
            girt_m = cross_section(EAVE_GIRT_MEMBER).width_m
            ply_m = cross_section(member.profile).width_m
            through_in = (girt_m + ply_m + sheathing_m) / M_PER_IN
            required_in = through_in + rules.minimum_structural_embedment_in
            bands = truss_girt_bands(model.plan, wall.assembly)
            authored = bands[1].framing if bands is not None else None
            clamped_in = (girt_m + ply_m) / M_PER_IN
            item, length_in, part, _thread = _block_screw_choice(
                authored, required_in, clamped_in)
            group = girt.setdefault(part, {
                "item": item, "length_in": length_in, "by_storey": Counter(),
                "through_in": through_in, "required_in": required_in,
            })
            group["by_storey"][roof.storey] += EAVE_GIRT_BLOCK_SCREWS

    rows = [hardware_row(
        g["item"], scope="eave gutter girt standoffs", count=sum(g["by_storey"].values()),
        part_number=part, size=f"{g['length_in']:g} in",
        by_storey=dict(sorted(g["by_storey"].items())),
        basis=(f"{EAVE_GIRT_BLOCK_SCREWS} per standoff into the eave blocking, through "
               f"girt + standoff plies + sheathing ({g['through_in']:.2f} in through + "
               f"{rules.minimum_structural_embedment_in:g} in embedment = "
               f"{g['required_in']:.2f} in required); one standoff per rafter bay"),
    ) for part, g in sorted(girt.items())]
    for part, per_block, scope, basis in (
        (_END_SCREW, EAVE_BLOCK_END_SCREWS, "eave blocking ends",
         "2 toe screws per end into the beveled web stiffener pair"),
        (_PLATE_SCREW, EAVE_BLOCK_PLATE_SCREWS, "eave blocking to plate",
         "2 toe screws per block down into the rafter plate"),
    ):
        if not blocks:
            break
        item, length_in, _thread = screw_by_part_number(part)
        by_storey = {storey: count * per_block for storey, count in sorted(blocks.items())}
        rows.append(hardware_row(
            item, scope=scope, count=sum(by_storey.values()), part_number=part,
            size=f"{length_in:g} in", by_storey=by_storey,
            basis=f"{basis}; restrains the block against the gutter girt's couple",
        ))
    return rows
