# Sunken garden — framing-top water protection

Model: `params/sunken_garden.py`; quantities: `takeoff/member_protection.py` (tape) and
`edge_trim` category `beam_cap` (metal).

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
such seams here.

## The detail, in the order it goes on

**1. Butyl tape, on every framing top.** `top_protection` on both `FloorSystem`s and on all
eleven beams and girts. Two SKUs, and the split matters:

| Members | Width | Tag |
|---|---|---|
| Joists, rims, blocking | 1.25"–1.5" | `butyl-tape` |
| The four 3-ply 2x12 PORCH beams | **4.5"** | `butyl-tape-beam` |
| The three BALCONY glulams | **3.5"** | `butyl-tape-beam` |

A 3-2x12 is 4 1/2" across. The common 1 5/8" joist roll and even the 3 1/8" "double joist"
roll leave both ply seams — the entire point — uncovered under a roll that looks like it did
the job. The BOM carries each row's member width, read off `cross_section`, so a beam that
gains a ply re-orders wider tape instead of silently under-covering.

**The balcony's three beams became treated GLULAM on 2026-09-03** (3-1/2" x 11-7/8",
24F-V5M1/SP; `notes/balcony_moment_columns.md` §5), which removes six of this note's
fourteen ply seams outright — a glulam arrives as one member. They keep the wide roll all
the same, at their own 3-1/2" width: an exposed framing top in weather wants a bonded
membrane whatever the member is made of, and 3-1/2" still rules out the 3 1/8" roll. The
seam argument now applies to the four PORCH beams only, and the same trade is available
there for the same money — it was not taken because nothing about the porch forced it.

**2. Formed aluminium cap, on all seven garden beams.** `TR-SG-CAP-*`, 69 LF over two
widths since the balcony's three went to glulam: 40 LF of 5 1/2" cap on the porch's
4 1/2" ply beams and 29 LF of 4 1/2" cap on the balcony's 3 1/2" glulams. The
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

**2a. The pillar tops were never covered here — and four of the six joints are gone.**
This note is exhaustive about beam tops and said nothing about the six pillar tops under
them. A 6x6 tops out 5.5" square and the beam on it is narrower, so each one leaves exposed
upward end grain on its east and west faces, directly under a beam whose faces shed onto it.
**Since 2026-09-03 only the TWO centre pillars are wood**; the four corners are cast concrete
with a screeded wash and a drip lip, which is a better answer to the same problem than any
bevel. The exposure at the two that remain is worse per joint, not better: a 3-1/2" glulam on
a 5-1/2" post leaves **1" of end grain** each side against the 3-2x12's 1/2". Two joints,
upward end grain, in the weather, on ~24 LF of the most expensive-per-LF wood in the
structure, and the only elements left here carrying a recurring repaint cost against a
100-year brief. The answer is a chamfer or bevel on the exposed rim, or a small formed drip
under the beam seat, and sealing the cut before the pillar is stood: $0–120, and the highest
durability-per-dollar item in the whole porch. Recorded in `POST_WHITE_PAINT.source`.

**2b. The beam soffit at the two cast columns.** `SUNKEN_GARDEN_COLUMN_20.source` already
specified a >=15° top wash and a level non-shrink-grout island, so the column top sheds. What
was missing is the AITC/WoodWorks **1/2"–1" standoff** — a grout island is a levelling bed,
not a standoff, and without one the KDAT soffit sits on concrete that wicks. Added
*beside* the grout island, not instead of it, on both `SUNKEN_GARDEN_COLUMN_20` and
`PIER_CONCRETE_12` (PT-SG-COL is the only one of the five piers with wood landing on it). It
must be stainless, or hot-dip with an isolator: KDAT is copper-treated and eats plain steel.
This is at the beam *soffit* and so does not touch the cap/tape order at the beam *top*.

**3. Sequencing — FIVE OF THE SEVEN caps go on before the joists do.** The balcony's three
beams and the porch's back pair carry their joists on top; the porch's front pair is
flush-framed with an open top. A cap over a
beam that will be joisted has to be laid while
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

## The beam tops were also an anchor question

**`FS-SG-DECK` carries no penetrations at all.** Two balcony heat-pump stands were bolted
through it — eight lags through the waterproof plank, every one landing in sacrificial 2x8
blocking rather than in a beam, so that no lag pierced `TR-SG-CAP-BL*` or the butyl under it
or seated in the ply seams this note exists to close. Both condensers moved to a ground pad
on 2026-09-02 (`notes/heat_pump_ground_pad.md`) and the stand, its blocking and its holes
went with them.

