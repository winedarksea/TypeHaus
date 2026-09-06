"""Catlin appliance catalog — the named products, where the owner has chosen one.

NOT ``# haus: editable``: like ``fixture_types``/``lighting_types`` these are catalog type
definitions rather than placed instances, and ``ApplianceType.needs`` is a ``frozenset``,
which the editable dialect forbids. The movable instances that reference these tags live in
``plan/placeables.py`` and ``plan/fixtures.py`` (both editable, so UI drags round-trip).

``library.placeables.appliances`` stays what it is: a *planning allowance* catalog, whose
own header says "final appliance selection by owner." This file is that selection. The
generic types are still in the library and still right for a house that has not chosen; a
36"x34" box called "Refrigerator" is the correct model of an undecided refrigerator. It is
the wrong model of a bought one, because the two numbers that matter — the width the run is
cut to and the circuit the electrician pulls — are the product's, not the class's.

Every dimension below is off the manufacturer's own spec sheet, and every ``source`` carries
the model number and the electrical requirement so a substitution is a one-line reviewable
change (the idiom ``plan/mep_hvac.py`` already uses for the Rheem HPWH and the EG4 gear).

Each type also names its ``product_ref`` — brand and model number as structured data in
``plan/products.py``, which is what the inspector sidebar and the estimate read.

**Nominal vs actual, and why the footprints look odd.** A "30-inch range" is 29 7/8" wide
and a "24-inch dishwasher" is 23 3/4". The cabinet opening is the nominal number; the
appliance is the actual one. These footprints are the *appliance*, so the run's arithmetic
in ``plan/placeables.py`` keeps landing on cabinet faces rather than drifting by an eighth
per box.

The cold storage is Frigidaire rather than LG (owner) and the reason is the bay, not the
badge: LG's only all-freezer is a 23 7/16" column, which would have left 12 9/16" of hole
in a 72" run built for two 36" boxes. See the pair's own note below.

What is deliberately NOT here: ``APPL-HOOD-RECIRC`` and ``APPL-DISPOSAL``. LG builds no
standalone recirculating canopy hood for the US market (its ductless path is an
over-the-range microwave, which this kitchen has no cabinet for — see the 5'-6" canopy in
``plan/placeables.py``), and builds no food-waste disposer at all. Both stay generic
allowances, which is the honest state of an unmade decision.
"""

from __future__ import annotations

from typehaus.model import ApplianceType, Service, ServicePort, ft, inch

from library.placeables._zones import front_zone

