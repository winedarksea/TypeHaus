# Shower assemblies — 2026-11-09

`plan/shower_assemblies.py` defines the four fixture-local assemblies placed in five showers.
`FixtureType.shower_assembly` supplies shared viewer, GLB and IFC geometry and the hot/cold
ports. Fixture tags, product references, and package pricing quantities remain unchanged.
Components are geometry with product references, not additional `ProductPart` purchases.

| Shower | Finished-face valve station, fixture-local inches | Into wall | Standing surface above fixture base | Head mounting station above fixture base |
| --- | --- | --- | --- | --- |
| Sauna | (18, 0, 51 7/16) | east | 2 in. | 80 in. |
| BATH2 | (0, 18, 48) | local north; east after -90° rotation | 1 1/2 in. | 79 1/2 in. |
| Attic | (0, 18, 48) | north | 2 in. preliminary base allowance | 80 in. |
| BATH1 tub | (-30, 0, 30) | west end | 2 in. preliminary tub-base allowance | 80 in. |
| Suite tub | (-30, 0, 30) | north end after -90° rotation | 2 in. preliminary tub-base allowance | 80 in. |

Head height is configurable independently of the surround height. The complete head and arm
bounds are checked against the resolved flat ceiling or the room's finished roof slope.
The tub heads are above the 73-inch integral surround and attach to the actual end walls;
the head arms do not attach to the long back wall. The insert geometry uses its 16-inch rim.
BATH2 has separately visible temperature and volume levers. The tub showers retain a wall
diverter and a separately fed handheld, plus the trim's spout. Docked combo handhelds use
hoses from the head outlet, without a second concealed riser.

The 2-inch half hub spacing and 1 3/4-inch inlet depth remain **APPROXIMATE** scaled R10000
geometry. `mep.shower_assembly_alignment` grades endpoint position and outward-axis arrival
independently of that certainty; the general fixture port check still reports approximate
manufacturer stations. Aligned geometry is not an exact manufacturer dimension. The valve
body, head shapes, hoses and lever dimensions remain illustrative envelopes.

## Supply coordination

- Sauna: valve and head at pan north–south centreline y=98 3/16 inches. Finished tile face
  x=209 3/4 inches; estimated hub plane x=211 1/2 inches. Hot is north (user's left facing
  east), cold south. Drops at y=104 3/16 and 92 3/16 turn into hubs at y=100 3/16 and
  96 3/16. The hot feed's upstream x=195/y=188 turn also clears BATH2's added joist.
- BATH2: keep the 48-inch station, corresponding to branch elevation 158 3/16 inches above
  the basement datum. The hot riser at y=189.5 inches stays north of the added y=186 joist,
  `PR-B-SH2-DRAIN` and the cleanout extension; its final 11 1/4-inch horizontal arrival reaches
  the hot hub at y=178 1/4. Moving that riser to the cold branch's 1 1/2-inch approach would
  recreate the documented drain conflict.
- Attic: the hot and cold risers stay south of the vents until elevation 288 3/4 inches,
  then move into the inlet plane y=267 3/8 inches and turn along the wall into side hubs.
- BATH1: retain the shared cold drop and WC tee at (32 1/2, 410 1/4) inches. A terminal
  valve-height branch reaches y=413, turns east to hub plane x=38 1/2, then south into the
  cold hub at y=411 1/2. The WC tee does not move. Hot approaches its hub from the south.
- Suite tub: the existing two horizontal side-hub arrivals in W-S-SBF are retained.

