---
license: cc-by-4.0
library_name: pytorch
tags:
  - autonomous-driving
  - traffic-signs
  - motion-planning
  - closed-loop-evaluation
  - metadrive
pretty_name: TrafficSignBench Models
---

# TrafficSignBench Models

Planner checkpoints for **[TrafficSignBench](https://emb-ai.github.io/traffic-sign-bench/)** — closed-loop evaluation of traffic-sign compliance.

Drop these weights into the benchmark repo as `checkpoints/` and the eval CLI picks them up automatically.

| Resource | Link |
| --- | --- |
| Code & eval | [github.com/emb-ai/traffic-sign-bench](https://github.com/emb-ai/traffic-sign-bench) |
| Scenes | [emb-ai/traffic-sign-bench](https://huggingface.co/datasets/emb-ai/traffic-sign-bench) |
| Project page | [emb-ai.github.io/traffic-sign-bench](https://emb-ai.github.io/traffic-sign-bench/) |

---

## What's inside

| Path | Planner | Role | Size |
| --- | --- | --- | ---: |
| `carl/nuplan_51479_1B/model_best.pth` | CaRL | nuPlan-trained baseline | 7.6 MB |
| `plant2_pretrain/epoch=029_final_3.ckpt` | PlanT-2 | pretrained baseline | 426 MB |
| `plant2_finetuned/plant2_supervised_2nd_final.pt` | PlanT-2-FT | rule-supervised fine-tune | 142 MB |

**Total ≈ 576 MB.** IDM and PPO ship with the code — no download needed.

---

## Quick start

From a checkout of [traffic-sign-bench](https://github.com/emb-ai/traffic-sign-bench):

```bash
# All checkpoints → ./checkpoints  (paths match eval defaults)
hf download emb-ai/traffic-sign-bench-models --local-dir checkpoints

# Or pull only what you need
hf download emb-ai/traffic-sign-bench-models \
  --include "carl/**" \
  --local-dir checkpoints
```

Then evaluate (scenes from the [dataset](https://huggingface.co/datasets/emb-ai/traffic-sign-bench) must already be under `data/scenes/`):

```bash
python -m traffic_bench.eval manifest sign=yield paths.split=test
python -m traffic_bench.eval run policy=carl sign=yield
python -m traffic_bench.eval run policy=plant2 sign=yield
python -m traffic_bench.eval run policy=plant2_ft sign=yield
```

Override a weight explicitly with `model_path=/path/to/file`.

---

## Layout

```text
checkpoints/                          ← --local-dir target
├── carl/
│   └── nuplan_51479_1B/
│       └── model_best.pth            ← policy=carl, carl_rule
├── plant2_pretrain/
│   └── epoch=029_final_3.ckpt        ← policy=plant2, plant2_rule
└── plant2_finetuned/
    └── plant2_supervised_2nd_final.pt ← policy=plant2_ft
```

Keep this tree under the **repo root**. Renaming folders breaks the defaults in `traffic_bench/eval/engine/sim/checkpoints.py`.

---

## Policy → checkpoint

| `policy=` | Planner | Sign access | Uses |
| --- | --- | --- | --- |
| `carl` | CaRL | none | `carl/.../model_best.pth` |
| `carl_rule` | CaRL + rule overlay | privileged | same file |
| `plant2` | PlanT-2 | none | `plant2_pretrain/...ckpt` |
| `plant2_rule` | PlanT-2 + rule overlay | privileged | same file |
| `plant2_ft` | PlanT-2-FT | learned from signs | newest `*.pt` / `*.ckpt` / `*.pth` in `plant2_finetuned/` |

`*_rule` planners read the active rule directly — useful as oracle upper bounds, not as fair baselines.

---

## Held-out results

Test split, 5 800 episodes. Conventional metrics are episode-weighted; **SCD** (Sign-Compliant Destination) is macro-averaged over scenario types.

| Planner | Driving Score ↑ | Destination ↑ | Collision ↓ | SCD ↑ |
| --- | ---: | ---: | ---: | ---: |
| IDM | 35.7 | 66.4% | 21.0% | 7.2% |
| PPO | 35.6 | 67.9% | 27.5% | 3.2% |
| CaRL | 39.6 | 73.7% | 21.0% | 2.9% |
| PlanT-2 | 28.6 | 56.1% | 43.3% | 5.9% |
| **PlanT-2-FT** | **74.2** | **74.8%** | **12.0%** | **72.3%** |

Rule-supervised fine-tuning lifts PlanT-2 SCD from **5.9% → 72.3%** without changing the backbone.

---

## Notes

- Weights are **PyTorch** checkpoints for TrafficSignBench eval, not standalone inference packages.
- `plant2_ft` resolves the **newest** weight file in `plant2_finetuned/` — put only the intended run there, or pass `model_path=`.
- CaRL originates from [autonomousvision/CaRL](https://github.com/autonomousvision/CaRL) (nuPlan). PlanT-2 from [emb-ai/plant2](https://github.com/emb-ai/plant2). PlanT-2-FT is fine-tuned on TrafficSignBench expert rollouts.
- Full install, multi-GPU eval, and sign registry: see the [benchmark README](https://github.com/emb-ai/traffic-sign-bench).

---

## License

Released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Please credit the original planner authors when redistributing CaRL or PlanT-2 derivatives.

---

## Citation

```bibtex
@misc{trafficsignbench2026,
  title     = {TrafficSignBench: Evaluating Traffic Rule Compliance
               in Autonomous Driving},
  year      = {2026},
  publisher = {GitHub},
  url       = {https://github.com/emb-ai/traffic-sign-bench}
}
```
