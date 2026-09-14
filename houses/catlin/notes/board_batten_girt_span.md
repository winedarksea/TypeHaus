# Board & batten over 24" open girts — hand-worked wind and withdrawal check

**House:** catlin, Ramsey County, Minnesota (MN Residential Code 2020, adopting the 2018 IRC).
**Structure:** the twenty north/south walls clad in `board-batten-24` over a 24" girt course.
**Written:** by hand, from the standards, before the modules were encoded.
**Oracle for:** `engineering/wall_panel.py` and `engineering/wall_panel_withdrawal.py`;
reproduced by `tests/test_wall_panel_calcs.py`. A calculation that only agrees with itself
is not verified.
**What is asked of the reviewer:** §5, §6 and §6.2 — all three of the failure modes IRC
R703.1.2 names are graded, and the question is whether the rational designs in §6 and §6.2
are the right ones, not whether a number is missing.

Subject: `board-batten-24` — **Metal Sales BBD75-1212**, a 24 ga concealed
**direct-fastened** steel board & batten panel, **12" net coverage**, 3/4" rib, PVDF Linen
White (81) — on the twenty north/south walls of the house, spanning the KDAT girt course at
**24" o.c.** (`EXT_2X6`, `PLANT_EXT_2X6_HUMID`).

**Revised 2026-09-11: the product was named, and the item became stampable.** Two things
changed and nothing else did. The panel was an unnamed "24 ga board & batten, 20" coverage"
with an allowable borrowed from Metal Sales' table; it became the Metal Sales product
itself, so the 58 psf is the named product's own number and its guide's substrate language
is on-label for this wall (§1). And the withdrawal allowable that §6 used to record as
*unpublished by anyone* is now **computed** from NDS 2018 §12.2 — a rational design, which
is exactly what IAPMO UES ER-309 authorises a design professional to do, rather than a wait
for a row nobody is going to print.

**Revised 2026-09-14, and two of these are CORRECTIONS to the paragraph above rather than
new work.**

1. **The panel is BBD75-1212, not BB75-1111.** BB75-1111 is the CLIP-fastened member of the
   family; BBD75 is the direct-fastened one, and §6's model — one screw per panel per girt
   at the nail strip — has always been BBD75's detail. Naming it makes the existing
   calculation true rather than adding to it. 12" coverage rather than 11" (§1, §6).
2. **The panel screw goes to the guide's own stocked 1", REVERSING the 2026-09-11 move to
   2".** That move had one argument behind it — "fasteners should extend 1/2" or more past
   the inside face of the support" — and the argument does not hold (§6). Every candidate
   length passes NDS §12.2; 1-1/2" is the recorded no-cost margin; **2" is affirmatively
   rejected** on ccSPF clearance. Nothing longer than 1-1/2" should ever be specified here.
3. **A third limit state, head pull-through, is added — §6.2.** IRC R703.1.2 names three
   failure modes a design analysis must consider and this note graded two of them. That was
   the one real gap the 2026-09-14 review found.
4. **Consequence: the governing limit state FLIPS to withdrawal**, 0.334 against bending's
   0.315 (it was 0.12 at 11" coverage with the 2" screw). Both pass wide and the two are 6%
   apart, so a later coverage or wind change can flip them back with no physical meaning
   whatever. Read the governing state as a label, not as a finding.

The east and west walls keep PBR — `pbr-panel-24` since 2026-09-14 — and are **not**
subjects here. **ESR-4729 does
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

**The substrate question is closed, and it is closed by the CODE and not by a letter.**
This section used to rest on one sentence in one install guide and to carry the question as
half-open. It is not half-open. Metal siding over open girts is the ordinary case, and
manufacturers publish these details precisely so a house does not need bespoke engineering.
Four things settle it, in descending order of authority:

**(i) IRC R703.1.2 (Wind resistance), verbatim:** *"Wind-pressure resistance of the siding,
soffit and backing materials shall be determined by **ASTM E330** or other applicable
standard test methods."* and *"Where wind-pressure resistance is determined by design
analysis, data from approved design standards and analysis conforming to generally accepted
engineering practice shall be used to evaluate the siding, soffit and backing material **and
its fastening**."* The section says nothing whatever about a solid substrate. It asks for a
wind-load path, by test or by analysis. That is what §2-§6.2 are.