BATH2's SS-3636 **molded centre-drain connection is resolved**: joist 011 moves from y=176
to 170 inches and a full-span TJI is added at y=186, keeping every bay at or below 16 inches.
The drain pipe and service port now share the molded centre; the required subfloor cut
leaves the ceiling below closed. See [BATH2 drain coordination](bath2_shower.md#drain-coordination).

## Sauna wet-wall construction — material qualification BLOCKED

USG explicitly permits Durock cement board in saunas and recommends waterproofing in wet
areas: [USG FAQ 567](https://assemblies-tools.usg.com/content/usgcom/en/resource-center/faqs/567.html),
read 2026-11-09. This establishes board suitability only. It does not qualify the complete
wet-wall system at the sauna's maximum temperature.

The two 36-inch splash spans now remove the wood finish and model, from room to wall:

1. 1/4-inch tile plus setting-bed allowance; actual tile/thinset selection remains open.
2. 1/2-inch USG Durock cement board.
3. 1/4-inch plywood packing on the existing horizontal liner supports. Support every board
   perimeter and joint; add edge nailers before installing board, and fasten through packing
   to the supports. Packing is not a substitute for the board manufacturer's fastening schedule.
4. Existing 1/2-inch liner strapping, except at the local valve pocket.
5. Existing 2-inch foil-faced polyiso, locally recessed for the valve pocket.
6. The stud wall, with the valve stringer supported between studs in its actual bay.

The 1/4-inch projection relative to the old wood face closes the pan-to-wall gap. The east
tile face is x=209 3/4 inches; the north tile face is y=116 1/8 inches. The backer and packing
are separate resolved solids and quantity rows; the removed shiplap no longer exists behind
them. Nominal gross coverage is approximately 45 square feet each of tile, Durock and packing,
clipped to each actual wall span. The valve pocket deducts insulation and strapping locally.

The stringer's mounting face is x=212 1/2 inches, **2 3/4 inches behind tile**, at the
manufacturer's target rather than at mid-stud. Delta's current
[50353 Rev O, p.3 step 1B](https://media.deltafaucet.com/MandI/50353%20Rev%20O.pdf),
read 2026-11-09, gives 2 3/4 ± 1/4 inches from stringer to finished face. That published
setback does not dimension the side-hub centres. `BK-B-SAUNA-VALVE` fits the clear stud bay;
its front stands 3/4 inch toward the room from the stud face. Its face offset, profile and
length reach framing and takeoff.

The 12 × 10-inch local pocket stops the foil-polyiso and strapping around the valve rather
than embedding the casting in foam. Retain insulation behind the pocket where it fits.
Return sauna foil across the recess edges and its back with a continuous heat-rated foil
liner; seal each pipe penetration to that liner. Keep service piping behind the room finish.
The section's dashed foil return describes the required continuity, **not an approved tape
or sealant selection**. Close the backer around the trim's actual plasterguard opening and
use a compatible waterproof valve collar sealed to the membrane, covered by the escutcheon.

Carry one continuous bonded waterproofing system from the tiled backer down over the pan's
wall upturn/flange, with the manufacturer's seam band, corner pieces and approved joint
sealant. Provide supported board edges and a movement joint where tile meets the adjoining
wood liner. Do not terminate waterproofing on the plywood packing or leave wood exposed to
shower water. Coordinate the foil/collar and pan-liner transitions before enclosure.

**Do not declare this construction detail resolved or release the tile package** until the
selected waterproofing, reinforcing tape/band, setting mortar, valve/pipe collars, foil tape,
and sealants have documented service-temperature compatibility for the actual sauna cycle,
and the pan-liner manufacturer accepts the connection. No complete named system with those
approvals has been established in this change. Durock is the specified board; the rest is a
recorded construction blocker. The current head and valve remain product-envelope geometry,
subject to delivered-product rough-in and heat-exposure confirmation.

## Temperature screening — recorded research, not a released system

Primary documents checked 2026-11-09:

| Component | Published evidence | Qualification status |
| --- | --- | --- |
| USG Durock 1/2-inch board | [USG FAQ 567](https://assemblies-tools.usg.com/content/usgcom/en/resource-center/faqs/567.html) explicitly permits sauna use | Board suitable; does not establish a waterproof system |
| LATICRETE HYDRO BAN **Sheet** Membrane | [North American DS-041.0](https://cdn-global.laticrete.com/-/media/project/laticrete-international/north-america/product-documents/product-data-sheets/lds0410_hydro-ban-sheet-membrane.pdf) publishes resistance from −22°F to +194°F and lists cement backer board as a substrate | Candidate for further qualification; the 194°F limit leaves only 4°F above a 190°F operating target. Confirm actual maximum surface temperature, exact SKU and current revision |
| HYDRO BAN sealing tape, corners and collars | Sheet datasheet lists the system accessories; [pipe-collar DS-65486-0325](https://www.laticrete.com/-/media/project/laticrete-international/north-america/files/support-and-downloads/product-support/product-data-sheet-en_hydro-ban-pipe-collars.pdf) describes urethane seals, seam overlaps and thin-set bonding | Do not transfer the sheet's temperature rating to the collar's elastomer without confirmation. The stated 50–90°F application window is not an in-service rating |
| LATASIL silicone | [Published North American datasheet](https://cdnmdm.laticrete.com/Datasheet/NA/101/Datasheet_NA_en_101.pdf) gives −40°F to +350°F service temperature | A plausible joint sealant; heat rating alone does not approve adhesion to the pan liner, foil facer or adjoining tape |
| Tile mortar, board-joint tape, foil tape and pan interface | No complete project-specific qualification established | Still blocked; identify the exact materials and confirm the entire interface set |

The candidate is the **sheet membrane**, not liquid HYDRO BAN or HYDRO BAN Board; those are
separate products. This research does not substitute a regional product or a foam board into
the Durock detail. For comparison, [Schluter's shower-system data sheet](https://assets.schluter.com/asset/570120892212/document_2nqfpg0pi13itfso529nhmlr7f/Shower%20System%20Data%20Sheet.pdf)
limits **KERDI-BOARD** to 158°F. That board figure is not a rating for KERDI sheet membrane.
A steam-room label by itself cannot establish suitability for this hotter sauna.

## Geometry reviews

No per-shower review images were committed; view the assemblies in `haus serve`. BATH2's
drain bay: [bath2-shower-drain-framing.svg](assets/bath2-shower-drain-framing.svg)
(`scripts/render_bath2_shower_drain.py`).

The shared geometry tests compare placed, rotated IFC mesh vertices and GLB vertices with
the viewer's source parts. Catlin regressions reuse the read-only model, context and IFC
fixtures. The head/arm check includes the attic roof slope. Hub tests independently reject
wrong handedness, an offset endpoint, perpendicular arrivals, and an arrival from inside
the valve body.

## Verification result — 2026-11-09

`scripts/verify.sh` passed: 10,893 engine tests passed (40 skipped), 376 starter-house checks
passed, Catlin strict checks reported 3,715 passes and **zero failures** (147 not evaluable),
ruff passed, and UI type checking and geometry tests passed. Focused regressions also checked
all ten supply arrivals, configurable docked-handheld heights, material-volume conservation,
furring-to-strapping accounting, and placed viewer/GLB/IFC vertices.

Reviewed reference snapshots now include the shower changes and current source geometry for
the already-present D-B-SUNKEN headflash removal and bearing-block detail revisions.
Construction release remains subject to the sauna temperature and interface qualification
above. BATH2's centered drain and coordinated joist/supply changes are recorded in
`bath2_shower.md` §5.
