# VOICEOVER — final timed script (2:59)

This script was written from the current visual cut. It introduces no terms or
claims beyond those already shown on screen. Cue timing is relative to each
scene; absolute scene windows match `src/config/timing.ts`.


| Absolute window | Scene cue | Narration                                                                                                                                 |
| --------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| 0:00–0:22       | 0.5       | At first glance, this trajectory looks successful.                                                                                           |
|                 | 4.7       | PlanT-2 earns a perfect driving score and avoids every collision.                                                                  |
|                 | 9.6       | Now watch the rule itself. At step fifty, the car keeps moving.                                                                           |
|                 | 15.3      | It fails to yield at the crosswalk. High metrics have hidden an illegal behavior.                                                         |
| 0:22–0:33       | 0.5       | TrafficSignBench makes rule compliance verifiable.                                                                                        |
|                 | 4.7       | Thirty-four signs, automatic checkers, and twenty-nine thousand targeted scenarios.                                                       |
| 0:33–0:52       | 0.4       | We start from all eight Vienna Convention classes.                                                                                        |
|                 | 4.6       | We retain only signs that impose explicit obligations with verifiable rule logic.                                                         |
|                 | 10.6      | Thirty-four signs remain, grouped by what capability they demand of the ego vehicle: priority, speed, obstacles, and routing.             |
| 0:52–1:01       | 0.4       | Across countries, rule meaning overlaps by ninety-two percent.                                                                            |
|                 | 5.0       | Change the appearance; reuse the same checker.                                                                                            |
| 1:01–1:20       | 0.3       | Every test begins with real road geometry: twenty-six thousand Moscow road fragments.                                                     |
|                 | 5.9       | We preserve three structural families: junctions, dual-path maps, and corridors.                                                          |
|                 | 11.9      | A sign turns each fragment into a simulator scene—and an executable closed-loop rule test.                                                |
| 1:20–1:36       | 0.3       | For each map, we sample ten controlled closed-loop variants.                                                                              |
|                 | 4.9       | We vary spawn lane, route, speed, traffic density, and background dynamics.                                                               |
|                 | 10.3      | Ten variants per map yield twenty-nine thousand scenarios—and robust evaluation.                                                          |
| 1:36–1:48       | 0.4       | We next evaluate standard planners. The metric is SCD: obey the sign and reach the destination.                                           |
|                 | 7.7       | Standard planners score only two point nine to nine percent.                                                                              |
| 1:48–2:34       | 0.5       | To close the gap, PlanT-2 learns from privileged, rule-compliant experts.                                                                 |
|                 | 5.8       | Eight experts drive each scenario. Failed rollouts are discarded.                                                                         |
|                 | 11.4      | We retain the top two successful trajectories by speed and comfort: thirty-six thousand eight hundred twenty-eight high-quality examples. |
|                 | 19.0      | Each frame becomes input: objects, sign, route, and local map.                                                                            |
|                 | 24.0      | Persistent sign-state and learned speed tokens carry the active rule and vehicle speed.                                                   |
|                 | 29.2      | We train on expert path, waypoints, and speed, adding just zero point four percent new parameters.                                        |
|                 | 37.2      | On held-out tests, overall SCD rises from five point nine to seventy-two point three percent, with gains in every group.                  |
| 2:34–2:56       | 0.4       | Therefore, this work shows that traffic-rule compliance must be tested explicitly.                                                        |
|                 | 5.7       | TrafficSignBench does it at scale: thirty-four signs, twenty-nine thousand closed-loop scenarios.                                         |
|                 | 12.7      | Safe autonomous driving needs scores that catch rule compliance—not only the destination or comfort.                                      |
| 2:56–2:59       | —         | Silent end card.                                                                                                                          |


The neural voice settings and exact cue bounds are in
`src/config/voiceover.json`. Regenerate the audio with:

```console
python tools/generate_voiceover.py
```

