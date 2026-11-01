"""Image II roof pieces (Metal Sales Residential Design Manual 5/2024, pp. 6-12).

``section_in`` runs from the piece's free end, in inches, x outboard of the bend (or the roof
edge) and y up, along the piece's weather face (the sheet lies to the path's right). The
Extended Eave is pitch-dependent, so the resolver builds it with ``extended_eave_section``;
the others are placed as drawn. Dimensions are checked by ``test_image_ii_roof_pieces``.
"""

import math

from typehaus.library.trim.profile import TrimProfile, pvdf

#: 24 ga base steel, the sheet every piece here is formed from (``SHEET_24_GA_M`` in resolve).
SHEET_24_GA_IN = 0.0239
#: The air left inside an open hem, so its two plies never share a face.
OPEN_HEM_GAP_IN = 1.0 / 16.0
#: The Extended Eave's legs in stretch-out order (RDM p. 11): 7/8 hem, the 5 in leg
#: (3-1/2 inboard of the face corner, 1-1/2 lip), the 1-1/2 return under the lip, the
#: 1-1/2 face, the 5/8 kick at 135 deg, its 1/2 open hem. Stretch-out 10 in.
EXTENDED_EAVE_LEGS_IN = (0.875, 5.0, 1.5, 1.5, 0.625, 0.5)
#: How far the pitched leg runs inboard of the face corner: the catalog reach. The bearing
#: on a deck is resolved from placed geometry (``resolve/roof_image_ii_eave.py``).
EXTENDED_EAVE_REACH_IN = 3.5


def hem_offset_in(sheet_in: float = SHEET_24_GA_IN, gap_in: float = OPEN_HEM_GAP_IN) -> float:
    """Centreline spacing of an open hem's two plies: each sheet plus the gap between them."""
    return 2.0 * sheet_in + gap_in


def extended_eave_section(slope: float, sheet_in: float = SHEET_24_GA_IN,
                          gap_in: float = OPEN_HEM_GAP_IN) -> tuple[tuple[float, float], ...]:
    """The Extended Eave at roof ``slope`` (rise/run), as legs and bends per RDM pp. 11, 31.

    Inches, x outboard and y up, origin at the corner where the face meets the pitched leg.
    The path is the piece's weather face: the sheet lies to its right, so the 7/8 hem and the
    lip's return sit under the leg and the drip hem inside the kick, each a real open hem.
    """
    hem, leg, ret, face, kick, drip = EXTENDED_EAVE_LEGS_IN
    angle = math.atan(abs(slope))
    down = (math.cos(angle), -math.sin(angle))     # down the pitch, outboard
    up = (math.sin(angle), math.cos(angle))        # off the pitched leg
    fold = hem_offset_in(sheet_in, gap_in)
    inboard = leg - ret

    def at(s: float, w: float) -> tuple[float, float]:
        return (s * down[0] + w * up[0], s * down[1] + w * up[1])

    kick_dir = (math.sin(math.pi / 4), -math.cos(math.pi / 4))
    tip = (kick * kick_dir[0], -face + kick * kick_dir[1])
    # The drip hem folds back inside the kick (to the sheet side, down and in).
    turn = (tip[0] - fold * math.sin(math.pi / 4), tip[1] - fold * math.cos(math.pi / 4))
    return (at(-inboard + hem, 0.0), at(-inboard, 0.0), at(-inboard, fold), at(ret, fold),
            at(ret, 0.0), (0.0, 0.0), (0.0, -face), tip, turn,
            (turn[0] - drip * kick_dir[0], turn[1] - drip * kick_dir[1]))


IMAGE_II_EXTENDED_EAVE = TrimProfile(
    "Image II Extended Eave",
    pvdf("52124XX"),
    # Drawn flat; the resolver builds it at the roof's pitch with ``extended_eave_section``.
    section_in=extended_eave_section(0.0),
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
    # the 5/8 in kick and the 1/2 in open hem folded back inside it.
    section_in=(
        (-1.0, 2.625), (0.0, 2.625), (0.0, 0.0),
        (0.625 * math.sin(math.pi / 4), -0.625 * math.cos(math.pi / 4)),
        ((0.625 - hem_offset_in()) * math.sin(math.pi / 4),
         -(0.625 + hem_offset_in()) * math.cos(math.pi / 4)),
        ((0.125 - hem_offset_in()) * math.sin(math.pi / 4),
         -(0.125 + hem_offset_in()) * math.cos(math.pi / 4))),
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
#: The vented peak (RDM 5/2024 p. 41) on a gable: the 7 in cover rides an Image II Profile
#: Vent Clip 6540000 (1 in, 3-1/8 in long; p. 13) over Profile Vent 6441899 on each slope,
#: where the closed ridge (p. 37) has a Z-closure. Two clips per panel, two #14 x 1-1/2 in
#: metalwood screws 8215100 per clip, one pop rivet 82409XX through the cover into each clip,
#: double-bead tape at both sides of every clip.
PROFILE_VENT_CLIP_LENGTH_IN = 3.125
PROFILE_VENT_CLIPS_PER_PANEL = 2
PROFILE_VENT_SCREWS_PER_CLIP = 2
#: The vent's low edge stands back of the cover's hem (SFS ProfileVent sheet 05/2024: "about
#: 1/2" to 1" up-slope from the ridge cap edge").
PROFILE_VENT_SETBACK_IN = 0.75
#: ProfileVent (Ventco; Metal Sales 6441899 is the 16 in Image II cut) net free area, SFS data
#: sheet 05/2024: "23.4 sq.in. per linear foot", "varies with thickness and profile", at 1.20
#: in nominal. Read as per foot of RIDGE (both strips), the conservative reading; the RDM
#: prints none.
PROFILE_VENT_NFA_IN2_PER_FT = 23.4
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


def eave_catalog_reach_in() -> float:
    """The Extended Eave's pitched leg inboard of its face corner (catalog, not bearing)."""
    return EXTENDED_EAVE_REACH_IN


def rake_deck_flange_in() -> float:
    """The 2-7/8 in leg of the Residential Rake Cleat that lies on the deck."""
    (x0, y0), (x1, y1) = IMAGE_II_RAKE_CLEAT.section_in[0:2]
    return math.hypot(x1 - x0, y1 - y0)
