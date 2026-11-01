# Provisional bedroom carpet and cushion

Owner selection, 2026-10-23. Goals: decent comfort, durability and cost effectiveness.
Applies to `RM-M-BED`, `RM-M-CLOSET`, and `RM-S-BED1/2/3`, which share
`catlin-carpet-raised`. The theater and basement stair retain their existing carpet/pad.

## Selected products and shopping guidance

| Item | Provisional selection | Published details |
| --- | --- | --- |
| Carpet | [STAINMASTER PetProtect Sweet Spot I, Romano](https://www.lowes.com/pd/5013298681), model **7L89100101** | Textured nylon, 48.8 oz/yd² **face weight**, 0.56-in pile height, 12-ft roll; twist unverified |
| Cushion | [Future Foam 150553488-32](https://www.homedepot.com/p/203393647) | Rebond, **8 lb/ft³ density**, **3/8-in thickness** (owner 2026-11-01; was the 7/16-in -33) |

Use **warm ivory/cream** as the color direction, pending a Romano sample in the house.
**Light warm greige** is the alternative to consider. The material's `#e5dccb` is an
approximate presentation color, not a measured sample match; retain `carpet-pile` rendering.

Favor nylon texture cut pile without a very tall pile. Approximately **35–60 oz/yd²
face weight**, preferably **0.4–0.6-in pile height**, and roughly **5–6+ turns/in** are
shopping guidelines, not hard pass/fail specifications. Sweet Spot I fits the face-weight
and pile-height preferences; no twist value is inferred. Assess comfort and construction
from the actual sample rather than treating face weight alone as proof of durability.

The linked Sweet Spot II has 58.5 oz/yd² face weight and 0.64-in pile; Sweet Spot I is
the shorter-pile starting point. Shaw Open III's listed 0.76-in pile is less aligned with
the height preference. Akita remains an example, without verified pile dimensions or a
current quote. Research references:

- [Sweet Spot II, Whitewashed Oak](https://www.lowes.com/pd/5013371643)
- [Shaw Open III, Soft Chamois specifications](https://stoneandtileshoppe.com/products/anso-open-iii-s-00103-soft-chamois-textured-nylon-carpet)
- [DH Floors Akita](https://www.dixie-home.com/products/dh-floors-akita)

## Budget and ordering

Carry **$3–4/ft² carpet material**, **$0.35–1/ft² cushion material**, and the existing
**$1–2.25/ft² carpet installation** allowance in `prices.toml`. Cushion labor is zero on
its own row because installation is already included once in carpet labor. These are
planning allowances, not bids; tax, delivery and any required preparation need a quote.
The displayed Lowe's **$2.84/ft²** promotion referenced an expired end date when reviewed;
it is research context only, not a current quote.

`catlin-bedroom-carpet-pad` bills only under the bedroom finish. The existing `carpet-pad`
remains separate. The model's area-plus-waste takeoff is an estimate, not a cutting plan:
obtain a roll/seam layout, verify roll width and cut lengths, and quote the actual order.

## Installed height and the doorways (owner, 2026-11-01)

No plywood. The model carries the carpet at **1.000 in over the subfloor**: 0.56-in published
pile + a **1/16-in backing allowance** (unpublished) + the 3/8-in cushion. That is 1/4 in over
the 3/4-in oak and tile at `D-S-BED1/2/3` and `D-M-BATH2`.

The owner's rule: take the 3/8-in cushion if it lets those doorways go without a transition
product. Both cushions were computed against the doorway check (`integrity.doorway_assembly`,
1 mm on every contact plane):

| | 3/8-in cushion | 7/16-in cushion |
| --- | ---: | ---: |
| carpet + backing alone (cushion stops at the bar) | 0.625 in | 0.625 in |
| field over the subfloor | 1.000 in | 1.0625 in |
| field over the oak/tile | **0.250 in** | 0.3125 in |

At a Z-bar the cushion is cut back and the 0.625-in carpet is tucked against the 3/4-in hard
floor, so the edge lands on the oak/tile plane with either cushion. What differs is the step
the carpet itself makes up to its field. 3/8 in stays within the 1/4 in that ICC A117.1 §303.2
lets stand as a vertical change with no edge treatment. 7/16 in stands 1/16 in past it and
would want a bevelled reducer. So: **3/8-in cushion, a Z-bar at each carpet-to-hard doorway,
no reducer** (`plan/doorway_transitions.py`, `BEDROOM_ZBAR`). It holds while the measured
backing is 0.10 in or less (0.185 in + backing ≤ 1/4 in + 1 mm).

`D-M-BED2` meets the hall LVP 0.80315 in below and takes a product either way: a 5/4 oak saddle
on the subfloor, top on the carpet plane under the leaf.

Measure the sample's backing and the compressed edge at a Z-bar mock-up before ordering; a
thicker backing re-opens the 1/4-in step, and the fix is a reducer, not plywood.

The 3/8-in pad still needs the carpet maker's acceptance. CRI's [general cushion guidance](https://carpet-rug.org/carpet-for-homes/selecting-the-right-carpet/)
does not replace the selected carpet maker's installation and warranty requirements.

## Before purchase and construction

- View a Romano sample beside the adjacent oak, tile and wall finishes; confirm warm cream
  appearance and comfort. Compare light warm greige if the sample does not suit the room.
- Obtain a current local quote, availability and delivery information, plus a roll/seam
  layout. Retain the selected model and color on the quote.
- Verify the exact cushion's acceptance, required certification and warranty conditions
  with the carpet supplier/installer. File the applicable installation and warranty
  documents; do not assume a branded pad warranty extension applies to Future Foam.
- Measure the backing and a Z-bar mock-up edge before ordering (see above).
