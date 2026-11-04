"""Independent geometric checks on generated catalog-installation coordination parts."""

from dataclasses import replace

from shapely.geometry import Polygon

from typehaus.resolve.geometry_slice import CutPlane, slice_solid

#: Sections that occupy space: the sill, the approach bodies and the pan's drop. Films that
#: are bonded to a face (dams, the apron) and the approach-support envelopes, which are
#: drawn INTO the structure they bear on, are not tested.
_TESTED_SECTIONS = ("catalog-sill-outline", "approach-tread", "ariddek-approach-board",
                    "pan-outlet-drop", "approach-cross-bearer")
_TOUCH_M2 = 1e-8


def catalog_seat_conflicts(model, wall, opening, placement):
    """The hard clashes of :func:`catalog_section_clashes`."""
    return catalog_section_clashes(model, wall, opening, placement)[0]


def catalog_section_clashes(model, wall, opening, placement):
    """Intersect the installation's sections and exterior boards with every solid near them.

    Every wall layer (air gaps and coatings excepted) and every resolved solid, not only
    the host wall: an approach once ran 2.2" into the veneer's grade beam unseen. Cut at
    the opening's centreline for the sections and the head, and at each jamb board's line.

    ``(conflicts, coordination)``. A clash with a resolved solid, any layer of the walls the
    installation names (host, seat, reveal), or another wall's STRUCTURE is a conflict. One
    with another wall's skin (foam, girt, cladding) is coordination: a field cut, but unseen.
    """
    specification = placement.specification
    references = (*specification.approach_opening_refs, specification.seat_opening_ref,
                  specification.exterior_opening_ref)
    named = {wall.tag, *(o.host_wall for o in model.openings if o.tag in references)}
    from typehaus.resolve.geometry import opening_center, wall_frame

    center = opening_center(wall, opening)
    _, tangent, normal, _ = wall_frame(wall)

    def local(point):
        delta = tuple(point[i] - center[i] for i in (0, 1))
        return (sum(delta[i] * normal[i] for i in (0, 1)),
                sum(delta[i] * tangent[i] for i in (0, 1)))

    pieces = [(s.name, Polygon(s.polygon_m), s.along_m - s.span_m / 2, s.along_m + s.span_m / 2)
              for s in placement.sections if s.name.startswith(_TESTED_SECTIONS)]
    pieces += [(b.name, Polygon(((b.normal_m - b.depth_m / 2, b.z_m - b.height_m / 2),
                                 (b.normal_m + b.depth_m / 2, b.z_m - b.height_m / 2),
                                 (b.normal_m + b.depth_m / 2, b.z_m + b.height_m / 2),
                                 (b.normal_m - b.depth_m / 2, b.z_m + b.height_m / 2))),
                b.along_m - b.width_m / 2, b.along_m + b.width_m / 2)
               for b in placement.boards if b.name.startswith("exterior")]
    if not pieces:
        return (), ()
    stations = sorted({0.0, *(round((lo + hi) / 2, 6) for *_, lo, hi in pieces)})
    reach = _bounds(body for _, body, _, _ in pieces)
    half = max(max(abs(lo), abs(hi)) for *_, lo, hi in pieces)
    conflicts, coordination = set(), set()
    # The opening's own derived parts (its flashing, trim) are the installation, not a clash.
    own = f"{opening.tag}-"
    for label, hard, solid in _nearby_solids(model, local, reach, half, named, own):
        for station in stations:
            for profile in slice_solid(solid, CutPlane("x", station)):
                body = Polygon(profile.outline, profile.voids)
                for name, piece, lo, hi in pieces:
                    if lo - 1e-9 <= station <= hi + 1e-9 and \
                            piece.intersection(body).area > _TOUCH_M2:
                        (conflicts if hard else coordination).add(
                            f"{name.split('-board')[0]} intersects remaining {label}")
    return tuple(sorted(conflicts)), tuple(sorted(coordination))


def _bounds(polygons):
    boxes = [p.bounds for p in polygons]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _nearby_solids(model, local, reach, half, named, own):
    """``(label, hard, solid)`` in the opening's (normal, along, z) frame, box-filtered."""
    from typehaus.resolve.geometry_ir import GMesh, GPrism
    from typehaus.resolve.geometry_walls import layer_solids

    x0, z0, x1, z1 = reach

    def near(points, lo_z, hi_z):
        mapped = [local(p) for p in points]
        return (min(m[0] for m in mapped) < x1 and max(m[0] for m in mapped) > x0
                and min(m[1] for m in mapped) < half and max(m[1] for m in mapped) > -half
                and lo_z < z1 and hi_z > z0)

    def moved(solid):
        if isinstance(solid, GMesh):
            return replace(solid, positions=tuple((*local(p), p[2]) for p in solid.positions))
        return replace(solid, ring=tuple(local(p) for p in solid.ring),
                       voids=tuple(tuple(local(p) for p in ring) for ring in solid.voids))

    for target in model.walls:
        if not near([p for ly in target.layers for p in ly.polygon], target.z0_m, target.z1_m):
            continue
        cuts = [o for o in model.openings if o.host_wall == target.tag]
        for layer in target.body_layers():
            if layer.function == "airgap" or layer.thickness_m <= 0:
                continue
            for solid in layer_solids(target, layer.polygon, cuts, layer_name=layer.name):
                if isinstance(solid, (GMesh, GPrism)):
                    hard = target.tag in named or layer.function == "structure"
                    yield f"{target.tag}/{layer.name}", hard, moved(solid)
    for solid in model.solids:
        ring = getattr(solid, "outline", None)
        if (not ring or getattr(solid, "sweep", None) is not None or solid.z1_m <= solid.z0_m
                or solid.tag.startswith(own)):
            continue
        if near(ring, solid.z0_m, solid.z1_m):
            yield solid.tag, True, moved(GPrism(tuple(ring), solid.z0_m, solid.z1_m,
                                          voids=tuple(getattr(solid, "voids", ()) or ())))


def catalog_drainage_conflicts(placement):
    """A full-width bearing or cover cannot occupy the apron water path."""
    apron = next((s for s in placement.sections if s.name == "impermeable-pan-apron"), None)
    if apron is None:
        return ("catalog installation has no modeled drainage apron",)
    water_path = Polygon(apron.polygon_m)
    tolerance = placement.specification.wrap_isolation_thickness.meters
    # Allow bonded/isolation films to touch the pan. A structural body with positive
    # intersection area dams it, regardless of the generator's claimed clearance.
    conflicts = []
    for section in placement.sections:
        if section.span_m < apron.span_m - tolerance or not (
            section.name.startswith("approach-cross-bearer")
            or section.name.startswith("approach-support")
        ):
            continue
        if Polygon(section.polygon_m).intersection(water_path).area > tolerance**2:
            conflicts.append(f"{section.name} blocks the full-width drainage apron")
    return tuple(conflicts)
