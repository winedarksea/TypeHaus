# Review exports — the SVG, PNG and PSD `haus render` writes

`haus render` is the look-at-it loop, and its three raster/vector formats now share one
thing: a **review-layer stack**, defined once in `emit/draw/review_layers.py`.

```
haus render houses/catlin --view plan --fmt png        # 4096 px on the longest edge
haus render houses/catlin --view plan --fmt svg        # named layers, for a vector editor
haus render houses/catlin --view plan --fmt psd        # raster layers, for Procreate
haus render houses/catlin --view plan --long-edge 1200 # smaller, for a quick look
haus render houses/catlin --view plan --dpi 300        # size by resolution instead
haus render houses/catlin --view section --slice SL-S-FIRE   # a house-AUTHORED section cut
haus render houses/catlin --view section --slice all         # every authored section
```

`--slice` is section-only, and it is what reaches a cut the house authored rather than the
derived house-centre one. Without a tag `--view section` draws the centre cut, exactly as it
always did. An authored slice comes out ANNOTATED — the same datums, ground line and room
names `haus print`'s A-301 carries, through the one `build_annotated_section` both use — with
one difference the crop is responsible for: the room names and the detail callouts are clipped
to the slice's own window, because they walk the model rather than the drawing and would
otherwise letter rooms and hang bubbles outside the frame. A DETAIL is deliberately not
reachable this way: details are their own view (`--view details`), cut with a joint plan and
their own paper, and routing one through the section path would draw it without either.

## The stack

Bottom to top. An AIA layer name says which *trade* drew a line; this says which **group a
reviewer would switch off**, and the mapping is `review_layers.layer_for`.

| # | Layer | Holds |
|---|---|---|
| 1 | Background | the white ground, the caption, a sheet's border and title block |
| 2 | Reference Underlay | the `preferences.toml` survey rasters |
| 3 | Site / Context | `C-*`, `L-*`, `A-SITE-*` |
| 4 | Building Shell | `A-WALL*`, `A-ROOF*`, `A-SLAB`, `A-FLOR-OPEN` |
| 5 | Structure | `S-*` |
| 6 | Openings | `A-DOOR`, `A-GLAZ*`, `S-FRAM-OPEN` |
| 7 | Stairs / Rails | `A-STAIR`, `A-RAIL` |
| 8 | Building Services | `P-*`, `M-*`, `E-*`, `A-FLR-HEAT` |
| 9 | Fixtures / Equipment | `A-FIXT`, `M-EQPT`, `M-HVAC-EQPM` |
| 10 | Furniture | `A-FURN` |
| 11 | Rooms | `A-AREA-IDEN` — room identification graphics, not wall geometry |
| 12 | Dimensions | `A-ANNO-DIMS` |
| 13 | Notes / Symbols | `A-ANNO-*`, `A-DETL-*`, `C-ANNO-*`, `A-SITE-ANNO` |
| 14 | Other | anything unmapped — visible, never dropped |
| 15 | Review Markup | empty; the sheet a reviewer draws on (PSD only) |

Background and Review Markup carry no drawing node and appear in the PSD only. A test
asserts every layer the writer has a pen for lands somewhere other than `Other`.

## One stacking order, three readers

`ArtistTagger` stamps each matplotlib artist with `gid="th-<slug>-<n>"` **and bands its
z-order into the layer's slot** (`order * 100 + the writer's own z`). So matplotlib draws in
review order; the SVG comes out already sorted, which is why grouping it is a re-parenting
and not a restack; and the PSD's per-layer passes composite back to the PNG.

**`haus print` is deliberately excluded.** Banding re-orders, and re-ordering the submittal
deliverable as a side effect of a review feature is not on — a high-layer fill would start
covering a low-layer line on a sheet a plan checker has already read. The permit set renders
through a `NullTagger` and is byte-for-byte what it was.

## SVG

Groups carry `id`, `data-typehaus-layer`, and Inkscape's `groupmode`/`label`, so Inkscape
shows them as layers and every other editor at least gets a named, selectable group. Text
stays outlined and patterns stay as they were; nothing is fetched from the network.

## PNG

Sized by `--long-edge` (default 4096) or by `--dpi`, never both — one names a pixel count,
the other a physical resolution. The default moved off dpi because a frameless snapshot's
inch size falls out of how much there happened to be to draw, so a dpi alone names no pixel
count a reader can rely on.

## PSD

8-bit RGB, RLE-compressed, one layer per non-empty review layer, cropped to its own ink (a
PSD layer carries an offset) with the Background and Review Markup full-canvas.

- **Open it from the Procreate Gallery.** Inserting a PSD into an existing canvas flattens
  it. ([Procreate import docs](https://help.procreate.com/articles/zyjjpk-importing-images))
- 4096 px balances legibility under a pencil against Procreate's hardware-dependent
  [canvas](https://help.procreate.com/articles/dabqrn-maximum-canvas-size) and
  [layer](https://help.procreate.com/articles/YB7CjQ-maximum-layer-limit) limits.
- **Layers ship unlocked.** psd-tools exposes no layer-protection API, and a lock
  hand-patched into the record structures breaks quietly on the next release — worse than no
  lock, because a reviewer would trust it.
- The composite is the PNG to within antialiasing: each layer is rasterized against
  transparency and blended afterwards, so an edge where two layers' ink overlaps is
  composited twice instead of drawn once. Measured on catlin's main plan: max channel
  difference 9, mean 0.02, no pixel off by more than 9.

A PSD is ~8 s and ~50 MB per plan at 4096 px — it renders one pass per layer. Use `--fmt
png` for the edit→check→look loop and `--fmt psd` when you actually want to mark it up.
