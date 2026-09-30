"""The west band brace and the canopy's rated head/base extras (owner, 2026-09-30).

`W-BW-SCREEN` tops out at +4'-0" and the `BM-BW-RW` glulam's soffit is at +6'-4 1/8". The 2'-4 1/8"
between them held only the in-fill slats and the two 6x6s, so the whole N-S shear had to bend
the posts through caps with no lateral rating. The band is now braced: a CS16 X on EACH face
of the frame, header face to the far post, flush with the 6x6 and glulam faces and 1" outboard
of the slats. A face's pair is two straps, one per load direction, each tension-only; the two
faces share a direction's force. Hand oracle: `notes/canopy_west_band.md` §3.

Every uid here was minted once with `typehaus.model.ids.new_uid()` (fmt never visits
`params/`) and must never be re-typed.
"""

from typehaus import Connector, ConnectorKind, StrapBrace, ft, inch, pt

from params.north_entry_frame import (
    COLUMN_HALF_FT,
    EAST_POST_SYSTEM,
    GARAGE_SEAT_Y_FT,
    HEADER_SOFFIT_FT,
    HEADER_TOP_FT,
    LANDING_WEST_FT,
    PIER_LINE_Y_FT,
    ROOF_COLUMN_EAST_X_FT,
    SCREEN_PANEL_TOP_FT,
)

# ** THE GEOMETRY IS SET BY THE NAILS AT THE POST END. ** A strap crosses a 6x6 face for only
# 5 1/2" / cos(theta), and CS16's two hole rows at 2 1/16" hold about one nail an inch, so the
# diagonal is steepened until six nails fit: the top ends stand 9 1/2" either side of midspan,
# not over the posts. On the glulam face there is room for many more.
_MID_Y_FT = (PIER_LINE_Y_FT + GARAGE_SEAT_Y_FT) / 2.0
_TOP_Y_OFFSET_FT = 9.5 / 12
_TOP_Z_FT = HEADER_TOP_FT - 1 / 12                  # 1" under the header top
_BOTTOM_Z_FT = SCREEN_PANEL_TOP_FT + 1 / 12         # 1" over the panel top and its cladding
_END_INSET_FT = 0.5 / 12                            # strap end 1/2" inside the far post face
_FACE_IN = 2.75                                     # half the 6x6 and the 5-1/2" glulam

#: ``(uid, tag, bottom y, top y)`` — D1 rises SOUTH from PT-BW-CNW (tension in a southward
#: push of the deck), D2 rises NORTH from PT-BW-CW (tension in a northward one).
_DIAGONALS = (
    ("D1", GARAGE_SEAT_Y_FT + COLUMN_HALF_FT - _END_INSET_FT, _MID_Y_FT - _TOP_Y_OFFSET_FT,
     {"W": "D8WTYA9CTR", "E": "FHXKYTZ61G"}),
    ("D2", PIER_LINE_Y_FT - COLUMN_HALF_FT + _END_INSET_FT, _MID_Y_FT + _TOP_Y_OFFSET_FT,
     {"W": "7ZKF7B86TT", "E": "APNR22T3W7"}),
)

BAND_STRAPS = []
for _d, _y_bot, _y_top, _uids in _DIAGONALS:
    # `face_plane` is to the LEFT of start->end: +x (east) for D1, which runs south, and -x for D2.
    _east_sign = 1 if _y_top < _y_bot else -1
    for _face, _sign in (("W", -_east_sign), ("E", _east_sign)):
        BAND_STRAPS.append(StrapBrace(
            uid=_uids[_face], tag=f"SB-BW-BAND-{_d}{_face}",
            start=pt(ft(LANDING_WEST_FT), ft(_y_bot)), start_elevation=ft(_BOTTOM_Z_FT),
            end=pt(ft(LANDING_WEST_FT), ft(_y_top)), end_elevation=ft(_TOP_Z_FT),
            face_plane=inch(_sign * _FACE_IN), product="CS16", width=inch(1.25), gauge=16,
            connects=("BM-BW-RW", "PT-BW-CNW" if _d == "D1" else "PT-BW-CW"),
            fasteners_each_end=6, fastener='10d x 2-1/2" common, HDG',
            source="notes/canopy_west_band.md §3 — tension-only, ESR-2105 Table 4 CS16; six "
                   "nails at each end, all six fit on the 6x6 face"))

