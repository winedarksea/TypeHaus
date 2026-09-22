# West rain garden RG-W-BASIN — hand-worked basis

**House:** catlin
**Structure:** `RG-W-BASIN`, its inlets `TR-G-LEADER-W` and `TR-RF-LEADER-W` with their
extensions, and the roofs they drain (`RF-GARAGE`, `RF-HOUSE`, `RF-BW-CANOPY`).
**Written:** 2026-09-21, by hand from the authored geometry.
**Oracle for:** `resolve/roof_catchment.py`, `resolve/rain_garden.py`,
`checks/mep/landscape_drainage.py` (`drainage.rain_garden_capacity`,
`drainage.infiltration_setback`, `drainage.leader_extension_fall`); reproduced by
`tests/test_catlin_gardens.py`.
**What is asked of the reviewer:** confirm §1's catchment split and §3's prismoidal volume.

> ⚠ The canopy's WEST half (80 sf) reaches the garage trough and falls to `TR-G-LEADER-W`
> in the field, but `RF-BW-CANOPY`'s gutter names only `TR-G-LEADER-E`, so the engine
> counts it nowhere. The basin is sized WITHOUT it. At 1" it is another 6.7 cf; the basin
> clears the counted demand by only 2.6 cf, so if that water is to be credited here the
> basin grows about 3'-0" north first.

> ⚠ Both Manual setbacks fall short, by the owner's choice (2026-09-21): about 1'-0" to the
> west lot line and 6'-6" to the garage's frost stem, against 10' each. Both report as
> advisory UNKNOWNs. Confirm with St Paul DSI and the west neighbour before digging.

---

## 1. Catchment (plan area, overhang included)

Each gable splits at its ridge; a half goes to the leaders that name its gutter.

| roof half | working | sf | to |
|---|---|---|---|
| RF-GARAGE west | (18.00 − 4.67) × (68.55 − 43.15) = 13.33 × 25.40 | 338.6 | TR-G-LEADER-W |
| RF-HOUSE west | (18.000 − (−0.604)) × (36.604 − (−0.604)) = 18.604 × 37.208 (cladding line) | 692.2 | TR-RF-LEADER-W |
| **basin total** | | **1,030.8** | |
| RF-BW-CANOPY west | 13.33 × 6.00 | 80.0 | uncounted (⚠ above) |

## 2. Demand

1.0" over 1,030.8 sf = 1,030.8 / 12 = **85.9 cf**.

## 3. Basin

Rim x −6'..−1', y 47'..82' (5' × 35' = 175 sf) at −3'-1", ponding 9", side slopes 2:1, so
the floor is the rim inset 2 × 0.75 = 1.5' each side: 2' × 32' = 64 sf at −3'-10".
Mid-depth (inset 0.75'): 3.5 × 33.5 = 117.25 sf.

Prismoidal: V = h/6 · (A_top + 4 A_mid + A_bottom) = 0.75/6 × (175 + 469 + 64) =
0.125 × 708 = **88.5 cf ≥ 85.9 cf**, a 2.6 cf margin. Overflow is over the rim at the north
end to daylight, falling to the street.

Media 12" under the whole rim: 175 cf = **6.48 cy**. Stone 6" under that: 87.5 cf =
**3.24 cy**. Both are billed over the rim area, conservatively, as the drywell's stone is.

## 4. Drawdown

UNKNOWN until a soil test states a saturated infiltration rate: the Manual wants the
ponding gone in 48 h, which needs at least 9 / 48 = 0.19 in/hr.

## 5. Setbacks (edge to face)

| to | working | ft | verdict |
|---|---|---|---|
| house basement W-B-N4 | rim south edge y=47' to the wall at y≈36.5' | 10.5 | PASS (≥ 10) |
| garage stem W-GF-N | rim east edge x=−1' to the stem face | 6.5 | UNKNOWN |
| west lot line x=−7' | x=−6' | 1.0 | UNKNOWN |

## 6. Leader extensions (4" solid PVC, SDR 35)

| leader | run | fall | slope | riser |
|---|---|---|---|---|
| TR-RF-LEADER-W | 1.02 + 10.33 + 3.20 = 14.55 ft, west of SL-M-HP3PAD | −40" → −44" = 4" | 2.3% | +12" → −40" = 4.33 ft |
| TR-G-LEADER-W | 4.73 → −3.00 = 7.73 ft | −41" → −44" = 3" | 3.2% | −18" → −41" = 1.92 ft |

Both exceed IRC Table P3005.3's 1/8 in/ft (1.04%). Billed length = 14.55 + 4.33 + 7.73 +
1.92 = **28.5 LF**. Both end in a pop-up emitter on the basin floor; a frozen line
backs up and overflows at the leader's own boot, which is the winter fallback.

## 7. What is NOT graded here

Pipe capacity (two 4" lines carry a 3" and a 4" leader), frost depth of the extensions,
and the neighbour's grade. The media mix's own infiltration rate is the supplier's.

## Sources

- Minnesota Stormwater Manual, bioretention design and minimum setbacks,
  https://stormwater.pca.state.mn.us/minimum_setback_requirements
- IRC 2018 Table P3005.3 — slope of horizontal drainage piping.
