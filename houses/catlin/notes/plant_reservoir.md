---
title: "Plant-room reservoir: finite vacation reserve and independent wired leak shutdown"
applied_to:
  - room: RM-S-PLANT
  - appliance: APPL-S-PLANT-RESERVOIR
  - appliance: APPL-S-PLANT-IRRIGATION
  - appliance: APPL-S-PLANT-WIRED-LEAK
  - appliance: APPL-S-PLANT-FILL-VALVE
  - pipe_accessory: PA-S-PLANT-RESERVOIR-STOP
  - door: D-S-PLANT
  - electrical_device: ED-S-PLANT-RC6
tags: [plumbing, backflow, irrigation, plant-room]
source:
  - plan/plant_reservoir.py
  - plan/plant_reservoir_types.py
  - plan/mep_supply_plant.py
  - plan/doorway_transitions.py
---

# Plant-room reservoir — revised owner requirements, 2026-11-10

Approximately 10 US gallons, no drain, automatic refill for everyday use and **ten days
with the manual supply stop CLOSED** on vacation. Two independently timed groups support
up to twelve small/medium pots each. Actual plant demand, not pot count alone, establishes
endurance. Hardware purchasing ceiling: **$1,000 before tax, shipping and house labour**.
The earlier 2026-11-03 “no automatic shutoff” decision is superseded for this installation.

This is a coordinated **basis of design**, not a commissioned system. The geometry and
BOM are implemented; the qualification holds below must close before fabrication/use.
Do not interpret a passing geometry test as potable approval or proof of flood protection.

## Water and control paths

```text
Existing 1/2-inch PEX / recessed manual stop, 1/4-inch compression outlet
  -> FloodStop FS14C motorized fill valve DIRECTLY ON THE STOP, arrow toward tank
  -> John Guest throttling valve, short rigid connection immediately after electric valve
  -> potable 1/4-inch flexible fill tube
  -> Kerick MA252 mechanical float on an independent stainless saddle
  -> exposed discharge opening, design 2 inches above DELIVERED flood rim
  -> free air through lid notch -> BRUTE reservoir (no drain/overflow)

Reservoir -> two separate top-entry reinforced suction hoses and inlet strainers
  -> two 12 V SHURflo internal-bypass pumps
  -> two 200-mesh filters / pressure test points
  -> two pressure-rated distribution lines -> 12 XB05PC emitters per group
```

The domestic supply ends in air. Do not extend its discharge tube into the tank or close
that gap with a funnel. Plunger leakage must also fall inside the tank. Suction, returns
and irrigation water must never join the domestic pipe. All reservoir penetrations are
above the rim; service does not depend on a below-water bulkhead staying watertight.

**Two independent wired floor detectors, co-located on the spill path:** FloodStop's
sensor closes its own fill valve; DiversiTech WS-1 removes pump permission. Neither uses
Zigbee, HA, Wi-Fi or cloud. Existing `AL-S-PLANT-LEAK` remains notification-only.
The detectors are separate systems: one sensor activating does NOT electrically trigger
the other. Demonstrating that representative spills wet BOTH is a commissioning hold;
if floor topography defeats this, add manufacturer-approved remote sensors or redesign
before accepting the installation. A small leak reaching only one detector is not a
proved combined shutdown. Do not claim otherwise from the drawing.

### Pump safety wiring (electrician's functional schematic)

```text
RC6 GFCI -> cord to enclosed equipment distribution
    +-- UNSWITCHED -> FloodStop adapter + 4 AA backup
    +-- UNSWITCHED -> TR40VA001 control transformer (120 -> 24 VAC)

24 VAC R -> WS-1 healthy contact -> M8000 CLOSED-ON-RISE
    -> [momentary ARM button OR K1 NO seal-in pole] -> RIB2401D K1 coil -> C
120 VAC L -> K1 second normally OPEN pole -> pump-permitted distribution
    -> timer A input / timed output -> GST120A12-R7B A -> fused 12 V pump A
    -> timer B input / timed output -> GST120A12-R7B B -> fused 12 V pump B
```

