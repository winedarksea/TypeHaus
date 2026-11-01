"""S-100's frost and footing-drainage notes: where a footing's frost protection comes from,
and where its drainage goes. Split out of ``foundation_notes.py``, which assembles them.
"""

from __future__ import annotations

from typehaus.resolve.model import ResolvedModel


def lowest_adjacent_grade_notes(model: ResolvedModel, frost_depth_in: float) -> list[str]:
    """Name the footings whose lowest adjacent grade is not the site grade plane.

    "ALL FOOTINGS TO BEAR 42\" MIN BELOW FINISHED GRADE" printed on this sheet for as long
    as it has existed, and on a site with an open sunken court beside the house it was
    simply false: the strips along that court bear 8" below the court floor, and the note
    told a reader — and an inspector — otherwise. The blanket claim is the thing that was
    wrong, not the number, so the note keeps the number and states the exceptions the
    geometry actually contains. Silent where there are none, which is most houses.
    """
    from typehaus.emit.draw.foundation_schedule import bearing_solids
    from typehaus.resolve.site_earth import (
        heated_floor_footprint,
        local_grade_elevation_m,
        open_excavation_floors,
    )

    reach_m = frost_depth_in * 0.0254
    floors = open_excavation_floors(model)
    if not floors:
        return []
    sheltered_by = heated_floor_footprint(model)
    shallow: list[tuple[str, float, str]] = []
    for solid in sorted(bearing_solids(model), key=lambda item: item.tag):
        grade_m, source = local_grade_elevation_m(
            model, solid.outline, reach_m, floors, sheltered_by)
        if source is None:
            continue
        cover_in = (grade_m - solid.z0_m) / 0.0254
        if cover_in < frost_depth_in - 1e-6:
            shallow.append((solid.tag, cover_in, source))
    if not shallow:
        return []
    sections = _declared_sections(model, frost_depth_in, {tag: cover for tag, cover, _ in shallow})
    replaced = [row for row in shallow if row[0] in sections]
    insulated = [row for row in shallow if row[0] not in sections]
    notes = ["THE LOWEST ADJACENT GRADE FOR " + ", ".join(
                f"{tag} ({cover:.0f}\" COVER)" for tag, cover, _ in shallow)
             + " IS THE FLOOR OF "
             + ", ".join(sorted({source for _, _, source in shallow}))
             + ", NOT THE SITE GRADE PLANE."]
    # Two different frost measures answer this condition and they carry different citations:
    # R403.3 for the house strips' wing insulation, but the garden's protection is the graded
    # stone section beneath it, not R403.3 — a blanket citation is wrong on the sheet an
    # inspector reads off.
    if insulated:
        notes.append("FROST PROTECTION FOR "
                     + ", ".join(tag for tag, _c, _s in insulated)
                     + " IS PER IRC R403.3 FIG. R403.3(3) AND TABLE R403.3(1) AT AIR-FREEZING "
                     "INDEX 3000, WING ABUTTING THE FOOTING, NOT BY DEPTH.")
    if replaced:
        notes.append("FROST PROTECTION FOR "
                     + ", ".join(tag for tag, _c, _s in replaced)
                     + " IS BY SOIL REPLACEMENT: EACH BEARS ON A DRAINED "
                     "NON-FROST-SUSCEPTIBLE SECTION REACHING "
                     f"{frost_depth_in:.0f}\" MIN BELOW THAT GRADE (ASCE 32, "
                     "PER IRC R403.1.4.1). SECTION GRADATION PER THE FOUNDATION DETAILS. "
                     "BUILDING OFFICIAL / ENGINEER ACCEPTANCE REQUIRED.")
    return notes


def _declared_sections(model: ResolvedModel, frost_depth_in: float,
                       cover_in: dict[str, float]) -> set[str]:
    """Footing tags protected by a declared, drained aggregate section reaching frost depth.

    The three conditions are ``structural.frost_depth``'s, and that check is the authority —
    this exists so the sheet can *name the right citation per footing*, which needs the same
    split the check makes. The section is measured from the same local grade: the footing's
    cover plus the bed's depth under the footing (``cover_in`` is the shallow footings').
    """
    from typehaus.resolve.drainage_network import drainage_evidence

    drained = drainage_evidence(model)
    top = {s.tag: s.z0_m for s in model.solids if s.category in ("footing", "pad")}
    return {bed.host for bed in model.footing_beddings
            if bed.non_frost_susceptible is True and bed.tag in drained
            and bed.host in cover_in and bed.host in top
            and cover_in[bed.host] + (top[bed.host] - bed.z0_m) / 0.0254
            >= frost_depth_in - 1e-6}


def drainage_note(model: ResolvedModel) -> str:
    """Where the perimeter tile discharges, read off the tile, and which beds run none.

    A sheet note is a statement about the building, so it reads the field that makes the
    statement, and says so plainly when the tile does not.
    """
    beddings = [bedding for bedding in model.footing_beddings if bedding.drain_tile]
    pipeless = [bedding for bedding in model.footing_beddings
                if bedding.in_drainage and not bedding.drain_tile]
    if not beddings:
        return _pipeless_note(pipeless).strip()
    # A bed handing its water to the bed it abuts is internal to one body of stone.
    beds = {bedding.tag for bedding in beddings}
    discharges = sorted({"THEIR SOAKAWAY COURSE" if d.lower() == "soakaway" else d.upper()
                         for bedding in beddings if bedding.drain_tile_spec is not None
                         and (d := (bedding.drain_tile_spec.discharge or "").strip())
                         and d not in beds})
    destination = (f"TO {', '.join(discharges)}" if discharges
                   else "TO AN APPROVED OUTLET (NOT MODELLED)")
    flood = sum(1 for bedding in beddings if bedding.stone_z0_m < bedding.z0_m)
    course = (f" {flood} BEDS CARRY A SOAKAWAY COURSE BELOW THE DRAINED SECTION; IT FLOODS"
              f" AND IS NOT FROST SECTION." if flood else "")
    return (f"PERIMETER DRAIN TILE IN THE FOOTING BEDDING AT {len(beddings)} FOOTINGS,"
            f" DRAINING {destination}.{course}{_pipeless_note(pipeless)}")


def _pipeless_note(pipeless) -> str:
    """The beds with no pipe: open-graded stone draining down into a flood course."""
    if not pipeless:
        return ""
    flood = sum(1 for bedding in pipeless if bedding.stone_z0_m < bedding.z0_m)
    return (f" {len(pipeless)} BEDS RUN NO PIPE: THEIR OPEN-GRADED STONE DRAINS INTO"
            f" {flood} SOAKAWAY COURSES BELOW THE DRAINED SECTION, WHICH FLOOD AND ARE NOT"
            f" FROST SECTION.")
