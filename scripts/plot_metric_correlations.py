#!/usr/bin/env python3
"""Plot conventional-metric correlations with grouped SR&Dest."""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle


@dataclass(frozen=True)
class Metric:
    key: str
    label: str


@dataclass(frozen=True)
class Scope:
    key: str
    label: str


@dataclass(frozen=True)
class Cohort:
    label: str
    kinds: frozenset[str]


METRICS = (
    Metric("driving_score", "DS"),
    Metric("route_completion", "RC"),
    Metric("efficiency", "Eff."),
    Metric("comfort", "Comf."),
)

SCOPES = (
    Scope("sr_dest_overall", "Overall"),
    Scope("sr_dest_priority", "Priority"),
    Scope("sr_dest_speed", "Speed"),
    Scope("sr_dest_obstacle", "Obstacle"),
    Scope("sr_dest_rerouting", "Rerouting"),
)

COHORTS = (
    Cohort("Standard baselines + PlanT-2-FT", frozenset({"base", "ours"})),
)


def parse_args() -> argparse.Namespace:
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=repo / "data" / "icra27_results" / "main_table_metrics.tsv",
        help="Planner-level metrics produced by build_icra_results.py.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo / "paper" / "imgs",
    )
    parser.add_argument(
        "--matrix-output",
        type=Path,
        default=repo
        / "data"
        / "icra27_results"
        / "metric_correlation_matrix.tsv",
    )
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))

    required = {
        "policy_key",
        "kind",
        *(metric.key for metric in METRICS),
        *(scope.key for scope in SCOPES),
    }
    missing = required - set(rows[0]) if rows else required
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")

    for row in rows:
        for field in (
            *(metric.key for metric in METRICS),
            *(scope.key for scope in SCOPES),
        ):
            value = float(row[field])
            if not math.isfinite(value):
                raise ValueError(f"Non-finite {field!r} for {row['policy_key']}")
    return rows


def select_cohort(
    rows: list[dict[str, str]],
    cohort: Cohort,
) -> list[dict[str, str]]:
    selected = [row for row in rows if row["kind"] in cohort.kinds]
    if len(selected) != 9 or len({row["policy_key"] for row in selected}) != 9:
        raise ValueError(
            f"{cohort.label}: expected nine unique configurations, "
            f"found {len(selected)} rows"
        )
    return selected


def rankdata(values: Iterable[float]) -> np.ndarray:
    """Return average ranks, including correct handling of tied values."""
    values = np.asarray(list(values), dtype=float)
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    start = 0
    while start < len(values):
        stop = start + 1
        while stop < len(values) and values[order[stop]] == values[order[start]]:
            stop += 1
        ranks[order[start:stop]] = 0.5 * (start + stop - 1) + 1.0
        start = stop
    return ranks


def spearman(x: Iterable[float], y: Iterable[float]) -> float:
    """Compute Spearman's rho as Pearson correlation of average ranks."""
    return float(np.corrcoef(rankdata(x), rankdata(y))[0, 1])


def correlation_matrix(
    rows: list[dict[str, str]],
) -> np.ndarray:
    matrix = np.empty((len(METRICS), len(SCOPES)), dtype=float)
    for metric_index, metric in enumerate(METRICS):
        for scope_index, scope in enumerate(SCOPES):
            matrix[metric_index, scope_index] = spearman(
                [float(row[metric.key]) for row in rows],
                [float(row[scope.key]) for row in rows],
            )
    return matrix


