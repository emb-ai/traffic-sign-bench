<p align="center">
  <img src="docs/static/images/signs/2.1.png" width="42" alt="Main road">
  &nbsp;
  <img src="docs/static/images/signs/2.4.png" width="42" alt="Yield">
  &nbsp;
  <img src="docs/static/images/signs/2.5.png" width="42" alt="Stop">
  &nbsp;
  <img src="docs/static/images/signs/3.1.png" width="42" alt="No entry">
  &nbsp;
  <img src="docs/static/images/signs/4.2.1.png" width="42" alt="Pass right">
  &nbsp;
  <img src="docs/static/images/signs/5.7.1.png" width="42" alt="One-way">
  &nbsp;
  <img src="docs/static/images/signs/5.19.png" width="42" alt="Crosswalk">
</p>

<h1 align="center">TrafficSignBench</h1>

<p align="center">
  <strong>Does your driving planner obey the sign that matters?</strong><br>
  A rule-centric, closed-loop benchmark built on real road geometry.
</p>

<p align="center">
  <a href="https://emb-ai.github.io/traffic-sign-bench/"><img src="https://img.shields.io/badge/Project_website-0F172A?style=for-the-badge" alt="Project website"></a>
  <a href="https://huggingface.co/datasets/emb-ai/traffic-sign-bench"><img src="https://img.shields.io/badge/Dataset-FFD21E?style=for-the-badge&logo=huggingface&logoColor=000" alt="Dataset on Hugging Face"></a>
  <a href="https://huggingface.co/emb-ai/traffic-rule-bench-models"><img src="https://img.shields.io/badge/Models-FFD21E?style=for-the-badge&logo=huggingface&logoColor=000" alt="Models on Hugging Face"></a>
  <a href="https://github.com/emb-ai/traffic-sign-bench"><img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github" alt="GitHub repository"></a>
</p>

<p align="center">
  <strong>34 signs</strong> · <strong>29 test types</strong> · <strong>29,000 closed-loop scenarios</strong> · <strong>17 planner configurations</strong>
</p>

---

Conventional scores can stay high while a planner ignores a yield sign, enters a prohibited road, or drives against traffic. TrafficSignBench turns each sign into an explicit test with a targeted scenario and an automatic rule checker.

<table>
  <tr>
    <th width="16%">Rule</th>
    <th width="42%">Base planner</th>
    <th width="42%">Rule-compliant twin</th>
  </tr>
  <tr>
    <td align="center">
      <img src="docs/static/images/signs/5.7.1.png" width="38" alt="One-way sign"><br>
      <strong>One-way</strong><br>
      <sub>5.7.1 · CaRL</sub>
    </td>
    <td align="center"><img src="docs/static/gifs/pairs/5.7.1/carl_base.gif" width="250" alt="CaRL violates the one-way rule"></td>
    <td align="center"><img src="docs/static/gifs/pairs/5.7.1/carl_expert.gif" width="250" alt="Rule-compliant CaRL respects the one-way rule"></td>
  </tr>
  <tr>
    <td align="center">
      <img src="docs/static/images/signs/3.1.png" width="38" alt="No-entry sign"><br>
      <strong>No entry</strong><br>
      <sub>3.1 · IDM</sub>
    </td>
    <td align="center"><img src="docs/static/gifs/pairs/3.1/idm_base.gif" width="250" alt="IDM enters a prohibited road"></td>
    <td align="center"><img src="docs/static/gifs/pairs/3.1/idm_expert.gif" width="250" alt="Rule-compliant IDM avoids a prohibited road"></td>
  </tr>
  <tr>
    <td align="center">
      <img src="docs/static/images/signs/5.15.1.png" width="38" alt="Lane-directions sign"><br>
      <strong>Lane directions</strong><br>
      <sub>5.15.1 · IDM</sub>
    </td>
    <td align="center"><img src="docs/static/gifs/pairs/5.15.1/idm_base.gif" width="250" alt="IDM ignores lane directions"></td>
    <td align="center"><img src="docs/static/gifs/pairs/5.15.1/idm_expert.gif" width="250" alt="Rule-compliant IDM follows lane directions"></td>
  </tr>
</table>

<p align="center">
  <a href="https://emb-ai.github.io/traffic-sign-bench/"><strong>Explore more rollouts, figures, and results on the project website →</strong></a>
</p>

> **Headline result:** rule-supervised PlanT-2-FT raises sign compliance and destination success from **5.9% to 72.3%** (**+66.4 pp**).

## What is included

- **Executable rule tests** for priority, speed, obstacle, and routing signs.
- **Real-map SUMO scenes** with controlled traffic, pedestrians, routes, and ego parameters.
- **Closed-loop evaluation** with target-rule compliance, progress, safety, and comfort metrics.
- **Reference planners** spanning IDM, PPO, CaRL, and PlanT-2, with rule-aware variants.
- **Oracle collection and selection** for rule-supervised fine-tuning.

```
real-map scenes → manifest → closed-loop rollouts → metrics
                       └── rule experts → oracle selection → fine-tuning
```

