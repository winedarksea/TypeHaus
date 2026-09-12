# Board & batten over 24" open girts — hand-worked wind and withdrawal check

**House:** catlin, Ramsey County, Minnesota (MN Residential Code 2020, adopting the 2018 IRC).
**Structure:** the twenty north/south walls clad in `board-batten-24` over a 24" girt course.
**Written:** by hand, from the standards, before the modules were encoded.
**Oracle for:** `engineering/wall_panel.py` and `engineering/wall_panel_withdrawal.py`;
reproduced by `tests/test_wall_panel_calcs.py`. A calculation that only agrees with itself
is not verified.
**What is asked of the reviewer:** §5 and §6 — both limit states are now graded, and the
question is whether the NDS rational design in §6 is the right one, not whether a number is
missing.

Subject: `board-batten-24` — **Metal Sales BB75-1111**, a 24 ga concealed-fastener steel
board & batten panel, **11" net coverage**, 3/4" rib — on the twenty north/south walls of
the house, spanning the KDAT girt course at **24" o.c.** (`EXT_2X6`,
`PLANT_EXT_2X6_HUMID`).

**Revised 2026-09-11: the product is now named, and the item is now stampable.** Two things
changed and nothing else did. The panel was an unnamed "24 ga board & batten, 20" coverage"
with an allowable borrowed from Metal Sales' table; it is now the Metal Sales product
itself, so the 58 psf is the named product's own number and its guide's substrate language
is on-label for this wall (§1). And the withdrawal allowable that §6 used to record as
*unpublished by anyone* is now **computed** from NDS 2018 §12.2 — a rational design, which
is exactly what IAPMO UES ER-309 authorises a design professional to do, rather than a wait
for a row nobody is going to print. The panel screw goes from 1-1/2" to **2"** as a direct
consequence: see §6.

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
at any spacing. That is decision #65's case: a real requirement outside the prescriptive
tables, with a computed demand and a capacity a seal can confirm.

**The substrate question is closed, on the named product's own words.** Metal Sales'
BB75-1111 Board & Batten install guide (2025-10) states on p.6 that the panel is *"designed
to be installed over open framing and/or directly over a wood substrate"*, and its list of
support materials includes **"Lumber – 1x or thicker"**. This wall's support is a 1-1/2"
KDAT 2x4 laid flat — 1x or thicker, and open framing. The panel is on-label here, quoted
rather than inferred, and the quote is authored onto the material as
`Material.open_framing_source` so the calculation refuses to grade a panel whose literature
does not say it (§6.1).

That is the change that made naming the product worth the panel-count cost. Of eight
manufacturers surveyed, only two permit open framing at all — Western States and Metal
Sales — and Western States, examined closely, publishes no load data for anything (§7).
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

## 5. Panel bending — read off the named product's own table

Metal Sales BB75-1111, 24 ga, read at the guide's 2'-0" fastener spacing: **58 psf
allowable outward** (suction), 43 psf inward.

    d/c = 18.2659 / 58 = **0.315**          -> passes, margin 3.18x

This is now the product's own number rather than a nearest-match borrowed from a table for
some other panel, which is most of what naming the product bought. The table's stated basis
is AISI 2016, three or more equal spans, L/180 deflection, no 1/3 stress increase — and its
note 2 says the allowable *"does not address web crippling, **fasteners, support material**
or load testing."* **That exclusion is why §6 exists**: the published number is bending and
only bending, and the manufacturer says so.

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

**A reading rule that makes the table quotable at all.** The guide's *"fastener spacing"* is
measured **along the panel's length**, not across it. For a panel run VERTICALLY over
horizontal girts — which is this wall — the fasteners land on the girts, so the table's
2'-0" column really is this wall's 24" girt spacing. It would **not** coincide for a
horizontally-run panel, and quoting this number for one would be wrong.

## 6. Withdrawal of the concealed leg's screws — NDS hand pass

**This is the limit state that governs a concealed panel, and it is now computed.** Nobody
publishes a pull-out value for a board-and-batten leg screwed into wood; the panel maker's
own table excludes fasteners by name (§5). What closes it is not a table but the code's own
equation, and IAPMO UES ER-309 states in as many words that *"the structural design
professional may rationally design other fastener and substrate combinations based on
engineering mechanics"*. NDS 2018 §12.2 is that mechanics.

