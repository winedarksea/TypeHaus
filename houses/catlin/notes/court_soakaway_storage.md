# Court soakaway course vs the design snowmelt — hand-worked basis

**House:** catlin
**Structure:** the 12" soakaway course under `FB-SG-W2`, `FB-SG-E2`, `FB-SG-S` and `FB-SG-ARCH`
(one body of stone with `FB-SG-W1`/`E1`), fed by `AD-SG-COURT`, `FD-SG-FIELD` and the pipeless
W1/E1 beds through continuous stone (§7), relieving at its lip to `FD-SG-OVERFLOW`.
**Written:** 2026-09-22, by hand from the bed outlines, before the check was run on catlin.
**Oracle for:** `checks/mep/soakaway_storage.py`, reported by `drainage.soakaway_storage`;
reproduced by `tests/test_catlin_court_drainage.py` (the engine's own synthetic case is
`tests/test_soakaway_storage.py`).
**Companions:** `notes/sunken_garden_court_free_body.md` — the court's structure, the chloride
argument and the retired well; `notes/rain_garden_sizing.md` — where the sump's pumped water
goes.
**What is asked of the reviewer:** check §1's lap arithmetic and whether §3's 48 h infiltration
credit is reasonable for a slow melt on presumed HSG D till.

> ⚠ The infiltration rate is PRESUMED (MPCA HSG D, 0.06 in/hr), like the soil class. It is 38%
> of the storage. Without it the course holds 155 cf against 222 cf and FAILS; the fallback
> is an 18" course (233 cf of voids alone). A soils report closes this.

> ⚠ The court's relief lip, -127 7/16", sits 36" INSIDE the 42" drained frost section: that
> section floods before relief. It cannot go lower by gravity. Reported as an UNKNOWN (§5).

---

## 1. The course in plan

Outlines from the resolved beds (ft; x east, y north). Every bed's course is 12" deep, from
the drained bottom -163 7/16" to -175 7/16".

