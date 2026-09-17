// Rooms, walls and floors in the LIVE editor, end to end (Stage 2 release gate).
//
//     cd ui && npm run rooms-check           # builds ui/dist, serves an empty-template copy
//     ROOMS_CHECK_SKIP_BUILD=1 npm run rooms-check
//
// Real taps over CDP against `haus serve` on a throwaway copy of houses/empty: rectangles by
// the Room tool, a T-junction that carries an attached sofa, a partition and its deletion,
// a wall-body drag with an attached sofa, and Add floor with copy viewed in 3D.
import { writeFileSync } from "node:fs";
import { join } from "node:path";
import {
  captureScreenshot, click, drag, evaluate, key, navigate, setViewport, waitFor,
} from "./lib/cdp.mjs";
import {
  S, UI, assert, buildUi, finish, near, openLiveHouse, scenarioRunner, sleep, toScreen,
} from "./lib/liveHouse.mjs";

const SHOTS = join(UI, "out", "rooms-check");
const FT = 0.3048;
buildUi("ROOMS_CHECK_SKIP_BUILD");
const { base, session, log, close } = await openLiveHouse("empty");

const { scenario, results } = scenarioRunner(session, SHOTS, () => evaluate(session, `const s = ${S};
  return { tool: s.tool, storey: s.activeStorey, conflict: s.conflict, save: s.saveState,
           saved: s.savedRevision, rev: s.model.revision, draft: s.roomDraft ?? null,
           toasts: s.toasts.map((t) => t.message).slice(-4),
           rooms: s.model.rooms.map((r) => [r.tag, r.storey]),
           walls: s.model.walls.map((w) => [w.tag, w.storey, w.axis]) };`));

const at = (xFt, yFt) => toScreen(session, evaluate, [xFt * FT, yFt * FT]);
const count = (what, storey = "main") => evaluate(session,
  `return ${S}.model.${what}.filter((e) => e.storey === ${JSON.stringify(storey)}).length;`);
const idle = () => waitFor(session, `const s = ${S};
  return s.saveState !== "saving" && s.savedRevision === s.model.revision;`, 30_000, "idle");
// Walls whose axis lies on x = xFt (both ends), on main.
const wallsAtX = (xFt) => evaluate(session, `return ${S}.model.walls.filter((w) => w.storey === "main"
  && w.axis.every((p) => Math.abs(p[0] - ${xFt * FT}) < 0.03)).map((w) => ({ tag: w.tag, axis: w.axis }));`);
const object = (tag) => evaluate(session,
  `return ${S}.model.canvas_objects.find((o) => o.tag === ${JSON.stringify(tag)}) ?? null;`);
const macro = (body) => evaluate(session, `return await ${S}.runMacro(${JSON.stringify(body)});`);

async function drawRect([ax, ay], [bx, by], rooms) {
  await evaluate(session, `const s = ${S}; s.setTool("room"); s.setRoomMode("rect"); return 1;`);
  await click(session, await at(ax, ay));
  await waitFor(session, `return !!document.querySelector("[data-room-draft]") || true`, 1000);
  await click(session, await at(bx, by));
  await waitFor(session, `return ${S}.model.rooms.filter((r) => r.storey === "main").length === ${rooms}`,
    30_000, `${rooms} rooms`);
  await idle();
}

async function attachSofa(wallTag, distanceM) {
  const res = await macro({ macro: "place_placeable", storey: "main", type_ref: "FURN-SOFA-84",
    position: ["1'", "1'"] });
  const tag = Object.keys(res?.minted ?? {}).find((t) => t.startsWith("FURN") || !t.startsWith("RM-"));
  assert(tag, `place_placeable minted nothing: ${JSON.stringify(res)}`);
  await macro({ macro: "attach_placeable", storey: "main", tag, wall: wallTag, face: "left",
    distance: distanceM });
  await idle();
  return tag;
}