**The fastener.** #10-12 x 2" pancake head **wood screw**, Type 17 point, 316 stainless or
ASTM A153 Class D HDG. D = **0.190"** (the #10 shank).

**The support.** The 24" girt course: KDAT 2x4 laid flat, so **1-1/2"** of southern yellow
pine, G = **0.55** (NDS 2018 Table 12.3.3A, "Southern Pine"). There is no sheathing behind
the nailer to catch a short screw.

### The equation, term by term

    W  = 2850 G^2 D                            NDS 2018 §12.2.1, lb per inch of penetration
       = 2850 x 0.55^2 x 0.190
       = 2850 x 0.3025 x 0.190
       = **163.80 lb/in**

    W' = W x C_D x C_M x C_t x C_eg            §12.2.3 / Table 11.3.1
       = 163.80 x 1.6 x 0.7 x 1.0 x 1.0
       = **183.46 lb/in**

| Factor | Value | Why |
|---|---|---|
| C_D, load duration | 1.6 | NDS Table 2.3.2, wind. The demand is a wind suction; a fastener is not exempt from the factor the rest of the house's wind capacities use. |
| C_M, wet service | 0.7 | NDS Table 11.3.3, withdrawal of a screw in a member that will be above 19% MC in service. A rainscreen cavity wets and dries with the weather. The same call `library/hardware.py` makes for this house's exterior connectors. |
| C_t, temperature | 1.0 | Table 11.3.4: sustained service below 100 °F. |
| C_eg, end grain | 1.0 | §12.2.4 would put it at 0.75 for a screw into end grain. Every screw here is into the side grain of a flat-laid 2x4. |
| C_i, incising | — | **Not applicable.** Table 11.3.1 lists no incising factor for connections, and KDAT SYP is not incised in any case. |
| treatment | — | **None.** NDS applies no reduction for preservative treatment to withdrawal; the treatment governs the fastener's *coating*, which is why the screw is stainless or A153-D. |

### Thread penetration — the two deductions a spreadsheet forgets

The panel's own flange is not the support, and the tapered tip carries no thread (NDS
App. L puts a wood screw's tip at 2D). What is left is capped at the support's thickness: a
screw that runs out the back of a 1-1/2" girt is not holding 2" of wood.

    p = length − flange − 2D,   capped at the girt
      = 2.000 − 0.0239 − 0.380 = 1.596"  ->  capped at **1.500"**

    capacity  Z = W' p = 183.46 x 1.500 = **275.2 lb**

### The demand

One screw per panel per girt — the batten hides a single line of fasteners at each support.
The tributary area is the girt spacing by the panel's **11" net coverage**:

    A = (24/12) x (11/12) = **1.8333 ft²**
    P = 18.2659 x 1.8333 = **33.49 lb**

    d/c = 33.49 / 275.2 = **0.12**

### Screw length is the whole answer, so the alternates are printed

| Screw | Penetration | Capacity | d/c |
|---|---|---|---|
| 1" (what a panel order ships with) | 0.596" | 109 lb | 0.31 |
| 1-1/2" (what this house specified until 2026-09-11) | 1.096" | 201 lb | 0.17 |
| **2" (specified)** | **1.500"** | **275 lb** | **0.12** |

All three pass the arithmetic. The 2" is specified for a different reason: Metal Sales'
detail asks that *"fasteners should extend 1/2" or more past the inside face of the
support"*, and in a 1-1/2" girt **no screw shorter than 2" can satisfy that.** The 2" passes
the girt fully with its tip outside — which is also why its penetration is capped and its
capacity does not keep rising with length. That closes what was an open variance item.

It must be a **wood-point (Type 17)** screw, not a self-drilling point: a drill point in a
1-1/2" nailer reams its own thread away, and NDS §12.2 is a wood-screw equation.

### Cross-check against a published row

ER-309's own DFL substrate row publishes **208 lb at 1" penetration**. The same equation at
DFL's G of 0.50 gives 2850 x 0.50² x 0.190 x 1.6 = 216.6 lb/in x 1" — 208 lb once the
report's own rounding is allowed for. The equation reproduces a published number for a
substrate that *is* in the report, which is the check that the arithmetic above is being
applied correctly to the one that is not.

