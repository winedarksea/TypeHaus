# Balcony fascia-mount geometry

`RL-SG-BALCONY` uses the existing Williams Colonial panel geometry on Ultralox 3 inch
fascia mounts. Nine posts serve eight bays: seven straight mounts and two outside corners.
The deck, fascia, mounts, rails and pickets share the resolved deck plane. Guard height is
42 inches vertically above the protected walking edge; bottom-rail clearance is 3 inches.

The fascia is entirely outside the framing. Its former centreline placement overlapped the
flank rim. Moving it outside the 1¼ inch rims requires 60⅛ inch maximum post spacing to
retain four front bays; the actual front bays remain below that limit and below the
manufacturer's 72.43 inch maximum. Guard rollover backing is located from the same mount
stations, with flank blocks behind the bolt tails so the nuts remain accessible below.
The front gutter remains 1 inch below the lowest complete bracket, including its pocket.

## Product evidence and display limits

- [Ultralox fascia instructions, June 2024](https://ultralox.com/wp-content/uploads/2024/07/ultralox-aluminum-railing-fascia-mount-install-instructions.pdf):
  bracket top ½ inch below the rim, four 5/16 × 4 inch through-bolts with front/back washers
  and nuts, four post screws, bottom insert, and a fascia support foot at panel midpoint.
  The screw-length text and illustration disagree; the model uses the 1 inch length also
  shown in ESR-3485 Figure 10.
- [Ultralox product guide](https://www.ultralox.com/wp-content/uploads/2025/06/Ultralox-Product-Guide.pdf):
  FM044300 straight bracket, FM144390 inside corner, FM244390 outside corner; 6 inch overall
  bracket height. The 5 inch mounting flange is distinct from the full pocket height.
  FM025900 identifies the fascia foot block.
- [ESR-3485 Figure 10](https://icc-es.org/wp-content/uploads/report-directory/ESR-3485.pdf):
  3.036 inch pocket, ¼ inch section, 5.64 inch straight flange width, 4.63 × 4 inch mounting
  hole pattern. The report's concrete anchorage row is not substituted for wood bolts.

The bracket shell and straight hole pattern use these dimensions. Threads, screw drives,
head/washer thickness, corner-hole inset, post-bottom insert and foot-block contours are
simplified display geometry. These contours are identified in `FasciaMountSpec`; they are
not fabrication drawings or a substitute for the supplied parts.

**Shallow-slope compatibility remains a product assumption.** The continuous roughly 1.2°
deck-following layout is the owner's chosen configuration. Williams documents 30–40° for
its stair panels; that range does not establish a shallow-slope rating for the level panel.
Confirm the panel/clip combination before ordering. No slope-capability verdict is inferred
from the successful geometry checks.

Mounts, fasteners and foot blocks are resolved once into body meshes shared by model.json,
the production 3D viewer, glTF and IFC. Their quantities remain included in the existing
railing rate; display subparts do not create additional priced railing rows. Foot-block
screws enter the fascia below the plank or the bottom rail, leaving the deck surface intact.

Run `npm --prefix ui run railing-review` after rebuilding model.json for production-builder
close-ups, including an explicitly labelled framing cutaway showing the inner nuts.
