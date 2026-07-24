"""2D detail components — the drawn context a junction needs but the model does not carry.

A grade line, a soil hatch, a french drain and its river-rock surround are drawing
conventions, not building elements: Revit calls them detail components and they live in the
view, not the model. TypeHaus derives them the same way it derives joint treatments — from
the live cut and the resolved planes around it — so they track a geometry edit instead of
freezing authored coordinates.

They are emitted as ordinary ``Polyline``/``Hatch`` nodes carrying a
``detail-component:<name>`` tag, deliberately *not* as new ``Symbol`` names: the writers
already render polylines and hatches correctly and keep them hit-testable, whereas an
unknown ``Symbol`` degrades to a bare circle.

Section coordinates throughout: ``u`` is the in-section axis, ``z`` is world z, both in
model inches at the point these nodes are built (the cutter's convention).
"""

from __future__ import annotations

from typehaus.emit.draw.scene import (
    ArchDimension,
    Hatch,
    IRNode,
    NamedPoint,
    Polyline,
    Text,
)

M_TO_IN = 39.37007874015748

LAYER = "A-DETL-CMPT"

# Reference dimensions (catlin-house Pset_ifcPlot_BasementConstruction), in inches.
DRAIN_DIAMETER_IN = 4.0
ROCK_WIDTH_IN = 10.0
ROCK_DEPTH_IN = 8.0


def _closed(points, tag: str, material: str | None, pattern: str | None,
            lineweight: float = 0.18) -> list[IRNode]:
    pts = tuple(points)
    nodes: list[IRNode] = []
    if pattern:
        nodes.append(Hatch(boundary=pts, pattern=pattern, layer=LAYER, material=material))
    nodes.append(Polyline(points=pts, layer=LAYER, closed=True, lineweight=lineweight,
                          tag=f"detail-component:{tag}"))
    return nodes


def grade_line(u0: float, u1: float, grade_z: float, wall_face_u: float) -> list[IRNode]:
    """The finish-grade line, drawn only outboard of the wall face it slopes away from."""
    start = max(u0, wall_face_u)
    if start >= u1:
        return []
    return [Polyline(points=((start, grade_z), (u1, grade_z)), layer="L-SITE-GRAD",
                     lineweight=0.5, tag="detail-component:grade-line")]


def soil_body(u0: float, u1: float, grade_z: float, z_bottom: float,
              wall_face_u: float) -> list[IRNode]:
    """Undisturbed soil outboard of the wall, from grade down to the crop bottom."""
    start = max(u0, wall_face_u)
    if start >= u1 or grade_z <= z_bottom:
        return []
    return _closed(
        ((start, z_bottom), (u1, z_bottom), (u1, grade_z), (start, grade_z)),
        "soil", "soil", "soil", lineweight=0.0,
    )


def french_drain(center_u: float, invert_z: float) -> list[IRNode]:
    """Perforated drain tile in a washed-rock surround, sitting on the footing bedding.

    Drawn as its rock envelope plus the pipe bore — the reference's own construction. The
    pipe is a square-cut octagon rather than a circle because the IR has no arc primitive
    that both writers render.
    """
    half_rock = ROCK_WIDTH_IN / 2.0
    nodes = _closed(
        ((center_u - half_rock, invert_z),
         (center_u + half_rock, invert_z),
         (center_u + half_rock, invert_z + ROCK_DEPTH_IN),
         (center_u - half_rock, invert_z + ROCK_DEPTH_IN)),
        "river-rock", "river-rock", "gravel",
    )
    r = DRAIN_DIAMETER_IN / 2.0
    cz = invert_z + r + 1.0
    k = r * 0.4142  # octagon: tan(22.5°)
    nodes.extend(_closed(
        ((center_u - k, cz - r), (center_u + k, cz - r),
         (center_u + r, cz - k), (center_u + r, cz + k),
         (center_u + k, cz + r), (center_u - k, cz + r),
         (center_u - r, cz + k), (center_u - r, cz - k)),
        "french-drain", "aggregate", None, lineweight=0.35,
    ))
    return nodes


