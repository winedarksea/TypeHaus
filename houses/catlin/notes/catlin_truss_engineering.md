# The catlin truss — engineering basis for an engineer's review and stamp

**House:** catlin, Minnesota (MN 2020 Residential Code, adopting the 2018 IRC).
**Element:** the exterior wall's cladding stand-off — two tiers of flat horizontal 2x4 girts
carried on 3-1/2" blocks, outboard of the sheathing and inside/behind 4" of closed-cell
spray foam.
**Written:** 2026-08-26. Every number below is recomputed here from first principles, with
the arithmetic shown, so a reviewer can check the whole chain without opening the model.
**What is asked of the reviewer:** this is a plain NDS connection design under IRC R301.1.3
engineered design. It is not a prescriptive furring schedule and does not claim to be one.
See §6 (Code path) for why IRC Table R703.15.1 is not the applicable provision.

---

## 1. The assembly

Four 1-1/2" layers outboard of the 1/2" plywood sheathing, all 2x stock, all horizontal:

| band | depth off sheathing | what | material |
|---|---|---|---|
| A | 0 – 1-1/2" | ccSPF, crossed by **block-1** (3-1/2" along the wall × 3-1/2" tall × 1-1/2" thick) at every stud station under every girt course | SPF |
| B | 1-1/2 – 3" | **inner girt** — 2x4 laid flat, horizontal, 24" o.c.; one 5" SDWS per block-1 through girt + block + sheathing into the stud | SPF |
| C | 3 – 4-1/2" | 1" ccSPF + 1/2" vented gap, crossed by **block-2** at MID-BAY stations, 8" off the block-1 line, bearing on the inner girt | KDAT |
| D | 4-1/2 – 6" | **outer girt** — 2x4 flat, same 24" courses at the SAME elevations; one 5" SDWS per block-2 into the inner girt; the cladding nailer and the window mount plane | KDAT |

Foam total 4" (band A + band B fill + the inner 1" of band C). Cladding face 6-1/2" proud of
the sheathing. Windows are OUTIE: the mount plane is the outer face of the outer girt.

**Materials are by exposure, and it is a rule of the design.** Everything inboard of the
foam face — block-1, the inner girt, and the inner band's jamb posts and head/sill courses —
is plain SPF: it is encapsulated in closed-cell foam and never sees water. Everything
standing in or outboard of the vent gap — block-2, the outer girt, and the outer band's
posts and courses — is KDAT. The outer girt is a 3-1/2"-deep horizontal ledge behind the
cladding that will wet-cycle for the life of the wall, and block-2's face is a ledge every
16" on the foam plane; treated stock is what carries that, not the vent alone.

**The screws are offset, not stacked.** Block-2 sits half a stud bay (8") off block-1, so no
fastener passes through both tiers. Every screw in this wall is **wood-to-wood with
continuous lateral support** — girt → block → sheathing → stud, or girt → block → inner girt.
No fastener bears on foam or cantilevers through it, which is the failure mode IRC Table
R703.15.1 tabulates and the reason that table's geometry does not describe this wall.

As built by the model: **1,957 block-1** and **2,197 block-2** across the house, one 5" SDWS
each — 4,154 screws total. The two counts differ because the two tiers' stations are offset
half a bay, so the module lands differently against course ends and rough openings.

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

### Tributary per block

Blocks at 16" o.c. horizontally (the stud module), girt courses at 24" o.c. vertically:

```
A = 16" × 24" = 384 in² = 2.67 ft²

suction  = 26.7 psf × 2.67 ft² = 71 lb   (withdrawal on the screw)
pressure = 20.0 psf × 2.67 ft² = 53 lb   (bearing, block on girt / block on sheathing)
gravity  ≈ 1.2 psf × 2.67 ft² + a share of the girt's 1.3 plf ≈ 5–7 lb
```

Both tiers see the same numbers, and so does a jamb-post block: the posts are on the same
16"/24" grid geometry with the same panel behind them.

---

## 3. Screw withdrawal — the governing check

Simpson **SDWS22500DB**, 0.220" shank × 5" long, DB (double-barrier) coating rated for
treated lumber.

NDS 2018 §12.2.3, wood screw withdrawal, W = 2,850 · G² · D lb per inch of thread
penetration; SPF G = 0.42, D = 0.220":

```
W    = 2,850 · 0.42² · 0.220 = 2,850 · 0.1764 · 0.220 = 110.6 lb/in
```

Thread penetration into the receiving member is **1-1/2"** (the design minimum; the 5" screw
has more available):

