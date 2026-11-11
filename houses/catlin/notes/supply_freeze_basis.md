# Supply pipe in an exterior stud bay — the steady-state freeze walk

**House:** catlin
**Stack:** `EXT_2X6` (W-M-W1, W-M-W3 and every other 2x6 main-storey wall of that type)
**Written:** by hand, before `checks/mep/supply_freeze.py` was compared to it.
**Oracle for:** `checks/mep/supply_freeze.py` / `supply_freeze_walk.py`
(`mep.supply_freeze_exposure`); reproduced by `tests/test_supply_freeze.py`.

> This is a HOUSE advisory, not a code requirement. No code section is cited: none was read
> for this rule. The basis is the arithmetic below.

## 1. The rule

Water freezes at 32 F (0 C). Walk the layers from the room (70 F, `interior_setpoint_f`) to
the design outdoor air (-15 F, `Site.design_temp_heating`, authored in `plan/site.py`),
steady state, and read the temperature on the pipe's OUTBOARD face:

    T = T_in - (T_in - T_out) * R_inboard / R_total        (R in US units, series path)

The pipe is flagged when T is under 32 F + 10 F = **42 F**. The 10 F is a judgement, not a
published number: it stands for what a steady-state walk leaves out (stud and fastener
bridging, convection around the pipe, wind-driven infiltration, a thermostat setback). It is
a constant in `FreezeAdvisory`; change it deliberately. A bay with no continuous insulation
outboard of the pipe is flagged whatever T is.

## 2. Inputs (read from the repo, not independently sourced)

| Item | Value | Where |
|---|---|---|
| Room film | R 1.4196 (RSI 0.25) | `building_science/glaser.py` `INTERIOR_SURFACE_R_US` |
| Outdoor film | R 0.2271 (RSI 0.04) | same, `EXTERIOR_SURFACE_R_US` |
| 1/2" gypsum | 0.9 R/in x 0.5" = 0.450 | library `gwb`/`gwb-ar`/`gwb-mr` |
| Fiberglass batt in the bay | 3.7 R/in | library `fiberglass`, the `CavityFill` of `stud` |
| 1/2" CDX | 1.25 R/in x 0.5" = 0.625 | library `cdx-plywood` |
| 4" ccSPF | 6.5 R/in x 4" = 26.000 | library `closed-cell-spray-foam` |

Cladding, girt and vent gap are outboard of a back-vented rainscreen cavity, so they carry no
R (the same cut `glaser_layers` makes); the outdoor film applies at the foam. Plan stations
from the sheathing plane (x = 0): room face 6.5", gypsum 6.0-6.5", bay 0.5-6.0", CDX 0-0.5",
ccSPF -4 to 0. The framing is not in the path: a pipe is in the bay, so the bay is the fill
alone (`analysis._layer_rsi` parallel-paths the framing in, which is right for a wall U and
wrong for a pipe).

## 3. The `PR-M-BATH2-LAV-CW` case (W-M-W3, same stack as W-M-W1)

1/2" PEX, OD 0.625", centreline at x = 4.000", so the outboard face is at x = 3.6875"
(2.8125" behind the room face).

    R_inboard  = 1.4196 + 0.450 + (6.0 - 3.6875) x 3.7   = 1.4196 + 0.450 + 8.5563 = 10.4258
    R_outboard = (3.6875 - 0.5) x 3.7 + 0.625 + 26.000 + 0.2271
               = 11.7938 + 0.625 + 26.000 + 0.2271       = 38.6459
    R_total    = 49.0717
    T          = 70 - 85 x 10.4258 / 49.0717             = 70 - 18.059 = **51.94 F**

51.94 F is 9.94 F above the 42 F line. Engine: 51.9 F (R 10.4 / 38.6).

## 4. Sensitivity: where in the bay

Same stack, R_total 49.0717 whatever the position; only the split moves.

| Pipe outboard face | R_inboard | T at -15 F |
|---|---|---|
| x = 3.6875" (the lav line) | 10.4258 | 51.94 F |
| x = 0.5", hard on the sheathing | 1.4196 + 0.450 + 5.5 x 3.7 = 22.2196 | **31.51 F** |

A pipe on the sheathing face of this wall is BELOW freezing even with 4" of ccSPF outboard:
the batt carries 41% of the wall's R and the drop across it is what the pipe sees. The 42 F
line is reached at R_inboard = 16.165, i.e. 3.864" of batt inboard of the pipe, a face 4.36"
behind the room face (1.64" in front of the sheathing); 32 F at R_inboard = 21.938, a face
5.92" back (0.58" from the sheathing).

## 5. The no-continuous-insulation case

The same bay with the ccSPF removed (cavity, CDX, cladding only), lav-line position:

    R_outboard = 11.7938 + 0.625 + 0.2271 = 12.6459
    T = 70 - 85 x 10.4258 / (10.4258 + 12.6459)             = **31.59 F**

Flagged on both counts: no continuous insulation outboard, and below freezing.

## 6. Limits

Steady state at the design hour, one-dimensional through the bay path. It does not model
the pipe's own conduction, a jacket (a jacket slows freezing and does not change the
ambient the pipe reaches), a vacant house, or air leaking through the bay. A framed layer
with no `CavityFill` is credited zero R: that warms a pipe whose unfilled layer is inboard
and cools one whose is outboard, so it is not uniformly conservative. A run carrying
`freeze_protection` is reported as protected, with the number beside it.
