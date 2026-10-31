// What the 3D view costs to load, measured in the LIVE app (→ Panel3D publishPerf).
//
//     .venv/bin/haus serve houses/catlin --port 8791     # in another shell
//     cd ui && npm run build && npm run perf-check
//
// Prints the /model payload, its fetch+parse time, the scene build time and the first frame's
// draw calls. Swiftshader frame times are meaningless; bytes, build ms and draw calls are not.
import { launchChromium, attachToPage, evaluate, navigate, setViewport } from "./lib/cdp.mjs";

const url = process.env.HAUS_URL ?? "http://127.0.0.1:8791/";
const browser = await launchChromium({ port: 9335 });
const session = await attachToPage(9335);
try {
  await setViewport(session, { width: 1400, height: 900 });
  await navigate(session, url);
  await evaluate(session, `
    const d = Date.now() + 90000;
    while (Date.now() < d) { if (window.__haus?.store?.getState?.()?.model?.walls?.length) return 1;
      await new Promise(r => setTimeout(r, 200)); }
    throw new Error("model never arrived");`);
  const wire = await evaluate(session, `
    const t0 = performance.now();
    const text = await (await fetch("/model")).text();
    const t1 = performance.now();
    JSON.parse(text);
    return { bytes: text.length, fetchMs: t1 - t0, parseMs: performance.now() - t1 };`);
  const perf = await evaluate(session, `
    window.__haus.perf = null;
    const st = window.__haus.store;
    st.getState().setViewMode("3d");
    st.getState().showEverything();
    const d = Date.now() + 90000;
    while (Date.now() < d) { if (window.__haus.perf) return window.__haus.perf;
      await new Promise(r => setTimeout(r, 200)); }
    throw new Error("3D scene never published its perf");`);
  // One camera-only frame's draw calls. A frame that re-renders shadows is not published (→
  // publishFrame), so a dolly that lands on one is simply sent again.
  const dollyCalls = () => evaluate(session, `
    await new Promise(r => setTimeout(r, 1500));
    const c = document.querySelector("canvas");
    const r = c.getBoundingClientRect();
    const d = Date.now() + 120000;
    while (Date.now() < d) {
      delete window.__haus.perf.frameCalls;
      c.dispatchEvent(new WheelEvent("wheel", { deltaY: 1, clientX: r.x + r.width / 2,
        clientY: r.y + r.height / 2, bubbles: true, cancelable: true }));
      const t = Date.now() + 30000; // a swiftshader frame of the whole house can take 15 s
      while (Date.now() < t) { if (window.__haus.perf.frameCalls !== undefined) return window.__haus.perf.frameCalls;
        await new Promise(r => setTimeout(r, 100)); }
    }
    throw new Error("no frame after a dolly");`);
  const frameCalls = await dollyCalls();
  // Calls per trade: each shown alone, against nothing shown (ground, sky, helpers). An element
  // on several trades counts under each, so the rows overlap and do not sum to the total.
  const trades = await evaluate(session, `
    return Object.keys(window.__haus.store.getState().visibleTrades).filter(k => !k.includes(":"));`);
  const isolate = (keys) => evaluate(session, `
    window.__haus.store.getState().showOnlyTrades(${JSON.stringify(keys)}); return 1;`);
  await isolate([]);
  const baseCalls = await dollyCalls();
  const perTrade = [];
  for (const trade of trades) {
    await isolate([trade]);
    perTrade.push([trade, (await dollyCalls()) - baseCalls]);
  }
  await evaluate(session, "window.__haus.store.getState().showEverything(); return 1;");
  // An edit: same building, new revision, so Panel3D rebuilds with every cache already warm.
  const rebuild = await evaluate(session, `
    window.__haus.perf = null;
    const st = window.__haus.store;
    st.setState({ model: { ...st.getState().model, revision: "perf-check-" + Date.now() } });
    const d = Date.now() + 90000;
    while (Date.now() < d) { if (window.__haus.perf) return window.__haus.perf;
      await new Promise(r => setTimeout(r, 100)); }
    throw new Error("no rebuild after a revision bump");`);
  const mb = (wire.bytes / 1e6).toFixed(1);
  console.log(`/model        ${mb} MB  fetch ${wire.fetchMs.toFixed(0)} ms  parse ${wire.parseMs.toFixed(0)} ms`);
  console.log(`scene build   ${perf.buildMs.toFixed(0)} ms  (first frame ${perf.renderMs.toFixed(0)} ms, swiftshader)`);
  console.log(`first frame   ${perf.calls} draw calls  ${perf.triangles} triangles  `
    + `${perf.geometries} geometries  ${perf.textures} textures`);
  console.log(`dolly frame   ${frameCalls} draw calls  (${baseCalls} with every trade hidden)`);
  console.log("calls by trade (shown alone, less the empty frame):");
  for (const [trade, calls] of perTrade.sort((a, b) => b[1] - a[1]).filter(([, c]) => c > 0)) {
    console.log(`  ${trade.padEnd(20)} ${String(calls).padStart(6)}`);
  }
  console.log(`rebuild       ${rebuild.buildMs.toFixed(0)} ms  (an edit: caches warm)  `
    + `${rebuild.geometries} geometries`);
} finally { session.close(); await browser.close(); }
