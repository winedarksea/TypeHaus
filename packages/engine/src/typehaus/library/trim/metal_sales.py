"""Metal Sales trim used by the exterior metal envelope.

Sections are centerline polylines in inches. An empty section means the section has not
been transcribed; consumers must not treat it as a drawable profile.
"""

import math

from typehaus.library.trim._image_ii import (  # noqa: F401 -- re-exported
    IMAGE_II_EXTENDED_EAVE,
    IMAGE_II_FLAT_CLEAT,
    IMAGE_II_OFFSET_CLEAT,
    IMAGE_II_RAKE_CLEAT,
    IMAGE_II_RESIDENTIAL_PEAK,
    IMAGE_II_RESIDENTIAL_RAKE,
    IMAGE_II_RIDGE_COVER,
    IMAGE_II_Z_CLOSURE,
    OPEN_HEM_GAP_IN,
)
from typehaus.library.trim.profile import TrimProfile
from typehaus.library.trim.profile import pvdf as _pvdf

PBR_BASE = TrimProfile(
    "1.25 inch Base",
    _pvdf("58138XX"),
    section_in=((0, 2.625), (0, 0), (1.25, 0), (1.6919, -0.4419)),
    receiver_throat_in=1.25,
    closure="6460800",
    source="PBR Install Guide 4/2024 pp. 20, 69",
)
WIDE_OUTSIDE_CORNER = TrimProfile(
    "Outside Corner - Wide",
    _pvdf("58132XX") + _pvdf("58136XX", 243.0),
    (122.0, 243.0),
    ((0.0, 5.5), (0.0, 0.0), (5.5, 0.0)),
    min_lap_in=3.0,
    fastener_role="trim_pop_rivet",
    fastener_rows=2,
    lap_fasteners=4,
    source="PBR Install Guide 4/2024 pp. 18, 66; BBD75 Install Guide 10/2025 pp. 16, 30",
)
BBD_BASE = TrimProfile(
    "Base Trim (vertical)",
    _pvdf("55545XX"),
    section_in=((0, 2.625), (0, 0), (1.2452, -0.1089), (1.6871, -0.5508)),
    hem_notch_in=2,
    closure="55548XX",
    source="BBD75 Install Guide 10/2025 pp. 16, 22",
)
BBD_C_CLOSURE = TrimProfile(
    "C-Closure",
    _pvdf("55548XX"),
    section_in=((0, 0), (2.75, 0), (2.75, 1), (1.75, 1)),
    hem_notch_in=2,
    source="BBD75 Install Guide 10/2025 pp. 17, 22",
)
BBD_TRANSITION = TrimProfile(
    "Transition Trim",
    _pvdf("55536XX"),
    section_in=((0, 2), (0, 0), (0.9962, -0.0872), (0.9962, -2.5872)),
    receiver_throat_in=1.0,
    hem_notch_in=2,
    fastener_role="trim_pop_rivet",
    fastener_rows=2,
    source="BBD75 Install Guide 10/2025 pp. 14, 40",
)
OPENING_HEAD = TrimProfile(
    "1.5 inch Sill/Head",
    _pvdf("58114XX"),
    section_in=((0, 2.5), (0, 0), (1.5, 0), (1.853553, -0.353553)),
    receiver_throat_in=1.5,
    # Also the BBD75 kit's window head: an accepted deviation, not a BBD75 row.
    source="PBR Install Guide 4/2024 pp. 20, 68-72. Not in the BBD75 Install Guide "
           "10/2025, which publishes only the trim-first 58720XX (p. 28); used on BBD75 "
           "walls because a window-first outie frame cannot go in under 58720XX's return",
)
#: BBD75's own head: 2-1/2 back leg, 1-1/8 seat at 95 deg, 2-1/2 face leg, a 4" return back
#: over the frame head and a 1/2" kick. A trim-first head: the frame goes in last under the
#: return (pp. 28-29 install order), so it does not seat over a window-first outie frame.
BBD_HEAD_TRIM = TrimProfile(
    "Head Trim",
    _pvdf("58720XX"),
    section_in=((0, 2.5), (0, 0), (1.1207, -0.0981), (1.1207, -2.5981), (-2.8793, -2.5981),
                (-3.2329, -2.9517)),
    receiver_throat_in=1.125,
    source="BBD75 Install Guide 10/2025 pp. 15, 28-29",
)
#: Window jamb sections are (along the wall, outward) from the rough-opening edge, as
#: ``window_jamb_section`` returns them. Legs: 1-3/8 reveal leg, 1 in C-hem over the rib,
#: 3-1/8 flange lapping the frame face (PBR pp. 21, 68).
PBR_WINDOW_JAMB = TrimProfile(
    "PBR Jamb",
    _pvdf("58208XX"),
    section_in=((-1.0, 1.375), (0.0, 1.375), (0.0, 0.0), (3.125, 0.0)),
    receiver_throat_in=1.375,
    source="PBR Install Guide 4/2024 pp. 21, 68",
)
WINDOW_JAMB_CUSTOM = TrimProfile(
    "Window jamb, custom brake",
    custom=True,
    source="Window-first outie detail, houses/catlin/notes/metal_trim_kit.md",
)
WINDOW_SILL_CUSTOM = TrimProfile(
    "Window sill cap, custom brake",
    custom=True,
    source="Window-first outie detail, houses/catlin/notes/metal_trim_kit.md",
)
BBD_PANEL_STARTER = TrimProfile(
    "Panel Starter",
    _pvdf("58728XX"),
    section_in=((0, 2.625), (0, 0), (1.125, 0)),
    receiver_throat_in=1.125,
    hem_notch_in=2,
    source="BBD75 Install Guide 10/2025 p. 14 (2-5/8 in and 1-1/8 in legs; hems not drawn)",
)
#: K6 over a metal-wall window head: 2" upstand on the foam, a top across the cavity and the
#: head course, a 2-1/2" (or longer, to lap 58114XX by 1") face leg, 3/4" end dams; 6.6-7" girth.
OPENING_HEAD_CAP = TrimProfile(
    "Window head cap (K6), custom brake",
    custom=True,
    source="Drained head over the outie window, houses/catlin/notes/opening_flashing_spec.md §4",
)
DOOR_HEAD_CUSTOM = TrimProfile(
    "Door head drip cap, custom brake",
    custom=True,
    source="Door head over casing, houses/catlin/notes/metal_trim_kit.md",
)
CORRUGATED_BASE = TrimProfile(
    "Corrugated 1.25 inch Base",
    section_in=PBR_BASE.section_in,
    receiver_throat_in=1.25,
    source="7/8 inch Corrugated product manual 9/2011 p. P7/8-4",
)
CORRUGATED_OUTSIDE_CORNER = TrimProfile(
    "Corrugated Outside Corner",
    stock_lengths_in=(122.0, 243.0),
    section_in=WIDE_OUTSIDE_CORNER.section_in,
    source="7/8 inch Corrugated product manual 9/2011 p. P7/8-4",
)
CORRUGATED_JAMB = TrimProfile(
    "Corrugated Jamb",
    section_in=((0, 2.5), (0, 0), (1, 0), (1, 1)),  # (outboard, along); back leg under panel
    receiver_throat_in=1.0,
    source="7/8 inch Corrugated product manual 9/2011 p. P7/8-4",
)
CORRUGATED_SILL_TO_SOFFIT = TrimProfile(
    "Corrugated Sill to Soffit 1.5 inch",
    section_in=((0, 2.5), (0, 0.08), (1.5, 0.08), (1.8536, -0.2736),
                (1.5, 0), (-3.25, 0), (-3.25, 0.08), (-2.875, 0.08)),
    receiver_throat_in=1.5,
    source="7/8 inch Corrugated product manual 9/2011 p. P7/8-4",
)

