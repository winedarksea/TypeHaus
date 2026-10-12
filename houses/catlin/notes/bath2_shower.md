# RM-M-BATH2's shower — thermostatic, one outlet, glass short of the ceiling

**House:** catlin
**Structure:** `FX-M-BATH2-SH` (`FX-SHOWER-36-THERMO-COMBO`), `WP-M-BATH2-SURR`, `REG-M-EXH2`,
`DU-M-ERV-R-BATH2`, `EQ-B-WH`.
**Written:** 2026-10-12, by hand, against `out/model.json` after the change.
**Oracle for:** nothing. This is a **decision record**. No engine module computes hot-water
duration or steam, and none is proposed. It follows `notes/TEMPLATE.md`'s shape so the
arithmetic can be redone line by line.
**Companions:** `notes/dwhr_decision.md` (§10 re-reads the DWHR "no" at 1.75 gpm);
`notes/interior_selections.md` (the ASSE 1016 argument every shower valve here rests on).
**What is asked of the reviewer:** §2's three assumptions (setpoint, usable fraction, mains
temperature). Disagree with one and redo the table.

> ⚠ **The grille is outside the enclosure on purpose, and the front glass's open top is the
> steam path.** Do not glass the front to the ceiling, add a transom, or move `REG-M-EXH2`
> back by the tub without re-reading §4. The ERV has no headroom to boost, so position is
> the only lever.

---

## 1. What changed, and why thermostatic

| Item | Before (2026-09-06) | After (2026-10-12) |
|---|---|---|
| Valve | R10000-UNBX rough, pressure-balance trim | **same rough**, Delta TempAssure 17T thermostatic trim |
| Outlets | fixed head + slide-bar handshower: diverter rough, second riser | **one**: Moen Attract Magnetix 26008 rain/handheld combo |
| Head flow | Speakman S-2005-H, 2.5 gpm | 1.75 gpm |
| Walls | marble-look panel to 7'-0" | solid-surface panel floor to ceiling (106"), 53.0 SF net |
| Base | kit pan | matching 36x36 solid-surface base |
| Glass | unspecified | tub (north) side floor to ceiling; front (west) fixed panel + door to 90" |
| Exhaust | `REG-M-EXH2` at (4'-0", 18'-0"), by the tub | (4'-2", 15'-4"), ~8" west of the front glass |

**The thermostatic argument is about the tank, not about the outlet count.** A
pressure-balance valve holds the hot-to-cold *ratio*. When the 80-gal heat-pump tank's outlet
starts to fall late in a long shower, the mixed water falls with it, at about 0.8 °F per °F
(the hot fraction in §2). A thermostatic valve re-mixes: it opens the hot side to hold the set
temperature until the outlet itself reaches the set point. It also gives a separate volume
control. The 2026-09-06 argument against thermostatic, that the element drifts and a PB spool
is nearly inert, still holds for the other four showers. It is outweighed here, in the one
shower used daily and long. The R10000 rough was chosen so this choice could be made from
outside the tile, and this is that choice.

## 2. How long one tank lasts at 1.75 gpm

Assumptions:

| # | term | value | why |
|---|---|---|---|
| B1 | tank setpoint | **120 °F** | the usual heat-pump setpoint; none is authored on `EQ-T-WATER-HEATER` |
| B2 | usable fraction before the outlet falls off | **0.70** × 80 gal = **56 gal** | the common stratified-tank figure; first-hour ratings imply about this |
| B3 | mixed temperature at the head | **105 °F** | |
| B4 | cold main | **50 °F** annual, **40 °F** February | as `dwhr_decision.md` A3 |

No credit is taken for recovery during the draw. Heat-pump-only recovery is about 7 gph at a
70 °F rise (~4,000 Btu/h), worth roughly 3 more minutes.

| term | working | 50 °F main | 40 °F main |
|---|---|---|---|
| hot fraction | (105 − Tc) / (120 − Tc) | 55/70 = **0.786** | 65/80 = **0.813** |
| hot draw | 1.75 × fraction | 1.375 gpm | 1.422 gpm |
| **minutes at 105 °F** | 56 / hot draw | **40.7 min** | **39.4 min** |

**About 40 minutes of one shower, summer or winter.** No tank, setpoint or mixing-valve change
is needed. Two back-to-back 15-minute showers draw 2 × 15 × 1.42 = 43 gal, inside the 56.

Past that point, the two valves behave differently. At an outlet of 110 °F with a 40 °F main,
a PB valve still set for 120 °F delivers 40 + 0.813 × 70 = **96.9 °F**. The 17T holds 105 °F
until the outlet itself is at about 105. That tail is the whole reason for the swap.

## 3. Glass heights

`RM-M-BATH2.clear_height_m` = 2.6924 m = **106"**.

| side | what | height | open above |
|---|---|---|---|
| north (tub) | fixed panel on the `W-M-TUBDK-S` knee wall | to the ceiling | none: water and steam stay off the tub deck |
| west (front) | fixed panel + door | **90"** (7'-6") | **16"** |
| east, south | solid-surface panels (`WP-M-BATH2-SURR`) | 106" | none |

