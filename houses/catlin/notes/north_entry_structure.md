# North entry schematic structure — 2026-09-10

Implements [the selected concept](../../../plans/north-gable-extension.md) for model
review. This is an unconditioned connector. Member sizes and connection markers are
schematic; neither the model nor the deck-span table establishes their capacity.

The garage moves 30 inches north, retaining its 24-foot square frost-depth ICF foundation.
The six-foot south roof extrusion shares the garage's 4:12 slopes and full gable width.
Its cantilever framing is an **off-model structural package**, not ordinary rake framing:
the truss supplier must provide outlookers/girders, backspan, east/west wall reactions,
drift from the taller house, unbalanced snow, uplift ties and foundation anchorage.
The extension changes the new truss order and is not an instruction to extend stock trusses.

## Landing bearing map

`FS-BW-FLOOR` retains UID `BWFS01AAAA`. Its finished surface is 0 inches at both thresholds; the framing is lowered one inch
for the composite thickness. Five exterior rises from -34 inches are exactly 6.8 inches. The west edge is x=6
feet to leave the slats and independent guard outside the full x=6.5..9.5-foot house-door
landing patch. The east edge remains x=11.5 feet. Both doors keep a full 36-inch patch.

| Member | Support | Connection requirement |
|---|---|---|
| BM-BW-HOUSE-SEAT | W-B-N3 and W-B-N2 concrete | Three fixed steel stand-off seats, reaching the concrete below the floor band; no load into cladding, foam or unsupported rim. |
| BM-BW-GARAGE-SEAT | W-GF-S1 and W-GF-S-DR concrete | Three sliding steel seats with uplift/lateral restraint and accessible vertical shims. |
| BM-BW-FW | Both seat beams | Ends outside the garage wall; supports west joist field and screen. |
| BM-BW-FC / FE | Both seat beams | Continue inside the service opening to the interior stair; design the overhang, negative moment, anchorage and deflection together. |
| FS-BW-FLOOR joists | FW / FC / FE | Flush hangers at 12-inch maximum centres, joist tape and compatible exterior fasteners. |
| FS-BW-GARAGE joists | FC / FE continuations | Separate narrower framing field under the same board direction and finish datum. |

The second FloorSystem is the structural zone inside the door, not a second concrete
landing. A 1/4-inch drainage/movement break separates its board field at the threshold.
It extends three clear feet beyond the ICF inner face; `ST-G-SERVICE` arrives exactly
at its north edge and 0-inch finish. The old unsupported `SL-G-STEP-0` is retired.
The existing garage flight remains KDAT; its five rises are rederived to the new finish.

Seat markers identify the load path and custom hardware in the takeoff but are not shop
drawings. Price their fabrication, anchors, thermal isolation, flashing and engineering
as one package. Concrete top elevations differ from the ledger elevations: steel brackets
must bridge that vertical offset, not just the insulation thickness. Keep both seats
inspectable. Verify differential movement before selecting the final slip direction.

## Tiers, screen and drainage

Four 24-inch composite treads climb west across the roughly six-foot clear passage.
The modeled carriage has stringers no more than 12 inches apart and 1-inch composite wear
surfaces. Design stringer notches, tread blocking and upper attachments for the long tread
module; the notched 2x12 representation is not a capacity calculation. The lower landing
is at least 36 inches deep, on drained compacted aggregate and replaceable pavers; grade
falls east into the open approach. Provide a slip/bearing detail that preserves riser
uniformity through seasonal movement. No new concrete is planned under this assembly.

The base elevation uses vertical on-edge 2x4 slats, 1.5-inch faces at 3-inch centres,
mounted clear of grade on the west frame. The separate 36-inch guard takes guard loads;
the slats are not credited as a guard. Design rail attachments and slat end fixings for
wind. Corrugated metal and opal polycarbonate remain price alternates: replacing the
slats with a solid wall requires the corresponding wind-load and drainage redesign.

Both garage gutter leaders now discharge north. Snow retention is required along the
east/west roof zones above the screen, tier approach and equipment circulation; the roof
supplier must size the crossbars/clamps, including the new six-foot roof area. Wind seam
clamps are **not** a substitute for snow retention.

At the house leave the modeled roughly 6.5-inch rake clearance; reserve 4–6 inches after
fascia/closure detailing. A positively sloped closure attaches only to the garage, ending
in a replaceable compressible/brush seal at the house. Maintain the house rainscreen and
access from below; no rigid coupling or trapped meltwater. Provide fire/draft closure at
the original garage south gable plane, retain garage gypsum and confirm service-door
rating/self-closing requirements with the AHJ. The movement joint is not fire separation.

## Excavation and release conditions

Excavate and waterproof the deeper house first while access is open. Confirm native
garage bearing before backfill; form garage footings/stem and coordinate sleeves while
the house cut remains accessible, then compact backfill in controlled lifts. The 30-inch
move improves the engineering excavation screen but does not prove soils or setbacks.
It preserves garage concrete volume and removes the passage's four pads, four piers and
unsupported concrete landing. Added framing/seat costs must be deducted from that saving.

Obtain the survey/zoning determination for the complete roof projection, actual soil and
foundation section, truss/bridge structural design and envelope/AHJ details before
construction procurement. These are external design deliverables, not completed model
checks. The model package can be reviewed while they remain open.
