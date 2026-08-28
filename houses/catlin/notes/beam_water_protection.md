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

**3. Sequencing — five of the seven caps go on before the joists do.** The balcony's three
beams and the porch's back pair carry their joists on top; only the porch's front pair is
flush-framed with an open top. A cap over a beam that will be joisted has to be laid while
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

## Still open

- **`structural.deck_beam_span` grades a roof deck against a deck table.** AWC DCA6 does not
  cover a deck that is also a roof and its snow envelope stops at 40 psf against the Twin
  Cities' ~50 psf ground snow. The knee braces are outside every prescriptive table. This
  belongs on the same consultant scope as the E-W bracing and the `FT-SG-*` frost design.
- **There is no beam-cantilever check** (`checks/structural/deck.py` grades span only), so a
  future south overhang would pass silently rather than be graded against R507.5.1's
  quarter-span limit — 26" on these beams.
- **PWT treated LVL may exist after all.** `params/sunken_garden.py` rejects treated
  engineered beams on the grounds that only Parallam Plus PSL is made treated, in depths that
  exclude 11 1/4". Pro Deck Supply (Minneapolis) appears to list PWT treated LVL 1 3/4" x
  11 7/8" at $223.20/12'. Two plies over the three balcony beams is ~$970 against ~$242–413
  for the 3-2x12s — a ~$550–725 delta that *removes* the seams instead of taping them. **Not
  verified; one phone call.** If it holds, the 2026-08-23 note in that file needs rewriting.
