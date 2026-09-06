# Board & batten over 24" open girts — hand-worked wind check

**House:** catlin, Ramsey County, Minnesota (MN Residential Code 2020, adopting the 2018 IRC).
**Structure:** the twenty north/south walls clad in `board-batten-24` over a 24" girt course.
**Written:** by hand, from the standard, before the module was encoded.
**Oracle for:** `engineering/wall_panel.py`, reported by `structural.wall_panel_span`;
reproduced by `tests/test_wall_panel_calcs.py`. A calculation that only agrees with itself
is not verified.
**What is asked of the reviewer:** §6 — the withdrawal allowable nobody publishes. The
bending check passes and is not the question.

Subject: `board-batten-24` — 24 ga concealed-fastener steel board & batten, 20" net
coverage — on the twenty north/south walls of the house, spanning the KDAT girt course at
**24" o.c.** (`EXT_2X6`, `PLANT_EXT_2X6_HUMID`).

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
in this guide are shown with panels attached to open framing"* — but that sentence is from
the **T-8 PlankWall** guide, a reveal panel, not a batten; see §7) and Metal Sales. McElroy
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

## 7. The literature survey, 2026-09-04 — and it comes back empty

**The gap is real, it is structured, and it is now evidenced.** A sweep of current ICC-ES,
IAPMO-UES and manufacturer technical data found **no product that publishes a suction or
withdrawal allowable for a concealed-fastener metal board-and-batten WALL panel over open
framing at 24" o.c.** Every document falls into one of exactly two buckets, and neither
answers §6's question:

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

1. **A rational-design path exists, and one report explicitly authorises it.** IAPMO UES
   **ER-309** (ASC Profiles / AEP Span, rev. 2025-06-24) publishes the per-fastener
   **pull-out** capacities behind its own tables — #10 into 20 ga Gr50 CFS: **124 lb**; into
   20 ga Gr33: **86 lb**; into DFL lumber at 1" minimum penetration: **208 lb** (steel per
   AISI S100, wood per NDS) — and states: *"The structural design professional may
   rationally design other fastener and substrate combinations based on engineering
   mechanics and the maximum panel/clip capacities stated within this report."* At §4's
   18.27 psf and one fastener per panel per girt that is a ~4 ft² tributary and ~73 lb per
   fastener. **That arithmetic is not done here and no d/c is published from it**: the girt
   is 1-1/2" KDAT, not 20 ga steel and not a 1"-penetration DFL member, so the pull-out row
   that would govern is not one of the three ER-309 prints. This is the shape of the
   engineered design §8 asks for, not a substitute for it.

   **One reading point that makes those tables quotable here at all.** ER-309's *"attachment
   spacing"* and ESR-4730's *"support fastener max. spacing"* are the fastener or clip
   spacing measured **along the panel's length**, not a girt-span table. For a panel run
   VERTICALLY over horizontal girts — which is this wall — the two coincide, so the reports'
   2'-0" column really is this wall's 24" girt spacing. It would **not** coincide for a
   horizontally-run panel, and quoting these numbers for one would be wrong.
2. **No 24"-coverage board-and-batten was found on the market.** Published coverages are 10"
   (Central States), 11" (Metal Sales BB75-1111), 12"/16" (Petersen, McElroy, Sheffield,
   Taylor, Drexel, Englert) and 16" (Berridge). `board-batten-24` is authored at **20" net
   coverage**, which is inside that range for a nominal-24" stock width — but the profile has
   not been matched to a named product, and fastener tributary area moves directly with
   coverage. **Naming the product is an owner decision and a possible cost change**; nothing
   here picks one.

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

1. **T-8 PlankWall is not a board-and-batten panel.** WSMR's own shop drawing titles it
   *"REVEAL PANEL PROFILE"* — a flush 7.75"-coverage plank with a recessed groove at the
   joint and a face that is planar. Board & batten reads as a batten standing *proud* of
   the field; T-8 is the geometric opposite. It was never the right analogue for this wall.
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

`wall_panel/W-M-S1` and its nineteen siblings, per `docs/engineering-toml-format.md`. One
stamp may cover all twenty — they are the same panel, the same spacing and the same wind —
but the register keeps them per element so that moving one wall stales that wall alone.
The engineer's fee is plausibly already inside `permits-design-testing-and-insurance`
($20k-60k in `prices.toml`); no new cost line was added for it.

---

## Sources

Every standard and document this note rests on, collected from the citations above.
Citation style is the house style: issue year on first use (`ASCE 7-16 §29.3`),
section form after. A document is listed here only if a number in this note came
out of it.

- **ASCE 7-16** — §26.10 (velocity pressure), §30.3 (C&C, walls)
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
- **Metal Sales BB75-1111 Board & Batten install guide**, 2025-10 —
  <https://www.metalsales.us.com/wp-content/uploads/2025/10/Install-Guide-BB75-1111_10-2025.pdf>
- **Berridge Batten Seam load chart, open framing** —
  <https://www.berridge.com/resources/batten-seam-panel-load-chart-open-framing/>

- **No published withdrawal or negative-pressure allowable exists** for a concealed-leg
  board-and-batten profile over open framing at 24" o.c. That absence is the finding, not a
  gap in this bibliography — see §6, §7 and `03-open-items.md` in the calculation package.
