"""Framing buried in a concrete or masonry wall layer (→ 12 §checks/structural).

``structural.member_interference`` walks framing against framing; a wall LAYER is not a
member, so a joist run through a brick wythe sat at 0 FAIL (catlin's 31 porch joists, for
as long as they did). This is the other half: every framing candidate (members plus
``column``/``beam`` solids, read through ``_interference_geom.framing_candidates``) against
every concrete or unit-masonry layer of every wall, graded as a plan overlap with a real
vertical overlap — the same two-part test, the same tolerances.

**Scope: concrete and masonry layers only**, read off the assembly layer (``Layer.masonry``,
``Layer.concrete``, or a material hatching ``concrete``/``masonry``), whatever its
function (a coating or FINISH excepted), so a brick veneer authored as CLADDING is in. A
framed wall's stud layer is out: its studs and plates are members the sibling grades.

Cleared, each for a stated reason and never by guess:

* the wall's own members, and anything bearing on or under the band (no vertical overlap);
* a stud-wall member at a junction the two walls share (the T/L convention
  ``member_interference`` already clears for framing against framing);
* a ``Post.within_wall`` naming this wall, and a ``Beam.ledger_on`` naming it;
* a POCKET: a beam that names this wall in its ``bearing_refs`` with an end inside the
  layer;
* a concrete/masonry column or pier (its assembly is itself concrete or masonry);
* a LINTEL: the masonry band starts at the beam's soffit (within tolerance), so the wythe is
  bedded on it and a steel angle's leg rising in the bed joints is the detail.

WARN severity with a FAIL result, matching the sibling's advisory convention.
"""

from __future__ import annotations

import math

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural._interference_geom import _TOL_AREA, framing_candidates
from typehaus.checks.structural.interference import _ENVELOPE_SKIN_KINDS, _JUNCTION_FRAMING
from typehaus.findings import Finding, Result, Severity, not_applicable
from typehaus.model.enums import LayerFunction
from typehaus.quantities import inch

_CHECK_ID = "structural.member_in_masonry"
_JUNCTION_TOL_M = inch(10.0).meters


#: Material hatch families that are poured or laid units — the catalog's own answer, the
#: one ``masonry_load.wall_support_kind`` reads (brick and CMU both hatch ``concrete``).
_MINERAL_HATCHES = frozenset({"concrete", "masonry"})


def _mineral_layer_names(plan, assembly_tag: str | None, cache: dict) -> set[str]:
    """Names of an assembly's concrete/masonry layers."""
    if assembly_tag in cache:
        return cache[assembly_tag]
    library = getattr(plan, "library", None)
    asm = library.resolve_assembly(assembly_tag) if library is not None and assembly_tag \
        else None
    names: set[str] = set()
    if asm is not None:
        # A coating (a wash, a trowelled film) hatches like its substrate and is not a body.
        hatch = {m.tag: m.hatch for m in library.materials if not m.coating}
        names = {ly.name for ly in (*asm.default_lining, *asm.layers)
                 if ly.function is not LayerFunction.FINISH
                 and (ly.masonry is not None or ly.concrete is not None
                      or hatch.get(ly.material_ref) in _MINERAL_HATCHES)}
    cache[assembly_tag] = names
    return names


def _subjects(model, plan, cache: dict):
    """``(wall, layer name, polygon, z0, z1)`` for every concrete/masonry wall layer."""
    from shapely.geometry import Polygon

    out = []
    for wall in model.walls:
        names = _mineral_layer_names(plan, wall.assembly, cache)
        for ly in wall.layers:
            if ly.is_cavity or not (ly.name in names or ly.material_ref == "concrete"):
                continue
            poly = Polygon(ly.polygon)
            if poly.is_valid and poly.area > _TOL_AREA:
                z0, z1 = ly.band(wall)
                out.append((wall, ly.name, poly, z0, z1))
    return out


def _authored(plan, cache: dict):
    """``(within, ledgers, bearings, mineral solids)`` read off the plan."""
    from typehaus.model.elements import Wall
    from typehaus.model.structure import Beam, Post

    within, ledgers, bearings, mineral = set(), set(), set(), set()
    if plan is None:
        return within, ledgers, bearings, mineral
    for el in plan.all_elements():
        if isinstance(el, Post) and el.within_wall:
            within.add((el.tag, el.within_wall))
        if isinstance(el, Beam):
            if el.ledger_on:
                ledgers.add((el.tag, el.ledger_on))
            bearings.update((el.tag, ref) for ref in el.bearing_refs)
        asm_tag = getattr(el, "assembly", None)
        if not isinstance(el, Wall) and asm_tag and _mineral_layer_names(plan, asm_tag, cache):
            mineral.add(el.tag)  # a concrete pier/column is not framing
    return within, ledgers, bearings, mineral


