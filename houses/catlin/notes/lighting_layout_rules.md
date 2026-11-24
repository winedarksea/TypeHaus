# Catlin lighting layout rules (lighting review, 2026-11-23)

The rulebook the 2026-11-23 lighting review worked to. Fixture *selection* (catalog, tiers,
tape, drivers) is settled in `DESIGN-LOG.md` "Lighting review"; this note is about *where*
lights go. `advisory.luminaire_placement` grades the body/equipment/door rules below;
row alignment is taste and stays out of the checks.

## Ceiling geometry first

- Cans in a room or zone lie on at most two row lines per direction, on one pitch, symmetric
  about the zone's own axis (walls, an opening, a fixed feature), in clear joist mid-bays.
  A can that breaks the pattern needs a fixed reason.
- A can answers to **fixed** work only: sink, peninsula, range, vanity, laundry counter,
  built-in desk, shower. Movable furniture (sofa, freestanding desk, bed) gets a lamp or a
  wall sconce. Owner exceptions (2026-11-24): the lounge puzzle table takes two 5000 K day
  cans on the room's east-west centre line, and the main-bed armchair a can mirroring the
  desk can, for a balanced five.
- Bedrooms that get rearranged (BED1-3) take a generic 2x2 grid symmetric about the room,
  ignoring bed and desk; no bed-head lamps.
- Floor lamps read as clutter: none in the lounge (its only lamp is the dining counter FADO),
  none where a ceiling can will do. The attic studio keeps two, its sloped ceiling takes no can.
- Removing a furniture can names what takes over its task light: a lamp, an existing
  sconce, or nothing (with the lux figure).

## Kitchen

- Counter rows sit at or roomward of the counter front edge (about 26-30" off the wall),
  never between the upper face and the counter edge.
- Under-cabinet tape carries counter task light; cans carry aisle and general light.
  Peninsula row on the worktop centreline; one shared x pitch across rows.
- Tall faces (fridge, pantry columns): the row at least ~18" off the face.
- A can ahead of the cook, never over the range body; the hood's light lights the cooktop.

## Utility (garage, workshop, furnace, ESS, laundry)

- Tubes and strips go over aisles and in front of working faces, parallel to them. Never
  above an equipment body, shelving, a hung duct or pipe, the opener rail, or the open
  garage door panel.
- Garage rows run beside and between the bays and over the bench, not over a car roof.
  Good tubes go where a bench may stand; the stair and the centre take a porcelain keyless.
- One fixture kind, one circuit and one switch group per utility room (owner, 2026-11-24).
- NEC 110.26(D) working-space light and 210.70(C) equipment light stay satisfied.

## Living room (premium)

Layers: coves (ambient, colour), a clean wash/accent line parallel to each washed wall,
a warm general row, the 5000 K day pair over the puzzle table, the dining pendant.

## Lamps, day and night, control

- Replaceable lamp (E26/GU10/E12) or generic 12 mm tape; integrated only in the exceptions
  already on record. A new type is a numbered mark variant, not a new family.
- Plug-in lamps are placeables on plain receptacles, switched at the lamp (`plan/lamps.py`).
  They do not count in `advisory.room_illuminance`.
- Kitchen/dining, lounge and the main-floor study each have a day layer and a night layer.
  Night is warm (<=2700 K), low, on its own switch, made by mixing sources (under-cabinet
  tape, lamps, coves, pendant) before any tunable gear.
- No new smart controls: HA stays on grow lights, exterior runs and the existing relay groups.

## Hard constraints

`electrical.ceiling_can_framing`, `ceiling_box_framing`/`_support`, `code.R303_1` lumen
floors in windowless rooms (the theatre's six sconces are the whole margin; its ceiling takes
no box), `R303_7`/`R303_8`, `electrical.room_lighting`, `stair_lighting_control`,
`working_space_lighting`, `lighting_controls` (switch and load on one circuit),
`led_gear_access`, `integrity.light_run_host`, and each room's `advisory.room_illuminance`.
