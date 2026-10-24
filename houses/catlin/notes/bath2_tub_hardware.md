# Bath2 tub hardware — 2026-10-22

![Dimensioned plan and east-wall elevation](assets/bath2_tub_hardware_review.svg)

The Kohler Underscore **K-1130-W1-0** (60 × 32 rectangle, since 2026-10-22; K-5713-W1 oval
before) sits in the deck enclosure. Moen Align T393 chrome
trim replaces the Delta Trinsic filler, using Moen 4794 rough-in. The filler mounts on the
constructed deck, independently of the tub brand. Two Align YB0424CH bars sit side by side
above the tub. Bath2's plumbing fittings and bathroom accessories are chrome; genuine
stainless cabinet pulls remain stainless. Other rooms retain their existing selections.

## Location and fit

Coordinates below are house-plan inches; elevations explicitly distinguish the storey
framing datum from finished floor, which is 1½ in. above that datum.

| Item | Location / dimension |
|---|---|
| Tub and filler centerline | x = 78.49 in. |
| Tub center | y = 232.615 in.; rim x 62.49–94.49, y 202.615–262.615 |
| Filler hole line | y = 200.41 in., unchanged |
| Filler envelope center | x = 78.49, y = 203.800625 in.; faces north |
| Filler mounting plane | 22¾ in. above framing datum = 21¼ in. AFF |
| Handle holes | x = 73.49 and 83.49 in.; 10 in. centers |
| Outlet center | x = 78.49, y = 207.66 in.; 2.61 in. inside the 55 1/8 in. basin top |
| Trim envelope | 15 15/16 × 9 1/32 × 6 13/32 in. |
| Bar centers | y = 218.615 and 246.615 in.; both 54 in. AFF |
| Bar hardware | 25.34 in. overall, 24 in. mounting centers; 2.66 in. between bars |
| Loaded towel allowance | 28 in. drop, 4½ in. wall projection; bottom at 26 in. AFF |
| Towel bottom above tub rim | 4¾ in. |

The manufacturer's drawing distinguishes **7 29/32 in. overall spout reach** from
**7¼ in. to the outlet center**. The spout's overall height is 6 13/32 in.; its outlet
underside is 3 23/32 in. above the deck. These replace the old representative Delta arch.
Uncalled-out tube diameters remain visualization approximations.

The closed levers point outward and their full quarter-turn sweeps clear the center spout.
The escutcheons and 1¼ in. rough holes fit on the foot ledge, south of the shell's outer
rim. The Bask receptacle is now at the head, far from them. The foot bay also holds the end
drain and K-7272, so check the 4794 body against the overflow elbow with the parts in hand. The holes
retain the original ledge station rather than moving with the center of the new envelope.
The 4794 accepts the modeled 2¼ in. rough deck plus ½ in. finish, and includes cold-expansion
PEX adapters for the house's PEX-A supply. Its 13 gpm at 45 psi is a valve rating, not an
installed-flow prediction.

## Supports and service handoff

Four towel-bar posts use three SPF 2×6 backing blocks, all flush with the bathroom stud
face and centered at 55½ in. above the framing datum. The middle block supports the two
inner posts. Actual clear bays are y = 244.75–259.25 and 228.75–243.25 on W-M-BA2E,
and 192.75–207.25 on W-M-BA2E2. The southern post crosses the authored wall split at
y = 216 in.; both wall segments are the same continuous physical plane.

The fixing check follows that connected, coplanar continuation and reports its actual wall.
It does not borrow wood across a gap, an offset face, or the opposite staggered stud row.
Loaded-towel, backing/stud, and backing/service intersections are checked in regression tests.

Order **T393 and 4794 together**, and include an ASSE-conforming temperature-limiting device.
Moen's sheet identifies separately purchased 104465 as ASSE 1070 certified. The filler price
includes a $100–200 material allowance for this device and its fittings; that is an allowance,
not a vendor quote or an additional routed valve element.

