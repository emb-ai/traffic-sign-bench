// ─────────────────────────────────────────────────────────────────────────────
// CONCLUSION — main findings of the paper (Sec. VII conclusion + abstract), one card each.
// Component: src/scenes/S15_Conclusion.tsx. Every number is from the current paper.
// ─────────────────────────────────────────────────────────────────────────────
import { COLORS } from "./style";

export const CONCLUSION = {
  durationSec: 16,
  kicker: "Conclusion",
  title: "Traffic-rule compliance must be tested explicitly",
  subtitle: "TrafficSignBench makes it systematic, scalable and verifiable",
  // reveal times (seconds from the start of the scene)
  timing: { header: 0.2, card0: 1.2, cardStep: 2.6 },
  cards: [
    {
      color: COLORS.blue,
      kicker: "Benchmark",
      value: "29,000",
      unit: "closed-loop scenarios",
      body: "34 signs with automatic rule checkers, 29 scenario types, real Moscow road geometry",
      icons: ["signs/yield.png", "signs/speed_limit_40.png", "signs/detour_right.png", "signs/direction_right.png"],
    },
    {
      color: COLORS.red,
      kicker: "Evaluation",
      value: "2.9–9.0%",
      unit: "overall SCD of standard planners",
      body: "High driving scores hide rule violations: conventional metrics are not enough",
      icons: [],
    },
    {
      color: "#2E8B57",
      kicker: "Rule-supervised fine-tuning",
      value: "5.9 → 72.3%",
      unit: "PlanT-2 → PlanT-2-FT",
      body: "Oracle expert trajectories + sign-aware tokens (+0.4% parameters); 96.6% sign compliance",
      icons: [],
    },
  ],
};
