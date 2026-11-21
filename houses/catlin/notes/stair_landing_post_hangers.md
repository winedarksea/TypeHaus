# ST-B2M landing framing on the well posts (2026-11-20)

Hand check for `resolve/stairs/post_cuts.py`, `joints/column_hung.py` and
`structural.landing_rim_support`. Owner-approved: a landing rim meeting an authored column
stops at its faces and hangs there; a rim running past a column is split at the faces.

## 1. What the columns are

| Column | Size | Plan box (in) | Height |
|---|---|---|---|
| P-M-STRWELL-SS | SPF 4x4 (`POST_CONCEALED_SPF`) | x 166.25..169.75, y 372.375..375.875 | PD-B-WELL top (-108.26") to main floor (0) |
| P-M-STRWELL-S | SPF 4x4 | x 166.1875..169.6875, y 382.375..385.875 | same |

Both stand through ST-B2M's two half-landings (lower framing -66.39..-59.14", upper
-59.02..-51.77"); ST-M2S's corner post (`landing-post-000`) stands on S's top.

## 2. What met them before, and what does now

Before: `landing-rim-lower-0` and `landing-rim-upper-1` (2x8, x=168", y 373.375..423.25")
started 2 1/2" inside SS and passed straight through S; `landing-joist-lower-000` /
`-upper-000` (y=374.125") ended on SS's centreline, 1 3/4" inside it. No connection.

Now (each piece hung at a post face on an LUC26Z):

| Member | Run | Ends |
|---|---|---|
| landing-rim-lower-0-seg0, -upper-1-seg0 | y 375.875..382.375 (6.5") | SS north face / S south face |
| landing-rim-lower-0-seg1, -upper-1-seg1 | y 385.875..423.25 (37.375") | S north face / frames into `landing-joist-*-004` (hung on W-B-N2) |
| landing-joist-lower-000 | x 169.75..212.75 (43") | SS east face / W-B-CN rim |
| landing-joist-upper-000 | x 123.25..166.25 (43") | W-B-STR rim / SS west face |

Eight LUC26Z: four on SS, four on S. The seg0 pieces are the slot's stud seats
(`well_wall.py` cuts the slot studs round them).

## 3. The part

C-C-2026 p. 110: LUC is the concealed-flange hanger "ideal for end of ledger/header or post
conditions". An LUS28's 1" outside flanges make it 3 9/16" wide (p. 112), wider than a 4x4's
3 1/2" face. LUC26Z is the 2x8 joist-size row: W 1 9/16", H 4 3/4" (66% of 7 1/4"), B 1 3/4",
(6) 0.162x3 1/2 header, (4) 0.148x1 1/2 joist. SPF/HF, p. 119: uplift 630, **floor (100) 610 lb**.
Side-grain fastening into the post, so the p. 110 end-grain factor 0.67 does not apply. Floor
(100) is the column for D + L floor/stair live load (C_D = 1.0).

**Screwed, not nailed (review 2026-11-20).** S carries a hanger on its south AND north face at
each seat (seg0 / seg1), and SS one on its north and one on its east (or west) face at a seat.
A 0.162x3 1/2 header nail goes ~3 7/16" into a 3 1/2" post, so opposite faces' nails would meet.
p. 26 (load adjustment for optional fasteners, face-mount hangers, straight download/uplift):
0.162x3 1/2 -> #10x1 1/2 SD screw **1.00**; 0.148x1 1/2 -> #9x1 1/2 SD screw **1.00**; fn. 5, no
mixing nails and screws in one connection. So each LUC26Z takes (6) SD10112 into the post and
(4) SD9112 into the member, at the table's 610 / 630 lb. Each side reaches ~1 7/16" into the
post: opposite faces stay ~5/8" apart. On SS the north (rim) and east/west (joist) hangers at
one seat can only reach the same ~1/2" x 1/2" column by the corner. Drive the second hanger's
screws clear of the first's. The fastener schedule is `connector_schedules.py`.

## 4. Loads (D 12 + L 40 = 52 psf, `stair_stringers.py`'s basis)

**Rim seg1 at S.** Run 37.375" (y 385.875..423.25). Joists 001/002/003 (44.75" = 3.729')
frame into it at y 389.375 / 405.375 / 421.375. Their tributaries are 15.625 / 16.0 / 8.94"
(half the gap each side: 001-002 is 16", 000-001 is 15.25", 003-004 is 1.875"). End reactions
are 52 x (15.625/12) x 3.729 / 2 = 126.2, then 129.3 and 72.2 lb. Lever to S's face:
1 - 3.5/37.375 = 0.906, 1 - 19.5/37.375 = 0.478, 1 - 35.5/37.375 = 0.050, giving
114.4 + 61.8 + 3.6 = **179.9 lb** vs 610: **0.29**. Smearing half the joist length along the
rim (52 x 1.865 x 3.115 / 2 = 151 lb) under-reads it, because joist 001 lands 3 1/2" off the
post. The check takes the larger of the two.

**Rim seg0.** No joist lands on its 6.5" run. The smeared strip is kept as a floor:
52 x 1.865 x 0.542 / 2 = **26 lb** (0.04).

**joist-lower-000 at SS.** Joist 43" (3.583'); tributary 15.26"/2 + 3/4" = 8.38" (0.698'):
uniform end = 52 x 0.698 x 3.583 / 2 = 65.1 lb. The lower flight's three stringer heads
(x 171 / 191.5 / 212", 60" run) bear on it: tributaries 11.0 / 20.5 / 11.0" (midpoints,
outer faces), so 52 x (11.0/12) x 5 / 2 = 119.2, 222.1, 119.2 lb. Lever to the SS end
(x 169.75): 0.971, 0.494, 0.017 -> 115.7 + 109.7 + 2.1 = 227.5 lb. Total **292.6 lb** vs
610: **0.48** (governs). `joist-upper-000` is the mirror (upper flight feet): 292.6 lb.

The check prints 293 / 180 / 26 lb. Uplift: none (no net upward load on a stair landing).
Per post, at 52 psf: SS carries 293 + 293 + 26 + 26 = 638 lb, S carries 26 + 26 + 180 + 180 =
412 lb (`stairwell_post_pad.md` §2 takes these at 55 psf).

## 5. Rim ends elsewhere

ST-B2M's wall-side rims are fastened along W-B-CN / W-B-STR full length; the north rim ends
frame into the wall-hung `landing-joist-*-004`. ST-M2S's partition rim bears 2.75" on
`landing-post-000` (R502.6: 1 1/2"), its north end on the W-M-N2 joist. The check reads the
wall-side rims geometrically. It does not grade their fastening to the studs.

## 6. Landing ledgers (Task B, 2026-11-20)

Each wall-side landing rim / end joist was drawn coincident with a 2x10 "ledger" board, its
top flush, so the board hung 2" below the 2x8 framing and the landing soffit board ran
through it. One board cannot occupy that place twice: the rim (or end joist) lying on the
wall face IS the ledger, fastened to the studs. Removed (member now carries the
`framed-wall-ledger:` tag alone):

| Stair | Board removed | Member that is the ledger |
|---|---|---|
| ST-B2M | ledger-W-B-CN-landing-rim-lower-1 | landing-rim-lower-1 |
| ST-B2M | ledger-W-B-STR-landing-rim-upper-0 | landing-rim-upper-0 |
| ST-M2S | ledger-W-M-C5B-landing-rim-lower-1 | landing-rim-lower-1 |
| ST-M2S | ledger-W-M-STRW-landing-rim-upper-0 | landing-rim-upper-0 |
| ST-M2S | ledger-W-M-N2-landing-joist-lower-003 | landing-joist-lower-003 |
| ST-M2S | ledger-W-M-N2-landing-joist-upper-003 | landing-joist-upper-003 |

A landing ledger off the face (none in catlin) now takes the member's own depth, bottom
flush. The concrete hanger bands on W-B-N2 (`hanger-W-B-N2-landing-joist-*-004`, 8") are
clipped at the joist underside (3/4" was below it). Stringer ledgers (2x10 inside 2x12
stringers, W-B-CN, W-B-STR3, W-S-SS2) are unchanged: none projects below its stringer.

## 7. Deck and riser at the posts (review 2026-11-20)

`riser-landing` stood on the post line (x 167.75..168.5) through both posts, and both decks
lapped the posts' halves. `post_cuts.py` now cuts a riser board at the post faces the way it
cuts the rims (`riser-landing-seg0` y 375.875..382.375, `-seg1` 385.875..423.25, one nosing
lip each). It also notches each landing deck round a post standing through it (the deck's
`plan_outline`; a post wholly inside a deck would need a hole and is left alone). Nothing of
ST-B2M overlaps either post now.

## Open

- **Joists into rims take no hanger.** Every landing joist frames into a rim (or the rim on a
  wall face) end-on, with no hanger and no ledger strip. IRC R502.6 / R502.6.2 ask for one of
  the two. Nothing grades or bills it. The u_split layout runs joists to the rim centrelines,
  so deriving the hangers means trimming the joists first.
- **Rim-on-wall fastening is ungraded.** The rim on a framed wall face is the ledger. Its
  nails/screws into the studs have no catalogued part or published capacity here. The old
  2x10 board was billed as one LUS each (a proxy, not its fastening), and that proxy left
  with it.
