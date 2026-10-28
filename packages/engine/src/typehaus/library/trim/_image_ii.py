"""Image II roof pieces (Metal Sales Residential Design Manual 5/2024, pp. 6-12).

``section_in`` runs from the piece's free end, in inches, x outboard of the bend (or the roof
edge) and y up. The roof resolver (``resolve/roof_image_ii.py``) places each section on the
edge. The flange of an eave is pitched, so the resolver rotates the block of points inboard
of the bend (x < 0) to the roof slope. Dimensions are checked by ``test_image_ii_roof_pieces``.
"""

import math

from typehaus.library.trim.profile import TrimProfile, pvdf

IMAGE_II_EXTENDED_EAVE = TrimProfile(
    "Image II Extended Eave",
    pvdf("52124XX"),
    # 7/8 in return off the 5 in deck flange, the flange, the 1-1/2 in face, the 5/8 in kick
    # and its 1/2 in drip hem. The manual's second 1-1/2 in lip is not drawn: its path is
    # unconfirmed (see the notes on the eave in metal_trim_kit.md).
    section_in=((-5.0, 0.875), (-5.0, 0.0), (0.0, 0.0), (0.0, -1.5),
                (0.625 * math.sin(math.pi / 4), -1.5 - 0.625 * math.cos(math.pi / 4)),
                (0.5 + 0.625 * math.sin(math.pi / 4),
                 -1.5 - 0.625 * math.cos(math.pi / 4))),
    hem_notch_in=3,
    source="Residential Design Manual 5/2024 pp. 6-12, 30-41",
)
IMAGE_II_OFFSET_CLEAT = TrimProfile(
    "Offset Cleat", ((24, "varies", 122.0, "5806499"),),
    section_in=((0.0, 0.0), (1.5, 0.0), (1.5 + math.sqrt(0.5**2 - 0.1875**2), 0.1875),
                (2.5 + math.sqrt(0.5**2 - 0.1875**2), 0.1875)),
    source="Residential Design Manual 5/2024 p. 12",
)
IMAGE_II_RESIDENTIAL_RAKE = TrimProfile(
    "Residential Rake", pvdf("52126XX"),
    # Top 1 in return over the panel turn-up, the 2-5/8 in main leg (origin at its foot),
    # the 5/8 in kick and the 1/2 in return hem back toward the building.
    section_in=((-1.0, 2.625), (0.0, 2.625), (0.0, 0.0),
                (0.625 * math.sin(math.pi / 4), -0.625 * math.cos(math.pi / 4)),
                (0.625 * math.sin(math.pi / 4) - 0.5, -0.625 * math.cos(math.pi / 4))),
    source="Residential Design Manual 5/2024 pp. 6-12, 30-41",
)
IMAGE_II_RAKE_CLEAT = TrimProfile(
    "Residential Rake Cleat", pvdf("52132XX"),
    # The 2-7/8 in leg lies on the deck; the origin is its bend.
    section_in=((-2.875, 0.0), (0.0, 0.0), (0.0, 1.5),
                (0.625 * math.sin(math.pi / 4), 1.5 - 0.625 * math.cos(math.pi / 4))),
    source="Residential Design Manual 5/2024 p. 9",
)
IMAGE_II_RIDGE_COVER = TrimProfile(
    "7 inch Ridge/Hip Cover", pvdf("52131XX"),
    # Apex at the crown; each 7 in slope leg ends in a 1 in hem folded back into the cover.
    section_in=((-7.0, -1.0), (-7.0, 0.0), (0.0, 0.0), (7.0, 0.0), (7.0, -1.0)),
    source="Residential Design Manual 5/2024 p. 8",
)
#: The vented ridge (PIM p. 20, Cobra vent detail): a 13 in step cover, 6-1/2 in legs at the
#: pitch with 1 in hems, over a Cobra vented closure. No manual prints its part number, so it
#: bills under its key, and the coverage check holds that one supplier question.
IMAGE_II_VENTED_STEP_RIDGE = TrimProfile(
    "13 inch Step Ridge/Hip Cover, Cobra vent",
    section_in=((-6.5, -1.0), (-6.5, 0.0), (0.0, 0.0), (6.5, 0.0), (6.5, -1.0)),
    source="Image II PIM p. 20, Vented Ridge (Cobra Vent) detail; leg length read off the "
           "drawing at its 2 in max deck slot",
)
#: The vent block under the crown. PIM p. 20 does not dimension it; read off the drawing at
#: the same scale, about 1-1/2 in. Its net free area is not printed (R806.2 stays UNKNOWN).
COBRA_VENT_IN = 1.5
IMAGE_II_Z_CLOSURE = TrimProfile(
    "Image II Z-Closure", pvdf("58603XX"),
    section_in=((-1.0, 0.0), (0.0, 0.0), (0.0, 1.0), (1.0, 1.0)),
    source="Residential Design Manual 5/2024 p. 12",
)
IMAGE_II_RESIDENTIAL_PEAK = TrimProfile(
    "Residential Peak", pvdf("52134XX"), source="Residential Design Manual 5/2024 p. 41"
)
IMAGE_II_FLAT_CLEAT = TrimProfile(
    "Flat Cleat", ((24, "varies", 122.0, "5806199"),), source="Residential Design Manual 5/2024"
)


def eave_deck_flange_in() -> float:
    """The 5 in deck flange of the Extended Eave: from its free end to the bend."""
    (x0, y0), (x1, y1) = IMAGE_II_EXTENDED_EAVE.section_in[1:3]
    return math.hypot(x1 - x0, y1 - y0)


def rake_deck_flange_in() -> float:
    """The 2-7/8 in leg of the Residential Rake Cleat that lies on the deck."""
    (x0, y0), (x1, y1) = IMAGE_II_RAKE_CLEAT.section_in[0:2]
    return math.hypot(x1 - x0, y1 - y0)
