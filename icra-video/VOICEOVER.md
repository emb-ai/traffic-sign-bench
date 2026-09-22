# VOICEOVER — draft (editable), 179 s, calm scientific pace

Timings are the scene windows from `src/config/timing.ts`. The video is readable without audio; the narration adds causality, not new facts. Every number is from the current paper.

| # | Window | Narration |
|---|---|---|
| 01 | 0:00–0:21 | PlanT-2 reaches its destination without a collision and receives a high driving score of ninety. Yet under conventional metrics, critical traffic-rule violations go completely unnoticed. At step 50, ego fails to yield to pedestrians on the crosswalk. Existing simulation benchmarks do not make traffic-rule compliance systematic, scalable, and directly verifiable. |
| 02 | 0:21–0:33 | To address this gap, we introduce TrafficSignBench: the first large-scale benchmark to jointly combine a broad taxonomy of thirty-four signs, automatic rule checkers, and twenty-nine thousand rule-targeted closed-loop scenarios. We use it to evaluate seventeen planners. |
| 03 | 0:33–0:51 | We begin with the eight sign classes of a Vienna-Convention reference system. We retain explicit obligations with machine-verifiable outcomes, while excluding signs whose meaning is primarily advisory, contextual, or conditional. All thirty-four retained signs are executable in simulation and reorganized by demanded planning capability into priority, speed, obstacles, and routing. |
| 04 | 0:51–0:59 | Legal semantics generalize internationally, with ninety-two percent average overlap across Vienna signatories. TrafficSignBench adapts by swapping sign appearance while reusing the same rule-verification logic. |
| 05 | 0:44–1:02 | The benchmark is grounded in real road geometry. Sign-free fragments are harvested from the Moscow road network — twenty-six thousand real-map crops: junctions, dual-path maps and corridors. Each crop becomes a simulator scene, and each scene an executable rule test. |
| 06 | 1:02–1:19 | Random agent placement rarely probes the intended rule. So interactions are rule-targeted. For yielding, a gated convoy is released as the ego approaches. For crosswalks, pedestrians follow controlled timing presets. |
| 07 | 1:19–1:32 | On dual-path maps, the destination makes the prohibited branch the shortest path. Compliance requires replanning onto the longer route. |
| 08 | 1:32–1:42 | Twenty-nine scenario types, one hundred crops each, ten variants per map: twenty-nine thousand scenarios. Maps are split by OpenStreetMap ID before sign assignment. |
| 09 | 1:42–1:56 | Planners receive structured sign semantics and output a trajectory; an online checker verifies every rollout. SCD counts an episode only when the sign is obeyed and the destination is reached. |
| 10 | 1:56–2:05 | Standard planners reach only two point nine to nine percent overall SCD. Can the gap be closed? |
| 11 | 2:05–2:22 | We adapt PlanT-2 without changing its backbone. Sign and state tokens plus a learnable speed token add only 0.4 percent parameters. The model is fine-tuned on oracle expert trajectories. |
| 12 | 2:22–2:36 | Overall SCD rises from five point nine to seventy-two point three percent. The benchmark exposes an actionable capability gap. |
| 13 | 2:36–2:48 | Removing sign identity while physical plates remain drops SCD from seventy-two point eight to fifteen point four percent on five hundred eighty paired episodes. |
| 14 | 2:48–2:56 | Remaining failures are primarily navigational: twenty-five percent obey the sign but miss the destination; only three percent violate it. |
| 15 | 2:56–2:59 | TrafficSignBench: explicit rule-conditioned closed-loop evaluation. |
