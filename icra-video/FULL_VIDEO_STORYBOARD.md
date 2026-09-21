# FULL VIDEO STORYBOARD — TrafficSignBench ICRA video (2026-09-21)

Format 1920×1080, 30 fps, 179 s total (limit 180 s). Compositions: `ICRA-Full` and the 44 s `ICRA-Intro`.
Edit points: text → `src/config/content.ts`, durations/reveals → `src/config/timing.ts`, look → `src/config/style.ts`, files → `src/config/assets.ts`.
Scene components: `src/scenes/S01_…S14_*.tsx`, including `S02B_Taxonomy.tsx`. Assets provenance: `ASSET_INDEX.md`. Narration: `VOICEOVER.md`.
Every clip is a real project rollout; presentation layer only adds text, boxes, marks, arrows, counters.

---

## 01 · Why explicit rule compliance? — 0:00–0:21 (21 s)
- **MESSAGE** A planner can look successful under conventional outcomes while violating a specific rule.
- **VISUAL** Crosswalk rollout on the left runs first pass at natural 10 Hz physical simulation speed; then conventional metrics appear (Driving Score 90.00, Collision Rate 0%). Video runs a second time and pauses exactly at step 50 as ego fails to yield to pedestrians on crosswalk; red rule-compliance failure alert triggers.
- **ASSET PATHS** `public/converted/problem_crosswalk.mp4`, `public/signs/crosswalk.png`
- **ON-SCREEN TEXT** Headline "High metrics can hide an illegal behaviour"; "Example: Pedestrian crossing compliance"; Driving Score 90.00, Comfort 88.0%, Efficiency 295.3, Collision Rate 0%; "Traffic-rule compliance: FAILED (STEP 50)"; evaluation-gap transition.
- **VOICEOVER** see VOICEOVER.md #01
- **TIMING** headline 0.25 s, example 0.75 s, metrics 10.3 s (after pass 1), rule failure 15.3 s (pausing at step 50), takeaway 16.6 s
- **SCIENTIFIC SOURCE** `data/runs/crosswalk/debug/2026-09-21_16-44-42/episodes_plant2.jsonl`, seed 1356480710

## 02 · TrafficSignBench reveal — 0:21–0:33 (12 s)
- **MESSAGE** The benchmark joins the three components required for systematic compliance evaluation.
- **VISUAL** The camera pulls back over a 7×5 mosaic of 35 diverse benchmark rollouts behind a sleek, compact translucent presentation panel.
- **ASSET PATHS** `public/converted/solution/*.mp4` (35 selected clips)
- **ON-SCREEN TEXT** "To address this gap, we introduce TrafficSignBench"; broad traffic-sign taxonomy · automatic rule checkers · rule-targeted closed-loop scenarios; 34 signs · 29,000 scenarios · 17 planners evaluated
- **SCIENTIFIC SOURCE** Introduction, contribution 1.

## 03 · Rule selection and testing taxonomy — 0:18–0:36 (18 s)
- **VISUAL** Signs begin in eight Vienna-Convention classes. Contextual signs grey out; 34 retained signs remain, then physically move into Priority, Speed, Obstacles, and Routing cards.
- **ASSET PATHS** `public/signs/*`, `public/taxonomy/extra/*`
- **ON-SCREEN TEXT** selection principle; 34 implemented signs with explicit, verifiable rule logic; final counts 8 / 7 / 8 / 11.
- **SCIENTIFIC SOURCE** Sec. III-A/B, Fig. 1.

## 04 · Semantic portability — 0:36–0:44 (8 s)
- **VISUAL** Two rows of real country-specific sign graphics—Yield and Turn left—across Russia, Germany, France, Italy, Turkey, the UK, and China, followed by current Table I values.
- **ASSET PATHS** `public/countries/{yield,direction_left}/*`, `flags/*.png`
- **ON-SCREEN TEXT** 92% average semantic overlap; adaptation by replacing visual appearance without changing verifier logic.
- **SCIENTIFIC SOURCE** Sec. III-A, Table I.

