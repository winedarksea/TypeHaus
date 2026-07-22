# Reviewer Ideas for Design
Note: reviewers provided general input not tailored to the app in particular


## Reviewer One
1. Reimagining the Layout: "Canvas-First"

The dual-sidebar approach often feels claustrophobic because it boxes the user in. You want the user to feel like they are working on a massive, open blueprint.

    The Figma/Linear Approach: Make the canvas take up 100% of the screen. Instead of rigid, heavily bordered sidebars, use floating panels with slight drop shadows over the canvas.

    Left Side (Creation): A slim, iconic floating toolbar for your drawing/placement tools. No text, just highly intuitive, sleek icons.

    Right Side (Contextual Inspector): This is your larger input panel. Crucially, it should be empty or hidden until something is selected. When a user taps a wall, the right panel slides in or populates with only the properties for that wall.

    2D/3D Split Screen: Instead of a rigid line down the middle, consider a Picture-in-Picture (PiP) approach for quick references, or a highly polished "Split View" toggle in a top-center floating pill menu.

2. Solving the "Homeless" Features (Building Science)

Building science is your differentiator. These features shouldn't be hidden; they need intuitive design patterns.

    Permit Checks (The "Linter" Pattern):

        Pattern: Borrow from code editors like VS Code. Place a subtle, persistent Status Bar at the bottom of the screen.

        Execution: On the right side of the status bar, show a pill that says "✅ 0 Code Conflicts" or "⚠️ 3 Permit Issues". When the user clicks it, a bottom drawer slides up detailing the issues (e.g., "Stair run length violates IRC 2021", "Inadequate egress window"). Clicking an issue centers the 2D canvas on the problem area.

    Transition Details & Wall Assemblies (The "Callout Node" Pattern):

        Pattern: Transition details don't belong in a menu; they belong on the plan.

        Execution: Introduce a "Details Layer." When activated, small, elegant circular nodes (callouts) appear on wall intersections, roof-to-wall joints, and foundations. Tapping a node enters a Focus Mode (taking over the screen) to show the exact transition drawing, moisture barrier overlaps, and thermal bridge mitigation.

3. Handling Complex Dialogues (Stairs, Windows, Assemblies)

Pop-up modals are visually jarring and obscure the canvas.

    Focus Modes / Drill-Downs: When a user edits a complex wall assembly stack, smoothly animate the rest of the canvas into a faded/dimmed state, and bring the wall segment to the center. Bring in a dedicated "Assembly Editor" sidebar. Once done, they click a back arrow (breadcrumbs) at the top left to return to the main floorplan.

    Direct Manipulation: For stair design, instead of a dialogue box with 15 text inputs (rise, run, stringer depth), use drag handles right on the 2D/3D canvas to stretch the stairs, with floating text boxes near the cursor showing real-time dimension updates.

4. Taming Layers, MEP, and Framing

When you have Architectural, Framing, Plumbing, HVAC, and Electrical layers, standard checkbox lists become tedious.

    Use "Workspaces" or "View Modes": Group layers into predefined workspaces accessible via a top-left dropdown or a segmented control at the bottom center.

        Modes: "Architecture," "Structural/Framing," "MEP," "Building Science/Thermal."

        When the user clicks "MEP," the UI automatically dims the architectural walls to 30% opacity, turns off framing, and highlights plumbing and electrical in vibrant, distinct colors (Blue for water, Red for HVAC, Yellow for electric).

        When "Building Science" mode is on, the 2D plan could show a color-coded thermal envelope overlay.

5. Interaction Details (Click/Tap & Drag)

    Snapping with Haptics: If targeting mobile/iPad, or trackpads, use subtle haptic feedback when a wall snaps to 90 degrees or a plumbing fixture snaps to a water line.

    Hover States (Desktop): When the cursor hovers over an interactive element, gently highlight it and show a micro-tooltip with its primary data (e.g., "Exterior Wall - R-26").

    Spacebar Panning: Adopt the standard design-tool behavior: holding Spacebar turns the cursor into a hand for dragging/panning the canvas, and the scroll wheel zooms.

6. Aesthetic Tips for an "Elegant" Feel

