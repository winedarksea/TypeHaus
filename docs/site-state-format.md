# Site state: `tasks.toml` visits and `inspections.toml`

Two hand-editable TOML files in `houses/<name>/`, read per request and **never written by
the build**. They sit outside the PatchOp/undo journal for the same reason `costs.toml`
does: booking a sub is not a plan edit, and un-booking one by pressing undo would be a lie
about the site.

The rule the whole surface rests on: **readiness is derived; dates are derived only from
authored inputs, and a missing input yields "needs confirmation", never a default.** The
engine will tell you a visit is blocked and name what is in the way. Given an authored
`duration_days` and a `[calendar]` it will also tell you the earliest date the sequence
allows. It will never invent how long a pour takes, what the lead time on the windows is,
or when a sub is free — none of that is in a geometry model, and a fabricated duration is
the number a whole schedule then gets built on.

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
planned = "2027-05-04"        # your intent, not confirmed with the sub
booked = { date = "2027-05-06", window = "07:00", confirmed_by = "Nordic Concrete",
           confirmed_at = "2027-04-30" }
duration_days = 2             # WORKING days on site. Authored, never defaulted.
contractor = "nordic"         # key into [contractors]
blocks_successors = true      # false takes this visit out of package-level expansion
shared_rows = false           # true where two visits deliberately bill the same rows
constraints = [
  { label = "rebar cages galvanized after fabrication, delivered", cleared = "2027-04-28" },
  { label = "P/E/M on site during forming (83 sleeves)",
    owner = "owner", next_action = "book the plumber for the same morning",
    follow_up = "2027-04-25", severity = "blocking" },
  { label = "locate ticket called in", kind = "locate", start = "2027-04-20" },
]
checkpoints = [
  { id = "forms", label = "Forms, steel and the thermal break set" },
  { id = "pour",  label = "Pour", after = ["insp/footing"] },
  { id = "strip", label = "Strip and cure", cure_days = 3 },
]
materials = [
  { id = "rebar", label = "Galvanized cages", lead_days = 21, source = "..." },
]
checked = ["sleeves:SL-B-SLAB"]   # handoff item ids ticked on the walk
skipped = [{ id = "dowels", reason = "the next sub sets them" }]
exceptions = [{ at = "2027-05-06", hold = "P/E/M on site during forming",
                note = "went ahead; plumber came at noon" }]
```

A package with **no** authored visits is one implicit visit: slug = the package slug,
`depends_on` = the package's own predecessors plus the inspection gates
`schedule/graph.py` is willing to imply, and `status` read from the package's `[entries]`
row. So a house that authors no visits still gets a complete board, and there is one status
ladder rather than two.

An **authored** visit gets exactly its authored `depends_on` (falling back to the package's
own predecessors where it authors none) and inherits **no** trade-wide inspection gate. A
gate names a trade and a trade is not a schedulable thing: stapling one onto every arrival
is what made catlin's excavation wait on the backfill inspection.

A **standalone** visit is `[visits."site/<label>"]`: it draws from no package at all, must
author its own `trade`, and usually names a `milestone`. Permits, locates, surveys,
deliveries, utility coordination and the punch list are all this shape.

`depends_on` may name any visit in the house, any `insp/<id>` (or `insp/<id>/<instance>`),
and any `visit#checkpoint` — which is what makes cross-trade order expressible: the sleeves
visit runs before the pour even though plumbing follows framing.

### `blocks_successors`, and why flatwork needs it

`TRADE_PREDECESSORS["framing"]` names the concrete **package**. Expanded to every concrete
arrival it made the framers wait on the driveway apron, which is authored last on purpose
and poured after they leave. `blocks_successors = false` takes a visit out of that
expansion; it keeps its own predecessors and its own readiness.

### Checkpoints

Ordered pauses **inside one arrival**, only where work must actually stop. The footing
inspection sits between the forms and the pour, and before checkpoints the only way to say
so was to invent two visits for one sub's one mobilisation.

A visit's status **derives** from its checkpoints — `in_progress` once the first starts,
`done` when the last is done — so `status` on a checkpointed visit is a validation error.
`verified` stays a visit-level fact: the owner walks the arrival once, not once per pause.

### `[calendar]`, `[contractors]` and `milestones`

```toml
[calendar]
workdays = [0, 1, 2, 3, 4]                 # 0 = Monday
holidays = ["2027-07-05", "2027-11-25"]

[contractors.nordic]
name = "Nordic Concrete"
phone = "612-555-0100"
trades = ["concrete"]
licence = "..."        # asked for only on electrical and plumbing
coi_expires = "2027-12-31"
w9 = "on file"
contract = "signed 2027-03-02"

milestones = [{ id = "preconstruction", label = "Preconstruction" }, ...]
```

A missing contractor document is an **attention** item on the visit and on the arrival
brief. It never blocks: great subs without digital paperwork have to stay bookable.

`haus schedule <house> --propose <package>` prints a split the engine derived from the BOM
row families and tag families, with proposed predecessors and the trade's default
constraint labels. It writes nothing. Paste what you accept.

## `inspections.toml`

