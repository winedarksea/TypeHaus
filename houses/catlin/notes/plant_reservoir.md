---
title: "Plant-room reservoir: manual fill and two independently timed shelf-pot circuits"
applied_to:
  - room: RM-S-PLANT
  - appliance: APPL-S-PLANT-RESERVOIR
  - appliance: APPL-S-PLANT-IRRIGATION
  - appliance: APPL-S-PLANT-WIRED-LEAK
  - pipe_accessory: PA-S-PLANT-RESERVOIR-STOP
  - door: D-S-PLANT
  - electrical_device: ED-S-PLANT-RC6
tags: [plumbing, irrigation, plant-room]
source:
  - plan/plant_reservoir.py
  - plan/plant_reservoir_types.py
  - plan/plant_reservoir_hardware.py
  - plan/mep_supply_plant.py
  - plan/doorway_transitions.py
---

# Plant-room reservoir — manual-fill revision, 2026-11-11

Use a **manually filled ten-gallon reservoir**, two independently timed irrigation circuits,
and wired leak/low-water protection. Initial installation serves individual shelf pots:
twelve per circuit. Hardware target **$1,200**, leaving **$300 contingency** under the
**$1,500 ceiling**, before tax, shipping and labor. Dependable, individually replaceable
components take priority. This revision supersedes automatic fill and manual ARM/seal-in.

This is a basis of design with purchasing and commissioning holds. Supplier quotations,
WaterWatcher revision qualification and physical acceptance remain open. Failed qualification
blocks purchasing; no undocumented substitutions. Repository geometry does not prove
containment, electrical suitability or plant endurance.

## Water path and attended filling

```text
Separate house service: 1/2-inch PEX -> recessed manual stop, 1/4-inch compression outlet
  -> removable potable fill tube, secured with discharge ABOVE the delivered tank rim
  -> attended fill with lid removed -> measured nine-gallon mark
  -> CLOSE manual stop and DISCONNECT tube afterward

Tank -> two independent top-entry reinforced suction hoses and inlet strainers
  -> two SHURflo 8000-543-210 pumps -> separate 200-mesh filters / pressure test points
  -> separate distribution headers -> twelve XB05PC shelf-pot outlets per circuit
```

There is no permanent domestic-water requirement or supply port on the reservoir appliance.
The room stop remains a separate manual house service. Confirm the removable potable tube,
compression ferrule/insert, discharge restraint and required above-rim separation with the
plumber before use. Never submerge the domestic discharge or connect it to irrigation tubing.
No automatic-fill float, fabricated fill saddle, FloodStop kit or throttling valve remains.
The tank has no drain/overflow; keep every penetration above its rim.

Domestic `PR-M-CW-PLANT-STUB` still has an unresolved supply-sizing basis. Do not invent a
WSFU value or reclassify the reservoir as a lavatory to suppress the permit-sizing UNKNOWN.
Attended filling is outside the unattended spill calculation and needs its own supervised
procedure. Disconnecting the tube is what removes the domestic supply from that release.

## Automatic pump permission and wired floor cutoff

Electrician's functional schematic (final assembly/load qualification required):

```text
RC6 GFCI -> SINGLE rack cord -> protected equipment distribution
  +-- upstream of both cutoffs -> TR40VA001 control transformer, 120 -> 24 VAC
  +-- HydroCheck WaterWatcher input
        -> WaterWatcher switched output -> RIBU1C K1 COM / normally OPEN contact
          -> permitted distribution -> timer A -> GST120A12-R7B A -> fuse -> pump A
                                    -> timer B -> GST120A12-R7B B -> fuse -> pump B

24 VAC R -> Madison M8000-NO (CLOSED ON RISING WATER) -> RIBU1C 24 VAC coil -> C
```

The float switches only the relay coil (manufacturer lists 46 mA at 24 VAC); never motor
or mains current. Verify close-on-rise in the actual installed orientation with an ohmmeter.
An empty tank or disconnected float wire de-energizes K1 and stops BOTH pumps. Manual
refilling restores permission automatically. There is no ARM button, seal-in contact or
manual restart requirement after ordinary low water or a dry power outage. Timers retain
independent local schedules; verify clock, programs and output state through interruptions.
Do not bridge timer outputs or provide a pump outlet that bypasses either cutoff.