The timer arrangement above is **timer demand AND manually armed pump permission**.
Do not bridge two timer outputs or backfeed their outlets. The common permission
contact is ahead of the two timer INPUTS; their clock
backup retains time, but confirm programs/outputs after recovery. Their dedicated outlets
and the supplies live inside the dry control enclosure. Only the rack's cord plug enters
RC6's in-use cover. No plug-in timer projects through that cover. Keep low-voltage and
mains terminations segregated; provide strain relief, grounding and fused motor harnesses.
No override outlet may power a pump around the relay. The low-level float carries only
relay-coil current; verify close-on-rise with an ohmmeter before connecting.

A floor event latches the WS-1 off until dry and manually reset, and FloodStop separately
requires its Open button. Drying the floor alone must not restart irrigation. Empty tank
or an open low-water wire de-energizes the pump relay; refill stays enabled. Return
of water alone does not rearm the seal-in relay; press ARM after checking the system.

**Power loss:** pumps stop. FloodStop can still close on its batteries; it is a motorized
ball valve, NOT a spring-return fail-closed valve. Exhausted batteries plus no mains leave
fill-valve position uncontrolled by sensing; the mechanical float remains the fill stop.
WS-1 may reset when power is interrupted, but the relay loses its seal-in and stays OFF
until ARM is pressed. Following any outage, inspect, verify the two
safety controls and timer state, and rearm locally. The vacation procedure closes the
manual water stop, so unattended mains failure cannot admit new supply water.

FloodStop's auxiliary pigtail has not been qualified as a latched, suitably rated pump
interlock. It is deliberately not connected to a guessed relay circuit. Removing batteries
from an integrated watering kit was also rejected as a substitute for a documented cutoff.

## Water budget and irrigation settings

Shared calculation inputs: `typehaus.model.plant_reservoir.RESERVOIR_WATER_BUDGET`.

| Quantity | Design allowance |
|---|---:|
| Nominal tank / conservative complete release | 10 gal |
| Normal measured fill | 9 gal |
| Unusable below suction / low-water cutoff | 1 gal |
| Untouched operating reserve | 1 gal |
| Ten-day irrigation allowance | **7 gal** |
| Maximum average daily draw | **0.7 gal/day** |
| 24 plants, equal initial allocation | **110.4 mL/plant/day** |
| One zone: 12 x 0.5 GPH emitters | 6 GPH |
| Initial daily run per zone | **210 seconds (3 min 30 sec)** |

Example schedules: A daily 06:00–06:03:30; B daily 08:00–08:03:30. Times avoid simultaneous
starting current and make delivered quantities easy to observe. Tune each group to its
plants; cap the SUM at 0.7 gal/day. Additional/larger pots consume that same water budget.
Cap unused outlets. Water thoroughly and let pots finish draining before departure.

Nine gallons and the one-gallon cutoff are **measured marks**, not a curve inferred from
the outside taper. The section shows illustrative heights only. Establish them using a
graduated container; set cutoff high enough to avoid suction air and vortexing. If usable
volume is smaller, lower the daily allowance or the supported collection. Never silently
raise the tank size. The successful trial, not this arithmetic, establishes autonomy.

**Hydraulics:** select internal bypass rather than the original SEAFLO pressure-switch pump
to avoid short cycling at 6 GPH. The current Pentair row rates 8000-543-210 at 35 psi bypass
and 7 A maximum. Use the 7 A value, not an older catalog's 5.5 A. The selected 8.5 A supply
has nominal current margin; verify cold motor starting before acceptance. Short daily runs
limit bypass heating; do not run a closed/bypassing zone continuously.

XB05PC pressure compensation requires 15–50 psi. The shelf's 75-inch elevation consumes
about 2.7 psi from a pump at 12 inches AFF, before pipe/filter losses. Measure pressure and
catch volume at the highest/farthest outlet with all twelve running; an open-flow pump
rating is not a hydraulic calculation. A separate low-flow regulator is omitted because
the pump's 35 psi bypass is inside the emitter range; verify the supplied pump's pressure.

**Siphon rule:** every emitter outlet and hose end stays ABOVE the maximum reservoir water
level, including future plants. Keep secured lines uphill from the tank and do not put
loose hoses in lower trays. Pump check valves are not credited as anti-siphon protection.
A floor-pot extension needs a separately selected positive shutoff/anti-siphon arrangement.
Lines can still drain their finite contents when pumps stop; include them in release volume.

