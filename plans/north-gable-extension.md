# Catlin house — selected extruded-gable north connector

**Original study:** 2026-09-08

**Decision update:** 2026-09-09

**Status:** selected concept and pre-design brief; no model or construction changes are
authorized by this study.

## Decision

Proceed into schematic design with this arrangement:

- Move the unbuilt 24 × 24-foot garage **2'-6" north**, keeping its x = 6'..30' position,
  ordinary frost-depth ICF stem and north-facing overhead door.
- Extend the garage's north-south gable **6'-0" south across its full 24-foot width**. This is
  a pure extrusion of the existing 4:12 roof, not a shed roof and not a stepped roof.
- Keep the connector cold and open to the east. Put a compact shared upper landing around
  `D-M-ENTRY` and `D-G-SERVICE` at the west end and climb to it on five broad tiers from the
  east.
- Preserve `FS-BW-FLOOR` as the one landing/floor identity. Extend its composite walking
  surface locally through the garage service-door opening and **retire `SL-G-STEP-0`**.
  Retain the interior garage flight `ST-G-SERVICE` below that landing.
- Design first for **no new concrete in the passage**: use the new garage roof framing for
  the roof and an engineered house-to-garage bridge for the landing. Keep helical supports
  as a priced fallback, not as the default.
- Price three west-edge assemblies. A vertical on-edge 2×4 screen and a corrugated-metal
  windwall are the leading choices; opal multiwall polycarbonate remains the daylight-rich
  alternate.

This supersedes the recommendation in [north-entry-options.md](north-entry-options.md). The
through-garage route and enclosed east gallery remain documented alternatives, but the
extruded gable is now the preferred north entry.

## Geometry fixed by this decision

Project coordinates use +y north; the main-floor framing datum is 0'-0" and approximate
finished grade is -2'-10".

| Item | Current model | Selected study geometry |
|---|---:|---:|
| House north cladding | y = 36'-7 1/4" | unchanged |
| Garage footprint | x = 6'..30'; y = 40'-8 5/8"..64'-8 5/8" | x unchanged; y = 43'-2 5/8"..67'-2 5/8" |
| Clear cladding-to-cladding passage | 4'-0 1/2" | about **6'-6 1/2"** |
| Garage north wall to modeled build line | 10'-3 3/8" | about **7'-9 3/8"** |
| House / garage door centres | x = 8' / x = 10' | unchanged |
| Roof | 24-foot-wide 4:12 gable, ridge north-south | full-width 6-foot south extrusion |
| Upper landing | current 4'-6" exterior deck plus separate 3 × 3-foot concrete garage landing | one compact composite landing, provisionally x = 6'-6"..11'-6" |

The six-foot roof stops about 6 1/2 inches short of the house cladding after the garage move.
Use **4–6 inches as the maintainable movement/drainage joint**; the truss/fascia detail may
consume the remaining fraction. The selected full-width roof knowingly shelters
`WIN-M-KITCH` near x = 29'-4" and reduces its direct north sky. The window remains; the
simpler roof is the chosen cost trade.

```text
WEST                                                               EAST / ARRIVAL

screen or wall | shared upper landing | four broad treads | lower landing | open approach
      x≈6      |   x≈6.5..11.5       |   4 × 24 in       |   36 in min  | under gable
               | house + garage doors | 5 equal rises total, climbing west

HOUSE  ===================== about 6'-6 1/2" clear =====================
                              movement joint
GARAGE ====================== moved 2'-6" north ========================
```

## Roof: one new truss package, no passage posts if feasible

Because the ridge runs north-south, the extension continues the garage's existing east- and
west-facing roof planes. It does not create a roof slope that drains toward the house. The
full x = 6'..30' width is also the least custom-looking result: the south rake simply moves
six feet.

The preferred structure is an **engineer-designed gable cantilever integrated into the new
garage truss package**. Structural outlookers/LVLs or a proprietary truss solution backspan
into the garage and transfer load to the east and west bearing walls. Do not describe all of
the extension load as landing on the south gable footing; the roof's primary bearing lines
are `W-G-E` and `W-G-W`.

This is not prescriptive rake framing. The engineer/truss supplier must design:

