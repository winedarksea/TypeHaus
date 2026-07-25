"""Named spacing/pitch/tolerance rules for the hardware take-off (no inline literals).

Every operational constant the hardware quantities depend on lives here as a field of a
frozen sub-config, so a house (or a reviewer) can see and override the rule that produced a
count instead of hunting for a magic number in the derivation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

IN_TO_M = 0.0254
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
    # Layer functions a fastened furring/batten layer can carry (roof battens resolve as an
    # air gap, wall furring as furring — the same screwed strip either way).
    fastened_layer_functions: frozenset = frozenset({"furring", "airgap"})
    # A strip is only *structurally* screwed when it is held off the framing by continuous
    # insulation; a rainscreen batten straight over sheathing takes ordinary siding nails.
    insulation_layer_functions: frozenset = frozenset({"insulation"})
    structure_layer_functions: frozenset = frozenset({"structure"})


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
        {"joist", "rafter", "rim", "landing", "stringer", "top_chord"})
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


@dataclass(frozen=True)
class HardwareTakeoffConfig:
    """The complete rule set behind :func:`typehaus.takeoff.hardware_takeoff`."""

    exterior_insulation_fasteners: ExteriorInsulationFastenerRules = field(
        default_factory=ExteriorInsulationFastenerRules)
    sill_plate_anchors: SillPlateAnchorRules = field(default_factory=SillPlateAnchorRules)
    wall_ties: WallTieRules = field(default_factory=WallTieRules)
    hanger_detection: HangerDetectionRules = field(default_factory=HangerDetectionRules)
    knee_braces: KneeBraceRules = field(default_factory=KneeBraceRules)
    # The construction-return take-off category that marks a wood sill plate on concrete.
    sill_plate_takeoff_category: str = "pt-sill-plate"


DEFAULT_HARDWARE_TAKEOFF_CONFIG = HardwareTakeoffConfig()