| bed | working | sf |
|---|---|---|
| FB-SG-W2 | x 5.500..12.500 = 7.000 × y -27.333..-11.000 = 16.333 | 114.33 |
| FB-SG-E2 | x 23.500..30.500 = 7.000 × 16.333 | 114.33 |
| FB-SG-S | x 9.000..27.000 = 18.000 × y -30.833..-22.500 = 8.333 | 150.00 |
| FB-SG-ARCH | x 9.000..27.000 = 18.000 × y -12.500..-9.500 = 3.000 (36" bed) | 54.00 |
| sum | | 432.67 |
| W2 ∩ S, E2 ∩ S | 2 × (x 9.0..12.5 = 3.5 × y -27.333..-22.5 = 4.833) = 2 × 16.917 | −33.83 |
| W2 ∩ ARCH, E2 ∩ ARCH | 2 × (3.5 × y -12.5..-11.0 = 1.5) = 2 × 5.25 | −10.50 |
| **course bottom (union)** | | **388.33** |

S and ARCH do not meet. Laps are counted once: the stone in a corner is one stone.

## 2. The demand

| term | working | value |
|---|---|---|
| ground snow | `Site.ground_snow_load_psf` | 50 psf |
| as water | 50 / 62.4 pcf | 0.8013 ft |
| catchment | `AD-SG-COURT.catchment`: x 9.5..26.5 = 17.000 × y -26.833..-10.500 = 16.333 | 277.67 sf |
| **melt** | 0.8013 × 277.67 | **222.5 cf** |

The catchment is the open court south of the balcony's front edge. The balcony roofs the
rest. The field is inside the catchment: frozen, it sheds to the grate like the rim.

## 3. The storage

| term | working | value |
|---|---|---|
| voids | 388.33 sf × 1.0 ft × 0.40 (#57 washed) | 155.3 cf |
| infiltration | 0.06 in/hr × 48 h = 2.88 in = 0.240 ft; × 388.33 sf | 93.2 cf |
| **held** | 155.3 + 93.2 | **248.5 cf** |

48 h is the MN Stormwater Manual's drawdown window, used here as a slow-melt credit. A melt
arrives over days, not in an hour. A storm gets no such credit and is not what this grades.

## 4. The comparison

248.5 cf held ≥ 222.5 cf of melt: **PASS at 1.12**. What governs is the infiltration credit:
remove it and the course alone is 0.70 of the demand.

The check prints "155 cf of voids (388 sf) + 93 cf infiltrated over 48 h (presumed rate) =
249 cf, against 222 cf of melt (50 psf over 278 sf of catchment via AD-SG-COURT)".

## 5. The lip

`FB-SG-W1.overflow_invert` = court top -109 7/16" − 18" field = **-127 7/16"** (on
`FB-SG-ARCH` until 2026-09-23, when the overflow moved to W1's west heel). The drained
section's bottom, the lowest `z0` in the body, is -163 7/16". The lip is 36" above it, so the
drained frost section fills before the water goes to `FD-SG-OVERFLOW` → `SM-B-RADON`.
Reported as UNKNOWN: "sits 36" above the drained section's bottom".

## 6. What is NOT graded here

Rain (the 1.7x ponding ratio covers it, `CLAUDE.md`). The wall-face inflow through the
dimpleboard. The melt rate against the 4" riser's capacity. Ice in the basin. The sump's pumped
volume. A frozen upper course. The water table, which nobody has measured.

## 7. The pipeless lateral, W1 → W2 (design basis; no check reads it)

No court bed runs a pipe since 2026-09-23. `FB-SG-W1`/`E1` have no course of their own, so
their water leaves sideways through 42" of #57 into the bed they abut (`discharge_ref`).
The engine grades only that the stone is continuous (`drainage.tile_lead`,
`drainage_network.drainage_evidence`), never the rate; this section is the rate.

| term | working | value |
|---|---|---|
| bed | `FB-SG-W1`: x 5.500..12.500 = 7.000 wide; y -11.000..-0.557 = 10.443 long | B 7.0 ft, L 10.44 ft |
| k | FHWA's floor for an "excellent" drainable base, 1,000 ft/day (below) | 1,000 ft/day |
| capacity | Dupuit, Q = k·B·(h1² − h2²)/2L, h1 = 6" at the house end, h2 = 0 where it drops into W2's course: 1000 × 7.0 × 0.25 / 20.89 | 84 cf/day = 3.5 cf/h |
| inflow bound | the whole 50 psf melt over a 10'-wide strip behind W1, 10.0 × 10.44 = 104.4 sf: 0.8013 × 104.4 over 48 h | 83.7 cf = 1.74 cf/h |
| mound | h1 = √(2·L·q/(k·B)) at that inflow; at k/10 | 4.2"; 13.4" |

Capacity is ~2.0x the bound at a 6" mound, and even a tenfold-slower stone mounds
13" of a 42" section. Infiltration through W1's own floor is ignored. The court's
own melt does not cross W1: it arrives in `FB-SG-ARCH` (§2).

**k is deliberately low.** 1,000 ft/day is FHWA's (1992) threshold for an "excellent"
drainage material, quoted in MnDOT NRRA202107 §2; the same review cites Cedergren (1994) at
10,000-100,000 ft/day for open-graded 1/2"-1" aggregate, which is what washed #57 is.

## Sources

- MPCA, Minnesota Stormwater Manual — design infiltration rates by HSG (D: 0.06 in/hr);
  48 h drawdown.
- ASCE 7-16 §7.2 / MN Rules 1303.1700 — ground snow load, 50 psf for this parcel (`plan/site.py`).
- ASTM C33 #57 — open-graded washed stone; ~0.40 voids is the common design figure.
- Oh, Likos & Edil, *Drainability of Base Aggregate and Sand*, MnDOT NRRA202107 (Aug 2021),
  §2: FHWA (1992) 0.353 cm/s = 1,000 ft/day for "excellent"; Cedergren (1994) 10,000-100,000
  ft/day for open-graded 1.27-2.54 cm aggregate.
  https://www.mndot.gov/research/reports/2021/NRRA202107.pdf
