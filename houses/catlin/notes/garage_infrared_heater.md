# Garage 1500 W infrared heater — 2026-11-06

The owner selected the **Dr Infrared Heater DR-238**, Home Depot 303985873, at **$110**.
Its black carbon radiant bar replaces the generic unit-heater box. The current
manufacturer manual (v250108) gives a 34.6x7.69x3.33in body. The shared
`infrared-heater` geometry draws the reflector, tube, guard, control end and paired
brackets, aimed 45 degrees down in a 34.6x14x8in installed envelope. The rear 6in is
an allowance for the supplied brackets, to be confirmed at installation.

`EQ-G-HEATER` keeps its factory cord and plugs directly into **ED-G-HEATER-RC**,
90in AFF beside the bar, on dedicated **20 A GFCI CKT-GAR-HEAT**. No hardwiring or
extension cord. The branch remains 1500 VA; the bare receptacle adds no appliance
load. Keep the cable behind the reflector. `RM-GARAGE` stays unconditioned.

The envelope is **96..104in AFF**, below a **122in ceiling**. This clears the
manual's 94.5in floor and 15.8in ceiling minimums. Leave 19.7in at adjacent walls
and 39.4in ahead of the radiant face, including people and combustible objects.
The workbench is more than 39.4in below the envelope. The manual excludes operation
where gasoline, paint or other flammable liquids are used or stored.

## Framer's layout

**BK-G-W-HEATER:** one **22.5in SPF 2x6**, fitted flush with the inside stud face,
fastened at both ends between `W-G-W` studs 007 and 008. Run: wall station
**168.75..191.25in** from the north start. Elevation **75.25..80.75in above the sill**
means **97.25..102.75in AFF**, because the slab is 22in below the wall datum.

The current manual's mounting diagram has a **10.8in gap between inner holes**,
with each outer hole another **1.1in** outboard. Centred on the heater at station
180in, the four holes are **173.5, 174.6, 185.4 and 186.5in**, all at **100in AFF**.
All four land on this block. Confirm the supplied template before drilling; use
wood fasteners appropriate to the brackets and backing rather than masonry plugs.

`advisory.wall_fixing_support` checks each equipment fixing against emitted wood
on the mounting face. Removing the block fails all four fixings.
`advisory.wall_backing_bearing` checks its ends. These checks establish geometry;
fastener capacity is not calculated.

Sources: [manufacturer product](https://drheaterusa.com/products/dr-238),
[current manufacturer manual](https://cdn.shopify.com/s/files/1/0496/6601/files/DR-238_User_Manual_v250108.pdf),
[owner's Home Depot selection](https://www.homedepot.com/p/303985873).
