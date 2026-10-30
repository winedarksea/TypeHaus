# Order list format

`haus order houses/<name>` is a retailer's shopping list built from the placeables BOM. Like
`haus millwork` and `haus bids`, it is only a view of quantities the estimate already bills,
so running it adds nothing to the estimate.

```
haus order houses/catlin --brand IKEA                 # printed
haus order houses/catlin --brand IKEA --md out/ikea.md --csv out/ikea.csv
haus order houses/catlin                              # every brand that supplies a part
haus order houses/catlin --json
```

## Where the rows come from (`takeoff/order_list.py`)

- **Frame row.** A placed type with a `product_ref` contributes one unit per instance.
- **Part row.** Each `FurnitureType.parts` / `FixtureType.parts` entry (a `ProductPart`) is
  already keyed by product. It contributes `quantity` units per instance.
- **Linear part** (one with `length`, such as a rail or toe kick):
  - Frames on one storey that sit within 1/2" of each other form a run.
  - Each run is rounded up to whole `Product.stock_length` sticks, and the takeoff row's
    `count` is that number of sticks. `length_ft` keeps the net length.
- **Packs.** `packs = ceil(units / Product.pack_quantity)`.
- **Unit price.** Shown only where `prices.toml` `[placeables]` prices the product tag, or
  failing that the type tag (#28). Part rows are priced per unit, not per pack.

## Columns

`brand, article, name, roles, units, pack_quantity, packs, length_ft, unit_price, used_by`

`article` is `Product.sku`. `used_by` lists the instance tags that consume the item.

## Unresolved

The list reports, rather than drops, anything that would leave it short:

- **No `product_ref`.** A SEKTION-family type with no `product_ref` and no parts. This is
  found by a `sektion-*` glyph other than the cover panel, or by a name containing
  SEKTION or FÖRBÄTTRA.
- **No `sku`.** A listed product whose article number has not been read yet.

## SEKTION parts

`library/placeables/sektion_parts.sektion_parts` derives a frame's parts from the same
`front_layout` the `sektion-axstad-kitchen-*` glyphs draw. That way the bill and the drawing
cannot disagree about how many doors there are. A house supplies a `SektionHardware`, which
maps each role to its product tag. A front size that has no product raises an error at load.
The rules and hand counts are in `houses/catlin/notes/ikea_sektion_order.md`.
