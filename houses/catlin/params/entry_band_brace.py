"""The west band brace and the canopy's rated head/base extras (owner, 2026-09-30).

`W-BW-SCREEN` tops out at +4'-0" and the `BM-BW-RW` glulam's soffit is at +6'-4 1/8". The band
between them carries the canopy's whole N-S shear. Since 2026-10-04 it is `SB-BW-BAND`: a 2x6
sill and top plate, a 6x6 centre post, and KDAT 2x4 slats at 45° rising to the centre from each
chord, each one a knee brace with a KBS1Z at both ends. It replaced a CS16 X on each face, kept
as the first backup with the sheathed-pier option in the note's §8. Hand oracle:
`notes/canopy_west_band.md` §3.

Every uid here was minted once with `typehaus.model.ids.new_uid()` (fmt never visits
`params/`) and must never be re-typed.
"""

from typehaus import Connector, ConnectorKind, SlatBrace, ft, inch, pt

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

# ** THE SLATS SIT FLUSH WITH THE WEST FACE, WHERE THE KBS1Z GO. ** A KBS1Z joins in-line
# members face to face, so the 3 1/2" slats stand flush with the 5 1/2" posts, plates and
# glulam on one face: 1" west of the line (+ is LEFT of south->north, which is west).
BAND = SlatBrace(
    uid="8QGAZ9GGFS", tag="SB-BW-BAND",
    start=pt(ft(LANDING_WEST_FT), ft(PIER_LINE_Y_FT)),
    end=pt(ft(LANDING_WEST_FT), ft(GARAGE_SEAT_Y_FT)),
    base_elevation=ft(SCREEN_PANEL_TOP_FT), top_elevation=ft(HEADER_SOFFIT_FT),
    plane_offset=inch(1.0), assembly="POST_KDAT", supported_by="W-BW-SCREEN",
    connects=("PT-BW-CW", "PT-BW-CNW", "BM-BW-RW", "W-BW-SCREEN"),
    source="notes/canopy_west_band.md §3 — 45° slats as knee braces, KBS1Z each end "
           "(IAPMO UES ER-280 Table 7, type 2); the bays share the push, one in tension, "
           "one in compression")

# ** THE EAVE COLLECTOR: THE DECK'S N-S SHEAR INTO THE WEST HEADER. ** The deck's boundary
# nailing lands on the truss heels and the eave blocking; H2.5ASS heel ties carry 110 lb of
# lateral each, nowhere near 1,045. Two LTP4 per bay, blocking to glulam top (note §3e).
# 2026-10-05: those blocks are absent from the resolved truss roof. The plates' lower halves
# seat on the header but their upper halves have no wood; the collector is INCOMPLETE.
_CLIP_Y_FT = (38.0, 39.0, 40.0, 41.0, 42.0, 42.75)
_CLIP_UIDS = ("2BGWCYHP73", "SDMYFZXN5Z", "812X7GD63H", "TGHVBBPNB4", "P6GS6PHFXD",
              "3XNNDTGRTE")
EAVE_CLIPS = [
    Connector(uid=_uid, tag=f"CN-BW-EAVE-{_i + 1}", kind=ConnectorKind.TENSION_TIE,
              position=pt(ft(LANDING_WEST_FT), ft(_y)), elevation=ft(HEADER_TOP_FT),
              size="LTP4", axis="y", connects=("RF-BW-CANOPY", "BM-BW-RW"),
              source=("canopy_west_band.md §3e — PROPOSED eave-blocking attachment to BM-BW-RW; "
                      "blocking members and fastening unresolved"))
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

ELEMENTS = [BAND, *EAVE_CLIPS, *HEAD_ANGLES, *PLATE_ANGLES]
