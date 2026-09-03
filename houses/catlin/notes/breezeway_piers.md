# Breezeway piers PR-BW-1..4 — hand-worked basis

**Oracle note for `engineering/deck_post.py` and `engineering/pier_basis.py`.** Worked by
hand from the authored geometry, not read out of the engine — a calculation that only agrees
with itself is not verified (`engineering/__init__.py`). `tests/test_pier_calcs.py` asserts
the engine reproduces every number below.

Same shape as `notes/sunken_garden_piers.md` §1–§5, and deliberately so: these are the same
12" round section out of the same assembly (`PIER_CONCRETE_12`), so §4 and §5 are the same
arithmetic with the same answer. Since 2026-09-03 that assembly names a real mix —
`CATLIN_EXPOSED_MIX`, 5,000 psi — instead of the presumptive 3,000 the engine used to
substitute, and §4's capacity below moves with it.

**These four get a richer mix than their exposure needs, and that is deliberate.** A
breezeway pier is not the salt-splash court `CATLIN_EXPOSED_MIX` was written for. But
`PIER_CONCRETE_12` also pours `PT-SG-COL`, which is; the five piers together are 0.82 CY;
and the mix these four used to name — "4,000 psi, class F2" — was not a legal mix at all,
because ACI Table 19.3.2.1 asks 4,500 psi of class F2. One ticket that is right beats two
tickets one of which is wrong, at four fifths of a yard. What is different — and is the whole reason this note exists separately — is §3.

**All four piers are identical.** Same height, same section, same tributary, same cage. Since
2026-09-03 the two garage-end piers no longer stop a course lower to dodge the garage bottom
plate; moving the posts inboard removed the clash the special case existed for.

---

## §1 — Geometry

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

## §2 — The load the model can account for

The deck `FS-BW-FLOOR` is the only load with a plan area anywhere in the model.

| term | working | lb |
|---|---|---|
| Deck area | (9.7708 − 6.2292) × (40.4167 − 36.8333) = 3.541667 × 3.583333 | 12.691 ft² |
| `BM-BW-FW` strip × length | 3.541667' joist span × 3.583333' | 12.691 ft² |
| its share to each of its 2 posts | 12.691 / 2 | 6.3455 ft² |
| Tributary, per pier | one beam each, so one share each | **6.3455 ft²** |
| Deck dead | 6.3455 × 10 psf (IRC R507.1) | 63.46 |
| Deck live | 6.3455 × 40 psf | **253.82** |
| 6x6 KDAT post above | (5.5² / 144) × (82.75 / 12) × 35 pcf | 50.70 |
| Pier self weight | (113.097 / 144) × (56.75 / 12) × 150 pcf | 557.14 |
| **D** | 63.46 + 50.70 + 557.14 | **671.30** |
| **L** | | **253.82** |
| Service | D + L | 925.12 |
| **Factored** | 1.2(671.30) + 1.6(253.82) = 805.56 + 406.11 | **1,211.67** |

**THE TRIBUTARY DOUBLED ON 2026-09-03, AND IT IS DELIBERATELY CONSERVATIVE.** It was
`12.691 / 4 posts = 3.1727 ft²`, an even split, which is the right answer here — this deck
*is* a regular four-post grid and each pier really does carry a quarter of it. The rule that
replaced it weights by each BEAM's own strip, because the even split was badly wrong on the
sunken garden's two decks (see `sunken_garden_piers.md` §2), and it gives every beam the FULL
joist span as its strip. `FS-BW-FLOOR` is a single-bay deck on two beams, so the two strips
cover the same 12.691 ft² twice and each pier is handed 6.3455 ft² where 3.1727 is the truth.

That is a 2× over-count and it is written down rather than absorbed. It is kept because the
alternative — a per-beam tributary width — would put this engine's post demand out of step
with the line load `engineering/glulam_beam.py` publishes for the same beam, and because on a
pier whose real question is §3 below it changes nothing: `structural.deck_footing_size` sizes
these pads at 1.00 ft² required against 1.78 built, and §4's capacity is 235× the demand.

The 6x6 uses its DRESSED 5.5" section and a conventional 35 pcf for wood, matching
`pier_basis._round_size` and `handed_dead`. Its height 82.75" is `_POST_TOP − _PIER_TOP`.

## §3 — What is NOT in that number, and why no d/c is published

`PR-BW-i` also carries `BM-BW-RW` or `BM-BW-RE` through the 6x6 above it, and those two roof
beams carry the whole enclosure: three 2x6 rafters, six drainage wedges, the 4'-0" × 4'-0"
roof sheet, and — through the H channels — the head of each 4'-0" × 8'-0" standing sheet.

**None of it has a plan area in the model.** The breezeway roof is neither a `Roof` nor a
`FloorSystem` (`params/breezeway.py` explains why: `resolve/roof_geometry.py` accepts only
Wall bearing refs, and a FloorSystem is pinned to a storey datum), so it is four `Beam`s and
some sticks. `pier_basis._deck_tributaries` distributes AREAS to posts, and there is no area
here to distribute. So `tributary_ft2 = 6.35` is an **under-count** of the pier's real load
despite being a 2× over-count of its deck share, and
`deck_post._detailing_only` publishes the six load-independent detailing states and reports
the axial one INCOMPLETE rather than printing a d/c against a demand it knows is short.

**A bounding estimate, so nobody reads that INCOMPLETE as "the pier might be too small".**
This is screening arithmetic — assumptions stated, not a design, and deliberately NOT what
the register publishes:

| | working | lb, all four piers |
|---|---|---|
| Roof sheet, 16 mm multiwall | 16 ft² × 0.55 psf | 9 |
| 3 rafters, 2x6 KDAT × 4'-0" | 3 × 4 × ~1.6 lb/ft | 19 |
| 2 roof beams, 2-2x8 × 3.58' | 2 × 3.58 × ~4.3 lb/ft | 31 |
| 6 wedges | 12 LF of 2x4 rip | 5 |
| 2 wall sheets, head half only | 2 × 32 ft² × 0.55 × 0.5 | 18 |
| **Unaccounted dead** | | **~82**, say **21 per pier** |
| Roof snow | `Site.ground_snow_load_psf` 50 × 16 ft² | 800, **200 per pier** |

Factored that is 1.2(21) + 1.6(200) = **345 lb** on top of §2's 1,211.67, so a bounded
factored demand is on the order of **1,560 lb**. Against §4's 285,893 lb capacity that is **d/c ≈
0.005**. *The section is not the question and never was.* What the register declines to do is
turn a bound into a number a reader would take at face value.

The remedy is upstream: give the roof a modelled area to divide, or have the engineer state
the demand. Either closes the INCOMPLETE with nothing in `deck_post.py` changed.

## §4 — The cage, and why it is the Code's minimum

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

## §5 — Slenderness and minimum eccentricity

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

## §6 — What is NOT graded here

No bending from the beams landing eccentrically beyond §6.6.4.5.4's minimum above; no wind or
seismic moment in the shaft; no development, splice or cover detail; and **no bearing check on
the pad**. That last is deliberate and is not an omission: `PD-BW-*` is a `Pad`, an IRC Table
R507.3.1 row, and `structural.deck_footing_size` grades it prescriptively (1.78 ft² provided
against 1.00 ft² required, on 1,500 psf soil). `engineering/spread_footing.py` scopes itself
to piers on a `Footing` for exactly that reason — the augered BELL is what the table does not
publish, and these have none.