**A published value would supersede this.** If a maker prints a pull-out for this screw into
wood, that number governs and this section becomes the cross-check rather than the answer.

## 6.1 What is still NOT checked

- **The girt itself in bending, and its block-to-stud connection.**
  `structural.girt_course_spacing` holds the spacing; nothing grades the stick.
- **Panel deflection, and thermal movement over a continuous run.**
- **The table's three-equal-span basis at the short walls.** Metal Sales publishes the 58
  psf for three or more equal spans. A wall whose girt course gives a panel only two spans
  is a stiffer support condition for the end spans and a softer one in the middle; the
  short north/south walls have not been counted against that basis.
- **Whether the supplier actually named on the order is the one in §1.** The whole substrate
  permission rests on Metal Sales' guide. A substitution is a re-check, not a swap.

## 7. The literature survey, 2026-09-04 (amended 2026-09-11)

**The gap is real, it is structured, and it is evidenced — and §6 now fills it by
calculation rather than by citation.** A sweep of current ICC-ES, IAPMO-UES and
manufacturer technical data found **no product that publishes a WITHDRAWAL allowable for a
concealed-fastener metal board-and-batten WALL panel over open framing at 24" o.c.** That
absence stands. What changed on 2026-09-11 is what is done about it: the rational-design
path in point 1 below is now **TAKEN**, and the Metal Sales row below has moved from
"nearest match" to *the product on this wall*. Every document still falls into one of
exactly two buckets, and neither answers §6 by itself:

**(a) Publishes a negative allowable, but requires a solid substrate** — so a batten profile
over open girts is off-label:

| Report | Date | The clause |
|---|---|---|
| ICC-ES ESR-5839 (Petersen) | 2026-04 | §3.1.6 *"The metal siding must be installed over solid substrate."* Board-and-batten is not among the profiles covered at all. |
| ICC-ES ESR-5838 (Drexel) | 2026-05 | §3.1.6, identical language; board-and-batten not covered. |
| ICC-ES ESR-4730 (Western States) | 2025-09 | §5.2 *"must be backed by a solid substrate."* Covers eight wall panels, T-8 PlankWall among them at 48 psf allowable negative — but §5.6 limits that to *"the wall panels only"* and §5.8 hands the fasteners to the RDP. Board & Batten is **absent** from the covered list. |
| IAPMO UES ER-309 §3 (AEP Select Seam Narrow Batten) | 2025-06-24 | *"Clip Usage: Over solid substrates only"* and *"Design Values are not available."* |
| Metal Sales Mini/Maxi-Batten | — | *"not recommended for use over open framing."* |
| Morin BCR / SWL / SCR | — | *"require a solid substrate."* |
| McElroy Nostalgia B&B | — | substrates *"Plywood or OSB"* only; ASTM E1592 uplift *"(Pending)"* — no load table, no report. |
| ATAS Monarch, and Multi-Purpose (MPW) | — | *"Load tables available upon request"* — i.e. nothing published. The nearest ATAS data in the right format is Rigid Wall II at −169.6 psf @ 2'-0" over min. 18 ga steel, which is a flush/reveal panel and not a batten. |
| ICC-ES ESR-2385 (Metal Sales) | reissued 2026-08 | the word *batten* appears zero times in the text layer (see the caveat below). Mini/Maxi-Batten is separately *"not recommended for use over open framing."* |
| ICC-ES ESR-5046 §Taylor T-Panel w/ Narrow Batten | rev. 2026-02 | 49.8 psf at 2'-0" — but the table is headed *"INSTALLATION OVER SOLID SUPPORT"* and note 8 confirms it is not suitable over open framing. Taylor's own Board & Batten data sheet says testing and ESR-5045 coverage are *"Coming soon."* |
| Central States Board & Batten | — | *"does not have any documented certified testing."* |
| Nu-Ray | — | makes no batten panel at all. |

**(b) Permits open framing, but the negative table explicitly excludes the fastener
connection** — that is, it omits precisely the limit state that governs here. The clearest
statement of it is ICC-ES **ESR-5045** (Taylor Metal, TMP Metal Siding, reissued 2026-04,
the newest and broadest wall-siding report that *does* allow open framing — §3.2.1 admits
C/Z/Hat cold-formed steel framing, min 20 ga, with no solid-substrate condition anywhere):