There is no glass element in the engine, so the heights live in the type's `source` and in
the `FX-SHOWER-36-THERMO-COMBO` price row, as on `FX-SHOWER-36-NEO-COMBO`.

## 4. Steam path and the grille

The Broan B210E75RT delivers ~206.6 cfm against the 205 cfm the code requires
(`mep.erv_static_budget`; `notes/erv_static_budget.md`). There is no headroom to boost
BATH2's 20 cfm, so the grille's position is the only lever.

- Warm, wet air rises and leaves the enclosure through the front's 16" open top.
- `REG-M-EXH2` now sits at **(4'-2", 15'-4")**. The front glass is at x = 4'-10 5/8", so the
  grille is **8 5/8" outside it**, right where the plume comes over. Before, it was ~4' away by
  the tub.
- It stays **outside** the enclosure and **always on**. A grille inside a glassed stall needs
  a wet-rated, listed-for-shower terminal, and the stall would still need make-up air.
- It is clear of `ED-M-BATH2-CAN1` at (2'-6", 16'-0"), 1'-8" west of it.
- `DU-M-ERV-R-BATH2` leaves the x = 3'-10 1/2" extract trunk in the **15'-4" bay**. FS-S-WEST's
  bay centres are 8" + n × 16", and this is the next bay north of BED2's 14'-0". It is a pure
  bay leg at `_BAY_Z`, crossing no truss. `haus route --run DU-M-ERV-R-BATH2 --evaluate`
  proposed the same lane, stopping 1 1/2" short of the grille's centre.
- After the move, `haus check` is unchanged: 0 FAIL and the same 69 UNKNOWN.
  `mep.ventilation_distribution` still passes for RM-M-BATH2.

## 5. What is NOT decided here

- **Drain-water heat recovery**: still no. See `dwhr_decision.md` §10.
- **A boost fan, a transom, or steam features**: not done.
- **The studio bath and sauna showers, and the two tub-showers' valves and walls**: unchanged.
  The tub-showers get only the 52535-SS head.
- **A flow-rate field**: none. Nothing in the engine would read it. 1.75 gpm lives on the
  product records in `plan/products_showering.py`.

### Open confirms (before the plumber orders)

1. **26008 finish.** Only chrome (26008) and Spot Resist Brushed Nickel (26008SRN) were found,
   with no stainless. Brushed nickel beside Delta Lumicoat stainless in one room is the mix
   this house rules out, so the head and the 17T go **chrome** together. The room's
   `FX-M-BATH2-TUB` filler is T2759-**SS**, so either accept chrome beside it, or take the
   filler in chrome too.
2. **17T SKU.** No Ashlyn-handle 17T number was found. T17264 is the Monitor 17
   *pressure-balance* trim and is not this. Confirm a 17T in chrome that fits the R10000
   before ordering.
3. **Solid-surface brand**, and that its 36x36 base's drain matches `FX-M-BATH2-SH`'s
   `drain_position`.

## Sources

- Moen 26008 product page and spec sheet: 1.75 gpm at 80 psi for units made after 3/1/2018
  (2.0 before); finishes 26008 (chrome), 26008SRN. Read 2026-10-12.
  https://www.moen.com/products/Attract/Attract-Chrome-Magnetix-Rainshower-Combo/26008
- Moen 26010SRN product page: 1.75 gpm max. Read 2026-10-12.
- Delta 52535-SS spec sheet (DSP-B-52535): 1.75 gpm at 80 psi, WaterSense, 1/2"-14 NPT.
- Delta TempAssure 17T Series listings: thermostatic trim for the MultiChoice R10000 body,
  separate volume and temperature controls.
- `houses/catlin/out/model.json`: `rooms` (RM-M-BATH2 clear height), and
  `plan/mep_registers.py`, `plan/mep_erv_l2.py`, `plan/fixture_types_wc.py`.
