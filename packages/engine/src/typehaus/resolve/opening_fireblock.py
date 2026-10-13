"""A chase's fireblock: the deck plane closed across the hole, cut around the runs (R302.11).

``FloorOpening.fireblock`` names the layers; the holes are never authored. Each resolve cuts
the sheet around whatever ``mep_envelopes.envelopes`` says stands in the band, so a rerouted
riser moves its hole with no plan edit. Layer 0's top is the deck top at the hole.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedFireblock, ResolvedSolid
from typehaus.resolve.overlay import difference, intersection, union_all

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedFloor, ResolvedModel

#: Clearance cut around each run's envelope: the bead the sealant fills. A cutting rule,
#: not a product choice — UL 1479 systems list 0 to 1/2"; 1/4" is the middle of that band.
ANNULAR_GAP_M = 0.25 * M_PER_IN
_TOUCH_M = 1e-4  # a hole meeting the edge or another hole leaves no web, not a sliver


def resolve_fireblocks(model: ResolvedModel) -> None:
    """Emit ``fireblock`` solids and ``model.fireblocks`` for every fireblocked chase."""
    targets = [(floor, tag, ring) for floor in model.floors for tag, ring in floor.chases
               if getattr(model.plan.by_tag(tag), "fireblock", ())]
    if not targets:
        return
    from typehaus.resolve.mep_envelopes import envelopes

    prisms = [p for env in envelopes(model) for p in env.prisms]
    for floor, tag, ring in targets:
        _one(model, floor, model.plan.by_tag(tag), ring, prisms)


def _one(model: ResolvedModel, floor: ResolvedFloor, opening, ring, prisms) -> None:
    from shapely.geometry import Polygon

    rect = Polygon(ring)
    centre = rect.centroid
    top = floor.deck_top_at(centre.x, centre.y)
    layers, sheet_holes = [], {}
    offset = 0.0
    for index, layer in enumerate(opening.fireblock):
        t = layer.thickness.meters
        z0, z1 = top - offset - t, top - offset
        holes = _holes(rect, prisms, z0, z1)  # each layer is cut by what crosses ITS band
        sheet = difference(rect, union_all(list(holes.values()))) if holes else rect
        parts = [g for g in getattr(sheet, "geoms", [sheet])
                 if g.geom_type == "Polygon" and g.area > 1e-9]
        for part_index, part in enumerate(parts):
            model.solids.append(ResolvedSolid(
                f"{opening.uid}-FB{index}{'' if part_index == 0 else part_index}",
                f"{opening.tag}-fireblock-{layer.name}", floor.storey, "fireblock",
                [tuple(p) for p in part.exterior.coords[:-1]], z0, z1,
                voids=tuple([tuple(p) for p in hole.coords[:-1]] for hole in part.interiors),
                material=layer.material_ref))
        layers.append((layer.material_ref, t, sum(g.area for g in parts)))
        if index == 0:
            sheet_holes = holes
        offset += t

    # The sheet is what is sealed and what can sliver; wool below packs round its runs.
    web, between = _min_web(rect, sheet_holes)
    model.fireblocks.append(ResolvedFireblock(
        opening_tag=opening.tag, storey=floor.storey, floor_tag=floor.tag,
        layers=tuple(layers),
        penetrations=tuple((tag, hole.length) for tag, hole in sheet_holes.items()),
        min_web_m=web, min_web_between=between))


def _holes(rect, prisms, z0: float, z1: float) -> dict:
    """Run tag -> its hole in ``rect``: every prism crossing ``z0..z1``, plus the annulus."""
    by_run: dict[str, list] = {}
    for prism in prisms:
        if prism.z1_m <= z0 or prism.z0_m >= z1 or not prism.footprint.intersects(rect):
            continue
        cut = intersection(prism.footprint.buffer(ANNULAR_GAP_M), rect)
        if not cut.is_empty and cut.area > 1e-9:
            by_run.setdefault(prism.tag, []).append(cut)
    return {tag: union_all(parts) for tag, parts in sorted(by_run.items())}


def _min_web(rect, holes: dict) -> tuple[float | None, tuple[str, ...]]:
    """The narrowest strip of sheet left: hole to hole, or hole to the opening edge."""
    best: tuple[float | None, tuple[str, ...]] = (None, ())
    tags = list(holes)
    gaps = [(rect.exterior.distance(holes[t]), (t, "edge")) for t in tags]
    gaps += [(holes[a].distance(holes[b]), (a, b))
             for i, a in enumerate(tags) for b in tags[i + 1:]]
    for gap, pair in gaps:
        if gap > _TOUCH_M and (best[0] is None or gap < best[0]):
            best = (gap, pair)
    return best
