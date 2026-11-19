"""A leafless through opening's drywall wrap (owner decision 2026-11-07, #122; → drywall_trims).

A walk-through passage with no leaf takes no casing: each gypsum face's board returns into
the reveal, and the face's outside corners take the standard's corner bead up both jambs
and across the head. Nothing runs along the floor, so a floor transition under the passage
(oak to tile) changes nothing. A pass-through off the floor (a sill) also returns across
the sill and beads it. A face without gypsum (a brick reveal) is skipped, as are blind ROs
and penetrations (``ResolvedOpening.is_leafless_through``).

Each gypsum face is one ``ResolvedPassageWrap`` record on ``model.passage_wraps``: its bead
and its share of the reveal's return strips (board and coatings, half the core depth each,
all of it when the other face is bare), billed as window returns are
(``takeoff/passage_wraps.py``). The return board and its paint skin are drawn as
``passage_return`` solids hosted on the opening.

Known limits: the jamb probe reads 0.3-1.0 m above the floor and the finish run comes from the
wall-wide ``depth_layers()``, so a tile or wainscot band can mislead either; the bead runs to
the RO head at the full RO width, ~1.5" a face over the wrapped opening.
"""

from __future__ import annotations

from typehaus.resolve.coatings import COATING_SKIN_M
from typehaus.resolve.drywall_trims import TrimContext, room_floor
from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.geometry_door_products import finish_faces
from typehaus.resolve.interior_trim_scope import face_is_gypsum
from typehaus.resolve.model import ResolvedSolid
from typehaus.resolve.model_trim import ResolvedPassageWrap
from typehaus.resolve.room_lookup import room_owning

_CATEGORY = "passage_return"
_ROOM_PROBE_M = 0.15
_JAMB_PROBE_M = 0.05
# The face over the head (and under a sill) is probed in this band off it.
_EDGE_PROBE = (0.02, 0.10)
_JAMB_PROBE = (0.3, 1.0)


def passage_wraps(ctx: TrimContext) -> None:
    """Emit each face's record, board and paint skin, and its corner beads. Idempotent."""
    model = ctx.model
    model.solids[:] = [s for s in model.solids if s.category != _CATEGORY]
    model.passage_wraps.clear()
    if ctx.standard is None:
        return
    walls = {wall.tag: wall for wall in model.walls}
    for opening in sorted(model.openings, key=lambda o: o.uid):
        wall = walls.get(opening.host_wall)
        if not opening.is_leafless_through or wall is None:
            continue
        for record, solids in _faces(model, ctx.materials, opening, wall):
            model.passage_wraps.append(record)
            model.solids.extend(solids)
            ctx.add("outside_corner", record.room, record.storey,
                    ctx.standard.outside_corner_ref, record.bead_length_m,
                    (record.opening, record.room or ""))


def _faces(model, materials, opening, wall) -> list[tuple[ResolvedPassageWrap, list]]:
    origin, tangent, normal, axis_length = wall_frame(wall)
    faces = finish_faces(wall)
    if axis_length <= 1e-9 or faces is None:
        return []
    cx = origin[0] + tangent[0] * opening.center_along_m
    cy = origin[1] + tangent[1] * opening.center_along_m
    sill_z = wall.base_ref_z_m + opening.sill_m
    head_z = sill_z + opening.height_m
    has_sill = not opening.is_passage
    runs = _finish_runs(wall, materials, origin, normal)
    core = (faces[1] - faces[0]) - sum(t for run in runs.values() for _m, t in run)
    found = []
    for side, face in ((1, faces[1]), (-1, faces[0])):
        lift = face + side * _ROOM_PROBE_M
        room = room_owning(model, wall.storey, (cx + normal[0] * lift, cy + normal[1] * lift))
        floor_z = sill_z if has_sill or room is None else room_floor(model, room)
        into = (-normal[0] * side, -normal[1] * side)

        def gypsum(along: float, z0: float, z1: float, face=face, into=into) -> bool:
            point = (cx + tangent[0] * along + normal[0] * face,
                     cy + tangent[1] * along + normal[1] * face)
            return face_is_gypsum(wall, point, into, z0, z1, materials)

        jamb = opening.width_m / 2.0 + _JAMB_PROBE_M
        probe = (floor_z + _JAMB_PROBE[0], min(floor_z + _JAMB_PROBE[1], head_z))
        jambs = tuple(sign for sign in (-1.0, 1.0) if gypsum(sign * jamb, *probe))
        head = gypsum(0.0, head_z + _EDGE_PROBE[0], head_z + _EDGE_PROBE[1])
        sill = has_sill and gypsum(0.0, sill_z - _EDGE_PROBE[1], sill_z - _EDGE_PROBE[0])
        if jambs or head or sill:
            found.append((side, face, room, floor_z, jambs, head, sill))
    out = []
    for side, face, room, floor_z, jambs, head, sill in found:
        record = ResolvedPassageWrap(
            opening=opening.tag, storey=wall.storey, room=room.tag if room else None,
            height_m=head_z - floor_z, width_m=opening.width_m, jambs=len(jambs), head=head,
            sill=sill, depth_m=max(core, 0.0) / len(found), finish=runs[side])
        frame = (cx, cy, tangent, normal)
        out.append((record, _solids(opening, wall, record, frame, (side, face, jambs),
                                    floor_z, head_z, materials)))
    return out