**(ii) BBD75-1212 lists an ASTM E 330 Load Test** on its own design page (install guide
p.13, and the Direct-Fastened CTR). That is R703.1.2's first path, named on the product.

**(iii) The allowable table is indexed on FASTENER SPACING, from 2'-0" to 6'-0", and 2'-0"
is the NARROWEST column** — 43 psf inward / 58 outward, falling to 22/13 at 6'-0". A table
built on fastener spacing across five span values is a spanning-between-supports table by
construction, and this wall's 24" girt sits at the strongest end of the published range,
with the manufacturer publishing spacings three times wider.

**(iv) The manufacturer's own words.** Metal Sales' BBD75 Board & Batten (Concealed
Direct-Fastened) install guide, 2025-10-16, states on p.7 that the panel is *"designed to be
installed over open framing and/or directly over a wood substrate"*; p.12's Support
Materials list reads **"Lumber – 1x or thicker"** and **"Steel Framing – 18 gauge or
thicker"**, neither of which is a solid substrate; every detail page's parts table says the
screw is for attachment to *"wood sheathing **or framing**"* (~20 occurrences); and the
Panel End detail p.44 draws the panel onto a single *"FRAMING MEMBER"* with no sheathing
plane at all. The Spec Data Sheet agrees in its own words — *"Designed for application over
solid sheathing **or open framing**"*, typical assembly *"Wood framing with moisture
barrier"* — as does the 2025-11 catalog, *"Applies over open framing or solid substrate"*.
The same page names the wood fastener, *"#10-12 x 1" Pancake Head Wood Screw"* under
*"Attaching to Wood"*.

This wall's support is a 1-1/2" KDAT 2x4 laid flat — 1x or thicker, and open framing. The
panel is on-label here, quoted rather than inferred, and the quote is authored onto the
material as `Material.open_framing_source` so the calculation refuses to grade a panel whose
literature does not say it (§6.1).

**The CTR's summary badge is a copy artifact and is dismissed.** The 07/2026 Condensed
Technical Reference carries an icon row that reads as sheathing-only. The same row on the
same sheet says `10" & 12" COVERAGE` while the sheet shows ONE panel at 11": the 12/2024 CTR
was a single sheet covering the 10" and 12" panels with exactly that row, and the 07/2026
split copied it verbatim onto both sheets. **No Tech Services letter is needed to proceed.**

**The clip correction, which is where the product name came from.** BB75-1111 is the
CLIP-fastened panel of this family and BBD75-1010/1212 the direct-fastened ones — the two
guides' cover pages say so outright. BB75's wall-base detail (guide p.20) reads *"PANEL CLIP
(SEE PAGE 17), CLIP FASTENERS (B), 2 PER CLIP"* (clip P/N 4934600 G90 / 49346F01 stainless);
BBD75's (p.22, and the jamb at p.24) reads *"PANEL FASTENER (B), AT NAIL STRIP"*. §6's
one-screw-per-panel-per-girt model is the second of those, so from 2026-09-11 to 2026-09-14
this note named the wrong panel for the arithmetic it was doing.

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

Taking span/3 rather than the panel's real 12" coverage is the **smaller** area and so the
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

Metal Sales BBD75-1212, 24 ga, read at the guide's 2'-0" fastener spacing: **58 psf
allowable outward** (suction), 43 psf inward. (BB75-1111's guide publishes the identical
row, which is why the clip/direct correction of §1 moved no number in this section.)

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

**And PBR, for comparison, at the same spacing:** Metal Sales' own PBR Condensed Technical
Reference (1/2026) wall table publishes **318 psf** allowable negative at 2'-0" in 24 ga and
236 psf in 26 ga, so the E/W walls run at better than 17x demand against board & batten's
3.18x. That table supersedes the ASC PS230 / Metal Panels Inc. / Homewood citations this
note used to carry for PBR, since as of 2026-09-14 the product on those walls is Metal Sales
too (`pbr-panel-24`). The ASD basis is the one to quote, because both capacities are
allowables.

