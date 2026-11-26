# Sauna seating — re-laid 2026-11-25 (issued 2026-10-11)

**2026-11-25 basement replan:** the sauna gave its north 2' to the bath (`RM-B-BATH`) and lost
its shower and tile splash. The old 78 × 28 bench, 20" foot deck, south reading platform and
their 4-seat arithmetic are retired. Two full-depth decks now run along the west wall. The
heater and window did not move. Dimensions are from finished liner faces, in inches;
elevations are above the basement finished slab. Resolved clear box x 122½–210, y 9¼–90¾
(`CLAUDE.md` says x from 121 5/8"; the resolved polygon starts at 122½"). The catalog is
`plan/sauna_types.py`, editable placements `plan/sauna.py`.

| Component | Length × depth | Top AFF | Resolved footprint (x; y) |
|---|---:|---:|---|
| Upper lying bench | 80 9/16 × 28 | 42 | 123¼–151¼; 10–90 9/16 |
| Lower deck | 80 9/16 × 28 | 24 | 151¼–179¼; 10–90 9/16 |
| Access step | 14 × 10 | 12 | 179¼–193¼; 68–78 |
| Recliner and bent pad envelope | 57½ × 26 | Deck mounted | 152¼–178¼; 10–67½ (lower deck, south end) |
| Reading platform (`FT-CATLIN-SAUNA-READING-58`) | 58½ × 28 | 24 | catalog only, 0 placed; `FURN-B-SAUNA-READING` retired |

