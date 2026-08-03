"""Shared plumbing-fixture catalog.

Tags are unique across the merged catalogs — ``integrity.duplicate_catalog_tag`` now
enforces what this docstring used to only assert.

A fixture's ``height`` is its **overall** height including the spout, because the generated
symbol keeps every part inside the declared box. That is why a lavatory is 40" and not 36" —
the deck plane lands where the counter is, and the faucet occupies the band above it.
"""

from __future__ import annotations

from library.placeables._zones import front_zone
from typehaus.model import (
    ClearancePolicy,
    ClearanceZone,
    FixtureType,
    Footprint2D,
    Mount,
    MountKind,
    Service,
    ft,
    inch,
    m,
    pt,
)

REFERENCE = "Residential planning allowance; final fixture selection by owner."

# IRC P2705.1's minimum is measured independently of the bowl: 15" from the
# water-closet centreline to each side and 21" clear in front.  Keeping this as
# a separate polygon means a product can use its actual manufactured footprint
# instead of pretending that the code envelope is the fixture's size.
WATER_CLOSET_SIDE_CLEARANCE = ft(1, 3)
WATER_CLOSET_FRONT_CLEARANCE = ft(1, 9)
WATER_CLOSET_CODE_PROFILE = "MN/IRC"


def _water_closet_required_clearance(depth) -> ClearanceZone:
    """Return the MN/IRC code envelope around a bowl facing local ``-y``."""
    half_depth = depth.meters / 2
    half_width = WATER_CLOSET_SIDE_CLEARANCE.meters
    front = half_depth + WATER_CLOSET_FRONT_CLEARANCE.meters
    return ClearanceZone(
        footprint=Footprint2D(points=(
            pt(m(-half_width), m(-front)), pt(m(half_width), m(-front)),
            pt(m(half_width), m(half_depth)), pt(m(-half_width), m(half_depth)),
        )),
        purpose="water-closet clearance", policy=ClearancePolicy.REQUIRED,
        source="MN/IRC: 30 in wide clearance and 21 in clear in front of water closet",
        code_profile=WATER_CLOSET_CODE_PROFILE,
    )

