# Window drywall returns

Implemented 2026-10-20. Windows with exposed interior gypsum receive square jamb and head
returns. The finish comes from the resolved wall, including room lining exceptions: board
material, each board's thickness, and the authored paint layers. Cedar sauna and PVC plant-room
liners do not receive gypsum returns.

The return meets the actual modeled frame's interior face. Its jambs start at the stool top;
no bottom drywall is added. A fabricated stone stool (quartz or Corian, a radiused front) is
the exception since 2026-10-30: it is templated after the returns, its shoulder notches
wrap the finished return corner, and the jamb board and its bead run past it to the stool's
underside. The two garage windows have no stool, so their jambs start at the
lower frame rail. Reversing a wall axis preserves the physical geometry. The head follows the
frame's clipped height under a raked wall; arched heads and finish stacks that cannot fit
produce an explicit resolve finding.

Paint wraps the narrow room-facing board ends as well as the reveal. This keeps the accent
wall's opening green instead of leaving an exposed white gypsum border. Coatings retain their
stated thickness in the live viewer, GLB, and IFC. The IFC coverings carry material references
and the host window tag.

An individual window can opt out by authoring `drywall_returns=False` on its `Window`.

## Quantities

Catlin currently has 36 return sets. The five windows with cedar or PVC interiors are excluded.
The installed quantities are approximately:

| Material | Quantity |
| --- | ---: |
| 5/8-inch gypsum board | 116.7 square feet |
| Standard interior paint, including front edges | 125.4 square feet |
| Accent interior paint, including front edges | 4.5 square feet |
| 3/4" bullnose corner bead, two jambs and head | 274.7 linear feet |
| Frame termination bead, two jambs and head | 274.7 linear feet |

Board and paint appear in `envelope_layers`, scope `window return`. Board area includes cut
head laps; paint counts exposed surfaces. Bare gypsum receives the existing derived-paint
allowance only where it faces an occupied room. Geometry adds no second structural-volume
charge. Board is measured by area, consistent with the existing wall finish takeoff; this is
not a sheet cutting optimization.

Beads appear in `drywall_trims` (kinds `window_corner` / `window_frame`), the estimate/CSV,
and the drywall bid package, since 2026-10-30 (decision #103) on `DRYWALL-STANDARD`'s parts
(`plan/drywall.py`): vinyl bullnose bead (Trim-Tex 7010, 3/4" radius) on the return edge
since 2026-10-30, tear-away L-bead at the frame,
priced per installed linear foot under `[drywall_trims]`, with the stock pieces each
return takes. Bead profiles are not separate 3D meshes.

**Bullnose, 2026-10-30 (owner).** Every return corner takes the bullnose, the look expected
at the wood stools, so stone and wood windows match. The three quartz and one Corian stools
on gypsum returns (`WIN-M-KITCH`, `-KITCH-N`, `-KIT-E`, `WIN-M-BATH2`) notch at the bead's
3/4" (`DrywallStandard.window_corner_radius`), above quartz's 3/8" and Corian's 1/2"
minimums, so the stone seats on the bead with no gap. A relieved notch against a square
bead was the fallback for quartz; it was not needed. The plant room's four Corian stools
have PVC liners, no return, and keep their 1/2" notch at the rough opening.

A browser review of the production 3D builders covers an ordinary oak-stool window, the accent
window, a quartz-stool window, and a garage window; its local artifact is
`out/window-return-review.png`.
