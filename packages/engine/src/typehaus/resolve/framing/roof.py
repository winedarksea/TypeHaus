"""Deterministic gable/shed roof framing from resolved roof planes (M3).

Two declarative framing modes, chosen per roof assembly's STRUCTURE ``FramingSpec``:

* **rafter** (default) — plain sloped members spanning eave→ridge. The eave birdsmouth is
  now emitted as a real ``seat_cut`` solid seated on the top plate (previously only a
  ``connection`` annotation string): the box member IR cannot subtract the notch, so the
  seat is a distinct clipped member that reads in the 3D model, section, and BOM.
* **truss** — a fabricated top-chord + bottom-chord + web assembly with a *raised heel* at
  the eave bearing, so full insulation depth carries over the top plate. The roof surface is
  lifted by the heel so the top chords lie on the deck plane and the heel block is real.

Also resolves an authored ridge :class:`Beam` (WP4) for *rafter* roofs: trims the rafter
ridge ends back by half the beam's width so they land on top of it, and records the ridge
condition. A truss roof carries its own ridge, so it emits no ridge Beam advisory.
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.findings import Finding, Result, Severity
from typehaus.model.assembly import FramingSpec
from typehaus.model.enums import ConditionKind, LayerFunction
from typehaus.model.spatial import Roof
from typehaus.model.structure import Beam
from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.tables import DEFAULT_SPACING
from typehaus.resolve.model import BoundaryCondition, FramedMember, ResolvedModel, ResolvedRoof

_RAFTER_CONNECTION = "ridge:adjustable-slope-hanger;eave:birdsmouth-1.17in"
# Reference birdsmouth seat cut (roof_wall_eave_detail_ifc.py): a 1.17" notch depth, seated
# over the width of the top plate the rafter bears on.
_BIRDSMOUTH_DEPTH_M = inch(1.17).meters
_SEAT_LEN_M = inch(3.5).meters
# A standard raised ("energy") heel when a truss assembly does not declare its own.
_DEFAULT_TRUSS_HEEL_M = inch(9.25).meters


def frame_roofs(model: ResolvedModel) -> list[Finding]:
    """Attach roof-plane framing (rafters or trusses) at the assembly's spacing."""
    findings: list[Finding] = []
    framed: list[ResolvedRoof] = []
    for roof in model.roofs:
        spec = _structure_framing(model, roof)
        if spec is not None and spec.roof_frame == "truss":
            new_roof, members = _frame_trusses(model, roof, spec)
            framed.append(replace(new_roof, members=members))
            continue
        rafters = _roof_rafters(model, roof)
        beam_member, beam_findings = _resolve_ridge_beam(model, roof)
        findings.extend(beam_findings)
        if beam_member is not None:
            beam_width_m = cross_section(beam_member.profile).width_m
            rafters = tuple(_trim_rafter_to_beam(r, roof, beam_width_m) for r in rafters)
            model.conditions.append(_ridge_condition(roof, beam_member))
        seat_cuts = _eave_seat_cuts(model, roof, rafters)
        rafters = tuple(replace(r, connection=_RAFTER_CONNECTION) for r in rafters)
        members = (rafters + _bearing_stiffeners(rafters) + seat_cuts
                   + ((beam_member,) if beam_member is not None else ()))
        framed.append(ResolvedRoof(
            uid=roof.uid, tag=roof.tag, storey=roof.storey, form=roof.form,
            footprint=roof.footprint, eave_z_m=roof.eave_z_m, ridge_z_m=roof.ridge_z_m,
            ridge_direction=roof.ridge_direction, assembly=roof.assembly,
            surface_area_m2=roof.surface_area_m2, members=members,
        ))
    model.roofs = framed
    return findings


def _structure_framing(model: ResolvedModel, roof: ResolvedRoof) -> FramingSpec | None:
    assembly = model.plan.library.resolve_assembly(roof.assembly)
    if assembly is None:
        return None
    layer = next((ly for ly in assembly.layers
                  if ly.function is LayerFunction.STRUCTURE and ly.framing is not None), None)
    return layer.framing if layer is not None else None


def _roof_element(model: ResolvedModel, roof: ResolvedRoof) -> Roof | None:
    element = model.plan.by_tag(roof.tag)
    return element if isinstance(element, Roof) else None


# --- rafter mode -------------------------------------------------------------------------

