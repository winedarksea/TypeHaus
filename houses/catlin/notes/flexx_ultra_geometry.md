# EQ-S-HP1-AH connection and service-space review — 2026-11-11

The matched outdoor unit's model and drawing datums are recorded separately in
[`flexx_ultra_outdoor_geometry.md`](flexx_ultra_outdoor_geometry.md).

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
18 1/8 high. Discharge is -x, return +x and service front -y. Since 2026-11-11 Catlin
places it at rotation 0 on `RM-A-EAST-UNFIN`'s attic deck, so those faces point west,
east and south; `SF-S-HP1` and its closet hatch are retired. The small face
markers are entirely within the cabinet envelope; they do not reserve fitting,
insulation, wrench, trap or cable-bend space.

| Interface | Verified size | Location certainty |
| --- | --- | --- |
| Supply | 11 5/8 across × 16 3/4 high when horizontal | West end; rear-biased centre inferred |
| Return | Clear opening unpublished; modelled 20 × 16 (inferred) | East end; provisional centre |
| Liquid refrigerant | 3/8 inch tube | Front face; schematic station |
| Vapor refrigerant | 3/4 inch tube | Front face; schematic station |
| Primary condensate | 3/4 inch PVC nominal | Front face; schematic station |
| Secondary condensate | 3/4 inch PVC nominal | Front face; schematic station |
| Power | 208–230 V | Front entry allowance; knockout not located |
| Controls | 24 VAC / RS485 | Separate front entry allowance; knockout not located |

## Fit findings

1. **Service space: resolved by the attic move (2026-11-11).** The front panel faces
   south onto open deck. The 24-inch zone (x 250 1/2–294, y 304 9/16–328 9/16) was checked
   clear of walls, ducts and equipment, with 70 1/2–91 1/2 inches of headroom under the
   roof. `mep.air_handler_coordination` stays UNKNOWN because there is no enclosure to
   test against, and that is correct. The attic service rules (passageway, level
   service space, a light switched at the entry and a receptacle near the unit) are open
   items in `plans/TODO.md`.
2. **Supply transition: modelled as a shop box.** `DU-A-HP1-SUP-NECK` (11 5/8 × 16 3/4,
   4 inches long) joins the aperture to `EQ-A-HP1-SUP-BOX` (22 1/2 × 14 × 21). Its 12 × 12
   bottom outlet drops through `FO-A-HP1-SUP` into the 18 × 8 trunk in `SF-S-DUCT`. The
   indoor manual asks for a solid bottom for the first 6 inches past the outlet, and the
   box floor provides it. The aperture's setback is still unpublished: confirm it on the
   delivered cabinet before the neck is cut.
3. **Return transition: 20 × 16, inferred.** `DU-A-HP1-RET-NECK` joins `EQ-S-ERV-MIX`
   (the return plenum) to the east end. No drawing dimensions the return aperture, so
   20 × 16 is an assumption, flagged on the duct. Measure the delivered cabinet.
4. **Condensate assembly is absent.** No primary or secondary line is drawn
   (`mep_drainage.py`), and neither is the external emergency pan (IMC 307.2.3: the unit
   is over finished ceilings). The cabinet is FLOOR-mounted on the deck, and the pan
   will lift it about 2 inches. A route down to a receptor is open.
5. **Heat kit: now inside the cabinet.** `EQ-S-HP1-STRIP` is drawn within the
   discharge half and keeps only its power port. `blower_interlock_ref` to the AH is
   the relation that pardons the overlap.
6. **Lineset and control routing are unverified.** The attic location sets a new route
   from `EQ-M-HP1-OD`, and no refrigerant pair is modelled.

The software tests verify aperture geometry, certainty labels, placement transforms,
service-zone detection and shared viewer/GLB/IFC geometry. They do not resolve these
installation gaps. Cabinet containment and existing duct connectivity passes must not
be used as permission to fabricate this assembly.
