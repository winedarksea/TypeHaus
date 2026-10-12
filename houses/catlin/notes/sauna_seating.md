# Sauna seating — issued layout, 2026-10-11

The resolved room has a long west-wall lying bench and a separate south/window-side
reading place. The heater, shower and window stay in their current positions. Dimensions
are from finished liner faces, in inches; elevations are above the basement finished slab.
The catalog is `plan/sauna_types.py`, and editable placements are `plan/sauna.py`.

| Component | Length × depth | Top AFF | Resolved footprint (x; y) |
|---|---:|---:|---|
| Upper lying bench | 78 × 28 | 42 | 123¼–151¼; 38 3/16–116 3/16 |
| Lower foot platform | 78 3/16 × 20 | 24 | 151¼–171¼; 38–116 3/16 |
| South reading platform | 58½ × 28 | 24 | 123¼–181¾; 10–38 |
| Access step | 14 × 10 | 12 | 171¼–185¼; 70 3/16–80 3/16 |
| Recliner and bent pad envelope | 57½ × 26 | Platform mounted | 123¾–181¼; 11–37 |

Keep the upper **78 × 28** surface uninterrupted: a backrest cannot project into the
28-inch usable depth. The ceiling underside is `CEIL-RM-B-SAUNA.z0_m`, **82 13/16 AFF**,
leaving **40 13/16 inches** over the upper bench. Older 90-inch and 18/36-inch notes are
superseded. Section cuts at y=72 and y=24 show placed platforms and the reading profile.

[Dimensioned occupancy review](assets/sauna_seating_review.svg) shows lounging and four
seated adults, with seat and leg envelopes. Three upper seats each have 26 inches of run,
18 inches of seat depth and the adjacent 20-inch foot deck. The fourth sits below at the
west end of the south platform, facing east, with 22 inches of seat and 22 inches of leg
support in a 26-inch-wide envelope. Remove the recliner and mattress for this arrangement.
More than four seats is not a design capacity. Lounging leaves a 26 × 68-inch lying envelope
upstairs and a separate supported reading position below.

## Reading fit and mattress qualification

The armless, removable recliner has its back toward the west and feet toward the east,
with daylight beside the reader. It supports itself on the platform; no window/trim
attachment. Drawn back angle is 110° from the seat, with positive locks targeted at
105°, 110° and 112°. The adjustment run stays inside the 57½-inch envelope. Rounded wood
slats support a 36-inch back, 22-inch seat and 22-inch leg section. The bent pad is mounted
on the same platform datum as the wood: its declared height is its bent envelope, not its
4-inch thickness. Adjustable neck and lumbar cushions are shown separately on the back.

Specify a custom **26 × 80 × 4-inch flat shikibuton-style mattress**, linen fabric and wool
filling by default, with flexible 36/22/22 sections, a washable removable linen cover and
natural-fiber securing ties. Flax filling is an alternative subject to the same qualification.
The 4-inch inclined back pad reduces nominal 22-inch seat depth to about 18 inches before
lumbar adjustment; confirm actual compressed depth rather than ordering from flat dimensions.

