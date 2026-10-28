"""Metal Sales trim used by the exterior metal envelope.

Sections are centerline polylines in inches. An empty section means the section has not
been transcribed; consumers must not treat it as a drawable profile.
"""

from typehaus.library.trim._image_ii import (  # noqa: F401 -- re-exported
    COBRA_VENT_IN,
    IMAGE_II_EXTENDED_EAVE,
    IMAGE_II_FLAT_CLEAT,
    IMAGE_II_OFFSET_CLEAT,
    IMAGE_II_RAKE_CLEAT,
    IMAGE_II_RESIDENTIAL_PEAK,
    IMAGE_II_RESIDENTIAL_RAKE,
    IMAGE_II_RIDGE_COVER,
    IMAGE_II_VENTED_STEP_RIDGE,
    IMAGE_II_Z_CLOSURE,
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
    source="PBR Install Guide 4/2024 pp. 16, 58",
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
    section_in=((0, 2.5), (0, 0), (1.5, 0), (1.8536, -0.3536)),
    receiver_throat_in=1.5,
    source="PBR Install Guide 4/2024 pp. 20, 68-72",
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
PBR_BOX_GUTTER_5X4 = TrimProfile(
    "PBR Box Gutter 5 x 4",
    _pvdf("58077XX") + _pvdf("58079XX", 243.0),
    (122.0, 243.0),
    ((0.0, BOX_GUTTER_BACK_IN), (0.0, 0.0), (BOX_GUTTER_BOTTOM_IN, 0.0),
     (BOX_GUTTER_BOTTOM_IN, BOX_GUTTER_FRONT_IN)),
    source="PBR Install Guide 4/2024 pp. 12, 46",
)

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
    "cobra-vented-closure": ("Cobra vented closure", "LF", "Image II PIM p. 20"),
    "58081XX": ("PBR box gutter end cap, left", "ea", "PBR Install Guide 4/2024 p. 12"),
    "58082XX": ("PBR box gutter end cap, right", "ea", "PBR Install Guide 4/2024 p. 12"),
    "58092XX": ("PBR box gutter strap", "ea", "PBR Install Guide 4/2024 p. 12"),
}

#: The profile-matched closure behind a head or sill trim, by the panel's finish.
PANEL_CLOSURE = {"ribbed-panel": "6460800", "board-and-batten": "55548XX",
                 "corrugated": "corrugated-closure"}

PROFILES = {key: value for key, value in globals().copy().items() if isinstance(value, TrimProfile)}