# --- laundry ---------------------------------------------------------------------------
#
# One object, two machines — the reasoning is ``library.placeables.appliances``'s on
# ``APPL-WASHER-DRYER-STACKED``: a factory-stacked tower is one 74 3/8" body with one
# footprint, one clearance band and one set of anchors, not a washer with a dryer set on
# top of it. As a *product* the box shrinks from the allowance's 28"x40"x80" to the real
# 27"x32 3/4"x74 3/8".
#
# The generic box was 7 1/4" deeper than the WashTower actually is. That matters here and
# nowhere else in the house: ``plan/fixtures.py``'s note on FX-M-LAUNDRY says the move
# north was sized by this appliance's depth, leaving 8 3/4" to the door plane for the
# bifold track. The real unit leaves 16", so the move is more comfortable than it was
# authored to be, not less — no geometry moves on account of this retype.
#
# ``ductless=True`` is the whole reason this product was chosen: the dryer half is a heat
# pump that condenses its moisture down a drain instead of blowing it out a wall, so there
# is no duct, no envelope penetration and no makeup air. M1502.1 exempts exactly this, and
# ``code.M1502_dryer_exhaust`` reads the flag rather than the name.
LG_WASHTOWER = ApplianceType(
    tag="APPL-LG-WASHTOWER", name="LG WashTower WKHC252HBA (washer + heat-pump dryer)",
    product_ref="PROD-LG-WKHC252HBA",
    footprint=(inch(27), inch(32.75)), height=inch(74.375),
    plan_symbol="washer-dryer-stacked",
    ductless=True,
    quick_closing=True,  # the washer half's hot and cold fill solenoids — P2903.5
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN,
                     Service.POWER_120, Service.POWER_240}),
    # Two circuits, one appliance: LG's own spec sheet rates the washer at 120V/10A and the
    # dryer at 240V, and the install literature calls for a 30A 4-wire cord. The house is
    # already built that way (CKT-LAUNDRY 20A 1-pole and CKT-DRYER 30A 2-pole in
    # plan/circuits.py, ED-M-LAUNDRY-RC1 and ED-M-LAUNDRY-DR1 in plan/electrical.py, whose
    # note already named an LG heat-pump dryer as the intended machine). Port elevations
    # follow the tower: washer plug low, dryer plug at the stacking bracket.
    ports=(ServicePort(tag="power-washer", service=Service.POWER_120,
                       position=(ft(0), ft(0), ft(0))),
           ServicePort(tag="power-dryer", service=Service.POWER_240,
                       position=(ft(0), ft(0), inch(43))),
           ServicePort(tag="supply-hot", service=Service.WATER_HOT,
                       position=(ft(0), ft(0), inch(36))),
           ServicePort(tag="supply-cold", service=Service.WATER_COLD,
                       position=(ft(0), ft(0), inch(36))),
           # The washer's discharge and the dryer's condensate both leave at the standpipe
           # band. The condensate outlet is behind the stacking bracket and is plumbed to
           # the drain rather than emptied from the tank — PR-M-DRYER-COND, air-gapped over
           # FX-M-LAUNDRY-SINK's rim (plan/fixtures.py).
           ServicePort(tag="drain", service=Service.DRAIN,
                       position=(ft(0), ft(0), inch(36)))),
    # LG's door-open depth is 57 1/2" overall, so the leaf itself projects 24 3/4" past the
    # 32 3/4" body. 30" is that leaf plus the few inches a person needs to stand in it, and
    # it stays RECOMMENDED (front_zone's only policy) so a laundry *closet* — where the band
    # is the doorway you stand in — still builds.
    clearances=(front_zone(inch(27), inch(32.75), inch(30),
                           "front-loader door swing and loading"),),
    source=("LG WashTower WKHC252HBA / WKHC252HWA, US spec sheet read 2026-08-24: 27\" W x "
            "74 3/8\" H x 32 3/4\" D, 57 1/2\" deep with the door open, alcove cutout 29\" x "
            "75 3/8\" x 36 3/4\". Washer 5.0 cu ft (LG USA; LG Canada's sheet says 5.8 — 5.0 "
            "is the US figure), 120V/10A on a 15A branch. Dryer 7.8 cu ft ventless heat "
            "pump, 240V 4-wire, 30A cord per the install guide, condensate drain outlet "
            "behind the stacking bracket, no duct. Supply 20-120 psi both inlets. 1\" side "
            "clearance. 353 lb."),
)

# --- cooking ---------------------------------------------------------------------------
#
# Induction, and the house is built around that choice: no gas is piped anywhere, the hood
# over it recirculates because there are no combustion products to exhaust, and the ERV
# carries the cooking load. Retyping from the library's ``APPL-ELECTRIC-RANGE`` narrows an
# allowance that covered coil, radiant and induction alike to the one that was meant.
#
# The 40A minimum circuit is *below* CKT-RANGE's 50A 2-pole breaker (plan/circuits.py slot
# 1), which is the right direction: a 50A branch feeds a 40A appliance, and the 14-50R the
# range's cord lands in is the receptacle a 50A circuit takes. No electrical change.
LG_INDUCTION_RANGE = ApplianceType(
    tag="APPL-LG-INDUCTION-RANGE", name="LG LSIL6336FE 30\" induction slide-in range",
    product_ref="PROD-LG-LSIL6336FE",
    # 29 7/8" x 29 5/16" is the appliance; the cabinet cutout is 30" x 25". The body is
    # deeper than the cutout because a slide-in oversails the counter front by design —
    # which is why plan/placeables.py stands the range 3" proud of the 24" bases beside it.
    footprint=(inch(29.875), inch(29.3125)), height=inch(36.5),
    plan_symbol="range",
    needs=frozenset({Service.POWER_240}),
    ports=(ServicePort(tag="power", service=Service.POWER_240,
                       position=(ft(0), ft(0), ft(0))),),
    source=("LG LSIL6336FE InstaView induction slide-in, Pro Builder spec sheet read "
            "2026-08-24: 29 7/8\" W x 36 1/2\" H x 29 5/16\" D (26 7/8\" excluding the door, "
            "48 5/8\" with it open), cooking surface at 36\", cutout 30\" x 36\" x 25\". "
            "6.3 cu ft oven + 0.8 cu ft drawer; 4 induction elements + 1 radiant, 4.3 kW "
            "UltraHeat. 11.9 kW at 240V, minimum 40A circuit, 4-wire NEMA 14-50R, cord not "
            "included. 30\" minimum to unprotected cabinet above — the canopy hood over it "
            "hangs at 5'-6\", 30\" over the 36\" cooking surface. 187.4 lb. The LG STUDIO "
            "LSIS6338F is the same chassis in Studio trim and the same 40A/14-50R, but "
            "several retailers now show it discontinued."),
)