One **packaged wired WaterWatcher floor sensor** stops both irrigation circuits. Its controller
is represented on the rack; the complete package is counted once at the sensor appliance.
`AL-S-PLANT-LEAK` remains a separate notification-only Zigbee device. No HA, radio, cloud,
or battery power is needed for irrigation permission.

**WaterWatcher qualification hold:** the [product page](https://www.hydrocheckproducts.com/product-page/waterwatcher-leak-detector)
checked 2026-11-11 lists $89.99, 15 A / 1 HP and unplug/replug reset. Its linked
[instructions](https://686cd715-8403-4bba-8416-177bc3df692b.usrfiles.com/ugd/686cd7_14a2dd5576b646d489ffa6060344e95d.pdf)
specify 13.8 A / 3/4 HP and a Smart Button reset when dry. Establish the exact supplied
revision, acceptable humidity/noncondensing conditions, combined power-supply input/inrush
rating and dry/wet power-recovery behavior before ordering. Do not combine the most favorable
claims from different revisions. Do not credit persistent fault memory across power loss.
A cutoff reset by power interruption is acceptable; an ordinary dry outage must permit
automatic scheduled watering to resume. Verify wet restoration stops both pumps; dry-after-leak
behavior and reset procedure must be recorded for the supplied revision.

The [RIBU1C sheet](https://hosted.functionaldevices.com/downloads/datasheets/RIBU1C.pdf)
lists 10 A resistive contacts and 5–95% noncondensing humidity. Check actual electronic-load
inrush against BOTH cutoff/contact ratings; a resistive current rating alone does not qualify
two switch-mode supplies. Keep mains terminations, timers, supplies and control components
inside a protected dry equipment compartment with grounding, strain relief, segregation and
manufacturer-required protection. Ventilation/condensation, enclosure fit and temperature
must be qualified with the electrician. Only the rack cord enters RC6's closed in-use cover.
Equipment must remain individually removable.

## Water budget and irrigation settings

Shared inputs: `typehaus.model.plant_reservoir.RESERVOIR_WATER_BUDGET`.

| Quantity | Allowance |
|---|---:|
| Nominal tank / conservative complete release | 10 gal |
| Measured operating fill | 9 gal |
| Unusable below suction / low-water cutoff | 1 gal |
| Operating reserve retained after trial | 1 gal |
| Initial ten-day watering allowance | **7 gal** |
| Maximum average daily draw | **0.7 gal/day** |
| 24 plants, equal initial allocation | 110.4 mL/plant/day |
| Each zone: twelve 0.5 GPH emitters | 6 GPH |
| Initial daily run per zone | **210 seconds (3 min 30 sec)** |

Example: A at 06:00, B at 08:00 to separate starts and aid delivery measurement. Tune each
circuit for its plants, capping the total at 0.7 gal/day. Cap unused outlets. Start the
trial with thoroughly watered, drained pots and a measured reservoir volume after priming.
The seven-gallon allocation is an initial trial setting, not proof of ten-day endurance.

Calibrate nine-gallon fill and one-gallon cutoff with measured water, not the tank's exterior
taper or schematic heights. Set cutoff above suction air/vortexing. If usable volume is lower,
reduce supported demand rather than silently increasing tank capacity.

[Pentair's pump selection](https://www.pentair.com/en-us/flow/commercial-products/water-supply-pumps/spray-pumps/8000_series_diaphgram_pumps.html)
uses 35 psi internal bypass and 7 A maximum. Retain one 8.5 A supply per pump, and verify
starting current, pressure and bypass heating with the delivered equipment. Short daily
runs limit heating; never assume closed-zone bypass permits continuous running. Separate
inlet strainers and downstream 200-mesh filters protect the pumps and emitters.

XB05PC emitters require 15–50 psi. Check pressure at the highest/farthest outlet with all
twelve operating, and catch EVERY pot's delivery. The 75-inch shelf consumes about 2.7 psi
relative to a pump at 12 inches AFF before line/filter losses; open-flow pump output is
not delivered emitter pressure. Measure actual retained distribution volume and daily draw.

**Siphon rule:** every emitter outlet and hose end must remain ABOVE maximum tank water
level. Secure them; pump check valves do not establish anti-siphon protection. Distribution
lines can drain their finite contents after shutdown. Future floor pots, tray watering,
soil-responsive devices or orchid misting require their own hydraulic and spill review.

## Spill calculation and service layout

Unattended release after manual fill tube disconnection is **10 gal tank + 1.75 gal
retained distribution = 11.75 gal**. No automatic-refill flow or valve-closure delay is
included. The line allowance covers two full 50-ft 0.600-inch-ID headers (1.47 gal),
100 ft of 0.170-inch-ID outlet tube (0.118 gal), plus suction/filter bodies. Remeasure
installed volume if hose lengths, filter bodies or distribution design change.

The resolved room is approximately 137.8 SF. Subtract the full 18 x 18-inch tank envelope
and 36 x 12-inch rack; release depth is about **0.143 inches**, below the 0.25-inch design
allowance and modeled 0.38-inch doorway water-stop crest. Retain the existing doorway
threshold. Physical containment verification, rather than geometry alone, determines whether
it needs changing. Verify actual floor escape points, uneven areas, perimeter penetrations,
jamb returns, reducer ends and toe seal; representative spill paths must reach the selected
sensor and stop both pumps. A drawing does not establish watertightness.

Tank center (166, 17.75) inches, rotation 180; 18-inch handles fit beyond the wall finish
at approximately y=7.79 inches. Rack center (164, 37), 36 x 12, rotation 180; east edge
x=182 stays west of the door swing's x>=186 strip. Its rear edge y=31 leaves 4.25 inches
between rack and tank envelopes. One approximate 3 x 3-inch floor sensor at (166, 28.8)
occupies this gap; qualify the actual supplied probe and site low point before fixing it.
Keep the spill path clear and use sealed fixings at the humid liner.

Lid lifts separately at the nominal 17.13-inch rim, with six inches of lift below the
32-inch sill. The top-entry suction envelope is 18.25 inches; rack height is 24 inches.
Verify delivered tank height (catalog may say 17.32), removable lid, suction routing, float
support and individual equipment removal. Preserve spare rack mounting space and tank access
for future additions. Approximate envelopes do not establish pump hole patterns or enclosure fit.

[Section and distribution illustration](plant_reservoir_section.svg) shows manual filling
and two independently timed shelf-pot groups; gallon marks govern illustrative water heights.

## Product schedule, pricing and purchasing holds

[Itemized procurement ledger](plant_reservoir_procurement.csv) records every hardware row's
supplier (or proposed supplier), SKU (blank explicitly means unresolved), quantity, unit price,
price date, price basis, availability, source and purchasing status. Product identities and
`ProductPart` quantities are in `plan/plant_reservoir_types.py` and
`plan/plant_reservoir_hardware.py`; prices join through `prices.toml`. Tests reconcile all
ledger rows with takeoff quantities and prices. No $60 commodity package or $30 rack bundle
remains. Rack materials, enclosure, hoses, fittings, connector harnesses, fuses, cords,
terminals, strain relief and mounting hardware are individually counted.

| Core product | Qty | Unit USD |
|---|---:|---:|
| Rubbermaid FG261000GRAY / FG260900GRAY lid | 1 each | 30 / 15 |
| SHURflo 8000-543-210 | 2 | 117.99 |
| MEAN WELL GST120A12-R7B | 2 | 40 |
| Hydrofarm TM01715D | 2 | 22 |
| Rain Bird XB05PC | 24 | 1.30 |
| SHURflo 255-323 inlet strainer | 2 | 12 |
| Rain Bird RBY075MPTX 200-mesh filter | 2 | 19.52 |
| HydroCheck WaterWatcher complete wired package | 1 | 89.99 |
| Madison M8000-NO | 1 | 27 |
| Functional Devices RIBU1C / TR40VA001 | 1 each | 25 / 22.20 |
| Individually itemized small hardware / rack materials (35 ledger rows) | — | 363.20 subtotal |

**Provisional total: $1,026.61**, $173.39 below the $1,200 target and $473.39 below the
$1,500 ceiling. Reserve at least $300 as contingency; do not treat it as a hardware row.
Only WaterWatcher and M8000-NO prices/availability were checked on manufacturer pages
2026-11-11. Remaining prices are unconfirmed budget allowances, including carried estimates;
most commodity supplier SKUs are still open. Proposed suppliers are not confirmed orders.
This is complete itemized cost accounting, **not a procurement-qualified quote**. Close all
blank SKUs, supplier stock checks, actual delivered quantities and prices before purchasing.

**Thread-interface hold:** the 255-323 strainer has 1/2-inch female NPSM with a face/O-ring
seal; the pump has 3/8-inch female NPT. Specify an adapter with 3/8 male NPT at the pump
and 1/2 male NPSM with the correct mating seat at the strainer. Prove that seat/seal with
the supplier; do not screw a generic tapered nipple into the straight-thread face seal
and assume PTFE makes it compatible. These two adapters are separate ledger rows from the
two pump-outlet barbs. Downstream each 3/4 male NPT filter gets its own female NPT inlet
barb and female NPT outlet/header adapter. Pressure-rate tubing and fittings to at least
50 psi and verify exact OD/ID compatibility. The unresolved adapter SKU is a purchase block.

## Commissioning and acceptance

1. **Purchasing:** resolve supplied WaterWatcher revision and environmental/load ratings,
   all adapter seats/SKUs and supplier quotations within the target/ceiling. Obtain the pump
   I-18 drawing. Qualification failure blocks ordering rather than permitting a substitution.
2. **Manual fill/service:** plumber approves removable potable tube and above-rim discharge;
   demonstrate attended fill, stop closure, tube disconnection, lid removal and equipment
   access. Calibrate measured nine-gallon fill and low-water marks.
3. **Controls:** test low water, disconnected float wiring and permission return after
   manual refill. Introduce leaks from representative points; verify the ONE selected wired
   sensor stops BOTH pumps. Record drying-after-leak/reset behavior for this revision.
4. **Power:** test dry and wet power restoration, timer retention/output, supply cold starts,
   pin pairs, motor/transformer protection and mains separation. Dry recovery must resume
   ordinary scheduled watering automatically; no persistent fault memory is assumed.
5. **Hydraulics:** measure each pot's delivery, highest/farthest pressure, bypass heating,
   actual retained line volume, noise and loose-hose release. Demonstrate no siphoning with
   a full tank and the lowest permitted outlet. Label the permitted outlet height.
6. **Containment:** survey actual floor escape points and representative spill paths;
   test perimeter/door seals. Geometry tests alone cannot establish watertightness.
7. **Ten-day trial:** begin with thoroughly watered, drained pots and measured primed tank
   volume. Accept healthy plants without damaging wilt, no leaks or dry running, and the
   operating reserve retained. Some drying by day ten is acceptable; maximum soil moisture
   is not required. Record start/end volumes; reduce demand if the trial fails.

Additional primary sources: [Madison M8000-NO](https://www.madisonsensor.com/std-min-lls-pp-flt-pp-stm-normally-open),
[MEAN WELL supply](https://www.meanwell.com/Upload/PDF/gst120a/gst120a-spec.pdf),
[Hydrofarm timer](https://s3.amazonaws.com/hydrofarmpubdocs/tm01715d_instructions.pdf),
[Rain Bird emitters](https://www.rainbird.com/professionals/specifier/emission-devices-bubblers),
[Pentair strainer interfaces](https://www.pentair.com/en-us/flow/shurflo/shurflo-products/shurflo-rv-applications/accessories/strainers.html),
[Rubbermaid dimensions](https://rcp.structpim.com/media/20254/brute-spec-sheet.pdf).
