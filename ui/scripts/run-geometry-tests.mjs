import { createServer } from "vite";

const server = await createServer({
  configFile: false,
  server: { middlewareMode: true },
  appType: "custom",
});

try {
  const { runPlanGeometryTests } = await server.ssrLoadModule("/src/three/planGeometry.test.ts");
  const { runArchGeometryTests, runCanvasObjectGeometryTests, runCanvasObjectPartsTests, runOpeningGeometryTests, runEarthGeometryTests, runFootingBeddingGeometryTests, runWholeHouseGlbTests, runSolidMaterialTests, runSelectionRegistrationTests, runViewFramingTests } = await server.ssrLoadModule("/src/components/Panel3D.test.ts");
  const { runModelGeometryTests } = await server.ssrLoadModule("/src/model/geometry.test.ts");
  const { runVisibilityTests } = await server.ssrLoadModule("/src/model/visibility.test.ts");
  const { runBomTests } = await server.ssrLoadModule("/src/model/bom.test.ts");
  const { runPlanWarningTests, runSpaceLabelTests } = await server.ssrLoadModule("/src/model/planWarnings.test.ts");
  const { runTransitionTests } = await server.ssrLoadModule("/src/model/transitions.test.ts");
  const { runVaporTests } = await server.ssrLoadModule("/src/model/vapor.test.ts");
  const { runOpenHouseTests } = await server.ssrLoadModule("/src/engine/openHouse.test.ts");
  const { runDoorSymbolTests } = await server.ssrLoadModule("/src/model/doorSymbols.test.ts");
  const { runRoofGeometryTests } = await server.ssrLoadModule("/src/three/roofGeometry.test.ts");
  const { runMaterialGeometryTests, runMemberColorTests } = await server.ssrLoadModule("/src/three/materials.test.ts");
  const { runDetailAnnotationTests } = await server.ssrLoadModule("/src/components/DetailCanvas.test.ts");
  const { runMemberPickingTests } = await server.ssrLoadModule("/src/three/memberPicking.test.ts");
  runPlanGeometryTests();
  runOpeningGeometryTests();
  runArchGeometryTests();
  runEarthGeometryTests();
  runFootingBeddingGeometryTests();
  runCanvasObjectGeometryTests();
  runCanvasObjectPartsTests();
  runWholeHouseGlbTests();
  runSolidMaterialTests();
  runSelectionRegistrationTests();
  runViewFramingTests();
  runVisibilityTests();
  runBomTests();
  runPlanWarningTests();
  runSpaceLabelTests();
  runTransitionTests();
  runVaporTests();
  runOpenHouseTests();
  runModelGeometryTests();
  runDoorSymbolTests();
  runRoofGeometryTests();
  runMaterialGeometryTests();
  runMemberColorTests();
  runDetailAnnotationTests();
  runMemberPickingTests();
  console.log("Plan geometry tests passed.");
} finally {
  await server.close();
}
