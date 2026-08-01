"""Authored site drainage → solids: interceptor trenches and soakaways.

The rest of the stormwater family is derived from something else — a gutter from a roof
edge, a bedding's tile from the excavation it lies in. These two are authored, because
where an interceptor trench runs and where a drywell goes are decisions about the site, not
consequences of the building. They resolve here rather than in :mod:`.accessories` because
that module is envelope trim and hardware; a trench across the yard is neither.
"""

from __future__ import annotations

from typehaus.findings import Finding, element_error
from typehaus.model.structure import Drywell, FrenchDrain
from typehaus.resolve.drain_tile import drain_tile_solids, resolved_spec
from typehaus.resolve.geometry import circle_outline, rect_between
from typehaus.resolve.model import ResolvedModel, ResolvedSolid

#: A drywell is a cylinder; the solid IR extrudes a plan outline, so the bore is faceted.
#: Matched to the vent/downspout risers so round things read alike in the viewer.
_DRYWELL_FACETS = 16


def resolve_drainage(model: ResolvedModel) -> list[Finding]:
    """Append french-drain and drywell solids. Findings report unresolvable references."""
    findings: list[Finding] = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if isinstance(element, FrenchDrain):
                findings.extend(_resolve_french_drain(model, element, storey.tag))
            elif isinstance(element, Drywell):
                findings.extend(_resolve_drywell(model, element, storey.tag))
    return findings


def _resolve_french_drain(model: ResolvedModel, el: FrenchDrain,
                          storey: str) -> list[Finding]:
    """The trench as a band per segment, with the tile derived inside it."""
    path = [point.xy_m for point in el.path]
    if len(path) < 2:
        return [element_error("integrity.french_drain_path",
                              f"french drain {el.tag} needs at least two path points",
                              el.tag)]
    half = el.trench_width.meters / 2.0
    z0 = el.invert.meters
    z1 = z0 + el.trench_depth.meters
    for index, (start, end) in enumerate(zip(path[:-1], path[1:])):
        if start == end:
            continue
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-{index:02d}", tag=f"{el.tag}-{index + 1}", storey=storey,
            category="french_drain", outline=rect_between(start, end, -half, half),
            z0_m=z0, z1_m=z1,
        ))
    # The pipe is not the trench: the trench is the excavation and the stone, and the tile
    # is the product inside it — billed separately, and the thing that actually carries.
    if el.tile is not None:
        model.solids.extend(drain_tile_solids(
            el.uid, el.tag, storey, path, z0, resolved_spec(el.tile), closed=False))
    return []


def _resolve_drywell(model: ResolvedModel, el: Drywell, storey: str) -> list[Finding]:
    radius = el.diameter.meters / 2.0
    depth = el.depth.meters
    if radius <= 0.0 or depth <= 0.0:
        return [element_error("integrity.drywell_dimensions",
                              f"drywell {el.tag} needs a positive diameter and depth",
                              el.tag)]
    z1 = _drywell_top_m(model, el, storey)
    model.solids.append(ResolvedSolid(
        uid=f"{el.uid}-00", tag=el.tag, storey=storey, category="drywell",
        outline=circle_outline(el.position.xy_m, radius, _DRYWELL_FACETS),
        z0_m=z1 - depth, z1_m=z1,
    ))
    return []


def _drywell_top_m(model: ResolvedModel, el: Drywell, storey: str) -> float:
    """Top of stone: authored, else site grade, else the storey datum.

    Grade before the datum because a soakaway is dug from the ground. A well outside the
    garage recorded on the basement storey would otherwise begin at the basement floor and
    be drawn hanging in the excavation.
    """
    if el.top_elevation is not None:
        return el.top_elevation.meters
    grade = model.plan.project.site.grade
    if grade is not None:
        return grade.meters
    storey_def = model.plan.storey(storey)
    return storey_def.elevation.meters if storey_def is not None else 0.0
