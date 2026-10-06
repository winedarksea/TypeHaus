export interface EngineeringFamily {
  kind: string;
  calculation: string;
  appendix: string;
  members: { item_id: string; path: string }[];
}

export interface EngineeringCalculations {
  revision: string;
  files: Record<string, string>;
  families: EngineeringFamily[];
}
