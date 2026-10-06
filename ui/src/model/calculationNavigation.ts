import type { EngineeringCalculations } from "../engine/engineeringTypes";

export interface CalculationPage {
  path: string;
  title: string;
}
export interface CalculationGroup {
  title: string;
  pages: CalculationPage[];
  members?: { family: string; pages: CalculationPage[] }[];
}

/** Every package file has one navigation entry, including the reading guide. */
export function calculationGroups(payload: EngineeringCalculations): CalculationGroup[] {
  const page = (path: string): CalculationPage => ({
    path,
    title: payload.files[path]?.match(/^# (.+)$/m)?.[1]
      ?? path.replace(/\.md$/, "").replace(/_/g, " "),
  });
  return [
    { title: "Overview", pages: Object.keys(payload.files)
      .filter((path) => !path.includes("/"))
      .sort((a, b) => a.localeCompare(b)).map(page) },
    { title: "Calculations by family", pages: payload.families.map((family) => page(family.calculation)) },
    { title: "Appendices", pages: payload.families.map((family) => page(family.appendix)),
      members: payload.families.map((family) => ({
        family: family.kind.replace(/_/g, " "),
        pages: family.members.map((member) => ({ path: member.path, title: member.item_id })),
      })) },
  ];
}

export function matchesCalculation(page: CalculationPage, filter: string): boolean {
  const needle = filter.trim().toLowerCase();
  return `${page.title} ${page.path}`.toLowerCase().includes(needle);
}

export function selectedCalculation(payload: EngineeringCalculations, path: string): string {
  return path in payload.files ? path : "00-cover.md";
}