def _roof_rafters(model: ResolvedModel, roof: ResolvedRoof) -> tuple[FramedMember, ...]:
    assembly = model.plan.library.resolve_assembly(roof.assembly)
    if assembly is None:
        return ()
    structure = next((layer for layer in assembly.layers
                      if layer.function is LayerFunction.STRUCTURE and layer.framing is not None), None)
    if structure is None or structure.framing is None:
        return ()
    spacing = (structure.framing.spacing or DEFAULT_SPACING).meters
    depth = structure.thickness.meters
    profile = structure.framing.member
    xs, ys = [point[0] for point in roof.footprint], [point[1] for point in roof.footprint]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    along_low, along_high = ((minx, maxx) if roof.ridge_direction == "x" else (miny, maxy))
    # Rafters repeat along the ridge and span perpendicular to it.
    count = int(round((along_high - along_low) / spacing))
    positions = [min(along_high, along_low + index * spacing) for index in range(count + 1)]
    if positions[-1] < along_high - 1e-9:
        positions.append(along_high)
    if roof.ridge_direction == "x":
        ridge = (miny + maxy) / 2
        halves = [half for value in positions for half in (
            ((value, miny), (value, ridge)), ((value, maxy), (value, ridge)),
        )]
    else:
        ridge = (minx + maxx) / 2
        halves = [half for value in positions for half in (
            ((minx, value), (ridge, value)), ((maxx, value), (ridge, value)),
        )]
    if roof.form == "shed":
        halves = halves[:len(positions)]
    members: list[FramedMember] = []
    rise = roof.ridge_z_m - roof.eave_z_m
    for index, (eave, ridge_point) in enumerate(halves):
        length = math.hypot(ridge_point[0] - eave[0], ridge_point[1] - eave[1], rise)
        members.append(FramedMember(
            roof.uid, f"rafter-{index:03d}", "rafter", profile, eave, ridge_point,
            roof.eave_z_m - depth, roof.eave_z_m, length,
            z0_end_m=roof.ridge_z_m - depth, z1_end_m=roof.ridge_z_m,
        ))
    return tuple(members)


def _bearing_stiffeners(rafters: tuple[FramedMember, ...]) -> tuple[FramedMember, ...]:
    """Model the I-joist eave web stiffener as a distinct bearing member.

    The seat itself is now a real ``seat_cut`` solid (see ``_eave_seat_cuts``); this solid
    makes the required beveled bearing reinforcement visible and countable in every emitter.
    """
    stiffeners: list[FramedMember] = []
    for rafter in rafters:
        if "I-joist" not in rafter.profile:
            continue
        stiffeners.append(FramedMember(
            rafter.parent_uid, f"{rafter.child_key}-eave-stiffener", "bearing_stiffener",
            "2x4", rafter.p0, rafter.p0, rafter.z0_m, rafter.z1_m,
            rafter.z1_m - rafter.z0_m, connection="eave:beveled-web-stiffener",
        ))
    return tuple(stiffeners)


def _eave_seat_cuts(
    model: ResolvedModel, roof: ResolvedRoof, rafters: tuple[FramedMember, ...]
) -> tuple[FramedMember, ...]:
    """A real birdsmouth SEAT-CUT solid seated on the top plate at every rafter eave.

    The lightweight member IR cannot subtract a notch from the raked rafter box, so the
    seat cut is emitted as a distinct clipped member — a short block bearing on the plate
    top over the seat length, so the rafter reads as a notched member seated on the wall
    rather than an exposed raked bar. Upgrades the former ``connection`` annotation.
    """
    plate_top = _bearing_plate_top(model, roof)
    if plate_top is None or not rafters:
        return ()
    seats: list[FramedMember] = []
    for rafter in rafters:
        (ex, ey), (rx, ry) = rafter.p0, rafter.p1
        dx, dy = rx - ex, ry - ey
        run = math.hypot(dx, dy)
        if run < 1e-9:
            continue
        seat = min(_SEAT_LEN_M, run * 0.5)
        inboard = (ex + dx / run * seat, ey + dy / run * seat)
        seats.append(FramedMember(
            rafter.parent_uid, f"{rafter.child_key}-seat", "seat_cut", rafter.profile,
            rafter.p0, inboard, plate_top, plate_top + _BIRDSMOUTH_DEPTH_M, seat,
            connection="eave:birdsmouth-seat",
        ))
    return tuple(seats)


def _bearing_plate_top(model: ResolvedModel, roof: ResolvedRoof) -> float | None:
    """Top-plate elevation the roof bears on (max bearing-wall top; None if unknown)."""
    element = _roof_element(model, roof)
    if element is None:
        return roof.eave_z_m
    tops = [w.z1_m for tag in element.bearing_refs if (w := model.wall(tag)) is not None]
    return max(tops) if tops else roof.eave_z_m


# --- truss mode --------------------------------------------------------------------------