**A NEWER Metal Sales table publishes 75 psf for this panel and is deliberately NOT
adopted.** The Condensed Technical Reference 07/2026 re-publishes BBD75 at 42 psf inward /
**75** outward at 2'-0" — off a *lower* section (Ixx 0.0156-0.0181 / Sxx 0.0246-0.0292
against the guide's Ixx 0.0442 / Sxx 0.0538). A lower section modulus with a higher
allowable is not reconcilable in either governing limit state: scaling 58 by the section
ratio gives ~25-29 psf, not 75. One of the two tables is wrong. Both are calculated per AISI
2016, neither is testing, and both footnote fasteners and support material out. **58 is
kept**, as the lower published number, and the discrepancy is a question for the Rogers
branch when quoting rather than a gate on anything. Corroborating that the guide's row is
the stale one: the guide gives an 11" panel a weight of 1.66 psf where the CTR gives the 10"
1.43 and the 12" 1.34 — heavier for less steel, which runs the wrong way.

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

**The fastener.** #10-12 x **1"** pancake head **wood screw**, Type 17 point, 316 stainless
or ASTM A153 Class D HDG. D = **0.190"** (the #10 shank). This is the guide's own
"Attaching to Wood" screw, the one a panel order ships with; the length is argued at the end
of this section, and it is a reversal of what this note said between 2026-09-11 and
2026-09-14.

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
App. L puts a wood screw's tip at 2D).

    p = length − flange − 2D
      = 1.000 − 0.0239 − 0.380 = **0.5961"**

    capacity  Z = W' p = 183.46 x 0.5961 = **109.4 lb**

There is also a cap at the support's own thickness — a screw that runs out the back of a
1-1/2" girt is not holding 2" of wood, whatever the box says — and at 1" **it does not
bind**. The cap describes the 2" this note rejects below, whose 1.596" of shank would be
cut back to 1.500".

### The demand

One screw per panel per girt at the nail strip — BBD75's own wall-base and jamb details.
The tributary area is the girt spacing by the panel's **12" net coverage**:

    A = (24/12) x (12/12) = **2.0000 ft²**
    P = 18.2659 x 2.0000 = **36.53 lb**

    d/c = 36.53 / 109.4 = **0.334**

**This is the governing limit state, ahead of bending's 0.315 — and it became so on
2026-09-14, for the first time.** At the old 11" coverage with the rejected 2" screw it was
0.12. Nothing about the building got worse: the demand rose 9% with the real coverage and
the capacity fell to what the stocked screw actually holds, and both remain a long way from
1.0. The two states are **6% apart**, so a later coverage change, a wind-basis change or a
girt re-spacing can flip them back the other way with no physical meaning at all. A reader
who sees "governed by withdrawal" change to "governed by bending" in some later revision
should read it as a label moving, not as a finding.

### Screw length is the whole answer, so the alternates are printed

All d/c below are against the 36.53 lb demand at 12" coverage.

| Screw | Penetration | Capacity | d/c | |
|---|---|---|---|---|
| **1" — the guide's own stocked screw** | **0.596"** | **109 lb** | **0.334** | **SPECIFIED (owner decision 2026-09-14)** |
| 1-1/2" | 1.096" | 201 lb | 0.182 | available margin at no cost, recorded and not taken |
| 2" | 1.500" (capped) | 275 lb | 0.133 | **REJECTED** — see the ccSPF clearance below |

**Every length passes, so length is not chosen on capacity. It is chosen on thread
engagement inside the girt — and the paragraph this note carried here from 2026-09-11 to
2026-09-14 was wrong.** That paragraph said the 2" was specified "for a different reason":
Metal Sales' detail asks that *"fasteners should extend 1/2" or more past the inside face of
the support"*, and in a 1-1/2" girt no screw shorter than 2" can. It gave the 2" exactly one
leg, and the leg does not hold, for three separate reasons:

