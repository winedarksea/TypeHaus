# RM-M-STUDY fitted booth

Design basis: 2026-10-19. Adults approximately 5′4″–6′0″, extended laptop work,
using the laptop's own keyboard. This fixed booth has limited adjustability; laptop
screen and keyboard positions remain coupled. It is not a universal ergonomic workstation.

## Construction and purchasing

The bench is an independent floor-standing carcass, not a solid-walnut slab or wall-hung
seat. Its immutable occurrence is FURN-M-STUDY-BENCH. Do not fasten into W-M-HS4:
that north wall contains the laundry pocket door. Glue and screw the plywood carcass together;
two internal partitions plus the two ends support the deck. Four triangular plywood
gussets transfer the reclined back load into those supports. Install on a level floor,
with protected shim pads as necessary; conceal rather than bridge the rear wall gap.

- Front: one **¾″ finished edge-glued black-walnut panel**, horizontal grain,
  matched heartwood coordinated with the desk. Mill from 4/4 stock; plan around
  rough boards up to 10″ wide, rather than requiring a single wide slab.
  Attach with slotted fixings and clearance for seasonal movement across its height;
  do not rigidly glue it to the plywood supports or trap it between fixed trim.
  The glued plywood carcass and gussets provide support independently of this face.
- Carcass, seat deck and back: nominal ¾″ **A-1 birch veneer-core plywood**;
  maple is acceptable at the same face/back grade and core specification.
  A is the face grade, 1 the back.
- Require sound cores without significant voids at fasteners or joints. Veneer face grade
  does not establish core quality. No MDF or particleboard substitution.
- Measure actual supplied thickness before cutting joinery. The model uses nominal ¾″;
  update the spec and regenerate the parts if changing thickness, rather than cutting
  nominal dadoes into thinner stock.
- Sand and seal all faces/edges beneath removable cushions. Match the solid walnut front,
  solid walnut edging and cap to the desktop's clear satin hardwax-oil finish. Conceal
  plywood edges with walnut edging; ease exposed arrises. The deck's supporting front
  edge gets a ¼″ roundover, including the solid seat-edge strip.
- Cap fixings permit seasonal solid-wood movement. No storage openings or drawers.

`BuiltInBenchSpec` owns dimensions and materials. `bench_parts()` generates the actual
notched supports, triangular gussets, angled substrate, seat/front/cap and upholstery.
Its geometry feeds viewer, GLB and IFC; its blanks feed solid-wood shop schedules
and the plywood sheet order.
Gusset and notch notes are cutting instructions, not rectangular finished shapes.
The 2″ high toe recess is 2″ behind the finished front, so each support's notch is
1¼″ deep from its own front edge. The back substrate blank includes the additional
length needed for its beveled ends, rather than only the rear-face slope length.
The millwork schedule orders whole 4×8 sheets by material, preserving grain with
⅛″ saw kerf and ¼″ edge trim per side. Its conservative rectangular-blank layout
includes no spare sheets. `haus millwork --json` retains individual `panel_cuts`
for fabrication reference; sheet quantities appear under `panels`. Upholstery is not
rough lumber and does not acquire board-foot quantities.

## Fit and upholstery

The current room's gypsum bounds are x=164⅜″..214⅝″, y=219⅜″..266⅝″. Keep west,
south and east doorway-return walnut at ¾″. Omit north walnut below 36″, keep its gypsum,
and retain north/south acoustic felt above 36″. Bench width is 48⅝″ with 1/16″ end scribes;
rear is 1/16″ off north gypsum. Dimensions are relative to finished room floor, not the
storey datum. Bench overall depth is derived from its back rake and lumbar contact face.

- Horizontal deck: 17½″ AFF. Unloaded seat cushion: 3″, top 20½″ AFF.
- Seat foam: high-resilience polyurethane, density **at least 2.5 lb/ft³**, supplier-rated
  **25% IFD 35–45 lbf**. Require the test method, specimen thickness and conditioning.
  Density is not firmness, and neither predicts occupied height on this rigid deck.
