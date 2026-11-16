"""A terminal neck's sheet metal: a closed box with a face lip, its duct joint cut.

Local frame (``terminal_geometry.terminal_frame``): x across the face, y its other
dimension (up on a wall), z depth into the cavity from the neck's face plane. A rectangular
neck is four walls and a back of the house's sheet (``DuctStandard.gauge_for`` at the neck's
larger side, else ``VISUALIZATION.sheet_m``), open at the face, with a lip round the face on
the grille's back: 1/2" or the grille's frame margin, whichever is less.

The duct's joint face is cut: an authored ``neck.inlet`` on whichever face its normal names;
else a stated ``neck.entry`` (``ENTRY_AXES``), cut to the named run's section; else the back
is left open (the run's own boot mates the whole back; a transfer sleeve has no run). A
``separate_boot`` damper box and a round collar stay open sleeves (``tube``).

Once the joints are known (after ``duct_parts``): ``boot_drawn`` names the plain necks whose
bought boot is drawn and trimmed at rather than stood in for (a 90), and ``joint_necks``
re-cuts a neck whose boot's collar enters its side.

Walls overlap at the corners by half a sheet, never sharing an edge, so each piece is a
closed solid on its own and the combined mesh stays manifold.
"""
from __future__ import annotations

from typing import Any

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import combine_meshes, transform_mesh
from typehaus.resolve.geometry_panel import panel
from typehaus.resolve.terminal_geometry import (
    VISUALIZATION,
    circle,
    rectangle,
    terminal_frame,
    tube,
)

#: The lip round a neck's face, at most: the boot flange a grille's frame covers.
LIP_M = 0.5 * M_PER_IN
_MIN_LIP_M = M_PER_IN / 32.0

#: ``neck.entry`` -> (local axis, sign) per mount kind. Left/right are the face's own -x/+x
#: (``terminal_frame``'s across); on a ceiling or floor "top"/"bottom" is the back.
ENTRY_AXES: dict[str, dict[str, tuple[int, int]]] = {
    "wall": {"back": (2, 1), "bottom": (1, -1), "top": (1, 1), "left": (0, -1),
             "right": (0, 1)},
    "ceiling": {"back": (2, 1), "top": (2, 1), "left": (0, -1), "right": (0, 1)},
    "floor": {"back": (2, 1), "bottom": (2, 1), "left": (0, -1), "right": (0, 1)},
}


def _shift(ring, du, dv):
    return tuple((a + du, b + dv) for a, b in ring)


def neck_box(width, height, depth, inlet=None, open_back=False, sheet_m=None,
             lip_m=LIP_M, lip_z=0.0):
    """The closed box (module docstring). ``inlet`` = (local centre, local unit normal,
    opening ring in that face's panel coordinates, centred on 0)."""
    t = min(sheet_m or VISUALIZATION.sheet_m, width / 4, height / 4, depth / 4)
    w, h, d = width, height, depth
    holes_on = {}
    if inlet is not None:
        (px, py, pz), normal, opening = inlet
        for axis in range(3):
            for sign in (-1, 1):
                if normal[axis] * sign > 0.99:
                    du, dv = ((py, pz - d / 2) if axis == 0 else (px, pz - d / 2)
                              if axis == 1 else (px, py))
                    holes_on[(axis, sign)] = (_shift(opening, du, dv),)
    parts = []
    for sign in (-1, 1):  # x walls span the full height; y walls stop half a sheet inside
        sheet = panel(rectangle(h, d), holes_on.get((0, sign), ()), 0, t)
        parts.append(transform_mesh(sheet, (w / 2 - t if sign > 0 else -w / 2, 0, d / 2),
                                    (0, 1, 0), (0, 0, 1), (1, 0, 0)))
        sheet = panel(rectangle(w - t, d), holes_on.get((1, sign), ()), 0, t)
        parts.append(transform_mesh(sheet, (0, h / 2 - t if sign > 0 else -h / 2, d / 2),
                                    (1, 0, 0), (0, 0, 1), (0, 1, 0)))
    if not open_back or (2, 1) in holes_on:
        parts.append(panel(rectangle(w - t, h - t), holes_on.get((2, 1), ()), d - t, d))
    if lip_m >= _MIN_LIP_M:
        z = min(max(lip_z, 0.0), d - 2 * t)
        parts.append(panel(rectangle(w + 2 * lip_m, h + 2 * lip_m),
                           (rectangle(w - t, h - t),), z, z + t))
    return combine_meshes(*parts)