def faces_soil(wall) -> bool:
    """Whether this foundation wall is detailed for soil contact.

    Read from the assembly, not the tag: a wall that backfills against earth carries
    damp-proofing or exterior rigid insulation outboard of its concrete, and an interior
    basement bearing wall — slab on both sides — does not. Drawing soil and a perimeter
    drain against the latter would be a drawing that lies about the building.
    """
    if not wall.is_foundation:
        return False
    structure = next((i for i, ly in enumerate(wall.layers)
                      if ly.function == "structure"), None)
    if structure is None:
        return False
    for layer in wall.layers[structure + 1:]:
        if layer.function in ("membrane", "insulation") and not layer.is_cavity:
            return True
    return False


def build_below_grade_components(model, wall, crop, direction: str,
                                 station: float) -> list[IRNode]:
    """Grade, soil and the perimeter drain for a below-grade wall, from resolved planes.

    Returns nothing unless the cut actually reaches below grade — an above-grade junction
    has no soil to draw, and guessing one would be a drawing that lies.
    """
    site = model.plan.project.site
    if site.grade is None or crop is None or not faces_soil(wall):
        return []
    (cu0, cz0), (cu1, cz1) = crop
    grade_z = site.grade.meters
    if not (cz0 < grade_z < cz1):
        return []

    u_lo, u_hi = _wall_faces(wall, direction, station)
    if u_lo is None:
        return []
    # Which side is outdoors comes from the assembly, not the drawing: layers are ordered
    # interior→exterior, so the last layer sits on the outboard face. Reading it off the
    # crop instead would just reflect the crop's own asymmetry back at us.
    outboard_is_high = _outboard_is_high(wall, direction, station)
    if outboard_is_high is None:
        return []
    face = u_hi if outboard_is_high else u_lo

    to_in = M_TO_IN
    nodes: list[IRNode] = []
    if outboard_is_high:
        nodes += soil_body(cu0 * to_in, cu1 * to_in, grade_z * to_in, cz0 * to_in,
                           face * to_in)
        nodes += grade_line(cu0 * to_in, cu1 * to_in, grade_z * to_in, face * to_in)
    else:
        # Mirror: soil fills from the crop's low edge up to the wall's inboard face.
        nodes += _mirrored_soil(cu0 * to_in, face * to_in, grade_z * to_in, cz0 * to_in)
        nodes.append(Polyline(points=((cu0 * to_in, grade_z * to_in),
                                      (face * to_in, grade_z * to_in)),
                              layer="L-SITE-GRAD", lineweight=0.5,
                              tag="detail-component:grade-line"))

    # The perimeter drain sits on the footing bedding. Only draw it when the footing is
    # actually in frame — a wall-top junction cropped 4 ft down the basement wall does not
    # reach it, and a drain floating at the crop edge is worse than no drain.
    footing = _footing_under(model, wall)
    if footing is not None and cz0 <= footing.z0_m and footing.z0_m + ROCK_DEPTH_IN / M_TO_IN <= cz1:
        offset = (ROCK_WIDTH_IN / 2.0 + 1.0) * (1.0 if outboard_is_high else -1.0)
        nodes += french_drain(face * to_in + offset, footing.z0_m * to_in)
    return nodes


def _mirrored_soil(u0: float, u1: float, grade_z: float, z_bottom: float) -> list[IRNode]:
    if u0 >= u1 or grade_z <= z_bottom:
        return []
    return _closed(((u0, z_bottom), (u1, z_bottom), (u1, grade_z), (u0, grade_z)),
                   "soil", "soil", "soil", lineweight=0.0)


def _outboard_is_high(wall, direction: str, station: float) -> bool | None:
    """True when the wall's outermost layer sits at the high end of the section axis."""
    from typehaus.emit.draw.section import _ring_cut_intervals

    depth = wall.depth_layers()
    if len(depth) < 2:
        return None
    first = _ring_cut_intervals(depth[0].polygon, direction, station)
    last = _ring_cut_intervals(depth[-1].polygon, direction, station)
    if not first or not last:
        return None
    return sum(last[0]) > sum(first[0])


def _wall_faces(wall, direction: str, station: float):
    from typehaus.emit.draw.section import _ring_cut_intervals

    bounds: list[float] = []
    for layer in wall.layers:
        for (a, b) in _ring_cut_intervals(layer.polygon, direction, station):
            bounds.extend((a, b))
    if not bounds:
        return None, None
    return min(bounds), max(bounds)


