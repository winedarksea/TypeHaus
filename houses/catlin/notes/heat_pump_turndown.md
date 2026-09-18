# Can these three heat pumps turn DOWN to their zones?

**House:** catlin
**Structure:** all three heat-pump systems — `EQ-M-HP1-OD` (FLEXX Ultra 24k, upstairs +
attic), `EQ-M-HP2-OD` (Multi Ultra 30k, three heads, basement + main floor), `EQ-M-HP3-OD`
(Sapphire 9k, the mudroom/mech stair zone).
**Written:** 2026-09-18, by hand, after the block-load correction gave the zone loads
something worth sizing against.
**Oracle for:** `checks/mep/hvac_sizing.py` (`mep.heat_pump_turndown`), the load
decomposition in `takeoff/hvac.HvacZone.heating_load_at_outdoor_f`, and `capacity_at`.
Reproduced by `tests/test_heat_pump_turndown.py` and `tests/test_heat_pump_ratings.py`.
**Companions:** `notes/block_load_basis.md` and `notes/solar_gain_basis.md` — the loads
every number here is measured against.
**What is asked of the reviewer:** **a purchase decision on all three systems, and it is
the largest open item in this house.** Two of the three fail Manual S's minimum-compressor
cap (HP3 by 3.7×), all three are over-sized on cooling by 2.8× to 45×, and the one that
passes the cap still cycles above 27 °F. §6 lays out what each would have to be replaced
with and what that costs in other decisions (soffit depth, the backup battery circuit, the
ERV manifold). **Nothing in §6 is authored — this note is the case, not the change.**

> ⚠ **`mep.heating_capacity` PASSES ALL THREE**, with margins of +6,743, +17,222 and
> +7,531 Btu/h. It is not wrong; it is answering a different question. A heat pump that
> cannot make enough heat on the coldest night is a house that gets cold once a year. A heat
> pump that cannot turn down to the load is a house that short-cycles for seven months, and
> that is the defect this note is about.

---

## 1. The load is a curve, and it now costs nothing to evaluate

The turndown question is *"at what outdoor temperature does the unit's minimum output fall
to the zone load"*, and neither side of that is a single number. The load side decomposes
off the report the zone already has — `LoadComponent.heating_delta_f` says which boundary
each component was charged against — so there is no second envelope walk:

```
load(T) = ground_coupled_btuh + air_coupled_ua × (setpoint − T)
```

| zone | air-coupled UA | ground-coupled | at −15 °F | at 5 °F | at 17 °F | at 47 °F |
|---|---|---|---|---|---|---|
| HP1 upstairs + attic | 181.30 | **0** | 15,410 | 11,784 | 9,609 | **4,170** |
| HP2 basement + main | 144.37 | **2,392** | 14,664 | 11,776 | 10,044 | **5,713** |
| HP3 mudroom + mech | 10.96 | 0 | 932 | 713 | 581 | **252** |

HP1's zone is the second storey and the attic, so it has **no** ground-coupled term at all
and its load is pure air. HP2's holds the basement, and its 2,392 Btu/h is the floor the air
term sits on — at the interior setpoint the air ΔT is zero and only the ground remains,
because the soil does not know what the air is doing.

**The invariant that keeps this honest:** `load(design) == heating_load_btu_per_hour`
exactly, to floating-point. The two checks solve against the same arithmetic, so they cannot
disagree about the same zone at the same hour.

## 2. The ratings tables, and where they came from

`ashp.neep.org/api/products/<id>/` — the ccASHP database's own API, read 2026-09-18. **It
is the one public source that publishes a MINIMUM capacity column**, which is the column
this whole note is about and which no manufacturer submittal for any of these three units
states. (The plan that asked for these tables rated the Multi's minimum as the highest risk
of the three — "may not exist publicly". It exists, at all four temperatures.)

**HP1 — FLEXX Ultra 24k**, NEEP 504980, AHRI 215213329, 70 °F return:

| odb | minimum | rated | maximum | COP min | COP max |
|---|---|---|---|---|---|
| −22 °F | **13,400** | — | 18,000 | 1.37 | 1.36 |
| −15 °F | — | 21,000 *(Gree)* | — | — | — |
| 5 °F | **14,000** | 25,000 | 25,000 | 2.55 | 2.00 |
| 17 °F | **7,100** | 20,600 | 21,600 | 2.77 | 2.67 |
| 47 °F | **10,800** | 25,000 | 25,400 | 5.11 | 3.56 |

NEEP's own `turndown_ratio` field says **2.31**, which is 25,000 / 10,800 — the same
minimum this table carries, from the same record.

**HP2 — Multi Ultra 30k**, NEEP 392050, AHRI 215218915: minimum 7,000 @ −22, 8,800 @ 5,
8,800 @ 17, **8,200 @ 47**; turndown ratio 3.29. A multi's minimum is the whole outdoor
unit's, not one head's — three heads share one compressor, so 8,200 Btu/h is the floor the
zone as a whole must absorb however the heads stage.

**HP3 — Sapphire 9k**, NEEP 393164, AHRI 214802444: minimum 2,600 @ −22, 2,600 @ 5,
2,800 @ 17, **2,700 @ 47**; turndown ratio 4.26 — the best of the three, and still nowhere
near enough.

Three notes on the data, each of which the schema exists to hold:

