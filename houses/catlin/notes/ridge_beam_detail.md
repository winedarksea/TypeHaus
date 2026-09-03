# Ridge beam RB-HOUSE — section, hangers, straps (2026-08-28)

> **SUPERSEDED IN PART, 2026-08-29 — the pitch and section below are one revision behind.**
> The roof went from 4:12 to 6:12 and the ridge from `2-1.75x14 LVL` to **`2-1.75x16 LVL`**
> (CLAUDE.md's "Structural ridge, not a rafter-tie roof" bullet is the current source of
> truth on both). The plumb-cut arithmetic in §1 is worked at 4:12 and gives 14" as the
> answer; at 6:12 the same method gives **14.15"**, which 14" misses by 0.15" and 16" clears
> by 1.85" — the *shape* of the argument (depth is a hanger dimension, not a bending one) is
> unchanged, only its 4:12 numbers are stale. **§4's weights are re-struck below** because
> that scales cleanly with depth. §§2-3's fastener overlap, hanger/strap schedule and
> stiffener geometry do NOT scale as cleanly — a 6:12 rafter meets the beam face at a
> different angle than a 4:12 one did — and have not been re-derived here; treat them as
> the right *shape* of check to run again, not as still-current numbers, until an engineer
> re-runs them at 6:12.

`2-1.75x14 LVL`, 36'-0", bearing continuously on `W-A-C1/C1B/C2`. Authored in
`plan/storeys/attic.py`; graded by `structural.ridge_beam_depth`. **Section is stale — see
the banner above; the beam is `2-1.75x16 LVL`.**

> **See also `notes/fortified_roof_cert.md`.** This beam's eliminate-the-thrust argument
> below is exactly FORTIFIED Home's §2.5 "engineered alternative" to collar ties, but it is
> documented here only as engineering narrative — the cert tracking note lists a stamped PE
> letter citing §2.5/Appendix B1 as the open item that closes it. Nothing below changes for
> that; this is a pointer, not a revision.

Three plies of `3-1.75x11.875 LVL` answered no load and the depth was an inch and a half
short. No neighbouring check grades a ridge beam's depth on its own — each opts out of a
ridge beam for a reason of its own — which is why `structural.ridge_beam_depth` exists.

## 1. Why 14", exactly

**The depth is a hanger dimension, not a bending one.** The beam spans nothing: the wall
under it is unbroken for all 36'. What sets its depth is the cut on the rafter it carries.

The resolver pins the beam's top to the roof plane at the peak (the ZIP deck bears across
it) and trims each rafter back to the beam's face, where the I-joist is cut **plumb** and
hung on a sloped face-mount hanger. The hanger's seat is at the bottom of that cut. So:

| | |
|---|---|
| rafter | 11 7/8" I-joist, 4:12 |
| plumb cut | 11.875 x hypot(1, 4/12) = **12.52"** |
| face is half a beam width off the peak | 1.75" x 4/12 = **0.58"** further down the plane |
| **beam must reach** | **13.10"** below the ridge line |
| bought | **14"** — the next depth LVL is made in (9.5 / 11.875 / **14** / 16 / 18) |
| margin | 0.90" |

At 11 7/8" the joist's bottom flange and the hanger seat hung **1.52"** past the soffit,
with nothing behind them. There is no 13" or 13 1/2" LVL, so 14" is not a comfort margin —
it is the only stock depth on the correct side of the line.

IRC R802.3 says a ridge *board* shall be "not less in depth than the cut end of the rafter".
A structural ridge *beam* is outside that section — R802.3 punts it to engineering — but the
criterion is the same one, and it is the sentence to quote at a plan review.

## 2. Why 3 1/2" wide is enough, and what it costs on the drawing

Nothing about the width is structural here. The 5 1/4" it replaced came from a "6x12" ask
recorded in the code, not from a calculation.

