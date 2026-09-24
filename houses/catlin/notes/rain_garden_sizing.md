# Rain gardens RG-W-BASIN and RG-E-BASIN — hand-worked basis

**House:** catlin
**Structure:** `RG-W-BASIN` and its mirror `RG-E-BASIN` (`params/landscape_gardens.py`), their
inlets `TR-G-LEADER-W`/`-E` and `TR-RF-LEADER-W`/`-E` with their extensions, and the roofs
they drain (`RF-GARAGE`, `RF-HOUSE`, `RF-BW-CANOPY`).
**Written:** 2026-09-21, by hand from the authored geometry; the east basin, the canopy's
two-leader split and 12" ponding 2026-09-23.
**Oracle for:** `resolve/roof_catchment.py`, `resolve/rain_garden.py`,
`checks/mep/landscape_drainage.py` (`drainage.rain_garden_capacity`,
`drainage.infiltration_setback`, `drainage.leader_extension_fall`); reproduced by
`tests/test_catlin_gardens.py`.
**What is asked of the reviewer:** confirm §1's catchment split and §3's prismoidal volume.

> ⚠ Both Manual setbacks fall short on both basins, by the owner's choice (2026-09-21, and
> the east basin mirrors it): about 1'-0" to the side lot line and 6'-6" to the garage's
> frost stem, against 10' each. They report as advisory UNKNOWNs. Confirm with St Paul DSI
> and both neighbours before digging.

---

## 0. The two basins are one design

The lot is x −7'..43', centred on x = 18'-0", and so are the house and the garage. Every
basin, leader and extension here is authored once and mirrored about that line (x → 36 − x),
so each side's numbers below are identical except where a walk forces a deeper pipe (§6).

## 1. Catchment (plan area, overhang included), per side

Each gable splits at its ridge (x = 18'); a half goes to the leaders that claim it.

| roof half | working | sf | to |
|---|---|---|---|
| RF-GARAGE west / east | (18.000 − 4.667) × (68.552 − 43.146) = 13.333 × 25.406 | 338.75 | TR-G-LEADER-W / -E |
| RF-BW-CANOPY west / east | 13.333 × 6.000 | 80.0 | TR-G-LEADER-W / -E |
| RF-HOUSE west / east | (18.000 − (−0.604)) × (36.604 − (−0.604)) / 2 → 18.604 × 37.208 | 692.2 | TR-RF-LEADER-W / -E |
| **per basin** | 338.75 + 80.0 + 692.2 | **1,110.95** | |

The canopy's trough is continuous with the garage's and falls north to both garage leaders.
Its `EaveGutter.downspout_ref` names BOTH, and each claims the canopy half on its own side;
until 2026-09-23 it named only the east one and the west half was counted nowhere.

Each 3" garage leader therefore carries 418.75 sf against the ~425 sf a 3" round clears at
8 in/hr (`plan/storeys/garage.py`).

## 2. Demand, per basin

1.0" over 1,110.95 sf = 1,110.95 / 12 = **92.6 cf**.

## 3. Basin, per side

West rim x −6'..−1', y 47'..82'; east rim x 37'..42', the mirror. 5' × 35' = 175 sf at
−3'-1", ponding 12", side slopes 2:1, so the floor is the rim inset 2 × 1.0 = 2.0' each side:
1' × 31' = 31 sf at −4'-1". Mid-depth (inset 1.0'): 3 × 33 = 99 sf.

Prismoidal: V = h/6 · (A_top + 4 A_mid + A_bottom) = 1.0/6 × (175 + 396 + 31) =
602 / 6 = **100.3 cf ≥ 92.6 cf**, a 7.7 cf margin. Overflow is over the rim at the north end
to daylight, falling to the street.

