# HVAC filter and service access

**Scope:** the filters and service faces currently identifiable in the Catlin plan, plus the
Broan B210E75RT intake screen. The plan does not grade a ladder setup or service envelope;
these locations need to stay accessible in the construction layout.

## Access schedule

| Item | Service access | Design direction |
|---|---|---|
| `REG-S-HP-RET` — System 1 return | 28 x 12 x 1 MERV 13 filter behind a hinged face that opens down; reachable from the hall floor. | Keep the entire grille face unobstructed for drop-down filter changes. No ladder or access panel is needed. |
| `EQ-B-ERV` — Broan B210E75RT | Internal MERV 8 washable filters (MERV 13 is an optional disposable filter). Its hinged cabinet door has two latches. The unit is exposed in `RM-B-FURNACE`, hung with its case bottom at +4'-6". | Preserve 13" in front of the maintenance door and 3" on the electrical-box side per Broan's drawing. The case is only 1 1/8" from north partition `W-B-ESS-S`, so keep both service zones facing into the open room. Use a portable ladder; do not enclose the unit or put storage in the service aisle. |
| `EQ-M-ERV-HOOD-OA` — outdoor intake | The 12" hood body is centered at +5'-0" main datum, or +7'-10" above the site grade; the screen runs from +7'-4" to +8'-4" above grade. Broan calls for quarterly inspection of the intake hood for leaves, twigs, ice, and snow, and cleaning as needed. | Use a portable ladder from the north slot. Keep a clear place to set it up; no fixed ladder or platform is modeled. The hood clears the HP3 disconnect work-space vertically, and intake/exhaust hood centers are 12'-0" apart. A ladder centered below the hood would temporarily occupy part of the disconnect's working-width; decide whether that maintenance-time overlap is acceptable or move the disconnect/hood. |
| `REG-M-BATH2-DRY-IN` — stall-drying fan intake | A 12 x 12 ceiling grille in `RM-M-BED` at +9'-0" covers the fan and drops for filter/fan access. Recommended filter: AAF PerfectPleat HC M8, nominal 10 x 10 x 1 in. (9.5 x 9.5 x 0.75 actual). | Keep the grille clear and reachable from a portable ladder. Verify the final grille holder accepts the actual filter dimensions; inspect monthly during initial use, then replace quarterly or sooner if loaded. |
| Gree indoor heads: `EQ-B-HP2-GYM`, `EQ-M-HP2-BED`, `EQ-M-HP2-LIVING`, `EQ-M-HP3-STAIR` | Each exposed wall head has a front filter face. The modeled bases are +6'-6", +7'-6", +7'-6", and +3'-0", respectively. Gree's owner manuals describe quarterly filter cleaning by lifting and pulling the filters forward. | Keep the faces and filter-removal path open. The three high heads require ladder access; the stair head is reachable from the floor. No access panels are needed while the heads remain surface-mounted. |

## ERV operating feedback

The pressure budget in `erv_static_budget.md` uses the clean-filter fan curve and does not
model the reserve consumed as filters load. Broan says VIRTUO maintains selected airflow
despite filter clogging in a typical installation. The unit's LCD reports real-time airflow
and diagnostics; its manual's low-airflow warnings direct the user to inspect the filters,
registers, intake/exhaust hoods, and ductwork. The sources describe no dedicated
filter-loading alarm. Keep quarterly cleaning on the maintenance schedule and check the
airflow display as a performance indicator.

## Before close-in

- Keep `EQ-B-ERV` exposed and orient its door and electrical-box side toward the open furnace
  room, away from the north partition. Preserve Broan's 13" and 3" clearances at the actual
  installed orientation.
- Keep the outdoor hood screen reachable with a portable ladder from the north slot. Do not
  add a permanent obstruction in the ladder setup area.
- Resolve whether the portable ladder's temporary overlap with the HP3 disconnect approach
  is acceptable; if not, relocate the disconnect or intake hood before close-in.
- Keep the System 1 return grille and bath-2 intake grille clear of furnishings and casework.
- Confirm the grille holder accepts the selected 10 x 10 x 1 in. nominal filter's actual
  9.5 x 9.5 x 0.75 in. dimensions when the grille product is selected.

## Manufacturer references

- [Broan B210E75RT specification sheet](https://broan-nutone.com/getmedia/9863cd5f-e206-478f-a30f-14d30c857c17/Spec_Sheet_B210E75RT_En_2.pdf?ext=.pdf): filter options, real-time airflow, VIRTUO, and service clearances.
- [Broan AI Series installation manual](https://www.broan-nutone.com/getmedia/26847653-1424-49e1-9415-6b2e8becf223/Installation_Guide_AI_2_Broan_En_1.pdf?ext=.pdf): quarterly filter and hood maintenance, hinged door, and airflow troubleshooting.
- [AAF PerfectPleat HC M8 product data sheet](https://aafterms.aafintl.com/-/media/files/aaf/commercial-and-industrial/us-products/pleated-filters/perfectpleat-hc-m8/perfectpleat-hc-m8_prod_mark_sht_afp-1-210.pdf): nominal and actual sizes, MERV 8 rating, airflow capacity, and pressure-drop data.
- [GREE Livo R32 indoor-unit manual](https://www.greecomfort.com/assets/our-products/livo-r32/documents/livo-r32-installation-owner-s-manual-indoor-a.pdf) and [GREE Sapphire R32 system documentation](https://www.greecomfort.com/system-documentation/): quarterly wall-head filter cleaning and access instructions.
