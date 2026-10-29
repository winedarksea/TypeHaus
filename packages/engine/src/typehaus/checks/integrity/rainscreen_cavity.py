"""The rainscreen cavity drains, vents and is insect-tight at its base, heads and band.

Base: an open air and water path under the raised steel trim, through a screen of 1/8" holes,
at the net free area DIN 18516-1 asks of an inlet; no KDAT on the aluminium; the Z, screen
and EPDM where the detail puts them. Heads: a cap floors the cavity and drains over the head
trim. Band: the BBD75 outlet strip's net free area. Everywhere a panel end opens its voids
into the cavity, it sits on a perforated strip (``notes/metal_trim_kit.md``). Hole size and
open fraction are read off the screen's Material. The slot is graded off the trim and EPDM;
the panel surface is not a resolved piece, so a panel drawn through the trim foot is unseen.
"""

from __future__ import annotations

from typehaus.checks.integrity.cladding_trim_runs import spans_cover
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import failed, not_applicable, passed, unknown
from typehaus.quantities import M_PER_IN
from typehaus.resolve.rainscreen_closures import (
    BASE_SCREEN_PRODUCT,
    BUG_SCREEN_HEIGHT_IN,
    MIN_NET_FREE_AREA_CM2_PER_M,
    base_flashing_spec,
    cavity_base_run,
    net_free_area_cm2_per_m,
    opening_head_spans,
    pan_top_z,
    screens_rainscreen_base,
)
from typehaus.resolve.rainscreen_strips import (
    BAND_OUTLET_PRODUCT,
    STRIP_PRODUCT,
    band_screen_spans,
)

CAVITY = "integrity.rainscreen_cavity"
_TOL = 1e-6
_MAX_HOLE_IN = 0.125
_CITE = "metal_trim_kit.md, Wall base stack; DIN 18516-1 (50 cm2/m)"
_HEAD_CITE = "opening_flashing_spec.md §4; IRC R703.4"
#: Categories of the girt band's wood: the girts, the blocks, the head and sill courses.
_GIRT_WOOD = {"strapping", "truss_block", "truss_blocking"}
_ALUMINIUM = {"RAINSCREEN_BASE_Z", BASE_SCREEN_PRODUCT, STRIP_PRODUCT, BAND_OUTLET_PRODUCT}


def _offsets(piece, n):
    return [x * n[0] + y * n[1] for x, y, _ in piece.body_mesh.positions]


def _along(piece, d):
    stations = [x * d[0] + y * d[1] for x, y, _ in piece.body_mesh.positions]
    return min(stations), max(stations)


def _mine(model, host, products):
    return [s for s in model.solids if s.host_ref == host and s.product in products
            and s.body_mesh is not None]


def perforation(model, pieces):
    """``(hole in, open fraction)`` authored on the pieces' Material, or None if unstated."""
    tags = {p.material for p in pieces}
    if len(tags) != 1:
        return None
    material = model.plan.library.material(next(iter(tags)) or "")
    if material is None or material.perforation_hole_in is None \
            or material.open_area_fraction is None:
        return None
    return material.perforation_hole_in, material.open_area_fraction


def _unstated(tag, what):
    return unknown(CAVITY, f"{tag}: the {what} Material states no perforation_hole_in and "
                   "open_area_fraction, so its insect-tightness and net free area are unread",
                   (tag,), code=_CITE)


def _base(model):
    findings, graded, areas, boxed = [], 0, [], []
    for wall in model.walls:
        run = cavity_base_run(model, wall)
        if run is None:
            continue
        spec = base_flashing_spec(model, wall)
        if spec is None:
            from typehaus.resolve.cladding_trim.openings import is_profiled_metal_wall

            if is_profiled_metal_wall(model, wall):
                findings.append(failed(CAVITY, f"{wall.tag} screened cavity has no base "
                                       "flashing specification", (wall.tag,), code=_CITE))
            else:
                boxed.append(wall.tag)
            continue
        before = len(findings)
        findings += _base_wall(model, wall, run, spec, areas)
        graded += len(findings) == before
    if boxed:
        findings.append(unknown(CAVITY, f"{len(boxed)} screened cavity bases have no "
                                "RainscreenBaseFlashing, so their drainage and vent path are "
                                "not graded", tuple(boxed), code=_CITE))
    if graded and not any(f.result.name == "FAIL" for f in findings):
        findings.append(passed(CAVITY, f"{graded} cavity bases drain and breathe through a "
                               "screened slot under the raised base trim (net free area "
                               f"{min(areas):.0f} cm2/m or more)", code=_CITE))
    return findings


