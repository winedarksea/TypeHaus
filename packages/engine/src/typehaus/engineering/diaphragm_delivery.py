"""A deck that hands its lateral load to its neighbour — the joint, the receiver, its walls.

``lateral_system`` grades a deck against the lines standing UNDER it. A canopy on pinned
posts has, in one direction or both, no line of its own: its ``DiaphragmSpec.delivers_to``
names the structure it is tied to, and this module grades every part of that path at 100%
of the deck-level shear, with no stiffness judgement across the joint and no relief
credited (``notes/canopy_garage_diaphragm.md``'s envelope):

* **open front** — SDPWS 4.2.5.2, ``L'`` and ``L'/W'``, where the deck is held on one edge;
* **the joint** — the deck's boundary nailing along it, the straps along it and across it,
  and the linear couple the strap line closes when the along-joint resultant is off it;
* **the plate clips** — the receiving roof's frame into the wall under it;
* **the receiving roof** — its unit-shear INCREMENT, lever rule on the resultant, and its
  span-to-depth;
* **each receiving line** — the delivered shear over its SURPLUS braced length (IRC
  R301.1.3) at its authored SDPWS 4.3A row, and the overturning at the line's authored
  hold-down, no dead load credited.

Every reference must resolve and the geometry must agree; otherwise the row is refused and
the reason goes in ``missing`` by name — a delivery with a part missing is not graded.

The open front's chord force, its couple into the far lines and its drift N/A are
``open_front``'s (``notes/canopy_west_band.md`` §6).

**Oracle.** ``houses/catlin/notes/canopy_garage_diaphragm.md`` §3 and §4;
``tests/test_diaphragm_delivery_calcs.py`` reproduces it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from typehaus.engineering.item import LimitState, Quantity

_M_PER_FT = 0.3048

#: SDPWS-2015 §4.2.5.2 — the open-front limits for a one-story structure.
OPEN_FRONT_MAX_DEPTH_FT = 25.0
OPEN_FRONT_ASPECT_ONE_STORY = 1.0


@dataclass
class DeliveryRows:
    """What this module hands back to the ``lateral_system`` record."""

    states: list[LimitState] = field(default_factory=list)
    inputs: list[Quantity] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    element_tags: list[str] = field(default_factory=list)


def _xy_ft(element: Any) -> tuple[float, float] | None:
    position = getattr(element, "position", None)
    if position is None:
        return None
    x, y = position.xy_m
    return x / _M_PER_FT, y / _M_PER_FT


def _direction(axis: str) -> str:
    return "E-W" if axis == "x" else "N-S"


def delivery_rows(ctx: Any, element: Any, resolved_roof: Any, wind: Any,
                  shears: dict[str, float], resultants: dict[str, float]) -> DeliveryRows:
    """Every row a declared ``delivers_to`` owes.

    ``shears`` is the deck-level ASD shear per axis (the frame's own where cast columns
    share it, the pinned-post demand otherwise) and ``resultants`` where each resolves ACROSS
    the wind. Both are graded at 100% here whatever any column took.
    """
    from typehaus.engineering.lateral_lines import on_boundary, panel_runs_along
    from typehaus.model.spatial import Roof

    rows = DeliveryRows()
    delivery = element.diaphragm.delivers_to
    receiver = ctx.plan.by_tag(delivery.roof)
    if not isinstance(receiver, Roof) or receiver.diaphragm is None:
        rows.missing.append(
            f"the receiving roof `{delivery.roof}` with a DiaphragmSpec of its own: "
            + ("it does not resolve" if receiver is None else "it declares no diaphragm"))
        return rows
    receiver_resolved = next((r for r in ctx.model.roofs if r.tag == delivery.roof), None)
    rows.element_tags.append(delivery.roof)

    joints = [ctx.plan.by_tag(t) for t in delivery.joint_refs]
    clips = [ctx.plan.by_tag(t) for t in delivery.plate_clip_refs]
    for tag, part in (*zip(delivery.joint_refs, joints, strict=True),
                      *zip(delivery.plate_clip_refs, clips, strict=True)):
        if part is None:
            rows.missing.append(f"joint connector `{tag}` named by {element.tag}'s "
                                f"delivers_to — it does not resolve")
    if not joints:
        rows.missing.append(f"a joint: {element.tag}'s delivers_to names no connector across "
                            f"it, and a delivery with nothing drawn across the joint is a claim")
    if rows.missing:
        return rows

    walls: dict[str, Any] = {}
    for line in delivery.lines:
        wall = ctx.plan.by_tag(line.wall)
        if wall is None:
            rows.missing.append(f"receiving wall `{line.wall}` — it does not resolve")
            continue
        boundary = on_boundary(ctx, wall, resolved_roof)
        under = (line.wall in (receiver.bearing_refs or ())
                 or (receiver_resolved is not None
                     and on_boundary(ctx, wall, receiver_resolved)))
        if not (boundary or under):
            rows.missing.append(
                f"receiving wall `{line.wall}` in agreement with the geometry: it lies "
                f"neither on {element.tag}'s boundary nor under {delivery.roof}'s bearing")
            continue
        walls[line.wall] = (wall, line, boundary)
    if rows.missing:
        return rows
    rows.element_tags += sorted(walls)

    # ** THE JOINT'S LINE AND WHICH AXIS RUNS ALONG IT, read off the parts themselves. **
    stations = [xy for xy in (_xy_ft(j) for j in joints) if xy is not None]
    xs, ys = [p[0] for p in stations], [p[1] for p in stations]
    along = "x" if (max(xs) - min(xs)) >= (max(ys) - min(ys)) else "y"
    across = "y" if along == "x" else "x"
    joint_len = (max(xs) - min(xs)) if along == "x" else (max(ys) - min(ys))
    joint_at = (sum(ys) / len(ys)) if along == "x" else (sum(xs) / len(xs))
    if joint_len <= 0.0:
        rows.missing.append("a joint with length: its connectors stand on one station")
        return rows

    fx = [p[0] / _M_PER_FT for p in resolved_roof.footprint]
    fy = [p[1] / _M_PER_FT for p in resolved_roof.footprint]
    depth = (max(fy) - min(fy)) if along == "x" else (max(fx) - min(fx))
    width = (max(fx) - min(fx)) if along == "x" else (max(fy) - min(fy))
    if delivery.open_front:
        rows.states += [
            LimitState("open front, L'", depth, OPEN_FRONT_MAX_DEPTH_FT, "ft",
                       f"SDPWS-2015 §4.2.5.2 — the deck's dimension normal to its open side, "
                       f"{depth:.3f}', against 25'"),
            LimitState("open front, L'/W'", depth / width, OPEN_FRONT_ASPECT_ONE_STORY, "",
                       f"SDPWS-2015 §4.2.5.2, one-story: {depth:.3f}' / {width:.3f}'")]

    spec = element.diaphragm
    v_along = shears.get(along, 0.0)
    v_across = shears.get(across, 0.0)
    rows.inputs += [Quantity(f"delivered_shear_{a}", shears.get(a, 0.0), "lb", 1.0)
                    for a in ("x", "y")]
    rows.states.append(LimitState(
        "joint boundary nailing, along", v_along / joint_len, spec.unit_shear_asd_plf, "plf",
        f"{spec.source}; {_direction(along)} {v_along:,.1f} lb along {joint_len:.2f}' of "
        f"joint, where the last bay lands on {delivery.roof}'s frame"))
    _straps(rows, joints, v_along, v_across, along, joint_at, joint_len,
            resultants.get(along), element.tag)
    _clips(rows, clips, v_along, along)

    # ** THE RECEIVING LINES. ** Along the joint the boundary walls take it directly; across
    # it the receiving roof carries it to the walls parallel to it, by the lever rule.
    boundary = [(w, ln) for w, ln, on in walls.values() if on and panel_runs_along(ctx, w, along)]
    far = [(w, ln) for w, ln, on in walls.values()
           if not on and panel_runs_along(ctx, w, across)]
    total_len = 0.0
    readings = {}
    for wall, line in boundary:
        reading = _surplus(ctx, rows, line.wall)
        if reading is not None:
            readings[line.wall] = reading
            total_len += reading[1] - reading[2]
    for wall, line in boundary:
        if line.wall in readings and total_len > 0.0:
            _, provided, required = readings[line.wall]
            share = v_along * (provided - required) / total_len
            _line_rows(ctx, rows, wall, line, share, readings[line.wall], along, True)
    if far:
        _receiving_roof(ctx, rows, receiver, receiver_resolved, far, v_across,
                        resultants.get(across), across)
    if delivery.open_front:
        from typehaus.engineering.open_front import open_front_rows

        far_readings = {ln.wall: r for _w, ln in far
                        if (r := _surplus(ctx, rows, ln.wall)) is not None}
        open_front_rows(ctx, rows, element, joints, v_along, along, far, far_readings)

    rows.states.append(LimitState(
        "torsional stability, delivered", 0.0 if (boundary and len(far) >= 2) else 1.0, 1.0,
        "", f"the deck is held along its {_direction(along)} joint by "
            f"{', '.join(w.tag for w, _ in boundary) or 'no wall'} and across it through "
            f"{delivery.roof} by {', '.join(w.tag for w, _ in far) or 'nothing'}: two "
            f"directions and a couple, so the open front is not a mechanism",
        is_detailing=True))
    if delivery.differential_movement:
        rows.notes.append(f"DIFFERENTIAL MOVEMENT: {delivery.differential_movement}")
    rows.notes.append(
        f"THE ENVELOPE: {delivery.roof} and its walls are graded at 100% of the "
        f"deck-level shear ({v_along:,.1f} lb {_direction(along)}, {v_across:,.1f} lb "
        f"{_direction(across)}), and every panel on this deck is ALSO graded at 100% along "
        f"its own run. No stiffness judgement is made across a joint between two separately "
        f"founded structures, and no relief is credited to either path.")
    return rows


def _straps(rows: DeliveryRows, joints: list[Any], v_along: float, v_across: float,
            along: str, joint_at: float, joint_len: float, resultant: float | None,
            tag: str) -> None:
    from typehaus.hardware.catalog import allowable_for_model

    allowable = allowable_for_model(joints[0].size or "")
    capacity = getattr(allowable, "uplift_lb", None)
    if allowable is None or capacity is None:
        rows.missing.append(f"a published allowable for the joint strap `{joints[0].size}`")
        return
    n = len(joints)
    cite = allowable.citation.split(":")[0]
    rows.states += [
        LimitState(f"{joints[0].size} joint straps, along", v_along / n, capacity, "lb",
                   f"{cite}; {v_along:,.1f} lb over {n} straps — the steel value, and the "
                   f"nail group behind it is direction-independent under 1/4in (NDS 12.3)"),
        LimitState(f"{joints[0].size} joint straps, across", v_across / n, capacity, "lb",
                   f"{cite}; {v_across:,.1f} lb of strap tension over {n} straps")]
    if resultant is None:
        return
    # The along-joint resultant sits off the joint; the strap line closes the couple.
    index = 0 if along == "x" else 1
    stations = [p.position.xy_m[index] / _M_PER_FT for p in joints]
    centre = sum(stations) / n
    second = sum((s - centre) ** 2 for s in stations)
    lever = abs(joint_at - resultant)
    couple = v_along * lever
    worst = couple * max(abs(s - centre) for s in stations) / second if second else 0.0
    rows.inputs.append(Quantity("joint_couple_lb_ft", couple, "lb-ft", 1.0))
    rows.states.append(LimitState(
        f"{joints[0].size} joint straps, rotation couple", worst, capacity, "lb",
        f"the {_direction(along)} resultant stands {lever:.3f}' off the joint, M = "
        f"{v_along:,.1f} x {lever:.3f} = {couple:,.1f} lb-ft, taken as a linear couple over "
        f"the strap stations (sum x^2 = {second:.1f} ft2)"))


def _clips(rows: DeliveryRows, clips: list[Any], v_along: float, along: str) -> None:
    from typehaus.hardware.catalog import allowable_for_model

    if not clips:
        rows.notes.append("NO PLATE CLIPS are named: the receiving frame's own bearing on the "
                          "wall is the only path from the joint into the wall, and it is not "
                          "graded")
        return
    allowable = allowable_for_model(clips[0].size or "")
    values = [v for v in (getattr(allowable, "lateral_f1_lb", None),
                          getattr(allowable, "lateral_f2_lb", None)) if v]
    if allowable is None or not values:
        rows.missing.append(f"a published lateral allowable for the plate clip `{clips[0].size}`")
        return
    rows.states.append(LimitState(
        f"{clips[0].size} plate clips, frame into wall", v_along / len(clips), min(values), "lb",
        f"{allowable.citation}; {_direction(along)} {v_along:,.1f} lb over {len(clips)} "
        f"clips at the LOWER of the two published directions, so no direction needs knowing. "
        f"{allowable.fasteners}"))


def _surplus(ctx: Any, rows: DeliveryRows, wall_tag: str) -> tuple[str, float, float] | None:
    reader = getattr(ctx, "bracing", None)
    reading = reader(wall_tag) if callable(reader) else None
    if reading is None:
        rows.missing.append(
            f"the braced-wall reading of `{wall_tag}`'s line: the delivered load is graded "
            f"on the SURPLUS a prescriptive line provides beyond R602.10.3's own requirement, "
            f"and without it there is no length to grade against")
    return reading


def _line_rows(ctx: Any, rows: DeliveryRows, wall: Any, line: Any, force: float,
               reading: tuple[str, float, float], axis: str, overturning: bool) -> None:
    line_tag, provided, required = reading
    surplus = provided - required
    rows.inputs.append(Quantity(f"receiving_{line.wall}_lb", force, "lb", 1.0))
    rows.states.append(LimitState(
        f"{line.wall} delivered shear on the surplus", force / surplus if surplus > 0 else
        float("inf"), line.unit_shear_asd_plf, "plf",
        f"{line.source}; IRC R301.1.3 — {line_tag} keeps its R602.10 grade for its own "
        f"building, and the {_direction(axis)} {force:,.1f} lb delivered is graded on the "
        f"{surplus:.3f}' of surplus ({provided:.3f}' provided less {required:.3f}' required)"))
    if overturning:
        _overturning(ctx, rows, wall, force, provided)


def _overturning(ctx: Any, rows: DeliveryRows, wall: Any, force: float,
                 provided_ft: float) -> None:
    """The delivered increment's end tension at the line's authored hold-down."""
    from typehaus.hardware.catalog import allowable_for_model
    from typehaus.model.enums import ConnectorKind

    resolved = ctx.model.wall(wall.tag)
    if resolved is None or provided_ft <= 0.0:
        return
    height = (resolved.z1_m - resolved.z0_m) / _M_PER_FT
    tension = force / provided_ft * height
    devices = [c for c in ctx.plan.all_elements()
               if getattr(c, "kind", None) is ConnectorKind.HOLD_DOWN
               and wall.tag in (getattr(c, "connects", ()) or ())]
    rows.inputs.append(Quantity(f"receiving_{wall.tag}_end_tension_lb", tension, "lb", 1.0))
    capacities = [(c, getattr(allowable_for_model(c.size or ""), "uplift_lb", None))
                  for c in devices]
    capacities = [(c, cap) for c, cap in capacities if cap]
    if not capacities:
        rows.missing.append(
            f"a hold-down on `{wall.tag}` for the delivered increment: "
            f"{force:,.1f} lb over {provided_ft:.3f}' x {height:.3f}' is {tension:,.1f} lb at "
            f"a panel end beside an opening, outside what the prescriptive line was designed "
            f"for, and no dead load is credited against it")
        return
    device, capacity = min(capacities, key=lambda row: row[1])
    rows.element_tags.append(device.tag)
    rows.states.append(LimitState(
        f"{wall.tag} overturning, delivered increment", tension, capacity, "lb",
        f"{device.size} ({device.tag}); v = {force:,.1f} / {provided_ft:.3f} = "
        f"{force / provided_ft:.2f} plf over h {height:.3f}', NO dead load credited. The "
        f"line's corner ends are R602.10.7 returns and take the same increment as detailing"))


def _receiving_roof(ctx: Any, rows: DeliveryRows, receiver: Any, resolved: Any,
                    far: list[tuple[Any, Any]], shear: float, resultant: float | None,
                    axis: str) -> None:
    """The receiving deck's unit-shear increment and its lines, lever rule on the resultant."""
    from typehaus.engineering.diaphragm_basis import (
        DIAPHRAGM_ASPECT_BLOCKED,
        DIAPHRAGM_ASPECT_UNBLOCKED,
    )
    from typehaus.engineering.lateral_lines import _ends_ft, panel_geometry_ft

    if resolved is None or resultant is None or len(far) < 2:
        rows.missing.append(
            f"two receiving lines under {receiver.tag} and a resultant to split between "
            f"them — a single line cannot take a load it does not stand under")
        return
    index = 0 if axis == "y" else 1
    placed = []
    for wall, line in far:
        ends = _ends_ft(ctx, wall)
        placed.append(((ends[0][index] + ends[1][index]) / 2.0, wall, line))
    placed.sort(key=lambda row: row[0])
    (lo, w_lo, l_lo), (hi, w_hi, l_hi) = placed[0], placed[-1]
    span = hi - lo
    if span <= 0.0:
        return
    to_hi = shear * (resultant - lo) / span
    to_lo = shear - to_hi
    # The depth is the receiving WALLS' own length — the boundary the shear enters them
    # along — not the roof's footprint, whose overhang carries no boundary shear.
    lengths = [panel_geometry_ft(ctx, w)[0] for w, _ in far if panel_geometry_ft(ctx, w)]
    depth = min(lengths) if lengths else 0.0
    if depth <= 0.0:
        return
    spec = receiver.diaphragm
    limit = DIAPHRAGM_ASPECT_BLOCKED if spec.blocked else DIAPHRAGM_ASPECT_UNBLOCKED
    rows.states += [
        LimitState(f"{receiver.tag} unit-shear increment", max(to_hi, to_lo) / depth,
                   spec.unit_shear_asd_plf, "plf",
                   f"{spec.source}; the {_direction(axis)} {shear:,.1f} lb enters along its "
                   f"edge at {resultant:.3f}' and splits by the lever rule, {to_lo:,.1f} lb "
                   f"to {w_lo.tag} and {to_hi:,.1f} lb to {w_hi.tag}, over {depth:.2f}' of "
                   f"depth. The INCREMENT — its own roof shear is the prescriptive path's"),
        LimitState(f"{receiver.tag} span-to-depth", span / depth, limit, "",
                   f"SDPWS Table 4.2.4, {'blocked' if spec.blocked else 'unblocked'}: "
                   f"{span:.2f}' between {w_lo.tag} and {w_hi.tag} over {depth:.2f}'",
                   is_detailing=True)]
    for wall, line, force in ((w_lo, l_lo, to_lo), (w_hi, l_hi, to_hi)):
        reading = _surplus(ctx, rows, line.wall)
        if reading is not None:
            _line_rows(ctx, rows, wall, line, force, reading, axis, False)
