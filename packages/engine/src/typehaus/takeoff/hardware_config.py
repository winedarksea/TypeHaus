"""Named spacing/pitch/tolerance rules for the hardware take-off (no inline literals).

Every operational constant the hardware quantities depend on lives here as a field of a
frozen sub-config, so a house (or a reviewer) can see and override the rule that produced a
count instead of hunting for a magic number in the derivation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

FT_TO_M = 0.3048


@dataclass(frozen=True)
class ExteriorInsulationFastenerRules:
    """The screw grid holding furring/battens through continuous exterior insulation.

    Strips land on the framing under them, so the horizontal pitch is the framing o.c.;
    the vertical pitch is the fastener spacing *along* each strip. Walls and roofs share
    the grid — only the required screw length differs, because a roof carries far more
    exterior foam than a wall.
    """

    # Furring strips follow the stud/rafter o.c. they must land on.
    strip_spacing_in: float = 16.0
    # Fasteners along each strip.
    fastener_pitch_along_strip_in: float = 24.0
    # Minimum penetration into the structural member past the sheathing/foam sandwich.
    minimum_structural_embedment_in: float = 1.5
    # Layer functions a screwed-through-the-foam layer can carry: wall furring resolves as
    # furring, a vented roof batten as an air gap, and a nailbase top deck as sheathing —
    # the same structural screw through the same foam in all three cases. Which one of
    # several matches is THE screwed layer is not decided here — see
    # `fasteners.exterior_insulation_fastening`, which takes the outermost candidate whose
    # path back to the foam crosses only membranes. That is what keeps a roof's inboard ZIP
    # and a wall's inboard sheathing out of it, and stops a vent mat rolled over a nailbase
    # deck from stealing the screw the deck below it is actually held by.
    fastened_layer_functions: frozenset = frozenset({"furring", "airgap", "sheathing"})
    # A strip is only *structurally* screwed when it is held off the framing by continuous
    # insulation; a rainscreen batten straight over sheathing takes ordinary siding nails.
    insulation_layer_functions: frozenset = frozenset({"insulation"})
    structure_layer_functions: frozenset = frozenset({"structure"})


@dataclass(frozen=True)
class ExposedFastenerCladdingRules:
    """The screw schedule for a face-fastened (exposed-fastener) metal wall panel.

    A clipped or seamed panel has no schedule here at all: its fixings ride inside the $/SF
    cladding rate. Only a material carrying ``Material.exposed_fastener`` reaches these
    rules, and that flag is the double-billing guard.

    Two independent terms make the count. The FIELD grid is the panel screwed down onto its
    supports — one screw in each flat between major ribs, at every support crossing. The
    SIDELAP is a separate line of stitch screws down each panel-to-panel joint, which the
    field grid cannot see because the joint is not a support.
    """

    # PBR major ribs at 12 in o.c.; the screws land in the flats between them, so the rib
    # pitch is also the horizontal screw pitch.
    rib_pitch_in: float = 12.0
    # The support crossing — for this house the horizontal girt course.
    support_pitch_in: float = 24.0
    # One panel's net coverage, which is the horizontal spacing of the sidelap joints.
    panel_coverage_in: float = 36.0
    # Stitch screws down a sidelap, between the supports.
    sidelap_stitch_pitch_in: float = 24.0
    # Panel + support embedment sets the screw length. The screw is meant to take the full
    # thickness of the nailer it lands in, not to stop part-way through it.
    panel_thickness_in: float = 0.02
    support_embedment_in: float = 1.4


@dataclass(frozen=True)
class SillPlateAnchorRules:
    """Anchorage of a wood sill plate to the concrete/ICF wall under it."""

    # MASA mudsill anchors run "roughly every 4 feet" along the plate.
    mudsill_anchor_pitch_ft: float = 4.0
    # IRC R403.1.6 — no plate piece is anchored by fewer than two anchors.
    minimum_anchors_per_run: int = 2
    # Embedded strap holdowns land at the ends of a sill run (shared ends are one holdown,
    # so the derivation counts *distinct* run endpoints, not runs x 2).
    holdowns_per_run_end: int = 1
    # Two run ends closer than this in plan are the same corner/butt joint.
    coincident_end_tolerance_in: float = 6.0


@dataclass(frozen=True)
class WallTieRules:
    """Uplift/continuity hardware in framed exterior walls."""

    # Member categories that run stud-to-plate and therefore take a tie.
    tied_stud_categories: frozenset = frozenset({"stud", "king", "corner"})
    # One tie per stud at the top plate; the bottom of the stud is developed through the
    # plate by the sill anchorage above, so it is not double-counted here.
    ties_per_stud: int = 1
    # Coil strap laps this far onto the wall above and below the floor band it crosses.
    coil_strap_lap_in: float = 16.0
    # Coiled strapping is bought by the coil, not the piece.
    coil_strap_coil_length_ft: float = 150.0
    # Junction kinds that read as a building corner for cross-floor strapping.
    corner_junction_kinds: frozenset = frozenset({"l"})
    # Strapping along the RUN between those corners. Corners alone gave catlin eight straps
    # for a three-storey house: two per 36 ft facade, with the middle thirty-two feet holding
    # the storey above it by nails through a rim board. Matched to the mudsill pitch on
    # purpose, so anchors, tie plates and straps share one 4 ft rhythm on the drawings.
    wall_strap_pitch_ft: float = 4.0
    minimum_straps_per_wall: int = 1


@dataclass(frozen=True)
class HangerDetectionRules:
    """How a hung (as opposed to bearing) framing connection is recognised.

    The condition is geometric — an end of a framed member lands *inside the depth* of a
    carrying beam rather than on top of it — so a hanger is billed from the resolved
    framing, never from a member's name.
    """

    # Members that carry other members in their depth.
    carrier_member_categories: frozenset = frozenset({"ridge_beam", "beam", "girder"})
    # Resolved solid categories that are also carriers (standalone beams, not framed).
    carrier_solid_categories: frozenset = frozenset({"beam"})
    # Members that can hang off a carrier.
    hangable_member_categories: frozenset = frozenset(
        {"joist", "rafter", "rim", "landing", "landing_framing", "stringer", "top_chord"})
    # A hung member's cut end stops short of the carrier centreline by about half the
    # carrier width; this bounds that gap (a 3-ply LVL is ~2.6" of it).
    end_gap_tolerance_in: float = 6.0
    # A member whose underside sits within this of the carrier top is *bearing on* it.
    bearing_seat_tolerance_in: float = 0.5


@dataclass(frozen=True)
class KneeBraceRules:
    """Knee braces are authored one element per *physical* brace, and billed the same way.

    This was a matched pair per joint, on the reasoning that a braced post takes one brace
    each side. That only holds where the beam continues past its post: at a beam *end* — every
    pillar of the balcony, and the common case for a deck — a single brace is all that fits in
    the beam's plane, and a post braced in two directions is two braces against two different
    members. Both are geometry the model already carries, so the take-off counts records
    rather than inferring a multiplier the plan cannot see.
    """

    # One connector per modeled brace. Raise it only for a hardware family that takes more
    # than one piece per brace.
    braces_per_location: int = 1
    # A 2x diagonal is through-bolted at each end — one 1/2" bolt per end. A second bolt per
    # end would split the 2x rather than strengthen the joint, so this is 2, not 4.
    bolts_per_brace: int = 2


@dataclass(frozen=True)
class UpliftTieRules:
    """The bearing/post hardware that makes the uplift load path continuous.

    Its sibling ``HangerDetectionRules`` recognises a *hung* end; these recognise the ends
    that **bear**, which is every other end in the house and none of the same ones.
    """

    # A rafter roof seats on its rafters. A truss roof seats on its HEELS: a truss's top
    # chord runs on past the plate to the overhang and crosses it more than a foot up, so a
    # rule that tied top chords would tie the wrong member at the wrong elevation.
    tied_roof_categories: frozenset = frozenset({"rafter", "truss_heel"})
    # Floors tie the joist only. A rim closes the joist ends and a trimmer frames an
    # opening; neither lands on a bearing line of its own.
    tied_floor_categories: frozenset = frozenset({"joist"})
    # One tie per bearing joint. Two joists lapping over an interior bearing wall are one
    # joint: the lap is nailed and the tie holds the pair to the plate. Raise this to two
    # for a schedule that ties each member of a lap separately.
    ties_per_bearing: int = 1
    # How far above a support's top face a member's underside may sit and still be bearing
    # ON it. It has to admit two real conditions and reject a third: a birdsmouthed I-joist
    # rafter's uncut underside stands ~3/4" proud of the plate, and a joist landing on a
    # foundation wall sits a 1-1/2" sill plate above the concrete the wall solid stops at.
    # A HUNG member's underside is ~11-7/8" *below* its carrier's top, and the test is
    # one-sided, so no tolerance in this range can confuse the two.
    bearing_seat_tolerance_in: float = 3.0
    # Plan allowance where a support has no width of its own to measure (a beam solid).
    # A wall uses half its own thickness instead, which is the real landing area.
    bearing_plan_tolerance_in: float = 8.0
    # Two member ends closer than this in plan are the same bearing joint.
    coincident_bearing_tolerance_in: float = 6.0
    # One strap per beam end that lands on a post — not the matched pair. See
    # ``uplift.post_beam_strap_rows`` for why, and ``KneeBraceRules`` for the same lesson.
    straps_per_post_beam_joint: int = 1
    # Lateral tie plates along a bottom plate standing on a floor band.
    tie_plate_pitch_ft: float = 4.0
    minimum_tie_plates_per_wall: int = 2
    # Below this height a ``Post`` is a squash block, not a column: a short piece filling a
    # joist bay to carry a point reaction down to the concrete. It bears and that is all it
    # does, so it takes no base and no uplift connector. 2'-0" is DCA6-2015 p.10's own
    # threshold — the height above which a deck post needs bracing, i.e. where the industry
    # already says a stick starts behaving like a column. catlin's case is P-M-STRLAND-SE, a
    # 13.4" block under the stair landing's third corner (plan/storeys/main.py).
    blocking_max_height_ft: float = 2.0


@dataclass(frozen=True)
class HardwareTakeoffConfig:
    """The complete rule set behind :func:`typehaus.takeoff.hardware_takeoff`."""

    exterior_insulation_fasteners: ExteriorInsulationFastenerRules = field(
        default_factory=ExteriorInsulationFastenerRules)
    exposed_fastener_cladding: ExposedFastenerCladdingRules = field(
        default_factory=ExposedFastenerCladdingRules)
    sill_plate_anchors: SillPlateAnchorRules = field(default_factory=SillPlateAnchorRules)
    wall_ties: WallTieRules = field(default_factory=WallTieRules)
    hanger_detection: HangerDetectionRules = field(default_factory=HangerDetectionRules)
    knee_braces: KneeBraceRules = field(default_factory=KneeBraceRules)
    uplift: UpliftTieRules = field(default_factory=UpliftTieRules)
    # The construction-return take-off category that marks a wood sill plate on concrete.
    sill_plate_takeoff_category: str = "pt-sill-plate"


DEFAULT_HARDWARE_TAKEOFF_CONFIG = HardwareTakeoffConfig()
