# The block load, component by component

**House:** catlin
**Structure:** the whole thermal envelope — every wall, roof, slab, window and door
`estimate_block_load` sums, plus the two air-side terms.
**Written:** 2026-09-18, by hand, against the arithmetic the engine had been doing since
M5 WP5.3.
**Oracle for:** `checks/building_science/ground.py` (§§1–3), the grade split in
`checks/building_science/energy_load.py` and
`resolve/site_earth.strip_grade_elevation_m` (§4), the raked-wall area (§5) and the air side
(§6). Reproduced by `tests/test_energy_ground.py` and
`tests/test_energy_envelope_scope.py`.
**Companions:** `notes/room_heat_loss_baths.md` (the same load, scoped to one room, and its
§4 moved with this pass); `notes/heat_pump_turndown.md` (what this load is then sized
against).
**What is asked of the reviewer:** nothing is deferred here and no seal is wanted — this is
a *calculation* note, not an engineering one. What it asks is that the eight figures in §7
be read as eight figures. **The total was right to 1% before any of this and every one of
its parts was wrong**, in both directions, by 0.5–2.0 kBtu/h.

> ⚠ **THIS IS NOT A MANUAL J.** It carries no hourly solar, no shading, no internal gains,
> no latent load and no duct losses, and its cooling term is a single all-orientations-peak
> window gain that overstates the glass by about 1.6×. What it *is* is every term written
> down where a reviewer can see which one is wrong. Sizing equipment off §7's heating figure
> is defensible; sizing a compressor off its cooling figure is not, and
> `mep.cooling_capacity` says so in every message it prints.

---

## 1. The ground design temperature is derived, and it checks itself

`Site.soil_temp_f` is 47.0 °F and `plan/site.py` says where that came from: the annual mean
of the twelve MSP 1991–2020 monthly TAVG normals, hand-computed and rounded. The twelve
normals are authored on the same object, so the engine can do the same sum:

```
(16.2 + 20.6 + 33.3 + 47.1 + 59.5 + 69.7 + 74.3 + 71.8 + 63.5 + 49.5 + 34.8 + 22.0) / 12
  = 562.3 / 12
  = 46.858 °F
```

Which rounds to 47. **That agreement is free and it is a real check**: two independent
statements of the same fact, one authored by hand and one derived, and the engine now names
a disagreement over 1 °F instead of letting one of them be wrong quietly.

But 47 °F is the **annual mean**, and the block load charged every below-grade surface
against it — a 23 °F ΔT at a 99% heating hour. The ground surface does not sit at its annual
mean in January. It swings about it, and ASHRAE Fundamentals Ch. 18 Fig. 13 publishes the
amplitude: **22 °F** for the North Central US, now authored as
`Site.ground_surface_amplitude_f` beside `ground_snow_load_psf`, which is the same class of
fact.

```
T_ground,design  = 46.858 − 22 = 24.858 °F   ->  heating ΔT = 70 − 24.86 = 45.14 °F
T_ground,summer  = 46.858 + 22 = 68.858 °F   ->  cooling ΔT = max(0, 68.86 − 75) = 0
```

**45 °F, not 23.** Nearly a factor of two on every below-grade surface in the house. And the
cooling side lands honestly at zero rather than at the 20 °F an air ΔT would have charged a
basement in July.

## 2. A basement wall's conductance falls with depth (Latta & Boileau)

Heat leaving a basement wall at depth *z* does not go straight out. It runs up through the
soil to the ground surface, and that path is about `π z / 2` long. So the conductance at
depth *z* is the assembly in series with that soil path:

```
U(z) = 1 / (R_assembly + π z / (2 k))        k_soil = 0.8 Btu/h·ft·°F
```

Averaged over the buried depth *D*, in closed form:

```
U_avg = (1 / D) ∫₀ᴰ dz / (R + π z / 2k)
      = (2 k / π D) · ln(1 + π D / (2 k R))
```

**Worked for `W-B-E1`**, R-21.8, buried 6.12 ft below its local grade (§4):

