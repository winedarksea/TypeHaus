# Laundry task track

`ED-M-LAUNDRY-TRACK` replaces the obstructed can while preserving UID `QTM000SAAA`.
The white rail runs east–west at (130.7", 258"), flush below the 108" ceiling.
Two 45° heads share channel 1 and `ED-M-LAUNDRY-SW`; `ED-M-LAUNDRY-PSU` owns
the 120V connection to `CKT-LT-MAIN`. The heads carry 22W at 24V, without a second
branch load. The supply is modeled at its 40VA rating, consistent with the house's
other lighting supplies; this is a scheduling convention, not a measured input VA.

| Component | Order model | Quantity | Procurement |
| --- | --- | ---: | --- |
| PureEdge magnetic rail | TS24M-2C-4FT-WH | 1 | Buy 48", field-cut to 36" |
| Radiant Medium head | T24M-2C-RADM-FL-30K-WH | 2 | Fixed 3000K, 11W, 660lm, CRI93, 45° |
| White end feed | TS24M-2C-EP-WH | 1 | West end |
| Universal supply enclosure | PSB-40W-UNI-24VDC-T | 1 | Surface mount; accessible cover |

Rail caps, slot covers, anchors and screws are included with the rail. All component
prices require a vendor quote; no verified price is available. The component order view
ships as `track_lighting_materials` in the BOM and lighting inspector. It describes the
same assemblies counted in `placeables`, so it is excluded from a second cost total.

The supply mounts on the laundry face of `W-M-BA2E`, centered at y=257", bottom 84"
above the main-storey datum. Its cover remains above the washer/dryer body. The authored
Class 2 surface raceway `CR-M-LAUNDRY-24V` rises above the enclosure and runs below
the ceiling to the west feed. Keep the enclosure ventilated and its cover removable.
The installation leaves the existing ceiling ducts, framing and pocket-door cavity intact.

Adapters sit at x=115.83" (machines) and x=145.55" (sink). Both heads aim south;
the Python catalog derives tilt from the modeled pivot/lens and the task target.
The machine target is the center of its north/front face. The sink target is the front
interior at y=240", 34" above the finished floor. Tests check both optical axes against
the tall machine and the rack's stowed body and 16" deployment envelope. Hanging
clothing can still interrupt the sink beam; adjust heads in the field as needed.
These checks establish geometry and sightlines, not an illuminance calculation.

Reusable factories live in `typehaus.library.track_lighting`. `magnetic_track_spec`
configures the PureEdge system; `standard_track_spec` configures WAC HT4-WT / HLE-WT
with H-2010-930-WT Silo X10 integral-driver heads (fixed 3000K, 10W each, 35° default,
25° included optic). Authored head offsets, azimuth, tilt and optic drive plan strokes,
canvas meshes, GLB and IFC. Hinge/adapter details without published dimensions are
schematic; all consumers use the same geometry. Interactive head editing is outside this change.

Sources: [PureEdge rail and supply specification](https://www.pureedgelighting.com/edge/specs/PureEdge_TS24M_Surface_Suspended_MagneticTrack_2C.pdf),
[Radiant Medium specification](https://www.pureedgelighting.com/pure/specs/PureEdge_T24M_Radiant_Medium.pdf),
[WAC H track](https://waclighting.com/product/h-track/),
[Silo X10 specification](https://www.waclighting.com/storage/waclighting-images/specsheet_pdf/2010-HJL_SPSHT.pdf).
