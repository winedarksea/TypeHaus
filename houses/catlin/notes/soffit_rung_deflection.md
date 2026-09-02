# Soffit ladder rungs — the deflection check, worked by hand

Written 2026-08-31. Model: `plan/storeys/second.py` (the three `Soffit` elements and their
`FramingSpec`s), `packages/engine/src/typehaus/resolve/framing/soffit.py` (the generator that
lays the members). Graded by `structural.soffit_rung_span`
(`packages/engine/src/typehaus/checks/structural/soffit.py`), which this note is the oracle
for. **A calc that only agrees with itself is not verified** — the arithmetic below was done
independently of the code, and the engine reproduces it to the third decimal.

## What had to be decided

`SF-S-HP1` is a 77" x 80" bulkhead built to hold System 1's air handler in `RM-S-STUDY2`'s
ceiling. `resolve/framing/soffit.py` framed it without
complaint, because that generator **lays rungs at any span**: it has no bearer concept, no
span table and no limit. Its rungs on this box are 72 3/4" of 2x2 at 16" o.c. Nothing in
`checks/` looked at them.

Two things follow. The rungs are what the underside gypsum hangs on, so their deflection is a
cracked-ceiling question, not an academic one. And the generator's other habit — one profile
for the rails and the rungs both — means the obvious fix (upsize the member) also **widens the
rails and eats the cavity**: a trial `2x2`->`2x4` produced
`FAIL (error) mep.duct_soffit_occupancy: … EQ-S-ERV-MIX … outside its clear cavity`.

## Load case, and what is deliberately not in it

| term | value | why |
|---|---|---|
| Dead load | **5 psf** | 5/8" gypsum on the underside and both returns (~2.75 psf), the ladder lumber itself, and a light-fixture allowance. |
| Live load | **none** | Nothing walks on a soffit and nothing is stored in one. IRC Table R301.5 has no line for the underside of a bulkhead; inventing one would be a load case adopted to look conservative rather than to be right. |
| Tributary | **16"** | The station spacing the generator actually laid, read back off the members rather than off `FramingSpec.spacing` — the module grid, not the authored input, is what got built. |
| E | **1,400,000 psi** | SPF No.2, NDS Supplement Table 4A. The same modulus the deck and joist tiers use; a soffit rung is ordinary dimension lumber. |
| Limit | **L/360** | IRC Table R301.7, ceiling with brittle finishes. Gypsum is exactly that. |

No span table publishes a 2x2 ceiling rung — IRC Table R802.5.1 starts at 2x4 and assumes an
attic — so the limit is computed, not looked up. The five inputs above are the whole of it.

## The section, and why "laid flat" is the load-bearing word

