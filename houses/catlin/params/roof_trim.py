"""RF-HOUSE eave water: the PBR 5 x 4 box gutter and its leaders (Tier 2, WP roof-eave).

The eaves are the WEST and EAST footprint edges (ridge N-S). RF-HOUSE has no fascia: the roof
footprint IS the wall cladding's outer face, and the eave is the Image II Extended Eave
(``resolve/roof_image_ii.py``). The chain, each piece shedding onto the next:

    Image II pan -> Extended Eave (face, kick) -> box gutter -> north-end leader

The gutter is stock PBR 58079XX, **installed level**, its back tucked behind the eave face and
its 3-1/2" roof flange run up the slope under the eave's pitched leg (PBR p. 46). Its place is
the catalog section's origin (back water face at the back top), read off the same
``EaveStack`` the engine stacks the eave with, built here from the roof's own layers
(``params/roof_panel``). No number below is typed in by hand. The engine sweeps the whole
formed piece and its end caps (``resolve/gutter_formed.py``); ``test_catlin_eave_water.py``
holds the laps. notes/box_gutter_sizing.md sizes it.

Not `# haus: editable`: params-generated trim, not UI-movable.
"""

from __future__ import annotations

from params.cladding import HOUSE_EW_OUTBOARD_IN, HOUSE_NS_OUTBOARD_IN
from params.roof_panel import EAVE_DECK_IN, PITCH, ROOFING_BASE_IN
from typehaus import DischargeExtension, Downspout, Gutter, TrimKind, ft, inch, pt
from typehaus.library.trim.metal_sales import BOX_GUTTER_BACK_IN, BOX_GUTTER_BOTTOM_IN
from typehaus.quantities import M_PER_IN
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M
from typehaus.resolve.roof_image_ii_eave import EaveStack

_HOUSE_FT = 36.0
#: The cladding face (== roof footprint edge); see params/cladding.py for the stack.
_WALL_OUTBOARD_IN = HOUSE_EW_OUTBOARD_IN
_EAVE_X_W = ft(0) - inch(_WALL_OUTBOARD_IN)
_EAVE_X_E = ft(_HOUSE_FT) + inch(_WALL_OUTBOARD_IN)
_EAVE_DECK = inch(EAVE_DECK_IN)  # structure plane at the eave edge (ResolvedRoof.eave_z_m)

#: The eave stack only needs the pitch and the roofing's base; the strip-in does not move it.
_STACK = EaveStack(slope=PITCH, membrane_top_w=ROOFING_BASE_IN * M_PER_IN,
                   strip_thickness_m=0.0, strip_material=None)
_ORIGIN_U_M, _ORIGIN_Z_M = _STACK.gutter_origin()
_GUTTER_BACK_IN = _ORIGIN_U_M / M_PER_IN   # back water face, out from the cladding face
_GUTTER_TOP_IN = _ORIGIN_Z_M / M_PER_IN    # back top == front crest, above the deck plane
#: Underside of the trough floor: the leader's top.
_TROUGH_FLOOR_IN = _GUTTER_TOP_IN - BOX_GUTTER_BACK_IN - SHEET_24_GA_M / M_PER_IN
#: Mid-width of the floor, where the leader takes its outlet.
_TROUGH_MID_IN = _GUTTER_BACK_IN + BOX_GUTTER_BOTTOM_IN / 2.0

#: The coil the chain is ordered in — ``RF-HOUSE.edge_trim_material``, the house's one exterior
#: dark, so the eave line reads as one dark outline. The leader takes the same coil.
_CHAIN_MATERIAL = "metal-dark-exterior"

#: The gutter design basis (SMACNA): St Paul 10-yr 5-min depth, NOAA Atlas 14 point table
#: (HDSC PDS, 2026-10-27). Intensity is depth over 5 min, x 12. notes/box_gutter_sizing.md §1.
_DESIGN_DEPTH_10YR_5MIN_IN = 0.628
_DESIGN_INTENSITY_IN_HR = _DESIGN_DEPTH_10YR_5MIN_IN * 12.0   # 7.54


def _above_deck(vertical_in: float):
    """An absolute elevation from a vertical offset above the deck plane at the eave."""
    return _EAVE_DECK + inch(vertical_in)


# The eaves run the full footprint, to the gable cladding faces; the engine carries the
# trough on to the eave piece's own end and caps it there.
_EAVE_Y0 = ft(0) - inch(HOUSE_NS_OUTBOARD_IN)
_EAVE_Y1 = ft(_HOUSE_FT) + inch(HOUSE_NS_OUTBOARD_IN)


def _out(eave_x, outward: float, inches_val: float):
    offset = inch(inches_val)
    return eave_x + offset if outward > 0 else eave_x - offset


