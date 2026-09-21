# ASSET INDEX — ICRA video (fast audit, 2026-09-19)

Repositories audited (read-only inspection):

- **TRB** = `smirnova/traffic-rule-bench-main` (main benchmark repo, writable workspace `icra-video/` inside it)
- **FT** = `smirnova/ft_rl3` (PlanT-2 fine-tuning campaign: dumps, checkpoints, eval GIFs)
- **Z** = `zinkovich/zinkovich/traffic-rule-bench` (collaborator, **read-only**; nothing was written or executed there)
- **LOCAL** = the working copy on the laptop (`sdc_new_signs/`), which holds older eval GIFs

Every converted clip lives in `public/converted/` (GIF → MP4, ffmpeg `fps=30, scale=800:800, yuv420p`, no speed change, originals untouched).
Every figure lives in `public/figures/`, sign icons in `public/signs/`, flags in `public/flags/`.

Status legend — **current**: consistent with the current paper; **old**: old-paper asset, visual only; **unknown**: provenance/checkpoint not verified.

## A. Simulator rollouts (real closed-loop footage)

| # | Source path | Repo | Type | What it shows | Scene | Scientific meaning | Status | Reuse | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 0a | `data/runs/crosswalk/debug/2026-09-21_16-44-42/gifs/*s1356480710_plant2_default.gif` | TRB | GIF 800² | PlanT-2 reaches the destination without collision but violates `PedestrianYieldRule` once | 01 | episode JSON: DS 90.00, efficiency 295.3, smooth-frame ratio 8.0%, collision 0% | current | ✅ | converted to a 10 s MP4 with the final violating frame held, not looped |
| 0b | `icra-video/gifs/solution/*.gif` (36 files) | TRB | GIF 800² | diverse benchmark rollouts used as a 6×6 zoom-out mosaic | 02 | visual benchmark coverage | current | ✅ | all 36 converted to deterministic 8 s MP4 clips |
| 1 | `docs/static/gifs/pairs/3.1/plant2_base.gif` | TRB | GIF 640², 77 fr | PlanT-2 baseline enters a **no-entry** road; on-screen verifier ends at *Violations: 9* | 11 | confirmed (counter in frame) | current | ✅ | Docs demo pair; scene id not recorded in filename |
| 2 | `docs/static/gifs/pairs/3.1/plant2_expert.gif` | TRB | GIF | rule-compliant expert on the same map turns away, *Violations: 0* | — | confirmed | current | ✅ | expert = privileged rule-compliant planner, **not** PlanT-2-FT |
| 3 | `docs/static/gifs/pairs/3.1/idm_base.gif` | TRB | GIF 720² | IDM enters no-entry road, *Violations: 10* | 09 | confirmed | current | ✅ | |
| 4 | `docs/static/gifs/pairs/5.15.1/plant2_{base,expert}.gif` | TRB | GIF 560² | lane-direction sign: base ends *Violations: 1*, expert *0* | 08, 09 | confirmed | current | ✅ | used for the COMPLIANT / VIOLATION checker HUD |
| 5 | `docs/static/gifs/pairs/5.7.1/{carl,plant2}_{base,expert}.gif` | TRB | GIF 560² | one-way sign: CaRL base violates (1), experts 0 | 02, 09 | confirmed | current | ✅ | |
| 6 | `ft_rl3/gifs_ft/n2_eq_3e5_e8/<sign>/gifs/*.gif` (58 files, 2 per scenario type) | FT | GIF 800² | fine-tuned PlanT-2 rollouts, **intermediate checkpoint `n2_eq_3e5` epoch 8** | 02, 04, 10, 11, 12, 14 | rollout real; **not the paper's final PlanT-2-FT checkpoint** | unknown ckpt | ⚠️ label as "intermediate checkpoint" | yield clips show the gated main-road convoy (`is_ego_in_yield_zone` HUD) |
| 7 | `ft_rl3/gifs_best/augA_e20/<sign>/gifs/*.gif` (18 files, routing signs) | FT | GIF 800² | fine-tuned rollouts on dual-path maps, checkpoint `augA` epoch 20 | 05 | as above | unknown ckpt | ⚠️ | `dual_T_1303406452_l_r_b5c03734` matches the map used in scenes 03/05 |
| 8 | `LOCAL gif_eval/dual_T_1303406452_l_r_b5c03734_v0_s1930004957_plant2_default.gif` | LOCAL | GIF 800² | PlanT-2 adapter rollout on the same dual-path map (2026-09-12 eval, checkpoint not recorded) | 03 | rollout real; policy label unknown | unknown ckpt | ⚠️ neutral label "closed-loop rollout" | |
| 9 | `reports/plant2_ft_v7/gifs_crosswalk/expert_idm_rule/gifs/seg_1103897132_…_idm_rule_default.gif` | TRB | GIF 800² | **rule-compliant IDM expert** at a crosswalk with timed pedestrians | 04 | confirmed | current | ✅ | 36 more crosswalk GIFs (experts + FT variants) in the same folder |
| 10 | `LOCAL gifs/sumo_3.24_258301_v0_s4035757764_plant2_default.gif` | LOCAL | GIF 800² | PlanT-2 on a 20 km/h limit, verifier counter 0→2 | 02 | confirmed | current | ✅ | |
| 11 | `ft_rl3/rec32/gifs/{expert,model}/junc_1116455525*.gif` | FT | GIF 800² | blocked-road junction, expert vs model | — | not used | unknown | – | |
| 12 | `third_party/plant2/Bench2Drive/assets/overview.mp4`, `third_party/plant2/assets/*.gif` | TRB/Z | MP4/GIF | upstream CARLA demos | — | **not our data** | – | ❌ | do not use |