1. **The girt IS the support, and the protrusion buys nothing.** Behind the girt is the 1/2"
   vent gap and then the ccSPF; at the discrete block stacks it is offcuts already hung on
   the same FastenMaster TimberLOK 8". A tip emerging into that plane adds no withdrawal, no
   bearing and no redundancy. There is nothing on the far side to engage.
2. **The rule cannot be a wood-engagement criterion, because on the guide's own thinnest
   listed supports it produces almost none.** Run the same stocked 1" screw (flange 0.0239",
   NDS App. L tip 2D = 0.380") against the Support Materials list, in *thread actually in the
   support*:

   | Listed support | thread in the support, 1" screw |
   |---|---|
   | OSB 7/16" | **0.034"** |
   | Plywood 1/2" | 0.096" |
   | **catlin's 1-1/2" KDAT girt** | **0.596"** |

   Whatever *"past the inside face"* is protecting, this girt already over-satisfies it with
   the stocked screw — ~18x the thread engagement of the manufacturer's own thinnest listed
   support. The sentence is a sheathing-era "make sure you went all the way through" proxy,
   not a design criterion.
3. **And it is not the governing document anyway.** The load table footnotes fasteners and
   support material out *by name* (note 2, §5) — which is precisely why `wall_panel` is an
   ENGINEERED record and not a `PublishedSpan`. IRC R703.1.2's design-analysis path is the
   one this wall is on, and it requires the analysis to reach *"its fastening"*. This section
   already **is** that analysis.

**And there is an affirmative reason not to go longer.** A 2" screw's tip stands 0.476" into
a 0.500" vent gap — **0.024" off the ccSPF face**. A girt milled a shade thin, or one screw
overdriven, and a tip is in the foam; across ~840 fasteners that is not a tail risk, it is a
rate. It also takes a special length off a purchase order that is already custom for the
316 SS / A153-D coating the KDAT contact requires. Nothing longer than 1-1/2" should ever be
specified on this wall.

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

## 6.2 Fastener head pull-through — the third mode R703.1.2 names

**Why this section exists at all.** IRC R703.1.2's last sentence is the one that scopes the
analysis, verbatim: *"**All applicable failure modes including bending rupture of siding,
fastener withdrawal and fastener head pull-through** shall be considered in the testing or
design analysis."* Three named modes. Until 2026-09-14 this note graded two of them — §5 and
§6 — and `engineering/wall_panel.py` returned exactly two limit states. That was the one
real gap the 2026-09-14 review found, and it is a gap in *coverage*, not in capacity: the
mode passes wide. The code names it, so the record should show it.

It is also the mode a concealed-leg panel is most exposed to on paper, because a **pancake
head is the smallest head sold** — it has to sit under the batten. That is the reason to
grade it rather than assume it away.

**The equation.** AISI S100, head pull-over (pull-through) of a screw through sheet steel:

    Pnov = 1.5 t d'w Fu

The terms are the PANEL and the HEAD, not the shank and the wood — the head pulls a slug of
sheet through the panel. So this section shares §6's demand and none of its capacity terms.

    t    = 0.0239"     the 24 ga panel flange the screw passes through (§6)
    d'w  = 0.40"       the #10-12 pancake head's bearing diameter
    Fu   = 65,000 psi  ASTM A792 Grade 50, the Galvalume substrate every painted panel
                       on this house is rolled from. Structural quality is 65 ksi; a
                       commercial-quality 52 ksi sheet would be 20% less, and the
                       equation is linear in it, so this is a term to confirm on the
                       order rather than to assume downward.

    Pnov = 1.5 x 0.0239 x 0.40 x 65,000 = **932.1 lb**    nominal
    Omega = 3.0                                            AISI S100 ASD, connections
    allowable = 932.1 / 3.0 = **310.7 lb**

**The demand is §6's, unchanged** — the same screw carries the same tributary:

    P = 36.53 lb

    d/c = 36.53 / 310.7 = **0.118**

**Passes at 8.5x, and it is the least of the three states.** Withdrawal governs at 0.334,
bending is 0.315, pull-through is 0.118. The ordering is the one a reader should expect: a
single screw carries only one panel width of suction, and 24 ga sheet at a 0.40" head is a
lot of bearing for 36 lb.

