"""Contact sheet of candidate scenes for the fine-tuning section (run locally, review only).

Inputs: generated/finetune/expert_scene_dirR.json (current scene) and generated/finetune/cands/c*_<sign>.json,
both written by extract_expert_scene.py from the real oracle collection (8 expert replays + real pick record).
Output: renders/scene_candidates/contact_sheet.png + one PNG per scene.

Line styles encode the REAL outcome: dashed = target-sign violation, dotted = destination not reached
(off-road / crash / no arrival), thick with dark casing = selected (real top-2), thin solid = successful but not selected.
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "renders/scene_candidates"
OUT.mkdir(parents=True, exist_ok=True)

NAMES = {"idm_rule/default": "IDMe", "idm_rule/s1": "IDMe-s1", "idm_rule/s2": "IDMe-s2", "idm_rule/s3": "IDMe-s3",
         "idm_rule/s4": "IDMe-s4", "ppo_rule/default": "PPOe", "carl_rule/default": "CaRLe",
         "plant2_rule/default": "PlanT-2e"}
COLORS = {"idm_rule/default": "#4C72B0", "idm_rule/s1": "#64B5CD", "idm_rule/s2": "#8172B3", "idm_rule/s3": "#937860",
          "idm_rule/s4": "#C9B458", "ppo_rule/default": "#55A868", "carl_rule/default": "#DD8452",
          "plant2_rule/default": "#D884BE"}

import os
import sys
# usage: contact_sheet_candidates.py [cands_dir] [ids,comma,separated] [out_name]
CAND_DIR = ROOT / "generated/finetune" / (sys.argv[1] if len(sys.argv) > 1 else "cands")
IDS = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
OUT_NAME = sys.argv[3] if len(sys.argv) > 3 else "contact_sheet.png"
scenes = [("c0 · CURRENT · direction_right", ROOT / "generated/finetune/expert_scene_dirR.json")]
for p in sorted(CAND_DIR.glob("*_*.json")):
    idx, sign = p.stem.split("_", 1)
    if IDS and idx not in IDS:
        continue
    scenes.append((f"{idx} · {sign}", p))


def status(e):
    if any(e["violations"].values()):
        return "rule"
    if e["crashed"]:
        return "crash"
    if e["out_of_road"]:
        return "off-road"
    if not e["arrived_dest"]:
        return "no arrival"
    return "ok"


def draw(ax, d, title):
    ex = d["experts"]
    xs = [p[0] for e in ex for p in e["track"][1:]]
    ys = [p[1] for e in ex for p in e["track"][1:]]
    pad = 12
    x0, x1, y0, y1 = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    half = max(x1 - x0, y1 - y0) / 2
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for poly in d["lanes"]:
        ax.add_patch(Polygon([p[:2] for p in poly], closed=True, fc="#DADADA", ec="#DADADA", lw=0.3))
    for l in d["lines"]:
        ax.plot([p[0] for p in l], [p[1] for p in l], color="#E0B000", lw=0.5)
    order = sorted(ex, key=lambda e: (e["selected_rank"] is not None, status(e) == "ok"))
    for e in order:
        k = f"{e['policy']}/{e['variant']}"
        tr = e["track"][1:]
        X, Y = [p[0] for p in tr], [p[1] for p in tr]
        st = status(e)
        if e["selected_rank"]:
            ax.plot(X, Y, color="#1A1A1A", lw=5.2, solid_capstyle="round", zorder=4)
            ax.plot(X, Y, color=COLORS[k], lw=3.4, solid_capstyle="round", zorder=5)
        elif st == "ok":
            ax.plot(X, Y, color=COLORS[k], lw=1.8, zorder=3)
        else:
            ax.plot(X, Y, color=COLORS[k], lw=1.8, ls="--" if st == "rule" else ":", zorder=2)
        ax.plot(X[-1], Y[-1], "o", ms=3.5, color=COLORS[k], mec="#1A1A1A", mew=0.4, zorder=6)
    s0 = ex[0]["track"][1]
    ax.plot(s0[0], s0[1], marker="s", ms=6, color="white", mec="#1A1A1A", mew=1.2, zorder=7)
    ax.set_xlim(cx - half, cx + half)
    ax.set_ylim(cy - half, cy + half)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#BBBBBB")
    ax.set_title(title, fontsize=11, fontweight="bold", loc="left")


REASON = {"rule": "target sign violated", "off-road": "left the road", "crash": "collision",
          "no arrival": "destination not reached"}
GREEN, RED, INK, MUTED, BADGE = "#2E8B57", "#D64533", "#1A1A1A", "#8A8F98", "#F2B705"


def mark(ax, x, y, ok, alpha):
    ax.add_patch(plt.Circle((x, y), 0.028, transform=ax.transAxes, color=GREEN if ok else RED, alpha=alpha, lw=0))
    ax.text(x, y - 0.003, "✓" if ok else "✗", transform=ax.transAxes, ha="center", va="center", color="white",
            fontsize=10, fontweight="bold", alpha=alpha)


def draw_table(ax, d):
    """v1-style selection table + Quality column (real flags, real F-scores, real top-2)."""
    ax.set_axis_off()
    cand = {(c["policy"], c["variant"]): c["f1"] for c in d["selection"]["all_candidates"]}
    X = {"name": 0.0, "rule": 0.30, "dest": 0.45, "reason": 0.53, "q": 0.78}
    y = 0.95
    for k, lab in (("rule", "Rule\nobeyed?"), ("dest", "Destination\nreached?"), ("q", "Quality")):
        ax.text(X[k], y, lab, transform=ax.transAxes, ha="center", va="center", fontsize=9.5, color=MUTED)
    ax.text(X["q"], y - 0.06, "F-score, β = 0.25", transform=ax.transAxes, ha="center", va="center", fontsize=7.5, color=MUTED)
    n_ok = 0
    for i, (k, name) in enumerate(NAMES.items()):
        e = next(x for x in d["experts"] if f"{x['policy']}/{x['variant']}" == k)
        st = status(e)
        f = cand.get((e["policy"], e["variant"]))
        sel = e["selected_rank"]
        n_ok += st == "ok"
        alpha = 1.0 if st == "ok" else 0.38
        yy = 0.82 - i * 0.088
        ax.plot([X["name"], X["name"] + 0.05], [yy, yy], transform=ax.transAxes, color=COLORS[k], lw=3.5, alpha=alpha,
                solid_capstyle="round")
        ax.text(X["name"] + 0.07, yy, name, transform=ax.transAxes, va="center", fontsize=12, alpha=alpha,
                fontweight="bold" if sel else "normal", color=INK)
        mark(ax, X["rule"], yy, st != "rule", alpha)
        mark(ax, X["dest"], yy, e["arrived_dest"] and not e["out_of_road"] and not e["crashed"], alpha)
        if st != "ok":
            ax.text(X["reason"], yy, REASON[st], transform=ax.transAxes, va="center", fontsize=8.5, color=RED, alpha=0.75)
        if f is not None:
            ax.text(X["q"], yy, f"{f:.2f}", transform=ax.transAxes, ha="center", va="center", fontsize=12,
                    color=INK if sel else MUTED, fontweight="bold" if sel else "normal")
        elif st == "ok":
            ax.text(X["q"], yy, "IDM: not best", transform=ax.transAxes, ha="center", va="center", fontsize=7.5, color=MUTED)
        else:
            ax.text(X["q"], yy, "—", transform=ax.transAxes, ha="center", va="center", fontsize=12, color=MUTED, alpha=0.6)
        if sel:
            ax.text(0.845, yy, f"selected #{sel}", transform=ax.transAxes, va="center", fontsize=8.5, fontweight="bold",
                    color=INK, bbox=dict(boxstyle="round,pad=0.25", fc=BADGE, ec="none"))
    nc = len(d["selection"]["all_candidates"])
    ax.text(0.0, 0.03, f"{n_ok} successful · {nc} compete on quality · {len([e for e in d['experts'] if e['selected_rank']])} selected",
            transform=ax.transAxes, fontsize=10.5, color=INK)


def cell(fig, rect, d, title):
    x, y, w, h = rect
    ax_map = fig.add_axes([x, y, w * 0.42, h * 0.86])
    draw(ax_map, d, title)
    ax_tab = fig.add_axes([x + w * 0.45, y, w * 0.53, h * 0.86])
    draw_table(ax_tab, d)


fig = plt.figure(figsize=(3 * 9.5, 3 * 4.6))
for i, (title, p) in enumerate(scenes):
    d = json.loads(p.read_text())
    t = f"{title}\n{d['meta']['scene_uid'][:58]}"
    cell(fig, ((i % 3) / 3 + 0.004, 1 - (i // 3 + 1) / 3 + 0.02, 1 / 3 - 0.008, 1 / 3 - 0.03), d, t)
    f2 = plt.figure(figsize=(12, 5.4))
    cell(f2, (0.01, 0.02, 0.98, 0.93), d, f"{title}\n{d['meta']['scene_uid']}")
    f2.savefig(OUT / f"{p.stem}.png", dpi=120)
    plt.close(f2)
fig.text(0.5, 0.004, "map: white square = start · dashed = target-sign violation · dotted = destination not reached · "
         "thick outlined = real top-2 selection · thin solid = successful, not selected · dot = end of rollout",
         ha="center", fontsize=12)
fig.savefig(OUT / OUT_NAME, dpi=80)
print("wrote", OUT / OUT_NAME, len(scenes), "scenes")