```
W_ref = 110.6 × 1.5 = 166 lb
W_ASD = 166 × C_D(1.6, wind) = 265 lb

utilisation = 71 / 265 = 27 %
```

**Block-1 screw:** 1-1/2" girt + 1-1/2" block + 1/2" sheathing = 3-1/2" through, then 1-1/2"
into the stud = **5.0" required**.
**Block-2 screw:** 1-1/2" girt + 1-1/2" block = 3" through, then 1-1/2" into the flat inner
girt = **4.5" required**. Same 5" part, same G = 0.42, same 265 lb.

Both are 27 % utilised at the corner-zone suction, 22 % in the field.

> **For the reviewer.** Substitute the ESR-2236 tabulated withdrawal value for the SDWS in
> place of the NDS general equation if you prefer; it is the same order of magnitude and the
> utilisation stays well under half. The point of the general equation here is that it is
> checkable without a proprietary report.

**Lateral support.** Both screws are wood-to-wood over their whole through-length with no
gap, no foam and no standoff in the path. This is an ordinary NDS connection, not a
cantilevered fastener through insulation.

---

## 4. Bending, bearing and shear

### Inner girt — worst case is a block-2 point load mid-span

Block-2 lands mid-bay, i.e. at the middle of a 16" span between two block-1s. Treat the
girt as a simple beam over 16":

```
M = P·L/4 = 71 × 16 / 4 = 284 in-lb
S = b·d²/6 = 3.5 × 1.5² / 6 = 1.31 in³      (2x4 laid FLAT: b = 3.5", d = 1.5")
f_b = 284 / 1.31 = 216 psi

F_b' = 875 (No.2 SPF) × C_D 1.6 × C_F 1.5 = 2,100 psi     →  10 % utilised
```

Deflection, E = 1.4 × 10⁶ psi, I = b·d³/12 = 3.5 × 1.5³ / 12 = 0.98 in⁴:

```
δ = P·L³ / (48·E·I) = 71 × 4,096 / (48 × 1.4e6 × 0.98) = 0.004"
```

### Outer girt — uniform suction from the cladding, 16" span

Cladding tributary on one course is 24" of wall height:

```
w = 26.7 psf × (24/12) ft = 53.4 plf = 4.45 lb/in
M = w·L²/8 = 4.45 × 256 / 8 = 142 in-lb
f_b = 142 / 1.31 = 108 psi                                →   5 % utilised
```

### Block bearing perpendicular to grain

The block bears on 3-1/2" × 3-1/2" = 12.25 in² of face:

```
F_c⊥ = 425 psi (SPF)  →  capacity 425 × 12.25 = 5,200 lb   vs 53 lb   →  1 % utilised
```

### Gravity shear on the screw

5–7 lb per block against a lateral design value in the hundreds of pounds. Not close.

**Nothing in the wood is above 10 % utilised.** The design is governed by the screw
withdrawal at 27 %, and that is where a reviewer's attention belongs.

---

## 5. Cladding fastening

Shown for completeness; the panel manufacturer's schedule governs the panel-to-girt
connection, and both options below have margin against it.

