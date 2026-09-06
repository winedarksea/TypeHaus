---
title: "Interior Selections — the 2026-09-06 pass"
applied_to:
  - product: PROD-TOTO-CT449CFGT60
  - product: PROD-HARVIA-PC110E
  - product: PROD-SILESTONE-ET-CALACATTA-GOLD
  - product: PROD-ROBERN-YM0030CPFPD3
  - material: quartz-counter
  - material: oak-counter
  - material: tile-floor-24
  - material: tile-wall-1224
tags:
  - fixtures
  - lighting
  - tile
  - casework
  - hardware
  - cost
source:
  - plan/products_interior.py
  - plan/products_lighting.py
  - plan/fixture_types.py
  - plan/fixture_types_wc.py
  - plan/lighting_types.py
  - plan/lighting_types_decor.py
  - plan/assemblies.py
  - prices.toml
---

# Notes

## What this is, and what it is not

A **design and decision note** — the third kind in `notes/README.md`. It is not a
calculation note (nothing here is oracled) and it is emphatically **not a detail note**: it
is named by no `Transition.notes=` in `plan/transitions.py`, so none of this prose renders
onto a sheet and none of it is byte-pinned. The two sauna sheet lines that *did* change on
this pass live in `sauna_basement_wall_detail.md`, where they belong.

The house was fully modelled structurally and almost every interior choice was a
placeholder: twenty-odd luminaires with full photometrics and **zero** named products, five
of six toilets on an allowance type, no faucet or shower valve anywhere, no countertop as
element *or* material *or* price row, and one generic 9 kW sauna heater. This pass turned
those into structured data the schedules, the 3D sidebar and the estimate can read.

The owner's criteria, in priority order and used that way throughout: **easy to clean**,
then cost-effective ("good value, not cheap"), then popular / minimalist / "just works and
just looks decent." Palette is white + black + white oak milled off family land in southern
Minnesota. Metal finish is **brushed/satin nickel or stainless — matte black was explicitly
rejected on cleanability.** Mid tier with a few deliberate splurges.

## The five things this pass found that were wrong, not merely unspecified

These matter more than the product names, because each was passing every check.

1. **The 9 kW sauna heater was undersized, and the comment holding it named the wall it was
   standing on.** `RM-B-SAUNA` is 555 cf; every manufacturer's own table puts 9 kW at
   283–494 cf, and the "rated 9 kW to 600 cf" the model asserted matches no published table.
   10.5 kW cascades into `CKT-SAUNA` (50 A → 60 A, 9000 → 10500 VA) and into the two sauna
   notes' sheet lines, whose "240 V, 50 A, 10.5 kW max" was never arithmetic that closed:
   NEC 424.3(B) makes this a continuous load at 125%, so 43.75 × 1.25 = **54.7 A**.
2. **`RM-M-BATH2`'s 54" vanity was legal only against a code Minnesota deletes.** Its sizing
   measured to the start of the water closet's **21" IRC P2705.1** front clearance and
   reported 3¼" of slack. Minn. R. 1309.0010 subp. 3.D deletes IRC chapters 25–33; the
   envelope actually drawn and enforced is **UPC 402.5's 24"**, against which 54" cleared by
   **0.24"**. Every real skirted one-piece toilet is 28½"–30" deep, so the first real product
   put the cabinet inside a code envelope. The vanity is 51" now.
3. **Countertops were unpriced scope.** No element, no material, no `prices.toml` row — the
   entire record was one docstring line in `library/placeables/casework.py`. This is why the
   estimate total *rises* on this pass, and the rise is honest: it is scope the house always
   had and the bill never carried.
4. **The peninsula's 15" overhang is outside the quartz warranty.** `CASE-PENINSULA-120` is a
   24" carcass with a 15" knee; Caesarstone's rule is max overhang = ⅓ of depth and not more
   than 15", with ≤14" unsupported in 3 cm. 15" on 24" is 38%.
5. **`ED-T-LT-MIRROR-RING`'s "master's lit mirror" was in the hall bath**, and the 36" /
   tunable / CRI 95 spec it carried described no product that exists.

