// Click a rafter in the LIVE 3D viewer — the picking path, end to end.
//
//     .venv/bin/haus serve houses/catlin --port 8791     # in another shell
//     cd ui && npm run build && npm run pick-check
//
// Needs a served house (HAUS_URL overrides the port) and a built `dist`, which is why this
// is a script and not a unit test. It exists because picking is the one contract with no
// Python-side guard: `Panel3D.test.ts` can prove a mesh went into `registry.picks`, but only
// a real pointer event can prove that a pointerup on a real canvas raycasts a real merged
// framing bucket, resolves the faceIndex back through `resolveMemberPickUid`, and lands the
// right member uid in the store. That chain broke silently when the birdsmouth turned the
// rafter into a GSweep, because a notched member draws a different number of triangles.
//
// Chromium runs headless with swiftshader; `--disable-gpu` blanks Panel3D with no error.
import { launchChromium, attachToPage, evaluate, navigate, setViewport } from "./lib/cdp.mjs";

const browser = await launchChromium({ port: 9333 });
const session = await attachToPage(9333);
try {
  await setViewport(session, { width: 1600, height: 1000 });
  await navigate(session, process.env.HAUS_URL ?? "http://127.0.0.1:8791/");

  await evaluate(session, `
    const d = Date.now() + 60000;
    while (Date.now() < d) { if (window.__haus?.store?.getState?.()?.model?.roofs?.length) return 1;
      await new Promise(r => setTimeout(r, 200)); }
    throw new Error("model never arrived");`);

  // Pose: 3D only, attic storey, and every skin layer group off so the framing is what the
  // camera can actually see. A rafter under 8" of foam and standing seam is not pickable,
  // and hiding a group takes its meshes out of the raycast too (isRenderedInScene).
  const pose = await evaluate(session, `
    const st = window.__haus.store;
    st.getState().setViewMode("3d");
    st.getState().setActiveStorey("attic");
    for (const g of ["sheathing","membrane","insulation","airgap","furring","cladding","finish","other"])
      st.getState().setLayerGroupVisible(g, false);
    st.getState().select("member", null);
    const d = Date.now() + 40000; let c = null;
    while (Date.now() < d) { c = document.querySelector("canvas");
      if (c && c.getBoundingClientRect().width > 100) break; await new Promise(r => setTimeout(r, 200)); }
    if (!c) throw new Error("3D canvas never mounted");
    await new Promise(r => setTimeout(r, 4000));
    const r = c.getBoundingClientRect();
    return { storey: st.getState().activeStorey, viewMode: st.getState().viewMode,
             rect: { x: r.left, y: r.top, w: r.width, h: r.height } };
  `);
  console.log("posed:", JSON.stringify(pose));

  const { x, y, w, h } = pose.rect;
  const hits = [];
  outer:
  for (let row = 1; row <= 11; row++) {
    for (let col = 1; col <= 15; col++) {
      const px = Math.round(x + (w * col) / 16);
      const py = Math.round(y + (h * row) / 12);
      for (const type of ["mousePressed", "mouseReleased"])
        await session.send("Input.dispatchMouseEvent", { type, x: px, y: py, button: "left",
          buttons: type === "mousePressed" ? 1 : 0, clickCount: 1, pointerType: "mouse" });
      const sel = await evaluate(session, `
        await new Promise(r => setTimeout(r, 30));
        const s = window.__haus.store.getState();
        const sel = s.selection;
        if (!sel || sel.kind !== "member" || !sel.uid) return null;
        let found = null;
        for (const roof of s.model.roofs ?? [])
          for (const m of roof.members ?? [])
            if (String(sel.uid).includes(m.key)) { found = { host: roof.tag, ...m }; break; }
        return { uid: String(sel.uid), key: found?.key ?? null, category: found?.category ?? null,
                 host: found?.host ?? null, connection: found?.connection ?? null,
                 seat: found?.seat ?? null, shape: found?.shape ?? null,
                 planOutline: found?.plan_outline?.length ?? null };
      `);
      if (sel) { hits.push({ px, py, ...sel }); if (sel.category === "rafter") break outer; }
    }
  }

  const rafter = hits.find((hit) => hit.category === "rafter");
  console.log(`member picks: ${hits.length}`);
  if (!rafter) { console.log(JSON.stringify(hits.slice(0, 5), null, 1)); throw new Error("no rafter picked"); }

  const inspector = await evaluate(session, `
    await new Promise(r => setTimeout(r, 500));
    for (const q of [".inspector", "[class*=inspector]", "aside", ".rail-panel"]) {
      const el = document.querySelector(q);
      if (el && el.innerText.trim()) return el.innerText.slice(0, 600);
    }
    return null;`);

  console.log("\nPICKED RAFTER:\n" + JSON.stringify(rafter, null, 1));
  console.log("\nINSPECTOR:\n" + (inspector ?? "(none found)"));
  console.log("\nOK: a real click on the live 3D canvas selected a notched rafter.");
} finally { session.close(); await browser.close(); }
