# Bath2 tub deck finish — one bonded Corian piece

**House:** catlin
**Structure:** `SL-M-TUBDK` (deck top), `WP-M-BATH2-TUBDK-APRON` (waterfall faces on
`W-M-TUBDK-W` / `-S`), `WP-M-BATH2-TUB-SPLASH`, `CT-M-BATH2-VANITY`, `STOOL-WIN-M-BATH2`,
`LR-M-BATH2-TUB-CLG`
**Written:** 2026-10-22, from the owner's material review of the same day.
**Oracle for:** nothing computed. This is a finish and fabrication decision. Its geometry is
pinned by `tests/test_catlin_bath2_tub_deck.py` and `tests/test_paneling_geometry.py`.
**Companions:** `notes/bath2_tub_hardware.md` covers the filler, bars and rim fit.
`notes/bath2_shower.md` covers the stall, glass and wet-wall spec.
**What is asked of the reviewer:** confirm that the fabricator can make the U, the two faces
and the splash as one bonded piece to these joints (§3), and that the chips pass §4.

> ⚠ The legs are 2-3⅞". Only bonded acrylic makes them, the apron and the stall face
> without seams or a breakage risk. Do not let a fabricator substitute quartz, cultured
> marble or tile on price. Every one was weighed and rejected in §2.

![Plan and section through the foot ledge and glass](assets/bath2_tub_deck_finish.svg)

---

## 1. What the deck leaves visible

The rim sits on ≤⅛" spacers at 22¾", so the visible deck is a thin U around it
(house-plan inches, resolved model):

| leg | working | visible |
|---|---|---|
| W | rim 62.49 − apron face 58.615 | 3⅞": apron on the shower's front-glass line |
| N, at HS1/HS2 | deck 264.615 − rim 262.615 | 2" |
| S, the foot ledge | rim 202.615 − deck 194.375 | 8¼": filler, glass |
| E, at BA2E | deck 94.615 − rim 94.49 | ⅛": silicone only |

(K-1130-W1, 60 × 32, since 2026-10-22.)

Tiled, that U is grout slivers and a cut tile edge on every leg but the south. The knee
walls' two exposed faces also stopped at the 20" framing top. The 20"→22¾" band under the
deck edge was unfinished, because `resolve/paneling.py` clamped a band to the wall height.

## 2. Options