## Water closets — the split is deliberate

| Room | Product | Why |
|---|---|---|
| `RM-M-BATH1` | TOTO SP `CT449CFGT60#01` + DuoFit `WT173M` | wall-hung + rimless is the cleanability ceiling: no horizontal ledge, and the china floats clear of the floor joint |
| `RM-M-BATH2` | TOTO Carlyle II `CST614CEFGAT40#01` | one-piece skirted — no tank-to-bowl gasket line, no gap behind the tank |
| `RM-S-BATH1`, `RM-S-SUITEBATH` | TOTO Aquia IV `CST446CEMGN#01` | skirted trapway, daily-use rooms |
| `RM-A-STUBATH`, `RM-B-BATH` | TOTO Drake `CST776CEFG#01` | same Tornado Flush and CeFiONtect glaze, half the money; gives up the skirt |

All-Aquia-IV across the four workhorses is $2,152 against $1,598 for the split, and it would
still leave two tank designs. A skirt earns nothing in an attic guest bath used a few weeks
a year or a basement sauna rinse.

**The bidet decides the carrier brand, and that is a rough-in decision, not a trim one.** A
WASHLET+ routes its supply *concealed through the bowl*, and only TOTO's own DuoFit frame has
that connection — buy Geberit and a braided hose crosses the finished tile forever. Both
frames are within an eighth of 500 mm, so `FX-TOILET-WH`'s `carrier_bay_width` holds either.

## The import question, answered by category rather than yes or no

The owner asked about importing plumbing from China and cabinets from Poland. Neither answer
is a flat no and neither is a flat yes.

**Plumbing: import the exposed things, buy the concealed valve domestically.** That captures
roughly 60–70% of the available saving at a small fraction of the risk.

| Category | Verdict |
|---|---|
| In-wall shower / tub-shower valve | **Hard no** — see below |
| Deck-mount tub filler | No, unless cUPC-marked *and* given a real removable access panel |
| Freestanding floor-mount filler | **Yes** — the mixing valve is in the exposed pillar |
| Showerheads, hand showers, hoses, slide bars | **Yes** — best savings ratio in the exercise |
| Trim rings, escutcheons, hooks, bars | Yes — but *shower trim* is brand-locked to its valve body |
| Waste-and-overflow | No — concealed under the tub |

The code gate is real and Minnesota did not soften it. `Minn. R. 4714.0408` amends only UPC
408.7 and leaves **408.3 intact**, so every shower and tub-shower needs an individual **ASSE
1016** compensating valve at the point of use; DLI's own interpretation says a master ASSE
1017 valve at the water heater does not eliminate it. `Minn. R. 4714.0301` then requires the
manufacturer's mark **cast or stamped on the part** — *"field markings shall not be
acceptable."* A certificate PDF cannot cure a missing mark.

Two traps, because they are how this goes wrong quietly:

- **"cUPC certified" almost always means ASME A112.18.1 + NSF 372, not ASSE 1016.** Those are
  the cheap, common listings. A factory can show a genuine certificate that does not cover
  the item in the box. Ask for the IAPMO file number, ask whether the listing *names ASSE
  1016*, then check it yourself at `pld.iapmo.org`.
- **G1/2 (BSPP) and 1/2" NPT are the same 14 TPI about 0.02" apart**, at 55° vs 60°, parallel
  vs tapered. They cross-thread readily, hold enough to pass a pressure test, and weep six
  months later inside a wall. Export SKUs ship NPT *only if you specify it in writing per
  SKU*. Shower arms and hand showers are the exception — the US showerhead connection is
  1/2" NPSM, near-identical to G1/2, which is exactly why the exposed trim is the safe
  category.

