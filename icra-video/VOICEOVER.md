# VOICEOVER — draft (editable), ≈ 175 s, ~420 words at a calm scientific pace

Timings are the scene windows from `src/config/timing.ts`. The video is readable without audio; the narration adds causality, not new facts. Every number is from the current paper.

| # | Window | Narration |
|---|---|---|
| 01 | 0:00–0:11 | A planner can look successful under conventional driving outcomes — and still violate a specific traffic rule. Here, a learned planner drives straight into a no-entry road. Aggregate driving metrics do not explicitly measure target-rule compliance. |
| 02 | 0:11–0:24 | TrafficSignBench turns sign-associated rules into explicit closed-loop tests: thirty-four traffic signs, twenty-nine functional scenario types, and twenty-nine thousand closed-loop scenarios, organised in four semantic groups — priority, speed, obstacles and routing. |
| 03 | 0:24–0:44 | The benchmark is grounded in real road geometry. Sign-free fragments are harvested from the Moscow road network — twenty-six thousand real-map crops: junctions, dual-path maps and corridors. Each crop becomes a simulator scene, and each scene an executable rule test. |
| 04 | 0:44–1:03 | Random agent placement rarely probes the intended rule. So interactions are rule-targeted. For yielding, a gated convoy on the main road is released exactly as the ego approaches the conflict zone. For crosswalks, pedestrians follow controlled timing presets, including late arrivals and chained groups. Rule-targeted interactions make the rule matter. |
| 05 | 1:03–1:17 | Routing restrictions require a rule-aware route decision. On dual-path maps, the destination is chosen so that the prohibited branch is the shortest path. The shortest route violates the active restriction; compliance requires replanning onto the longer route. |
| 06 | 1:17–1:28 | Twenty-nine scenario types, one hundred real-map crops each, ten variants per map — twenty-nine thousand scenarios, varying spawn lane, initial speed, route length, traffic density and background dynamics. Maps are split eighty–twenty by unique OpenStreetMap ID before any sign is assigned. |
| 07 | 1:28–1:37 | Sign appearance varies across jurisdictions, but the underlying rule semantics are largely shared: on average, ninety-two percent of the implemented signs have a semantic equivalent across the analysed Vienna-Convention signatories. |
| 08 | 1:37–1:52 | Planners receive structured sign semantics and output a trajectory; an online checker verifies every rollout. The primary metric, SCD, counts an episode only when the sign is obeyed *and* the destination is reached. |
| 09 | 1:52–2:01 | Under this criterion, standard planners reach only two point nine to nine percent overall SCD. Can the gap be closed? |
| 10 | 2:01–2:19 | We adapt PlanT-2 without touching its backbone. Traffic signs enter as object tokens with learned class projections. A persistent sign-state token stores the active sign class and its posted value. A learnable speed token feeds a discrete ego-speed head, trained jointly with the path and waypoint heads. This adds one hundred forty-eight thousand parameters — 0.4 percent. The model is fine-tuned on oracle expert trajectories. |
| 11 | 2:19–2:33 | Overall SCD rises from five point nine to seventy-two point three percent, across every semantic group. The benchmark exposes an actionable capability gap. |
| 12 | 2:33–2:46 | Is it the sign channel? Removing sign identity from the planner input — while the physical plates stay in the scene — drops SCD from seventy-two point eight to fifteen point four percent on five hundred eighty paired episodes. |
| 13 | 2:46–2:54 | What remains hard? Twenty-five percent of episodes obey the sign but miss the destination; only three percent violate the sign. Remaining failures are primarily navigational. |
| 14 | 2:54–2:57 | TrafficSignBench: explicit rule-conditioned closed-loop evaluation. |