def _base_wall(model, wall, run, spec, areas):
    out, tag, n, d = [], wall.tag, run.outward, run.direction

    def fail(message, fix=None):
        out.append(failed(CAVITY, f"{tag}: {message}", (tag,), code=_CITE, fix=fix))

    z_pieces = _mine(model, tag, {"RAINSCREEN_BASE_Z"})
    screens = _mine(model, tag, {BASE_SCREEN_PRODUCT})
    epdm = _mine(model, tag, {"EPDM_BASE_ISOLATION"})
    trim = [s for s in model.solids if s.host_ref == tag and s.body_mesh is not None
            and s.tag.startswith(f"TRIM-{tag}-BASE-")]
    if not spans_cover([_along(p, d) for p in z_pieces], run.start, run.end):
        fail("the cavity has no continuous Z flashing to drain it")
    if not spans_cover([_along(p, d) for p in screens], run.start, run.end):
        fail("the cavity base is open to insects: no continuous insect screen")
        return out
    holes = perforation(model, screens)
    if holes is None:
        out.append(_unstated(tag, "base screen"))
        return out
    if holes[0] > _MAX_HOLE_IN:
        fail(f"insects pass the screen's {holes[0]:.3f} in holes (over 1/8 in)")
    if spec.upstand.meters + _TOL < BUG_SCREEN_HEIGHT_IN * M_PER_IN:
        fail("the Z upstand is shorter than the screen it holds")
    outer_pan = pan_top_z(wall, spec, run, run.outer_offset)
    if any(abs(min(z for *_, z in p.body_mesh.positions) - outer_pan) > _TOL for p in screens):
        fail("the screen is not seated on its Z pan")
    for piece in z_pieces:
        points = [(x * n[0] + y * n[1], z) for x, y, z in piece.body_mesh.positions]
        inner = pan_top_z(wall, spec, run, run.inner_offset)
        if not (any(abs(o - run.inner_offset) < _TOL and abs(z - inner) < _TOL
                    for o, z in points)
                and any(abs(o - run.outer_offset) < _TOL and abs(z - outer_pan) < _TOL
                        for o, z in points)):
            fail("the Z is displaced from its bearing seat")
            break
    if not trim:
        return out
    trim_offsets = [o for p in trim for o in _offsets(p, n)]
    if min(trim_offsets) < run.outer_offset + spec.isolation_thickness.meters - _TOL:
        fail("the steel base trim reaches the aluminium (no EPDM between them)")
    leg = run.outer_offset + spec.isolation_thickness.meters + 0.05 * M_PER_IN
    foot = min(z for p in trim for x, y, z in p.body_mesh.positions
               if x * n[0] + y * n[1] <= leg)
    exposed = foot  # the screen's outer leg breathes from the pan up to the lap
    if not spans_cover([_along(p, d) for p in epdm], run.start, run.end):
        fail("no continuous EPDM where the steel trim laps the screen")
    else:
        e_off = [o for p in epdm for o in _offsets(p, n)]
        e_z = [z for p in epdm for *_, z in p.body_mesh.positions]
        if (abs(min(e_off) - run.outer_offset) > _TOL
                or abs(max(e_off) - run.outer_offset - spec.isolation_thickness.meters) > _TOL
                or abs(min(e_z) - wall.z0_m - spec.trim_rise.meters) > _TOL
                or max(e_z) < foot + _TOL):
            fail("the EPDM is displaced from the trim's lap on the screen")
        exposed = min(e_z)
    open_height = exposed - outer_pan
    area = net_free_area_cm2_per_m(open_height, holes[1])
    areas.append(area)
    if foot - outer_pan <= _TOL or open_height <= _TOL:
        fail("the base trim dams the pan edge: no open slot for air or water under it",
             fix="raise the base trim foot off the seat (RainscreenBaseFlashing.trim_rise)")
    elif area + 1e-9 < MIN_NET_FREE_AREA_CM2_PER_M:
        fail(f"the cavity cannot breathe: {open_height / M_PER_IN:.2f} in of open screen is "
             f"{area:.0f} cm2/m net free area, under {MIN_NET_FREE_AREA_CM2_PER_M:.0f}")
    out += _foundation_clear(model, wall, run)
    return out