**Not found (would most improve the video):** paired PlanT-2 vs PlanT-2-FT on the *same* scene from the final checkpoint; sign-channel-ablation pairs (input present vs removed); a PlanT-2-FT failure that obeys the sign but misses the destination; a random-placement vs targeted comparison.

## B. Maps and scenes (real geometry)

| # | Source | Repo | Type | What | Scene | Status | Notes |
|---|---|---|---|---|---|---|---|
| 13 | `traffic_bench/scene_collection/maps/nets/moscow.net.xml` (145 MB) | TRB | SUMO net | the full Moscow road network derived from OSM | 03, 06 | current | rendered by our `icra-video/tools/render_overview.py` → `generated/moscow_crops_overview.png` (4000×4502) + `.json` extents |
| 14 | `traffic_bench/scene_collection/maps/index/{junctions,segments}.jsonl` | TRB | JSONL | crop centres: 6,457 junctions, 13,056 segments (matches paper) | 03, 06 | current | `dual_path_candidates.jsonl` has no `center_xy` (0 drawn) |
| 15 | `data/scenes/direction_right/dual_T_1303406452_l_r_b5c03734/{map.net.xml,meta.json,custom_cropped.png}` | TRB | scene | dual-path T-junction; meta has `crop_bbox_xy`, baseline (95 m, prohibited) and compliant (313 m) edge paths | 03, 05 | current | crop rendered with the project renderer `traffic_bench.scene_collection.preview.render_network` via `icra-video/tools/render_scene_map.py` → `generated/map_dual_T_1303406452*.png` |
| 16 | `data/scenes/no_entry/dual_T_1146724846_l_s_0c2c7fff/` | TRB | scene | second dual-path example (rendered, not used) | — | current | |
| 17 | `traffic_bench/scene_collection/maps/previews/junctions_overview.png` | TRB | PNG | matplotlib overview of enumerated T/X/O junctions | — | current | has axes/title; replaced by #13 |
| 18 | `Z/tools/render_map.py`, `TRB/traffic_bench/scene_collection/preview.py` | Z/TRB | code | map renderer (roads, junction polygons, zebra, dual-path routes) | 03, 05 | – | executed only from TRB with output into `icra-video/generated/` |

## C. Paper figures and graphics