**The one real constraint is fastener interference, and it is resolved by a clause, not by
geometry.** LSSR header fasteners are (14) 10d x 2 1/2" (IAPMO-ES ER-280 Table 11), and 28
rafter *pairs* land directly opposite one another. Two mirrored nail patterns in a 3 1/2"
beam overlap through a 1 1/2" band, and the usual escape — clinch the protruding tips on the
back face — is blocked by the other hanger.

ER-280 §3.2.2 permits the alternative outright:

> "The thickness (depth) of the wood main member shall be equal to or greater than the length
> of the fasteners specified in the tables in this report, **unless the reduced penetration
> effect on the load calculation per the applicable ANSI/AWC National Design Specification
> for Wood Construction and its Supplement (NDS) is taken into account**, or as required by
> wood member design, whichever is greater."

Each rafter delivers roughly **600 lb** to the ridge (12 sf tributary at ~50 psf) against an
LSSR2.37 rated **1,565 lb**. Shortening the header nails and taking the NDS penetration
reduction lands nowhere near the limit.

**Put the shorter fastener on the schedule.** This is the whole reason 3 1/2" is available
here, and it would not be on a beam that was working near capacity. A ridge sized by bending
rather than by a plumb cut should be 5 1/4" and take the full 2 1/2" nails.

## 3. What goes on it, per rafter and per pair

| part | count | rule |
|---|---|---|
| LSSR sloped/skewable hanger | 38 — one per rafter end | derived, `takeoff/hangers.py` |
| beveled web stiffener pair, 23/32" ply x 4" | 38 at the ridge (+38 at the eave) | derived, `resolve/framing/roof.py` |
| LSTA24 strap over the peak | 19 — one per opposing **pair** | derived, `takeoff/hangers.py` |
| H2.5A, beam to top plate | 10 — 4' o.c. plus both ends | derived, `takeoff/uplift.py` |
| SDW22 3 3/4" ply screws | 4 per hanger, one face | spec, not modelled |

**LSSR is the right part for an I-joist**, on the condition that it gets web stiffeners —
Simpson/Weyerhaeuser CSG-TJUS25 lists it for TJIs and notes "the LSSR requires web stiffeners
that are 4" wide and attached with (4) nails each side". Do not substitute LSSU on the
strength of its name.

**The strap is not optional at this pitch.** Weyerhaeuser roof detail **H5S** — the sloped-
hanger-at-a-ridge-beam detail, required above 3:12, and 4:12 is above 3:12 — calls for an
"LSTA24 (Simpson or USP) strap with twelve 10d (0.148" x 1 1/2") nails", 2 3/8" minimum end
distance. APA EWS D710 detail 10c asks for the same from 1/4:12. The hanger carries a
rafter's weight down into the beam and does nothing across the peak; the strap is what makes
the two slopes one structure. The house had a hanger per rafter and no straps until this note.

**Beveled web stiffeners, both sides, cut to the roof slope**, per Weyerhaeuser H5/H5S and
D710 10c. The house modelled them at the eave and none at the ridge for the same period.
They sit *inboard* of the plumb cut, filling the joist's own web cavity with their outer
face flush to it — which is also where the model now draws them.

**They are PLYWOOD** — 23/32" CDX each side, ripped **4" wide** for the LSSR's "(4) nails
each side". The cavity a stiffener fills is (2 5/16" flange - 3/8" web) / 2 = **15/16" a
side**, so the 2x4 the model billed until 2026-09-02 was not a material error only: a 1 1/2"
stick does not physically go in. One modelled member per rafter end stands for the pair;
`prices.toml`'s `4x1.4375 stiffener panel` row prices it as two pieces.

## 4. Ply stitching, and the two sticks