## 05 · Real maps → executable rule tests — 0:44–1:02 (18 s) ★
- **MESSAGE** Grounded in real road geometry, one continuous process.
- **VISUAL** Stage (left): real Moscow SUMO network with all crop centres → blue highlight of the scene's crop bbox (from meta.json) → zoom → project-rendered crop → simulator scene preview → real closed-loop rollout **on the same crop** `dual_T_1303406452`. Right: headline, 5-step list, 26,020 counter, family breakdown.
- **ASSET PATHS** `figures/moscow_crops_overview.png` (+`.json` extents), `figures/map_dual_T_1303406452_plain.png`, `figures/scene_preview_dual_T_1303406452.png`, `converted/eval0912_direction_right_dual_T_1303406452.mp4`
- **ON-SCREEN TEXT** "Real road geometry → executable rule test"; 26,020 real-map crops; Junctions 6,457 · Dual-path 6,507 · Corridors 13,056
- **TIMING** highlight 2 s, zoom 3–7 s, crop 6.5 s, preview 10 s, rollout 13 s
- **SCIENTIFIC SOURCE** Sec. III-C; `scene_collection/maps/index/*.jsonl`; scene `meta.json`
- **TODO** The zoom pixel-aligns the bbox, but the crossfade to the vector crop is not pixel-registered (different renderer margins). Rollout policy label is neutral ("closed-loop rollout") because the checkpoint of that eval GIF is not recorded.

## 06 · Rule-targeted generation — 1:02–1:19 (17 s) ★
- **MESSAGE** Random placement may never activate the rule; interactions are rule-critical.
- **VISUAL** Yield rollout (gated convoy on the main road, HUD shows `is_ego_in_yield_zone`), three numbered steps; then crosswalk rollout of the rule-compliant IDM expert with pedestrians.
- **ASSET PATHS** `converted/ft_n2_yield_junc_1057163165.mp4` (trim 4 s), `converted/expert_idm_rule_crosswalk_seg_1103897132.mp4`, `signs/yield.png`, `signs/crosswalk.png`
- **ON-SCREEN TEXT** "Rule-targeted interactions make the rule matter."; steps; footnote "* intermediate fine-tuning checkpoint"
- **TIMING** crosswalk from 11 s
- **SCIENTIFIC SOURCE** Sec. III-D
- **NOTES** No fake "random" comparison is shown. **[MISSING SCIENTIFIC ASSET: real inactive/random-placement rollout for contrast]**

## 07 · Routing decision — 1:19–1:32 (13 s) ★
- **MESSAGE** The shortest route violates the restriction; compliance requires replanning.
- **VISUAL** Real dual-path crop; project-rendered route overlay from meta.json (red baseline 95 m prohibited / green compliant 313 m); then fine-tuned rollout on that map.
- **ASSET PATHS** `figures/map_dual_T_1303406452_plain.png`, `figures/map_dual_T_1303406452_routes.png`, `converted/ft_augA_direction_right_dual_T_1303406452.mp4`, `signs/direction_right.png`
- **ON-SCREEN TEXT** sign 4.1.2; route lengths; headline; footnote
- **SCIENTIFIC SOURCE** Sec. III-C/III-D; `meta.json` `dual_path.baseline_length_m = 94.93`, `compliant_length_m = 313.26`
- **NOTES** Route geometry is from project data, not drawn by hand.

## 08 · Scale + split — 1:32–1:42 (10 s)
- **VISUAL** 29 × 100 × 10 = 29,000; five variation chips; split chain (Unique OSM IDs → 80/20 → sign assignment); small real overview of crop centres.
- **ASSET PATHS** `figures/moscow_crops_overview.png`
- **ON-SCREEN TEXT** "Split before sign assignment", 23,200 train · 5,800 test, "sampled from nuPlan-calibrated distributions"
- **SCIENTIFIC SOURCE** Sec. III-C (split), III-D (variants), Fig. 2

