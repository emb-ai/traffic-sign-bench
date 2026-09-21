#!/usr/bin/env python3
"""Plot category-level composition and within-category oracle consistency."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from plot_oracle_expert_diversity import (
    DEFAULT_EXTRA_ROOT,
    EXPERTS,
    ScenarioComposition,
    load_data,
    set_plot_style,
)


CATEGORY_ORDER = ("Priority", "Speed", "Detour", "Directional control")
CATEGORY_LABELS = {
    "Priority": "Priority",
    "Speed": "Speed",
    "Detour": "Obstacles",
    "Directional control": "Routing",
}
COLORS = {
    "IDM": "#90CAF9",
    "PPO": "#E76F51",
    "CaRL": "#A1CB35",
    "PlanT-2": "#FCAD38",
}
PERCENT_TEXT_COLORS = {
    "IDM": "#111827",
    "PPO": "#111827",
    "CaRL": "#111827",
    "PlanT-2": "#111827",
}


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trajectory-root",
        type=Path,
        action="append",
        dest="trajectory_roots",
        help="Directory containing one subdirectory per sign. May be repeated.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root / "paper" / "imgs",
        help="Destination directory for figures and category statistics.",
    )
    args = parser.parse_args()
    if not args.trajectory_roots:
        args.trajectory_roots = [
            repo_root / "data" / "trajectories",
            DEFAULT_EXTRA_ROOT,
        ]
    return args


def group_data(
    data: list[ScenarioComposition],
) -> dict[str, list[ScenarioComposition]]:
    grouped: dict[str, list[ScenarioComposition]] = defaultdict(list)
    for item in data:
        grouped[item.group].append(item)
    missing = set(CATEGORY_ORDER) - set(grouped)
    if missing:
        raise ValueError(f"Missing scenario categories: {sorted(missing)}")
    return dict(grouped)


def category_counts(
    items: list[ScenarioComposition],
) -> dict[str, int]:
    return {
        expert: sum(item.counts[expert] for item in items)
        for expert in EXPERTS
    }


def write_category_stats(
    grouped: dict[str, list[ScenarioComposition]],
    output_path: Path,
) -> None:
    fieldnames = [
        "category",
        "n_scenarios",
        "n_trajectories",
        "expert",
        "expert_count",
        "aggregate_percent",
        "scenario_mean_percent",
        "scenario_sd_percent",
        "scenario_min_percent",
        "scenario_max_percent",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for category in CATEGORY_ORDER:
            items = grouped[category]
            counts = category_counts(items)
            total = sum(counts.values())
            for expert in EXPERTS:
                values = [item.percentage(expert) for item in items]
                writer.writerow(
                    {
                        "category": CATEGORY_LABELS[category],
                        "n_scenarios": len(items),
                        "n_trajectories": total,
                        "expert": expert,
                        "expert_count": counts[expert],
                        "aggregate_percent": f"{100 * counts[expert] / total:.3f}",
                        "scenario_mean_percent": f"{mean(values):.3f}",
                        "scenario_sd_percent": f"{stdev(values):.3f}",
                        "scenario_min_percent": f"{min(values):.3f}",
                        "scenario_max_percent": f"{max(values):.3f}",
                    }
                )


def save_figure(
    fig: mpl.figure.Figure,
    output_dir: Path,
    stem: str,
    title: str,
) -> tuple[Path, Path]:
    png_path = output_dir / f"{stem}.png"
    pdf_path = output_dir / f"{stem}.pdf"
    fig.savefig(
        png_path,
        dpi=600,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.08,
        metadata={"Title": title},
    )
    fig.savefig(
        pdf_path,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.08,
        metadata={
            "Title": title,
            "Creator": "TrafficRuleBench plotting script",
        },
    )
    plt.close(fig)
    return png_path, pdf_path


def plot_category_composition(
    grouped: dict[str, list[ScenarioComposition]],
    output_dir: Path,
) -> tuple[Path, Path]:
    set_plot_style()
    fig, ax = plt.subplots(figsize=(7.7, 3.55), facecolor="white")
    fig.subplots_adjust(left=0.205, right=0.88, top=0.75, bottom=0.23)

    handles = [Patch(facecolor=COLORS[expert], label=expert) for expert in EXPERTS]
    fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.87),
        ncol=4,
        frameon=False,
        columnspacing=2.0,
        handlelength=1.6,
        fontsize=13.5,
    )

    for y, category in enumerate(CATEGORY_ORDER):
        items = grouped[category]
        counts = category_counts(items)
        total = sum(counts.values())
        left = 0.0
        for expert in EXPERTS:
            width = 100 * counts[expert] / total
            ax.barh(
                y,
                width,
                left=left,
                height=0.58,
                color=COLORS[expert],
                edgecolor="white",
                linewidth=0.75,
                zorder=3,
            )
            if width >= 4:
                ax.text(
                    left + width / 2,
                    y,
                    f"{width:.1f}%",
                    ha="center",
                    va="center",
                    fontsize=9.0 if width < 7 else 10.5,
                    fontweight="bold",
                    color=PERCENT_TEXT_COLORS[expert],
                    zorder=4,
                )
            left += width
        ax.text(
            101.4,
            y,
            f"{len(items)} scenarios\nn={total:,}",
            ha="left",
            va="center",
            fontsize=9.2,
            color="#696761",
            linespacing=1.15,
            clip_on=False,
        )

    ax.set_xlim(0, 100)
    ax.set_yticks(
        range(len(CATEGORY_ORDER)),
        [CATEGORY_LABELS[category] for category in CATEGORY_ORDER],
    )
    ax.invert_yaxis()
    ax.tick_params(axis="y", length=0, pad=8, labelsize=13.5)
    ax.set_xticks((0, 25, 50, 75, 100))
    ax.tick_params(axis="x", labelsize=10.5)
    ax.set_xlabel(
        "Share of oracle-selected top-2 trajectories (%)",
        labelpad=9,
        fontsize=13.5,
    )
    ax.xaxis.grid(True, color="#DEDDD9", linewidth=0.65)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    return save_figure(
        fig,
        output_dir,
        "oracle_expert_diversity_by_category",
        "Oracle expert composition by category",
    )


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = load_data(args.trajectory_roots)
    grouped = group_data(data)

    stats_path = args.output_dir / "oracle_expert_diversity_by_category.tsv"
    write_category_stats(grouped, stats_path)
    composition_paths = plot_category_composition(grouped, args.output_dir)

    for path in (*composition_paths, stats_path):
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