| # | Source | Repo | Type | What | Scene | Status | Notes |
|---|---|---|---|---|---|---|---|
| 19 | `Z/paper/imgs/semantics/1.pdf` | Z | PDF | source of current Fig. 1 (four group cards with verifier examples) | 02 | current | rasterised to `figures/taxonomy_fig1.png`; scene 02 rebuilds the cards from icons + clips |
| 20 | `TRB/traffic_bench/signs/icons/*.png` (64) | TRB | PNG | project sign icons | 02, 04, 05, 10 | current | copied to `public/signs/` |
| 21 | `Z/paper/imgs/signs/*.png` (56), `signs.pdf` | Z | PNG/PDF | sign grid for the paper | — | current | alternative icon source |
| 22 | `Z/paper/imgs/flags/*.png` | Z | PNG | flags used in Table I | 07 | current | copied to `public/flags/` |
| 23 | `Z/paper/imgs/_old/sign_countries.pdf` | Z | PDF | **old paper Fig. 4**: Yield + Turn-left signs in 7 countries | 07 | **old (visual only)** | its bracket labels are cropped out; all numbers on screen come from current Table I (DE 91, FR 84, IT 94, TR 100, UK 97, CN 91, mean 92%) |
| 24 | `Z/paper/imgs/traj.pdf` | Z | PDF | Fig. 3 oracle-expert composition | — | current | `figures/oracle_composition_fig3.png`, not used (not in the target story) |
| 25 | `Z/scripts/scene_analysis/figures/geographic_diversity.pdf` | Z | PDF | lat/lon scatter of crops | — | current | `figures/geographic_diversity.png`, not used (replaced by #13) |
| 26 | `Z/paper/imgs/planner/{1..4}.png` | Z | PNG | 4-frame rollout sequence around a no-entry sign (old paper) | — | old | not used |
| 27 | `Z/paper/imgs/rules/*.png`, `TRB/docs/static/images/rules/*.png` | Z/TRB | PNG | per-sign rule illustrations (isometric cartoons) | — | current | could illustrate scene 04; not used in MVP |
| 28 | `TRB/docs/static/images/teaser*.png` | TRB | PNG | old TrafficRuleBench teaser (45 signs, 20,600 scenes) | — | **old, obsolete numbers** | ❌ do not use |
| 29 | `Z/paper/imgs/{correlation,metric_scatter_grid,metrics_CI,per_scenario_sr_dest_forest}.pdf/png` | Z | PDF/PNG | current result plots | — | current | not needed for the MVP story |
| 30 | `FT/reports/*/curves.png` | FT | PNG | training curves | — | – | not used |

## D. Architecture / code (for scene 10 grounding)

| # | Source | Repo | What was verified |
|---|---|---|---|
| 31 | `TRB/third_party/plant2/PlanT/model.py` (md5 `50ee6f6f…`, identical to the local `trb-stop` copy) | TRB | `tok_emb`: one `Linear(6→n_embd)` per object class incl. **one per PDD sign code** (33 sign classes) → "sign object tokens with learned class projections"; `sign_emb = Embedding(NUM_SIGN_CLASSES=49)` over a `code@value` vocabulary (e.g. `3.24@20`) → "sign-state token stores active class and posted value"; `speed_token` learnable parameter appended to the sequence, read by `ego_speed_classifier(n_embd→8 bins)` → "learnable speed token feeds a discrete ego-speed head"; `path_generator` (20 pts) + `wp_generator` (8 pts) → path and waypoint heads |
| 32 | `TRB/third_party/plant2/PlanT/util/sign_id.py` | TRB | `SIGN_ID_VOCAB` = 21 legacy + 15 value-qualified + 12 added codes = 48 (+1 unknown) |
| 33 | `TRB/third_party/plant2/PlanT/config/model/PlanT.yaml` | TRB | `bins_speed: 8`, `path+wps` representation, `input_ego_speed: False` |
| 34 | parameter count | derived | 33×(6·512+512) + 49·512 + 512 + (512·8+8) = **147,976** ⇔ hidden size 512. Matches the paper exactly; hidden size itself is inherited from the pretrained HF config (not in the yaml) |
| 35 | `Z/scripts/plant2_ft_pipeline/tools/viz_train_global_gif.py`, `TRB/third_party/plant2/PlanT/util/viz_batch.py` | Z/TRB | token/BEV visualisers — not needed for the MVP |
| 36 | architecture figures | all | **none found** (no SVG/PDF/PNG of the PlanT-2-FT architecture in any repo) → scene 10 is a hand-built animated figure |
