# The catlin truss — engineering basis for an engineer's review and stamp

**House:** catlin, Minnesota (MN 2020 Residential Code, adopting the 2018 IRC).
**Element:** the exterior wall's cladding stand-off — one tier of flat horizontal 2x4 girts
carried on 4-1/2" blocks, standing in free air outboard of 4" of closed-cell spray foam.
Every number below is recomputed here from first principles, with the arithmetic shown, so a
reviewer can check the whole chain without opening the model.
**Oracle for:** `typehaus/wind.py`, reproduced by `tests/test_wind_loads.py`; the
`rafter/RF-*` deferral in `engineering/deferred.py`; and **§3 for
`typehaus/engineering/girt_screw.py`**, reproduced by `tests/test_girt_screw_calcs.py`.
**What is asked of the reviewer:** this is a plain NDS connection design under IRC R301.1.3
engineered design. It is not a prescriptive furring schedule and does not claim to be one.
See §6 (Code path) for why IRC Table R703.15.1 is not the applicable provision.

**And one thing to read first, because it changes where a reviewer's attention belongs.**
This wall now has a **single load path**: one screw per crossing, and nothing else holds the
cladding to the building. There is no second tier, no second fastener pass and no nail. The
compensation is that the screw carries no gravity at all — the block bears the cladding's
weight in direct compression on the sheathing — so it is a pure withdrawal element, and §3
is the whole of the design. **The screw pattern is the one thing this wall cannot miss.**

---

## 1. The assembly

Two bands outboard of the 1/2" plywood sheathing, both 2x stock laid flat, both horizontal:

| band | depth off sheathing | what | material |
|---|---|---|---|
| A | 0 – 4" | ccSPF, ONE application, crossed by **the block**: three loose 3-1/2" x 3-1/2" x 1-1/2" offcuts stacked flat on the sheathing, over every OTHER stud, at every 24" course | KDAT |
| A' | 4 – 4-1/2" | the block's proud 1/2": the **continuous vent gap** behind every course | — |
| B | 4-1/2 – 6" | **the girt** — 2x4 flat, horizontal, 24" o.c., standing in free air; the cladding nailer and the window mount plane. One **8" SDWS22800DB** per crossing through girt + block + sheathing, 1-1/2" into the stud | KDAT |

Foam total 4", in one lift. Cladding face 6" proud of the sheathing at the mount plane and
7-1/4" at the panel face — **both unchanged from the two-tier wall**, which is why nothing
outside this wall moved when the tier was deleted. Windows are OUTIE: the mount plane is the
outer face of the girt.

**Why there is only one girt tier.** A second, inner tier — plain SPF 2x4 flat, buried in the
foam, with the outer tier's blocks bearing on it and a second screw into it — is rejected for
three reasons, in order of size:

1. **It sat directly on the sheathing**, so it gave its own screw no thermal break at all,
   and it cost a **10.9 % framing fraction in the first 1-1/2" of the foam** to hold up
   nothing but the tier above it. §7 prices that at R-2.7.
2. **The foam does not need backing.** ICC-ES **ESR-4073** §4.4.2 permits 7-1/4" of this
   product on a vertical surface with nothing in it (self-weight ~0.05 psi against ASTM
   D1623 tensile adhesion of 32 psi and up); planed lumber in the foam is a shrinkage-crack
   interface, not a support. **ESL-1372** lists 3-3/4" of ccSPF between horizontal Z-girts
   screwed to studs at 28" o.c. — the same wall with a steel girt instead of a wooden one.
3. **Its rigidity contribution was nil.** ccSPF's racking bonus is its bond to the sheathing
   FACE, which is unchanged; a girt lying on that face adds no diaphragm.

**Materials are by exposure, and the rule got simpler.** Everything outboard of the sheathing
is now KDAT — the girt is a 3-1/2"-deep horizontal ledge behind the cladding that will
wet-cycle for the life of the wall, and the block plies stand in the same foam-face plane at
every crossing. The SPF tier that was encapsulated and never wet no longer exists, so there
is no longer an untreated piece anywhere out here. **KDAT on the girt and on the plies is
mandatory.**

**The block is a stack of three loose offcuts, not a machined spacer.** 3-1/2" x 3-1/2" x
1-1/2" pieces dropped on a snapped stud line and clamped by the girt screw — no tack, no
glue. Four things follow: the plies are cut from the girt stock at the saw; the block bears
the cladding's gravity in direct compression on the sheathing (§4), so the screw is pure
withdrawal; the block's **proud 1/2"** is what holds the girt off the foam and IS the vent
gap; and its depth is read off the resolved stack by
`resolve/framing/truss_girts.py`, never authored, so moving the girt out in the assembly
moves the ply count, the screw length and the BOM row with it.

