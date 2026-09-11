# Site state: `tasks.toml` visits and `inspections.toml`

Two hand-editable TOML files in `houses/<name>/`, read per request and **never written by
the build**. They sit outside the PatchOp/undo journal for the same reason `costs.toml`
does: booking a sub is not a plan edit, and un-booking one by pressing undo would be a lie
about the site.

The rule the whole surface rests on: **readiness is derived, dates are authored.** The
engine will tell you a visit is blocked and name what is in the way. It will never tell you
when the concrete sub is coming, how long the pour takes, or what the lead time on the
windows is — none of that is in a geometry model, and a fabricated duration is worse than
an absent one.

## `tasks.toml` — `[entries]` and `[visits]`

`[entries."task/<trade>/<storey>"]` is unchanged (`status`, `started`, `completed`,
`assignee`, `note`) and still keyed on the work-package slug `takeoff/tasks.py` derives.
The status vocabulary gained one value: `verified`. `done` is the sub's claim that they are
finished; `verified` is the owner's own walk of the handoff list afterwards.

`[visits]` is new. A **visit** is the schedulable unit — one sub, one arrival — because a
(trade x storey) package is the right grain for money and the wrong grain for a phone call.
catlin's concrete is roughly six mobilisations across two subs with inspections between
them, and the plumbing sleeves go in before the pour while the trade order puts plumbing
after framing.

```toml
[visits."task/concrete/building/footings"]
# The slug is the package slug + "/" + a label you choose. The visit id is
# derive_guid(project_uuid, slug) — never hand-minted (see the root CLAUDE.md).
label = "House + court footings, belled piers"
rows = ["concrete:footing"]                        # optional subset of the package's BOM rows
element_tags = ["FT-B-*", "FT-SG-*"]               # globs, matched against the package's tags
depends_on = ["task/earth/basement", "insp/erosion"]   # visit slugs and/or insp/<id>
status = "scheduled"          # todo | scheduled | in_progress | done | verified
scheduled = "2027-05-04"      # prose, authored, never computed
assignee = "Nordic Concrete"
contact = "612-555-0100"
note = "Belled piers need the auger; confirm 48h ahead."
constraints = [
  { label = "rebar cages galvanized after fabrication, delivered", cleared = "2027-04-28" },
  { label = "P/E/M on site during forming (83 sleeves)" },
]
checked = ["sleeves:SL-B-SLAB"]   # handoff item ids ticked on the walk
```

A package with **no** authored visits is one implicit visit: slug = the package slug,
`depends_on` = the package's own predecessors plus every inspection whose `gates` names its
trade. So a house that authors no visits still gets a complete board.

`depends_on` may name any visit in the house, which is what makes cross-trade order
expressible: the sleeves visit runs before the pour even though plumbing follows framing.

`haus schedule <house> --propose <package>` prints a split the engine derived from the BOM
row families and tag families, with proposed predecessors and the trade's default
constraint labels. It writes nothing. Paste what you accept.

## `inspections.toml`

```toml
[authorities.building]
label = "Saint Paul DSI"
phone = "651-266-9002"
window = "7:30-9:00 M-F"      # when you may call
lead_days = 1                 # business days' notice they ask for

[entries.footing]
requested = "2027-05-04"
scheduled = "2027-05-05"
inspector = "..."
result = "pass"               # pass | fail | partial
result_date = "2027-05-08"
reinspect = "2027-05-08"
history = ["2027-05-05 fail: bolts off plate layout", "2027-05-08 pass"]
checked = ["permit card posted"]                 # on_site ticks
requires = ["task/concrete/building/footings"]   # visits that must be under way first
waived = "DSI: not required on a slab-on-grade addition"
note = "..."

[[extra]]                     # an inspection this house needs that the profile lacks
id = "as_built_survey"
label = "As-built survey before backfill"
authority = "building"
after = ["foundation_wall"]
gates = ["earth"]
```

The engine ships **no phone numbers**: `[authorities]` is house-owned, like `prices.toml`.
`waived` is state, not spec — the AHJ said this one is not required *here*, which is a
different sentence from `not_applicable` (this building does not have the condition the
inspection covers, established from positive evidence in the model).

The profile's own list is data on `JurisdictionProfile.inspections`
(`checks/jurisdiction.InspectionSpec`); `[[extra]]` is for what a house or an AHJ adds.
catlin carries one: the girt-screw hold before the foam goes on, with `authority = "owner"`
— a hold the owner placed on themselves is not an AHJ visit, and giving it a phone number
would be a lie.

## Write path

`PUT /inspections {"ops": [...]}` with `set_inspection`, `set_extra_inspection` or
`remove_extra_inspection`; `PUT /tasks` gained `set_visit` beside the existing `set_task`.
Both are all-or-nothing, return the fresh GET payload, and 400 on a malformed op — the same
contract `/costs` and `/tasks` already keep.
