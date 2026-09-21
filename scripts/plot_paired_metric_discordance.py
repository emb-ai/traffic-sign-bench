#!/usr/bin/env python3
"""Paired destination-vs-compliance analysis by planner and scenario type.

Replaces planner-rank Spearman heatmaps (n=9, IDM-variant inflated) with
matched scenario-level outcomes and scenario-clustered uncertainty.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle


LOCAL_SCENARIOS = {
    "2.1": "main_road",
    "2.3": "secondary_road",
    "2.4": "yield",
    "2.5": "stop",
    "4.3": "roundabout",
    "5.19": "crosswalk",
    "3.2": "blocked_road",
    "4.1.1": "direction_straight",
    "4.1.2": "direction_right",
    "4.1.3": "direction_left",
    "4.1.4": "direction_straight_right",
    "4.1.5": "direction_straight_left",
    "4.1.6": "direction_left_right",
    "3.1": "no_entry",
    "3.18.1": "no_turn_right",
    "3.18.2": "no_turn_left",
    "5.7.1": "one_way_right",
    "5.7.2": "one_way_left",
}
ALL_CODES = (
    "2.1",
    "2.3",
    "2.4",
    "2.5",
    "4.3",
    "5.19",
    "3.24",
    "4.6",
    "5.21",
    "5.31",
    "3.2",
    "4.2.1",
    "4.2.2",
    "4.2.3",
    "5.11.1",
    "5.11.2",
    "5.14.1",
    "5.14.2",
    "4.1.1",
    "4.1.2",
    "4.1.3",
    "4.1.4",
    "4.1.5",
    "4.1.6",
    "3.1",
    "3.18.1",
    "3.18.2",
    "5.7.1",
    "5.7.2",
)
GROUPS = {
    "Priority": ("2.1", "2.3", "2.4", "2.5", "4.3", "5.19"),
    "Speed": ("3.24", "4.6", "5.21", "5.31"),
    "Obstacle": (
        "3.2",
        "4.2.1",
        "4.2.2",
        "4.2.3",
        "5.11.1",
        "5.11.2",
        "5.14.1",
        "5.14.2",
    ),
    "Routing": (
        "4.1.1",
        "4.1.2",
        "4.1.3",
        "4.1.4",
        "4.1.5",
        "4.1.6",
        "3.1",
        "3.18.1",
        "3.18.2",
        "5.7.1",
        "5.7.2",
    ),
}
CODE_TO_GROUP = {code: group for group, codes in GROUPS.items() for code in codes}
GROUP_COLORS = {
    "Priority": "#4C78A8",
    "Speed": "#E76F51",
    "Obstacle": "#72A447",
    "Routing": "#E3A128",
}
POLICIES = (
    ("idm", "base", "idm_default", "idm_default", "IDM"),
    ("idm_s1", "base", "idm_s1", "idm_s1", "IDM"),
    ("idm_s2", "base", "idm_s2", "idm_s2", "IDM"),
    ("idm_s3", "base", "idm_s3", "idm_s3", "IDM"),
    ("idm_s4", "base", "idm_s4", "idm_s4", "IDM"),
    ("ppo", "base", "ppo_lidar_default", "ppo_lidar", "PPO"),
    ("carl", "base", "carl_default", "carl", "CaRL"),
    ("plant2", "base", "plant2_default", "plant2", "PlanT-2"),
    ("plant2_ft", "ours", None, None, "PlanT-2-FT"),
)
def parse_args() -> argparse.Namespace:
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=repo)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo / "paper" / "imgs",
    )
    return parser.parse_args()


def set_plot_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIXGeneral", "DejaVu Serif", "Times New Roman"],
            "mathtext.fontset": "stix",
            "font.size": 8.4,
            "axes.labelsize": 8.6,
            "axes.titlesize": 8.8,
            "axes.edgecolor": "#8A8984",
            "axes.linewidth": 0.7,
            "axes.axisbelow": True,
            "xtick.color": "#3F3E3A",
            "ytick.color": "#3F3E3A",
            "text.color": "#252522",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def load_sources(repo: Path) -> dict[tuple[str, str], dict[str, float]]:
    local: dict[tuple[str, str], dict[str, str]] = {}
    for code, family in LOCAL_SCENARIOS.items():
        path = repo / "data/icra27_results/sources/local" / f"{family}.csv"
        with path.open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                local[(code, row["baseline"])] = row

    ext: dict[tuple[str, str], dict[str, str]] = {}
    with (repo / "data/icra27_results/sources/smirnova_v7_rl3_metrics.tsv").open(
        newline="", encoding="utf-8"
    ) as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            ext[(row["pdd"], row["policy"])] = row

    ft: dict[str, dict[str, str]] = {}
    with (repo / "data/icra27_results/sources/plant2_ft_per_sign_baseline.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        for row in csv.DictReader(stream):
            ft[row["pdd_code"]] = row

    records: dict[tuple[str, str], dict[str, float]] = {}
    for key, kind, local_name, ext_name, family in POLICIES:
        for code in ALL_CODES:
            if kind == "ours":
                raw = ft[code]
                rec = {
                    "dest": float(raw["dest_rate"]),
                    "sc": float(raw["target_compliance_rate_event"]),
                    "scd": float(raw["sr_and_dest"]),
                    "driving_score": float(raw["avg_driving_score"]),
                    "collision": float(raw["crash_rate"]),
                    "comfort": float(raw["avg_comfort"]),
                    "relative_speed": float(raw["avg_driving_efficiency"]),
                    "n": float(raw["n"]),
                }
            else:
                raw = local.get((code, local_name or ""))
                if raw is not None:
                    rec = {
                        "dest": float(raw["dest_rate"]),
                        "sc": float(raw["target_compliance_rate_event"]),
                        "scd": float(raw["sr_and_dest"]),
                        "driving_score": float(raw["avg_driving_score"]),
                        "collision": float(raw["crash_rate"]),
                        "comfort": float(raw["avg_comfort"]),
                        "relative_speed": float(raw["avg_driving_efficiency"]),
                        "n": float(raw["n"]),
                    }
                else:
                    raw = ext[(code, ext_name or "")]
                    rec = {
                        "dest": float(raw["dest"]),
                        "sc": float(raw["compliance"]),
                        "scd": float(raw["sr_dest"]),
                        "driving_score": float(raw["driving_score"]),
                        "collision": float(raw["collision_rate"]),
                        "comfort": float(raw["comfort"]),
                        "relative_speed": float(raw["efficiency"]),
                        "n": float(raw["n"]),
                    }
            rec.update(
                family=family,
                group=CODE_TO_GROUP[code],
                code=code,
                kind=kind,
            )
            records[(key, code)] = rec
    return records


def pearson(xs: list[float], ys: list[float]) -> float:
    arr_x = np.asarray(xs, dtype=float)
    arr_y = np.asarray(ys, dtype=float)
    if arr_x.std() < 1e-12 or arr_y.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(arr_x, arr_y)[0, 1])


def clustered_gap_summary(
    points: list[dict[str, float]],
    *,
    seed: int,
    draws: int = 20_000,
) -> dict[str, float]:
    """Summarize Dest-SC while resampling scenario types as clusters."""
    code_means = []
    for code in sorted({str(point["code"]) for point in points}):
        gaps = [
            100.0 * (point["dest"] - point["sc"])
            for point in points
            if point["code"] == code
        ]
        code_means.append(float(np.mean(gaps)))
    values = np.asarray(
        [100.0 * (point["dest"] - point["sc"]) for point in points],
        dtype=float,
    )
    rng = np.random.default_rng(seed)
    sampled = rng.choice(
        np.asarray(code_means, dtype=float),
        size=(draws, len(code_means)),
        replace=True,
    ).mean(axis=1)
    return {
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "ci_lo": float(np.quantile(sampled, 0.025)),
        "ci_hi": float(np.quantile(sampled, 0.975)),
        "n_cells": float(len(points)),
        "n_types": float(len(code_means)),
    }


def family_balanced_cells(points: list[dict[str, float]]) -> list[dict[str, float]]:
    """Collapse five IDM variants so each planner family has equal cell weight."""
    fields = (
        "dest",
        "sc",
        "scd",
        "driving_score",
        "collision",
        "comfort",
        "relative_speed",
    )
    cells: list[dict[str, float]] = []
    for code in sorted({str(point["code"]) for point in points}):
        code_points = [point for point in points if point["code"] == code]
        for family in ("IDM", "PPO", "CaRL", "PlanT-2"):
            family_points = [
                point for point in code_points if point["family"] == family
            ]
            if not family_points:
                raise ValueError(f"Missing {family} cell for scenario {code}")
            cell = {
                field: float(np.mean([point[field] for point in family_points]))
                for field in fields
            }
            cell.update(
                code=code,
                family=family,
                group=family_points[0]["group"],
            )
            cells.append(cell)
    return cells


def within_type_association(
    cells: list[dict[str, float]],
    metric: str,
    outcome: str,
    *,
    seed: int,
    draws: int = 20_000,
) -> dict[str, float]:
    """Repeated-measures correlation with scenario-clustered bootstrap."""
    covariance_terms = []
    metric_ss_terms = []
    outcome_ss_terms = []
    for code in sorted({str(cell["code"]) for cell in cells}):
        code_cells = [cell for cell in cells if cell["code"] == code]
        metric_values = np.asarray([cell[metric] for cell in code_cells], dtype=float)
        outcome_values = np.asarray([cell[outcome] for cell in code_cells], dtype=float)
        metric_values -= metric_values.mean()
        outcome_values -= outcome_values.mean()
        covariance_terms.append(float(np.sum(metric_values * outcome_values)))
        metric_ss_terms.append(float(np.sum(metric_values**2)))
        outcome_ss_terms.append(float(np.sum(outcome_values**2)))

    covariance = np.asarray(covariance_terms)
    metric_ss = np.asarray(metric_ss_terms)
    outcome_ss = np.asarray(outcome_ss_terms)
    correlation = float(
        covariance.sum() / np.sqrt(metric_ss.sum() * outcome_ss.sum())
    )
    rng = np.random.default_rng(seed)
    sampled = rng.integers(0, len(covariance), size=(draws, len(covariance)))
    bootstrap = covariance[sampled].sum(axis=1) / np.sqrt(
        metric_ss[sampled].sum(axis=1) * outcome_ss[sampled].sum(axis=1)
    )
    return {
        "r": correlation,
        "ci_lo": float(np.quantile(bootstrap, 0.025)),
        "ci_hi": float(np.quantile(bootstrap, 0.975)),
        "n_cells": float(len(cells)),
        "n_types": float(len(covariance)),
    }


def metric_associations(
    points: list[dict[str, float]],
) -> list[dict[str, str | float]]:
    cells = family_balanced_cells(points)
    rows: list[dict[str, str | float]] = []
    for outcome_idx, (outcome, outcome_label) in enumerate(
        (("sc", "SC"), ("scd", "SCD"))
    ):
        for metric_idx, (metric, metric_label) in enumerate(
            (
                ("dest", "Dest"),
                ("collision", "Crash"),
                ("comfort", "Comfort"),
                ("relative_speed", "Rel. speed"),
            )
        ):
            summary = within_type_association(
                cells,
                metric,
                outcome,
                seed=3027 + 100 * outcome_idx + metric_idx,
            )
            rows.append(
                {
                    "outcome": outcome_label,
                    "metric": metric_label,
                    **summary,
                }
            )
    return rows


def draw_scatter(ax, points: list[dict[str, float]], r_sc: float) -> None:
    ax.add_patch(
        Rectangle(
            (70, 0),
            35,
            50,
            facecolor="#F4E1E1",
            edgecolor="none",
            zorder=0,
        )
    )
    ax.plot([0, 100], [0, 100], color="#C4C3BE", lw=0.8, ls="--", zorder=1)
    for point in points:
        ax.scatter(
            100.0 * point["dest"],
            100.0 * point["sc"],
            s=18,
            marker="o",
            c="#777671",
            edgecolors="none",
            alpha=0.62,
            zorder=3,
        )
    ax.set_xlim(-2, 102)
    ax.set_ylim(-2, 102)
    ax.set_xlabel("Dest (%)")
    ax.set_ylabel("SC (%)")
    ax.set_title("(a) Destination vs. compliance", loc="left", pad=4, fontweight="semibold")
    ax.grid(True, color="#E7E6E1", lw=0.5)
    for spine in ax.spines.values():
        spine.set_color("#B7B6B1")
    ax.text(
        0.03,
        0.97,
        rf"descriptive $r={r_sc:+.2f}$" if np.isfinite(r_sc) else "",
        transform=ax.transAxes,
        va="top",
        fontsize=7.4,
        color="#3F3E3A",
    )


def write_gap_stats(
    path: Path,
    summaries: list[dict[str, str | float]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "regime",
        "group",
        "n_scenario_types",
        "n_cells",
        "mean_dest_minus_sc_pp",
        "median_dest_minus_sc_pp",
        "cluster_bootstrap_ci95_lo",
        "cluster_bootstrap_ci95_hi",
    )
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(summaries)


def draw_associations(
    ax: mpl.axes.Axes,
    rows: list[dict[str, str | float]],
) -> None:
    metrics = ["Dest", "Crash", "Comfort", "Rel. speed"]
    styles = (
        ("SC", "#765A91", "o", -0.11),
        ("SCD", "#008F87", "D", 0.11),
    )
    for outcome, color, marker, offset in styles:
        for index, metric in enumerate(metrics):
            row = next(
                item
                for item in rows
                if item["outcome"] == outcome and item["metric"] == metric
            )
            y = len(metrics) - 1 - index + offset
            center = float(row["r"])
            ax.errorbar(
                center,
                y,
                xerr=[
                    [center - float(row["ci_lo"])],
                    [float(row["ci_hi"]) - center],
                ],
                fmt=marker,
                color=color,
                ecolor=color,
                elinewidth=1.05,
                capsize=2.0,
                markersize=4.5,
                label=outcome if index == 0 else None,
                zorder=3,
            )
    ax.axvline(0, color="#777671", lw=0.8, zorder=1)
    ax.set_xlim(-0.82, 0.82)
    ax.set_xticks((-0.8, -0.4, 0.0, 0.4, 0.8))
    ax.set_ylim(-0.5, 3.5)
    ax.set_yticks(range(3, -1, -1), metrics)
    ax.set_xlabel("Within-type Pearson $r$")
    ax.set_title("(c) Conventional metrics", loc="left", pad=4, fontweight="semibold")
    ax.grid(True, axis="x", color="#E7E6E1", lw=0.5)
    ax.legend(loc="upper right", frameon=False, fontsize=7.0)


def write_association_stats(
    path: Path,
    rows: list[dict[str, str | float]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "outcome",
        "metric",
        "n_scenario_types",
        "n_family_balanced_cells",
        "within_type_pearson_r",
        "cluster_bootstrap_ci95_lo",
        "cluster_bootstrap_ci95_hi",
    )
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "outcome": row["outcome"],
                    "metric": row["metric"],
                    "n_scenario_types": int(float(row["n_types"])),
                    "n_family_balanced_cells": int(float(row["n_cells"])),
                    "within_type_pearson_r": f"{float(row['r']):.6f}",
                    "cluster_bootstrap_ci95_lo": f"{float(row['ci_lo']):.6f}",
                    "cluster_bootstrap_ci95_hi": f"{float(row['ci_hi']):.6f}",
                }
            )


def render_figure(
    records: dict[tuple[str, str], dict[str, float]],
    output_dir: Path,
    gap_stats_path: Path,
    association_stats_path: Path,
) -> None:
    set_plot_style()
    base = [rec for (key, _), rec in records.items() if rec["kind"] == "base"]
    ours = [rec for rec in records.values() if rec["kind"] == "ours"]
    r_base = pearson([r["dest"] for r in base], [r["sc"] for r in base])

    associations = metric_associations(base)

    figure = plt.figure(figsize=(7.16, 2.85), facecolor="white")
    grid = figure.add_gridspec(
        1,
        3,
        left=0.065,
        right=0.99,
        bottom=0.19,
        top=0.86,
        width_ratios=(1.05, 1.18, 0.94),
        wspace=0.38,
    )
    ax0 = figure.add_subplot(grid[0, 0])
    ax1 = figure.add_subplot(grid[0, 1])
    ax2 = figure.add_subplot(grid[0, 2])
    draw_scatter(ax0, base, r_base)

    groups = ["Overall", "Priority", "Speed", "Obstacle", "Routing"]
    stats_rows: list[dict[str, str | float]] = []
    for regime_idx, (regime, points, color, marker, offset) in enumerate(
        (
            ("Standard", base, "#B45454", "o", -0.12),
            ("PlanT-2-FT", ours, "#3E6F98", "s", 0.12),
        )
    ):
        for group_idx, group in enumerate(groups):
            subset = points if group == "Overall" else [
                point for point in points if point["group"] == group
            ]
            summary = clustered_gap_summary(
                subset,
                seed=2027 + 100 * regime_idx + group_idx,
            )
            y = len(groups) - 1 - group_idx + offset
            ax1.errorbar(
                summary["mean"],
                y,
                xerr=[
                    [summary["mean"] - summary["ci_lo"]],
                    [summary["ci_hi"] - summary["mean"]],
                ],
                fmt=marker,
                color=color,
                ecolor=color,
                elinewidth=1.1,
                capsize=2.2,
                markersize=5.0,
                zorder=3,
            )
            stats_rows.append(
                {
                    "regime": regime,
                    "group": group,
                    "n_scenario_types": int(summary["n_types"]),
                    "n_cells": int(summary["n_cells"]),
                    "mean_dest_minus_sc_pp": f"{summary['mean']:.6f}",
                    "median_dest_minus_sc_pp": f"{summary['median']:.6f}",
                    "cluster_bootstrap_ci95_lo": f"{summary['ci_lo']:.6f}",
                    "cluster_bootstrap_ci95_hi": f"{summary['ci_hi']:.6f}",
                }
            )
    ax1.axvspan(0, 70, color="#F4E1E1", alpha=0.6, zorder=0)
    ax1.axvspan(-60, 0, color="#E4EEF6", alpha=0.7, zorder=0)
    ax1.axvline(0, color="#777671", lw=0.8, zorder=1)
    ax1.set_xlim(-60, 70)
    ax1.set_ylim(-0.55, 4.55)
    ax1.set_yticks(range(4, -1, -1), groups)
    ax1.set_xlabel("Dest $-$ SC (percentage points)")
    ax1.set_title("(b) Clustered paired gaps", loc="left", pad=4, fontweight="semibold")
    ax1.grid(True, axis="x", color="#E7E6E1", lw=0.5)
    ax1.text(0.02, 0.98, "PlanT-2-FT: SC $>$ Dest", transform=ax1.transAxes, fontsize=6.8, color="#416B8A", va="top")
    ax1.text(0.98, 0.98, "Standard: Dest $>$ SC", transform=ax1.transAxes, fontsize=6.8, color="#8D4A4A", ha="right", va="top")
    draw_associations(ax2, associations)

    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / "correlation.png"
    pdf_path = output_dir / "correlation.pdf"
    figure.savefig(png_path, dpi=400, facecolor="white")
    figure.savefig(pdf_path, facecolor="white")
    plt.close(figure)
    write_gap_stats(gap_stats_path, stats_rows)
    write_association_stats(association_stats_path, associations)
    overall_base = clustered_gap_summary(base, seed=2027)
    overall_ours = clustered_gap_summary(ours, seed=2127)
    print(f"Wrote {png_path}")
    print(f"Wrote {pdf_path}")
    print(
        "base cells",
        len(base),
        "Dest>=70 & SC<=50:",
        sum(r["dest"] >= 0.7 and r["sc"] <= 0.5 for r in base),
        "r Dest-SC",
        round(r_base, 3),
        "gap",
        round(overall_base["mean"], 2),
        "CI",
        (round(overall_base["ci_lo"], 2), round(overall_base["ci_hi"], 2)),
        "FT gap",
        round(overall_ours["mean"], 2),
    )


def render_scatter_grid(
    records: dict[tuple[str, str], dict[str, float]],
    output_dir: Path,
) -> None:
    """Render raw paired-cell scatters for supplementary diagnosis."""
    base = family_balanced_cells(
        [record for record in records.values() if record["kind"] == "base"]
    )
    ours = [record for record in records.values() if record["kind"] == "ours"]
    metrics = (
        ("dest", "Destination", 100.0),
        ("collision", "Crash rate", 100.0),
        ("comfort", "Comfort", 100.0),
        ("relative_speed", "Relative speed", 1.0),
    )
    outcomes = (("sc", "SC"), ("scd", "SCD"))
    figure, axes = plt.subplots(
        2,
        4,
        figsize=(7.16, 4.0),
        sharey="row",
        facecolor="white",
    )
    figure.subplots_adjust(left=0.07, right=0.995, bottom=0.13, top=0.91, hspace=0.33, wspace=0.20)
    for row_index, (outcome, outcome_label) in enumerate(outcomes):
        for column_index, (metric, title, scale) in enumerate(metrics):
            axis = axes[row_index, column_index]
            base_x = np.asarray([scale * cell[metric] for cell in base])
            base_y = np.asarray([100.0 * cell[outcome] for cell in base])
            ours_x = np.asarray([scale * cell[metric] for cell in ours])
            ours_y = np.asarray([100.0 * cell[outcome] for cell in ours])
            axis.scatter(
                base_x,
                base_y,
                s=14,
                color="#777671",
                alpha=0.48,
                edgecolors="none",
                label="Standard families" if row_index == column_index == 0 else None,
            )
            axis.scatter(
                ours_x,
                ours_y,
                s=32,
                marker="*",
                color="#C155A3",
                alpha=0.86,
                edgecolors="white",
                linewidths=0.3,
                label="PlanT-2-FT" if row_index == column_index == 0 else None,
            )
            raw_r = pearson(base_x.tolist(), base_y.tolist())
            axis.text(
                0.04,
                0.95,
                rf"raw $r={raw_r:+.2f}$",
                transform=axis.transAxes,
                va="top",
                fontsize=6.8,
            )
            axis.set_ylim(-3, 103)
            axis.grid(True, color="#E7E6E1", lw=0.45)
            axis.spines["top"].set_visible(False)
            axis.spines["right"].set_visible(False)
            if row_index == 0:
                axis.set_title(f"({chr(97 + column_index)}) {title}", loc="left", fontweight="semibold")
            if row_index == 1:
                unit = " (%)" if metric != "relative_speed" else " (%)"
                axis.set_xlabel(title + unit)
            if column_index == 0:
                axis.set_ylabel(outcome_label + " (%)")
    figure.legend(
        handles=[
            Line2D([0], [0], marker="o", color="none", markerfacecolor="#777671", markersize=5, label="Standard families"),
            Line2D([0], [0], marker="*", color="none", markerfacecolor="#C155A3", markersize=8, label="PlanT-2-FT"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 1.0),
        ncol=2,
        frameon=False,
        fontsize=7.2,
    )
    for extension, kwargs in (("png", {"dpi": 400}), ("pdf", {})):
        figure.savefig(
            output_dir / f"metric_scatter_grid.{extension}",
            facecolor="white",
            bbox_inches="tight",
            pad_inches=0.03,
            **kwargs,
        )
    plt.close(figure)

    tex = r"""\begin{figure*}[t]