def _sheet_m(model: Any, neck: Any) -> float | None:
    from typehaus.resolve.duct_standard import duct_standard

    standard, _ = duct_standard(getattr(model, "plan", None))
    row = (standard.gauge_for(max(neck.width.meters, neck.height.meters))
           if standard is not None else None)
    return row.thickness.meters if row is not None else None


def _run_section(model: Any, tag: str) -> tuple[bool, float, float] | None:
    """(round, width, depth) of the run the register names, from the plan."""
    plan = getattr(model, "plan", None)
    el = plan.by_tag(tag) if hasattr(plan, "by_tag") else None
    run = plan.by_tag(el.duct_ref) if getattr(el, "duct_ref", None) else None
    if run is None:
        return None
    if getattr(run, "diameter", None) is not None:
        return True, run.diameter.meters, run.diameter.meters
    if getattr(run, "width", None) is not None and getattr(run, "depth", None) is not None:
        return False, run.width.meters, run.depth.meters
    return None


def _entry_inlet(model, obj, neck, kind, t):
    """The stated entry face as an inlet cut to the run's section, or None."""
    axis, sign = ENTRY_AXES.get(kind, {}).get(neck.entry, (2, 1))
    w, h, d = neck.width.meters, neck.height.meters, neck.depth.meters
    centre = [0.0, 0.0, d / 2]
    centre[axis] = sign * (w / 2, h / 2, d / 2)[axis] + (d / 2 if axis == 2 else 0.0)
    span = ((h, d), (w, d), (w, h))[axis]
    most = (span[0] - 3 * t, span[1] - 3 * t)
    section = _run_section(model, obj.tag)
    if section is None or section[0]:
        dia = min(section[1] if section else min(most), *most)
        opening = circle(dia)
    else:
        opening = rectangle(min(section[1], most[0]), min(section[2], most[1]))
    normal = [0.0, 0.0, 0.0]
    normal[axis] = float(sign)
    return tuple(centre), tuple(normal), opening


def _authored_inlet(obj, neck, kind):
    authored = neck.inlet
    position = tuple(v.meters for v in authored.position)
    normal = (*authored.normal, 0)
    if kind == "wall":
        position = (position[0], position[2], position[1])
        normal = (authored.normal[0], 0, authored.normal[1])
    opening = (circle(authored.width.meters) if authored.section == "round"
               else rectangle(authored.width.meters, authored.height.meters))
    return position, normal, opening


def _lip(model, obj, neck, kind):
    """(lip width, its z): the grille frame's margin past the neck, on the grille's back."""
    types = getattr(getattr(getattr(model, "plan", None), "library", None),
                    "register_types", ())
    catalog = next((c for c in types if c.tag == obj.type_ref), None)
    if catalog is None:
        return LIP_M, 0.0
    fw = catalog.footprint[0].meters
    fh = catalog.height.meters if kind == "wall" else catalog.footprint[1].meters
    margin = min(fw - neck.width.meters, fh - neck.height.meters) / 2.0
    # A wall neck starts behind its grille; a ceiling or floor neck at the room face.
    z = 0.0 if kind == "wall" else catalog.height.meters
    return (min(LIP_M, margin) if margin > 0 else 0.0), z


def neck_mesh(model, obj, neck, joint=None):
    """The neck's sheet metal, placed behind the face (module docstring). ``joint`` =
    (local inlet, open back) overrides the cut: ``joint_necks``'s side entry."""
    frame = terminal_frame(model, obj)
    if frame is None or neck.section is None:
        return None
    sheet = _sheet_m(model, neck)
    w, h, d = neck.width.meters, neck.height.meters, neck.depth.meters
    if neck.section == "round" or neck.separate_boot:
        return transform_mesh(tube(w, h, d, neck.section, sheet), *frame)
    kind = obj.mount.kind.value
    t = min(sheet or VISUALIZATION.sheet_m, w / 4, h / 4, d / 4)
    if joint is not None:
        inlet, open_back = joint
        lip, lip_z = _lip(model, obj, neck, kind)
        return transform_mesh(neck_box(w, h, d, inlet, open_back=open_back, sheet_m=sheet,
                                       lip_m=lip, lip_z=lip_z), *frame)
    if neck.inlet is not None:
        inlet = _authored_inlet(obj, neck, kind)
    elif neck.entry is not None:
        inlet = _entry_inlet(model, obj, neck, kind, t)
    else:
        inlet = None
    lip, lip_z = _lip(model, obj, neck, kind)
    mesh = neck_box(w, h, d, inlet, open_back=inlet is None, sheet_m=sheet,
                    lip_m=lip, lip_z=lip_z)
    return transform_mesh(mesh, *frame)