def _at_shared_junction(model, wall, member_parent, pt) -> bool:
    """True if ``pt`` is at a junction joining ``wall`` and the member's own wall."""
    other = next((w.tag for w in model.walls if w.uid == member_parent), None)
    if other is None:
        return False
    for j in getattr(model, "junctions", ()) or ():
        walls = {inc.wall_tag for inc in j.incidents}
        if {wall.tag, other} <= walls and \
                math.hypot(pt[0] - j.point[0], pt[1] - j.point[1]) <= _JUNCTION_TOL_M:
            return True
    return False


@check(Tier.STRUCTURAL, _CHECK_ID)
def member_in_masonry(ctx: CheckContext) -> list[Finding]:
    """No framing member shares volume with a concrete or masonry wall layer."""
    from shapely.geometry import Point
    from shapely.strtree import STRtree

    plan = getattr(ctx, "plan", None)
    cache: dict = {}
    subjects = _subjects(ctx.model, plan, cache)
    if not subjects:
        return [not_applicable(_CHECK_ID, "no wall in this plan has a concrete or masonry "
                               "layer, so no framing can be buried in one")]
    tol_z = inch(ctx.preferences.framing.interference_tolerance_in).meters
    within, ledgers, bearings, mineral = _authored(plan, cache)
    cands = [c for c in framing_candidates(ctx.model)
             if c.kind not in _ENVELOPE_SKIN_KINDS and c.label not in mineral]
    tree = STRtree([c.poly for c in cands])
    worst: dict[tuple[str, str], tuple[float, float, str]] = {}
    for wall, name, poly, z0, z1 in subjects:
        for j in tree.query(poly):
            c = cands[j]
            if c.parent == wall.uid:
                continue
            inter = poly.intersection(c.poly)
            if inter.area <= _TOL_AREA:
                continue
            rp = inter.representative_point()
            pt = (rp.x, rp.y)
            lo, hi = c.zband_at(pt)
            overlap = min(hi, z1) - max(lo, z0)
            if overlap <= tol_z:
                continue
            if (c.kind in _JUNCTION_FRAMING
                    and _at_shared_junction(ctx.model, wall, c.parent, pt)):
                continue
            if (c.label, wall.tag) in within or (c.label, wall.tag) in ledgers:
                continue
            if c.kind == "beam":
                ends_in = any(poly.buffer(tol_z).covers(Point(p)) for p in c.seg)
                if ends_in and (c.label, wall.tag) in bearings:
                    continue  # a pocket the beam declares
                if abs(z0 - lo) <= tol_z:
                    continue  # a lintel: the wythe is bedded on this beam
            key = (c.label, wall.tag, c.parent)
            if inter.area > worst.get(key, (0.0, 0.0, ""))[0]:
                worst[key] = (inter.area, overlap, f"{name} ({wall.assembly})")
    owner = {el.uid: el.tag for el in plan.all_elements()} if plan is not None else {}
    out = []
    for (label, wall_tag, parent), (area, overlap, layer) in sorted(worst.items()):
        own = owner.get(parent, parent)
        out.append(Finding(
            severity=Severity.WARN,
            check_id=_CHECK_ID,
            message=(f"[advisory, not engineering] framing {label} ({own}) is buried in "
                     f"{wall_tag}'s "
                     f"{layer} layer: {area / inch(1).meters ** 2:.1f} sq in shared in plan, "
                     f"{overlap / inch(1).meters:.2f}\" vertically"),
            element_tags=(own, wall_tag, label),
            fix_hint=("stop the member at the masonry face (a ledger, hanger or pocket "
                      "named in bearing_refs), or move the wall"),
            result=Result.FAIL,
        ))
    if not out:
        out.append(Finding(
            severity=Severity.WARN, check_id=_CHECK_ID, result=Result.PASS,
            message=(f"[advisory, not engineering] {len(subjects)} concrete/masonry wall "
                     f"layer(s) stand clear of every framing member"),
            element_tags=tuple(sorted({w.tag for w, *_ in subjects}))))
    return out
