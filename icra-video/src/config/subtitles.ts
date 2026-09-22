// Draft subtitles, one list per scene (seconds relative to the scene start).
// Mirrors VOICEOVER.md. Enable with SHOW_SUBTITLES in config/style.ts.
import { SceneKey } from "./timing";
import type { SubLine } from "../lib/Subtitles";

export const SUBTITLES: Record<SceneKey, SubLine[]> = {
  s01_hook: [
    { from: 0.5, to: 10.0, text: "PlanT-2 reaches the destination without a collision and receives a high driving score of 90." },
    { from: 10.2, to: 15.2, text: "Yet under conventional metrics, critical traffic-rule violations go completely unnoticed." },
    { from: 15.3, to: 20.5, text: "At step 50, ego fails to yield to pedestrians on the crosswalk. Existing benchmarks do not make compliance directly verifiable." },
  ],
  s02_benchmark: [
    { from: 0.4, to: 5.5, text: "To address this gap, we introduce TrafficSignBench — a large-scale benchmark for systematic compliance evaluation." },
    { from: 5.8, to: 11.5, text: "It combines 34 traffic signs, automatic rule checkers, and 29,000 rule-targeted closed-loop scenarios across 17 planners." },
  ],
  s02b_taxonomy: [
    { from: 0.3, to: 5, text: "We begin with the eight sign classes of a Vienna-Convention reference system." },
    { from: 5, to: 10, text: "We retain explicit obligations with machine-verifiable outcomes, excluding primarily advisory, contextual, or conditional signs." },
    { from: 10, to: 17.7, text: "The resulting 34 implemented signs are reorganized into priority, speed, obstacles, and routing." },
  ],
  s03_realmaps: [
    { from: 0.5, to: 5.2, text: "The benchmark is grounded in real road geometry: 26,020 sign-free crops of the Moscow road network." },
    { from: 5.2, to: 11.4, text: "Junctions, dual-path maps and corridors preserve three distinct structural families." },
    { from: 11.4, to: 17.7, text: "A traffic sign turns each real-map crop into a closed-loop executable rule test." },
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
    { from: 0.3, to: 7.7, text: "Legal semantics remain 92% invariant across jurisdictions; adaptation requires only swapping sign appearance while reusing rule logic." },
  ],
  s08_interface: [
    { from: 0.5, to: 7, text: "Planners receive structured sign semantics; an online checker verifies every rollout." },
    { from: 7, to: 14.5, text: "SCD counts an episode only if the sign is obeyed and the destination is reached." },
  ],
  s09_gap: [
    { from: 0.5, to: 8.5, text: "Standard planners reach only 2.9 to 9.0 percent overall SCD. Can the gap be closed?" },
  ],
  s10_architecture: [
    { from: 0.3, to: 5.4, text: "Can the gap be closed? Explicit sign constraints turn planners into privileged experts, and PlanT-2 learns from their best trajectories." },
    { from: 5.6, to: 18.8, text: "All eight experts drive each training scenario. We keep only rollouts that obey the sign and reach the destination, and retain the top two by speed and comfort: 36,828 oracle trajectories." },
    { from: 19.1, to: 26.8, text: "Each frame becomes planner input: object tokens for the vehicles and the sign, the route and a local map, plus a persistent sign-state token and a learned speed token." },
    { from: 27.0, to: 31.2, text: "These additions cost only 0.4% parameters; the PlanT-2 backbone is unchanged." },
    { from: 31.4, to: 36.4, text: "The selected expert trajectory supervises path, waypoints and speed, producing PlanT-2-FT." },
    { from: 36.9, to: 52.5, text: "On held-out test scenarios, overall SCD rises from 5.9% to 72.3%, with gains in every group, within 7.7 points of the strongest privileged expert." },
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
  s16_diversity: [
    { from: 0.3, to: 7.9, text: "We vary the conditions and target the interaction: background agents are added at the sparse, typical and dense quantiles of nuPlan traffic." },
    { from: 8.2, to: 13.7, text: "Each map becomes ten variants of spawn, speed, route, density and agent dynamics: 29 × 100 × 10 = 29,000 scenarios." },
  ],
  s15_conclusion: [
    { from: 0.3, to: 15.7, text: "TrafficSignBench turns 34 traffic signs into 29,000 verifiable closed-loop tests on real maps. Standard planners reach at most 9% SCD; rule-supervised fine-tuning lifts PlanT-2 to 72.3%. Right-of-way and sign-conditioned routing remain the open challenge." },
  ],
  s14_end: [],
};
