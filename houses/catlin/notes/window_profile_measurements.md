# Window profile measurements: public-source review

Reviewed and modeled 2026-11-07 in `plan/window_types.py`. The 3D model uses the public
Alucover exterior faces and inward sash-bottom limit. Supplier confirmation remains for the
ordered Alucover adaptor. §2 (Andersen) is history since 2026-11-13: the escape units are Max
Light (35/35 mm faces), and Andersen is the documented revert.

## 1. Drutex IGLO Energy Alucover / DAKAM

**Dimensioned Alucover sections are available.** Fensterblick publishes profile 70001
with operable sash 70013, together with sill-adaptor sections. These are dealer-hosted
product drawings, not a DAKAM order submittal:

- [Alucover detail index](https://www.fensterblick.de/detailzeichnungen-kunststoff-alu-fenster-drutex-iglo-energy-alucover.html).
- [70001 / 70013 operable section](https://www.fensterblick.de/files/bilder/detailzeichnungen-iglo/1080/drutex-iglo-energy-alucover-70001-70013-fenster-124mm.jpg).
- [70001 fixed section](https://www.fensterblick.de/files/bilder/detailzeichnungen-iglo/1080/drutex-iglo-energy-alucover-70001-festverglasung-74mm.jpg).
- [54123 adaptor](https://www.fensterblick.de/files/bilder/detailzeichnungen/drutex-iglo-energy-fensterbankanschluss-30mm-54123.jpg),
  [54113 adaptor](https://www.fensterblick.de/files/bilder/detailzeichnungen/drutex-iglo-energy-fensterbankanschluss-30mm-zusatz-54113.jpg),
  [50114 adaptor](https://www.fensterblick.de/files/bilder/detailzeichnungen/drutex-iglo-energy-fensterbankanschluss-50mm-50114.jpg).

| Drawing dimension | Published value | Meaning for the model |
|---|---:|---|
| Bare PVC frame depth / depth to aluminium cap | 82 / 93 mm | Confirms the authored 93 mm depth; neither is a rail height. |
| Exterior capped frame face / added operable sightline | 74 / 50 mm | Authored on fixed / operable types, replacing the Phius-based 75 + 50 mm. |
| Room-side bottom of inward sash above bare PVC frame bottom | 38 mm | Authored as `inward_sash_bottom_height`, limiting the 3D stool top. |
| Room-side sash profile height | 85 mm | A physical profile dimension, distinct from the added 50 mm exterior sightline. |
| Fixed section's room-side face | 73 mm | Includes that fixed section's glazing detail; do not assume it is the operable stool-bearing rail. |
| 54123 / 54113 installed adaptor extension below frame | 30 mm | Both drawings dimension the extension from PVC frame bottom, excluding the engagement above it. |
| 50114 installed adaptor extension below frame | 50 mm | An alternative assembly, not evidence that DAKAM supplies it. |

The Alucover drawings also label a 2 mm difference between the exterior cap-bottom
reference and the PVC frame bottom. Keep the PVC frame, cap, and adaptor datums explicit.

**Conditional clearance, calculated from the drawings:** with a retained 30 mm adaptor,
the inward sash's bottom is 30 + 38 = **68 mm (2.677") above the adaptor bottom**; with
50114 it is **88 mm (3.465")**. These are sash-bottom elevations before running clearance,
not released stool heights. Do not subtract the 38 mm sash-bottom dimension from the
74 mm exterior face: the cap and PVC bottom references differ, and the exterior face
does not establish the room-side rail intended by `sill_rail_height`.

[DAKAM's Drutex brochure](https://dakamgroup.com/wp-content/uploads/2025/01/katalog_okien_pvc_en.pdf),
printed pp. 12–13, lists a five-chamber PVC under-sill trim with gasket as standard, but
does not identify its profile number or dimension the sash overlap. The 54123 drawing
has five chambers below its engagement; that is a useful candidate, not confirmation
of DAKAM's supplied assembly.

**Remaining DAKAM request:** confirm 70001 / 70013 for the quoted Alucover windows,
the retained adaptor number and height, whether the quoted unit height includes it,
and a dimensioned operable sill section showing the stool-bearing rail and lowest inward
sash edge from the same installed bottom datum. Specify the required running clearance.
**2026-11-07, adaptor modelled on operable units.** On the bare frame the operable stool
(top at 38 mm, 1.18" thick) sat 1.1" into the sill pan's 1 1/2" back dam
(`FlashingConfig.back_dam_m`; 56 stool/pan solid overlaps). A PVC unit on a backdammed pan
needs the adaptor, and DAKAM's brochure lists an under-sill trim as standard, so operable
types now carry the 30 mm 54123 adaptor in the unit envelope: **68 mm** stool limit
(`inward_sash_bottom_height`) and a 104 mm sill sightline. The stool then clears the
dam by about 0.05". The ordered adaptor and its height are still DAKAM's to confirm. The direct measurement avoids inventing an interior rail / lap
split from an exterior face. Fixed units retain an explicit **75 mm provisional stool
rail** so the exterior face correction does not disturb the dining counter alignment;
the 73 mm fixed glazing detail is not evidence of a stool-bearing rail. Once selected,
include the retained adaptor in the unit envelope before adding its height to the stool.
Profile and adaptor identities are also recorded on the house's `Product` records.

## 2. Andersen 400 operating casement (retired 2026-11-13; kept as the egress revert)

**A published architectural face split exists.** Andersen's
[Architectural Tools page](https://www.andersenwindows.com/for-professionals/architect/architectural-tools)
links a [PDF section archive](https://edge.sitecorecloud.io/andersencor0d3d-andersencorae0f-prod102c-dc69/media/Project/AndersenCorporation/AndersenWindows/AndersenWindows/files/architectural-tools/400-series/400-series-2d-sections-updated-12-12-2017/aw-400_series-sections-casement_awning-pdf.zip).
Inside it, read page 2 of `AW-400_Series-Sections-Casement_Awning.pdf` (2016-10-04)
and `AW-400_Series-Sections-Contemporary_Casement_Awning.pdf` (2022-02-14).
The operating sections A/2, B/2, C/2 give:

| Location | Unit edge to unobstructed glass, dimensioned | Sash face, dimensioned | Remaining exposed frame allowance, calculated |
|---|---:|---:|---:|
| Jamb B/2 | 2 3/16" (55.5625 mm) | 1 5/8" (41.275 mm) | **9/16" (14.2875 mm)** |
| Head A/2 | 2 3/8" (60.325 mm) | 1 5/8" | **3/4" (19.05 mm)** |
| Sill C/2 | 2 7/16" (61.9125 mm) | 1 5/8" | **13/16" (20.6375 mm)** |

The final column subtracts the sash face from the total sightline. It describes the
exposed allowance, including the frame-to-sash gap, not the full frame extrusion.
At the sill, for example, the drawing separately labels 5/8" to the frame ledge;
the remaining 3/16" is between that ledge and the sash. Interior trim dimensions use
different points again. Do not put the net jamb allowance into a stool rail field.

Both architectural files explicitly state: “Details have been optimized for use in
architectural software and do not match manufacturing specifications.” They depict
dual-pane glazing and predate the selected triple-pane offering. Their jamb total is
4 3/8" across the unit, versus the current custom-size sheet's rounded 4.40" deduction.
They improve the geometry evidence but do not release the selected triple-pane profile.

As a separate check, Andersen's own [C6 sash part 9065577](https://parts.andersenwindows.com/product/casement-window-sash/01t2J000006Xlf6QAC)
lists 22.969" overall sash width and 19 3/4" visible glass. Half their difference is
1.6095", close to but not exactly the architectural 1 5/8". That listing is a Low-E
replacement sash, not the selected custom triple-pane assembly.

The [2025–26 product-detail sheet](https://www.andersenwindows.com/-/media/Project/AndersenCorporation/AndersenWindows/AndersenWindows/files/technical-docs/product-details/productdetails-windows--400series-casement-awning-casement-awningpicture-transom.pdf),
p. 1, additionally publishes **2 7/8" base jamb depth behind the installation flange**,
**1 5/16" forward projection**, and **4 9/16" overall jamb depth** with the extension
shown. None alone is the model's front-to-back basic-frame depth; retain that hold.
The same sheet dimensions the interior sill ledge **1 1/8" above the unit bottom**.

**Remaining Andersen request:** verify the operating head/jamb/sill sections for
AND-N-1-04162 triple-pane custom casements with the widest-opening hinge, including the
exterior visible frame/sash split, interior sill-ledge elevation, trim-stop option and
basic-frame depth with named front/back datums. Confirm whether the public architectural
split remains applicable. The model now authors all three exposed allowances using
`frame_face_width`, `frame_head_face_width` and `frame_sill_face_width`, plus the 1 5/8"
`sash_face_width`. `sill_rail_height` is independently 1 1/8", so stools follow the interior
ledge rather than the exterior jamb allowance. These are architectural modeling dimensions;
they do not change the separately published net-clear egress deductions or custom-size step.
