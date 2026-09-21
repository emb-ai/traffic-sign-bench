#!/usr/bin/env python3
"""Plot nuPlan and TrafficSignBench IDM parameter distributions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from scipy.stats import gaussian_kde


COLORS = {
    "nuPlan": "#A1CB35",
    "TrafficSignBench": "#D5A33F",
}


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=repo_root / "data" / "runs",
        help="Directory containing generated-scene manifests.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root / "paper" / "imgs",
        help="Destination directory for the final PDF and PNG.",
    )
    return parser.parse_args()


def set_plot_style() -> None:
    """Configure compact, publication-ready typography."""
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIXGeneral", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 9.5,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "axes.edgecolor": "#AAA8A3",
            "axes.linewidth": 0.75,
            "axes.axisbelow": True,
            "xtick.color": "#4B4A47",
            "ytick.color": "#4B4A47",
            "text.color": "#292826",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def load_generated_parameters(runs_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    """Read IDM acceleration and following-distance values from all manifests."""
    acceleration: list[float] = []
    following_distance: list[float] = []

    for manifest in sorted(runs_dir.glob("*/**/real_manifest.jsonl")):
        with manifest.open(encoding="utf-8") as stream:
            for line in stream:
                record = json.loads(line)
                acc = record.get("profile_ACC_FACTOR")
                distance = record.get("profile_DISTANCE_WANTED")
                if acc is not None and np.isfinite(acc):
                    acceleration.append(float(acc))
                if distance is not None and np.isfinite(distance):
                    following_distance.append(float(distance))

    if not acceleration or not following_distance:
        raise ValueError(f"No IDM parameters found under {runs_dir}")
    return np.asarray(acceleration), np.asarray(following_distance)


def load_nuplan_parameters(repo_root: Path) -> tuple[np.ndarray, np.ndarray]:
    stats_dir = (
        repo_root
        / "traffic_bench"
        / "eval"
        / "engine"
        / "traffic"
        / "nuplan_statistics"
    )
    acceleration = pd.read_csv(stats_dir / "acc_pos.csv.gz", usecols=["acceleration"])[
        "acceleration"
    ].dropna().to_numpy()
    following_distance = pd.read_csv(
        stats_dir / "following.csv.gz", usecols=["following_distance"]
    )["following_distance"].dropna().to_numpy()
    return acceleration, following_distance


def _plot_kde(
    ax: mpl.axes.Axes,
    values: np.ndarray,
    *,
    lower: float,
    upper: float,
    color: str,
) -> None:
    if values.size < 50:
        return
    rng = np.random.default_rng(2026)
    sample = (
        values
        if values.size <= 50000
        else rng.choice(values, 50000, replace=False)
    )
    kde = gaussian_kde(sample, bw_method="scott")
    x = np.linspace(lower, upper, 500)
    density = kde(x)
    ax.fill_between(x, density, color=color, alpha=0.065, linewidth=0, zorder=3)
    ax.plot(
        x,
        density,
        color=color,
        linewidth=2.25,
        solid_capstyle="round",
        zorder=5,
    )


def _plot_histogram(
    ax: mpl.axes.Axes,
    values: np.ndarray,
    *,
    bins: np.ndarray,
    color: str,
) -> None:
    density, edges = np.histogram(values, bins=bins, density=True)
    ax.stairs(
        density,
        edges,
        fill=True,
        facecolor=color,
        edgecolor="none",
        alpha=0.20,
        zorder=1,
    )
    ax.stairs(
        density,
        edges,
        fill=False,
        color=color,
        linewidth=0.75,
        alpha=0.58,
        zorder=2,
    )


def plot_distribution(
    ax: mpl.axes.Axes,
    nuplan: np.ndarray,
    benchmark: np.ndarray,
    *,
    bins: np.ndarray,
    xlabel: str,
    title: str,
) -> None:
    lower, upper = bins[0], bins[-1]
    nuplan = nuplan[(nuplan >= lower) & (nuplan <= upper)]
    benchmark = benchmark[(benchmark >= lower) & (benchmark <= upper)]

    _plot_histogram(
        ax,
        nuplan,
        bins=bins,
        color=COLORS["nuPlan"],
    )
    _plot_histogram(
        ax,
        benchmark,
        bins=bins,
        color=COLORS["TrafficSignBench"],
    )

    _plot_kde(ax, nuplan, lower=lower, upper=upper, color=COLORS["nuPlan"])
    _plot_kde(
        ax,
        benchmark,
        lower=lower,
        upper=upper,
        color=COLORS["TrafficSignBench"],
    )

    ax.set_title(title, loc="left", pad=7, fontweight="semibold")
    ax.set_xlabel(xlabel, labelpad=4)
    ax.set_ylabel("Density", labelpad=4)
    ax.set_xlim(lower, upper)
    ax.margins(y=0.06)
    ax.yaxis.grid(True, color="#DFDED9", linewidth=0.6, alpha=0.9)
    ax.xaxis.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(width=0.7, length=3.2)

    legend_handles = [
        Line2D(
            [0],
            [0],
            color=COLORS[name],
            linewidth=2.2,
            solid_capstyle="round",
            label=name,
        )
        for name in ("nuPlan", "TrafficSignBench")
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper right",
        frameon=True,
        fancybox=False,
        edgecolor="#DEDDD9",
        framealpha=0.92,
        fontsize=8.0,
        handlelength=1.4,
        borderpad=0.35,
        labelspacing=0.25,
    )


def save_figure(fig: mpl.figure.Figure, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = "idm_nuplan_distributions"
    metadata = {
        "Title": "IDM parameter distributions: nuPlan and TrafficSignBench",
        "Creator": "TrafficRuleBench plotting script",
    }
    fig.savefig(
        output_dir / f"{stem}.png",
        dpi=600,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.05,
        metadata={"Title": metadata["Title"]},
    )
    fig.savefig(
        output_dir / f"{stem}.pdf",
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.05,
        metadata=metadata,
    )
    plt.close(fig)


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    set_plot_style()

    generated_acc, generated_follow = load_generated_parameters(args.runs_dir)
    nuplan_acc, nuplan_follow = load_nuplan_parameters(repo_root)

    fig, axes = plt.subplots(1, 2, figsize=(4.9, 2.5), facecolor="white")
    fig.subplots_adjust(left=0.11, right=0.99, bottom=0.16, top=0.90, wspace=0.32)

    plot_distribution(
        axes[0],
        nuplan_acc,
        generated_acc,
        bins=np.linspace(0.0, 4.0, 26),
        xlabel=r"Acceleration ($\mathrm{m\,s^{-2}}$)",
        title="(a) IDM acceleration",
    )
    plot_distribution(
        axes[1],
        nuplan_follow,
        generated_follow,
        bins=np.linspace(0.0, 40.0, 26),
        xlabel="Following distance (m)",
        title="(b) IDM following distance",
    )

    save_figure(fig, args.output_dir)
    print(f"Wrote {args.output_dir / 'idm_nuplan_distributions.pdf'}")
    print(f"Wrote {args.output_dir / 'idm_nuplan_distributions.png'}")


if __name__ == "__main__":
    main()
