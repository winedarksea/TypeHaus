"""Independent geometric checks on generated catalog-installation coordination parts."""

from shapely.geometry import Polygon


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
