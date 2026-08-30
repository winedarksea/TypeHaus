# Sunken garden — framing-top water protection

Written 2026-08-27. Model: `params/sunken_garden.py`; quantities:
`takeoff/member_protection.py` (tape) and `edge_trim` category `beam_cap` (metal).

## What the problem actually was

The question that started this was "are the beams too exposed to rain, and should the
balcony cantilever further to shelter them". Both halves turned out to be wrong, and the
measurement is worth keeping because it is the reason nothing was cantilevered.

**Overhang does not shelter a post.** The CFD literature (Foroushani, Ge & Naylor, *Effects
of Overhangs on the Wind-Driven Rain Wetting of a Low-Rise Building*, Buildings XII / ORNL
2013) puts the fully-dry strip below an overhang at roughly **1.7–2.2x the projection**, and
finds the overhang has "almost no effect on the lower half of the facade". On a 10'-0"
pillar, 6" of overhang protects the top ~1'; 18" protects the top ~3'; the bottom half gets
nothing at any dimension you would build. Sheltering these pillars would take an overhang on
the order of 5'. And this structure is **freestanding** — open on all four sides — so an
east/west overhang does nothing at all against the south wind, which is the driving one here.

**The beams were never the wet members.** The balcony's three beams sit under `FS-SG-DECK`'s
watertight aluminium plank; the front edge already has fascia -> drip flashing -> box gutter
-> leader. What is genuinely in the weather is the six pillars, the two front girts and the
knee braces — and none of those is helped by more deck.

What IS a real defect, and what this note is about, is the **ply seam**. Every beam in this
structure is three plies of 2x12. A site-built multi-ply beam has an open joint running its
whole length between each pair of plies; it holds water and the grit that stops the water
drying, and in this climate it freezes what it holds about a hundred times a year. Fourteen
such seams here, and until 2026-08-27 nothing in the model could see or bill the membrane
that closes them.

## The detail, in the order it goes on

**1. Butyl tape, on every framing top.** `top_protection` on both `FloorSystem`s and on all
eleven beams and girts. Two SKUs, and the split matters:

| Members | Width | Tag |
|---|---|---|
| Joists, rims, blocking, the four single-ply 2x12 girts | 1.25"–1.5" | `butyl-tape` |
| The seven 3-ply 2x12 beams | **4.5"** | `butyl-tape-beam` |

A 3-2x12 is 4 1/2" across. The common 1 5/8" joist roll and even the 3 1/8" "double joist"
roll leave both ply seams — the entire point — uncovered under a roll that looks like it did
the job. The BOM carries each row's member width, read off `cross_section`, so a beam that
gains a ply re-orders wider tape instead of silently under-covering.

**2. Formed aluminium cap, on the seven built-up beams only.** `TR-SG-CAP-*`, 66 LF. The
cap laps 1/2" past each beam face and turns down 1 1/2"; `thickness` is derived from
`SPEC.back_beam` / `SPEC.balcony_beam`, not written down.

**The cap is bedded ON the tape, and that order is structural to the detail.** AWC DCA6:
aluminium must not contact copper-treated lumber — the MCA/ACQ/CA-C copper corrodes it. An
aluminium cap laid on bare KDAT would be a new defect, not a fix. The tape under it is the
dielectric. **Anything that removes the tape from these beams has to change this metal too.**

The same rule is why the tape is not optional on `FS-SG-DECK` either: that deck is aluminium
plank laid straight onto copper-treated pine, and the tape is what separates them. On
`FS-SG-PORCH` the tape is doing the ordinary job instead — the composite plank above it is
**gapped**, so rain reaches the framing tops directly, on a deck that is a roof over a porch.

**2a. The pillar tops were never covered here.** This note is exhaustive about beam tops and
says nothing about the six pillar tops under them. A 6x6 tops out 5.5" square and the
3-2x12 on it is 4.5" wide, so every one of the six leaves **1/2" of exposed upward end grain
on its east and west faces, directly under a beam whose faces shed onto it**. Six joints,
upward end grain, in the weather, on 51.4 LF of the most expensive-per-LF wood in the
structure — the six painted pillars cost more than both cast columns and all four porch
beams combined, and they are the only elements carrying a recurring repaint cost against a
100-year brief. The answer is a chamfer or bevel on the exposed rim, or a small formed drip
under the beam seat, and sealing the cut before the pillar is stood: $0–120, and the highest
durability-per-dollar item in the whole porch. Recorded in `POST_WHITE_PAINT.source`.

**2b. The beam soffit at the two cast columns.** `SUNKEN_GARDEN_COLUMN_20.source` already
specified a >=15° top wash and a level non-shrink-grout island, so the column top sheds. What
was missing is the AITC/WoodWorks **1/2"–1" standoff** — a grout island is a levelling bed,
not a standoff, and without one the KDAT soffit sits on concrete that wicks. Added 2026-08-28
*beside* the grout island, not instead of it, on both `SUNKEN_GARDEN_COLUMN_20` and
`PIER_CONCRETE_12` (PT-SG-COL is the only one of the five piers with wood landing on it). It
must be stainless, or hot-dip with an isolator: KDAT is copper-treated and eats plain steel.
This is at the beam *soffit* and so does not touch the cap/tape order at the beam *top*.