```toml
[permit]
number = "..."
issued = "2027-03-14"
expires = "2028-03-14"
code_edition = "mn-2020"      # a FIELD, not a constant — which cycle this permit is under
nec_edition = "2026"

[authorities.building]
label = "Saint Paul DSI"
phone = "651-266-9002"
portal_url = "https://www.stpaul.gov/paulie"
window = "7:30-9:00 M-F"      # when you may call
lead_days = 1                 # business days' notice they ask for
method = "phone"              # phone | portal | email
source_url = "..."            # where you read the number
confirmed = "2026-09-11"      # the day you last checked it against that source

[entries.footing]
requested = "2027-05-04"
scheduled = "2027-05-05"
inspector = "..."
checked = ["permit card posted"]                 # on_site ticks
requires = ["task/concrete/building/footings"]   # visits that must be under way first
note = "..."
attempts = [
  { date = "2027-05-05", result = "fail", corrections = ["bolts off plate layout"] },
  { date = "2027-05-08", result = "partial", approved = ["FT-B-*"],
    note = "court piers not ready" },
  { date = "2027-05-12", result = "pass" },
]

[entries."footing/court"]     # a SECOND instance of the same spec
scope = ["FT-SG-*"]           # tag globs and/or visit slugs it covers
requested = "2027-06-01"

# A waiver outranks the model's own evidence, so it names who granted it.
# waived = { by = "DSI, J. Smith", date = "2027-04-02", ref = "email 2 Apr" }

[[extra]]                     # an inspection this house needs that the profile lacks
id = "as_built_survey"
label = "As-built survey before backfill"
authority = "building"
after = ["foundation_wall"]
gates = ["earth"]
```

The engine ships **no phone numbers**: `[authorities]` is house-owned, like `prices.toml`.
Who *inspects* is a house fact too — Minn. Stat. 326B.36 subd. 1 and 6 let a municipality
run its own electrical, plumbing and mechanical inspections, and Saint Paul does all three
on three different numbers. The profile only says which authority *kind* each inspection
belongs to.

`lead_days`, the appointment window and the reinspection fee are **not published** by
Saint Paul DSI. Minn. R. 1300.0210 subp. 4 obliges the authority to state them at permit
issuance: leave them blank and the board says so rather than carrying a number nobody gave.

**Attempts, not a result.** `attempts` is an ordered list and the state derives from the
last of them. A `partial` releases only the scope it `approved`: a visit whose element tags
fall entirely inside it sees the inspection as resolved and every other visit stays blocked.
There is no `reinspect` field — the next booking after a fail is the next `scheduled`, and
one date in two places is how the two disagree.

**Instances.** `[entries.footing]` is the default instance of the `footing` spec;
`[entries."footing/court"]` is a second one with its own `scope`, booking and attempts. A
visit depends on `insp/footing/court` for that one, or on the bare `insp/footing` for all
of them.

`waived` is state, not spec — the AHJ said this one is not required *here*, which is a
different sentence from `not_applicable` (this building does not have the condition the
inspection covers, established from positive evidence in the model). It is a table with a
`by`, and a bare string fails validation: a claim that outranks model evidence has to say
who made it.

The profile's own list is data on `JurisdictionProfile.inspections`
(`checks/jurisdiction.InspectionSpec`); `[[extra]]` is for what a house or an AHJ adds.
catlin carries one: the girt-screw hold before the foam goes on, with `authority = "owner"`
— a hold the owner placed on themselves is not an AHJ visit, and giving it a phone number
would be a lie.

## Write path

Everything folds through one op vocabulary in `schedule/site_ops.py`, whichever endpoint or
command it arrives at — which is the point: an agent that edits TOML directly has to be
trusted to reproduce every rule, and an agent that calls ops only has to name what it wants.

| ops | what they change |
|---|---|
| `set_visit`, `set_checkpoint`, `tick_handoff`, `skip_handoff`, `clear_hold`, `add_hold`, `add_exception` | `tasks.toml` `[visits]` |
| `set_task` | `tasks.toml` `[entries]` |
| `set_inspection`, `add_attempt`, `set_instance`, `set_authority`, `set_permit`, `set_extra_inspection`, `remove_extra_inspection` | `inspections.toml` |

`PUT /schedule` and `PUT /inspections` take `{"ops": [...]}` and an optional
`"if_revision"` — the content hash the caller's own `GET` echoed. A mismatch is **409 with
the fresh payload**, not a merge: the file may have been edited by hand thirty seconds ago.
A batch is all-or-nothing, and every write is a temp file plus `os.replace`, so a crash
leaves the previous file complete.

Every status-changing op stamps `updated` and appends one `{at, from, to}` line to the
entry's bounded `log`, in the TOML. There is no journal file.

### The rules both a hand edit and a write are held to

- `verified` needs every hold cleared, every handoff item ticked or `skipped` **with a
  reason**, and every inspection the visit depends on resolved. One request may not both
  clear the last hold and verify.
- `done` while a blocking hold is open records an `exception`. The hold stays open and the
  board lists exceptions first.
- Two visits claiming one BOM row is an error unless both declare `shared_rows = true`.
- A dependency loop is named, and the board shows the last valid state plus the error.

`haus site validate <house>` runs load + graph + rules and exits 1 on any error;
`haus site migrate <house>` folds the old spellings (`result`/`history` into `attempts`, a
string `waived` into a table) and lists what only a person can resolve. Historical `done`
never becomes `verified`.