## Spill calculation and layout

The existing resolved room floor is approximately 137.8 SF, with a modeled doorway water-stop
crest 0.38 inches above the vinyl. That crest is only useful if both ends, jambs, toe bead
and all perimeter penetrations hold water. Verify the **lowest actual escape elevation**;
uneven floor, unsealed trim or another low opening invalidate the flat-room calculation.

Conservatively subtract the entire 18 x 18 inch tank envelope and 36 x 12 inch equipment
rack, rather than just rack feet. Allow 1.75 gal retained in tubing/filter bodies and a commissioned
maximum fill rate of 0.1 GPM. Acceptance limits: up to 60 seconds for water to reach and
activate the floor detectors, plus 15 seconds for valve closure. These are test limits,
not manufacturer's promised response times.

The 1.75 gal allowance covers both full 50-ft headers at 0.600-inch ID
(1.47 gal), 100 ft of 0.170-inch-ID outlet tube (0.118 gal), and suction/filter allowance.
Prime the lines before the vacation fill mark; actual daily draw includes refilling any
line volume that drains between cycles.

Total bounded release = 10 + 1.75 + 0.1 x 75/60 = **11.875 gal** for a release on the intact, rate-limited fill branch. This gives about
**0.144 inches** on the remaining floor, below the 0.25-inch design depth and modeled
0.38-inch crest. A stuck float with failed leak shutdown remains an **unbounded** supply
release while the manual stop is open. Throttling delays it; it does not prevent it.
A leaking connection upstream of the throttling valve does not obey the 0.1 GPM bound;
measure that separate unrestricted-flow case and verify containment/shutdown before accepting
the installation. The electric valve cannot isolate a leak upstream of itself.

Tank centre is (166, 17.75) inches; rotation 180 puts fill toward the south wall. Published
handle width is 18 inches; minimum bounding-box y is 8.75 inches, beyond the wall finish
at approximately 7.79 inches. The separately modeled FloodStop valve at (155, 9.75),
13–16 inches AFF, mounts directly at the manual stop BEFORE flexible tubing; its kit is
still billed only once on the rack. Equipment rack centre (164, 37), size 36 x 12, rotation 180:
east edge x=182 stays west of the door-swing strip x>=186. Rack rear edge y=31 leaves a
4.25-inch separation from the tank's conservative envelope. Wired detectors at (166, 28.8)
occupy the gap. Keep the floor strip open so water reaches them; move/add probes to actual
low points on site. No new equipment attaches through the humid liner without a sealed fixing.

Tank bracket top is 21 inches; the removable lid at the 17.13-inch rim has six inches of
lift below the 32-inch window sill. Rack top is 24 inches. Keep the equipment service area
toward the room free of movable plants and furniture. Published body dimensions do not
establish the bracket arm travel, pump mounting pattern or finished enclosure fit.

[Section and distribution illustration](plant_reservoir_section.svg) — schematic water
levels, explicit inlet/discharge distinction, and the two irrigation groups.

## Product schedule and dated budget

Catalog product refs and per-assembly quantities are in `plan/plant_reservoir_types.py`;
`ProductPart` makes them actual takeoff rows. The tank and rack are priced by their parent
appliance type; neither is billed again as an extra product. The FloodStop sensor, controller
and adapter are one kit, not three additional purchases. Its floor symbol does not rebill it.

USD, **2026-11-10**, before tax, delivery and installation. **A = purchasing allowance**, not
a verified quotation. Pump's $117.99 is the retailer's `product:price:amount`; M8000 $27 is
maker retail. TR40VA001 $22.20 is SupplyHouse retail; RBY075MPTX $19.52 is Sprinkler Warehouse retail. A budget target is not a promise of current availability or a complete quote.