The economics behind the hard no: landed cost is ≈1.7–2.2× the unit price in small
quantities once Section 301 (HTS 8481.80 is on List 3), the 2025 IEEPA stacking and broker
fees are counted, and **de minimis is gone** — eliminated for China in May 2025 and globally
that August — so there is no "order one and see." Against that, replacing an in-wall valve
through finished tile is **$2,000–4,500**, or $5,000–9,000+ when a discontinued field tile
forces a re-tile, versus a $300–500 saving. And the failure mode of a cheap thermostatic
valve is that the element degrades and it silently stops compensating — it stops doing the
one thing ASSE 1016 exists to guarantee. The practical gate arrives before the inspector
does: the permit runs through a licensed contractor whose licence is on the line, and most
will decline to install an unmarked concealed valve.

**Cabinets: Poland is a don't, and the owner's own mill is why.** Five things stack, and the
last is decisive: 15% Section 232 duty on the cabinets *and the parts*, plus brokerage and
$3–6k of ocean and drayage; **EU carcasses are 600 mm deep and 870 mm high** against a US 24"
and 34.5", and a 24" US dishwasher opening is not a 600 mm EU opening; no warranty recourse
across an ocean; Nobilia is German rather than Polish and sells dealer-based semi-custom
here, so there is no arbitrage; and the whole reason to import is a wood front at a low
price, which **$2/sf white oak in 4/4 and 8/4 up to 18" wide beats outright, duty-free, with
no lead time.** If you want European engineering, buy the *hardware* — Blum/Hettich ship
duty-cheap and are the part Europe is genuinely best at — and put it in domestic boxes.

The tariff timing is worth knowing: Section 232 is 25% on wooden cabinets and vanities from
2025-10-14, and the scheduled jump to 50% was **delayed one year to 2027-01-01**, so 25%
holds through 2026. If anything is imported, do it in 2026 — the 50% is scheduled, not
cancelled.

**The dining light is the owner's own import, and its risk is different from the plumbing
risk.** A luminaire is *hardwired equipment*, so NEC 110.2 / 110.3(B) require it to be listed
and installed per its listing. Buy only a fixture with a real UL/ETL/cETLus mark and verify
the mark is **on the fixture**, not merely claimed in the listing text — "FCC certified" is a
radio-emissions declaration and means nothing here. Confirm 120 V. Confirm the driver is
ELV/TRIAC-dimmable *and replaceable*, and budget a spare with the order: a captive
proprietary driver is the part that dies at 12–20 years, and on an import there is no
replacement channel at all.

## Cleanability, stated as the rules it actually reduces to

Most of the choices in this pass fall out of four rules rather than out of taste.

1. **Grout length per square foot is 144 × (1/a + 1/b).** A 24×24 gives 1.0 lineal ft/sf; a
   3×12 subway gives 5.0; a penny round gives 24+. Large-format is ~3× easier to keep clean
   than subway and ~9× easier than mosaic. Grout colour and grout chemistry come second and
   third, a long way behind.
2. **A ledge is worse than a surface.** Skirted and wall-hung toilets, a slab cabinet door
   rather than a shaker (the inside corner of a shaker rail is where cooking grease lives), a
   round bar pull rather than a square one (no flat top face to hold aerosolised oil), no
   tab/edge pulls at all (grease goes behind the tab into a gap no cloth reaches), a
   drywall shadow-gap reveal rather than a metal bead at eye level.
3. **Homogeneous beats coated.** Cultured marble is a ~0.020" gelcoat over filled polyester
   and a refinish lays down a *thinner* one; compression-moulded solid surface sands back to
   new. Silestone's satin-anodised drain profile is through-surface where "matte graphite
   black" is paint on aluminium that chips to bright metal at a cut end. SS304 pulls have no
   plating to wear through, where budget "satin nickel" wears to yellow at the thumb in five
   to eight years.
4. **The cleaner is part of the specification, and two of them are destructive.** High-pH
   cleaners — bleach, ammonia, glass cleaner, degreasers, scouring powder, melamine sponges —
   are the **#1 cause of light quartz yellowing**, ahead of UV. Ammonia and vinegar damage a
   lighted mirror's glass; Robern specifies 50/50 water and isopropyl **on the cloth, never
   sprayed on the mirror**. And acid is the one thing that removes Minnesota hard-water
   scale, which is why there is no honed marble anywhere in a shower here. Put all of that in
   the owner's manual.

