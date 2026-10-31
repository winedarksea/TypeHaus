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
  framing and never print). Cuts closer than `--min-piece-m` (0.6 m) merge into the one with
  the most floor. There is no registration: walls stack on walls.
- **Objects.** One per building per piece, named by storey (`main`, `second`, `attic`). A shell
  inside the building's box stays in its object (a sink a hair above its floor still prints:
  the gap is under a layer); a shell outside it is its own object (`second-2`). Shells under
  `--min-island-mm3` (2) are dropped and counted; a sealed internal void is filled.
- **Plate.** The lowest piece is fused to a 1.5 mm plate, its footprint's box plus
  `--plate-margin-mm` (3).
- **Orientation.** Each upper piece is tried upright and upside down and keeps the one with less
  support: downward area steeper than 45 degrees that is not on the bed, reported in mm².
- **Files.** `house.3mf` and `furniture.3mf` are core-spec 3MF, one object and one build item
  per piece, laid out in a row; Bambu Studio auto-arranges. Plates and filament assignments are
  Bambu/Orca project features and are not written. Two runs are byte-identical.

## The policy table (`print3d/policy.py`)

| treatment | kinds | rule |
|---|---|---|
| BODY | wall, slab (room-owned), floor, ceiling, roof, stair, soffit, fascia, column, beam, countertop, slab band/platform/finish, pad | thickened up to `--min-wall-mm` (2 x nozzle) |
| DETAIL | fixtures, appliances, fixed casework, equipment, surface luminaires, trellis | thickened up to `--min-feature-mm` (nozzle) |
| TRIM | cladding trim, baseboard, door casing, window return and stool, gutter, downspout, opening lining | never thickened; dropped below a feature |
| DROP | site and landscape, footings and sub-slab, framing, connectors, every MEP run and box, flashing, sill pans, screens, clamps, solar panels, railings, door leaves and glass, suspended lights, registers, other devices | never printed |
| LOOSE | movable furniture | `furniture.3mf`, graded below |

- `--include railing,solar_panel,site` prints a dropped kind (site is room-less flatwork);
  `--exclude KIND` drops one. An unknown kind is an error: add its row.
- **Fixed vs movable** is `resolve/placeable_fixity.is_fixed`, the same rule interior trim stops
  at: casework with a work surface or hung on a wall, a fixture that needs hot water or is hung,
  and every appliance.
- **Thickening is per element, in its own frame**, one affine transform with no remeshing: a
  wall across its axis (and along it by the same absolute growth, closing the corner notch), a
  floor, ceiling or slab along z, a roof along its slope's normal, anything else along its
  thinnest axis. Past `--max-thicken` (3x) the element is dropped and listed.

## Furniture

Printed true, never thickened. A piece passes when it is a closed solid, its smallest drawn
primitive is at least `--min-feature-mm`, it stands on at least 30% of its footprint, it is no
taller than four base widths, and its support is under a quarter of its footprint. Every
rejection is listed with its first failing test. At 1:128 most chairs and tables fail on their
legs; that is expected.

## Slicer hints

0.08-0.12 mm layers. A 0.2 mm nozzle (`--nozzle 0.2`) keeps window mullions and trim that a
0.4 mm nozzle drops. Single colour by default; assign filament per object in Studio.