def _kdat(model):
    findings, graded = [], 0
    for wall in model.walls:
        found = _kdat_on_aluminium(model, wall)
        graded += found is not None
        findings += found or []
    if graded and not findings:
        findings.append(passed(CAVITY, f"no girt-band KDAT touches the aluminium on {graded} "
                               "walls", code="AWC DCA6"))
    return findings


def _kdat_on_aluminium(model, wall):
    """Treated wood on aluminium corrodes it (AWC DCA6): no girt-band wood may touch any
    aluminium piece on the wall or its openings (the base Z and U, every strip)."""
    from shapely.geometry import MultiPoint, Polygon

    from typehaus.resolve.framing.footprint import member_footprint

    hosts = {wall.tag} | {o.tag for o in model.openings if o.host_wall == wall.tag}
    metal = [s for s in model.solids if s.host_ref in hosts and s.product in _ALUMINIUM
             and s.body_mesh is not None]
    wood = [m for m in wall.members if m.category in _GIRT_WOOD and m.material == "kdat"]
    if not metal or not wood:
        return None
    shapes = []
    for piece in metal:
        zs = [z for *_, z in piece.body_mesh.positions]
        hull = MultiPoint([(x, y) for x, y, _ in piece.body_mesh.positions]).convex_hull
        shapes.append((piece, hull, min(zs), max(zs)))
    for member in wood:
        ring, z_lo, z_hi = member_footprint(member)
        plan = Polygon(ring)
        for piece, hull, bottom, top in shapes:
            # Touching counts: wood resting on the metal is the contact this forbids.
            if z_lo > top + _TOL or z_hi < bottom - _TOL or plan.distance(hull) > _TOL:
                continue
            return [failed(CAVITY, f"{wall.tag}: KDAT {member.child_key} bears on aluminium "
                           f"{piece.tag}", (wall.tag,), code="AWC DCA6",
                           fix="raise the starter girt (RainscreenBaseFlashing.starter_rise) "
                               "or hold the strip off the wood")]
    return []


def _foundation_clear(model, wall, run):
    n, d = run.outward, run.direction
    for foundation in model.walls:
        if not foundation.is_foundation or abs(foundation.z1_m - wall.z0_m) > 0.01:
            continue
        gap = abs(sum((a - b) * c for a, b, c in zip(
            foundation.axis[0], wall.axis[0], n, strict=True)))
        stations = sorted(sum(a * b for a, b in zip(point, d, strict=True))
                          for point in foundation.axis)
        if gap > 0.05 or min(stations[1], run.end) - max(stations[0], run.start) <= 0.01:
            continue
        offsets = [max(x * n[0] + y * n[1] for x, y in layer.polygon)
                   for layer in foundation.layers if layer.polygon
                   and layer.band(foundation)[1] >= wall.z0_m - 0.01]
        if offsets and max(offsets) >= run.outer_offset - _TOL:
            return [failed(CAVITY, f"{wall.tag}: the Z drip does not clear the foundation "
                           "face", (wall.tag, foundation.tag), code=_CITE)]
    return []


def _heads(model):
    from typehaus.resolve.opening_flashing import opening_flashing_frame
    from typehaus.resolve.opening_head_cap import CAP_HEAD_LAP_IN, CAP_PRODUCT, head_cap

    findings, graded, bare = [], 0, []
    for wall in model.walls:
        for opening, s0, s1, _z in opening_head_spans(model, wall):
            head = {s.product for s in model.solids if s.host_ref == opening.tag
                    and s.product in ("OPENING_HEAD", "DOOR_HEAD_CUSTOM")}
            if not head:
                bare.append(opening.tag)  # a catalog unit's head (a hold point), or no kit
                continue
            frame = opening_flashing_frame(model, wall, opening)
            tag, d = opening.tag, frame.along
            before = len(findings)
            if "OPENING_HEAD" in head:
                caps = _mine(model, tag, {CAP_PRODUCT})
                cap = head_cap(model, wall, opening, frame)
                lo, hi = (frame.point(s, 0, 0) for s in (s0, s1))
                span = sorted(x * d[0] + y * d[1] for x, y, _ in (lo, hi))
                if not caps or not spans_cover([_along(p, d) for p in caps], *span):
                    findings.append(failed(CAVITY, f"{tag}: the cavity over the head has no "
                                           "cap to floor and drain it", (tag,), code=_HEAD_CITE))
                elif cap is None or min(z for p in caps for *_, z in p.body_mesh.positions) \
                        > cap.head_trim_top - CAP_HEAD_LAP_IN * M_PER_IN + 0.05 * M_PER_IN:
                    findings.append(failed(CAVITY, f"{tag}: the head cap's face leg does not "
                                           "lap the head trim by 1 in", (tag,), code=_HEAD_CITE))
            if not _mine(model, tag, {STRIP_PRODUCT}):
                findings.append(failed(CAVITY, f"{tag}: the panel end over the head opens its "
                                       "voids to insects (no perforated strip)", (tag,),
                                       code=_HEAD_CITE))
            graded += len(findings) == before
    if bare:
        findings.append(unknown(CAVITY, f"no kit head trim over {len(bare)} cavity head(s), "
                                "so no cap or strip is derived there (a catalog unit's head "
                                "is a hold point)", tuple(bare), code=_HEAD_CITE))
    if graded and not any(f.result.name == "FAIL" for f in findings):
        findings.append(passed(CAVITY, f"{graded} window and door heads are capped, drain "
                               "over their trim, and seat their panel end on a strip",
                               code=_HEAD_CITE))
    return findings