> *"Tabulated allowable negative loads do not consider panel connection to structural
> support. The fastener connection strength must be determined by registered design
> professional."*

The word *batten* appears **zero times in ESR-5045's text layer** — see the two unclosed
items at the end of this section for what that does and does not establish.
Metal Sales' own BB75-1111 Board &
Batten guide (2025-10) is the nearest real batten product that both permits open framing
(*"Steel Framing – 18 gauge or thicker"*) and publishes a 2'-0" outward number — 58 psf —
and its note 2 says the same thing: *"Allowable load does not address web crippling,
**fasteners, support material** or load testing."* Panel bending only, exactly as §5.

**Three independent sweeps, one answer.** A second pass over McElroy, ATAS and Metal Sales
(the three most likely to carry a wood-girt batten product) and a third over AEP, Sheffield,
Drexel and Western States each reached the same conclusion and added the rows above. **None
of those makes a 24"-coverage batten panel at all** — published coverages are 11", 12" and
8/12/16". Sheffield's SMI Board & Batten cites Florida approval FL45939 with no numbers
published and details drawn on *"SHEATHING (BY OTHERS)"*.

**Two things the survey turned up that are not in §6 and belong to somebody's decision, not
to this note's arithmetic.**

1. **A rational-design path exists, one report explicitly authorises it, and §6 now TAKES
   it.** IAPMO UES
   **ER-309** (ASC Profiles / AEP Span, rev. 2025-06-24) publishes the per-fastener
   **pull-out** capacities behind its own tables — #10 into 20 ga Gr50 CFS: **124 lb**; into
   20 ga Gr33: **86 lb**; into DFL lumber at 1" minimum penetration: **208 lb** (steel per
   AISI S100, wood per NDS) — and states: *"The structural design professional may
   rationally design other fastener and substrate combinations based on engineering
   mechanics and the maximum panel/clip capacities stated within this report."* At §4's
   18.27 psf and one fastener per panel per girt over an 11" panel that is a 1.83 ft²
   tributary and 33.5 lb per fastener. **That arithmetic is now done — §6.** The girt is
   1-1/2" KDAT, not 20 ga steel and not a 1"-penetration DFL member, so none of ER-309's
   three rows can simply be read off; what its authorising sentence permits, and what §6
   does, is to go back to the NDS equation the DFL row itself came from. ER-309's DFL row is
   reproduced there to within a pound as the check that the equation is being applied right.

   **One reading point that makes those tables quotable here at all** (the same rule §5
   states for the Metal Sales column). ER-309's *"attachment
   spacing"* and ESR-4730's *"support fastener max. spacing"* are the fastener or clip
   spacing measured **along the panel's length**, not a girt-span table. For a panel run
   VERTICALLY over horizontal girts — which is this wall — the two coincide, so the reports'
   2'-0" column really is this wall's 24" girt spacing. It would **not** coincide for a
   horizontally-run panel, and quoting these numbers for one would be wrong.
2. **No 24"-coverage board-and-batten exists on the market, and the model no longer claims
   one.** Published coverages are 10" (Central States), **11" (Metal Sales BB75-1111)**,
   12"/16" (Petersen, McElroy, Sheffield, Taylor, Drexel, Englert) and 16" (Berridge).
   `board-batten-24` was authored at 20" net coverage against no named product; **on
   2026-09-11 it became Metal Sales BB75-1111 at 11"**, which is the owner decision this
   point asked for. The tag keeps its spelling — it reads as the 24 GAUGE, which is
   unchanged. The coverage change is not cosmetic: it roughly doubles the panel count and
   the screw count against `prices.toml`, and fastener tributary area moves directly with
   it in §6.

One product does publish an open-framing *system* allowable for a batten panel and is worth
recording because it is the closest thing that exists: **Berridge Batten Seam**, 16"
coverage, 24 ga, open framing on 16 ga steel support, panel-to-purlin 48", batten clip 20"
o.c., 2 × #10 — **52.5 psf allowable / 105 psf ultimate**, from UL90 Construction #262. It is
not 24" o.c., not this coverage, and not over wood girts.

