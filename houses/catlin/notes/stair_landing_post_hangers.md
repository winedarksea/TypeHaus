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
Side-grain nailing into the post, so the p. 110 end-grain factor 0.67 does not apply.

## 4. Loads (D 12 + L 40 = 52 psf, `stair_stringers.py`'s basis)

**Rim seg1 at S.** Joists 44.75" long frame into it, so half, 22.375" (1.865'), loads the
rim; run 37.375" (3.115'). End = 52 x 1.865 x 3.115 / 2 = **151 lb** vs 610: 0.25.

**Rim seg0.** 6.5" run, same width: 52 x 1.865 x 0.542 / 2 = **26 lb** (0.04).

**joist-lower-000 at SS.** Joist 43" (3.583'); tributary 15.26"/2 + 3/4" = 8.38" (0.698'):
uniform end = 52 x 0.698 x 3.583 / 2 = 65.1 lb. The lower flight's three stringer heads
(x 171 / 191.5 / 212", 60" run) bear on it: tributaries 11.0 / 20.5 / 11.0" (midpoints,
outer faces), so 52 x (11.0/12) x 5 / 2 = 119.2, 222.1, 119.2 lb. Lever to the SS end
(x 169.75): 0.971, 0.494, 0.017 -> 115.7 + 109.7 + 2.1 = 227.5 lb. Total **292.6 lb** vs
610: **0.48** (governs). `joist-upper-000` is the mirror (upper flight feet): 292.6 lb.

The check prints 293 / 151 / 26 lb. Uplift: none (no net upward load on a stair landing).

## 5. Rim ends elsewhere

ST-B2M's wall-side rims are fastened along W-B-CN / W-B-STR full length; the north rim ends
frame into the wall-hung `landing-joist-*-004`. ST-M2S's partition rim bears 2.75" on
`landing-post-000` (R502.6: 1 1/2"), its north end on the W-M-N2 joist.

## Open

The posts' pad (`stairwell_post_pad.md`) still reads its own landing load, not these
reactions; the deck boards still lap the posts (not notched in the model).
