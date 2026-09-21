// ─────────────────────────────────────────────────────────────────────────────
// CONTENT — every visible scientific text and number.
// Source of truth: the CURRENT paper (Self_Driving-3.pdf). Section/table
// references are given per item. Edit text here, not inside scene files.
// ─────────────────────────────────────────────────────────────────────────────

export const BENCH = "TrafficSignBench";

export const NUMBERS = {
  signs: 34, // Sec. III-A, Fig. 1
  scenarioTypes: 29, // Sec. III-B
  scenarios: "29,000", // Sec. III-D
  mapsPerSign: 100, // Sec. III-C: 100 maps per sign (80 train / 20 test)
  variantsPerMap: 10, // Sec. III-D
  train: "23,200",
  test: "5,800",
  crops: "26,020", // Sec. III-C
  junctions: "6,457",
  dualPath: "6,507",
  corridors: "13,056",
  semanticOverlap: "92%", // Table I, mean over Vienna signatories
  standardPlannersSCD: "2.9–9.0%", // Sec. V-A, Table II
  plant2SCD: 5.9, // Table II
  plant2FtSCD: 72.3, // Table II
  gainPoints: "+66.4", // Sec. V-A
  ablationEpisodes: 580, // Sec. V-D
  ablationSCD: { with: 72.8, without: 15.4 },
  ablationCompliance: { with: 90.3, without: 28.9 },
  failObeyMiss: "24.7%", // Sec. V-B: 1,430 of 5,800
  failViolate: "3.4%", // Sec. V-B: 198 episodes
  failCompliance: "96.6%", // Sec. V-B pooled sign compliance
  plannerParams: "37.2 M", // Sec. IV-D
  addedParams: "147,976", // Sec. IV-D
  addedParamsPct: "+0.4%",
  oracleTrajectories: "36,828", // Sec. IV-C
};

// Table II — group SCD (%) for PlanT-2 vs PlanT-2-FT
export const GROUP_SCD = [
  { key: "priority", label: "Priority", base: 5.8, ft: 57.2 },
  { key: "speed", label: "Speed", base: 29.8, ft: 96.2 },
  { key: "obstacles", label: "Obstacles", base: 0.7, ft: 90.8 },
  { key: "routing", label: "Routing", base: 1.1, ft: 58.4 },
] as const;

// Table II — overall SCD of standard baselines
export const BASELINE_SCD = [
  { label: "IDM", scd: 7.2 },
  { label: "PPO", scd: 3.2 },
  { label: "CaRL", scd: 2.9 },
  { label: "PlanT-2", scd: 5.9 },
];

// Table I — semantic equivalence of the 34 signs per country
export const COUNTRIES = [
  { key: "germany", label: "Germany", pct: 91, vienna: true },
  { key: "france", label: "France", pct: 84, vienna: true },
  { key: "italy", label: "Italy", pct: 94, vienna: true },
  { key: "turkey", label: "Turkey", pct: 100, vienna: true },
  { key: "uk", label: "UK", pct: 97, vienna: false },
  { key: "china", label: "China", pct: 91, vienna: false },
];

// Fig. 1 — semantic groups
export const GROUPS = [
  { key: "priority", signs: 8, scenarios: 6, example: "yield" },
  { key: "speed", signs: 7, scenarios: 4, example: "speed limit" },
  { key: "obstacles", signs: 8, scenarios: 8, example: "detour" },
  { key: "routing", signs: 11, scenarios: 11, example: "one way" },
] as const;