Keep the upper **80 9/16 × 28** surface uninterrupted: a backrest cannot project into the
28-inch usable depth. The ceiling underside is `CEIL-RM-B-SAUNA.z0_m`, **84 1/16 AFF**,
leaving **42 1/16 inches** over the upper bench (raised 1" on 2026-11-01 to R305.1's 7'-0"
when the shower made the room a bathroom; the height stayed when the shower left). Older 90-inch, 18/36-inch and 78-inch notes are
superseded. The east aisle (x 179¼–210, 30¾") holds the step, floor drain and heater.

[Dimensioned occupancy review](assets/sauna_seating_review.svg) shows lounging and seated
adults, with seat and leg envelopes. **Design capacity is three seated.** With the recliner
and mattress lifted off, three sit on the upper bench, each with 26 inches of run and 18
inches of seat depth, feet on the 28-inch lower deck. A fourth fits only shoulder to
shoulder at ~20 inches each: not a design capacity. Lounging leaves a 26 × 68-inch lying
envelope on the upper bench (12 9/16" spare along its length), and the recliner is a separate
reading place on the lower deck.

## Reading fit and mattress qualification

The armless, removable recliner stands on the lower deck's south end, back north and feet
to the window, so the daylight is ahead of the reader. It supports itself on the deck; no
window/trim attachment. Drawn back angle is 110° from the seat, with positive locks targeted at
105°, 110° and 112°. The adjustment run stays inside the 57½-inch envelope (y 10–67½"). Rounded wood
slats support a 36-inch back, 22-inch seat and 22-inch leg section. The bent pad is mounted
on the same deck datum as the wood: its declared height is its bent envelope, not its
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
the upper bench. Provide removable deck stops/restraints within the reserved footprint
if the fit trial requires them; no wall or window attachment.
Reading takes priority over computing. No armrests are specified. This physical trial is
outstanding and cannot be replaced by the geometric model.

## Framing, service and heater installation

Use unfinished owner basswood slats on bought kiln-dried Douglas fir framing, eased edges, concealed suitable fasteners,
open posts and removable deck panels. Transverse bearers carry the long deck slats;
Deck-panel joints land on transverse bearers so the drain-side section can lift.
Connected stretchers carry the low perimeter lighting rails. Inclined side stringers
carry the recliner back slats into its rear uprights and base rails. Design framing/connections for three adults on the
upper bench and the lower deck carrying the recliner or the sitters' feet; symbol members are coordination geometry, not a structural
joinery certification. Secure the step against sliding/tipping. Mock up the 12/24/42-inch
access sequence, including the final 18-inch rise, while the upper bench is occupied. The step
stands beside the lower deck's free north 23 inches, past the recliner's head.

### Slat check (2026-10-20): 3/4" basswood on bearers at 16" o.c. or closer

The touched surfaces are the owner's clearest basswood, 4/4 dressed to **3/4" x 3 1/2"** (the
wall liner's stock, so the mill runs one basswood thickness), at 1/2" gaps; the bearers are
bought Douglas fir 2x4s, 1 1/2" x 3 1/2". **Bearers at 16" o.c. or closer is the rule** (the
cut lists in `plan/sauna_types.py`: 7 per deck, 2 on the step; since 2026-11-25 the deck
bearers sit at **13 7/16" o.c.**, 80 9/16" over six spaces, stiffer than the rule; was 5/4 to
1" at 24" until 2026-10-20). Take one 250 lb adult as ~85 lb on each of three slats at midspan:

| | L = 16" (the rule) | L = 24" (too far) |
|---|---|---|
| `S = b*d^2/6` (b 3.5", d 0.75") | 0.328 in^3 | 0.328 in^3 |
| `I = b*d^3/12` | 0.123 in^4 | 0.123 in^4 |
| `M = P*L/4` | 340 in-lb | 510 in-lb |
| `f = M/S` | **≈ 1,040 psi** (~8x on ~8,700 psi MOR) | ≈ 1,550 psi (~5.6x) |
| `d = P*L^3/(48*E*I)`, E ≈ 1.46 x 10^6 psi | **≈ 0.04"** | ≈ 0.14", springy |

At 16" the 3/4" slat is stiffer than the old 1" slat at 24" (0.06", 875 psi), at a still
ample ~8x on strength. Do not open the bearers back up to 24": basswood is soft, and a knee
or a foot stepping to the upper bench loads one or two slats, not three.

Posts, stretchers, the recliner and the heater fence are not designed yet (coordination geometry, above), so they
are carried as a bought Douglas fir allowance in `notes/wood_supply.md`, not as cuts.

The floor drain `FX-B-SAUNA-FD` (6 x 6, x 193-199, y 81-87) stands in the open east aisle, 3"
north of the step and 14" east of the lower deck, so the decks need no service panel over it.
`PR-B-COND` and `PR-B-COND-HP2-GYM` drop in `W-B-SA-N`'s 198 3/4"-211 3/4" bay (x=208") and end
in one 9-inch-AFF air gap over the grate at (196, 84); keep the grate and that outlet visible and
nothing stored in the aisle. Inset posts leave the west low exhaust `REG-B-EXH2` clear; keep its
face, damper access and flow path open. No fascia, bedding or stored items may obstruct this path.
The sauna drain's cleanout is no longer in the sauna: `CO-B-SAUNA-HEAD` is a floor cap in the
bath, 4" in front of the lav ((200 1/2, 122)), because the 3" branch's upper terminal now sits
under the bath's lav drop. The old aisle cap at (181, 60) and its rising extension are gone.

The aisle is **30 3/4 inches** (lower deck to east liner), **16 3/4 inches** east of the step,
**13 inches** from the lower deck to the heater and **6 1/2 inches** from the lower deck to the
junction box (`ED-B-SAUNA-JB`, x 185 3/4-191 3/4, y 9 1/4-15 1/4, on the south liner). The
recliner is 7 1/2 inches from the box. The box stays at 18-22 AFF; keep its cover/tool access
open and verify the actual installed box's service needs before making the deck.

The selected **US Harvia HPCS11U1H / PC110E 10.5 kW** manual Figure 5 requires 1.2 inches
side/back, 4 inches in front, 32.5 inches above and a minimum 78-inch room height. The modeled
heater (x 192 1/4-207 1/4, y 12 1/2-28 1/2, 45 in. tall, SE corner) has 2 3/4 inches east,
3 1/4 south and **39 1/16 inches above**. The furniture clears
the conservative 4-inch horizontal limit by 9 inches. [Harvia's installation manual, §§3.2–3.3 and
Figure 5](https://www.kbauthority.com/files/PDF/Harvia/HPCS11U1H%20Manual%20Sheet.pdf)
also requires a wall-attached softwood heater fence below the rock line. Fabricate this with
the joinery: its nearest face must stay at least 4 inches from the heater front, and its
posts/rails must leave the low junction-box cover reachable. Fence connections, rock line,
actual delivered unit clearances and box access are installation checks; the seating symbol
is not a fabricated fence detail. Do not use another market's heater manual.

The new framing includes a low mounting rail along the lower deck's east edge; both 24 V tape
runs remain at **16 AFF**, independent of the 24-inch deck tops. `LR-B-SAUNA-WEST` runs y 90 9/16
to 67 1/2, north of the recliner's head; `LR-B-SAUNA-SOUTH` y 67 1/2 to 10 beside the recliner;
one switch. Total **80 9/16 inches** (6.714 ft) at 3 W/ft = **20.14 W**; 125% sizing load
**25.2 W**, 42% of the 60 W external driver (`ED-B-SAUNA-LT-PSU`, on the workshop face of
`W-B-SA-W` since the bath took `W-B-SA-N`). Use the existing heat-rated tape and external
driver/switch.

## Cost and acceptance

All six custom seating types have material/labor allowances in `prices.toml`; five are placed,
one takeoff count apiece (the reading platform is priced but 0 ea). Combined allowance of the
five: **$2,330–$7,450** (was $2,630–$8,350 with the reading platform). These are planning
ranges, not supplier quotes; obtain joinery/recliner/pad
quotes after the mock-up and heat qualification. The joinery scope includes service panels,
heater fence, mounting rails and coordinated cleanout-cap access. Drain piping and lighting
continue through their existing trade takeoffs; do not duplicate their complete installations.

Automated checks cover containment, fixture separation, finished headroom, occupied seat/leg
space, cleanout access, connected framing, clearance to the floor drain/exhaust/condensate, actual rail attachment,
driver capacity, placed section geometry and priced counts. These verify the coordinated
layout. The mattress qualification, one-hour mock-up and installed service-access review
remain required before fabrication.
