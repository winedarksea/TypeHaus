# Court face: LP SmartSide 38 Series panel

## Wind read (ESR-1301 Table 3A)

`structural.cladding_wind` on `W-B-S2-FR` and `W-B-S3-FR` (material `lp-smartside-smooth-panel`,
`published_cladding`, `basis="ultimate"`). Reproduced by `tests/test_cladding_ultimate_row.py`.

**Demand (worked in `catlin_truss_engineering.md` §2 and `board_batten_girt_span.md` §2).**
V_ult 115 mph, Exposure B, RC II, h = 34.7626 ft above the lowest ground, K_h 0.73071,
q_h = 21.0282 psf. Zone 5 (area 2 ft x 2/3 ft = 1.333 ft^2, under 10 ft^2 so GC_p is flat):

    outward  q_h (1.4 + 0.18) = 33.2246 psf ultimate   ->  0.6 x = 19.9348 psf ASD
    inward   q_h (1.0 + 0.18) = 24.8133 psf ultimate   ->  0.6 x = 14.8880 psf ASD

**The row (ESR-1301, reissued Feb 2026, p.6; APA PR-N124 rev. 2026-07-02 Table 3a).**
"PANEL SIDING INSTALLED VERTICALLY WITH 0.113-INCH NAILS", category 3/8, 7/16 and 19/32:
max wall stud spacing 16 in, fasteners 6 in edges / 12 in field, **71 psf** maximum ultimate wind
pressure, V_ult B 170 / C 140 / D 130. Same category at 6 in field: 133 psf. The only 24 in rows
are 19/32 (190 Series); the 38 Series (3/8) has none. fn 1: HDG plain-shank nail, 0.113 in
minimum shank, "a minimum of 2 inches" into framing; fn 2: studs SG >= 0.42; fn 3: three-second
gust at 30 ft, Zone 5, smallest area. The pressures are ULTIMATE, so the demand is compared at
33.2 psf, not 19.93.

**On-label check (16 in studs).** 33.2 <= 71 psf, d/c 0.47; V_ult 115 <= 170 (B).

**Why this wall is not on-label.** Three departures, none of which the table covers:

1. The girts are 24 in o.c., not 16 in (the row's stud spacing; the 38 Series label rating is
   16 in, CAT 2025 p.35, ESR s.4.3).
2. The girts are 1-1/2 in KDAT strapping over a vented cavity: AI 2024 p.2 "LP does not
   recommend panel siding for use over furring strips/strapping ... LP will NOT warrant for
   Buckling", and a 2-1/2 in 8d box nail bites only the 1-1/2 in girt, not fn 1's 2 in.
3. (Held on the owner's word, not the model) the vertical joints land on joint nailers.

**Off-label estimate (not a code read).**

    nail-governed:  133 / 71 = 1.87 ~ 12/6 field spacing, so 71 psf is fastener-governed.
    PR-N124 fn 2 per-fastener floor, ASD: 71 x 0.6 x (16 x 12 / 144 ft^2) = 56.8 ~ 57 lbf. Matches.
    At 24 in girts, one field nail takes 19.9348 x (24 x 12 / 144 = 2 ft^2) = 39.9 lbf
        -> d/c 39.9 / 56.8 = 0.70  (= 33.2 / (71 x 16/24 = 47.3 psf))
    panel bending, 133 x (16/24)^2 = 59.1 psf ultimate vs 33.2 -> d/c 0.56 (not governing)
    inward 24.8 psf is below both.

**Verdict.** UNKNOWN, by design, on both directions: the row's 16 in spacing and 2 in
penetration drift, and LP's strapping position is off-label. The estimate says it should
generally work (d/c ~0.70 on the nail). The owner accepted it 2026-11-24: the wall is sheltered
under the porch roof and the panel is small and cheap to replace. Caveat the estimate does not
cover: withdrawal goes with embedment, so the 1-1/2 in girt gives at most 3/4 of what a 2 in
embedment gives; the 57 lbf floor assumed 2 in. An NDS 12.2 nail read at the girt's SG (KDAT
southern pine) is the check before anyone leans on the 0.70.

`structural.cladding_fastener` is N/A for this panel: the row's pressure is the nailed
assembly's capacity, so the nail is a condition of the row (graded here), and no concealed-leg
screw or metal flange exists for the NDS screw / AISI pull-through arithmetic.