**What would move it.** A smaller head (a trim-head or a low-profile washer-less screw), a
thinner panel (26 ga would take the allowable to ~233 lb, d/c 0.157 — still fine), or a
commercial-quality rather than structural-quality sheet. Two of those three are things a
purchasing substitution could do quietly, which is the argument for the state being in the
record rather than in a footnote.

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

**Head pull-through has come OFF this list** — it was on it until 2026-09-14 and is now §6.2.

**One recorded known condition, not a gap and not new.** BBD75-1212's air and water tests are
published *"with building wrap"* — *"ASTM E 283 Air Leakage, with building wrap"*, *"ASTM
E 331 Water Penetration, with building wrap"* — and this wall has no wrap. That is not a
panel-selection issue and it is not new: the ccSPF is the water plane here, which is already
a logged alternate-approval item under Minn. R. 1300.0110
(`notes/catlin_truss_engineering.md` §9), and **every** alternative panel in §7 carries the
same test basis. Recorded so a reviewer meets it here rather than discovering it. Nothing
changes.

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
Metal Sales' own BBD75 Board &
Batten guide (2025-10-16) is the nearest real batten product that both permits open framing
(*"Steel Framing – 18 gauge or thicker"*) and publishes a 2'-0" outward number — 58 psf —
and its note 2 says the same thing: *"Allowable load does not address web crippling,
**fasteners, support material** or load testing."* Panel bending only, exactly as §5.

**Three independent sweeps, one answer.** A second pass over McElroy, ATAS and Metal Sales
(the three most likely to carry a wood-girt batten product) and a third over AEP, Sheffield,
Drexel and Western States each reached the same conclusion and added the rows above. **None
of those makes a 24"-coverage batten panel at all** — published coverages are 10", 11", 12"
and 16". Sheffield's SMI Board & Batten cites Florida approval FL45939 with no numbers
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
   18.27 psf and one fastener per panel per girt over a 12" panel that is a 2.00 ft²
   tributary and 36.5 lb per fastener. **That arithmetic is now done — §6.** The girt is
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
   one.** Published coverages are 10" (Central States, Metal Sales BBD75-1010),
   11" (Metal Sales BB75-1111), **12" (Metal Sales BBD75-1212**, Petersen, McElroy,
   Sheffield, Taylor, Drexel, Englert) and 16" (Berridge).
   `board-batten-24` was authored at 20" net coverage against no named product; on
   2026-09-11 it became Metal Sales BB75-1111 at 11", and **on 2026-09-14 Metal Sales
   BBD75-1212 at 12"** — the clip/direct correction of §1, which moves the coverage with it.
   The tag keeps its spelling — it reads as the 24 GAUGE, which is unchanged. The coverage
   change is not cosmetic: it moves the panel count and the screw count against
   `prices.toml` (~915 screws at 11", ~840 at 12"), and fastener tributary area moves
   directly with it in §6.

   **BBD75-1212 carries no product approval at all**, which is worth recording next to this.
   The Direct-Fastened CTR reads "2023 FBC Approval - FL47647.1 **(BBD75-1010 only)**", and
   BB75-1111's own FL47647.1 is scoped *"over Sheathing"* — so the approval would not reach
   this wall for any of the three widths. Florida approval is not a Minnesota requirement;
   it is an indicator of what has been through a lab, and the 1010 is the width Metal Sales
   actually tested. It does not change §1's conclusion, which rests on R703.1.2 and on the
   panel's own ASTM E 330 listing.

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

### 7.9 The published alternative not taken (2026-09-12, CORRECTED 2026-09-14)

**This section named the wrong AEP panel, and the correction matters because the reason
given for not taking it — "the batten line is the cost" — was false of the right one.**

The entry read: *AEP Span Flush Panel*, IAPMO UES ER-309 Tables 6.6/6.7, 24 ga, 12"
coverage, 66 psf ASD negative at 24" over "Lumber (DFL) 1" min" open framing — a published
span table for this exact condition, but on a FLUSH profile, so taking it would have cost
the batten line the house is for.

