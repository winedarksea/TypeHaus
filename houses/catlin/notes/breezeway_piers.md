> Superseded 2026-09-10: all four passage pads/piers are retired. This is the archived
> calculation for the former enclosure; see [north entry structure](north_entry_structure.md).

# Breezeway piers PR-BW-1..4 — hand-worked basis

**House:** catlin, Ramsey County, Minnesota (MN Residential Code 2020, adopting the 2018 IRC).
**Structure:** `PR-BW-1..4`, the four 12" round cast piers under the breezeway posts.
**Written:** 2026-09-03, by hand from the authored geometry, not read out of the engine.
**Oracle for:** `engineering/deck_post.py` and `engineering/pier_basis.py`, reported by
`structural.deck_post_size`; reproduced by `tests/test_pier_calcs.py`, which asserts the
engine reproduces every number below.
**Companions:** `notes/sunken_garden_piers.md` — the same 12" section out of the same
assembly, on belled footings instead of pads.
**What is asked of the reviewer:** §3. The cage and the detailing are complete; the axial
state is declined because the demand is a known under-count, and §3 is the bound that says
why that is not a doubt about the section.

Same shape as `notes/sunken_garden_piers.md` §1–§5, and deliberately so: these are the same
12" round section out of the same assembly (`PIER_CONCRETE_12`), so §4 and §5 are the same
arithmetic with the same answer. Since 2026-09-03 that assembly names a real mix —
`EXPOSED_MIX`, 5,000 psi — instead of the presumptive 3,000 the engine used to
substitute, and §4's capacity below moves with it.

**These four get a richer mix than their exposure needs, and that is deliberate.** A
breezeway pier is not the salt-splash court `EXPOSED_MIX` was written for. But
`PIER_CONCRETE_12` also pours `PT-SG-COL`, which is; the five piers together are 0.82 CY;
and the mix these four used to name — "4,000 psi, class F2" — was not a legal mix at all,
because ACI Table 19.3.2.1 asks 4,500 psi of class F2. One ticket that is right beats two
tickets one of which is wrong, at four fifths of a yard. What is different — and is the whole reason this note exists separately — is §3.

**All four piers are identical.** Same height, same section, same tributary, same cage. Since
2026-09-03 the two garage-end piers no longer stop a course lower to dodge the garage bottom
plate; moving the posts inboard removed the clash the special case existed for.

---

## 1. Geometry

| | |
|---|---|
| Section | 12" round cast concrete, `PIER_CONCRETE_12` |
| Pad top | −5'-4" (grade −2'-10", 42" frost, 12" pad) |
| Pier top | −0'-7 1/4" (`_PIER_TOP`, the floor-beam soffit) |
| **Height h** | 4.729167' = **56.75"** |
| **A_g** | π × 6² = **113.097 in²** |
| r (circle) | d/4 = 3.00" |

**h/d = 56.75 / 12 = 4.73.** ACI 318-19 §2.3 calls a member a PEDESTAL at 3.0 or less;
past that it is a **COLUMN**, and §14.1.5 does not permit a plain concrete column at any
stress. These four therefore need a cage whatever the load is — which is §4.

§14.1.2's exclusion for piers *embedded in ground* does not reach: grade is −2'-10" and the
pier top is −0'-7 1/4", so 2'-2 3/4" of the shaft stands free above the soil.

## 2. The load the model can account for

Two areas: the deck `FS-BW-FLOOR` below, and — since 2026-09-04 — the roof field above.

**RE-WORKED 2026-09-09 FOR THE 4'-6" DECK.** The breezeway went from 4'-0" to 4'-6" E-W so
that `D-G-SERVICE` gets the R311.3 landing it had been missing (`params/breezeway.py::_EW_FT`).
Every plan dimension in this section moved with it; nothing in §1, §4, §5 or §6 did, because
the pier's own section and height are untouched. The 4'-0" figures are kept in the right-hand
column so the two states can be diffed rather than trusted.

