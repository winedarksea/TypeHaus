"""What fills the guard between its posts and rails — the part R312.1.3 is actually about.

A ``Railing`` used to resolve to posts + N horizontal rails and nothing else, so a 42" guard
authored with ``infill="balusters", baluster_spacing=4"`` *drew* two bars with a wide-open
40" gap between them while the code check passed on the authored field alone. The model
asserted a compliance it did not depict. This module is the geometry catching up to the
vocabulary the data model already had.

Nothing here is a new authored field. The count of pickets, the count of cables and the
panel's reveal are all *derived* — a count field would let the drawn guard and the code
verdict disagree, which is the exact defect being fixed.

Infill spans post face to post face and is gated off for a ``role == "handrail"``, the same
predicate ``checks/code/mn_residential/fall_protection.py`` uses to census guards, so the
geometry and the code census agree about what a guard is.
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.findings import Finding, Result, Severity
from typehaus.model.structure import Railing
from typehaus.resolve.geometry import Vec, add, length, rect_between, scale, sub, unit
from typehaus.resolve.model import ResolvedModel, ResolvedSolid
from typehaus.resolve.railings.parts import RailingParts
from typehaus.resolve.railings.spans import RailingSurface

#: Ceiling on the solids one railing's infill may add. ~4x the largest guard anyone has
#: authored (the Catlin balcony is 88 pickets), so it never fires on real authoring — it is
#: there to turn a pathological input (a 200' run at a 1/4" gap) into a build message
#: instead of a silent viewer stall. A budget, not an LOD scheme: the geometry that *is*
#: emitted is always full fidelity, so nothing downstream has to know it was capped.
INFILL_SOLID_BUDGET = 400

#: A bay wider than this multiple of the authored post spacing is a manufacturing problem
#: for a sheet product (see ``railing_post_stations``'s known defect). Balusters absorb it
#: invisibly; a 9'-3" glass lite does not exist.
_BAY_OVERSIZE_FACTOR = 1.5


def emit_infill(model: ResolvedModel, el: Railing, storey: str, stations: list[Vec],
                surface: RailingSurface, parts: RailingParts,
                rail_h: float) -> list[Finding]:
    """Fill every bay of ``stations``, appending to ``model.solids``.

    Returns WARN findings for the two conditions worth a build message: a truncated budget,
    and a bay too wide for the sheet product authored into it.
    """
    if el.infill is None or el.role == "handrail":
        return []
    # Balusters and cable derive their count from the clear gap. Without it there is nothing
    # to derive from, and inventing a rhythm would draw a guard the R312.1.3 check is
    # simultaneously reporting UNKNOWN about.
    if el.infill in ("balusters", "cable") and el.baluster_spacing is None:
        return []

    gap = el.baluster_spacing.meters if el.baluster_spacing is not None else 0.0
    post_spacing = max(el.post_spacing.meters, 0.3)
    rail_half = parts.rail_section_m / 2.0
    solids: list[ResolvedSolid] = []
    oversize: list[str] = []
    truncated = False

    # strict=True: two slices of the same station list, both one shorter than it.
    for a, b in zip(stations[:-1], stations[1:], strict=True):
        bay = length(sub(b, a))
        clear = bay - parts.post_section_m
        if clear <= 1e-6:
            continue
        direction = unit(sub(b, a))
        inset = scale(direction, parts.post_section_m / 2.0)
        face_a, face_b = add(a, inset), sub(b, inset)
        if el.infill in ("panel", "mesh") and clear > _BAY_OVERSIZE_FACTOR * post_spacing:
            oversize.append(f"{clear / 0.3048:.2f}'")

        if el.infill == "balusters":
            bay_solids = _balusters(el, storey, face_a, face_b, direction, clear,
                                    gap, surface, parts, rail_h, rail_half)
        elif el.infill == "cable":
            bay_solids = _cables(el, storey, face_a, face_b, gap, surface, parts,
                                 rail_h, rail_half)
        else:  # "panel" | "mesh" — both draw as a sheet; the material is what says which
            bay_solids = _panel(el, storey, face_a, face_b, surface, parts,
                                rail_h, rail_half)

        room = INFILL_SOLID_BUDGET - len(solids)
        if len(bay_solids) > room:
            solids.extend(bay_solids[:max(room, 0)])
            truncated = True
            break
        solids.extend(bay_solids)

    # ``ResolvedSolid`` is frozen, so the style functions build them unnamed and the
    # naming happens once here — one running index across every bay, which is what makes a
    # uid unique and a tag readable ("RL-SG-BALCONY-BAL57").
    for index, solid in enumerate(solids):
        model.solids.append(replace(solid, uid=f"{el.uid}-i{index:03d}",
                                    tag=f"{el.tag}-{_TAG_WORD[el.infill]}{index + 1}"))

    findings: list[Finding] = []
    if truncated:
        findings.append(Finding(
            severity=Severity.WARN, check_id="geometry.railing_infill_truncated",
            message=(f"railing {el.tag} infill stopped at the {INFILL_SOLID_BUDGET}-solid "
                     "budget; the drawn guard is shorter than the authored run"),
            element_tags=(el.tag,), result=Result.FAIL))
    if oversize:
        findings.append(Finding(
            severity=Severity.WARN, check_id="geometry.railing_bay_oversize",
            message=(f"railing {el.tag} has {len(oversize)} bay(s) of "
                     f"{', '.join(oversize)} clear against a {post_spacing / 0.3048:.2f}' "
                     f"post spacing; a {el.infill} that wide is not a stock sheet"),
            element_tags=(el.tag,), result=Result.FAIL))
    return findings


_TAG_WORD = {"balusters": "BAL", "cable": "CABLE", "panel": "PANEL", "mesh": "MESH"}


def derived_infill_count(clear: float, width: float, gap: float) -> int:
    """The smallest ``n`` whose ``n+1`` gaps across ``clear`` are each ``<= gap``.

    R312.1.3's own algebra, and the reason no count is ever authored: ``n`` pickets of
    ``width`` leave ``n + 1`` openings totalling ``clear - n*width``, so
    ``(clear - n*width) / (n + 1) <= gap`` reduces to ``n >= (clear - gap) / (width + gap)``.
    Deriving it here means the drawn guard and the check's verdict cannot disagree.
    """
    if width + gap <= 0.0:
        return 0
    return max(int(math.ceil((clear - gap) / (width + gap) - 1e-9)), 0)


def _balusters(el: Railing, storey: str, face_a: Vec, face_b: Vec, direction: Vec,
               clear: float, gap: float, surface: RailingSurface, parts: RailingParts,
               rail_h: float, rail_half: float) -> list[ResolvedSolid]:
    """Vertical pickets, re-spaced evenly so the actual gap is at or under the authored one.

    Drawn with :func:`rect_between` rather than an axis-aligned square: a picket on a
    diagonal run is square to *the run*, or the balcony guard's angled legs come out as
    lozenges.

    Plumb even on a rake — the foot lands on the nosing line under that picket and the head
    rises ``rail_h`` from there, so every picket is the same length however the run slopes.
    Both ends are trimmed half a rail section so the picket tucks under the banded rail
    instead of poking through it.
    """
    width = parts.baluster_width_m
    count = derived_infill_count(clear, width, gap)
    if count <= 0:
        return []
    actual_gap = (clear - count * width) / (count + 1)
    half = width / 2.0
    out: list[ResolvedSolid] = []
    for index in range(count):
        along = actual_gap * (index + 1) + width * index + half
        centre = add(face_a, scale(direction, along))
        z0 = surface.height_at(centre) + rail_half
        out.append(ResolvedSolid(
            uid="", tag="", storey=storey, category=parts.infill_category,
            outline=rect_between(add(centre, scale(direction, -half)),
                                 add(centre, scale(direction, half)), -half, half),
            z0_m=z0, z1_m=z0 + rail_h - parts.rail_section_m,
            assembly=el.assembly, material=parts.infill_material,
        ))
    return out


def _cables(el: Railing, storey: str, face_a: Vec, face_b: Vec, gap: float,
            surface: RailingSurface, parts: RailingParts, rail_h: float,
            rail_half: float) -> list[ResolvedSolid]:
    """Horizontal tensioned cable — the same sphere algebra rotated into Z.

    One thin band per cable per span, deliberately **not** routed through
    :mod:`typehaus.resolve.round_solids`. Faceting exists to fix the silhouette of a 4"
    pipe; a 3/16" cable is 4.8 mm, so a facet ring would cost 6x the solids to move an edge
    by well under one screen pixel (~594 solids instead of 99 for one balcony guard).
    Nothing reads these quantitatively — railings bill per element.
    """
    diameter = parts.cable_diameter_m
    clear_height = rail_h - parts.rail_section_m
    count = derived_infill_count(clear_height, diameter, gap)
    if count <= 0:
        return []
    actual_gap = (clear_height - count * diameter) / (count + 1)
    half = diameter / 2.0
    out: list[ResolvedSolid] = []
    for pa, pb, surface_z in surface.spans(face_a, face_b):
        for index in range(count):
            z = (surface_z + rail_half + actual_gap * (index + 1)
                 + diameter * index + half)
            out.append(ResolvedSolid(
                uid="", tag="", storey=storey, category=parts.infill_category,
                outline=rect_between(pa, pb, -half, half),
                z0_m=z - half, z1_m=z + half,
                assembly=el.assembly, material=parts.infill_material,
            ))
    return out


def _panel(el: Railing, storey: str, face_a: Vec, face_b: Vec, surface: RailingSurface,
           parts: RailingParts, rail_h: float, rail_half: float) -> list[ResolvedSolid]:
    """One thin prism per span: post face to post face, rail-top to rail-underside.

    On a rake it reuses ``spans`` and stair-steps, which costs nothing and keeps one story
    about how the prism-only IR fakes a slope. Mesh comes here too — drawing the wire is
    thousands of solids for a feature invisible past about a metre, so mesh draws as a sheet
    and its *material* is what says mesh.
    """
    half = parts.panel_thickness_m / 2.0
    out: list[ResolvedSolid] = []
    for pa, pb, surface_z in surface.spans(face_a, face_b):
        out.append(ResolvedSolid(
            uid="", tag="", storey=storey, category=parts.infill_category,
            outline=rect_between(pa, pb, -half, half),
            z0_m=surface_z + rail_half, z1_m=surface_z + rail_h - rail_half,
            assembly=el.assembly, material=parts.infill_material,
        ))
    return out