## Lighting — what changed and why

**3000 K, fixed, house-wide.** The dining fixture was 2700 K and the kitchen cans 3000 K in
an open plan where you see both at once, which reads as a defect rather than as warmth. 2700 K
also pushes white paint yellow and makes white oak read orange, which is precisely this
palette's failure mode. Fixed rather than 5CCT selectable: the DIP switch gets set wrong
constantly, one can at 4000 K in a run of eight is a screaming defect, and a dedicated
phosphor gives better R9 than a warm/cool blend.

**The black baffles went white, and the glare argument survives intact.** The old spec bought
glare control with a dark absorbing ring; a **deeply regressed white reflector** hides the
source behind the aperture's own depth instead. It controls glare at least as well, the trim
disappears into a white ceiling instead of reading as a row of dark holes, and there is a
smooth surface to wipe rather than a ribbed baffle that traps dust and shows a grey halo.

**The 3" cans stay, against the review that proposed dropping them.** They are not a
stylistic inconsistency: all thirteen are in halls, closets, the laundry and the two stairs,
and they *are* the house's output split. Dropping them would push every one of those from
650 lm to 900 and over-light the circulation. Every can is on a dimmer, so trimming a living
room below 900 lm is a commissioning setting rather than a different fixture.

**COB retires the deep frosted diffuser.** The dots a tape shows are geometry: a diffuser only
blends discrete emitters when the standoff is at least one LED pitch, which at 60 LED/m means
a 16–25 mm channel — and most "slim" channels are 8–9 mm, which is why people buy slim
channel plus a frosted lens and still see dots. COB is dot-free in a shallow channel with a
light lens and does not pay the 15–30% (opal) or 40–60% (smoked) lumen tax.

**A driver is the part that dies, not the LED.** At 3 h/day, 25,000 h is 23 years, so every
LED fixture "never needs relamping" — but electrolytic capacitors are rated at 25 °C and
halve their life per 10 °C above. That single fact chose the stairwell fixture (3 × E26 on
no driver, over a chandelier lift package that also wants 3 ft of accessible level cavity
plumb above a peaked trussed ridge, and that cannot fix obsolescence anyway), put the pantry
slot's driver outside the stud bay, and is why the lit mirror is described here as a
consumable rather than discovered as one in 2032.

**The lit mirror.** The owner's requirement is an integrated LED mirror, not sconces. The
market's default "LED mirror" is **backlit** — a halo thrown at the wall behind the glass,
which photographs beautifully and puts almost nothing on a face; the tells are "halo",
"ambient glow", "floating". Robern's Vitality Perimeter is genuinely front-lit (the band is
etched into the front of the pane), round, 3000 K, CRI 90+ with R9 50+, and carries a
defogger. It is **not field-serviceable**, the warranty is one year, and reported failures
cluster at five to six years; the one line with replaceable LED strips and a seven-year
warranty (Electric Mirror Fusion) makes no round. It goes in the primary suite bath, which is
also where the type's own comment always said it belonged.

## What has to reach a trade before a wall closes

This is the part of the pass with a deadline on it.

- **Blocking, and it is the only irreversible item on the list.** A ¾" plywood strip, 12"
  wide, spanning two stud bays, ~40" to ~80" AFF, in **all five wet walls** — including the
  ones with no slide bar planned, because blocking only where today's model's screws land
  pins the house to today's model forever, and a continuous band costs about twelve dollars.
  Block the drop elbow, valve, tub spout and shower arm in the same pass, and **put grab-bar
  backing at 33–36" AFF**: without it everyone grabs the bar anyway, toggles in cement board
  work loose, and water wicks down the anchor holes into the stud bay as a concealed leak.
  Retrofit after tile is $1,500–4,000.
- **Order every vanity top drilled single-hole, in writing.** All eight lavatory faucets are
  single-hole. Field-drilling a cast top chips it and voids its warranty.