## Quick start

TrafficSignBench is tested on Linux with Python 3.10. The commands below run a one-scenario IDM smoke test; neural planners require the checkpoints described later.

### 1. Install

```bash
git clone --recurse-submodules https://github.com/emb-ai/traffic-sign-bench.git
cd traffic-sign-bench

conda create -n trafficsignbench python=3.10 -y
conda activate trafficsignbench

pip install -e third_party/metadrive
pip install -e .
pip install eclipse-sumo sumolib hydra-core scipy pandas \
  stable-baselines3 pyproj "geopandas<1.0" timm huggingface_hub
```

If the repository was cloned without submodules, run `git submodule update --init --recursive`.

### 2. Download scenes

For the quick start, download only the yield-sign scenes:

```bash
hf download emb-ai/traffic-sign-bench \
  --repo-type dataset \
  --include "scenes/yield/**" \
  --local-dir data
```

Remove `--include "scenes/yield/**"` to download the complete benchmark. Files are placed under `data/scenes/<sign>/`.

### 3. Run one test

```bash
python -m traffic_bench.eval manifest \
  sign=yield scenario.max_total=1

python -m traffic_bench.eval run \
  policy=idm sign=yield jobs=1 gif.enabled=true
```

Results are written to `data/runs/yield/debug/`, including episode records, metrics, and a GIF.

## Evaluation

The CLI follows three steps:

```bash
# Build a stable test manifest.
python -m traffic_bench.eval manifest sign=yield paths.split=test

# Evaluate one or several planners.
python -m traffic_bench.eval run \
  policies=[idm,idm_rule,plant2_ft] sign=yield

# Combine completed runs across all signs.
python -m traffic_bench.eval metrics combine sign=all
```

Use `sign=all` for the complete benchmark and `policies=all` for every registered planner. Nested sign IDs use paths such as `direction/right` and `detour/left`.

The primary metric, `target_compliant_event`, records whether the ego vehicle obeyed the active sign inside its evaluation zone. Each episode also reports destination success, route completion, all detected violations, and nuPlan-style comfort.

For split semantics, parallel multi-GPU evaluation, configuration overrides, and the complete sign registry, see the [evaluation guide](traffic_bench/eval/README.md).

## Planners and checkpoints

Checkpoint-free planners:

- `idm` — sign-agnostic CurveAwareIDM baseline.
- `idm_rule` — IDM with explicit rule handling.
- `ppo_lidar`, `ppo_rule` — PPO baseline and rule-aware variants.

Neural planners:

- `carl`, `carl_rule` — CaRL base and rule-aware variants.
- `plant2`, `plant2_rule`, `plant2_ft` — PlanT-2 variants.

Download the published weights:

```bash
hf download emb-ai/traffic-rule-bench-models --local-dir checkpoints
```

The default paths are `checkpoints/carl/nuplan_51479_1B/model_best.pth`, `checkpoints/plant2_pretrain/epoch=029_final_3.ckpt`, and `checkpoints/plant2_finetuned/`.

PlanT-2 uses its own environment; follow the setup notes in [emb-ai/plant2](https://github.com/emb-ai/plant2).

## Oracle data and fine-tuning

Collect rule-expert rollouts:

```bash
SIGN=yield SMOKE=1 ./traffic_bench/oracle/collect/collect.sh
```

Then select one oracle trajectory per scene with the [oracle pipeline](traffic_bench/oracle/collect/README.md) and fine-tune PlanT-2 using [`finetune/`](finetune/README.md).

To generate new scenes from OpenStreetMap instead of using the release, see the [scene-collection pipeline](traffic_bench/scene_collection/README.md).

## Repository map

```text
traffic_bench/
├── signs/              # sign objects and rule checkers
├── envs/               # SUMO environment and traffic actors
├── agents/             # planners and model adapters
├── eval/               # manifest → rollout → metrics
├── oracle/             # expert collection and selection
└── scene_collection/   # OSM harvesting and scene generation
data/                   # downloaded scenes and generated runs
docs/                   # GitHub Pages website and visual assets
finetune/               # PlanT-2 fine-tuning
third_party/            # MetaDrive, PlanT-2, and CaRL
```

More documentation:

- [Project website](https://emb-ai.github.io/traffic-sign-bench/) — interactive rollouts, benchmark overview, figures, and extended results.
- [Evaluation](traffic_bench/eval/README.md) — CLI, signs, splits, parallel runs, and metrics.
- [Oracle pipeline](traffic_bench/oracle/README.md) — expert rollouts and trajectory selection.
- [Scene collection](traffic_bench/scene_collection/README.md) — real-map harvesting and benchmark packaging.

## Citation

If TrafficSignBench is useful in your research, please cite:

```bibtex
@misc{trafficsignbench2026,
  title        = {TrafficSignBench: Evaluating Traffic Rule Compliance in Autonomous Driving},
  author       = {{EMB AI}},
  year         = {2026},
  howpublished = {\url{https://github.com/emb-ai/traffic-sign-bench}},
  note         = {Code, scenes, and models}
}
```
