# Image II eave rib-end sealing — decision and specification, 2026-11-08

**Decision.** Close every exposed Image II eave rib end with Metal Sales tube sealant. Follow
the 2026 guide's hem bead and tape in full. No vent closure, no across-pan foam closure, no
weep holes. Field-formed metal rib caps (guide pp. 32–33) remain an installer alternative;
they are not specified or estimated here. Cap fabrication would have to precede hemming.

The software deliverable is 100 resolved rib ends, each with one treatment. **This does not
establish field watertightness or adhesion**, and the items under "Open" below stay open.

## Source

`sources/metal-sales-image-ii-install-2026.pdf`: *Image II Installation Guide*, footer date
4/1/2026, created 2026-04-08. Retrieved and checked 2026-11-08 from
<https://www.metalsales.us.com/wp-content/uploads/2026/04/Image-II_Install-Guide-4-2026.pdf>.
sha256 `83a74b7b92b8e83e1ea8810225d9518b8150c7abc420aaf2ec0b3878014775f9`.

| Printed page | What it requires |
| --- | --- |
| 26 | Eave: "Fill exposed end of ribs with tube sealant"; double-bead tape on the offset cleat's bottom leg |
| 27 | Extended Eave: same fill note; double-bead tape on the extended leg |
| 28–29 | Box and residential gutter: "Fill ends of Image II ribs with Tube Sealant" |
| 31 | Notch ribs 1-1/2" from the panel end; continuous bead of tube sealant inside the open hem |
| 32–33 | Optional field-bent rib caps, made before hemming; clean debris and excess sealant |
| Accessories | 6403200 "Acrylic Tube Sealant" clear; 64032XX "Tube Sealant" color match; both listed at 3.31 lb |

The older pocket guide and the 2024 Residential Design Guide are consistent on sealed or
field-closed rib ends. The 2024 guide's bead six inches upslope is **not** added here: the
2026 eave details do not call for it, and details from different years are not accumulated.

## Where each seal goes

Rib end, looking upslope (one seam; the plug is confined to the rib):

```
          ___crown___
         /###########\      ### tube sealant plug, inside the rib only
   pan  /#############\  pan
  _____/###############\_____
```

Mid-pan section, house Extended Eave (no rib is cut here, so no plug is drawn):

```
  field membrane -> strip-in -> [6403899 tape] -> pan
                                                  pan folds round the lip,
                                                  continuous 64032XX bead inside the hem
  eave leg (under the strip-in) -> lip; eave face over the gutter back
```

Seam section, house Extended Eave (`SL-D-EAVE-RIB`):

```
  crown ======================.     rib notched 1-1/2" back from the panel end
        plug, 1-1/2" allowance |   fill starts at the notch and runs upslope
  ----- strip-in / eave leg ---'
```

**House (RF-HOUSE, wrapped Extended Eave).** 54 rib ends over the box gutters. The strip-in
already covers the whole eave leg, so the guide's tape goes on top of the strip-in, directly
under the pan, as chosen 2026-11-08. No geometry changes.

**Garage and canopy (RF-GARAGE, RF-BW-CANOPY, offset cleat on a fascia eave).** 38 and 8 rib
ends. Offset cleat on 6403899 tape, hem bead, rib fill. The garage's soffit intake, baffles and
ridge vent are a separate path and are not touched; sealant must not reach them.

## Installation sequence

1. Prepare and clean surfaces. Install membrane, flashing and strip-in, then the tape.
2. If metal caps were chosen instead, fabricate them now, before hemming.
3. Notch ribs 1-1/2"; hem the pan; run the continuous bead inside the open hem.
4. Engage the eave piece, fasten, and snap panels eave to peak in one direction.
5. Fill each exposed rib end. Keep sealant inside the rib: never across a pan, into the gutter
   line or between parts that must move.
6. Clean excess. Inspect every termination before gutters or access obstruct it.

Local plugs must not bond a panel to fixed flashing beyond this detail; keep nail-slot and hem
movement.

## Product status

Selected: **64032XX, color match**, matched to the roof panel at order. Identity beyond that is
**unconfirmed**. No technical data sheet for any Metal Sales tube sealant could be found on
2026-11-08. The catalog names chemistry only for the clear 6403200 (acrylic); the 2021 product
manual says "urethane, 10.3 oz cartridge"; 3.31 lb is not one such cartridge.

Not yet recorded, because nothing published states them: chemistry, package, compatibility with
PVDF/galvanized panel and with the butyl membrane or tape it may touch, surface preparation,
application temperature, cure and rain exposure, service temperature, UV exposure, movement
capability, shelf life and repair method.

| Value | Used | Status |
| --- | --- | --- |
| Rib fill depth | 1-1/2" | **Allowance**: the guide gives none; set to its notch length |
| Hem bead | 1/4" round | **Allowance**: the guide says only "continuous bead" |
| Cartridge | 10.3 fl oz | **Allowance**: 2021 manual; current package unconfirmed |
| Waste | 20% | **Allowance** |
| Rib cavity | 0.549 sq in | From the modeled seam, itself traced proportionally |

These surface as `advisory.eave_rib_sealing_spec` UNKNOWNs, outside the permit gate by decision;
`integrity.eave_rib_sealing` separately grades that every rib end is closed once. The 3D model
carries no plug solid: the records and the seam detail carry it, so an allowance never looks
like a measured shape.

## Secondary drainage: open

The former drawing claim was that water on the strip-in leaves "at the pan hem's return". The
guide's bead fills that hem and its tape lies across the leg, so **that exit is closed by the
specified detail, and no other exit has been demonstrated.** The drawings now say so. Do not
restore the claim, omit the tape or bead, cut weep holes or extend a plug across a pan to
create one. Reopening the ribs would not create a suitable drainage system either.

Question prepared for Metal Sales (not sent; no response has been requested or received):

> On a 6:12 Image II roof over a fully adhered butyl membrane, with Extended Eave 52124XX over
> a box gutter flange and a membrane strip-in covering the extended leg to the lip: is a
> continuous tube-sealant bead in the open hem plus double-bead tape on the strip-in acceptable,
> and is any secondary outlet required at the hem? Which chemistry is 64032XX, in what package,
> is it compatible with butyl membrane, and what rib fill depth do you intend?

## Quantity effect

| Row | Before | After |
| --- | --- | --- |
| Rib ends closed | 0 | 100 (54 house, 38 garage, 8 canopy) |
| 64032XX cartridges | 0 | 11 (159.4 cu in net, 191.3 with waste, pooled) |
| Hem bead | 0 | 130.8 LF |
| 6403899 eave tape | 0 | 137.0 LF added to the ridge tape |
| Construction total | $880,507–$1,666,834 | $880,877–$1,667,666 (+$370 to +$832); prices are allowances, not quotes, and no saving is claimed |

## Open

Construction holds are tracked in [construction_holds.md](construction_holds.md): product data,
plug depth, secondary drainage and a representative mock-up. Membrane full-coverage approval,
gutter supports, snow control and gutter splices remain their own work items.
