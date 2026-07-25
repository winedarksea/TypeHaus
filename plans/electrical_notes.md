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