def _panel_end_strips(model):
    """Every free panel end over a screened base sits on a strip."""
    from typehaus.resolve.cladding_trim.base import base_trim_spans

    findings, graded = [], 0
    for face, _key, span, lo, hi, _z, _depth in base_trim_spans(model):
        wall = face.wall
        if not screens_rainscreen_base(model, wall):
            continue
        graded += 1
        strips = [s for s in _mine(model, wall.tag, {STRIP_PRODUCT})
                  if s.tag.startswith(f"{wall.tag}-BASESTRIP-S{span}-")]
        if not spans_cover([_along(p, face.d) for p in strips], lo, hi):
            findings.append(failed(CAVITY, f"{wall.tag}: the panel end at the base opens its "
                                   "voids to insects (no perforated strip)", (wall.tag,),
                                   code=_CITE))
    if graded and not findings:
        findings.append(passed(CAVITY, f"{graded} base panel-end runs seat on a perforated "
                               "strip", code=_CITE))
    return findings


def _band(model):
    from typehaus.resolve.cladding_trim.runs import cladding_face

    findings, graded, areas = [], 0, []
    for wall in model.walls:
        spans = band_screen_spans(model, wall)
        if not spans:
            continue
        face = cladding_face(wall, next(ly for ly in wall.layers if ly.function == "cladding"))
        before = len(findings)
        lower = _mine(model, wall.tag, {BAND_OUTLET_PRODUCT})
        upper = [s for s in _mine(model, wall.tag, {STRIP_PRODUCT}) if "-BANDSTRIP-" in s.tag]
        for _joint, lo, hi in spans:
            if not spans_cover([_along(p, face.d) for p in lower], lo, hi):
                findings.append(failed(CAVITY, f"{wall.tag}: the band has no vented outlet "
                                       "strip, so the cavity below it cannot breathe out",
                                       (wall.tag,), code=_CITE))
                break
            if not spans_cover([_along(p, face.d) for p in upper], lo, hi):
                findings.append(failed(CAVITY, f"{wall.tag}: the upper panel's batten ends "
                                       "open to insects at the band (no strip)", (wall.tag,),
                                       code=_CITE))
                break
        holes = perforation(model, lower)
        if lower and holes is None:
            findings.append(_unstated(wall.tag, "band outlet strip"))
            continue
        for piece in lower:
            offsets = _offsets(piece, face.n)
            area = net_free_area_cm2_per_m(max(offsets) - min(offsets), holes[1])
            areas.append(area)
            if area + 1e-9 < MIN_NET_FREE_AREA_CM2_PER_M:
                findings.append(failed(CAVITY, f"{wall.tag}: the band outlet is too small to "
                                       f"breathe: {area:.0f} cm2/m net free area", (wall.tag,),
                                       code=_CITE))
                break
        graded += len(findings) == before
    if graded and not findings:
        findings.append(passed(CAVITY, f"{graded} BBD75 bands vent the cavity through a "
                               f"perforated outlet ({min(areas):.0f} cm2/m) and seat the upper "
                               "panel on a strip", code=_CITE))
    return findings


@check(Tier.INTEGRITY, CAVITY)
def rainscreen_cavity(ctx: CheckContext) -> list:
    model = ctx.model
    if not any(screens_rainscreen_base(model, wall) or opening_head_spans(model, wall)
               for wall in model.walls):
        return [not_applicable(CAVITY, "no wall carries a drained and vented rainscreen")]
    return [*_base(model), *_kdat(model), *_panel_end_strips(model), *_heads(model),
            *_band(model)]