To move away from the ugly, clunky CAD look, focus on modern typography, spacing, and color theory:

    Color Palette: Use a muted "Dark Mode" (like charcoal, not pure black) or a clean "Light Mode" (off-white, paper-like background). Use vibrant accent colors only for selections and MEP systems.

    Typography: Use a modern, crisp sans-serif typeface (like Inter, SF Pro, or Roboto). Use tabular figures (monospaced numbers) for all dimensions so numbers don't jump around when resizing a wall.

    Lines and Grid: Make the background grid highly subtle (e.g., 5-10% opacity). Give architectural walls crisp, dark outlines with clean white/grey fills, looking like a high-end vector illustration rather than a pixelated CAD export.

    Glassmorphism (Sparingly): For your floating toolbars or the permit-check drawers, using a slight background blur (acrylic effect) allows the blueprint lines to pass underneath, making the app feel incredibly modern and maximizing the feeling of space.

## Reviewer Two

The strongest direction is **not** to make the existing sidebars prettier. It is to reduce how much permanent interface surrounds the drawing.

The application should feel like:

> **A large, calm drawing surface with intelligent controls appearing near the object or task being worked on.**

A good reference blend would be:

* Shapr3D’s selection-adaptive commands
* Figma’s canvas, inspector, and command search
* Onshape’s task-dependent toolbars and parametric history
* Autodesk Forma’s analysis layers and performance-oriented views

Shapr3D explicitly recommends tools based on the current selection, while Onshape changes its toolbar according to whether the user is sketching, assembling, or performing another operation. Figma provides searchable actions for less frequently used commands, and Forma organizes environmental information as selectable analytical layers. Those are particularly relevant patterns for your application. ([Shapr3D Help Center][1])

