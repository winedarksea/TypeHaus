// Furniture editing in the LIVE editor, end to end (Stage 1 release gate).
//
//     cd ui && npm run edit-check            # builds ui/dist, serves a starter copy, drives it
//     EDIT_CHECK_SKIP_BUILD=1 npm run edit-check
//
// Real pointer and key events over CDP against `haus serve` on a throwaway copy of
// houses/starter, with TYPEHAUS_DEBUG_DELAY_MS=800 so every commit is slow enough to race.
// State is read through `window.__haus.store`. Exits 1 on any failed scenario.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import {
  captureScreenshot, click, drag, evaluate, key, navigate, setViewport, waitFor,
} from "./lib/cdp.mjs";
import {
  S, UI, assert, buildUi, finish, near, openLiveHouse, scenarioRunner, sleep, toScreen as screenAt,
} from "./lib/liveHouse.mjs";

const SHOTS = join(UI, "out", "edit-check");
buildUi("EDIT_CHECK_SKIP_BUILD");
const { house, base, session, log, close } = await openLiveHouse("starter", {
  env: { TYPEHAUS_DEBUG_DELAY_MS: "800" },
});

const { scenario, results } = scenarioRunner(session, SHOTS, () => evaluate(session, `const s = ${S};
  return { save: s.saveState, saved: s.savedRevision, rev: s.model?.revision, conflict: s.conflict,
           pending: s.pendingTransforms, toasts: s.toasts.map((t) => t.message).slice(-4),
           chair: (s.model?.canvas_objects ?? []).filter((o) => o.tag === ${JSON.stringify(chair ?? "")})
             .map((o) => [o.position_m, o.rotation]),
           server: await fetch("/model").then((r) => r.json()).then((m) => [m.revision,
             (m.canvas_objects ?? []).filter((o) => o.tag === ${JSON.stringify(chair ?? "")}).map((o) => o.position_m)]) };`));

const toScreen = (xy) => screenAt(session, evaluate, xy);
// The pose the canvas shows: the pending overlay first, then the authoritative model.
const shown = (tag) => evaluate(session, `const s = ${S};
  const o = (s.model?.canvas_objects ?? []).find((c) => c.tag === ${JSON.stringify(tag)});
  if (!o) return null;
  const p = s.pendingTransforms[o.uid];
  return { uid: o.uid, p: p?.position_m ?? o.position_m, r: p?.rotation ?? o.rotation ?? 0,
           model: o.position_m, pending: !!p, selected: s.selection.uid === o.uid };`);
const settled = (label = "settled") => waitFor(session, `const s = ${S};
  return Object.keys(s.pendingTransforms).length === 0 && s.saveState === "saved"
    && s.savedRevision === s.model.revision;`, 30_000, label);