# --- cleaning --------------------------------------------------------------------------
#
# ``quick_closing`` survives the retype and has to: the fill solenoid is the reason
# PA-M-DW-WHA-HW exists on the kitchen hot branch (plan/mep_supply_devices.py), and
# ``mep.water_hammer_arrestor`` reads this flag, not the product name.
#
# Hot water only, like the allowance it replaces — LG's install manual takes a hot supply at
# 20-120 psi and there is no cold connection to make. So the arrestor count stays one.
LG_DISHWASHER = ApplianceType(
    tag="APPL-LG-DISHWASHER", name="LG LDTS5552S 24\" QuadWash dishwasher",
    product_ref="PROD-LG-LDTS5552S",
    footprint=(inch(23.75), inch(24.625)), height=inch(33.625),
    plan_symbol="dishwasher",
    needs=frozenset({Service.WATER_HOT, Service.DRAIN, Service.POWER_120}),
    quick_closing=True,  # solenoid fill valve — P2903.5
    ports=(ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(0))),
           ServicePort(tag="supply", service=Service.WATER_HOT, position=(ft(0), ft(0), ft(0))),
           ServicePort(tag="drain", service=Service.DRAIN, position=(ft(0), ft(0), ft(0)))),
    # 24" of door plus standing room, unchanged from the allowance: the leaf drops rather
    # than swinging, so the band is the open door's own reach across the aisle.
    clearances=(front_zone(inch(23.75), inch(24.625), ft(2), "dishwasher door swing"),),
    source=("LG LDTS5552S top-control QuadWash with TrueSteam and 3rd rack, LG USA listing "
            "and owner's manual read 2026-08-24: 23 3/4\" W x 24 5/8\" D x 33 5/8\" H "
            "(603 x 625 x 854 mm), 15 place settings, 46 dBA. 120V 60Hz on a dedicated 15A "
            "or 20A circuit (CKT-DISHWASHER is 20A 1-pole, plan/circuits.py slot 34). Hot "
            "supply 20-120 psi; standard drain with air gap."),
)