\centering
\includegraphics[width=\textwidth]{imgs/metric_scatter_grid.pdf}
\caption{\textbf{Raw paired-cell diagnostic plots.}
Each gray point is one (planner family, scenario type) cell after averaging the
five IDM parameterizations; stars show PlanT-2-FT. Rows compare conventional
metrics with isolated sign compliance (SC) and joint success (SCD). Raw
correlations retain between-scenario difficulty and are descriptive; the
within-type, scenario-clustered estimates in Fig.~\ref{fig:correlation}(c) are
the primary association analysis.}
\label{fig:metric_scatter_grid}
\end{figure*}
"""
    (output_dir / "metric_scatter_grid.tex").write_text(tex, encoding="utf-8")


def render_scd_scatter_grid(
    records: dict[tuple[str, str], dict[str, float]],
    output_dir: Path,
) -> None:
    """Render SCD against four conventional driving metrics in a 2x2 grid."""
    base = family_balanced_cells(
        [record for record in records.values() if record["kind"] == "base"]
    )
    ours = [record for record in records.values() if record["kind"] == "ours"]
    metrics = (
        ("driving_score", "Driving Score", 1.0, (-3.0, 103.0)),
        ("dest", "Destination", 100.0, (-3.0, 103.0)),
        ("relative_speed", "Efficiency", 1.0, (0.0, 380.0)),
        ("collision", "Collision rate", 100.0, (-3.0, 103.0)),
    )

    figure, axes_grid = plt.subplots(
        2,
        2,
        figsize=(3.9, 4.35),
        sharey=True,
        facecolor="white",
    )
    figure.subplots_adjust(
        left=0.14,
        right=0.985,
        bottom=0.10,
        top=0.88,
        hspace=0.48,
        wspace=0.25,
    )
    for panel_index, (axis, (metric, title, scale, xlim)) in enumerate(
        zip(axes_grid.ravel(), metrics)
    ):
        base_x = np.asarray([scale * cell[metric] for cell in base])
        base_y = np.asarray([100.0 * cell["scd"] for cell in base])
        ours_x = np.asarray([scale * cell[metric] for cell in ours])
        ours_y = np.asarray([100.0 * cell["scd"] for cell in ours])
        axis.scatter(
            base_x,
            base_y,
            s=15,
            color="#777671",
            alpha=0.48,
            edgecolors="none",
            zorder=2,
        )
        axis.scatter(
            ours_x,
            ours_y,
            s=34,
            marker="*",
            color="#C155A3",
            alpha=0.86,
            edgecolors="white",
            linewidths=0.3,
            zorder=3,
        )
        raw_r = pearson(base_x.tolist(), base_y.tolist())
        axis.text(
            0.04,
            0.95,
            rf"standard-family $r={raw_r:+.2f}$",
            transform=axis.transAxes,
            va="top",
            fontsize=6.8,
        )
        axis.set_xlim(*xlim)
        axis.set_ylim(-3, 103)
        axis.set_title(
            f"({chr(97 + panel_index)}) {title}",
            loc="left",
            pad=4,
            fontweight="semibold",
        )
        axis.set_xlabel(title + " (%)")
        axis.grid(True, color="#E7E6E1", lw=0.5)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)

    axes_grid[0, 0].set_ylabel("SCD (%)")
    axes_grid[1, 0].set_ylabel("SCD (%)")
    figure.legend(
        handles=[
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor="#777671",
                markersize=5,
                label="Standard families",
            ),
            Line2D(
                [0],
                [0],
                marker="*",
                color="none",
                markerfacecolor="#C155A3",
                markersize=8,
                label="PlanT-2-FT",
            ),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.98),
        ncol=2,
        frameon=False,
        fontsize=8,
        handlelength=1.2,
    )

    metadata = {
        "Title": "SCD versus conventional driving metrics",
        "Creator": "scripts/plot_paired_metric_discordance.py",
    }
    for extension, kwargs in (
        ("png", {"dpi": 450, "metadata": {"Title": metadata["Title"]}}),
        ("pdf", {"metadata": metadata}),
    ):
        figure.savefig(
            output_dir / f"scd_metric_scatter_grid.{extension}",
            facecolor="white",
            bbox_inches="tight",
            pad_inches=0.03,
            **kwargs,
        )
    plt.close(figure)

    tex = r"""\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{imgs/scd_metric_scatter_grid.pdf}
\caption{\textbf{Joint sign-and-destination success versus conventional metrics.}
Each gray point is one standard (planner family, scenario type) cell after
averaging the five IDM parameterizations; stars show PlanT-2-FT cells.
The 29 scenario types yield 116 standard-family cells and 29 PlanT-2-FT
cells. Displayed Pearson correlations use only the standard-family cells and
are descriptive: they retain between-scenario difficulty. Driving Score is
shown for completeness but is not used for cross-source claims because it
inherits the incompatible Route Completion conventions discussed in
Section~\ref{sec:metrics}.}
\label{fig:scd_metric_scatter_grid}
\end{figure}
"""
    (output_dir / "scd_metric_scatter_grid.tex").write_text(
        tex,
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    records = load_sources(args.repo)
    render_figure(
        records,
        args.output_dir,
        args.repo / "data" / "icra27_results" / "paired_dest_sc.tsv",
        args.repo / "data" / "icra27_results" / "metric_associations.tsv",
    )
    render_scatter_grid(records, args.output_dir)
    render_scd_scatter_grid(records, args.output_dir)


if __name__ == "__main__":
    main()
