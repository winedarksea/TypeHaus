# Board & batten over 32" open girts — hand-worked wind check

**Oracle for `packages/engine/src/typehaus/engineering/wall_panel.py`.** Worked here first,
by hand, from the standard; the module is checked against these numbers by
`packages/engine/tests/test_wall_panel_calcs.py`. A calculation that only agrees with itself
is not verified.

Subject: `board-batten-24` — 24 ga concealed-fastener steel board & batten, 20" net
coverage — on the twenty north/south walls of the house, spanning the outer KDAT girt course
at **32" o.c.** (`CATLIN_EXT_2X6`, `PLANT_EXT_2X6_HUMID`). The east and west walls keep
`pbr-panel-26` and are **not** subjects here: PBR at these spacings is covered by ICC-ES
**ESR-4729**, which is a prescriptive path — a reviewer reads the report's table and the
question is closed.

## 1. Why this is an engineered item and not a check

Board & batten is **not a purlin-bearing profile**, and it appears nowhere in ESR-4729. The
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

    span = 32" = 2.6667 ft
    A    = 2.6667 x (2.6667/3) = 2.3704 ft^2

Taking span/3 rather than the panel's real 20" coverage is the **smaller** area and so the
**more negative** GC_p — the conservative side, and it needs no product dimension. It makes
no difference to the coefficient here: at 2.37 ft^2 we are well below the figure's 10 ft^2
knee, where the curve is drawn flat.

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

Metal Sales' 24 ga board & batten table, interpolated to a 32" span: **51 psf allowable**.
Western States, the assumed supplier, publishes none at all.

    d/c = 18.2659 / 51 = **0.358**          -> passes, margin 2.79x

**And PBR, for comparison, at the same spacing:** ESR-4729 gives ~160 psf negative, i.e.
d/c = 0.114 and a margin of **8.76x**. Against the *strength-level* number the same two read
1.68x and 5.26x, which is where the "~1.5x against ~4.5x" figures quoted during the design
pass came from — they are the same comparison on the other basis, and the ASD pair is the
one to quote, because 51 and 160 are both allowables.

**Either way the conclusion is the same and it is not "fine".** The girts were sized for
PBR. Swapping the panel spends about two-thirds of the margin that spacing was bought with,
and it spends it on the profile with no evaluation report behind it.

## 6. What is NOT checked here

- **Withdrawal of the concealed leg's fasteners — the governing limit state.** Unpublished
  at any spacing, by anyone. This is why the record is `INCOMPLETE` whatever §5 returns: a
  panel that clears the only table anybody printed has not thereby been designed.
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