| option | durability | clean assembly | cost (est.) | verdict |
|---|---|---|---|---|
| A. Quartz, 2 cm, mitred waterfall | hard, stain-proof | 2" legs and the 2½" W leg are breakage-prone around a 57" hole; mitres are glued, not bonded | high | rejected |
| B. **Corian-class 12 mm acrylic** | renewable: sands back; ≥ ½" radii | **one bonded piece**: U, waterfall faces and splash with inconspicuous seams | ~$40-80/SF installed | **chosen** |
| C. Cultured marble | thin gelcoat over filled polyester; scorches, cannot be renewed (the house's reason for Swan Contour, `plan/products_interior.py`) | moulded to stock sizes only | low-mid | rejected |
| D. Swanstone deck stock | through-colour | BD-4896 is a pre-moulded 48 × 96 whirlpool deck, not a fabricator sheet; thin Swanstone cannot be thermoformed | mid | rejected |
| E. Tile | ordinary | slivers, a tile edge on every leg, and it was unbilled | low | rejected |

B wins on the legs: only a bonded acrylic makes a 2" leg, a seamless apron and a stall face
with no horizontal joint under the glass. **Corian Glacier White**, with Hi-Macs or Staron
of the same class accepted (`PROD-CORIAN-GLACIER-WHITE`). One fabricator and one lot also
supply the vanity top and its 810P bowl and the window stool.

**The shower walls stay Swanstone** (owner). A Corian floor-to-ceiling stall was considered:
about $1.5-3k more, one piece to the ceiling. It was **declined**. The SS-3696 panels still
top out at 96" against the 106" ceiling, so `bath2_shower.md` §5 confirm 3 stays open
(filler or top cap).

## 3. The detail

- **Rim flush.** The rim stays at 22¾" on ≤⅛" spacers, per the Kohler reading. The Corian U
  is template-cut to the rim outline plus ⅛", with a silicone joint. There is no E leg: the
  rim stands ⅛" off BA2E, in silicone.
- **Waterfall faces.** The W apron and the S stall face are mitred and bonded to the top,
  with an eased ⅛" arris. Both run down to the floor tile with a ⅛" silicone joint, and the
  SW outside corner is bonded. Bond over the existing ½" exterior ply.
- **Wall joints.** ⅛" expansion and silicone at HS1 and BA2E. At the E end the stall face
  meets the Swanstone E-wall panel (`WP-M-BATH2-SURR` on BA2E2) in a silicone colour-break
  corner, and the SS-3636's flange tucks behind the stall face.
- **Splash.** 6" Corian on HS1/HS2 (N) and BA2E/BA2E2 (E), 22¾"-28¾" above the storey
  datum. On the N it is bonded or coved to the deck's N leg, so there is no horizontal joint.
  On the E the ½" splash laps the rim, which is ⅛" off BA2E: it sits on the rim lip in
  silicone, like an alcove flange. Painted gypsum above meets only the splash's eased top
  edge, and its SW and E ends are finished, eased edges. It clears the towel-bar posts
  (54") and every bathroom-face device on BA2E/HS1, all above 28" or west of the deck.
- **Glass.** It stands on the S leg in a routed channel or clamps. On the stall side of the
  glass the top slopes ≥ ¼" into the stall. There is no horizontal joint under the glass.
- **Filler.** The fabricator drills the two 1¼" handle holes and the spout hole to the Moen
  template. 12 mm sits within the 4794's 1¼" finish allowance.
- **Access panels.** Two removable leaves cut from the W apron, ⅛" reveal: the 20 × 15
  heater-end `FURN-M-BATH2-TUBDK-AP-N` (on `BK-M-TUBDK-AP-N`) and the 14 × 14 foot
  `FURN-M-BATH2-TUBDK-AP` (on `BK-M-TUBDK-AP`). Leave each out of the bond.
- **Fabrication.** Corian's bulletins want a ≥ ½" (13 mm) inside radius on an L- or
  U-shaped piece and ≥ 3/16" on a cutout. Cutouts are router-cut only, with bits ≥ 10 mm and
  edges rounded over ≥ 1/16". The rim cutout's corners are the U's inside corners and take
  the ½".

## 4. Colour (owner, 2026-10-22; confirm with physical chips)

- **Swanstone Carrara (221)**, veined, for the SS-3636 base and the shower walls. This
  closes the colour item of `bath2_shower.md` §5 confirm 3.
- **Corian Glacier White**, solid, for the deck, faces, splash, vanity top and stool.
- The solid white frames the veined stall. The Calacatta vanity this replaced was the
  room's other pattern; the vanity is now Corian too, so Carrara is the only veining.
- Rules: never put two different veined imitations side by side. Judge the chips under both
  5000 K and 2700 K (`bath2_lighting.md`), next to a quartz offcut and a floor tile.
- **Open:** Carrara's grey veins against any gold-veined piece that remains in view.

## 5. In the model

- `solid-surface-fabricated` (12 mm, `#f4f5f4`). The deck top is `TUBDECK_INT_PLY_CAP`'s ½"
  `deck-top` FINISH layer: `SL-M-TUBDK` is 2¾" thick with its top at 22¾", and the ply
  stays at 22¼". **Known approximation:** the layer shares the cap's outline less
  `FO-M-TUBDK`, so it includes the 1" lap under the rim, about 5 SF where the real U is
  ~1.8 SF. No collision or integrity finding fires on that lap.
- `resolve/paneling.py` clamps a band on a wall named in any `TubEnclosureSpec.knee_wall_refs`
  to the `deck_ref` solid's finished top, so both faces run 0.75"→22.75".
- Prices are ESTIMATES in three rows under one tag, each cross-referencing the others:
  `[envelope_layers]` the top, `[wood_surfaces]` the faces and splash, `[countertops]` the
  vanity top and stool. The 810P bowl is in `FX-VANITY-48-SEKTION`'s row.
- `LR-M-BATH2-TUBDECK` (deck nosing) is retired: no LEDs near the floor. `LR-M-BATH2-TUB-CLG`
  is a damp-rated E3 run in the ceiling 2" off BA2E, y 196"-262", on the same PSU and dimmer.

## 6. What is NOT graded here

Nothing in the engine grades a finish's seam, radius, bond or colour. The splash's
clearance to devices and the glass channel are by hand (§3). The fabricator's shop drawing
governs the U's outline. The model's outline is the cap's.

## Sources

Read 2026-10-22:

- Moen 4794 rough-in specification: decks up to 2¾" plus up to 1¼" of finish —
  https://assets.moen.com/shared/docs/product-specifications/4794sp.pdf
- Corian Solid Surface Fabrication/Installation Fundamentals, L- and U-shaped pieces (13 mm
  minimum inside radius) — https://www.4willis.com/wp-content/uploads/2019/10/Corian-SS_Fabrication_Manual-Chapter20_Requirements_k-25705.pdf
- Corian Solid Surface Cutting and Cutouts, K-25289 (5 mm / 3/16" cutout radius, router only,
  ≥ 10 mm bits) — https://www.corian.com/sites/corian.com/IMG/pdf/k-25289-cutting-and-cutouts.pdf
- Corian 810P lavatory sheet (Jan 2026: 16⅜ × 13 × 5") —
  https://www.tools.corian.com/IMG/pdf/corian_lav_810p_new.pdf
- Swanstone BD-4896 specification (a pre-moulded 48 × 96 bathtub deck; no fabricator sheet
  was found) — https://www.manualsdir.com/manuals/288537/swanstone-bd-4896-specification.html
- JLC, "Working With Thin Solid Surfacing" (Swanstone sheet is not thermoformable) —
  https://www.jlconline.com/how-to/interiors/working-with-thin-solid-surfacing_o/
- Swanstone Carrara (221) colour, e.g. SS0369601.221 — https://firstsupply.com/Product/SWASS0369601CAR
- Quartz waterfall breakage and cultured-marble gelcoat renewal: the house's own reasoning
  (`PROD-SWAN-CONTOUR`), with no new document read for them.
