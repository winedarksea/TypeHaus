# EQ-S-HP1-AH connection and service-space review — 2026-11-11

The model now has a horizontal-left FXU24 cabinet shell, an open supply aperture,
an open return end, schematic connection markers and a required front service zone.
The connection markers are coordination allowances, not drilling locations. No port
has been promoted to `EXACT`: the published drawings do not dimension their stations.

## Manufacturer evidence

- [FXU24 submittal, GREE_FXU24_230V_R32_SUB_01272026](https://www.greecomfort.com/assets/our-products/flexx-ultra-r32/documents/flexx-ultra-r32-submittal-24mbh-a.pdf),
  pp.2,4,6: shipped W18 1/8 × H43 1/2 × D21 1/4 inches; horizontal-left needs no
  drain-pan relocation; minimum 24 inches in front of the service panels. The supply
  opening is A11 5/8 × B16 3/4 inches. The perspective view places it toward the rear,
  but does not dimension its setback. The return aperture is not dimensioned.
- [Indoor installation manual](https://www.greecomfort.com/assets/our-products/flexx-ultra-r32/documents/flexx-ultra-r32-installation-owner-s-manual-indoor-a.pdf),
  §§4.2–4.4: front service space, external pan, drainage pitch, 3/8 liquid and 3/4 gas
  refrigerant connections for FXU24, and primary/secondary condensate connections
  using 3/4-inch PVC, with a trap close to the coil.
- **Document conflict:** the current generic manual §2.3 groups FXU24 with a
  W21 1/4 × H48 3/16 × D21 1/4 cabinet, while the model-specific submittal gives the
  smaller cabinet above. Retain the model-specific submittal basis provisionally;
  obtain the drawing for the actual ordered revision before fabricating anything.
  Nominal drain size is not a verified thread specification or fitting outside diameter.

## Product frame and placed geometry

The horizontal cabinet is 43 1/2 inches along local x, 21 1/4 along local y and
18 1/8 high. Discharge is -x, return +x and service front -y. Catlin's 90-degree
placement turns those faces south, north and east respectively. The small face
markers are entirely within the cabinet envelope; they do not reserve fitting,
insulation, wrench, trap or cable-bend space.

| Interface | Verified size | Location certainty |
| --- | --- | --- |
| Supply | 11 5/8 across × 16 3/4 high when horizontal | South end; rear-biased centre inferred |
| Return | Clear opening unpublished | North end; provisional centre |
| Liquid refrigerant | 3/8 inch tube | Front face; schematic station |
| Vapor refrigerant | 3/4 inch tube | Front face; schematic station |
| Primary condensate | 3/4 inch PVC nominal | Front face; schematic station |
| Secondary condensate | 3/4 inch PVC nominal | Front face; schematic station |
| Power | 208–230 V | Front entry allowance; knockout not located |
| Controls | 24 VAC / RS485 | Separate front entry allowance; knockout not located |

## Fit findings that remain open

1. **Service space fails.** The east case face is x244 5/8 inches; the derived
   east cavity limit is x258 inches, leaving 13 3/8 inches against the required 24.
   The return occupies the east lane as well. `AO-S-HP1-AP` is an underside hatch;
   it does not establish access perpendicular to the east-facing service panels.
   `mep.air_handler_coordination` reports a FAIL rather than crediting cabinet fit
   as service access. Rework the cabinet orientation/enclosure and return together.
2. **Supply transition is missing.** The 18×8 trunk begins at the cabinet face,
   but cannot be attached directly to the 11 5/8×16 3/4 aperture. With the provisional
   rear-aligned station, the opening centre is 4 13/16 inches west and 3 13/16 inches
   below the trunk centre. A 3-inch vibration connector does not make that offset
   transition. Its length, flange allowance, eccentricity and service clearance need
   explicit geometry once the cabinet revision and opening setback are confirmed.
3. **Return transition is unverified.** The 10×18 return reaches the north case,
   but no manufacturer drawing establishes its mating aperture. Do not copy the
   supply dimensions onto it or mark its case-level connectivity as exact fit.
4. **Condensate assembly is absent.** The primary line from this handler is still
   undrawn (`mep_drainage.py`). An independent secondary protection arrangement,
   trap/cleanout, external emergency pan, supports and their removal path need geometry.
   The resolved cabinet currently starts at the cavity floor; that does not reserve
   space under it for a pan. Re-check the complete pitched assembly vertically.
5. **Heat kit still has legacy external geometry.** `EQ-S-HP1-STRIP` is drawn south
   of the cabinet, despite FLEXA2LHTR05KWD being an internal accessory. Its current
   envelope and air port are not a verified factory assembly. Replace that independent
   external body with an explicitly hosted internal accessory while preserving its
   circuit, heating capacity and takeoff identity. Do not fabricate an inline heater
   from the existing placement.
6. **Lineset and control routing are unverified.** The new connection markers expose
   the interfaces, but the model has no routed refrigerant pair or verified fitting and
   insulation envelopes. Face markers do not establish separation from the return duct.

The software tests verify aperture geometry, certainty labels, placement transforms,
service-zone detection and shared viewer/GLB/IFC geometry. They do not resolve these
installation gaps. Cabinet containment and existing duct connectivity passes must not
be used as permission to fabricate this assembly.
