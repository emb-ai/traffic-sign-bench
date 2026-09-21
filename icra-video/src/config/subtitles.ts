// Draft subtitles, one list per scene (seconds relative to the scene start).
// Mirrors VOICEOVER.md. Enable with SHOW_SUBTITLES in config/style.ts.
import { SceneKey } from "./timing";
import type { SubLine } from "../lib/Subtitles";

export const SUBTITLES: Record<SceneKey, SubLine[]> = {
  s01_hook: [
    { from: 0.5, to: 5, text: "A planner can look successful under conventional driving outcomes…" },
    { from: 5, to: 10.5, text: "…while violating a specific traffic rule. Aggregate metrics do not measure target-rule compliance." },
  ],
  s02_benchmark: [
    { from: 0.5, to: 6, text: "TrafficSignBench turns sign-associated rules into explicit closed-loop tests." },
    { from: 6, to: 12.5, text: "34 traffic signs, 29 functional scenario types, 29,000 closed-loop scenarios in four semantic groups." },
  ],
  s03_realmaps: [
    { from: 0.5, to: 6, text: "The benchmark is grounded in real road geometry: sign-free fragments of the Moscow road network." },
    { from: 6, to: 12, text: "26,020 real-map crops: junctions, dual-path maps and corridors." },
    { from: 12, to: 19.5, text: "Each crop becomes a simulator scene and an executable rule test." },
  ],
  s04_targeted: [
    { from: 0.5, to: 8, text: "Random agent placement rarely activates the rule. Here a gated convoy is released exactly as the ego approaches." },
    { from: 8, to: 18.5, text: "Pedestrians follow controlled timing presets. Rule-targeted interactions make the rule matter." },
  ],
  s05_routing: [
    { from: 0.5, to: 7, text: "On dual-path maps the destination makes the prohibited branch the shortest path." },
    { from: 7, to: 13.5, text: "Compliance requires replanning onto the longer route." },
  ],
  s06_scale: [
    { from: 0.5, to: 5, text: "29 scenario types, 100 real-map crops each, 10 variants: 29,000 scenarios." },
    { from: 5, to: 10.5, text: "Maps are split by unique OpenStreetMap ID before sign assignment." },
  ],
  s07_portability: [
    { from: 0.5, to: 8.5, text: "Sign appearance varies across jurisdictions; the rule semantics largely do not — 92% average overlap among Vienna-Convention signatories." },
  ],
  s08_interface: [
    { from: 0.5, to: 7, text: "Planners receive structured sign semantics; an online checker verifies every rollout." },
    { from: 7, to: 14.5, text: "SCD counts an episode only if the sign is obeyed and the destination is reached." },
  ],
  s09_gap: [
    { from: 0.5, to: 8.5, text: "Standard planners reach only 2.9 to 9.0 percent overall SCD. Can the gap be closed?" },
  ],
  s10_architecture: [
    { from: 0.5, to: 6, text: "PlanT-2 keeps its backbone. Signs enter as object tokens with learned class projections." },
    { from: 6, to: 11, text: "A persistent sign-state token stores the active sign and posted value; a speed token feeds a discrete speed head." },
    { from: 11, to: 17.5, text: "Only 0.4% more parameters, fine-tuned on oracle expert trajectories." },
  ],
  s11_result: [
    { from: 0.5, to: 13.5, text: "Overall SCD rises from 5.9% to 72.3%. The benchmark exposes an actionable capability gap." },
  ],
  s12_ablation: [
    { from: 0.5, to: 12.5, text: "Removing sign identity from the input — plates still in the scene — drops SCD from 72.8% to 15.4% on 580 paired episodes." },
  ],
  s13_failures: [
    { from: 0.5, to: 7.5, text: "24.7% of episodes obey the sign but miss the destination; only 3.4% violate it. Remaining failures are navigational." },
  ],
  s14_end: [],
};