**Exposed-fastener ribbed panel** (#12 gasketed screw, D = 0.216", 1-1/4" thread in the
1-1/2" outer girt, at 12" o.c. across a 24" course spacing):

```
W    = 2,850 × 0.42² × 0.216 = 108.6 lb/in
W_ASD = 108.6 × 1.25 × 1.6 = 217 lb
demand = 26.7 psf × (12" × 24" = 2.0 ft²) = 53 lb          →  25 % utilised
```

**Snap-lock clip** (#10 × 1" screw, D = 0.190", ~0.9" effective thread, two screws per clip,
clips at 24" o.c. on a 16" seam spacing):

```
W    = 2,850 × 0.42² × 0.190 = 95.5 lb/in
W_ASD = 95.5 × 0.9 × 1.6 = 137 lb per screw
demand per clip = 26.7 psf × (16" × 24" = 2.67 ft²) = 71 lb, over 2 screws = 36 lb each
                                                            →  26 % utilised
```

**Coating.** Block-2's screw passes through KDAT into SPF, so the SDWS's DB coating (rated
for treated lumber) is the specification, not an upgrade. The cladding fasteners land in the
KDAT outer girt and must be treated-lumber rated too. Exposed-fastener panel screws already
are; **snap-lock clip screws are not by default — say so on the order.**

---

## 6. Code path

Minnesota 2020 Residential Code, adopting the 2018 IRC.

- **IRC R703.15** governs *cladding attachment directly over foam sheathing* — a furring
  strip or a cladding fastener that passes **through** the foam and bears on it or spans it.
  Table R703.15.1 tabulates fastener size and spacing for exactly that geometry, and its
  4" foam-thickness limit belongs to it.
- **Here nothing is attached through foam.** Band A is sprayed to the block-1 faces before
  the inner girts go on; band C is shaved to a gauge behind the block-2 faces before the
  outer girts go on. Every screw is wood-to-wood over its whole length with continuous
  lateral support. R703.15 is therefore not the applicable provision, and its 4" limit is
  moot for the same reason.
- **The applicable path is IRC R301.1.3 engineered design**, and the furring-to-framing
  connection is a plain NDS connection — this note.
- **Cladding-to-furring** is IRC R703.3 plus the panel manufacturer's schedule (§5).
- **The water, air and vapour control layer is the ccSPF**, exactly as
  `notes/outie_window_truss_detail.md` records. There is no WRB sheet and nothing here
  changes that: the foam is sprayed after the window bucks are set and before the outer
  girts, and it is continuous around every opening.

---

## 7. Thermal

1-D parallel path, the same reading `analysis._layer_rsi` takes, at ccSPF R-6.5/in, SPF and
KDAT ≈ R-1.25/in and R-0.95/in respectively.

| band | make-up | framing fraction | R |
|---|---|---|---|
| A | 1-1/2" ccSPF (R 9.75), crossed by 1-1/2" SPF block-1 (R 1.88) | 3.2 % | **8.6** |
| B | 1-1/2" ccSPF (R 9.75), crossed by 3-1/2" of flat SPF girt per 24" course (R 1.88) | 14.6 % | **6.0** |
| C | 1" ccSPF + 1/2" vented gap (R 6.5), crossed by 1-1/2" KDAT block-2 (R 1.43) | 3.2 % | **5.8** |
| D | outer girt, outboard of the vent gap | — | **0** |

```
band A:  1/R = 0.968/9.75 + 0.032/1.88 = 0.0993 + 0.0170 = 0.1163  →  R 8.6
band B:  1/R = 0.854/9.75 + 0.146/1.88 = 0.0876 + 0.0779 = 0.1655  →  R 6.0
band C:  1/R = 0.968/6.50 + 0.032/1.43 = 0.1489 + 0.0224 = 0.1714  →  R 5.8

foam zone total = 8.6 + 6.0 + 5.8 = 20.4     (against 26.0 for 4" of unbroken ccSPF)
```

**Whole wall, honest: ≈ R-37.5.** Everything inboard of the foam zone — gypsum, the 2x6 stud
bay with its mineral wool at 23 % framing, the sheathing, and the air films — sums to about
R-17.1, and 17.1 + 20.4 = 37.5.

**The model's own card reads R-40.7, and that is 3.2 points optimistic.** Two reasons, both
worth knowing:

1. The blocks are framed by the resolver, not authored as a `CavityFill`, so bands A and C
   carry no framing factor on the card and read as unbroken foam.
2. The outer girt is a solid layer with no fill, so the card credits its R-1.4 — but it
   stands outboard of a vented gap and is thermally outside the envelope.

**`preferences.toml` sets `wall_r = 40`. This wall does not meet it, at R-37.5.** The card
says otherwise and the card is wrong. State it plainly rather than reading the target as met.

**The 2-D truth is better than the 1-D number, and 1-D cannot credit it.** The buried inner
girt is a fin connecting a block-1 and a block-2 that are 8" apart along the wall, not
stacked. A 1-D parallel path treats each band independently and so charges the full
short-circuit at every layer; the real heat path has to travel that 8" through 1-1/2" of
wood before it can cross the next band. The stagger is a thermal decision as much as a
fastening one, and its benefit is unclaimed here.

---

## 8. Sequencing

This replaces the build order in `notes/outie_window_truss_detail.md`, and step 4 is the one
that cannot be reordered.

1. **Sheathe.** 1/2" plywood, ordinary schedule.
2. **Bucks.** 6" deep, all four sides of every rough opening. They go on before the foam,
   because the foam is the water plane and it can only be continuous around an opening if
   the buck is already there to spray to.
3. **Snap the stud lines** on the sheathing, and **tack the block-1s** — one nail each. The
   block is the screw's *spacer*, not its anchor; the 5" SDWS that actually holds it is
   driven later, through the girt.
4. **First foam lift, 1-1/2", flush to the block-1 faces.** *Before the inner girts.* A flat
   girt lying 1-1/2" off the sheathing shadows the pocket behind it, and foam sprayed after
   the girt is on will void there. This is not a preference about access; it is the reason
   band A is a separate lift.
5. **Inner girts**, plus the jamb posts and head/sill courses at every opening, set on the
   blocks. One 5" SDWS per block through girt + block + sheathing into the stud.
6. **Tack the block-2s** mid-bay on the inner girts, 8" off the block-1 line.
7. **Second foam lift, 2-1/2", shaved to a gauge 1/2" behind the block-2 faces** — i.e. to
   the inner-girt face plus 1". See §9.
8. **Outer girts** on the block-2s, one 5" SDWS each.
9. **Sill pans, windows, cladding.**

---

## 9. Risks, stated plainly

**The 1/2" gap is inside ccSPF surface tolerance.** A sprayed lift is not a machined surface,
and a half inch of clearance can close locally. The specification is that the applicator
**shaves band C to a gauge** — inner girt face + 1" — rather than spraying to a thickness and
hoping. Two alternatives buy margin if the owner wants it, and either is a clean substitution:

- a **2" block-2** (giving a 1" gap, and a 6-1/2" stack instead of 6"), or
- **3-3/4" of foam** instead of 4" (giving a 3/4" gap at the cost of R-1.6).

**Water on the flat outer-girt top.** A 3-1/2" horizontal ledge behind cladding will collect
what gets past the panel. It can go back into the 1/2" gap behind the girt (which is the
drainage plane) or forward past the girt's face. Both are open, both drain down the vented
cavity to the screened base. A bevel rip on the girt top is **not** required and is not
modelled. What carries this is the vent plus the KDAT in the two outer layers — and the
KDAT is not optional for that reason.

