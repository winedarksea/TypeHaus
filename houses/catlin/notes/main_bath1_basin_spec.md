# RM-M-BATH1 — wall basin and timber support

Current selection, 2026-10-21. Replaces the Vero 0703500008 hand-rinse basin.
The owner chose a roomier bowl and authorized the associated layout adjustments.

## Fixture and fittings

| Item | Specification |
|---|---|
| Basin | **Duravit D-Code 07054500002**, white ceramic, wall mounted, glazed underside, overflow, one factory-punched central faucet hole; cUPC listed |
| Overall | Published US footprint **17¾″ wide × 13⅜″ projection**; metric drawing 450 × 340 mm, china height 145 mm (US nominal 5¾″). Allow ceramic tolerances when setting out. |
| Usable bowl | Manufacturer's internal dimensions **15⅜″ × 8½″**. These are plan dimensions, not vertical water depth. The replaced Vero's bowl was 10⅝″ × 7⅛″. |
| Mounting height | **34″ rim above finished floor**. China underside 718.6 mm / 28.2913″ AFF; the model's additional 140 mm is the generic faucet symbol, not additional china. |
| Faucet | **Duravit B.2 S B21010001U10**, chrome, single lever, single hole, no cover plate; 4″ reach, 3⅝″ outlet height above deck, adjustable aerator, 3/8″ compression hoses, US pop-up/drain assembly; WaterSense and cUPC listed. This compact mixer replaces the Arvo selection in this room. |
| Waste | Included overflow-compatible pop-up; 1¼″ chrome-plated brass tubular P-trap with accessible cleanout/slip joints, code-compatible transition to the existing 1½″ wall arm. Exposed trap arm offsets east to the wall stub at x=51″; do not use a corrugated flexible waste. |
| Supplies | Accessible quarter-turn stops below the basin, hot at x=48″ and cold at x=56″; braided connectors sized to reach without tension. Cold branch passes on the bathroom side of the stack; the hot riser ends below the blocking. |

The bowl is wider and deeper in plan than the previous hand-rinse selection. Confirm
hand clearance and splash behavior with the actual basin and mixer before final drilling;
set the aerator into the bowl and check handle/pop-up operation against the finished wall.
This is a compact powder-room basin, with no claim of accessible knee clearance or a
load-rated transfer support.

## Blocking and fixing detail

`W-M-STOS` retains its existing thickness and location. Its local assembly
`INT_2X4_BASIN_SUPPORT` uses **2×4 studs at 8″ on center**, adding supports at x=40″
and 56″. The bathroom-facing finish remains in the same plane. Do not transfer the
prototype partition's tested acoustic rating to this altered stud layout.

Provide two **solid nominal 4×10 SPF blocks**, actual **3½″ thick × 9¼″ high**,
fitted between the full-height studs and flush with their faces:

| Model element | Horizontal extent, from the west wall axis | Bottom / top above main storey datum |
|---|---|---|
| `BK-M-STOS-BASIN` | x=40¾″ to 47¼″; cut length 6½″ | 28½″ / 37¾″ |
| `BK-M-STOS-BASIN-R` | x=48¾″ to 55¼″; cut length 6½″ | 28½″ / 37¾″ |

Fasten **each block end with three 16d common nails, 0.162″ × 3½″**, face-nailed
through the adjacent stud into the block before closing the wall; stagger the nails
vertically. Secure the full-height support studs to the sole and top plates using the
partition framing schedule. The block-to-stud connections are part of the installation,
not a loose noggin held by drywall.

The basin center is **x=48⅞″**. Manufacturer drawing `1266560` gives fixing holes
**240 mm apart and 55 mm below the rim**. Set the two mounting axes at approximately:

- **x=44.151″ and 53.599″**, both within their solid blocking targets.
- **31.835″ AFF** vertically. With the current 0.9862″ finished-floor build-up, this
  is **32.821″ above the main storey datum**. Recalculate from actual finished floor
  if that build-up changes; backing elevations and fixture heights use different datums.

Use two **M10 through-bolts**, zinc plated, with **2″ square × ⅛″ steel backing
washers/plates** at the closet side of the timber and ceramic-compatible nylon shoulder
bushes, washers and nuts at the basin. Select bolt length from the actual ceramic and
finish build-up (nominal M10 × 160 mm), with full nut engagement. Recess the rear head
and plate only enough to keep the closet lining flush. Dry-fit the supplied ceramic
bushes and confirm the through-bolt arrangement with Duravit's installation requirements.
Tighten evenly by hand; do not load bare ceramic with a steel nut or impact driver.

Photograph both blocks, fastenings and service routes before wall closure. The solid
blocks stop at x=55¼″, **west of the 3″ stack at x=60″**. Do not notch them for that
stack, bore a fixing into a pipe, use gypsum anchors, or substitute a thin plywood strip.
The supply stubs and waste arm are below the blocks. Prebore a 2″ vertical service hole
through the right block at x=51″ for the 1½″ PVC vent (1.9″ actual OD), centered in
the 3½″ wall depth. Keep this bore separate from the right fixing at x=53.599″ and its
2″ backing plate; do not enlarge or slot the hole. The vent remains vertical until
above the basin flood rim.

## Layout effect

The AP toilet moves **1¾″ west**, with its carrier following and an above-floor offset to the existing drain drop, so the deeper
basin stays outside the toilet's required clearance. The 30″ modeled outswing moves
**2″ south**. Finished basin aisle is **32.365″**; the basin trims **¼″** from the
north end of the modeled doorway, leaving **29¾″ geometrically aligned** before
jambs, stops and the door leaf. Toilet front clearance remains **24.49″**.
No further northward partition move is needed. This does not establish wheelchair access.

## Manufacturer references

- [Duravit US D-Code 070545](https://pro.duravit.us/pro/html/default/402880943a1b6e1b013a1bd282eb0051.us-en.html?ncat=washbasins&nser=7120&product=94764)
- [Manufacturer plan drawing 1266559](https://csassets.duravit.com/1/2/Duravit_TD_1266559.pdf)
- [Manufacturer fixing/elevation drawing 1266560](https://csassets.duravit.com/1/2/Duravit_TD_1266560.pdf)
- [Duravit US B.2 S mixer B21010001U10](https://pro.duravit.us/pro/html/default/402880943a1b6e1b013a1bd282eb0051.us-en.html?ncat=faucets&nser=1821&product=4147387)

Copies of both manufacturer drawings are in `notes/assets/`. Field setting-out follows
the actual supplied china, not a scaled print or the generic model symbol.