def write_matrix(
    path: Path,
    matrices: list[tuple[Cohort, np.ndarray]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(
            [
                "cohort",
                "conventional_metric",
                *(f"SR&Dest {scope.label}" for scope in SCOPES),
            ]
        )
        for cohort, matrix in matrices:
            for metric, values in zip(METRICS, matrix):
                writer.writerow(
                    [
                        cohort.label,
                        metric.label,
                        *(f"{value:.6f}" for value in values),
                    ]
                )


def set_plot_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIXGeneral", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 8.2,
            "axes.edgecolor": "#AAA9A5",
            "axes.linewidth": 0.6,
            "xtick.color": "#343431",
            "ytick.color": "#343431",
            "text.color": "#252522",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def annotation_color(value: float) -> str:
    return "white" if abs(value) >= 0.61 else "#292824"


def render_figure(
    matrices: list[tuple[Cohort, np.ndarray]],
    output_dir: Path,
) -> tuple[Path, Path]:
    set_plot_style()
    cmap = LinearSegmentedColormap.from_list(
        "metric_alignment",
        (
            "#30AFFF",
            "#B9E3FA",
            "#F7F7F5",
            "#E7A4A4",
            "#DA4848",
        ),
    )

    figure = plt.figure(figsize=(3.55, 1.9), facecolor="white")
    grid = figure.add_gridspec(
        1,
        2,
        width_ratios=(20, 0.9),
        left=0.15,
        right=0.95,
        bottom=0.08,
        top=0.79,
        wspace=0.10,
    )
    axes = [figure.add_subplot(grid[0, 0])]
    color_ax = figure.add_subplot(grid[0, 1])
    image = None

    for panel_index, (ax, (cohort, matrix)) in enumerate(
        zip(axes, matrices)
    ):
        image = ax.imshow(
            matrix,
            vmin=-1.0,
            vmax=1.0,
            cmap=cmap,
            interpolation="nearest",
            aspect="auto",
        )
        ax.set_xticks(
            range(len(SCOPES)),
            [scope.label for scope in SCOPES],
        )
        ax.set_yticks(
            range(len(METRICS)),
            [metric.label for metric in METRICS],
        )
        ax.xaxis.tick_top()
        ax.tick_params(axis="x", length=0, pad=7, labelsize=8.3)
        ax.tick_params(axis="y", length=0, pad=6, labelsize=8.3)
        ax.get_xticklabels()[0].set_fontweight("bold")

        ax.set_xticks(np.arange(-0.5, len(SCOPES), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(METRICS), 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.25)
        ax.tick_params(
            which="minor",
            bottom=False,
            left=False,
            top=False,
            right=False,
        )

        for row in range(len(METRICS)):
            for column in range(len(SCOPES)):
                value = matrix[row, column]
                ax.text(
                    column,
                    row,
                    f"{value:+.2f}".replace("-", "−"),
                    ha="center",
                    va="center",
                    fontsize=8,
                    fontweight=(
                        "semibold"
                        if panel_index == 0 and column == 0
                        else "normal"
                    ),
                    color=annotation_color(value),
                    zorder=3,
                )

        if panel_index == 0:
            ax.axvline(0.5, color="#777671", linewidth=0.75, zorder=4)
            ax.add_patch(
                Rectangle(
                    (-0.47, -0.47),
                    0.94,
                    len(METRICS) - 0.06,
                    fill=False,
                    edgecolor="#5F5E5A",
                    linewidth=0.8,
                    zorder=4,
                )
            )
        for spine in ax.spines.values():
            spine.set_visible(False)

    if image is None:
        raise ValueError("At least one correlation matrix is required")
    colorbar = figure.colorbar(image, cax=color_ax, orientation="vertical")
    colorbar.set_ticks((-1, -0.5, 0, 0.5, 1))
    colorbar.ax.tick_params(labelsize=7.0, length=2.2, width=0.5, pad=2)
    colorbar.set_label(r"Spearman $\rho$", fontsize=7.7, labelpad=4)
    colorbar.outline.set_linewidth(0.5)
    colorbar.outline.set_edgecolor("#AAA9A5")

    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / "metric_correlation_analysis.png"
    pdf_path = output_dir / "metric_correlation_analysis.pdf"
    title = "Conventional-metric correlation with grouped SR&Dest"
    figure.savefig(
        png_path,
        dpi=600,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.035,
        metadata={"Title": title},
    )
    figure.savefig(
        pdf_path,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.035,
        metadata={
            "Title": title,
            "Creator": "TrafficRuleBench metric-correlation plotting script",
        },
    )
    plt.close(figure)
    return png_path, pdf_path


def render_tex(path: Path) -> None:
    text = r"""\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{imgs/metric_correlation_analysis.pdf}
\end{figure}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = read_rows(args.input)
    matrices = [
        (cohort, correlation_matrix(select_cohort(rows, cohort)))
        for cohort in COHORTS
    ]
    write_matrix(args.matrix_output, matrices)
    figure_paths = render_figure(matrices, args.output_dir)
    tex_path = args.output_dir / "metric_correlation_analysis.tex"
    render_tex(tex_path)
    for path in (*figure_paths, tex_path, args.matrix_output):
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
