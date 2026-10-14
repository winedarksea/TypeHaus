"""Nothing physical may intrude into an explicitly reserved finite volume."""

from __future__ import annotations

from collections.abc import Iterator

from shapely.geometry import LineString, MultiPoint, Point, Polygon, box

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity, passed, unknown
from typehaus.resolve.geometry_ir import GBox, GPrism
from typehaus.resolve.geometry_millwork import base_run_prisms
from typehaus.resolve.geometry_openings import opening_parts
from typehaus.resolve.mep_envelopes import Prism, envelopes, run_polylines, run_sections
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.placeable_bodies import body_prism
from typehaus.resolve.sweep import sweep_legs

CHECK_ID = "integrity.clear_zone_intrusion"
CONTACT_TOLERANCE_M = 1e-9
MIN_INTERSECTION_AREA_M2 = CONTACT_TOLERANCE_M ** 2


def _solid_prism(tag: str, kind: str, solid: GPrism | GBox) -> Prism:
    if isinstance(solid, GPrism):
        return Prism(tag, kind, Polygon(solid.ring, holes=solid.voids),
                     solid.z0_m, solid.z1_m)
    points = (*solid.corners_bottom, *solid.corners_top)
    return Prism(tag, kind, MultiPoint([(p[0], p[1]) for p in points]).convex_hull,
                 min(p[2] for p in points), max(p[2] for p in points))


def _bodies(model: ResolvedModel, run_tags: set[str]) -> Iterator[Prism]:
    for item in model.canvas_objects:
        body = body_prism(item)
        if body is not None:
            yield _solid_prism(item.tag, item.kind, body)
    # Plumbing accessories and derived cleanouts are solids rather than placeables.
    # Runs use their insulated segment envelopes above, never their whole-run z bounds.
    run_solid_uids = {f"{run.uid}-run" for run in
                      (*model.pipe_runs, *model.ducts, *model.conduits)}
    for solid in model.solids:
        if (solid.tag not in run_tags and solid.uid not in run_solid_uids
                and len(solid.outline) >= 3):
            if solid.sweep is not None:
                for start, end in sweep_legs(solid.sweep):
                    yield _solid_prism(solid.tag, solid.category, GBox(start, end))
            else:
                yield Prism(solid.tag, solid.category,
                            Polygon(solid.outline, holes=solid.voids), solid.z0_m, solid.z1_m)
    for run in model.base_runs:
        for solid in base_run_prisms(run):
            yield _solid_prism(run.tag, "baseboard", solid)
    door_types = {item.tag: item for item in model.plan.library.door_types}
    for opening in model.openings:
        wall = model.wall(opening.host_wall)
        if wall is None:
            continue
        product = door_types.get(opening.type_ref)
        parts = opening_parts(wall, opening,
            operation=product.operation if product is not None else None,
            is_glazed=product is not None and product.glazed,
            is_trimless=product is not None and product.trimless,
            bookcase_door=product.bookcase_door if product is not None else None,
            leaf_set=product.leaf_set if product is not None else "pull")
        for part in parts:
            if "leaf" not in part.key and part.key != "glass":
                continue
            for solid in part.solids:
                # Opening products are upright prisms/boxes at rest, not swing sectors.
                if isinstance(solid, (GPrism, GBox)):
                    yield _solid_prism(opening.tag, "opening leaf at rest", solid)


def _overlaps(zone, footprint, prism: Prism) -> bool:
    overlap = min(zone.z1_m, prism.z1_m) - max(zone.z0_m, prism.z0_m)
    return (overlap > CONTACT_TOLERANCE_M
            and prism.footprint.is_valid
            and footprint.intersection(prism.footprint).area > MIN_INTERSECTION_AREA_M2)


def _potential_run_footprints(model: ResolvedModel) -> dict:
    """Locate schematic runs even when no elevations exist to build their envelopes.

    Missing dimensions remain the run checks' global gap. A reservation reports that gap
    when the run's known nominal footprint could occupy this reservation, so a schematic
    run on the other side of the house does not make every zone UNKNOWN.
    """
    sections = run_sections(model)
    footprints = {}
    for _kind, tag, path, _z in run_polylines(model):
        if not path:
            footprints[tag] = None
            continue
        geometry = Point(path[0]) if len(set(path)) == 1 else LineString(path)
        radius = sections.get(tag, (0.0, 0.0, None))[0]
        footprints[tag] = geometry.buffer(radius) if radius > 0 else geometry
    return footprints


@check(Tier.INTEGRITY, CHECK_ID)
def clear_zone_intrusion(ctx: CheckContext) -> list[Finding]:
    if not ctx.model.clear_zones:
        return []
    run_envelopes = envelopes(ctx.model)
    potential_footprints = _potential_run_footprints(ctx.model)
    candidates = [prism for envelope in run_envelopes for prism in envelope.prisms]
    candidates.extend(_bodies(ctx.model, {envelope.tag for envelope in run_envelopes}))
    findings = []
    for zone in ctx.model.clear_zones:
        footprint = Polygon(zone.outline)
        intrusions: dict[str, Prism] = {}
        invalid_tags = set()
        for prism in candidates:
            if prism.tag in zone.except_tags:
                continue
            if not prism.footprint.is_valid:
                overlap = min(zone.z1_m, prism.z1_m) - max(zone.z0_m, prism.z0_m)
                if (overlap > CONTACT_TOLERANCE_M and not prism.footprint.is_empty
                        and footprint.intersects(box(*prism.footprint.bounds))):
                    invalid_tags.add(prism.tag)
                continue
            if _overlaps(zone, footprint, prism):
                intrusions.setdefault(prism.tag, prism)
        for tag, prism in sorted(intrusions.items()):
            findings.append(Finding(
                check_id=CHECK_ID,
                severity=Severity.ERROR if zone.policy == "required" else Severity.WARN,
                result=Result.FAIL if zone.policy == "required" else Result.ADVISORY,
                message=f"{tag} ({prism.kind}) intrudes into {zone.tag}: {zone.purpose}",
                element_tags=(zone.tag, tag),
                fix_hint="Move the element outside the zone's outline and finite height band."))
        gaps = []
        findings.extend(unknown(CHECK_ID,
            f"{tag} has an invalid physical footprint intersecting the zone's bounds",
            (zone.tag, tag)) for tag in sorted(invalid_tags))
        for envelope in run_envelopes:
            if not envelope.gaps or envelope.tag in zone.except_tags:
                continue
            if envelope.prisms:
                relevant = any(_overlaps(zone, footprint, prism) for prism in envelope.prisms)
            else:
                possible = potential_footprints.get(envelope.tag)
                relevant = possible is None or footprint.intersects(possible)
            if relevant:
                gaps.extend(envelope.gaps)
        for item in ctx.model.canvas_objects:
            if (item.tag not in zone.except_tags and len(item.footprint) >= 3
                    and body_prism(item) is None
                    and (item.body_z0_m is None or item.body_z0_m < zone.z1_m)
                    and (item.body_z1_m is None or item.body_z1_m > zone.z0_m)
                    and footprint.intersection(Polygon(item.footprint)).area > 0):
                gaps.append(f"{item.tag} overlaps the zone but has no resolved body height")
        findings.extend(unknown(CHECK_ID, gap, (zone.tag,)) for gap in gaps)
        if not intrusions and not gaps and not invalid_tags:
            findings.append(passed(CHECK_ID,
                f"{zone.tag} is clear: {zone.purpose}", (zone.tag,)))
    return findings