def _frame_trusses(
    model: ResolvedModel, roof: ResolvedRoof, spec: FramingSpec
) -> tuple[ResolvedRoof, tuple[FramedMember, ...]]:
    """Raised-heel trusses: top + bottom chords, king post + diagonal webs, heel blocks.

    Returns the roof (its surface lifted by the raised heel so the top chords sit on the
    deck plane) and the emitted truss members. Falls back to the unchanged roof + no members
    if the bearing geometry cannot be resolved.
    """
    element = _roof_element(model, roof)
    if element is None:
        return roof, ()
    span_ax = 1 if roof.ridge_direction == "x" else 0
    ridge_ax = 1 - span_ax
    bearings: list[tuple[float, float]] = []  # (span coordinate, plate top z)
    along_lo = along_hi = None
    for tag in element.bearing_refs:
        wall = model.wall(tag)
        if wall is None:
            continue
        (ax, ay), (bx, by) = wall.axis
        span_coord = ay if span_ax == 1 else ax
        r0, r1 = (ay, by) if ridge_ax == 1 else (ax, bx)
        lo, hi = min(r0, r1), max(r0, r1)
        along_lo = lo if along_lo is None else min(along_lo, lo)
        along_hi = hi if along_hi is None else max(along_hi, hi)
        bearings.append((span_coord, wall.z1_m))
    if along_lo is None or len(bearings) < 2:
        return roof, ()
    bearings.sort()
    bear_lo, bear_hi = bearings[0][0], bearings[-1][0]
    plate_top = max(z for _, z in bearings)

    span_vals = [p[span_ax] for p in roof.footprint]
    foot_lo, foot_hi = min(span_vals), max(span_vals)
    span_mid = (foot_lo + foot_hi) / 2.0
    half = (foot_hi - foot_lo) / 2.0 or 1.0

    chord = spec.chord_member or spec.member
    web = spec.web_member or "2x4"
    cd = cross_section(chord).depth_m
    wd = cross_section(web).depth_m
    heel = spec.heel_height.meters if spec.heel_height is not None else _DEFAULT_TRUSS_HEEL_M

    def plane_z(s: float, eave: float, ridge: float) -> float:
        return ridge - (ridge - eave) * abs(s - span_mid) / half

    # Lift the surface so the top-chord underside clears the raised heel over each bearing.
    needed = plate_top + heel + cd
    delta = 0.0
    for bear, _ in bearings:
        delta = max(delta, needed - plane_z(bear, roof.eave_z_m, roof.ridge_z_m))
    new_eave = roof.eave_z_m + delta
    new_ridge = roof.ridge_z_m + delta
    new_roof = replace(roof, eave_z_m=new_eave, ridge_z_m=new_ridge)

    orient = (1.0, 0.0) if roof.ridge_direction == "x" else (0.0, 1.0)

    def plan_pt(pos: float, s: float) -> tuple[float, float]:
        return (pos, s) if roof.ridge_direction == "x" else (s, pos)

    spacing = (spec.spacing or DEFAULT_SPACING).meters
    count = int(round((along_hi - along_lo) / spacing))
    positions = [min(along_hi, along_lo + i * spacing) for i in range(count + 1)]
    if positions[-1] < along_hi - 1e-9:
        positions.append(along_hi)

    members: list[FramedMember] = []
    top_at_lo = plane_z(bear_lo, new_eave, new_ridge)
    top_at_hi = plane_z(bear_hi, new_eave, new_ridge)
    for ti, pos in enumerate(positions):
        tag = f"truss-{ti:03d}"
        # Bottom chord (ceiling): horizontal, bearing-to-bearing on the top plates.
        members.append(FramedMember(
            roof.uid, f"{tag}-bc", "bottom_chord", chord,
            plan_pt(pos, bear_lo), plan_pt(pos, bear_hi),
            plate_top, plate_top + cd, abs(bear_hi - bear_lo),
        ))
        # Top chords: eave tail → apex, lying on the (lifted) deck plane.
        apex = plan_pt(pos, span_mid)
        members.append(FramedMember(
            roof.uid, f"{tag}-tc-lo", "top_chord", chord, plan_pt(pos, foot_lo), apex,
            new_eave - cd, new_eave, math.hypot(span_mid - foot_lo, new_ridge - new_eave),
            z0_end_m=new_ridge - cd, z1_end_m=new_ridge,
        ))
        members.append(FramedMember(
            roof.uid, f"{tag}-tc-hi", "top_chord", chord, plan_pt(pos, foot_hi), apex,
            new_eave - cd, new_eave, math.hypot(foot_hi - span_mid, new_ridge - new_eave),
            z0_end_m=new_ridge - cd, z1_end_m=new_ridge,
        ))
        # Raised-heel blocks: plate top → top-chord underside at each bearing.
        for side, bear, top_at in (("lo", bear_lo, top_at_lo), ("hi", bear_hi, top_at_hi)):
            pt = plan_pt(pos, bear)
            heel_top = max(plate_top + cd, top_at - cd)
            members.append(FramedMember(
                roof.uid, f"{tag}-heel-{side}", "truss_heel",
                web, pt, pt, plate_top, heel_top, heel_top - plate_top, orient=orient,
            ))
        # King post: bottom-chord top → apex underside.
        members.append(FramedMember(
            roof.uid, f"{tag}-king", "truss_web", web, apex, apex,
            plate_top + cd, new_ridge - cd, (new_ridge - cd) - (plate_top + cd), orient=orient,
        ))
        # Diagonal webs: bottom-chord quarter points → apex (a simple Fink reading).
        for side, bear in (("lo", bear_lo), ("hi", bear_hi)):
            quarter = (bear + span_mid) / 2.0
            members.append(FramedMember(
                roof.uid, f"{tag}-web-{side}", "truss_web", web,
                plan_pt(pos, quarter), apex,
                plate_top + cd, plate_top + cd + wd,
                math.hypot(span_mid - quarter, (new_ridge - cd) - (plate_top + cd)),
                z0_end_m=new_ridge - cd - wd, z1_end_m=new_ridge - cd,
            ))
    return new_roof, tuple(members)