def _footing_under(model, wall):
    """The strip footing carrying this wall, by the ``FT-<wall suffix>`` naming convention."""
    suffix = wall.tag[2:] if wall.tag.startswith("W-") else wall.tag
    return next((s for s in model.solids
                 if s.category == "footing" and s.tag == f"FT-{suffix}"), None)


# ===========================================================================
# Sheet-metal + junction component vocabulary (ported from
# catlin_reference/scripts/detail_utils.py: _flashing / _path_from_steps /
# _thick_polyline). These are drawing conventions, emitted as Polyline+Hatch
# so both writers render them (a Symbol would degrade to a bare circle), and
# derived from the resolved faces around the live cut like the grade/soil
# components above — so they track a geometry edit instead of freezing
# authored coordinates. Section coords throughout: (u, z) in inches.
# ===========================================================================

FLASH_THK_IN = 0.5      # schematic sheet-metal thickness
GUTTER_DEPTH_IN = 5.0
GUTTER_HEIGHT_IN = 5.0
SILL_GASKET_IN = 0.25   # 1/4" sill gasket (Pset_ifcPlot BasementToFramedWall)
SCREEN_IN = 0.6         # insect-screen band height


def _path_from_steps(start_uz, steps) -> list[tuple[float, float]]:
    """Polyline from a start point + a list of (du, dz) steps (flashing profiles)."""
    u, z = float(start_uz[0]), float(start_uz[1])
    pts = [(u, z)]
    for du, dz in steps:
        u += float(du)
        z += float(dz)
        pts.append((u, z))
    return pts


def _thick_polyline(points, thickness: float,
                    miter_min_dot: float = 0.25) -> list[tuple[float, float]]:
    """Thicken a centreline into a closed constant-width polygon (pure-Python port).

    ``miter_min_dot`` clamps the miter at sharp corners so right-angle flashing
    profiles keep constant thickness without spiking.
    """
    import math

    pts = [(float(u), float(z)) for (u, z) in points]
    if len(pts) < 2:
        raise ValueError("need at least 2 points")

    seg_norms: list[tuple[float, float]] = []
    for (u0, z0), (u1, z1) in zip(pts, pts[1:]):
        nx, nz = -(z1 - z0), (u1 - u0)
        mag = math.hypot(nx, nz) or 1e-9
        seg_norms.append((nx / mag, nz / mag))

    vnorms: list[tuple[float, float]] = [(0.0, 0.0)] * len(pts)
    vnorms[0] = seg_norms[0]
    vnorms[-1] = seg_norms[-1]
    for i in range(1, len(pts) - 1):
        n0, n1 = seg_norms[i - 1], seg_norms[i]
        mx, mz = n0[0] + n1[0], n0[1] + n1[1]
        mag = math.hypot(mx, mz)
        if mag < 1e-6:
            vnorms[i] = n1
            continue
        mx, mz = mx / mag, mz / mag
        denom = max(mx * n1[0] + mz * n1[1], miter_min_dot)
        vnorms[i] = (mx / denom, mz / denom)

    half = thickness / 2.0
    outer = [(u + half * nx, z + half * nz) for (u, z), (nx, nz) in zip(pts, vnorms)]
    inner = [(u - half * nx, z - half * nz) for (u, z), (nx, nz) in zip(pts, vnorms)]
    return outer + inner[::-1]


def flashing_nodes(centerline, thickness: float = FLASH_THK_IN, *,
                   material: str = "metal", tag: str = "flashing",
                   lineweight: float = 0.45) -> list[IRNode]:
    """Sheet-metal flashing as a thickened polyline (fill + closed outline)."""
    if len(centerline) < 2:
        return []
    poly = tuple(_thick_polyline(centerline, thickness))
    return [
        Hatch(boundary=poly, pattern="metal", layer=LAYER, material=material),
        Polyline(points=poly, layer=LAYER, closed=True, lineweight=lineweight,
                 tag=f"detail-component:{tag}"),
    ]


def _rect_pts(u0: float, z0: float, u1: float, z1: float):
    return ((u0, z0), (u1, z0), (u1, z1), (u0, z1))


# --- per-wall layer geometry helpers ---------------------------------------

