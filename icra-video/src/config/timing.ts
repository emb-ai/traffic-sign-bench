// ─────────────────────────────────────────────────────────────────────────────
// TIMING — scene durations (seconds) and in-scene reveal times (seconds).
// "Make Scene 4 three seconds longer" = change one number in SCENE_SECONDS.
// FPS is fixed at 30.
// ─────────────────────────────────────────────────────────────────────────────
import { FT_SCENE } from "./fineTuningScene";
import { CONCLUSION } from "./conclusionScene";
import { DIVERSITY } from "./diversityScene";

export const FPS = 30;

export const SCENE_SECONDS = {
  s01_hook: 22,
  s02_benchmark: 11,
  s02b_taxonomy: 19,
  s07_portability: 9,
  s03_realmaps: 19,
  s04_targeted: 17,
  s05_routing: 13,
  s06_scale: 10,
  s08_interface: 14,
  s09_gap: 12,
  // Colleague fine-tuning section (expert collection → planner input → PlanT-2-FT)
  s10_architecture: FT_SCENE.durationSec,
  s11_result: 14,
  s12_ablation: 12, // kept for standalone / types; omitted from SCENE_ORDER
  s13_failures: 8,
  s16_diversity: DIVERSITY.durationSec, // scenario diversity, right after the real-maps slide
  s15_conclusion: CONCLUSION.durationSec, // main findings, after the fine-tuning section
  s14_end: 3,
} as const;

export type SceneKey = keyof typeof SCENE_SECONDS;
// s04–s06, s08, s11 + s13 (results and failures are shown at the end of s10), s12 stay available as components, but are omitted from the current cut.
export const SCENE_ORDER: SceneKey[] = [
  "s01_hook",
  "s02_benchmark",
  "s02b_taxonomy",
  "s07_portability",
  "s03_realmaps",
  "s16_diversity",
  "s09_gap",
  "s10_architecture",
  "s15_conclusion",
  "s14_end",
];

export const TOTAL_SECONDS = SCENE_ORDER.reduce((a, k) => a + SCENE_SECONDS[k], 0);
export const TOTAL_FRAMES = TOTAL_SECONDS * FPS;

// Cross-fade at every scene boundary (seconds). 0 = hard cut.
export const SCENE_FADE = 0.35;

// In-scene reveal times, in seconds from the start of that scene.
export const T = {
  // checks: early in the first pass (shortly after headline + example)
  s01: { headline: 0.25, example: 0.75, checks: 2.6, ruleFail: 15.3, mainText: 16.6 },
  s02: { title: 0.2, cards: 1.0, cardStep: 0.35, numbers: 5.5 },
  s03: {
    map: 0.1,
    counterStart: 1.6,
    counterEnd: 4.2,
    breakdown: 2.45,
    selection: 5.25,
    crops: 5.75,
    signs: 9.15,
    rollouts: 11.45,
  },
  s04: { yieldClipTrim: 4.0, convoyLabel: 3.0, yieldLabel: 6.0, crosswalkStart: 11.0, mainText: 8.0 },
  s05: { map: 0.0, baseline: 1.5, compliant: 3.5, rollout: 6.5, mainText: 4.5 },
  s06: { formula: 0.5, axes: 3.0, axisStep: 0.35, split: 6.0, splitStep: 0.6 },
  s07: { figure: 0.3, flags: 1.5, flagStep: 0.18, result: 4.7 },
  s08: { chain: 0.5, chainStep: 0.7, hud: 4.5, scd: 8.5, scdStep: 1.2 },
  s09: { clips: 0.3, numbers: 3.0, question: 6.5 },
  s10: {
    scene: 0.3,
    baseTokens: 1.2,
    signToken: 3.5,
    stateToken: 5.5,
    speedToken: 7.5,
    heads: 9.5,
    params: 11.0,
    expert: 12.5,
    rollout: 15.0,
  },
  s11: { clips: 0.3, numbers: 3.0, bars: 6.0, barStep: 0.5 },
  s12: { clips: 0.3, numbers: 3.5, compliance: 8.0 },
  s13: { numbers: 0.5, text: 4.0 },
  s14: { title: 0.2 },
};
