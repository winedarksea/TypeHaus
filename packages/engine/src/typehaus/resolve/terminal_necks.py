"""The parts behind an air terminal: legacy boot boxes or a dimensioned ceiling assembly.

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
    """``(register tag, plan ring, z0, z1, part)`` for every physical or clearance envelope.

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
        if neck.components:
            for component in neck.components:
                box = component_box(obj, component)
                out.append((obj.tag, *(box or ((), 0.0, 0.0)), component.part))
            continue
        box = (_box(model, obj, neck)
               if obj.mount is not None and obj.body_z0_m is not None else None)
        out.append((obj.tag, *(box or ((), 0.0, 0.0)), neck.part))
    return out


def component_box(obj, component) -> tuple[tuple, float, float] | None:
    """Place one ceiling component using the same face plane as the legacy neck."""
    if obj.mount is None or obj.mount.kind.value != "ceiling" or obj.body_z0_m is None:
        return None
    dx, dy = _rotate(tuple(v.meters for v in component.offset[:2]), obj.rotation_degrees)
    ring = _rectangle((obj.position[0] + dx, obj.position[1] + dy),
                      _rotate((1.0, 0.0), obj.rotation_degrees),
                      _rotate((0.0, 1.0), obj.rotation_degrees),
                      component.width.meters, component.height.meters, centred=True)
    bottom = obj.body_z0_m + component.offset[2].meters
    return ring, bottom, bottom + component.depth.meters


def terminal_inlet(model: ResolvedModel, tag: str):
    """World-space (centre, outward normal, width, height), or None if not placeable."""
    obj = next((o for o in model.canvas_objects if o.tag == tag and o.kind == "Register"), None)
    if obj is None or obj.mount is None:
        return None
    catalog = next((t for t in model.plan.library.register_types if t.tag == obj.type_ref), None)
    inlet = catalog.neck.inlet if catalog is not None and catalog.neck is not None else None
    if inlet is None or obj.body_z0_m is None:
        return None
    if obj.mount.kind.value == "ceiling":
        dx, dy = _rotate(tuple(v.meters for v in inlet.position[:2]), obj.rotation_degrees)
        return ((obj.position[0] + dx, obj.position[1] + dy,
                 obj.body_z0_m + inlet.position[2].meters),
                _rotate(inlet.normal, obj.rotation_degrees),
                inlet.width.meters, inlet.height.meters)
    if obj.mount.kind.value != "wall":
        return None
    across = _rotate((1.0, 0.0), obj.rotation_degrees)
    back = _back(model, obj, _rotate((0.0, 1.0), obj.rotation_degrees))
    if back is None or obj.body_z1_m is None:
        return None
    along, behind, up = (v.meters for v in inlet.position)
    behind += _face_offset(obj, back)
    return ((obj.position[0] + across[0] * along + back[0] * behind,
             obj.position[1] + across[1] * along + back[1] * behind,
             (obj.body_z0_m + obj.body_z1_m) / 2 + up),
            (across[0] * inlet.normal[0] + back[0] * inlet.normal[1],
             across[1] * inlet.normal[0] + back[1] * inlet.normal[1]),
            inlet.width.meters, inlet.height.meters)


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
    """Draw parts, with a shared inspect group; quantities come from the catalog parts."""
    types = {t.tag: t for t in model.plan.library.register_types}
    for obj in model.canvas_objects:
        catalog = types.get(obj.type_ref) if obj.kind == "Register" else None
        neck = getattr(catalog, "neck", None)
        if neck is None:
            continue
        if neck.components:
            for component in neck.components:
                if component.clearance_only:
                    continue
                box = component_box(obj, component)
                if box is None:
                    continue
                ring, z0, z1 = box
                # Keep the established NECK pick identity for the boot itself.
                suffix = "NECK" if component.tag == "BOOT" else f"NECK-{component.tag}"
                model.solids.append(ResolvedSolid(
                    uid=f"{obj.uid}-{suffix.lower()}", tag=f"{obj.tag}-{suffix}",
                    storey=obj.storey, category="terminal_neck", outline=ring,
                    z0_m=z0, z1_m=z1, product=component.product_ref,
                    host_ref=obj.tag, group=obj.tag))
        else:
            box = (_box(model, obj, neck)
                   if obj.mount is not None and obj.body_z0_m is not None else None)
            if box is None:
                continue
            ring, z0, z1 = box
            model.solids.append(ResolvedSolid(
                uid=f"{obj.uid}-neck", tag=f"{obj.tag}-NECK", storey=obj.storey,
                category="terminal_neck", outline=ring, z0_m=z0, z1_m=z1,
                product=neck.product_ref, host_ref=obj.tag))
