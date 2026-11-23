# `D-B-SUNKEN` rim header — hand check

**House:** catlin. **Element:** `D-B-SUNKEN` (63 5/16" RO French pair) in `W-B-S3-FR`, headed in
`FS-M-EAST`'s band (`Door.header_in_band`). **Written:** 2026-10-31 by hand for the LVL plies;
**rewritten 2026-11-23 (decision 12)** for the 2-ply LSL rim header, which replaces them.
**Oracle for:** `checks/structural/rim_header.py` and `engineering/band_header*.py`, reproduced
by `tests/test_rim_header.py`; the arithmetic is `notes/engineering_review_2026-11-22/scratch/L3/hand.py`.
**Retired:** `band_header/D-B-SUNKEN` (an engineered item, 0.434). The header is a published read
now, so nothing of it is left on the engineering register.
**Open:** the ForteWEB report. The exact input is `notes/engineering_review_2026-11-22/forteweb_D-B-SUNKEN.md`;
**ForteWEB report: owner to run and retain.**

## 1. Why the header is in the band, and what it is now

The RO is 82 7/8" with a -1 3/4" sill, so the rough head stands 4 5/8" under the plates and no
R602.7 header fits (geometry review C3-E2). `W-B-S3-FR` is BEARING but runs PARALLEL to
`FS-M-EAST`'s joists, so the member over the opening is the y=0 edge-joist line: the floor's
1 1/4" x 11 7/8" TimberStrand LSL edge rim. The review (F-08) found that rim alone is a published
header for the span (TJ-8000 p.6, 6'-0" row, 792 plf; d/c 0.060) and that the two 1 3/4" LVL plies
beside it did no work the rim could not. They are deleted. **One ply of the same rim stock sits behind
the rim, pack to pack (x 18'-2 11/32" to 24'-5 21/32", the outer faces of the two 4-stud packs)**: a
2-ply 1 1/4" LSL header, **Weyerhaeuser TJ-8000 (March 2025) p.7, *Load tables: 2-ply rim board*,
1 1/4" 1.3E TimberStrand LSL, 11 7/8"** (a row, so a prescriptive read). The ply is also
`D-M-PORCH`'s HeadLOK backer (`exterior_door_sill_beam.md` §3: 1 1/4" in the rim + 3/4" in the
ply = 2.0" of thread). It is not a bearing ref: `resolve/floors.py` would cut every joist at that line.

## 2. What loads it

| Term | Working | Value |
|---|---|---|
| Clear span | the RO | 63.3125" = 5.276 ft |
| Bearings | 4 x 1 1/2" pack each end (TJ-8000 p.6 wants 4 1/2" minimum) | 6" each |
| Span c-c of bearing | 63.3125 + 6 | 69.3125" = **5.776 ft** (read up to the 6'-0" row) |
| Floor strip | 1.125 + 14.875 / 2 | 8.5625" = 0.71354 ft |
| Floor load | IRC R301.5, 40 live + 10 dead | 50 psf -> **35.68 plf** (the header's weight neglected: TJ-8000 p.6) |
| Door seats (F-07) | `D-M-PORCH`'s sill beam, two seats, `exterior_door_sill_beam.md` §3 | **325.73 lb each**, at the seat screw groups, 4.969" in from the RO edge (7.969" from the bearing's centre), both at once |

The packs of `D-M-PORCH` above are the same 63 5/16" RO on the same centre, so its stacked jamb
loads stand on the bearings and not in the span. The seat reactions DO sit in the span (F-07, which
the LVL record left out), 7.25" outboard of the rim's face: a vertical load plus a couple.

## 3. The header, and why the table's uniform-load row needs a cross-check

TJ-8000's rows are **uniform load, simple span** (p.6 general notes). The seat loads are point loads
near the bearings, so they are carried as the uniform load with the same end shear, midspan moment and
midspan deflection (the largest of the three, so each limit state is covered):

    R  = wL/2 + P          = 35.677/12 x 69.3125/2 + 325.73               = 428.77 lb
    M  = wL^2/8 + P a      = 1,785.4 + 325.73 x 7.96875                  = 4,381 lb-in (365 lb-ft)
    equivalent uniform:    shear 2R/L = 148.5 plf, moment 8M/L^2 = 87.5 plf, deflection 96.8 plf
    148.5 plf against the table's 1,582 plf at 6'-0": d/c 0.094   (`structural.rim_header`, "header")

An independent cross-check from the design values, not the table (ESR-1387 Table 1, 1.3E, joist/beam
orientation: E 1.3e6, Fb 1,700 x C_v (12/d)^0.092 = 1,701 psi, Fv 425 psi; b = 2.5", d = 11.875",
S = 58.76 in^3):

| Limit state | Demand | Capacity | d/c |
|---|---|---|---|
| Bending | 4,381 lb-in | 1,701 x 58.76 = 99,982 lb-in | 0.044 |
| Shear (end reaction) | 428.8 lb | 2/3 x 425 x 2.5 x 11.875 = 8,411 lb | 0.051 |
| Deflection | strip 0.0029" + seats 0.0068" = 0.0096" | L/240 = 0.289" | 0.033 |
| Bearing | 428.8 / (6 x 2.5) = 28.6 psi | 360 psi (TJ-8000 p.5, D7672) | 0.079 |

The same design values, as a uniform load at 6'-0": 1,852 plf in moment, 2,804 plf in shear, against
the table's **1,582**: the table is the more conservative number, so the equivalent-uniform read is on
the safe side. ForteWEB takes the vertical loads only (not the couple), so it is the closure for the
table's uniform-load condition and nothing more; its input is retained (see the top).

## 4. Fastening and seat load introduction (graded apart from the header)

- **Ply fastening**, TJ-8000 p.7 (2-ply connections), 1 1/4" plies, **top load**: 10d (0.128"-0.131" x
  3") nails in **3 rows at 12" o.c., one face**, clinched. Authored exactly that (`PlyFastening`).
- **Seat load into the ply, side load**, p.7: the same nails, 3 rows, **560 plf on either outside
  member**. The seat's reaction over its own 10" (the whole of it taken as reaching the ply):
  325.73 / (10/12) = **390.9 plf, 0.698**.
- **The couple**: 325.73 x 7.25" = 2,361.6 lb-in per seat, carried by the seat screws in
  tension and the sheathing in compression, as `exterior_door_sill_beam.md` §3 grades it: NDS 12.4.1
  combined lateral and withdrawal, **0.965** on the G 0.42 column. `structural.rim_header` reads it
  from the door's own placement record and does not redo it.

## 5. The stacked jambs, and the jamb pack down to the foundation (F-09)

**Takedown, per seat**, as before (stated 15 psf wall, 50 psf floors, the gable's roof strip over half a
24" rafter spacing; `engineering/jamb_takedown.py`): L = 63.3125 / 2 + 6.0 = 37.65625" = 3.13802 ft
and the west seat governs at **1,708.35 lb**, of which 1,171.13 lb is above `FS-S-EAST`. The header's own
end reaction is **428.77 lb** (§3), so **2,137.1 lb** goes down through the band into the host
wall's pack (it was 1,846.6 lb with the strip alone; the seats are the difference).

Bearing, NDS §3.10.2 (no C_D, C_b 1.0), SPF plates Fc-perp 425 psi, the rim's own 360 psi (TJ-8000
p.5 note 2, ASTM D7672):

| Interface | Demand | Capacity | d/c |
|---|---|---|---|
| `D-M-PORCH` pack on `W-M-S2`'s plate | 1,708.35 / (6 x 5.5) = 51.8 psi | 425 | 0.122 |
| `W-M-S2`'s plate on the rim and its ply | 1,708.35 / (6 x 2.5) = 113.9 psi | min(425, 360) | 0.316 |
| rim and ply on `W-B-S3-FR`'s plates | 2,137.1 / (6 x 2.5) = 142.5 psi | 360 | 0.396 |
| rim, concentrated vertical load under the pack (TJ-8000 p.5; **the ply behind is not credited**) | 1,708 lb | 3,760 lb | 0.454 |
| rim, vertical load under the pack (p.5) | 1,708 / 0.5 ft = 3,417 plf | 5,400 plf | **0.633** |
| the pack's 4 studs on the plate under them (F-09) | 2,137.1 / (4 x 1.5 x 5.5) = 64.8 psi | 425 (the PT sill taken at SPF's value) | 0.152 |
| `D-S-BALCONY` pack on `FS-S-EAST`'s edge rim | 1,171.13 lb: 0.311 concentrated, 2,342 plf **0.434** | 3,760 lb, 5,400 plf | |

