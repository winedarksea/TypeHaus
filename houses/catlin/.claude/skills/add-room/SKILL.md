---
name: add-room
description: Add a room to the plan — nodes + enclosing walls + a Room claim, then build, check, and render a plan snapshot to verify the result.
---

# /add-room

Add a new room to the house and prove it closes.

## Steps
1. **Read intent first.** Skim `brief.md` (spatial program, must-haves) and
   `preferences.toml` (envelope/structure targets) so the room fits the design.
2. **Pick the storey file** under `plan/storeys/` (default `main.py`). Read it to learn the
   existing node tags, wall assembly tag (e.g. `EXT_2X6` / `HOUSE_WALL_2X6_WITH_ZIPR`), and
   coordinate frame.
3. **Add geometry** to the editable lists, keyword-args only, dimensions via `ft(...)`:
   - `NODES`: the room corners (`Node(tag=..., position=pt(ft(x), ft(y)))`).
   - `WALLS`: enclosing `Wall(...)` edges between the new nodes, `assembly=` an existing tag.
   - `ROOMS`: one `Room(tag=..., seed=pt(...), occupancy=Occupancy.<KIND>, floor_finish=...)`.
   Leave `uid=` off new elements.
4. **Mint uids:** run `haus fmt .` (assigns a fresh uid to every element missing one).
5. **Build + check:** `haus build .` then `haus check .`. Resolve every ERROR (a gap in the
   wall loop, an unresolved assembly tag, an open room).
6. **Look:** `haus render --view plan .` and read `out/render/plan_<storey>.png`. Confirm the
   room closes, walls meet at corners, and the space reads sensibly. Fix and re-render.
7. **Report** the final plan snapshot and the room's resolved area (from `haus ls`).

## Guardrails
- Never edit `out/`. Never change an existing `uid`. No math/loops in editable files.
- If a wall won't close, check that adjacent walls share node tags exactly.