def _layer_intervals(wall, direction: str, station: float) -> dict:
    """{layer.name: (u_lo, u_hi, function)} for layers the cut crosses, inches."""
    from typehaus.emit.draw.section import _ring_cut_intervals

    out: dict = {}
    for layer in wall.layers:
        ivs = _ring_cut_intervals(layer.polygon, direction, station)
        if ivs:
            lo = min(min(iv) for iv in ivs)
            hi = max(max(iv) for iv in ivs)
            out[layer.name] = (lo * M_TO_IN, hi * M_TO_IN, layer.function)
    return out


def _face(iv, outboard_is_high: bool, outer: bool) -> float:
    lo, hi = iv[0], iv[1]
    if outer:
        return hi if outboard_is_high else lo
    return lo if outboard_is_high else hi


def _by_function(intervals: dict, function: str):
    """Outermost interval carrying ``function`` (furring/cladding/insulation…)."""
    hits = [iv for iv in intervals.values() if iv[2] == function]
    return hits[-1] if hits else None


def zero_overhang_eave(model, wall, condition, crop, direction, station) -> list[IRNode]:
    """Box gutter + drip edge + insect-screen vent at the zero-overhang eave.

    Ported from roof_wall_eave_detail_ifc.png: a fascia-style box gutter mounted
    on the exterior plane, a drip edge turning down off the roof furring, and the
    continuous wall→eave→ridge vent screened at the eave.
    """
    outboard_is_high = _outboard_is_high(wall, direction, station)
    if outboard_is_high is None or crop is None:
        return []
    (cu0, cz0), (cu1, cz1) = crop
    junction_z = (wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m) * M_TO_IN
    intervals = _layer_intervals(wall, direction, station)
    clad = _by_function(intervals, "cladding") or _by_function(intervals, "furring")
    if clad is None:
        return []
    out_sign = 1.0 if outboard_is_high else -1.0
    clad_out = _face(clad, outboard_is_high, outer=True)

    nodes: list[IRNode] = []
    # Drip edge: turns down off the roof deck edge onto the fascia.
    drip = _path_from_steps((clad_out - out_sign * 0.5, junction_z + 1.0),
                            [(out_sign * 1.6, 0.0), (0.0, -2.4)])
    nodes += flashing_nodes(drip, tag="drip-edge")

    # Box gutter: a U trough hung just outboard of the fascia.
    back_u = clad_out + out_sign * 0.6
    front_u = back_u + out_sign * GUTTER_DEPTH_IN
    top_z = junction_z - 1.5
    trough = [
        (back_u, top_z),
        (back_u, top_z - GUTTER_HEIGHT_IN),
        (front_u, top_z - GUTTER_HEIGHT_IN),
        (front_u, top_z + 0.5),
    ]
    nodes += flashing_nodes(trough, thickness=0.6, material="gutter", tag="box-gutter")

    # Insect-screened vent at the eave: a short cross-hatched band on the wall face.
    screen_u0 = min(clad_out, clad_out - out_sign * 3.0)
    screen_u1 = max(clad_out, clad_out - out_sign * 3.0)
    scr_z0 = junction_z - 3.0
    if scr_z0 > cz0 * M_TO_IN:
        nodes += _closed(_rect_pts(screen_u0, scr_z0, screen_u1, scr_z0 + SCREEN_IN),
                         "insect-screen", None, "rigid", lineweight=0.3)
    return nodes


