# Sunken garden — framing water protection

Model: `params/sunken_garden.py`; tape quantities: `takeoff/member_protection.py`.

The current frame has two porch wall ledgers (`BM-SG-LDGW/E`), two treated-glulam
balcony beams (`BM-SG-BLW/BLE`), and four concrete balcony columns
(`PT-SG-B{R,F}{1,3}`). The porch joists span ledger to ledger; the balcony joists
span between the glulams. See `notes/balcony_moment_columns.md` §12 for the
2026-09-22 frame redesign.

## 1. Butyl tape on framing tops

Both floor systems and the ledgers and balcony beams carry `top_protection`.

| Members | Framing-top width | Tag |
|---|---|---|
| Joists, rims, blocking and porch ledgers | 1.5" | `butyl-tape` |
| The two balcony glulams | 3.5" | `butyl-tape-beam` |

The BOM reads the member width from `cross_section`. Cover the whole framing top;
a 3 1/8" roll does not cover a 3 1/2" glulam.

On `FS-SG-DECK`, tape separates the aluminium plank from the treated wood below.
On `FS-SG-PORCH`, the composite boards are gapped, so rain reaches the framing tops.
Keep the specified separation between aluminium and copper-treated wood at any
added flashing or hardware.

## 2. Drained balcony beam seats

Each of the four concrete column heads carries a modelled `SS316-SHIM-35`
standoff pack (`CN-SG-STDF-*`), with a 1/2"–1" drained gap and no grout island.
The column top has a wash and drip lip. The pack is 316 stainless, with EPDM or
HDPE isolation where it meets the zinc-coated `HETA20Z` tie pair.

The pack supports the beam; the cast-in tie pair restrains it. The lapped shim
leaves accommodate the tilted beam soffit. See
`notes/balcony_differential_movement.md` §3 for that bearing detail and
`params/column_heads.py` for the head-connector specification.

## 3. Treatment procurement and field cuts

**Confirm the supplier's KDAT preservative before ordering.** The treatment
chemistry remains open in `notes/catlin_truss_engineering.md` §9; the selected
fastener and connector coatings must be checked against the supplied treatment.

The exterior-framing specification calls for **2% copper naphthenate on every
field-cut end, notch and drilled hole**, per AWPA M4. See
`notes/north_entry_structure.md` §6 and `notes/composite_decking.md`.

## 4. Preserve the watertight balcony surface

`FS-SG-DECK` carries no equipment penetrations. The heat pumps are on ground
pads (`notes/heat_pump_ground_pad.md`). Any future deck-mounted equipment must
satisfy `mep.deck_equipment_support_coverage`; its anchors must land in authored
sacrificial blocking rather than in a beam.