## Recommended application shell

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Project  ▸  First Floor     DESIGN | ANALYZE | DOCUMENT      Undo  Search│
├──────┬───────────────────────────────────────────────────────────┬───────┤
│ Tool │                                                           │       │
│ rail │                     2D / 3D CANVAS                        │ Insp. │
│      │                                                           │       │
│      │       contextual controls appear near selection           │       │
│      │                                                           │       │
├──────┴───────────────────────────────────────────────────────────┴───────┤
│ Level · Scale · Snap · View lens · Selection · 3 warnings · Units       │
└──────────────────────────────────────────────────────────────────────────┘
```

The components should have sharply differentiated responsibilities:

| Region                   | Responsibility                                          |
| ------------------------ | ------------------------------------------------------- |
| Top bar                  | Project, workspace, view, undo, search, collaboration   |
| Narrow left rail         | Starting tools only                                     |
| Optional left drawer     | Project hierarchy, levels, systems, views               |
| Canvas                   | Drawing, manipulation, temporary dimensions, feedback   |
| Right inspector          | Properties of the current selection or active operation |
| Bottom status rail       | Scale, snapping, constraints, warnings, coordinates     |
| Expandable bottom drawer | Issues, checks, history, logs, schedules                |

The critical rule is:

> **Only one large side panel should normally be open.**

The left project drawer and right inspector can coexist on wide monitors, but the application should not require both to remain expanded.

A reasonable desktop geometry is:

* Top bar: 44–52 px
* Tool rail: 48–56 px
* Project drawer: 220–280 px
* Inspector: 320–400 px, resizable
* Status rail: 28–36 px
* Canvas: preferably at least 65% of the window width

On tablets, both drawers should overlay the canvas temporarily rather than permanently compress it.

# 1. Replace the tool sidebar with a task rail

The left side should not contain every possible command. It should contain approximately six high-level tool groups:

* Select
* Build
* Openings
* Components
* Systems
* Annotate
* Measure

Selecting **Build**, for example, could open a small palette containing:

```text
Wall
Room
Floor
Roof
Foundation
Column
Beam
Stair
```

Once a tool is active, its main parameters belong in a **context bar or inspector**, not in another permanent toolbar.

For example, activating Wall could produce:

```text
[Exterior 2×6 wall ▾] [Centerline ▾] [Level 1 ▾] [Height: 9'-0"] [Chain ✓]
```

This bar could float immediately above the canvas or appear beneath the top bar. It disappears when Wall mode ends.

This is materially cleaner than reserving an entire sidebar for tool options.

## Add a command palette

A searchable command interface should handle commands that users know exist but cannot immediately locate:

```text
⌘K
> show air barrier
> convert wall type
> generate section
> run stair check
> isolate plumbing
```

It should also show shortcuts, recent commands, and matching object types. Figma uses this pattern to expose a large action space without putting every command permanently onscreen. ([Figma Help Center][2])

# 2. Make the right panel a true contextual inspector

The right inspector should answer:

> “What can I change about the thing I have selected?”

It should not become a miscellaneous configuration panel.

For a wall, it might contain:

```text
WALL
Exterior Wall — Type W04

Geometry
  Length             14'-6"
  Height              9'-0"
  Base constraint     Level 1
  Top constraint      Level 2
  Alignment           Sheathing face

Assembly
  W04 · 2×6 + exterior insulation
  Thickness           10⅝"
  Nominal R-value     R-31
  [Edit assembly]

Behavior
  Load bearing        Yes
  Room bounding       Yes
  Exterior            Yes

Documentation
  Mark                W-104
  Notes               —
```

Use three levels of disclosure:

1. **Primary fields:** frequent values, always visible.
2. **Collapsed sections:** less common values.
3. **Dedicated editor:** complex assembly or component design.

Do not put 40 equally prominent controls in a scrolling panel.

Other useful inspector behavior:

* Search properties by name.
* Pin one or two fields while changing selections.
* Multi-selection shows common fields.
* Mixed values are shown explicitly.
* Units can accept expressions such as `9 ft + 3.5 in`.
* Dimensions use tabular numerals.
* Every calculated value identifies whether it is user-entered, inherited, or derived.
* Hovering a property highlights the corresponding geometry.
* Changing a field previews the result before committing.

# 3. Separate workspaces from visibility layers

Your application has at least three different concepts that should not be conflated:

1. **What task am I performing?**
2. **What objects are visible?**
3. **How should visible objects be represented?**

These should become separate controls.

## Workspace

A workspace alters the primary tools and inspector emphasis:

```text
DESIGN
ANALYZE
DOCUMENT
```

You might eventually add specialist workspaces:

```text
Architecture
Envelope
Structure
Mechanical
Electrical
Plumbing
```

But those may work better as disciplines inside Design rather than top-level modes.

## Visibility

Visibility determines which model categories are shown:

```text
Architecture
Structure
Framing
HVAC
Plumbing
Electrical
Site
Annotations
Reference geometry
```

## Representation or detail level

Representation determines how those objects are drawn:

```text
Conceptual
Schematic
Detailed
Fabrication
```

Thus framing can be:

* hidden;
* shown schematically;
* shown as exact members;
* shown as fabrication-level geometry.

This is substantially clearer than treating “exact framing versus schematic framing” as unrelated layers.

# 4. Replace layer-checkbox overload with saved view recipes

Users should rarely need to manipulate dozens of layer toggles individually.

Provide named view recipes such as:

* Architectural plan
* Presentation plan
* Framing plan
* Foundation plan
* Plumbing coordination
* Mechanical coordination
* Electrical plan
* Air-sealing plan
* Permit plan
* Egress review
* Construction detail view

A compact filter bar could show:

```text
[Level 1] [Architecture] [Schematic] [Existing + New] [Permit view]
```

Each item is a filter chip. Clicking it opens the underlying options.

The full layer tree still exists for advanced control, but common work happens through presets. Forma’s organization of site data and environmental results as navigable layers is a useful precedent for analysis-oriented visibility rather than a single undifferentiated layer list. ([Autodesk][3])

Allow users to save their current combination as a named view:

```text
Save view as: “Second-floor framing coordination”
```

Saved views should include:

* Level and cut plane
* Camera
* Visible disciplines
* Detail level
* Analysis lens
* Section box
* Annotation visibility
* Color overrides

# 5. Introduce building-science “lenses”

This is the feature that can make the application feel fundamentally different from conventional residential CAD.

A **lens** is not merely visibility. It semantically transforms the model to answer a particular question.

Suggested lenses:

```text
Normal
Structure
Water control
Air control
Vapor control
Thermal control
Fire separation
Acoustics
Drainage
Ventilation
Daylight
Energy
Code
```

## Example: air-control lens

When active:

* Ordinary geometry becomes muted.
* The designated air-control layer becomes visually dominant.
* Connections between assemblies are shown as continuity paths.
* Discontinuities receive numbered markers.
* Penetrations are highlighted.
* The right inspector reports the selected assembly’s air-control material.
* The bottom rail reports total unresolved discontinuities.

## Example: thermal lens

Show:

* Insulation location and effective thickness
* Framing fraction
* Major thermal bridges
* Approximate effective R-value
* Interior surface-temperature risk
* Slab-edge, rim-joist, parapet, and opening transitions

## Example: drainage lens

Show:

* Roof and site drainage direction
* Drainage planes
* Flashing paths
* Weeps and outlets
* Potential reverse laps
* Below-grade drainage and capillary breaks

Every lens needs a persistent legend. Never rely on color alone: combine color with line pattern, icons, labels, or hatch. Important visual controls and indicators should retain sufficient contrast; WCAG specifies a 3:1 contrast threshold for meaningful non-text graphics. ([W3C][4])

# 6. Give permit and performance checks an “Issues” system

Checks should not live in a conventional settings panel. They should be a first-class review system similar to compiler diagnostics or engineering-model coordination issues.

Place a compact design-health indicator in the top or bottom bar:

```text
Design health:  2 errors  ·  7 warnings  ·  14 advisories
```

Selecting it opens an Issues drawer:

```text
ISSUES

ERROR
✕ Stair headroom below minimum                     Level 2
✕ Bedroom egress opening insufficient              Bedroom 3

WARNING
△ Air-control layer disconnected                   North rim joist
△ Plumbing vent intersects roof valley             Roof

ADVISORY
○ Exterior door threshold lacks assigned detail    Mudroom
```

Selecting an issue should:

1. Navigate to the correct level and view.
2. Zoom to the object.
3. Highlight the relevant geometry.
4. Display the exact measured condition.
5. Explain the rule.
6. Offer a focused corrective action.

An issue record should contain:

```text
Rule
Jurisdiction and code edition
Severity
Affected objects
Measured value
Required value
Why it matters
Suggested fixes
Status
Responsible person
Suppression or exception rationale
```

Support these states:

```text
Open
Acknowledged
Resolved
Waived
Not applicable
Stale
```

“Stale” matters because a previously resolved check may become invalid after model changes.

## Continuous versus requested checks

Run inexpensive local checks continuously:

* Door clearances
* Stair geometry
* Minimum room dimensions
* Fixture spacing
* Simple egress checks
* Missing assembly assignments

Run expensive checks on request or after idle time:

* Structural calculations
* Energy simulation
* Moisture simulation
* Whole-house mechanical checks
* Complex code dependency checks

Do not interrupt drawing with modal errors. Show invalid geometry as a preview, explain the conflict, and allow the user to correct it.

# 7. Make transition details first-class model objects

Transition details should not be stored as disconnected drawings or hidden documentation artifacts.

They should be **linked children of model junctions**.

Examples:

* Wall to foundation
* Wall to roof
* Window to wall
* Door threshold
* Balcony penetration
* Roof valley
* Exterior insulation termination
* Rim joist
* Parapet
* Deck ledger
* Plumbing or duct penetration

A transition detail contains:

```text
Geometry reference
Assemblies being joined
Control-layer mappings
Detail drawing
Notes and specifications
Generated/manual status
Revision state
Applicable conditions
```

Show small detail markers directly on the plan, section, or 3D model:

```text
D-12
D-13 !
D-14 ↻
```

Possible states:

* Assigned and current
* Required but missing
* Generated draft
* Manually overridden
* Out of date because geometry changed
* Conflicting with another detail

## Details workspace

The Documentation workspace should contain a **Details navigator**:

```text
Generated details
Assigned details
Missing transitions
Out-of-date details
Detail library
```

Opening a detail should enter a focused workbench:

```text
┌────────────────────┬───────────────────────────────┬───────────────────┐
│ Junction context   │ Enlarged detail drawing       │ Layers and notes  │
│ and linked objects │ with editable annotations     │ specifications    │
└────────────────────┴───────────────────────────────┴───────────────────┘
```

This is a better home than either the ordinary layer panel or a generic drawing-sheet manager.

# 8. Use dedicated workbenches for complex components

Stairs, windows, doors, roofs, and assemblies are too complex for ordinary property panels, but they should not become disconnected multi-page wizards.

Use a **focused workbench** that temporarily replaces or overlays part of the main interface.

## Stair workbench

```text
┌───────────────────────────────────────────┬──────────────────────────┐
│              LIVE 2D / 3D                 │ Stair definition         │
│                                           │                          │
│   plan, section, manipulators, clearances  │ Floor-to-floor: 9'-9"   │
│                                           │ Configuration: U-shaped  │
│                                           │ Riser count: 16          │
│                                           │ Tread: 10¼"              │
│                                           │ Width: 42"               │
│                                           │                          │
│                                           │ ✓ Riser height           │
│                                           │ ✓ Tread depth            │
│                                           │ ✕ Headroom               │
└───────────────────────────────────────────┴──────────────────────────┘
```

Use direct manipulation and constraints together:

* Drag landing position.
* Type exact dimensions.
* Lock important values.
* Generate valid alternatives.
* Preview headroom volume.
* Show code checks continuously.
* Apply or cancel the complete edit as one transaction.

A wizard is appropriate only for initial creation:

```text
Select stair type → select levels → place stair
```

Afterward, editing should happen in the workbench.

## Window and door editor

Keep common properties in the inspector:

```text
Width
Height
Sill height
Handing
Type
Frame material
```

Open the full editor only for:

* Mullion layout
* Glazing configuration
* Rough opening
* Flashing strategy
* Thermal properties
* Hardware
* Trim and casing
* Parametric family geometry

## Wall-assembly editor

Use a three-column arrangement:

```text
Assembly library | Layered section | Properties and performance
```

The center should be a tactile, enlarged wall section where users can:

* Drag layers to reorder them.
* Insert or remove materials.
* Change thickness numerically.
* Mark control functions.
* Set framing and cavity behavior.
* Identify service cavities.
* Define repeating members.
* Inspect junction compatibility.

Performance metrics should update continuously:

```text
Nominal R-value
Effective R-value
U-factor
Total thickness
Mass
Vapor profile
Fire rating
Acoustic rating
Embodied carbon
Approximate cost
```

# 9. Make 2D and 3D complementary rather than equivalent

Since most work occurs in 2D, do not force equal-sized split view by default.

Recommended view states:

1. **2D primary**
2. **3D primary**
3. **Vertical split**
4. **Horizontal split**
5. **2D with floating 3D preview**
6. **3D with floating plan navigator**

The floating preview is likely the best everyday mode:

```text
┌───────────────────────────────────────────────┐
│                                               │
│                  2D PLAN                      │
│                                               │
│                              ┌──────────────┐ │
│                              │ synchronized │ │
│                              │ 3D preview   │ │
│                              └──────────────┘ │
└───────────────────────────────────────────────┘
```

The preview can be resized, docked, expanded, or dismissed.

Synchronization should include:

* Selection
* Hover highlighting
* Current level
* Section cut
* Visibility state
* Camera target
* Temporary previews
* Issue markers

Selecting a window in 2D should highlight the same window in 3D and display the same inspector.

When drawing a wall, the 3D preview should update continuously but at a lower rendering quality if necessary.

# 10. Optimize drawing interactions around intent

A sophisticated floor-plan editor should support both novice and expert interaction patterns simultaneously.

## Wall drawing

Support both:

* Click–move–click
* Press–drag–release

While drawing, show:

* Ghost geometry
* Length
* Angle
* Alignment reference
* Wall-side or justification
* Snap target
* Constraint state
* Resulting room closure
* Conflicts

Typing should immediately capture numeric input:

```text
18' 6" Enter
```

Tab should cycle fields:

```text
Length → angle → offset
```

## Temporary dimensions

Selecting an object should expose editable temporary dimensions near the geometry:

```text
← 3'-4" →  [window]  ← 7'-8" →
```

Clicking a temporary dimension turns it into an input. Pinning it converts it into a persistent constraint.

## Predictive selection

Before clicking, hover or stylus proximity should indicate what will be selected.

For overlapping objects:

* Repeated click cycles candidates.
* A small selection list appears.
* Number keys select candidates.
* Selection filters can restrict to walls, systems, annotations, and so forth.

## Manipulators

Use geometry-specific handles:

* Wall endpoint
* Wall length
* Arc radius
* Window offset
* Door swing
* Stair landing
* Roof slope
* Section depth

The visual handle may be small for precision, but the actual pointer hit region should be larger. WCAG 2.2 defines a minimum target of 24×24 CSS pixels for most pointer targets, while touch-oriented systems often use larger targets; Material Design, for example, requires 48 dp targets for chips. ([W3C][5])

# 11. Design explicit interaction states

CAD applications frequently become confusing because the user cannot tell whether they are selecting, drawing, editing, or navigating.

Always expose the active state:

```text
SELECT
DRAW WALL
EDIT STAIR
PLACE WINDOW
MEASURE
```

Use several coordinated cues:

* Cursor shape
* Small state label near the top-left canvas corner
* Active tool highlight
* Contextual instructions
* Esc hierarchy
* Preview geometry style

Esc behavior should be predictable:

1. Cancel current sub-operation.
2. Exit current tool.
3. Clear selection.

Do not use Esc to unexpectedly discard an entire complex edit.

For repetitive tools, distinguish:

```text
One placement
Continuous placement
Repeat last command
```

# 12. Create a disciplined visual language

The visual style should be **quiet, architectural, and information-dense**, rather than decorative.

## Base palette

Use:

* Off-white or very light neutral canvas
* Cool gray interface surfaces
* Near-black primary text
* One brand accent
* Semantic colors only for model meaning or status

Avoid:

* Strong gradients
* Excessive cards
* Rounded containers around every property
* Large drop shadows
* Multiple competing accent colors
* Glossy “3D” controls
* Borders around every field

Use borders only to explain hierarchy. Prefer spacing and background shifts.

## Suggested hierarchy

```text
Canvas                  #f7f7f5-like neutral
Primary surface         slightly cooler neutral
Secondary surface       subtly differentiated
Primary text            near black
Secondary text          medium gray
Selection               brand accent
Error                    red
Warning                  amber
Success                  green
Reference geometry       desaturated blue-gray
```

Exact colors should be validated for contrast and color-vision deficiencies.

## Typography

Use a neutral, highly legible system or neo-grotesque family.

Recommended behavior:

* 12–14 px dense desktop UI text
* 14–16 px touch UI text
* Tabular numerals for dimensions
* Medium weight for section headings
* Normal weight for values
* Monospaced formatting only where it improves formulas or identifiers

Do not uppercase every panel heading. Reserve uppercase for compact mode indicators such as `ANALYZE`.

## Geometry

A moderate radius system works better than either perfectly square or excessively rounded controls:

```text
Inputs             4–6 px
Menus              6–8 px
Large overlays     8–12 px
Icon buttons       4–6 px
```

Architecture drawing geometry itself should remain sharp and precise, even if interface surfaces have slight rounding.

## Motion

Use animation only to preserve spatial continuity:

* Panel expansion
* Inspector state change
* Selection transition
* 2D/3D synchronization
* Zooming to an issue
* Entering a workbench

Transitions should generally be fast and non-elastic. Avoid bouncing, overshoot, or decorative motion.

# 13. Use semantic color carefully

Because the application contains systems, performance data, warnings, and architectural graphics, color collisions are a serious risk.

Establish a precedence hierarchy:

1. Errors and warnings
2. Current selection
3. Active analysis lens
4. Discipline colors
5. Ordinary object styling

For example, a plumbing pipe should not remain bright blue while an air-control analysis is active if that blue distracts from the analytical result. Nonessential colors should mute automatically.

Never encode a state only through color:

```text
Red + error icon + label
Amber + warning triangle + label
Dashed line + discontinuity marker
Hatch + material label
```

Provide a legend whenever a lens or analytical view changes the drawing’s semantics.

# 14. Support density profiles

You have both precision pointer work and tap/drag behavior, so one fixed density will be unsatisfactory.

Provide:

```text
Interface density
○ Compact
● Comfortable
○ Touch
```

This can adapt:

* Row heights
* Icon spacing
* Handle hit regions
* Inspector padding
* Tooltip delay
* Context-menu size
* Floating-toolbar geometry

The actual model geometry should not visually grow; only interactive regions and controls should.

For stylus devices, a strong default is:

* Stylus selects, draws, and manipulates.
* Fingers navigate the canvas.
* Two fingers pan, zoom, and rotate.
* Long press opens contextual commands.
* Palm input is ignored during stylus drawing.

Make this configurable because users develop strong CAD interaction preferences.

# 15. Build a coherent object hierarchy

The project navigator should reflect architectural reasoning rather than only raw geometry.

```text
PROJECT
├── Site
├── Building
│   ├── Levels
│   │   ├── Basement
│   │   ├── Level 1
│   │   ├── Level 2
│   │   └── Roof
│   ├── Systems
│   │   ├── Envelope
│   │   ├── Structure
│   │   ├── Plumbing
│   │   ├── Mechanical
│   │   └── Electrical
│   ├── Assemblies
│   ├── Rooms and zones
│   └── Details
├── Views
├── Sheets
├── Schedules
└── Issues
```

Objects can appear in more than one logical collection without being duplicated. A window might belong to:

* Level 1
* Exterior envelope
* Window schedule
* Egress analysis
* Detail D-17

The navigator should therefore behave like indexed views over a model graph, not like a strict filesystem.

# 16. Treat object selection as the universal navigation mechanism

The most elegant interaction loop is:

```text
See object
→ select object
→ relevant tools appear
→ inspect or manipulate
→ receive immediate feedback
```

Selection should be able to lead anywhere:

* Select wall → edit assembly
* Select junction → open transition detail
* Select room → inspect occupancy and ventilation
* Select issue marker → open rule explanation
* Select duct → isolate mechanical system
* Select window → evaluate egress and thermal properties
* Select floor → view structural span behavior

This reduces the need for users to remember where a feature “lives.”

# 17. A strong final structure for your application

I would organize the product around five concepts:

## Design

Create and modify architectural objects.

```text
Architecture · Envelope · Structure · Systems
```

## Views

Control how the model is observed.

```text
Level · discipline · detail · phase · camera · section
```

## Lenses

Interpret the model through building-science questions.

```text
Air · water · thermal · vapor · fire · energy · code
```

## Details

Resolve model transitions into constructible documentation.

```text
Junctions · generated details · detail library · stale details
```

## Issues

Track design failures, ambiguities, and incomplete decisions.

```text
Permit · performance · coordination · documentation
```

This makes permit checking and transition details feel like integral parts of the design environment rather than secondary features bolted onto a CAD interface.

# Highest-value redesign sequence

The best implementation order would be:

1. Replace the permanent tool sidebar with a narrow tool rail and contextual toolbar.
2. Convert the right side into a strict selection inspector.
3. Add saved view recipes and separate visibility from representation.
4. Add a synchronized floating 3D preview.
5. Build the Issues drawer and canvas markers.
6. Introduce dedicated stair and wall-assembly workbenches.
7. Make transition details linked model objects.
8. Add building-science lenses, starting with air, water, and thermal continuity.
9. Add a command palette and customizable shortcuts.
10. Refine typography, spacing, color hierarchy, and motion.

The resulting product would retain the power of a professional BIM application but feel more like a modern direct-manipulation design tool: canvas-first, object-centered, analytically aware, and much less visually oppressive.

[1]: https://support.shapr3d.com/hc/en-us/articles/7873882619548-Adaptive-user-interface?utm_source=chatgpt.com "Adaptive user interface"
[2]: https://help.figma.com/hc/en-us/articles/23570416033943-Use-the-actions-menu-in-Figma-Design?utm_source=chatgpt.com "Use the actions menu in Figma Design"
[3]: https://www.autodesk.com/learn/ondemand/course/design-performance-and-sustainability-with-autodesk-forma-revit-and-insight/unit/2W3yyX6fERmmeZNq5Q50DV?utm_source=chatgpt.com "Learn to use the Forma interface and features"
[4]: https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html?utm_source=chatgpt.com "Understanding Success Criterion 1.4.11: Non-text Contrast"
[5]: https://www.w3.org/TR/WCAG22/?utm_source=chatgpt.com "Web Content Accessibility Guidelines (WCAG) 2.2"
