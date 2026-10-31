"""The part of an air terminal behind its face: one box per register whose type has a neck.

A register resolves as its face (``RegisterType.footprint``/``height``, an inch deep). What
is in the cavity — a stamped boot, a disc valve's collar, an inline damper and its actuator —
was nowhere in the model, so nothing could say a boot did not fit its bay. The box is drawn
from ``TerminalNeck``: up from a ceiling face, down from a floor face, and into the host from
a wall face. ``mep.terminal_neck_fit`` grades it.

A ceiling face is the body's bottom and a floor face the body's top (``resolve/placeables``
puts the body in the board). A wall face's BACK is found, not assumed: the resolved rotation
does not say which side of the face the wall is on (two catlin sidewalls share a rotation
and face opposite ways): a hosted terminal's back is the side its wall's axis is on, and a
free one's is the side whose probe lands in a wall layer or a soffit.
"""

from __future__ import annotations

import math

from typehaus.resolve.model import ResolvedModel, ResolvedSolid

#: How far past the face the back-side probe looks for the host it is set in.
_PROBE_M = 0.05


def neck_boxes(model: ResolvedModel) -> list[tuple[str, tuple, float, float, str]]:
    """``(register tag, plan ring, z0, z1, part)`` for every register with a typed neck.

    A wall terminal whose back cannot be found comes back with an EMPTY ring, so the check
    can say so rather than skip it.
    """
    types = {t.tag: t for t in getattr(model.plan.library, "register_types", ())}
    out: list[tuple[str, tuple, float, float, str]] = []
    for obj in model.canvas_objects:
        product = types.get(obj.type_ref) if obj.kind == "Register" else None
        neck = getattr(product, "neck", None)
        if neck is None:
            continue
        box = (_box(model, obj, neck)
               if obj.mount is not None and obj.body_z0_m is not None else None)
        out.append((obj.tag, *(box or ((), 0.0, 0.0)), neck.part))
    return out


def _rotate(local: tuple[float, float], degrees: float) -> tuple[float, float]:
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return local[0] * c - local[1] * s, local[0] * s + local[1] * c


def _box(model: ResolvedModel, obj, neck) -> tuple[tuple, float, float] | None:
    width, height, depth = neck.width.meters, neck.height.meters, neck.depth.meters
    cx, cy = obj.position
    kind = getattr(obj.mount.kind, "value", obj.mount.kind)
    if kind in ("ceiling", "floor"):
        ring = _rectangle((cx, cy), _rotate((1.0, 0.0), obj.rotation_degrees),
                          _rotate((0.0, 1.0), obj.rotation_degrees), width, height,
                          centred=True)
        if kind == "ceiling":
            return ring, obj.body_z0_m, obj.body_z0_m + depth
        top = obj.body_z1_m if obj.body_z1_m is not None else obj.body_z0_m
        return ring, top - depth, top
    across = _rotate((1.0, 0.0), obj.rotation_degrees)
    back = _back(model, obj, _rotate((0.0, 1.0), obj.rotation_degrees))
    if back is None:
        return None
    face = _face_offset(obj, back)
    ring = _rectangle((cx + back[0] * face, cy + back[1] * face), across, back, width,
                      depth, centred=False)
    top = obj.body_z1_m if obj.body_z1_m is not None else obj.body_z0_m
    mid = (obj.body_z0_m + top) / 2.0
    return ring, mid - height / 2.0, mid + height / 2.0


def _rectangle(origin, u, v, width: float, extent: float, *, centred: bool) -> tuple:
    """A ring ``width`` along ``u`` and ``extent`` along ``v``: centred on ``origin`` both
    ways, or running from ``origin`` in ``+v`` (a wall neck behind its face)."""
    ox, oy = origin
    half = width / 2.0
    lo, hi = (-extent / 2.0, extent / 2.0) if centred else (0.0, extent)
    return tuple((ox + u[0] * a + v[0] * b, oy + u[1] * a + v[1] * b)
                 for a, b in ((-half, lo), (half, lo), (half, hi), (-half, hi)))


def _face_offset(obj, back: tuple[float, float]) -> float:
    """Distance from the body's centre to its back face, read off the footprint."""
    cx, cy = obj.position
    return max((x - cx) * back[0] + (y - cy) * back[1] for x, y in obj.footprint)


def _back(model: ResolvedModel, obj, axis: tuple[float, float]) -> tuple[float, float] | None:
    """Which of ``±axis`` points into the host: a wall's layers or a soffit's box."""
    from shapely.geometry import Point, Polygon

    wall = model.wall(obj.attachment_wall) if obj.attachment_wall else None
    if wall is not None and len(wall.axis) >= 2:
        # Hosted: the back is the side the wall's axis is on, recessed or not.
        from shapely.geometry import LineString

        line = LineString([wall.axis[0], wall.axis[-1]])
        here = line.distance(Point(obj.position))
        step = [(sign, line.distance(Point(obj.position[0] + axis[0] * sign * 0.01,
                                            obj.position[1] + axis[1] * sign * 0.01)))
                for sign in (1.0, -1.0)]
        sign, nearer = min(step, key=lambda item: item[1])
        if here < 1e-6 or nearer >= here:
            return None
        return axis[0] * sign, axis[1] * sign
    # Free-standing on a face (a soffit lining): the side whose probe lands in a host.
    hosts = [Polygon(layer.polygon) for host in model.walls if host.storey == obj.storey
             for layer in host.layers if len(layer.polygon) >= 3]
    hosts += [Polygon(s.outline) for s in model.soffits
              if s.storey == obj.storey and len(s.outline) >= 3]
    hits = []
    for sign in (1.0, -1.0):
        direction = (axis[0] * sign, axis[1] * sign)
        reach = _face_offset(obj, direction) + _PROBE_M
        probe = Point(obj.position[0] + direction[0] * reach,
                      obj.position[1] + direction[1] * reach)
        if any(host.covers(probe) for host in hosts):
            hits.append(direction)
    return hits[0] if len(hits) == 1 else None


def emit_terminal_necks(model: ResolvedModel) -> None:
    """Append each neck as a ``terminal_neck`` solid on its register's storey."""
    storeys = {obj.tag: obj.storey for obj in model.canvas_objects}
    for tag, ring, z0, z1, _part in neck_boxes(model):
        if not ring:
            continue
        uid = next((o.uid for o in model.canvas_objects if o.tag == tag), tag)
        model.solids.append(ResolvedSolid(
            uid=f"{uid}-neck", tag=f"{tag}-NECK", storey=storeys[tag],
            category="terminal_neck", outline=ring, z0_m=z0, z1_m=z1))