def basement_framed_wall(model, framed, concrete, crop, direction,
                         station) -> list[IRNode]:
    """Flashings + air-seal components at the basement→framed-wall transition.

    Ported from basement_to_framed_wall_detail_ifc.png: an L-flashing off the
    sheathing onto the basement foam, a Z-flashing with drip edge at the bottom of
    the rainscreen furring, an insect screen above it, and the sill gasket + a
    spray-foam sealant bead sealing the mudsill line.
    """
    outboard_is_high = _outboard_is_high(framed, direction, station)
    if outboard_is_high is None or crop is None:
        return []
    junction_z = framed.z0_m * M_TO_IN  # top of concrete == bottom of framed wall
    intervals = _layer_intervals(framed, direction, station)
    out_sign = 1.0 if outboard_is_high else -1.0

    furring = _by_function(intervals, "furring")
    clad = _by_function(intervals, "cladding")
    sheath = _by_function(intervals, "sheathing")
    foam = _by_function(intervals, "insulation")
    stud = _by_function(intervals, "structure")
    nodes: list[IRNode] = []

    # L-flashing: from the sheathing face turning down onto the basement foam.
    if sheath is not None and foam is not None:
        sheath_out = _face(sheath, outboard_is_high, outer=True)
        foam_out = _face(foam, outboard_is_high, outer=True)
        lflash = _path_from_steps((sheath_out, junction_z + 3.0),
                                  [(0.0, -2.85), (out_sign * (foam_out - sheath_out), 0.0)])
        nodes += flashing_nodes(lflash, tag="l-flashing")
        # Spray-foam sealant bead at the outer end of the L-flashing.
        beb0 = foam_out - out_sign * 0.75
        nodes += _closed(_rect_pts(min(beb0, foam_out), junction_z,
                                   max(beb0, foam_out), junction_z + 0.9),
                         "sealant-bead", "spray-foam", "foam", lineweight=0.3)

    # Z-flashing with drip edge at the bottom of the rainscreen furring/cladding.
    if furring is not None and clad is not None:
        fur_in = _face(furring, outboard_is_high, outer=False)
        clad_out = _face(clad, outboard_is_high, outer=True)
        zpath = _path_from_steps((fur_in, junction_z + 2.4), [
            (0.0, -2.15),
            (out_sign * (clad_out - fur_in), 0.0),
            (out_sign * 0.55, 0.0),
            (0.0, -4.2),
            (out_sign * 0.7, -0.25),
        ])
        nodes += flashing_nodes(zpath, tag="z-flashing")
        # Insect screen just above the Z-flashing.
        s0, s1 = sorted((fur_in, clad_out))
        nodes += _closed(_rect_pts(s0, junction_z + 2.65, s1, junction_z + 2.65 + SCREEN_IN),
                         "insect-screen", None, "rigid", lineweight=0.3)

    # Sill gasket (1/4") + treated mudsill air seal under the stud line.
    if stud is not None:
        s_lo, s_hi = stud[0], stud[1]
        nodes += _closed(_rect_pts(min(s_lo, s_hi), junction_z, max(s_lo, s_hi),
                                   junction_z + SILL_GASKET_IN),
                         "sill-gasket", "rubber", None, lineweight=0.35)
    return nodes


def build_overlay_components(model, derived) -> list[IRNode]:
    """Dispatch per-detail flashing/gutter/gasket vocabulary off the overlay id.

    The recipe ids are authored on ``Transition.overlay`` (houses/catlin
    transitions.py); this is where they stop being inert strings and drive the
    2D detail vocabulary.
    """
    tr = getattr(derived, "transition", None)
    overlay = getattr(tr, "overlay", None) if tr is not None else None
    if not overlay:
        return []
    crop_pts = derived.view.crop
    if crop_pts is None:
        return []
    crop = (crop_pts[0].xy_m, crop_pts[1].xy_m)
    direction, station = derived.direction, derived.station
    walls = [w for w in (model.wall(t) for t in derived.condition.element_tags)
             if w is not None]

    if overlay == "zero-overhang-eave":
        wall = next((w for w in walls if not w.is_foundation), None) or (
            walls[0] if walls else None)
        if wall is None:
            return []
        return zero_overhang_eave(model, wall, derived.condition, crop, direction, station)

    if overlay == "basement-framed-wall":
        framed = next((w for w in walls if not w.is_foundation), None)
        concrete = next((w for w in walls if w.is_foundation), None)
        if framed is None:
            return []
        return basement_framed_wall(model, framed, concrete, crop, direction, station)

    return []


# ===========================================================================
# Detail chrome: material legend band + derived dimension strings. Both read
# the resolved layer thicknesses so they track a geometry edit, and both emit
# ordinary IR nodes (Hatch/Polyline/Text/ArchDimension) the writers render.
# ===========================================================================

TEXT_H = 1.5


def _participating_layers(model, derived):
    """(material_ref, thickness_in, function) for every cut layer in this detail."""
    out: list[tuple[str, float, str]] = []
    for tag in derived.condition.element_tags:
        wall = model.wall(tag)
        if wall is None:
            continue
        for layer in wall.layers:
            if layer.is_cavity:
                continue
            out.append((layer.material_ref, layer.thickness_m * M_TO_IN, layer.function))
    for roof in model.roofs:
        if roof.tag not in derived.condition.element_tags:
            continue
        asm = model.plan.library.resolve_assembly(roof.assembly)
        if asm is None:
            continue
        for layer in asm.layers:
            out.append((layer.material_ref, layer.thickness.meters * M_TO_IN,
                        layer.function))
    return out


