# M1 — Views: Slices, Transitions, Fork & Compare

**Purpose:** the view and boundary-condition layer over the resolved model. Schema lands in
WP1.3, condition derivation in WP1.4 (→ 11), coverage checks in WP1.8 (→ 12); the library
content and detail renderings land in M3 (→ 30 WP3.2). This doc is the design reference all
of those cite.

## Slices — one view mechanism for plans, sections, details (#36)

A **`Slice`** is an authored view of the resolved model produced by cutting it:

```python
Slice(tag="A-101", kind="plan", storey="main")                        # auto-scaffolded
Slice(tag="A-A", kind="section", plane=vertical(("N-3", "N-9")))
Slice(tag="DTL-EAVE", kind="detail", plane=vertical(("N-3", "N-9")),
      crop=around(("W-201", "RF-A"), pad=ft(2)),
      exaggerate=ExaggerationSpec(min_draw=inch(0.35)))
```

- **Floorplans are plan slices** (auto-scaffolded per storey at the 4' cut, overridable);
  sections are vertical slices at building extent; details are slices cropped tight around a
  boundary condition. All render through the one drawing IR (→ 20 §Drawing IR) and cut
  **real resolved geometry** — studs, plates, I-joists with bevel cuts and web stiffeners,
  layer polygons, concrete — the eave detail's structure is *cut from the model*, never
  re-drawn beside it. Sections and details cut the **whole-building** `ResolvedModel`
  (→ 02 §Pipeline), so a section spans storeys — including the rim/band zones the
  storey-stack conditions (#43) describe.
- **Overlay layer — 2D-only build-science content.** Flashing profiles, sealant beads, insect
  screens, gravel hatch, grade lines are deliberately never 3D-modeled. A detail slice
  carries overlay elements drawn in its 2D frame but **anchored to model references** — the
  same `(uid, face-role)` scheme dimensions use (→ 21b §Driven dimensions), plus named points
  ("top of foundation wall", "outer face of wall EPS") — so when an assembly gains a CI
  layer, anchors move and the overlay **re-flows**; an anchor that no longer resolves is an
  error finding, never a silently stale drawing. Most overlay content arrives packaged in
  `Transition` recipes rather than authored per slice.
- **Exaggeration, honestly labeled:** `ExaggerationSpec` clamps thin layers (membranes,
  gaskets, sill seal) to a minimum draw thickness and re-lays-out the stack 1-D along the
  assembly normal so neighbors stay adjacent; annotations and dimensions always state
  **true** dimensions. A detail-slice affordance only — plans and sections stay true-scale.
- **Annotations are shared, placed per view.** An `Annotation` exists once, anchored to model
  refs; each Slice holds `AnnotationPlacement(annotation_ref, visible, leader/text
  overrides)`. The same note can appear as a pin in the 3D panel, on the working floorplan,
  and on the permit detail — each placement independent, so "permit-ready" composition is
  show/hide/move, not re-authoring. `notes/*.md` frontmatter binds prose to slice/transition
  tags as before.
- **UI slice manager** (→ 21b): list of all views; draw a cut line on the plan to create a
  section/detail; the 3D panel shows slice planes as widgets with cross-highlighting.

## Transitions — bridge details as first-class boundary conditions (#37)

Assemblies describe the *field* of a wall; buildings fail at the **boundaries between**
fields. The existing eave and basement details are exactly this — not drawings of a wall but
of the wall↔roof and wall↔foundation conditions; window waterproofing is the wall↔opening
condition. So boundaries are modeled explicitly:

- **Conditions are derived, never authored.** The resolver enumerates every boundary
  condition in the model: wall↔roof edges (eave/rake, per plane), wall↔foundation bearing
  lines, opening perimeters (head/jamb/sill × host assembly), assembly-change nodes (→ 11
  §Wall variation), wall↔slab, soffit↔wall, and — per #43 — **storey-stack** (the rim/band
  condition: wall below ↔ FloorSystem ↔ wall above) and **stack-width-change** (assemblies of
  different widths stacked, e.g. catlin's 2x6 → 2x4 shelf, with per-layer face jogs
  quantified). `haus explain --transitions` prints the distinct conditions with instance
  counts — the model's detail schedule is **enumerable by construction**.
- **Condition-key grammar — resolved.**

  ```
  ConditionKey  = (kind: ConditionKind, participants: tuple[Ref, ...])
  ConditionKind = eave | rake | wall_foundation | wall_slab
                | opening_head | opening_jamb | opening_sill
                | assembly_change | soffit_wall
                | storey_stack | stack_width_change
  ```

  Participants are ordered by role, not sorted alphabetically — `(storey_stack,
  asm_below, floor_system, asm_above)` and `(opening_sill, opening_type, host_assembly)` are
  unambiguous. A `Transition` binds a **pattern** over keys:
  - **exact ref** — `"EXT-2X6-CI"`;
  - **any** — `"*"`;
  - **predicate** — a small closed set: `variant_of("EXT-1")` (the base and all its
    variants), `layers_end_with("furring", "cladding")` (assembly-family matching by
    outermost layers), `kind_is(ICF)`.
  - **Specificity order:** exact > predicate > `*`; ties broken by declaration order (plan
    before `library/`). Exactly one binding wins per condition instance; a multi-match at
    equal specificity is an info finding so overlapping library items get noticed.
- **A `Transition` binds a condition pattern to:**
  1. an **overlay recipe** — parametric 2D elements (§Slices) anchored to *both* sides'
     faces (membrane lapping from sheathing onto foundation foam; Z-flashing + drip edge into
     the gutter; window sill pan turning up the jambs; rim-band air-sealing tape from
     sheathing below to sheathing above). Anchoring to both sides is what makes the bridge
     re-flow when either side's assembly changes;
  2. **notes** (the `notes/*.md` binding, printed with the detail);
  3. optional **`ConstructionRule` references** — the pre-resolve rules (#45) responsible
     for real 3D consequences such as birdsmouth/bearing-plate choice, I-joist web stiffeners,
     or blocking. The Transition verifies that its rule resolved and illustrates its result;
     it cannot direct the solver. This removes a resolve → transition-match → solver-directive
     → resolve cycle.
  4. optional **continuity declarations** — which control layers (AIR/WATER/VAPOR/THERMAL)
     this transition carries across the boundary; consumed by the continuity check below.
- **Interface-first matching (#44):** a condition supplies participating interface roles and
  compact construction families in addition to assembly refs. Patterns match roles/family
  first; an exact assembly ref is an optional specialization. Thus an eave detail survives a
  CI-thickness change or compatible variant without treating unrelated assemblies as equal.
- **Coverage is checked; change is safe:**
  - an unbound condition → warn finding ("(eave, EXT-1-BRICK, ROOF-A): no transition — 2
    instances"); `/permit-check` requires full coverage;
  - swapping an assembly re-keys its conditions: still matched → overlays re-flow silently;
    no longer matched → the finding names exactly the detail work the change created.
    **This is the answer to "when does a local swap become a discontinuity": the moment it
    creates a condition no transition covers.**
  - a transition whose anchors no longer resolve (the layer it flashed over was removed) is
    an error finding, never a silently wrong drawing.
- **Control-layer continuity rides on this:** layers tagged with `control` roles (→ 10
  §Element model) let an advisory check walk each control layer (air/water/vapor/thermal)
  across junctions **and stack edges (#43)**; a control layer that dead-ends at a boundary
  whose transition doesn't declare continuity for it is a warn — the eave, sill, and rim-band
  details exist precisely to close these paths, and now the model can say whether they do.
- **Library seam:** transitions are prime `library/` content — the zero-overhang metal-roof
  eave, CI-wall-onto-ICF sill, flanged-window flashing kit, **rim-band air-sealing**,
  **stack-width-change shelf** — each shipping its overlay recipe, notes, continuity
  declarations, and the assembly patterns it covers. The existing catlin details port as the
  first library transitions (→ 30 WP3.2).

## Fork & compare — in-plan variants (#38)

Early design is a usable mess on purpose. Forking is duplication with provenance — no git
re-implementation, no CRDT:

- **Fork units:** an assembly forks as a sibling declaration (`variant_of=…, active=False` —
  the variant mechanism with the substitution left open-ended); a storey forks as a sibling
  file (`plan/storeys/main__b.py`, its storey declared `variant_of="main", active=False`).
- **One active member per variant set** builds into IFC/sheets/checks. Inactive variants
  still parse and resolve (their own resolve pass) so compare is live. Yes, that is a full
  duplicate resolve — heavy and pragmatic; a resolve is seconds, and the honest copy beats
  overlay/patch schemes that drift (rejected, → 01 §Rejected).
- **Identity:** forked elements get **fresh uids** (uniqueness holds) with `forked_from`
  retained per element, so compare aligns elements pairwise without heuristics (the → 20
  §Diff Hungarian matcher covers additions); cross-variant references are integrity errors.
- **Compare view** (→ 21b): side-by-side canvases, linked pan/zoom, element-level delta list
  (same classifier as `haus diff`), takeoff/R-value deltas.
- **Promote = swap `active` + uid remap:** promoting a variant deactivates the original and
  remaps surviving elements **back to their `forked_from` uids** (#33 machinery), so
  GUID/diff continuity and external references survive; the demoted original can be kept as a
  variant or deleted. One journaled, undoable operation.
- **Bounded mess:** variants don't nest (a fork of a fork joins the same set), and
  `haus build` nags (warn finding) when a set's inactive members exceed a preference or go
  long untouched — a nudge to promote or delete, never a blocker.

## Risks owned

- **Risk 7 — overlay/transition anchor robustness** (shared with → 30): anchors reuse the
  dimension `(uid, face-role)` scheme — one resolver, one failure surface; unresolvable
  anchor = error finding; golden-image tests re-render every `library/` transition across
  assembly parameter sweeps (CI thickness bumps, layer swaps, lining overrides).
- **Risk 8 — transition-coverage noise:** coverage findings are warn-tier during design and
  only hard-gate in `/permit-check`; the predicate patterns above are what keep one library
  transition covering a whole assembly family, so the distinct-condition count stays low.

## Open questions — resolved in this doc

- **Condition-key + wildcard pattern grammar** → §Transitions (role-ordered participants;
  exact / predicate / `*` with specificity order and single-winner rule).
- **Where storey-stack conditions come from** → derived by the WP1.4 vertical stacking pass
  (→ 11 §Vertical stacking); this doc defines only their keys and bindings.
