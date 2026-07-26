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
