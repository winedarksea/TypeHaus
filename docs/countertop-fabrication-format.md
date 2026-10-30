# Countertop fabrication package (`haus countertops`)

```
haus countertops houses/<name> [--material <tag>] [--out out/countertops] [--json]
```

One folder per material, `out/countertops/<material>/`:

| file | what |
|---|---|
| `<TAG>.dxf` | one piece, inches (`INSUNITS=1`), true arcs |
| `shop-drawings.pdf` | cover (material block, piece schedule) + one page per piece |
| `pieces.csv`, `pieces.md` | the piece list; the Markdown adds the material block and holds |

**Scope** is the takeoff's (`takeoff/countertops.countertop_stools`): every `Countertop`,
plus each `WindowStool` cut from a countertop material. A material with
`requires_custom_milling` goes to `haus millwork` instead. Gross area stays square-cornered.

**Piece frame.** Counter-clockwise, the longest finished edge along +x at y = 0, origin at
the bounding-box minimum. Cutout and hole centres are located from the left end (x) and the
front edge (y).

## DXF layers

| layer | entity |
|---|---|
| `CUT` | the closed outline, one `LWPOLYLINE`, fillets as bulges; uid/tag XDATA (`TYPEHAUS`) |
| `CUTOUT` | fixture openings (schematic: cut to the delivered template) |
| `HOLE` | drilled holes, `CIRCLE` |
| `EDGE-FINISHED`, `EDGE-WALL`, `EDGE-SEAM`, `EDGE-ABUTMENT` | each edge's straight run |
| `DIMS`, `TEXT` | overall and centre dimensions; tag, material, profile, R callouts |

## Edge kinds (`resolve/countertop_edges.py`)

A strip 1/16"–1/2" outside each edge is tested against, in order: wall layers standing at the
top's height (`wall`), another slab (`seam`), a placeable rising more than 6" above the top
(`abutment`: a tall pantry, a fridge; a slide-in range is not one), else `finished`. An edge
is split where its kind changes; a run under 1" joins its neighbour and the edge is reported
mixed.

**Radii** (opt-in: a piece with no `corner_radius` stays square). A convex corner between
two finished edges takes `Countertop.corner_radius` / `WindowStool.corner_radius`; a concave
corner takes `Material.inside_corner_radius_in` (default 3/8"); every other corner is square. Fillets that share an edge split it in
proportion; one that cannot fit is clamped and graded. The viewer, GLB and IFC draw the same
fillets (`resolve/fillet.py`).

## Holds

Every piece: field template after cabinets are set. Each cutout: cut to the delivered
fixture's template. An appliance hung under a cutout (a disposer): its deck button is
located from its own template. Any opening: the narrowest web is dimensioned, and the
fabricator's minimum web governs. A cantilever names its support and the members under it.

## Check

`advisory.countertop_fabrication` FAILs a piece whose bounding box exceeds the material's
`slab_size_in` both ways (seam it or order a jumbo slab) or whose radius was clamped; a mixed
edge or a missing slab size is UNKNOWN. N/A with no fabricated pieces. A hole outside its
slab is a load error (`integrity.countertop_cutout`).