# --- cold storage ----------------------------------------------------------------------
#
# **Why this pair is not LG.** Everything else in this file is LG because the owner asked
# for LG. Cold storage is not, because LG does not build the shape this kitchen has. The
# west run's cold bay is 72" — two 36" boxes under two 36" over-cabinets — and LG's only
# all-freezer for the US market is the LROFC1104V, a 23 7/16" column. Dropping it in leaves
# 12 9/16" of hole in a finished run, and the alternative (LG's 24" fridge column + 24"
# freezer column as a 48" pair) throws away two feet of the bay. Frigidaire Professional's
# single-door pair is 32 7/8" each, 65 3/4" together, and fits the bay it was measured for.
#
# **Why not Bosch, which was the other candidate.** Bosch's US column line is exactly two
# models (a 30" refrigerator and an 18" freezer), and they are genuinely better on depth —
# 24 3/4" with the panel, essentially flush with a 24" cabinet, against Frigidaire's 27".
# Two things rule them out here and both are geometry rather than money. Their cutout is
# **84" tall**: the cold boxes in this run stand 72" with CASE-OVER-36 uppers above them at
# a 6'-0" mount, so an 84" column does not sit under an over-cabinet, it deletes it. And
# 30"+18" is a 48" pair, which is the LG problem again in a more expensive form. (They are
# also roughly twice the price, which is the least interesting of the three reasons.)
#
# **NO WATER IS CONNECTED TO EITHER UNIT, and that is a decision, not an omission**
# (owner: the sink already carries filtered water and the household does not use
# the dispenser). Both products ship plumbed-capable — the all-refrigerator has an internal
# dispenser and filter, the all-freezer a dual-bin automatic ice maker on a 1/4" line — and
# Frigidaire's Use & Care manual sanctions running both dry outright: switch the ice maker
# off at its green On/Off switch and disable the dispenser at the control display. So
# ``needs`` is POWER_120 alone on both, which is the truthful description of what this
# house connects, and neither unit appears in any `serves` list.
#
# The provision for changing that mind is already built: PR-M-CW-COLDSTORE-STUB runs a
# capped 1/2" line to PA-M-COLDSTORE-STUB behind this bay (plan/mep_supply.py). Connecting
# it later is a stop and a 1/4" line, not a demolished kitchen — and Frigidaire's
# TTFLTRICEKIT feeds the freezer's ice maker from the refrigerator's valve, so ONE line
# serves the pair. If that day comes, both types gain WATER_COLD and `quick_closing=True`
# (the ice maker's fill valve is exactly what P2903.5 is about) and the stub gains an
# arrestor. None of that is true today, so none of it is authored today.
#
# Dimensions are the cabinet, and the height is the one WITH the hinge cover (71 1/2" bare)
# because the hinge is what has to clear the over-cabinet above. Frigidaire does not publish
# depth-with-handle, depth-without-door, or width-at-90-degrees — flagged rather than
# guessed; the projection past the cabinet faces wants a tape on a floor sample.
_FRIGIDAIRE_SOURCE = (
    'Frigidaire Professional single-door column pair, manufacturer spec sheets rev 10/21 '
    'and the shared Use & Care manual, read 2026-08-24: 32 7/8" W x 27" D (with door) x '
    '71 1/2" H (72 1/2" to the top of the hinge), 58 1/4" deep with the door open 90 '
    'degrees, 18.9 cu ft each. Clearances 3/16" sides, 1" top and rear. Each unit requires '
    'its OWN dedicated 115V 60Hz 15A grounded duplex outlet — the manual is explicit that a '
    'side-by-side pair takes two. Recommended paired cutout 66 1/4" wide. Depth with '
    'handle, depth without door and width at 90 degrees are NOT published by Frigidaire.'
)

# The `install_parts` is not an accessory, it is a condition of standing the two cabinets
# against each other: TWINSPAIRKIT carries an anti-condensation heater for the shared side
# walls, without which the seam sweats. Billed as a part because it is an order, not
# geometry — the same idiom APPL-M-DISP's control loop uses in plan/placeables.py. The
# 75"/79" flush trim kits Frigidaire also sells are deliberately NOT ordered: they assume a
# built-in cutout, and this run puts 21" over-cabinets at 75" instead.
#
# ** 75" IS THE SPEC, NOT A PREFERENCE. ** 72" would put the over-cabinets 1/2" below the
# 72 1/2" hinge and 1 1/2" below the 1" top clearance this very source records. The mount is
# the manufacturer's minimum, and it lands on the 75" trim kit's own datum by coincidence.
FRIGIDAIRE_ALL_REFRIGERATOR = ApplianceType(
    tag="APPL-FRIG-PRO-ALLFRIDGE",
    name="Frigidaire Professional FPRU19F8WF 19 cu ft all-refrigerator column",
    product_ref="PROD-FRIGIDAIRE-FPRU19F8WF",
    footprint=(inch(32.875), inch(27)), height=inch(72.5),
    plan_symbol="refrigerator",
    needs=frozenset({Service.POWER_120}),
    ports=(ServicePort(tag="power", service=Service.POWER_120,
                       position=(ft(0), ft(0), ft(2))),),
    # 36" holds the 31 1/4" the leaf projects past the cabinet plus somewhere to stand while
    # it is open — the same band the allowance carried, and unchanged by the retype.
    clearances=(front_zone(inch(32.875), inch(27), ft(3), "refrigerator door swing"),),
    source=_FRIGIDAIRE_SOURCE + " This unit has a water dispenser and filter and NO ice "
                                "maker; it is installed with no water connected.",
)
FRIGIDAIRE_ALL_FREEZER = ApplianceType(
    tag="APPL-FRIG-PRO-ALLFREEZER",
    name="Frigidaire Professional FPFU19F8WF 19 cu ft all-freezer column",
    product_ref="PROD-FRIGIDAIRE-FPFU19F8WF",
    footprint=(inch(32.875), inch(27)), height=inch(72.5),
    plan_symbol="refrigerator",
    needs=frozenset({Service.POWER_120}),
    ports=(ServicePort(tag="power", service=Service.POWER_120,
                       position=(ft(0), ft(0), ft(2))),),
    clearances=(front_zone(inch(32.875), inch(27), ft(3), "freezer door swing"),),
    source=_FRIGIDAIRE_SOURCE + ' This unit has a factory dual-bin automatic ice maker '
                                '(1/4" line, 30-100 psi) which is switched OFF and left '
                                'unconnected; there is no manual ice tray option.',
)


