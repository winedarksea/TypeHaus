import { createServer } from "vite";

const server = await createServer({
  configFile: false,
  server: { middlewareMode: true },
  appType: "custom",
});

try {
  const { runPlanGeometryTests } = await server.ssrLoadModule("/src/three/planGeometry.test.ts");
  const { runArchGeometryTests, runCanvasObjectGeometryTests, runOpeningGeometryTests, runEarthGeometryTests, runFootingBeddingGeometryTests, runWholeHouseGlbTests, runSolidMaterialTests, runSelectionRegistrationTests } = await server.ssrLoadModule("/src/components/Panel3D.test.ts");
  const { runModelGeometryTests } = await server.ssrLoadModule("/src/model/geometry.test.ts");
  const { runRoofGeometryTests } = await server.ssrLoadModule("/src/three/roofGeometry.test.ts");
  const { runMaterialGeometryTests } = await server.ssrLoadModule("/src/three/materials.test.ts");
  const { runDetailAnnotationTests } = await server.ssrLoadModule("/src/components/DetailCanvas.test.ts");
  runPlanGeometryTests();
  runOpeningGeometryTests();
  runArchGeometryTests();
  runEarthGeometryTests();
  runFootingBeddingGeometryTests();
  runCanvasObjectGeometryTests();
  runWholeHouseGlbTests();
  runSolidMaterialTests();
  runSelectionRegistrationTests();
  runModelGeometryTests();
  runRoofGeometryTests();
  runMaterialGeometryTests();
  runDetailAnnotationTests();
  console.log("Plan geometry tests passed.");
} finally {
  await server.close();
}
