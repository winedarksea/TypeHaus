# Stair stringers — how many, and of what (2026-09-28)

Model: `Stair.stringer_profile` / `stringer_material` / `stringer_spacing` /
`published_stringer_span` on ST-B2M (`plan/storeys/main.py`), ST-M2S (`second.py`) and ST-S2A
(`attic.py`). Graded by `structural.stair_stringer` and `structural.stair_tread_span`
(`checks/structural/stair_stringers.py`). `tests/test_stair_stringers.py` reproduces §2–§4.

## 1. Why

Every flight had two 2x12s, one at each lane edge, whatever its width or run, and nothing
graded them. ST-S2A's straight flight runs 10'-0" on two sawn 2x12s. ST-M2S's oak treads
spanned 39 3/8" clear between its two.

## 2. The rule

- **Sawn** (`2xN`): AWC DCA 6-2015 Fig. 28, horizontal run ≤ 6'-0" and throat ≥ 5". The IRC
  sizes no interior stringer; DCA 6 is the published prescriptive limit for a cut 2x stringer.
- **Engineered** (LSL/LVL): the maker's own stringer table, as a `PublishedSpan`.
- **Throat** = depth − R·T / √(R² + T²), perpendicular to the rake.
- **A stringer ledgered full length to a wall does not span** (`resolve/stairs/bearing.py`
  lags a ledger along it). Only the free stringers are graded.
- **Tread span** (practice only): clear distance between adjacent stringers ≤ 36".

## 3. By hand

R = riser, T = going, run = treads × T on the free stringer.

| Flight | R | T | run | profile | throat | limit |
|---|---|---|---|---|---|---|
| ST-B2M lower/upper | 110.4237/15 = 7.3616" | 10" | 6 × 10 = 60" = 5.00' | 2x12 | 11.25 − 73.616/12.426 = **5.32"** | 6'-0", 5" |
| ST-M2S lower/upper | 120.5138/16 = 7.5321" | 10" | 7 × 10 = 70" = 5.83' | 2x12 | 11.25 − 75.321/12.519 = **5.23"** | 6'-0", 5" |
| ST-S2A straight | 120/16 = 7.5" | 10" | 12 × 10 = 120" = 10.00' | 1.75x11.875 LSL | 11.875 − 75/12.5 = **5.875"** | 11'-8", 5.75" |

ST-S2A was **10.00' against 6'-0"** on sawn 2x12 — the FAIL this note retires. By beam
arithmetic (40 + 10 psf, SPF No.2 Fb 875, E 1.4e6, section = 1.5 × 5.25" throat, 18"
tributary on the free stringer, simple span 120"): M = 75 plf × 10² / 8 = 938 ft·lb, fb =
11,250 / 6.89 = 1,633 psi (ratio 1.9), Δ = 0.67" = L/180. It was not close.

## 4. ST-S2A's read

Weyerhaeuser #9010 (June 2021) p.4, "1-Ply TimberStrand LSL Stringers, IRC Maximum Stringer
Run — 40 psf Live Load/12 psf Dead Load", 1 3/4" 1.55E, 11 7/8", 36" tread width:

| 2 stringers, without | 2 stringers, with 2x4 | 3 stringers, without | 3 stringers, with 2x4 |
|---|---|---|---|
| 10'-0" | 10'-10" | **11'-8"** | 12'-6" |

Two stringers without reinforcement read exactly 10'-0" against a 10'-0" run: legal, and no
margin. **Three stringers at `stringer_spacing = 18"`** read 11'-8", 1'-8" spare, and match
the U stairs' centre stringer. Footnote 2: throat ≥ 5 3/4" at 11 7/8", and 5.875" clears it.
Footnote 1: riser ≤ 7 3/4" (7.5"), tread ≥ 10" (10"), story ≤ 151" (120").

The row is L/360 live / L/240 total at 40 + 12 psf. The check's demand is 40 (IRC R301.5
stairs) + 12 dead (1 1/2" oak ≈ 4.5 psf, three LSL stringers ≈ 5.5 psf over 3', a gypsum
soffit ≈ 2) = 52 psf, equal to the row.

## 5. The U stairs' centre stringer

The 2x12s already pass DCA 6. The centre stringer is for the treads: at `stringer_spacing =
22"` each flight gets three stringers, and the clear tread span falls from 39.4" (ST-M2S) and
38.1" (ST-B2M) to 18.9" and 18.3". Cost is four 8' 2x12s net (92 → 96 LF ordered: ST-S2A's
two 14' 2x12s left the row) and 42 LF of LSL.