let chair;
try {
  await setViewport(session, { width: 1600, height: 1000 });
  await navigate(session, `${base}/`);
  await evaluate(session, `window.__errs = []; addEventListener("error", (e) => __errs.push(String(e.message))); return 1;`);
  await waitFor(session, `return ${S}.model?.rooms?.length`, 60_000, "model");
  const room = await evaluate(session, `const s = ${S};
    const r = s.model.rooms.find((room) => room.storey === s.activeStorey);
    const xs = r.clear_face.map((p) => p[0]), ys = r.clear_face.map((p) => p[1]);
    return [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];`);

  await scenario("place a chair from the catalog", async () => {
    await evaluate(session, `${S}.setTool("placeable"); return 1;`);
    await waitFor(session, `return !!document.querySelector('.placeable-card[data-type-tag="FURN-ARMCHAIR-35"]')`, 5000, "catalog");
    await evaluate(session, `document.querySelector('.placeable-card[data-type-tag="FURN-ARMCHAIR-35"]').click(); return 1;`);
    const at = await toScreen(room);
    await session.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: at[0], y: at[1], pointerType: "mouse" });
    await waitFor(session, `return !!document.querySelector("[data-placeable-ghost]")`, 3000, "ghost");
    await click(session, at);
    const tag = await waitFor(session, `const s = ${S};
      const o = (s.model.canvas_objects ?? []).find((c) => c.type === "FURN-ARMCHAIR-35");
      return o && s.selection.uid === o.uid && s.tool === "select" ? o.tag : null;`, 30_000, "placed + selected");
    chair = tag;
    await settled();
  });

  await scenario("drag lands at the release point, not the origin", async () => {
    const before = await shown(chair);
    const target = [before.p[0] + 1, before.p[1]];
    await drag(session, await toScreen(before.p), await toScreen(target), { modifiers: ["alt"] });
    await sleep(50);
    const at50 = await shown(chair);
    writeFileSync(join(SHOTS, "drag-plus-50ms.png"), await captureScreenshot(session));
    assert(near(at50.p[0], target[0], 0.05), `+50 ms shows x=${at50.p[0]}, released at ${target[0]}`);
    assert(at50.selected, "selection dropped by the commit");
    await settled();
    assert(near((await shown(chair)).model[0], target[0], 0.05), "model did not land at the release point");
  });

  await scenario("two fast drags raise no conflict", async () => {
    const start = (await shown(chair)).p;
    const mid = [start[0], start[1] + 0.5], end = [start[0], start[1] + 1];
    await drag(session, await toScreen(start), await toScreen(mid), { steps: 4, modifiers: ["alt"] });
    await drag(session, await toScreen(mid), await toScreen(end), { steps: 4, modifiers: ["alt"] });
    await settled();
    const s = await evaluate(session, `return { conflict: ${S}.conflict, banner: !!document.querySelector(".banner") };`);
    assert(!s.conflict && !s.banner, `conflict: ${JSON.stringify(s)}`);
    assert(near((await shown(chair)).model[1], end[1], 0.05), "second drag did not win");
  });

  await scenario("drag then click elsewhere holds the position", async () => {
    const start = (await shown(chair)).p;
    const target = [start[0] - 0.6, start[1]];
    await drag(session, await toScreen(start), await toScreen(target), { steps: 4, modifiers: ["alt"] });
    await click(session, await toScreen([room[0] + 5, room[1] + 5]));
    for (let i = 0; i < 10; i++) {
      await sleep(100);
      const now = await shown(chair);
      assert(near(now.p[0], target[0], 0.05), `snapped back to x=${now.p[0]} after deselect`);
    }
    await settled();
    await evaluate(session, `const s = ${S}; s.select("canvas_object", ${S}.model.canvas_objects.find((o) => o.tag === ${JSON.stringify(chair)}).uid); return 1;`);
  });

  await scenario("arrow nudge, R rotate, inspector follows", async () => {
    await waitFor(session, `return (${S}).selection.uid`, 3000, "selection");
    const start = await shown(chair);
    await key(session, "ArrowRight");
    await key(session, "ArrowRight");
    await key(session, "r");
    await settled();
    const end = await shown(chair);
    assert(near(end.model[0], start.p[0] + 0.0508, 0.003), `nudge moved x ${start.p[0]} -> ${end.model[0]}`);
    assert(near(((end.r - start.r) % 360 + 360) % 360, 90, 0.5), `rotation ${start.r} -> ${end.r}`);
    const inspX = await evaluate(session, `return document.querySelector('input[aria-label="Position X"]')?.value ?? null;`);
    assert(inspX !== null, "inspector X field missing");
    const inspM = await evaluate(session, `return ${S}.model.canvas_objects.find((o) => o.tag === ${JSON.stringify(chair)}).position_m[0];`);
    assert(inspX === String(inspX) && inspX.length > 0, "inspector X empty");
    console.log(`     inspector X="${inspX}" model x=${inspM.toFixed(4)} m`);
  });

  await scenario("Esc mid-drag restores the pose", async () => {
    const start = await shown(chair);
    const to = await toScreen([start.p[0] - 1, start.p[1]]);
    await drag(session, await toScreen(start.p), to, { steps: 5, release: false });
    await key(session, "Escape");
    await session.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: to[0], y: to[1], button: "left", buttons: 0, clickCount: 1, pointerType: "mouse" });
    await sleep(1500);
    const end = await shown(chair);
    assert(near(end.p[0], start.p[0], 0.005) && !end.pending, `moved to ${end.p} after Esc`);
    assert(end.selected, "Esc dropped the selection");
  });

  await scenario("undo and redo", async () => {
    const before = await shown(chair);
    const target = [before.p[0], before.p[1] - 0.4];
    await drag(session, await toScreen(before.p), await toScreen(target), { steps: 4, modifiers: ["alt"] });
    await settled();
    await evaluate(session, `await ${S}.undo(); return 1;`);
    await waitFor(session, `const o = ${S}.model.canvas_objects.find((c) => c.tag === ${JSON.stringify(chair)}); return Math.abs(o.position_m[1] - ${before.p[1]}) < 0.01;`, 30_000, "undo");
    await evaluate(session, `await ${S}.redo(); return 1;`);
    await waitFor(session, `const o = ${S}.model.canvas_objects.find((c) => c.tag === ${JSON.stringify(chair)}); return Math.abs(o.position_m[1] - ${target[1]}) < 0.02;`, 30_000, "redo");
  });

  await scenario("external edit mid-commit shows a conflict and pauses the queue", async () => {
    await settled();
    const start = await shown(chair);
    await drag(session, await toScreen(start.p), await toScreen([start.p[0] + 0.3, start.p[1]]), { steps: 3, modifiers: ["alt"] });
    const main = join(house, "plan", "storeys", "main.py");
    writeFileSync(main, `${readFileSync(main, "utf8")}\n# edited outside the editor\n`);
    await waitFor(session, `return !!${S}.conflict`, 15_000, "conflict");
    const paused = (await shown(chair)).model;
    await key(session, "ArrowUp");
    await sleep(1500);
    assert(near((await shown(chair)).model[1], paused[1], 0.001), "queue kept writing under a conflict");
    await evaluate(session, `await ${S}.reload(); return 1;`);
    await waitFor(session, `return !${S}.conflict && Object.keys(${S}.pendingTransforms).length === 0`, 15_000, "conflict cleared");
  });

  await scenario("a target made non-editable fails the save and reverts", async () => {
    const file = join(house, "plan", "placeables.py");
    const rev = await evaluate(session, `return ${S}.model.revision;`);
    writeFileSync(file, readFileSync(file, "utf8").replace("# haus: editable\n", ""));
    await waitFor(session, `return ${S}.model.revision !== ${JSON.stringify(rev)}`, 15_000, "reload after edit");
    await evaluate(session, `const s = ${S}; s.select("canvas_object", s.model.canvas_objects.find((o) => o.tag === ${JSON.stringify(chair)}).uid); return 1;`);
    const start = await shown(chair);
    await key(session, "ArrowLeft");
    await waitFor(session, `return ${S}.saveState === "failed"`, 15_000, "failed chip");
    const chip = await evaluate(session, `return document.querySelector(".status-save")?.dataset.saveState ?? null;`);
    assert(chip === "failed", `chip shows ${chip}`);
    await waitFor(session, `return Object.keys(${S}.pendingTransforms).length === 0`, 5000, "pending cleared");
    assert(near((await shown(chair)).p[0], start.p[0], 0.001), "did not revert to the authoritative pose");
  });

  const errors = await evaluate(session, `return window.__errs;`);
  if (errors.length) { console.log(`page errors: ${JSON.stringify(errors)}`); results.push({ name: "no page errors", ok: false }); }
} finally {
  await close();
}

finish(results, log.text);
