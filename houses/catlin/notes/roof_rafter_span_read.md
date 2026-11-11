# `RF-HOUSE` rafter span and ridge bearing — published-table read

**House:** catlin, Ramsey County, Minnesota (MN Residential Code 2020, adopting the 2018 IRC).
**Structure:** the house roof's 11-7/8" TJI 230 rafters at 24" o.c., 6:12, bearing on the beveled
ridge plate `RB-HOUSE` (TJ-4000 R14W).
**Written:** 2026-09-11; rewritten 2026-11-10 when the joists went from hung to bearing.
**Oracle for:** `structural.ridge_bearing`, and a PRESCRIPTIVE read graded by
`structural.rafter_span` through `checks/structural/published.py`, pinned by
`tests/test_snow_checks.py` and `tests/test_ridge_beam_depth.py`.

> The 19'-3" this house once quoted was an interpolation to 35 psf, and a span table is not
> interpolated (`checks/structural/snow.py`). The honest read is the row, **18'-4"**.

## 1. The span, and which span it is

| Term | Working | Value |
|---|---|---|
| Horizontal run | eave plumb cut to the ridge centreline | **17'-11 1/2"** (17.96') |
| Sloped length | the run at 6:12, x 1.118 | 20.08' |
| Spacing | resolved, not authored | **24" o.c.** |
| Profile | `ROOF` assembly | **11.875 TJI 230** |
| Flat-roof snow | Ps, ASCE 7-16 §7.3, Pg 50 at Ce/Ct/Is = 1.0 | 35 psf |
| Roof dead | the table's own basis | 15 psf |

The comparison is the HORIZONTAL projection, which is what an I-joist roof table is indexed by.
The run to the centreline overstates the clear span between bearings, so the read is conservative.

## 2. The row, read verbatim

Weyerhaeuser **TJ-4000**, July 2025, **p.13**, roof table (p.12 is cantilevers), 11-7/8" TJI 230,
40 + 15, Low: **24" 18'-4"**, 16" 22'-5"; "If your slope is 6:12 or less, use the Low slope column."

    17'-11 1/2"  <=  18'-4"        margin 4-1/2"

p.13 general notes: "Minimum bearing length of 1¾" end and 3½" intermediate, without web
stiffeners." "A support beam or wall at the high end is required. Ridge board applications do
not provide adequate support."

## 3. The high-end support: R14W

This note used to quote that last sentence as "ridge **beam** applications". That was a
mistranscription; the guide says ridge **board**. A wall at the high end is exactly what p.13
asks for, so the row applies outright. `PublishedSpan.high_end="bearing"` is the typed guard: if
the resolved seat stops agreeing, `structural.rafter_span` refuses the row.

**p.32, R14/R14W:** double-bevel bearing plate, **LSTA18 with twelve 10d (0.148" x 1½") nails**,
2⅜" minimum end distance, web stiffeners both sides at R14W only, "additional blocking may be
required for shear transfer". **p.30:** end bearing is one 8d (0.113" x 2½") each side, 1½"
minimum from the end. R7S is an intermediate-bearing detail and does not apply.

The plate is 5-1/2" wide, so each joist bears **2-3/4"** against 1-3/4".

**APA D710A 10a:** above 1/4:12 "design joist attachment to beveled plate to transfer lateral
thrust"; above 4:12 "connectors are required to resist lateral thrust". Plate attachment is "1 -
16d at 16" o.c.", with a "blocking panel, x-bridging, or 23/32" ... continuous closure". A 3-1/2"
16d barely reaches the wall plate at the 2-1/8" edge, so this house screws instead (§4).

## 4. Reaction, thrust and fasteners

    tributary  = 17.96' / 2 x 2.0' o.c.        = 17.96 ft2
    reaction   = 17.96 x (35 + 15) psf          = ~900 lb
    with the ridge's share of the unbalanced case, take    **~980 lb**

**Joist end bearing, p.6:** TJI 230 11-7/8" at 1¾": **1,060 lb** no stiffeners, **1,485 lb** with.
The row's own maximum reaction is 18.33 x 55 = 1,008 lb.

**Thrust:** with no friction, R x tan(θ) = 980 x 0.5 = **~490 lb per joist**. The strap is primary.

    LSTA18, C-C-2026 pp.290-291: (14) 0.148" x 2-1/2", 1,235 DF/SP, **1,115 SPF/HF**
    at R14's twelve nails: 1,115 x 12/14 x 1.15/1.6 = **687 lb**       d/c 0.71

**Uplift:** IRC R802.11 requires 212 lb per connection.

    H8, C-C-2026 pp.299-301: (5) 0.148" x 1-1/2" each leg, 780 DF/SP, **710 SPF/HF**    d/c 0.30

Detail 13 is "H8 attaching I-Joist to Double Top Plates". **NW-D217** (TJI Roof Joist Uplift
Connection, expires Jan 2027; cites Simpson 2024) allows H8 with 10d at **780 DF/SP, 710 SPF/HF**,
to 12:12, nailed through a web stiffener running 1" past the plate; 10d (0.148" x 3") reaches that
value, and the 1-1/2" nail row needs extra stiffener nailing. **Note 1: H2.5A, H2.5T, RT7A and
RT8A are limited to 3:12 or less, and are not to be nailed into the flange.** NW-D217 draws H8 at
a low-end seat; using it on the high-end bevel is this house's reading of a joist-to-plate row. No
manufacturer letter is sought.

**Plate to wall:** SDWS22600DB, two per 24" bay, ±1-1/4" off the centreline, staggered 8" apart.
ER-192 rev. 09/08/2026 Table 7: thread 3", HF/SPF W 187 lb/in, **W_max 495 lb** at C_D 1.0, 792 lb
at 1.6; Table 8: 1-7/16" edge, 6" end, staggered rows. At ±1-1/4" the plate is 2.875" thick, leaving
the whole thread in the 3" double top plate. 424 lb per bay, 212 lb a screw, **d/c 0.27**.

## 5. What is NOT graded here

- **Snow basis.** MN metro standard (pg 50, 35 psf roof) against the 40 psf column. Unbalanced
  snow is not part of the prescriptive basis.
- **The unbalanced lateral difference.** The strap ties opposing joists; the difference in their
  thrust under unbalanced snow is outside the row and ungraded.
- **The strap, the H8 nailing and the plate screws** are hand reads above. The check grades the
  plate's bearing, its top against the joist underside, and its continuous support.
- **The eave birdsmouth.** The row is a clear span between bearings.
- **The two TRUSSED roofs**, deferred to the fabricator (`notes/catlin_truss_engineering.md`).

## Sources

TJ-4000 July 2025 pp.6, 13, 30-32; Weyerhaeuser NW-D217; Simpson C-C-2026 pp.290-291, 299-301;
IAPMO UES ER-192 rev. 09/08/2026 Tables 7-8; APA D710A; ASCE 7-16 §7.3.
