// The chosen product, printed identically wherever a selection has one — an appliance in
// the canvas inspector, a door or window on its opening, a material behind a member or a
// trim solid. Before this the answer lived in prose inside a type's `name` ("LG WashTower
// WKHC252HBA (washer + heat-pump dryer)"), which is not something a panel can lay out and
// not something an estimator can join against; the engine carries brand and model as data
// now (model/product.py), and this is the one renderer for it.
//
// Deliberately NOT a card or a section: a product is three more facts about the thing
// already selected, so it lands as `.kv` rows in the block that is already open.
import { Fragment } from "react";
import type { ProductSpec } from "../model/types";

/**
 * Brand / Model / Product / SKU / Spec sheet rows for a resolved product, as bare `.kv`
 * siblings — never wrapped in a row div, which is what `.kv`'s two-column grid requires.
 *
 * Renders nothing at all when there is no product — an unchosen product is the ordinary
 * state of most of a house, and an empty "Brand —" row would read as a gap in the data
 * rather than as a specification nobody has narrowed yet. Each row likewise drops out when
 * its own field is empty: a brand chosen without a model is a real, honest state.
 *
 * The url is an `<a>`, not a `.badge`: a badge in this panel means "navigate to another
 * view of this model", and a manufacturer's page is neither.
 */
export function ProductRows({ product }: { product: ProductSpec | null }) {
  if (!product) return null;
  return <Fragment>
    <span className="k">Brand</span><span>{product.brand}</span>
    {product.model && <>
      <span className="k">Model</span><span className="prov">{product.model}</span>
    </>}
    {product.name && <>
      <span className="k">Product</span><span>{product.name}</span>
    </>}
    {product.sku && <>
      <span className="k">SKU</span><span className="prov">{product.sku}</span>
    </>}
    {product.url && <>
      <span className="k">Spec sheet</span>
      <span><a href={product.url} target="_blank" rel="noreferrer">{product.brand} product page</a></span>
    </>}
  </Fragment>;
}
