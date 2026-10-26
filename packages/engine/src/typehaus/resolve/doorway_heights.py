"""Installed threshold heights, never a silent substitute of the rough-opening datum."""


def installed_threshold_elevation(opening, wall):
    assembly = getattr(opening, "doorway", None)
    if assembly is None:
        # Unselected legacy/synthetic openings have no product contract to contradict.
        return wall.base_ref_z_m + opening.sill_m, "rough-opening estimate"
    placement = assembly.exterior_placement
    if placement and placement.threshold_upper_z_m is not None:
        return placement.threshold_upper_z_m, "catalog crest plus installation tolerance"
    sills = [c for c in assembly.components if c.specification.role in ("sill", "track")]
    if sills:
        return max(c.top_z_m for c in sills), "documented installed section"
    if placement and placement.sill_design_status == "SCHEMATIC":
        caps = [s for s in placement.sections if s.name == "threshold-cap-design-envelope"]
        if caps:
            return max(z for s in caps for _, z in s.polygon_m), "schematic crest estimate"
    return None, "installed threshold section is missing"
