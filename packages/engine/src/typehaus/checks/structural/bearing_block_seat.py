"""``structural.bearing_block_seat`` — a beam's bearing stud over a 2x6 box has a cheek under it.

``resolve/floor_blocking.py`` frames a 2x6 box (flat rails under the deck and on the plate,
cheeks on edge between) where a run crosses a bearing bay. The cheeks are the only members in
the box that carry down: a point load landing between them rides a flat rail across the
pass-through. A wall's own studs spread their line load through the plates, but a stud under a
beam end is a point load, so it needs a cheek under it (or no box: a solid block carries it).

Scope, from the model: every stud, king, jack, corner or post of a wall standing on a floor
whose footprint a beam above overlaps (the beam's underside within a floor's depth of the
wall's top plate), and which lies over a bearing-line or ladder box of that floor.

* FAIL — no cheek under the stud (a quarter of its footprint over the box puts it there, and
  a quarter on a cheek carries it; a stud mostly on the joist closing the bay is not over it);
* PASS — a cheek stands under it;
* N/A — only where every such stud was read and none stands over a box.
"""

from __future__ import annotations

import re

from shapely.geometry import MultiPolygon, Polygon

from typehaus.checks._authoring import failed, not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import inch
from typehaus.resolve.blocking_parts import BASE_TOL_M, FIT_TOL_M
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.model import ResolvedFloor, ResolvedModel
from typehaus.resolve.stacked_ladder import LADDER_BLOCK_PREFIX

_CID = "structural.bearing_block_seat"
_POINTS = frozenset({"stud", "king", "jack", "corner", "post"})
_BOX_PREFIXES = ("bearing-block-", LADDER_BLOCK_PREFIX)
#: A beam bears on a wall whose top plate is this far under its underside: a flush beam sits
#: on the plate, one in the floor depth above it on the deck's rim and joists.
_BEAM_REACH_M = inch(14).meters
#: Share of a stud's footprint that puts it over a box, and that a cheek must cover to carry it.
_MIN_COVER = 0.25


_PART = re.compile(r"(?:(?:-p\d+)?-rail-(?:top|bottom)|-cheek-.+)$")


def _boxes(floor: ResolvedFloor) -> dict[str, dict[str, list[Polygon]]]:
    """``{box key: {"rails": [...], "cheeks": [...]}}`` plan footprints, solid blocks left out."""
    out: dict[str, dict[str, list[Polygon]]] = {}
    for m in floor.members:
        part = _PART.search(m.child_key)
        if m.category != "blocking" or not m.child_key.startswith(_BOX_PREFIXES) or not part:
            continue
        kind = "cheeks" if "-cheek-" in part.group() else "rails"
        if kind == "rails" and not part.group().endswith("-rail-top"):
            continue
        out.setdefault(m.child_key[:part.start()], {"rails": [], "cheeks": []})[kind].append(
            Polygon(member_footprint(m)[0]))
    return {k: v for k, v in out.items() if v["rails"]}


def _beam_bearing_studs(model: ResolvedModel, floor: ResolvedFloor, z_deck: float):
    """``(wall, stud, footprint, beam tag)`` for each point-load stud under a beam end."""
    beams = [(s.tag, Polygon(s.outline), s.z0_m) for s in model.solids
             if s.category == "beam" and len(s.outline) >= 3]
    for wall in model.walls:
        if (wall.storey != floor.storey or wall.is_foundation
                or abs(wall.z0_m - z_deck) > BASE_TOL_M):
            continue
        top = wall.plate_top_z_m if wall.plate_top_z_m is not None else wall.z1_m
        for stud in wall.members:
            if stud.category not in _POINTS or stud.p0 != stud.p1:
                continue
            ring = Polygon(member_footprint(stud)[0])
            for tag, outline, z0 in beams:
                if -BASE_TOL_M <= z0 - top <= _BEAM_REACH_M and \
                        ring.buffer(-FIT_TOL_M).intersects(outline):
                    yield wall, stud, ring, tag
                    break


@check(Tier.STRUCTURAL, _CID)
def bearing_block_seat(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    boxes_seen = studs_seen = 0
    for floor in ctx.model.floors:
        joists = [m for m in floor.members if m.category == "joist"]
        boxes = _boxes(floor)
        if not joists or not boxes:
            continue
        boxes_seen += len(boxes)
        envelopes = {k: MultiPolygon(v["rails"]).envelope for k, v in boxes.items()}
        carried: list[str] = []
        for wall, stud, ring, beam in _beam_bearing_studs(
                ctx.model, floor, max(m.z1_m for m in joists)):
            studs_seen += 1
            for key, env in envelopes.items():
                if ring.intersection(env).area < _MIN_COVER * ring.area:
                    continue  # mostly on the joist or trimmer that closes the bay
                cover = max((ring.intersection(c).area for c in boxes[key]["cheeks"]),
                            default=0.0)
                tags = (floor.tag, wall.tag, beam)
                what = f"{wall.tag} {stud.child_key} (under {beam}) over {floor.tag}'s {key}"
                if cover >= _MIN_COVER * ring.area:
                    carried.append(f"{wall.tag} {stud.child_key}")
                else:
                    out.append(failed(
                        _CID, f"{what}: no cheek stands under it, so the beam's point load "
                        "rides a flat 2x6 rail across the pass-through",
                        tags, fix="keep a run out of the cheek's footprint (a riser's hole "
                        "ends the rail on a cheek there; a leg along the box strips both), "
                        "or move the stud off the box"))
        if carried:
            out.append(passed(_CID, f"{floor.tag}: {len(carried)} beam bearing stud(s) over its "
                              f"boxes each stand on a cheek ({', '.join(carried)})",
                              (floor.tag,)))
    if out:
        return out
    return [not_applicable(
        _CID, f"{studs_seen} beam bearing stud(s) read over {boxes_seen} floor 2x6 box(es); "
        "none stands over a box")]
