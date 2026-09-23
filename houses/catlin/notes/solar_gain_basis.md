# Fenestration solar gain, hour by hour

**House:** catlin
**Structure:** all 41 pieces of glass in the thermal envelope — 207.3 sf south, 58.7 east,
49.8 west, 42.9 north — plus the roof, which is the other solar-dominated surface.
**Written:** 2026-09-18, by hand, after `notes/block_load_basis.md` established that the
solar term was the one thing that pass deliberately did **not** touch.
**Oracle for:** `checks/building_science/solar.py` — the ASHRAE clear-sky irradiance (§1),
the single house-wide peak hour (§2), the shading planes (§3), the AED excursion (§4),
internal gains and the latent split (§5) and the roof's sol-air excess (§6). Reproduced by
`tests/test_energy_solar.py`.
**Companions:** `notes/block_load_basis.md` — the conduction and air-side half of the same
load, and §8 of it is the promissory note this note pays.
**What is asked of the reviewer:** **nothing — §6 closed on 2026-09-18.** It asked for the
roof panel's solar reflectance, and the owner stated it: the roof is a **different profile
from the walls in the same colour** — 24 ga PVDF standing seam, Metal Sales Linen White
(81), SR 0.73, so `solar_absorptance` 0.27. The sol-air term is live and adds 329 Btu/h.
A house-local material `standing-seam-linen-white` carries it, because a colour is this
house's choice and the library's generic `standing-seam` is shared.

> ⚠ **THIS IS STILL NOT A MANUAL J**, and what it now lacks is a shorter list: no duct
> gains, no room-by-room distribution, no thermal-mass lag on anything, and a sol-air roof
> term that is an instantaneous upper bound rather than a damped one. What it does carry is
> every term at one *coincident* hour, which is the thing the weighted sum could not do.

---

## 1. The weights were nearly backwards, and this is the table that says so

The term this replaces was

```
window_solar += area × shgc × ORIENTATION_WEIGHT[facade] × 164.0
ORIENTATION_WEIGHT = {N 0.25, E 0.70, S 1.00, W 0.85}
```

South at 1.00, i.e. *south is the peak*. It is not. The ASHRAE clear-sky model on a vertical
surface, 21 July, 44.98 °N:

```
E_b = A / exp(B / sin β)                          A = 346.1, B = 0.207   (July)
E_D = E_b cos θ,  cos θ = cos β cos γ             direct on the surface
E_d = C E_b (1 + cos Σ)/2 = 0.5 C E_b             sky diffuse, Σ = 90°, C = 0.136
E_r = E_b (C + sin β) ρ (1 − cos Σ)/2             ground bounce, ρ = 0.2
```

Each orientation at its **own** peak hour:

| facade | own peak | at solar hour | as a fraction of the day's peak |
|---|---|---|---|
| E | **230.1** Btu/h·ft² | 08:00 | 1.00 |
| W | **230.1** | 16:00 | 1.00 |
| S | 161.4 | 12:00 | **0.70** |
| N | 53.5 | 18:00 | 0.23 |

So the weights had south 43% too high and east 30% too low. North, at 0.25 against a real
0.23, was the only one close — and north is the one that matters least.

**Why south is not the peak at 45 °N in July.** The noon sun is 65.6° up. A vertical south
window sees it at an incidence angle of 65.6° off normal, so `cos θ` is 0.41 and most of the
beam slides past the glass. East and west see the sun low and nearly square on. This is the
same fact that makes a south overhang work and a west one useless (§3), and it reverses in
January, when the low sun is square on to south glass — which is why a *heating*-season
solar credit would need its own pass and this engine still takes none.

## 2. One peak hour for the whole house

The second error, and the worse one. A single weighted sum charges the east glass its 8 a.m.
peak and the west glass its 4 p.m. peak **in the same hour**. No such hour exists.

Evaluated every half hour from 08:00 to 20:00, catlin's house-wide total peaks at **solar
10:30**:

