// ─────────────────────────────────────────────────────────────────────────────
// TIMING — scene durations (seconds) and in-scene reveal times (seconds).
// "Make Scene 4 three seconds longer" = change one number in SCENE_SECONDS.
// Total must stay under 180 s. FPS is fixed at 30.
// ─────────────────────────────────────────────────────────────────────────────
export const FPS = 30;

export const SCENE_SECONDS = {
  s01_hook: 11,
  s02_benchmark: 13,
  s03_realmaps: 20,
  s04_targeted: 19,
  s05_routing: 14,
  s06_scale: 11,
  s07_portability: 9,
  s08_interface: 15,
  s09_gap: 9,
  s10_architecture: 18,
  s11_result: 14,
  s12_ablation: 13,
  s13_failures: 8,
  s14_end: 3,
} as const;

export type SceneKey = keyof typeof SCENE_SECONDS;
export const SCENE_ORDER: SceneKey[] = Object.keys(SCENE_SECONDS) as SceneKey[];

export const TOTAL_SECONDS = SCENE_ORDER.reduce((a, k) => a + SCENE_SECONDS[k], 0);
export const TOTAL_FRAMES = TOTAL_SECONDS * FPS;

// Cross-fade at every scene boundary (seconds). 0 = hard cut.
export const SCENE_FADE = 0.35;

// In-scene reveal times, in seconds from the start of that scene.
export const T = {
  s01: { kicker: 0.4, headline: 1.0, checks: 2.0, ruleFail: 5.0, mainText: 7.0 },
  s02: { title: 0.2, cards: 1.0, cardStep: 0.35, numbers: 5.5 },
  s03: {
    fullMap: 0.0,
    highlight: 2.0,
    zoomStart: 3.0,
    zoomEnd: 7.0,
    cropRender: 6.5,
    scenePreview: 10.0,
    rollout: 13.0,
    counterStart: 2.0,
    counterEnd: 5.0,
    breakdown: 6.0,
  },
  s04: { yieldClipTrim: 4.0, convoyLabel: 3.0, yieldLabel: 6.0, crosswalkStart: 11.0, mainText: 8.0 },
  s05: { map: 0.0, baseline: 1.5, compliant: 3.5, rollout: 6.5, mainText: 4.5 },
  s06: { formula: 0.5, axes: 3.0, axisStep: 0.35, split: 6.0, splitStep: 0.6 },
  s07: { figure: 0.3, flags: 2.0, flagStep: 0.3, result: 5.0 },
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
