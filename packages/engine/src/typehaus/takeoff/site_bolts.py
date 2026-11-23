"""Site-length through-bolts and lags for bolted angles (decision #147).

A ``ConnectorFastening.site_bolts`` entry names a bolt or lag per leg. A bolt's length is
the grip, measured along the bolt line from the leg face through the contiguous wood behind
it (framing members, beams and the tied wall's structure and sheathing layers), plus the
angle's steel, a washer, the nut and two threads, rounded up to the next stocked length.
A lag takes its schedule's minimum (HL fn 7). Oracle: catlin ``notes/hl_site_bolts.md``.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from shapely.geometry import LineString, Point, Polygon

from typehaus.hardware.catalog import (
    ROLE_SITE_BOLT,
    ROLE_SITE_LAG,
    hardware_by_model,
    structural_hardware_catalog,
)
from typehaus.hardware.connector_fastening import connector_fastening
from typehaus.hardware.plan_geometry import centerline_endpoints
from typehaus.model.enums import LayerFunction
from typehaus.model.structure import Connector
from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.bases_caps import (
    ANGLE_DIMENSIONS,
    STEEL_GAUGE_THICKNESS_IN,
)
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_row import hardware_row

#: ASME B18.2.2 heavy-hex nut height and ASME B18.22.1 Type A (USS) washer thickness, and
#: the UNC pitch (threads per inch), by bolt diameter. Two threads stand past the nut.
_NUT_IN = {0.5: 31 / 64, 0.75: 47 / 64}
_WASHER_IN = {0.5: 0.097, 0.75: 0.134}
_TPI = {0.5: 13, 0.75: 10}
_REACH_M = 24 * M_PER_IN  # the longest grip looked for
_JOIN_M = 0.125 * M_PER_IN  # a gap this small is still one stack
_WOOD_LAYERS = (LayerFunction.STRUCTURE.value, LayerFunction.SHEATHING.value)


def bolt_allowance_in(diameter_in: float) -> float:
    """Washer + nut + two threads past the nut, added to grip and steel."""
    return _WASHER_IN[diameter_in] + _NUT_IN[diameter_in] + 2 / _TPI[diameter_in]


def stocked_length_in(needed_in: float, lengths) -> float:
    """The shortest stocked length at or over ``needed_in``."""
    fits = [length for length in sorted(lengths) if length >= needed_in - 1e-6]
    if not fits:
        raise LookupError(f"no stocked length reaches {needed_in:.2f} in")
    return fits[0]


def _unit(vector) -> tuple[float, float]:
    norm = math.hypot(*vector)
    return (vector[0] / norm, vector[1] / norm)


def _member_axis(model: ResolvedModel, tag: str):
    """(centre, along-axis unit) of a beam solid or wall, or ``None``."""
    wall = model.wall(tag)
    if wall is not None:
        (x0, y0), (x1, y1) = wall.axis
        return ((x0 + x1) / 2, (y0 + y1) / 2), _unit((x1 - x0, y1 - y0))
    solid = next((s for s in model.solids if s.tag == tag and len(s.outline) >= 3), None)
    if solid is None:
        return None
    (x0, y0), (x1, y1) = centerline_endpoints(list(solid.outline))
    return ((x0 + x1) / 2, (y0 + y1) / 2), _unit((x1 - x0, y1 - y0))


def _wood_footprints(model: ResolvedModel, z_m: float, tag: str) -> list[Polygon]:
    """Plan footprints of wood at ``z_m``: horizontal members, beams, the tied wall's layers."""
    out = []
    for member in model.all_members():
        if not (member.z0_m - 1e-6 <= z_m <= member.z1_m + 1e-6) or member.p0 == member.p1:
            continue
        width = member.plan_width_m or cross_section(member.profile).width_m
        out.append(LineString([member.p0[:2], member.p1[:2]]).buffer(width / 2, cap_style=2))
    for solid in model.solids:
        if solid.category in ("beam", "post") and len(solid.outline) >= 3 \
                and solid.z0_m - 1e-6 <= z_m <= solid.z1_m + 1e-6:
            out.append(Polygon(solid.outline))
    wall = model.wall(tag)
    if wall is not None and wall.z0_m <= z_m <= wall.z1_m:
        for layer in wall.layers:
            low = wall.z0_m if layer.z0_m is None else layer.z0_m
            high = wall.z1_m if layer.z1_m is None else layer.z1_m
            function = getattr(layer.function, "value", layer.function)
            if function in _WOOD_LAYERS and not layer.is_cavity \
                    and len(layer.polygon) >= 3 and low <= z_m <= high:
                out.append(Polygon(layer.polygon))
    return out


def grip_in(model: ResolvedModel, connector: Connector, z_m: float, leg: int,
            from_heel_in: float) -> float:
    """Contiguous wood behind the leg on ``connects[leg]``, along the bolt line, inches."""
    tag = connector.connects[leg]
    frame = _member_axis(model, tag)
    if frame is None:
        raise LookupError(f"{connector.tag}: cannot place a bolt in {tag!r}")
    centre, along = frame
    face = connector.position.xy_m
    # The hole stands D3 off the heel, i.e. toward the member's middle along its axis.
    to_centre = (centre[0] - face[0], centre[1] - face[1])
    sign = 1.0 if to_centre[0] * along[0] + to_centre[1] * along[1] >= 0 else -1.0
    hole = (face[0] + sign * along[0] * from_heel_in * M_PER_IN,
            face[1] + sign * along[1] * from_heel_in * M_PER_IN)
    across = (-along[1], along[0])
    if to_centre[0] * across[0] + to_centre[1] * across[1] < 0:
        across = (-across[0], -across[1])
    ray = LineString([hole, (hole[0] + across[0] * _REACH_M, hole[1] + across[1] * _REACH_M)])
    spans = []
    for footprint in _wood_footprints(model, z_m, tag):
        hit = ray.intersection(footprint)
        for piece in getattr(hit, "geoms", [hit]):
            if piece.is_empty or piece.length <= 0:
                continue
            a, b = (ray.project(Point(c)) for c in (piece.coords[0], piece.coords[-1]))
            spans.append((min(a, b), max(a, b)))
    reach = 0.0
    for start, end in sorted(spans):
        if start > reach + _JOIN_M:
            break
        reach = max(reach, end)
    if reach <= 0.0:
        raise LookupError(f"{connector.tag}: no wood behind the leg on {tag!r}")
    return reach / M_PER_IN