def _solids(opening, wall, record, frame, where, floor_z, head_z, materials) -> list:
    """The return board on each wrapped edge and the paint skin on its reveal face.

    Each board stands inside the RO, its back on the framing, from the finish face back
    through the field board's cut edge and this face's share of the core.
    """
    cx, cy, tangent, normal = frame
    side, face, jamb_signs = where
    board = [(m, t) for m, t in record.finish if t > 0]
    coat = next((m for m, _t in record.finish
                 if getattr(materials.get(m), "coating", False)), None)
    if not board:
        return []
    thick = sum(t for _m, t in board)
    reach = face - side * (thick + record.depth_m)
    near, far = sorted((face, reach))
    half = opening.width_m / 2
    z0 = floor_z + (thick if record.sill else 0.0)
    z1 = head_z - (thick if record.head else 0.0)

    def ring(a0: float, a1: float, n0: float = near, n1: float = far):
        def at(a, n):
            return (cx + tangent[0] * a + normal[0] * n, cy + tangent[1] * a + normal[1] * n)
        return (at(a0, n0), at(a1, n0), at(a1, n1), at(a0, n1))

    jambs = [(s, "jamb-left" if s < 0 else "jamb-right") for s in jamb_signs]
    pieces = [(edge, ring(min(s * half, s * (half - thick)), max(s * half, s * (half - thick))),
               z0, z1) for s, edge in jambs]
    if record.head:
        pieces.append(("head", ring(-half, half), head_z - thick, head_z))
    if record.sill:
        pieces.append(("sill", ring(-half, half), floor_z, floor_z + thick))
    skins = []
    if coat is not None:
        inner = half - thick
        skins = [(f"paint-{edge}", ring(min(s * inner, s * (inner - COATING_SKIN_M)),
                                        max(s * inner, s * (inner - COATING_SKIN_M))), z0, z1)
                 for s, edge in jambs]
        if record.head:
            skins.append(("paint-head", ring(-inner, inner), z1 - COATING_SKIN_M, z1))
        if record.sill:
            skins.append(("paint-sill", ring(-inner, inner), z0, z0 + COATING_SKIN_M))
    key = "A" if side > 0 else "B"
    return [ResolvedSolid(
        uid=f"{opening.uid}-WRAP{key}-{edge}", tag=f"{opening.tag}-wrap-{key.lower()}-{edge}",
        storey=wall.storey, category=_CATEGORY, outline=outline, z0_m=lo, z1_m=hi,
        material=coat if edge.startswith("paint-") else board[-1][0], host_ref=opening.tag)
        for edge, outline, lo, hi in (*pieces, *skins) if hi - lo > 1e-9]


def _finish_runs(wall, materials, origin, normal) -> dict[int, tuple[tuple[str, float], ...]]:
    """Each face's board and coatings, read inward from that face until the first layer
    that is neither."""
    def offset(layer) -> float:
        return sum((p[0] - origin[0]) * normal[0] + (p[1] - origin[1]) * normal[1]
                   for p in layer.polygon) / max(len(layer.polygon), 1)

    layers = sorted((layer for layer in wall.depth_layers() if len(layer.polygon) >= 3),
                    key=offset)
    runs: dict[int, tuple[tuple[str, float], ...]] = {}
    for side, ordered in ((1, layers[::-1]), (-1, layers)):
        run = []
        for layer in ordered:
            material = materials.get(layer.material_ref)
            if not (getattr(material, "coating", False)
                    or getattr(material, "gypsum_type", None) is not None):
                break
            run.append((layer.material_ref, layer.thickness_m))
        runs[side] = tuple(run)
    return runs