def material_legend(model, derived, u_left: float, z_top: float) -> list[IRNode]:
    """One swatch + label per distinct material in the cut, with resolved thickness."""
    seen: dict[str, float] = {}
    order: list[str] = []
    for material, thick, _fn in _participating_layers(model, derived):
        if material and material not in seen:
            seen[material] = thick
            order.append(material)
    if not order:
        return []
    from typehaus.emit.draw.palette import detail_hatch

    nodes: list[IRNode] = []
    nodes.append(Text(anchor=(u_left, z_top + 3.0), content="MATERIALS", height=TEXT_H,
                      layer="A-ANNO-TEXT"))
    size = 2.6
    step = 3.6
    for i, material in enumerate(order):
        y1 = z_top - i * step
        y0 = y1 - size
        # ``metal`` maps to a no-overlay fill in both writers (and the UI), so the
        # swatch reads as its material fill when the material has no hatch family.
        pattern = detail_hatch(material) or "metal"
        nodes.append(Hatch(boundary=_rect_pts(u_left, y0, u_left + size, y1),
                           pattern=pattern, layer=LAYER, material=material))
        nodes.append(Polyline(points=_rect_pts(u_left, y0, u_left + size, y1),
                              layer=LAYER, closed=True, lineweight=0.2))
        label = f'{material}  {seen[material]:.3g}"'
        nodes.append(Text(anchor=(u_left + size + 1.5, (y0 + y1) / 2),
                          content=label, height=TEXT_H, layer="A-ANNO-TEXT"))
    return nodes


def _sum_ci(intervals: dict) -> tuple[float, float, float] | None:
    """(u_lo, u_hi, total_in) of the continuous exterior-insulation band, if any."""
    ins = [iv for iv in intervals.values() if iv[2] == "insulation"]
    if not ins:
        return None
    lo = min(iv[0] for iv in ins)
    hi = max(iv[1] for iv in ins)
    return lo, hi, sum(abs(iv[1] - iv[0]) for iv in ins)


def dimension_strings(model, derived, crop, direction, station) -> list[IRNode]:
    """ArchDimension strings derived from the resolved layer thicknesses.

    Total continuous insulation and stud depth on the framed wall; XPS layer
    count × thickness on the foundation side.
    """
    nodes: list[IRNode] = []
    walls = [w for w in (model.wall(t) for t in derived.condition.element_tags)
             if w is not None]
    framed = next((w for w in walls if not w.is_foundation), None)
    concrete = next((w for w in walls if w.is_foundation), None)

    def _dim(p0, p1, offset, text):
        nodes.append(ArchDimension(
            kind="linear", ends=(NamedPoint(xy=p0), NamedPoint(xy=p1)),
            p0=p0, p1=p1, offset=offset, text=text))

    if framed is not None:
        oi = _outboard_is_high(framed, direction, station)
        intervals = _layer_intervals(framed, direction, station)
        junction_z = framed.z0_m * M_TO_IN
        top = (framed.top_z1_m if framed.top_z1_m is not None else framed.z1_m) * M_TO_IN
        z_here = junction_z + 6.0 if concrete is not None else top - 6.0
        ci = _sum_ci(intervals)
        if ci is not None and oi is not None:
            lo, hi, total = ci
            _dim((lo, z_here), (hi, z_here), 4.0,
                 f'{total:.3g}" CI')
        stud = _by_function(intervals, "structure")
        if stud is not None:
            _dim((stud[0], z_here + 8.0), (stud[1], z_here + 8.0), 3.0,
                 f'{abs(stud[1] - stud[0]):.3g}" stud')

    if concrete is not None:
        oi = _outboard_is_high(concrete, direction, station)
        intervals = _layer_intervals(concrete, direction, station)
        xps = [iv for iv in intervals.values() if iv[2] == "insulation"]
        if xps and oi is not None:
            lo = min(iv[0] for iv in xps)
            hi = max(iv[1] for iv in xps)
            total = sum(abs(iv[1] - iv[0]) for iv in xps)
            z_here = (concrete.z0_m + concrete.z1_m) / 2.0 * M_TO_IN
            _dim((lo, z_here), (hi, z_here), 3.0,
                 f'{total:.3g}" XPS ({len(xps)} layers)')
    return nodes
