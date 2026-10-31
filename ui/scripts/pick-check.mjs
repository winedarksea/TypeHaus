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

  // Pose: 3D only, attic storey, and every trade but framing off so the framing is what the
  // camera can actually see. A rafter under 8" of foam and standing seam is not pickable,
  // and hiding a trade takes its meshes out of the raycast too (isRenderedInScene).
  const pose = await evaluate(session, `
    const st = window.__haus.store;
    st.getState().setViewMode("3d");
    st.getState().setActiveStorey("attic");
    st.getState().showOnlyTrades(["framing"]);
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

  // --- Pieces and groups: a real click on one board, one drip-edge leg, one baluster. ---
  await navigate(session, process.env.HAUS_URL ?? "http://127.0.0.1:8791/");
  await evaluate(session, `
    const d = Date.now() + 60000;
    while (Date.now() < d) { if (window.__haus?.store?.getState?.()?.model?.roofs?.length) return 1;
      await new Promise(r => setTimeout(r, 200)); }
    throw new Error("model never arrived");`);
  await evaluate(session, `
    const st = window.__haus.store.getState();
    st.setViewMode("3d");
    const d = Date.now() + 40000;
    while (Date.now() < d) { const c = document.querySelector("canvas");
      if (c && c.getBoundingClientRect().width > 100 && window.__haus.probe) break;
      await new Promise(r => setTimeout(r, 200)); }
    await new Promise(r => setTimeout(r, 3000));
    return 1;`);

  // Each target is found from the model, aimed at by the probe, then clicked for real.
  const targets = JSON.parse(await evaluate(session, `
    const m = window.__haus.store.getState().model;
    const out = [];
    const win = (m.openings ?? []).filter(o => o.kind === "window");
    // Seated windows draw their casing as cladding trim, so the board a click reaches is the frame.
    for (const piece of ["frame:jamb-left", "exterior_trim:jamb-left"])
      for (const o of win) out.push({ label: "window board", want: { kind: "opening", uid: o.uid, piece },
        query: { uid: o.uid, piece } });
    for (const c of m.door_casings ?? []) if (c.pieces?.[0]?.name) {
      const piece = "casing:" + c.uid + ":" + c.pieces[0].name;
      out.push({ label: "door casing leg", want: { kind: "opening", uid: c.opening_uid, piece },
        query: { uid: c.opening_uid, piece } });
    }
    for (const o of (m.openings ?? []).filter(o => o.is_door))
      for (const p of o.authored_product_parts ?? [])
        if (p.role === "hinge") out.push({ label: "door hinge", want: { kind: "opening", uid: o.uid, piece: p.key },
          query: { uid: o.uid, piece: p.key } });
    for (const roof of m.roofs ?? []) {
      const seen = new Set();
      for (const mem of roof.members ?? []) {
        if (!mem.group || seen.has(mem.group)) continue;
        const kind = mem.group.endsWith("-drip-edge") ? "drip edge" : mem.group.endsWith("-gutter") ? "gutter" : null;
        // Aim at the outward leg: the flange is under the roofing.
        if (!kind || !(mem.key.endsWith("-face") || mem.key.endsWith("-front"))) continue;
        seen.add(mem.group);
        const uid = roof.uid + "::" + mem.group;
        out.push({ label: kind, want: { kind: "member", uid },
          query: { uid, at: [(mem.p0[0] + mem.p1[0]) / 2, (mem.p0[1] + mem.p1[1]) / 2, (mem.z0_m + mem.z1_m) / 2] } });
      }
    }
    const lead = new Map();
    for (const s of m.solids ?? []) if (s.group && s.host_ref && !lead.has(s.group)) lead.set(s.group, s.uid);
    for (const s of m.solids ?? []) {
      if (!s.group || !s.host_ref || !/-i\\d+$/.test(s.uid)) continue;
      const xs = s.outline.map(p => p[0]), ys = s.outline.map(p => p[1]);
      const uid = lead.get(s.group);
      out.push({ label: "baluster", want: { kind: "solid", uid },
        query: { uid, at: [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2, (s.z0_m + s.z1_m) / 2] } });
    }
    // A multi-part product draws its same-material parts as one merged mesh (→ three/mergeParts.ts).
    const types = new Map((m.catalog?.canvas_object_types ?? []).map(t => [t.tag, t]));
    for (const c of m.canvas_objects ?? []) {
      const type = types.get(c.type ?? "");
      if (c.domain === "opening" || type?.model_glb || (type?.model_parts?.length ?? 0) < 3) continue;
      out.push({ label: "placed product", want: { kind: "canvas_object", uid: c.uid }, query: { uid: c.uid } });
    }
    return JSON.stringify(out);`));
  const wanted = ["window board", "door casing leg", "door hinge", "drip edge", "gutter", "baluster",
    "placed product"];
  for (const label of wanted) {
    const candidates = targets.filter((t) => t.label === label);
    let done = null;
    console.log("target:", label);
    for (const t of candidates.slice(0, 24)) {
      const at = await evaluate(session, `return window.__haus.probe(${JSON.stringify(t.query)});`);
      if (!at) continue;
      for (const type of ["mousePressed", "mouseReleased"])
        await session.send("Input.dispatchMouseEvent", { type, x: Math.round(at.x), y: Math.round(at.y),
          button: "left", buttons: type === "mousePressed" ? 1 : 0, clickCount: 1, pointerType: "mouse" });
      const sel = await evaluate(session, `
        await new Promise(r => setTimeout(r, 60));
        const s = window.__haus.store.getState().selection; return { kind: s.kind, uid: s.uid, piece: s.piece ?? null };`);
      const ok = sel.kind === t.want.kind && sel.uid === t.want.uid && (t.want.piece ? sel.piece === t.want.piece : true);
      console.log(`${ok ? "ok  " : "FAIL"} ${label}: ${JSON.stringify(sel)}`);
      if (!ok) throw new Error(`${label}: wanted ${JSON.stringify(t.want)}`);
      done = sel; break;
    }
    if (!done) console.log(`SKIP ${label}: no ${candidates.length ? "reachable" : "such"} target (${candidates.length} candidates)`);
  }
} catch (e) { console.log("PICK-CHECK FAILED:", e.message); process.exitCode = 1; }
finally { session.close(); await browser.close(); }
