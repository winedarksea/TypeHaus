"""House-roof wind clamps — parametric module (plan/wind_clamps.py has the layout rationale).

Twelve S-5-N Mini clamps, three per eave corner, on the first three seams in from each rake. Each
clamp's elevation is the top of the standing-seam metal at its x, from the same
``seam_top_inches`` the PV clamps in ``params/solar.py`` use — never a typed literal.

Not ``# haus: editable``: a Connector is not a UI-movable kind, so nothing is written back
to these. The eave x-stations are derived from the cladding face and the eave stack.
"""

from params.cladding import HOUSE_EW_OUTBOARD_IN
from params.roof_panel import seam_top_inches
from params.roof_trim import EAVE_STACK
from typehaus import Connector, ConnectorKind, inch, pt
from typehaus.quantities import M_PER_IN
from typehaus.resolve.accessories import seam_clamp_half_length_m
from typehaus.resolve.roof_image_ii_eave import LAP_GAP_M

ROOF_TAG = "RF-HOUSE"
_SIZE = "S-5-N Mini"
# Each clamp sits on the field seam just upslope of the eave pieces: its downslope end one
# lap gap inboard of the field skin's cut (``EaveStack.pan_cut_u``), off the cladding face.
_SEAT_IN = (EAVE_STACK.pan_cut_u() - seam_clamp_half_length_m(_SIZE) - LAP_GAP_M) / M_PER_IN
WEST_EAVE_IN = -HOUSE_EW_OUTBOARD_IN - _SEAT_IN
EAST_EAVE_IN = 36 * 12 + HOUSE_EW_OUTBOARD_IN + _SEAT_IN
# Plan y of the three seams in from each rake.
SOUTH_STATIONS_IN = (8, 24, 40)
NORTH_STATIONS_IN = (424, 408, 392)


def _clamp(uid: str, tag: str, x_in: float, y_in: float) -> Connector:
    return Connector(
        uid=uid, tag=tag, kind=ConnectorKind.STANDING_SEAM_CLAMP,
        position=pt(inch(x_in), inch(y_in)), elevation=inch(seam_top_inches(x_in)),
        connects=(ROOF_TAG,), size=_SIZE)


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
