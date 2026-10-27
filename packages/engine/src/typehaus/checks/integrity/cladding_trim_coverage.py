"""Grade modeled window trim spans and report the remaining coverage gaps."""

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import failed, not_applicable, passed, unknown
from typehaus.library.trim.metal_sales import PROFILES
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.openings import is_profiled_metal_wall
from typehaus.resolve.opening_flashing import opening_flashing_frame

_COVERAGE = "integrity.cladding_trim_coverage"
_FIT = "integrity.cladding_trim_fit"
_TOLERANCE_M = 1e-6
_SIDES = ("HEAD", "SILL", "JAMB-LEFT", "JAMB-RIGHT")


def _spans_cover(spans, start, end):
    cursor = start
    for low, high in sorted(spans):
        if high < cursor - _TOLERANCE_M:
            continue
        if low > cursor + _TOLERANCE_M:
            return False
        cursor = max(cursor, high)
    return cursor >= end - _TOLERANCE_M


def _windows(model):
    for opening in model.openings:
        if opening.kind != "window":
            continue
        wall = model.wall(opening.host_wall)
        if wall is not None and is_profiled_metal_wall(model, wall):
            yield opening, wall


@check(Tier.INTEGRITY, _COVERAGE)
def cladding_trim_coverage(ctx: CheckContext) -> list:
    model = ctx.model
    walls = [wall for wall in model.walls if is_profiled_metal_wall(model, wall)]
    if not walls:
        return [not_applicable(_COVERAGE, "no profiled metal walls")]
    pieces = [solid for solid in model.solids if solid.category == "cladding_trim"]
    findings = []
    checked = 0
    for opening, wall in _windows(model):
        frame = opening_flashing_frame(model, wall)
        seat = opening.window_seat
        if frame is None or seat is None:
            findings.append(unknown(_COVERAGE, "window seat or wall frame is unavailable",
                                    (opening.tag,)))
            continue
        low = opening.center_along_m - opening.width_m / 2
        high = low + opening.width_m
        bottom = wall.base_ref_z_m + opening.sill_m
        top = bottom + opening.height_m - seat.head_drop_m
        for side in _SIDES:
            selected = [piece for piece in pieces if piece.host_ref == opening.tag
                        and f"-TRIM-{side}-" in piece.tag]
            if not selected:
                findings.append(failed(_COVERAGE, f"{opening.tag} lacks {side.lower()} trim",
                                       (opening.tag,)))
                continue
            if any(piece.body_mesh is None or not piece.body_mesh.positions for piece in selected):
                findings.append(unknown(_COVERAGE, f"{opening.tag} {side.lower()} has no mesh",
                                        (opening.tag,)))
                continue
            if side.startswith("JAMB"):
                spans = [(min(point[2] for point in piece.body_mesh.positions),
                          max(point[2] for point in piece.body_mesh.positions)) for piece in selected]
                expected = (bottom, top)
            else:
                def station(point):
                    return sum((point[i] - frame.origin[i]) * frame.along[i] for i in range(2))
                spans = [(min(map(station, piece.body_mesh.positions)),
                          max(map(station, piece.body_mesh.positions))) for piece in selected]
                expected = (low, high)
            if not _spans_cover(spans, *expected):
                findings.append(failed(_COVERAGE, f"{opening.tag} {side.lower()} has a gap",
                                       (opening.tag,)))
        checked += 1
    if checked and not findings:
        findings.append(passed(_COVERAGE, f"all four trim runs span {checked} metal-wall windows"))
    findings.append(unknown(_COVERAGE,
        "complete wall-edge, door, small-opening and roof coverage is not yet graded; "
        "window span checks do not establish weatherproofing"))
    return findings


@check(Tier.INTEGRITY, _FIT)
def cladding_trim_fit(ctx: CheckContext) -> list:
    model = ctx.model
    windows = list(_windows(model))
    if not windows:
        return [not_applicable(_FIT, "no profiled metal wall windows")]
    pieces = [solid for solid in model.solids if solid.category == "cladding_trim"]
    findings = []
    checked = 0
    for opening, wall in windows:
        heads = [piece for piece in pieces if piece.host_ref == opening.tag
                 and "-TRIM-HEAD-" in piece.tag]
        if not heads:
            findings.append(unknown(_FIT, "no modeled head trim to grade", (opening.tag,)))
            continue
        cladding = next((layer for layer in wall.layers if layer.function == "cladding"), None)
        for head in heads:
            profile = PROFILES.get(head.product or "")
            if cladding is None or profile is None or profile.receiver_throat_in is None:
                findings.append(unknown(_FIT, "head throat or panel depth unavailable", (opening.tag,)))
                continue
            checked += 1
            if profile.receiver_throat_in * M_PER_IN + _TOLERANCE_M < cladding.thickness_m:
                findings.append(failed(_FIT, f"{opening.tag} head throat is smaller than the panel depth",
                                       (opening.tag,), code=profile.source))
    if checked and not findings:
        findings.append(passed(_FIT, f"{checked} window head throats clear the nominal panel depth",
                               code="PBR Install Guide 4/2024 pp. 19, 68–72"))
    findings.append(unknown(_FIT, "frame laps, sill upstands, lap order, panel lengths and "
                            "door-head clearance are not yet graded from installed geometry"))
    return findings
