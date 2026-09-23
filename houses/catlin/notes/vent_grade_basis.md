# Vent grade — the oracle for `mep.vent_grade` and `mep.vent_grade_margin`

**House:** catlin, Minnesota. **Code:** MN Plumbing Code, Minn. R. ch. 4714, which adopts
the UPC. **Not IRC P3104.1** — Minn. R. 1309.0010 subp. 3.D deletes IRC chapters 25-33 and
P3104 is in chapter 31, so the section that governs a vent's grade here is **UPC 905.1**
(*Vent Grade and Connections*): vent pipes shall be free of drops and sags, and each vent
shall be graded and connected so as to drip back to the drainage pipe by gravity. This is
the same correction `notes/` and `checks/mep/plumbing_dwv.py` already carry for the drainage
half (UPC 708.0, not IRC P3005.3).

**Oracle for:** `checks/mep/vent_geometry.py`, both checks. Reproduced numerically by
`packages/engine/tests/test_vent_grade.py`.

The rule has two halves and this engine grades them as two checks, exactly as
`mep.drain_slope` / `mep.drain_slope_margin` split the drainage grade:

1. **`mep.vent_grade`, Tier.CODE** — *free of drops and sags*. Over a run's segments in
   path order (drainage connection → terminal) the elevation may never decrease. A vertex
   below both its neighbours is a low point; condensate collects there, the vent seals, and
   the trap seals it protects are siphoned by the next fixture that discharges. Vertical
   segments (zero plan length) are exempt: a riser holds no grade.
2. **`mep.vent_grade_margin`, Tier.ADVISORY** — the house's own **1/8"/ft**, from
   `plan/mep_venting.py`'s header ("fall ~1/8"/ft back toward the fixtures so condensate
   returns rather than pooling"). 905.1 states a *direction* and no figure, so a shortfall
   is reported as PASS with an `ADVISORY — ` prefix, the way `mep.equipment_turndown` reports
   an over-sized unit. It is not a code defect and nothing in the permit set gates on it.

Elevations below are inches, storey-relative as authored; a *difference* along one run is
the same number on any datum, which is why the check reads the profile without touching
`storeys`. Plan coordinates are inches in the project frame.

---

## 1. `PR-M-KITCH-VENT` — per-vertex elevations (the `z_m` branch)

Authored in `plan/mep_venting.py`: 1 1/2", serving `FX-M-KITCH-SINK`, six vertices with six
authored elevations.

| i | plan point (in) | elevation (in) |
|---|---|---|
| 0 | (392, 429) | `ft(9,3)` = 111 |
| 1 | (392, 232) | `ft(9,4)` = 112 |
| 2 | (180, 232) | `ft(9,6.375)` = 114.375 |
| 3 | (180, 296) | `ft(9,8.75)` = 116.75 |
| 4 | (12, 296) | `ft(9,9)` = 117 |
| 5 | (12, 414) | `ft(9,9.25)` = 117.25 |

Plan lengths (every leg is orthogonal, so each is one subtraction), and the rise across it:

    seg 0  429 − 232 = 197" = 16.4167 ft    rise 112    − 111     = +1.000"
    seg 1  392 − 180 = 212" = 17.6667 ft    rise 114.375 − 112    = +2.375"
    seg 2  296 − 232 =  64" =  5.3333 ft    rise 116.75 − 114.375 = +2.375"
    seg 3  180 −  12 = 168" = 14.0000 ft    rise 117    − 116.75  = +0.250"
    seg 4  414 − 296 = 118" =  9.8333 ft    rise 117.25 − 117     = +0.250"

**`mep.vent_grade`: PASS.** Five segments, five positive rises, no drop and therefore no
sag. Five of five are horizontal, so the finding counts five.