def _plain_neck(neck: Any) -> bool:
    return (neck is not None and not neck.separate_boot and not neck.components
            and neck.inlet is None and neck.entry is None)


def boot_drawn(model: Any) -> set[str]:
    """Registers whose plain neck does NOT stand in for the boot: a bought or shop boot
    (not integral) met by a 90. Its boot is drawn (``duct_part_solids``) and the run trimmed
    at it, like a ``separate_boot``'s. A straight end stays the neck's own."""
    from typehaus.resolve.boot_solids import boot_entry

    types = {t.tag: t for t in getattr(model.plan.library, "register_types", ())}
    necks = {o.tag: getattr(types.get(o.type_ref), "neck", None)
             for o in model.canvas_objects if o.kind == "Register"}
    return {part.other for part in model.duct_parts
            if part.kind == "boot" and not part.integral
            and _plain_neck(necks.get(part.other)) and boot_entry(part) in ("end", "side")}


def _side_cut(frame, neck, joint, t):
    """``neck_box``'s inlet for a collar through a side wall, clipped to that wall."""
    from shapely.geometry import Polygon, box

    from typehaus.resolve.sweep import leg_frame

    origin, *axes = frame
    centre, axis, size, behind = joint
    local = [sum((centre[i] - origin[i]) * a[i] for i in range(3)) for a in axes]
    dots = [sum(axis[i] * a[i] for i in range(3)) for a in axes[:2]]
    k = 0 if abs(dots[0]) >= abs(dots[1]) else 1
    sign = 1 if dots[k] > 0 else -1
    w, h, d = neck.width.meters, neck.height.meters, neck.depth.meters
    other = 1 - k  # the wall's in-plane axes: the other side axis, then depth
    a, b = local[other], local[2] - d / 2
    if size.is_round:
        ring = circle(size.width, (a, b))
    else:
        right, up = leg_frame(axis)
        ext = [abs(sum(right[i] * axes[j][i] for i in range(3))) * size.width
               + abs(sum(up[i] * axes[j][i] for i in range(3))) * size.depth
               for j in (other, 2)]
        ring = tuple((a + u, b + v) for u, v in rectangle(*ext))
    span = (h, w)[k]
    cut = Polygon(ring).intersection(box(-span / 2 + 1.5 * t, -d / 2 + 1.5 * t,
                                         span / 2 - 1.5 * t, d / 2 - 1.5 * t))
    if cut.is_empty or cut.geom_type != "Polygon" or cut.area < 1e-8:
        return None, behind
    opening = tuple((x - a, y - b) for x, y in tuple(cut.exterior.coords)[:-1])
    position = [0.0, 0.0, local[2]]
    position[k], position[other] = sign * (w, h)[k] / 2, a
    normal = [0.0, 0.0, 0.0]
    normal[k] = float(sign)
    return (tuple(position), tuple(normal), opening), behind


def joint_necks(model: Any) -> None:
    """Re-cut each plain neck a 90 boot's collar enters from the side (``boot_solids.
    neck_side_joint``): the collar's hole in that wall, the back shut unless a box is drawn
    behind it. After ``duct_parts``: the joint is known only once every run is resolved."""
    from dataclasses import replace

    from typehaus.resolve.boot_solids import neck_side_joint

    drawn = boot_drawn(model)
    if not drawn:
        return
    types = {t.tag: t for t in model.plan.library.register_types}
    objects = {o.tag: o for o in model.canvas_objects}
    joints = {}
    for part in model.duct_parts:
        if part.kind == "boot" and part.other in drawn:
            joint = neck_side_joint(part)
            if joint is not None:
                joints[part.other] = joint
    for index, solid in enumerate(model.solids):
        tag = solid.host_ref
        if tag not in joints or solid.tag != f"{tag}-NECK" or solid.category != "terminal_neck":
            continue
        obj, neck = objects[tag], types[objects[tag].type_ref].neck
        frame = terminal_frame(model, obj)
        if frame is None or neck.section != "rectangular":
            continue
        w, h, d = neck.width.meters, neck.height.meters, neck.depth.meters
        t = min(_sheet_m(model, neck) or VISUALIZATION.sheet_m, w / 4, h / 4, d / 4)
        inlet, behind = _side_cut(frame, neck, joints[tag], t)
        model.solids[index] = replace(solid, body_mesh=neck_mesh(
            model, obj, neck, joint=(inlet, behind)))