The rule that governed them stands and is enforced, not merely written down:
`mep.deck_equipment_support_coverage` FAILs an anchor that lands on a beam
(`notes/heat_pump_deck_mounting.md`, decision #64). **Anything that puts equipment back on
this deck has to satisfy it.**

## Still open

- **`structural.deck_beam_span` grades a roof deck against a deck table.** AWC DCA6 does not
  cover a deck that is also a roof and its snow envelope stops at 40 psf against the Twin
  Cities' ~50 psf ground snow. Still true of the four PORCH beams, which pass the table
  prescriptively. The three BALCONY beams left the table entirely on 2026-09-03 and are
  graded as `deck_beam/BM-SG-BL*` by `engineering/glulam_beam.py` — on NDS bending, shear,
  bearing and deflection with wet-service factors, which is a real design rather than a
  table lookup, though it still takes 50 psf and inherits this same snow question. The knee
  braces that were also outside every prescriptive table are gone; four fixed cast columns
  carry the lateral system and are graded as `deck_post/PT-SG-B*`. What is left for the
  consultant here is the snow envelope and the `FT-SG-*` frost design.
- **There is no beam-cantilever check** (`checks/structural/deck.py` grades span only), so
  an overhang on a beam passes silently rather than being graded against R507.5.1's
  quarter-of-back-span limit. **This is live, not hypothetical, and it got TIGHTER twice on
  2026-09-03.** First `PT-SG-BF2` moved 15" north onto the porch deck when `PT-SG-FCOL`
  shrank to a 12" round; then `PT-SG-BF1`/`BF3` moved 5 1/4" north so their beams would
  cantilever clear of the cast rounds' tops (`_y_front_pillar`). Both shortened a back span
  without moving the north overhang at all. The arithmetic is checked by hand in
  `notes/balcony_moment_columns.md` §5 and beside `_y_rear_pillar` in
  `params/sunken_garden.py`, because nothing in the engine checks it:

  | | `BM-SG-BLW` / `BLE` | `BM-SG-BLC` |
  |---|---|---|
  | back span | **7.33' = 88.0"** (was 93.25") | **6.75' = 81.0"** |
  | north overhang (`_y_rear_pillar` → `_y_in_n`) | 20.0" | 20.0" |
  | south overhang (front column axis → deck edge) | **8.0"** | 15.0" |
  | R507.5.1 limit (back span / 4) | **22.0"** | **20.25"** |
  | margin on the governing overhang | **2.0"** | **0.25"** |

  A quarter of an inch is not a margin, it is a coincidence, and two inches is not much
  better. Re-check both by hand if the rear pillar row, `_y_front_pillar`, `PT-SG-BF2`'s 3"
  offset, or the porch depth ever moves again — and note that on `BLC` the fix if it ever
  goes over is to move BF2 SOUTH toward the beam axis, which lengthens the back span, not to
  shorten the overhang (the overhang is the deck edge). **On `BLW`/`BLE` that escape is
  gone**: BF1/BF3 cannot go south without putting the 12" rounds back out past the beam
  ends, which is the ponding detail the move was made to kill. The lever there is the REAR
  row, and moving it means moving the back-beam line.

**Two span knife-edges**, both found while checking whether a longer beam was possible. Neither
is a finding today; both are one dimension change away from a red suite.
`structural.deck_beam_span` looks IRC Table R507.5(1) up on the **joist** span the beam carries,
and the table's rows are 6/8/10/12/14/16/18', so the lookup steps down in cliffs rather than
sliding.

- **Porch — 9" of joist-span headroom.** `FS-SG-PORCH`'s joists span 7.25', which reads the
  8' row → a 10.25' limit against the four porch beams' 10.00' span. At a joist span of
  8.01' the lookup drops to the 10' row (9.17') and **all four porch beams FAIL by 10"**
  at once. The 9" of headroom is the distance from 7.25' to 8.00'.
- ~~**Balcony.**~~ **OFF THE TABLE 2026-09-03.** The three balcony beams are glulam and have
  no row in Table R507.5(1) at all, so there is no lookup for a joist span to step. They are
  engineered items instead; the cliff cannot reach them.
- ~~**PWT treated LVL may exist after all.**~~ **ANSWERED, by a different product.** The
  lead was an unverified Pro Deck Supply listing for PWT treated LVL 1 3/4" x 11 7/8" at
  $223.20/12', two plies over the three balcony beams for ~$970 against ~$242–413 for the
  3-2x12s. What was bought instead is **treated SYP structural glulam, 3-1/2" x 11-7/8",
  24F-V5M1/SP** (Anthony Power Preserved / Boise Cascade, ~$35/LF through Lakeville): one
  manufactured member with published engineered values, a stocked product rather than a
  listing, and no ply seam at all. `params/sunken_garden.py`'s rejection note was about
  **Parallam Plus PSL depths** and said nothing about glulam; it has been rewritten on
  `SPEC.balcony_beam`. The four PORCH beams are still 3-ply KDAT and the same trade is
  still open for them.
