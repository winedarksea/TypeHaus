# 3D print export

`haus print3d houses/<name>` writes the house as a ready-to-print file set for a desktop FDM
printer (sized for a Bambu A1, 256 x 256 x 256 mm): the house cut at grade and fused to a thin
plate, each storey above it a lift-off piece, and movable furniture in a file of its own.
It needs the `print3d` extra (`pip install 'typehaus[print3d]'`, manifold3d) and sits outside
`haus check` and the standard gate (decision #106).

```
haus print3d houses/catlin                       # out/print3d/house.3mf, furniture.3mf, report.md
haus print3d houses/catlin --timing --stl        # stage timings; one STL per piece too
haus print3d houses/catlin --nozzle 0.2          # halves both minimums
haus print3d houses/catlin --scale 150           # print at 1:150, or refuse and name the largest
haus print3d houses/catlin --include railing,site --exclude plant --no-furniture
```

## What comes out

- **Scale.** The largest standard architect's scale at which every piece fits the bed less
  `--margin-mm` (default 4): 1:96 (1/8" = 1'-0"), 1:100, 1:128 (3/32" = 1'-0"), 1:150,
  1:192 (1/16" = 1'-0"), 1:200. A scale rule then measures the print. Catlin lands on 1:128.
- **Pieces.** Cut at grade and at the underside of each storey's floor package, so every
  upper piece stands on its own ceiling plane and lifting one off shows the rooms below. A
  floor prints as its whole package, solid from its joists' underside to its deck (joists are
  framing and never print), with the ceiling under it fused on (see MERGE below), so the cut
  falls at the ceiling's face. Cuts closer than `--min-piece-m` (0.6 m) merge into the one with
  the most floor. There is no registration: walls stack on walls.
- **Objects.** One per building per piece, named by storey (`main`, `second`, `attic`). A shell
  inside the building's box stays in its object (a sink a hair above its floor still prints:
  the gap is under a layer); a shell outside it is its own object (`second-2`). Shells under
  `--min-island-mm3` (2) are dropped and counted; a sealed internal void is filled.
- **Plate.** The lowest piece is fused to a 1.5 mm plate, its footprint's box plus
  `--plate-margin-mm` (3).
- **Orientation.** Each upper piece is tried upright and upside down and keeps the one with less
  support: downward area steeper than 45 degrees that is not within the first layer
  (0.2 mm) of the bed, reported in mm².
- **Files.** `house.3mf` and `furniture.3mf` are core-spec 3MF, one object and one build item
  per piece, laid out in a row; Bambu Studio auto-arranges. Plates and filament assignments are
  Bambu/Orca project features and are not written. Two runs are byte-identical.

## The policy table (`print3d/policy.py`)

| treatment | kinds | rule |
|---|---|---|
| BODY | wall, slab (room-owned), floor, ceiling, roof, stair, soffit, fascia, column, beam, countertop, slab band/platform/finish, pad | thickened up to `--min-wall-mm` (2 x nozzle), unless merged |
| DETAIL | fixtures, appliances, fixed casework, equipment, surface luminaires, trellis | thickened up to `--min-feature-mm` (nozzle) |
| TRIM | cladding trim, baseboard, door casing, window return and stool, gutter, opening lining | never thickened; dropped below a feature |
| DROP | site and landscape, downspouts (they stand off the wall on unmodelled brackets), footings and sub-slab, framing, connectors, every MEP run and box, flashing, sill pans, screens, clamps, solar panels, railings, door leaves and glass, suspended lights, registers, other devices | never printed |
| LOOSE | movable furniture | `furniture.3mf`, graded below |

- **MERGE into host** (`print3d/merge.py`), before any thickening. A countertop fuses to the
  largest base in its own `hosts` (a loose end panel or cover in that run comes along); a
  ceiling to the floor or slab package whose underside its top touches, by most plan overlap;
  a loose placeable to its `host_fixture_ref` fixture or `attachment_wall` wall (towel bars,
  paper holders, curtain tracks). A merged part thinner than its minimum grows toward its
  host to it, exposed face fixed, with no `--max-thicken` cap: the growth is inside the host.
  The merged item takes the host's kind and treatment. A part with no host (catlin's garage
  ceiling, under trusses) falls back to its own row. The report's "merged into host" column
  counts them.
- `--include railing,solar_panel,site` prints a dropped kind (site is room-less flatwork);
  `--exclude KIND` drops one. A kind with no row, in the model or in either flag, is an
  error: add its row.
- **Fixed vs movable** is `resolve/placeable_fixity.is_fixed`, the same rule interior trim stops
  at: casework with a work surface or hung on a wall, a fixture that needs hot water or is hung,
  and every appliance.
- **Thickening is per element, in its own frame**, one affine transform with no remeshing: a
  wall across its axis (and along it by the same absolute growth, closing the corner notch), a
  floor, ceiling or slab along z, a roof along its slope's normal, anything else along its
  thinnest axis. Past `--max-thicken` (3x) the element is dropped and listed.

## Furniture

Printed true, with one exception: a flat plate thinner than `--min-feature-mm` that rests on
another of the piece's primitives (a tabletop on its legs) or hangs from one (an apron) grows
to that minimum toward it, top or bottom face fixed (`print3d/plates.py`). A vertical thin
panel is not grown. A piece passes when it is a closed solid, its smallest drawn primitive is
at least `--min-feature-mm`, and, upright or else upside down (a table on its top), it stands
on at least 30% of its footprint, is no taller than four base widths, and needs support under
a quarter of its footprint. Every rejection is listed with its first failing test. At 1:128
catlin prints 30 of 82 pieces; most chairs still fail on their legs, which is expected.

## Slicer hints

0.08-0.12 mm layers. A 0.2 mm nozzle (`--nozzle 0.2`) keeps window mullions and trim that a
0.4 mm nozzle drops. Single colour by default; assign filament per object in Studio.
