# Natural wood appearance

2026-10-16 · procedural 3D baseline for lightly aged indoor wood, minimally amber satin clear.
These are visual approximations, not measured reflectance or a finish-product specification.

## Species calibration

The palette is defined in `typehaus.library.wood_appearance.NATURAL_WOOD_COLORS`.
House modules marked `# haus: editable` retain literal colors because the editing dialect
requires literals; the model JSON test checks those against the library defaults.

| Species identifier | Default sRGB | Character and references |
| --- | --- | --- |
| `cherry` | `#b77d60` | [Black cherry](https://www.wood-database.com/black-cherry/): warm reddish brown; fine grain, sparse small gum-like markings. |
| `ash` | `#d9cbb0` | [White ash](https://www.wood-database.com/white-ash/): pale beige/light brown; pronounced ring figure, no conspicuous oak rays. |
| `elm` | `#bd9975` | [American elm](https://www.wood-database.com/american-elm/): light reddish brown; wavy interlocked grain. |
| `walnut` | `#80634f` | [Black walnut](https://www.wood-database.com/black-walnut/): chocolate brown, darker streaks and restrained cooler board variation. |
| `oak` | `#c4b18c` | [White oak](https://www.wood-database.com/white-oak/): muted olive-tan; coarse grain, broad quartered ray fleck. |
| `locust` | `#b9aa68` | [Black locust](https://www.wood-database.com/black-locust/): yellow-brown with a greenish cast, before mature russet aging. |
| `basswood` | `#e5dcc4` | [Basswood](https://www.wood-database.com/basswood/): pale cream, quiet straight grain and little contrast. |
| `red-oak` | `#cbaa8d` | [Red oak](https://www.wood-database.com/red-oak/): pinkish tan-brown, open grain; smaller quartered rays than white oak. |
| `sugar-maple` | `#e6d9bf` | [Sugar maple](https://www.wood-database.com/hard-maple/): creamy sapwood, fine restrained grain; no default birdseye/curl. |

The references inform species character and color relationships. Their sealed samples do
not establish an exact water-based polyurethane color, sheen, or aging interval. Display,
lighting, individual trees, and finishing preparation affect the final appearance.

## Rendering contract

- `species` remains the existing takeoff identifier; `oak` means white oak for appearance.
- `finish` still selects the board format or carries an existing construction finish note.
  `solid-board` is the neutral jointless recipe; `oak-board` remains supported.
- `wood_surface` independently selects `natural-clear` (default for supported species),
  `unfinished`, or `painted`. Painted wood keeps joints but loses wood-color variation.
- The sauna liner and locust trim remain unfinished. Hardwax-oil construction notes remain
  intact; the natural-clear rendering baseline does not revise their finish specifications.
- Species profiles control growth-ring spacing, pores, rays, interlock, color spread, and
  sparse markings. Fine rings and fibers are filtered to texture resolution; broad ring
  groups preserve the visible figure without aliasing unresolved annual rings. Most boards are plainsawn, with some straight/quartered stock and
  restrained sapwood. Dimensions are metres. Figure and board selection are deterministic.
- Albedo textures carry full color with a white material tint. `woodBaseColor` in material
  user data retains the authored sRGB hex for diagnostics. Without canvas, rendering uses
  the authored flat color. Schematic mode stays flat.
- Solid pieces have separate face/end groups. Crosscuts use a square cross-section atlas;
  side faces follow physical grain direction. Continuous tiles blend at their longitudinal
  wrap. Four broad lanes accommodate the house's shelves and slab widths.
- Satin clear uses roughness 0.48, unfinished 0.88, and painted 0.62, with restrained pore
  variation. These are renderer settings, not gloss-meter measurements. Wood is dielectric.
- GLB carries the same base colors, converted from sRGB to linear `baseColorFactor`.
  Exported GLB does not include procedural textures. LVP and unspecified woods retain
  their existing rendering path.

## Reproduce the review

From the repository root:

```sh
node ui/scripts/wood-review.mjs
.venv/bin/haus build houses/catlin --only json
node ui/scripts/wood-review.mjs --house
```

The harness uses the existing Chromium/CDP tools and its own local Vite server. It runs
real-canvas assertions and writes overview, distance, detail, and optional Catlin images
plus diagnostic JSON into `out/wood-review/`. A failed browser assertion fails the command.
The review HTML is a development entry, excluded from the production application's build.

- [Before overview](../out/wood-review/before-overview.png)
- [After overview](../out/wood-review/after-overview.png)
- [After detail](../out/wood-review/after-detail.png)
- [After distance](../out/wood-review/after-distance.png)
- [Catlin objects](../out/wood-review/after-catlin.png)
- [Catlin suite at room scale](../out/wood-review/after-suite.png)

`--before` recreates the former generic streak/oak maps and old colors for comparison;
red oak and maple use placeholder colors because neither previously had a species profile.
The initial before screenshots were captured before the renderer changes. The recreated
comparison shares the corrected solid-piece geometry, rather than restoring old UV bugs.

The Catlin card uses actual resolved cherry casing, ash table, elm post, walnut
countertop, oak tread, basswood ceiling, locust base, and painted oak shiplap through the
production builders. A separate suite cutaway shows the oak floor, painted MDF/poplar headboard, painted base, cherry door casing,
and elm posts at their full-size relative positions. Card objects are uniformly fitted, so their on-screen sizes differ
from room-scale use. Browser checks verify species, finish, selection, and solid atlas lanes.