- **Only the −15 °F rows are not NEEP's.** NEEP publishes −22, 5, 17 and 47 and nothing
  between; this site designs at −15. Systems 1 and 2 carry a **manufacturer** row there
  (Gree's Extended Ratings, 21,000 and 23,687) rather than an interpolation of two NEEP
  rows, because a published read at the exact design temperature beats an interpolation of
  two. System 3 takes the interpolation, because its zone is 932 Btu/h and nothing turns
  on it.
- **Where two documents disagree, one row and one basis.** NEEP says the Sapphire makes
  12,000 Btu/h at 17 °F; Gree's submittal says 8,900. The NEEP row is authored and the
  submittal figure is recorded in its `citation` prose. Never blended — an average of two
  published numbers is a number nobody published.
- **The Sapphire's map is not monotone in temperature, and that is real.** 12,000 at 17 °F
  and 11,500 at 5 °F are both *above* the 10,600 rated at 47 °F: capacity rising as it gets
  colder, a boosted low-ambient map where the compressor overspeeds below a threshold. The
  validator deliberately has no monotonicity rule, because one would refuse the machine this
  house bought.

## 3. Manual S §2: the minimum-compressor sizing factor

A modulating heat pump's **minimum** output may be up to **0.80 of the design heating
load**. Above that it cannot settle at the load through most of the season, so it cycles.

Two halves, and they are easy to run together:

* the **denominator is the DESIGN load** — that is what a sizing factor *is*, and using the
  load at whatever temperature the row happens to be would be a stricter rule this engine
  invented;
* the **numerator is the LARGEST published minimum**, and finding it is why the check walks
  the whole table. An inverter's floor moves with outdoor temperature and is rarely highest
  at the design row.

| | largest minimum, and where | design load | **sizing factor** | Manual S cap | verdict |
|---|---|---|---|---|---|
| HP1 | 14,000 @ **5 °F** | 15,410 | **0.91** | 12,328 Btu/h | **FAIL** |
| HP2 | 8,800 @ **5 °F** | 14,664 | **0.60** | 11,731 Btu/h | pass |
| HP3 | 2,800 @ **17 °F** | 932 | **3.00** | 746 Btu/h | **FAIL** |

**None of the three binds at the design row**, which is the whole argument for the table
over a scalar. A check reading only −15 °F would report HP1's minimum as 13,556 Btu/h
(interpolated between the −22 and 5 rows) for a factor of 0.88 — still a FAIL, but 3%
understated and pointing at a temperature the unit spends 150 hours a year at instead of the
one it will actually be asked to idle through.

**HP2 passes, and it is not comfortable.** 0.60 is well inside the cap. §4 is why that is
not the end of the story.

## 4. The crossover temperature — reported on a PASS too

The sentence an owner can act on. "It modulates down to the load only below −5.9 °F" is a
fact about this building's year; "minimum sizing factor 0.91" is one nobody can act on.

Solved on the first sign flip of `minimum(T) − load(T)` across the rows that state a
minimum. For HP1:

| odb | minimum | load | difference |
|---|---|---|---|
| −22 °F | 13,400 | 16,679 | **−3,279** |
| 5 °F | 14,000 | 11,784 | **+2,216** |
| 17 °F | 7,100 | 9,609 | −2,509 |
| 47 °F | 10,800 | 4,170 | +6,630 |

The first flip is between −22 and 5:

```
T = −22 + 27 × 3,279 / (3,279 + 2,216) = −22 + 27 × 0.5967 = −5.9 °F
```

**HP1 modulates continuously only below −5.9 °F.** In Minneapolis that is on the order of
150 hours a year; the other 5,000 heating hours it cycles.

(Note the difference flips *back* negative at 17 °F, because the minimum column dips to
7,100 there. The solve takes the FIRST bracket, which is the conservative reading: the
warmest temperature at which the unit is certainly still cycling is what the owner feels.)

**HP2's crossover is 27.0 °F** — `17 + 30 × 1,244 / (1,244 + 2,487)` — and this is the case
worth dwelling on. **It passes the Manual S cap at 0.60 and cycles above 27 °F anyway**,
because its load falls faster than its floor does: its zone carries 2,392 Btu/h of
ground-coupled load that does not move with the weather, so at 47 °F the load is still
5,713 Btu/h while the compressor's floor is 8,200. A published cap and a physical
description are not the same statement, and the check prints both — on a PASS as well as on
a FAIL — precisely so nobody reads 0.60 as "this one is fine".

**HP3's difference is positive at every published temperature**: its minimum never reaches
its load, and the check says so rather than extrapolating a crossover out of the table.

## 5. Cooling is worse, and it is a different Manual S rule

Manual S caps cooling selection at **1.30** of the design cooling load for a modulating unit
(1.15 for single-stage). Derived from the unit's own ratings table — a row whose minimum and
maximum differ is a unit that modulates — so there is no new authored flag for it to be
wrong in.

| | sensible cooling load | rated | **ratio** |
|---|---|---|---|
| HP1 | 8,665 Btu/h | 24,000 | **2.77** |
| HP2 | 5,322 | 28,400 | **5.34** |
| HP3 | 202 | 9,100 | **45.06** |

**The load is an upper bound, so the ratio is a LOWER one.** The cooling side carries no
roof sol-air term (no `solar_absorptance` is authored — `solar_gain_basis.md` §6) and only
occupant latent, so the true loads are higher and the true ratios lower than these. Even
so: 45× is not a rounding question, and an over-sized compressor does not merely waste
money. It short-cycles, never reaches the steady-state coil condition its latent rating was
measured at, and leaves a house **cold and damp** — which in a Minnesota August is the
failure mode people describe as "the AC runs but it feels clammy".

## 6. What would actually fix it — NOT authored, and each one costs something else

**HP3 is the clearest and the cheapest to fix, and no product solves it.** A 932 Btu/h
heating zone and a 202 Btu/h cooling zone do not want a 9,000 Btu/h heat pump; they want no
heat pump. Searched against NEEP's whole cold-climate listing: the smallest ENERGY STAR
cold-climate unit published anywhere has a minimum near 2,000 Btu/h, which is still 2.7×
this zone's 746 Btu/h cap. **There is nothing to buy.** The two rooms are
a mudroom and a mechanical room. Options, roughly in order:

1. **Delete the system.** Serve `RM-M-MUDROOM` from System 2's branch (it already reaches
   the adjacent rooms) and let the mech room take the ambient. This frees the backup battery
   circuit `EQ-M-HP3-OD` occupies, deletes `SL-M-HP3PAD` and its whole north-pad assembly,
   and removes `REG-M-XFER-MUD`'s reason to exist. **Biggest simplification in the house.**
