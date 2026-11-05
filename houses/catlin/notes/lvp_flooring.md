# Cotton Oak LVP: the whole main floor

Owner selection, 2026-11-01 (replaces Quincy Oak): **Karndean Art Select Rigid Core Cotton
Oak, AKP-RL38**, click-lock floating, laid directly on the 3/4" plywood subfloor across the
whole main floor. No tile medallions this pass. Context: decision #112 replaced the concrete
deck `SL-M-DECK` with wood floor trusses (`FS-M-NE`), so there is no cap, no wood/concrete
boundary and no movement joint (`mixed_deck_movement_joint.md` is retired).

## Published spec (read 2026-11-01)

From the [product page](https://www.karndean.com/en-us/floors/products/cotton-oak-akp-rl38):
**48 x 7 in. plank, 7.0 mm total thickness, 30 mil wear layer, bevelled edge, rigid core,
23.51 SF/box.** The page does not say whether the 7.0 mm includes an attached pad. The
[2026 brochure](https://www.karndean.com/globalassets/karndean/b2c-blocks/b2c-document-listing-block/usa/brochures/resi-brochure-2026.pdf)
lists the same 7.0 mm beside its rigid-core format and says the format has a "sound-absorbing
backing", so the model treats 7.0 mm as the whole product, backing included, and adds no pad
or underlay. No price is published; the `lvp` row in `prices.toml` is still Quincy's
placeholder until a local quote. The colour is the mean of the central half of Karndean's
overhead image (`#d6cebb`), a photographic approximation: check a sample in the house light.

## Installation rules that matter here

From Karndean's [Rigid Core Plank and Tile installation guide](https://www.karndean.com/globalassets/karndean/b2c-blocks/b2c-document-listing-block/usa/installation-guides/karndean-rigid-core_plank-and-tile-installation-guide-usa.pdf)
(KD8132GLO, January 2024; index at karndean.com/en-us/floors/services/installation-guides/):

- Floating floor, always over a solid base. A separate underlay is not normally recommended.
- Wood subfloor: solid with minimal flexibility, loose boards fastened, plywood overlay where
  needed (ASTM F1482). Flat to 3/16" in 10 ft in any direction. Wood moisture not above 13%.
- Expansion gap at least 3/16" (5 mm) around the room perimeter and every fixed object
  including pipes; 5/16" (8 mm) for areas over 1000 SF. A joint (5/16") is also required
  where a run exceeds 50 ft in either direction. The LVP field is about 841 SF of rooms (709 SF
  net in the takeoff), under 1000 SF, so 3/16" is the minimum; 5/16" is kept as margin.
- Install permanent fixtures before the floor, leaving the gap. Trim and base fix to the wall,
  not to the plank.
- Underfloor heating is allowed if the interface between the backing and the subfloor stays at
  or below **85 F (27 C)**; electric systems: consult the heater maker. Avoid hot spots;
  rugs and furniture that stop air circulation are a risk.
- Max 65-85 F room temperature in use; protect from prolonged direct sun and from stoves.
- **Not published:** a cabinet-specific rule. The guide's only stance is to install fixed
  objects first and leave the expansion gap, which is why the model cuts the plank out of
  fixed base cabinets (`Material.floating`, kick left under) and never pins the plank.

## Consequences in the house

- Finished floor +1.0255906" (3/4" + 7 mm), 0.0787" (2 mm) over Quincy. Storey datum stays the
  top of joists; sills stay on the datum.
- Radiant: none under the plank. `FH-M-DINING` was retired with `SL-M-DECK` (decision #112),
  so the 85 F interface rule above only matters if a rug-sized film is added later
  (`plans/TODO.md`, tile medallions).
- `D-M-STUDY` has plank on both sides at one plane: no reducer. `D-M-BED2` keeps its
  5/4 oak saddle (rise now 0.7244" to the 1.75" carpet plane).
- Stair arrivals, base/paneling starts and plumbing elevations that quote the plank top moved
  by +0.0787" (ST-M2S base and ST-B2M top at 1.0255906", etc.); tests pin them.
- The east window row (sill 2'-10 9/32") rose 9/32" so the stools stay on the counter tops,
  which now stand on the plank instead of a flush cap.

## Alternatives retained for sampling

- [A&A Surfaces Whitmore White HD-LVR5015-0017](https://www.homedepot.com/p/310230523):
  5 mm incl. attached underlayment, 7 x 48 in., 20 mil.
- COREtec Pro Classics Quincy Oak VV017-01018 (previous selection): 5 mm incl. cork, 7 x 48 in.,
  20 mil, 28.84 SF/carton, listed $5.69/SF 2026-10-26.
- [Mohawk PureTech Plus Native Ridge Talc Oak PTL04-721](https://www.mohawkflooring.com/shop/Resilient/detail/PTL04/Native_Ridge/721/Talc_Oak?productLine=PureTech%20Plus):
  8 mm body + 2 mm pad = 10 mm, 7.5 x 54 in., 22 mil.
- [Shaw Ascent NB Alpine 2832V-01134](https://shawfloors.com/en-us/vinyl/ascent-nb-alpine-9-/2832v-01134):
  WPC, 8 mm with pad, 9 x 72 in., 20 mil.
- Mohawk SolidTech Plus (Akers SDP07-231 and similar): SPC, 6 mm incl. 1 mm pad, 20 mil;
  Akers $4.49/SF at Avalon Flooring (retailer-reported).

A switch updates `params/flooring.py`, the stair arrivals, transitions and the other literals
that quote the plank top, together.
