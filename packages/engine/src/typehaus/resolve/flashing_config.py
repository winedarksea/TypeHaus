"""Physical flashing dimensions; display offsets never change these sections.

The one set of numbers: the 3D opening flashing and the 2D opening-perimeter detail
(``emit/draw/detail_components/opening.py``) both read ``FLASHING``.
"""

from dataclasses import dataclass

from typehaus.quantities import inch


@dataclass(frozen=True)
class FlashingConfig:
    sheet_m: float = inch(0.032).meters
    sill_membrane_m: float = inch(0.060).meters
    perimeter_membrane_m: float = inch(0.020).meters
    head_rise_m: float = inch(3).meters
    outie_head_rise_m: float = inch(2).meters
    #: The drip's throw past the face it protects: the casing face, or the cladding.
    head_projection_m: float = inch(0.5).meters
    head_drop_m: float = inch(1.6).meters
    #: How far the head runs past each casing end (past the RO where there is no casing).
    head_end_lap_m: float = inch(1).meters
    #: Each end of the head's shedding leg turns up this far, so water leaves at the drip.
    head_end_dam_m: float = inch(0.75).meters
    #: Strip-in over the head's upstand: down the metal, and up the water plane above it.
    head_strip_lap_m: float = inch(2).meters
    back_dam_m: float = inch(1.5).meters
    #: The rigid strip the back dam is turned up against.
    back_dam_strip_m: float = inch(0.5).meters
    end_dam_m: float = inch(6).meters
    pan_drop_m: float = inch(0.75).meters
    #: Outie walls: the pre-foam membrane ("raccoon", BSI-048) laid on the sheathing face
    #: round the RO, under the foam, so the foam laps over it in shingle order.
    raccoon_band_m: float = inch(4).meters
    #: Outie walls: the band on each jamb post's outer face under the window flange's
    #: landing (a 1-3/8" fin less the jamb inset) and the J-receiver's edge, with lap.
    post_band_m: float = inch(2).meters
    perimeter_lap_m: float = inch(2).meters
    hem_m: float = inch(0.25).meters
    drainage_slope: float = 0.25 / 12
    #: Shim space between a window unit and the membrane at each jamb and the head.
    #: Buck and flashing consume additional RO space; the sill bears on the pan.
    install_gap_m: float = inch(0.25).meters
    obstacle_clearance_m: float = inch(0.0625).meters
    membrane_material: str = "fluid-applied-flashing"
    sill_shim_material: str = "kdat"


FLASHING = FlashingConfig()