**Fastener coating.** Block-2's screw passes through KDAT into SPF, so the DB coating is the
spec. Cladding fasteners land in KDAT and must be treated-rated: exposed-fastener panel
screws already are, snap-lock clip screws generally are not (§5).

**Two owner-optional upgrades, not material swaps.** A 2026-08-26 assessment of switching
the outer girt to 20 ga hat channel or a composite/FRP section concluded KDAT 2x4 stays —
steel loses too much screw pullout margin for the 2,473-count PBR field fastening (§5) and
still needs KDAT jamb posts and head/sill courses at every opening either way, and FRP runs
4-6x the KDAT rate for durability this wall's vent gap and PBR rib voids already cover. Two
narrower, cheaper items from that review are worth carrying as options, applied at the
owner's discretion rather than changing `assemblies.py`:

- **Brush-treat field-cut ends** with copper naphthenate as they're cut. KDAT's .15 pcf
  retention doesn't follow the saw, and a 2,432 LF field course puts a fresh untreated cut
  at every course-to-course butt.
- **Acetylated wood (e.g. Accoya) for the jamb posts and head/sill courses at openings**
  (~192 LF) — the hardest KDAT to inspect or replace later, sitting behind the window
  returns where the sill pan and panel jamb closure meet. Also drops the DB-coating
  requirement on fasteners into it.

**Field courses stop clear of every opening.** The girt frame holds field courses one piece
width (3-1/2") clear of each rough opening in both axes, and fills that zone with the
opening's own frame — a jamb post on each side with its inner face on the RO edge, and head
and sill courses spanning the opening. There is no 60" unsupported head course: the head
course is blocked back to the cripples at every stud station, so its span is 16".

**Window elevations and course breaks.** Every window taller than 24" necessarily interrupts
some field courses; that is inherent to a horizontal girt and is not a defect. What *is*
avoidable is a near-miss — a head or sill landing an inch or two off a course line, which
turns one clean junction into two pieces of framing inches apart. Where a window's head
elevation lands exactly on a course line, or its sill exactly 3-1/2" above one, the opening's
head or sill course **is** the field course and nothing extra is cut. See
`notes/outie_window_truss_detail.md` for which of catlin's openings currently do that and
which do not.

---

## 10. What the reviewer is being asked to confirm

1. The ASCE 7-16 C&C pressures in §2, and whether Exposure C is the right conservatism.
2. The NDS withdrawal value in §3, or its ESR-2236 substitute, and the 1-1/2" minimum thread
   penetration into the stud and into the inner girt.
3. That §6's reading is right: that a wood-to-wood screw with continuous lateral support
   between framing members is an R301.1.3 engineered connection and not an R703.15
   through-foam furring attachment.
4. Whether anything in §9 needs to become a specification line rather than a note.
