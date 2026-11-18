# LED construction: hand-worked lead drop (oracle)

Decision #137, 2026-11-17. `resolve/led_leads.py` derives each 24 V lead and sizes it from
`LED-STANDARD` (`plan/led_construction.py`). This note checks one case by hand, so the engine
is checked against independent arithmetic, not only against its own output.
`packages/engine/tests/test_led_construction.py` pins the engine to these numbers.

## Inputs

- **Run.** `LR-M-LIVING-E`: the lounge east cove, 144" (12'-0"), E4 tape at 6.1 W/ft with every channel on.
  - Load: 12 × 6.1 = 73.2 W.
  - Current: 73.2 / 24 = **3.05 A**.
- **Gear.** On the study ceiling bank (owner, 2026-11-17).
  - `ED-M-LIVING-LT-PSU-E` (driver) is at (204.5", 243.0").
  - `ED-M-LIVING-LT-CTRL-E` (controller) is at (204.5", 253.25").
  - The board face is 107.5" (the study's finished ceiling).
- **Standard.**
  - Drop limit: 3% of 24 V.
  - Slack: +10%.
  - Stocked cables: 18, 16 and 14 AWG.
  - A driver-to-controller leg is sized on half the budget. The feed leg gets what that leg leaves.
- **Copper resistance.** NEC Chapter 9 Table 8, stranded uncoated, 75 C, ohms per 1000 ft per conductor:

  | AWG | Ω/kft |
  |-----|-------|
  | 18  | 7.95  |
  | 16  | 4.99  |
  | 14  | 3.14  |

- **Drop formula.** For a two-wire lead the drop is out and back: V = I × 2 × R × L.

## Driver to controller

The pair sits 10.25" apart, within the 6' pairing distance, so the lead runs direct.

- Length: 10.25 × 1.10 = 11.275" = 0.9396 ft.
- 18 AWG: 2 × 7.95 × 0.9396 / 1000 = 0.014939 Ω.
- Drop: 3.05 × 0.014939 = 0.04556 V = **0.190%**, inside the 1.5% half budget.

## Controller to feed

The tape is fed at the end nearest the controller: the north end, (425.19", 156.0", 107.0").

The route is up to the cavity plane (107.5" + 0.05 m = 109.47"), east, south, then down to the board face.

| Segment | Length |
|---------|--------|
| up      | 1.97"   |
| east    | 220.69" |
| south   | 97.25"  |
| down    | 2.47"   |
| **sum** | **322.38"** |

- With slack: 322.38 × 1.10 = 354.62" = 29.551 ft.
- Budget left: 3.000 - 0.190 = **2.810%**.

Try each gauge:

| AWG | Resistance (2 × Ω/kft × 29.551 / 1000) | Drop | Result |
|-----|-----------------------------------------|------|--------|
| 16  | 0.29492 Ω | 0.8995 V = 3.748% | over budget |
| 14  | 0.18558 Ω | 0.5660 V = **2.358%** | fits |

**14 AWG** is the smallest gauge that fits.

## Result

The total lead drop is 0.190 + 2.358 = **2.548%**, under 3%.

`electrical.led_voltage_drop` still reports UNKNOWN for this run because SuperLightingLED publishes no single-feed length for the E4 tape. A 12' run is well inside the usual 5 m reel. Read the real figure off the supplier before ordering.