| facade | Btu/h at 10:30 | its own peak, and when |
|---|---|---|
| S | 7,735 | 8,563 (at 12:00) |
| E | 2,938 | 4,725 (at 08:00) |
| W | 796 | 4,014 (at 16:00) |
| N | 685 | 715 (at 12:00) |
| **total** | **12,154** | **18,017** if all four peaked at once |

The 18,017 column is the one to look at: it is within 4% of the 17,435 the weighted sum
reported. So the weights, wrong as §1 shows them to be, were wrong in a way that roughly
**cancelled across four facades** — and essentially the *whole* 1.43× overstatement is the
hour-coincidence error. That is worth stating plainly because it is the opposite of what a
reviewer would guess from §1's table: fixing the weights alone, as `block_load_basis.md` §8
warned, would have changed almost nothing while looking like a fix.

South leads the peak hour at 64% of it, not the 100% the weights implied by putting south
alone at 1.00. 10:30 rather than noon because the east glass is still contributing 2,938 at
that hour and has fallen to under 1,200 by noon, while south only gains 840 between the two.

## 3. Shading: the thing overhead is a FLOOR, not an eave

**`RF-HOUSE` projects nothing past the main-floor south wall.** Measured: the roof covers
that wall in plan and its footprint edge lands on the wall's own exterior face, so the
overhang there is 0.00 ft. An eave-only shading model therefore reports *no shading on any
south glass in this house* — including on `D-M-BALC`, 33 sf of glazed door and the largest
single piece of south glass there is.

