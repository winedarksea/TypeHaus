# Drain water heat recovery — measurement and decision

**House:** catlin
**Structure:** `PR-B-MAIN-DRAIN`, `PR-M-S-BATH1-DRAIN`, `PR-M-S-SUITE-DRAIN`,
`PR-A-STUBATH-DRAIN`, the five shower waste branches, and `EQ-B-WH`.
**Written:** 2026-09-19, by hand, against `out/model.json` at contentHash-of-record.
**Oracle for:** nothing. This is a **decision record**, not a calculation oracle — no engine
module computes DWHR and none is proposed. It follows `notes/TEMPLATE.md`'s shape because the
arithmetic still has to be redoable line by line.
**What is asked of the reviewer:** §5's four assumptions are the whole argument — occupancy,
shower length, cold-main temperature, and the HPWH's in-situ COP. Disagree with one and redo
§6. Nothing else in the note is a judgement.

> ⚠ **The answer is no, and it is not because the house has nowhere to put one.** It has an
> excellent place: 80 3/8" of clear, accessible, above-slab 4" vertical stack carrying four of
> the five showers, with the cold trunk 1'-10" away. The unit does not pay because `EQ-B-WH`
> is a heat pump and already divides the recoverable heat by ~3. **Revisit this note if the
> HPWH is ever replaced by a resistance tank** (§8) — the stack is not consumed by the
> decision and the retrofit stays available for the life of the building.

---

## 1. Every shower, and the vertical drain directly below it

Project z, inches, main floor = 0. Storey datums: basement −109.438", main 0", second 120",
attic 240". `VERT` is a segment whose plan position does not move.