- **`RM-M-BATH1`'s carrier must be on an interior partition.** A concealed cistern in a
  `EXT_2X6` bay displaces insulation, sits outboard of the vapour control and puts
  standing water in the coldest part of a Minnesota wall.
- **`RM-A-STUBATH` is the highest-consequence rough-in in the house.** Every supply line and
  its shower valve must stay inside the thermal envelope on an interior partition.
- **A GFCI receptacle at each washlet toilet**, 6–12" AFF, offset to the rear-left cord exit,
  on **one 20 A circuit per bath** — not both washlet baths ganged. An instant-heat seat
  draws 1.2–1.4 kW while heating.
- **A concealed GFCI receptacle behind the lit mirror**, plus a full-width flat 2× blocking
  band (the outer brackets sit only ±5" from the centreline) and a conductor for a **second
  switch leg**, because the defogger must be switched independently of the lights.
- **The tub deck's access panel is 20" L × 15" H minimum** — Kohler's own dimension — serving
  the `R2707` filler body, the K-7272 waste-and-overflow and the Bask connection at once. And
  the deck stack-up is capped at 2⅛" rough + ¼"–1¼" finished, so decide it before ordering.
- **Tee a ½" hose bibb off the cold at the laundry box.** No mainstream pull-down sprayer is
  hose-threaded and every ¾"-hose-threaded utility faucet is a two-handle rigid spout with no
  spray, so the brief cannot be met by one faucet.
- **Write "unmodified ANSI A118.1 mortar" into the tile contract** where DITRA-HEAT is used.
  The membrane is impervious, so a modified latex mortar cannot air-dry and may take 14–60+
  days to cure — a setter defaulting to modified out of habit produces a floor that looks
  perfect and has a warranty of zero. And do not energise the mat until mortar and grout have
  cured (~7 days); force-drying grout with radiant heat presents as "bad grout."

## Deliberately not done

- **No countertop element.** The material tags and the price row exist; the geometry does
  not, because `library/placeables/casework.py` is explicit that countertops are not separate
  elements and inventing one is a schema change, not a selections pass. Logged in
  `plans/TODO.md`.
- **No door-hardware schema.** `DoorType` carries no lockset, hinge, lever or finish field.
  The selection is recorded as `Product` records, a retuned allowance and this note. Also
  logged.
- **No per-room lumen re-split of the 4" cans.** Moving 41 instances is a lighting-design
  pass, not a product pass, and the dimmers already provide the lever.
- **No waterfall on the peninsula** — $700–1,200 to kill the knee space at one end of a
  three-stool run, and the most dated-in-five-years detail in the current vocabulary.
- **No epoxy grout on the floors.** At a ⅛" joint on rectified 24×24 the grout is ~1% of the
  floor; epoxy's advantage is per unit of grout *surface*, matte warm-white porcelain is the
  worst possible haze substrate, and PERMACOLOR needs no sealer ever.

## Still open

- Confirm the **Aquia IV height suffix** — the researched SKU is regular height (14 15/16"
  rim), not universal.
- Confirm the **SP bowl's projection** against a spec sheet; 19.3" is the library allowance's
  figure carried unchanged, and the clearance envelope is drawn off it.
- Confirm **Delta `-SS` stainless stock** before the plumber orders; the showering line is
  being thinned and several sibling SKUs came back discontinued.
- Confirm the **Robern round unit's cleat spacing** off the sheet in the carton, and its CCT
  on the box label.
- **`RM-A-STUBATH`'s vanity contradiction** is still open: `fixture_types.py` says
  `FX-VANITY-36-SHALLOW` is used there, `fixtures.py` still places `FX-LAV-COMPACT`.
- **The studio wet bar's bowl** — if it handles ice and glassware, a vitreous-china lav is
  the wrong product and it wants a stainless bar sink.
- Take one drawing of the peninsula to three Twin Cities fabricators, and **vet the shop
  rather than the showroom**: wet cutting on every operation including hand edge-work,
  respirators on faces, and OSHA silica exposure monitoring on file.
- Prices throughout are 2026 list or street, gathered against retailers that block automated
  fetching. **They are budget figures, not quotes.**