export const TEXT = {
  s01: {
    kicker: "Closed-loop rollout · sign 3.1 “No entry”",
    headline: "Looks fine. Breaks the rule.",
    checks: [
      { label: "Destination", note: "not shown in this clip", state: "unknown" },
      { label: "Collision-free", note: "not shown in this clip", state: "unknown" },
      { label: "Rule compliant", note: "on-screen verifier: violations > 0", state: "fail" },
    ],
    main: "Aggregate driving metrics do not explicitly measure target-rule compliance.",
    clipLabel: "PlanT-2 (baseline) · planner enters a no-entry road",
  },
  s02: {
    title: `${BENCH}`,
    subtitle: "sign-associated rules → explicit closed-loop tests",
    stats: [
      { value: "34", label: "traffic signs" },
      { value: "29", label: "functional scenario types" },
      { value: "29,000", label: "closed-loop scenarios" },
    ],
  },
  s03: {
    headline: "Real road geometry",
    headline2: "→ executable rule test",
    steps: ["Moscow road network (OpenStreetMap → SUMO)", "Crop a sign-free fragment", "Real-map crop", "Simulator scene", "Closed-loop rollout"],
    cropsLabel: "real-map crops",
    breakdown: [
      { label: "Junctions", n: "6,457", use: "priority" },
      { label: "Dual-path", n: "6,507", use: "routing" },
      { label: "Corridors", n: "13,056", use: "speed · obstacles · crosswalk" },
    ],
    mapCaption: "all 26,020 crop centres on the real network",
    rolloutLabel: "closed-loop rollout on this crop",
  },
  s04: {
    headline: "Rule-targeted interactions make the rule matter.",
    sub: "Random agent placement rarely activates the rule — TrafficSignBench creates rule-critical interactions.",
    yieldTitle: "Yield (sign 2.4)",
    yieldSteps: ["ego approaches the junction", "gated convoy on the main road is released as the ego approaches", "planner must yield"],
    crosswalkTitle: "Crosswalk (sign 5.19)",
    crosswalkSteps: ["pedestrians follow controlled temporal presets", "late-arriving individuals · chained groups"],
    yieldClipLabel: "fine-tuned PlanT-2 rollout*",
    crosswalkClipLabel: "rule-compliant expert rollout",
    footnote: "* intermediate fine-tuning checkpoint",
  },
  s05: {
    headline: "The shortest route violates the active restriction.",
    headline2: "Compliance requires replanning.",
    sign: "Sign 4.1.2 “Turn right” on a real dual-path T-junction",
    baseline: { label: "shorter route → prohibited", length: "95 m" },
    compliant: { label: "longer route → compliant", length: "313 m" },
    rolloutLabel: "fine-tuned PlanT-2 rollout on this map*",
    footnote: "* intermediate fine-tuning checkpoint · routes from scene metadata",
  },
  s06: {
    headline: "Real-map diversity × controlled variation",
    formula: ["29", "×", "100", "×", "10", "=", "29,000"],
    formulaLabels: ["scenario types", "", "real-map crops each", "", "variants", "", "scenarios"],
    axes: ["ego spawn lane", "initial speed", "route length", "traffic density", "background dynamics"],
    axesNote: "sampled from nuPlan-calibrated distributions",
    split: ["Unique OpenStreetMap IDs", "80 / 20 train–test split", "sign assignment"],
    splitText: "Split before sign assignment",
    splitSizes: "23,200 train · 5,800 test",
  },
  s07: {
    headline: "Different appearance. Shared rule semantics.",
    sub: "of the 34 implemented signs have a semantic equivalent",
    result: "92% average semantic overlap",
    resultSub: "across analysed Vienna-Convention signatories",
    vienna: "Vienna Convention",
    nonVienna: "Non-Vienna",
    figureNote: "“Yield” and “Turn left” in seven jurisdictions",
  },
  s08: {
    chain: ["Structured sign semantics", "Planner", "Trajectory", "Online rule checker"],
    smallLabel: "Planning-level compliance",
    compliant: "COMPLIANT ✓",
    violation: "VIOLATION ✕",
    clipLeft: "rule-compliant expert · sign 5.15.1",
    clipRight: "PlanT-2 · sign 5.15.1",
    scdTitle: "SCD — Sign Compliance × Destination",
    scdRows: [
      { obey: true, dest: true, scd: true },
      { obey: true, dest: false, scd: false },
      { obey: false, dest: true, scd: false },
    ],
    scdLabels: { obey: "Obey sign", dest: "Reach destination", scd: "SCD" },
  },
  s09: {
    headline: "Standard planners",
    number: "2.9–9.0%",
    numberLabel: "overall SCD on all 29 scenario types",
    clips: [
      { label: "IDM · no entry", scd: "7.2%" },
      { label: "CaRL · one way", scd: "2.9%" },
      { label: "PlanT-2 · lane directions", scd: "5.9%" },
    ],
    question: "Can the gap be closed?",
  },
  s10: {
    headline: "PlanT-2 → PlanT-2-FT",
    sub: "37.2 M-parameter PlanT-style planner · backbone unchanged",
    sceneLabel: "structured scene representation",
    baseTokens: ["vehicles", "pedestrians", "static objects", "route"],
    newTokens: [
      { title: "traffic-sign object tokens", note: "learned class projection per sign class" },
      { title: "persistent sign-state token", note: "active sign class + posted value" },
      { title: "learnable speed token", note: "feeds a discrete ego-speed head" },
    ],
    backbone: "PlanT-2 transformer backbone",
    heads: ["path", "waypoints", "speed"],
    headsNote: ["L1", "L1", "cross-entropy, soft two-hot"],
    params: "+147,976 parameters (+0.4%)",
    expert: ["36,828 oracle expert trajectories", "rule-supervised fine-tuning", "PlanT-2-FT"],
    rolloutLabel: "fine-tuned PlanT-2 rollout*",
    footnote: "* intermediate fine-tuning checkpoint",
  },
  s11: {
    metric: "Overall SCD · all 29 scenario types",
    left: { name: "PlanT-2", value: "5.9%", clip: "no entry · violations: 9" },
    right: { name: "PlanT-2-FT", value: "72.3%", clip: "no entry · violations: 0*" },
    gain: "+66.4 points",
    barsTitle: "Group SCD (%)",
    footnote: "* different scenes; fine-tuned rollout from an intermediate checkpoint",
    takeaway: "The benchmark exposes an actionable capability gap.",
  },
  s12: {
    headline: "Sign-channel ablation",
    sub: "sign identity and sign state removed from the planner input — the physical plates stay in the scene",
    left: "sign input present",
    right: "sign input removed",
    episodes: "580 paired episodes",
    scd: { label: "SCD", from: "72.8%", to: "15.4%" },
    compliance: { label: "Compliance", from: "90.3%", to: "28.9%" },
    missing: "MISSING SCIENTIFIC ASSET: paired rollouts with sign input present vs removed (same scene, same seed)",
  },
  s13: {
    headline: "What remains hard?",
    a: { value: "24.7%", label: "obey the sign, miss the destination" },
    b: { value: "3.4%", label: "violate the target sign" },
    compliance: "PlanT-2-FT sign compliance 96.6% (pooled audit)",
    text: "Remaining failures are primarily navigational.",
    missing: "MISSING SCIENTIFIC ASSET: PlanT-2-FT rollout that obeys the sign but does not reach the destination",
  },
  s14: {
    title: BENCH,
    sub: "Explicit rule-conditioned closed-loop evaluation",
    line: "34 signs · 29 tests · 29,000 scenarios",
  },
};