- Initial occupied seat target: **19–20″ AFF**, nominal 19½″. Verify using the actual foam,
  wrap and cover. Use removable fit pads/shims and footrest adjustment; record changes.
- Seat front: rounded waterfall foam nose, 1″ design radius, thin polyester wrap,
  zippered warm gray performance-fabric cover and concealed non-slip retention.
- Back: **100° included angle** to horizontal seat, supported by carcass gussets;
  cap finishes at 36″ AFF. Approximately 1″ resilient foam, with no hard ridge at the cap.
  Upholster a sample to select back-foam firmness; the thin pad must not bottom at lumbar
  contact. Do not apply the seat's 4″-sample IFD value as a thin-pad compression claim.
- Lumbar insert: gently contoured, removable, initially ½″ maximum projection,
  center **7″ above occupied seat**, concealed height adjustment **6–9″ above it**.
  Model the nominal position at 26½″ AFF. Cover access permits repositioning/replacement.
- Effective seat depth: **17″**, lumbar contact plane to seat nose. Removable inserts
  shorten it for smaller users; verify thigh support and a gap behind the knees.
- Footrest: purchased removable non-slip platform, approximately 18″ × 12″,
  independent height adjustment 1–6″ and tilt 0–20°. Modeled at nominal 3″/10°.
  Place under the fixed desk; shift/remove it for an individual user. Keep the low
  south-wall ventilation grille unobstructed.

The fixed walnut desk remains 29″ wide and 29½″ high; both desk and folding leaf are
16″ deep. The leaf fills the remaining finished width with 1/16″ end scribes. Both tops
use the same flitch, 1″ finished off 5/4 stock, grain east–west. The refit has approximately
9½″ between desk and bench fronts; feet extend beneath the desk. The leaf is modeled
deployed but normally folded down for entry. Do not treat its deployed footprint as
unobstructed walking space.

The old 18⅞″ projection Hebgo supports cannot fit a 16″ leaf. Specify **two Sugatsune
EB-303/EP-BL**, 307 mm projection and 165 mm height, with continuous ledger/piano hinge
and catches into the fixed top for lateral restraint. The manufacturer publishes
position-dependent P1/P2 ratings, 150/75 kgf; do not add ratings or claim them at a
16″ front-edge overhang without checking the installation/load position. Verify lag
connections to study-face let-in blocking and the seated knee envelope before fabrication.
No through bolts may bridge the staggered wall leaves. The folded panel is approximately
12½″..28½″ AFF; keep outlets and the return grille clear of its full sweep and footprint.

Bench construction, plywood, solid front and trim costs remain in FT-STUDY-BENCH. Seat/back
upholstery, fit inserts and purchased footrest remain in cabinet-study-booth-cushions.
The existing estimate ranges are provisional pending revised fabrication/upholstery quotes.
The shop schedule is an unpriced mirror, never another cost.

## Fabrication acceptance — outstanding physical work

Before releasing fabrication, test a full-size mock-up with the actual cushion construction
and representative users at both ends of the height range for **at least 60 minutes**.
Confirm supported feet and thighs, clearance behind knees, lumbar contact, relaxed shoulders,
comfortable laptop keyboard reach, no pressure ridge or foam bottoming, and safe entry with
the leaf stowed. Check hands can release both brackets and knees clear the folded arms.
The shortest user should not need to slide forward and abandon lumbar support.

Record measured occupied height and all foam/insert/shim adjustments. If construction
geometry changes, update the authored spec, regenerate 3D and shop outputs and rerun fit
checks. Software tests do not complete this physical acceptance step.

References: [Columbia plywood specification guidance](https://www.columbiaforestproducts.com/resources/frequently-asked-questions),
[PFA foam density and firmness](https://pfa.org/foam-performance/),
[Cornell workstation guidance](https://ergo.human.cornell.edu/ergoguide.html),
[OSHA seating guidance](https://www.osha.gov/etools/computer-workstations/components/chairs/),
[Sugatsune bracket](https://www.sugatsune.com/folding-bracket-black-eb-303-ep-bl/).
