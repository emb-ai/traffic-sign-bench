// ─────────────────────────────────────────────────────────────────────────────
// SCENARIO DIVERSITY — one real-map crop → background agents at nuPlan density quantiles → 10 variants → 29,000.
// Component: src/scenes/S16_Diversity.tsx. Paper Sec. III-D ("Rule-Targeted Scenario Generation").
//
// Data (all real, 2026-09-22):
//  • Map = the corridor crop of the real-maps slide (seg_1241471060, sign 4.2.1 detour right). Its 10 test variants are
//    rows 1–10 of traffic-rule-bench-main/data/runs_v7/detour_right/test/real_manifest.jsonl; frames = GIF step 10
//    (square 800×800, one second into the rollout) of a rule-compliant IDM rollout of each row, rendered without the text HUD
//    (server: icra-video/generated/diversity/seg_1241471060, tools/nohud_run.py). Previous 480×800 step-20 crops
//    live in public/diversity/_old/. Caption values are the row fields density_percentile, spawn_velocity_ms,
//    route_length_level_m.
//  • Histogram = nuPlan count_moving_r150_per_lane (moving vehicles within 150 m per lane of the ego road),
//    traffic_bench/eval/engine/traffic/nuplan_statistics/densities.csv.gz → public/diversity/nuplan_density_hist.json.
//    The benchmark probes its p25 / p50 / p75 (2.33 / 4.0 / 5.5), see traffic_density_levels.py.
// ─────────────────────────────────────────────────────────────────────────────

export const DIVERSITY = {
  durationSec: 14,
  kicker: "Scenario diversity",
  title: "Map expansion enables statistically robust evaluation",
  subtitle: "Each real map becomes 10 controlled closed-loop variants",
  axisLabel: "We sample",
  axes: [
    { number: "01", label: "Ego spawn lane", detail: "sampled when sign-valid", example: false },
    { number: "02", label: "Route length", detail: "distance levels", example: false },
    { number: "03", label: "Initial speed", detail: "3.6 · 7.8 · 11.1 m/s", example: false },
    { number: "04", label: "Traffic density", detail: "nuPlan p25 · p50 · p75", example: true },
    { number: "05", label: "Background-agent dynamics", detail: "IDM behavior profiles", example: false },
  ],

  timing: {
    header: 0.1,
    crop: 0.3, // the corridor crop of the real-maps slide
    zoom: 1.2, // crop zooms in → simulator frame of the same map, no traffic yet
    hist: 2.6, // nuPlan density histogram
    levels: [3.4, 4.9, 6.4], // p25 → p50 → p75: marker moves, traffic around the ego changes
    tiles: 8.2, // the map multiplies into its 10 variants
    tileStep: 0.12,
    formula: 9.9,
  },

  crop: { src: "real_maps/corridor.png", label: "Corridor · real-map crop", sign: "signs/detour_right.png" },
  emptyFrame: "diversity/v1.png", // variant v0 at rollout step 10: no background traffic
  histogram: "diversity/nuplan_density_hist.json",
  histTitle: "Worked example · traffic density",
  histSubtitle: "Background traffic is sampled from the empirical nuPlan distribution",
  histAxis: "moving vehicles within 150 m, per lane",
  agentsNote: "Background agents follow IDM with nuPlan-sampled parameters",
  levels: [
    { name: "sparse", q: 25, value: 2.33, frame: "diversity/v4.png" },
    { name: "typical", q: 50, value: 4.0, frame: "diversity/v2.png" },
    { name: "dense", q: 75, value: 5.5, frame: "diversity/v8.png" },
  ],

  gridKicker: "One source map",
  gridTitle: "10 sampled variants",
  gridNote: "same road geometry · different controlled conditions",

  // the 10 test variants of the map (manifest rows 1–10): density · initial speed · route length, and the IDM
  // time headway of the background agents (profile_TIME_WANTED, one of the sampled agent-dynamics parameters)
  tiles: [
    { src: "diversity/v1.png", caption: "no traffic · 5.0 m/s · 90 m", agents: "base scene" },
    { src: "diversity/v2.png", caption: "p50 · 11.1 m/s · 90 m", agents: "IDM headway 0.79 s" },
    { src: "diversity/v3.png", caption: "p50 · 7.8 m/s · 90 m", agents: "IDM headway 1.05 s" },
    { src: "diversity/v4.png", caption: "p25 · 7.8 m/s · 120 m", agents: "IDM headway 0.93 s" },
    { src: "diversity/v5.png", caption: "p75 · 3.6 m/s · 120 m", agents: "IDM headway 2.74 s" },
    { src: "diversity/v6.png", caption: "p50 · 11.1 m/s · 90 m", agents: "IDM headway 1.02 s" },
    { src: "diversity/v7.png", caption: "p50 · 3.6 m/s · 90 m", agents: "IDM headway 0.42 s" },
    { src: "diversity/v8.png", caption: "p75 · 11.1 m/s · 120 m", agents: "IDM headway 0.62 s" },
    { src: "diversity/v9.png", caption: "p75 · 7.8 m/s · 120 m", agents: "IDM headway 3.75 s" },
    { src: "diversity/v10.png", caption: "p75 · 3.6 m/s · 120 m", agents: "IDM headway 3.75 s" },
  ],
  formula: [
    { value: "29", label: "scenario types" },
    { value: "100", label: "maps per type" },
    { value: "10", label: "variants per map" },
  ],
  total: "29,000",
  totalLabel: "closed-loop scenarios",
  split: "23,200 train · 5,800 test",
};
