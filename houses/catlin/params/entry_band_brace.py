"""The west band brace and the canopy's rated head/base extras (owner, 2026-09-30).

`W-BW-SCREEN` tops out at +4'-0" and the `BM-BW-RW` glulam's soffit is at +6'-4 1/8". The band
between them carries the canopy's whole N-S shear. Since 2026-10-26, SB-BW-BAND has one
6x6 knee brace per bay running exactly corner to corner, chord to top plate, with two
standard open-knee KBS1Z per end; both faces are flush. Hand oracle:
`notes/canopy_west_band.md` §3. The c = -6½" 4x6 and the former chevron are backups in §8.

Every uid here was minted once with `typehaus.model.ids.new_uid()` (fmt never visits
`params/`) and must never be re-typed.
"""

from params.canopy_beam_hoods import ELEMENTS as BEAM_HOOD_ELEMENTS
from params.north_entry_frame import (
    COLUMN_HALF_FT,
    EAST_POST_SYSTEM,
    GARAGE_SEAT_Y_FT,
    HEADER_SOFFIT_FT,
    HEADER_TOP_FT,
    LANDING_WEST_FT,
    PIER_LINE_Y_FT,
    ROOF_COLUMN_EAST_X_FT,
    SCREEN_CLADDING_WEST_X_FT,
    SCREEN_PANEL_TOP_FT,
)
from typehaus import (
    Connector,
    ConnectorKind,
    Flashing,
    FormedFlashingSection,
    SlatBrace,
    TrimKind,
    ft,
    inch,
    pt,
)

BAND = SlatBrace(
    uid="8QGAZ9GGFS", tag="SB-BW-BAND",
    start=pt(ft(LANDING_WEST_FT), ft(PIER_LINE_Y_FT)),
    end=pt(ft(LANDING_WEST_FT), ft(GARAGE_SEAT_Y_FT)),
    base_elevation=ft(SCREEN_PANEL_TOP_FT), top_elevation=ft(HEADER_SOFFIT_FT),
    slat="6x6", corner_to_corner=True, connectors_per_end=2,
    plane_offset=inch(0), assembly="POST_KDAT", supported_by="W-BW-SCREEN",
    # Under TR-BW-SCREEN-CAP: the dielectric between its steel and the KDAT, and the seal at
    # every cut-out, turned up each slat and post 1" (the porch beams' wide roll).
    top_protection="butyl-tape-beam",
    connects=("PT-BW-CW", "PT-BW-CNW", "BM-BW-RW", "W-BW-SCREEN"),
    source="notes/canopy_west_band.md §3, 2026-10-26 — one 6x6 corner-to-corner knee brace "
           "per bay, chord to top plate, two open-knee KBS1Z each end (ER-280 Table 7 "
           "type 1, equal width, interpolated to 45.868 deg)")

# ** THE EAVE COLLECTOR: THE DECK'S N-S SHEAR INTO THE WEST HEADER. ** The deck's boundary
# nailing lands on the truss heels and the eave blocking; H2.5ASS heel ties carry 110 lb of
# lateral each, nowhere near 1,045. Two LTP4 per bay, blocking to glulam top (note §3e).
# The diaphragm recipe derives solid, bevelled 2-2x10 SPF heel blocks in every bay, flush
# with the header's inboard face; the plates join them to the glulam directly. ZMAX with HDG
# nails: Simpson publishes no stainless LTP4, and the glulam is treated (IRC R317.3.1).
_CLIP_Y_FT = (38.0, 39.0, 40.0, 41.0, 42.0, 42.75)
_CLIP_UIDS = ("2BGWCYHP73", "SDMYFZXN5Z", "812X7GD63H", "TGHVBBPNB4", "P6GS6PHFXD",
              "3XNNDTGRTE")
EAVE_CLIPS = [
    Connector(uid=_uid, tag=f"CN-BW-EAVE-{_i + 1}", kind=ConnectorKind.TENSION_TIE,
              position=pt(ft(LANDING_WEST_FT), ft(_y)), elevation=ft(HEADER_TOP_FT),
              size="LTP4Z", axis="y", connects=("RF-BW-CANOPY", "BM-BW-RW"),
              source=("canopy_west_band.md §3e — bevelled 2-2x10 SPF blocking to BM-BW-RW; "
                      "12 0.131x1.5in HDG nails per LTP4Z, six into each member, direct to wood"))
    for _i, (_y, _uid) in enumerate(zip(_CLIP_Y_FT, _CLIP_UIDS, strict=True))
]
# ** THE EAST CHORD INTO ITS END STRAP. ** CN-BW-JOINT-7 nails into the joint-bay 2-2x10 block,
# not the glulam; this plate is the east chord force's only way between them. "-y" puts it
# on the header's west (inboard) face, where the block is flush.
EAVE_CLIPS.append(
    Connector(uid="SQVBR8AEND", tag="CN-BW-EAVE-E", kind=ConnectorKind.TENSION_TIE,
              position=pt(ft(ROOF_COLUMN_EAST_X_FT), ft(_CLIP_Y_FT[-1])),
              elevation=ft(HEADER_TOP_FT), size="LTP4Z", axis="-y",
              connects=("RF-BW-CANOPY", "BM-BW-RE"),
              source=("canopy_west_band.md §6 — 2-2x10 joint-bay block to BM-BW-RE, the chord "
                      "force into CN-BW-JOINT-7; 12 0.131x1.5in HDG nails, six per member")))


def _head_angles(x_ft, south_tag, north_tag, south_uid, north_uids, beam):
    """The across-beam path an AC cap does not rate (ESR-2604 Table 3 fn. 6).

    Retain one south / two north angles: the west tail extension does not increase
    their graded transverse demand or require another angle at the south post.
    """
    out = [Connector(uid=south_uid, tag=f"CN-BW-A35-{south_tag[6:]}N",
                     kind=ConnectorKind.TENSION_TIE,
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

# The cap sits ON the exposed sill, fitted around the brace and its connectors. It never
# changes a bearing surface or the sill-to-wall interface. West drip clears the corrugated;
# east return projects only 1/8" past the existing 2x6, preserving passage clearance.
_CAP_WEST_FT = SCREEN_CLADDING_WEST_X_FT - 0.125 / 12
_CAP_EAST_FT = LANDING_WEST_FT + (2.75 + 0.125) / 12
_CAP_CENTRE_FT = (_CAP_WEST_FT + _CAP_EAST_FT) / 2
SILL_CAP = Flashing(
    uid="PD2PPXS59S", tag="TR-BW-SCREEN-CAP", kind=TrimKind.BEAM_CAP,
    path=(pt(ft(_CAP_CENTRE_FT), ft(PIER_LINE_Y_FT + COLUMN_HALF_FT)),
          pt(ft(_CAP_CENTRE_FT), ft(GARAGE_SEAT_Y_FT - COLUMN_HALF_FT))),
    top_elevation=ft(SCREEN_PANEL_TOP_FT + 1.5 / 12), depth=inch(0.75),
    thickness=ft(_CAP_EAST_FT - _CAP_WEST_FT), back_side="right",
    material="metal-dark-exterior", host_ref=BAND.tag,
    section=FormedFlashingSection(profile="cap", slope=0.25 / 12, fit_to_brace_sill=True))

ELEMENTS = [BAND, SILL_CAP, *EAVE_CLIPS, *HEAD_ANGLES, *PLATE_ANGLES, *BEAM_HOOD_ELEMENTS]
