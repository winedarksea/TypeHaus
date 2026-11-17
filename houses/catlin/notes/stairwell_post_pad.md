# PD-B-WELL — the stairwell post pad, hand-worked

Written 2026-11-16. `P-M-STRWELL-S` and `P-M-STRWELL-SS` (4x4 SPF, slab to main floor, now
inside `W-B-WELL`) bore on the 3 1/2" `SL-B-FLOOR` over 2" XPS with no footing. Nothing in
the IRC sizes a column on a slab-on-ground, so that would have been an engineered item. One
thickened-slab pad under both posts takes them back to a prescriptive bearing read.

## 1. Geometry

- Pad x 160..176", y 366.375..390.375" (16" x 24"), centred on the two posts
  (SS y 371.875..375.375", S y 381.374..384.874", both x ~166.2..169.7").
- Top = slab top (-9'-1 7/16"), bottom 8" below it (-9'-9 7/16"); poured with the slab
  (`cast_with=("SL-B-FLOOR",)`), same 4,000 psi interior mix. The XPS and retarder stop at
  its edge; it bears 2 1/2" down into the 4" capillary stone (1 1/2" of stone left under
  it). The resolver draws the slab and its sub-slab layers with the pad's plan cut out
  (`resolve/slab_clip.py`), so the drawing shows no stone under the pad either.
- Projection past the posts: 6 1/4" (x), 5 1/2" (y). That is within the 8" thickness
  (IRC R403.1.1: P <= T), and 8" is ACI 318-19 §14.3.1.2's minimum plain-footing thickness.
- The ABU44 cast-in bolts (AB-058-10-SS, bottom 4" below the slab underside) now land in the
  pad instead of hanging below a 3 1/2" slab.

## 2. Load takedown

Stair loads at 40 psf live (IRC R301.5) + 15 psf dead (the takedown rounds the 12 psf in
`stair_stringer_basis.md` up) = **55 psf**. Each corner share is taken as a quarter of a
half-landing plus a quarter of the flight arriving at it. That assumes the inner stringer
lands at the corner and is conservative against the two-way split.

| item | basis | lb |
|---|---|---|
| ST-B2M landing corner (post SS) | 2 halves x [(44.75/2 x 49.88/2) + (42.5/2 x 60/2)]/144 = 16.60 sf x 55 | 913 |
| ST-M2S landing post (on S) | 2 halves x [(44.81/2 x 41.50/2) + (41.06/2 x 70/2)]/144 = 16.44 sf x 55 | 904 |
| ST-M2S well partition, north end | half its inner-stringer load, 2 x (41.06/2 x 70)/144 = 19.96 sf x 55 / 2 | 549 |
| ST-M2S partition self-weight, half | 6 psf x 5.2' x 9.0' / 2 | 140 |
| ST-B2M well partition, north end | 1' of inner stringers 2 x (21.25 x 12)/144 = 3.54 sf x 55, + 6 psf x 9.2' | 250 |
| W-B-WELL over the pad | 6 psf x 1.54' x 9.2' | 85 |
| two posts | 2 x 0.0851 sf x 9.03' x 27 pcf | 42 |
| **column load P** | | **2,883** |
| pad self-weight (gross, no displaced-soil credit) | 16 x 24 x 8 in3 = 1.778 cf x 145 pcf | 258 |
| **total on soil** | | **3,141** |

Both partition ends are counted in full, though `ST-B2M`'s stands on the slab about 2" south
of the pad (y ~364.5"). Its load reaches the soil through the slab whether or not the pad
picks it up.

## 3. Bearing

    A = 16 x 24 / 144 = 2.667 sf
    q = 3,141 / 2.667 = 1,178 psf   <=   2,000 psf (IRC Table R401.4.1, GM; presumed soil)
    ratio 0.59

The site class is PRESUMED (`plan/site.py` `SoilBasis`), as for every other bearing figure
in this house.

## 4. What grades it

**Nothing in the engine grades a pad under an interior column.** `structural.deck_footing_size`
reads deck and roof posts only, and the slab had no reader before this either.
`structural.concrete_interference` passes it on the `cast_with` declaration, and
`structural.frost_depth` counts it among the bases. This note is the only sizing record.
Re-run §2 if either stair's landing or the posts move.
