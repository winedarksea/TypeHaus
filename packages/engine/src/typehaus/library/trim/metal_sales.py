"""Metal Sales trim used by the exterior metal envelope.

Sections are centerline polylines in inches. An empty section means the section has not
been transcribed; consumers must not treat it as a drawable profile.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TrimProfile:
    name: str
    part_numbers: tuple[tuple[int, str, float, str], ...] = ()
    stock_lengths_in: tuple[float, ...] = (122.0,)
    section_in: tuple[tuple[float, float], ...] = ()
    receiver_throat_in: float | None = None
    min_lap_in: float = 2.0
    hem_notch_in: float = 0.0
    closure: str | None = None
    fastener_role: str = "trim_stitch_screw"
    fastener_spacing_in: float = 12.0
    fastener_rows: int = 1
    #: Extra fasteners through each lap (PBR corner laps are riveted 2 in o.c.; BBD75 takes none).
    lap_fasteners: int = 0
    source: str = ""
    custom: bool = False
    maker: str = "Metal Sales"


def _pvdf(number: str, length: float = 122.0) -> tuple[tuple[int, str, float, str], ...]:
    return ((24, "PVDF", length, number),)


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
    receiver_throat_in=1.5,
    source="7/8 inch Corrugated product manual 9/2011 p. P7/8-4",
)

IMAGE_II_EXTENDED_EAVE = TrimProfile(
    "Image II Extended Eave",
    _pvdf("52124XX"),
    hem_notch_in=3,
    source="Residential Design Manual 5/2024 pp. 6-12, 30-41",
)
IMAGE_II_OFFSET_CLEAT = TrimProfile(
    "Offset Cleat", ((24, "varies", 122.0, "5806499"),), source="Residential Design Manual 5/2024"
)
IMAGE_II_RESIDENTIAL_RAKE = TrimProfile(
    "Residential Rake", _pvdf("52126XX"), source="Residential Design Manual 5/2024 pp. 6-12, 30-41"
)
IMAGE_II_RAKE_CLEAT = TrimProfile(
    "Residential Rake Cleat", _pvdf("52132XX"), source="Residential Design Manual 5/2024"
)
IMAGE_II_RIDGE_COVER = TrimProfile(
    "7 inch Ridge/Hip Cover", _pvdf("52131XX"), source="Residential Design Manual 5/2024"
)
IMAGE_II_Z_CLOSURE = TrimProfile(
    "Image II Z-Closure", _pvdf("58603XX"), source="Residential Design Manual 5/2024"
)
IMAGE_II_RESIDENTIAL_PEAK = TrimProfile(
    "Residential Peak", _pvdf("52134XX"), source="Residential Design Manual 5/2024 p. 41"
)

IMAGE_II_RAKE_4IN_CUSTOM = TrimProfile(
    "Residential Rake, 4 in face, custom brake",
    custom=True,
    source="52126XX main leg extended 1-3/8 in; houses/catlin/notes/metal_trim_kit.md",
)
IMAGE_II_FLAT_CLEAT = TrimProfile(
    "Flat Cleat", ((24, "varies", 122.0, "5806199"),), source="Residential Design Manual 5/2024"
)
IMAGE_II_VENTED_RIDGE = TrimProfile(
    "Image II vented ridge (13 in step cover, Cobra vent)",
    custom=True,
    source="Image II PIM 3/2021 p. 20; part numbers unconfirmed with Metal Sales",
)

#: Stock face of the catalog Residential Rake's main leg (Residential Design Manual p. 9).
RESIDENTIAL_RAKE_FACE_IN = 2.625

#: Loose closures, sealant and tape: part -> (name, unit, source). Priced by the house.
SUPPLIES = {
    "6460800": ("PBR Inside Closure", "LF", "PBR Install Guide 4/2024 p. 69"),
    "55548XX": ("BBD75 C-Closure", "LF", "BBD75 Install Guide 10/2025 p. 22"),
    "corrugated-closure": ("Corrugated profile closure", "LF", "Corrugated manual p. P7/8-4"),
    "6411499": ("Universal Closure", "LF", "Residential Design Manual 5/2024"),
    "58603XX": ("Image II Z-Closure", "LF", "Residential Design Manual 5/2024"),
    "6403899": ("Double-bead tape", "LF", "Residential Design Manual 5/2024"),
    "butyl-tape": ("Butyl tape", "LF", "PBR Install Guide 4/2024 p. 69"),
    "tube-sealant": ("Tube sealant", "LF", "PBR Install Guide 4/2024 pp. 16-21"),
    "trim-stitch-screw": ("1/4-14 x 7/8 in stitch screw", "ea", "Metal Sales trim guides"),
    "trim-pop-rivet": ("1/8 in pop rivet", "ea", "Metal Sales trim guides"),
}

#: The profile-matched closure behind a head or sill trim, by the panel's finish.
PANEL_CLOSURE = {"ribbed-panel": "6460800", "board-and-batten": "55548XX",
                 "corrugated": "corrugated-closure"}

PROFILES = {key: value for key, value in globals().copy().items() if isinstance(value, TrimProfile)}