```
π D / (2 k)       = 3.14159 × 6.12 / 1.6      = 12.018
1 + 12.018 / 21.8                             = 1.5513
ln(1.5513)                                    = 0.43904
2 k / (π D)       = 1.6 / (3.14159 × 6.12)    = 0.083205
U_avg             = 0.083205 × 0.43904        = 0.03653 Btu/h·ft²·°F
R_eff             = 1 / 0.03653               = 27.4
```

**R-27.4, not R-21.8** — the soil adds R-5.6 on this wall. Two sanity gates on the algebra,
because both were live errors in drafts of it:

* Dropping the π (using `z / 2k`) gives `U_avg = 0.04226`, R-23.7. Too small a change to
  notice by eye, which is exactly why it is written down.
* Putting the π in the wrong place — `π / (2 k z)` rather than `π z / (2 k)` — gives R-76,
  which is absurd and is the form to watch for.

The house's own numbers, from the resolved model:

| wall | R | buried | U_avg | R_eff |
|---|---|---|---|---|
| `W-B-E1`, `W-B-E2` | 21.8 | 6.12 ft | 0.0365 | 27.4 |
| `W-B-N1`, `W-B-S1`, `W-B-W1`, `W-B-W2` | 21.5 | 6.12 ft | 0.0370 | 27.0 |
| `W-B-N3`, `W-B-S4` | 21.5 | 6.04 ft | 0.0371 | 27.0 |
| `W-B-N2`, `W-B-N4` | 21.5 | 5.79 ft | 0.0374 | 26.7 |

Total: **763.3 ft² at UA 28.16**, where `A / R` would have claimed UA 35.4.

## 3. A basement floor: the soil IS the insulation

The same path, from the bottom of it. The distance out is set by how far the middle of the
floor is from the nearest exterior wall — the floor's **shortest plan dimension** *w* — and
by its depth *z* (ASHRAE Fundamentals Ch. 18):

```
U = (2 k / π w) · ln( (w/2 + z/2 + k R / π) / (z/2 + k R / π) )
```

**Worked for `SL-B-FLOOR`**, R-11.13, 36.0 ft on its short side, 6.286 ft below grade:

```
k R / π      = 0.8 × 11.13 / 3.14159 = 2.8345
near         = 6.286 / 2 + 2.8345    = 5.97755
far          = 36.0 / 2 + 5.97755    = 23.97755
ln(far/near) = ln(4.01127)           = 1.389076
2 k / (π w)  = 1.6 / (3.14159 × 36)  = 0.0141471
U            = 0.0141471 × 1.389076  = 0.0196524 Btu/h·ft²·°F
R_eff        = 50.88
```

**R-50.9 over an R-11.1 assembly.** The soil is four fifths of it. Billing this floor at
`A / R_assembly` against a soil ΔT overstated it about 2×: 1,296 ft² at `1/11.13` is UA 116
against the honest 25.5.