TOILET = FixtureType(
    tag="FX-TOILET-STD", name="Water closet", footprint=(ft(1, 8), ft(2, 4)), height=ft(2, 6),
    plan_symbol="toilet", source=REFERENCE,
    needs=frozenset({Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(_water_closet_required_clearance(ft(2, 4)),),
)
LAVATORY = FixtureType(
    tag="FX-LAV-24", name="Lavatory", footprint=(ft(2), ft(1, 8)), height=ft(3, 4),
    plan_symbol="lavatory", source=REFERENCE,
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
)
VANITY = FixtureType(
    tag="FX-VANITY-36", name="Vanity with sink", footprint=(ft(3), ft(1, 9)), height=ft(3, 6),
    plan_symbol="vanity", source=REFERENCE,
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(front_zone(ft(3), ft(1, 9), ft(1, 9), "lavatory front clearance"),),
)
TUB = FixtureType(
    tag="FX-TUB-60", name="Alcove bathtub", footprint=(ft(5), ft(2, 6)), height=ft(1, 8),
    plan_symbol="tub", source=REFERENCE,
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
)
# A tub-shower is one fixture, not a tub with a shower placed on top of it: the same 60x30
# alcove, but the type's height is the surround (7', matching SHOWER) rather than the tub
# rim, because that is what has to clear a sloped ceiling and what the ``tub-shower`` symbol
# carries its head and valve on.
TUB_SHOWER = FixtureType(
    tag="FX-TUBSHOWER-60", name="Alcove tub-shower", footprint=(ft(5), ft(2, 6)), height=ft(7),
    plan_symbol="tub-shower", source=REFERENCE,
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
)
SHOWER = FixtureType(
    tag="FX-SHOWER-36", name="Shower", footprint=(ft(3), ft(3)), height=ft(7),
    plan_symbol="shower", source=REFERENCE,
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
)
# A drop-in sink's bowls hang below its deck, so the mount elevation puts that deck at the
# standard 36" counter height rather than leaving the fixture sitting on the floor. The
# ``kitchen-sink`` symbol puts its deck at half the type's height — 9" of bowl below, 9" of
# gooseneck above — so 36" - 9" = 27" is the mount that lands the rim on the countertop.
KITCHEN_SINK = FixtureType(
    tag="FX-KITCHEN-SINK-33", name="Double-bowl kitchen sink", footprint=(ft(2, 9), ft(1, 10)),
    height=ft(1, 6), plan_symbol="kitchen-sink", source=REFERENCE,
    mount=Mount(kind=MountKind.WALL, elevation=inch(27)),
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
)

# A floor drain is a fixture in the schedule's sense — it traps, it drains, it vents, it has
# to be located — but it is not a *served* fixture: nothing supplies it, so ``needs`` carries
# neither WATER_COLD nor WATER_HOT and the supply checks correctly leave it alone (the same
# asymmetry FX-HYDRANT-Y34SS has in the other direction). Footprint is the strainer flange a
# plan can draw; ``height`` is only how far that flange stands above the finish floor, because
# everything else about the fixture is below it and is PipeRun geometry rather than massing.
#
# No trap primer is declared: this type exists for wet-room floors that see water in normal
# use, where the trap seal is maintained by use. A floor drain in a room that stays dry for
# months (a mechanical room) wants a primer line, which would be a different type.
FLOOR_DRAIN = FixtureType(
    tag="FX-FLOOR-DRAIN", name="Floor drain", footprint=(inch(6), inch(6)), height=inch(0.5),
    plan_symbol="floor-drain",
    needs=frozenset({Service.DRAIN, Service.VENT}),
    source='6" square adjustable strainer over a 2" cast body with an integral trap; final '
           "selection by owner. Set the strainer flush with the finish floor at the low "
           "point of the slope, and coordinate the flange with the waterproofing membrane's "
           "clamping ring.",
)

# --- compact bathroom class ---------------------------------------------------------
# A powder room too small for the standard pair is not a catlin problem: a wall-hung WC on
# an in-wall carrier plus an 18" lavatory is the standard answer, so both are shared types
# rather than house-local ones. The carrier frame is why an instance authors its
# ``drain_position`` on the wall line rather than under the bowl.
TOILET_WALL_HUNG = FixtureType(
    tag="FX-TOILET-WH", name="Wall-hung water closet (compact)",
    footprint=(inch(15), inch(19.3)), height=inch(21),
    plan_symbol="toilet", needs=frozenset({Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(_water_closet_required_clearance(inch(19.3)),),
    source='TOTO RP compact wall-hung class, 15" x 19.3", on an in-wall carrier.',
)
LAVATORY_COMPACT = FixtureType(
    tag="FX-LAV-COMPACT", name="Compact lavatory", footprint=(ft(1, 6), inch(14)),
    height=ft(2, 10), plan_symbol="lavatory",
    # VENT added 2026-07-30: it was missing while its sibling FX-TOILET-WH above declared it,
    # which is the same omission the library dedupe found on the other lavatory types — a
    # fixture that drains is vented, and leaving VENT off does not make the vent unnecessary,
    # only unchecked. `mep.trap_arm_length` is what surfaced it: that check walks DRAIN
    # fixtures, so it asked for this lavatory's vent while `mep.vent_reachability`, which
    # walks VENT fixtures, was skipping it entirely.
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    source='Compact powder-room lavatory, 18" x 14"; final fixture selection by owner.',
)
# The point of this type is what is *not* in ``needs``: only WATER_COLD. A frost-free
# hydrant drains through its own weep at the buried shutoff, not into the sanitary system,
# so the sleeve check correctly declines to demand a drain sleeve for it. Footprint is the
# escutcheon (what a plan can draw), height the handle above the slab.
WALL_HYDRANT = FixtureType(
    tag="FX-HYDRANT-Y34SS", name='Frost-free wall hydrant, 3/4" stainless',
    footprint=(inch(6), inch(6)), height=ft(2, 6), plan_symbol="hydrant",
    needs=frozenset({Service.WATER_COLD}),
    source='Y34SS-class frost-free wall hydrant, 3/4" stainless, 6\' bury. Specify the '
           "manufacturer's supplemental epoxy coating over the buried barrel where the "
           "floor runs salt slush (the standard finish is not rated for chloride "
           "immersion), and a screw-on hose-bib vacuum breaker on the outlet — required "
           "backflow protection for a hose connection.",
)
# The other way to make a hydrant frost-free, and the one a wall in a heated building
# allows: a Woodford Model 19. ``WALL_HYDRANT`` above is a *yard* hydrant: its seat is 6'
# down, below the frost line, and the barrel drains to it. This one's seat is at the inboard
# end of the barrel,
# inside the conditioned envelope, and the barrel pitches outward so it drains itself the
# moment the handle closes. There is no bury depth to specify because there is no bury —
# which is why ``mep.hydrant_freeze_depth`` exempts these and
# ``mep.exterior_hydrant_protection`` grades them on the penetration instead.
#
# What that trades away is the wall it goes through. A metal tube from outside air to inside
# air is a thermal bridge, so the installation is as much of the product as the hydrant is:
# transition to PEX at the seat rather than continuing in metal, sleeve the barrel, and seal
# the hole with a gasket, a bracket and closed-cell foam. Those parts ride the
# ``PipeAccessory(PENETRATION_SEAL)`` at each hydrant, not this type — the same hydrant
# through a different wall takes a different kit.
#
# ``mount`` is WALL at 24": the handle stands two feet over whatever deck the hydrant serves,
# which is the height you can get a hose fitting onto without kneeling.
WALL_HYDRANT_SELF_DRAINING = FixtureType(
    tag="FX-HYDRANT-SD34", name='Self-draining frost-free wall hydrant, 3/4", anti-siphon',
    footprint=(inch(6), inch(6)), height=inch(8), plan_symbol="hydrant",
    needs=frozenset({Service.WATER_COLD}),
    mount=Mount(kind=MountKind.WALL, elevation=inch(24)),
    source="Woodford Model 19 self-draining frost-free wall faucet, 3/4\" NPT inlet, MHT "
           "outlet, integral anti-siphon vacuum breaker, barrel length chosen for the wall "
           "stack it passes (here 2x6 + 4\" continuous exterior insulation + rainscreen "
           "~= 10\"). The seat sits inside the conditioned envelope and the barrel pitches "
           "outward to drain; specify the PEX transition at the seat, a sleeve over the "
           "barrel, and the manufacturer's gasketed escutcheon over a foamed penetration.",
)

# --- laundry ------------------------------------------------------------------------
# The freestanding utility tub: a deep single basin in its own cabinet, standing on the floor
# rather than dropped into a counter, which is why it is a fixture with a plinth and not a
# sink plus a ``sink-base``.
#
# ``height`` is 43" and the cabinet is 34". That is not a contradiction, it is this module's
# stated convention (see the docstring): the declared box has to contain the spout, and a
# laundry faucet is a tall gooseneck standing 9" over the rim so a bucket fits under it. The
# ``laundry-sink`` symbol puts its deck at 34/43 of the declared height, so the rim lands at
# the cabinet's real 34" and the faucet occupies the band above.
#
# Its ``DRAIN``/``VENT`` pair is what lets it serve as an indirect-waste receptor: an air-gapped
# condensate or appliance discharge wants a *trapped* receptor that sees water in normal use,
# which a laundry tub is and a finished-room lavatory is not.
LAUNDRY_SINK = FixtureType(
    tag="FX-LAUNDRY-SINK-24", name="Laundry utility sink with cabinet",
    footprint=(inch(24), inch(21)), height=inch(43), plan_symbol="laundry-sink",
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    source='Glacier Bay QL033Y class: 24" x 21" x 34" stainless laundry tub in a white '
           'cabinet, with faucet. The 43" declared height is the box including the '
           "gooseneck; the rim is at 34\". Final fixture selection by owner.",
)

STARTER_FIXTURE_TYPES = (TOILET, LAVATORY, VANITY, TUB, TUB_SHOWER, SHOWER, KITCHEN_SINK,
                         FLOOR_DRAIN, TOILET_WALL_HUNG, LAVATORY_COMPACT, WALL_HYDRANT,
                         WALL_HYDRANT_SELF_DRAINING, LAUNDRY_SINK)