def _eave_water(side: str, index: int, eave_x, outward: float):
    """One eave's box gutter; ``outward`` is -1 west / +1 east.

    Both runs go south->north (+y), whose left-hand normal points west: the house is on the
    right of the west run and on the left of the east one, which tells the section its back.
    """
    x = _out(eave_x, outward, _GUTTER_BACK_IN)
    return Gutter(
        uid=f"RTGT0{index}AAAA", tag=f"TR-RF-GUTTER-{side}", kind=TrimKind.GUTTER,
        path=(pt(x, _EAVE_Y0), pt(x, _EAVE_Y1)),
        top_elevation=_above_deck(_GUTTER_TOP_IN), depth=inch(BOX_GUTTER_BACK_IN),
        thickness=inch(BOX_GUTTER_BOTTOM_IN), material=_CHAIN_MATERIAL, host_ref="RF-HOUSE",
        slope=f"installed level; outlet at the north end ({side})",
        downspout_ref=f"TR-RF-LEADER-{side}",
        back_side="right" if outward < 0 else "left", product="PBR_BOX_GUTTER_5X4")


# --- Downspouts ---------------------------------------------------------------------------
# One 4" round leader per eave, each draining half the roof (18' x 37.1' plan = 690.7 sf).
# At the St Paul 10-yr 5-min intensity a 4" round serves 2,001 sf and a 3" round 1,126 sf
# (PGI-18; notes/box_gutter_sizing.md §4). Both clear the design basis. The 4" stays because
# the 3" fails the 100-yr 5-min sloped cross-check.
#
# Both go to the NORTH end, discharging into the 4' gap toward the garage rather than onto
# the freestanding sunken-garden structure 5" off the south face. Each hangs on the trough's
# centre line, so it takes the outlet straight down out of the gutter floor. Each runs to its
# buried extension's riser and on to its own rain garden, mirrored about x=18'-0"
# (`_discharge`). The S-5! CanDuit clamps that
# hold it to the standing-seam siding are in plan/mep.py; per the reference they steady the
# leader and are explicitly not its primary support.
_LEADER_DIA_IN = 4.0
_LEADER_Y = ft(_HOUSE_FT) - inch(6.0)
# The riser from +1'-0" down to the extension's inlet bills with the extension.
_LEADER_BOTTOM = ft(1)


def _leader(side: str, index: int, eave_x, outward: float):
    x = _out(eave_x, outward, _TROUGH_MID_IN)
    return Downspout(
        uid=f"RTDS0{index}AAAA", tag=f"TR-RF-LEADER-{side}",
        position=pt(x, _LEADER_Y),
        top_elevation=_above_deck(_TROUGH_FLOOR_IN),
        bottom_elevation=_LEADER_BOTTOM,
        diameter=inch(_LEADER_DIA_IN),
        material=_CHAIN_MATERIAL, gutter_ref=f"TR-RF-GUTTER-{side}",
        # Four clamps at roughly 6' o.c. down the ~24' run (plan/mep.py::LEADER_CLAMPS).
        clamp_refs=tuple(f"CN-A-LEADER-{side}{n}" for n in (1, 2, 3, 4)),
        **_discharge(side, x))


# 4" solid PVC buried north to a pop-up emitter in the side's basin
# (params/landscape_gardens.py), the east run the west's mirror about x=18'-0". The WEST run
# passes west of SL-M-HP3PAD in open yard; the EAST one passes under walks D and C, so its
# inlet drops 8" to put the pipe's crown under their Class 5 base (-3'-7"). Both outlets
# stand within 2" of the basin floor (-4'-1"). notes/rain_garden_sizing.md §6.
# The WEST line also carries SM-B-RADON's pumped water: PR-B-SUMP-DISCH wyes into its riser
# at -1'-10" (plan/mep_drainage.py), so that basin takes groundwater too.
_INVERTS = {"W": (ft(-3, -4), ft(-3, -11)), "E": (ft(-4), ft(-4, -2))}


def _discharge(side: str, leader_x) -> dict:
    def mx(x_ft: float):
        return ft(x_ft) if side == "W" else ft(_HOUSE_FT - x_ft)

    inlet, outlet = _INVERTS[side]
    return dict(
        discharge_ref=f"RG-{side}-BASIN",
        extension=DischargeExtension(
            path=(pt(leader_x, _LEADER_Y), pt(mx(-1.5), ft(36, 2)),
                  pt(mx(-1.5), ft(46, 6)), pt(mx(-3.5), ft(49))),
            diameter=inch(4), material="pvc-sdr35",
            inlet_invert=inlet, outlet_invert=outlet))


# FORTIFIED Roof §4.5's drip is the Image II eave and rake pieces themselves.
ATTIC_ELEMENTS = [
    _eave_water("W", 1, _EAVE_X_W, -1.0), _eave_water("E", 2, _EAVE_X_E, 1.0),
    _leader("W", 1, _EAVE_X_W, -1.0), _leader("E", 2, _EAVE_X_E, 1.0),
]


# Wall corners are derived from the resolved cladding faces and their trim kits.
MAIN_ELEMENTS = []