**The Western States open-framing quote, run down.** §1 cites WSMR as one of two suppliers
permitting open framing, on the strength of *"most details in this guide are shown with
panels attached to open framing"* (T-8 PlankWall Install Guide, doc `4209-22`, p.1). That
sentence is verbatim and real. It does not reach this wall, for three separate reasons, and
the third is the one that matters:

1. ~~**T-8 PlankWall is not a board-and-batten panel.**~~ **AMENDED 2026-09-11, and this
   point was wrong.** T-8 itself is indeed a reveal panel — WSMR's own shop drawing titles it
   *"REVEAL PANEL PROFILE"*, a flush 7.75"-coverage plank — but the guide it appears in is
   not a T-8-only document. Doc `4209-22` covers a **"BOARD AND BATTEN - BB, custom width
   10" to 25""** on p.4, and the *"most details in this guide are shown with panels attached
   to open framing"* sentence on p.1 is written across the guide, batten profile included.
   So the guide does reach a board-and-batten panel after all, and the original grounds for
   dismissing the quote do not hold. **Points 2 and 3 below still stand and are what
   actually settle it** — and point 3 is the one that matters: the guide publishes no load
   data of any kind, so an open-framing permission from it closes nothing. That is precisely
   why the product moved to Metal Sales, whose guide permits open framing *and* prints a
   number.
2. **It is covered by ESR-4730, not outside it.** T-8 appears in that report's Table 1,
   Table 2 and Figure 6 by name, so §5.2's solid-substrate condition governs it. ESR-4730
   §5.1 settles the conflict with the install guide explicitly: *"In the event of a conflict
   between the manufacturer's published installation instructions and this report, the most
   stringent governs."* The solid substrate governs.
3. **The install guide carries no load data at all** — no psf, no span table, no wind
   pressure anywhere in its 40 pages. What it says instead is *"Please consult a design
   engineer for load and design calculations."* An open-framing permission with no allowable
   behind it does not close §5's question; it restates it.

And ESR-4730's own number cannot be borrowed: T-8's row reads **48 psf at a 12" maximum
spacing**, and footnote 3 defines that spacing as *"panel support fasteners or clips ... along
panel length"* — the same reading trap as ER-309 above. Table 2 has no span variable at all.
For a vertically-run panel the fasteners land on the girts, so this wall's **24" girts would
violate that 12" maximum outright**, quite apart from the substrate condition.

**WSMR does make a true board-and-batten panel, and it is simply unrated.** Its catalog
(`4222-23`, 10"-25" coverage, 3/4" panel height, 2" batten, concealed fasteners) publishes
**no load table, no psf, no span table and no ESR number**, and it is one of the products
*absent* from ESR-4730's covered list. That is the WSMR row that actually bears on this wall,
and it is a blank. One trap worth naming: that catalog has a *"Substrate"* row reading
`AZ 50 (Galvalume)` / `Aluminum` — that is the panel's own base metal, **not** a permitted
wall backing, and must not be read as a framing permission.

**Two things the survey could not close, and they are gaps in the survey rather than
findings.** Stated so nobody reads them as verified absences:

1. **ESR-5045's 88 figures are images, not text.** The "zero occurrences of *batten*" result
   above is a text-layer search, so a batten profile drawn only in a figure would not be
   caught by it. The quotation from note 3 is unaffected — it is text and was read — but if
   this item ever turns on whether ESR-5045 covers a batten profile, someone has to page
   through the figures by eye.
2. **Sheffield's Florida approval FL45939 would not load.** Any pressures it publishes are
   unverified here. Sheffield's own details draw the panel on *"SHEATHING (BY OTHERS)"*,
   which is the reason it sits in bucket (a) above, but the record itself was not read.

**Nothing in the model changed on the strength of this survey**, and that is the point: an
absence of published data is a finding, not a licence to interpolate one.

## 8. What a seal has to cover

**One item, twenty walls: `wall_panel/W-A-N1`.** Until 2026-09-11 the register carried
twenty separate `wall_panel/*` items, one per wall, all INCOMPLETE. They are one panel, one
girt spacing and one corner-zone demand — one design — and they are now one grouped record
keyed by the lowest member tag, with all twenty walls in `element_tags`. Twenty identical
sheets were twenty chances for a reviewer to stamp nineteen and miss one.
`haus engineering --item wall_panel/W-M-S1` resolves to the group and says so.

