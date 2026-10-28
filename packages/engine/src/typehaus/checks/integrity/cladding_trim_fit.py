"""Grade the fit of resolved trim against the rows it was selected from."""

from __future__ import annotations

from typehaus.checks.integrity.cladding_trim_runs import along_extent, metal_wall_openings
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import failed, not_applicable, passed, unknown
from typehaus.library.trim.metal_sales import PROFILES, RESIDENTIAL_RAKE_FACE_IN
from typehaus.model.cladding_trim import TrimCondition
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.runs import kit_faces, metal_faces
from typehaus.resolve.opening_flashing import head_flashing_section, opening_flashing_frame
from typehaus.resolve.rainscreen_closures import BUG_SCREEN_HOLE_IN, screens_rainscreen_base

FIT = "integrity.cladding_trim_fit"
_TOL = 1e-6
_MIN_FRAME_LAP_M = 0.75 * M_PER_IN
_UPSTAND_MARGIN_M = 0.0625 * M_PER_IN
_BBD_RUN_LIMIT_M = 240 * M_PER_IN
_MAX_HOLE_IN = 0.125
_PBR_CITE = "PBR Install Guide 4/2024 pp. 19, 68-72"


def _opening_runs(ctx, pieces):
    model, findings, checked = ctx.model, [], {"throat": 0, "lap": 0, "upstand": 0, "order": 0}
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
        for head in heads:
            profile = PROFILES.get(head.product or "")
            if cladding is None or profile is None or profile.receiver_throat_in is None:
                findings.append(unknown(FIT, "head throat or panel depth unavailable",
                                        (opening.tag,)))
            elif profile.receiver_throat_in * M_PER_IN + _TOL < cladding.thickness_m:
                findings.append(failed(FIT, f"{opening.tag} head throat is smaller than the "
                                            "panel depth", (opening.tag,), code=profile.source))
            else:
                checked["throat"] += 1
        # The jamb's inboard leg must lap the unit's frame face.
        for side, edge, inward in (("JAMB-LEFT-", lo, 1.0), ("JAMB-RIGHT-", hi, -1.0)):
            for jamb in part(side):
                stations = along_extent([jamb], frame)[0]
                reach = (stations[1] - edge) if inward > 0 else (edge - stations[0])
                lap = reach - (seat.jamb_inset_m if seat else 0.0)
                if lap + _TOL < _MIN_FRAME_LAP_M:
                    findings.append(failed(FIT, f"{opening.tag} jamb laps the frame "
                                                f"{lap / M_PER_IN:.2f} in, under 3/4 in",
                                           (opening.tag,), code="metal_trim_kit.md, Openings"))
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
    notes = {"throat": "head throats clear the panel depth", "lap": "jamb frame laps reach 3/4 in",
             "upstand": "sill upstands stay under the unit", "order": "heads lap over their jambs"}
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
    """Where the stock 2-5/8 in rake leg covers the face; where not, the custom 4 in is UNKNOWN."""
    findings, custom = [], []
    for roof in ctx.model.roofs:
        for member in roof.members:
            key = member.child_key
            if (member.category == "drip_edge" and key.startswith("rake")
                    and key.endswith("-drip-edge-face") and roof.tag != "RF-HOUSE") or (
                    member.category == "corner_trim" and key.endswith("-panel-rake-face")):
                face = (member.z1_m - member.z0_m) / M_PER_IN
                if face > RESIDENTIAL_RAKE_FACE_IN + 1e-6:
                    custom.append(f"{roof.tag}:{key}")
    if custom:
        findings.append(unknown(
            FIT, f"{len(custom)} rake runs need a 4 in face; the stock Residential Rake 52126XX "
                 f"covers {RESIDENTIAL_RAKE_FACE_IN} in, so they are billed as a custom-brake "
                 "extension of its main leg, whose fabrication Metal Sales has not confirmed",
            tuple(sorted(custom)[:4]), code="Residential Design Manual 5/2024 p. 9",
            fix="get the 4 in rake and the custom jamb/sill/head brake limits in writing"))
    return findings


@check(Tier.INTEGRITY, FIT)
def cladding_trim_fit(ctx: CheckContext) -> list:
    model = ctx.model
    pieces = [solid for solid in model.solids if solid.category == "cladding_trim"]
    if not pieces:
        return [not_applicable(FIT, "no catalog cladding trim resolved")]
    return [*_opening_runs(ctx, pieces), *_run_limits(ctx, pieces), *_door_heads(ctx, pieces),
            *_base_cavity(ctx, pieces), *_rake_faces(ctx)]