2. **A small resistance panel or toe-kick heater** in the mudroom, on a thermostat. 932
   Btu/h is 273 W. No compressor, no turndown question, no pad, no refrigerant line.
3. **Keep it and accept the cycling**, which is the do-nothing option and should be a
   decision rather than a default. The unit is on the backup circuit for the VFD soft start,
   and that was a deliberate choice worth re-examining on its own terms.

**HP1 is the hardest, and the reason is a genuine conflict between the two Manual S caps.**
The zone wants **15,410 Btu/h of heat at −15 °F and 8,665 Btu/h of sensible cooling** — a
1.8 : 1 ratio — and the two rules pull opposite ways: the heating side wants a big machine,
the cooling cap (1.30) wants one rated no higher than 11,265 Btu/h.

Searched against NEEP's cold-climate listing on 2026-09-18: filtering for
`cooling_capacity_rated_95 <= 11,265`, a low-temperature cut-out at or below −15 °F, and a
low-temperature capacity of at least 15,410 Btu/h returns **zero products**. Relaxing the
cooling ceiling to 14,000 returns zero. At 18,000 it returns 21, none of them centrally
ducted (the nearest are non-ducted multizones).

**No single unit satisfies both caps for this zone**, which is worth stating plainly rather
than shopping around indefinitely. The real answers are therefore structural:

* **Split the zone.** Two smaller systems each land closer to a unit's floor on both sides.
  Costs a second outdoor unit, a second pad and a second circuit.
* **Accept the cooling over-size and fix only the turndown.** A deeper-turndown unit of the
  same nominal size — the search space to shop, and the constraint to shop against is
  "minimum at any published temperature under 12,328 Btu/h".
* **Accept both**, on the argument that the cooling season here is short. This is the
  do-nothing option and should be a decision rather than a default.

Any of the first two reaches back into `houses/catlin/CLAUDE.md`'s soffit-depth argument: the
FLEXX Ultra's 18 1/8" depth is what drove `SF-S-HP1` from a 17" drop to 21", and a different
cabinet moves that again.

**HP2 passes Manual S and still cycles above 27 °F**, which is a judgement rather than a
defect: the cap says the equipment is legitimately selected and §4 says the owner will hear
it run in bursts for most of the season. A 2-port unit carrying two of the three heads,
plus something small for the third, would lower the floor from 8,200 Btu/h — but it is a
comfort trade, not a compliance one, and it is the one of the three that could reasonably be
left alone.

**None of this is a decision the engine can make**, which is why the checks FAIL rather than
proposing. What the engine now does is state the constraint in the units an equipment
selector shops in: *"find a unit whose minimum at 47 °F is under 12,328 Btu/h and whose
cooling is under 11,265."*

## 7. What is NOT graded here

- **Defrost.** A cold-climate unit spends real time in reverse below freezing and the
  published capacity tables are steady-state. Nothing here carries a defrost penalty.
- **Cycling losses as a number.** The check says a unit short-cycles; it does not estimate
  what that costs in seasonal COP, because doing so honestly needs a bin-hour model and this
  engine has none.
- **Head-level staging on the multi.** HP2's floor is treated as the outdoor unit's, which
  is right for the zone as a whole, but a three-head multi with one head calling behaves
  differently from one with all three, and no model here distinguishes them.
- **The lockout is checked but not the defrost band.** `mep.heating_capacity` FAILs a unit
  whose `min_operating_temp_f` is warmer than the site design temperature. All three of
  these are rated to −22 °F against a −15 °F design, so none trips it.