## 09 · Planner interface + checker + SCD — 1:42–1:56 (14 s)
- **VISUAL** Two real clips (expert: Violations 0 → COMPLIANT ✓; PlanT-2: Violations 1 → VIOLATION ✕, badges appear at 4.5 s, states taken from the clips' own counters); chain diagram; then SCD truth table (✓✓→✓, ✓✕→✕, ✕✓→✕).
- **ASSET PATHS** `converted/pair_5_15_1_plant2_expert.mp4`, `converted/pair_5_15_1_plant2_base.mp4`
- **SCIENTIFIC SOURCE** Sec. IV-A (SCD), Sec. III (verifiers)

## 10 · Existing planner gap — 1:56–2:05 (9 s)
- **VISUAL** IDM / CaRL / PlanT-2 baseline clips; 2.9–9.0%; small bars IDM 7.2, PPO 3.2, CaRL 2.9, PlanT-2 5.9; "Can the gap be closed?"
- **ASSET PATHS** `converted/pair_3_1_idm_base.mp4`, `converted/pair_5_7_1_carl_base.mp4`, `converted/pair_5_15_1_plant2_base.mp4`
- **SCIENTIFIC SOURCE** Table II, Sec. V-A

## 11 · PlanT-2 → PlanT-2-FT architecture — 2:05–2:22 (17 s) ★
- **VISUAL** Animated figure: base object tokens (vehicles, pedestrians, static objects, route) → + traffic-sign object tokens → + persistent sign-state token → + learnable speed token → backbone → path / waypoints / speed heads → "+147,976 parameters (+0.4%)" → expert supervision chain (36,828 oracle trajectories → rule-supervised fine-tuning → PlanT-2-FT) → cut to a fine-tuned rollout (speed limit).
- **ASSET PATHS** `signs/no_entry.png`, `signs/speed_limit_20.png`, `converted/ft_n2_speed_limit_seg_1011196718.mp4`
- **SCIENTIFIC SOURCE** Sec. IV-C/IV-D; `third_party/plant2/PlanT/model.py` (`tok_emb`, `sign_emb`, `speed_token`, `ego_speed_classifier`, path/wp generators); count derivation in ASSET_INDEX.md #34
- **NOTES** No architecture figure exists in any repo; this one is built from the code. Rollout is from an intermediate checkpoint (footnoted).

## 12 · Main result — 2:22–2:36 (14 s)
- **VISUAL** PlanT-2 clip (no entry, violations 9) beside a fine-tuned clip (no entry, violations 0; different scene); 5.9% → 72.3% count-up, +66.4 points; group SCD bars from Table II; takeaway.
- **ASSET PATHS** `converted/pair_3_1_plant2_base.mp4`, `converted/ft_n2_no_entry_dual_T_1221647944.mp4`
- **SCIENTIFIC SOURCE** Table II, Sec. V-A
- **TODO** **[MISSING SCIENTIFIC ASSET: paired PlanT-2 vs final PlanT-2-FT rollouts on the same scene]**

## 13 · Sign-channel ablation — 2:36–2:48 (12 s) ★
- **VISUAL** Left: real fine-tuned clip labelled "sign input present"; right: placeholder box; numbers 580 paired episodes, SCD 72.8 → 15.4, Compliance 90.3 → 28.9.
- **ASSET PATHS** `converted/ft_n2_detour_right_seg_1241471060.mp4`
- **SCIENTIFIC SOURCE** Sec. V-D, Table III
- **TODO** **[MISSING SCIENTIFIC ASSET: paired rollouts with sign input present vs removed (same scene, same seed)]** — plates must remain visible in both.

## 14 · Remaining failures — 2:48–2:56 (8 s)
- **VISUAL** placeholder box + 24.7% / 3.4% / compliance 96.6% (pooled audit) / "Remaining failures are primarily navigational."
- **SCIENTIFIC SOURCE** Sec. V-B
- **TODO** **[MISSING SCIENTIFIC ASSET: PlanT-2-FT rollout that obeys the sign but does not reach the destination]**

## 15 · End frame — 2:56–2:59 (3 s)
- **VISUAL** faint real roundabout rollout behind "TrafficSignBench / Explicit rule-conditioned closed-loop evaluation / 34 signs · 29 tests · 29,000 scenarios".
- **ASSET PATHS** `converted/ft_n2_roundabout_rb_032ea693fcab.mp4`

---

### Cutting plan if the total must shrink
End frame (−1 s) → portability (−2 s) → scale (−2 s) → benchmark overview (−2 s) → failures wording (−1 s). Protected: 01, 03, 04, 05, 08, 10, 11, 12.
