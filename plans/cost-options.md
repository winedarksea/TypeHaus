# Cost options — priced upgrades and downgrades

Started 2026-08-08. A running list of swaps we could make **if the number comes in tight**,
each with the line it actually moves in `houses/catlin/prices.toml`, so a decision is a
decision about dollars rather than about taste.

Rules for this file:

- Every row cites the estimate line it changes and the delta at both ends of the range.
  A swap with no number in it does not belong here yet — it belongs in TODO.md's
  "Potential cost cutting" list until someone prices it.
- **Nothing here is decided.** The plan as authored is the plan. This is the menu.
- Deltas are against the 2026-08-08 estimate (construction total $284,966 – $586,391).
  They are material-basis like the rest of prices.toml, so a real bid moves them.
- **The tree moved on 2026-08-18** and every row above the concrete one is still measured
  against the old baseline. `concrete:slab` was pricing the suspended main-floor deck at the
  slab-on-grade rate; giving it its own key took the construction total from
  $274,206 – $562,712 to **$307,330 – $627,774**. That is a correction to what the house
  already costs, not a change to the house — no geometry moved.
- A swap that changes what the house *does* — not just what it costs — says so under
  **Cost of the cut**. Those are not free money.

## Downgrades (money back)

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

Ideas from TODO.md's cost-cutting list that still need a number before they can move here:

- Remove the attic level, switch to truss + blown-in insulation. Touches framing,
  envelope_layers, floor_finishes, stairs and the ST-S2A guard at once; needs a variant,
  not an arithmetic estimate. `haus variants compare` is the tool.
- Standing seam → architectural asphalt. `envelope_layers:standing-seam` is 6,327 SF over
  two rows at **$15,817 – $37,961**, the single largest material line in the house, so
  this is the biggest lever on the list — and the one most likely to change the building.