**IRC R602.7.5** (read on UpCodes, MN 2018, 2026-11-23): headers are supported at each end by one or more
jack studs (provided: 2) and Table R602.7.5's full-height studs each end: for a header span up to 6 ft,
**2 at less than 140 mph Exposure B, 1 at 115 mph or less Exposure B** (the site is V_ult 115, Exposure B:
1; provided: 2 kings each end).

**Governs: the rim under the pack, d/c 0.633** (it was 0.434 with a 1,171 lb pack on FS-S-EAST's rim; the
rim over `D-B-SUNKEN` takes the whole 1,708 lb). It is a published table row, so it is a prescriptive
read and not a seal. Under the 0.85 cost-review trigger (decision 30).

## The rim joint (TJ-8000 p.5), open

p.5's header application: "Locate joint a minimum of 12" beyond opening". `FS-M-WEST`'s edge rim ends at
x=215.25" and `FS-M-EAST`'s begins at 216": the floors' seam at the 18' bearing line, **8.34" from the
west jamb** (224.34"), 2.34" outside the pack. The header ply stops at the floor's outline (216") too,
so nothing bridges the joint, and a floor's rim cannot be lengthened over its neighbour's.
`structural.rim_header` grades it UNKNOWN. Options: move the seam 3.7" west (the bearing line moves);
move the opening 3.7" east (the door, its RO and the PORCH packs above); or Weyerhaeuser confirms the
splice (ForteWEB models one continuous piece).

## Not graded here

Dry-use service (the band is inside the envelope; TJ-8000 p.5: dry-use only). Lateral support: the
subfloor sheathes the top edge. The ply's nails are not billed as a separate line.

## Sources

- Weyerhaeuser **TJ-8000** *Trus Joist Rim Board Specifier's Guide*, March 2025 (read 2026-11-23,
  `weyerhaeuser.com/woodproducts/document-library/tj-8000/`): p.5 header application and allowable
  vertical loads (note 2: 360 psi), p.6 1-ply and how-to-use (4 1/2" bearing, neglect header weight,
  "use ForteWEB ... for loading conditions not shown"), p.7 2-ply table and connections.
- ICC-ES **ESR-1387** Table 1 (TimberStrand 1.3E, joist/beam orientation) for the cross-check.
- IRC 2018 R602.7.5, Table R602.7.5, R301.5, Table R301.7 (MN, UpCodes).
- AWC NDS 2018 §3.10.2. `notes/exterior_door_sill_beam.md` §3 (the seat reactions).