A slab **on grade** is a different quantity entirely and is not this formula. Its loss is
around its edge, which is why every standard publishes it as an **F-factor in Btu/h per
linear foot of exposed perimeter per °F**, against outdoor design *air*. catlin has no slab
on grade inside its envelope, so the engine's F-factor branch never fires here; it is in
`ground.py` with the two published ASHRAE 90.1 Table A6.3 rows (F-0.73 uninsulated, F-0.54
with R-10 to 24") because an area-times-soil-ΔT reading of an uninsulated one is about 10×
low, and the next house should not have to rediscover that.

## 4. Grade is local, and it is read off a strip, not a radius

`Site.grade` is a single plane at **−0.864 m**. Two of this house's basement walls do not
live under it:

```
W-B-S2-FR / W-B-S3-FR   z0 = −2.596 m,  top = 0.000 m
SL-SG-FLOOR (the sunken-garden court floor)  top = −2.780 m
```

The court floor is the ground surface those walls face. Splitting them at the global plane
buries **1.73 m of open-air walkout wall in soil ΔT** — a 3.7× understatement on the very
walls the envelope-scope fix has just added to the load.

`resolve/site_earth.py` already solves the general problem for the frost check and its
`nearest_grade_station` is already clamped never to raise a local grade above `Site.grade`.
What it could not do is *direction*: `local_grade_elevation_m` measures distance
**radially**, which is right for frost — frost drives in from every exposed face — and wrong
for a thermal ΔT, where a wall is graded by the soil it is backfilled against, on one side.

`W-B-S1` is the wall that proves it. It is collinear with the walkout and clips the court's
corner, so radius cannot separate the two:

```
radial distance to SL-SG-FLOOR:   W-B-S1  0.148 m      W-B-S2-FR  0.100 m
```

0.148 against 0.100 is not a separation. `strip_grade_elevation_m` sweeps an 18" strip off
the wall's **exterior face** — the face `both_faces_interior` has already identified, so no
new geometry — and asks what share of that strip the court floor covers. The separation is
about 25×, and the answer is right for every wall in the house:

| wall | graded at | governed by | buried |
|---|---|---|---|
| `W-B-S2`, `W-B-S2-FR`, `W-B-S3`, `W-B-S3-FR` | −2.780 m | `SL-SG-FLOOR` | **0.00 ft** |
| `W-B-S1`, `W-B-E1`, `W-B-W1`, … | −0.914 m | nearest grade station | 6.12 ft |
| `W-A-S2`, `W-A-S3` (attic gables) | −2.780 m | `SL-SG-FLOOR` | 0.00 ft |

The split emits **three** wall components, not two:

| component | area | UA | heating ΔT |
|---|---|---|---|
| `walls` (framed, above its local grade) | 3,233.7 ft² | 73.66 | 85 °F |
| `foundation_walls` (below its local grade, ground-coupled) | 763.3 ft² | 28.16 | 45.14 °F |
| `foundation_walls_above_grade` (concrete in the open air) | 253.1 ft² | 11.53 | 85 °F |

The third is a component rather than a line folded into `walls` for two reasons. Folded into
`foundation_walls` it charges open-air concrete a soil ΔT; folded into `walls` it claims to
carry cladding, which breaks the `walls.area_ft2 ≤ clad_wall_area_ft2` bound the energy sheet
test asserts. And a **framed** wall below its local grade goes to the ground-coupled band,
because a split that only reached foundation walls would fail the first framed walkout,
which is literally `W-B-S2-FR`'s family.

## 5. A raked gable wall is a trapezoid

`ResolvedWall.z1_m` is the wall's *bounding* height, and for a `ToRoof` wall that is the
**ridge**. `top_z0_m` / `top_z1_m` are the real top at the two ends. Billing
`length × (z1_m − z0_m)` makes every gable a rectangle:

```
W-A-N2B   z0 = 6.096 m,  z1 = ridge,  top_z0/top_z1 = 8.611 / 6.096 m
```

Over catlin's attic gables: **657.6 ft² billed against 414.0 ft² real — 243.6 ft² of
invented wall, about 470 Btu/h of heating.** A straight rake between two end elevations makes
the face a trapezoid, and a trapezoid's area is its length times the *mean* of its two
heights, which is what `_wall_top_z_m` returns.

## 6. The air side: three multipliers, all of them missing

```
q = 1.08 × ACF × CFMnat × uplift × ΔT
```

**N is a table, not a number.** `CFMnat = CFM50 / N` is the LBL model (Sherman & Grimsrud),
and N is `base × height × shielding`. The flat 18.0 the engine defaulted to is one cell of
that table — two storeys, normal shelter — read as though it were the whole thing:

```
base 18.5 × height(2 storeys) 0.8 × shielding(Exposure B, well-shielded) 1.2  =  17.76
```

Shielding comes off `Site.wind_exposure`, which this house already authors for wind: ASCE 7
§26.7.3's B / C / D are the same three surroundings the LBL shielding classes name, so there
is nothing new to keep in sync. Height is authored (`infiltration_storeys = 2`) because "how
many storeys" in the LBL sense is above-grade conditioned height over the leakage plane, and
a storey list holding a basement, an attic pocket and a detached garage on the house's own
keys cannot answer it.

**Sherman's N yields an ANNUAL AVERAGE.** A design hour is not an average hour. Below four
storeys the heating design rate is about **1.5×** the annual average — the design hour is the
year's coldest and windiest, which is what drives stack and wind pressure — and the cooling
design rate is about **0.84×** it. The uplift is on infiltration only: an ERV runs at its
commissioned airflow whatever the weather is doing.

**1.08 is a sea-level figure.** At 830 ft the air is thinner:

```
ACF = (1 − 6.8754e−6 × 830)^5.2559 = 0.9704
```

Net, on the house's 1.0 ACH50 over 46,159 ft³ of conditioned volume (room clear-face area ×
the storey's `default_ceiling_height`, which is what `_volume_ft3` measures):

```
CFM50  = 1.0 × 46,159 / 60            = 769.3
CFMnat = 769.3 / 17.76                = 43.32
q_heat = 1.08 × 0.9704 × 43.32 × 1.5 × 85   =  5,788 Btu/h
```

Against 3,924 Btu/h before: the uplift is 1.5×, the ACF takes 3% back, and the N-factor
change (18.0 → 17.76) adds 1.4%. And the ERV, which takes no uplift:

```
73.5 cfm net of sensible recovery
q_vent = 1.08 × 0.9704 × 73.5 × 85          =  6,547 Btu/h
```

## 7. The result, and what to read it as

| component | area | UA | heating ΔT | Btu/h |
|---|---|---|---|---|
| `walls` | 3,233.7 ft² | 73.66 | 85 | 6,261 |
| `foundation_walls` | 763.3 ft² | 28.16 | 45.14 | 1,271 |
| `foundation_walls_above_grade` | 253.1 ft² | 11.53 | 85 | 980 |
| `roof` | 1,547.9 ft² | 29.10 | 85 | 2,474 |
| `slab` | 1,296.0 ft² | 25.47 | 45.14 | 1,150 |
| `windows` | 261.0 ft² | 61.21 | 85 | 5,203 |
| `doors` | 120.0 ft² | 24.00 | 85 | 2,040 |
| infiltration | — | — | 85 | 5,788 |
| ERV ventilation air | — | — | 85 | 6,547 |
| | | | | **31,714** |

Cooling: **22,154 Btu/h, 1.846 tons**, of which 17,435 is the window-and-door solar term —
and that term is the one §0's warning is about.

**The heating total was 31,731 before any of this and is 31,714 after.** Seventeen Btu/h, on
a pass that changed five terms by 0.5–2.0 kBtu/h each. It is the clearest possible statement
of why a block load is a table and not a number: every correction here was real, several were
factor-of-two, and a reviewer looking only at the bottom line would have seen nothing at all.

**Cooling moved 21,672 → 22,154 and the tonnage *fell*, 1.806 → 1.846 … then further.** The
envelope corrections put cooling up; splitting the cooling setpoint from the heating one
(Manual J's 75 °F, where one setpoint had been serving both) took the cooling ΔT from 20 °F
to 15 and took a quarter off every conduction term in that column. The two nearly cancel,
which is the same lesson again.

## 8. What is NOT in here

- **Solar is still wrong and was deliberately left wrong.** The orientation weights
  `{N 0.25, E 0.70, S 1.0, W 0.85}` put south at the peak; at 45 °N in July the own-peak
  irradiances are N 54 / E 240 / S 172 / W 240 Btu/h·ft², so south is 0.72 of the peak. The
  term is 71% of the cooling load and a *partial* fix moves the number the wrong way —
  raising E/W without adding shading or fixing the all-orientations-peak-at-once error makes
  it worse. It changes once, with an hourly method and an AED excursion.
- **Internal gains, latent load and SHR.** `cooling_tons = cooling / 12000` is sensible-only.
- **Buffer spaces.** A surface facing an unconditioned-but-enclosed space is charged the full
  outdoor ΔT — conservative, so it oversizes — and the gap is *named*. There is nowhere in
  this model to get a buffer temperature from, and "garage = (indoor + outdoor)/2" is the
  rule of thumb this package forbids. catlin emits zero such lines: its garage is detached.
- **Duct losses.** System 1's trunk runs in a conditioned soffit, so the omission is small
  here and would not be in a house with attic duct.
