"""House-roof wind clamps — parametric module (plan/wind_clamps.py has the layout rationale).

Twelve S-5-S clamps, three per eave corner, on the first three seams in from each rake. Each
clamp's elevation is the top of the standing-seam metal at its x, from the same
``seam_top_inches`` the PV clamps in ``params/solar.py`` use — never a typed literal.

Not ``# haus: editable``: a Connector is not a UI-movable kind, so nothing is written back
to these, and the eave x-stations are derived from the cladding face in ``params/roof_panel``.
"""

from params.roof_panel import seam_top_inches

from typehaus import Connector, ConnectorKind, inch, pt

ROOF_TAG = "RF-HOUSE"
# The eaves sit on the cladding face, 6.6" out from the 36'-0" footprint either side.
WEST_EAVE_IN = -6.6
EAST_EAVE_IN = 438.6
# Plan y of the three seams in from each rake.
SOUTH_STATIONS_IN = (8, 24, 40)
NORTH_STATIONS_IN = (424, 408, 392)


def _clamp(uid: str, tag: str, x_in: float, y_in: float) -> Connector:
    return Connector(
        uid=uid, tag=tag, kind=ConnectorKind.STANDING_SEAM_CLAMP,
        position=pt(inch(x_in), inch(y_in)), elevation=inch(seam_top_inches(x_in)),
        connects=(ROOF_TAG,), size="S-5-S")


HOUSE_ROOF_WIND_CLAMPS = [
    _clamp("YK8A1SM9QY", "CN-A-WIND-RFSW-1", WEST_EAVE_IN, SOUTH_STATIONS_IN[0]),
    _clamp("4WN1JM8CEM", "CN-A-WIND-RFSW-2", WEST_EAVE_IN, SOUTH_STATIONS_IN[1]),
    _clamp("QBF8MEM0Y2", "CN-A-WIND-RFSW-3", WEST_EAVE_IN, SOUTH_STATIONS_IN[2]),
    _clamp("4S2GHP86NJ", "CN-A-WIND-RFNW-1", WEST_EAVE_IN, NORTH_STATIONS_IN[0]),
    _clamp("1975K7T22B", "CN-A-WIND-RFNW-2", WEST_EAVE_IN, NORTH_STATIONS_IN[1]),
    _clamp("P82E2WK4H5", "CN-A-WIND-RFNW-3", WEST_EAVE_IN, NORTH_STATIONS_IN[2]),
    _clamp("TA82SFQ7ET", "CN-A-WIND-RFSE-1", EAST_EAVE_IN, SOUTH_STATIONS_IN[0]),
    _clamp("69ERPP5H3P", "CN-A-WIND-RFSE-2", EAST_EAVE_IN, SOUTH_STATIONS_IN[1]),
    _clamp("BDR46H1QRE", "CN-A-WIND-RFSE-3", EAST_EAVE_IN, SOUTH_STATIONS_IN[2]),
    _clamp("9HRSYREBH3", "CN-A-WIND-RFNE-1", EAST_EAVE_IN, NORTH_STATIONS_IN[0]),
    _clamp("6VZ2BHET24", "CN-A-WIND-RFNE-2", EAST_EAVE_IN, NORTH_STATIONS_IN[1]),
    _clamp("0E7Y1BH1RN", "CN-A-WIND-RFNE-3", EAST_EAVE_IN, NORTH_STATIONS_IN[2]),
]