try {
  await setViewport(session, { width: 1600, height: 1000 });
  await navigate(session, `${base}/`);
  await evaluate(session, `window.__errs = []; addEventListener("error", (e) => __errs.push(String(e.message))); return 1;`);
  await waitFor(session, `return !!${S}.model && !!document.querySelector("svg.canvas-svg")`, 60_000, "model");
  // 40 px/m puts the 36' x 12' layout left of centre, clear of the inspector a selection opens.
  await evaluate(session, `const s = ${S}; s.setActiveStorey("main");
    const r = document.querySelector("svg.canvas-svg").getBoundingClientRect();
    s.setView({ scale: 40, tx: r.width * 0.15, ty: r.height * 0.75 }); return 1;`);
  let sofa;

  await scenario("a rectangle draws four walls and a room", async () => {
    await drawRect([0, 0], [16, 12], 1);
    assert(await count("walls") === 4, `walls: ${await count("walls")}`);
    const sel = await evaluate(session, `const s = ${S}; return s.selection.kind;`);
    assert(sel === "room", `selection is ${sel}`);
  });

  await scenario("an adjacent rectangle shares the wall", async () => {
    await drawRect([16, 0], [28, 12], 2);
    assert(await count("walls") === 7, `walls: ${await count("walls")}`);
    assert((await wallsAtX(16)).length === 1, "shared wall duplicated");
  });

  await scenario("a shorter neighbour T-splits the wall and carries the attached sofa", async () => {
    const [east] = await wallsAtX(28);
    sofa = await attachSofa(east.tag, 9 * FT);
    const before = await object(sofa);
    await drawRect([28, 0], [36, 6], 3);
    assert((await wallsAtX(28)).length === 2, "east wall not split");
    const after = await object(sofa);
    assert(after.attachment && near(after.position_m[0], before.position_m[0])
      && near(after.position_m[1], before.position_m[1]),
      `sofa moved ${JSON.stringify(before.position_m)} -> ${JSON.stringify(after.position_m)}`);
  });

  await scenario("a partition inside a room splits it", async () => {
    await drawRect([0, 0], [8, 12], 4);
  });

  await scenario("deleting the partition merges the rooms", async () => {
    const [partition] = await wallsAtX(8);
    assert(partition, "no partition wall");
    await evaluate(session, `const s = ${S}; s.setTool("select");
      s.select("wall", s.model.walls.find((w) => w.tag === ${JSON.stringify(partition.tag)}).uid); return 1;`);
    await key(session, "Delete");
    await waitFor(session, `return ${S}.model.rooms.filter((r) => r.storey === "main").length === 3`, 30_000, "merge");
    assert((await wallsAtX(8)).length === 0, "partition still there");
    await idle();
  });

  await scenario("dragging a shared wall's body carries its attached sofa", async () => {
    const [shared] = await wallsAtX(16);
    const sofa2 = await attachSofa(shared.tag, 6 * FT);
    const before = await object(sofa2);
    await evaluate(session, `const s = ${S}; s.setTool("select");
      s.select("wall", s.model.walls.find((w) => w.tag === ${JSON.stringify(shared.tag)}).uid); return 1;`);
    await sleep(300);
    await drag(session, await at(16, 3), await at(18, 3), { steps: 8 });
    await waitFor(session, `return ${S}.model.walls.some((w) => w.tag === ${JSON.stringify(shared.tag)}
      && w.axis.every((p) => Math.abs(p[0] - ${18 * FT}) < 0.03))`, 30_000, "wall at 18'");
    await idle();
    const after = await object(sofa2);
    assert(near(after.position_m[0] - before.position_m[0], 2 * FT, 0.03),
      `sofa dx ${after.position_m[0] - before.position_m[0]}`);
  });

  await scenario("add a floor with the layout copied, seen in 3D", async () => {
    const mainRooms = await count("rooms");
    // Three evaluates: the reload re-renders enough to collect a long-awaited CDP promise.
    await evaluate(session, `await ${S}.client.addStorey({ tag: "upper", elevation: "9'",
      ceiling_height: "8'", copy_from: "main" }); return 1;`);
    await evaluate(session, `void ${S}.reload(); return 1;`);
    await waitFor(session, `return ${S}.model.storeys?.some?.((st) => st.tag === "upper")
      || ${S}.model.rooms.some((r) => r.storey === "upper")`, 30_000, "upper loaded");
    await evaluate(session, `${S}.setActiveStorey("upper"); return 1;`);
    await waitFor(session, `return ${S}.model.rooms.filter((r) => r.storey === "upper").length === ${mainRooms}`,
      30_000, "copied rooms");
    await evaluate(session, `${S}.setViewMode("3d"); return 1;`);
    await waitFor(session, `return !!document.querySelector(".panel-3d canvas, canvas")`, 15_000, "3d canvas");
    await sleep(3000);
    writeFileSync(join(SHOTS, "two-floors-3d.png"), await captureScreenshot(session));
    await evaluate(session, `${S}.setViewMode("2d"); return 1;`);
  });

  const errors = await evaluate(session, `return window.__errs;`);
  if (errors.length) { console.log(`page errors: ${JSON.stringify(errors)}`); results.push({ name: "no page errors", ok: false }); }
} finally {
  await close();
}

finish(results, log.text);
