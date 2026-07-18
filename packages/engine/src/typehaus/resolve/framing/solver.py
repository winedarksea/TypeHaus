"""Wall framing solver (#20) — pure deterministic (polygons, spec) -> [FramedMember].

Members are lightweight records (no geometry kernel) until emit (risk 6). M1 handles
level wall tops only; the raked-top/rafter arm activates with M3 roofs (→ 30 WP3.11).
"""

from __future__ import annotations

from typehaus.model.enums import LayerFunction
from typehaus.model.plan import PlanModel
from typehaus.resolve.framing.tables import (
    DEFAULT_SPACING,
    header_size,
    king_jack_counts,
    member_actual,
)
from typehaus.resolve.geometry import add, length, scale, sub, unit
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedWall


def _structure_layer(plan: PlanModel, assembly_tag: str):
    asm = plan.library.resolve_assembly(assembly_tag)
    if asm is None:
        return None
    for layer in asm.layers:
        if layer.function is LayerFunction.STRUCTURE:
            return layer
    return None


def frame_wall(plan: PlanModel, rw: ResolvedWall, openings: list) -> tuple[FramedMember, ...]:
    """Generate studs, plates, and opening framing for one resolved wall.

    ``openings`` is a list of (center_m, width_m, height_m, sill_m, is_door) tuples.
    """
    layer = _structure_layer(plan, rw.assembly)
    if layer is None or layer.masonry is not None:
        return ()  # masonry walls take the arithmetic-takeoff path, no members (#23)
    spec = layer.framing
    if spec is None:
        return ()

    p0, p1 = rw.axis
    axis_len = length(sub(p1, p0))
    d = unit(sub(p1, p0))
    spacing = (spec.spacing or DEFAULT_SPACING).meters
    member = spec.member
    z0, z1 = rw.z0_m, rw.z1_m
    plate_h = 1.5 * 0.0254

    members: list[FramedMember] = []

    # --- plates ---------------------------------------------------------------
    members.append(_plate(rw, p0, p1, "plate-bottom", z0, z0 + plate_h))
    top_plates = 2 if spec.double_top_plate and not spec.advanced_framing else 1
    for i in range(top_plates):
        zt = z1 - plate_h * (i + 1)
        members.append(_plate(rw, p0, p1, f"plate-top-{i}", zt, zt + plate_h))

    # --- studs at spacing, skipping those inside an opening's rough width ------
    stud_z0 = z0 + plate_h
    stud_z1 = z1 - plate_h * top_plates
    n = int(axis_len // spacing)
    idx = 0
    for i in range(n + 1):
        s = i * spacing
        if s > axis_len + 1e-6:
            break
        if _inside_opening(s, openings):
            continue
        pt = add(p0, scale(d, s))
        members.append(
            FramedMember(rw.uid, f"stud-{idx:03d}", "stud", member, pt, pt,
                         stud_z0, stud_z1, stud_z1 - stud_z0)
        )
        idx += 1

    # --- opening framing (king/jack/header/cripple/sill) ----------------------
    for oi, (center, width, height, sill, is_door) in enumerate(openings):
        members.extend(
            _frame_opening(rw, d, p0, center, width, height, sill, is_door, member,
                           stud_z0, stud_z1, oi)
        )
    return tuple(members)


def _plate(rw: ResolvedWall, p0, p1, key: str, z0: float, z1: float) -> FramedMember:
    return FramedMember(rw.uid, key, "plate", "plate", p0, p1, z0, z1, length(sub(p1, p0)))


def _inside_opening(s: float, openings) -> bool:
    for (center, width, _h, _sill, _door) in openings:
        if center - width / 2 - 0.02 <= s <= center + width / 2 + 0.02:
            return True
    return False


def _frame_opening(rw, d, p0, center, width, height, sill, is_door, member,
                   z0, z1, oi) -> list[FramedMember]:
    from typehaus.quantities import m as _m

    out: list[FramedMember] = []
    kings, jacks = king_jack_counts(_m(width))
    half = width / 2
    header_bottom = (z0 + sill + height) if not is_door else (z0 + height)
    for side, sign in (("l", -1), ("r", +1)):
        edge = center + sign * half
        for k in range(kings):
            pos = add(p0, scale(d, edge + sign * (0.04 + k * 0.04)))
            out.append(FramedMember(rw.uid, f"king-{oi}-{side}{k}", "king", member,
                                    pos, pos, z0, z1, z1 - z0))
        for j in range(jacks):
            pos = add(p0, scale(d, edge + sign * (0.01 + j * 0.04)))
            out.append(FramedMember(rw.uid, f"jack-{oi}-{side}{j}", "jack", member,
                                    pos, pos, z0, header_bottom, header_bottom - z0))
    hl = add(p0, scale(d, center - half))
    hr = add(p0, scale(d, center + half))
    out.append(FramedMember(rw.uid, f"header-{oi}", "header",
                            header_size(_m(width), rw is not None), hl, hr,
                            header_bottom, header_bottom + 0.14, width))
    return out


def frame_model(plan: PlanModel, model: ResolvedModel) -> None:
    """Attach framed members to every resolved wall (mutates the model in place)."""
    by_host: dict[str, list] = {}
    for op in model.openings:
        by_host.setdefault(op.host_wall, []).append(
            (op.center_along_m, op.width_m, op.height_m, op.sill_m, op.is_door)
        )
    framed: list[ResolvedWall] = []
    for rw in model.walls:
        members = frame_wall(plan, rw, by_host.get(rw.tag, []))
        framed.append(
            ResolvedWall(
                uid=rw.uid, tag=rw.tag, storey=rw.storey, assembly=rw.assembly,
                axis=rw.axis, layers=rw.layers, z0_m=rw.z0_m, z1_m=rw.z1_m,
                is_foundation=rw.is_foundation, members=members,
            )
        )
    model.walls = framed
