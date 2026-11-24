# ForteWEB input — D-B-SUNKEN 2-ply LSL rim header (retained evidence, decision 12)

**Status: ForteWEB report: owner to run and retain.** This file is the exact input. The engine
could not run ForteWEB, so no report exists yet; when one does, save it beside this file as
`forteweb_D-B-SUNKEN_report.pdf` and note its date and program version below. The hand calc
that stands in for it until then is `notes/sunken_door_band_header.md` §3-§4; the arithmetic is
`scratch/L3/hand.py`. Weyerhaeuser's own rule for loads the rim-board table does not show
(TJ-8000 p.6): "use ForteWEB software or contact your Weyerhaeuser representative".

## Member

| Field | Entry |
|---|---|
| Product | TimberStrand LSL rim board, 1 1/4" 1.3E (ICC-ES ESR-1387) |
| Depth | 11 7/8" |
| Plies | 2 (the floor's edge rim `FS-M-EAST` `edge-rim-0-000-0` and one ply of the same stock behind it, `params/main_deck.py`) |
| Ply connection | 10d (0.128"-0.131" x 3"), 3 rows, 12" o.c., one face, clinched (TJ-8000 p.7, top load) |
| Application | Floor header, dry use, simple span, load duration 100% (floor) |
| Lateral support | top edge sheathed by the subfloor |

## Supports

Two bearings, each the 4-stud jamb pack of `D-B-SUNKEN` (2 kings + 2 jacks, 4 x 1 1/2" = 6")
on the `W-B-S3-FR` top plates (SPF).

| Field | Entry |
|---|---|
| Rough opening (clear span) | 63 5/16" = 5.276 ft |
| Bearing length, each end | 6" (TJ-8000 p.6 minimum 4 1/2"; plies extend 6" past the opening) |
| Span, centre to centre of bearing | 63.3125 + 6 = 69.3125" = **5.776 ft** |
| Bearing, each end | the member's first and last 6": supports centred at 3.00" and 72.3125" from the left end (x 221.34" and 290.66") |

## Loads (IRC R301.5, Table R301.7; TJ-8000 p.6: neglect the header's own weight)

Positions are measured **from the member's left end** (the west end, the outer face of the west
jamb pack, x = 218.34"); the member is 75.3125" long, bearing 0"-6" and 69.3125"-75.3125".

Floor strip = 1.125" (rim line to the outer edge) + 14.875"/2 (half-way to the next joist line
at y = 16") = 8.5625" = **0.71354 ft**.

| Load | Case | Entry | Basis |
|---|---|---|---|
| Uniform, full span | Dead | **7.135 plf** (10 psf x 0.71354 ft) | R301.5 floor dead |
| Uniform, full span | Live (floor) | **28.542 plf** (40 psf x 0.71354 ft) | R301.5 |
| Point, west seat | Live | **325.73 lb** at **10.97" from the left end** (6.00" bearing + 4.97" to the screw group's centroid; x = 229.31") | `D-M-PORCH` sill beam seat reaction, `notes/exterior_door_sill_beam.md` §3 (worst reaction, PyNite spring model) |
| Point, east seat | Live | **325.73 lb** at **64.34" from the left end** (x = 282.69") | same; both seats at their worst at once (conservative: one 300 lb load gives 325.73 and about -26 lb) |

**Seat loads are SIDE loads on the outer ply**, the 1 1/4" rim (the ply on the exterior face);
they are not top loads. The seat's HeadLOK screws bear on the rim's outer face and into the
backing ply behind it, so enter each as a side-applied (face) load on ply 1 and not as a load on
the member's top. **The dead/live split of the seat loads is conservatively all live**: the sill
beam's 300 lb is an approach live load, and no dead component is separated out.

Deflection limits: L/360 live, L/240 total (IRC Table R301.7; the table's own basis).

## What ForteWEB cannot take, and where it is graded instead

**Torsional restraint assumption at the bearings.** Each seat's couple is 325.73 lb x 7.25" =
**2,362 lb-in** (2,361.6), two of them. ForteWEB takes no torsion, so the run assumes the header
is restrained against rolling at both bearings (the wall plates under it, and the subfloor
nailed to its top edge), and that the couple is self-equilibrated in the seat (screw tension
against the sheathing's bearing, `exterior_door_sill_beam.md` §3) before it reaches the header.
Whatever residual rolling reaches the header is resisted at the bearings by the plates and the
subfloor sheathing. This is an assumption the run cannot test; Weyerhaeuser can confirm it.

The seat reactions act **7.25" outboard of the rim's face** (0.5" sheathing + 6.0" seat +
0.75"), so each is a vertical load plus a couple (2,361.6 lb-in at 325.73 lb). ForteWEB takes
the vertical load only. Graded separately in `structural.rim_header` and the note §5: the
couple as the seat screws' combined lateral and withdrawal (0.965, NDS 12.4.1), the seat load
into the ply's nailing (390.9 of 560 plf side load, TJ-8000 p.7), the jamb bearing from the
band to the foundation, and the stacked jamb load, which lands on the bearings and not in the
span (`D-M-PORCH` stands on the same RO and centre).

## Hand values the run should agree with (the report may be more or less conservative)

End reaction **428.8 lb** each (R = wL/2 + P, w = 35.68 plf), midspan moment **4,381 lb-in**
(365 lb-ft), against 99,982 lb-in (ESR-1387 Table 1: Fb 1,700 psi, C_v 1.0010, S = 58.76 in³)
and 8,411 lb in shear; bearing 28.6 psi on 6" x 2.5". The published table row
(TJ-8000 p.7, 6'-0", 1 1/4" 11 7/8"): **1,582 plf** total; the loads above are
**148.5 plf** as the equivalent uniform. Deflection about 0.010" against L/240 = 0.289".

## Run record

| Date | Operator | ForteWEB version | Result | File |
|---|---|---|---|---|
| (owner to run) | | | | |