RAINSCREEN_BASE_Z = TrimProfile(
    "Rainscreen base Z, 0.040 inch aluminium", stock_lengths_in=(120.0,),
    custom=True, maker="custom brake", source="Catlin wall base stack",
)

#: Stock face of the catalog Residential Rake's main leg (Residential Design Manual p. 9).
RESIDENTIAL_RAKE_FACE_IN = 2.625

#: PBR box gutter 58077XX/58079XX (PBR Install Guide 4/24 p. 12). The front is the lower
#: side, so it is the waterway that sets the gutter's capacity (notes/box_gutter_sizing.md).
BOX_GUTTER_BOTTOM_IN = 5.0
BOX_GUTTER_BACK_IN = 5.0
BOX_GUTTER_FRONT_IN = 4.0
#: Hangers at 3'-0" o.c.: p. 46 gives no strap spacing, so this is the sculptured gutter's
#: maximum (p. 63), applied to the box. Confirm with Metal Sales.
BOX_GUTTER_STRAP_SPACING_FT = 3.0
#: The 3-1/2 in roof flange at the specified angle, and the front bead: 1 out, 1 up, 1 back.
BOX_GUTTER_FLANGE_IN = 3.5
BOX_GUTTER_BEAD_IN = 1.0
#: The bead's hem is drawn but not dimensioned on p. 12; read off the drawing at scale.
BOX_GUTTER_HEM_IN = 0.5


