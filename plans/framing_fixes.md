# Plan: Framing calculation + 3D presentation refinements (TypeHaus)

## Context

The framing engine already generates studs, plates, headers, floor joists, slabs, and rafters, but the 3D UI shows almost none of it correctly. Exploration found the root causes:

| Reported bug | Root cause |
|---|---|
| Floor joists + basement slab invisible | `Panel3D.tsx:172-201` renders only `walls` and `furniture`; `floors[]`/`solids[]` aren't even in the UI `Model` type ([types.ts:285](ui/src/model/types.ts#L285)) |
| Door headers slope diagonally | UI draws each member as a line from `(p0, z0_m)` to `(p1, z1_m)` — bottom elevation at one end, top at the other. Engine headers are horizontal (single scalar, [solver.py:171-175](packages/engine/src/typehaus/resolve/framing/solver.py#L171)) |
| Roof missing; studs "shrink" | No `buildRoof` in the UI (model.json *does* carry `roofs[]` with rafters + footprint). Shrinking studs are the correct gable-rake behavior — they only look wrong with no roof drawn. Also, no ridge beam member exists in the engine |
| Members render as thin lines | `Panel3D.tsx:293-302` uses zero-width `LineSegments`, ignoring `profile` |
| Corner studs missing | Engine emits only 1 supplemental corner stud ([solver.py:93-103](packages/engine/src/typehaus/resolve/framing/solver.py#L93)), no 3-/4-stud assembly |
| Attic knee story | Catlin attic authoring is mostly correct already (5' knee walls, I-joist roof assembly, and an RB-HOUSE Beam is *authored* at [attic.py:144](houses/catlin/plan/storeys/attic.py#L144) — but no resolver consumes Beam elements). The R305.1 habitable-attic check already exists ([rules.py:75-89](packages/engine/src/typehaus/checks/code/mn_residential/rules.py#L75)) — nothing to build there |

User decisions: configurable corners defaulting to 3-stud; solid instanced boxes built in the UI from model.json (not glTF); include engineered-lumber catalog, rim boards, trade visibility toggles, and true I-profiles for I-joists.

Dev env: no uv; run via repo-root `.venv` (Py3.9) + `PYTHONPATH=packages/engine/src`. Avoid 3.11-only runtime constructs despite pyproject saying >=3.11.

## Work packages (in order)

### WP0 — Fix raked-wall king-stud bug (engine)
`solver.py`: `stud_z1` is reassigned inside the stud loop (line 86) and the leftover raked value is passed to `_frame_opening` (line 109) as every king stud's top. Rename the loop-local, and compute each king stud's top at its own station on raked walls (pass a `top_at(s)` closure or `top_start/top_end` into `_frame_opening`). Headers stay horizontal.
**Accept:** new test — on a catlin ToRoof gable wall, each king's `z1_m` matches the roof plane at its own plan point minus plates.

### WP1 — Structured lumber catalog (engine)
New `packages/engine/src/typehaus/resolve/framing/profiles.py` (keep `tables.py` for existing consumers):
- Frozen `CrossSection(shape: "rect"|"i_joist", width_m, depth_m, flange_width_m?, flange_thickness_m?, web_thickness_m?, plies)` + `cross_section(profile: str)`.
- Parses everything in the repo today **without mutating stored profile strings** (structural checks at [checks.py:13-17](packages/engine/src/typehaus/checks/structural/checks.py#L13) key on exact strings): `"2x4"`…, multi-ply `"2-2x8"`, `"<depth> I-joist"` (flange 2.5" default / 3.5" for 14–16" series, flange thk 1.375", web 3/8"), `"3.5x11.875 LVL"`, `"N-1.75x<depth> LVL"`, `"1.25x<depth> rim"`, `"engineered-LVL"` fallback, safe rect fallback for unknowns. Constant `RIDGE_BEAM_DEFAULT = "3-1.75x11.875 LVL"` (3 plies × 1.75" = 5.25" × 11.875" ≈ user's "6x12").
- Fix plates emitting literal profile `"plate"` ([solver.py:143](packages/engine/src/typehaus/resolve/framing/solver.py#L143)) → use wall `spec.member`; category stays `"plate"`. Re-grep for consumers keying on profile `"plate"` (haus ls counters change cosmetically).
- `floors.py:_member_depth_m` regex → `cross_section(...).depth_m`.
- **Document the orientation convention once here** (stud: 1.5" along wall axis, 3.5" through wall) and mirror it in `types.ts`.
**Accept:** `test_profiles.py` covers every profile string in the repo + `"3-1.75x11.875 LVL"` → (0.13335, 0.3016) m; structural findings unchanged.

### WP2 — Configurable corner assemblies (engine)
`FramingSpec.corner_style: Literal["3-stud","4-stud"] = "3-stud"` ([assembly.py:17](packages/engine/src/typehaus/model/assembly.py#L17)). Current single supplemental corner stud + 2 endpoint studs *is* the 3-stud assembly; for `"4-stud"` emit a second supplemental at 2×1.5" offset with the same raked-top interpolation. Stable deterministic keys.
**Accept:** existing corner test passes on default; new test asserts two `corner` members with `corner_style="4-stud"`.

### WP3 — Rim boards at floor perimeters (engine)
In `floors.py:_resolve_floor`: emit 2 band-joist members capping joist ends along the outermost bearing boundaries, category `"rim"`, profile `f"1.25x{depth_in} rim"`, same z-band as joists (edge joists parallel to span already exist — don't double-emit).
**Accept:** catlin FS-SECOND/FS-ATTIC each get exactly 2 `rim` members; joist-count tests (which filter `category=="joist"`) still pass.

### WP4 — Ridge beam + rafter connections (engine + catlin authoring)
- `FramedMember` ([model.py:32](packages/engine/src/typehaus/resolve/model.py#L32)): add `orient: tuple[float,float] | None` (plan-frame axis for vertical members with p0==p1 — set from `d` in `frame_wall`; solves UI cross-section orientation without reaching back to the wall) and `connection: str | None`.
- `resolve/framing/roof.py`: resolve authored `Beam` elements whose node axis is coincident+parallel with the ridge line (match on line, not endpoints — RB-HOUSE spans y=8'8"→36') → emit `category="ridge_beam"` member, `z1=ridge_z_m`, `z0=z1−depth`. Trim rafter ridge ends back by half beam width with plane-consistent `z*_end_m`; annotate rafters `connection="ridge:adjustable-slope-hanger"` and `connection="eave:birdsmouth-1.17in"` (annotation only — box geometry doesn't carry seat cuts; the 2D detail pipeline owns that, per the eave-detail reference).
- Add `ConditionKind.ROOF_RIDGE` + emit a `BoundaryCondition` (`detail="lvl-ridge-hanger"`) for the transitions/detail pipeline to bind later.
- Gable roof with no authored beam → WARN finding `structural.ridge_support` (starter must stay error-clean).
- `attic.py:146`: RB-HOUSE size `"5.5x11.875 LVL"` → `"3-1.75x11.875 LVL"`.
**Accept:** RF-HOUSE gets one ridge_beam member; update `test_catlin_equivalence_m3.py:150-152` (rafter count stays 56; `z1_end` now ridge_z minus half-beam-width × slope); garage roof gets WARN, no error.

### WP5 — Serialization contract (engine → UI)
`server/model_json.py`: factor the 4 duplicated member serializations (lines 159, 238, 261, 274) into `_member_json(m)` emitting uniformly: existing fields + `z0_end_m`/`z1_end_m` (fixes floors/stairs omissions) + `shape`, `width_m`, `depth_m`, i-joist flange/web dims, `orient`, `connection`. **UI never parses profile strings.**
**Accept:** test asserts every member dict carries shape/width/depth; FS-SECOND joists have `shape=="i_joist"`; a stud carries `orient`.

### WP6 — UI types (`ui/src/model/types.ts`)
Extend `Member` with the WP5 fields; add `Solid` and `Floor` interfaces; add `members` to `Roof`; add `solids?`/`floors?` to `Model` (optional, matching existing `roofs?` pattern).
**Accept:** `cd ui && npx tsc --noEmit` clean.

### WP7 — Trade visibility toggles (UI)
`store.ts`: `visibleTrades: Record<"walls"|"framing"|"floors"|"concrete"|"roof"|"stairs"|"furniture", boolean>` + setter. `Panel3D`: one `THREE.Group` per trade; HUD buttons beside the nordic/schematic toggle; new `SceneApi.setVisibility` flips `group.visible` + `requestRender()` — no scene rebuild. Mapping per TODO.md: wall members→framing, floors→floors (hideable for stair continuity), solids→concrete, roof surface+members→roof.

### WP8 — Solid instanced member rendering + new builders (UI)
Extract `ui/src/three/members.ts`; replace the LineSegments block ([Panel3D.tsx:292-302](ui/src/components/Panel3D.tsx#L292)):
1. **Rect prismatic members:** one `InstancedMesh` per trade (unit box + per-instance matrix). Vertical (p0≈p1): footprint `width_m` along `orient` × `depth_m` across, height z1−z0. Horizontal/sloped: local X along the 3D axis, square-cut ends (stated approximation). Per-instance `setColorAt` by category.
2. **Raked members** (`z0_end_m != null` — raked plates, rafters): port the exact 8-vertex mesh from [emitter.py:add_member_box](packages/engine/src/typehaus/emit/gltf/emitter.py#L103) (vertical ends, sloped top/bottom), merged into one BufferGeometry per trade — correct shape, one draw call.
3. **I-joists:** three InstancedMeshes (top flange, bottom flange, web) sharing the member's axis transform; sloped I-joist rafters use the rotated-box transform (plumb ends not modeled — stated).
4. Angled-header bug disappears by construction (z0/z1 = bottom/top).
New builders in `setModel`: `buildSolid` (outline `ExtrudeGeometry`, same recipe as wall layers at Panel3D.tsx:260-270, concrete grey), `buildFloor`, `buildRoof` (sloped quads from footprint/eave_z/ridge_z/ridge_direction, slightly transparent so framing reads underneath + members incl. ridge beam), `buildStair`.
**Perf/hygiene:** ≤~6 draw calls per trade; extend `clear()` to traverse-and-dispose geometries (current code leaks); render-on-demand preserved.

### WP9 — Verification
- Engine: `PYTHONPATH=packages/engine/src .venv/bin/python -m pytest packages/engine/tests -q` — new tests per WP + updated `test_catlin_equivalence_m3.py`; `test_starter_resolves_clean` stays green.
- Contract: serve catlin (`PYTHONPATH=packages/engine/src .venv/bin/python -m typehaus.cli.app serve houses/catlin --port 8000`), then `curl /model` and assert: RF-HOUSE has a `ridge_beam` member; all members carry `width_m`/`shape`; FS-SECOND has 2 rims.
- UI: `cd ui && HAUS_ENGINE=http://127.0.0.1:8000 npm run dev` + `npx tsc --noEmit`. Visual checklist: horizontal headers; solid true-width studs (1.5" face along wall); gable studs shortening under a *visible* roof; ridge beam ≈5.25"×11.875" at x=18'; I-profile joists/rafters; slab + footings visible; 3-stud corners; trade toggles isolate framing/concrete/floors; orbit stays smooth (no RAF loop).

## Risks
- Profile strings are check keys — catalog is parse-only, never rewrites `member.profile`.
- `width_m`/`depth_m` orientation convention is the one silent engine/UI disagreement point — defined once in `profiles.py`, mirrored in `types.ts`, covered by the WP5 test.
- Rafter-trim changes golden assertions (`test_catlin_equivalence_m3.py:152`; check `test_detail_sheets.py` for attic section goldens).
- Plate profile change ripples into `haus ls` counters — re-grep consumers at implementation time.
