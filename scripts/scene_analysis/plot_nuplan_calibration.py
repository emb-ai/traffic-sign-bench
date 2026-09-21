#!/usr/bin/env python3
"""Render the main-text nuPlan calibration figure from generation manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


NUPLAN_COLOR = "#90B800"
BENCH_COLOR = "#FFB900"


def parse_args() -> argparse.Namespace:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=repo)
    parser.add_argument("--output-dir", type=Path, default=repo / "paper" / "imgs")
    return parser.parse_args()


def set_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIXGeneral", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 8.2,
            "axes.labelsize": 8.4,
            "axes.titlesize": 8.8,
            "axes.edgecolor": "#A5A39E",
            "axes.linewidth": 0.7,
            "axes.axisbelow": True,
            "xtick.color": "#454440",
            "ytick.color": "#454440",
            "text.color": "#292826",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def load_generated(runs_dir: Path) -> tuple[dict[str, np.ndarray], int]:
    records: list[dict[str, object]] = []
    for sign_dir in sorted(runs_dir.iterdir()):
        if not sign_dir.is_dir() or sign_dir.name.startswith("_"):
            continue
        for split in ("train", "test"):
            manifest = sign_dir / split / "real_manifest.jsonl"
            if not manifest.is_file():
                continue
            with manifest.open(encoding="utf-8") as stream:
                records.extend(json.loads(line) for line in stream)

    def values(field: str) -> np.ndarray:
        return np.asarray(
            [
                float(record[field])
                for record in records
                if record.get(field) is not None
                and np.isfinite(float(record[field]))
            ],
            dtype=float,
        )

    data = {
        "density": values("nuplan_vehicles_per_frame"),
        "speed": values("spawn_velocity_ms"),
        "acceleration": values("profile_ACC_FACTOR"),
        "deceleration": values("profile_DEACC_FACTOR"),
    }
    if any(array.size == 0 for array in data.values()):
        missing = [name for name, array in data.items() if array.size == 0]
        raise ValueError(f"Missing generated calibration fields: {missing}")
    return data, len(records)


def load_nuplan(stats_dir: Path) -> dict[str, np.ndarray]:
    return {
        "density": pd.read_csv(stats_dir / "densities.csv.gz", usecols=["count_r150"])[
            "count_r150"
        ].dropna().to_numpy(dtype=float),
        "speed": pd.read_csv(stats_dir / "routes.csv.gz", usecols=["initial_speed"])[
            "initial_speed"
        ].dropna().to_numpy(dtype=float),
        "acceleration": pd.read_csv(
            stats_dir / "acc_pos.csv.gz", usecols=["acceleration"]
        )["acceleration"].dropna().to_numpy(dtype=float),
        "deceleration": pd.read_csv(
            stats_dir / "acc_neg.csv.gz", usecols=["deceleration"]
        )["deceleration"].dropna().to_numpy(dtype=float),
    }


def ks_statistic(left: np.ndarray, right: np.ndarray) -> float:
    left = np.sort(np.asarray(left, dtype=float))
    right = np.sort(np.asarray(right, dtype=float))
    support = np.sort(np.unique(np.concatenate((left, right))))
    left_cdf = np.searchsorted(left, support, side="right") / left.size
    right_cdf = np.searchsorted(right, support, side="right") / right.size
    return float(np.max(np.abs(left_cdf - right_cdf)))


def ecdf_points(values: np.ndarray, max_points: int = 6000) -> tuple[np.ndarray, np.ndarray]:
    ordered = np.sort(values)
    if ordered.size <= max_points:
        indices = np.arange(ordered.size)
    else:
        indices = np.unique(np.linspace(0, ordered.size - 1, max_points).astype(int))
    return ordered[indices], (indices + 1) / ordered.size


def dominant_probe_values(values: np.ndarray, count: int = 3) -> np.ndarray:
    """Return the most frequently used discrete probes, ordered by value."""
    unique, counts = np.unique(np.asarray(values, dtype=float), return_counts=True)
    if unique.size < count:
        raise ValueError(f"Expected at least {count} probe values, found {unique.size}")
    selected = np.argsort(counts)[-count:]
    return np.sort(unique[selected])


def draw_panel(
    ax: mpl.axes.Axes,
    reference: np.ndarray,
    generated: np.ndarray,
    *,
    title: str,
    xlabel: str,
    xlim: tuple[float, float],
    clipping: tuple[float, float] | None,
    probe_labels: tuple[str, str, str] | None = None,
) -> float:
    target = np.clip(reference, *clipping) if clipping else reference
    statistic = ks_statistic(target, generated)

    target_x, target_y = ecdf_points(target)
    ax.plot(target_x, target_y, color=NUPLAN_COLOR, lw=1.8, label="nuPlan")

    if probe_labels:
        probes = dominant_probe_values(generated)
        for index, (value, label) in enumerate(zip(probes, probe_labels)):
            ax.axvline(
                value,
                color=BENCH_COLOR,
                lw=1.35,
                ls=(0, (3, 2)),
                alpha=0.95,
                zorder=2,
            )
            # low left of its cut, mid/high right of theirs; same vertical level
            horizontal_alignment = "right" if index == 0 else "left"
            x_offset = -4 if index == 0 else 4
            ax.annotate(
                label,
                xy=(value, 0.90),
                xycoords=("data", "axes fraction"),
                xytext=(x_offset, 0),
                textcoords="offset points",
                ha=horizontal_alignment,
                va="center",
                fontsize=6.8,
                color="#8B671D",
                fontweight="semibold",
                clip_on=False,
                bbox={
                    "facecolor": "white",
                    "edgecolor": "none",
                    "pad": 0.6,
                    "alpha": 0.92,
                },
            )
    else:
        generated_x, generated_y = ecdf_points(generated)
        ax.plot(
            generated_x,
            generated_y,
            color=BENCH_COLOR,
            lw=1.5,
            ls=(0, (3, 2)),
            label="TrafficSignBench",
        )

    ax.set_xlim(*xlim)
    ax.set_ylim(0, 1.02)
    ax.set_title(title, loc="left", pad=4, fontweight="semibold")
    ax.set_xlabel(xlabel)
    ax.grid(True, color="#E7E6E1", lw=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.text(
        0.97,
        0.06,
        f"$D={statistic:.3f}$",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7.0,
        bbox={"facecolor": "white", "edgecolor": "#D1D0CB", "pad": 1.7, "alpha": 0.88},
    )
    return statistic


def render(repo: Path, output_dir: Path) -> None:
    generated, manifest_count = load_generated(repo / "data" / "runs")
    reference = load_nuplan(
        repo / "traffic_bench" / "eval" / "engine" / "traffic" / "nuplan_statistics"
    )
    specs = (
        (
            "density",
            "(a) Traffic density",
            r"$n_{\mathrm{vehicles}}$ (r = 150 m)",
            (0.0, 70.0),
            None,
            ("low", "mid", "high"),
        ),
        (
            "speed",
            "(b) Initial ego speed",
            r"Speed ($\mathrm{m\,s^{-1}}$)",
            (0.0, 18.0),
            None,
            ("low", "mid", "high"),
        ),
        (
            "acceleration",
            "(c) IDM acceleration",
            r"Acceleration ($\mathrm{m\,s^{-2}}$)",
            (0.0, 4.0),
            (0.2, 4.0),
            None,
        ),
        (
            "deceleration",
            "(d) IDM deceleration",
            r"Deceleration ($\mathrm{m\,s^{-2}}$)",
            (0.0, 5.0),
            (0.2, 5.0),
            None,
        ),
    )

    set_style()
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
    axes = axes_grid.ravel()
    statistics = {}
    for axis, (key, title, xlabel, xlim, clipping, probe_labels) in zip(axes, specs):
        statistics[key] = draw_panel(
            axis,
            reference[key],
            generated[key],
            title=title,
            xlabel=xlabel,
            xlim=xlim,
            clipping=clipping,
            probe_labels=probe_labels,
        )
    axes[0].set_ylabel("Empirical CDF")
    axes[2].set_ylabel("Empirical CDF")
    figure.legend(
        handles=[
            Line2D([0], [0], color=NUPLAN_COLOR, lw=1.8, label="nuPlan"),
            Line2D(
                [0],
                [0],
                color=BENCH_COLOR,
                lw=1.8,
                ls=(0, (3, 2)),
                label="TrafficSignBench",
            ),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.98),
        ncol=2,
        frameon=False,
        fontsize=8,
        handlelength=1.8,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "Title": "TrafficSignBench calibration against nuPlan",
        "Creator": "scripts/scene_analysis/plot_nuplan_calibration.py",
    }
    for extension, kwargs in (
        ("png", {"dpi": 450, "metadata": {"Title": metadata["Title"]}}),
        ("pdf", {"metadata": metadata}),
    ):
        figure.savefig(
            output_dir / f"nuplan_stats.{extension}",
            facecolor="white",
            bbox_inches="tight",
            pad_inches=0.03,
            **kwargs,
        )
    plt.close(figure)
    print(f"Loaded {manifest_count:,} generation manifests")
    print("KS:", " ".join(f"{key}={value:.3f}" for key, value in statistics.items()))
    print(f"Wrote {output_dir / 'nuplan_stats.pdf'}")


def main() -> None:
    args = parse_args()
    render(args.repo, args.output_dir)


if __name__ == "__main__":
    main()
