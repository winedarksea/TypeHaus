# PVKIT rake review — 2026-11-10

Owner supplied a review suggesting published PVKIT capacities, HUR grabs and
additional attachments near the rake. This review records what those sources
resolve for the current Catlin array. No supplier contact was made.

## Published grab data

[IAPMO UES ER-945, Table 1 and §3.2](https://floridabuilding.org/upload/PR_Tech_Docs/FL47050_R0_AE_ER_0945.pdf)
lists **353 lbf EdgeGrab** and **861 lbf MidGrab** allowable uplift. These are
grab/standoff component capacities; the system is limited by the weaker grab
or seam-clamp connection. Table 2 lists Image II **26 ga**, not the modeled
24 ga, so it does not close our exact roof connection check. The retrieved
report states validity through **2026-08-31**, already past this review date;
obtain a current evaluation before relying on it for permit submittal. Its
§3.5.1 assembly loading example uses Jinko modules and S-5-E Mini clamps, not
our Aptos/Image II assembly. Thus the grab-capacity source lookup is complete,
but assembly applicability and current recognition remain open.

## Current modeled array

`params/solar.py` authors 18 Aptos DNA-108-BF10-410W modules, one row of nine
on each 6:12 roof plane, portrait, 67.7 × 44.6 inches. The southern module starts
4 inches from the modeled south roof boundary; the north end reserves the
36-inch access pathway. Site basis in `plan/site.py` is 115 mph ultimate wind,
Exposure B, Risk Category II. The southern rake clearance is a layout dimension,
not a demonstrated wind setback.

There are four individual `S-5-PVKIT` connectors per module (72 total), with
full N carriers selected through the hardware catalog. The model does not
distinguish EdgeGrab from MidGrab or author shared grabs between modules.
Consequently the 861 lbf MidGrab value cannot be assigned to these generic
connectors without resolving the actual frame connections and shared reactions.

Module surface area is `67.7 × 44.6 / 144 = 20.97 sf`. As a component-only
screen, four 353 lbf EdgeGrabs sum to 1,412 lbf, equivalent to **67.3 psf**
uniform net uplift over that area **only with equal reactions**. This is not
the site's wind pressure or an assembly rating. Actual support spacing,
cantilevers and pressure zones determine individual reactions, and the roof
connection or module frame may govern first. Do not compare ultimate wind
pressure directly with these allowable capacities.

There is also an unresolved geometric interface: `clamp_columns_inches()`
chooses seam stations at least 6 inches inside the 44.6-inch module ends, while
the two cross-slope support positions are 6 inches in plan inside the other
module boundaries. Those points alone do not establish that a physical PVKIT
grab reaches the frame. Confirm actual frame contact, Aptos permitted clamping
edges/zones, frame thickness and load rating before treating these generic
support markers as an installation layout. The current 1.3-inch frame is
33.0 mm, within the 30–46 mm range shown in the
[PVKIT installation instructions](https://f.hubspotusercontent00.net/hubfs/3482954/Resources/Product%20Documents/Solar/PVKIT%202.0/pvkit-2-0-installation.pdf);
that dimensional fit does not establish permitted clamp positions.

## Reviewer suggestions and remaining decisions

- **Mini versus full clamps:** the current catalog already selects full N for
  PV. [S-5!'s PVKIT page](https://www.s-5.com/products/solar-panels-on-metal-roof-pvkit-2-0/)
  expressly includes compatible Mini clamps. Mini is not categorically excluded
  from PV use; its suitability depends on the exact connection and loads.
- **HUR:** [S-5!'s current HUR page](https://www.s-5.com/products/pvkit-hur-solar-panels-on-metal-roof/)
  describes HUR 3.0, 6-inch grabs and a 150 psf uplift rating. That does not
  establish a 150 psf rating for our Aptos module, Image II panel, clamp and roof
  fastening combination. Keep HUR as an option if the calculated limit is the
  module/grab interface; it cannot establish roof-fastener capacity.
- **More attachments:** six per module is not a general approved remedy. Each
  added grab must engage an Aptos-approved frame location and transfer load
  through a seam and roof attachment. A generic third support row may miss the
  frame or fall outside the module's approved clamp configuration.
- **Setbacks and zones:** calculate zones and net PV pressures under the
  applicable ASCE 7 edition and rooftop-array provisions. The reviewer's rough
  edge-width rule is insufficient to establish a compliant setback or demand
  for this 6:12, near-ridge array. Access setbacks and wind zones are separate
  constraints; the north access pathway alone does not close wind design.

Next calculation needs an explicit grab/frame layout, site wind pressures and
support reactions, then the complete module → grab → N clamp → Image II panel
→ panel fastening → roof structure load path. Retain the PVKIT rake item open;
the newly resolved item is the published grab-capacity lookup.
