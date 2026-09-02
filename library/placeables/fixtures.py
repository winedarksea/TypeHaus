"""Shared plumbing-fixture catalog.

Tags are unique across the merged catalogs, enforced by ``integrity.duplicate_catalog_tag``.

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
    ServicePort,
    ft,
    inch,
    m,
    pt,
)

REFERENCE = "Residential planning allowance; final fixture selection by owner."

# The code envelope is measured independently of the bowl: 15" from the water-closet
# centreline to each side and 24" clear in front.  Keeping this as a separate polygon means
# a product can use its actual manufactured footprint instead of pretending that the code
# envelope is the fixture's size.
#
# ** THE FRONT DIMENSION IS 24", NOT IRC P2705.1's 21", AND IN MINNESOTA THAT IS NOT A
# CHOICE. ** The chain: Minn. R. 1309.0010 subp. 3.D deletes
# IRC chapters 25-33 outright (P2904 is the only survivor), and Minn. R. 1309.0307 replaces
# R307.1 with one sentence — "Plumbing fixtures shall be installed in accordance with
# Minnesota Rules, chapter 4714". 4714.0050 adopts the 2018 UPC, and chapter 4714 contains
# no amendment to section 402 (its Chapter 4 parts are .0405 and up; there is no 4714.0402),
# so UPC 402.5 stands unamended: "No water closet ... shall be set closer than fifteen (15)
# inches from its center to any side wall or obstruction ... The clear space in front of any
# water closet or bidet shall be not less than twenty-four (24) inches." Anoka's and
# Farmington's residential bathroom handouts both print 15"/24" and cite 402.5. The 21"
# figure is IRC's, and the 21" *dwelling-unit exception* people cite for it is a Washington
# state amendment, not a Minnesota one.
#
# The side dimension is 15" in both codes and does not move. UPC's other number, 30", is
# centre-to-centre between two adjacent similar fixtures, NOT a compartment width — the 30"
# alcove this polygon draws is the 15"+15" restated, which is the same in either code.
#
# Cite as UPC 402.5, as adopted by Minn. R. 4714.0050. ``code_profile`` is what gates this
# zone: a house that sets no ``active_code_profile`` has it dropped in
# ``resolve/placeables.py::_resolved_clearance_zones`` and is graded against nothing.
WATER_CLOSET_SIDE_CLEARANCE = ft(1, 3)
WATER_CLOSET_FRONT_CLEARANCE = ft(2)
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
        source="UPC 402.5 (Minn. R. 4714.0050): 15 in from the centreline to any side "
               "wall or obstruction, 24 in clear in front of the water closet",
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
# rather than house-local ones.
#
# ** THE WASTE IS A 3" DROP THROUGH THE FLOOR *INSIDE THE WALL*, NOT A CLOSET FLANGE. **
# This is the whole reason the type carries ``ports``, and it is the thing a plan gets
# wrong. Three separate mistakes are all ruled out by the numbers below:
#
#   * **Size.** A residential in-wall carrier connects at 3" (Geberit Duofix calls out
#     "3" pipe (90 mm)" at the waste and 2" at the vent; TOTO DuoFit WT171M/WT172M is the
#     same Ø90 mm outlet). 3" is also the MN minimum — Minn. R. 4714.0702 Table 702.1 gives
#     a 1.6 gpf water closet a 3" minimum trap size at 3.0 DFU private — so a wall-hung WC
#     is a 3" branch, never a 1 1/2"/2" one and never a bare tee off the 4" building drain.
#     (The 4.375"/110 mm fittings in Geberit's table are for floor-mount BACK-OUTLET bowls,
#     a different product.) Cast-iron commercial carriers — Zurn Z1203-N, Smith 0210 —
#     ship 4" but catalogue a 3" variant (Z1203-NL3); they also want a 14" chase, which is
#     why they are not the residential detail.
#   * **Plan position.** The drop is on the BOWL'S OWN CENTRELINE but 1 3/4" behind the
#     front of the carrier frame (TOTO SS-01413/SS-01448 dimension it as "Drain Hole C/L:
#     1-3/4" from front of frame"), and the finished wall covering stands another 1/2"-2"
#     in front of the frame. That puts it ~2 1/4"-3 3/4" behind the finished wall face —
#     inside the stud bay, not under the china. ``_expected_drain_point``'s convention
#     branch (no WATER_HOT => drain under the footprint) is therefore WRONG for this type,
#     which is why an instance must author ``drain_position``; the waste port below is the
#     type's statement of where that point belongs relative to the bowl.
#   * **Elevation.** The bowl's trap is integral and sits above the floor, so there is no
#     floor trap and no closet bend at deck level: the stub turns down inside the frame and
#     the long-turn happens BELOW the deck, in the joist bay. A run whose first vertex is at
#     the fixture's own position and whose first invert is under the finished floor is
#     describing a floor-mounted WC, whatever type the fixture references.
#
# ``mount`` puts the china on the wall rather than the floor: 15" finished rim height, the
# standard (non-ADA) setting and the low end of the 15"-19" range every in-wall frame
# publishes — so the body spans 1 3/8" to 15" above the floor and nothing stands on it.
# The tank is not in ``height`` at all, because the tank is in the wall.
#
# Framing depth is a real constraint on specifying this type: a 2x4 (3 1/2") bay is the
# manufacturers' minimum and needs their 2x4 outlet kit, because 3" DWV is 3.5" OD and
# 90 mm HDPE is 3.54" — the pipe is as wide as the cavity. A 2x6 (5 1/2") bay is the
# comfortable detail and the only one that takes Geberit's LH/RH horizontal offset
# connectors. Grade the host wall against ``advisory.wet_wall_depth`` before using this.
#
# Sources: Geberit GNA7225 (Duofix 2x4, 111.798.00.1) and GNA7274 (optional waste fittings);
# TOTO SS-01413 (WT172M) / SS-01448 (WT171M); Zurn Specification Drainage Engineering Guide,
# carrier systems; Minn. R. 4714.0702 Table 702.1.
TOILET_WALL_HUNG = FixtureType(
    tag="FX-TOILET-WH", name="Wall-hung water closet (compact)",
    footprint=(inch(15), inch(19.3)), height=inch(13.625),
    plan_symbol="toilet-wall-hung",
    needs=frozenset({Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(_water_closet_required_clearance(inch(19.3)),),
    mount=Mount(kind=MountKind.WALL, elevation=inch(1.375)),
    # Geberit's Duofix element is 500 mm (19 11/16") wide across the frame's uprights, and
    # TOTO's DuoFit is within an eighth of it, so the clear bay between the flanking studs
    # is the real constraint on where this fixture can go — not the china's 15" footprint.
    # 19.75" rounds Geberit's 500 mm up to the nearest sixteenth. ``framing/carriers.py``
    # turns this into a stud keepout and frames the bay; nothing else in the catalog sets it.
    carrier_bay_width=inch(19.75),
    # Local product frame: the bowl faces -y (the clearance zone above is drawn that way),
    # so +y is into the wall and the back of the china is at +9.65" (half of 19.3"). The
    # waste and vent are both a further 2 1/4" back — 1/2" of gypsum plus the frame's own
    # 1 3/4" — which is 11.9" from the bowl centre.
    ports=(
        # z=0: the drop crosses the floor plane here. This is the point a ``drain_position``
        # override and any sleeve/joist-bay penetration must land on.
        ServicePort(tag="waste", service=Service.DRAIN,
                    position=(inch(0), inch(11.9), inch(0)), connection_size=inch(3),
                    notes="3\" (90 mm) vertical drop through the deck inside the carrier "
                          "frame; the long-turn to the branch is below the floor"),
        # The individual vent is a tapping ON the waste fitting, just above the bend — 2" NH
        # on a Zurn carrier, 2" NPTF on the Geberit cast-iron bend — so it rises in the same
        # bay the drop falls in, not in whatever chase the room happens to have.
        ServicePort(tag="vent", service=Service.VENT,
                    position=(inch(0), inch(11.9), inch(4)), connection_size=inch(2),
                    notes="2\" vent takeoff integral to the carrier's waste fitting"),
        # Behind the actuator plate, which is the only opening in the finished wall: Geberit
        # puts that opening 26 3/8" above the base of the frame, and the angle stop is
        # reached through it. Concealed but accessible, which is what UPC 402.4 is after.
        ServicePort(tag="cold", service=Service.WATER_COLD,
                    position=(inch(0), inch(11.9), inch(26.375)), connection_size=inch(0.5),
                    notes="1/2\" fill supply to the concealed tank, with its angle stop "
                          "reached through the actuator-plate opening"),
    ),
    source='TOTO RP compact wall-hung class, 15" x 19.3" china on a Geberit Duofix / TOTO '
           'DuoFit class in-wall carrier: 3" (90 mm) waste dropping through the deck '
           '1 3/4" behind the frame face, 2" vent takeoff at the fitting, 1/2" fill to the '
           'concealed tank, 15" finished rim height (frames adjust 15"-19"). Needs a '
           '3 1/2" bay as an absolute minimum and wants a 5 1/2" one.',
)
LAVATORY_COMPACT = FixtureType(
    tag="FX-LAV-COMPACT", name="Compact lavatory", footprint=(ft(1, 6), inch(14)),
    height=ft(2, 10), plan_symbol="lavatory",
    # VENT belongs here: a fixture that drains is vented, and leaving VENT off does not make
    # the vent unnecessary, only unchecked. `mep.trap_arm_length` walks DRAIN fixtures, so it
    # would ask for this lavatory's vent, while `mep.vent_reachability`, which walks VENT
    # fixtures, would skip it entirely without this flag.
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
    integral_vacuum_breaker=True,
    source="Woodford Model 19 self-draining frost-free wall faucet, 3/4\" NPT inlet, MHT "
           "outlet, integral anti-siphon vacuum breaker (ASSE 1052), barrel length chosen "
           "for the wall stack it passes (here 2x6 + 4\" continuous exterior insulation + "
           "rainscreen ~= 10\"). The breaker ships on the faucet body — do not schedule a "
           "second, screw-on one. The seat sits inside the conditioned envelope and the "
           "barrel pitches outward to drain; specify the PEX transition at the seat, a "
           "sleeve over the barrel, and the manufacturer's gasketed escutcheon over a "
           "foamed penetration.",
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
