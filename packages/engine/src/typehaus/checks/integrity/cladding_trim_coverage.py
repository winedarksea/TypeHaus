"""Grade that every free cladding and roof edge ends in a modeled trim piece."""

from __future__ import annotations

import math

from typehaus.checks.integrity.cladding_trim_runs import (
    along_extent,
    door_opening_trim,
    metal_wall_openings,
    spans_cover,
    z_extent,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import failed, not_applicable, passed, unknown
from typehaus.library.trim.metal_sales import PROFILES
from typehaus.model.cladding_trim import TrimCondition
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.base import _DOOR_REACH_M
from typehaus.resolve.cladding_trim.openings import SMALL_PENETRATION_M, is_profiled_metal_wall
from typehaus.resolve.cladding_trim.runs import covered_below, kit_faces, subtract_spans
from typehaus.resolve.metal_skin_profiles import PANEL_PROFILES
from typehaus.resolve.opening_flashing import opening_flashing_frame
from typehaus.takeoff.cladding_trim import cladding_trim_takeoff

COVERAGE = "integrity.cladding_trim_coverage"
_SIDES = ("HEAD", "SILL", "JAMB-LEFT", "JAMB-RIGHT")
_CORNER_RADIUS_M = 8 * M_PER_IN
_CATALOG_RIDGES = {"ridge:closed-cap", "ridge:image-ii-vented"}


def _pieces(model):
    return [solid for solid in model.solids if solid.category == "cladding_trim"]


def _window_like(ctx, pieces):
    """Four-side trim on every metal-wall window and every rough opening above a penetration."""
    model, findings, checked = ctx.model, [], 0
    for opening, wall in metal_wall_openings(model, kinds=("window", "rough_opening")):
        small = max(opening.width_m, opening.height_m) < SMALL_PENETRATION_M
        if opening.kind == "rough_opening" and small:
            findings.append(not_applicable(
                COVERAGE, "a penetration under 6 in is closed by its fixture's own flange",
                (opening.tag,)))
            continue
        frame = opening_flashing_frame(model, wall)
        seat = opening.window_seat
        if frame is None:
            findings.append(unknown(COVERAGE, "wall frame is unavailable", (opening.tag,)))
            continue
        low = opening.center_along_m - opening.width_m / 2
        bottom = wall.base_ref_z_m + opening.sill_m
        for side in _SIDES:
            selected = [p for p in pieces if p.host_ref == opening.tag
                        and f"-TRIM-{side}-" in p.tag]
            if not selected:
                findings.append(failed(COVERAGE, f"{opening.tag} lacks {side.lower()} trim",
                                       (opening.tag,)))
                continue
            if side.startswith("JAMB"):
                # A jamb stands on its sill's envelope, upstand included, not the sill datum.
                sill_top = max((z for p in pieces if p.host_ref == opening.tag
                                and "-TRIM-SILL-" in p.tag and p.body_mesh
                                for _, _, z in p.body_mesh.positions), default=bottom)
                top = bottom + opening.height_m - (seat.head_drop_m if seat else 0.0)
                ok = spans_cover(z_extent(selected), sill_top, top)
            else:
                ok = spans_cover(along_extent(selected, frame), low, low + opening.width_m)
            if not ok:
                findings.append(failed(COVERAGE, f"{opening.tag} {side.lower()} has a gap",
                                       (opening.tag,)))
        checked += 1
    if checked and not findings:
        findings.append(passed(COVERAGE, f"all four trim runs span {checked} metal-wall "
                                         "windows and rough openings"))
    return findings


def _doors(ctx, pieces):
    findings, checked = [], 0
    for opening, wall in metal_wall_openings(ctx.model, kinds=("door",)):
        problem = door_opening_trim(ctx.model, wall, opening, pieces)
        if problem is None:
            continue
        checked += 1
        if problem:
            findings.append(failed(COVERAGE, f"{opening.tag} {problem}", (opening.tag,)))
    if checked and not findings:
        findings.append(passed(COVERAGE, f"{checked} metal-wall doors carry both jambs and a "
                                         "head drip (or the band over a catalog unit)"))
    return findings


def _bases(ctx, pieces):
    model, findings, checked = ctx.model, [], 0
    entries = list(kit_faces(model, TrimCondition.BASE))
    faces = [face for face, _ in entries]
    for face, _ in entries:
        if covered_below(face, faces):
            continue
        cuts = [(a, b) for opening, a, b in face.openings(model)
                if face.wall.base_ref_z_m + opening.sill_m < face.z0 + _DOOR_REACH_M]
        needed = subtract_spans(face.lo, face.hi, cuts)
        mine = [p for p in pieces if p.tag.startswith(f"TRIM-{face.wall.tag}-BASE-")]
        spans = []
        for piece in mine:
            stations = [sum(c * d for c, d in zip(pt[:2], face.d, strict=True))
                        for pt in piece.body_mesh.positions]
            spans.append((min(stations), max(stations)))
        checked += 1
        if not all(spans_cover(spans, a, b) for a, b in needed):
            findings.append(failed(COVERAGE, f"{face.wall.tag} has a free panel bottom with no "
                                             "base trim", (face.wall.tag,)))
    if checked and not findings:
        findings.append(passed(COVERAGE, f"every free panel bottom ({checked} wall stacks) "
                                         "carries its kit's base trim"))
    return findings


def _corner_kit(model, materials, wall_tag):
    wall = model.wall(wall_tag)
    for layer in (wall.layers if wall else ()):
        material = materials.get(layer.material_ref)
        key = material.trim_kit.get(TrimCondition.OUTSIDE_CORNER) if material else None
        if layer.function == "cladding" and key:
            return key
    return None


def _corners_and_ends(ctx, pieces):
    model, findings = ctx.model, []
    materials = {m.tag: m for m in model.plan.library.materials}
    convex = 0
    for junction in model.junctions:
        if junction.kind != "l" or len(junction.incidents) != 2:
            continue
        if not all(_corner_kit(model, materials, i.wall_tag) for i in junction.incidents):
            continue
        near = [p for p in pieces if "CORNER" in p.tag and p.outline and math.dist(
            junction.point,
            (sum(x for x, _ in p.outline) / len(p.outline),
             sum(y for _, y in p.outline) / len(p.outline))) < _CORNER_RADIUS_M]
        convex += 1
        if not near and not _upper_storey_corner(model, junction):
            findings.append(failed(COVERAGE, f"corner {junction.node_tag} has no outside "
                                             "corner trim", (junction.node_tag,)))
    screens = {f.wall.tag for f, _ in kit_faces(model, TrimCondition.SCREEN_END)}
    for junction in model.junctions:
        for incident in junction.incidents if junction.kind == "open_end" else ():
            if incident.wall_tag in screens and not any(
                    p.tag.startswith(f"TRIM-{incident.wall_tag}-END-") for p in pieces):
                findings.append(failed(COVERAGE, f"{incident.wall_tag} has an open end with "
                                                 "no end trim", (incident.wall_tag,)))
    if convex and not findings:
        findings.append(passed(COVERAGE, f"{convex} outside corners and every screen end carry "
                                         "trim"))
    return findings


def _upper_storey_corner(model, junction) -> bool:
    """A stacked corner is trimmed once, by the run through its lowest storey."""
    return any(other is not junction and other.storey != junction.storey
               and other.kind == "l"
               and math.dist(other.point, junction.point) < 1e-6 for other in model.junctions)


def _roof_edges(ctx):
    model = ctx.model
    rows = [r for r in cladding_trim_takeoff(model) if r["kind"] == "roof"]
    tagged = {tag for r in rows for tag in r["tags"]}
    findings, runs = [], 0
    for roof in model.roofs:
        for member in roof.members:
            key = member.child_key
            if member.category == "drip_edge" and key.endswith("-drip-edge-face"):
                tag = f"{roof.tag}:{key[:-len('-drip-edge-face')]}"
            elif member.category == "corner_trim" and key.endswith("-panel-rake-face"):
                tag = f"{roof.tag}:{key.removesuffix('-panel-rake-face')}"
            elif member.category == "ridge_cap" and member.connection in _CATALOG_RIDGES:
                tag = f"{roof.tag}:{key}"
            else:
                continue
            runs += 1
            if tag not in tagged:
                findings.append(failed(COVERAGE, f"{tag} has no catalog roof-edge piece",
                                       (roof.tag,)))
    if runs and not findings:
        findings.append(passed(COVERAGE, f"{runs} Image II eave, rake and ridge runs "
                                         "map to catalog pieces"))
    return findings


def _wall_tops(ctx, pieces):
    """Check each exposed roof-terminated wall edge against the actual closure meshes."""
    from typehaus.resolve.cladding_trim.wall_tops import exposed_wall_top_edges

    findings, edges = [], exposed_wall_top_edges(ctx.model)
    finishes = {material.tag: material.finish for material in ctx.model.plan.library.materials}
    tolerance = 0.125 * M_PER_IN
    for edge in edges:
        spans = []
        for piece in pieces:
            if (piece.host_ref != edge.wall.tag or piece.product != edge.product
                    or not piece.body_mesh):
                continue
            points = piece.body_mesh.positions
            stations = [p[0]*edge.face.d[0] + p[1]*edge.face.d[1] for p in points]
            def error(p, station, edge=edge):
                expected = (edge.z_start + (edge.z_end-edge.z_start)
                            * (station-edge.start)/(edge.end-edge.start))
                return abs(p[2] - expected)
            throat = PROFILES[edge.product].receiver_throat_in if (
                edge.product == "CORRUGATED_SILL_TO_SOFFIT") else 0
            expected_depth = edge.face.back + throat * M_PER_IN
            depth = min(abs(p[0]*edge.face.n[0] + p[1]*edge.face.n[1] - expected_depth)
                        for p in points)
            elevation_error = min(error(p, s) for p, s in zip(points, stations, strict=True))
            if depth <= tolerance and elevation_error <= tolerance:
                spans.append((min(stations), max(stations)))
        # A rib fill stops at the end of its own (mitred) skin and finds no void under a
        # rib crown, so it may fall that much short of an end without leaving it open.
        skin = PANEL_PROFILES.get(finishes.get(edge.face.layer.material_ref))
        slack = max(edge.face.layer.thickness_m,
                    (skin.crown_width_m or 0.0) if skin is not None else 0.0)
        spans = [(lo - slack, hi + slack) for lo, hi in spans]
        if edge.end - edge.start > slack and not spans_cover(spans, edge.start, edge.end):
            findings.append(failed(
                COVERAGE, f"{edge.wall.tag} has an uncovered or displaced "
                f"{edge.condition.value} termination", (edge.wall.tag,)))
    if edges and not findings:
        findings.append(passed(COVERAGE, f"{len(edges)} exposed wall tops carry their closures"))
    return findings


@check(Tier.INTEGRITY, COVERAGE)
def cladding_trim_coverage(ctx: CheckContext) -> list:
    model = ctx.model
    if not [wall for wall in model.walls if is_profiled_metal_wall(model, wall)]:
        return [not_applicable(COVERAGE, "no profiled metal walls")]
    pieces = _pieces(model)
    findings = [*_window_like(ctx, pieces), *_doors(ctx, pieces), *_bases(ctx, pieces),
                *_corners_and_ends(ctx, pieces), *_roof_edges(ctx), *_wall_tops(ctx, pieces)]
    findings.append(unknown(
        COVERAGE,
        "the garage's vented ridge: Metal Sales publishes no part number for the 13 in step "
        "ridge cover, and the Cobra vented closure's net free area is unprinted",
        fix="ask Metal Sales for the 13 in step cover and Cobra closure part numbers and NFA "
            "(notes/metal_trim_kit.md)"))
    return findings