**Fabrication/purchase gate:** obtain written hot-sauna suitability for the entire assembly
(fabric, filling, thread, ties, any fasteners and cushions), at the intended temperature and
humidity. The requirement is that it can remain during heating; supplier approval is still
outstanding. Natural fibers alone do not establish this. [Home of Wool's custom cushion
information](https://homeofwool.com/blog/all-natural-wool-cushions-for-a-healthy-home/) makes
it a fabrication candidate, without establishing sauna approval. [Futon Tokyo's cotton
futon](https://futontokyo.com/products/gots-certified-japanese-futon-mattress-gray) is a
construction reference, needing custom dimensions and separate heat verification.
Lift and air the mattress after wet use; damp filling must not stay permanently on the deck.

Before fabrication, make a full-size mock-up with the actual 4-inch mattress. Complete a
one-hour reading trial **cool and dry**, checking supported head, lumbar and feet, usable
seat depth, stable positive locks, frame sliding/tipping, and access while someone occupies
the upper bench. Provide removable platform stops/restraints within the reserved footprint
if the fit trial requires them; no wall or window attachment.
Reading takes priority over computing. No armrests are specified. This physical trial is
outstanding and cannot be replaced by the geometric model.

## Framing, service and heater installation

Use unfinished sauna-suitable basswood/aspen with eased edges, concealed suitable fasteners,
open posts and removable deck panels. Transverse bearers carry the long deck slats;
Deck-panel joints land on transverse bearers so the drain-side section can lift.
Connected stretchers carry the low perimeter lighting rails. Inclined side stringers
carry the recliner back slats into its rear uprights and base rails. Design framing/connections for three adults on the
upper bench and one adult below; symbol members are coordination geometry, not a structural
joinery certification. Secure the step against sliding/tipping. Mock up the 12/24/42-inch
access sequence, including the final 18-inch rise, while the upper bench is occupied.

The floor drain `FX-B-SAUNA-FD` lies under the lower foot platform. Removable deck panels
must expose its grate, both condensate air-gap terminations and connections without cutting
joinery. Both drops now descend inside the north-wall cavity, then run below the foot deck;
no pipe pierces its slats. Their 9-inch-AFF outlets end over the grate at x=162 and x=160
inches, y=98 3/16 inches; keep these outlets visible when the service panel is lifted. Inset posts leave the west low exhaust `REG-B-EXH2` clear; keep its face, damper
access and flow path open. No fascia, bedding or stored items may obstruct this path.
`CO-B-SAUNA-HEAD` retains its drain fitting and has a rising extension to a flush aisle cap
at **(181, 60)**, with a vertical terminal below the flush cap. Its 18 × 18-inch access
square clears both platforms and the step. Coordinate this extension with the plumber before the slab pour. Include it in the joinery/service allowance.

There is **24½ inches** of floor aisle east of the step and **28 inches** east of the reading
platform, **10½ inches** from reading platform to heater, and **4 inches** between reading
platform and junction box. The box remains at 18–22 AFF; keep its cover/tool access open and
verify the actual installed box's service needs before making the deck.

The selected **US Harvia HPCS11U1H / PC110E 10.5 kW** manual Figure 5 requires 1.2 inches
side/back, 4 inches in front, 32.5 inches above and a minimum 78-inch room height. The modeled
heater has 2½ inches east, 3 inches south and **37 13/16 inches above**. The furniture clears
the conservative 4-inch horizontal limit. [Harvia's installation manual, §§3.2–3.3 and
Figure 5](https://www.kbauthority.com/files/PDF/Harvia/HPCS11U1H%20Manual%20Sheet.pdf)
also requires a wall-attached softwood heater fence below the rock line. Fabricate this with
the joinery: its nearest face must stay at least 4 inches from the heater front, and its
posts/rails must leave the low junction-box cover reachable. Fence connections, rock line,
actual delivered unit clearances and box access are installation checks; the seating symbol
is not a fabricated fence detail. Do not use another market's heater manual.

The new framing includes low perimeter mounting rails; both 24 V tape runs remain at
**16 AFF**, independent of the 24-inch deck tops. `LR-B-SAUNA-WEST` follows the foot deck;
`LR-B-SAUNA-SOUTH` follows the exposed reading-deck edges. Total **116 11/16 inches**
(9.724 ft) at 3 W/ft = **29.17 W**; 125% sizing load **36.46 W**, below the 48 W (80%) limit
of the existing 60 W external driver. Use the existing heat-rated tape and external driver/switch.

## Cost and acceptance

All six custom seating types have material/labor allowances in `prices.toml` and one takeoff
count apiece. Combined material/labor allowance: **$2,630–$8,350**. These are planning
ranges, not supplier quotes; obtain joinery/recliner/pad
quotes after the mock-up and heat qualification. The joinery scope includes service panels,
heater fence, mounting rails and coordinated cleanout-cap access. Drain piping and lighting
continue through their existing trade takeoffs; do not duplicate their complete installations.

Automated checks cover containment, fixture separation, finished headroom, occupied seat/leg
space, cleanout access, connected framing, clearance to the floor drain/exhaust/condensate, actual rail attachment,
driver capacity, placed section geometry and priced counts. These verify the coordinated
layout. The mattress qualification, one-hour mock-up and installed service-access review
remain required before fabrication.
