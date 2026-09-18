"""The routing space as a picture: per level, what is clear, what costs, what refuses.

Phase 8 of the routing roadmap. A refusal already says what blocked it and by how much
(:mod:`typehaus.routing.diagnostics`); this says the same thing about the space *before*
anybody searches it — which is the question a person actually asks looking at a plan, and
the one a multimodal agent can act on.

**Four classes, and each one names the action it implies.** The class is not a severity:

* **green** — verified clear for this service's section at this level. Nothing is in it and
  nothing prices it, so a route through it costs travel and nothing else.
* **orange** — conditional passage, with the action attached. Either a priced region (a
  finished room, in-wall travel: take it and be charged) or a MOVABLE blocker (another
  service run: re-route that one and this opens). Both are things a person can decide.
* **red** — prohibited under the current design and policy: a rough opening, a floor void,
  unsleeved concrete. A route does not negotiate with these.
* **gray** — insufficient geometry to say. The caller's own ``--avoid`` (which is "you told
  me not to", not "it is concrete") and anything the model places too vaguely to grade.

**The classes are read off ``HardPrism.kind``, never inferred from a tag**, and the mapping
is :func:`~typehaus.routing.diagnostics.mobility_of` — the same one the refusals use. A view
that classified a lane differently from the refusal about that lane would be worse than no
view.

**Diagnostic relaxation never turns an unresolved collision green.** A counterfactual lifts
a movable blocker to price what would open; this module shows that blocker as *orange with
the lift named*, and the space under it stays exactly as red or as orange as it is. Drawing
the relaxed world would be drawing a house nobody has.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from typehaus.routing.diagnostics import Mobility, mobility_of

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.routing.space import RoutingSpace

CLASS_GREEN = "green"
CLASS_ORANGE = "orange"
CLASS_RED = "red"
CLASS_GRAY = "gray"

#: Mobility to class. ``PRICED`` never reaches here from a hard prism — a soft prism is
#: orange by construction below — but the row is present so the mapping is total and a new
#: mobility cannot fall through to green by omission.
_CLASS_BY_MOBILITY = {
    Mobility.FIXED: CLASS_RED,
    Mobility.MOVABLE: CLASS_ORANGE,
    Mobility.PRICED: CLASS_ORANGE,
    Mobility.UNKNOWN: CLASS_GRAY,
}


@dataclass(frozen=True)
class Region:
    """One classified polygon on one level, and the sentence that goes with it."""

    level_m: float
    klass: str
    tag: str
    kind: str
    #: shapely Polygon or MultiPolygon, in the project frame.
    footprint: Any
    #: What a reader should do about it, in words. Never "blocked": an instruction.
    action: str

    def payload(self, *, decimals: int = 4) -> dict:
        from shapely.geometry import mapping

        return {
            "level_m": round(self.level_m, decimals),
            "class": self.klass,
            "tag": self.tag,
            "kind": self.kind,
            "action": self.action,
            "area_m2": round(self.footprint.area, decimals),
            "geometry": mapping(self.footprint),
        }


def _action(klass: str, kind: str, tag: str) -> str:
    if klass == CLASS_RED:
        return (f"{tag} is {kind} — framed, poured or cut. A route does not negotiate with "
                "it; move the terminal, or sleeve it and author the penetration")
    if klass == CLASS_ORANGE and kind == "run":
        return (f"{tag} is another service run. `haus route --run {tag}` proposes it a new "
                "lane, and `--counterfactual` prices what lifting it would open — neither "
                "is a claim that it may move")
    if klass == CLASS_ORANGE:
        return (f"{tag} is priced, not prohibited: a route may take it and is charged the "
                "per-foot rate `[mep.routing]` states for it")
    return (f"{tag} carries too little geometry to classify — it is an --avoid the caller "
            "named, or a run the model places schematically. Author it, or accept that "
            "nothing here is graded")


def regions_at(space: RoutingSpace, level_m: float) -> list[Region]:
    """Every classified region on one level, red first so a reader meets the refusals first.

    A prism is *on* a level when the level is inside its z band; nothing is projected from
    another level, because a region drawn where the obstacle is not is exactly the error the
    per-level lattice was built to stop making.

    **One region per element, not per segment.** A run is one prism per leg, and a reader who
    asked what is in the way wants to be told "this duct" once rather than eleven times with
    the same sentence. The legs are unioned; the element is the thing a person acts on.
    """
    merged: dict[tuple[str, str, str], list] = {}
    for prism in space.hard:
        if prism.footprint.is_empty or not (prism.z0_m <= level_m <= prism.z1_m):
            continue
        klass = _CLASS_BY_MOBILITY.get(mobility_of(prism.kind), CLASS_GRAY)
        merged.setdefault((klass, prism.tag, prism.kind), []).append(prism.footprint)
    for prism in space.soft:
        if prism.footprint.is_empty or not (prism.z0_m <= level_m <= prism.z1_m):
            continue
        merged.setdefault((CLASS_ORANGE, prism.tag, prism.kind), []).append(prism.footprint)

    from typehaus.resolve import overlay

    order = {CLASS_RED: 0, CLASS_ORANGE: 1, CLASS_GRAY: 2, CLASS_GREEN: 3}
    return [Region(level_m=level_m, klass=klass, tag=tag, kind=kind,
                   footprint=(parts[0] if len(parts) == 1 else overlay.union_all(parts)),
                   action=_action(klass, kind, tag))
            for (klass, tag, kind), parts in sorted(
                merged.items(), key=lambda item: (order[item[0][0]], item[0][1], item[0][2]))]


def clear_at(space: RoutingSpace, level_m: float, regions: list[Region]) -> Region | None:
    """The green region: the search bbox with everything classified taken out of it.

    Green is derived by subtraction rather than asserted, and that is the whole of its
    honesty — it cannot claim clear space that something else claimed, because it is
    literally what is left. An empty result is a level with no room at all and says so by
    being ``None``.
    """
    from shapely.geometry import box

    from typehaus.resolve import overlay

    minx, miny, maxx, maxy = space.bbox
    field = box(minx, miny, maxx, maxy)
    taken = [r.footprint for r in regions]
    if taken:
        # ``resolve.overlay`` rather than bare shapely: its fixed-precision grid is what
        # keeps a union of a hundred buffered polylines from producing slivers that then
        # read as green hairlines between two obstacles. Same reason every other union in
        # this repo goes through it.
        field = overlay.difference(field, overlay.union_all(taken))
    if field.is_empty or field.area <= 0:
        return None
    return Region(level_m=level_m, klass=CLASS_GREEN, tag="clear", kind="clear",
                  footprint=field,
                  action="verified clear for this service's section at this level: a route "
                         "here is charged travel and nothing else")


def space_view(space: RoutingSpace, levels: list[float]) -> list[Region]:
    """Every level's regions, green last on each level so it draws underneath the rest."""
    out: list[Region] = []
    for level in levels:
        regions = regions_at(space, level)
        out.extend(regions)
        clear = clear_at(space, level, regions)
        if clear is not None:
            out.append(clear)
    return out


def summary(regions: list[Region]) -> dict[str, Any]:
    """Counts and areas by class and by level — the part a terminal can print."""
    by_class: dict[str, dict[str, float]] = {}
    for region in regions:
        entry = by_class.setdefault(region.klass, {"count": 0.0, "area_m2": 0.0})
        entry["count"] += 1
        entry["area_m2"] += region.footprint.area
    return {
        "levels": sorted({round(r.level_m, 4) for r in regions}),
        "by_class": {klass: {"count": int(entry["count"]),
                             "area_m2": round(entry["area_m2"], 4)}
                     for klass, entry in sorted(by_class.items())},
    }
