# Board & batten over 24" open girts — hand-worked wind check

**Oracle for `packages/engine/src/typehaus/engineering/wall_panel.py`.** Worked here first,
by hand, from the standard; the module is checked against these numbers by
`packages/engine/tests/test_wall_panel_calcs.py`. A calculation that only agrees with itself
is not verified.

Subject: `board-batten-24` — 24 ga concealed-fastener steel board & batten, 20" net
coverage — on the twenty north/south walls of the house, spanning the KDAT girt course at
**24" o.c.** (`CATLIN_EXT_2X6`, `PLANT_EXT_2X6_HUMID`).

The east and west walls keep `pbr-panel-26` and are **not** subjects here. **ESR-4729 does
not cover this wall at all.** It is Western States' report, it covers ROOF panels only, and
it is written for 24 ga minimum over 16 ga steel supports. PBR's wall capacity has to be
read off a manufacturer's own wall table, and it is: ASC Building Products' PS230, Metal
Panels Inc. and Homewood all publish 144-168 psf allowable negative at a 3'-0" span, which
is 6x or better at 24". That is still a table a reviewer can read, so PBR stays prescriptive
and out of the register — but on the strength of a span table, not of an evaluation report
that never governed it.

## 1. Why this is an engineered item and not a check

Board & batten is **not a purlin-bearing profile**, and no evaluation report covers it. The
only published capacity for it is a manufacturer's own span table; the manufacturers
disagree about whether open girts are permitted at all; and the limit state that actually
governs a concealed panel — withdrawal of the hidden leg's screws — is published by nobody
at any spacing. Western States states the consequence directly: *"consult a design engineer
for load and design calculations."*

Of eight manufacturers surveyed, **two permit open framing**: Western States (*"most details
in this guide are shown with panels attached to open framing"*) and Metal Sales. McElroy
lists solid deck only; Lyon caps furring at 18"; Best Buy Metals says solid decking.
**Substituting one of the other six forces a second girt course or a continuous OSB layer,
which costs more than the panel switch itself** — which is why it is written into the
`prices.toml` row as well as here.

## 2. Velocity pressure — ASCE 7-16 §26.10

Site basis (`plan/site.py`, and see `notes/catlin_truss_engineering.md` for its derivation):
V_ult **115 mph** (MN Rules 1309.0301), Exposure **B**, Risk Category **II**, K_zt **1.0**
(§26.8.2, flat suburban parcel), K_d **0.85** (Table 26.6-1), K_e taken as **1.0** (§26.9
permits it; the tabulated value at this site's 830 ft is 0.97, so 1.0 is conservative).

Mean roof height, RF-HOUSE:

    eave  6.384925 m  = 20.9479 ft
    ridge 9.220200 m  = 30.2500 ft
    h = (20.9479 + 30.2500) / 2 = 25.5990 ft

K_z, Table 26.10-1, Exposure B (z_g = 1200 ft, alpha = 7):

    K_z = 2.01 (z/z_g)^(2/alpha) = 2.01 x (25.5990/1200)^(2/7)
        = 2.01 x (0.0213325)^0.285714
        = 2.01 x 0.333106
        = 0.669544

q_h, eq. 26.10-1:

    q_h = 0.00256 x K_z x K_zt x K_d x K_e x V^2
        = 0.00256 x 0.669544 x 1.0 x 0.85 x 115^2
        = 0.00256 x 0.669544 x 0.85 x 13,225
        = 19.2679 psf              (strength level)

## 3. Cladding pressure — ASCE 7-16 §30.3, Fig. 30.3-1 (walls)

Effective wind area (§26.2), span x effective width, width not less than span/3:

    span = 24" = 2.0000 ft
    A    = 2.0000 x (2.0000/3) = 1.3333 ft^2

Taking span/3 rather than the panel's real 20" coverage is the **smaller** area and so the
**more negative** GC_p — the conservative side, and it needs no product dimension. It makes
no difference to the coefficient here: at 1.33 ft^2 we are well below the figure's 10 ft^2
knee, where the curve is drawn flat, so nothing in §2-§4 moves with the girt spacing.
**The demand is unchanged. The whole of the girt-spacing gain in this note is on the
capacity side.**

    Zone 5 (corner):  GC_p = -1.4
    Zone 4 (field):   GC_p = -1.1
    GC_pi = +-0.18    (Table 26.13-1, enclosed; taken with the sign that worsens suction)

    p(zone 5) = q_h (GC_p - GC_pi) = 19.2679 x (-1.4 - 0.18) = -30.4432 psf   strength
    p(zone 4) =                     19.2679 x (-1.1 - 0.18) = -24.6629 psf   strength

**Zone 5 governs what gets ordered.** A wall panel is one product and runs through both
zones; nobody orders two gauges for one elevation.

## 4. To ASD — §2.4.1

Every capacity this house cites (NDS, ICC-ES, IAPMO UES, and a manufacturer's span table)
is an **allowable**. Wind acts at 0.6W in the ASD combinations, so the demand has to come to
the same basis before the two are set beside each other:

    zone 5:  0.6 x 30.4432 = **18.2659 psf**
    zone 4:  0.6 x 24.6629 = 14.7977 psf

## 5. Panel bending — the only limit state anybody published

Metal Sales' 24 ga board & batten table, read at a 24" span: **58 psf allowable outward**
(suction), 43 psf inward. Western States, the assumed supplier, publishes none at all.

    d/c = 18.2659 / 58 = **0.315**          -> passes, margin 3.18x

Suction is what is graded, because suction is what governs a wall panel: it is the negative
zone-5 pressure of §3 that pulls the panel off its fasteners. The inward 43 psf is recorded
because it is the smaller of the two, and against the same 18.27 psf demand it is d/c 0.43 —
still passing, and still not the limit state that matters.

**And PBR, for comparison, at the same spacing:** the wall tables named in the header give
144-168 psf allowable negative at 3'-0", so at 24" it is ~6x that demand or better against
board & batten's 3.18x. The ASD basis is the one to quote, because both capacities are
allowables.

**The girts were sized for PBR, and swapping the panel still spends most of the margin the
spacing was bought with.** The 24" course module buys back some of it, closing the profile
with no evaluation report behind it to 0.32.

## 6. What is NOT checked here

- **Withdrawal of the concealed leg's fasteners — the governing limit state.** Unpublished
  at any spacing, by anyone. This is why the record is `INCOMPLETE` whatever §5 returns: a
  panel that clears the only table anybody printed has not thereby been designed. What the
  house DOES specify for it is the screw itself: 1-1/2", stainless or ASTM A153 Class D HDG,
  never the 1" plated pancake screw a panel order ships with — see the `board-batten-24` row
  in `prices.toml`. It has to take the full thickness of the 1-1/2" KDAT girt, because there
  is no sheathing behind the nailer to catch a short one. Metal Sales' own detail asks for
  1/2" past the inside face of the support, which no 1-1/2" screw in a 1-1/2" girt can give;
  that needs a written variance and is an open item.
- The girt itself in bending, and its block-to-stud connection (`structural.girt_course_spacing`
  holds the spacing; nothing grades the stick).
- Panel deflection, and thermal movement over a continuous run.
- Whether the supplier actually named on the order permits open framing (§1).

## 7. What a seal has to cover

`wall_panel/W-M-S1` and its nineteen siblings, per `docs/engineering-toml-format.md`. One
stamp may cover all twenty — they are the same panel, the same spacing and the same wind —
but the register keeps them per element so that moving one wall stales that wall alone.
The engineer's fee is plausibly already inside `permits-design-testing-and-insurance`
($20k-60k in `prices.toml`); no new cost line was added for it.