Grades, rise ÷ plan:

    seg 0  1.000 / 16.4167 = 0.0609 "/ft
    seg 1  2.375 / 17.6667 = 0.1344 "/ft
    seg 2  2.375 /  5.3333 = 0.4453 "/ft
    seg 3  0.250 / 14.0000 = 0.0179 "/ft   <- flattest
    seg 4  0.250 /  9.8333 = 0.0254 "/ft

**`mep.vent_grade_margin`: PASS with `ADVISORY — `.** The flattest leg is segment 3 at
**0.018"/ft**, a seventh of the 1/8"/ft this house grades a vent to — 1/4" of fall spread
over fourteen feet is level within the tolerance a hanger is set to. It does rise, so 905.1
is satisfied and no FAIL is issued.

## 2. `PR-S-BATH1-VENT` — two authored inverts (the interpolation, and the fallback)

2", `start_elevation=ft(9,3)` = 111, `end_elevation=ft(9,4)` = 112, four vertices and no
per-vertex tuple. The resolver interpolates over developed plan length, so every segment
comes out at the same grade and the check's two branches must agree on that number.

    A (116.4, 372) → B (60, 318)   √(56.4² + 54²) = √(3180.96 + 2916) = √6096.96 = 78.08"
    B (60, 318)    → C (12, 318)   48"
    C (12, 318)    → D (12, 421.3) 103.3"
    developed plan length           78.08 + 48 + 103.3 = 229.38" = 19.1150 ft

    grade = (112 − 111) / 19.1150 = 0.05231 "/ft, on every segment

2026-09-23: the chase moved from (12, 414) to (12, 421.3), so leg C→D grew 96" → 103.3"
(was 222.08" / 0.054"/ft).

**`mep.vent_grade`: PASS** (three segments, each +0.052"/ft × its own length, all positive).
**`mep.vent_grade_margin`: PASS with `ADVISORY — `** at 0.052"/ft, under 1/8"/ft.

Strip the resolved per-vertex tuple and the check's second branch reads the same run as one
segment of 19.1150 ft rising 1.000" — **0.052"/ft, the identical number**. That is the point
of the two branches being written from one profile: a legacy run with two inverts and a
routed run with six must not be graded against different arithmetic.

## 3. The whole house, 2026-09-19

Eight vent runs, and the flattest horizontal leg of each:

| run | elevations | segments | flattest | verdict |
|---|---|---|---|---|
| `PR-B-BATH-VENT` | per-vertex | 4 (1 riser) | 0.073"/ft | PASS / advisory |
| `PR-B-SAUNA-VENT` | per-vertex | 6 (1 riser) | 0.044"/ft | PASS / advisory |
| `PR-M-WC-VENT` | per-vertex | 5 | 0.085"/ft | PASS / advisory |
| `PR-M-KITCH-VENT` | per-vertex | 5 | 0.018"/ft | PASS / advisory |
| `PR-S-BATH1-VENT` | two inverts | 3 | 0.054"/ft | PASS / advisory |
| `PR-S-SUITEBATH-VENT` | two inverts | 6 | 0.068"/ft | PASS / advisory |
| `PR-A-STUBATH-VENT` | per-vertex | 2 | 0.152"/ft | PASS / PASS |
| `PR-A-BAR-VENT` | per-vertex | 3 (1 riser) | 0.300"/ft | PASS / PASS |

**8 of 8 PASS the CODE check** — nothing in this house drops or sags on its way to a
terminal. Six of the eight hold less than 1/8"/ft and carry the advisory prefix, which is
the fact the model could not state before: the two attic runs are the only vents in catlin
built at a grade a plumber would recognise as a grade. The two-storey wet-wall runs are
long, the head between a flood-level rim and the chase is thin, and 905.1 does not ask for
more — but the house's own header does, and now the report says so out loud.

## 4. What this does not claim

Not a venting *design*: whether a vent is required, where it may connect, its size and its
termination are `mep.vent_reachability`, `mep.vent_termination_height`, `mep.pipe_sizing`
and `checks/mep/vent_path.py`. This note is about one thing — the shape of the profile
between the drainage connection and the terminal.