| term | working | lb | was (4'-0") |
|---|---|---|---|
| Deck area | (11.0208 − 6.9792) × (40.4167 − 36.8333) = 4.041667 × 3.583333 | 14.4826 ft² | 12.691 |
| `BM-BW-FW` strip × length | 4.041667' joist span × 3.583333' | 14.4826 ft² | 12.691 |
| its share to each of its 2 posts | 14.4826 / 2 | 7.2413 ft² | 6.3455 |
| Tributary, per pier | one beam each, so one share each | **7.2413 ft²** | 6.3455 |
| Deck dead | 7.2413 × 10 psf (IRC R507.1) | 72.41 | 63.46 |
| Deck live | 7.2413 × 40 psf | **289.65** | 253.82 |
| Roof field, framed rectangle | 4.5000' rafter span × 3.5833' beam run | 16.125 ft² | 14.333 |
| Roof field, `GL-BW-ROOF` outline | 4.5' × 4.0' | 18.000 ft² | 16.000 |
| Roof field taken | the LARGER — the rafters oversail the beams 2 3/4" each end | **18.000 ft²** | 16.000 |
| its share, per pier | 18.000 / 2 beams / 2 posts | **4.5000 ft²** | 4.0000 |
| Roof dead | 4.5000 × 10 psf | 45.00 | 40.00 |
| Roof snow | 4.5000 × 50 psf (`Site.ground_snow_load_psf`, flat) | **225.00** | 200.00 |
| 6x6 KDAT post above | (5.5² / 144) × (82.75 / 12) × 35 pcf | 50.70 | 50.70 |
| Pier self weight | (113.097 / 144) × (56.75 / 12) × 150 pcf | 557.14 | 557.14 |
| **D** | 72.41 + 45.00 + 50.70 + 557.14 | **725.26** | 711.30 |
| **L** | 289.65 + 225.00 | **514.65** | 453.82 |
| Service | D + L | 1,239.91 | 1,165.12 |
| **Factored** | 1.2(725.26) + 1.6(514.65) = 870.31 + 823.44 | **1,693.75** | 1,579.67 |

The E-W post-to-post span is `_EW_FT` less half a dressed 6x6 at each end:
4.5 − 2(5.5/24) = **4.041667'** = 4'-0 1/2". The N-S frame run is untouched at 3.583333'
(3'-7"), because the 4'-0 1/2" slot between the two cladding faces did not move. The roof
covering is the only term where the sheet itself grew: `GL-BW-ROOF` is now 4'-6" × 4'-0",
cut from an 8'x4' rather than being an exact half of one.

**Snow, not deck live, on the roof share.** The two areas are kept apart in `_Pier` for
exactly this reason: 50 psf ground snow is larger than IRC Table R301.5's 40 psf occupancy
load, so folding the roof into the deck tributary would grade it at 40 and understate the
pier. No C_e/C_t/C_s reduction is taken — this is a screening load on a pier at d/c 0.006,
and the reductions belong to `checks/structural/snow.py` against a roof slope this flat
field has not got.

**THE TRIBUTARY DOUBLED ON 2026-09-03, AND IT IS DELIBERATELY CONSERVATIVE.** An even split
would be `14.4826 / 4 posts = 3.6207 ft²`, which is the right answer here — this deck *is* a
regular four-post grid and each pier really does carry a quarter of it. The rule that replaced
it weights by each BEAM's own strip, because the even split was badly wrong on the sunken
garden's two decks (see `sunken_garden_piers.md` §2), and it gives every beam the FULL joist
span as its strip. `FS-BW-FLOOR` is a single-bay deck on two beams, so the two strips cover
the same 14.4826 ft² twice and each pier is handed 7.2413 ft² where 3.6207 is the truth.

That is a 2× over-count and it is written down rather than absorbed. It is kept because the
alternative — a per-beam tributary width — would put this engine's post demand out of step
with the line load `engineering/glulam_beam.py` publishes for the same beam, and because on a
pier whose real question is §3 below it changes nothing: `structural.deck_footing_size` sizes
these pads at 1.00 ft² required against 1.78 built (and the widening did not move either
number — 1,239.91 lb service over 1,500 psf is 0.83 ft², still under the 12"-side minimum
that governs), and §4's capacity is 169× the demand.

The 6x6 uses its DRESSED 5.5" section and a conventional 35 pcf for wood, matching
`pier_basis._round_size` and `handed_dead`. Its height 82.75" is `_POST_TOP − _PIER_TOP`.

## 3. How the roof entered the number, and what is still outside it

**Closed 2026-09-04.** Until then this section explained why NO d/c was published: the
breezeway roof is neither a `Roof` nor a `FloorSystem`, so `_deck_tributaries` found no
polygon, `_unmodelled_beams` flagged `BM-BW-RW`/`RE`, and `deck_post` reported the axial
state INCOMPLETE rather than print a ratio against a demand it knew was short.

What closed it is `pier_basis._rafter_fields`, and the point is that **it reads an area
rather than inventing one**. A `Beam` naming two other `Beam`s as its bearing refs is
stating, in the model, that it spans between them; `BM-BW-R1..3` all name `BM-BW-RW` and
`BM-BW-RE`, so those three rafters are a framed field and that pair of beams carries it.
The field's plan extent is then the larger of two numbers the model already holds — the
framed rectangle (4.5' × 3.5833' = 16.125 ft²) and the covering authored over it
(`GL-BW-ROOF`, 4.5' × 4.0' = 18.000 ft²). The covering wins here, and it should: the
rafters oversail each beam by 2 3/4", and that eave is real load on real posts. Taking the
framed rectangle alone would understate every pier by 10.4%.

**What is still outside the number, and why it does not reopen the item.** Three things:

| | working | lb, all four piers |
|---|---|---|
| 3 rafters, 2x6 KDAT × 4'-6" | 3 × 4.5 × ~1.6 lb/ft | 22 |
| 2 roof beams, 2-2x8 × 3.58' | 2 × 3.58 × ~4.3 lb/ft | 31 |
| 6 wedges | 13.5 LF of 2x4 rip | 6 |
| 2 wall sheets, head half only | 2 × 32 ft² × 0.55 × 0.5 | 18 |
| **Self weight of the frame, and the standing sheets' heads** | | **~77**, say **19 per pier** |

The framing's own weight is not in the 10 psf: that figure is a covering allowance, and the
sticks below it are modelled as sticks. The standing 4'-0" × 8'-0" wall sheets hang their
heads on the roof beams through the H channels, and they have no plan area over this field
at all. Together they are **~19 lb per pier**, factored **~23 lb**, against §2's 1,693.75.

That is a 1.3% under-count and it is written down rather than absorbed, because the honest
place for a residual is a note and not a silent margin. It does not reopen the INCOMPLETE
for one reason only: §4's capacity is **285,893 lb**, so the item sits at **d/c ≈ 0.006**
and a 1.3% move on the demand is invisible at three decimal places. *The section is not the
question and never was.* Were this a ratio anywhere near 1.0, the residual would have to be
modelled rather than noted.

**The independent bound, re-worked for the 4'-6" deck and still the check on §2.** Built
the way the pre-closure screening estimate was, from the deck alone plus a hand estimate of
the roof, and never allowed to see `pier_basis`:

- deck, factored: 1.2(72.41 + 50.70 + 557.14) + 1.6(289.65) = 816.30 + 463.44 = **1,279.75**
- roof dead, counted as the covering's ACTUAL 0.55 psf plus the frame residual above:
  4.5 × 0.55 + 19 ≈ 21.5 lb → 1.2(21.5) = **25.8**
- roof snow: 1.6(4.5 × 50) = **360.00**
- bound ≈ 1,279.75 + 25.8 + 360.00 = **~1,665 lb**

§2 computes **1,693.75**, 1.7% higher, and higher is the right side for the same reason it
was before: the bound counts the covering's real 0.55 psf where §2 charges a flat 10 psf of
roof dead. Two arithmetics that were never allowed to see each other agree to within 1.7%.
(At 4'-0" the same pair of methods read ~1,560 and 1,579.67, agreeing to 1.3%.)

## 4. The cage, and why it is the Code's minimum

`vertical_reinforcement='(4) #5 vertical, #3 ties @ 10" o.c.'`

| ACI 318-19 | required | provided | |
|---|---|---|---|
| §10.6.1.1 floor | 0.01 A_g = **1.1310 in²** | (4) #5 = 4 × 0.31 = **1.24 in²** | ρ = 1.096% ✓ |
| §10.6.1.1 ceiling | 0.08 A_g = 9.048 in² | 1.24 in² | ✓ |
| §10.7.3.1(b) | 4 bars in circular ties | 4 | ✓ (six is the SPIRAL case) |
| §25.7.2.1 | #3 tie for #10 and smaller | #3 | ✓ |
| §25.7.2.2 pitch | least of 16d_b = 10.0", 48d_t = 18.0", h = 12.0" → **10.0"** | 10.0" | ✓ |

The only other cage that clears the floor is 6-#4 at 1.20 in² — a nickel less steel and two
more bars to cut, bend and tie. Do not thin this to "save concrete": the 1% floor is a creep,
shrinkage and accidental-moment rule and is indifferent to §3's load question entirely.

**Axial capacity, for the record even though no d/c is published:**
φ α P_o = 0.65 × 0.80 × [0.85 × 5,000 × (113.097 − 1.24) + 60,000 × 1.24]
= 0.52 × [475,392 + 74,400] = **285,893 lb**.

(It was 187,011 lb while `PIER_CONCRETE_12` named no mix and the engine substituted IRC
Table R402.2's presumptive 3,000 psi. Nothing about the pier changed; what changed is that
the model can now say what is in it. §3's bound was a factor of 140 clear of the old number
and is a factor of 216 clear of this one, so the conclusion is untouched either way.)

## 5. Slenderness and minimum eccentricity

| | working | |
|---|---|---|
| k | 1.0, non-sway (leaning-column assumption — see below) | |
| k·l_u / r | 1.0 × 56.75 / 3.00 | **18.92** |
| §6.2.5 non-sway floor | 34 − 12(M1/M2) ≥ 22, taken at **22** | 18.92 < 22 → **neglectable** |
| δ_ns | computed anyway | **1.0005** |
| e_min, §6.6.4.5.4 | 0.6 + 0.03(12) = 0.96", × δ_ns | **0.9604"** |
| cap, R22.4.2 | 0.10 h | **1.20"** → ratio 0.800 ✓ |

**k = 1.0 rests on the same leaning-column assumption the balcony's does.** These four posts
carry no brace; `structural.lateral_racking` gives the frame's storey shear to something that
collects it, and reports that claim UNKNOWN. If it fails, k = 2.0 and the threshold drops to
§6.2.5's sway value — at k·l_u/r = 37.8 slenderness would no longer be neglectable. Nothing
in §3's bound comes close to mattering at that d/c, but the assumption is named rather than
buried.

## 6. What is NOT graded here

No bending from the beams landing eccentrically beyond §6.6.4.5.4's minimum above; no wind or
seismic moment in the shaft; no development, splice or cover detail; and **no bearing check on
the pad**. That last is deliberate and is not an omission: `PD-BW-*` is a `Pad`, an IRC Table
R507.3.1 row, and `structural.deck_footing_size` grades it prescriptively (1.78 ft² provided
against 1.00 ft² required, on 1,500 psf soil). `engineering/spread_footing.py` scopes itself
to piers on a `Footing` for exactly that reason — the augered BELL is what the table does not
publish, and these have none.

---

## Sources

Every standard and document this note rests on, collected from the citations above.
Citation style is the house style: issue year on first use (`ASCE 7-16 §29.3`),
section form after. A document is listed here only if a number in this note came
out of it.

- **ACI 318-19** — §2.3
- IRC R507.1, IRC Table R402.2, IRC Table R507.3.1
