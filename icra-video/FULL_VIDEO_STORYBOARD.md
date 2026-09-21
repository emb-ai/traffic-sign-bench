# FULL VIDEO STORYBOARD — TrafficSignBench ICRA video (MVP, 2026-09-19)

Format 1920×1080, 30 fps, 177 s total (limit 180 s). Composition `ICRA-Full`.
Edit points: text → `src/config/content.ts`, durations/reveals → `src/config/timing.ts`, look → `src/config/style.ts`, files → `src/config/assets.ts`.
Scene components: `src/scenes/S01_…S14_*.tsx`. Assets provenance: `ASSET_INDEX.md`. Narration: `VOICEOVER.md`.
Every clip is a real project rollout; presentation layer only adds text, boxes, marks, arrows, counters.

---

## 01 · Why explicit rule compliance? — 0:00–0:11 (11 s)
- **MESSAGE** A planner can look successful under conventional outcomes while violating a specific rule.
- **VISUAL** Real rollout starts on frame 0 (no title card): PlanT-2 baseline entering a "no entry" road; verifier counter climbs to 9. Right: sign icon, "Looks fine. Breaks the rule.", three check rows, main text.
- **ASSET PATHS** `public/converted/pair_3_1_plant2_base.mp4` (TRB docs pair 3.1), `public/signs/no_entry.png`
- **ON-SCREEN TEXT** Destination —, Collision-free —, Rule compliant ✕ (only the last is supported by the clip's own counter); "Aggregate driving metrics do not explicitly measure target-rule compliance."
- **VOICEOVER** see VOICEOVER.md #01
- **TIMING** kicker 0.4 s, headline 1.0 s, checks 2.0 s, ✕ at 5.0 s, main text 7.0 s
- **SCIENTIFIC SOURCE** Sec. I; Fig. 1 (sign 3.1); clip HUD
- **TODO** replace "—" marks with ✓ once a rollout with known destination/collision outcome (episode JSON) is chosen
- **NOTES** clip is 3 s and loops

## 02 · What is TrafficSignBench? — 0:11–0:24 (13 s)
- **MESSAGE** Sign-associated rules become explicit closed-loop tests.
- **VISUAL** Four Fig.-1-style cards (Priority / Speed / Obstacles / Routing) with project sign icons and one real clip each; bottom: 34 · 29 · 29,000.
- **ASSET PATHS** `converted/ft_n2_yield_junc_1015545863.mp4`, `converted/plant2_speed_3_24_seg_258301.mp4`, `converted/ft_n2_detour_right_seg_1241471060.mp4`, `converted/pair_5_7_1_plant2_expert.mp4`, `public/signs/*`
- **ON-SCREEN TEXT** "TrafficSignBench — sign-associated rules → explicit closed-loop tests"; per card "8 signs · 6 scenarios" etc.; 34 traffic signs / 29 functional scenario types / 29,000 closed-loop scenarios
- **TIMING** cards 1.0 s + 0.35 s steps, numbers 5.5 s
- **SCIENTIFIC SOURCE** Fig. 1, Sec. III-B, III-D
- **NOTES** Not all 34 signs shown. Card counts (8/7/8/11 signs; 6/4/8/11 scenarios) from Fig. 1.

## 03 · Real maps → executable rule tests — 0:24–0:44 (20 s) ★
- **MESSAGE** Grounded in real road geometry, one continuous process.
- **VISUAL** Stage (left): real Moscow SUMO network with all crop centres → blue highlight of the scene's crop bbox (from meta.json) → zoom → project-rendered crop → simulator scene preview → real closed-loop rollout **on the same crop** `dual_T_1303406452`. Right: headline, 5-step list, 26,020 counter, family breakdown.
- **ASSET PATHS** `figures/moscow_crops_overview.png` (+`.json` extents), `figures/map_dual_T_1303406452_plain.png`, `figures/scene_preview_dual_T_1303406452.png`, `converted/eval0912_direction_right_dual_T_1303406452.mp4`
- **ON-SCREEN TEXT** "Real road geometry → executable rule test"; 26,020 real-map crops; Junctions 6,457 · Dual-path 6,507 · Corridors 13,056
- **TIMING** highlight 2 s, zoom 3–7 s, crop 6.5 s, preview 10 s, rollout 13 s
- **SCIENTIFIC SOURCE** Sec. III-C; `scene_collection/maps/index/*.jsonl`; scene `meta.json`
- **TODO** The zoom pixel-aligns the bbox, but the crossfade to the vector crop is not pixel-registered (different renderer margins). Rollout policy label is neutral ("closed-loop rollout") because the checkpoint of that eval GIF is not recorded.

## 04 · Rule-targeted generation — 0:44–1:03 (19 s) ★
- **MESSAGE** Random placement may never activate the rule; interactions are rule-critical.
- **VISUAL** Yield rollout (gated convoy on the main road, HUD shows `is_ego_in_yield_zone`), three numbered steps; then crosswalk rollout of the rule-compliant IDM expert with pedestrians.
- **ASSET PATHS** `converted/ft_n2_yield_junc_1057163165.mp4` (trim 4 s), `converted/expert_idm_rule_crosswalk_seg_1103897132.mp4`, `signs/yield.png`, `signs/crosswalk.png`
- **ON-SCREEN TEXT** "Rule-targeted interactions make the rule matter."; steps; footnote "* intermediate fine-tuning checkpoint"
- **TIMING** crosswalk from 11 s
- **SCIENTIFIC SOURCE** Sec. III-D
- **NOTES** No fake "random" comparison is shown. **[MISSING SCIENTIFIC ASSET: real inactive/random-placement rollout for contrast]**

## 05 · Routing decision — 1:03–1:17 (14 s) ★
- **MESSAGE** The shortest route violates the restriction; compliance requires replanning.
- **VISUAL** Real dual-path crop; project-rendered route overlay from meta.json (red baseline 95 m prohibited / green compliant 313 m); then fine-tuned rollout on that map.
- **ASSET PATHS** `figures/map_dual_T_1303406452_plain.png`, `figures/map_dual_T_1303406452_routes.png`, `converted/ft_augA_direction_right_dual_T_1303406452.mp4`, `signs/direction_right.png`
- **ON-SCREEN TEXT** sign 4.1.2; route lengths; headline; footnote
- **SCIENTIFIC SOURCE** Sec. III-C/III-D; `meta.json` `dual_path.baseline_length_m = 94.93`, `compliant_length_m = 313.26`
- **NOTES** Route geometry is from project data, not drawn by hand.

## 06 · Scale + split — 1:17–1:28 (11 s)
- **VISUAL** 29 × 100 × 10 = 29,000; five variation chips; split chain (Unique OSM IDs → 80/20 → sign assignment); small real overview of crop centres.
- **ASSET PATHS** `figures/moscow_crops_overview.png`
- **ON-SCREEN TEXT** "Split before sign assignment", 23,200 train · 5,800 test, "sampled from nuPlan-calibrated distributions"
- **SCIENTIFIC SOURCE** Sec. III-C (split), III-D (variants), Fig. 2

## 07 · Semantic portability — 1:28–1:37 (9 s)
- **VISUAL** Old-paper Fig. 4 sign graphics (Yield / Turn-left in 7 jurisdictions; bracket labels cropped) + flag tiles with current Table I values.
- **ASSET PATHS** `figures/sign_countries_oldpaper.png` (old paper, visual only), `flags/*.png`
- **ON-SCREEN TEXT** "Different appearance. Shared rule semantics."; DE 91 · FR 84 · IT 94 · TR 100 | UK 97 · CN 91; "92% average semantic overlap across analysed Vienna-Convention signatories"
- **SCIENTIFIC SOURCE** Sec. III-A, Table I (current). Wording deliberately avoids "generalizes across countries".

## 08 · Planner interface + checker + SCD — 1:37–1:52 (15 s)
- **VISUAL** Two real clips (expert: Violations 0 → COMPLIANT ✓; PlanT-2: Violations 1 → VIOLATION ✕, badges appear at 4.5 s, states taken from the clips' own counters); chain diagram; then SCD truth table (✓✓→✓, ✓✕→✕, ✕✓→✕).
- **ASSET PATHS** `converted/pair_5_15_1_plant2_expert.mp4`, `converted/pair_5_15_1_plant2_base.mp4`
- **SCIENTIFIC SOURCE** Sec. IV-A (SCD), Sec. III (verifiers)

## 09 · Existing planner gap — 1:52–2:01 (9 s)
- **VISUAL** IDM / CaRL / PlanT-2 baseline clips; 2.9–9.0%; small bars IDM 7.2, PPO 3.2, CaRL 2.9, PlanT-2 5.9; "Can the gap be closed?"
- **ASSET PATHS** `converted/pair_3_1_idm_base.mp4`, `converted/pair_5_7_1_carl_base.mp4`, `converted/pair_5_15_1_plant2_base.mp4`
- **SCIENTIFIC SOURCE** Table II, Sec. V-A

## 10 · PlanT-2 → PlanT-2-FT architecture — 2:01–2:19 (18 s) ★
- **VISUAL** Animated figure: base object tokens (vehicles, pedestrians, static objects, route) → + traffic-sign object tokens → + persistent sign-state token → + learnable speed token → backbone → path / waypoints / speed heads → "+147,976 parameters (+0.4%)" → expert supervision chain (36,828 oracle trajectories → rule-supervised fine-tuning → PlanT-2-FT) → cut to a fine-tuned rollout (speed limit).
- **ASSET PATHS** `signs/no_entry.png`, `signs/speed_limit_20.png`, `converted/ft_n2_speed_limit_seg_1011196718.mp4`
- **SCIENTIFIC SOURCE** Sec. IV-C/IV-D; `third_party/plant2/PlanT/model.py` (`tok_emb`, `sign_emb`, `speed_token`, `ego_speed_classifier`, path/wp generators); count derivation in ASSET_INDEX.md #34
- **NOTES** No architecture figure exists in any repo; this one is built from the code. Rollout is from an intermediate checkpoint (footnoted).

## 11 · Main result — 2:19–2:33 (14 s)
- **VISUAL** PlanT-2 clip (no entry, violations 9) beside a fine-tuned clip (no entry, violations 0; different scene); 5.9% → 72.3% count-up, +66.4 points; group SCD bars from Table II; takeaway.
- **ASSET PATHS** `converted/pair_3_1_plant2_base.mp4`, `converted/ft_n2_no_entry_dual_T_1221647944.mp4`
- **SCIENTIFIC SOURCE** Table II, Sec. V-A
- **TODO** **[MISSING SCIENTIFIC ASSET: paired PlanT-2 vs final PlanT-2-FT rollouts on the same scene]**

## 12 · Sign-channel ablation — 2:33–2:46 (13 s) ★
- **VISUAL** Left: real fine-tuned clip labelled "sign input present"; right: placeholder box; numbers 580 paired episodes, SCD 72.8 → 15.4, Compliance 90.3 → 28.9.
- **ASSET PATHS** `converted/ft_n2_detour_right_seg_1241471060.mp4`
- **SCIENTIFIC SOURCE** Sec. V-D, Table III
- **TODO** **[MISSING SCIENTIFIC ASSET: paired rollouts with sign input present vs removed (same scene, same seed)]** — plates must remain visible in both.

## 13 · Remaining failures — 2:46–2:54 (8 s)
- **VISUAL** placeholder box + 24.7% / 3.4% / compliance 96.6% (pooled audit) / "Remaining failures are primarily navigational."
- **SCIENTIFIC SOURCE** Sec. V-B
- **TODO** **[MISSING SCIENTIFIC ASSET: PlanT-2-FT rollout that obeys the sign but does not reach the destination]**

## 14 · End frame — 2:54–2:57 (3 s)
- **VISUAL** faint real roundabout rollout behind "TrafficSignBench / Explicit rule-conditioned closed-loop evaluation / 34 signs · 29 tests · 29,000 scenarios".
- **ASSET PATHS** `converted/ft_n2_roundabout_rb_032ea693fcab.mp4`

---

### Cutting plan if the total must shrink
End frame (−1 s) → portability (−2 s) → scale (−2 s) → benchmark overview (−2 s) → failures wording (−1 s). Protected: 01, 03, 04, 05, 08, 10, 11, 12.
