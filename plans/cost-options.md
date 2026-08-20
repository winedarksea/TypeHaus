# Cost options — priced upgrades and downgrades

Started 2026-08-08. A running list of swaps we could make **if the number comes in tight**,
each with the line it actually moves in `houses/catlin/prices.toml`, so a decision is a
decision about dollars rather than about taste.

Rules for this file:

- Every row cites the estimate line it changes and the delta at both ends of the range.
  A swap with no number in it does not belong here yet — it belongs in TODO.md's
  "Potential cost cutting" list until someone prices it.
- **Nothing here is decided.** The plan as authored is the plan. This is the menu.
- Deltas are against the estimate current when the row was written. **Read the baseline
  note below before comparing any two rows** — the baseline has moved twice, and neither
  move was the house changing.
- **The tree moved on 2026-08-18.** `concrete:slab` was pricing the suspended main-floor
  deck at the slab-on-grade rate; giving it its own key took the construction total from
  $274,206 – $562,712 to $307,330 – $627,774.
- **The tree moved much further on 2026-08-20, and this is the important one.** Research
  pass 4 added LABOUR to the file. Before it, 21 of 24 sections were material-only and the
  estimate reported **$0 of labour**; the total was $306,982 – $627,214. After it:

  | | before | after |
  |---|---|---|
  | construction total | $306,982 – $627,214 | **$574,980 – $1,135,114** |
  | material | $218,600 – $460,708 | $241,513 – $491,416 |
  | labour | **$0** | **$211,280 – $421,533** |
  | merged (installed, unsplit) | $88,381 – $166,506 | $122,188 – $222,165 |
  | $/gross sf | $51 – $104 | **$96 – $189** |
  | unpriced rows | 54 | 37, and all 37 are documented mirrors |

  **No geometry moved.** That is labour that was always going to be paid, plus material
  corrections in both directions, arriving in the file. Every row below dated before
  2026-08-20 is measured against a material-only baseline and its *proportion* of the total
  is now roughly half what the row says, even where its dollars are unchanged.
- **And it moved a third time, later on 2026-08-20 — this is the one to quote.** The
  allowance register at the end of this file was authored into `prices.toml`, and three of the
  four bid-ladder stages were turned on. Nothing in the house changed; the estimate stopped
  omitting the excavator.

  | | resolved quantities only | with allowances and the ladder |
  |---|---|---|
  | subtotal_net | $576,557 – $1,139,150 | **$840,047 – $1,776,100** |
  | + waste, contingency, tax | — | $138,899 – $285,352 |
  | **total** | $576,557 – $1,139,150 | **$978,947 – $2,061,452** |
  | $/gross sf | $96 – $189 | **$163 – $343** |
  | unpriced rows | 0 actionable | 0 actionable |

  Four owner decisions the same day took **$64,782** off that high end: wire closet shelving
  rather than a laminate system (−$35,000), a summer pour (−$21,000), the code-minimum ice
  barrier confirmed as base scope, and suburban Hennepin's 8.525% tax rather than the city's
  9.025% (−$3,182).

  `[markup]` — the general contractor's overhead and profit, roughly $130,000 – $375,000 — is
  **off by choice** and present at zero. Add it for a GC-contracted number.
- **A delta below is still measured against the section it names, not against the total.**
  Turning the ladder on multiplies every one of them by roughly 1.20 on the way to the bottom
  line (waste, then 10% contingency, then material tax), and by ~1.40 if markup is switched on.
  A $10,000 saving in `[envelope_layers]` is about $12,000 off the printed total today.
- **Rows are now material+labour unless they say otherwise**, so a delta here is much closer
  to what a bid moves than it used to be. It is still not a bid.
- A swap that changes what the house *does* — not just what it costs — says so under
  **Cost of the cut**. Those are not free money.

## Downgrades (money back)

### Standing-seam metal roof → architectural asphalt shingle
`envelope_layers:standing-seam`, 6,322 SF over two rows — **$60,064 – $116,966 → roughly
$34,800 – $56,900. Saves ~$25,000 – $60,000.**

Researched 2026-08-20, and with labour in the file this is now **the largest single lever on
the list by a wide margin** — bigger than the basement deck. It was in "Not yet priced" until
this pass; it is priced now.

Standing seam is $12 – $22/SF installed in Minnesota, and the split is **60 – 70% labour**,
which is why adding labour tripled this line rather than doubling it: panels are often
roll-formed on site, every clip is placed individually, and the seams are mechanically
crimped in a separate pass. Architectural asphalt is the opposite — a fast, deeply
competitive trade with far more crews bidding it.

| | standing seam | architectural asphalt |
|---|---|---|
| material | $3.50 – $7.50/SF | $1.50 – $3.00/SF |
| labour | $6.00 – $11.00/SF | $3.50 – $6.00/SF |
| installed | **$9.50 – $18.50/SF** | **$5.00 – $9.00/SF** |
| 6,322 SF | **$60,064 – $116,966** | **$31,600 – $56,900** |

**Three things that move with it and are not in the table:**
- **The snow-retention hardware goes away.** `hardware:S-5!`, `S-5! ColorGard`, `S-5! CanDuit`
  and `SS-GASKET-12` are all seam-clamp products that only exist because the roof has seams —
  roughly **$1,000 – $2,200** of the hardware section. Asphalt needs pad-style guards instead
  if it needs any, which is cheaper but not free.
- **`edge_trim:ridge_cap` and `edge_cladding` change product**, from formed metal to shingle
  ridge. Shingle ridge is $1.50 – $3.50/LF to lay against $4 – $8 for metal.
- **The PV mounting method changes.** `hardware:S-5-PVKIT` (48 ea) is a *seam* clamp: it
  attaches to standing seam without a single penetration. On asphalt the array needs
  flashed penetrating feet, which is more hardware, more labour and 48 more holes in the roof.
  This is the strongest single argument for keeping the metal.

**Cost of the cut:** service life, most obviously — 50+ years against 25 – 30, on a roof
that is also the solar substrate, so the reroof and the array's service life stop being
independent decisions. Then the architecture: this is a metal-clad house whose walls and
roof are the same material and whose edge details are all formed metal. Shingling the roof
alone would break that, and shingling the walls is not an option. If the metal roof goes,
the elevations want revisiting, which is not a $/SF question.

### Basement ceiling: 9" suspended concrete deck → 11-7/8" I-joists at 16" o.c.
`concrete:slab:CATLIN_DECK_9_INT`, 34.26 cy / 1,233 SF — **$31,862 – $60,298 today.**
Still the second-largest structural swap on the list. **The full entry is below under its
2026-08-18 heading and its numbers still stand**, with two 2026-08-20 amendments:

- **The low end of the concrete side is not obtainable, for a reason the old entry only
  guessed at.** A Twin Cities sub that owns deck shoring is a *commercial* contractor, and the
  derived mobilisation floor for bringing shoring, forms, a rebar crew and a finishing crew to
  a one-off residential site is **$25,000 – $40,000** — which over 1,233 SF is $20 – $32/SF.
  The old $25.68/SF low sat *inside* that floor. `prices.toml` now carries $30.56 – $58.33/SF;
  treat ~$30/SF as the practical floor and expect real bids clustered at **$40 – $55/SF**.
- **The joist side gains labour too**, so the saving does not grow as much as the concrete
  line did. Both columns move; the gap widens, but by less than the headline suggests.

### Elm tudor posts → a paint- or stain-grade species
`concrete:column:ELM_TIMBER`, 4 posts / 40 LF — **$2,006 – $6,001 → roughly $700 – $1,500.
Saves ~$1,300 – $4,500.**

Researched 2026-08-20. The cost here is not the wood, it is that **a 6-1/8" square S4S elm
timber does not exist as a purchasable article**. Nothing thicker than 12/4 is on any Twin
Cities urban-salvage price list, elm has interlocked grain that twists and checks badly in
thick sections, and the technically correct way to get a stable post is a glued-up blank from
8/4 kiln-dried stock — which is millwork shop time, not lumber. You also lose ~30% of the
board footage getting from a 7×7 rough blank to a 6-1/8" finished face.

In Douglas fir, poplar or paint-grade SPF the same four posts are a lumberyard purchase.

**Cost of the cut:** these are the suite's tudor posts and elm is the whole point of them —
it is a local salvage story (Dutch elm removals) in a visible interior position. This is a
character cut, not a performance cut. **Before cutting it, get the actual quote:** one call
to Wood From The Hood or Siwek Millwork would replace the widest range in `prices.toml` with
a number, and the low end of that range is only $2,006.

### Aluminium balcony deck → composite plank over a membrane
`concrete:slab:BALCONY_DECK_ALUMINUM`, 181 SF — **$5,838 – $10,290 → roughly $2,000 – $3,600.
Saves ~$3,800 – $6,700.**

Interlocking waterproof aluminium plank (Wahoo AridDek, Nexan LockDry, Versadeck Versadry)
is sold as a **dry-below roof-deck assembly**, not as decking, which is why it is 3 – 4x a
composite board. It is also entirely quote-only — no dealer, no e-commerce, no forum post
with a transacted number anywhere — so this is the least certain large line in the file.

**Cost of the cut:** the space under the balcony stops being dry. If nothing lives under
there, this is close to free money. If it shelters the porch below, the membrane-and-composite
alternative has to do the same job with a hidden membrane, and hidden membranes over occupied
space are exactly where balconies fail.

**Do this first:** Versadeck's sales line is a Twin Cities number, **(651) 356-1870**. One
call turns the weakest row in `prices.toml` into a real one and may make the swap unnecessary.

### Fabricated box gutter → seamless K-style throughout
`drainage:gutter`, the 73.7 LF dark box run — **$1,179 – $2,506 → roughly $600 – $1,100.
Saves ~$600 – $1,400.** Plus the conductor heads a box gutter generally needs ($150 – $400
each), which are not in the estimate at all.

Box gutter is ~3x K-style in labour and ~2.5x in material: heavier prefinished gauge, shop
mitres, sealed splices, and it must be set to a true line because a box profile shows every
wave. Seamless K-style is roll-formed on site off a coil truck.

**Cost of the cut:** the box profile is a deliberate edge detail on a house whose whole
edge language is formed metal. It reads very differently from a K-style ogee.

### Trimless interior door → a standard cased prehung
`openings:DT-INT-SWING30-TRIMLESS`, 1 ea — **$1,220 – $2,800 → $305 – $755. Saves
~$915 – $2,045**, and removes a schedule risk worth more than the money.

