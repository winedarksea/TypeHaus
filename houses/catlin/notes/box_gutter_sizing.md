# Box gutter sizing: TR-RF-GUTTER-E/W, catalog 5x4 PBR box gutter

**House:** catlin
**Structures:** `TR-RF-GUTTER-E`/`-W` (was the custom 6 in x 5 in box, `params/roof_trim.py`),
leaders `TR-RF-LEADER-E`/`-W` (4 in round), roof `RF-HOUSE` (6:12, ridge N-S at x=18').
Adopted: Metal Sales PBR box gutter 58077XX/58079XX (5 in bottom, 4 in front waterway, 5 in back),
20'-3" lengths, with 58081XX/58082XX end caps and 58092XX straps.
**Written:** 2026-10-27, by hand from the resolved model and the Metal Sales manuals.
**Oracle for:** plan item 5 of the trim plan (the box gutter swap). `tests/test_gutter_sizing.py`
pins the numbers in sections 1-5.

> Unverified inputs are listed in section 7.

---

## 1. Design intensity

**Design basis: SMACNA 10-yr, 5-min intensity** (owner's brief, 2026-10-27), not the 100-yr 1-hr
figure the first draft used. The 100-yr 1-hr row stays as a cross-check.

St Paul point, NOAA Atlas 14 Vol. 8 (lat 44.9537, lon -93.0900). Depths in inches. The values are
the HDSC PDS point estimates read from the table (not interpolated): the 5-min row, columns
10-yr, 5-yr, 25-yr and 100-yr, and the 60-min 100-yr cell. The 10-yr 5-min depth has a 90% band
of 0.493 to 0.811 in (section 7).

| Duration, ARI | Depth (in) | Intensity (in/hr) | Use |
|---|---|---|---|
| 5-min, 10-yr | 0.628 | **7.54** | **design basis** (SMACNA 10-yr 5-min) |
| 60-min, 100-yr | 3.55 | 3.55 | cross-check (IPC-style 100-yr 1-hr) |
| 5-min, 5-yr | 0.533 | 6.40 | PGI-15 recorded basis |
| 5-min, 25-yr | 0.765 | 9.18 | PGI-15 recorded basis |
| 5-min, 100-yr | 0.990 | 11.88 | stricter cross-check |

The 8 in/hr that `params/roof_trim.py` carried had no cited source and matches no row above.
It is retired: the leader comment now cites section 4.

## 2. Drainage area per side

From `resolve/roof_catchment.py` halves of the `RF-HOUSE` footprint, which runs to the cladding faces
(x -0.604' to 36.604', y -0.563' to 36.562'). Each half is the full eave, so one leader per side.

- West half: 18.604' x 37.125' = **690.68 sf plan area**. East half identical.
- The 648 sf in the brief is 18' x 36', which omits the 7.25" E/W and 6.75" N/S cladding stand-off.
- Pitch 6:12 (`plan/storeys/attic.py:594`). Design area is the horizontal projection. The sources
  in hand state no pitch factor. Sensitivity: x sqrt(1 + (6/12)^2) = x 1.118, giving **772.2 sf**.
- Gutter length served by one leader: **L = 37.12 ft** (north outlet at y = 35.5').

## 3. Gutter demand against the 5x4 section

Metal Sales (PGI-16, NIST-derived chart): **W = 0.0106 * M^(-4/7) * L^(3/28) * (IA)^(5/14)**,
W in ft, M = depth/width, L in ft, I in/hr, A in sf.
Check: PGI-16's worked example (L 40, M 0.75, IA 7200) gives 5.31 in, which the manual reads as
"between 5 and 6 in".

Sections (PBR install 4/24, p. 12, Box Gutter 58077XX/58079XX): the catalog box is 5.00 in bottom,
4.00 in front, 5.00 in back, with a 1 in hem at the front top. The front is the lower side, so it
is the waterway and sets M = 4/5 = 0.80. The 5x4 section is the one the chart is read for. Current
custom 6x5 is 6.00 in wide, 5.00 in deep, so M = 0.833.

Width required at the catalog depth, W_req = 12 * 0.0106 * 0.8^(-4/7) * 37.12^(3/28) * (IA)^(5/14)
= 0.2128 * (IA)^(5/14) in, with 0.8^(-4/7) = 1.136 and 37.12^(3/28) = 1.473.

| Case | I (in/hr) | A (sf) | IA | 5x4 W_req (in) | 5x4 vs 5.00 in | 6x5 W_req (in) | 6x5 vs 6.00 in |
|---|---|---|---|---|---|---|---|
| **5-min 10-yr, plan (design)** | 7.54 | 690.68 | 5,205 | 4.52 | **PASS** (0.48 in) | 4.42 | PASS |
| **5-min 10-yr, 6:12 sloped** | 7.54 | 772.2 | 5,819 | 4.71 | **PASS** (0.29 in) | 4.60 | PASS |
| 100-yr 1-hr, plan | 3.55 | 690.68 | 2,452 | 3.46 | PASS | 3.38 | PASS |
| 100-yr 1-hr, 6:12 sloped | 3.55 | 772.2 | 2,741 | 3.60 | PASS | 3.51 | PASS |
| 5-min 5-yr, plan | 6.40 | 690.68 | 4,418 | 4.26 | PASS | 4.17 | PASS |
| 5-min 25-yr, plan | 9.18 | 690.68 | 6,340 | 4.85 | PASS (0.15 in) | 4.74 | PASS |
| 5-min 25-yr, sloped | 9.18 | 772.2 | 7,089 | 5.05 | **FAIL** (0.05 in) | 4.93 | PASS |
| 5-min 100-yr, plan | 11.88 | 690.68 | 8,205 | 5.32 | **FAIL** | 5.20 | PASS |
| 5-min 100-yr, sloped | 11.88 | 772.2 | 9,174 | 5.54 | **FAIL** | 5.41 | PASS |

At a 5.00 in width the depth needed is 2.10 in (100-yr 1-hr) and 4.46 in (5-min 100-yr, plan).
The 5x4 has 4.00 in, so it covers the design basis with room, and not the 5-minute 25-yr sloped or
100-yr cases.

## 4. Leaders, outlet and count

Metal Sales spacing rule (PGI-18): **DS = 1200 * A / (R * I)**, A = leader area (sq in),
R = roof width drained (ft) = 18.604 ft, I in/hr. Maximum spacing = DS; it must be at least L = 37.12 ft.
A leader therefore serves 1200 * A / I sf of roof.

| Leader | Area (sq in) | Serves at 10-yr 5-min (sf) | Required area, 10-yr plan / sloped | Required area, 5-min 100-yr sloped | Max spacing, 10-yr plan | Verdict |
|---|---|---|---|---|---|---|
| 4 in round (kept, both sides) | 12.57 | 2,001 | 4.34 / 4.85 | 7.64 | 107.6 ft | PASS |
| 3 in round (not used) | 7.07 | 1,126 | 4.34 / 4.85 | 7.64 | 60.5 ft | PASS on the design basis; FAIL the 100-yr sloped cross-check (38.4 ft at 100-yr plan) |

- **Why 4 in:** the 3 in clears the design basis, but it fails the 100-yr 5-min sloped cross-check, and
  the 4 in clears it. The 4 in is kept.
- **Outlet:** 4 in leader against 5.00 in gutter bottom. PGI-15 requires downspout <= bottom width: **PASS**.
- **Count:** one leader per side at the north end, L = 37.12 ft, under PGI-18's 50 ft maximum: **PASS**.
- The existing `TR-RF-LEADER-W/E` (4 in) are kept.

## 5. Verdict

East and west halves are identical, so the verdict is the same on each side.

- **Catalog 5x4 gutter: PASS** on the SMACNA design basis (5-min 10-yr, 7.54 in/hr). Demand is
  4.52 in on plan area and 4.71 in on 6:12 sloped area, against 5.00 in. The 4.00 in waterway
  covers both.
- **Catalog 5x4 gutter: FAIL** on the 5-min 25-yr sloped case (5.05 in) and both 5-min 100-yr
  cases. These are cross-checks beyond the design basis. The 5x4 has no margin there, and PGI-15
  records 25-yr intensities, so a reviewer who holds the 25-yr sloped case to the design basis
  will object to the 5x4. The 10-yr 90% upper band also fails on sloped area (section 7).
- **4 in round leader: PASS** in every case.
- **Outlet and count: PASS.**
- The current 6x5 box passes every row, including the 100-yr 5-min sloped case (5.41 in against 6.00 in).
  It is the fallback if the 25-yr sloped case governs review.

## 6. Discrepancies in the existing model

- `roof_trim.py` gave 8 in/hr, uncited and not a NOAA row. Retired; see section 1.
- `roof_trim.py` said a 3 in leader clears about 425 sf at 8 in/hr. The PGI-18 relation gives
  1,060 sf at 8 in/hr (1200 * 7.07 / 8). The 425 figure is not reproduced by any source in hand,
  and the comment has been rewritten against section 4.
- The brief's 648 sf per side omits the cladding stand-off. The model gives 690.68 sf per side.
- The catalog box's back is 5 in and its front 4 in. Since 2026-10-28 the model sweeps the whole
  formed piece (`pbr_box_gutter_section`, `resolve/gutter_formed.py`), so the 4 in front, the 1 in
  bead and the 3-1/2 in roof flange are all in the model; `Gutter.depth` is the back.

## 7. Unresolved

1. **Code basis.** IPC Figure 1106.1 / Appendix B was not verified. A web summary suggested Minnesota may
   not adopt IPC 1106.1 (the DLI minutes it cited returned 404). Confirm the adopted storm-drainage
   provisions (Minn. R. ch. 4714) before sealing.
2. **NOAA values.** Read 2026-10-27 from the HDSC PDS point response for this lat/lon (the `mw.h5`
   quantiles, not a summary). The 5-min row and the 60-min 100-yr cell match the earlier reading.
   Column order follows NOAA's ascending ARI. Still verify on the NOAA PFDS page before sealing.
3. **SMACNA basis.** The 10-yr 5-min design basis is the owner's brief. The SMACNA manual is not in
   `houses/catlin/notes/sources/`, so its text is not verified here.
4. **Confidence band.** At the 10-yr 90% upper bound (0.811 in = 9.73 in/hr) the 5x4 needs 4.95 in on
   plan area (PASS, 0.05 in) and 5.16 in on sloped area (FAIL). The point estimate is what the basis
   calls for, so the verdict stands, but the sloped margin is inside the band.
5. **Pitch convention.** Plan-area design basis is used; the 6:12 sloped case is shown beside it.
   The sources in hand do not settle which applies.
6. **Intensity basis.** PGI-15 says Metal Sales intensities are recorded at 5-yr and 25-yr recurrence.
   Section 5 shows where the 5x4 sits against that record.
7. The gutter is installed level (section 8). Outlet hydraulics are not checked here.
8. **Straps and outlets.** PBR p. 46 gives no strap spacing. The model bills straps at 3'-0" o.c.,
   the maximum the same manual gives for its sculptured gutter hangers (p. 63). The outlet into the
   gutter floor is a shop cut; no catalog part is named for it.

## 8. Level installation acceptance

The gutter is installed **level** (2026-10-28): its back tucks behind the Image II Extended Eave
face and its roof flange runs up under the eave's pitched leg, and the eave is level, so a fall
would open the flange off the leg at one end. The PGI-16 relation in section 3 is the level-gutter
(Beij/NIST) relation, so the SMACNA level basis **stands** and section 3 is unchanged.

Resolved section, inches out from the cladding face (u) and above the deck plane at the edge (z),
from `EaveStack` at y = 17'-4":

| Point | u | z |
|---|---|---|
| Back top = front crest (section origin) | 0.06 | 0.73 |
| Front wall top (the 4 in waterway) | 5.06 | -0.27 |
| Trough floor, water face | 0.06 to 5.06 | -4.27 |
| Flange upslope end (lowest inward route) | -3.07 | 2.30 |
| Eave face bottom | 0.11 | -0.76 |
| Eave kick tip | 0.47 | -1.28 |
| Pan drip at the lip | 1.48 | -0.01 |

Acceptance:

- **Level within +/-1/8 in over the run, and never falling away from the outlet.** Any tolerance
  goes toward the north outlet.
- **Retained water** is limited to the film below a flush outlet: the outlet is cut flush in the
  floor, so a level trough holds no standing depth above it.
- **The north tail drains back with no fall.** The outlet centre is 12.75 in from the gable
  face; the trough runs on 0.5 in more under the eave's run-out to its end cap. A level tail
  that short empties through the outlet as the head on it drops.
- **Outlet against the kick and the end cap.** The 4 in outlet centred on the 5 in floor
  (u 0.56 to 4.56) leaves 0.5 in each side. The kick tip stands over its inboard edge but 3.0 in
  above the floor, so it does not crowd the inlet. The north end cap is 11.25 in past the outlet's
  edge.
- **Clear section.** The eave face, kick and open hem now hang inside the mouth: the face's
  lowest 0.49 in, the 5/8 kick and the 1/2 hem lie below the front top (-0.27), i.e. inside the
  4 in design waterway. As 24 ga sheet that is under 0.05 sq in of the 20 sq in waterway (0.25%),
  and it runs along the flow, not across it. The pan drip and the lip stand above the front top.
  **No change to W_req or M.** The full gutter spills over the front: the crest is 1.57 in below
  the flange's upslope end.
- **Open:** the hanger screws pierce the back 4.7 in below the crest (pending bracket selection;
  sealed fastener). They are the only route inward below the crest
  (`test_catlin_eave_water.py::test_a_full_gutter_spills_outward`).

## Sources

- Metal Sales, *General Information*, PGI-15 to PGI-19, Gutter and Downspout Sizing:
  `houses/catlin/notes/sources/metal-sales-general-information.pdf`.
- Metal Sales, *PBR Panel Install* (4/24), p. 12, Box Gutter 58077XX/58079XX and End Cap 58081XX/58082XX,
  strap 58092XX; p. 46 box gutter detail; p. 63 sculptured gutter hanger spacing:
  `houses/catlin/notes/sources/metal-sales-pbr-install-2024.pdf`.
- NOAA Atlas 14 Vol. 8, point query (HDSC PDS):
  https://hdsc.nws.noaa.gov/cgi-bin/new/cgi_readH5.py?lat=44.9537&lon=-93.0900&type=pf&data=depth&units=english&series=pds
- Model: `resolve/roof_catchment.py`, `params/roof_trim.py`, `plan/storeys/attic.py` (`Pitch(6, 12)`).
