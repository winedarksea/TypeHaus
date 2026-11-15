"""NEC 110.26 open enclosure doors, reported under ``electrical.panel_working_space``.

Each panel's door leaf is taken as its enclosure's width, hinged on the side its type's
``door_hinge`` names (facing the enclosure); open at 90 degrees it stands as a plan segment
square to the face from the hinge edge, over the enclosure's own height.

* **(A)(2)**: a leaf no wider than the 36 in. depth sweeps inside the working-space window the
  check already proves clear, so it passes with it. A wider leaf is UNKNOWN.
* **Access (intro)**, ``access_findings``: with every leaf open at once, some clear window of
  each panel still holds a 24 in. stretch along the face that no leaf reaching below 6 1/2 ft
  crosses (zero leaf thickness). Panels whose leaves reach each other's windows are graded as
  one group, since one hinge assignment must serve all of them; an unstated hinge is tried
  both ways: every combination passing is PASS, some is UNKNOWN naming the types that need
  ``door_hinge``, none is FAIL. **Not wired yet**: on Catlin's W-B-W1 no assignment clears
  ``ED-B-BACKUP-PANEL`` (23.87" between ``ED-B-PANEL-2``'s north leaf and its own), a design
  question for the owner (``plans/TODO-nec-2026.md``).
"""

from __future__ import annotations

import itertools
import math

from shapely.geometry import LineString

from typehaus.findings import Finding, Result, by_result
from typehaus.model.nec import NEC, cite

_CID = "electrical.panel_working_space"
_IN = 0.0254
_DEPTH_M, _HEIGHT_M, _ACCESS_M = 36 * _IN, 78 * _IN, 24 * _IN
_TOL_M = 1e-4


def _frame(body):
    a = math.radians(body.rotation_degrees)
    return (math.cos(a), math.sin(a)), (math.sin(a), -math.cos(a))


def _span(body) -> tuple[float, float, float]:
    """(lo, hi) along the face and the face's outward offset, in the body's frame."""
    along, out = _frame(body)
    s = [x * along[0] + y * along[1] for x, y in body.footprint]
    f = max(x * out[0] + y * out[1] for x, y in body.footprint)
    return min(s), max(s), f


def leaf_width_m(body) -> float:
    lo, hi, _ = _span(body)
    return hi - lo


def _leaf(body, hinge: str) -> LineString:
    """The open leaf: from the hinge edge on the face, square out by the leaf width.
    Facing the enclosure, its right hand is +along, so "right" hinges at the high end."""
    along, out = _frame(body)
    lo, hi, f = _span(body)
    s = hi if hinge == "right" else lo
    w = hi - lo
    pts = [(s, f), (s, f + w)]
    return LineString([(u * along[0] + v * out[0], u * along[1] + v * out[1]) for u, v in pts])


def _has_stretch(window, frame_body, leaves) -> bool:
    """Whether the window holds a 24 in. stretch along the face no leaf crosses."""
    along, _ = _frame(frame_body)
    coords = list(window.exterior.coords)
    s_lo = min(x * along[0] + y * along[1] for x, y in coords)
    s_hi = max(x * along[0] + y * along[1] for x, y in coords)
    blocked: list[tuple[float, float]] = []
    for leaf in leaves:
        cut = window.intersection(leaf)
        if cut.is_empty:
            continue
        s = [x * along[0] + y * along[1] for x, y in _points(cut)]
        blocked.append((min(s), max(s)))
    edge = s_lo
    for b0, b1 in sorted(blocked):
        if b0 - edge >= _ACCESS_M - _TOL_M:
            return True
        edge = max(edge, b1)
    return s_hi - edge >= _ACCESS_M - _TOL_M


def _points(geom) -> list[tuple[float, float]]:
    if hasattr(geom, "geoms"):
        return [p for g in geom.geoms for p in _points(g)]
    return list(geom.coords)


def _placed(panels, bodies) -> list:
    return [p for p in panels if p.tag in bodies and len(bodies[p.tag].footprint) >= 3]