Two flush, lift-out west-apron leaves in matching 12 mm Corian (drawn ½ in.), not hinged
metal doors. Sizes below are the leaves, with a ⅛ in. reveal on every edge. See
`bath2_tub_deck_finish.md` §3 for cutouts, retention and removal. **North, 20×15 in.**
(`FURN-M-BATH2-TUBDK-AP-N`, matching Kohler's published minimum clear service size at the
heater end; keep retainers out of that opening) reaches the Bask power supply and its
outlet on HS1 behind the head. **South, 14×14 in.** reaches the end drain, K-7272 and the 4794. The knee
walls are 2x3 at 24 in. o.c. under one top plate (IRC R602.5), so both leaves sit in whole
bays. Before closing the apron, demonstrate access to each valve nut, hose release, drain
connection, Bask plug and power supply with the actual parts installed. Hose loops and the limiting
device must remain serviceable and clear of electrical components. Final access adequacy
and template clearances require the delivered parts; the model does not represent the
rough's complete hose/manifold geometry.

The K-1130-W1 sheet publishes the 59½ × 31½ in. cutout and the 20 × 15 in. heater-end panel;
the carton template and delivered Moen trim still govern final drilling.

## Reviewer points, 2026-10-22

Checked against Kohler's sheets (K-5713-W1 rev 10-08-2026, K-1130-W1 rev 10-14-2026).

| Point | Verdict |
|---|---|
| 32" tub gives more legroom (42" vs 39-9/16") | Not against *our* tub: the K-5713-W1 oval bottom is 43 × 25⅝ in.; the 1130 is 42 × 23½. Switched anyway for a 3¾ in. narrower deck, a published cutout, a 34° backrest and 17⅛ in. of water (81 gal; 57 gal hot against the 80-gal HPWH). The deck face now sits on the shower's front-glass line. |
| Clearflo slotted overflow required | Already selected (K-7272-CP); the 1130 lists the same. |
| Service panel adjacent to the heater | Correct; the old panel and outlet were in the foot bay, 40+ in. from a head-end supply. Fixed as above. |
| Underscore with integral alcove apron | Not worth it. The heated alcove is 60 × 30 (K-1121-RW/LW); it needs end walls both ends (the south end is the open shower), a wall valve instead of the deck filler, and loses the foot ledge the glass stands on. Cheaper, not better. |

Filled with a 200 lb bather the 1130 is ~72 psf over its plan (60 for the oval). The
blocking and sister in `params/main_deck.py` stand; the engineer of record confirms.

## Orderable finishes and costs

Bath2-only chrome variants: YB0486CH hand-towel bar, YB0403CH shower-side hook, YB0408CH paper
holder, Delta Arvo 15840LF lavatory faucet, and Kohler K-7272-CP drain/overflow. The shower
retains its previously selected chrome head and Delta thermostatic trim.

Chrome describes a finish. Moen specifies zinc for the bath towel bars and hook, and zinc
posts with a stainless steel bar for the hand-towel holder. These are not solid-stainless
assemblies. Product identity lives in the catalogs; material and installation allowances
live in `prices.toml`. The tub drain remains included in the tub allowance; the Arvo remains
in the plumbing faucet allowance, so neither is billed twice.

Moen's live shop data on 2026-10-22 listed T393 at $534.84 and 4794 at $169.44; the rendered
T393 page showed $501.40. The filler material band covers both plus the limiting-device
allowance. Chrome hardware unit prices were $75.20/bar, $51.20/hand bar, $34.44/hook,
and $62.76/paper holder, before shipping and tax. Reconfirm at ordering.

## Sources and regeneration

- [Moen T393 dimensional drawing](https://assets.moen.com/shared/docs/product-specifications/t393sp.pdf)
- [Moen 4794 rough-in specification](https://assets.moen.com/shared/docs/product-specifications/4794sp.pdf)
- [Moen towel bar specification](https://assets.moen.com/shared/docs/product-specifications/yb0424sp.pdf)
- [Moen hand-towel bar specification](https://assets.moen.com/shared/docs/product-specifications/yb0486sp.pdf)
- [Kohler heated-bath installation guide](https://techcomm.kohler.com/techcomm/pdf/1196030-2.pdf)
- [Kohler K-1130-W1 specification](https://techcomm.kohler.com/techcomm/pdf/K-1130-W1_spec_US-CA_Kohler_en.pdf)
- [Chrome Arvo faucet](https://www.deltafaucet.com/bathroom/product/15840LF.html)
- [Chrome Clearflo drain](https://www.kohler.com/en/products/bathtubs/shop-bathtubs-shower-drains/clearflo-slotted-overflow-bath-drain-7272?skuId=7272-CP)

Regenerate SVG and PNG from the repository root:
`.venv/bin/python scripts/render_bath2_tub_hardware.py`.