| Part / model | Qty | Unit $ | Basis / connection / envelope |
|---|---:|---:|---|
| Rubbermaid FG261000GRAY | 1 | 30 A | 15.63 dia, 18 handles, 17.13 high per spec |
| Rubbermaid FG260900GRAY lid | 1 | 15 A | Matching 10 gal lid; field notches |
| Kerick MA252 | 1 | 25 A | 1/4 OD tube; arm/setout field-qualified |
| Fabricated 304 stainless saddle | 1 | 20 A | Slotted bracket; independent of removable lid |
| FloodStop FS14C / 20020 kit | 1 | 150 A | 1/4 compression; controller within 30 inches of valve |
| John Guest PPSV040808W | 1 | 12 A | 1/4 OD tube; throttle verified at highest supply pressure |
| SHURflo 8000-543-210 | 2 | 117.99 | 3/8 NPT; drawing I-18 hold; 9 x 4.5 x 4.5 service box |
| MEAN WELL GST120A12-R7B | 2 | 40 A | 12 V 8.5 A; 167 x 67 x 35 mm; locking 4-pin |
| Hydrofarm TM01715D | 2 | 22 A | Local seconds-resolution schedules; one timer per group |
| Rain Bird XB05PC | 24 | 1.30 A | 0.5 GPH; 15–50 psi |
| SHURflo 255-323 strainers | 2 | 12 A | 1/2 barb inlet x NPSM outlet; adapt suction to 3/8 NPT |
| Rain Bird RBY075MPTX | 2 | 19.52 | 3/4 MPT 200-mesh inline filter; no regulator |
| DiversiTech WS-1 | 1 | 50 A | 24 VAC; manual-reset floor detector |
| Madison M8000 | 1 | 27 | 1/8 NPT bracket mount; 1-inch float; close-on-rise |
| Functional Devices RIB2401D | 1 | 35 A | DPDT: seal-in and supply contact; 24 VAC coil |
| Functional Devices TR40VA001 | 1 | 22.20 | 120/24 VAC 40 VA control transformer |
| Fabricated 36 x 12 x 24 rack/enclosure | 1 | 30 A | Removable equipment, dry segregated electrical compartment |
| Commodity fitting/wiring package below | 1 | 60 A | Defined allowance; purchase list must close before ordering |

Total: **$930.42**; **$69.58** unallocated to the $1,000 ceiling. Most prices remain
allowances, so procurement is on hold until supplier totals including all small parts fit.
Do not remove protection or under-rate a supply to preserve the estimate.

The commodity package must include: 4 ft potable 1/4 OD fill tube and correct compression
ferrules/inserts; adapters and pressure test points for the separately counted 200-mesh filters; four 3/8 NPT
pump hose-barb adapters; strainer adapters; two top-entry reinforced suction hoses and
clamps; two 50-ft 1/2-inch blank pressure-rated distribution tubing rolls (>=50 psi); a 100-ft
roll of 1/4-inch outlet tubing; 24 emitter outlet
stakes; compatible tees, end caps and securing clips; two grounded NEMA5-15/C13 supply
cords; two correctly pinned Kycon KPPX-4P mating harnesses; motor fuses/holders to OEM
requirements; control wiring, one guarded 1NO momentary ARM pushbutton, coil suppression, protected
terminals, strain relief, four AA backup batteries
and sensor/float brackets. This is an explicit commodity specification, not a named retail
kit. Confirm filter/tube pressure ratings and fitting/thread standards before purchasing.

## Qualification holds and commissioning

1. **Potable fill / air gap:** confirm MA252 suitability/listing with plumber/AHJ, supply
   pressure rating and actual effective opening. Prior Dial 4154 and 94045 were cooler parts,
   not demonstrated potable selections. Read the adopted MN UPC air-gap requirements from
   the primary code; retain a 2-inch design gap pending that verification. An assumed orifice
   or the inlet `ServicePort` cannot prove code compliance.
2. **Delivered geometry:** reconcile Rubbermaid sheet's 17.13-inch rim against current
   catalog's 17.32-inch height. Fix bracket relative to the actual rim, not the floor.
   Demonstrate MA252 float closes at the measured nine-gallon mark with the entire discharge
   assembly two inches above the rim. If it cannot, revise bracket/valve before fabrication.
   Fit the independent bracket and lid notch, and prove unobstructed float travel/lid removal.
3. **Procurement:** close all A prices, exact filter/tubing/fitting SKUs and electrical
   enclosure parts; obtain pump I-18 dimensional drawing. The shown envelopes are not shop
   drawings. Do not call this BOM fully procurement-qualified until these items close.