What actually shades it is `FS-SG-DECK`, the sunken-garden **balcony deck**: a
`FloorSystem`, 0.98 m above the door head (1.05 m until it came down 3", 2026-09-23), its
near edge 2 3/4" clear of the wall face and its far edge 9.9 ft out.

So the shading model takes **any** horizontal plane overhead — a roof's footprint, a slab's
outline, a floor deck's outline — and a plane blocks a **band**, not a half-space:

```
drop per foot of run   = tan β / cos γ            (the profile angle)
top of the shadow      = z_plane − near × drop     ← the NEAR edge
bottom of the shadow   = z_plane − far  × drop     ← the FAR edge
```

An eave is the degenerate case: `near = 0`, so the band's top is the eave itself and the
depth is the classic `P tan β / cos γ`. Worked for `D-M-BALC` at the 10:30 peak (β = 59.4°,
γ = 44.7° east of the south normal):

```
drop/ft = tan 59.4° / cos 44.7° = 1.6890 / 0.7112 = 2.374 ft per ft
top     = 3.086 − 0.23 × 2.374 × 0.3048 = 2.920 m
bottom  = 3.086 − 9.90 × 2.374 × 0.3048 = −4.078 m
```

The door runs 1.219 to 2.032 m, wholly inside that band: **fully shaded at the peak hour**
(the engine agrees — shaded fraction 1.000), which is what this house's own review recorded
and what nothing in the engine could see.

Three disciplines worth naming:

- **The bands are a UNION, not a sum.** `D-B-PATIO` in the court wall has both the porch
  deck and the balcony deck over it, overlapping. Shading the same inch twice is not more
  shade, and a sum would run past 1.0 and turn the gain *negative*.
- **Only the DIRECT beam is shaded.** Diffuse sky and ground bounce still reach glass under
  an overhang, so a fully shaded south window is not a zero-gain window — of the 144.2
  Btu/h·ft² incident on `D-M-BALC` at the peak hour, 98.6 is direct and blocked and
  **45.6 still reaches the glass**. This is conservative in one further respect: a plane
  overhead also blocks part of the sky the diffuse term integrates over, and that is not
  subtracted.
- **It is lateral as well as vertical.** `WIN-M-LIV-S1` is in the same wall 10 ft east of
  `D-M-BALC` and is **not** shaded, because the balcony stops at x = 8.76 m and the window
  is at 9.75. A model that shades everything on the south wall is as wrong as one that
  shades nothing.

## 4. The AED excursion

ACCA TRB 2003-001a. A house whose fenestration gain is **diverse** — spread over the day,
several orientations sharing it — rides its peak hour on the structure's own thermal mass. A
house whose gain is concentrated in two hours cannot: the mass is still absorbing when the
next hour's gain arrives. The excursion is the part of the peak the mass will not take:

```
average over 08:00-20:00 = 8,683 Btu/h
peak                     = 12,154 Btu/h
excursion = 12,154 − 1.3 × 8,683 = 12,154 − 11,288 = 866 Btu/h
```

**866 Btu/h, which is 7% — catlin has good exposure diversity and pays almost nothing.**
That is the honest answer for this house and it is worth writing down precisely because it
is small: the term exists to catch the house that is *not* diverse (a glass wall facing one
way), and a term that is 7% here would be 30% there.

## 5. Internal gains, and the latent split

Manual J, **cooling only**. There is no heating credit here and there should not be: a
design heating hour is 4 a.m. in January with the house asleep and the appliances off, and
crediting seven people against it is how a system ends up unable to recover from a setback.

```
occupants = bedrooms + 1 = 6 + 1 = 7
sensible  = 7 × 230 + 1,200 (kitchen appliance allowance) = 2,810 Btu/h
latent    = 7 × 200                                        = 1,400 Btu/h
```

`bedrooms + 1` is Manual J's own rule and it is a fact the model already carries
(`Room.occupancy == BEDROOM`), not an authored guess. The appliance allowance takes the low
end of the published 1,200–2,400 band: the high end is a second oven or a commercial-style
range, and a house that wants it should say so rather than have the engine assume it.

**SHR 0.94**, and the latent number is honestly incomplete:

```
sensible 20,695 / (20,695 + 1,400) = 0.937
```

The two air-side latent terms are **named, not guessed**. An infiltration or ventilation
latent load needs the cooling design outdoor **humidity ratio**, and nothing on `Site`
carries one — `monthly_normals`' RH is a monthly *mean*, not a 1% design coincident wet
bulb. And the ERV's **latent** recovery is unstated; `sensible_recovery_effectiveness` is
the only field there is. Both omissions understate the latent load, so the real SHR is
lower than 0.94 and a unit selected on 0.94 will be short on moisture removal. That is the
caveat the sizing checks print.

**The tonnage is now a TOTAL.** `cooling_tons = (sensible + latent) / 12,000`, because a ton
of refrigeration is a total, not a sensible. It was sensible-only, which understated every
selection by the latent share.

## 6. The roof's sol-air excess — CLOSED 2026-09-18

A roof is **solar-dominated and nearly ΔT-independent**. Charging it the same 15 °F cooling
ΔT as a wall is the last big error in the cooling column. ASHRAE's sol-air temperature is
the temperature the surface behaves as though it faced:

```
T_sol-air = T_out + α I / h_o − ε ΔR / h_o
            h_o = 4.0 Btu/h·ft²·°F  (horizontal, summer film)
            ε ΔR / h_o = 7 °F       (a horizontal surface sees the whole cold sky;
                                     a vertical one gets 0, which is why this term is
                                     on the roof and nowhere else)
```

At the 10:30 peak hour the horizontal clear-sky irradiance is **271.1 Btu/h·ft²** (full sky
diffuse, no ground bounce — a roof sees no ground). For three candidate roof colours, against
`RF-HOUSE`'s UA of 29.103:

| roof | α | T_sol-air | CTD over 75 °F | added cooling |
|---|---|---|---|---|
| black EPDM | 0.90 | 144 °F | 69 °F | **+1,572** Btu/h over the 15 °F ΔT |
| mid-grey | 0.55 | 120 °F | 45 °F | **+881** Btu/h |
| Linen White, SR 0.73 | 0.27 | 101 °F | 26 °F | **+329** Btu/h |
| *what the load carries today* | — | — | 15 °F | 0 |

**The roof is Linen White, α 0.27, and the third row is the answer: +329 Btu/h.** The owner
confirmed on 2026-09-18 that the roof is the same Metal Sales PVDF Linen White (81) as the
walls on a *different profile* — concealed-clip standing seam rather than the walls'
exposed-fastener PBR panel. Same SR 0.73 / TE 0.86 / SRI 89 from the same colour guide.

It is authored on a new house-local material `standing-seam-linen-white`, not on the
library's generic `standing-seam`: a colour is this house's choice and the library row is
the shared catalog entry that other houses read. Every other building-science number on it
is `standing-seam`'s verbatim — continuous sheet steel carries no R and no vapour permeance
whatever its colour — so nothing but the cooling load moves.

**Until it was stated, the roof carried the plain air ΔT and the omission was a CAVEAT in
the report rather than an entry in `unknown_inputs`.** That distinction is still the live
design and it is worth keeping: an *omitted refinement* must not take the equipment-sizing
verdict to UNKNOWN, and an *assumed* absorptance would be exactly the rule of thumb this
package forbids. `color` could not have stood in — it is an sRGB presentation triple and
says nothing about the near-infrared, where most of the energy is.
``tests/test_energy_solar.py`` exercises both halves: the live term, and a stripped model
where the caveat fires instead.

**The term is an upper bound either way**, and stated as one: this is the *instantaneous*
sol-air temperature with **no mass lag**. A real roof's peak flux arrives later and damped
by the assembly's own heat capacity. The decrement factor that would correct it is a table
this engine does not have, and inventing one is worse than a stated bound in the
conservative direction.

## 7. What moved

| | before | after |
|---|---|---|
| glass solar | 17,435 Btu/h | **12,154** at solar 10:30 |
| AED excursion | — | **866** |
| internal sensible | — | **2,810** |
| roof sol-air | — | **329** |
| cooling, sensible | 22,154 Btu/h | **20,868** |
| latent | — | **1,400** (occupants only) |
| SHR | — | **0.94** (an upper bound) |
| tons | 1.846 (sensible only) | **1.856** (total) |

The sensible cooling load falls 5.8% and the tonnage barely moves, which — as in
`block_load_basis.md` — is five real corrections cancelling. The glass came down 5.3 kBtu/h;
the internal gains put 2.8 back, the roof 0.3, and the latent took the tonnage the other
way.

## 8. What is still NOT in here

- **No thermal-mass lag anywhere.** Every term is instantaneous at one hour. A masonry house
  would behave very differently and this would not show it.
- **No duct gains.** System 1's trunk runs in a conditioned soffit, so the omission is small
  here and would not be in a house with attic duct.
- **No room-by-room distribution.** The zone loads are still `estimate_block_load` with a
  room filter, whose attribution is plan-overlap and whose air side is volume share. The
  `mep.*` sizing checks say so in every message.
- **Wall sol-air.** Manual J gives the *same* cooling HTM to all four wall orientations and
  so does this. That is Manual J's own simplification, not an omission of one — a wall is
  ΔT-dominated in a way a roof is not.

## Revision 2026-09-23 — WIN-A-S2/-S3 WT-1436 → WT-1424 (c3c46cff)

Two unshaded south windows lost 1.167 sf each; SHGC 0.35, so ΔA·SHGC = −0.817 ft². At
10:30 south irradiance is 144.2 Btu/h·ft²: −118 off the peak (12,271 → 12,154). The 08:00–20:00
mean south irradiance is 85.1: −69.5 off the average (8,752 → 8,683). At its own noon peak
(161.4): −132 (8,695 → 8,563). Excursion follows, 894 → 866. Sensible cooling −153.2
(21,021.1 → 20,867.9) = glass −118 + excursion −28 + conduction −0.53 UA × 15 °F = −8.

