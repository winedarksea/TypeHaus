"""Independent geometric checks on generated catalog-installation coordination parts."""

from dataclasses import replace

from shapely.geometry import Polygon


def catalog_seat_conflicts(model, wall, opening, placement):
    """Intersect remaining seat/reveal layers with the central installation section."""
    from typehaus.resolve.geometry import opening_center, wall_frame
    from typehaus.resolve.geometry_ir import GMesh
    from typehaus.resolve.geometry_slice import CutPlane, slice_solid
    from typehaus.resolve.geometry_walls import layer_solids

    specification = placement.specification
    references = (*specification.approach_opening_refs, specification.seat_opening_ref)
    notches = [next((o for o in model.openings if o.tag == reference), None)
               for reference in references if reference]
    targets = {wall.tag, *(notch.host_wall for notch in notches if notch is not None)}
    reveal = next((o for o in model.openings
                   if o.tag == specification.exterior_opening_ref), None)
    if reveal is not None:
        targets.add(reveal.host_wall)
    center = opening_center(wall, opening)
    _, tangent, normal, _ = wall_frame(wall)
    profiles = [s for s in placement.sections if s.name.startswith(
        ("ariddek-approach-board", "pan-outlet-drop", "approach-cross-bearer"))]
    def local(point):
        delta = tuple(point[i] - center[i] for i in (0, 1))
        return (sum(delta[i] * normal[i] for i in (0, 1)),
                sum(delta[i] * tangent[i] for i in (0, 1)))

    collisions = set()
    for tag in sorted(targets):
        target = model.wall(tag)
        cuts = [o for o in model.openings if o.host_wall == tag]
        for layer in target.body_layers():
            for solid in layer_solids(target, layer.polygon, cuts, layer_name=layer.name):
                if isinstance(solid, GMesh):
                    transformed = replace(solid, positions=tuple(
                        (*local(p), p[2]) for p in solid.positions))
                else:
                    transformed = replace(solid, ring=tuple(local(p) for p in solid.ring),
                                          voids=tuple(tuple(local(p) for p in ring)
                                                      for ring in solid.voids))
                for profile in slice_solid(transformed, CutPlane("x", 0)):
                    body = Polygon(profile.outline, profile.voids)
                    for section in profiles:
                        if Polygon(section.polygon_m).intersection(body).area > 1e-8:
                            collisions.add(f"{section.name.split('-board')[0]} intersects "
                                           f"remaining {target.tag}/{layer.name}")
    return tuple(sorted(collisions))


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
