200A service line (meter not built into panel)
	Use a 225A or higher rated panel
Conduit, make it easy to run new lines
240V for hot tub, 240V for sauna, 240V water heater, 240V range, 240V dryer, 240V car, 240 splits 2x, HRV/ERV 240V
2 EV chargers:
	1x NEMA 6-20 (240V, 20A)
	1x NEMA 14-50 (240V, 50A)

On the backup (just 120V might be cheaper)
	Smart Relays (Shelly Pro 4PM) and contractors
		Ideally send a shutdown command via HA, wait a little, then disconnect relay
		DIN Rail
			Also 24V supplies
			DIN Rail UPS (maybe separate 24V UPS for LED lights as backup light)
				Capacitors for 24V LED and POE maybe
	Kitchen Outlet 1
		Fridge (efficient) 200W
			Most efficient 2025:  Frigidaire - FPRU19F8W* Model Number Information
			1 Fully Fridge and 1 Fully Freezer is the same
		Freezer
		WiFi (energy efficient, POE
	Basement Outlet 1:
		HA, Router
	Basement and kitchen lighting 100W
	Water heater heat pump (500W compressor, 4000W backup)
		Stick to the Rheem 120V without "hybrid" boost, 120V versions seem to use less power
	Sump pump (1000W startup)
	Maybe one minisplit (the smallest)
		Current thinking is one minisplit pointing down upstairs hallway (larger unit) and a smaller unit in the basement (also smaller unit with very deep cold rating)

Solar Panels are going to be mounted using standing seam clamps (no penetrations) near the roof ridge, on both sides of the gable ridge.
First pass should model the panels. Just one row each side of the ridge for now, 440W panels at 69.4 × 44.6 × 1.2 in and report the total wattage installed.
Electrical for the panels runs out the house near where the radon vent comes out.

## Lighting Notes
Need a 'professional' lighting plan that clearly lists the lighting and also lays it out. Ideally would import cleanly into Revit/Sketchup.

### Initial Lighting Plan
Rim of room led strips
	Shadow gap ceiling (installed when drywall is installed)
		Make sure it is isolated (mounted to drywall side sheet, not framing) for sound isolation
		Living Room (both sides)
		Upstairs hallway
	Box in ceiling for AC/DC power supply
Panel lights
	Kitchen
	Fitness Room
	Workshop, Furnace
Recessed cans, Recessed lighting (replaceable bulbs, 4" housing, recessed baffle trim, black baffle)
	Living room section
	Hallways (main floor)
	Bathrooms (moisture/water tolerant)
	Most Bedrooms
	Closets
	Apparently more, smaller cans (3") is cool these days
	Example: ELCO Lighting EL49LDICA or EL39LDICA
Hanging Linear Tube lights in plant room
	https://www.superiorlighting.com/decorative-linear-led-tube-light-6-foot-multi-watt-selectable-25-40-50-watts-color-temperature-selectable-30k-35k-40k-black-finish-120-277v/
	Over plants by windows in plant room (ideally damp rated and growth spectrum optimized)
		Manually option: with T8 wiring harness, T8 bracket hanger, cable suspension kit, junction box, and ceiling canopy kit
		Have this "smart" so can be on a timer
Linear Wall Lamp
	Second master bedroom over bed (RM-S-SUITE)
Sconces
	Soft "up and down" sconces are traditional for the "theater" on a dimmer (TV Room)
	Spotlight (down) sconce in two studies to sides of windows away from window by a few feet (more privacy at night)
	RM-A-DEN, upper wall spotlight sconce for task lighting with switch on sconce
	Sconces along stairs to upper levels in bedrooms/study with attic access
Hanging Fixtures
	Chandelier over the stairway on 2nd floor
	Fancy light fixture over dining room table
Ceiling Fan Lights
	Ceiling fan light in exercise area
	Ceiling fan light in 2nd floor plant room
	Large ceiling fan (60") on porch ceiling
Mirror lights (all bathrooms)
	Oksana wants a large mirror with a glowing light ring in master bedroom
		Front lit (towards user) better, many are side lit only
		Check controls, make sure usable, one that remembers settings, and the status led isn't too bright
		Will require hardwiring or outlet behind the mirror
Railing Lights or Baseboard level lights
	Along basement stairs

## Heating / Ventilation (decided 2026-07-25)
All-electric. No gas service, no furnace — the gas furnace EQ-B-FURNACE is deleted from
plan/mep.py and there was never a GAS UtilityLine in plan/site.py to feed it.
	Heat + cool: the two minisplits (CKT-MINI-1 large upstairs, CKT-MINI-2 small deep-cold
		basement, the one on backup)
	Heat, supplemental (decided 2026-07-25): five separately controlled electric
		resistance loads, 4.7 kW connected in total. None of them is sized to carry a
		room — the minisplits do that, and their sizing is a separate pass.
		Three radiant floor zones, 120V mat at 12 W/sf on a 3" serpentine, each on its
		own 15A GFCI circuit with its own line-voltage stat:
			FH-M-BATH2    main bath, 41.5 sf, 498 W   CKT-FH-BATH2
			FH-M-DINING   under the dining table, 58.0 sf, 696 W   CKT-FH-DINING
			FH-S-ENSUITE  NW bathroom (the hall bath), 42.4 sf, 509 W   CKT-FH-ENSUITE
		GFCI at the breaker on all three: NEC 424.44(G) requires it for heating cable in
			a bathroom or kitchen floor, and mat manufacturers require Class A protection
			on every mat regardless, so the dining zone gets it too.
		Zone polygons are drawn 4" off every wall and around every fixture footprint —
			`advisory.floor_heat_fixture_keepout` fails the build otherwise, which is the
			right answer: no cable under a closet flange or a shower pan.
		Two 1,500 W / 120V units, 20A each and no GFCI (hard-wired equipment, and
			210.8(A) protects receptacles):
			EQ-M-FIREPLACE  linear electric fireplace, east wall at the living room's SE
				corner (the south wall has only 2'-1" of clear wall there)   CKT-FIREPLACE
			EQ-G-HEATER     garage bench heater, west wall at 6'-0"   CKT-GAR-HEAT
		20A rather than 15A on those two is not a preference: 1,500 W = 12.5A, and a
			continuous load is figured at 125% = 15.6A, which needs the 16A a 20A breaker
			allows. The mats are 4-6A and 15A is the honest breaker for them.
		RM-B-SAUNA has no floor heat. FH-B-SAUNA was deleted the same day — a heated
			floor in a room that runs at 190 F has nowhere to put its heat, and its stat
			had no honest place to read room air from.
	There is no "supply" *heat*. The DU-M-ERV-SUP / DU-M-ERV-RET trunks and their registers
		are the ERV's fresh-air supply and stale-air return, sized for ~197 cfm (ASHRAE
		62.2: 0.03 x 5,078 sf + 7.5 x (5 bedrooms + 1)), not a furnace CFM. Distribution is
		second storey only today — main storey, basement and attic have no ERV terminals.
	Watch the service: the NEC 220.82 estimate is ~224A against a 200A service. The five
		space heaters above cost it nothing — 220.82(C) *selects* the heating term rather
		than summing it, and five separately controlled resistance units at 40% (C)(5) =
		1.9 kVA lose to the two minisplits at 100% (C)(2) = 6.3 kVA. What drives the
		overage is the two EV circuits at 13.4 kVA continuous plus the sauna and the two
		water heaters. Load management (an EV EMS per 625.42, or interlocking the sauna)
		or a service bump is a real decision, not a rounding issue.
	Panel space: 35 circuits, 13 of them 2-pole = 48 spaces. Past a 42-space panel; the
		225A enclosure needs to be a 54-circuit one (or the spare 2-pole goes).