def site_bolt_rows(model: ResolvedModel) -> list:
    """One row per (bolt or lag family, stocked length), by storey."""
    catalog = structural_hardware_catalog()
    solids = {solid.tag: solid for solid in model.solids}
    counts: dict[tuple, Counter] = defaultdict(Counter)
    notes: dict[tuple, list[str]] = defaultdict(list)
    for storey in model.plan.storeys:
        for connector in model.plan.storey_elements(storey.tag):
            if not isinstance(connector, Connector) or not connector.size:
                continue
            schedule = connector_fastening(connector.size)
            if schedule is None or not schedule.site_bolts:
                continue
            angle = hardware_by_model(connector.size)
            dims = ANGLE_DIMENSIONS.get(connector.size.removesuffix("HDG"))
            steel_in = STEEL_GAUGE_THICKNESS_IN[dims.gauge] if dims else 0.0
            solid = solids.get(connector.tag)
            z_m = (solid.z0_m + solid.z1_m) / 2 if solid else connector.elevation.meters
            for bolt in schedule.site_bolts:
                role = ROLE_SITE_BOLT if bolt.kind == "bolt" else ROLE_SITE_LAG
                item = next(i for i in catalog
                            if i.role == role and i.bolt_diameter_in == bolt.diameter_in)
                if bolt.kind == "bolt":
                    grip = grip_in(model, connector, z_m, bolt.leg,
                                   angle.bolt_from_heel_in or 0.0)
                    need = grip + steel_in + bolt_allowance_in(bolt.diameter_in)
                    why = (f"{grip:.3f} grip + {steel_in:.4f} steel + "
                           f"{bolt_allowance_in(bolt.diameter_in):.3f} washer/nut/2 threads")
                else:
                    need, why = bolt.min_length_in, f"lag minimum {bolt.min_length_in:g} in"
                length = stocked_length_in(max(need, bolt.min_length_in),
                                           item.part_number_by_length_in)
                key = (item.model, length)
                counts[key][storey.tag] += bolt.per_leg
                notes[key].append(f"{connector.tag} into {connector.connects[bolt.leg]}: "
                                  f"{why} = {need:.3f} in")
    rows = []
    for (model_name, length), by_storey in sorted(counts.items()):
        item = next(i for i in catalog if i.model == model_name)
        rows.append(hardware_row(
            item, scope="connector site bolts", count=sum(by_storey.values()),
            part_number=item.part_number_by_length_in[length], size=f'{length:g}"',
            by_storey=dict(sorted(by_storey.items())),
            basis="next stocked length over the need: " + "; ".join(notes[(model_name, length)])))
    return rows


#: A DTT2's seat (C-C-2026 p. 60: 14 ga), the steel the rod crosses at each end.
_DTT_SEAT_IN = 0.0747


def tension_rod_rows(model: ResolvedModel) -> list:
    """One 1/2" rod per DTT2Z pair on a common rod line (a tie each side of a wall): seat to
    seat, plus each seat's steel and a washer, nut and two threads past it."""
    from typehaus.library.hardware.site_bolts import TENSION_ROD_12

    by_line: dict[tuple, list] = defaultdict(list)
    storeys: dict[tuple, str] = {}
    for storey in model.plan.storeys:
        for el in model.plan.storey_elements(storey.tag):
            if isinstance(el, Connector) and el.size == "DTT2Z" and el.axis in ("x", "y"):
                x, y = el.position.xy_m
                across = round((y if el.axis == "x" else x) / M_PER_IN, 1)
                key = (tuple(el.connects), el.axis, across,
                       round(el.elevation.meters / M_PER_IN, 1) if el.elevation else None)
                by_line[key].append(el)
                storeys[key] = storey.tag
    counts: Counter = Counter()
    notes: dict[float, list[str]] = defaultdict(list)
    by_storey: dict[float, Counter] = defaultdict(Counter)
    allowance = bolt_allowance_in(0.5) + _DTT_SEAT_IN
    for key, ties in sorted(by_line.items(), key=lambda kv: str(kv[0])):
        if len(ties) != 2:
            continue
        a, b = (t.position.xy_m for t in ties)
        span = math.dist(a, b) / M_PER_IN
        need = span + 2 * allowance
        length = stocked_length_in(need, TENSION_ROD_12.part_number_by_length_in)
        counts[length] += 1
        by_storey[length][storeys[key]] += 1
        notes[length].append(f"{ties[0].tag} to {ties[1].tag}: {span:.3f} seat to seat + "
                             f"2 x {allowance:.3f} seat/washer/nut/2 threads = {need:.3f} in")
    return [hardware_row(
        TENSION_ROD_12, scope="connector site bolts", count=n,
        part_number=TENSION_ROD_12.part_number_by_length_in[length], size=f'{length:g}"',
        by_storey=dict(sorted(by_storey[length].items())),
        basis="next stock cut over the need: " + "; ".join(notes[length]))
        for length, n in sorted(counts.items())]