The plies are stitched with **SDW22 3 3/4"**, four per hanger, driven from one face — Trus
Joist **SE-N101** (Aug 2026) Table 1, Assembly A, side-loaded 3 1/2" 2-ply. Worth knowing
what the third ply would have cost: Assembly B (5 1/4", 3-ply) wants **5"** screws driven
from **both** faces. Deeper is cheaper than wider here, in fasteners as well as in LVL.

**Order it in three pieces.** A beam supported everywhere may be butt-spliced over any
bearing point, so the takeoff buys the 36' as **three 12-footers** off the ordinary stock
ladder rather than one over-length special order that needs a crane and a freight charge.
36'-0" divides three ways exactly, so there is no offcut, and the lineal feet — and therefore
the money — are identical either way. `FramedMember.continuously_supported` is derived from
the bearing refs actually reaching, not from their being named.

The cap is a **handling** number, not a stock one: 16' and 20' are both on the ladder.
**RE-STRUCK 2026-08-29 for the 16" section** (was 7.7 lb/ft/ply at 14" — LVL weight scales
with depth at a fixed 1.75" width, so 7.7 × 16/14 = 8.8 lb/ft/ply): a 20' ply is now **176
lb** and a 12' ply is **106 lb** — still the difference between a lift and two framers, and
still nowhere near a crane. Worth stating explicitly since it wasn't before: **even the 36'
one-piece alternative this beam avoids would only be 317 lb** (8.8 × 36) — heavy enough to
justify the three-piece order on handling and freight, but not on rigging. `_MAX_SPLICE_PIECE_FT`
in `takeoff/framing.py` holds the cap, and splicing loses whenever it would order more feet
than one stick, so the cap can never turn a one-foot overshoot into three feet of offcut.

**Stagger the splices between plies.** Cut one of ply B's three sticks in half: ply B reads
**6 + 12 + 12 + 6** against ply A's **12 + 12 + 12**, so the joints fall at 6'/18'/30' against
12'/24'. Three sticks per ply either way, no offcut, and the beam is continuous in at least
one ply at every station. Every joint lands over the bearing wall, which is the only place
any of them is allowed.

## 5. What is NOT here, and why

- **A mixed LVL + sawn sandwich.** No manufacturer permits a sawn ply in a built-up LVL
  member: LP's load tables say "plies of the same grade of LVL", Boise and Murphy list only
  LVL widths, and Weyerhaeuser's one published exception (PSL with LVL) requires *matching
  MOE* — 2.0E against a 2x's 1.6E is nowhere near. The stiffness mismatch means the sawn ply
  attracts far less than its share while reaching its own much lower Fb first, and ESR-2552
  §3.2.2 sets different maximum moisture contents for the two (19% sawn, 16% engineered), so
  the sawn ply shrinks in depth away from the LVL over a 36' run with sheathing bearing on
  top. A spacer is a spacer; it is never a ply. There is also no 2x14 stock.
- **A rafters-over-the-ridge detail.** It would make the beam's depth free, but at 4:12 it
  needs a beveled bearing plate the full 36' (Weyerhaeuser: a beveled plate is mandatory past
  1/4:12 at a 3 1/2" bearing), a birdsmouth is prohibited at the high end, and the Simpson
  VPA alternative caps at 1,105-1,245 lb with *no* duration-of-load increase. Hanging is the
  detail the model draws and the cheaper one to build.

## Sources

- IAPMO-ES **ER-280** §3.2.2 and Table 11 — LSSR/LSSJ, header thickness and fastener schedule
- ICC-ES **ESR-2552** §3.2.2 — face-mount hangers, substrate and moisture content
- Simpson / Weyerhaeuser **CSG-TJUS25** (Aug 2025) — connector selection for TJIs, note 5
- Weyerhaeuser **TJ-4000 / TJ-4500** details **H5 / H5S**, and the slope-factor table
- Trus Joist **SE-N101** (Aug 2026) Table 1 — multi-ply beam connections for hangers
- Weyerhaeuser **TJ-9000** — multi-ply nailing/bolting, top-loaded and side-loaded
- APA EWS **D710** detail **10c** — I-joist to ridge beam
- IRC **R802.3** — ridge board depth, and the referral of a ridge beam to engineering