def pbr_box_gutter_section(slope: float, gap_in: float = OPEN_HEM_GAP_IN,
                           ) -> tuple[tuple[float, float], ...]:
    """The full 5 x 4 box gutter (PBR p. 12) with its flange at roof ``slope`` (rise/run).

    Inches, x outboard and y up, origin at the back top where the flange leaves it. The path
    is the water face (the sheet lies to its right). The front crest equals the back top.
    The bead's top leg ends in an open hem folded under it, ``gap_in`` clear.
    """
    angle = math.atan(abs(slope))
    flange = (-BOX_GUTTER_FLANGE_IN * math.cos(angle), BOX_GUTTER_FLANGE_IN * math.sin(angle))
    back, floor, front, bead = (BOX_GUTTER_BACK_IN, BOX_GUTTER_BOTTOM_IN, BOX_GUTTER_FRONT_IN,
                                BOX_GUTTER_BEAD_IN)
    crest = front - back + bead
    return (flange, (0.0, 0.0), (0.0, -back), (floor, -back), (floor, front - back),
            (floor + bead, front - back), (floor + bead, crest), (floor, crest),
            (floor, crest - gap_in), (floor + BOX_GUTTER_HEM_IN, crest - gap_in))


def pbr_box_gutter_end_cap(sheet_in: float) -> tuple[tuple[float, float], ...]:
    """The 58081XX/58082XX end cap's plate: the trough's outer outline up to the crest.

    Same frame as ``pbr_box_gutter_section``; ``sheet_in`` is the gutter's own thickness, so
    the plate covers the sheet's edge as the cap's flange laps it.
    """
    t, back, floor = sheet_in, BOX_GUTTER_BACK_IN, BOX_GUTTER_BOTTOM_IN
    bead_bottom = BOX_GUTTER_FRONT_IN - back - t
    return ((-t, 0.0), (-t, -back - t), (floor + t, -back - t), (floor + t, bead_bottom),
            (floor + BOX_GUTTER_BEAD_IN + t, bead_bottom), (floor + BOX_GUTTER_BEAD_IN + t, 0.0))


#: ``section_in`` is the waterway alone (back, floor, front); ``pbr_box_gutter_section`` is
#: the whole formed piece.
PBR_BOX_GUTTER_5X4 = TrimProfile(
    "PBR Box Gutter 5 x 4",
    _pvdf("58077XX") + _pvdf("58079XX", 243.0),
    (122.0, 243.0),
    ((0.0, BOX_GUTTER_BACK_IN), (0.0, 0.0), (BOX_GUTTER_BOTTOM_IN, 0.0),
     (BOX_GUTTER_BOTTOM_IN, BOX_GUTTER_FRONT_IN)),
    source="PBR Install Guide 4/2024 pp. 12, 46",
)

#: The 4 x 3-1/2 rectangular downspout (PBR Install Guide 4/2024 pp. 13-14): 4 in face by
#: 3-1/2 in, 14.0 sq in of waterway against a 4 in round's 12.57. Elbows 58102XX (95 deg) and
#: 58106XX (45 deg), strap 58110XX. Metal Sales rolls no round leader.
DOWNSPOUT_4X3_5_IN = (4.0, 3.5)
DOWNSPOUT_4X3_5 = TrimProfile(
    "Downspout 4 x 3-1/2",
    _pvdf("58094XX") + _pvdf("58097XX", 243.0),
    (122.0, 243.0),
    ((0.0, 0.0), (DOWNSPOUT_4X3_5_IN[0], 0.0), (DOWNSPOUT_4X3_5_IN[0], DOWNSPOUT_4X3_5_IN[1]),
     (0.0, DOWNSPOUT_4X3_5_IN[1])),
    source="PBR Install Guide 4/2024 pp. 13-14",
)