# --- ridge beam (rafter roofs) -----------------------------------------------------------

def _find_ridge_beam(model: ResolvedModel, roof: ResolvedRoof) -> Beam | None:
    """An authored Beam whose node axis is coincident+parallel with the ridge line.

    Matches on the infinite line (constant x for a "y"-running ridge, constant y for
    an "x"-running ridge), not on endpoints — the beam need not span the full ridge.
    """
    xs = [p[0] for p in roof.footprint]
    ys = [p[1] for p in roof.footprint]
    axis = 1 if roof.ridge_direction == "x" else 0
    ridge_const = ((min(ys) + max(ys)) / 2 if axis == 1 else (min(xs) + max(xs)) / 2)
    nodes = {e.tag: e.position.xy_m for e in model.plan.storey_elements(roof.storey)
             if e.element_kind == "Node"}
    for element in model.plan.storey_elements(roof.storey):
        if not isinstance(element, Beam):
            continue
        start, end = nodes.get(element.start_node), nodes.get(element.end_node)
        if start is None or end is None:
            continue
        if (abs(start[axis] - ridge_const) < 1e-6 and abs(end[axis] - ridge_const) < 1e-6):
            return element, start, end
    return None


def _resolve_ridge_beam(
    model: ResolvedModel, roof: ResolvedRoof
) -> tuple[FramedMember | None, list[Finding]]:
    found = _find_ridge_beam(model, roof)
    if found is None:
        if roof.form != "gable":
            return None, []
        return None, [Finding(
            severity=Severity.WARN, check_id="structural.ridge_support",
            message=f"roof {roof.tag} has no authored ridge Beam — the ridge line has "
                    "no modeled support member (advisory, not engineering)",
            element_tags=(roof.tag,), result=Result.UNKNOWN,
        )]
    beam, start, end = found
    depth = cross_section(beam.size).depth_m
    z1 = roof.ridge_z_m
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    member = FramedMember(
        beam.uid, "ridge-beam", "ridge_beam", beam.size, start, end, z1 - depth, z1, length,
    )
    return member, []


def _trim_rafter_to_beam(rafter: FramedMember, roof: ResolvedRoof, beam_width_m: float) -> FramedMember:
    """Pull the rafter's ridge end back by half the beam width, staying on the roof plane."""
    ex, ey = rafter.p0
    rx, ry = rafter.p1
    dx, dy = rx - ex, ry - ey
    horiz_run = math.hypot(dx, dy)
    trim = min(beam_width_m / 2.0, horiz_run * 0.5)
    if horiz_run < 1e-9 or trim <= 0.0:
        return rafter
    fraction = (horiz_run - trim) / horiz_run
    new_p1 = (ex + dx * fraction, ey + dy * fraction)
    new_top = roof.eave_z_m + (roof.ridge_z_m - roof.eave_z_m) * fraction
    depth = rafter.z1_m - rafter.z0_m
    new_bottom = new_top - depth
    new_length = math.hypot(new_p1[0] - ex, new_p1[1] - ey, new_top - roof.eave_z_m)
    return replace(rafter, p1=new_p1, length_m=new_length, z0_end_m=new_bottom, z1_end_m=new_top)


def _ridge_condition(roof: ResolvedRoof, beam_member: FramedMember) -> BoundaryCondition:
    assemblies = (roof.assembly,)
    return BoundaryCondition(
        kind=ConditionKind.ROOF_RIDGE, assemblies=assemblies, detail="lvl-ridge-hanger",
        element_tags=(roof.tag, beam_member.parent_uid), key=f"roof_ridge:{roof.tag}",
    )
