"""Grade the fit of resolved trim against the rows it was selected from."""

from __future__ import annotations

import math
import re

from typehaus.checks.integrity.cladding_trim_runs import (
    along_extent,
    metal_wall_openings,
    spans_cover,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import failed, not_applicable, passed, unknown
from typehaus.library.trim._image_ii import IMAGE_II_RESIDENTIAL_RAKE
from typehaus.library.trim.metal_sales import PROFILES
from typehaus.model.cladding_trim import TrimCondition
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.openings import (
    brake_girth_and_bends,
    small_opening_seat,
    window_profile_sections,
)
from typehaus.resolve.cladding_trim.runs import kit_faces, metal_faces
from typehaus.resolve.opening_flashing import head_flashing_section, opening_flashing_frame
from typehaus.resolve.rainscreen_closures import (
    BUG_SCREEN_HEIGHT_IN,
    BUG_SCREEN_HOLE_IN,
    cavity_base_run,
    screens_rainscreen_base,
)
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
_MAX_HOLE_IN = 0.125
_FOUNDATION_MATCH_HEIGHT_M = 0.01
_FOUNDATION_MATCH_PLAN_M = 0.05
_FOUNDATION_MIN_OVERLAP_M = 0.01
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


def _base_cavity(ctx, pieces):
    """Where a rainscreen cavity opens at the base trim, it is screened and the trim stays out.

    The cavity bottom must be covered by perforation of 1/8 in or less; the base trim's back
    leg must sit on the cladding back plane, never inboard across the cavity mouth.
    """
    model, findings, checked = ctx.model, [], 0
    for wall in model.walls:
        run = cavity_base_run(model, wall)
        assembly = model.plan.library.resolve_assembly(wall.assembly)
        spec = assembly.rainscreen_base_flashing if assembly else None
        if run is None:
            continue
        if spec is None:
            from typehaus.resolve.cladding_trim.openings import is_profiled_metal_wall

            if is_profiled_metal_wall(model, wall):
                findings.append(failed(FIT, f"{wall.tag} screened cavity has no base flashing "
                                            "specification", (wall.tag,)))
            continue
        z_pieces = [p for p in pieces if p.host_ref == wall.tag
                    and p.product == "RAINSCREEN_BASE_Z" and p.body_mesh]
        isolation = [p for p in pieces if p.host_ref == wall.tag
                     and p.product == "EPDM_BASE_ISOLATION" and p.body_mesh]
        def spans(items, direction=run.direction):
            result = []
            for piece in items:
                stations = [x*direction[0] + y*direction[1]
                            for x, y, _ in piece.body_mesh.positions]
                result.append((min(stations), max(stations)))
            return result
        if not spans_cover(spans(z_pieces), run.start, run.end):
            findings.append(failed(FIT, f"{wall.tag} rainscreen base lacks continuous Z flashing",
                                   (wall.tag,)))
        if not spans_cover(spans(isolation), run.start, run.end):
            findings.append(failed(FIT, f"{wall.tag} lacks continuous aluminium/steel isolation",
                                   (wall.tag,)))
        elif any(abs(min(x*run.outward[0] + y*run.outward[1]
                         for x, y, _ in p.body_mesh.positions) - run.outer_offset) > _TOL
                 or abs(max(x*run.outward[0] + y*run.outward[1]
                            for x, y, _ in p.body_mesh.positions)
                        - run.outer_offset - spec.isolation_thickness.meters) > _TOL
                 for p in isolation):
            findings.append(failed(FIT, f"{wall.tag} isolation is displaced from the Z face",
                                   (wall.tag,)))
        elif any(abs(max(z for _, _, z in p.body_mesh.positions) - (
                wall.z0_m + spec.sheet_thickness.meters * (1 + spec.slope**2)**0.5
                - spec.slope * (run.outer_offset-run.inner_offset))) > _TOL
                 for p in isolation):
            findings.append(failed(FIT, f"{wall.tag} isolation is displaced above the Z face",
                                   (wall.tag,)))
        screen = next((s for s in model.solids if s.tag == f"{wall.tag}-BUGSCREEN"), None)
        if screen is None or screen.body_mesh is None:
            findings.append(failed(FIT, f"{wall.tag} Z flashing has no seated screen", (wall.tag,)))
        elif spec.upstand.meters + _TOL < BUG_SCREEN_HEIGHT_IN * M_PER_IN:
            findings.append(failed(FIT, f"{wall.tag} Z upstand is shorter than its screen",
                                   (wall.tag,)))
        elif z_pieces:
            # Compare the actual screen bottom to the specified pan surface, then check that
            # every piece still occupies that seat after model mutations.
            count = len(screen.body_mesh.positions) // 2
            for x, y, z in screen.body_mesh.positions[:count]:
                offset = x*run.outward[0] + y*run.outward[1]
                expected = (wall.z0_m + spec.sheet_thickness.meters * (1 + spec.slope**2)**0.5
                            - spec.slope * (offset - run.inner_offset))
                if abs(z - expected) > _TOL:
                    findings.append(failed(FIT, f"{wall.tag} screen is not seated on its Z",
                                           (wall.tag,)))
                    break
            pan_top = wall.z0_m + spec.sheet_thickness.meters * (1 + spec.slope**2)**0.5
            depth = run.outer_offset - run.inner_offset
            def point_near(piece, offset, z, run=run):
                return any(abs(x*run.outward[0] + y*run.outward[1] - offset) < _TOL
                           and abs(pz-z) < _TOL for x, y, pz in piece.body_mesh.positions)
            if any(not point_near(p, run.inner_offset, pan_top)
                   or not point_near(p, run.outer_offset, pan_top - depth*spec.slope)
                   or not point_near(p, run.inner_offset, pan_top + spec.upstand.meters)
                   for p in z_pieces):
                findings.append(failed(FIT, f"{wall.tag} Z is displaced from its bearing seat",
                                       (wall.tag,)))
        trim = [p for p in pieces if p.host_ref == wall.tag and p.body_mesh
                and p.tag.startswith(f"TRIM-{wall.tag}-BASE-")]
        if trim and min(x*run.outward[0] + y*run.outward[1]
                        for p in trim for x, y, _ in p.body_mesh.positions) < (
                            run.outer_offset + spec.isolation_thickness.meters - _TOL):
            findings.append(failed(FIT, f"{wall.tag} steel trim reaches the aluminium Z",
                                   (wall.tag,)))
        for foundation in model.walls:
            if (not foundation.is_foundation
                    or abs(foundation.z1_m-wall.z0_m) > _FOUNDATION_MATCH_HEIGHT_M):
                continue
            n, d = run.outward, run.direction
            gap = abs(sum((a-b)*c for a, b, c in zip(
                foundation.axis[0], wall.axis[0], n, strict=True)))
            stations = sorted(sum(a*b for a, b in zip(point, d, strict=True))
                              for point in foundation.axis)
            if (gap > _FOUNDATION_MATCH_PLAN_M
                    or min(stations[1], run.end)-max(stations[0], run.start)
                    <= _FOUNDATION_MIN_OVERLAP_M):
                continue
            offsets = [max(x*n[0]+y*n[1] for x, y in layer.polygon)
                       for layer in foundation.layers if layer.polygon
                       and layer.band(foundation)[1] >= wall.z0_m-_FOUNDATION_MATCH_HEIGHT_M]
            if offsets and max(offsets) >= run.outer_offset - _TOL:
                findings.append(failed(FIT, f"{wall.tag} Z drip does not clear the foundation face",
                                       (wall.tag, foundation.tag)))
    screens = {s.tag: s for s in model.solids if s.tag.endswith("-BUGSCREEN")}
    for face, _key in kit_faces(model, TrimCondition.BASE):
        wall = face.wall
        mine = [p for p in pieces if p.host_ref == wall.tag and p.tag.startswith("TRIM-")
                and "-BASE-" in p.tag and p.body_mesh]
        if not mine or not screens_rainscreen_base(model, wall):
            continue
        screen = screens.get(f"{wall.tag}-BUGSCREEN")
        if screen is None:
            findings.append(failed(FIT, f"{wall.tag} base trim closes a rainscreen cavity with "
                                        "no insect screen", (wall.tag,),
                                   code="metal_trim_kit.md, Wall base stack"))
            continue
        if BUG_SCREEN_HOLE_IN > _MAX_HOLE_IN:
            findings.append(failed(FIT, f"{wall.tag} cavity screen holes exceed 1/8 in",
                                   (wall.tag,), code="metal_trim_kit.md, Wall base stack"))
            continue
        mouth = max(x * face.n[0] + y * face.n[1] for x, y in screen.outline)
        leg = min(p[0] * face.n[0] + p[1] * face.n[1]
                  for piece in mine for p in piece.body_mesh.positions)
        if leg + _TOL < mouth:
            findings.append(failed(
                FIT, f"{wall.tag} base trim crosses the cavity mouth "
                     f"{(mouth - leg) / M_PER_IN:.2f} in", (wall.tag,),
                code="metal_trim_kit.md, Wall base stack"))
        else:
            checked += 1
    if checked and not findings:
        findings.append(passed(FIT, f"{checked} base trims leave a screened cavity mouth clear",
                               code="metal_trim_kit.md, Wall base stack"))
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
            *_base_cavity(ctx, pieces), *_rake_faces(ctx), *_band_laps(pieces),
            *_site_brake(ctx, pieces), *_soffit_panel_joint(ctx)]
