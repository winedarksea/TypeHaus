"""Geometry prerequisites for a lateral plate joining roof blocking to a collector beam."""

from __future__ import annotations

from collections.abc import Sequence

from shapely.geometry import Point, Polygon

from typehaus.engineering.blocking_geometry import top_at
from typehaus.model import Connector
from typehaus.resolve.geometry_members import member_box
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.roof_geometry import roof_height_at

# Face coincidence, not an allowance for a plate floating clear of its nailing wood.
ATTACHMENT_FACE_TOLERANCE_M = 1e-4


def collector_attachment_missing(model: ResolvedModel, roof_tag: str, collector_tag: str,
                                 clips: Sequence[Connector]) -> list[str]:
    """Require blocking beneath the deck and flush with each plate's upper nailing face.

    This is a geometry prerequisite, not verification of nail count, edge distances or
    the blocking's anchorage. Hardware entries alone cannot establish an installed path.
    """
    roof = next((roof for roof in model.roofs if roof.tag == roof_tag), None)
    collector = next((solid for solid in model.solids if solid.tag == collector_tag), None)
    if roof is None or collector is None:
        return [f"resolved roof and collector geometry for {roof_tag} into {collector_tag}"]
    blocks = [member for member in roof.members if member.category == "blocking"]
    clip_tags = {clip.tag for clip in clips}
    solids = {solid.tag: solid for solid in model.solids if solid.tag in clip_tags}
    tolerance = ATTACHMENT_FACE_TOLERANCE_M
    collector_outline = Polygon(collector.outline)
    missing = []
    for clip in clips:
        solid = solids.get(clip.tag)
        if solid is None or solid.body_mesh is None:
            missing.append(f"{clip.tag}: resolved collector plate body for its wood attachment")
            continue
        # Select the wood-facing surface, excluding the sheet's outward thickness face.
        upper_points = [point for point in solid.body_mesh.positions
                        if point[2] > collector.z1_m + tolerance
                        and collector_outline.boundary.distance(Point(point[:2])) <= tolerance]
        lower_points = [point for point in solid.body_mesh.positions
                        if collector.z0_m - tolerance <= point[2] < collector.z1_m - tolerance
                        and collector_outline.boundary.distance(Point(point[:2])) <= tolerance]
        supported = False
        for block in blocks:
            # Cut/swept blocking needs its real face geometry, not a bounding-box claim.
            if block.elevation_profile is not None:
                continue
            body = member_box(block)
            if body is None or not upper_points or not lower_points:
                continue
            outline = Polygon([point[:2] for point in body.corners_bottom])
            bases = [point[2] for point in body.corners_bottom]
            tops = [top_at(block, point[:2]) for point in upper_points]
            if (max(abs(z - collector.z1_m) for z in bases) <= tolerance
                    and all(outline.boundary.distance(Point(p[:2])) <= tolerance
                            for p in upper_points)
                    and all(top is not None and top >= point[2] - tolerance
                            and top >= roof_height_at(roof, point[:2]) - tolerance
                            for top, point in zip(tops, upper_points, strict=True))):
                supported = True
                break
        if not supported:
            missing.append(
                f"{clip.tag}: eave blocking between {roof_tag}'s deck and {collector_tag}'s "
                "top, with a face flush to the plate's upper nailing half; the hardware "
                "count alone does not connect the deck to the collector")
    return missing