- six-foot cantilever and backspan, including the dropped-chord or girder-truss arrangement;
- local drift from the 33-foot house gable, unbalanced snow and sliding-snow cases;
- open-end and partially screened wind pressure, uplift and the load path to the garage ICF;
- a fire/draft closure in the plane of the original garage south gable; and
- fascia, soffit, ventilation and roof-panel attachment at the long cantilever.

The prior study's approximate 90–101 psf drift screen is an engineering input, not a model
capacity result. The TypeHaus roof resolver can draw a six-foot `edge_overhangs` surface but
does not create the required structural outlookers, backspan, drift case or uplift load path.

**Fallback only if the truss package cannot carry the cantilever:** price a full-width tip
beam on the minimum engineer-selected helical pile layout. Helical piles avoid excavating
and casting isolated footings in the passage, but their installed price and visible columns
make them second choice. Do not silently restore four concrete pads and piers.

### Roof water, snow and the house joint

- Reverse both garage-eave gutter falls and place leaders at the **north** end. The current
  south leaders would discharge beside the new stairs and wall.
- Put snow retention on the roof zones that can release onto the west screen/wall, tiers,
  HP3 or the east approach. Size it with the metal-roof supplier.
- Keep the roof structurally independent from the house. At the south rake use a formed,
  positively sloped closure fixed to the garage extension only, ending at the house with a
  replaceable compressible or brush seal. Preserve the house rainscreen drainage path.
- Make the 4–6-inch joint inspectable and cleanable from below. Do not fill it with rigid
  foam, grout or sealant that couples the two buildings or traps ice.

## `FS-BW-FLOOR`, `SL-G-STEP-0` and the tiered stair

### One walking surface, two honest structural zones

The architectural goal is one continuous composite datum from the house door, across the
passage, through `D-G-SERVICE` and over the top of the interior garage stair. The structure
cannot be represented by simply enlarging `FS-BW-FLOOR.subfloor_outline`: the present joists
and two beams only support the small current frame, and the two doors are offset by two feet.

Use this structural concept for pricing and engineering:

1. Span shallow primary members **north-south between engineered seats at the house and
   garage frost-founded structures**. Use E-W headers/rim members to support the five-foot
   union of the two 36-inch door-landing patches.
2. Align one primary member through the one-foot overlap of the two door openings where
   practical, allowing it or a connected header to continue into the garage landing. Other
   members terminate at mapped concrete/wood seats; they cannot pass through solid wall.
3. Fix the frame at one building and use an engineered slip/bearing detail at the other for
   differential horizontal movement. Provide accessible shimming or another explicit method
   for correcting small vertical settlement before finish boards are installed.
4. Support the interior three-foot-deep garage landing from that continuation or from a
   garage-only frame. Keep the composite board direction and joint pattern visually
   continuous across the service-door threshold, with a deliberate movement/drainage break.