`_frame_one` lays every soffit member **flat**: a rung gets a z-band of one stock *thickness*
(1.5"), so it bends about its **weak** axis. That is the right build — a flat rung is a nailer
for the board below — but it means `b` and `h` swap, and I grows with depth *linearly*
instead of cubically.

    I = b h³ / 12,   with b = dressed depth, h = dressed thickness (1.5")

| nominal | dressed | I laid flat |
|---|---|---|
| 2x2 | 1.5 x 1.5 | 1.5 x 1.5³ / 12 = **0.4219 in⁴** |
| 2x3 | 1.5 x 2.5 | 2.5 x 1.5³ / 12 = **0.7031 in⁴** |
| 2x4 | 1.5 x 3.5 | 3.5 x 1.5³ / 12 = **0.9844 in⁴** |

## The arithmetic

Uniform load per inch of rung, at 16" tributary:

    w = 5 psf x (16/12 ft) / 12 in/ft = 0.5556 lb/in

Simply supported, uniformly loaded — a rung spans between two rails and nothing continuous
crosses it:

    δ = 5 w L⁴ / (384 E I)

At L = 72.75" (SF-S-HP1's clear cavity), L⁴ = 2.8005e7 in⁴:

| rung | I | δ | L/δ | verdict |
|---|---|---|---|---|
| **2x2** | 0.4219 | 5(0.5556)(2.8005e7) / (384 · 1.4e6 · 0.4219) = **0.343"** | **L/212** | fails |
| 2x3 | 0.7031 | **0.206"** | **L/353** | still fails — and by only 2% |
| **2x4** | 0.9844 | **0.147"** | **L/495** | passes |

Bending and shear are not stated. On a 5 psf ceiling over a six-foot 2x2 they are nowhere near
governing, and quoting a stress ratio for them would dress an arithmetic identity as analysis.

**The 2x3 line is why the interim recommendation in this house's own notes was wrong.** It
assumed the rung stood on edge (I = 1.9531 in⁴, δ = 0.074", L/978). Flat, it fails.

## The other two boxes, as a discrimination check

A limit that fails everything is not a limit. The same arithmetic at the other two spans:

| soffit | rungs | L | I | δ | ratio |
|---|---|---|---|---|---|
| SF-S-DUCT | 19 x 2x2 | 30.75" | 0.4219 | 0.0109" | **L/2808** |
| SF-S-SUITE | 4 x 2x2 | 31.75" | 0.4219 | 0.0124" | **L/2551** |
| SF-S-HP1 | 4 x 2x4 | 72.75" | 0.9844 | 0.147" | **L/495** |

Two orders of magnitude between the passing boxes and the failing one, because δ goes as L⁴.
The check fails exactly one soffit in this house, which is the right number.

## The fix, and why it is `plate_member` and not a bigger member

`FramingSpec.plate_member` already existed and was already documented as "the plate size when
it differs from `member`"; the rails were already emitted with category `"plate"`. They were
simply never read here. `_ladder_stock(spec)` now returns `(plate_member or member, member)`
and `_frame_one` threads two profiles: **rails, ladder studs and end blocking on the rail
profile; rungs on the rung profile.** `soffit_clear_section` mirrors it, subtracting only the
rail depth from `across`.

So on `SF-S-HP1`:

    framing=FramingSpec(member="2x4", plate_member="2x2", spacing=inch(16))

- `across` is **still 72.75"** — the rails are still 2x2, so the cavity width does not move,
  and `EQ-S-ERV-MIX` stays in the box.
- `along` is unchanged — every 2x is 1.5" thick, and `along` is set by the end blocking.
- **`z[0]` does not move** — the rung is still laid flat at 1.5". This is the point that made
  this the right design rather than merely a working one: `DU-S-HP-RET` is a **14" duct in a
  14.25" cavity** before the box was deepened, and any fix that moved `z[0]` — an on-edge
  rung, a deeper rung, a mid-height bearer — would have forced the return plenum and the ERV
  feed to be re-authored on top of everything else.

Defaulting `plate_member` to `member` leaves every soffit that does not set it framed
byte-identically, which is why nothing else in the house moved.

## Rejected alternatives

- **An intermediate bearer.** Mid-`across` on SF-S-HP1 lands *inside the air handler*, and the
  only free lanes are the south-branch riser and the ERV feed. Building it would also force
  `SoffitClearSection` from one interval into lanes, rewriting `soffit_occupancy`,
  `duct_soffit_occupancy` and its PASS message — a large change to the most carefully argued
  check in the MEP tier, for a member that cannot be built.
- **Honouring `FramingSpec.direction`.** The box is 77 x 80 and the rungs already span the
  shorter axis. Forcing the other way gives 75.75" — *worse*. `direction` being ignored here
  is correct: "run the ladders the long way" is what a ladder *is*, not a preference.
- **Splitting SF-S-HP1 into two rectangles.** Split in x and neither half is wider than the
  43 1/2" cabinet. Split in y and `long_axis` flips to x, re-grading every occupant across the
  wrong dimension — precisely the inversion the 80"-over-77" ordering exists to prevent.

## What the check does not do

It grades **deflection only**, on the **longest** rung in each soffit, against a **derived**
tributary. It says nothing about the rail-to-deck fastening, nothing about the hanger spacing,
and nothing about a soffit carrying anything other than its own board — a soffit asked to hold
a piece of equipment off its rungs is outside this note. A soffit with no `FramingSpec` gets
**no finding at all**, not UNKNOWN: it is drawn but not built, there is no lumber to grade, and
`mep.duct_soffit_occupancy` already reports the missing spec once.