**The right entry is AEP Span Flex Series `1.2FX20-12d`, and it is a genuine batten
profile**: a 10" field plus one 2" x 1-1/4" batten per 12", direct fastened through a
nailing flange. It is covered by **ER-309 Table 7.2**, headed *"Over solid substrate or over
open framing"*, with a substrate row that reads literally **"Lumber (DFL) 1" min"** at
2'-0" spacing: **89 psf ASD**. ER-309 p.9 also publishes the wood pull-out values behind
it — DFL, 1" min thread, #10 -> 208 lb — which is the very row §6 already reproduces as its
cross-check. So it is a published span table for this exact condition ON A BATTEN, which
means it would be graded as a `PublishedSpan` (`checks/structural/published.py`) and would
take `wall_panel/W-A-N1` **out of the engineering register** entirely, exactly as PBR is
out of it on the strength of its wall span tables. No seal, no item, no calculation — **and
no loss of appearance.**

**It is still not taken, for three reasons that have nothing to do with load or looks.**

1. **No Midwest plant.** AEP Span's nearest against Metal Sales' Rogers, MN — freight and
   lead time on a made-to-order coil run, on every trim piece as well as the field panel.
2. **The report expires 2026-09-30.** A `PublishedSpan` graded off an expired evaluation
   report is worse than an engineered item: it looks closed and is not.
3. **It would reopen the girt question this house has just closed the other way.** AEP's own
   guide spec says *"Direct contact or run-off from CCA, ACQ, AC, or other treated lumber…
   can cause panels and trim to fail prematurely. Avoid contact with these materials."*
   Every girt on this wall is KDAT. The evidence on treated-wood contact (see below) is that
   a both-sides-coated panel on a dry, vented girt is fine; but AEP writes the exclusion into
   its own spec, and buying a published table at the price of a written warranty exclusion is
   not a trade worth making.

**Also recorded, and also not taken: Metal Sales TLC-13 / TLC-15.** Direct-fastened, load
table footnoted to ASTM E330 testing on girts, and available in **40' lengths** — which
would run the 31.4' gable unjointed, against BBD75's 20' maximum and its storey-line
Transition Trim. It is a recessed reveal, not a batten.

**And the central finding of §7 is confirmed rather than narrowed:** no manufacturer
anywhere publishes a concealed board-and-batten wall load table over open WOOD framing at
24" o.c. Three independent sweeps agree. Competitors mostly require a deck outright
(Western States ESR-4730 §5.2, Petersen ESR-5839 §3.1.6, Drexel ESR-5838 §3.1.6, Sheffield,
McElroy) or permit open framing only over 16-18 ga steel (Berridge, ATAS).

This is all written down so that the next person to ask "why is this panel an engineered
item when the one next to it is not?" gets the answer in one place rather than re-running
§7 — and so that nobody re-derives the Flush Panel entry and repeats its mistake.

### 7.10 KDAT girts in contact with painted Galvalume — researched 2026-09-14, verdict: KEEP THE GIRTS

This is not a panel-selection question and it does not change a model number, but it is the
one durability question the 100-year target actually turns on, and it is recorded here so it
is not re-litigated from a scary one-liner. Separate what was MEASURED from what a warranty
merely excludes:

- **Measured.** USDA FPL GTR-227 (Zelinka) is the only independent dataset. Corrosion of
  metal in contact with copper-treated wood *"climbs from less than 1 µm/yr at 16% moisture
  content to more than 40 µm/yr at 26% MC"*, and *"when the wood is dry, embedded metals do
  not corrode"*. **Moisture content is the whole mechanism.** At 100% RH, galvanized steel
  reads ACQ 32 / CA 29 / MCQ 19 / CCA 16 / untreated 4.4 µm/yr — so micronized is better than
  soluble but is **~4x untreated, not "similar to untreated"** as Koppers markets it; do not
  repeat that claim. Stainless in the same test was *"statistically indistinguishable from
  zero"*, which is the specified panel screw.
