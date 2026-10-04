# Simpson connector models

Known Simpson products now use simplified folded steel meshes instead of marker boxes.
The viewer, geometry IR, glTF and IFC share the same mesh. Connector categories render
black for visibility; coating suffixes retain their part numbers and share their shape.

The models preserve the published opening, height, bearing length, standoff and sheet
thickness. Seats follow the carried member's actual end, width and slope; fixed stock
parts keep their manufactured dimensions. Adjustable caps space their independent pieces
around the connected beam. Bases use the supporting concrete datum, and embedded straps
extend below their pour datum. Picking bounds follow the mesh.

Dimensions come from Simpson's
[Wood Construction Connectors catalog C-C-2026](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog).
Family tables, installation datums and the remaining contour approximations are recorded in:

- [Hangers](simpson-hanger-geometry.md): LUS, HU/HUC/HUCQ, HHUS, IUS, LSSR, LSC and THA.
- [Bases, caps and heavy angles](simpson-base-cap-geometry.md): ABU, CBSQ, PC, CCQ,
  AC/ACE, L50 and HL.
- [Ties and straps](simpson-tie-geometry.md): hurricane ties, mudsill anchors, embedded
  holdowns, tension ties, straps, stud ties and lighter angles.

The Titen HD stainless ledger anchors use the published 1/2-inch diameter, 6-inch length
and 3/4-inch wrench size from Simpson's
[anchoring catalog](https://www.strongtie.com/resources/literature/anchoring-systems-catalog)
and [THDSS product table](https://www.strongtie.com/screwanchors_mechanicalanchoringproducts/thdss_anchor/p/stainless-steel-titen-hd).
Their shaft threads are omitted and their hex-head height is illustrative.

Most nail holes, threads, welds and bend radii are omitted. Existing perforated KBS1Z
meshes remain in use and also fit standalone knee-brace ends. Generic family designations
use documented representative stock geometry, including STHD14 for an unsized STHD and
LUS210-2 for the oversized generic I-joist connections. These display selections do not
change structural part selection, allowable loads or purchase quantities. CS16 needs an
authored cut length to produce a standalone mesh; straps already resolved as framing
members retain their authored run. Unknown products keep their marker geometry.

The previously hidden THA floor-truss hangers, lateral tie plates and derived post bases
now draw at their existing joints. Derived solids retain their billing flag, so adding
the bodies does not create a second hardware order or volume-based steel charge.
Opposing hangers retain separate carried-member identities instead of merging at a
snapped ridge station. Repeated construction-detail tags select their sill run by location
and elevation. Automatically scheduled post bases now apply the existing catalog timber
inset, bringing the two stairwell posts clear of their newly visible seats; the documented
catalog standoff discrepancy for authored bases remains unchanged.

Geometry tests cover published dimensions, clear openings, positive winding, mirrored
placement, both ends of hung members, face placement and matching JSON/IR/IFC bodies.
