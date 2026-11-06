"""Published framing hole charts this house builds to (decision #117).

Not editable: a chart is transcribed data, read once and cited. ``Library.joist_hole_charts``
matches each to every deck of its member, so FS-ATTIC (editable) needs no import.
Hand-worked against the house's runs in ``notes/framing_bore_limits.md`` §11.
"""

from typehaus import JoistHoleChart, PublishedHole, inch

_TJI = "11.875 TJI 230"
_SOURCE = ("ICC-ES ESR-1153 (TJI joists), Figure 2, Table A; with Weyerhaeuser TJ-4000 "
           "Specifier's Guide p.8 \"Allowable Holes\" for the 5\" and 7\" columns and the "
           "1 1/2\" field hole")
_TABLE = ("Table A, End Support: minimum distance from edge of hole to inside face of "
          "nearest end support, 11-7/8\" TJI 230, round hole")

# (round hole size, Table A distance), as printed: 2" 1'-0", 3" 1'-6", 4" 2'-0", 5" 2'-6",
# 6 1/2" 3'-0", 7" 3'-6", 8 7/8" 6'-6". ESR-1153 omits the 5"/7" columns; the rest agree.
_LADDER = ((2.0, 12), (3.0, 18), (4.0, 24), (5.0, 30), (6.5, 36), (7.0, 42), (8.875, 78))

TJI_230_HOLES = JoistHoleChart(
    member=_TJI,
    source=_SOURCE,
    table=_TABLE,
    rows=tuple(PublishedHole(source=_SOURCE, table=f'{_TABLE}: {size:g}" column',
                             member=_TJI, max_diameter=inch(size),
                             zone_from_bearing=inch(dist))
               for size, dist in _LADDER),
    # Fn 1: "the clear distance between multiple holes must be twice the length of the
    # longest dimension of the largest hole".
    min_spacing_diameters=2.0,
    # TJ-4000: "1 1/2" holes may be cut anywhere in web outside of hatched zone" (6" at each
    # support) "if they are located 3" away horizontally (edge-to-edge) from a larger hole".
    field_hole_max=inch(1.5),
    field_hole_zone=inch(6),
    condition=("uniform loads; distances from END supports only (Table B, intermediate or "
               "cantilever, not transcribed); no span-adjustment factor is published; "
               "holes anywhere vertically in the web, 1/8\" of web left top and bottom; "
               "no flange cut or notched"),
)

JOIST_HOLE_CHARTS = (TJI_230_HOLES,)
