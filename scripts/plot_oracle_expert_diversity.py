#!/usr/bin/env python3
"""Plot the expert composition of oracle-selected training trajectories."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


EXPERTS = ("IDM", "PPO", "CaRL", "PlanT-2")
COLORS = {
    "IDM": "#426B9A",
    "PPO": "#B45A6A",
    "CaRL": "#3B8F78",
    "PlanT-2": "#D5A33F",
}
TEXT_COLORS = {
    "IDM": "white",
    "PPO": "white",
    "CaRL": "white",
    "PlanT-2": "#27251F",
}

DEFAULT_EXTRA_ROOT = Path(
    "/home/jovyan/shares/SR006.nfs2/smirnova/traffic-rule-bench-main/"
    "data/trajectories_v6"
)

# Order mirrors the semantic taxonomy used in the paper.
SCENARIOS = (
    ("Priority", "main_road", "Main road"),
    ("Priority", "secondary_road", "Secondary road"),
    ("Priority", "yield", "Yield"),
    ("Priority", "stop", "Stop"),
    ("Priority", "roundabout", "Roundabout"),
    ("Priority", "crosswalk", "Crosswalk"),
    ("Speed", "speed_limit", "Speed limit"),
    ("Speed", "min_speed", "Min speed"),
    ("Speed", "zone_speed_limit", "Zone speed limit"),
    ("Speed", "residential_zone", "Residential zone"),
    ("Detour", "blocked_road", "Blocked road"),
    ("Detour", "detour_left", "Detour left"),
    ("Detour", "detour_right", "Detour right"),
    ("Detour", "detour_either", "Detour either side"),
    ("Detour", "bike_lane", "Bike lane"),
    ("Detour", "bike_lane_road", "Bike lane road"),
    ("Detour", "bus_lane", "Bus lane"),
    ("Detour", "bus_lane_road", "Bus lane road"),
    ("Directional control", "no_entry", "No entry"),
    ("Directional control", "no_turn_left", "No left turn"),
    ("Directional control", "no_turn_right", "No right turn"),
    ("Directional control", "direction_straight", "Straight only"),
    ("Directional control", "direction_left", "Left only"),
    ("Directional control", "direction_right", "Right only"),
    ("Directional control", "direction_straight_left", "Straight or left"),
    ("Directional control", "direction_straight_right", "Straight or right"),
    ("Directional control", "direction_left_right", "Left or right"),
    ("Directional control", "one_way_left", "One way — left"),
    ("Directional control", "one_way_right", "One way — right"),
)


@dataclass(frozen=True)
class ScenarioComposition:
    group: str
    key: str
    label: str
    counts: dict[str, int]

    @property
    def total(self) -> int:
        return sum(self.counts.values())

    def percentage(self, expert: str) -> float:
        return 100.0 * self.counts[expert] / self.total


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
        help="Destination directory for PDF, PNG, and aggregated TSV files.",
    )
    args = parser.parse_args()
    if not args.trajectory_roots:
        args.trajectory_roots = [
            repo_root / "data" / "trajectories",
            DEFAULT_EXTRA_ROOT,
        ]
    return args


def resolve_metrics_path(trajectory_roots: list[Path], key: str) -> Path:
    candidates = []
    for root in trajectory_roots:
        candidates.extend(
            (
                root / key / "final" / "oracle_metrics" / "oracle_metrics_summary.tsv",
                root / key / "oracle_metrics" / "oracle_metrics_summary.tsv",
            )
        )
    for path in candidates:
        if path.is_file():
            return path
    searched = "\n  ".join(str(path) for path in candidates)
    raise FileNotFoundError(
        f"Missing oracle metrics for '{key}'. Searched:\n  {searched}"
    )


def read_composition(
    trajectory_roots: list[Path],
    group: str,
    key: str,
    label: str,
) -> ScenarioComposition:
    metrics_path = resolve_metrics_path(trajectory_roots, key)

    with metrics_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    matches = [row for row in rows if row["metric"].startswith("oracle picks")]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one 'oracle picks' row in {metrics_path}, found {len(matches)}"
        )
    row = matches[0]

    idm_columns = sorted(column for column in row if column.startswith("idm_"))
    if not idm_columns:
        raise ValueError(f"No IDM columns found in {metrics_path}")

    counts = {
        "IDM": sum(int(row[column]) for column in idm_columns),
        "PPO": int(row["ppo_signs"]),
        "CaRL": int(row["carl_rule"]),
        "PlanT-2": int(row["plant2_rule"]),
    }
    oracle_total = int(row["ORACLE_new"])
    if sum(counts.values()) != oracle_total:
        raise ValueError(
            f"Expert picks sum to {sum(counts.values())}, but ORACLE_new is "
            f"{oracle_total} in {metrics_path}"
        )
    return ScenarioComposition(group, key, label, counts)


def load_data(trajectory_roots: list[Path]) -> list[ScenarioComposition]:
    data = [
        read_composition(trajectory_roots, group, key, label)
        for group, key, label in SCENARIOS
    ]
    if any(value <= 0 for item in data for value in item.counts.values()):
        raise ValueError("Every expert must contribute at least one selected trajectory.")
    return data


def write_aggregated_tsv(
    data: list[ScenarioComposition],
    output_path: Path,
) -> None:
    totals = {expert: sum(item.counts[expert] for item in data) for expert in EXPERTS}
    grand_total = sum(totals.values())
    fieldnames = ["group", "scenario", "source_key", "selected_total"]
    for expert in EXPERTS:
        fieldnames.extend((f"{expert}_count", f"{expert}_percent"))

    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        overall: dict[str, str | int] = {
            "group": "All",
            "scenario": "Overall",
            "source_key": "all",
            "selected_total": grand_total,
        }
        for expert in EXPERTS:
            overall[f"{expert}_count"] = totals[expert]
            overall[f"{expert}_percent"] = f"{100 * totals[expert] / grand_total:.3f}"
        writer.writerow(overall)

        for item in data:
            row: dict[str, str | int] = {
                "group": item.group,
                "scenario": item.label,
                "source_key": item.key,
                "selected_total": item.total,
            }
            for expert in EXPERTS:
                row[f"{expert}_count"] = item.counts[expert]
                row[f"{expert}_percent"] = f"{item.percentage(expert):.3f}"
            writer.writerow(row)


def set_plot_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIXGeneral", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "axes.edgecolor": "#BBB8B0",
            "axes.linewidth": 0.7,
            "axes.axisbelow": True,
            "xtick.color": "#4B4A47",
            "ytick.color": "#272725",
            "text.color": "#272725",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def add_stacked_bar(
    ax: mpl.axes.Axes,
    y: float,
    percentages: dict[str, float],
    *,
    height: float,
    detailed_labels: bool,
) -> None:
    left = 0.0
    for expert in EXPERTS:
        width = percentages[expert]
        ax.barh(
            y,
            width,
            left=left,
            height=height,
            color=COLORS[expert],
            edgecolor="white",
            linewidth=0.65,
            zorder=3,
        )
        if detailed_labels:
            label = f"{expert}\n{width:.1f}%"
            font_size = 8.2
        elif width >= 5.0:
            label = f"{width:.0f}%"
            font_size = 6.8
        else:
            label = ""
            font_size = 6.8
        if label:
            ax.text(
                left + width / 2,
                y,
                label,
                ha="center",
                va="center",
                color=TEXT_COLORS[expert],
                fontsize=font_size,
                fontweight="bold",
                linespacing=0.9,
                zorder=4,
            )
        left += width


def make_figure(
    data: list[ScenarioComposition],
    output_dir: Path,
) -> tuple[Path, Path]:
    set_plot_style()
    output_dir.mkdir(parents=True, exist_ok=True)

    totals = {expert: sum(item.counts[expert] for item in data) for expert in EXPERTS}
    grand_total = sum(totals.values())
    overall_pct = {
        expert: 100.0 * totals[expert] / grand_total for expert in EXPERTS
    }

    n_groups = len({item.group for item in data})
    panel_b_units = len(data) + 0.85 * max(n_groups - 1, 0)
    fig_height = 2.55 + 0.30 * panel_b_units

    fig = plt.figure(figsize=(7.55, fig_height), facecolor="white")
    grid = fig.add_gridspec(
        2,
        1,
        height_ratios=(1.0, max(panel_b_units / 2.2, 8.0)),
        left=0.285,
        right=0.955,
        top=0.875,
        bottom=0.075,
        hspace=0.28,
    )
    ax_overall = fig.add_subplot(grid[0])
    ax_signs = fig.add_subplot(grid[1])

    fig.text(
        0.06,
        0.975,
        "Oracle-selected trajectories combine complementary experts",
        fontsize=16.5,
        fontweight="bold",
        ha="left",
        va="top",
    )
    fig.text(
        0.06,
        0.948,
        "Expert provenance of top-2 trajectories selected for training",
        fontsize=10.2,
        color="#5E5C57",
        ha="left",
        va="top",
    )
    fig.text(
        0.06,
        0.912,
        f"{grand_total:,} selected trajectories across {len(data)} scenarios",
        fontsize=10.5,
        fontweight="bold",
        color="#272725",
        ha="left",
        va="center",
    )
    fig.text(
        0.94,
        0.912,
        "4 / 4 experts contribute to every scenario",
        fontsize=9.2,
        color="#5E5C57",
        ha="right",
        va="center",
    )

    handles = [Patch(facecolor=COLORS[expert], label=expert) for expert in EXPERTS]
    fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.62, 0.895),
        ncol=4,
        frameon=False,
        columnspacing=1.6,
        handlelength=1.45,
        handleheight=0.75,
        fontsize=9.0,
    )

    add_stacked_bar(
        ax_overall,
        0,
        overall_pct,
        height=0.58,
        detailed_labels=True,
    )
    ax_overall.set_xlim(0, 100)
    ax_overall.set_ylim(-0.52, 0.52)
    ax_overall.set_yticks([])
    ax_overall.set_xticks([])
    ax_overall.set_title(
        r"$\bf{a}$  Overall composition",
        loc="left",
        pad=8,
        fontweight="normal",
    )
    for spine in ax_overall.spines.values():
        spine.set_visible(False)

    positions: list[float] = []
    group_starts: dict[str, float] = {}
    y = 0.0
    previous_group: str | None = None
    for item in data:
        if previous_group is not None and item.group != previous_group:
            y += 0.85
        if item.group not in group_starts:
            group_starts[item.group] = y
        positions.append(y)
        percentages = {expert: item.percentage(expert) for expert in EXPERTS}
        add_stacked_bar(
            ax_signs,
            y,
            percentages,
            height=0.64,
            detailed_labels=False,
        )
        ax_signs.text(
            101.4,
            y,
            f"n={item.total:,}",
            ha="left",
            va="center",
            fontsize=6.8,
            color="#77746E",
            clip_on=False,
        )
        previous_group = item.group
        y += 1.0

    ax_signs.set_xlim(0, 100)
    ax_signs.set_ylim(positions[-1] + 0.65, -0.95)
    ax_signs.set_yticks(positions, [item.label for item in data])
    ax_signs.tick_params(axis="y", length=0, pad=7, labelsize=8.0)
    ax_signs.set_xticks((0, 25, 50, 75, 100), ("0", "25", "50", "75", "100"))
    ax_signs.set_xlabel("Share of selected top-2 trajectories (%)", labelpad=7)
    ax_signs.xaxis.grid(True, color="#DEDDD9", linewidth=0.65)
    ax_signs.set_title(
        r"$\bf{b}$  Composition by scenario type",
        loc="left",
        pad=14,
        fontweight="normal",
    )
    ax_signs.spines["top"].set_visible(False)
    ax_signs.spines["right"].set_visible(False)
    ax_signs.spines["left"].set_visible(False)

    for group, start in group_starts.items():
        ax_signs.text(
            -0.31,
            start - 0.53,
            group.upper(),
            transform=ax_signs.get_yaxis_transform(),
            ha="left",
            va="bottom",
            fontsize=7.0,
            fontweight="bold",
            color="#77746E",
            clip_on=False,
        )

    fig.text(
        0.06,
        0.038,
        "IDM aggregates the default policy and four parameter variants. "
        "Each row is normalized by its oracle-selected trajectory count.",
        fontsize=7.4,
        color="#5E5C57",
        ha="left",
        va="bottom",
    )
    fig.text(
        0.06,
        0.018,
        "Source: trajectories/*/final/oracle_metrics and trajectories_v6/*/oracle_metrics",
        fontsize=7.0,
        color="#77746E",
        ha="left",
        va="bottom",
    )

    png_path = output_dir / "oracle_expert_diversity.png"
    pdf_path = output_dir / "oracle_expert_diversity.pdf"
    fig.savefig(
        png_path,
        dpi=600,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.08,
        metadata={"Title": "Oracle-selected trajectory expert composition"},
    )
    fig.savefig(
        pdf_path,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.08,
        metadata={
            "Title": "Oracle-selected trajectory expert composition",
            "Creator": "TrafficRuleBench plotting script",
        },
    )
    plt.close(fig)
    return png_path, pdf_path


def main() -> None:
    args = parse_args()
    data = load_data(args.trajectory_roots)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    tsv_path = args.output_dir / "oracle_expert_diversity.tsv"
    write_aggregated_tsv(data, tsv_path)
    png_path, pdf_path = make_figure(data, args.output_dir)
    print(f"Wrote {png_path}")
    print(f"Wrote {pdf_path}")
    print(f"Wrote {tsv_path}")
    totals = {expert: sum(item.counts[expert] for item in data) for expert in EXPERTS}
    grand = sum(totals.values())
    print(f"Scenarios: {len(data)}")
    print(f"Total selected: {grand}")
    for expert in EXPERTS:
        print(f"  {expert}: {totals[expert]} ({100 * totals[expert] / grand:.1f}%)")


if __name__ == "__main__":
    main()
