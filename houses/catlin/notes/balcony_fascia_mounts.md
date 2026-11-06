# Balcony fascia-mount geometry

`RL-SG-BALCONY` is the Williams Colonial panel on Ultralox 3 inch fascia mounts. Nine posts
serve eight bays: seven straight mounts and two outside corners. Every corner bracket meets a
straight bracket across its panel, as the guide requires. The deck, fascia, mounts, rails and
pickets share the resolved deck plane. The bottom-rail clearance is 3 inches.

## The detail (2026-11-05)

- **Fastener:** four SD04964 5/16 × 6 inch structural screws per bracket, into SG ≥ 0.50
  backing. The stack is ¼ bracket + 1 PVC fascia + 4½ SYP = 5¾ inches, so the tip ends
  ¼ inch past the last ply.
- **Backing:**
  - Flanks: the 2x12 KDAT rim plus two blocks tight to its inside face, in each bay beside
    the post's joist line.
  - Front: the edge joist plus two 20-inch sister plies inboard of each interior post, and a
    block to the next joist.
  - Rear: the flank rims oversail the plank by 1½ inches, so the end posts' rear screws
    hold 1⅜ inches (≥ 4D) to the cut end. The north edge joist is doubled into that
    oversail, which puts wood behind the upper rear screws and gives the base flashing a
    bed. It runs in two pieces that break with the flashing beyond D-S-BALCONY's casing,
    where the door's own threshold outriggers cross the gap.
  - The movement gap to the cladding is now 1¾ inches (it was 2¾).
- **Corners:** FM244390 wraps the framed corner. Its outboard walls run full, and its
  inboard walls jog 45° onto flanges that start ⅞ inch past the fascia corner, leaving the
  post's corner open (product drawing). Its holes sit within 4D of the corner by the
  maker's own detail, so the resolver grades corner screws for reaching wood and not for end
  distance. The flank rims lap the edge joist's end, so the wrap sits on solid framing.
- **Post:** the stock 48-inch tube (post kit with cap), uncut. The post bottom is flush
  with the bracket bottom on its ⅛ inch insert, and the bracket top is ½ inch below the rim
  top. That gives 48 − 6 + ⅛ − 2 = **40⅛ inches** over the plank, against R312.1.2's 36.
  The height is derived in params from `post_tube_length`. The resolver refuses a post
  longer than the tube rather than shortening it.
- **Drip:** TR-SG-DRIP is four pieces, one per front bay, field-notched and sealed at each
  bracket's front leaf. The brackets still sit over TR-SG-APRON's upstand.
- **Bought beside each bracket:** the post kit with cap, the bracket screws,
  self-drilling post screws, and the post-bottom plug. All of it sits inside the per-LF
  railing rate.

`resolve/railings/fascia_backing.py` walks each screw through `FS-SG-BALCONY.members`. It
raises "misses its backing" unless the tip lands within ½ inch past the last ply contiguous
with the band (gap ≤ 1/16 inch). For a straight bracket it raises "end distance" under 4D to
the band's end.

## Hand check for the plan reviewer (no engine check)

The load is 200 lb outward at the top rail (R301.5), resisted by one straight bracket. Take
the pivot at the bracket heel bearing on the fascia, 8 inches below the walking surface:

- Moment: M = 200 × (40.125 + 8) = 9,625 in-lb.
- Screw rows are 5½ and 1½ inches above the heel, two screws per row. Elastic share:
  Σd² = 2(5.5² + 1.5²) = 65 in², so T(upper) = 9,625 × 5.5 / 65 = **814 lb per screw**.
- Capacity, using NDS 12.2-1 (lag screw) as the proxy for the 5/16 inch structural screw:
  W = 1800 G^1.5 D^0.75 = 1800 × 0.55^1.5 × 0.3125^0.75 = 307 lb/in.
- Thread in SYP is 4½ − ¼ tip = 4¼ inches. With C_D = 1.0 and C_M = 0.7 (wet service),
  W′ = 307 × 4.25 × 0.7 = **913 lb**. Ratio 0.89.

Open for the reviewer: the blocks and sisters must carry their share back to the joists. That
means a nail schedule for the backing, which the model does not draw. Ultralox's written OK for
SD04964 over 1 inch of PVC fascia is a TODO.

## Product evidence and display limits

- [Ultralox 2025 Product Guide](https://www.ultralox.com/wp-content/uploads/2025/06/Ultralox-Product-Guide.pdf),
  p.37 (**governs**). Wood fascia: 4 × SD04964 5/16 × 6 inch screws into SG ≥ 0.50
  blocking. 48-inch tube for the 42-inch system, cut to fit. Post bottom flush with the
  bracket bottom; bracket top ½ inch below the rim top. FM044300 straight, FM144390 inside
  and FM244390 outside corner, 6 inch overall bracket height; FM025900 foot block.
- The June 2024 fascia instruction PDF (5/16 × 4 inch through-bolts) now returns 404 and is
  **superseded**. Its bolts could not reach a block.
- [ESR-3485 Figure 10](https://icc-es.org/wp-content/uploads/report-directory/ESR-3485.pdf):
  3.036 inch pocket, ¼ inch section, 5.64 inch straight flange, 4.63 × 4 inch hole pattern,
  1 inch post screws. The report's fascia row is concrete only.

Threads, drives, head and washer thickness, the corner-hole inset, the corner jog, the
post-bottom insert and the foot-block contours are display geometry, named in
`FasciaMountSpec`. They are not a drilling template.

**Shallow-slope compatibility remains a product assumption.** The deck-following layout runs
at roughly 1.2°. Williams documents 30–40° for its stair panels, which does not establish a
shallow-slope rating for the level panel. Confirm the panel/clip combination before ordering.

Mounts, fasteners and foot blocks resolve once into body meshes, shared by model.json, the
viewer, glTF and IFC. Foot-block screws (2 inches) enter the fascia below the plank. Run
`npm --prefix ui run railing-review` after rebuilding model.json for the close-ups.