This is an engineered **non-prescriptive ledger/bearing condition**. The house has thick
exterior insulation and a rainscreen; the garage has ICF and a grade beam at the service
door. AWC DCA 6 prohibits ordinary prescriptive ledger attachment to or through exterior
veneer and limits gaps to the structural band. The construction section must show the real
bearing substrate, standoffs, flashing, lateral restraint and corrosion-compatible
connectors—not fasteners disappearing into cladding or EPS. See the
[AWC DCA 6 deck guide](https://awc.org/wp-content/uploads/2022/02/AWC-DCA62015-DeckGuide-1804.pdf).

If the engineer cannot produce a simple, inspectable bridge, retain the minimum independent
helical supports required for the landing. That fallback is preferable to frost-depth
cast-in-place pads in the house backfill zone. It also makes the floor independent of the
two buildings, at the cost of piles and separate movement joints at both thresholds.

### Finished landing

- The current `SL-G-STEP-0` is a six-inch slab with top at 0'-0" while the garage slab is at
  -2'-10". As modeled, it has no wall, post or thickened support beneath the intervening 28
  inches; “poured with the slab” is not a complete load path. Retiring it is a structural
  correction, not merely a finish change.
- Preserve the `FS-BW-FLOOR` UID/tag when this is eventually modeled. Retire
  `SL-G-STEP-0` and its 0.17 cy concrete quantity; do not retire `ST-G-SERVICE`.
- Make the upper landing at least x = 6'-6"..11'-6" so it contains the full width of both
  door landing patches. Final edges must clear door swings, handrail returns and west screen
  posts.
- Set the **finished composite surface**, not merely the joist top, relative to both sills.
  Keep exterior drainage below and away from the thresholds; then rederive the interior and
  exterior stair rises from that finished elevation.
- Use capped composite decking listed for exterior deck/stair use, manufacturer-required
  joist/stringer spacing, 3/16-inch-class drainage gaps, joist tape, field treatment on every
  PT cut and salt-compatible fasteners. Avoid a hidden pan that can hold salty meltwater over
  the ICF.

### East tiers

Use five equal rises over the approximately 34-inch grade-to-landing difference: nominally
**6.8 inches each**, verified after final grading and deck-board thickness are known. The
selected schematic module is four **24-inch-deep** composite treads/platforms followed by a
minimum 36-inch lower landing. From the provisional upper-platform edge at x = 11'-6", that
puts the four tiers at about x = 11'-6"..19'-6" and the lower landing at
x = 19'-6"..22'-6", leaving a sheltered open approach farther east.

- Maintain at least 36 inches clear; use most of the roughly six-foot passage width for a
  generous procession and snow clearing.
- Provide a continuous graspable handrail for all five risers. A garage-wall rail is the
  visually quiet default, but its anchors must reach structure rather than cladding/EPS.
- Protect any walking edge more than 30 inches above adjacent grade. Integrate the west-edge
  screen with the guard only if it is engineered for guard loads and four-inch opening
  limits; otherwise provide a separate guard.
- Frame the terraces as a coordinated stair/platform assembly attached to the frost-stable
  upper landing, with the lower end on a drained, compacted-aggregate/paver landing and an
  engineer/AHJ-approved movement detail. Seasonal movement may not destroy the 3/8-inch
  riser-uniformity tolerance.
- Keep roof leaders, HP3 meltwater and snow storage away from the bottom landing.

Minnesota's field guidance summarizes the controlling residential dimensions as 36-inch
minimum stair width, 7 3/4-inch maximum riser, 10-inch minimum tread and a handrail for four
or more risers. Decking and flashing must follow their product instructions. See the
[Minnesota DLI Code Administration Manual](https://www.dli.mn.gov/sites/default/files/pdf/cam.pdf).

## Excavation and concrete: selected practical approach

### Corrected code basis

Minnesota is still enforcing its 2020 Residential Code, based on the **2018 IRC**, while the
next residential-code adoption remains in rulemaking. See [DLI's current-code
page](https://www.dli.mn.gov/business/codes-and-laws/2020-minnesota-state-building-codes),
the [official Minnesota Rules chapter 1309](https://www.revisor.mn.gov/rules/1309/), and the
[chapter 1309 rulemaking docket](https://www.dli.mn.gov/about-department/rulemaking/rulemaking-docket-minnesota-rules-1309).

The earlier version of this study incorrectly called the garage footing a violation of IBC
§1809.6's 30-degree adjacent-footing rule. That section is not reproduced as a prescriptive
rule in the adopted Minnesota IRC. Keep the 30-degree line and a 1.5:1 excavation slope as
**conservative engineering/geotechnical screens** for undisturbed bearing, construction
access and differential settlement—not as an automatic code failure. The governing design
obligation is still a complete load path onto suitable undisturbed soil or approved
engineered fill.

The current four-foot layout places the garage south footing only about 44.2 inches from the
house footing/bedding reference, inside the conservative screens used in the original study.
Moving the garage 2'-6" north increases that separation to about 74.2 inches, roughly four
inches beyond the 70.0-inch 30-degree screen measured from the house bedding underside. This
is useful but not generous; survey, overdig and actual soil can consume the margin.

### Foundation decision

Keep the garage's current foundation type:

- 20 × 8-inch strip footings bearing at frost depth;
- 6-inch-core ICF stem to the existing garage floor/wall elevations; and
- the current isolated garage slab and thermal-break concept.

Do **not** pursue a floating slab in this concept. Minnesota may permit one for some detached
garages, but the owner has selected frost-depth ICF for durability, the high service-door
threshold and predictable movement beside the landing. DLI's garage fact sheet confirms the
distinction between attached frost footings and eligible detached floating slabs:
[Garages and the 2020 Minnesota Residential Code](https://www.dli.mn.gov/sites/default/files/pdf/edu_garages.pdf).

Moving the garage changes coordinates, not concrete quantity. The current resolved takeoff
contains about **8.82 cy of `GARAGE_ICF_6`** and about **3.95 cy of 20 × 8-inch perimeter
footing**; the translated 24 × 24-foot foundation keeps essentially those quantities. The
current study target removes 0.17 cy at `SL-G-STEP-0` and, only if the bridge-floor concept
works, the connector's four pads and four piers (about 0.26 + 0.82 cy). Their real saving is
avoiding eight small congested pours and a later excavation mobilization, not the commodity
value of roughly one cubic yard. At the current unitized estimate rates, the four pads and
piers account for roughly **$1,100–$2,100 installed** before any small-load, access or separate
mobilization premium; the small concrete landing adds only about $65–$115 of unitized slab
work. Treat these as comparison values, not bids, and offset them against the engineered
bridge connectors or any helical-pile fallback.

### Construction sequence

1. **Survey and stake both footprints first.** Confirm the moved garage, front/building
   setbacks, driveway grade and roof projection before excavation.
2. **Strip and rough-grade the whole north work zone once.** Establish separate stockpile and
   machine routes so the garage footing bench is not driven over or loosened.
3. **Excavate the deeper house first.** Place bedding, house footings/walls, waterproofing,
   insulation and drain tile while the north face is fully accessible.
4. **Verify the garage bearing bench before backfill.** A geotechnical/structural field review
   must confirm the moved south footing is on native competent soil or prescribe engineered
   fill. Do not let an excavator infer the line from the model's 30-degree arithmetic.
5. **Form and pour the garage footing/stem while the house cut is still open.** Coordinate the
   service-door grade beam, buried hydrant/water crossing, electrical conduit and sleeves in
   this pour. This avoids reopening a narrow trench beside a finished basement wall.
6. **Backfill in controlled lifts.** Protect the house drainage/foam and document compaction
   where the stair landing, hardscape or equipment pads will bear.
7. **Pour slabs and exterior pads after heavy foundation work.** Keep the upper landing and
   tiers framed/dry-supported; do not add ad-hoc cast piers to solve framing in the field.

If field soil or survey invalidates the moved-footprint screen, stop and choose an engineered
stable-fill/retaining detail or a localized stepped/deepened garage footing. The former
study's -8'-9" south-footing concept remains a fallback for engineering—not part of the
selected base design and not a claimed few-hundred-dollar change.

## West edge study

All three alternates occupy the garage west-wall plane near x = 6' and run from the house
joint to the garage. Keep them structurally independent from the house. The roof engineer
must receive the selected porosity because it changes wind pressure and lateral demand.

| Alternate | Weather / light | Durability and maintenance | Cost / appearance | Study disposition |
|---|---|---|---|---|
| **Vertical on-edge 2×4 screen** | Partial wind and snow reduction; best drying and dappled west light | KDAT/PT members on a raised metal shoe; cap/end-treat cuts; periodic stain or paint | Lowest complexity; warm, domestic texture | **Leading option.** Price about 50% open, with actual 1 1/2-inch faces and 1 1/2-inch gaps; use deeper 3 1/2-inch orientation for oblique privacy. |
| **Corrugated-metal windwall** | Best opaque wind block; darkest and most drift-prone at the closed end | Very durable if the lower edge is raised, vented and isolated from salt; matching garage sheets simplify ordering | Likely low-to-medium material cost, but higher wind framing and flashing | **Leading option.** Use garage-profile metal outside and a smooth pale, wipeable inner face or neatly exposed framing. |
| **Opal multiwall polycarbonate** | Solid weather protection with diffuse daylight | Good but scratchable; channels, weeps and closures demand careful cleaning/detailing | Highest material/detail cost; lightest visual result | Carry as an additive alternate, using vertical flutes and a replaceable weeped sill above splash. |

The slatted screen is not equivalent to a windwall, and a full wall is not merely an enlarged
guard. Price the first two from the same elevation and loading criteria. Select after viewing
a full-size three-foot-wide mock-up from the street, the entry and the kitchen.

## HP3, fire and zoning

### HP3

`EQ-M-HP3-OD` cannot remain in the roofed passage. Its current interim position clears the
existing glazing in x but the 48 1/2-inch passage cannot satisfy the manufacturer's inlet and
discharge clearances in y; a wider roofed corridor still creates a cold-air, noise and
defrost-ice problem on the entry route.

Move it to the house north face west of the connector, discharging north into open yard,
subject to the final line-set, disconnect, leader and snow-shed design. Move the cabinet,
pad/stand, line set and electrical service as one coordinated assembly.

### Fire and zoning questions to settle before truss design

Saint Paul's current accessory-building guidance gives detached-accessory exceptions only
when the accessory building is at least six feet from the principal building. The moved
garage walls are more than six feet away, but the roof extension approaches within inches
and may make the combined work “attached” for setback and lot-coverage purposes. Obtain a
written zoning determination using the **whole roofed geometry**, not just the wall-to-wall
dimension. See [Saint Paul accessory-building
guidance](https://www.stpaul.gov/departments/planning-and-economic-development/planning/current-activities/1-6-unit-housing/accessory-buildings).

Ask the building official in the same submission how the roof affects garage-to-dwelling
separation. The design allowance is:

- garage walls/ceiling retain their current gypsum protection;
- `D-G-SERVICE` becomes a dedicated rated/self-closing garage door type if required;
- fire/draft blocking closes the old south gable plane beneath the continuous roof; and
- the extension remains unconditioned and receives no house-air supply or return.

Do not claim that a 4–6-inch movement gap alone provides fire separation.

## Cost hierarchy and design gates

These are relative cost drivers, not bids.

| Decision | Base direction | Why it is economical |
|---|---|---|
| Garage foundation | Translate ordinary frost-depth ICF 2'-6" north | Preserves the current simple perimeter and avoids planned deepening at the house interface. |
| Roof | Integrated engineered truss cantilever | Uses new construction to keep posts, piles and concrete out of the passage. |
| Landing | Engineered foundation-to-foundation bridge | Reuses two frost-stable structures and absorbs the garage landing instead of pouring a separate step. |
| Tiers | PT/KDAT frame with capped-composite wear surface | Dry, repairable construction; avoids a large decorative concrete stair. |
| West edge | Bid slatted wood and corrugated metal together | Both are simple, durable assemblies; selection can follow real pricing and a mock-up. |
| Finish | Repeat garage metal, house dark trim and existing composite | Limits new trades and custom finish systems. |

Before model implementation, obtain four compact deliverables:

1. **Survey/zoning memo:** moved footprint, roof projection, setbacks, lot coverage and
   attached/detached determination.
2. **Geotechnical/foundation section:** actual soils, excavation/backfill sequence, garage
   south-footing bearing and contingency if native soil is disturbed.
3. **Structural concept set:** truss cantilever, drift/uplift, landing bearing map and slip
   joint, tier support, west-edge loads and complete load paths.
4. **Envelope/AHJ section:** roof-to-house movement joint, both thresholds, service-door
   fire/draft separation, roof drainage, snow retention and HP3 relocation.

## Eventual model work and acceptance checks

This study does not authorize code changes. When the decisions above are engineered and
approved, the implementation package should:

- translate every garage-dependent item 2'-6" north, including foundation, slab, walls,
  roof, doors, interior stair, devices, sleeves, leaders, hydrant dependencies, driveway and
  site notes;
- replace the current breezeway roof/walls while preserving `FS-BW-FLOOR`, retiring
  `SL-G-STEP-0` and retaining `ST-G-SERVICE`;
- model real floor bearings/supports rather than relying on `subfloor_outline`, and add a
  screen/fence primitive only if the selected west assembly needs one;
- represent the engineered roof framing honestly or issue an explicit off-model structural
  item—`edge_overhangs` alone is not sufficient; and
- update takeoff/design records so no obsolete pads, piers, posts, glazing or concrete
  landing remain.

Acceptance review must show:

- both 36-inch door landing patches fully supported and clear of swings;
- five equal exterior rises, broad authored treads, lower landing, handrail, guards and
  comfortable headroom;
- the interior garage stair meeting the final composite landing without a hidden step;
- every landing member bearing on a named structural substrate with no ICF/wall collision;
- roof drift, uplift, fireblock, gutter, snow and movement-joint details called out;
- HP3 manufacturer clearances and defrost discharge clear of the walk;
- the moved driveway reaching the north overhead door at acceptable grades; and
- north/east/west plan and section views confirming the full-width gable and selected west
  screen/wall look intentional.