def door_findings(panels, bodies, clear_windows) -> list[Finding]:
    """110.26(A)(2) for every panel whose working space was proven clear."""
    out: list[Finding] = []
    for panel in _placed(panels, bodies):
        if not clear_windows.get(panel.tag):
            continue
        width = leaf_width_m(bodies[panel.tag])
        tags, code = (panel.tag,), cite(NEC.WORKING_SPACE_DOOR)
        if width > _DEPTH_M + _TOL_M:
            out.append(by_result(_CID, Result.UNKNOWN, f"{panel.tag}: a {width / _IN:.1f}\" leaf "
                                 "swings past the 36\" working depth; its 90-degree opening is "
                                 "not shown clear", tags, code))
        else:
            out.append(by_result(_CID, Result.PASS, f"{panel.tag}: its {width / _IN:.1f}\" leaf "
                                 "opens 90 degrees inside the clear 36\" working space", tags,
                                 code))
    return out


def _reaches(other, windows, floor) -> bool:
    """Whether ``other``'s open leaf, on either hinge, can stand in one of these windows."""
    return (other.body_z0_m is not None and other.body_z0_m < floor + _HEIGHT_M
            and any(not w.intersection(_leaf(other, side)).is_empty
                    for w in windows for side in ("left", "right")))


def _groups(placed, bodies, clear_windows, floors) -> list[list]:
    """Panels whose leaves can reach each other's windows, as connected groups."""
    graded = [p for p in placed if clear_windows.get(p.tag)]
    links = {p.tag: {o.tag for o in placed if bodies[o.tag].storey == bodies[p.tag].storey
                     and _reaches(bodies[o.tag], clear_windows[p.tag], floors[p.tag])}
             for p in graded}
    seen: set[str] = set()
    out: list[list] = []
    for p in graded:
        if p.tag in seen:
            continue
        group, todo = set(), [p.tag]
        while todo:
            tag = todo.pop()
            if tag in group:
                continue
            group.add(tag)
            todo += [t for t in links.get(tag, ()) if t not in group]
            todo += [t for t, near in links.items() if tag in near and t not in group]
        seen |= group
        out.append([o for o in placed if o.tag in group])
    return out


def access_findings(panels, bodies, types, clear_windows, floors) -> list[Finding]:
    """The intro's access test, jointly per group: one hinge assignment must serve them all."""
    code = cite(NEC.WORKING_SPACE_ACCESS)
    placed = _placed(panels, bodies)
    hinge = {p.tag: getattr(types.get(p.type_ref or ""), "door_hinge", None) for p in placed}
    out: list[Finding] = []
    for group in _groups(placed, bodies, clear_windows, floors):
        graded = [p for p in group if clear_windows.get(p.tag)]
        free = [p for p in group if hinge[p.tag] is None]
        results = []
        for sides in itertools.product(("left", "right"), repeat=len(free)):
            chosen = {p.tag: hinge[p.tag] for p in group if hinge[p.tag]}
            chosen.update({p.tag: s for p, s in zip(free, sides, strict=True)})
            leaves = [_leaf(bodies[t], s) for t, s in chosen.items()]
            results.append(all(any(_has_stretch(w, bodies[p.tag], leaves)
                                   for w in clear_windows[p.tag]) for p in graded))
        tags = tuple(sorted(p.tag for p in group))
        head = f"{', '.join(tags)}: every leaf open at 90 degrees"
        if all(results):
            out.append(by_result(_CID, Result.PASS, f"{head} leaves a clear 24\" stretch in "
                                 "each working space" + (", for any hinge" if free else ""),
                                 tags, code))
        elif any(results):
            need = sorted({p.type_ref or p.tag for p in free})
            out.append(by_result(_CID, Result.UNKNOWN, f"{head}: a clear 24\" stretch in each "
                                 f"working space for some hinge sides only; {', '.join(need)} "
                                 "state no door_hinge", tags, code,
                                 "author door_hinge from the load centre's sheet"))
        else:
            out.append(by_result(_CID, Result.FAIL, f"{head}: no hinge sides leave a clear 24\" "
                                 "stretch in every working space", tags, code,
                                 "space the enclosures apart"))
    return out