# --- the guest studio's wet bar ---------------------------------------------------------
# ** THIS IS THE ONE APPLIANCE IN THE HOUSE THAT IS A CLASS, NOT A PRODUCT, AND IT IS
# DELIBERATE. ** Every other type in this file is a chosen model off its own spec sheet,
# with a `product_ref` a machine can follow. This one is not, because the catalog had no
# undercounter refrigerator at all — `library.placeables.appliances` carries a 36"x34"
# "Refrigerator" and nothing smaller — and the owner has chosen no bar fridge. A generic
# 24" box IS the correct model of an undecided one; inventing a model number would be the
# lie. Give it a `product_ref` when somebody buys something.
#
# It lives here rather than in an editable file for the reason this module's header gives:
# `ApplianceType.needs` is a `frozenset`, which the editable dialect forbids. The placed
# instance is in `plan/placeables.py`, which is editable, so a UI drag round-trips.
#
# 24" x 24" x 34" is the standard undercounter envelope — it fits a 24" cabinet opening under a
# 36" counter with the toe kick and the compressor clearance the class needs. Nothing in the
# shared catalog is under 6' tall, which is why this entry exists at all.
#
# POWER_120 only — no water, no drain, NO ICE MAKER LINE. That is the whole point of the entry:
# a bar fridge plumbed for ice is a second water line and a second drain in an attic, and the
# studio's plumbing budget is one stack. No water also means no `quick_closing`, so
# `mep.water_hammer_arrestor` does not fire on it.
#
# ** AND THERE IS NO COOKING APPLIANCE, WHICH IS THE POINT OF THE WHOLE WET BAR. ** Sink
# plus fridge is a bar; add a range or a cooktop and the studio becomes a second dwelling
# unit, and IRC R302.3's two-family separation lands on the floor and the centre wall.
# Do not add one here.
BAR_REFRIGERATOR = ApplianceType(
    tag="APPL-BAR-FRIDGE-24",
    name='24" undercounter beverage refrigerator (class allowance)',
    footprint=(inch(24), inch(24)), height=inch(34),
    plan_symbol="refrigerator",
    needs=frozenset({Service.POWER_120}),
    ports=(ServicePort(tag="power", service=Service.POWER_120,
                       position=(ft(0), ft(0), ft(1))),),
    source='Undercounter all-refrigerator, 24" nominal (24" x 24" x 34"), 120V/15A '
           "cord-and-plug, no water connection. CLASS ALLOWANCE: final appliance selection by "
           "owner, unlike every other type in this file.",
)


APPLIANCE_TYPES = (LG_WASHTOWER, LG_INDUCTION_RANGE, LG_DISHWASHER,
                   FRIGIDAIRE_ALL_REFRIGERATOR, FRIGIDAIRE_ALL_FREEZER,
                   BAR_REFRIGERATOR)