The 2026-08-20 pass found this to be the most under-priced line in the openings table. A
hidden-jamb reveal door is not a carpentry item, it is a **three-trade sequencing item**: the
frame is set dead plumb *before* drywall, the rock is terminated into it with reveal bead, and
the reveal takes a Level-5 finish with zero tolerance for later movement. $75 – $200 of its
labour lands on the drywall sub, and drywall subs commonly exclude cracking at the reveal from
their warranty.

**Cost of the cut:** one detail in one doorway. This is the cheapest quality-per-dollar
decision on the list to reverse later — except that you cannot reverse it later, because the
frame has to go in before the drywall.

### Standing-seam metal roof → architectural asphalt shingle
`envelope_layers:standing-seam`, 6,322 SF over two rows — **$60,064 – $116,966 → roughly
$34,800 – $56,900. Saves ~$25,000 – $60,000.**

Researched 2026-08-20, and with labour in the file this is now **the largest single lever on
the list by a wide margin** — bigger than the basement deck. It was in "Not yet priced" until
this pass; it is priced now.

Standing seam is $12 – $22/SF installed in Minnesota, and the split is **60 – 70% labour**,
which is why adding labour tripled this line rather than doubling it: panels are often
roll-formed on site, every clip is placed individually, and the seams are mechanically
crimped in a separate pass. Architectural asphalt is the opposite — a fast, deeply
competitive trade with far more crews bidding it.

| | standing seam | architectural asphalt |
|---|---|---|
| material | $3.50 – $7.50/SF | $1.50 – $3.00/SF |
| labour | $6.00 – $11.00/SF | $3.50 – $6.00/SF |
| installed | **$9.50 – $18.50/SF** | **$5.00 – $9.00/SF** |
| 6,322 SF | **$60,064 – $116,966** | **$31,600 – $56,900** |

**Three things that move with it and are not in the table:**
- **The snow-retention hardware goes away.** `hardware:S-5!`, `S-5! ColorGard`, `S-5! CanDuit`
  and `SS-GASKET-12` are all seam-clamp products that only exist because the roof has seams —
  roughly **$1,000 – $2,200** of the hardware section. Asphalt needs pad-style guards instead
  if it needs any, which is cheaper but not free.
- **`edge_trim:ridge_cap` and `edge_cladding` change product**, from formed metal to shingle
  ridge. Shingle ridge is $1.50 – $3.50/LF to lay against $4 – $8 for metal.
- **The PV mounting method changes.** `hardware:S-5-PVKIT` (48 ea) is a *seam* clamp: it
  attaches to standing seam without a single penetration. On asphalt the array needs
  flashed penetrating feet, which is more hardware, more labour and 48 more holes in the roof.
  This is the strongest single argument for keeping the metal.

**Cost of the cut:** service life, most obviously — 50+ years against 25 – 30, on a roof
that is also the solar substrate, so the reroof and the array's service life stop being
independent decisions. Then the architecture: this is a metal-clad house whose walls and
roof are the same material and whose edge details are all formed metal. Shingling the roof
alone would break that, and shingling the walls is not an option. If the metal roof goes,
the elevations want revisiting, which is not a $/SF question.

### Basement ceiling: 9" suspended concrete deck → 11-7/8" I-joists at 16" o.c.
`concrete:slab:CATLIN_DECK_9_INT`, 34.26 cy / 1,233 SF — **$31,862 – $60,298 today.**
Still the second-largest structural swap on the list. **The full entry is below under its
2026-08-18 heading and its numbers still stand**, with two 2026-08-20 amendments:

- **The low end of the concrete side is not obtainable, for a reason the old entry only
  guessed at.** A Twin Cities sub that owns deck shoring is a *commercial* contractor, and the
  derived mobilisation floor for bringing shoring, forms, a rebar crew and a finishing crew to
  a one-off residential site is **$25,000 – $40,000** — which over 1,233 SF is $20 – $32/SF.
  The old $25.68/SF low sat *inside* that floor. `prices.toml` now carries $30.56 – $58.33/SF;
  treat ~$30/SF as the practical floor and expect real bids clustered at **$40 – $55/SF**.
- **The joist side gains labour too**, so the saving does not grow as much as the concrete
  line did. Both columns move; the gap widens, but by less than the headline suggests.

### Elm tudor posts → a paint- or stain-grade species
`concrete:column:ELM_TIMBER`, 4 posts / 40 LF — **$2,006 – $6,001 → roughly $700 – $1,500.
Saves ~$1,300 – $4,500.**

Researched 2026-08-20. The cost here is not the wood, it is that **a 6-1/8" square S4S elm
timber does not exist as a purchasable article**. Nothing thicker than 12/4 is on any Twin
Cities urban-salvage price list, elm has interlocked grain that twists and checks badly in
thick sections, and the technically correct way to get a stable post is a glued-up blank from
8/4 kiln-dried stock — which is millwork shop time, not lumber. You also lose ~30% of the
board footage getting from a 7×7 rough blank to a 6-1/8" finished face.

In Douglas fir, poplar or paint-grade SPF the same four posts are a lumberyard purchase.

**Cost of the cut:** these are the suite's tudor posts and elm is the whole point of them —
it is a local salvage story (Dutch elm removals) in a visible interior position. This is a
character cut, not a performance cut. **Before cutting it, get the actual quote:** one call
to Wood From The Hood or Siwek Millwork would replace the widest range in `prices.toml` with
a number, and the low end of that range is only $2,006.

### Aluminium balcony deck → composite plank over a membrane
`concrete:slab:BALCONY_DECK_ALUMINUM`, 181 SF — **$5,838 – $10,290 → roughly $2,000 – $3,600.
Saves ~$3,800 – $6,700.**

Interlocking waterproof aluminium plank (Wahoo AridDek, Nexan LockDry, Versadeck Versadry)
is sold as a **dry-below roof-deck assembly**, not as decking, which is why it is 3 – 4x a
composite board. It is also entirely quote-only — no dealer, no e-commerce, no forum post
with a transacted number anywhere — so this is the least certain large line in the file.

**Cost of the cut:** the space under the balcony stops being dry. If nothing lives under
there, this is close to free money. If it shelters the porch below, the membrane-and-composite
alternative has to do the same job with a hidden membrane, and hidden membranes over occupied
space are exactly where balconies fail.

**Do this first:** Versadeck's sales line is a Twin Cities number, **(651) 356-1870**. One
call turns the weakest row in `prices.toml` into a real one and may make the swap unnecessary.

### Fabricated box gutter → seamless K-style throughout
`drainage:gutter`, the 73.7 LF dark box run — **$1,179 – $2,506 → roughly $600 – $1,100.
Saves ~$600 – $1,400.** Plus the conductor heads a box gutter generally needs ($150 – $400
each), which are not in the estimate at all.

Box gutter is ~3x K-style in labour and ~2.5x in material: heavier prefinished gauge, shop
mitres, sealed splices, and it must be set to a true line because a box profile shows every
wave. Seamless K-style is roll-formed on site off a coil truck.

**Cost of the cut:** the box profile is a deliberate edge detail on a house whose whole
edge language is formed metal. It reads very differently from a K-style ogee.

### Trimless interior door → a standard cased prehung
`openings:DT-INT-SWING30-TRIMLESS`, 1 ea — **$1,220 – $2,800 → $305 – $755. Saves
~$915 – $2,045**, and removes a schedule risk worth more than the money.

The 2026-08-20 pass found this to be the most under-priced line in the openings table. A
hidden-jamb reveal door is not a carpentry item, it is a **three-trade sequencing item**: the
frame is set dead plumb *before* drywall, the rock is terminated into it with reveal bead, and
the reveal takes a Level-5 finish with zero tolerance for later movement. $75 – $200 of its
labour lands on the drywall sub, and drywall subs commonly exclude cracking at the reveal from
their warranty.

**Cost of the cut:** one detail in one doorway. This is the cheapest quality-per-dollar
decision on the list to reverse later — except that you cannot reverse it later, because the
frame has to go in before the drywall.

### Post bases: ABU66SS stainless → ABU66Z/RZ ZMAX galvanized
`hardware:ABU66SS`, 10 ea — **$1,500 – $2,300 → ~$550. Saves ~$950 – $1,750.**

Confirmed 2026-08-08 as genuinely stainless because the posts are exposed outdoors, and
kept for now. ZMAX is the standard exterior answer and is fine in most exposed locations;
stainless is what you buy for splash zones, coastal air, and pressure-treated contact you
expect to stay wet.

**Cost of the cut:** service life at the one detail nobody re-does without jacking the
structure. This is the wrong $1,000 to save unless everything else has already been cut.

### Basement ceiling: 9" suspended concrete deck → 11-7/8" I-joists at 16" o.c.
`concrete:slab:CATLIN_DECK_9_INT`, 34.26 cy / 1,233 SF, plus the main floor's finish —
**point estimate ~$21,300 saved, likely $16,100 – $27,700.**

Researched 2026-08-18. The largest single downgrade on this list by a factor of four, and
the only one that changes the structural system rather than a product selection.

| | concrete deck | I-joist floor |
|---|---|---|
| structure, all-in installed | $31,862 – $60,298 (~$26 – $49/SF) | $13,045 – $25,819 ($10.58 – $20.94/SF) |
| main-floor finish, 996 SF | sealer $996 – $2,989 | LVP $3,487 – $9,963 |
| **total** | **$32,858 – $63,287** | **$16,532 – $35,782** |
| point estimate | $46,381 ($36/SF deck, $2 sealer) | $25,089 ($15.50/SF system, $6 LVP) |

**Why the concrete number is so much larger than the estimate used to say.** Until today
`concrete:slab` priced this deck at $175 – $280/cy — the slab-on-grade rate, which is
ready-mix plus placement and nothing else. SL-M-DECK is not poured on the ground. It is
cast 9'-0" in the air and carries formwork, ~10' shoring on a one-month rental minimum
(ACI 347 keeps the shores until strength is verified), 2.0 – 2.7 tons of reinforcing, a
boom pump, a polish-ready trowel finish, a small-job/commercial-sub mobilization premium,
and a structural engineer's stamp. The old rate worked out to $4.86 – $7.78/SF for a
suspended structural deck against a published range of $20 – $40 and $25 – $50/SF. It was
low by 3-5x. The joist side needs none of that: the layout comes free with the EWP package
from the supplier, and there is no formwork, no shoring, no cure and no crane.