- **The scary study does not describe this wall.** U.S. Steel TBP 2005.19 — the source of
  "prepainted Galvalume is more susceptible than prepainted HDG" — ran its architectural set
  in a test that *"simulates sheets in near contact with standing water"*, a *"continuously
  damp environment"*, on **ACQ-D**, the highest-copper soluble chemistry. Its own conclusions
  are *"corrosion requires water… designs should focus on eliminating wetness"*. Painted
  specimens ran on a different order of magnitude from bare ones: *"the severe corrosion of
  the unpainted… materials illustrates the effectiveness of paint films"*.
- **The current industry position is permissive for this case.** MCA's treated-lumber
  bulletin: *"Service conditions where wood is protected from wetting, and the moisture
  content is less than 20%, have shown little corrosion potential, even with ACQ and CA"*,
  naming micronized copper as one of two acceptable outcomes — the barrier being the
  *alternative* to it, not an additional requirement. MCA's Fastener Compatibility bulletin
  v3, 09/2025 adds: *"**If panels are coated on both sides, a moisture barrier may not be
  needed.**"* This panel is coated both sides.
- **The warranty exclusion is real but is a short instrument on the wrong face.** AEP Span
  and Fabral say avoid contact; Sheffield excludes treated lumber. But a PVDF paint warranty
  covers chalk, fade and adhesion on the **weather face** for 35-45 years and the substrate
  warranty is 50. On a 100-year target, buying assembly changes to preserve a warranty that
  covers neither the face in question nor the back half of the service life is bad value —
  and AEP is not the supplier here in any case.
- **Against keeping it, honestly:** no manufacturer publishes a detail SHOWING treated wood
  girts in a vented rainscreen (Metal Sales, McElroy, AEP Span, Fabral, Bridger, Sheffield
  and Steelscape all checked), and no study tests a *vented* cavity in either direction. That
  is a hole in the literature, not evidence of safety. Post-frame construction is the de
  facto field precedent with no published failure survey either way.

**Actions, none of which is a girt swap:**

1. **Read the end tag before ordering.** MCA / micronized (MicroPro, YellaWood, ProWood,
   Northern Crossarm "KDAT Brown") -> change nothing. **CA-C (Wolmanized) or ACQ — soluble —
   -> change the order**, while it is still a phone call. This is the one real decision.
2. **Upgrade the coil's BACKER coat and confirm the backside is primed.** Per U.S. Steel TBP
   2005.10 the exterior film is ~1 mil PVDF but *"backers are usually neutral color
   polyesters and are not usually specified"* at ~0.5 mil — **the weaker, cheaper,
   unspecified film is the one facing the treated wood.** Highest-leverage 100-year item in
   this assembly, and it is a line on the order rather than a design change.
3. **Specify painted-head 316 screws.** MCA's table rates 300-series stainless on painted
   Galvalume "Yes" with fine print assuming *"the fastener will also be painted"*. Costs
   nothing and looks better.
4. **Do NOT cap the girts with a self-adhered strip.** It converts a ledge that dries from
   two sides into one that dries from one, punctured at every screw; U.S. Steel warns felt
   and paper barriers *"hold moisture and increase corrosion"*, and Koppers warns against
   treated wood *"encased, sealed, or wrapped… where trapped moisture can occur"*. Possible
   narrow exception: the bottom course and splash zone only, where wetting is real.
5. **Treat the vent path as structural**, because here it is: continuous top and bottom, and
   attention to drifted snow at the wall base. Every line of evidence turns on the wood
   staying under 20% MC.
