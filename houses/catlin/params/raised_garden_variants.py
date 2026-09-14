"""Raised-planter geometry used only by the sunken-garden comparison variants."""

from __future__ import annotations

from typehaus import FootingBedding, FoundationWall, Node, ft, inch, pt


def setback_planter_elements(*, court_west_axis_ft: float, court_east_axis_ft: float,
                             court_south_axis_ft: float, court_wall_thickness_in: float,
                             north_ft: float, bed_width_in: float, setback_in: float,
                             yard_grade_in: float, soil_height_in: float) -> list:
    """Return one closed, U-shaped planter ring with stable tags and no court contact."""

    wall_half_ft = court_wall_thickness_in / 24.0
    block_half_ft = 0.5
    setback_ft = setback_in / 12.0
    bed_width_ft = bed_width_in / 12.0

    west_inner = court_west_axis_ft - wall_half_ft - setback_ft - block_half_ft
    east_inner = court_east_axis_ft + wall_half_ft + setback_ft + block_half_ft
    south_inner = court_south_axis_ft - wall_half_ft - setback_ft - block_half_ft
    west_outer = west_inner - 1.0 - bed_width_ft
    east_outer = east_inner + 1.0 + bed_width_ft
    south_outer = south_inner - 1.0 - bed_width_ft

    coordinates = (
        ("N-RGV-NWI", west_inner, north_ft),
        ("N-RGV-NWO", west_outer, north_ft),
        ("N-RGV-SWO", west_outer, south_outer),
        ("N-RGV-SEO", east_outer, south_outer),
        ("N-RGV-NEO", east_outer, north_ft),
        ("N-RGV-NEI", east_inner, north_ft),
        ("N-RGV-SEI", east_inner, south_inner),
        ("N-RGV-SWI", west_inner, south_inner),
    )
    nodes = [Node(uid=f"RGVN{i:02d}AAAA", tag=tag, position=pt(ft(x), ft(y)))
             for i, (tag, x, y) in enumerate(coordinates, start=1)]

    top = inch(yard_grade_in + soil_height_in)
    base = inch(yard_grade_in - 6.0)
    shared = dict(assembly="RETAINING_BLOCK_12", top_elevation=top,
                  bottom_elevation=base, unbalanced_fill=inch(soil_height_in))
    edges = (
        ("W-RGV-NW-CAP", 0, 1), ("W-RGV-W-OUT", 1, 2),
        ("W-RGV-S-OUT", 2, 3), ("W-RGV-E-OUT", 3, 4),
        ("W-RGV-NE-CAP", 4, 5), ("W-RGV-E-IN", 5, 6),
        ("W-RGV-S-IN", 6, 7), ("W-RGV-W-IN", 7, 0),
    )
    walls = [FoundationWall(uid=f"RGVW{i:02d}AAAA", tag=tag,
                            start_node=coordinates[a][0], end_node=coordinates[b][0],
                            **shared)
             for i, (tag, a, b) in enumerate(edges, start=1)]
    beds = [FootingBedding(uid=f"RGVB{i:02d}AAAA", tag=f"FB-{wall.tag[2:]}",
                           host_ref=wall.tag, undercut=inch(6), width=inch(24),
                           aggregate="MnDOT Class 5 aggregate base", geotextile=True,
                           drain_tile=False)
            for i, wall in enumerate(walls, start=1)]
    return [*nodes, *walls, *beds]

