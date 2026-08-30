"""MN Rules 1303.2402 — the passive radon control system every new MN dwelling must have.

This is a *Minnesota* rule with no IRC parent: MN Rules 1303.2400-.2402 make a passive
soil-gas system mandatory in every new residential structure in the state, and a plan
reviewer looks for it on the foundation and plumbing sheets. Nothing in the engine graded
it, even though this house has modeled the whole system — sealed sump, shared radon/vent
riser, exterior junction box for a future fan — since long before the rule was encoded.

What is gradeable from the model, and what is not:

* **Subpart 4.E, sealed sump cover** — ``Sump.sealed_cover``. Direct.
* **Subpart 5, the vent pipe** — that one exists, rises from the collection point, and
  terminates 12" above the roof. The 12" is *derived* by ``resolve/vent_termination.py``
  and already graded by ``mep.vent_termination_height``, so this rule asserts the system's
  existence and its connection, not the clearance a sibling check owns.
* **Subpart 5, 10 ft from any opening into conditioned space** — geometry, and the one
  requirement here a plan can get wrong without anyone noticing until the fan goes in.
  Measured from the exhaust point and read with IRC AF103's 2 ft vertical allowance; see
  ``_separation_findings`` for why both of those matter to the answer.
* **Subpart 6, the fan's power source** — an approved box at the anticipated fan location,
  and explicitly *not* in conditioned space, a basement, or a crawl space.

Deliberately not graded, because the model carries no field for them and inventing one to
hold a boolean nobody sets would be worse than saying so here: subpart 2's membrane laps,
subpart 3's 10 ft of perforated pipe under the membrane, subpart 5's "Radon Gas Vent
System" labels and its 24"-diameter fan clearance, and the R-4 insulation on pipe in
unconditioned space. Those are field-verified items on this house's sheets.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import DeviceKind, PipeSystem
from typehaus.model.mep import Sump, VentRun
from typehaus.quantities import ft
from typehaus.resolve.geometry import opening_center
from typehaus.resolve.vent_termination import exterior_riser_point

_CODE = "MN 1303.2402"
_CID = "code.MN_1303_2402_radon"

# Subpart 5: the vent pipe terminates "at least 10 feet away from any window or other
# opening into the conditioned spaces of the building".
_MIN_OPENING_SEPARATION = ft(10)
# IRC AF103's qualifier on that sentence, which MN's own text drops: the 10 ft applies to an
# opening "less than 2 feet below the exhaust point". See ``_separation_findings``.
_EXHAUST_CLEARANCE_ABOVE_OPENING = ft(2)
# How close an approved box has to be to the exterior riser to read as "in the anticipated
# location of the vent pipe fan" (subpart 6). A fan sits in a 3 ft length of the riser and
# the box goes beside it; 8 ft of plan separation is generous without accepting a box on
# the far side of the house.
_FAN_BOX_REACH = ft(8)


def _exterior_riser_point(vent: VentRun) -> tuple[float, float]:
    """Plan point of the riser *outside* the wall, which is what subpart 5 measures from.

    The chase point is inside the building; the pipe leaves through ``wall_ref`` and rises
    up the cladding. Measuring separation from the chase would answer a question about a
    pipe nobody can smell.

    This DELEGATES rather than re-deriving. It used to compute ``chase_position +
    exit_offset`` itself, which was the same arithmetic the resolver does — and it stopped
    being the same the moment ``VentRun`` grew ``chase_offset``: a riser that jogs inside
    before it rises leaves the wall somewhere the chase point does not predict, and this
    check would have gone on grading the separation of a pipe that is not there. One
    derivation, one place: :func:`typehaus.resolve.vent_termination.exterior_riser_point`.
    """
    return exterior_riser_point(vent)


@check(Tier.CODE, _CID)
def radon_control_system(ctx: CheckContext) -> list[Finding]:
    """MN 1303.2402 — a passive radon system, vented clear of the openings it would re-enter.

    Applicability is unconditional in Minnesota: every new residential structure gets one,
    so a plan with no radon riser FAILs rather than scope-passing. There is no "this house
    does not have soil gas" case.
    """
    out: list[Finding] = []
    sumps = [e for e in ctx.plan.all_elements() if isinstance(e, Sump) and e.radon_vent]
    risers = [e for e in ctx.plan.all_elements()
              if isinstance(e, VentRun) and PipeSystem.RADON in e.systems]
    if not risers:
        return [_fail(_CID, "no vent run carries the RADON system; MN 1303.2402 requires a "
                            "passive soil-gas vent from the collection point through the "
                            "roof in every new residential structure", (), _CODE)]

    for riser in risers:
        served = [s for s in sumps if s.vent_ref == riser.tag]
        if not served:
            out.append(_unknown(_CID, f"radon riser {riser.tag} names no collection point — "
                                "no sump or sub-slab T fitting in the model feeds it, so "
                                "subpart 3's connection cannot be traced", (riser.tag,),
                                _CODE))
        for sump in served:
            if sump.sealed_cover:
                out.append(_pass(_CID, f"{sump.tag} is the sealed collection point for "
                                       f"{riser.tag}", _CODE))
            else:
                out.append(_fail(_CID, f"{sump.tag} vents radon through an unsealed cover; "
                                       "subpart 4.E requires a sealed or gasketed cover on a "
                                       "sump serving as the vent termination point",
                                 (sump.tag,), _CODE))
        out.extend(_separation_findings(ctx, riser))
        out.append(_fan_power_finding(ctx, riser))
    return out


def _separation_findings(ctx: CheckContext, riser: VentRun) -> list[Finding]:
    """Subpart 5's 10 ft between the *exhaust point* and any opening into conditioned space.

    Two decisions in here, both of which change the answer for a riser that rides a gable
    wall past the windows below it, which is how this house is built.

    **What is measured.** The pipe is closed; only its terminus emits soil gas, so the
    separation is measured from the exhaust point, not from every foot of riser standing
    beside a wall. Measuring the riser line instead condemns the ordinary detail.

    **The vertical allowance.** MN 1303.2402 subp. 5 reads "at least 10 feet away from any
    window or other opening into the conditioned spaces" with no qualifier. Its parent —
    IRC Appendix AF103 (AF103.5.3 in the 2018 edition, AF103.8 in the 2021) — is the same
    sentence *plus* "that is less than 2 feet below the exhaust point", which is the clause
    that makes the rule about re-entrainment rather than about plan geometry. This grades on
    the IRC formulation and says so in the finding, naming the drop it relied on: an opening
    two feet or more below the exhaust is exempt, and the nearest one that is not has to
    keep its 10 ft.
    """
    from typehaus.resolve.vent_termination import derived_termination_elevation

    rx, ry = _exterior_riser_point(riser)
    conditioned = {room.tag for room in ctx.model.rooms if room.conditioned}
    if not conditioned:
        return [_unknown(_CID, f"no room resolves as conditioned, so {riser.tag}'s 10 ft "
                               "separation has nothing to be measured against",
                         (riser.tag,), _CODE)]
    exhaust_m = derived_termination_elevation(ctx.model, riser)
    if exhaust_m is None:
        exhaust_m = (riser.roof_termination_elevation.meters
                     if riser.roof_termination_elevation is not None else None)
    if exhaust_m is None:
        return [_unknown(_CID, f"{riser.tag} clears no derivable roof and authors no "
                               "termination elevation, so the exhaust point the 10 ft is "
                               "measured from is unknown", (riser.tag,), _CODE)]

    storeys = {s.tag: s for s in ctx.plan.storeys}
    nearest_tag, nearest_m, nearest_drop = None, None, 0.0
    exempt_tag, exempt_drop = None, None
    for opening in ctx.model.openings:
        wall = ctx.model.wall(opening.host_wall)
        storey = storeys.get(wall.storey) if wall is not None else None
        if wall is None or storey is None:
            continue
        point = opening_center(wall, opening)
        if point is None:
            continue
        head_m = storey.elevation.meters + opening.sill_m + opening.height_m
        drop_m = exhaust_m - head_m
        distance = ((point[0] - rx) ** 2 + (point[1] - ry) ** 2) ** 0.5
        if drop_m >= _EXHAUST_CLEARANCE_ABOVE_OPENING.meters:
            if exempt_drop is None or distance < exempt_drop:
                exempt_tag, exempt_drop = opening.tag, distance
            continue
        if nearest_m is None or distance < nearest_m:
            nearest_tag, nearest_m, nearest_drop = opening.tag, distance, drop_m
    if nearest_m is None:
        return [_pass(_CID, f"every opening into conditioned space sits at least "
                            f"{_EXHAUST_CLEARANCE_ABOVE_OPENING.inches / 12:.0f}' below "
                            f"{riser.tag}'s exhaust at {exhaust_m / 0.3048:.1f}' — AF103's "
                            "vertical allowance, nearest in plan being "
                            f"{exempt_tag}", _CODE)]
    if nearest_m + 1e-6 < _MIN_OPENING_SEPARATION.meters:
        return [_fail(_CID, f"{riser.tag}'s exhaust stands {nearest_m / 0.3048:.1f}' in plan "
                            f"from {nearest_tag}, whose head is only "
                            f"{nearest_drop / 0.3048:.1f}' below it; subpart 5 requires 10' "
                            "from any opening into conditioned space that is less than 2' "
                            "below the exhaust point",
                      (riser.tag, nearest_tag or ""), _CODE)]
    return [_pass(_CID, f"{riser.tag}'s exhaust clears the nearest opening not exempted by "
                        f"the 2' vertical allowance ({nearest_tag}) by "
                        f"{nearest_m / 0.3048:.1f}'", _CODE)]


def _fan_power_finding(ctx: CheckContext, riser: VentRun) -> Finding:
    """Subpart 6 — a box at the fan's anticipated location, outside conditioned space.

    The rule's prohibition is the interesting half and it is *not* redundant with "put it
    outside": a box in the basement beside the stack would be the obvious place to put it
    and is the one place the rule names. So the location test asks which room the box stands
    in, not merely whether it is on an exterior wall.
    """
    from shapely.geometry import Point, Polygon

    rx, ry = _exterior_riser_point(riser)
    boxes = [e for e in ctx.plan.all_elements()
             if getattr(e, "element_kind", None) == "ElectricalDevice"
             and getattr(e, "kind", None) is DeviceKind.JUNCTION_BOX]
    if not boxes:
        return _fail(_CID, f"{riser.tag} has no electrical box at the fan location; subpart 6 "
                           "requires the circuit and an approved box to be installed during "
                           "construction so the system can be made active", (riser.tag,),
                     _CODE)
    # The fan sits in a 3 ft length of the riser, so its box is beside the riser — on the
    # storey the pipe leaves the building on. The reach test alone is PLAN-ONLY and this
    # house is four storeys tall, so on its own it collects junction boxes anywhere in the
    # section: moving VR-M-RADON-VENT 2'-10" west on 2026-08-30 pulled RM-S-BATH1's LED
    # driver, two floors down, inside 8'-0" of the riser and reported a *bathroom niche
    # transformer* as the radon fan's box. The room search below then named a BASEMENT room
    # for a second-storey device, because it too ranges over every storey at once.
    #
    # A box that declares no room is kept whatever storey it is on: ED-A-PV-JB is outside
    # the building entirely, which is exactly where subpart 6 wants this one, and it has no
    # room to match against. A box that declares a room is only a candidate on the riser's
    # own exit storey.
    exit_wall = ctx.model.wall(riser.wall_ref) if riser.wall_ref else None
    exit_storey = exit_wall.storey if exit_wall is not None else None
    room_storey = {room.tag: room.storey for room in ctx.model.rooms}
    reach = _FAN_BOX_REACH.meters
    near = []
    for box in boxes:
        bx, by = box.position.xy_m
        if ((bx - rx) ** 2 + (by - ry) ** 2) ** 0.5 > reach:
            continue
        declared = getattr(box, "room", None)
        if (declared and exit_storey is not None
                and room_storey.get(declared, exit_storey) != exit_storey):
            continue
        near.append(box)
    if not near:
        return _fail(_CID, f"the plan's junction box(es) "
                           f"({', '.join(sorted(b.tag for b in boxes))}) stand more than "
                           f"{_FAN_BOX_REACH.inches / 12:.0f}' from {riser.tag}'s exterior "
                           "riser; subpart 6 puts the fan's box at the anticipated fan "
                           "location", tuple(sorted(b.tag for b in boxes)) + (riser.tag,),
                     _CODE)
    interior = []
    for box in near:
        point = Point(*box.position.xy_m)
        for room in ctx.model.rooms:
            if len(room.clear_face) < 3 or not room.conditioned:
                continue
            # Same storey only — a plan point is over every storey at once, and a box is on
            # exactly one of them.
            if exit_storey is not None and room.storey != exit_storey:
                continue
            if Polygon(room.clear_face).covers(point):
                interior.append((box.tag, room.tag))
                break
    if interior:
        return _fail(_CID, "; ".join(f"{tag} stands inside conditioned room {room}"
                                     for tag, room in interior)
                     + " — subpart 6 forbids the fan's box in any conditioned space, "
                       "basement or crawl space",
                     tuple(tag for tag, _room in interior), _CODE)
    return _pass(_CID, f"{', '.join(sorted(b.tag for b in near))} stands at {riser.tag}'s "
                       "exterior riser, outside conditioned space, for a future fan", _CODE)
