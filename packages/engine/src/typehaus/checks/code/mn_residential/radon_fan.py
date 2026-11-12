"""MN 1303.2402 — the future fan: its power (subp. 6) and its space on the riser (subp. 5.D).

Same check id as :mod:`.radon`, which calls in here; split only to keep files short.

* **Subp. 6** wants "an electrical circuit terminating in an approved electrical box" at the
  fan's location, outside conditioned space. A nearby box is not a circuit: the riser names
  its box (``VentRun.fan_power_ref``) and the box names a panel branch.
* **Subp. 5.D** wants a 24"-diameter, 3 ft long clear space around the vent pipe for the fan.
  Graded on the riser's exterior (TERM) leg, a 24" cylinder clipped at the wall it rides:
  that wall is the one thing a fan may sit against.
"""

from __future__ import annotations

from typing import Any

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext
from typehaus.findings import Finding
from typehaus.model.mep import VentRun
from typehaus.quantities import ft, inch
from typehaus.resolve.placeables import placed_xy
from typehaus.resolve.room_lookup import axis_polygon, axis_ring

_CODE = "MN 1303.2402"
_CID = "code.MN_1303_2402_radon"

# How close the box has to be to the exterior riser to be "in the anticipated location".
_FAN_BOX_REACH = ft(8)
# Subp. 5.D's space for the fan.
FAN_SPACE_DIAMETER = inch(24)
FAN_SPACE_LENGTH = ft(3)
# An RP145-class in-line radon fan (RadonAway RP140/145 data sheet: 9.7" dia x 8.5" H),
# and the gap that keeps its housing off the siding.
FAN_OD = inch(9.7)
FAN_SIDING_GAP = inch(0.5)
# Exterior casing proud of a rough opening's edge, read as part of the opening.
_OPENING_TRIM = inch(3.5)
_STEP_M = inch(1).meters
_IN = 0.0254