4. **Electrical:** wet-test WS-1, prove NO relay wiring and open-wire/low-water shutdown.
   Verify PSU cold starts, proper pin pairs, fuse sizing, closed RC6 cover and mains separation.
   Prove no pump runs on battery power or from an unswitched bypass outlet.
5. **Fill fault:** hold float open under supervision. Confirm <=0.1 GPM at worst supply
   pressure. Introduce a small measured spill at each likely leak point; time water arrival
   and shutdown at BOTH wired detectors. Both pumps and fill must stop within the modeled
   limits. Drying alone must not restart either. Test/reset both controls independently.
6. **Watering:** catch every emitter's delivery, including highest/farthest and lowest,
   with all zone outlets active. Measure terminal pressure, daily draw and tubing retained
   volume. Check closed-zone heating, pump noise, loose-hose release and siphoning with pump
   off, including a full tank and the lowest permitted pot. Label the permitted outlet height.
7. **Power recovery:** test mains loss, FloodStop battery operation/low battery, dry and wet
   restoration, clock retention, cutoff return and intentional rearm. Record actual behavior;
   neither valve fail-close nor alarm-latch retention across complete power loss is assumed.
8. **Vacation trial:** run a full ten days with manual stop CLOSED, measured start/end tank
   volumes and representative plants. Require healthy plants, <=7 gal use, reserve retained,
   no dry running/leaks, and the safety tests above. Reduce demand if the trial fails.

### What the engine still does not certify

Domestic `PR-M-CW-PLANT-STUB` still lacks a supported tank fixture-unit basis; do not add a
fake WSFU value or disguise the tank as a lavatory. The visual symbol uses
`ModelRepresentation.symbol`, leaving that code vocabulary untouched. No automatic check
certifies the inlet air gap, physical floor water-tightness, detector water travel, wiring,
pump curve or plant survival. Reservoir tests establish authored dimensions and arithmetic.

## Source documents

- [Rubbermaid BRUTE manufacturer dimensions](https://rcp.structpim.com/media/20254/brute-spec-sheet.pdf).
- [Kerick M series](https://www.cdivalve.com/products/detail/kerick-m-series-float-valves).
- [FloodStop installation documents](https://ipsplumbingproducts.com/brands/floodstop/floodstop-installation-instructions/), FS14C/20020 manual.
- [Pentair 8000 product rows](https://www.pentair.com/en-us/flow/commercial-products/water-supply-pumps/spray-pumps/8000_series_diaphgram_pumps.html).
- [Pentair 8000 installation manual](https://www.pentair.com/content/dam/extranet/web/nam/shurflo/manuals/911-314-series-8000-pump-iom.pdf).
- [Pump retail price](https://sprayersupplies.com/8000-543-210-shurflo-a6501568).
- [MEAN WELL GST120A sheet](https://www.meanwell.com/Upload/PDF/gst120a/gst120a-spec.pdf).
- [Hydrofarm timer instructions](https://s3.amazonaws.com/hydrofarmpubdocs/tm01715d_instructions.pdf).
- [Rain Bird emitters](https://www.rainbird.com/professionals/specifier/emission-devices-bubblers).
- [WS-1 instructions](https://media.diversitech.com/doc/doc00036.pdf).
- [M8000 maker specification and retail](https://www.madisonsensor.com/m8000-single-point-level-switch).
- [Functional Devices RIB specifications](https://hosted.functionaldevices.com/downloads/datasheets/RIB2401D.pdf).
- [Minnesota chapter 6 amendments](https://www.revisor.mn.gov/rules/4714.0603/) (not a replacement for the adopted UPC table).

- [Control transformer primary specification](https://hosted.functionaldevices.com/downloads/datasheets/TR40VA001.pdf).
- [Control transformer retail](https://www.supplyhouse.com/Functional-Devices-TR40VA001-Transformer-40-VA-120-to-24-Vac-Foot-and-Single-Threaded-Hub-Mount).
- [200-mesh filter manufacturer](https://www.rainbird.com/professionals/specifier/zone-filters-pressure-regulators) and [retail](https://www.sprinklerwarehouse.com/rain-bird-200-mesh-inline-wye-filter-3-4-in-rby075mptx).