**3. Sequencing — ALL SEVEN caps go on before the joists do, since 2026-08-29.** It was
five of seven: the balcony's three beams and the porch's back pair carried their joists on
top, and only the porch's front pair was flush-framed with an open top. Dropping that pair —
which is what put `PT-SG-FCOL`'s top, and `PT-SG-BF2` with it, on concrete — put those two
caps on the same sequence as the rest. A cap over a beam that will be joisted has to be laid while
the beam top is still open, and the joists then bear on it. That is fine for a coil cap under
a 2x8's bearing area and **impossible to retrofit without pulling the deck**. It is the whole
labour half of the `beam_cap` price row; it is not a return-visit trade.

## What was deliberately not done

- **No extra cantilever**, for the reason at the top. The deck stays 21'-0" x 8'-8".
- **No metal frame.** Fortress Evolution steel prices ~$3,000–4,000 over the wood as framing
  material alone, has no 2x8 profile and no white finish, and its CCRR-0313 listing excludes
  wood support posts and hands post anchorage to an engineer. Structural aluminium posts are
  not a residential product. HSS steel columns run ~$350–750 each erected.
- **No post wrap.** A PVC wrap over a post that gets wet is a moisture trap; it hides the
  post without drying it.

## The beam tops are now also an anchor question

Two balcony heat-pump stands were bolted through `FS-SG-DECK` on 2026-08-28, eight lags
through the waterproof plank. **None of them lands on a beam, and that is deliberate**: a lag
into a beam top would pierce `TR-SG-CAP-BL*` and the butyl under it and seat in the very ply
seams this note exists to close. Every anchor lands in sacrificial 2x8 blocking instead, which
inherits `FS-SG-DECK.top_protection` and so is taped by the same rule and the same roll.

`mep.deck_equipment_support` FAILs an anchor that lands on a beam, so the cap/tape order here
is now enforced rather than merely written down. See `notes/heat_pump_deck_mounting.md` and
decision #64. **Anything that moves a stand leg has to re-check that.**

## Still open

- **`structural.deck_beam_span` grades a roof deck against a deck table.** AWC DCA6 does not
  cover a deck that is also a roof and its snow envelope stops at 40 psf against the Twin
  Cities' ~50 psf ground snow. The knee braces are outside every prescriptive table. This
  belongs on the same consultant scope as the E-W bracing and the `FT-SG-*` frost design.
- **There is no beam-cantilever check** (`checks/structural/deck.py` grades span only), so
  an overhang on a beam passes silently rather than being graded against R507.5.1's
  quarter-of-back-span limit. **This is now live, not hypothetical.** The 2026-08-28 move of
  the rear balcony pillar row onto the back-beam line left the three balcony beams with a
  real north overhang, and the arithmetic is checked by hand in `params/sunken_garden.py`
  beside `_y_rear_pillar` because nothing in the engine checks it:

  | | |
  |---|---|
  | back span (`_y_rear_pillar` → `_y_ax_front`) | 7.00' = 84" |
  | north overhang (`_y_rear_pillar` → `_y_in_n`) | 20.0" |
  | R507.5.1 limit (back span / 4) | 21.0" |
  | margin | 1.0" |

  A 1" margin is thin enough that it has to be re-checked by hand if either the rear pillar
  row or the porch depth ever moves again.

## Two span knife-edges

Both found 2026-08-28 while checking whether a longer beam was possible. Neither is a
finding today; both are one dimension change away from a red suite, and neither was written
down anywhere before. `structural.deck_beam_span` looks IRC Table R507.5(1) up on the
**joist** span the beam carries, and the table's rows are 6/8/10/12/14/16/18', so the lookup
steps down in cliffs rather than sliding.

- **Porch — 9" of joist-span headroom.** `FS-SG-PORCH`'s joists span 7.25', which reads the
  8' row → a 10.25' limit against the four porch beams' 10.00' span. At a joist span of
  8.01' the lookup drops to the 10' row (9.17') and **all four porch beams FAIL by 10"**
  at once. The 9" of headroom is the distance from 7.25' to 8.00'.
- **Balcony — the knife-edge that change retired.** `FS-SG-DECK`'s joist span is *exactly*
  10.00', reading the 10' row (9.17'). Any increase at all drops it to the 12' row (8.33').
  Against the old 8.667' beam span that was a fail on the next inch; against today's 7.00'
  there is 16" of room even after the step down. Moving the rear pillar row is what bought
  that, and it is the durability change's least visible benefit.
- **PWT treated LVL may exist after all.** `params/sunken_garden.py` rejects treated
  engineered beams on the grounds that only Parallam Plus PSL is made treated, in depths that
  exclude 11 1/4". Pro Deck Supply (Minneapolis) appears to list PWT treated LVL 1 3/4" x
  11 7/8" at $223.20/12'. Two plies over the three balcony beams is ~$970 against ~$242–413
  for the 3-2x12s — a ~$550–725 delta that *removes* the seams instead of taping them. **Not
  verified; one phone call.** If it holds, the 2026-08-23 note in that file needs rewriting.
