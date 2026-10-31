// Cold public-app timing and snapshot/engine handoff probe.
// Build with `node landing/build-site.mjs`, serve site/, then:
//   node ui/scripts/measure-first-house.mjs http://127.0.0.1:8877/app/
import { attachToPage, evaluate, launchChromium, navigate } from "./lib/cdp.mjs";

const url = process.argv[2] ?? "http://127.0.0.1:8877/app/";
const direct3d = process.argv.includes("--3d");
const browser = await launchChromium({ port: 9333 });
const page = await attachToPage(browser.port);
try {
  await page.send("Page.addScriptToEvaluateOnNewDocument", { source: `
    window.__firstHouse = { shell: null, house: null, three: null, engine: null, snapshot: null,
      sceneBuilds: 0, lastPerf: null };
    const probe = () => {
      const t = window.__firstHouse;
      // Panel3D publishes a fresh perf object per scene build (→ publishPerf).
      if (window.__haus?.perf && window.__haus.perf !== t.lastPerf) {
        t.lastPerf = window.__haus.perf;
        t.sceneBuilds++;
      }
      if (t.shell === null && document.querySelector('.topbar')) t.shell = performance.now();
      if (t.house === null && document.querySelector('.canvas-svg .wall-fills')) {
        requestAnimationFrame(() => { if (t.house === null) t.house = performance.now(); });
      }
      if (t.three === null && document.querySelector('.pane canvas')) {
        requestAnimationFrame(() => { if (t.three === null) t.three = performance.now(); });
      }
      const state = window.__haus?.store?.getState();
      if (state?.model && !state.engineReady && !t.snapshot) {
        t.snapshot = { revision: state.model.revision, walls: state.model.walls,
          storeys: state.model.storeys, view: state.view, activeStorey: state.activeStorey };
      }
      if (state?.engineReady && t.engine === null) {
        t.engine = performance.now();
        t.model = { revision: state.model.revision, walls: state.model.walls,
          storeys: state.model.storeys, view: state.view, activeStorey: state.activeStorey };
      }
    };
    setInterval(probe, 20);
  ` });
  await navigate(page, direct3d ? new URL("?mode=3d", url).href : url);
  // Change both controls while the preview is showing. The engine handoff must leave them
  // alone, including the canvas' fit-once behavior for a newly selected storey.
  const previewDeadline = Date.now() + 5_000;
  while (Date.now() < previewDeadline) {
    if (await evaluate(page, "return !!window.__firstHouse.snapshot")) break;
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  const selectedStorey = direct3d ? null : await evaluate(page, `
    const s = window.__haus.store.getState();
    const other = s.model.storeys.find((storey) => storey.tag !== s.activeStorey)?.tag;
    if (other) s.setActiveStorey(other);
    return other;
  `);
  await new Promise((resolve) => setTimeout(resolve, 400));
  const selectedView = direct3d ? null : await evaluate(page, `
    window.__haus.store.getState().setView({ scale: 137, tx: 333, ty: 222 });
    return window.__haus.store.getState().view;
  `);
  // A cold 3D open headless is engine boot plus a swiftshader scene build: allow for both.
  const deadline = Date.now() + 150_000;
  let result;
  do {
    result = await evaluate(page, `const t = window.__firstHouse; return {
      shell: t.shell, house: t.house, three: t.three, engine: t.engine,
      snapshotRevision: t.snapshot?.revision, engineRevision: t.model?.revision,
      visibleGeometryEqual: t.snapshot && t.model
        ? JSON.stringify(t.snapshot.walls) === JSON.stringify(t.model.walls) &&
          JSON.stringify(t.snapshot.storeys) === JSON.stringify(t.model.storeys) : null,
      storeyPreserved: t.snapshot && t.model
        ? ${JSON.stringify(selectedStorey)} === t.model.activeStorey : null,
      viewPreserved: t.snapshot && t.model
        ? JSON.stringify(${JSON.stringify(selectedView)}) === JSON.stringify(t.model.view) : null,
      selectedView: ${JSON.stringify(selectedView)}, actualView: t.model?.view ?? null,
      wallCount: t.model?.walls.length ?? t.snapshot?.walls.length ?? 0,
      wallDifference: t.snapshot && t.model ? t.snapshot.walls.map((w, i) => ({w, other:t.model.walls[i], i})).filter((p) => JSON.stringify(p.w) !== JSON.stringify(p.other)).slice(0, 1).map(({w,other,i}) => ({i, tag:w.tag, changedKeys:Object.keys(w).filter(k => JSON.stringify(w[k]) !== JSON.stringify(other?.[k])), snapshotAxis:w.axis, engineAxis:other?.axis})) : null,
      error: window.__haus?.store?.getState().error ?? null,
      boot: window.__haus?.boot ?? null,
    };`);
    if ((result.engine && (!direct3d || result.three)) || result.error) break;
    await new Promise((resolve) => setTimeout(resolve, 250));
  } while (Date.now() < deadline);
  // The 3D scene is built from the snapshot; the engine's model carries the same revision and must
  // not rebuild it. Give a handoff rebuild time to land before counting.
  if (direct3d) {
    await new Promise((resolve) => setTimeout(resolve, 3000));
    result.sceneBuilds = await evaluate(page, "return window.__firstHouse.sceneBuilds");
  }
  const { boot, ...summary } = result;
  console.log(JSON.stringify(summary, null, 2));
  // The worker's boot timeline (→ worker.ts mark): each step's duration and the page ms it ended.
  if (boot) {
    console.log("boot step        ms     ends at");
    for (const [name, { ms, at }] of Object.entries(boot).sort((a, b) => a[1].at - b[1].at)) {
      console.log(`${name.padEnd(14)} ${ms.toFixed(0).padStart(6)} ${at.toFixed(0).padStart(10)}`);
    }
  }
  if (!(direct3d ? result.three : result.house) || !result.engine || !result.visibleGeometryEqual ||
      (direct3d && result.sceneBuilds !== 1) ||
      (!direct3d && (!result.storeyPreserved || !result.viewPreserved)) ||
      result.snapshotRevision !== result.engineRevision) process.exitCode = 1;
} finally {
  page.close();
  await browser.close();
}