def _ftin(meters: float) -> str:
    inches = meters / _IN
    feet = int(inches // 12)
    return f"{feet}'-{inches - feet * 12:.1f}\""


def fan_power_finding(ctx: CheckContext, riser: VentRun,
                      riser_xy: tuple[float, float]) -> Finding:
    """Subp. 6 — the riser's named box, on a panel branch, at the fan, outside the envelope."""
    from typehaus.model.enums import DeviceKind

    ref = riser.fan_power_ref
    if not ref:
        rx, ry = riser_xy
        near = sorted(
            e.tag for e in ctx.plan.all_elements()
            if getattr(e, "element_kind", None) == "ElectricalDevice"
            and getattr(e, "kind", None) is DeviceKind.JUNCTION_BOX
            and (xy := placed_xy(ctx.model, e)) is not None
            and ((xy[0] - rx) ** 2 + (xy[1] - ry) ** 2) ** 0.5 <= _FAN_BOX_REACH.meters)
        seen = f" ({', '.join(near)} stand nearby)" if near else ""
        return _unknown(_CID, f"{riser.tag} names no fan_power_ref{seen}; a nearby box is "
                              "not a circuit, so subpart 6's circuit terminating in an "
                              "approved box at the fan location is not shown",
                        (riser.tag,), _CODE)
    box = ctx.plan.by_tag(ref)
    if getattr(box, "element_kind", None) != "ElectricalDevice":
        return _fail(_CID, f"{riser.tag}'s fan_power_ref {ref} is not an electrical device",
                     (riser.tag,), _CODE)
    circuits = {c.tag: c for c in ctx.plan.library.circuits}
    circuit = circuits.get(box.circuit or "")
    if circuit is None:
        return _fail(_CID, f"{ref} names no circuit, so subpart 6's circuit to the fan "
                           "box is not shown", (ref, riser.tag), _CODE)
    panel = ctx.plan.by_tag(circuit.panel_ref)
    if getattr(panel, "kind", None) is not DeviceKind.PANEL or circuit.source:
        return _fail(_CID, f"{ref}'s circuit {circuit.tag} is not a load branch of a panel "
                           "(a PV/ESS source feed cannot power a fan)", (ref, riser.tag),
                     _CODE)
    bx, by = placed_xy(ctx.model, box)
    rx, ry = riser_xy
    if ((bx - rx) ** 2 + (by - ry) ** 2) ** 0.5 > _FAN_BOX_REACH.meters:
        return _fail(_CID, f"{ref} stands more than {_FAN_BOX_REACH.inches / 12:.0f}' from "
                           f"{riser.tag}'s exterior riser; subpart 6 puts the box at the "
                           "anticipated fan location", (ref, riser.tag), _CODE)
    exit_wall = ctx.model.wall(riser.wall_ref) if riser.wall_ref else None
    storey = exit_wall.storey if exit_wall is not None else None
    from shapely.geometry import Point

    for room in ctx.model.rooms:
        if (room.conditioned and len(axis_ring(room)) >= 3
                and (storey is None or room.storey == storey)
                and axis_polygon(room).covers(Point(bx, by))):
            return _fail(_CID, f"{ref} stands inside conditioned room {room.tag} — subpart 6 "
                               "forbids the fan's box in any conditioned space, basement or "
                               "crawl space", (ref, riser.tag), _CODE)
    slot = f", slot {circuit.slot}" if getattr(circuit, "slot", None) else ""
    return _pass(_CID, f"{ref} powers {riser.tag}'s future fan on {circuit.tag} "
                       f"({circuit.panel_ref}{slot}), outside conditioned space "
                       "(subpart 6)", _CODE)


def radon_leg(model: Any, riser: VentRun
              ) -> tuple[str, tuple[float, float], float, float] | None:
    """The RADON pipe's exterior leg as ``(tag, plan point, z bottom, z top)``."""
    from typehaus.resolve.vent_termination import riser_polylines

    legs = riser_polylines(model, riser)
    radon = next((leg for leg in legs if leg[0].endswith("-radon")), legs[0] if legs else None)
    if radon is None:
        return None
    tag, path, z = radon
    return tag, path[-1], z[-2], z[-1]


def fan_space(model: Any, riser: VentRun) -> tuple[float, float] | None:
    """The lowest clear subp. 5.D window ``(z0, z1)`` on the radon leg, or None."""
    return _fan_space_scan(model, riser)[0]


def fan_space_findings(ctx: CheckContext, riser: VentRun) -> list[Finding]:
    """Subp. 5.D — a 24" x 3 ft clear space on the exterior leg, and a fan that fits it."""
    leg = radon_leg(ctx.model, riser)
    if leg is None:
        return [_unknown(_CID, f"{riser.tag} resolves no exterior leg, so subpart 5.D's fan "
                               "space cannot be graded", (riser.tag,), _CODE)]
    _tag, (px, py), z0, z1 = leg
    out = []
    wall = _wall_footprint(ctx.model, riser, (px, py))
    if wall is not None:
        from shapely.geometry import Point

        standoff = Point(px, py).distance(wall)
        need = FAN_OD.meters / 2 + FAN_SIDING_GAP.meters
        if standoff + 1e-6 < need:
            out.append(_fail(_CID, f"{riser.tag}'s radon pipe stands {standoff / _IN:.2f}\" "
                                   f"off {riser.wall_ref}'s cladding; a {FAN_OD.inches:.1f}\" "
                                   f"fan needs {need / _IN:.2f}\" (subpart 5.D)",
                             (riser.tag,), _CODE))
    if z1 - z0 + 1e-6 < FAN_SPACE_LENGTH.meters:
        return [*out, _fail(_CID, f"{riser.tag}'s exterior radon leg is "
                                  f"{(z1 - z0) / _IN:.1f}\" long; subpart 5.D needs "
                                  f"{FAN_SPACE_LENGTH.inches:.0f}\" for the fan",
                            (riser.tag,), _CODE)]
    window, blocker = _fan_space_scan(ctx.model, riser)
    if window is not None:
        return [*out, _pass(_CID, f"{riser.tag}'s fan space: a {FAN_SPACE_DIAMETER.inches:.0f}"
                                  f"\" x {FAN_SPACE_LENGTH.inches / 12:.0f}' clear cylinder "
                                  f"from {_ftin(window[0])} to {_ftin(window[1])} on the "
                                  "radon leg (subpart 5.D)", _CODE)]
    return [*out, _fail(_CID, f"no {FAN_SPACE_LENGTH.inches / 12:.0f}' length of "
                              f"{riser.tag}'s exterior radon leg has a clear "
                              f"{FAN_SPACE_DIAMETER.inches:.0f}\" circle for the fan; "
                              f"{blocker} stands in it (subpart 5.D)",
                        (riser.tag, blocker), _CODE)]


def _fan_space_scan(model: Any, riser: VentRun):
    """``((z0, z1), None)`` for the first clear window, else ``(None, a blocker's tag)``."""
    from shapely.geometry import Point

    from typehaus.resolve import overlay

    leg = radon_leg(model, riser)
    if leg is None:
        return None, None
    own, (px, py), z_lo, z_hi = leg
    space = Point(px, py).buffer(FAN_SPACE_DIAMETER.meters / 2)
    wall = _wall_footprint(model, riser, (px, py))
    if wall is not None:
        space = overlay.difference(space, wall)
    obstacles = [o for o in _obstacles(model, riser, own)
                 if o[1].intersection(space).area > 1e-8]
    length = FAN_SPACE_LENGTH.meters
    z, blocker = z_lo, None
    while z + length <= z_hi + 1e-9:
        hit = next((o for o in obstacles if o[2] < z + length and o[3] > z), None)
        if hit is None:
            return (z, z + length), None
        blocker = blocker or hit[0]
        z += _STEP_M
    return None, blocker or "the leg's own length"


def _obstacles(model: Any, riser: VentRun, own: str) -> list[tuple[str, Any, float, float]]:
    """Every ``(tag, plan footprint, z0, z1)`` a fan could hit near the riser."""
    from shapely.geometry import Point, Polygon

    from typehaus.resolve.mep_envelopes import envelopes, opening_prisms

    out: list[tuple[str, Any, float, float]] = []
    for env in envelopes(model):
        if env.tag == own:
            continue
        out.extend((env.tag, p.footprint, p.z0_m, p.z1_m) for p in env.prisms)
    for obj in model.canvas_objects:
        if len(obj.footprint) >= 3:
            top = obj.body_z1_m if obj.body_z1_m is not None else obj.z_m + inch(1).meters
            bottom = obj.body_z0_m if obj.body_z0_m is not None else obj.z_m
            out.append((obj.tag, Polygon(obj.footprint), bottom, top))
    for element in model.plan.all_elements():
        if (getattr(element, "element_kind", None) == "Connector"
                and riser.tag not in (getattr(element, "connects", ()) or ())
                and getattr(element, "position", None) is not None
                and getattr(element, "elevation", None) is not None):
            z = element.elevation.meters
            out.append((element.tag, Point(element.position.xy_m).buffer(inch(1).meters),
                        z - inch(1).meters, z + inch(1).meters))
    for tag, _door, _host, prism, low, high, _for in opening_prisms(model, erode_m=0.0):
        trim = _OPENING_TRIM.meters
        out.append((tag, prism.buffer(trim), low - trim, high + trim))
    return out


def _wall_footprint(model: Any, riser: VentRun,
                    point: tuple[float, float]) -> Any | None:
    """The host wall and walls in line with it near ``point``: what a fan sits against."""
    from shapely.geometry import Point, Polygon

    from typehaus.resolve import overlay

    host = model.wall(riser.wall_ref) if riser.wall_ref else None
    if host is None:
        return None
    near = Point(point)
    (ax, ay), (bx, by) = host.axis
    pieces = []
    for wall in model.walls:
        if wall.storey != host.storey:
            continue
        (cx, cy), (dx, dy) = wall.axis
        cross = (bx - ax) * (dy - cy) - (by - ay) * (dx - cx)
        norm = (((bx - ax) ** 2 + (by - ay) ** 2) * ((dx - cx) ** 2 + (dy - cy) ** 2)) ** 0.5
        if norm <= 0 or abs(cross) / norm > 0.05:
            continue
        pieces.extend(poly for layer in wall.layers if len(layer.polygon) >= 3
                      if (poly := Polygon(layer.polygon).buffer(0)).distance(near) < 1.0)
    return overlay.union_all(pieces) if pieces else None
