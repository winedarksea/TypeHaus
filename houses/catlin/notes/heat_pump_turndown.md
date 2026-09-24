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
**What is asked of the reviewer:** **nothing is blocked; §7 records what the owner decided
on 2026-09-18 and what stays open.** Two of the three systems exceed Manual S's
minimum-compressor cap, all three are over-sized on cooling by 2.7× to 39×, and the one
that passes the cap still cycles above 27 °F. **All of it is reported as ADVISORY, not as a
FAIL** — see §7 — so none of it gates a build or a permit set.

> ⚠ **`mep.heating_capacity` PASSES ALL THREE**, with margins of +6,743, +17,222 and
> +7,531 Btu/h. It is not wrong; it is answering a different question. A heat pump that
> cannot make enough heat on the coldest night is a house that gets cold once a year. A heat
> pump that cannot turn down to the load is a house that short-cycles for seven months, and
> that is the subject of this note.

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
| HP1 upstairs + attic | 180.76 | **0** | 15,365 | 11,750 | 9,580 | **4,158** |
| HP2 basement + main | 144.37 | **2,392** | 14,664 | 11,776 | 10,044 | **5,713** |
| HP3 mudroom + mech + closet | 12.27 | 0 | 1,043 | 797 | 650 | **282** |

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
near enough for a 1,043 Btu/h zone.

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
| HP1 | 14,000 @ **5 °F** | 15,365 | **0.91** | 12,292 Btu/h | **advisory** |
| HP2 | 8,800 @ **5 °F** | 14,664 | **0.60** | 11,731 Btu/h | pass |
| HP3 | 2,800 @ **17 °F** | 1,043 | **2.69** | 834 Btu/h | **advisory** |

**None of the three binds at the design row**, which is the whole argument for the table
over a scalar. A check reading only −15 °F would report HP1's minimum as 13,556 Btu/h
(interpolated between the −22 and 5 rows) for a factor of 0.88 — still a FAIL, but 3%
understated and pointing at a temperature the unit spends 150 hours a year at instead of the
one it will actually be asked to idle through.

**HP2 passes, and it is not comfortable.** 0.60 is well inside the cap. §4 is why that is
not the end of the story.

## 4. The crossover temperature — reported on a PASS too

The sentence an owner can act on. "It modulates down to the load only below −6.1 °F" is a
fact about this building's year; "minimum sizing factor 0.91" is one nobody can act on.

Solved on the first sign flip of `minimum(T) − load(T)` across the rows that state a
minimum. For HP1:

| odb | minimum | load | difference |
|---|---|---|---|
| −22 °F | 13,400 | 16,630 | **−3,230** |
| 5 °F | 14,000 | 11,750 | **+2,250** |
| 17 °F | 7,100 | 9,580 | −2,480 |
| 47 °F | 10,800 | 4,158 | +6,642 |

The first flip is between −22 and 5:

```
T = −22 + 27 × 3,230 / (3,230 + 2,250) = −22 + 27 × 0.5894 = −22 + 15.9 = −6.1 °F
```

**HP1 modulates continuously only below −6.1 °F.** In Minneapolis that is on the order of
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
| HP1 | 8,982 Btu/h | 24,000 | **2.67** |
| HP2 | 5,322 | 28,400 | **5.34** |
| HP3 | 231 | 9,100 | **39.5** |

**The load is an upper bound, so the ratio is a LOWER one.** The cooling side now carries
the roof's sol-air term (the owner stated the panel colour on 2026-09-18) but still only
occupant latent, so the true loads are higher and the true ratios lower than these. Even
so: 39× is not a rounding question, and an over-sized compressor does not merely waste
money. It short-cycles, never reaches the steady-state coil condition its latent rating was
measured at, and leaves a house **cold and damp** — which in a Minnesota August is the
failure mode people describe as "the AC runs but it feels clammy".

## 6. What would actually fix it — NOT authored, and each one costs something else

**HP3 is the clearest and the cheapest to fix, and no product solves it.** A 932 Btu/h
heating zone and a 202 Btu/h cooling zone do not want a 9,000 Btu/h heat pump; they want no
heat pump. Searched against NEEP's whole cold-climate listing: the smallest ENERGY STAR
cold-climate unit published anywhere has a minimum near 2,000 Btu/h, which is still 2.4×
this zone's 834 Btu/h cap. **There is nothing to buy.** §7 records that it stays anyway,
and the one fact that argues for keeping it. The two rooms are
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
The zone wants **15,365 Btu/h of heat at −15 °F and 8,889 Btu/h of sensible cooling** — a
1.7 : 1 ratio — and the two rules pull opposite ways: the heating side wants a big machine,
the cooling cap (1.30) wants one rated no higher than 11,556 Btu/h (11,265 on the 8,665
Btu/h load of 2026-09-18, which the search below used).

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
  "minimum at any published temperature under 12,292 Btu/h".
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
selector shops in: *"find a unit whose minimum at 47 °F is under 12,292 Btu/h and whose
cooling is under 11,556."*

## 7. What the owner decided, 2026-09-18

**Everything here is an ADVISORY, not a FAIL.** Both `mep.heat_pump_turndown` and the
over-size branch of `mep.cooling_capacity` return PASS with the message led by
`ADVISORY —`. The reasoning is the owner's and it is about what a verdict is for: *"an
oversize unit is not ideal, but it is hardly a reason to fail an entire house — a permit
department doesn't care about an oversized unit."* Short-cycling costs efficiency, comfort
and compressor life; it is not a defect anybody grades at plan review, and calling a whole
house failing over it makes the 0-FAIL gate mean less rather than more. The arithmetic is
reported in full either way. **Under-size still FAILs**, and so does a compressor lockout
warmer than the site design temperature — those are houses that do not work.