# ** THE EAVE COLLECTOR: THE DECK'S N-S SHEAR INTO THE WEST HEADER. ** The deck's boundary
# nailing lands on the truss heels and the eave blocking; H2.5ASS heel ties carry 110 lb of
# lateral each, nowhere near 1,045. Two LTP4 per bay, blocking to glulam top (note §3e).
_CLIP_Y_FT = (38.0, 39.0, 40.0, 41.0, 42.0, 42.75)
_CLIP_UIDS = ("2BGWCYHP73", "SDMYFZXN5Z", "812X7GD63H", "TGHVBBPNB4", "P6GS6PHFXD",
              "3XNNDTGRTE")
EAVE_CLIPS = [
    Connector(uid=_uid, tag=f"CN-BW-EAVE-{_i + 1}", kind=ConnectorKind.TENSION_TIE,
              position=pt(ft(LANDING_WEST_FT), ft(_y)), elevation=ft(HEADER_TOP_FT),
              size="LTP4", axis="y", connects=("RF-BW-CANOPY", "BM-BW-RW"),
              source="canopy_west_band.md §3e — eave blocking to BM-BW-RW, the N-S collector")
    for _i, (_y, _uid) in enumerate(zip(_CLIP_Y_FT, _CLIP_UIDS, strict=True))
]


def _head_angles(x_ft, south_tag, north_tag, south_uid, north_uids, beam):
    """A35Z on each post face that has the glulam's soffit over it: the across-beam path an
    AC cap does not rate (ESR-2604 Table 3 fn. 6). The header ENDS on the south post."""
    out = [Connector(uid=south_uid, tag=f"CN-BW-A35-{south_tag[6:]}N", kind=ConnectorKind.TENSION_TIE,
                     position=pt(ft(x_ft), ft(PIER_LINE_Y_FT + COLUMN_HALF_FT)),
                     elevation=ft(HEADER_SOFFIT_FT), size="A35Z", axis="x",
                     connects=(beam, south_tag))]
    for (face, dy), uid in zip((("S", -COLUMN_HALF_FT), ("N", COLUMN_HALF_FT)), north_uids,
                               strict=True):
        out.append(Connector(uid=uid, tag=f"CN-BW-A35-{north_tag[6:]}{face}",
                             kind=ConnectorKind.TENSION_TIE,
                             position=pt(ft(x_ft), ft(GARAGE_SEAT_Y_FT + dy)),
                             elevation=ft(HEADER_SOFFIT_FT), size="A35Z", axis="x",
                             connects=(beam, north_tag)))
    return out


HEAD_ANGLES = _head_angles(LANDING_WEST_FT, "PT-BW-CW", "PT-BW-CNW", "5A8157DVCY",
                           ("B0NRHTX5KQ", "Q770QM4P0J"), "BM-BW-RW")
if EAST_POST_SYSTEM == "kdat":
    HEAD_ANGLES += _head_angles(ROOF_COLUMN_EAST_X_FT, "PT-BW-RE", "PT-BW-RNE", "KBKGY27VPW",
                                ("RZM25K9XJ5", "MCMP8D4H02"), "BM-BW-RE")

# ** THE PANEL'S TOP PLATE INTO EACH POST, E-W. ** The panel spans vertically to its top plate,
# which dies into the two posts' side faces; its out-of-plane reaction (and the slat band's
# bottom half) reaches the posts through one A35Z at each plate end (note §5b).
PLATE_ANGLES = [
    Connector(uid=_uid, tag=f"CN-BW-PLATE-{_s}", kind=ConnectorKind.TENSION_TIE,
              position=pt(ft(LANDING_WEST_FT), ft(_y)), elevation=ft(SCREEN_PANEL_TOP_FT),
              size="A35Z", axis="x", connects=("W-BW-SCREEN", _post))
    for _s, _y, _post, _uid in (
        ("S", PIER_LINE_Y_FT + COLUMN_HALF_FT, "PT-BW-CW", "F7D0CY64SS"),
        ("N", GARAGE_SEAT_Y_FT - COLUMN_HALF_FT, "PT-BW-CNW", "EA9WDEE7QV"),
    )
]

ELEMENTS = [*BAND_STRAPS, *EAVE_CLIPS, *HEAD_ANGLES, *PLATE_ANGLES]