#: Gutter products whose whole formed piece is transcribed: product -> (section(slope),
#: end-cap plate(sheet_in), (left cap, right cap) part numbers as seen from the front).
FORMED_GUTTERS = {
    "PBR_BOX_GUTTER_5X4": (pbr_box_gutter_section, pbr_box_gutter_end_cap,
                           ("58081XX", "58082XX")),
}

#: Loose closures, sealant and tape: part -> (name, unit, source). Priced by the house.
SUPPLIES = {
    "6460800": ("PBR Inside Closure", "LF", "PBR Install Guide 4/2024 p. 69"),
    "55548XX": ("BBD75 C-Closure", "LF", "BBD75 Install Guide 10/2025 p. 22"),
    "corrugated-closure": ("Corrugated profile closure", "LF", "Corrugated manual p. P7/8-4"),
    "corrugated-outside-closure": ("Corrugated outside closure", "LF",
                                   "Corrugated manual p. P7/8-5"),
    "6411499": ("Universal Closure", "LF", "Residential Design Manual 5/2024"),
    "58603XX": ("Image II Z-Closure", "LF", "Residential Design Manual 5/2024"),
    "6403899": ("Double-bead tape", "LF", "Residential Design Manual 5/2024"),
    "butyl-tape": ("Butyl tape", "LF", "PBR Install Guide 4/2024 p. 69"),
    "epdm-isolation": ("EPDM dissimilar-metal isolation", "LF", "Catlin wall base stack"),
    "tube-sealant": ("Tube sealant", "LF", "PBR Install Guide 4/2024 pp. 16-21"),
    "trim-stitch-screw": ("1/4-14 x 7/8 in stitch screw", "ea", "Metal Sales trim guides"),
    "trim-pop-rivet": ("1/8 in pop rivet", "ea", "Metal Sales trim guides"),
    "6441899": ("Profile Vent, notched 16 in Image II, 100 ft roll", "LF",
                "Residential Design Manual 5/2024 pp. 13, 41"),
    "6540000": ("Image II Profile Vent Clip", "ea", "Residential Design Manual 5/2024 pp. 13, 41"),
    "8215100": ("#14 x 1-1/2 in metalwood screw", "ea", "Residential Design Manual 5/2024 p. 41"),
    "ridge-end-closure": ("Ridge cover gable-end closure, field-formed from the cover's coil", "ea",
                          "no catalog gable piece; RDM 5/2024 p. 39 hip end cap by analogy"),
    "58081XX": ("PBR box gutter end cap, left", "ea", "PBR Install Guide 4/2024 p. 12"),
    "58082XX": ("PBR box gutter end cap, right", "ea", "PBR Install Guide 4/2024 p. 12"),
    "58092XX": ("PBR box gutter strap", "ea", "PBR Install Guide 4/2024 p. 12"),
    "58102XX": ("4 x 3-1/2 in downspout elbow, 95 deg", "ea", "PBR Install Guide 4/2024 p. 14"),
    "58106XX": ("4 x 3-1/2 in downspout elbow, 45 deg", "ea", "PBR Install Guide 4/2024 p. 14"),
    "58110XX": ("4 in downspout strap", "ea", "PBR Install Guide 4/2024 p. 14"),
    "leader-rect-round-adapter": ("4 x 3-1/2 in rectangular to 4 in round leader adapter", "ea",
                                  "no Metal Sales part; into the buried 4 in PVC"),
}

#: The profile-matched closure behind a head or sill trim, by the panel's finish. Over a
#: rainscreen, a panel end at a base or head sits on a perforated strip instead
#: (``resolve/rainscreen_strips.py``), billed with the insect screens; sills stay closed.
PANEL_CLOSURE = {"ribbed-panel": "6460800", "board-and-batten": "55548XX",
                 "corrugated": "corrugated-closure"}

PROFILES = {key: value for key, value in globals().copy().items() if isinstance(value, TrimProfile)}
