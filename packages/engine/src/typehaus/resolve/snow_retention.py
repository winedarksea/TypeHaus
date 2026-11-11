"""Dimensioned ColorGard component meshes in the shared roof-local frame."""

from typehaus.findings import Finding
from typehaus.hardware import snow_retention as dimensions
from typehaus.model.structure import Connector
from typehaus.resolve.geometry_ir import GBox, GMesh
from typehaus.resolve.geometry_slice_box import _hull, outward_box_mesh
from typehaus.resolve.model import ResolvedModel, ResolvedSolid
from typehaus.resolve.snow_retention_layout import snow_retention_layout


def resolve_snow_retention(model: ResolvedModel, connector: Connector,
                           storey: str) -> list[Finding]:
    layout, findings = snow_retention_layout(model, connector)
    if layout is None:
        return findings
    spec = connector.snow_retention
    assert spec is not None  # the shared layout refuses point-only connectors
    inch = dimensions.INCH_M
    clamp_bottom = layout.seam_height / inch - dimensions.CLAMP_TOE_BELOW_SEAM_TOP_IN
    clamp_top = clamp_bottom + dimensions.CLAMP_HEIGHT_IN
    rail_v = dimensions.RAIL_DOWNSLOPE_IN
    wall = dimensions.EXTRUSION_WALL_IN
    rail_bottom = clamp_top - dimensions.RAIL_FLANGE_HEIGHT_FROM_BOTTOM_IN
    rail_top = rail_bottom + dimensions.RAIL_HEIGHT_IN
    half_strip = dimensions.COLORSTRIP_WIDTH_IN / 2
    strip_centre = (rail_bottom + rail_top) / 2
    strip_bottom, strip_top = strip_centre - half_strip, strip_centre + half_strip
    strip_front = rail_v + wall + layout.sheet_thickness / inch

    def part(suffix, product, boxes, material=dimensions.ALUMINUM_MATERIAL):
        """Union of disjoint rectangular extrusion regions, all dimensions in inches."""
        positions, triangles = [], []
        for u0, u1, v0, v1, w0, w1 in boxes:
            bottom = tuple(layout.world(u * inch, v * inch, w0 * inch)
                           for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)))
            top = tuple(layout.world(u * inch, v * inch, w1 * inch)
                        for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)))
            mesh = outward_box_mesh(GBox(bottom, top))
            offset = len(positions)
            positions.extend(mesh.positions)
            triangles.extend(tuple(i + offset for i in tri) for tri in mesh.triangles)
        uid = f"{connector.uid or connector.tag}-{suffix}"
        model.solids.append(ResolvedSolid(
            uid=uid, tag=f"{connector.tag}-{suffix}", storey=storey,
            category="snow_guard", product=product, material=material,
            outline=_hull([(p[0], p[1]) for p in positions]),
            z0_m=min(p[2] for p in positions), z1_m=max(p[2] for p in positions),
            body_mesh=GMesh(tuple(positions), tuple(triangles)), derived=True,
            host_ref=connector.tag, group=connector.tag))

    for index, (start, end) in enumerate(layout.segments, 1):
        # Keep expansion joints visible, without changing purchased stock quantities.
        gap = dimensions.SPLICE_GAP_IN / 2
        a = start / inch + (gap if index > 1 else 0)
        b = end / inch - (gap if index < len(layout.segments) else 0)
        base_v = rail_v - dimensions.RAIL_BASE_WIDTH_IN
        part(f"RAIL-{index}", spec.crossmember, [
            (a, b, rail_v, rail_v + wall, rail_bottom, rail_top),
            (a, b, base_v, rail_v, clamp_top, clamp_top + wall),
            (a, b, rail_v + wall, rail_v + 2 * wall, rail_bottom, strip_bottom),
            (a, b, strip_front, rail_v + 2 * wall, strip_bottom, rail_bottom + wall),
            (a, b, rail_v + wall, rail_v + 2 * wall, strip_top, rail_top),
            (a, b, strip_front, rail_v + 2 * wall, rail_top - wall, strip_top)])
        if index < len(layout.segments):
            half = dimensions.SPLICE_LENGTH_IN / 2
            part(f"SPLICE-{index}", "ColorGard 2.0 Splice (included)", [
                (end / inch - half, end / inch + half, base_v, rail_v,
                 clamp_top - wall, clamp_top)])

    # One sheared strip for this run: no unnecessary joint at a crossmember splice.
    part("COLORSTRIP", "ColorGard ColorStrip", [
        (layout.start / inch, layout.end / inch, rail_v + wall,
         rail_v + wall + layout.sheet_thickness / inch,
         strip_bottom, strip_top)], layout.roof_material)

    for index, station in enumerate(layout.supports, 1):
        u = station / inch
        half_width = dimensions.CLAMP_WIDTH_IN / 2
        throat = dimensions.CLAMP_THROAT_WIDTH_IN / 2
        half_length = dimensions.CLAMP_LENGTH_IN / 2
        throat_top = clamp_bottom + dimensions.CLAMP_THROAT_HEIGHT_IN
        part(f"CLAMP-{index}", spec.clamp, [
            (u - half_width, u - throat, -half_length, half_length,
             clamp_bottom, throat_top),
            (u + throat, u + half_width, -half_length, half_length,
             clamp_bottom, throat_top),
            (u - half_width, u + half_width, -half_length, half_length,
             throat_top, clamp_top)])
        half_clip = dimensions.VERSACLIP_WIDTH_IN / 2
        foot_end = dimensions.VERSACLIP_FOOT_END_IN
        rise_end = dimensions.VERSACLIP_RISE_END_IN
        part(f"VERSACLIP-{index}", spec.attachment, [
            (u - half_clip, u + half_clip, -half_length, foot_end,
             clamp_top, clamp_top + wall),
            (u - half_clip, u + half_clip, foot_end, rise_end,
             clamp_top, clamp_top + 2 * wall),
            (u - half_clip, u + half_clip, rise_end, rail_v,
             clamp_top + wall, clamp_top + 2 * wall)])
        half_head = dimensions.BOLT_HEAD_WIDTH_IN / 2
        bolt_v = dimensions.BOLT_CENTRE_DOWNSLOPE_IN
        part(f"BOLT-{index}", "S-5-N M8 bolt (included)", [
            (u - half_head, u + half_head, bolt_v - half_head, bolt_v + half_head,
             clamp_top + wall, clamp_top + wall + dimensions.BOLT_HEAD_HEIGHT_IN)],
             dimensions.STAINLESS_MATERIAL)

    for index, station in enumerate(layout.snow_clips, 1):
        u = station / inch
        half = dimensions.SNOCLIP_WIDTH_IN / 2
        sheet = dimensions.SNOCLIP_SHEET_IN
        foot = layout.sheet_thickness / inch
        part(f"SNOCLIP-{index}", spec.snow_clip, [
            (u - half, u + half, -wall, 0, foot + sheet, clamp_top),
            (u - half, u + half, -dimensions.SNOCLIP_FOOT_DEPTH_IN, -wall,
             foot + sheet, foot + 2 * sheet),
            (u - half, u + half, 0, rail_v, clamp_top - sheet, clamp_top)])
        part(f"FOOT-{index}", "SnoClip rubber foot (included)", [
            (u - half, u + half, -dimensions.SNOCLIP_FOOT_DEPTH_IN, 0,
             foot, foot + sheet)], "epdm")
    return findings