(At the old 9" the same rim held 88.5 cf, 4.1 cf short once the canopy half was counted.)

Media 12" under the whole rim: 175 cf = 6.48 cy a basin, **12.96 cy** both. Stone 6" under
that: 87.5 cf = 3.24 cy a basin, **6.48 cy** both. Billed over the rim area, conservatively,
as the drywell's stone is.

The floor is only 1'-0" wide at 12". It takes ONE planted row on its centre line
(`_FLOOR_GRID`'s 6" edge inset), 15" o.c. along the run.

## 4. Drawdown

UNKNOWN until a soil test states a saturated infiltration rate: the Manual wants the
ponding gone in 48 h, which needs at least 12 / 48 = **0.25 in/hr** (0.19 at the old 9").

## 5. Setbacks (edge to face)

| basin | to | working | ft | verdict |
|---|---|---|---|---|
| W | house basement W-B-N4 | rim south edge y=47' to the wall face | 10.5 | PASS (≥ 10) |
| W | garage stem W-GF-N | rim east edge x=−1' to the stem face | 6.5 | UNKNOWN |
| W | west lot line x=−7' | x=−6' | 1.0 | UNKNOWN |
| E | house basement W-B-E2 | rim SW corner (37', 47') to the wall face | 10.4 | PASS (≥ 10) |
| E | garage stem W-GF-E | rim west edge x=37' to the stem face | 6.5 | UNKNOWN |
| E | east lot line x=43' | x=42' | 1.0 | UNKNOWN |

The east basement reads 0.1' closer than the west because W-B-E1/E2 are the house's two
12" pours (they bear `SL-M-DECK`); every other segment is 8".

## 6. Leader extensions (4" solid PVC, SDR 35)

Each outlet must stand no more than 2" above the floor it lets go over (−4'-1"), so at 12"
of ponding every outlet came down 3". The EAST runs pass under walks (A for the garage, D and
C for the house), whose 4" slab and 6" of Class 5 bottom at −3'-7": a 4" pipe's crown clears
that at an −4'-0" invert, so both east inlets sit there, and both east outlets land 1" below
the floor, in the media, with the emitter rising through it.

| leader | run (ft) | fall | slope | riser |
|---|---|---|---|---|
| TR-RF-LEADER-W | 0.91 + 10.33 + 3.20 = 14.44 | −40" → −47" = 7" | 4.0% | +12" → −40" = 4.33 |
| TR-G-LEADER-W | 4.73 → −3.00 = 7.73 | −41" → −47" = 6" | 6.5% | −18" → −41" = 1.92 |
| TR-RF-LEADER-E | 14.44, the mirror | −48" → −50" = 2" | 1.2% | +12" → −48" = 5.00 |
| TR-G-LEADER-E | (29.58, 67.58) → (39.00, 68.49) = 9.46 | −48" → −50" = 2" | 1.8% | −18" → −48" = 2.50 |

All four exceed IRC Table P3005.3's 1/8 in/ft (1.04%). Billed length = west 28.42 + east
31.40 = **59.8 LF**. The garage east run starts at its drop on the garage north wall, not
under the trough outlet (2026-09-23, `notes/sidewalk_layout.md` §3), and runs straight to
the old outlet point. Each ends in a pop-up emitter on its basin floor; a frozen line backs up
and overflows at the leader's own boot, which is the winter fallback.

The house runs start at the leader's authored position (x = −0'-10 9/16" / 36'-10 9/16"),
not the 8.77" the clamps still quote.

**The west line is shared (2026-09-22).** `SM-B-RADON`'s pumped discharge, `PR-B-SUMP-DISCH`
(1 1/2" PVC Sch 40), wyes into `TR-RF-LEADER-W`'s riser at −22", 18" above the extension's
−40" inlet. So the west basin also takes pumped groundwater — the house perimeter tile and,
through the one-tie bridge, the court's relief — which is **not in §2's design volume**, by
the owner's choice (2026-09-23): `drainage.rain_garden_capacity` reports it as an UNKNOWN
beside the PASS. The 7.7 cf margin is unclaimed headroom for it, not a credit. In winter the
buried line freezes; the pump's ice guard spills at the foundation foot, where the water can
recirculate to the perimeter tile and the pit.

## 7. What is NOT graded here

Pipe capacity (4" lines carrying 3" and 4" leaders, one also the pump), frost depth of the
extensions, the pumped volume, the risers' sleeves through walks A and D, a buried pipe
against a walk's base, and the neighbours' grade. The media mix's own infiltration rate is
the supplier's.

## Sources

- Minnesota Stormwater Manual, bioretention design and minimum setbacks,
  https://stormwater.pca.state.mn.us/minimum_setback_requirements
- IRC 2018 Table P3005.3 — slope of horizontal drainage piping.