**System 3 stays, for now.** *"We may keep it for now. We may remove it later."* Two
changes went in with that decision:

- **`RM-M-MUD-CLOSET` joined its zone.** It was one of three conditioned rooms no equipment
  claimed. It opens off the mudroom, shares its air, and is on the wrong side of the house
  for System 2's heads. The zone's design load goes 932 → 1,043 Btu/h and the sizing factor
  3.00 → 2.69. (`RM-B-ESS` and `RM-M-PANTRY` joined System 2 later; see the 2026-09-24
  addendum.)
- **The modelled load for this zone is an under-count, and the reason is the front door.**
  `estimate_block_load` apportions the house's blower-door infiltration by *conditioned
  volume share* — a whole-house average. These rooms are the entry vestibule: on a moving
  day, a delivery afternoon, or any evening with people coming and going, the air changes
  here are several times the house average and the real load is correspondingly higher than
  1,043 Btu/h. **Nothing in the engine can see a door being held open** — there is no
  occupancy or door-use input anywhere — so it is recorded rather than modelled. It is also
  the one argument that cuts *against* §6's case for deleting System 3: the zone this unit
  is over-sized for is measured on a day nobody is using the front door.

**System 1 keeps its cooling over-size.** *"It's perfectly fine that it is oversized for
summer; it's unlikely we can find a unit that is perfectly balanced for both winter and
summer needs."* §6's search bears that out — NEEP returns zero products meeting both caps —
so the ratio (2.67 then, 2.70 at 2026-09-23) stands as a recorded decision rather than an open item.

**The air handler was challenged and checked.** The concern was that Gree shows the FLEXX
Ultra paired with a floor-standing upflow air handler rather than the low-profile ceiling
unit modelled here. **It is a multi-position air handler and horizontal ceiling mounting is
a factory configuration** — the January 2026 submittal's clearances page states "Horizontal
Left Configuration – No Modification Needed" — so the 18 1/8" cabinet height and
`SF-S-HP1`'s 21" drop are right. Two things came out of that check and are recorded in
`plan/equipment_types.py` and `houses/catlin/CLAUDE.md`, neither modelled and neither
graded: **a secondary drain pan is required** under equipment over a finished ceiling
(manufacturer and IRC M1411.3 / IMC 307.2.3), eating 1 1/2"–2" of the drop's remaining
slack; and **horizontal RIGHT requires relocating the factory drain pan**, so which hand
`rotation=deg(90)` lands on belongs on the purchase order.

**The roof's sol-air term is now live.** The owner confirmed the roof is the same Linen
White as the walls on a different profile — 24 ga PVDF standing seam, SR 0.73, so
`solar_absorptance` 0.27. `solar_gain_basis.md` §6 is closed and the roof adds 329 Btu/h of
cooling load.

## 8. What is still open

- **System 1's turndown**, at 0.91 against the 0.80 cap. The constraint to shop against, if
  it is ever revisited: *a unit whose minimum at any published temperature is under 12,292
  Btu/h*, with the soffit-depth consequence in §6.
- **System 3's existence.** Kept for now, explicitly reversible.

## 9. What is NOT graded here


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

## Addendum 2026-09-22 — System 2 after the court narrowed

HP2's zone lost 17.0 sf of framed walkout (W-B-S2-FR/-S3-FR, −28.5 Btu/h) and gained 12.2 sf
buried and 2.6 sf above-grade concrete (W-B-S1/-S4, +32.6 Btu/h): design load **14,668 Btu/h**
(was 14,664), ground-coupled **2,412** (was 2,392), crossover **27.1 °F** (was 27.0). Sizing
factor unchanged at 0.60; no verdict moves. The figures above are the pre-narrowing ones.

## Addendum 2026-09-23 — System 1 after WIN-A-S2/-S3 went WT-1436 → WT-1424

c3c46cff: −2.33 sf of glass (U 0.25) became wall (U 0.0228), ΔUA = −0.583 + 0.053 = −0.53,
so HP1's air UA 181.30 → 180.76 and its design load 15,410 → **15,365** (−0.53 × 85 = −45).
§§1, 3, 4, 6 and 8 above carry the new HP1 figures; the Manual S cap is 0.80 × 15,365 =
**12,292**, the crossover **−6.1 °F** (was −5.9). The NEEP search in §6 is the 2026-09-18 one
and stands. The sensible cooling 8,665 → 8,889 is drift since 2026-09-18, not this change
(less glass can only lower it).

## Addendum 2026-09-24 — System 2 claims the pantry and the ESS closet

Every conditioned room is now in a zone. `RM-M-PANTRY` joined `EQ-M-HP2-LIVING` and
`RM-B-ESS` joined `EQ-B-HP2-GYM`, both for their load only: neither gets a register, and
the ESS closet is a sealed Type X box that should never get a supply boot. HP2's design
load goes 14,668 → 14,793 (pantry) → **14,877 Btu/h** (ESS), and ground-coupled goes 2,412 →
**2,441** (the closet's slab). The sizing factor goes 0.60 → **0.59**, and the crossover goes
27.1 → **28.0 °F**. No verdict moves.

System 1 moves too, the same day. `PLANT_EXT_2X6_HUMID` gained 5/8" of gypsum behind the
membrane (R316.4), which adds R to `W-S-S1`/`W-S-W4`. HP1's design load goes 15,365 →
**15,359 Btu/h**, so the Manual S cap is 0.80 × 15,359 = **12,287 Btu/h**. The sizing factor
stays 0.91 and the crossover stays −6.1 °F.
