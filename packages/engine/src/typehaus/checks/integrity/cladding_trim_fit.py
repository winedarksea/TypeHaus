"""Grade the fit of resolved trim against the rows it was selected from."""

from __future__ import annotations

import math
import re

from typehaus.checks.integrity.cladding_trim_runs import (
    along_extent,
    metal_wall_openings,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import failed, not_applicable, passed, unknown
from typehaus.library.trim._image_ii import IMAGE_II_RESIDENTIAL_RAKE
from typehaus.library.trim.metal_sales import PROFILES
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.openings import (
    brake_girth_and_bends,
    small_opening_seat,
    window_profile_sections,
)
from typehaus.resolve.cladding_trim.runs import metal_faces
from typehaus.resolve.opening_flashing import head_flashing_section, opening_flashing_frame
from typehaus.resolve.rainscreen_closures import screens_rainscreen_base
from typehaus.resolve.roof_edge_geometry import roof_slope
from typehaus.resolve.roof_image_ii import CONNECTION_RAKE, RAKE_BELOW_HEAD_M
from typehaus.resolve.roof_layer_setbacks import above_structure_layers

FIT = "integrity.cladding_trim_fit"
_TOL = 1e-6
# The jamb's inboard flange reaches the frame face; the frame joint is a sealant line laid
# with the frame last (BBD75 pp. 24-26, "sealant (by others)"), so no lap width is required.
_MIN_FRAME_LAP_M = 0.0
_FRAME_JOINT_CITE = "BBD75 Install Guide 10/2025 pp. 24-26; PBR Install Guide 4/2024 p. 68"
# Site-brake gate: a 10'-6" hand brake bends flat 24 ga PVDF to 24 in girth and 4 bends.
_BRAKE_GIRTH_IN = 24.0
_BRAKE_BENDS = 4
# BBD75 p. 40: the Transition Trim's 2-1/2 in lower leg lies on the lower panel.
_BAND_LAP_M = 2.5 * M_PER_IN
_BAND_CITE = "BBD75 Install Guide 10/2025 p. 40"
_UPSTAND_MARGIN_M = 0.0625 * M_PER_IN
_BBD_RUN_LIMIT_M = 240 * M_PER_IN
_PBR_CITE = "PBR Install Guide 4/2024 pp. 19, 68-72"


def _opening_runs(ctx, pieces):
    model, findings = ctx.model, []
    checked = {"throat": 0, "lap": 0, "upstand": 0, "order": 0, "sill": 0}
    for opening, wall in metal_wall_openings(model, kinds=("window", "rough_opening")):
        seat, frame = opening.window_seat, opening_flashing_frame(model, wall)
        mine = [p for p in pieces if p.host_ref == opening.tag]
        if not mine or frame is None:
            continue
        cladding = next((layer for layer in wall.layers if layer.function == "cladding"), None)
        lo = opening.center_along_m - opening.width_m / 2
        hi = lo + opening.width_m
        reveal = frame.clad - frame.mount

        def part(name, mine=mine):
            return [p for p in mine if f"-TRIM-{name}" in p.tag and p.body_mesh]

        heads, sills = part("HEAD-"), part("SILL-")
        jambs = part("JAMB-LEFT-") + part("JAMB-RIGHT-")
        # Every receiver leg must clear the panel depth. Site-brake jambs carry no throat.
        for kind, piece in [("head", p) for p in heads] + [("jamb", p) for p in jambs]:
            profile = PROFILES.get(piece.product or "")
            if profile is None or profile.receiver_throat_in is None:
                if kind == "head":
                    findings.append(unknown(FIT, "head throat or panel depth unavailable",
                                            (opening.tag,)))
            elif cladding is None:
                findings.append(unknown(FIT, "head throat or panel depth unavailable",
                                        (opening.tag,)))
            elif profile.receiver_throat_in * M_PER_IN + _TOL < cladding.thickness_m:
                findings.append(failed(FIT, f"{opening.tag} {kind} throat is smaller than the "
                                            "panel depth", (opening.tag,), code=profile.source))
            else:
                checked["throat"] += 1
        # The jamb's inboard flange must reach the unit's frame face; the frame joint is sealed.
        for side, edge, inward in (("JAMB-LEFT-", lo, 1.0), ("JAMB-RIGHT-", hi, -1.0)):
            for jamb in part(side):
                stations = along_extent([jamb], frame)[0]
                reach = (stations[1] - edge) if inward > 0 else (edge - stations[0])
                lap = reach - (seat.jamb_inset_m if seat else 0.0)
                if lap + _TOL < _MIN_FRAME_LAP_M:
                    findings.append(failed(FIT, f"{opening.tag} jamb does not reach the frame "
                                                f"face ({lap / M_PER_IN:.2f} in)",
                                           (opening.tag,), code=_FRAME_JOINT_CITE))
                else:
                    checked["lap"] += 1
        bottom = wall.base_ref_z_m + opening.sill_m
        for sill in sills:
            top = max(point[2] for point in sill.body_mesh.positions) - bottom
            if seat and top > seat.sill_rise_m - _UPSTAND_MARGIN_M:
                findings.append(failed(FIT, f"{opening.tag} sill upstand reaches the unit",
                                       (opening.tag,), code="metal_trim_kit.md, Openings"))
            else:
                checked["upstand"] += 1
        # Jamb over sill: each jamb stands on the sill's envelope, upstand included.
        if sills and jambs:
            cap_top = max(p[2] for sill in sills for p in sill.body_mesh.positions)
            for jamb in jambs:
                if min(p[2] for p in jamb.body_mesh.positions) + _UPSTAND_MARGIN_M < cap_top:
                    findings.append(failed(FIT, f"{opening.tag} jamb ends below its sill cap",
                                           (opening.tag,), code=_FRAME_JOINT_CITE))
                else:
                    checked["sill"] += 1
        # Shingle order: the head's throat reaches further out than the jamb return it
        # laps, and the head runs past both jambs.
        if heads and part("JAMB-LEFT-") and reveal > 0:
            head_span = along_extent(heads, frame)
            head_depth = max(_depth(p, frame) for p in heads)
            jamb_depth = max(_depth(p, frame) for p in part("JAMB-LEFT-"))
            reaches = (min(s for s, _ in head_span) < lo - _TOL
                       and max(e for _, e in head_span) > hi + _TOL)
            if head_depth + _TOL < jamb_depth or not reaches:
                findings.append(failed(FIT, f"{opening.tag} head does not lap over its jambs",
                                       (opening.tag,), code="metal_trim_kit.md, Openings"))
            else:
                checked["order"] += 1
    notes = {"throat": "reveal legs and head throats clear the panel depth",
             "lap": "jamb flanges reach the frame face",
             "upstand": "sill upstands stay under the unit", "order": "heads lap over their jambs",
             "sill": "jambs land on their sill caps"}
    findings += [passed(FIT, f"{n} {notes[k]}", code=_PBR_CITE if k == "throat" else None)
                 for k, n in checked.items() if n and not any(
                     notes[k] in f.message for f in findings)]
    return findings


def _depth(piece, frame) -> float:
    return max(sum((p[i] - frame.origin[i]) * frame.outward[i] for i in range(2))
               for p in piece.body_mesh.positions)


def _run_limits(ctx, pieces):
    """No BBD75 panel run over 20 ft: the band splits each wall's height."""
    findings, checked = [], 0
    for face in metal_faces(ctx.model, {"board-and-batten"}):
        spec = _spec(ctx.model, face)
        joints = sorted(j.meters for j in spec.panel_joint_elevations) if spec else []
        top = max(_top_at(face.wall, face, point) for point in (face.lo, face.hi))
        edges = [face.z0, *[j for j in joints if face.z0 < j < top], top]
        for low, high in zip(edges, edges[1:], strict=False):
            checked += 1
            if high - low > _BBD_RUN_LIMIT_M + _TOL:
                findings.append(failed(
                    FIT, f"{face.wall.tag} has a {(high - low) / M_PER_IN / 12:.1f} ft BBD75 run, "
                         "over the 20 ft panel maximum", (face.wall.tag,),
                    code="BBD75 Install Guide 10/2025"))
    for piece in pieces:
        profile = PROFILES.get(piece.product or "")
        if profile and piece.trim_length_m and piece.trim_stock_length_in and (
                piece.trim_length_m > piece.trim_stock_length_in * M_PER_IN + _TOL):
            findings.append(failed(FIT, f"{piece.tag} is cut longer than its stock",
                                   (piece.tag,)))
    if checked and not findings:
        findings.append(passed(FIT, f"{checked} BBD75 panel runs stay within 20 ft and every "
                                    "trim cut within its stock length",
                               code="BBD75 Install Guide 10/2025"))
    return findings


def _spec(model, face):
    wall = face.wall
    assembly = model.plan.library.resolve_assembly(wall.assembly) if wall.assembly else None
    return next((layer for layer in (assembly.layers if assembly else ())
                 if layer.name == face.layer.name), None)


def _top_at(wall, face, station):
    from typehaus.resolve.geometry_walls import wall_top_at

    x, y = face.xy(station)
    return min(face.z1, wall_top_at(wall, x, y))


def _door_heads(ctx, pieces):
    """A door's head drip stands clear of its casing face."""
    model, findings, checked = ctx.model, [], 0
    for opening, wall in metal_wall_openings(model, kinds=("door",)):
        heads = [p for p in pieces if p.host_ref == opening.tag and "-TRIM-HEAD-" in p.tag]
        frame = opening_flashing_frame(model, wall, opening)
        if not heads or frame is None:
            continue
        section = head_flashing_section(wall, opening, frame)
        placement = opening.doorway.exterior_placement if opening.doorway else None
        casing = placement.specification.casing_thickness.meters if placement else 0.0
        checked += 1
        if section.front + _TOL < frame.clad + casing:
            findings.append(failed(FIT, f"{opening.tag} head drip does not clear the casing",
                                   (opening.tag,)))
    if checked and not findings:
        findings.append(passed(FIT, f"{checked} door head drips clear their casings"))
    return findings


def _rake_faces(ctx):
    """The stock rake's leg covers the roofing above the wall head plus the 1 in below it."""
    model, findings, rakes = ctx.model, [], []
    stock_in = max(z for _, z in IMAGE_II_RESIDENTIAL_RAKE.section_in)
    for roof in model.roofs:
        members = [m for m in roof.members if m.connection == CONNECTION_RAKE]
        if not members:
            continue
        layers = above_structure_layers(model.plan.library.resolve_assembly(roof.assembly))
        roofing = next(layer for layer in layers if layer.name == "roofing")
        stack_in = roofing.thickness.meters * math.hypot(1.0, roof_slope(roof)) / M_PER_IN
        required_in = stack_in + RAKE_BELOW_HEAD_M / M_PER_IN
        rakes.append((roof.tag, len(members), required_in))
        if required_in > stock_in + 1e-6:
            findings.append(failed(
                FIT, f"{roof.tag} rake needs {required_in:.2f} in of leg over the roofing and "
                     f"hem, past the stock 52126XX's {stock_in:.3f} in",
                (roof.tag,), code="Residential Design Manual 5/2024 p. 9"))
    if rakes and not findings:
        tags = ", ".join(f"{tag} ({count} runs)" for tag, count, _ in rakes)
        findings.append(passed(
            FIT, f"stock rake 52126XX leg {stock_in:.3f} in covers the roofing and 1 in below "
                 f"the head ({max(r for *_, r in rakes):.2f} in needed) on {tags}",
            code="Residential Design Manual 5/2024 p. 9"))
    return findings


def _band_laps(pieces):
    """Each BBD75 band's lower leg lies on the lower panel by the manual's 2-1/2 in."""
    lower = {}
    for piece in pieces:
        match = re.search(r"-BAND-(\d+)-", piece.tag)
        if piece.product != "BBD_TRANSITION" or match is None or not piece.body_mesh:
            continue
        joint = int(match.group(1)) * M_PER_IN
        depth = joint - min(p[2] for p in piece.body_mesh.positions)
        key = (piece.host_ref, match.group(1))
        lower[key] = min(lower.get(key, depth), depth)
    short = [key for key, depth in lower.items() if depth + _TOL < _BAND_LAP_M]
    if short:
        return [failed(FIT, f"{len(short)} band joints lap the lower panel under 2-1/2 in",
                       tuple(sorted({wall for wall, _ in short})), code=_BAND_CITE)]
    if lower:
        return [passed(FIT, f"{len(lower)} band joints lap the lower panel 2-1/2 in",
                       code=_BAND_CITE)]
    return []


def _site_brake(ctx, pieces):
    """Every site-brake section fits the 10'-6 in hand brake: 24 in girth, four bends."""
    model, sections = ctx.model, []
    for opening, wall in metal_wall_openings(model, kinds=("window", "rough_opening")):
        frame = opening_flashing_frame(model, wall)
        products = {p.product for p in pieces if p.host_ref == opening.tag}
        if frame is None or not products & {"WINDOW_JAMB_CUSTOM", "WINDOW_SILL_CUSTOM"}:
            continue
        jamb, sill = window_profile_sections(frame, opening.window_seat or small_opening_seat())
        if "WINDOW_JAMB_CUSTOM" in products:
            sections.append((opening.tag, "jamb", jamb))
        if "WINDOW_SILL_CUSTOM" in products:
            sections.append((opening.tag, "sill", sill))
    for opening, wall in metal_wall_openings(model, kinds=("door",)):
        frame = opening_flashing_frame(model, wall, opening)
        if frame is None or not any(p.host_ref == opening.tag and p.product == "DOOR_HEAD_CUSTOM"
                                    for p in pieces):
            continue
        head = head_flashing_section(wall, opening, frame)
        sections.append((opening.tag, "door head", [(x / M_PER_IN, z / M_PER_IN)
                                                    for x, z in head.points]))
    findings = []
    for tag, name, points in sections:
        girth, bends = brake_girth_and_bends(points)
        if girth > _BRAKE_GIRTH_IN or bends > _BRAKE_BENDS:
            findings.append(failed(FIT, f"{tag} {name} is {girth:.1f} in girth with {bends} "
                                        "bends, over the 10'-6 in hand brake",
                                   (tag,), code="metal_trim_kit.md, Openings"))
    if sections and not findings:
        findings.append(passed(FIT, f"{len(sections)} site-brake sections fit a 10'-6 in hand "
                                    "brake: 24 in girth, four bends or fewer",
                               code="metal_trim_kit.md, Openings"))
    return findings


def _soffit_panel_joint(ctx):
    """A soffit attachment crosses the modeled continuous wall panel at its head joint."""
    runs = []
    for solid in ctx.model.solids:
        if solid.product != "CORRUGATED_SILL_TO_SOFFIT":
            continue
        wall = ctx.model.wall(solid.host_ref)
        if wall is None:
            continue
        if any(layer.function == "cladding" and layer.band(wall)[0] < solid.z0_m
               and layer.band(wall)[1] > solid.z0_m for layer in wall.layers):
            runs.append(solid)
    if not runs:
        return []
    return [unknown(
        FIT, "corrugated Sill to Soffit meets a wall panel modeled continuously through "
        "the soffit height; its physical panel break and installation order are not resolved",
        tuple(sorted({s.host_ref for s in runs if s.host_ref})),
        code="Corrugated manual p. P7/8-4",
        fix="coordinate the panel break and soffit attachment before grading this junction")]


@check(Tier.INTEGRITY, FIT)
def cladding_trim_fit(ctx: CheckContext) -> list:
    model = ctx.model
    pieces = [solid for solid in model.solids if solid.category == "cladding_trim"]
    if not pieces and not any(screens_rainscreen_base(model, wall) for wall in model.walls):
        return [not_applicable(FIT, "no catalog cladding trim resolved")]
    return [*_opening_runs(ctx, pieces), *_run_limits(ctx, pieces), *_door_heads(ctx, pieces),
            *_rake_faces(ctx), *_band_laps(pieces),
            *_site_brake(ctx, pieces), *_soffit_panel_joint(ctx)]