**The screw is one screw.** 8" x 0.220" through the girt (1-1/2"), the three plies (4-1/2")
and the sheathing (1/2"), 1-1/2" into the stud. It is **wood-to-wood with continuous lateral
support over its whole through-length** — no gap, no foam and no standoff in the path — which
is the failure mode IRC Table R703.15.1 tabulates and the reason that table's geometry does
not describe this wall. The foam is sprayed around it afterwards.

As built by the model: **1,128 blocks** (3,384 plies) and **1,128 screws** across the house,
one screw per station, block on every OTHER stud. The crossing tributary is
**32" x 24" = 5.33 ft2**, and every load below moves with it.

**Openings are framed the same way as the field, and this must not drift.** At every rough
opening the one KDAT band carries **jamb posts** (vertical, inner face ON the RO edge) and
**head and sill courses** (horizontal, spanning post to post), each standing on its own
three-ply offcut block at **≤ 24" centres** — on the king or jack, on the header above the
head, or on the rough sill framing below the sill, all of which are already there. The window
flange bears on those posts and courses at the 6" mount plane
(`notes/outie_window_truss_detail.md`).

**The buck is 3/8" plywood and carries no window load.** It lines the RO on four sides from
the sheathing face out to the mount plane; it dams the foam at the reveal, faces the reveal,
and carries the sill pan and the head flashing. **It is not a 6"-deep timber**, and it is not
what the window hangs on — the posts and courses are. Its thermal contribution is small for
the same reason it is not structural, and §7 gives the number, because the opposite is easy
to assume from a drawing.

**Two courses are not on the field module:**

- a **starter** at the bottom of the band. On a main-storey wall the band runs 13-7/16" below
  the sole plate, over the floor rim board, because that is where the cladding laps; the
  starter is the nailer for it. Its blocks bear on the **rim board**, not on a stud — 1-1/2"
  of thread into a 1-1/2" rim, the same penetration §3 designs to, into the same SPF. That
  is the one place in the wall where the screw does not reach a stud, and it is why
  `test_truss_girt_geometry.py` excludes those blocks from its stud-lap measurement;
- a **rake nailer** along each gable's raked top, with its own blocks on the same module. It
  closes the cladding's raked edge, which the courses below could only reach to within one
  board of. Its blocks bear on the raked studs and on the raked top plate; they are drawn
  square and cut on the rake on the job. Tributary on a rake block is bounded by the field's
  own 32" x 24" — the nailer is the top edge of the band, so it collects from one side only.

---

## 2. Loads

### Wind (governs)

ASCE 7-16 Components & Cladding, Minnesota Risk Category II.

- V<sub>ult</sub> = 115 mph; Exposure **C** (taken conservatively — the site is Exposure B by
  surroundings, and the Exposure B numbers are given below for reference); mean roof height
  h = 30 ft; K<sub>z</sub> = 0.98, K<sub>zt</sub> = 1.0, K<sub>d</sub> = 0.85, K<sub>e</sub> = 1.0.

```
q_h = 0.00256 · K_z · K_d · V²
    = 0.00256 · 0.98 · 0.85 · 115²
    = 0.00256 · 0.98 · 0.85 · 13,225
    = 28.2 psf
```

- Wall zone 5 (corner), GC<sub>p</sub> = −1.4; GC<sub>pi</sub> = ±0.18 (enclosed):

```
p_ult = q_h · (GC_p − GC_pi) = 28.2 · (−1.4 − 0.18) = −44.6 psf
p_ASD = 0.6 · p_ult                                 = −26.7 psf   ← used everywhere below
```

- Wall zone 4 (field), GC<sub>p</sub> = −1.1: p<sub>ult</sub> = 28.2 · (−1.28) = −36.1 psf →
  **−21.6 psf ASD**.
- Positive (inward) pressure, GC<sub>p</sub> = +1.0: 28.2 · (1.0 + 0.18) = +33.3 psf →
  **+20.0 psf ASD**.
- Exposure B reference: K<sub>z</sub> = 0.70 → q<sub>h</sub> = 20.1 psf → −31.8 psf ult →
  **−19.1 psf ASD**. The design carries the Exposure C number, 40 % higher.

**Every check below uses the zone 5 corner suction, −26.7 psf ASD, over the whole house.**
That is deliberately conservative: the corner zone is a fraction of the wall area and the
field is 19 % lower.

### Dead

- 24 ga snap-lock standing seam ≈ **1.2 psf**; 26 ga exposed-fastener ribbed ≈ **0.9 psf**
  (the owner's likely substitution).
- SPF 2x4 ≈ **1.3 plf**.

### Tributary per crossing

One block on every OTHER stud (32" o.c. horizontally), girt courses at 24" o.c. vertically:

```
A = 32" x 24" = 768 in² = 5.33 ft²

suction  = 26.7 psf x 5.33 ft² = 142 lb   (Exposure C, the design basis — withdrawal)
suction  = 19.1 psf x 5.33 ft² = 102 lb   (Exposure B, what the site actually is)
pressure = 20.0 psf x 5.33 ft² = 107 lb   (bearing, block on sheathing)
gravity  ≈ 1.2 psf x 5.33 ft² + a course's share of the girt's 1.3 plf ≈ 10 lb
```

A jamb-post block sees the same numbers: the posts are on the same panel and are blocked at
every course elevation the RO crosses, so at 24" or better.

**The tributary is 50 % larger than the 3.56 ft² of the two-tier wall**, and that is the
price of halving the screw count. It is paid in §3, where the utilisation rises and stays
well under one.

---

## 3. The girt crossing screw — the ONLY load path, and three limit states

**FastenMaster TimberLOK, 8", part TLOK08** — 0.189" shank, **2" thread** (ICC-ES ESR-1078,
reissued 2026-01, Table 1A). Coating rated for ACQ-D at or below 0.40 pcf (§4.1.7 / Table 6),
which is what the KDAT girt it passes through requires.

**Superseded 2026-09-12:** this was the Simpson SDWS22800DB. It is not a preference change —
see "the engagement check" below; the SDWS cannot clamp this stack, and nothing in the house
had ever written down the thread length that decides it.

### 3.1 The screw's length, term by term — and there are TWO stacks, not one

```
girt                  1-1/2"  \
block, three plies    4-1/2"  /  the CLAMPED STACK       6"
sheathing               1/2"     nailed to the stud
                      ------
through                 6-1/2"
screw                   8"
                      ------
into the stud           1-1/2"     <- the embedded thread the design is worked at
```

The distinction is the correction. **The sheathing is nailed to the stud**, so it is on the
stud's side of the joint and is not one of the members being drawn together. The clamped
stack is therefore **6.0"**, not the 6-1/2" a through-count gives. Everything below turns on
that number.

The stud is 5-1/2" deep, so 3" of penetration is available and the screw is nowhere near
bottoming out.

### 3.2 The engagement check — the one this note did not previously make

A lag-type screw draws two members together only if the members being clamped are spanned by
**plain shank**. Thread biting in the near member jacks it away from the far one and the
joint stands open, whatever the withdrawal number says.

```
required:  plain shank  >=  clamped stack

TimberLOK 8":   8" - 2" thread = 6.0" shank   vs  6.0" stack   ->  OK, exactly
SDWS22800DB:    8" - 3" thread = 5.0" shank   vs  6.0" stack   ->  1.0" of thread
                                                                   INSIDE the stack
```

**Every SDWS22 has a 3" thread whatever its overall length** — IAPMO UES ER-192 Table 7.
That is the fact this note was missing. An earlier draft cited ESR-2236, which is the
report for the SDS, not the SDWS. At 8" long the SDWS stands an inch of thread in the girt
and block and jacks the girt off its blocks; the fix at 10" (SDWS221000DB) restores the
engagement and the owner wants an 8" screw. TimberLOK's 2" thread clears the stack exactly
and starts where the stud does.

Rothoblaas HBS/TBS 8 mm was checked and rejected — 3-1/8" thread at every length, and
ESR-4645 is dry-service only. HECO TOPIX-plus has no US evaluation report.

### 3.3 Withdrawal from the stud

ESR-1078 **Table 2**, withdrawal per inch of embedded thread, SPF G = 0.42:

```
W      = 170 lb/in                          (ESR-1078 Table 2, published test value)
p      = 1-1/2" of embedded thread          (§3.1)
Z      = 170 x 1.5 x C_D(1.0)  =  255 lb
```

**C_D is 1.0 and that is deliberate.** NDS Table 2.3.2 would give 1.6 for wind, but that
factor belongs to the NDS equation; applying it to a *tested* allowable whose report does
not authorise it would inflate this capacity by 60 % on a clause nobody has read. **The
reviewer is asked to check ESR-1078 §4 and restore 1.6 if the report permits it** — the
design passes either way and this note states the conservative reading.

**C_M is 1.0, dry service.** The embedded thread lands in a stud inside a continuous
closed-cell foam air and water barrier. 0.7 (wet service) is the alternate if a reviewer
disagrees, and would put the capacity at 179 lb — still passing.

**Cross-check against the code's own equation**, printed the way
`notes/board_batten_girt_span.md` prints ER-309's DFL row:

```
NDS 2018 §12.2.1   W = 2,850 G² D = 2,850 x 0.42² x 0.189 = 95.0 lb/in   (unadjusted)
```

The tested 170 lb/in governs; the general equation is here so a reviewer can see the two are
the same order and the report is not an outlier.

**NDS §12.1.4.6 minimum penetration:** 6 D = 6 x 0.189" = **1.134"**, against 1.5" embedded.
Satisfied with margin.

### 3.4 Head pull-through of the girt

ESR-1078 **Table 3**, 1-1/2" side member. The girt IS that side member — a single flat 2x4
of KDAT at SG 0.55 — so the table's assumption is the built condition and not an analogy:

```
head pull-through = 200 lb
```

This is the *lowest* of the three capacities and it is what governs. HeadLOK 8" (HLGM8) is
the recorded alternate: same 2" thread, flat head, 600 lb pull-through at SG 0.55 — three
times the margin. It is not specified because ESR-1078 Table 2 wants **2.0"** of embedded
thread for it, which needs the 1/2" ply counted on the stud side, and the report is silent
on sheathing. If the reviewer is willing to count it, HeadLOK is the better screw.

### 3.5 The demand, and the three ratios

The site's own basis — **115 mph V_ult, Exposure B, Risk Category II** — at the building's
mean roof height of 25.60 ft, worked in full in `notes/board_batten_girt_span.md` §2-§4 and
recomputed identically here because the panel and the screw carry **one** suction:

```
q_h      = 19.27 psf
GC_p     = -1.4   (ASCE 7-16 Fig. 30.3-1, Zone 5 corner, at 1.33 ft² effective area)
GC_pi    =  0.18  (Table 26.13-1, enclosed)
strength = 19.27 x (1.4 + 0.18)         = 30.44 psf
ASD      = 0.6 x 30.44                  = 18.27 psf      (ASCE 7-16 §2.4.1)

tributary = 32" x 24"                   = 5.33 ft²
demand    = 18.27 x 5.33                = 97.4 lb per crossing
```

| limit state | demand | capacity | d/c |
|---|---|---|---|
| thread engagement (shank across the clamped stack) | 6.0 in | 6.0 in | **1.000** |
| withdrawal from the stud | 97.4 lb | 255 lb | 0.382 |
| **head pull-through of the girt** | 97.4 lb | **200 lb** | **0.487** |
| minimum penetration, 6 D | 1.134 in | 1.500 in | 0.756 |

Engagement is a *detailing* row: it reads 1.000 because the screw fits exactly, which is the
right answer and not a margin to be spent. The governing strength state is head pull-through
at **d/c 0.487**.

**Exposure C, printed as the alternate.** §2 works the same wall at Exposure C (26.7 psf
suction, 142 lb per crossing) as a conservatism on a site that is Exposure B by its
surroundings. At C the ratios are 0.558 withdrawal and **0.712 pull-through** — still
passing, on a basis the site does not need.

### 3.6 What a reviewer should know about the wood

**The main-storey studs are LSL, which is outside ESR-1078 §3.2's scope.** They are graded
here at SPF, **G 0.42** — conservative against LP's ~0.50 equivalent — and a reviewer is
asked to confirm or replace that reading. The second-storey and attic studs are ordinary
dimensional SPF and the value is exact for them.

**Lateral support.** The screw is wood-to-wood over its whole through-length with no gap, no
foam and no standoff in the path. This is an ordinary connection, not a cantilevered
fastener through insulation.

### 3.7 There is no redundancy behind it

The two-tier wall put two independent screws at every station on two different modules. This
one puts one, and it is the only thing tying the cladding assembly to the structure. What
buys it back: the screw carries **no gravity at all** (§4), the pattern is simple enough to
inspect from the ground before the foam goes on, and the girt lying across the blocks is
continuous and screwed at every block along its run, so no single screw resists a rotation on
its own.

**Stainless was considered and rejected** (SDWS27800SS, Type 316, IAPMO UES ER-192). It
carries the SDWS's 3" thread and therefore fails §3.2 for the same reason, before cost,
driving torque or thermal bridging is reached. The full cost and thermal argument is recorded
against the screw row in `prices.toml`.

**This section is oracled by `typehaus/engineering/girt_screw.py`**, item
`girt_screw/W-A-N1`, and reproduced by `tests/test_girt_screw_calcs.py`. Run
`haus engineering houses/catlin --item girt_screw/W-A-N1` to see every term above printed
from the model.

---

## 4. Bending, bearing and shear

### The girt — uniform suction, 32" span between blocks

Cladding tributary on one course is 24" of wall height:

```
w   = 26.7 psf x (24/12) ft = 53.4 plf = 4.45 lb/in
M   = w·L²/8 = 4.45 x 32² / 8 = 4.45 x 128 = 570 in-lb
S   = b·d²/6 = 3.5 x 1.5² / 6 = 1.31 in³      (2x4 laid FLAT: b = 3.5", d = 1.5")
f_b = 570 / 1.31 = 435 psi

F_b' = 875 (No.2 SPF) x C_D 1.6 x C_F 1.5 = 2,100 psi     ->  21 % utilised
```

Deflection, E = 1.4 x 10⁶ psi, I = b·d³/12 = 0.98 in⁴, w = 4.45 lb/in over 32":

```
δ = 5·w·L⁴ / (384·E·I) = 5 x 4.45 x 1,048,576 / (384 x 1.4e6 x 0.98) = 0.044"
  = L/727                                                    -> far inside L/240
```

The span doubled (16" -> 32") and the load per foot fell a third (24" of tributary instead
of 32"), so the moment rose from 190 to 570 in-lb — **21 % where the outer girt was 7 %**.
It is still the second-least-utilised element in the wall.

### Block bearing — and why the screw carries no gravity

The block bears on 3-1/2" x 3-1/2" = 12.25 in² of sheathing face, and it is a stack of three
loose plies clamped by the screw, not a glued or nailed built-up member. Every ply bears on
the one below it over the same 12.25 in²; nothing is in tension between them.

```
inward pressure:  107 lb / 12.25 in² = 8.7 psi
gravity:           10 lb / 12.25 in² = 0.8 psi
F_c⊥ = 425 psi (SPF sheathing face / SPF stud behind it)   ->  2 % utilised
```

**This is the reason the fastener schedule can be one screw.** The cladding's weight arrives
at the block and goes straight into the sheathing and the stud behind it in compression; the
screw never sees it. A furring strip standing off 4" of rigid board has no such bearing and
must carry the same weight in bending across a compressible span, which is what sets that
wall's screw spacing (§7.1).

### Shear on the screw

~10 lb per crossing of gravity, against a lateral design value in the hundreds of pounds.
Not close, and it is incidental rather than designed-for: the block bears.

**Nothing in the wood is above 21 % utilised.** The design is governed by the screw
withdrawal at 54 % (Exposure C) / 38 % (Exposure B), and that is where a reviewer's attention
belongs.

---

## 5. Cladding fastening

Shown for completeness; the panel manufacturer's schedule governs the panel-to-girt
connection, and it has margin against the pressures of §2.

**Exposed-fastener ribbed panel** (#12 gasketed screw, D = 0.216", 1-1/4" thread in the
1-1/2" girt, at 12" o.c. across a 24" course spacing):

```
W      = 2,850 x 0.42² x 0.216 = 108.6 lb/in
W_ASD  = 108.6 x 1.25 x 1.6    = 217 lb
demand = 26.7 psf x (12" x 24" = 2.00 ft²) = 53 lb          ->  25 % utilised
```

Closing the courses from 32" to 24" took this from 33 % to 25 %, and it took the panel's own
span question with it (below).

**THE CLADDING SCREW IS 2", TYPE 17 WOOD POINT, STAINLESS OR ASTM A153 CLASS D HDG**
(2026-09-11). Not the 1" "plated" stock pancake screw a panel order ships with, and not the
1-1/2" this note specified before, and this is a specification line:

- it has to take the **full 1-1/2" thickness** of the KDAT girt, because there is no
  sheathing behind the nailer to catch a short screw — the girt stands in free air;
- it lands in treated stock, in weather, galvanically coupled to a coated steel panel. That
  is the one genuine corrosion exposure in this assembly, and it is the opposite case from
  the girt screw of §3, which lives encapsulated in closed-cell foam in dry service;
- Metal Sales' published detail asks for **1/2" past the inside face of the support**.
  **THIS IS NOW CLOSED, not an open variance.** A 1-1/2" screw in a 1-1/2" girt could never
  give it; the 2" does, with the tip standing outside the girt's inboard face, and no
  supplier variance is needed. See `notes/board_batten_girt_span.md` §6, which works the
  withdrawal at the 2" length and prints the 1" and 1-1/2" alternates in d/c;
- **a wood point, not a drill point.** It is graded as an NDS wood screw, and a self-drilling
  point in a 1-1/2" girt reams its own thread away.

> **For the reviewer — the panel's own span.**
> The arithmetic above is the fastener into the girt. The **panel spanning between courses**
> is a separate question. **ESR-4729 does not cover this wall**: it is Western States'
> report, it covers ROOF panels only, and it is written for 24 ga minimum over 16 ga STEEL
> supports. The correct sources are the manufacturers' own wall span tables, and at 24" they
> are comfortable — ASC PS230, Metal Panels Inc. and Homewood all publish 144-168 psf
> allowable negative for PBR at a 3'-0" span, so 6x or better at 24"; Metal Sales publishes
> 58 psf outward / 43 psf inward for 24 ga board & batten at 24", which is d/c 0.31 / 0.43
> against the 18.3 psf ASD zone-5 suction that `notes/board_batten_girt_span.md` works from
> the house's actual mean roof height.

**Coating.** The girt screw of §3 passes through KDAT into SPF, so TimberLOK's coating
rated for ACQ-D at or below 0.40 pcf (ESR-1078 §4.1.7 / Table 6) is the specification. See §9 for the one open question behind
that: which preservative the KDAT actually carries.

---

## 6. Code path

Minnesota 2020 Residential Code, adopting the 2018 IRC.

- **IRC R703.15** governs *cladding attachment directly over foam sheathing* — a furring
  strip or a cladding fastener that passes **through** the foam and bears on it or spans it.
  Table R703.15.1 tabulates fastener size and spacing for exactly that geometry, and its
  4" foam-thickness limit belongs to it.
- **Here nothing is attached through foam, and the one-tier wall makes that clearer, not
  less clear.** The girt is fastened to the structure BEFORE any foam exists: all the wood
  and the whole screw pass happen on the flat wall (§8), and the ccSPF is sprayed around a
  finished frame afterwards. The screw is wood-to-wood over its whole through-length. R703.15
  is not the applicable provision and its 4" limit is moot for the same reason.
- **IRC R703.3.2** makes a cladding attachment above 30 psf a designed one in any case, which
  is what this note is.
- **The applicable path is IRC R301.1.3 engineered design**, and the girt-to-framing
  connection is a plain NDS connection — §3.
- **Cladding-to-girt** is IRC R703.3 plus the panel manufacturer's schedule (§5).
- **IRC R702.7.1 / the SPFA 50 % ratio** — the condensation-control ratio for a Class II
  interior vapour situation. 4" of ccSPF is R-26 over a bay at R-20.4, i.e. **56 % of the
  assembly's R outboard of the framing**, against the 50 % SPFA guidance and comfortably over
  the R-11.25 that zone 6 asks for a 2x6 wall. It cleared before and it clears by more now:
  the deleted inner girt was wood in the outboard half.
- **The water, air and vapour control layer is the ccSPF**, exactly as
  `notes/outie_window_truss_detail.md` records. There is no WRB sheet: the foam is sprayed
  after the window bucks are set and is continuous around every opening.

---

## 7. Thermal

1-D parallel path, the same reading `analysis._layer_rsi` takes, at ccSPF R-6.5/in, KDAT
R-0.95/in, fibreglass R-3.7/in.

| band | make-up | framing fraction | R |
|---|---|---|---|
| A | 4" ccSPF (R 26.0), crossed by the 3-1/2" x 3-1/2" block over a 32" x 24" crossing | **1.6 %** | **23.8** |
| A' | the block's proud 1/2" — vented gap | — | **0** |
| B | the girt, outboard of the vent gap | — | **0** |

```
ff = (3.5 x 3.5) / (32 x 24) = 12.25 / 768 = 0.0160

band A: 1/R = 0.984/26.0 + 0.016/3.80 = 0.03785 + 0.00421 = 0.04205  ->  R 23.78
```

(The block is 4-1/2" deep but only 4" of it is in the band; the proud 1/2" is the gap.)

**The foam zone went 21.1 -> 23.8, and every point of it is the deleted inner girt.** That
tier put 3-1/2" of flat wood across every course through the first 1-1/2" of the foam — a
10.9 % framing fraction — plus a second block tier in band C. What replaced all of it is a
single 1.6 % block, and the fraction fell for two reasons at once: there is one block tier
instead of two, and its crossing grid opened from 16" x 32" (512 in²) to 32" x 24" (768 in²),
so the same 12.25 in² of wood is spread over half again as much wall.

**Whole wall, wood only: R-39.8.** Everything inboard of the foam zone — gypsum, the 2x6 stud
bay with its fibreglass batt at 23 % framing, the sheathing and the air films — sums to
**R-16.1**, and 16.1 + 23.8 = 39.85. It was **R-37.3** on the two-tier wall.

### 7.0 The fasteners, counted the same way the wood is

The wood-only number above is what this note has always reported, and it leaves the screws
out. They are not negligible, and both designs deserve the same treatment.

A screw is 0.220" diameter = **0.038 in²** of steel (k ≈ 300 Btu·in/hr·ft²·°F), and it runs
up the **middle of the block**, so it is a steel core inside the wood path rather than a
fourth path through the foam. Counted the same isothermal-planes way the blocks are:

```
band A with the screw:
  foam    (768 - 12.25) / 26.00        = 29.067
  wood    (12.25 - 0.038) / 3.80       =  3.214
  steel   0.038 / (4.0/300 = 0.01333)  =  2.851
  total C = 35.132 over 768 in²  ->  U = 0.04574  ->  R 21.86
```

**So the screws cost R-1.9 in the band and the wall is R-37.9, not R-39.8.** On the two-tier
wall the same arithmetic gives band A 8.86 -> 7.83 and band C 5.99 -> 5.50, a foam zone of
20.0 against 21.6, and a whole wall of **R-36.1**.

**The through-screw IS slightly worse than the two it replaces — and the deleted girt pays
for it three times over.** A third as many screws each crossing three times the depth is
roughly a wash in count-times-length, and the new one loses on top of that because it crosses
foam where the old block-1 screw crossed only 1-1/2". The comparison, wall to wall:

| | two tiers | one tier (this wall) |
|---|---|---|
| wood only | R-37.6 | **R-39.8** |
| with fasteners | R-36.1 | **R-37.9** |
| fastener penalty | −1.5 | −1.9 |

**Both columns of that table are an upper bound on the penalty, and the reason is worth
stating.** The isothermal-planes method used throughout §7 assumes heat spreads laterally
between layers, which for a small high-conductance rod overstates the bridge; the opposite
bound — a strictly isolated parallel path, where the screw's 0.0096 % of the area carries the
whole wall's R in series behind it — puts the penalty near **zero**. The truth is in between
and nearer the isothermal figure, and pinning it needs a 2-D or 3-D model that this note does
not build. **Quote the range, never one end of it.**

`preferences.toml` sets `wall_r = 40`. **At R-39.8 wood-only the wall now effectively meets
it** (0.2 short, inside the noise of any of these readings); at R-37.9 with the fasteners
counted it is 2.1 short. It was 2.7 short before this change on the wood-only basis and 3.9
short with fasteners. **The model's own card reads R-43.5 and is 3.7 points optimistic**, for
two reasons that have not changed: the blocks are framed by the resolver rather than authored
as a `CavityFill`, so band A reads as unbroken foam; and the girt is a solid layer with no
fill, so the card credits its R-1.4 although it stands outboard of a vented gap and is
thermally outside the envelope.

### 7.0.1 The bucks are not the bridge; the blocks are

It is easy to look at a section and conclude the opposite — the buck is a continuous ring of
wood right through the insulation at every opening, and the blocks are little pieces. Counted,
it is the other way round by an order of magnitude:

```
buck   3/8" plywood, 512 LF of reveal, k ≈ 0.80 Btu·in/hr·ft²·°F, path 6"
       A = 0.375" x 512 LF = 16.0 ft²        C = 0.80 x 16.0 / 6.0   =  2.1 Btu/hr·°F
block  1,128 blocks x 12.25 in², KDAT k ≈ 1.05, path 4" (the foam band)
       A = 96.0 ft²                          C = 1.05 x 96.0 / 4.0   = 25.3 Btu/hr·°F
```

**The blocks are roughly 12x the bucks.** Two reasons compound: the buck is a thin *sheet* on
its edge — 3/8" against the block's full 3-1/2" x 3-1/2" — and it is plywood, which is about
25 % less conductive than the solid KDAT of a block. If the fastener term is ever worth
chasing (§3, and the stainless rejection recorded in `prices.toml`), the blocks are the term
to chase and the bucks are not.

### 7.1 Against the rigid-foam wall — the comparison this wall type exists to win

This is the argument the owner's intuition raises: *this wall pays for wood inside the
insulation layer, and a rigid-foam wall does not.* That is true. Here is what it buys back.

Same studs, same OSB, same 4" exterior layer, same 8" screws; only the exterior layer differs.

| exterior layer | ccSPF + block girt (this wall) | 4" polyiso + furring |
|---|---|---|
| nominal | R-26 (6.5/in aged) | R-22 (24 on the label, cold-derated) |
| wood crossing the layer | 1.6 % blocks | **none** — the furring is outboard of the foam |
| screws crossing it | 1 per 5.33 ft² | 1 per ~2.7 ft² |
| effective, screws counted / not | **R-21.9 to R-23.8** | **R-19.0 to R-22.0** |

```
polyiso, 1 screw per 2.7 ft² = 388.8 in²:
  foam   (388.8 - 0.038) / 22.0        = 17.671
  steel  0.038 / (4.0/300)             =  2.851
  total C = 20.52 over 388.8 in²  ->  U = 0.05278  ->  R 18.95
```

The three terms, in size order:

1. **ccSPF's R/inch over cold-derated polyiso is worth ≈ +4 R and dominates.** Polyiso's
   labelled R-6/in is measured at 75 °F mean and falls through a Minnesota winter; 6.5/in
   aged for ccSPF does not.
2. **Half the screw density is worth ≈ +1 R, and it is a consequence of the BLOCK, not of
   the fastener.** The block bears the cladding's gravity in direct compression (§4), so this
   screw is a pure withdrawal element at 54 % of allowable. A furring screw over rigid board
   carries that same gravity in bending across a compressible 4" span, and **its spacing is
   set by that**, not by withdrawal.
3. **The blocks cost ≈ −1.6 R.** This is the owner's objection, and it is real.

**Net ≈ +3 R**, before two differences that are not R-values at all: the foam is the air and
water barrier (no WRB, no taped seams, no sequencing risk at an opening), and it is bonded to
the sheathing rather than standing the cladding off a creeping substrate.

> **The one number here that is an argument rather than a citation** is the "roughly 2x"
> furring-screw density. It is reasoned from what sets that spacing — gravity in bending over
> a compressible span — and not read off a table. Read IRC R703.15's own table at 4" foam
> before this note is printed with the ratio in it, or print the argument without the ratio.

`prices.toml` (~767-770) says the structural half of this in its own words: the girt screws
replaced *"the 10" screws holding 1/2" furring through 4" of rigid board... every fastener
here is wood-to-wood with continuous lateral support and nothing bears on foam."* This
section is that sentence with the R numbers attached.

---

## 8. Sequencing

**This is the labour case for the whole design, and it is the owner's first priority.** All
the wood and the entire screw pass happen ON THE FLAT WALL, before it is stood up; the
sprayer arrives once, to a finished frame. There is no framing operation between two foam
lifts any more, which is what used to force a second mobilisation.

1. **Sheathe**, flat on the deck. 1/2" plywood, ordinary schedule.
2. **Mark the 24" course lines off the sole plate**, and snap the stud lines across them.
3. **Bucks.** 6" deep, all four sides of every rough opening — unchanged.
4. **Drop three offcuts at each crossing** on every other stud line. Loose, no tack: the
   girt screw clamps them.
5. **Lay the girt over them, mark the stud line across its face, drive the 8" TimberLOK
   (TLOK08).** The mark is not optional — the screw is otherwise blind through 6" of wood
   into a 1-1/2" target. **Head seated FLUSH** — not recessed, not proud; the panel bears on
   this face, and the screw's 6" of plain shank is what draws girt and block down onto the
   sheathing. **If the head will not pull down, the screw is wrong.** That is the field
   symptom of §3.2: a thread standing in the clamped stack jacks the girt off its blocks, and
   no amount of driver is the answer.
6. **Jamb posts and head/sill courses at each RO**, on their own blocks, screwed at ≤ 24".
7. **Tilt.**
8. **Foam: one 4" application** of **Huntsman Heatlok HFO High Lift (ICC-ES ESR-4073)**,
   sprayed through the 20-1/2" clear between courses and behind them — the girt stands 1/2"
   off the foam face, so the whole plane is reachable from outside. **§4.2 permits 6-1/2" per
   pass**, and the TDS ladder is 6.5" at or below 70 F, 4" at 70-80 F, 3.25" above 80 F, so
   4" in one application holds **below 80 F** and substrate temperature on the day is the
   condition. Heatlok HFO *Pro* is a different product (ESL-1372, 2" per pass) and would force
   a second lift and a second mobilisation; do not let a supplier substitute it silently. **Fillet against the block sides** (BSI-048), do not butt square. **Shave to a
   gauge 1/2" behind the block's outer face**; the blocks stand proud at every crossing and
   are the gauge.
9. **Sill pans, jamb trim, windows, head flashing, head trim, cladding.**

**What is given up, and it is a real cost.** With every wall section framed on its own deck
off its own sole plate, a **±1" course step between wall sections is tolerated**. The
alternative — stringing the courses across a whole facade after tilt-up — is the standard
mitigation for oil-canning, whose named cause is support misalignment. It is given up
deliberately, on the owner's premise that the labour is worth more than the line. Say so to
the cladding installer rather than letting them discover it.

## 9. Risks, stated plainly

**THE FOAM IS THE ONLY WATER PLANE, AND ITS WRB LISTING IS AN OPEN ALTERNATE-APPROVAL ITEM.**
This wall has no housewrap, no building paper and no membrane: the ccSPF is air, water,
vapour and thermal in one application, and §1 says so. **ICC-ES ESR-4073 does not evaluate
water-resistive barrier.** The only ccSPF report found granting a WRB listing is Icynene
ProSeal Eco (ESR-3493 §4.6, 1-1/2" minimum) and it **expired in 2021**, so it cannot be
leaned on. Approval here runs through **Minn. R. 1300.0110** (alternate materials and
methods) on **Huntsman's own ASTM E331 and ASTM E2178 data for the product actually bought**.
That data has to be in hand before the order, not at inspection. It is stated here as an open
item rather than buried, because a reviewer reading §1 would otherwise reasonably assume the
WRB question was closed by the ESR, and it is not.


**Foam shrinkage at the block, and the fillet.** Planed lumber shrinks; a square cold joint
where the foam meets a block side is exactly where a crack goes, and this wall has 1,131
blocks with four sides each. The specification is **a fillet against every block side**
(BSI-048's rule for foam against a projecting member), not a butt. It is a spray technique,
it costs nothing in material, and it is inside the labour half of the ccSPF rate in
`prices.toml`. It is a hold point on the first wall, not an inspection at the end.

**The screw is blind, and the mark is the mitigation.** 8" through 6" of wood into a 1-1/2"
stud, driven from outside the girt. The stud line must be marked ACROSS the girt face as it
is laid (§8 step 5). A missed stud is invisible once the foam is on, and this is a single
load path. **Inspect the screw pattern from the ground before the sprayer arrives** — it is
the last moment it can be seen, and it is cheap.

**One block on the house lands 3" off its stud, and it is a field instruction.** `W-A-N1`'s
course at the attic gable is cut by the RAKE at 128.0" — 1-3/4" past the king over that
window's head — so the mandatory end block lands at 129.75" where the nearest stick is that
king at 126.75". The frame will not move it (the block would stand 3" out past the girt it
carries), and the frame is right. **Drive this one into the king and let the girt end bear on
the block's outer half**, or add a cripple at the module.
`test_truss_girt_geometry.py::test_the_block_lands_on_the_stud_it_is_screwed_to` names it and
holds the count at one; if it ever grows, the block grid has drifted and that is a different
problem.

**Water on the flat girt top.** A 3-1/2" horizontal ledge behind cladding will collect what
gets past the panel. It can go back into the 1/2" gap behind the girt (which is the drainage
plane, and is CONTINUOUS now that nothing else stands in it) or forward past the girt's face.
Both drain down the vented cavity to the screened base. A bevel rip on the girt top is **not**
required and is not modelled. What carries this is the vent plus the KDAT — and the KDAT is
not optional for that reason.

**Which preservative the KDAT actually carries — OPEN.** §3's rejection of stainless rests on
the DB coating being sufficient for the girt screw, which holds comfortably for copper azole
or micronized CA in dry service. Simpson rates **ACQ-Type D** as more corrosive than either
and asks for ZMAX/HDG as the *connector* minimum against it. Zelinka, Glass & Derome (USFS
Forest Products Lab, *Corrosion Science* 83 (2014) 67-74) measured fastener corrosion in
ACQ-treated wood as **"nearly undetectable" at 75 % RH (~14 % MC)**, with a sigmoidal
threshold near 15 % MC — and this screw is encapsulated in closed-cell foam, which is dry
service by definition. **Confirm the supplier's treatment before this note closes the
corrosion question.**

**Two owner-optional upgrades, not material swaps.** Switching the girt to 20 ga hat channel
or a composite/FRP section was assessed and rejected — KDAT 2x4 stays: steel loses
too much screw pullout margin for the PBR field fastening (§5) and still needs KDAT jamb posts
and head/sill courses at every opening either way, and FRP runs 4-6x the KDAT rate for
durability this wall's vent gap and PBR rib voids already cover. Two narrower items are worth
carrying as options:

- **Brush-treat field-cut ends** with copper naphthenate as they are cut. KDAT's .15 pcf
  retention does not follow the saw, and a course-to-course butt is a fresh untreated cut.
  **The block plies make this bigger than it was**: 3,384 offcuts, six cut faces each.
- **Acetylated wood (e.g. Accoya) for the jamb posts and head/sill courses at openings**
  (~192 LF) — the hardest KDAT to inspect or replace later, sitting behind the window returns
  where the sill pan and panel jamb closure meet. Also drops the DB-coating requirement on
  fasteners into it.

**Field courses stop clear of every opening.** The girt frame holds field courses one piece
width (3-1/2") clear of each rough opening in both axes and fills that zone with the opening's
own frame — a jamb post on each side with its inner face on the RO edge, and head and sill
courses spanning the opening. There is no 60" unsupported head course: the head course is
blocked back to the cripples at every module station under it.

**Window elevations and course breaks.** Every window taller than 24" now interrupts some
field courses; that is inherent to a horizontal girt and is not a defect. What *is* avoidable
is a near-miss — a head or sill landing an inch or two off a course line, which turns one
clean junction into two pieces of framing inches apart. **The design rule:**
`course_offset` is 0, so a course BOTTOM lands on the framing-base
module, and a new opening wants its **HEAD on a 24" multiple above the sole plate, or its
SILL 3-1/2" above one**. Thirteen of catlin's opening edges land exactly on a course line and
thirty sit in the 7" shadow of one, which is the swept optimum among the phases that keep
every bay within the module. See
`test_truss_girt_courses.py::test_no_field_course_lands_in_the_shadow_of_a_head_or_sill_course`
for the sweep and `notes/outie_window_truss_detail.md` for the per-opening table.

---

## 10. What the reviewer is being asked to confirm

1. The ASCE 7-16 C&C pressures in §2, and whether Exposure C is the right conservatism.
2. **The single load path.** §3 at 0.487 governing (Exposure B, the site's own basis) /
   0.712 (Exposure C) on one 8" screw per 5.33 ft², with the block carrying gravity in
   bearing so the screw is pure withdrawal. Is one fastener per crossing acceptable without
   redundancy, and is 1-1/2" of thread into the stud the right design penetration when 3" is
   available?
3. The ESR-1078 Table 2 withdrawal value in §3.3, and its NDS §12.2 cross-check.
4. That §6's reading is right: that a wood-to-wood screw with continuous lateral support
   between framing members, driven before any foam exists, is an R301.1.3 engineered
   connection and not an R703.15 through-foam furring attachment.
5. Whether anything in §9 needs to become a specification line rather than a note — the
   fillet at the blocks and the marked stud line are the two candidates.
6. **§3.2, the thread engagement check**, and whether the clamped stack is rightly read as
   6.0" (girt + block) rather than 6-1/2". The sheathing is nailed to the stud; the note's
   position is that it is therefore on the stud's side of the joint and is not a member being
   drawn together. If a reviewer reads it the other way, the TimberLOK no longer clears and
   the screw goes to 10".
7. **§3.4, head pull-through**, which is the governing state and the lowest of the three
   capacities. Specifically: is ESR-1078 Table 3's 1-1/2" side member at SG 0.55 the right
   row for a single flat KDAT 2x4 standing in free air, and is HeadLOK worth the 2.0"
   embedded-thread reading it would require?
8. **§3.3's C_D of 1.0.** ESR-1078 §4 should be checked; if the report authorises a
   load-duration adjustment, withdrawal capacity rises to 408 lb and d/c falls to 0.239.

---

## Sources

Every standard and document this note rests on, collected from the citations above.
Citation style is the house style: issue year on first use (`ASCE 7-16 §29.3`),
section form after. A document is listed here only if a number in this note came
out of it.

- **ASCE 7-16**
- ASTM A153, ASTM D1623
- **IAPMO UES ER-192** (SDWS thread lengths, Table 7 — the superseded screw)
- **ICC-ES ESR-1078** (FastenMaster TimberLOK, reissued 2026-01; Tables 1A, 2, 3, §4.1.7)
- **ICC-ES ESR-4073** (Huntsman Heatlok HFO High Lift; §4.2, §4.4.2)
- ICC-ES ESR-3493 (Icynene ProSeal Eco §4.6 — expired 2021, cited only as not usable)
- IAPMO UES ER-309 (AEP Span; the published open-framing alternative, §5)
- Minn. R. 1300.0110
- IRC R301.1.3, IRC R702.7.1, IRC R703.15, IRC R703.3, IRC R703.3.2, IRC Table R703.15.1