6. Not taken, recorded: untreated kiln-dried girts (NRCA permits non-treated where a
   secondary means of waterproofing exists, and the 4" ccSPF is one) — rejected because these
   girts are not decorative furring, they carry every cladding screw's withdrawal (§6), so a
   decay failure is a cladding-detachment failure. Borate is disqualified (leaches under
   liquid water, UC1/UC2). Ecolife/PTI organic treatment would remove the question entirely,
   but **KDAT Ecolife 2x4 availability in the upper Midwest could not be confirmed.**

**Ranked 100-year limiters for this assembly, for the record:** (1) the exposed fasteners'
EPDM washers, 15-40 yr — see the `T09150HWAM` note in `prices.toml`; (2) the base-of-wall
salt and snow zone on the street elevation, where 18-24" of grade clearance and a separately
replaceable bottom band are the answer and `haus check` grades neither; (3) copper-treated
wood in direct contact, above; (4) sealants; (5) paint appearance, recoverable by a ~$1-3/SF
Kynar Aquatec field recoat at year 40-50. Painted Galvalume itself is LAST: USS warrants AZ50
painted at 50 yr and the MCA/ZAC field study projects 60-375.

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

**What the seal is being asked to confirm** is no longer an absence. All three of the
failure modes IRC R703.1.2 names are graded: bending **0.315** against the manufacturer's own
published allowable (§5), withdrawal **0.334** against NDS 2018 §12.2 (§6) — the governing
state since 2026-09-14 — and head pull-through **0.118** against AISI S100 (§6.2). The
judgement in front of the engineer is whether the rational designs in §6 and §6.2 are the
right ones for this connection — the wet-service call, the tip and flange deductions, one
screw per panel per girt as the fastener pattern, and the 0.40" head bearing diameter — not
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
- **IRC 2018 R703.1.2** (Wind resistance) — the ASTM E330 clause, the design-analysis clause,
  and the sentence naming the three failure modes §5 / §6 / §6.2 answer
- **AISI S100** — head pull-over, `Pnov = 1.5 t d'w Fu`, and Omega 3.0 for connections (§6.2)
- **ASTM A792** — Grade 50 Galvalume sheet, Fu 65 ksi (§6.2)
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
- **Metal Sales BBD75 Board & Batten (Concealed Direct-Fastened) install guide**,
  2025-10-16 — **the product on this wall**; substrate language p.7, Support Materials list
  p.12, the ASTM E 330 Load Test line and the allowable load table with its note 2 p.13, the
  "Attaching to Wood" fastener row and the "1/2" past the inside face of the support" rule,
  the wall-base detail p.22 and jamb p.24 ("PANEL FASTENER (B), AT NAIL STRIP"), and the
  Panel End detail p.44 —
  <https://www.metalsales.us.com/wp-content/uploads/2025/10/Install-Guide-BBD75_10-2025.pdf>
- **Metal Sales BB75-1111 Board & Batten install guide**, 2025-10 — the CLIP-fastened
  sibling. Read for the comparison in §1 and §5: the identical 43/58 psf table, and the
  wall-base detail p.20 ("PANEL CLIP (SEE PAGE 17), CLIP FASTENERS (B), 2 PER CLIP") that
  is the difference between the two products —
  <https://www.metalsales.us.com/wp-content/uploads/2025/10/Install-Guide-BB75-1111_10-2025.pdf>
- **Metal Sales Concealed Direct-Fastened Condensed Technical Reference**, 07/2026 — the
  42/75 psf table RECORDED AND NOT ADOPTED (§5), the section properties behind it, the
  "BBD75-1010 only" FBC scoping (§7 point 2), and the copy-artifact icon row (§1)
- **Metal Sales Spec Data Sheet, BBD75** — "Designed for application over solid sheathing or
  open framing"; ASTM E 283 / E 331 "with building wrap" (§6.1)
- **Metal Sales 24 ga PVDF colour guide**, 9/2026 — Linen White (81): SR 0.73 / TE 0.86 /
  SRI 89 per ASTM C1549 / C1371 / E1980, 45-yr film / 35-yr chalk-fade warranty
- **Metal Sales PBR-Panel Condensed Technical Reference**, 1/2026 — 318 psf (24 ga) / 236 psf
  (26 ga) allowable negative at 2'-0", the comparison in §5
- **Metal Sales 7/8" Corrugated Wall Condensed Technical Reference**, 1/2024 — 34-2/3" wall
  coverage (32" is the roof figure) and 412 psf at 2'-0"; cited for the garage, not for this
  wall
- **USDA FPL GTR-227** (Zelinka), **U.S. Steel TBP 2005.19** and **TBP 2005.10**, and the
  **MCA** treated-lumber and Fastener Compatibility (v3, 09/2025) bulletins — §7.10
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