Membership is pinned. `element_tags` is not hashed, so `panel_count` is carried as an input
instead: a wall joining or leaving the group stales the seal, exactly as moving a wall
would. Per-wall staling is what the old shape bought and it is not worth twenty stamps —
the panel is one product order.

**What the seal is being asked to confirm** is no longer an absence. Both limit states are
graded: bending 0.31 against the manufacturer's own published allowable (§5), withdrawal
0.12 against NDS 2018 §12.2 (§6). The judgement in front of the engineer is whether the
rational design in §6 is the right one for this connection — the wet-service call, the tip
and flange deductions, and one screw per panel per girt as the fastener pattern — not
whether a number is missing. §6.1 lists what is still outside it.

The engineer's fee is plausibly already inside `permits-design-testing-and-insurance`
($20k-60k in `prices.toml`); no new cost line was added for it.

---

## Sources

Every standard and document this note rests on, collected from the citations above.
Citation style is the house style: issue year on first use (`ASCE 7-16 §29.3`),
section form after. A document is listed here only if a number in this note came
out of it.

- **ASCE 7-16** — §26.10 (velocity pressure), §30.3 (C&C, walls)
- **AWC NDS 2018** — §12.2 (wood screw withdrawal), §12.2.4 (end grain), Table 2.3.2 (load
  duration), Table 11.3.1 (which adjustment factors apply to a connection), Table 11.3.3
  (wet service), Table 12.3.3A (specific gravity), Appendix L (fastener dimensions)
- **ASTM A153** — hot-dip galvanizing on hardware
- **MN Rules 1309.0301** — the 115 mph statewide basic wind speed
- **ICC-ES ESR-4729** — cited HERE ONLY TO EXCLUDE IT. It is Western States' report, it
  covers ROOF panels over 16 ga steel supports, and **it does not cover this wall at all.**
  A reader who reaches for it has the wrong document.

**The §7 survey, 2026-09-04.** Documents read, not merely cited:

- **ICC-ES ESR-5045** (Taylor Metal, TMP Metal Siding), reissued 2026-04 —
  <https://icc-es.org/wp-content/uploads/report-directory/ESR-5045.pdf>
- **IAPMO UES ER-309** (ASC Profiles / AEP Span), rev. 2025-06-24 —
  <https://forms.iapmo.org/ues_reports/reports/er_0309.pdf>
- **ICC-ES ESR-4646** (Innovative Metals / IMETCO, "Element"), reissued 2024-10 —
  <https://icc-es.org/wp-content/uploads/report-directory/ESR-4646.pdf>
- **ICC-ES ESR-5839** (Petersen), 2026-04; **ESR-5838** (Drexel), 2026-05; **ESR-4730**
  (Western States), 2025-09 — all three require a solid substrate.
- **Metal Sales BB75-1111 Board & Batten install guide**, 2025-10 — **the product on this
  wall**; substrate language p.6, allowable load table and its note 2, panel fastener row,
  and the "1/2" past the inside face of the support" rule —
  <https://www.metalsales.us.com/wp-content/uploads/2025/10/Install-Guide-BB75-1111_10-2025.pdf>
- **Western States Metal Roofing install guide `4209-22`** — read in full 2026-09-11. Covers
  "BOARD AND BATTEN - BB, custom width 10" to 25"" (p.4) and permits open purlins (p.1), and
  publishes **no load data anywhere**: "Design calculations for fastener spacing should be
  completed by the design engineer" (p.3). See §7, WSMR point 1 as amended.
- **Berridge Batten Seam load chart, open framing** —
  <https://www.berridge.com/resources/batten-seam-panel-load-chart-open-framing/>

- **No published withdrawal allowable exists** for a concealed-leg board-and-batten profile
  over open framing at 24" o.c. That absence is still the finding, and it is not a gap in
  this bibliography. What changed on 2026-09-11 is that the absence is now answered by a
  rational design from NDS 2018 §12.2 (§6) rather than left open — which is what ER-309
  authorises and what a seal over this item confirms.