**The three bearing lines already exist.** `W-B-CN` / `W-B-CS` / `W-B-CS2` at x=18' plus the
east and west foundation walls are what the concrete deck bears on now, so the joists bear
on the same lines at the same 18' clear span the second and attic floors already run. This
is a like-for-like swap of FS-SECOND onto the basement, not a new structural scheme.

**Spec note, and it matters.** At 11-7/8" and 16" o.c. over 18'-0" clear, a **TJI 110 fails
outright** — 17'-8" max, short of the span even at code's L/360. **TJI 210 is the minimum
that works** (19'-3" at L/480). Spec the **230** anyway: it is ~$650 more over this deck and
buys real margin on a floor with finished rooms below. Do not let a supplier value-engineer
this to a 110.

**Two things that are NOT extra cost, and are commonly over-budgeted:**
- *Fire protection.* IRC/MN R501.3 wants a 1/2" gypsum membrane under I-joists. The 5/8"
  basement ceiling in the build-up above already exceeds it by a thickness step. No Flak
  Jacket, no intumescent coating, **$0**.
- *Bridging.* Weyerhaeuser: "TJI joist floor framing does not require bridging or mid-span
  blocking." Web stiffeners are not triggered at this span either. **$0.**

**What the range means.** The two ends are like-for-like — both options lean, then both
options rich. The full envelope is −$3,100 (the swap costs slightly *more*) to $46,900, but
the losing end needs the concrete to land at $25.68/SF *and* the joist floor to take union
labor, TJI-brand stock, sound batts and resilient channel all at once. The concrete low end
is the shakier of the two: most residential concrete subs will not bid a suspended deck at
all, and a commercial sub's job minimum is in the $25k – $50k range, so $32,660 may simply
not be obtainable. Treat the downside as unlikely and the upside as real.

**Sensitivity — polish, not sealer.** The table prices the concrete floor as a penetrating
densifier/sealer on the trowel finish ($1 – $3/SF), which is what `floor_finishes`
`sealed-concrete` actually is. If the intent was ever a genuinely *polished* floor, that is
a separate specialty contract at $4 – $8/SF for a Level 1-2 finish on a job this small, and
the saving grows by a further **$3,000 – $5,000**.

**Not priced, and a real further upside:** the deck is 112.5 psf of dead load before live
load. Losing it may let the foundation walls and footings shed reinforcement. Nobody has
asked the engineer, so it is not in the number.

**Cost of the cut** — this is the row with the most non-dollar consequence on the list:
- **Acoustics.** A 9" slab between the basement and the main floor is a level of impact and
  airborne isolation a wood floor does not reach. The $0 – $2,950 of batts and resilient
  channel at the high end of the joist column narrows the gap and does not close it.
- **Thermal mass.** 34 cy of concrete inside the thermal envelope, under the south glazing
  the whole facade is composed around. Deleting it changes how the house rides a sunny
  January day, and no line in prices.toml sees that.
- **Basement head height.** 9'-0" floor-to-floor less a 9" deck is 8'-3" clear today. Less
  11-7/8" of joist, 3/4" of subfloor and 5/8" of ceiling it is **7'-10 3/4"** — 5 1/4" gone.
  Still well over R305.1's minimum, and the duct soffits that a joist bay would make
  unnecessary are deliberately *not* credited here, so the real loss under the ducts is
  smaller than this. But the general ceiling does drop.
- **The in-slab radiant embed.** `FH-M-DINING` (232 LF) and `FH-M-BATH2` (37 LF) carry
  `embed=in_slab(0.5)`. There is no slab to embed in; both become mat-under-LVP and have to
  be re-authored. Roughly a wash in dollars.
- **The sauna liner extent comes off.** `assemblies.py` already anticipates this in prose:
  `_SAUNA_CEILING_EXTENT` bounds the liner at WALL_TOP − 1'-6" and says "if the basement
  ever goes to a joist ceiling running the full width, the liner would run the wall's whole
  height and this extent should come back off."

### Exterior guards: Trex Signature → builder-grade aluminium
`railings:RAILING-EXT-ALUMINUM-FASCIA`, 74.6 LF — **$2,835 – $5,222 → ~$1,492 – $2,611 at
$20-35/LF. Saves ~$1,343 – $2,611.**

Twice the run it was written against: since 2026-08-18 this line carries both the balcony
guard (38.3 LF) and RL-SG-PORCH (36.3 LF), which replaced the porch's masonry parapet. They
are the same product and would be downgraded together, or the two levels stop matching.

**Cost of the cut:** these are the guards you see from the sunken garden, from both levels
at once now, and the powder-coat finish is most of what you are buying.

### Basement brick veneer: delete
`wall_structure:BASEMENT_BRICK_VENEER`, 1.37 cy — **$1,233 – $2,603.**

**Cost of the cut:** the one masonry note on the basement wall.

### Stair treads: red oak → carpet on all three flights
`framing:deck 11x1.5` + `tapered tread` + `deck 44.625x1.5` — **$2,668 – $5,544 → roughly
$1,200 – $2,800. Saves ~$1,400 – $2,700.**

The basement flight (ST-B2M) is already carpet by decision. Extending that to ST-M2S and
ST-S2A is the cheapest finish change in the house per dollar.

**Cost of the cut:** oak treads are a main-stair item you look at every day.

### Garage: rainscreen-drop downgrade (superseded below if full ICF is taken)
Remove rain screen from cladding (snap lock directly to Zip-R)
Use snap lock rather than mechanically seamed standing seam for the roof of garage (house roof must remain mechanically seamed)

This is a downgrade of the *current* wood-wall assembly (drops the 0.375" 1x4 rainscreen
furring under `GARAGE_WALL_2X6`'s standing-seam cladding). It is moot under the full-ICF
upgrade below — an ICF wall has no furring layer to remove, and the wall cladding changes
to stucco anyway. The garage roof's snap-lock-vs-mechanically-seamed question is unaffected
either way and remains open.

### System 3: Gree Sapphire → Vireo/Livo single-zone
`placeables:EQ-T-GREE-SAPPHIRE-9` + `-OD` — **$2,600 – $3,450 → ~$1,600 – $2,200. Saves
~$1,000 – $1,250.**

**Cost of the cut:** real, and structural. The Sapphire is on this circuit *because* its
true VFD inverter soft-starts, which is what lets it run off the battery — a hard-starting
compressor is what a battery inverter cannot carry (see plan/electrical.py). Swapping it
means giving up backup heat on that zone, or resizing the inverter. Do not treat this as a
like-for-like $1,000.

## Taken

### Sunken-garden arch → column, beams and a metal railing — **done 2026-08-18**
Measured against the tree immediately before the change, not estimated:
**$282,561 – $580,402 → $277,166 – $569,145. Saved $5,395 – $11,257.**

| line | before | after |
|---|---|---|
| `wall_structure` | $47,822 – $94,192 | $43,630 – $85,180 (**−$4,191 – −$9,012**) |
| `envelope_layers` | $56,568 – $116,051 | $55,497 – $113,843 (**−$1,070 – −$2,208**) |
| `footing_bedding` | $4,435 – $8,387 | $3,670 – $6,944 (**−$764 – −$1,443**) |
| `concrete` | $19,974 – $32,346 | $19,233 – $31,181 (**−$741 – −$1,166**) |
| `railings` | $3,125 – $6,551 | $4,505 – $9,092 (**+$1,379 – +$2,541**) |
| `hardware` | $8,606 – $15,454 | $8,598 – $15,485 (−$8 – +$31) |

The `wall_structure` line is exactly the $4,191 – $9,012 this row was written against —
`SUNKEN_GARDEN_ARCH_16` (3.31 cy) and `PORCH_RAILING_MASONRY` (3.15 cy) both deleted. The
rest was not in the original estimate and is why the real saving is a third larger again:
`FT-SG-ARCH` and its 42" aggregate bed went with the wall it carried, and the parapet took
its brick/CMU/stucco face area out of `envelope_layers`.

What was bought back: `RL-SG-PORCH`, 36.3 LF of the same fascia-mount guard as the balcony,
which is the whole `railings` increase; `PT-SG-FCOL` (0.53 cy) and its footing;
`BM-SG-FRW`/`FRE`; and about 17 LF of extra 6x6, because five of the six balcony pillars now
start at a concrete wall top or the decking rather than 42" up on masonry.

Curved formwork was the expensive part, as this row predicted — the yard of concrete was
always the cheap part.

## Upgrades (money out)

### Breezeway glazing: 16mm polycarbonate → aluminium storefront with insulated glass
`concrete:glazing:BREEZEWAY_GLAZED_WALL`, 79.2 SF — **$1,424 – $3,168 → $8,100 – $16,455.
Costs ~$6,700 – $13,300.**

Worth stating plainly because it is easy to misread the estimate: **the breezeway is not
glazed in glass today.** `assemblies.py:358-378` is a single 0.63" layer of 16mm 5-wall
polycarbonate standing in a U-channel at the deck and an F-channel at the beam, with the 6x6
posts either end as the frame. There is no glass, no frame and no thermal break in the model.

The upgrade is dominated by a fixed cost that does not scale down: **mobilisation, shop
drawings and a glazier's minimum are $1,500 – $3,500 of it**, and the same assembly at
1,000+ SF prices at $60 – $95/SF against $103 – $208/SF here. A 79 SF job also cannot be
bought from a fabricator directly — Viracon and its peers will not quote it — so it routes
through a glazier buying IGUs from a smaller shop.

**What you get:** the breezeway is deliberately unheated and uninsulated, so this buys
appearance, acoustics and durability, not performance. **What you lose:** multiwall polycarb
is opal and diffusing, which is a genuinely different quality of light from clear glass, and
it is far less bird-hazardous — the assembly already specifies bird-safety film, and clear
glass in a breezeway between two buildings is close to a worst case for bird strikes.

### Breezeway roof: polycarbonate panel → a stock fixed skylight
`concrete:glazing:BREEZEWAY_ROOF_GLAZING`, 16 SF — **$480 – $960 → $1,430 – $3,185.
Costs ~$950 – $2,225.**

A Velux FCM 4646 (~15 SF, the right size) is $408 – $700 with an ECL curb-mount flashing kit
at $118 – $185, plus curb framing and a roofer to set and tie in. Real published dealer
pricing, unlike almost everything else in the breezeway.

**Do not confuse this with custom sloped glazing.** A one-off sloped unit with a laminated
inboard lite is $200 – $480/SF — 2 – 4x a stock Velux for the same aperture, because
engineering and mobilisation do not shrink. If the opening is genuinely a 16 SF square, the
stock skylight is the defensible choice and the custom unit is not an upgrade, it is a
purchase of the word "custom".

### Roof: eave-and-valley ice barrier → full-deck high-temp ice & water
**$5,000 – $11,000 → $17,400 – $38,300. Costs ~$12,400 – $27,300.**

**Neither option is in the estimate today** — see the missing-scope register below; the roof
is priced as bare panel with no underlayment at all, so this is an upgrade *from a hole*.

Minnesota code requires an ice barrier from the eave edge to 24" inside the exterior wall
line, which is the ~2,000 SF option. But **standing seam wants high-temp ice-and-water over
the entire deck** as standard practice — metal runs hotter than shingle and a standard
membrane can soften and telegraph. If the metal roof is kept, budget the full-deck number and
treat the eaves-only figure as the code floor rather than the specification.

### Main-floor concrete: sealer → genuine polish
`floor_finishes:sealed-concrete`, 1,155 SF — **$1,270 – $3,696 → roughly $4,600 – $8,100.
Costs ~$3,300 – $4,400.**

The line prices a penetrating densifier and two coats of sealer on the trowel finish, which
is what `sealed-concrete` is. A genuinely *polished* floor is a separate specialty contract
at $3 – $7/SF more for a Level 1-2 finish on a job this small. Noted here as an upgrade
because the reverse — assuming the estimate already buys a polished floor — is the mistake
people make reading this line. It is also the sensitivity that shrinks the basement-deck
downgrade above: if the floor is polished, deleting the deck saves a further $3,000 – $5,000.

### Interior vapour retarder: poly → a smart membrane
**$2,200 – $4,000 → $5,700 – $10,700. Costs ~$3,500 – $6,700.** Also not in the estimate
today. Minnesota Climate Zone 6 requires a Class I or II retarder (0.3 – 1.0 perm) on the
warm side. Polyethylene meets it. A variable-permeance membrane (Intello, MemBrain) meets it
too and lets the assembly dry inward in summer, which matters more in a house with 2" of
exterior polyiso holding the sheathing cold. This is the cheapest building-science insurance
on the list per dollar.

### Breezeway glazing: 16mm polycarbonate → aluminium storefront with insulated glass
`concrete:glazing:BREEZEWAY_GLAZED_WALL`, 79.2 SF — **$1,424 – $3,168 → $8,100 – $16,455.
Costs ~$6,700 – $13,300.**

Worth stating plainly because it is easy to misread the estimate: **the breezeway is not
glazed in glass today.** `assemblies.py:358-378` is a single 0.63" layer of 16mm 5-wall
polycarbonate standing in a U-channel at the deck and an F-channel at the beam, with the 6x6
posts either end as the frame. There is no glass, no frame and no thermal break in the model.

The upgrade is dominated by a fixed cost that does not scale down: **mobilisation, shop
drawings and a glazier's minimum are $1,500 – $3,500 of it**, and the same assembly at
1,000+ SF prices at $60 – $95/SF against $103 – $208/SF here. A 79 SF job also cannot be
bought from a fabricator directly — Viracon and its peers will not quote it — so it routes
through a glazier buying IGUs from a smaller shop.

**What you get:** the breezeway is deliberately unheated and uninsulated, so this buys
appearance, acoustics and durability, not performance. **What you lose:** multiwall polycarb
is opal and diffusing, which is a genuinely different quality of light from clear glass, and
it is far less bird-hazardous — the assembly already specifies bird-safety film, and clear
glass in a breezeway between two buildings is close to a worst case for bird strikes.

### Breezeway roof: polycarbonate panel → a stock fixed skylight
`concrete:glazing:BREEZEWAY_ROOF_GLAZING`, 16 SF — **$480 – $960 → $1,430 – $3,185.
Costs ~$950 – $2,225.**

A Velux FCM 4646 (~15 SF, the right size) is $408 – $700 with an ECL curb-mount flashing kit
at $118 – $185, plus curb framing and a roofer to set and tie in. Real published dealer
pricing, unlike almost everything else in the breezeway.

**Do not confuse this with custom sloped glazing.** A one-off sloped unit with a laminated
inboard lite is $200 – $480/SF — 2 – 4x a stock Velux for the same aperture, because
engineering and mobilisation do not shrink. If the opening is genuinely a 16 SF square, the
stock skylight is the defensible choice and the custom unit is not an upgrade, it is a
purchase of the word "custom".

### Roof: eave-and-valley ice barrier → full-deck high-temp ice & water
**$5,000 – $11,000 → $17,400 – $38,300. Costs ~$12,400 – $27,300.**

**Neither option is in the estimate today** — see the missing-scope register below; the roof
is priced as bare panel with no underlayment at all, so this is an upgrade *from a hole*.

Minnesota code requires an ice barrier from the eave edge to 24" inside the exterior wall
line, which is the ~2,000 SF option. But **standing seam wants high-temp ice-and-water over
the entire deck** as standard practice — metal runs hotter than shingle and a standard
membrane can soften and telegraph. If the metal roof is kept, budget the full-deck number and
treat the eaves-only figure as the code floor rather than the specification.

### Main-floor concrete: sealer → genuine polish
`floor_finishes:sealed-concrete`, 1,155 SF — **$1,270 – $3,696 → roughly $4,600 – $8,100.
Costs ~$3,300 – $4,400.**

The line prices a penetrating densifier and two coats of sealer on the trowel finish, which
is what `sealed-concrete` is. A genuinely *polished* floor is a separate specialty contract
at $3 – $7/SF more for a Level 1-2 finish on a job this small. Noted here as an upgrade
because the reverse — assuming the estimate already buys a polished floor — is the mistake
people make reading this line. It is also the sensitivity that shrinks the basement-deck
downgrade above: if the floor is polished, deleting the deck saves a further $3,000 – $5,000.

### Interior vapour retarder: poly → a smart membrane
**$2,200 – $4,000 → $5,700 – $10,700. Costs ~$3,500 – $6,700.** Also not in the estimate
today. Minnesota Climate Zone 6 requires a Class I or II retarder (0.3 – 1.0 perm) on the
warm side. Polyethylene meets it. A variable-permeance membrane (Intello, MemBrain) meets it
too and lets the assembly dry inward in summer, which matters more in a house with 2" of
exterior polyiso holding the sheathing cold. This is the cheapest building-science insurance
on the list per dollar.

### Garage: full-height ICF walls (stem extended to the top plate)
`wall_structure:GARAGE_ICF_FULL` (new key, replaces `GARAGE_WALL_2X6` on all four walls),
plus `envelope_layers:icf-eps`/`stucco` — **net envelope+structure delta ≈ $5,600 – $10,900
more**, before the (unquantified, both directions) framing removal and new-detail costs
below. Not a full BOM line yet — see "What's genuinely new" before implementing.

**Basis, mixed on purpose, matching the house's own convention.** Per `prices.toml`'s
`[basis]` table, `wall_structure` is **installed** (ready-mix + placement labor already in
the $/cy rate) but `envelope_layers` is **materials only** — no labor for hanging the EPS
facing, troweling 3-coat stucco, or removing the old cladding is in the $2,640–4,560 and
$1,200–2,700 lines below. Only the $5,280–11,000 concrete line is a real installed number;
treat the envelope-layer lines as understating true installed cost, same as every other
`envelope_layers` row in this house's estimate.

Researched 2026-08-19. The garage (`houses/catlin/plan/storeys/garage.py`) is **freestanding**,
24'×24', 96 LF of perimeter, 4' north of the house — not attached, which matters for a couple
of the arguments below. It is already a hybrid, not pure wood: a 22" `GARAGE_ICF_6` stem
(6" core, 2.5" EPS each face, 8.82 CY today) carries an 8'-0" `GARAGE_WALL_2X6` wood wall up
to the plate, for a 9'-10" total wall height. The engine already treats ICF as a `concrete`
`STRUCTURE` layer with a `MasonrySpec` (`unit_size="ICF-6"`), billed through `wall_structure`
(NAHB 1200 / CSI 03 30 00) exactly like the stem is today — extending the stem to the plate
is a bigger version of an assembly that already exists and takes off cleanly, not a new
material or cost-code family.

**What changes, quantities.** New ICF tier: 8'-0" added height × 96 LF = 768 SF gross wall
face, replacing the wood-wall tier. Net of openings — `D-G-OVERHEAD` (16'×7' = 112 SF) on
the gable-end W-G-E, `D-G-SERVICE` (3'×6'-8" ≈ 20 SF) on the bearing wall W-G-S, plus an
estimated ~30 SF for W-G-W's windows (not sized in this pass — the plan doesn't schedule
them yet; adjust when it does) — net wall face ≈ **600 SF**.

| cost code | line | qty | $/unit | low | high |
|---|---|---|---|---|---|
| **Added** | | | | | |
| `wall_structure` | ICF-6 concrete, new tier | ~11 CY (600 SF × 0.0185 cy/SF, 6" core) | $480–1000/cy | $5,280 | $11,000 |
| `envelope_layers` | `icf-eps`, both faces | 1,200 SF | $2.2–3.8/SF | $2,640 | $4,560 |
| `envelope_layers` | `stucco`, exterior finish | 600 SF | $2–4.5/SF | $1,200 | $2,700 |
| **Added subtotal** | | | | **$9,120** | **$18,260** |
| **Removed** | | | | | |
| `envelope_layers` | `zip-r` sheathing | 600 SF | $2.2–4.2/SF | $1,320 | $2,520 |
| `envelope_layers` | `mineral-wool` cavity fill | 600 SF | $1.1–2/SF | $660 | $1,200 |
| `envelope_layers` | `standing-seam` wall cladding | 600 SF | $2.5–6/SF | $1,500 | $3,600 |
| **Removed subtotal** | | | | **$3,480** | **$7,320** |
| **Net delta (envelope + structure)** | | | | **$5,640** | **$10,940** |

The 2x6 stud framing and the 1x4 rainscreen furring being removed have no dedicated
$/SF rate in `prices.toml` (framing is billed by member/BF elsewhere in the house, not
isolated for this one wall), so their saving isn't in the table above. A generic
stick-framing allowance (not house-sourced — flag this as a rough external number, not a
prices.toml line) of roughly $2,000–$4,500 for 768 SF of 2x6 + furring would trim the net
delta down toward breakeven at the low end. Interior 5/8" GWB is unchanged in material and
rate either way — only its attachment moves from studs to the ICF's embedded furring
strips, a labor detail with no sourced $/SF delta (see below).

**What's genuinely new — read before implementing:**

- **The roof-truss-to-ICF sill detail isn't automated yet.** The engine's PT-sill/anchor-bolt/
  sill-gasket machinery (`resolve/construction_sills.py::_find_framed_on_concrete`, the same
  logic that already authors the stem-to-wood-wall junction here) only fires for a framed
  wall stacked on a concrete wall **between storeys**. It does not fire for a roof bearing
  directly on a masonry/ICF wall's own top within one storey — `resolve/framing/roof.py`'s
  truss bearing logic reads only the wall's top elevation and (for rafters) emits a
  wood-specific birdsmouth that would be wrong cast into ICF. Materials are trivial — a PT
  2x6 sill, sill gasket, anchor bolts at 6' o.c. per IRC R611.9 (embedded ≥7" into the ICF's
  top pour), and hurricane ties at each truss, on 96 LF, call it $150–350 — but getting the
  model to actually place them means either authoring a thin synthetic wood top-course into
  the new ICF assembly (cheap, plan-data only) or writing a new `ConstructionRule`/finder
  pair keyed off `Roof.bearing_refs` walls carrying a `MasonrySpec`, mirroring
  `_find_framed_on_concrete` and `takeoff/anchors.py::mudsill_anchor_rows`. This is an
  implementation note, not just a dollar line.
- **Garage-door jamb bucks.** Both LVL headers (`2-1.75x14 LVL` at the 16' overhead door,
  `3-1.75x5.5 LVL` at the service door) currently bear on jack studs inside the wood wall.
  In full ICF they'd bear on jamb bucks (PT or ICF-manufacturer proprietary bucking, e.g.
  Fox Buck/BuildBuck) cast into the form — manufacturer guidance wants ≥12" jamb width at a
  garage-door-scale opening, with lintel reinforcing extending ≥24" into the solid wall past
  each side. No engine logic exists today for opening/jamb framing against a `MasonrySpec`
  wall (`resolve/framing/openings.py` assumes stud-bay framing). Budget a few hundred dollars
  per jamb for buck material; get an ICF installer's number before treating this as solid.
- **Cripple wall above the overhead door.** ICF pours in fixed block courses, so the short,
  odd-height segment between the top of the 16' door's header and the truss-bearing line is
  standard practice to frame in wood rather than form in ICF — a small, cheap detail, but
  flag it so nobody tries to pour it.
- **Footing/stem load check.** The existing stem and its footing were sized for a 22" ICF
  stem carrying a light 2x6 wall above. A full-height ICF wall is meaningfully heavier dead
  load on the same footing — nobody has asked the engineer whether `FT-GF-*` still works
  once the wall above it is concrete instead of wood.

**Two things that do NOT change, confirmed:**
- **Ceiling insulation.** ICF replaces the *wall's* thermal envelope only; the truss
  bottom-chord blown-in/batt insulation is a separate line, unaffected either way — no
  double-count, no gap.
- **Gable-end cladding.** The gable triangles above W-G-E/W-G-W are framed by the truss
  system itself (`resolve/framing/roof_gable.py` drops 2x4 gable studs at 16" o.c.
  regardless of what the wall below is built from) and clad by the wall→roof closure in
  `resolve/roof_edge.py`, which needs its own small cladding source — OSB + snap-lock
  standing seam — once the wall below has no sheathing/cladding layers of its own to extend
  upward. This is exactly why the gable ends keep standing-seam cladding under full ICF: it
  was never derived from the wall, only from the truss.

**What you get, not captured in the dollar figures above:** meaningfully better fire
resistance, wind/impact resistance and sound isolation than 2x6-frame-and-metal-siding, plus
thermal mass. Worth weighing against the fact that this is a **detached, unheated-to-code
garage** — the usual ICF payback argument is energy performance in conditioned space, and
detached accessory structures are the case multiple cost guides flag as the weakest
justification for the premium. If the driver here is durability/fire/impact rather than
energy, say so; it changes which end of the range is worth paying for.

### Garage: CMU block wall with exterior Zip-R (third wall-system option)
`wall_structure:GARAGE_CMU_8` (new key, replaces `GARAGE_WALL_2X6`'s 8'-0" tier only — the
existing ICF stem stays, same reasoning as below), plus unchanged `envelope_layers:zip-r`/
`standing-seam` and a new `furring` line for the interior lining — **net delta ≈ $11,200 –
$15,600 more**, before the same unquantified framing-removal saving noted for the ICF
option. Counterintuitively **the more expensive of the two masonry options**, and it carries
a real engine gap the ICF option doesn't. Read "Why this one's a harder sell" before treating
it as the cheap-and-cheerful alternative to ICF.

Researched 2026-08-19, same session as the ICF entry above — same 600 SF net wall-face basis
(the 8'-0" wood-wall tier only; the below-grade/near-grade 22" `GARAGE_ICF_6` stem stays ICF,
since that's the tier doing the moisture/thermal-break job at grade and CMU is a poor
substitute for it there — converting the stem too is a different, bigger, unpriced option).
The appeal of this option over full ICF is that it keeps the garage's *existing* exterior
skin — Zip-R sheathing, rainscreen, standing-seam cladding — unchanged, rather than swapping
to stucco. Two things work against it:

**Basis note, same as the ICF entry.** The `wall_structure` CMU line ($10,800–14,360) is
**installed** by house convention (`prices.toml`'s `[basis]` table) — labor's in it. The
furring line below ($1,614–1,926) is sourced from an *installed* homewyse figure, which is
actually richer than the house's own `framing` convention (materials only) — call that line
the one exception where labor happens to already be included, not a gap. Everything else
that carries over unchanged (zip-r, standing-seam) stays on the house's materials-only
`envelope_layers` basis, same caveat as the ICF entry: real installed cost for those is
higher than shown, and — new in this option — so is the CMU-specific Tapcon-attachment labor
premium flagged below, which has no dollar figure at all.

1. **CMU installed cost runs higher than ICF, not lower.** Current cost-guide figures put
   8" grouted/reinforced CMU (partial grout, not solid) at **$18–24/SF installed** typical,
   $14–32/SF full range, against ICF's **$8–18/SF** (Midwest $8.50–14/SF) already in the
   estimate above. This is the opposite of the "plain block must be cheaper than a fancy
   foam-form system" intuition, and is corroborated only indirectly (two different source
   families, not one head-to-head study) — worth a mason's quote before leaning on it, but
   directionally it's a real finding, not noise.
2. **The engine's PT-sill/anchor-bolt/gasket machinery doesn't fire for CMU at all today —
   a strictly larger gap than ICF's.** `resolve/construction_sills.py::_find_framed_on_concrete`
   (the finder that already authors the *existing* stem-to-wood-wall sill detail) gates on
   `layer.material_ref == "concrete"` exactly. ICF's structure layer *is* tagged
   `"concrete"` (it trips this finder today), but a real CMU structure layer is tagged
   `"cmu"` — a different material ref — so it silently would not fire. There is also no
   distinct masonry (CSI 04 22 00) cost code anywhere in `takeoff/cost_codes.py`; CMU would
   bill through the same 03 30 00 "concrete" code as ICF, which is fine for the dollar total
   but wrong for trade categorization if that ever matters downstream. Fixing this cleanly
   is engine work (broadening the finder's gate to `_is_concrete(lower_asm) or
   _is_masonry(lower_asm)`, or an equivalent new rule), not a plan-data edit.

**What changes, quantities** (600 SF net wall face, same door/window deductions as the ICF
entry — 16'×7' overhead door, 3'×6'-8" service door, ~30 SF window allowance not yet sized):

| cost code | line | qty | $/unit | low | high |
|---|---|---|---|---|---|
| **Added** | | | | | |
| `wall_structure` | CMU-8, gross-volume basis (0.0247 cy/SF nominal) | ~14.8 CY | $730–970/cy (derived from $18–24/SF ÷ 0.0247 cy/SF) | $10,800 | $14,360 |
| new `furring` layer for interior GWB | 1x3/1x4 or Z-furring at 16-24" o.c. — CMU has no integrated furring strips the way ICF does, so this is genuinely new, not a relabel | 600 SF | $2.69–3.21/SF | $1,614 | $1,926 |
| **Added subtotal** | | | | **$12,414** | **$16,286** |
| **Removed** | | | | | |
| `envelope_layers` | `mineral-wool` cavity fill (no cavity to fill in solid block; exterior Zip-R is already carrying the R-value) | 600 SF | $1.1–2/SF | $660 | $1,200 |
| **Removed subtotal** | | | | **$660** | **$1,200** |
| **Net delta** | | | | **$11,214** | **$15,626** |

`zip-r` sheathing and `standing-seam` wall cladding are **unchanged, zero net delta** — they
carry over from the current wood-wall assembly onto the CMU face essentially as-is (the
resolver doesn't care what's under a SHEATHING-function layer; a `zip-r` layer sitting on a
CMU structure layer bills identically to one sitting on studs). That's the whole appeal of
this option over full ICF. Not priced: any masonry-attachment labor premium on the Zip-R
Tapcon-through-to-block install (no source isolates this, but a real premium over screwing
into wood is expected — treat the low end of the range as optimistic), and a **CMU bond-beam
course** (a full-grout, horizontally-reinforced top course before the sill plate) — standard
practice at a CMU top-of-wall, genuinely additional quantity beyond the partial-grout
schedule the rest of the wall uses, but no sourced $/LF figure to put on it. Budget a mason's
quote for 96 LF of bond beam before treating this as final.

**Anchor bolts are tighter than the ICF option, not the same.** The ICF entry above uses
IRC R611.9's 6' o.c. figure. That's ICF-specific. CMU falls under the general R403.1.6.3
sill-anchorage rule instead, which caps spacing at **4' o.c.** (the 6' o.c. exception is for
sills on concrete floors, not masonry wall tops) — more bolts, a real if small cost
difference from the ICF option, not a rounding error to wave away.

**Where CMU wins.** A partially-grouted (32–48" o.c.) CMU wall at ~50–55 psf is meaningfully
lighter than either ICF's continuous 6" core (~74 psf) or a fully-grouted CMU wall (~78
psf) — roughly 30% less dead load on the same footing than the full-ICF option, which
matters given neither option has had the footing re-checked (see the ICF entry's flag).
CMU also has a well-documented, low-uncertainty lintel detail at the garage-door opening
(a precast or steel lintel bearing on solid-grouted jamb cells, per CMHA's TR91B lintel
design manual) — genuinely more standard and less speculative than ICF's jamb-buck detail,
which came back thin in that research pass.

**Bottom line.** On current figures this option costs more than full ICF (~$11,200–15,600
vs. ~$5,600–10,900) for a wall that's structurally lighter but has a bigger unfinished
engine gap and a less novel finish (same cladding, not a real upgrade in that department).
It's the right answer only if the wood-wall-tier weight matters to the footing more than the
dollars do, or if avoiding a stucco finish is a hard requirement — otherwise full ICF reads
as the stronger option of the two masonry choices.

### Oak flooring in the LVP rooms
`floor_finishes:lvp` 1,272 SF at **$2,544 – $5,724** → oak at the `oak` rate is
**$5,088 – $10,176. Costs ~$2,500 – $4,500.**

Rooms: living, study, second-floor hall, and the two upstairs baths (the baths are the
reason this is not an obvious swap — oak in a bathroom is a maintenance decision).

## Not yet priced

One idea from TODO.md's cost-cutting list still needs a number before it can move here:

- Remove the attic level, switch to truss + blown-in insulation. Touches framing,
  envelope_layers, floor_finishes, stairs and the ST-S2A guard at once; needs a variant,
  not an arithmetic estimate. `haus variants compare` is the tool.
- *(Standing seam → architectural asphalt was priced on 2026-08-20 and has moved up to
  Downgrades, where it is now the largest row on the list.)*

## Scope the model cannot resolve — the allowance register

Compiled 2026-08-20 and **authored into `prices.toml` the same day** (see the reconciliation at
the end of this section). It began as a register of real cost the estimate could not see,
because Type:Haus prices the quantities the model resolves and the model does not resolve
earthwork, permits or a general contractor. It is now the source document behind the
`[allowances]` table — each line below is a row there, and the two are meant to be diffable.

Overlaps between trades have been removed (gutters, ice-and-water, radon and window flashing
each turned up in two research passes and are counted once). Ranges are installed dollars for
this house — 6,012 gross sf, full walk-out basement, detached garage — in 2026 Twin Cities
money, and they exclude GC overhead and profit, which is itemised separately at the bottom.

### Site and structure

| item | low | high | note |
|---|---|---|---|
| Excavation, backfill, haul-off, rough grade | $24,000 | $55,000 | **The biggest hole.** Huge swing on whether spoils stay on site — a walk-out consumes fill reshaping the daylight side, which can collapse haul-off from $30k to $2 – 5k |
| Rebar, furnished and installed | $10,000 | $18,000 | ~5 tons. Currently in **neither** the $/cy rates nor a line of its own — `prices.toml`'s wall and footing rates were raised on 2026-08-20 on the assumption it rides inside them, which is a decision that should be made explicitly |
| Garage slab, driveway apron, walks | $18,000 | $44,000 | Driveway and city walk are usually a separate contract let months later |
| Drain tile labour, rock, sump, daylight outlet | $9,000 | $19,000 | The `drain_tile` line now covers the pipe; this is the rest |
| Concrete pumping | $4,600 | $7,800 | **The single most-forgotten line.** Ready-mix suppliers never include it and flatwork subs quote "pump by others". Two live 2026 rate sheets: $200 – $225/hr + $4/cy, 4-hr minimum |
| Damp- or waterproofing | $1,200 | $16,000 | MN code minimum is damp-proofing only (IRC R406.1) at $1,200 – $3,200; +dimple board $3,500 – $7,000; full membrane $8,000 – $16,000 |
| Window bucks and block-outs | $1,500 | $4,500 | |
| Radon rough-in and egress window wells | $3,400 | $10,200 | MN requires radon-resistant new construction |
| Cold-weather concrete, **if the pour lands Nov – Apr** | $8,000 | $21,000 | 10 – 25% of the concrete package. Admixtures and hot water are only $30 – 45/cy; an enclosure and ground thaw double it, and the suspended deck is the worst case because you are tenting the *underside* of a slab 9' in the air |
| Survey, staking, erosion control, temporary shoring | $2,000 | $6,000 | Silt fence and a rock construction entrance are required by the watershed district in the metro |

### Envelope

| item | low | high | note |
|---|---|---|---|
| Roof underlayment, full field | $4,500 | $9,000 | The roof is priced as bare panel |
| Ice & water barrier | $5,000 | $38,300 | $5 – 11k for the code eave-and-valley minimum, $17.4 – 38.3k for the full-deck high-temp the metal actually wants. See the upgrade entry above |
| Drip edge, valley metal, boots, custom flashings, snow retention | $6,000 | $14,000 | Partly overlaps `edge_trim`; this is the balance |
| Rainscreen furring over the exterior polyiso | $4,400 | $8,800 | Needed for cladding attachment through 2" of foam either way |
| Window and door flashing tape, sill pans, air sealing | $5,100 | $11,800 | 45 openings |
| Air sealing labour and two blower-door tests | $3,100 | $7,200 | MN limits to 3.0 ACH50 |
| Interior vapour retarder | $2,200 | $10,700 | Poly at the low end, smart membrane at the high — see the upgrade entry |
| Attic/ceiling blown insulation | $2,700 | $4,700 | The batt quantities read as walls only |
| Exterior sealants and caulking | $1,800 | $4,500 | |
| Sub-slab vapour barrier, sill sealer, capillary break | $1,255 | $2,760 | |
| Scaffolding and lift rental | $3,000 | $8,000 | |
| Exterior hoods and their flashing | $800 | $2,000 | Dryer, range, HRV, hose bibs |

### MEP

| item | low | high | note |
|---|---|---|---|
| PV array — modules, racking, rapid shutdown, labour | $24,000 | $46,000 | Only the inverter, battery and PV junction box are priced today. $3.00 – $3.82/W installed in MN |
| **Branch-circuit conductors** | $10,000 | $25,000 | **The largest MEP omission, and easy to miss precisely because conduit *is* priced.** ~4,500 – 6,500 LF of NM-B plus service-entrance and sub-feeders |
| Municipal water and sewer connection, SAC | $6,000 | $18,000 | Verify the 2026 Met Council SAC rate directly. Unsewered would be well $12 – 25k + septic/mound $18 – 45k, a different number entirely |
| Electrical service entrance and utility connection | $3,500 | $9,000 | Includes temporary construction power |
| Refrigerant line sets and accessories | $3,735 | $7,090 | 5 pairings, ~145 LF. Entirely absent today |
| Water softener and filtration | $2,500 | $6,000 | Optional on Minneapolis municipal water, essential on a well |
| Structured low-voltage drops | $2,000 | $6,000 | The enclosure is priced; the 20 – 35 drops are not |
| Range hood and MN code makeup air | $1,500 | $4,500 | Not optional on a tight all-electric house |
| AFCI/GFCI/dual-function breakers | $1,400 | $2,900 | A "load centre" price is the can and main only |
| HVAC controls, thermostats, zone control | $1,200 | $3,000 | |
| Duct insulation, mastic, leakage test | $1,000 | $2,500 | Required for the MN energy-code duct test |
| Bath exhaust fans | $750 | $2,400 | There are 20.7 LF of exhaust duct and no fans |
| Condensate drains, traps, pumps | $600 | $1,600 | |
| Radon fan upgrade, commissioning, smoke/CO, surge, misc | $2,450 | $8,000 | |
| MEP permits | $1,500 | $4,000 | Separate from the building permit |

### Interior finishes

| item | low | high | note |
|---|---|---|---|
| Interior trim and baseboard | $12,000 | $20,000 | ~1,400 – 1,800 LF, in no key today |
| **Paint and finish on trim and doors** | $8,000 | $18,000 | `envelope_layers:latex-paint` is wall and ceiling area only — it does not see a linear foot of trim or a door face |
| Closet shelving and rod | $3,000 | $40,000 | **Pick a lane.** Wire is $3 – 5k; a semi-custom laminate system is $12 – 40k. A $35k swing on an undecided item |
| Floor prep and self-levelling | $4,500 | $11,700 | |
| Tile backer board and waterproofing | $4,000 | $8,000 | Explicitly *not* inside the tile labour rate |
| Door hardware | $3,000 | $11,000 | ~36 doors |
| Window stools and aprons | $3,300 | $7,400 | 41 windows |
| Floor transitions, thresholds, stair nosings | $1,000 | $3,000 | Seven finishes meeting each other |
| Garage door opener | $500 | $1,400 | |
| Protection, final clean, dumpsters | $3,500 | $8,500 | |

### The three that dwarf all of the above

| item | low | high |
|---|---|---|
| **General conditions** — supervision, temporary power and heat, portable toilet, site fencing, trash, small tools | $35,000 | $80,000 |
| **General contractor overhead and profit** — 13 – 22% is the published band, applied to the priced scope plus the missing scope above | $100,000 | $375,000 |
| **Design, permits, plan review, SAC/WAC, testing, insurance** | $20,000 | $60,000 |

### ✅ Authored into the estimate, 2026-08-20

**This register is no longer a register.** On the owner's decision every line above is now a
row in `houses/catlin/prices.toml`'s new `[allowances]` table, so `haus takeoff` prices it,
the bid ladder carries it and `haus tasks` schedules it under the right trade. What follows is
the reconciliation between this document and that table — they should agree line for line, and
where they deliberately do not, it says so.

`[allowances]` is the one section with no quantity behind it: `estimate_costs` synthesises a
row per key at count 1, so the number authored is the line total and the unit prints as `ls`.
The mechanism is `cli/prices.ALLOWANCES`; the discipline is in the table's own header comment.

**Three deliberate differences from the tables above** — the estimate is *not* simply their sum:

| line | register | authored | why |
|---|---|---|---|
| Rebar | $10,000 – $18,000 | **absent** | `[basis_notes] concrete` says rebar is *inside* the $/cy rates, and those rates were raised on 2026-08-20 on exactly that assumption. Authoring it would bill ~5 tons of steel twice. Reversing the decision means taking it out of the concrete rates the same day |
| GC overhead and profit | $100,000 – $375,000 | **absent** | That is the `[markup]` stage, which the owner deliberately left at zero. Putting it in `[allowances]` would turn it on through a side door — and take contingency *and sales tax* on a builder's fee |
| Ice & water barrier | $5,000 – $38,300 | $5,000 – $11,000 | Only the code minimum is base scope. The full-deck high-temp membrane stays an **upgrade** entry, so the base number stays a base number |
| Cold-weather concrete | $8,000 – $21,000 | $0 – $21,000 | It is a schedule question with a yes/no answer. A summer pour is genuinely zero, and a $8,000 floor hides that |

General conditions ($35,000 – $80,000) **is** authored, because general conditions is not
overhead and profit — supervision, temporary power and heat, the toilet, fencing and trash are
direct job cost. Conflating the two is the most common way a residential estimate goes wrong by
six figures.

Subtotals of the four tables above: site $81,700 – $201,500, envelope $39,855 – $121,760,
MEP $62,135 – $145,990, finishes $42,800 – $129,000. Authored `[allowances]` total, after the
four adjustments above and the four owner decisions below: **$263,490 – $636,950**.

**Four owner decisions, 2026-08-20**, each of which changed an authored row:

| row | was | now | why |
|---|---|---|---|
| `cabinet-closet-shelving-and-rod` | $3,000 – $40,000 | **$3,000 – $5,000** | Wire shelving on standards. **−$35,000 off the high end** — the largest single narrowing any decision on this file produced |
| `concrete-cold-weather-protection` | $0 – $21,000 | **$0 – $0** | Summer pour, May – Oct. Row kept at zero as the reminder of what a schedule slip costs (it is $8,000 – $21,000 if the pour lands Nov – Apr) |
| `roof-ice-and-water-barrier-code-minimum` | code minimum | **code minimum, confirmed** | Not a saving — a strategy. A highly insulated assembly under a low-friction standing seam over a quality full-field underlayment stops a dam *forming*; full-deck membrane insures against one that already has. **Do not let the full-field underlayment be value-engineered out while this stays at the minimum** — together they are the defence, and dropping one leaves neither |
| `[tax] material_rate` | 9.025% | **8.525%** | Suburban Hennepin, not the city. −$3,182. Note the asymmetry left deliberately in place: every *labour* rate in the file is localised to Minneapolis wages and does **not** drop at the city line — suburban Hennepin is the same labour market. Only tax is jurisdictional |

`haus takeoff` now prints the whole ladder rather than a net subtotal:

| stage | low | high |
|---|---|---|
| resolved quantities (every section but `[allowances]`) | $576,557 | $1,139,150 |
| `[allowances]` — the register above | $263,490 | $692,950 |
| **subtotal_net** | **$840,047** | **$1,832,100** |
| waste | $25,470 | $47,904 |
| subtotal_ordered | $865,517 | $1,880,004 |
| contingency, 10% | $86,552 | $188,000 |
| markup — **off by choice** | $0 | $0 |
| sales tax, 9.025% on material only | $28,454 | $58,229 |
| **total** | **$980,523** | **$2,126,233** |
| **$/gross sf** | **$163** | **$354** |
| *memo:* GC overhead and profit at 15 – 20%, if taken | *+$130,000* | *+$375,000* |

*(The paragraph that stood here said the ice-and-water barrier and the closet system were
together ~$65,000 of the spread and that deciding them would narrow the range more than any
other pair. Both were decided on 2026-08-20, along with the pour season and the tax
jurisdiction, and the four together took $64,782 off the high end — see the decision table
above. The prediction was almost exactly right.)*

**That reconciles.** Published 2026 Twin Cities custom-home cost is $250 – $400+/sf, and this
house is a complex one — walk-out basement, suspended concrete deck, five refrigerant systems,
sauna, plant room, PV and battery. $163 – $354/sf without a GC's margin, rising to roughly
$185 – $416/sf with one, sits exactly where it should relative to that band: the low end is an
owner-builder who avoids the fee, and the published band assumes a GC.

**And this is still decision #28, not an exception to it.** The engine ships no numbers; the
*house* says what its excavation costs, in the house's own file, exactly as it says what a
yard of concrete costs. What changed on 2026-08-20 is only that an allowance has no quantity
to multiply — so it is a lump sum at count 1 rather than a rate. Nothing was folded into a
fudge factor: every line above is its own row, with its own basis, on its own line of
`haus takeoff`, flowing through the same waste, contingency, cost-code and tax path as a
stick of 2x6.

**Sales tax reaches less than half of this.** `haus takeoff` prints that it could not reach
$290,550 – $709,886 of merged material+labour — `[concrete]`, `[wall_structure]`, the
seamless-gutter row, and most of `[allowances]`, where a lump sum for unquoted scope has no
honest split. That figure is the exact measure of what declaring more splits would be worth,
and it is printed rather than assumed away. (MN taxes materials only: a contract to improve
real property is not itself taxable and construction labour is exempt — the contractor is the
end user of the materials. MN DOR Sales Tax Fact Sheet 128.)

## Refactors — where the price model itself is the problem

Not cost swaps. These are places where the *estimate* is wrong or fragile in a way no rate
change fixes, found during the 2026-08-20 pass. Ordered by how much they distort the number.

### ~~`PORCH_DECK_COMPOSITE` disagrees with itself by 10x~~ — **not a bug; closed 2026-08-20**
Two passes read the solid `SL-BW-DECK` (0.05 cy = 16.5 SF) and the `[sheet_goods]`
`composite-deck` row (164.7 SF) as one deck counted twice, ten-fold apart. They are **two
different decks**, and `takeoff/framing.py:223` proves it: the sheet_goods `subfloor` scope
reads `FloorSystem.subfloor` and nothing else, so a `Slab` can never reach it.

- 164.7 SF is `FS-SG-PORCH`'s `subfloor=DeckLayer(material_ref="composite-deck")` — the
  **sunken-garden porch**, whose own slab was deleted so the plank became the floor system's
  surface layer (`params/sunken_garden.py:606`).
- 16.5 SF is the **breezeway deck** (`params/breezeway.py:351`), 4.0' × 4.11' between the house
  cladding and the garage stem. That is exactly its modelled outline.

Neither double-counts the other. The breezeway solid is now priced ($216 – $515) and the last
genuinely-unpriced row in the file is gone — every remaining entry on `haus takeoff`'s
"not priced" list is a confirmed mirror.

### ~~Six rows are priced per cubic yard~~ — **built 2026-08-20: a row may name its own unit**
`structural_solids` bills by volume, so `drain_tile`, `sump`, `bug_screen`, `thermal_break`,
`RETAINING_BLOCK_12` and `BASEMENT_BRICK_VENEER` all carried a $/cy rate for something no trade
sells by the yard. The line totals were honest; the *rates* were numbers nobody could
sanity-check — `bug_screen` was 18 screens against 0.04 cy, a multiplier of **~6,000**, so a
25-cent-per-foot error moved the printed $/cy by $1,500.

A price row can now say `unit = "..."` and be read against a different field of the same BOM
row (`cli/price_file.ALTERNATE_UNITS`). Only fields the row already carries are offered: this
converts nothing and derives nothing, and a unit a section does not offer is a hard load-time
error rather than 3.13 cubic yards priced at a per-foot rate.

| row | was | now | multiplier |
|---|---|---|---|
| `drain_tile` | $1,500 – $3,400/cy | **$18 – $42/SF** — $6 – 14/LF, ×3 | 6,000 → **3** |
| `sump` | $2,100 – $6,300/cy | **$400 – $1,200/ea** — literally the per-basin price | → **1** |
| `thermal_break` | $300 – $500/cy | **$25 – $90/ea** | → **1** |
| `bug_screen` ×2 | $3,840 – $19,200/cy | **$19 – $64/SF** | ~6,000 → **~25** |
| `RETAINING_BLOCK_12` | $800 – $1,600/cy | **$30 – $60/SF of face** | → **1** |
| `BASEMENT_BRICK_VENEER` | $1,450 – $2,850/cy | **$20 – $45/SF of face** | → **1** |

Every conversion is within 3% of the money it replaces except `thermal_break`, which was
**wrong by 10x in the direction that hides scope** — three column bearing pads were billing
$9 – $15 in total. This is what an unauditable rate costs you.

`drain_tile`'s conversion is exact rather than estimated: `resolve/drain_tile.py` extrudes each
run as a band exactly one pipe diameter wide, so at 4" pipe the plan area is LF/3. The takeoff
confirms it from the other side — `footing_bedding` independently reports
`drain_tile_ft` 515.3 + 246.0 = **761.3 LF** against a derived 761.4.

### 761 LF of drain tile is a lot of drain tile
Not a pricing problem — a *quantity* to look at, surfaced by the conversion above. The model
derives a **separate closed ring around each of the 26 footing beddings** (tags run
`FB-B-CE-DT-1..4`, `FB-B-CN-DT-1..4`, …), rather than one perimeter ring around the building
plus laterals. That is what `drain_tile_solids(..., closed=True)` does per bedding, and it is
defensible for isolated pad footings; for a continuous basement wall footing it counts the
run out and back. At $6 – 14/LF the difference between 761 LF and a single ~250 LF perimeter is
**$3,000 – $7,200**. Worth confirming against the drainage plan before anyone bids it.

### ~~`[drainage]` blends two products that differ 3x~~ — **built 2026-08-20**
`cli/prices.QUALIFIED_KEY_FIELD` now qualifies `[drainage]` on the row's `product`, the same
mechanism `[concrete]` already used for `category:assembly`. Four keys where there were two:

| key | LF | rate |
|---|---|---|
| `gutter:aluminum` | 47.8 | $8 – $15/LF **installed, merged** |
| `gutter:metal-dark-exterior` | 73.7 | $10 – $25 material + $12 – $22 labour |
| `downspout:aluminum` | 26.4 (2 drops) | $5 – $9 + $2 – $4 |
| `downspout:metal-dark-exterior` | 50.0 (2 drops) | $10 – $20 + $4 – $8 |

The bare `gutter` and `downspout` keys are **deleted, not kept as a fallback** — a fallback
would silently bill an unpriced product at whatever the last blend happened to be, where its
absence surfaces the product on `haus takeoff`'s unpriced list. Total money moved 3%, which is
the point: this was always weighted right for *today's* mix. The box-gutter downgrade is now a
subtraction instead of an argument about an average.

The genuine limit stands and is recorded in the file: seamless K-style is roll-formed on site
from coil, so there is no moment at which a material price and a labour price exist separately.
That row is `basis = "installed"` and reports as merged rather than carrying an invented split.

### ~~Three roof-edge quantities do not obviously reconcile~~ — **they do; closed 2026-08-20**
Reading the BOM tags rather than the totals settles all three. There is no phantom trim and no
mirror; the numbers are describing different things.

**Fascia, 251.5 LF, is three runs and one of them is deliberately doubled.**

| Rows | LF | What |
|---|---|---|
| `TR-SG-FASCIA`, PVC 9"×1" | 38.3 | sunken-garden porch |
| `RF-GARAGE:*-fascia-0`, spf 1.5×5.5, 6 edges | 106.2 | garage fascia **backer** |
| `RF-GARAGE:*-fascia-1`, cellular PVC, the *same* 6 edges | 107.0 | garage fascia **face** |

So the garage perimeter is ~106 LF carrying two plies — a wood backer with cellular PVC over
it, the outer ply 0.8 LF longer because it wraps the corners. That is a real detail, correctly
billed twice. The house (`RF-HOUSE`) has **no fascia at all**, which is right for a standing-seam
roof that closes out into trim.

**Edge cladding, 243.9 LF, is not fascia.** All 15 tags are `W-*-closure-*-cladding` — the
standing-seam closure over the top of the walls, 9 on the house and 6 on the garage. The
near-match to 251.5 LF is a coincidence of two buildings' perimeters, not a mirror. **No
$1,700 – $4,000 of phantom trim exists**; that concern is withdrawn.

**Gutter, 121.5 LF, is under half of either because gutters go on eaves, not rakes** — 21.0
(sunken garden) + 26.8 (garage low eave only) + 73.7 (house E and W eaves). The 73.7 matches
`TR-RF-DRIP-E/W` exactly: same two edges, drip edge under gutter.

**Downspouts are 4 drops, not an unknown count.** `drainage` reports `count` explicitly: 2 ×
3" aluminium (26.4 LF) and 2 × 4" dark formed (50.0 LF). Four drops averaging 19 ft is right
for a two-storey walk-out, and 4 drops on 121.5 LF of gutter is a normal spacing. The earlier
"probably 5 – 7 drops, distrust the length" note was wrong — the count was in the BOM all along.

### ~~`construction_returns:pt-sill-plate` is an open authoring question~~ — **closed 2026-08-20**
The question was whether the 306.6 LF is a separate pressure-treated mudsill or a second count
of the wall's own bottom plate. It is the second, and two facts in the engine settle it:

1. `resolve/framing/solver.py:_append_plates` appends exactly one `plate-bottom` member to
   **every** framed wall, unconditionally — there is no branch that skips it when the wall
   lands on concrete. `[framing]` has already bought the board on all 306.6 LF.
2. `CR-CONC-TO-FRAMED-SILL` (`plan/assemblies.py:972`) is `kind="bearing_plate"` with
   `dimension=inch(1.5)` — one 2x course, the same 1.5" as that bottom plate. The construction
   rules are documented as "typed declarations of the physical returns the junction solver
   leaves", so the rule *states that this plate must be PT*. It does not add a plate.

The `spf` material the takeoff reports is therefore not a bug to chase — it is the framing
member's own species, and this row is the upgrade on it. `prices.toml` already prices exactly
the delta (PT premium, sill sealer, anchor bolts, drill-and-set labour), so **no change to the
number is needed** and the "add $1.30 – $2.20/LF if confirmed" caveat has been removed as
actively misleading.

### ~~Waste, contingency, markup and tax are all still absent~~ — **three of four on, 2026-08-20**
The ladder was flat — `subtotal_net` == `total` — so the printed number was a *net* number
wearing the word "total". On the owner's decision three of the four stages are now declared in
`prices.toml`, and the fourth is present at zero so turning it on is one edit.

- **`[waste]`** — 3 – 10% by section, **on material only**. It never rides on declared labour:
  you buy 110 SF of board to install 100 SF, but you do not pay the installer 10% more for it,
  because an installed labour rate is quoted per square foot of *finished* area and already has
  normal cutting inside it. This was a real defect when the stage was first turned on — 41% of
  the waste ($10,531 – $19,796) was landing on labour, which is precisely what made waste and
  contingency read as one stage charged twice. Fixed in `cost_model.apply_waste` and pinned by
  `test_waste_never_rides_on_declared_labour`; the stage dropped from $25,470 – $47,904 to
  **$14,938 – $28,107**. The one admitted exception is a merged row, where the material half
  cannot be identified — waste over-applies there exactly where tax under-applies.
  Deliberately *not* declared on `framing`, `sheet_goods`,
  `floor_finishes` or `wood_surfaces`: those four bill on an order quantity that already carries
  their waste, and the loader makes an entry on one of them a hard error rather than a silent
  double-count. Nor on `openings`, `placeables`, `sleeves`, `plumbing_specialties`,
  `install_parts` or `allowances` — you do not over-order a window or an excavator, and a
  wasted one is a mistake, not a rate. **Each omission is a claim, and the file says so.**
- **`[contingency]` 10%** on the ordered subtotal. Ten rather than the 15 – 20% a
  schematic-design estimate needs, precisely *because* this house is modelled to a level of
  detail most estimates never reach. Note that it applies to `[allowances]` too, which for a
  line already carrying a 2× range is arguably belt-and-braces — left that way rather than
  special-cased, because a contingency that skips the least-certain third of the estimate is
  not a contingency.
- **`[tax]` 8.525% on material only, and only on material that has not already been taxed
  once.** Auditing where each material rate came from turned up a real double-count: a shelf
  price (Menards, a yard's $/LF, a manufacturer's list) is pre-tax and clean, and
  [Homewyse explicitly excludes sales tax](https://www.homewyse.com/services/cost_to_estimate_home_remodeling_costs.html) —
  but a rate **back-derived from a published *installed* cost** is not, because that figure is
  a contractor's price to a homeowner with the tax already passed through inside it.
  `[openings]`'s own header admitted it: *"Published window costs are almost all installed
  prices, so these are backed out."* Three sections were affected — `openings`, `floor_finishes`
  and the six split `allowances` rows — worth **$7,887 – $17,685** of tax charged twice.

  Fixed with a new `[tax_included]` table, same key shape as `[waste]` (`"section"` or
  `"section:key"`, because tax-inclusiveness varies row by row inside a section exactly as
  waste does). It is a **boolean, not a rate**: "does this number already have tax in it" has
  an answer, "what effective rate is buried in this national average" does not, and the loader
  refuses a float so nobody invents one. What the stage skips is *printed* rather than
  absorbed, beside the merged figure. The tax stage fell from $26,551 – $54,450 to
  **$18,664 – $36,765**.

  **The flag is the second-best answer.** The best one is to re-source the rate from a pre-tax
  list price, which deletes the entry — `[openings]` is being re-sourced from manufacturer list
  prices now, and its flag comes out when that lands.

- ~~**`[tax]` 9.025% on material only**~~ — the Minneapolis combined rate (6.875% state + 0.15%
  Hennepin + 0.5% city + 1.5% special district). Suburban Hennepin would be 8.525% and is a
  one-line change. MN taxes materials and not residential construction labour: a contract to
  improve real property is not itself taxable and the contractor is the end user of the
  materials (MN DOR Fact Sheet 128). **This entry only means anything because of the
  material/labour split pass** — it still cannot reach $290,550 – $709,886 of merged rows, and
  `haus takeoff` prints exactly that figure rather than assuming it away.
- **`[markup]` is zero by choice**, and present so it is one edit. Overhead and profit are two
  stages rather than one because they compound in a fixed order: profit is taken on
  (ordered + contingency + overhead). Twin Cities custom residential runs 8 – 12% overhead and
  5 – 10% profit — on this house, roughly **$130,000 – $375,000**.

**The trap this leaves.** GC overhead and profit is deliberately absent from `[markup]` *and*
deliberately absent from `[allowances]`. Turning on one without noticing the other is a
six-figure double-count in one direction or a six-figure hole in the other. There is a test
(`test_catlin_does_not_pay_the_gc_twice`) that pins both halves together.

### The roof is priced as bare panel, and the boundary is now guessed in two places
`envelope_layers:standing-seam` is panel and clips. Underlayment, the code ice-and-water,
flashings, boots and snow retention are now `[allowances]` rows; drip edge and closure are in
`edge_trim`; seam clamps are in `hardware`. That is four tables describing one roof, and the
split between them is an assumption nobody has checked against a roofer.

**This is the highest-value phone call on the whole list.** A single roofing quote settles what
is inside the roofer's number and what is not, and it touches the largest line in the house
(standing seam at $60k – $117k) plus three allowance rows worth $15,500 – $34,000. It is also
the one place where the new `[allowances]` table can double-count without anything catching it:
if the roofer's price includes underlayment, `roof-underlayment-full-field` has to come out the
same day. See the "one rule" note at the head of that table.

## Open questions for the owner

Everything else in this file is either decided, priced, or a documented mirror. These are not.

| # | question | what it moves |
|---|---|---|
| 1 | **Is the GC fee in or out?** `[markup]` is at zero today, so the printed $980k – $2.13M is a subcontractor sum. | +$130,000 – $375,000, and it is the single largest undecided number |
| 2 | **Is rebar inside the concrete $/cy rates, or its own line?** The file assumes inside and the allowance is omitted on that basis. Reversing it means editing both places at once, or paying for ~5 tons of steel twice. | $10,000 – $18,000 if the assumption is wrong |
| 3 | **Is 761 LF the right length of drain tile?** The model rings each of 26 footing beddings separately rather than running one perimeter. | $3,000 – $7,200 |
| 4 | **One roofing quote** — see immediately above. Four tables describe one roof and the split between them is unchecked. | resolves ~$15,500 – $34,000 of boundary |

Question 1 is a choice. Questions 2 – 4 are facts somebody can go and find.

**Answered 2026-08-20** and no longer open: closet shelving (wire), ice barrier (code minimum,
as a strategy rather than a saving), pour season (summer, so cold-weather protection is zero)
and tax jurisdiction (suburban Hennepin, 8.525%). All four are recorded in the decision table
in the allowance-register section above, with their reasoning, in `prices.toml` as well as here.