| Shower | Storey | Its own waste run | Vertical drop before the first turn | Then |
|---|---|---|---|---|
| `FX-S-BATH1-SH` (60" tub-shower) | second | `PR-M-S-BATH1-TUB-DRAIN`, 1 1/2" | **3.00"** (z 120.75 → 117.75) at (3'-3 1/4", 34'-1 1/2") | 4'-1" horizontal south inside the deck |
| `FX-S-SUITEBATH-TUBSH` (60" tub-shower) | second | `PR-M-S-SUITE-TUB-DRAIN`, 1 1/2" | **3.32"** (120.75 → 117.44) at (16'-5 5/8", 21'-9 1/8") | 2'-9" + 5'-2 3/4" horizontal inside the deck |
| `FX-A-STUBATH-SH` (36" neo) | attic | `PR-A-STUBATH-SH-DRAIN`, 2" | **7.00"** (240.75 → 233.75) at (16'-2 5/8", 20'-7 5/8") | 6'-7" horizontal west inside the deck |
| `FX-M-BATH2-SH` (36" diverted) | main | `PR-B-SH2-DRAIN`, 2" | **15.40"** (0.00 → −15.40) at (1'-9", 17'-3") | 45° to the basement collector |
| `FX-B-SAUNA-SH` | basement | `PR-B-SAUNA-DRAIN`, 2" | 10.5", then under-slab | nothing below it — it is the bottom storey |

**What is in the way is the floor deck, and it is 12" deep.** Main's ceiling plane resolves at
z = 108" and second's structure at z = 120": 11 7/8" of I-joist plus subfloor. A 1 1/2" trap arm
that must stay in that deck can fall 3" before it turns, and does. The same holds at the attic
deck. The rooms below are `RM-M-MUDROOM` / `RM-M-MECH` (under BATH1's tub),
`RM-M-LIVING` / `RM-M-STUDY` (under the suite tub) and `RM-S-SUITEBATH` (under the attic
shower) — two of the three are finished living space, so dropping a stack through them to win
vertical is not on offer either.

**Conclusion of §1: a shower-only (greywater) DWHR is geometrically impossible in this house.**
The longest dedicated shower vertical is 15.4", and the three upper-storey showers — the only
ones with anything below them — give 3", 3 1/4" and 7". The smallest unit on the market
(`Power-Pipe R3-36`, 3" × 36") wants 39" between fittings. Nothing here is close.

## 2. The collected stacks, which are long enough

| Stack | Ø | Plan position | Vertical extent (project z) | Length | Where it is |
|---|---|---|---|---|---|
| `PR-M-S-BATH1-DRAIN` | 3" | (5'-0", 26'-6") | 123.0 → −22.0 | **12'-1"** | buried in a main-floor wall between `RM-M-BATH1` and `RM-M-MUD-CLOSET` |
| `PR-M-S-SUITE-DRAIN` | 3" | (13'-0", 16'-10 3/4") | 115.5 → −22.0 | **11'-5 1/2"** | buried in a main-floor wall at `RM-M-CLOSET` |
| `PR-A-STUBATH-DRAIN` | 3" | (9'-7 1/2", 19'-4") | 231.5 → 116.0 | **9'-7 1/2"** | buried in a second-floor wall at `RM-S-SUITEBATH` |
| `PR-B-MAIN-DRAIN` | 4" | (3'-0", 15'-6") | −29.098 → −122.638 | 7'-9 1/2" total, of which **80.34" (6'-8 3/8") is above the slab** | open in `RM-B-WORKSHOP` |

The first three are inside finished, insulated wall cavities. A 3" Power-Pipe is ~4 1/2" over
the fins and would need a chase; more to the point it would be un-serviceable and its cold-side
re-plumb would have to be fished through two storeys. Set them aside.

**`PR-B-MAIN-DRAIN` is the candidate.** Its vertical leg:

| term | working | value |
|---|---|---|
| top of vertical (project) | `elevations` vertex `ft(6, 8.3375)` basement-relative | −29.098" |
| basement slab top | storey `elevation_m` −2.7797125 m | −109.438" |
| clear vertical above slab | 109.438 − 29.098 | **80.34"** |
| basement ceiling plane | −2.7797125 + 2.4622125 m | −12.50" |
| top of pipe below the ceiling | 29.098 − 12.50 | 16.60" |
| under-slab continuation | −109.438 → −122.638 | 13.20" below slab |

Room: `RM-B-WORKSHOP`, occupancy `utility`, 8'-1" clear. Open, serviceable, and the pipe hangs
in the room rather than in a soffit.

**What it carries.** `PR-B-MAIN-DRAIN.serves` lists 17 fixtures including `FX-M-BATH2-SH`,
`FX-S-BATH1-SH` and `FX-S-SUITEBATH-TUBSH`; `FX-A-STUBATH-SH` reaches it via
`PR-A-STUBATH-DRAIN` → `PR-M-S-SUITE-DRAIN`, which lands on the collector at (6'-0", 16'-6").
Every branch joins **at or upstream of (3'-0", 16'-6")**, one foot upstream of the drop — so
the whole 80.34" carries all four upper- and main-storey showers. Only `FX-B-SAUNA-SH` misses
it (`PR-B-SAUNA-DRAIN` goes under-slab independently). It also carries three WCs, which is
permitted — a DWHR is a double-wall drain and is listed for a soil stack — but it means the
unit sees non-shower flow it recovers nothing from.

**Fit.** `Power-Pipe R4-60` requires **63" between fittings**. 80.34 − 63 = **17.34" spare**
for the two couplings and a developing length above. It fits. An R4-72 would not.

## 3. The water heater, and the cold feed

`EQ-B-WH` — Rheem ProTerra 80 gal **hybrid heat pump** (PROPH80 / XE80T10HS45U0 class), 4.5 kW
resistance element, 30A/240V `CKT-WH-240`, in `RM-B-FURNACE` at (5'-6", 24'-0").
Distance from the stack's vertical at (3'-0", 15'-6"): √(30² + 102²) = 106.3" = **8'-10 1/4"**.

The cold feed passes the stack. `PR-B-CW-TRUNK` (1 1/4") runs along y = 16'-0" at z = −8.799",
from x = 4'-9" eastward; its nearest vertex to the stack is (4'-9", 16'-0"), √(21² + 6²) =
**21.8" = 1'-10"** away in plan. `PR-B-CW-WH` (1") leaves that same trunk vertex and runs to
the tank. So an equal-flow hookup — preheated cold to both the tank inlet and the shower cold
branches — is a short re-plumb of `PR-B-CW-TRUNK` at one point, not a house-wide re-route.
**The plumbing is not the obstacle.** (The `PR-B-CW-SBATH` and `PR-B-CW-SUITE` risers likewise
run 7 1/4" from their own drain stacks over 10 ft, at (5'-7 1/4", 26'-6") and (13'-7",
16'-10 3/4") — noted only because it means the buried-stack option would also plumb easily if
the wall were ever open.)

## 4. The product

`Power-Pipe R4-60` (RenewABILITY Energy), 4" × 60".

| term | value | source |
|---|---|---|
| rated effectiveness | **56.4%** | manufacturer product page; CSA B55.1 test, Intertek-verified |
| CSA B55.1 rating flow | 9.5 L/min (2.5 gpm), equal flow | CSA B55.1 method |
| vertical required between fittings | 63" | manufacturer product page |
| unit price | **$1,624 USD** (list, Sept 2026) | manufacturer store |
| moving parts / maintenance | none | manufacturer |

ThermoDrain and EcoDrain publish comparable figures in the same length class; the arithmetic
below does not turn on which brand, and R4-60 is used because its required-length number is
the one that had to be checked against §2.

## 5. Assumptions (the whole argument lives here)

| # | Assumption | Value | Why |
|---|---|---|---|
| A1 | showers per day | **3** | 2–3 person household, taken at its upper bound |
| A2 | shower | 8 min at 2.0 gpm = **16.0 gal** | no showerhead flow is authored on any `FixtureType`; 2.0 gpm is the WaterSense ceiling |
| A3 | cold main | **50 °F** | St Paul annual mean; the seasonal range is roughly 40 °F (Feb) to 62 °F (Aug) |
| A4 | drain temperature at the unit | **95 °F** | 105 °F mixed less ~10 °F to pan, trap and the 12'+ of 3" and 4" pipe between the shower and the basement |
| A5 | HPWH in-situ COP | **3.3** | ProTerra 80 gal rated UEF ~4.0; derated for a 60–65 °F basement and resistance assist on recovery |
| A6 | space-heat make-up | heating-season fraction **0.6**, space heat pump seasonal COP **2.8** | the HPWH takes its heat out of `RM-B-FURNACE`, and for most of a Minnesota year the Gree systems put it back |
| A7 | electricity | **$0.1698/kWh** | Xcel Minnesota residential, Minneapolis, 2026 |

## 6. The arithmetic

**Per shower.**

| term | working | value |
|---|---|---|
| available ΔT | 95 − 50 | 45.0 °F |
| recovered rise on the incoming cold | 0.564 × 45.0 | 25.4 °F |
| mass through the unit | 16.0 gal × 8.33 lb/gal | 133.3 lb |
| heat recovered | 133.3 × 1.0 Btu/lb·°F × 25.4 | **3,386 Btu** |

Equal-flow accounting: the preheated cold splits to the mixing valve and to the tank, so the
recovered heat is a saving on the water-heating load either way. No credit is taken for the
DWHR's small pressure drop or for the fact that one WC flush during a shower dilutes the film.

**Per year.**

| term | working | value |
|---|---|---|
| showers | 3 × 365 | 1,095 |
| water-heating load avoided | 1,095 × 3,386 Btu | 3.71 MBtu = **1,087 kWh delivered** |

**Electricity, and this is where it dies.**

| term | working | value |
|---|---|---|
| HPWH electricity for that load | 1,087 / 3.3 | 329 kWh |
| heat the HPWH would have pulled from the basement | 1,087 × (1 − 1/3.3) | 758 kWh-equivalent |
| space-heat make-up, heating season | 0.6 × 758 / 2.8 | 162 kWh |
| **effective electricity saved** | 329 + 162 | **491 kWh/yr** |
| effective whole-house COP for water heating | 1,087 / 491 | 2.21 |
| **annual saving** | 491 × $0.1698 | **$83/yr** |

**Cost.**

| term | value |
|---|---|
| R4-60 unit | $1,624 |
| plumber, ~5 h: cut 63" out of the 4" PVC, two no-hub couplings, tee `PR-B-CW-TRUNK` 1'-10" away, run cold in/out, re-point `PR-B-CW-WH` and the cold shower branches to the preheated side | $450–800 |
| **installed** | **~$2,300** |

**Rebates.** None found. Xcel Energy Minnesota's residential rebate summary and its water
heater rebate page carry heat-pump water heater rebates ($400–500, plus a $600 insulation/air
sealing bonus) but **no drain water heat recovery line item**; Minnesota's CIP has no
residential DWHR measure I could find; there is no federal 25C credit for DWHR. Assume **$0**.

**Payback.**

    $2,300 / $83 per year  =  27.7 years

## 7. The comparison that governs

The governing term is A5/A6 — the water heater's COP — not the stack, not the price, not the
effectiveness. Redo the same 1,087 kWh/yr against other tanks:

| water heater | effective COP | kWh saved | $/yr | simple payback |
|---|---|---|---|---|
| electric resistance | 1.0 | 1,087 | $185 | **12.5 yr** |
| this house's HPWH, basement-only accounting | 3.3 | 329 | $56 | 41 yr |
| **this house's HPWH, with winter make-up (A6)** | **2.21** | **491** | **$83** | **27.7 yr** |

Even the generous end of the occupancy assumption does not rescue it: four 10-minute showers a
day at 2.5 gpm with a 45 °F main — a five-person household, not this one — gives 2,511 kWh
delivered, 1,136 kWh saved, $193/yr, and a 12-year payback. **At 2–3 people it is 28 years**,
which is longer than the mortgage and about equal to the service life of the fixtures whose
water it would be recovering.

## 8. Decision

**No. Do not install a DWHR unit.** Nothing is authored; no model element changes.

The reasoning, in the order it matters:

1. **A shower-only unit is impossible.** The longest vertical directly under any shower is
   15.4" (`PR-B-SH2-DRAIN`) and the three upper-storey showers give 3", 3 1/4" and 7" — a 12"
   floor deck is the constraint and it is not negotiable. The highest-value DWHR arrangement
   is off the table by geometry alone.
2. **A soil-stack unit is possible and easy, and still does not pay.** `PR-B-MAIN-DRAIN` gives
   80.34" of open above-slab 4" vertical in `RM-B-WORKSHOP` carrying four of five showers,
   with the cold trunk 1'-10" away. An R4-60 fits with 17" to spare. The payback is 28 years.
3. **`EQ-B-WH` already took the saving.** A heat pump water heater divides the recoverable heat
   by its COP. The same unit on the same stack behind a resistance tank pays back in 12.5
   years; the ProTerra makes it 28. Paying twice for the same efficiency is the error this
   note exists to avoid.
4. **No rebate closes the gap.** $0 found. It would take roughly a $1,300 rebate — 80% of the
   unit price — to bring this to a 10-year payback.

**Revisit when, and only when:**

- `EQ-B-WH` is replaced by an electric-resistance tank, or the HPWH is run resistance-only for
  a long stretch (the ESPHome/econet governor in `plan/mep_hvac.py` forces heat-pump-only on
  battery, which is the opposite direction and does not trigger this);
- occupancy rises to five or more, or the shower pattern changes materially;
- the price of an R4-60 installed falls below about $900, or a Minnesota rebate appears.

**The option is preserved at no cost.** Nothing in the design consumes that 80" of stack, and
the cold trunk stays where it is. The retrofit is a half-day job at any future date, in an open
utility room, with no finish disturbed — which is itself the strongest argument for not doing
it now.

## 9. What is NOT decided here

- **Shower flow rates.** No `FixtureType` in this house authors a gpm. A2 is an assumption, not
  a model reading, and §6 would move with it.
- **Cold-main temperature.** A3 is an annual mean. A seasonal calculation would raise the
  winter saving and lower the summer one; it does not move a 28-year payback.
- **The HPWH's real COP.** A5 and A6 are estimates. No energy model in this engine computes
  water heating; `building_science.energy` is an envelope UA calculation and says nothing about
  domestic hot water.
- **Whether to insulate the hot drain.** A separate and much cheaper question, not asked here.
- **The sauna shower.** `FX-B-SAUNA-SH` drains under-slab and is outside every option above.
- **Any code question.** MN ch. 4714 (UPC) permits a listed double-wall DWHR on a drain; since
  nothing is being installed, that reading was not pursued past confirming it is not a barrier.

## Sources

- RenewABILITY Energy Inc. — Power-Pipe R4-60 product page: 56.4% rated efficiency, 63"
  vertical drain between fittings, $1,624 USD (accessed 2026-09-19).
  https://www.renewability.com/products/r4-60
- CSA B55.1 — *Test method for measuring efficiency and pressure loss of drain water heat
  recovery units*; rated effectiveness is measured at 9.5 L/min, equal flow.
- Xcel Energy — *Minnesota 2024–2026 Residential Rebate Summary* (information sheet) and the
  Minnesota residential water heater rebate page: heat pump water heater rebates listed, no
  drain water heat recovery measure (accessed 2026-09-19).
  https://mn.my.xcelenergy.com/s/residential/home-rebates/water-heaters
- Xcel Energy Minnesota residential rate, Minneapolis, 2026: 16.98 ¢/kWh.
- GreenBuildingAdvisor — *Drain-Water Heat Recovery* (green basics) and the HPWH-pairing
  discussion: the standard statement that a preheater saves little behind a high-COP heat pump
  because most of the energy is the final lift above 100 °F.
  https://www.greenbuildingadvisor.com/green-basics/drain-water-heat-recovery
- `houses/catlin/out/model.json` — `plumbing.riser`, `storeys`, `rooms`; and
  `houses/catlin/plan/mep_drainage.py` (`PR-B-MAIN-DRAIN.elevations`),
  `plan/mep_hvac.py` (`EQ-T-WATER-HEATER`, `EQ-B-WH`), `plan/mep_supply.py`
  (`PR-B-CW-TRUNK`, `PR-B-CW-WH`).
