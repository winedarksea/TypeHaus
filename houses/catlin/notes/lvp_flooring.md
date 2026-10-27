# Quincy Oak LVP and concrete cap coordination

Provisional owner selection, 2026-10-26: **COREtec Pro Classics Quincy Oak,
VV017-01018**, click-lock floating SPC. The [manufacturer product page](https://coretecfloors.com/en-us/products/coretec-pro-classics/quincy-oak-vv017-01018)
lists nominal **7 × 48-inch planks, 5 mm total thickness including attached cork,
20 mil wear layer, UV acrylic finish and microbeveled edges**, 28.84 SF/carton.
The listed $5.69/SF material price is an allowance pending a local delivered quote;
existing floating-floor installation labor remains separate. Confirm carton quantity,
waste/cut layout, freight, tax, current stock and the physical sample before ordering.

## Appearance and installation

The model uses the mean color of the central half of COREtec's
[vv017_01018_1to1 plank image](https://shawfloors.widen.net/content/2stmgfpfwp/jpeg/vv017_01018_1to1?crop=false&fmt=jpeg&h=0&quality=85&w=840),
**#bfb6ad**. This is a pale warm gray oak photographic approximation, not a measured
reflectance or a guarantee of the delivered color. The existing low-sheen procedural
7 × 48-inch plank recipe supplies oak grain and shallow microbevels. Its grain and
six-print repeat are schematic, not the manufacturer's actual print set. Check a
sample in the house light; the goal remains the lightest white wood appearance.

Use the attached cork only: no separate acoustic mat, no extra mat charge and no
assumption that a pad compresses to zero height. COREtec's
[installation guide](https://pdmsview.shawinc.com/USFloors/COREtec-Pro/Installation/Residential-Installation-Guidelines-for-SPC-Produc)
requires a clean, dry, structurally sound subfloor, flat within 3/16 inch in 10 feet
or 1/8 inch in 6 feet, and 1/4-inch perimeter expansion for areas below 2,500 SF.
Do not lay sheet plastic over the wood subfloor. Its
[second-underlayment bulletin](https://pdmsview.shawinc.com/Technical-Bulletins/Hard-Surface/Additional-cork-under-pro-plus-enhanced)
allows residential secondary underlayment up to 3 mm when fully adhered, but reports
no significant additional acoustic benefit; that option is not selected here.
Keep floating edges free under trims and fixed cabinetry independently supported.

## Clean cap dimensions versus flooring thickness

Keep the existing flat bearing seat at −13 7/16 inches, 10-inch EPS form,
3/4-inch framed plywood and **4 3/8-inch concrete cap**. Heights are above the
main top-of-joist datum. Concrete top remains **+0.9375 inch**; Quincy Oak top is
**+0.9468504 inch**, a nominal **0.0093504-inch** difference.

With these fixed structural depths, exact nominal equality would require:

**Cap thickness = 4 3/16 inches + installed flooring thickness in inches.**

| Total LVP depth including attached pad | Nearby cap dimension | LVP relative to concrete |
| --- | ---: | ---: |
| 4 mm | 4 3/8 in | 0.0300 in lower |
| **5 mm — Quincy Oak / Whitmore White** | **4 3/8 in** | **0.0094 in higher** |
| 6 mm | 4 7/16 in | 0.0138 in lower |
| 7 mm — Cotton Oak rigid core | 4 7/16 in | 0.0256 in higher |
| 8 mm | 4 1/2 in | 0.0025 in higher |

These are calculated nominal comparisons, excluding coating thickness, not approvals
for alternate structural caps. All are within the project's nominal 1/16-inch flush
target. A cap change requires coordinating the assembly layers, concrete quantity,
reinforcement/cover, published span basis and structural review. The 4 1/2-inch option
also exceeds the current bearing-seat check's 1/4-inch cap-to-bare-plywood allowance;
a future finished-surface-aware check is needed before selecting it.

The nominal 3/4-inch plywood is another coordination assumption: measure the actual
panel and installed plank and the selected concrete coating. Set the finished edge
flush from samples and survey levels; do not specify an impractical thousandth-inch
pour tolerance or add a compressible mat to tune it. Preserve both legs of the
L-shaped material boundary and the y=13-foot movement break described in
[mixed-deck movement joint](mixed_deck_movement_joint.md). Flush finish planes still
need a floating-floor-compatible edge/movement detail.

## Alternatives retained for sampling

- [A&A Surfaces Whitmore White HD-LVR5015-0017](https://www.homedepot.com/p/310230523):
  white/light-gray wood look, 5 mm including attached underlayment, nominal 7 × 48 inches,
  20 mil wear layer. Fits the same nominal cap pairing; unselected.
- [Karndean Cotton Oak AKP-RL38](https://www.karndean.com/en-us/floors/products/cotton-oak-akp-rl38):
  chalky white/cream oak, 7 mm rigid core, 48 × 7 inches, 30 mil wear layer.
  The rigid-core product is distinct from gluedown RL38. Unselected; any substitution
  must update installed depth, stair arrivals and cap coordination together.

The generic engine-library `lvp` remains unchanged. Catlin replaces that one material
under the same tag and links its selected product; the material and main-deck height
calculation share `params/flooring.py`. Editable stair files retain coordinated
numeric literals, verified against resolved walking surfaces by tests.
