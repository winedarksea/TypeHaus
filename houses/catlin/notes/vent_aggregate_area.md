# Aggregate vent area (UPC 904.1) — hand-worked basis

**House:** catlin
**Structure:** `VR-M-STACK` (the one sanitary vent terminal), `PR-B-MAIN-DRAIN` (the building drain)
**Written:** 2026-11-19, by hand, before `mep.vent_aggregate_area` was encoded.
**Oracle for:** `checks/mep/vent_area.py`, reported by `mep.vent_aggregate_area`; reproduced by
`tests/test_vent_aggregate_area.py`.
**Companions:** `notes/bath2_vent_move_options.md` covers the BATH2 WC vent's own route.
**What is asked of the reviewer:** confirm §2's 50 DFU against Table 702.1, and §4's areas.

> ⚠ The governing sewer is the REQUIRED one (Table 703.2 on the DFU), not the pipe as drawn.
> A radon leg is a separate system and never counts toward the area.

---

## 1. Code read

| Source | Text, as read | Use here |
|---|---|---|
| UPC 904.1 (MN 4714.0050 adopts it unamended; there is no 4714.0904) | the vents serving a building drain need an aggregate cross-sectional area not less than the largest required building sewer, as determined from Table 703.2 | the rule |
| MN 4714.0906 subp. 1 (906.1) | "Each vent pipe or stack shall extend through its flashing and shall terminate vertically not less than 12 inches (305 mm) above the roof." | flashed penetration + vertical terminal; no roof penetration required |
| subp. 2 (906.3) | full required size, 12" above the roof; flagpoling banned except on a used roof | the RF-HOUSE roof is weather-only |
| subp. 3 (906.7) | terminal >= 2", not smaller than the required vent; "Any change in diameter shall be made inside the building not less than 12 inches (305 mm) below the roof in an insulated space" | the increaser is inside, in the conditioned attic |
| UPC 906.2 (unamended) | 10 ft from, or 3 ft above, an openable window, door, opening or air intake; 3 ft from a lot line | graded elsewhere (`code.MN_1303_2402_radon`, ERV terminal checks) |
| UPC 906.4 (unamended) | vents for **outdoor installations** extend >= 10 ft above grade and are securely supported | this is a vent serving an outdoor fixture, not an exterior vent pipe; the terminal is ~26' up and strapped |
| UPC 906.5 / 906.6 (unamended) | watertight approved flashing "at the roof around vent pipes"; sheet lead >= 3 lb/sf | a wall flashing, §5 |

No unamended 906 subsection found requires the pipe to pass through the roof, or freeze
protection for an exterior vent leg. MN 906.7 is the frost rule, and an inside increaser with a
4" terminal meets it. The side exit stays (owner, 2026-11-19).

Source quality: 4714.0906 was read on revisor.mn.gov. The UPC 904.1 and 906.2-906.6 wording
above comes from secondary summaries, because UpCodes and ICC put the UPC text behind a login. Check
those two rows against the printed 2018 UPC before they are cited on a sheet.

## 2. Demand: the building drain

`PR-B-MAIN-DRAIN` leaves through the exit sleeve that `mep.sewer_exit_invert` grades. Its
upstream union of fixtures, from Table 702.1:

| Group | Fixtures (DFU) | Sum |
|---|---|---|
| Basement | B-BATH WC 3, LAV 1, UTIL sink 2; SAUNA shower 2, floor drain 2 | 10 |
| Main | BATH1 WC 3, LAV 1; BATH2 WC 3, sink 1, shower 2, tub 2; kitchen 2; laundry sink 2; washer 3 | 19 |
| Second | BATH1 WC 3, LAV 1, tub-shower 2, vanity 1 + 1; SUITEBATH WC 3, LAV 1, tub-shower 2 | 14 |
| Attic | STUBATH WC 3, LAV 1, shower 2; bar sink 1 | 7 |
| **Total** | | **50** |

Table 703.2, horizontal: 3" carries 35 DFU, 4" carries 216. 50 > 35, so the **required building
sewer is 4"**: A = π/4 · 4² = **12.57 in²**.

## 3. The vent tree, and where it reaches atmosphere

Every branch vent ties into `VR-M-STACK`'s VENT pipe below its one terminal:

| Branch | DFU served | Ties in |
|---|---|---|
| `PR-B-SAUNA-VENT` (2", takes `PR-B-BATH-VENT`) | 10 | the chase, at the basement ceiling |
| `PR-M-WC-VENT` / `PR-M-BATH2-VENT` (main floor) | 19 | up `PR-S-BATH1-VENT` into the chase below the 19'-6" jog |
| `PR-S-BATH1-VENT` (2") | 8 | the chase below the jog |
| `PR-S-SUITEBATH-VENT` | 6 | the jog's crown at (9'-0", y 34'-4.9") |
| `PR-A-STUBATH-VENT` (2", takes `PR-A-BAR-VENT`) | 7 | the 4" head, just under the 23'-8" exit |

`FX-M-BATH2-WC`'s in-wall vent (`notes/bath2_vent_move_options.md`) is not drawn yet. It also ties in
below the terminal, so it does not change the area. Drawing it is out of scope here.

## 4. Capacity, and the comparison

| Case | Terminal | Working | Area | vs 12.57 in² |
|---|---|---|---|---|
| Before | 3" | π/4 · 3² | 7.07 in² | **FAIL**, 56% |
| After | 4" (3x4 increaser at 20'-6") | π/4 · 4² | 12.57 in² | **PASS**, 100% |

Nominal diameters on both sides, as 904.1 compares sizes.

Developed length of the stack: 3" from the radon pit floor (-8'-10") up to the increaser,
36.9 ft (8'-10" + 19'-6" rise, the 7'-7" jog, then 1'-0" on to 20'-6"), then 4" for 8.8 ft
(3'-2" to the exit, 2'-7.8" out, 2'-11.8" to the terminal), 45.7 ft in all. Table 703.2's vent
column gives a 3" vent 84 DFU and 212 ft, so 50 DFU over 36.9 ft is inside it. The 3" chase
riser stays 3".

Subp. 3 check: the increaser at 20'-6" (246") is under the 6:12 roof at the riser's plan point
(8'-5", 34'-4.9"). Over that point the roof surface stands 307.8", which is 61.8" above the
increaser against the 12" required. The fitting sits in the conditioned attic (unvented ccSPF
roof). The engine grades this as `integrity.vent_increaser_roof`.

## 5. What is NOT graded here

- The vent's own Table 703.2 length and DFU per branch (`mep.vent_reachability`, `mep.vent_connection`).
- Vents upstream of a pump or ejector, which 904.1 excludes. Catlin has none on a sanitary branch: the
  sump is drain tile.
- The wall flashing. It is recorded in `plan/mep_vent_clamps.py` and
  `notes/outie_window_truss_detail.md`, and no check grades it.

## Sources

- MN Rules 4714.0906 (2020 MN Plumbing Code, vent termination), revisor.mn.gov, read 2026-11-19.
- MN Rules 4714.0050, which adopts the 2018 UPC with amendments; ch. 9 has no 4714.0904.
- UPC 2018 §904.1, §906.2-906.6, and Tables 702.1 / 703.2. The section text is from secondary
  summaries (open-exam-prep UPC 906 / 904 study notes; Salina KS ADM-2.0904.1(2)), and the
  printed text needs confirming.
