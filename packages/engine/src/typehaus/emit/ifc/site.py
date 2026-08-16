"""IFC emission for the parcel: the earth sheet, buried utilities, footing bedding, georef.

Split out of :mod:`typehaus.emit.ifc.emitter` (→ AGENTS.md §1.1). Everything here is measured
from grade rather than from a storey, and that is the seam: the earth sheet's top face *is*
the grade plane (its voids are the excavated footprints), a utility line is authored as a
depth below it, a footing's bedding is the excavation under the pour, and ``_georef`` is what
ties this local frame to a real coordinate system.
"""

from __future__ import annotations

from typing import Any

from typehaus._meta import PSET_SOURCE
from typehaus.emit.ifc import lowlevel as ll
from typehaus.model.ids import derive_child_guid, derive_guid
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry import polygon_area, rect_between
from typehaus.resolve.model import ResolvedModel


def _earth_sheet(model: ResolvedModel):
    """The IR's site earth prism, or ``None`` when the model carries no derived geometry.

    ``resolve_preview`` skips the geometry stage deliberately, so every IR read in this
    emitter is optional rather than assumed.
    """
    geometry = getattr(model, "geometry", None)
    element = geometry.by_uid("site-earth") if geometry is not None else None
    if element is None or not element.parts:
        return None
    return element.parts[0].solids[0]


def _emit_site_representation(f: Any, body: Any, ifc_site: Any, model: ResolvedModel) -> None:
    """The earth sheet of the parcel ring — imports as a lot slab (Phase 4).

    The sheet is cut by every excavated footprint (house, garage, sunken garden — see
    ``resolve/site_earth.py``); without those voids the lot slab runs straight through the
    interior spaces that were dug out of it.

    Geometry comes from the IR, which puts the sheet's *top* face on the grade plane. IFC
    used to extrude the same ring 5cm **upward** from grade, so the ground the exporter
    handed Revit stood 5cm above the ground the viewer drew and every slab-on-grade sat that
    much proud of its own site. Soil is what is under grade; this is the reconciliation the
    earth's blessed diff called for.
    """
    site = model.plan.project.site
    parcel = [p.xy_m for p in site.parcel]
    if len(parcel) < 3:
        return
    sheet = _earth_sheet(model)
    if sheet is not None:
        ll.assign_representation(f, ifc_site, ll.add_prism_from_profile(
            f, body, list(sheet.ring), sheet.z1_m - sheet.z0_m, sheet.z0_m, sheet.voids))
    props = {"parcel_area_m2": abs(polygon_area(parcel))}
    for spec in site.setbacks:
        key = f"setback_edge{spec.edge}_{spec.label or 'UNLABELED'}_ft"
        props[key] = spec.distance.inches / 12.0
    ll.ensure_pset(f, ifc_site, "TypeHaus_Site", props)


def _emit_utilities(f: Any, body: Any, model: ResolvedModel, project_uuid: Any) -> None:
    site = model.plan.project.site
    grade_z = site.grade.meters if site.grade is not None else 0.0
    for line in site.utilities:
        path = [p.xy_m for p in line.path]
        if len(path) < 2:
            continue
        depth_m = line.depth.meters if line.depth is not None else 1.0
        z0 = grade_z - depth_m
        for index in range(len(path) - 1):
            profile = rect_between(path[index], path[index + 1], -0.05, 0.05)
            child_key = f"seg-{index:02d}"
            uid = f"{line.kind.value}/{line.entry.xy_m}/{child_key}"
            element = ll.create_entity(f, "IfcBuildingElementProxy",
                                       name=f"UTIL-{line.kind.value}/{child_key}")
            element.GlobalId = derive_child_guid(project_uuid, "site-utilities", uid)
            ll.assign_representation(
                f, element, ll.add_prism_from_profile(f, body, profile, 0.1, z0))
            ll.ensure_pset(f, element, "TypeHaus_Utility", {
                "kind": line.kind.value, "entry_x_m": line.entry.xy_m[0],
                "entry_y_m": line.entry.xy_m[1],
            })


def _emit_footing_bedding(f: Any, body: Any, bedding: Any, storeys: dict[str, Any],
                          project_uuid: Any) -> None:
    """Excavation/bedding prep as a proxy solid under the footing (its own outline,
    from the compacted-stone-bed underside up to the footing underside)."""
    element = ll.create_entity(f, "IfcBuildingElementProxy", name=bedding.tag)
    element.GlobalId = derive_guid(project_uuid, bedding.uid)
    ll.assign_representation(f, element, ll.add_prism_from_profile(
        f, body, bedding.outline, bedding.z1_m - bedding.z0_m, bedding.z0_m,
    ))
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": bedding.uid, "tag": bedding.tag,
                                               "host": bedding.host})
    ll.ensure_pset(f, element, "TypeHaus_FootingBedding", {
        "host": bedding.host,
        "aggregate": bedding.aggregate,
        "geotextile": bedding.geotextile,
        "drain_tile": bedding.drain_tile,
        "perimeter_insulation_in": (bedding.perimeter_insulation_m / M_PER_IN
                                    if bedding.perimeter_insulation_m is not None else 0.0),
        "cast_foam_in_aggregate": bedding.cast_foam_in_aggregate,
    })
    ll.assign_container(f, element, storeys[bedding.storey])


def _georef(f: Any, ifc_project: Any, model: ResolvedModel, source_context: Any) -> None:
    """IfcProjectedCRS + IfcMapConversion from Site (pyproj transforms, → 12)."""
    site = model.plan.project.site
    crs = f.createIfcProjectedCRS(site.crs)
    try:
        import math

        import pyproj

        transformer = pyproj.Transformer.from_crs("EPSG:4326", site.crs, always_xy=True)
        easting, northing = transformer.transform(site.lon, site.lat)
        # A lat/lon outside the target CRS's valid domain (e.g. the (0, 0) placeholder a
        # minimal test fixture authors against the Minnesota UTM default) transforms to inf,
        # not an exception — IfcMapConversion then rejects it outright. Best-effort means
        # this falls back with everything else out-of-domain, not that it takes the whole
        # export down.
        if not (math.isfinite(easting) and math.isfinite(northing)):
            raise ValueError("non-finite georeference transform")
    except Exception:  # noqa: BLE001 - georef is best-effort in M1
        easting, northing = 0.0, 0.0
    f.createIfcMapConversion(
        source_context, crs, easting, northing, site.elevation.meters,
        1.0, 0.0,  # XAxisAbscissa/Ordinate — true_north rotation applied here
        1.0,
    )
