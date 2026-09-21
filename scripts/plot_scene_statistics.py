#!/usr/bin/env python3
"""Build paper-grade statistical figures for generated benchmark scenes.

The analysis deliberately distinguishes three statistical units:

* source-pool maps (the harvested OSM inventory);
* sign-map allocations (one physical map assigned to one sign and split);
* scenario rows (correlated augmentations nested within a sign-map).

Run from anywhere:

    python scripts/plot_scene_statistics.py

The default canonical manifest combines this checkout's ``data/runs`` with the
seven completed corridor families in Smirnova's ``data/runs_v7``. Debug
manifests and the separate restricted-lane extension are excluded.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


# Colorblind-safe, print-friendly palette (Okabe-Ito plus neutral tones).
BLUE = "#0072B2"
ORANGE = "#E69F00"
GREEN = "#009E73"
VERMILLION = "#D55E00"
PURPLE = "#CC79A7"
SKY = "#56B4E9"
YELLOW = "#F0E442"
INK = "#202124"
MID = "#63666A"
LIGHT = "#D9DADD"
PALE = "#F2F3F4"

FAMILY_COLORS = {
    "Junction": BLUE,
    "Dual-path": VERMILLION,
    "Corridor": GREEN,
}
SPLIT_COLORS = {"train": BLUE, "test": ORANGE}
SUBTYPE_COLORS = {
    "T": BLUE,
    "X": ORANGE,
    "O": GREEN,
    "straight": PURPLE,
    "curved": SKY,
}
HIERARCHY_COLORS = {
    "Sign family / task": PURPLE,
    "Map within sign": ORANGE,
    "Augmentation within map": GREEN,
}


@dataclass(frozen=True)
class SignSpec:
    sign_id: str
    code: str
    label: str
    paper_group: str
    map_family: str
    expected_speed_levels: int | None


SIGN_SPECS: tuple[SignSpec, ...] = (
    SignSpec("main_road", "2.1", "Main road", "Priority", "Junction", 1),
    SignSpec("secondary_road", "2.3", "Secondary road", "Priority", "Junction", 1),
    SignSpec("yield", "2.4", "Yield", "Priority", "Junction", 1),
    SignSpec("stop", "2.5", "Stop", "Priority", "Junction", 1),
    SignSpec("roundabout", "4.3", "Roundabout", "Priority", "Junction", 1),
    SignSpec("crosswalk", "5.19", "Crosswalk", "Priority", "Corridor", 3),
    SignSpec("speed_limit", "3.24", "Speed limit", "Speed", "Corridor", None),
    SignSpec("min_speed", "4.6", "Minimum speed", "Speed", "Corridor", None),
    SignSpec("residential_zone", "5.21", "Residential zone", "Speed", "Corridor", None),
    SignSpec("zone_speed_limit", "5.31", "Zone speed limit", "Speed", "Corridor", None),
    SignSpec("blocked_road", "3.2", "Movement prohibited", "Detour", "Junction", 3),
    SignSpec("detour_left", "4.2.2", "Pass obstacle left", "Detour", "Corridor", 3),
    SignSpec("detour_right", "4.2.1", "Pass obstacle right", "Detour", "Corridor", 3),
    SignSpec("detour_either", "4.2.3", "Pass either side", "Detour", "Corridor", 3),
    SignSpec("no_entry", "3.1", "No entry", "Directional control", "Dual-path", 3),
    SignSpec("no_turn_left", "3.18.2", "No left turn", "Directional control", "Dual-path", 3),
    SignSpec("no_turn_right", "3.18.1", "No right turn", "Directional control", "Dual-path", 3),
    SignSpec("direction_straight", "4.1.1", "Straight only", "Directional control", "Dual-path", 3),
    SignSpec("direction_right", "4.1.2", "Right only", "Directional control", "Dual-path", 3),
    SignSpec("direction_left", "4.1.3", "Left only", "Directional control", "Dual-path", 3),
    SignSpec(
        "direction_straight_right",
        "4.1.4",
        "Straight or right",
        "Directional control",
        "Dual-path",
        3,
    ),
    SignSpec(
        "direction_straight_left",
        "4.1.5",
        "Straight or left",
        "Directional control",
        "Dual-path",
        3,
    ),
    SignSpec(
        "direction_left_right",
        "4.1.6",
        "Left or right",
        "Directional control",
        "Dual-path",
        3,
    ),
    SignSpec("one_way_right", "5.7.1", "One way — right", "Directional control", "Dual-path", 3),
    SignSpec("one_way_left", "5.7.2", "One way — left", "Directional control", "Dual-path", 3),
)

SPECS_BY_ID = {spec.sign_id: spec for spec in SIGN_SPECS}
GROUP_ORDER = ("Priority", "Speed", "Detour", "Directional control")
POOL_INDEX_NAMES = {
    "Junction": "junctions.jsonl",
    "Dual-path": "dual_path_candidates.jsonl",
    "Corridor": "segments.jsonl",
}


@dataclass
class SceneDataset:
    rows: list[dict[str, Any]]
    maps: list[dict[str, Any]]
    pools: dict[str, list[dict[str, Any]]]
    manifest_paths: list[Path]
    density_calibration: dict[str, Any]
    nuplan_report: dict[str, Any]


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--extra-runs-root",
        type=Path,
        default=Path(
            "/home/jovyan/shares/SR006.nfs2/smirnova/"
            "traffic-rule-bench-main/data/runs_v7"
        ),
        help="Completed corridor-family manifests used with this checkout.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root / "paper" / "imgs",
        help="Destination for PDF, PNG, TSV, and JSON artifacts.",
    )
    parser.add_argument(
        "--strict-targets",
        action="store_true",
        help="Fail unless all 25 signs have exactly 80/20 maps and 10 scenarios/map.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def map_id(row: dict[str, Any]) -> str:
    return Path(str(row["net_path"])).parent.name


def place_id(row: dict[str, Any]) -> str:
    value = row.get("junction_id") or row.get("osm_way_id")
    return str(value) if value is not None else map_id(row)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def row_topology(row: dict[str, Any]) -> str:
    layout = row.get("junction_layout") or {}
    return str(layout.get("shape") or row.get("segment_type") or "unknown")


def resolve_manifest_root(repo_root: Path, extra_root: Path, sign_id: str) -> Path:
    local_root = repo_root / "data" / "runs"
    # Prefer the completed v7 versions where available. In particular this
    # replaces the one-augmentation local speed_limit snapshot.
    if (extra_root / sign_id).is_dir():
        return extra_root
    return local_root


def load_dataset(repo_root: Path, extra_root: Path) -> SceneDataset:
    rows: list[dict[str, Any]] = []
    paths: list[Path] = []
    missing: list[Path] = []

    for spec in SIGN_SPECS:
        root = resolve_manifest_root(repo_root, extra_root, spec.sign_id)
        for split in ("train", "test"):
            path = root / spec.sign_id / split / "real_manifest.jsonl"
            if not path.is_file():
                missing.append(path)
                continue
            paths.append(path)
            for row in read_jsonl(path):
                row["_sign_id"] = spec.sign_id
                row["_sign_label"] = spec.label
                row["_paper_group"] = spec.paper_group
                row["_map_family"] = spec.map_family
                row["_split"] = split
                row["_map_id"] = map_id(row)
                row["_place_id"] = place_id(row)
                rows.append(row)

    if missing:
        formatted = "\n  ".join(str(path) for path in missing)
        raise FileNotFoundError(f"Canonical manifests are incomplete. Missing:\n  {formatted}")

    representative: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["_sign_id"], row["_split"], row["_map_id"])
        if key not in representative or row.get("is_nominal", False):
            representative[key] = row
    maps = list(representative.values())

    index_root = repo_root / "traffic_bench" / "scene_collection" / "maps" / "index"
    pools = {
        family: read_jsonl(index_root / filename)
        for family, filename in POOL_INDEX_NAMES.items()
    }

    statistics_root = (
        repo_root
        / "traffic_bench"
        / "eval"
        / "engine"
        / "traffic"
        / "nuplan_statistics"
    )
    density_calibration = json.loads(
        (statistics_root / "density_calibration_sumo.json").read_text(encoding="utf-8")
    )
    nuplan_report = json.loads(
        (statistics_root / "statistics_report.json").read_text(encoding="utf-8")
    )
    return SceneDataset(
        rows=rows,
        maps=maps,
        pools=pools,
        manifest_paths=paths,
        density_calibration=density_calibration,
        nuplan_report=nuplan_report,
    )


def set_plot_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIXGeneral", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 8.2,
            "axes.titlesize": 9.2,
            "axes.labelsize": 8.2,
            "axes.edgecolor": MID,
            "axes.linewidth": 0.65,
            "axes.axisbelow": True,
            "xtick.labelsize": 7.2,
            "ytick.labelsize": 7.2,
            "xtick.color": MID,
            "ytick.color": INK,
            "text.color": INK,
            "legend.fontsize": 7.2,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )


def clean_axis(ax: mpl.axes.Axes, *, grid: str | None = None) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid == "x":
        ax.xaxis.grid(True, color=LIGHT, linewidth=0.55)
    elif grid == "y":
        ax.yaxis.grid(True, color=LIGHT, linewidth=0.55)


def panel_title(ax: mpl.axes.Axes, letter: str, title: str) -> None:
    ax.set_title(rf"$\bf{{{letter}}}$  {title}", loc="left", pad=6, fontweight="normal")


def save_figure(
    fig: mpl.figure.Figure,
    output_dir: Path,
    stem: str,
    title: str,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / f"{stem}.png"
    pdf_path = output_dir / f"{stem}.pdf"
    fig.savefig(
        png_path,
        dpi=600,
        bbox_inches="tight",
        pad_inches=0.055,
        metadata={"Title": title},
    )
    fig.savefig(
        pdf_path,
        bbox_inches="tight",
        pad_inches=0.055,
        metadata={
            "Title": title,
            "Creator": "TrafficRuleBench scene statistics",
        },
    )
    plt.close(fig)
    return png_path, pdf_path


def canonical_counts(data: SceneDataset) -> dict[str, Any]:
    train_places = {row["_place_id"] for row in data.maps if row["_split"] == "train"}
    test_places = {row["_place_id"] for row in data.maps if row["_split"] == "test"}
    scenario_counts = Counter((r["_sign_id"], r["_split"], r["_map_id"]) for r in data.rows)
    return {
        "signs": len({row["_sign_id"] for row in data.rows}),
        "scenarios": len(data.rows),
        "train_scenarios": sum(row["_split"] == "train" for row in data.rows),
        "test_scenarios": sum(row["_split"] == "test" for row in data.rows),
        "map_allocations": len(data.maps),
        "train_maps": sum(row["_split"] == "train" for row in data.maps),
        "test_maps": sum(row["_split"] == "test" for row in data.maps),
        "unique_places": len(train_places | test_places),
        "train_places": len(train_places),
        "test_places": len(test_places),
        "train_test_place_overlap": len(train_places & test_places),
        "complete_map_fraction": np.mean([count == 10 for count in scenario_counts.values()]),
        "source_pool_maps": sum(len(rows) for rows in data.pools.values()),
    }


def selected_unique_places(data: SceneDataset) -> list[dict[str, Any]]:
    selected: dict[tuple[str, str], dict[str, Any]] = {}
    for row in data.maps:
        key = (row["_split"], row["_place_id"])
        selected.setdefault(key, row)
    return list(selected.values())


def subtype_counts(
    rows: Iterable[dict[str, Any]],
    family: str,
    *,
    pool: bool,
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        if not pool and row["_map_family"] != family:
            continue
        if family in {"Junction", "Dual-path"}:
            subtype = str(row.get("shape") if pool else row_topology(row))
        else:
            subtype = str(row.get("segment_type") if pool else row_topology(row))
        counts[subtype] += 1
    return counts


def plot_geography(ax: mpl.axes.Axes, data: SceneDataset) -> None:
    places = selected_unique_places(data)
    for family in ("Junction", "Dual-path", "Corridor"):
        for split, marker, size, alpha in (
            ("train", "o", 6.5, 0.34),
            ("test", "o", 11.0, 0.85),
        ):
            points = [
                row
                for row in places
                if row["_map_family"] == family
                and row["_split"] == split
                and is_number(row.get("longitude"))
                and is_number(row.get("latitude"))
            ]
            if not points:
                continue
            xs = [float(row["longitude"]) for row in points]
            ys = [float(row["latitude"]) for row in points]
            if split == "train":
                ax.scatter(
                    xs,
                    ys,
                    s=size,
                    marker=marker,
                    color=FAMILY_COLORS[family],
                    alpha=alpha,
                    linewidths=0,
                    rasterized=True,
                )
            else:
                ax.scatter(
                    xs,
                    ys,
                    s=size,
                    marker=marker,
                    facecolors="none",
                    edgecolors=FAMILY_COLORS[family],
                    alpha=alpha,
                    linewidths=0.65,
                    rasterized=True,
                )
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_aspect(1.0 / math.cos(math.radians(55.7)))
    ax.tick_params(length=2.5)
    clean_axis(ax)
    panel_title(ax, "a", f"Geographic coverage ({len(places):,} unique places)")
    family_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="none",
            markerfacecolor=color,
            markeredgewidth=0,
            markersize=4.5,
            label=family,
        )
        for family, color in FAMILY_COLORS.items()
    ]
    family_handles.extend(
        (
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="none",
                markerfacecolor=MID,
                markeredgewidth=0,
                markersize=4.2,
                label="Train",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="none",
                markerfacecolor="none",
                markeredgecolor=MID,
                markersize=4.2,
                label="Test",
            ),
        )
    )
    ax.legend(
        handles=family_handles,
        loc="lower left",
        ncol=2,
        frameon=False,
        handletextpad=0.35,
        columnspacing=0.8,
        borderaxespad=0.2,
    )


def plot_selected_structure(ax: mpl.axes.Axes, data: SceneDataset) -> None:
    families = ("Junction", "Dual-path", "Corridor")
    subtype_orders = {
        "Junction": ("T", "X", "O"),
        "Dual-path": ("T", "X"),
        "Corridor": ("straight", "curved"),
    }
    for y, family in enumerate(families):
        counts = subtype_counts(data.maps, family, pool=False)
        total = sum(counts.values())
        left = 0.0
        for subtype in subtype_orders[family]:
            width = 100.0 * counts[subtype] / total if total else 0.0
            ax.barh(
                y,
                width,
                left=left,
                height=0.54,
                color=SUBTYPE_COLORS[subtype],
                edgecolor="white",
                linewidth=0.7,
            )
            if width >= 9:
                ax.text(
                    left + width / 2,
                    y,
                    f"{subtype}\n{width:.0f}%",
                    ha="center",
                    va="center",
                    fontsize=6.8,
                    color="white" if subtype not in {"X"} else INK,
                    fontweight="bold",
                    linespacing=0.85,
                )
            left += width
        ax.text(
            101.5,
            y,
            f"n={total:,}",
            va="center",
            ha="left",
            color=MID,
            fontsize=6.8,
            clip_on=False,
        )
    ax.set_xlim(0, 100)
    ax.set_yticks(range(len(families)), families)
    ax.invert_yaxis()
    ax.set_xticks((0, 25, 50, 75, 100))
    ax.set_xlabel("Share of sign–map allocations (%)")
    ax.tick_params(axis="y", length=0)
    clean_axis(ax, grid="x")
    panel_title(ax, "b", "Structural coverage of evaluated maps")


def speed_density_matrix(data: SceneDataset) -> tuple[np.ndarray, int]:
    per_map: dict[tuple[str, str, str], np.ndarray] = {}
    for row in data.rows:
        if row.get("is_nominal", False):
            continue
        if SPECS_BY_ID[row["_sign_id"]].expected_speed_levels != 3:
            continue
        density = row.get("density_level_id")
        speed = row.get("spawn_velocity_level_id")
        if density not in (0, 1, 2) or speed not in (0, 1, 2):
            continue
        key = (row["_sign_id"], row["_split"], row["_map_id"])
        per_map.setdefault(key, np.zeros((3, 3), dtype=float))
        per_map[key][int(density), int(speed)] += 1
    normalized = []
    for matrix in per_map.values():
        if matrix.sum() > 0:
            normalized.append(matrix / matrix.sum())
    if not normalized:
        raise ValueError("No maps expose both density and ego-speed probe levels.")
    return 100.0 * np.mean(normalized, axis=0), len(normalized)


def plot_speed_density_heatmap(
    ax: mpl.axes.Axes,
    data: SceneDataset,
    *,
    letter: str,
    title: str,
) -> None:
    matrix, n_maps = speed_density_matrix(data)
    expected = 100.0 / 9.0
    deviation = matrix - expected
    vmax = max(2.0, float(np.max(np.abs(deviation))))
    image = ax.imshow(
        deviation,
        cmap="RdBu_r",
        vmin=-vmax,
        vmax=vmax,
        aspect="auto",
        interpolation="nearest",
    )
    for row in range(3):
        for col in range(3):
            ax.text(
                col,
                row,
                f"{matrix[row, col]:.1f}%",
                ha="center",
                va="center",
                fontsize=7.2,
                color=INK,
                fontweight="bold",
            )
    ax.set_xticks((0, 1, 2), ("p25\n3.61", "p50\n7.75", "p75\n11.05"))
    ax.set_yticks((0, 1, 2), ("p25\nsparse", "p50\ntypical", "p75\ndense"))
    ax.set_xlabel("Initial ego-speed probe (m/s)")
    ax.set_ylabel("Traffic-density probe")
    ax.tick_params(length=0)
    panel_title(ax, letter, f"{title} (map-weighted, n={n_maps:,})")
    colorbar = ax.figure.colorbar(image, ax=ax, fraction=0.045, pad=0.025)
    colorbar.set_label("Deviation from uniform grid (pp)", fontsize=7.0)
    colorbar.ax.tick_params(labelsize=6.5)


def variance_decomposition(
    data: SceneDataset,
    field: str,
) -> tuple[float, float, float, int]:
    values = [
        row
        for row in data.rows
        if not row.get("is_nominal", False) and is_number(row.get(field))
    ]
    if len(values) < 2:
        return 0.0, 0.0, 0.0, len(values)
    x = np.array([float(row[field]) for row in values])
    grand = float(x.mean())
    total = float(np.square(x - grand).sum())
    if total <= 0:
        return 0.0, 0.0, 0.0, len(values)

    by_sign: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_map: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in values:
        by_sign[row["_sign_id"]].append(row)
        by_map[(row["_sign_id"], row["_split"], row["_map_id"])].append(row)

    sign_means = {
        sign: float(np.mean([float(row[field]) for row in group]))
        for sign, group in by_sign.items()
    }
    ss_sign = sum(
        len(group) * (sign_means[sign] - grand) ** 2
        for sign, group in by_sign.items()
    )
    ss_map = 0.0
    ss_aug = 0.0
    for key, group in by_map.items():
        sign = key[0]
        map_values = np.array([float(row[field]) for row in group])
        map_mean = float(map_values.mean())
        ss_map += len(group) * (map_mean - sign_means[sign]) ** 2
        ss_aug += float(np.square(map_values - map_mean).sum())
    fractions = np.array([ss_sign, ss_map, ss_aug]) / total
    fractions = np.clip(fractions, 0.0, 1.0)
    fractions /= fractions.sum()
    return float(fractions[0]), float(fractions[1]), float(fractions[2]), len(values)


def plot_variance_decomposition(
    ax: mpl.axes.Axes,
    data: SceneDataset,
    *,
    letter: str,
    title: str,
    compact: bool = False,
) -> None:
    metrics = (
        ("spawn_velocity_ms", "Ego speed"),
        ("traffic_density", "Traffic density"),
        ("max_path_length_m", "Route budget"),
        ("profile_ACC_FACTOR", "NPC acceleration"),
        ("profile_DEACC_FACTOR", "NPC deceleration"),
        ("background_npc_count", "NPC count"),
    )
    hierarchy = tuple(HIERARCHY_COLORS)
    results = [variance_decomposition(data, field) for field, _ in metrics]
    for y, result in enumerate(results):
        left = 0.0
        for index, name in enumerate(hierarchy):
            width = 100.0 * result[index]
            ax.barh(
                y,
                width,
                left=left,
                height=0.57,
                color=HIERARCHY_COLORS[name],
                edgecolor="white",
                linewidth=0.55,
            )
            if width >= (12 if compact else 8):
                ax.text(
                    left + width / 2,
                    y,
                    f"{width:.0f}",
                    ha="center",
                    va="center",
                    color="white" if name != "Map within sign" else INK,
                    fontsize=6.4,
                    fontweight="bold",
                )
            left += width
    ax.set_yticks(range(len(metrics)), [label for _, label in metrics])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks((0, 25, 50, 75, 100))
    ax.set_xlabel("Share of total sum of squares (%)")
    ax.tick_params(axis="y", length=0)
    clean_axis(ax, grid="x")
    panel_title(ax, letter, title)


def plot_main_overview(data: SceneDataset, output_dir: Path) -> tuple[Path, Path]:
    set_plot_style()
    counts = canonical_counts(data)
    fig = plt.figure(figsize=(7.25, 5.65), constrained_layout=False)
    grid = fig.add_gridspec(
        2,
        2,
        left=0.075,
        right=0.965,
        bottom=0.205,
        top=0.865,
        hspace=0.49,
        wspace=0.46,
    )
    ax_geo = fig.add_subplot(grid[0, 0])
    ax_structure = fig.add_subplot(grid[0, 1])
    ax_grid = fig.add_subplot(grid[1, 0])
    ax_variance = fig.add_subplot(grid[1, 1])

    plot_geography(ax_geo, data)
    plot_selected_structure(ax_structure, data)
    plot_speed_density_heatmap(
        ax_grid,
        data,
        letter="c",
        title="Coverage of the controlled stress grid",
    )
    plot_variance_decomposition(
        ax_variance,
        data,
        letter="d",
        title="Where scenario variation is introduced",
        compact=True,
    )
    hierarchy_handles = [
        Patch(facecolor=color, label=name)
        for name, color in HIERARCHY_COLORS.items()
    ]
    ax_variance.legend(
        handles=hierarchy_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.39),
        ncol=3,
        frameon=False,
        fontsize=5.8,
        handlelength=1.0,
        handletextpad=0.3,
        columnspacing=0.65,
        borderaxespad=0,
    )

    fig.suptitle(
        "TrafficRuleBench scenes combine real-map breadth with controlled variation",
        x=0.075,
        y=0.985,
        ha="left",
        fontsize=12.0,
        fontweight="bold",
    )
    fig.text(
        0.075,
        0.952,
        (
            f"{counts['signs']} signs  ·  {counts['map_allocations']:,} sign–map allocations  ·  "
            f"{counts['scenarios']:,} scenarios  ·  "
            f"{counts['train_test_place_overlap']} train/test place overlap"
        ),
        ha="left",
        va="center",
        fontsize=8.4,
        color=MID,
    )
    fig.text(
        0.075,
        0.02,
        (
            "Units: panels a–b use unique places or sign–map allocations; "
            "panels c–d use non-nominal scenario rows nested within maps. "
            "Current canonical manifest snapshot; debug and restricted-lane extensions excluded."
        ),
        ha="left",
        va="bottom",
        fontsize=6.6,
        color=MID,
    )
    return save_figure(
        fig,
        output_dir,
        "scene_statistical_overview",
        "TrafficRuleBench generated-scene statistical overview",
    )


def pool_subtype_order(family: str) -> tuple[str, ...]:
    if family == "Junction":
        return ("T", "X", "O")
    if family == "Dual-path":
        return ("T", "X")
    return ("straight", "curved")


def plot_pool_inventory(ax: mpl.axes.Axes, data: SceneDataset) -> None:
    families = ("Junction", "Dual-path", "Corridor")
    values = [len(data.pools[family]) for family in families]
    bars = ax.bar(
        range(3),
        values,
        color=[FAMILY_COLORS[family] for family in families],
        width=0.64,
    )
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + max(values) * 0.025,
            f"{value:,}",
            ha="center",
            va="bottom",
            fontsize=7.5,
            fontweight="bold",
        )
    ax.set_xticks(range(3), families)
    ax.set_ylabel("Harvested OSM map fragments")
    ax.set_ylim(0, max(values) * 1.18)
    clean_axis(ax, grid="y")
    panel_title(ax, "a", f"Current source-pool inventory (n={sum(values):,})")


def plot_pool_vs_selected(ax: mpl.axes.Axes, data: SceneDataset) -> None:
    families = ("Junction", "Dual-path", "Corridor")
    y_positions: list[float] = []
    labels: list[str] = []
    y = 0.0
    for family in families:
        order = pool_subtype_order(family)
        for source_name, rows, pool in (
            ("Source pool", data.pools[family], True),
            ("Benchmark", data.maps, False),
        ):
            counts = subtype_counts(rows, family, pool=pool)
            total = sum(counts.values())
            left = 0.0
            for subtype in order:
                width = 100.0 * counts[subtype] / total if total else 0.0
                ax.barh(
                    y,
                    width,
                    left=left,
                    height=0.58,
                    color=SUBTYPE_COLORS[subtype],
                    edgecolor="white",
                    linewidth=0.6,
                )
                if width >= 10:
                    ax.text(
                        left + width / 2,
                        y,
                        f"{subtype} {width:.0f}%",
                        ha="center",
                        va="center",
                        fontsize=6.3,
                        fontweight="bold",
                        color="white" if subtype != "X" else INK,
                    )
                left += width
            y_positions.append(y)
            labels.append(f"{family}\n{source_name}")
            ax.text(101.2, y, f"n={total:,}", va="center", fontsize=6.3, color=MID)
            y += 0.82
        y += 0.42
    ax.set_yticks(y_positions, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks((0, 25, 50, 75, 100))
    ax.set_xlabel("Composition within map family (%)")
    ax.tick_params(axis="y", length=0)
    clean_axis(ax, grid="x")
    panel_title(ax, "c", "Source pool vs evaluated-map structure")


def ecdf(values: Sequence[float]) -> tuple[np.ndarray, np.ndarray]:
    x = np.sort(np.asarray(values, dtype=float))
    y = np.arange(1, len(x) + 1, dtype=float) / len(x)
    return x, y


def selected_dual_gains(data: SceneDataset) -> tuple[list[float], list[float]]:
    source_rows = data.pools["Dual-path"]
    by_scene = {str(row["scene_id"]): float(row["gain_m"]) for row in source_rows}
    selected_ids = {
        row["_map_id"] for row in data.maps if row["_map_family"] == "Dual-path"
    }
    selected = [by_scene[scene_id] for scene_id in selected_ids if scene_id in by_scene]
    source = [float(row["gain_m"]) for row in source_rows]
    return source, selected


def plot_dual_gain(ax: mpl.axes.Axes, data: SceneDataset) -> None:
    source, selected = selected_dual_gains(data)
    for values, label, color, linewidth in (
        (source, "Source pool", MID, 1.25),
        (selected, "Evaluated unique maps", VERMILLION, 1.8),
    ):
        x, y = ecdf(values)
        ax.plot(x, y, color=color, linewidth=linewidth, label=f"{label} (n={len(values):,})")
    selected_median = float(np.median(selected))
    ax.axvline(selected_median, color=VERMILLION, linestyle=":", linewidth=0.9)
    ax.text(
        selected_median + 8,
        0.08,
        f"selected median\n{selected_median:.0f} m",
        color=VERMILLION,
        fontsize=6.6,
        va="bottom",
    )
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Extra distance of the legal route (m)")
    ax.set_ylabel("Cumulative share")
    clean_axis(ax, grid="y")
    ax.legend(frameon=False, loc="upper left")
    panel_title(ax, "d", "Strength of the dual-path temptation")


def plot_map_diversity(data: SceneDataset, output_dir: Path) -> tuple[Path, Path]:
    set_plot_style()
    fig = plt.figure(figsize=(7.25, 5.65))
    grid = fig.add_gridspec(
        2,
        2,
        left=0.085,
        right=0.965,
        bottom=0.105,
        top=0.925,
        hspace=0.43,
        wspace=0.36,
    )
    plot_pool_inventory(fig.add_subplot(grid[0, 0]), data)
    plot_geography(fig.add_subplot(grid[0, 1]), data)
    # The shared geography routine names itself panel a; correct that title here.
    geo_ax = fig.axes[1]
    geo_ax.set_title(
        rf"$\bf{{b}}$  Geographic coverage ({len(selected_unique_places(data)):,} unique places)",
        loc="left",
        pad=6,
        fontweight="normal",
    )
    plot_pool_vs_selected(fig.add_subplot(grid[1, 0]), data)
    plot_dual_gain(fig.add_subplot(grid[1, 1]), data)
    fig.suptitle(
        "Real-map inventory, selection coverage, and route geometry",
        x=0.085,
        y=0.985,
        ha="left",
        fontsize=12.0,
        fontweight="bold",
    )
    fig.text(
        0.085,
        0.025,
        (
            "Source: current scene_collection map indices and canonical train/test manifests. "
            "Benchmark composition uses sign–map allocations; the geographic panel deduplicates physical places."
        ),
        ha="left",
        va="bottom",
        fontsize=6.6,
        color=MID,
    )
    return save_figure(
        fig,
        output_dir,
        "scene_map_diversity",
        "TrafficRuleBench real-map diversity",
    )


def plot_scenarios_per_map(ax: mpl.axes.Axes, data: SceneDataset) -> None:
    counts = Counter((r["_sign_id"], r["_split"], r["_map_id"]) for r in data.rows)
    histogram = Counter(counts.values())
    xs = sorted(histogram)
    ys = [histogram[x] for x in xs]
    bars = ax.bar(xs, ys, color=BLUE, width=0.72)
    for bar, value in zip(bars, ys):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + max(ys) * 0.02,
            f"{value:,}",
            ha="center",
            va="bottom",
            fontsize=7.0,
            fontweight="bold",
        )
    ax.axvline(10, color=VERMILLION, linestyle="--", linewidth=1.0, label="Protocol target")
    ax.set_xlabel("Scenario rows per sign–map allocation")
    ax.set_ylabel("Number of map allocations")
    ax.set_ylim(0, max(ys) * 1.15)
    clean_axis(ax, grid="y")
    ax.legend(frameon=False, loc="upper left")
    panel_title(ax, "a", "Nested expansion is complete for available maps")


def plot_route_density_heatmap(ax: mpl.axes.Axes, data: SceneDataset) -> None:
    matrix = np.zeros((3, 2), dtype=float)
    for row in data.rows:
        if row.get("is_nominal", False):
            continue
        density = row.get("density_level_id")
        route = row.get("max_path_length_m")
        if density not in (0, 1, 2):
            continue
        if not is_number(route):
            continue
        route_index = 0 if float(route) <= 100 else 1
        matrix[int(density), route_index] += 1
    row_normalized = 100.0 * matrix / matrix.sum()
    image = ax.imshow(
        row_normalized,
        cmap="Blues",
        vmin=0,
        vmax=max(20.0, float(row_normalized.max())),
        aspect="auto",
    )
    for i in range(3):
        for j in range(2):
            ax.text(
                j,
                i,
                f"{int(matrix[i, j]):,}\n{row_normalized[i, j]:.1f}%",
                ha="center",
                va="center",
                color=INK,
                fontsize=7.1,
                fontweight="bold",
                linespacing=0.9,
            )
    ax.set_xticks((0, 1), ("90 m", "120 m"))
    ax.set_yticks((0, 1, 2), ("p25 sparse", "p50 typical", "p75 dense"))
    ax.set_xlabel("Route-budget probe")
    ax.set_ylabel("Traffic-density probe")
    ax.tick_params(length=0)
    panel_title(ax, "c", "Route × traffic stress coverage")
    colorbar = ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.025)
    colorbar.set_label("Share of eligible scenarios (%)", fontsize=7.0)
    colorbar.ax.tick_params(labelsize=6.5)


def plot_augmentation_coverage(data: SceneDataset, output_dir: Path) -> tuple[Path, Path]:
    set_plot_style()
    fig = plt.figure(figsize=(7.25, 5.05))
    grid = fig.add_gridspec(
        2,
        2,
        left=0.085,
        right=0.965,
        bottom=0.205,
        top=0.865,
        hspace=0.49,
        wspace=0.50,
    )
    plot_scenarios_per_map(fig.add_subplot(grid[0, 0]), data)
    plot_speed_density_heatmap(
        fig.add_subplot(grid[0, 1]),
        data,
        letter="b",
        title="Ego speed × traffic density",
    )
    plot_route_density_heatmap(fig.add_subplot(grid[1, 0]), data)
    plot_variance_decomposition(
        fig.add_subplot(grid[1, 1]),
        data,
        letter="d",
        title="Hierarchical variance decomposition",
    )
    handles = [
        Patch(facecolor=color, label=name)
        for name, color in HIERARCHY_COLORS.items()
    ]
    fig.axes[-1].legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.36),
        ncol=3,
        frameon=False,
        fontsize=5.8,
        handlelength=1.0,
        handletextpad=0.3,
        columnspacing=0.65,
        borderaxespad=0,
    )
    fig.suptitle(
        "Scenario expansion covers a controlled, hierarchical stress design",
        x=0.085,
        y=0.985,
        ha="left",
        fontsize=12.0,
        fontweight="bold",
    )
    fig.text(
        0.085,
        0.02,
        (
            "The ten rows per map are correlated design points, not independent samples. "
            "Heatmaps exclude the nominal zero-traffic row; the speed grid excludes task-conditioned speed signs."
        ),
        ha="left",
        va="bottom",
        fontsize=6.6,
        color=MID,
    )
    return save_figure(
        fig,
        output_dir,
        "scene_augmentation_coverage",
        "TrafficRuleBench scenario augmentation coverage",
    )


def plot_speed_calibration(ax: mpl.axes.Axes, data: SceneDataset) -> None:
    stats = data.nuplan_report["speed_stats"]
    percentiles = stats["percentiles"]
    p5 = float(percentiles["5%"])
    p25 = float(percentiles["25%"])
    p50 = float(percentiles["50%"])
    p75 = float(percentiles["75%"])
    p95 = float(percentiles["95%"])
    probes = np.array([3.61, 7.75, 11.05])
    targets = np.array([p25, p50, p75])

    ax.hlines(1.0, p5, p95, color=MID, linewidth=1.0)
    ax.hlines(1.0, p25, p75, color=BLUE, linewidth=8.0, alpha=0.38)
    ax.plot(p50, 1.0, marker="|", markersize=14, markeredgewidth=1.4, color=BLUE)
    ax.scatter(probes, np.full(3, 0.63), color=VERMILLION, s=24, zorder=3)
    for label, probe, target in zip(("p25", "p50", "p75"), probes, targets):
        delta = 100.0 * (probe - target) / target
        ax.plot([target, probe], [0.96, 0.67], color=LIGHT, linewidth=0.7, zorder=1)
        ax.text(
            probe,
            0.49,
            f"{label}\n{probe:.2f}\n({delta:+.0f}%)",
            ha="center",
            va="top",
            fontsize=6.5,
            color=VERMILLION,
            linespacing=0.88,
        )

    task_values = [
        float(row["spawn_velocity_ms"])
        for row in data.rows
        if row["_paper_group"] == "Speed"
        and not row.get("is_nominal", False)
        and is_number(row.get("spawn_velocity_ms"))
    ]
    if task_values:
        q5, q25, q50, q75, q95 = np.percentile(task_values, (5, 25, 50, 75, 95))
        ax.hlines(0.18, q5, q95, color=MID, linewidth=1.0)
        ax.hlines(0.18, q25, q75, color=PURPLE, linewidth=8.0, alpha=0.38)
        ax.plot(q50, 0.18, marker="|", markersize=13, markeredgewidth=1.4, color=PURPLE)
        ax.text(
            q95 + 0.2,
            0.18,
            "task-conditioned",
            va="center",
            fontsize=6.5,
            color=PURPLE,
        )
    ax.set_ylim(0, 1.25)
    ax.set_yticks((1.0, 0.63, 0.18), ("nuPlan", "generic probes", "speed-rule scenes"))
    ax.set_xlabel("Initial ego speed (m/s)")
    ax.tick_params(axis="y", length=0)
    clean_axis(ax, grid="x")
    panel_title(ax, "a", "Initial-speed support and quantile probes")


def plot_density_calibration(ax: mpl.axes.Axes, data: SceneDataset) -> None:
    calibration = data.density_calibration
    curve = calibration["sim_curve"]
    x = np.array(sorted(float(key) for key in curve))
    p25 = np.array([float(curve[str(value)]["p25"]) for value in x])
    p50 = np.array([float(curve[str(value)]["p50"]) for value in x])
    p75 = np.array([float(curve[str(value)]["p75"]) for value in x])
    ax.fill_between(x, p25, p75, color=SKY, alpha=0.25, label="Simulator IQR")
    ax.plot(x, p50, color=BLUE, linewidth=1.8, marker="o", markersize=3.0, label="Simulator median")

    targets = np.array(
        data.nuplan_report["traffic_density"]["count_moving_r150_per_lane"]["p25/50/75"],
        dtype=float,
    )
    controls = np.array([0.1462, 0.2682, 0.6])
    for index, (target, control) in enumerate(zip(targets, controls)):
        color = (ORANGE, VERMILLION, PURPLE)[index]
        ax.axhline(target, color=color, linestyle=":", linewidth=0.9, alpha=0.9)
        ax.axvline(control, color=color, linestyle="--", linewidth=0.8, alpha=0.7)
        ax.scatter(
            [control],
            [target],
            marker="X",
            s=34,
            color=color,
            edgecolor="white",
            linewidth=0.45,
            zorder=4,
        )
        ax.text(
            control,
            target + 0.22,
            f"p{25 + 25 * index}",
            ha="center",
            va="bottom",
            fontsize=6.3,
            color=color,
            fontweight="bold",
        )
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, max(8.5, float(p75.max()) + 0.5))
    ax.set_xlabel("Simulator traffic-density control")
    ax.set_ylabel("Moving NPCs per lane\n(within 150 m)")
    clean_axis(ax, grid="y")
    ax.legend(frameon=False, loc="upper left")
    panel_title(ax, "b", "Inverse calibration to nuPlan traffic quantiles")


def plot_idm_alignment(ax: mpl.axes.Axes, data: SceneDataset) -> None:
    report = data.nuplan_report
    definitions = (
        ("profile_NORMAL_SPEED", "NPC desired speed", report["speed_stats"]["median"]),
        (
            "profile_ACC_FACTOR",
            "NPC acceleration",
            report["acceleration_stats"]["median"],
        ),
        (
            "profile_DEACC_FACTOR",
            "NPC deceleration",
            report["deceleration_stats"]["median"],
        ),
    )
    for y, (field, label, reference) in enumerate(definitions):
        values = np.array(
            [
                float(row[field])
                for row in data.rows
                if not row.get("is_nominal", False) and is_number(row.get(field))
            ]
        )
        ratios = values / float(reference)
        q5, q25, q50, q75, q95 = np.percentile(ratios, (5, 25, 50, 75, 95))
        ax.hlines(y, q5, q95, color=MID, linewidth=1.0)
        ax.hlines(y, q25, q75, color=GREEN, linewidth=6.0, alpha=0.45)
        ax.scatter(q50, y, color=GREEN, edgecolor="white", linewidth=0.45, s=28, zorder=3)
        ax.text(
            q95 + 0.035,
            y,
            f"median {q50:.2f}×",
            va="center",
            fontsize=6.4,
            color=MID,
        )
    ax.axvline(1.0, color=VERMILLION, linestyle="--", linewidth=1.0, label="nuPlan median")
    ax.set_yticks(range(len(definitions)), [label for _, label, _ in definitions])
    ax.invert_yaxis()
    ax.set_xlabel("Manifest IDM parameter / nuPlan median")
    ax.tick_params(axis="y", length=0)
    clean_axis(ax, grid="x")
    ax.legend(frameon=False, loc="lower right")
    panel_title(ax, "c", "Post-transform IDM marginals (5–95%, IQR, median)")


def plot_nuplan_calibration(data: SceneDataset, output_dir: Path) -> tuple[Path, Path]:
    set_plot_style()
    fig = plt.figure(figsize=(7.25, 2.75))
    grid = fig.add_gridspec(
        1,
        3,
        left=0.075,
        right=0.975,
        bottom=0.22,
        top=0.83,
        wspace=0.53,
        width_ratios=(1.0, 1.15, 1.05),
    )
    plot_speed_calibration(fig.add_subplot(grid[0, 0]), data)
    plot_density_calibration(fig.add_subplot(grid[0, 1]), data)
    plot_idm_alignment(fig.add_subplot(grid[0, 2]), data)
    fig.suptitle(
        "nuPlan is used for calibrated probes and IDM marginals—not scene cloning",
        x=0.075,
        y=0.985,
        ha="left",
        fontsize=11.5,
        fontweight="bold",
    )
    fig.text(
        0.075,
        0.045,
        (
            "Panel a compares the current nuPlan summary with manifest probes; percentages are relative quantile errors. "
            "Panel b uses the benchmark's SUMO-scene calibration sweep. Panel c reports transformed manifest parameters; "
            "desired speed is intentionally clipped by the simulator policy."
        ),
        ha="left",
        va="bottom",
        fontsize=6.4,
        color=MID,
    )
    return save_figure(
        fig,
        output_dir,
        "scene_nuplan_calibration",
        "TrafficRuleBench nuPlan calibration analysis",
    )


def per_sign_audit(data: SceneDataset) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for spec in SIGN_SPECS:
        sign_rows = [row for row in data.rows if row["_sign_id"] == spec.sign_id]
        sign_maps = [row for row in data.maps if row["_sign_id"] == spec.sign_id]
        by_map = Counter((row["_split"], row["_map_id"]) for row in sign_rows)
        train_maps = sum(row["_split"] == "train" for row in sign_maps)
        test_maps = sum(row["_split"] == "test" for row in sign_maps)
        complete_fraction = float(np.mean([value == 10 for value in by_map.values()]))
        non_nominal = [row for row in sign_rows if not row.get("is_nominal", False)]
        density_levels = len(
            {
                int(row["density_level_id"])
                for row in non_nominal
                if row.get("density_level_id") in (0, 1, 2)
            }
        )
        speed_levels = len(
            {
                int(row["spawn_velocity_level_id"])
                for row in non_nominal
                if row.get("spawn_velocity_level_id") in (0, 1, 2)
            }
        )
        unique_places = len({row["_place_id"] for row in sign_maps})
        result.append(
            {
                "group": spec.paper_group,
                "sign_id": spec.sign_id,
                "code": spec.code,
                "label": spec.label,
                "train_maps": train_maps,
                "test_maps": test_maps,
                "scenarios": len(sign_rows),
                "mean_scenarios_per_map": len(sign_rows) / len(sign_maps),
                "complete_map_fraction": complete_fraction,
                "density_levels": density_levels,
                "speed_levels": speed_levels,
                "expected_speed_levels": spec.expected_speed_levels,
                "unique_places": unique_places,
                "place_uniqueness": unique_places / len(sign_maps),
            }
        )
    return result


def plot_audit_matrix(data: SceneDataset, output_dir: Path) -> tuple[Path, Path]:
    set_plot_style()
    audit = per_sign_audit(data)
    target_values = np.empty((len(audit), 5), dtype=float)
    annotations = np.empty((len(audit), 5), dtype=object)
    for row_index, row in enumerate(audit):
        target_values[row_index, 0] = row["train_maps"] / 80.0
        annotations[row_index, 0] = f"{row['train_maps']}/80"
        target_values[row_index, 1] = row["test_maps"] / 20.0
        annotations[row_index, 1] = f"{row['test_maps']}/20"
        target_values[row_index, 2] = row["complete_map_fraction"]
        annotations[row_index, 2] = f"{100 * row['complete_map_fraction']:.0f}%"
        target_values[row_index, 3] = row["density_levels"] / 3.0
        annotations[row_index, 3] = f"{row['density_levels']}/3"
        expected_speed = row["expected_speed_levels"]
        if expected_speed is None:
            target_values[row_index, 4] = np.nan
            annotations[row_index, 4] = "task"
        else:
            target_values[row_index, 4] = row["speed_levels"] / expected_speed
            annotations[row_index, 4] = f"{row['speed_levels']}/{expected_speed}"

    uniqueness = np.array([[row["place_uniqueness"]] for row in audit])
    coverage_cmap = LinearSegmentedColormap.from_list(
        "coverage",
        (VERMILLION, "#F6D6C8", PALE, "#B9E1D2", GREEN),
    )
    fig = plt.figure(figsize=(7.25, 8.0))
    grid = fig.add_gridspec(
        1,
        2,
        left=0.265,
        right=0.94,
        bottom=0.085,
        top=0.92,
        width_ratios=(5.0, 1.0),
        wspace=0.08,
    )
    ax = fig.add_subplot(grid[0, 0])
    ax_unique = fig.add_subplot(grid[0, 1], sharey=ax)
    image = ax.imshow(
        target_values,
        cmap=coverage_cmap,
        vmin=0.75,
        vmax=1.02,
        aspect="auto",
        interpolation="nearest",
    )
    image.cmap.set_bad(LIGHT)
    unique_image = ax_unique.imshow(
        uniqueness,
        cmap="Blues",
        vmin=0.5,
        vmax=1.0,
        aspect="auto",
        interpolation="nearest",
    )

    for i in range(len(audit)):
        for j in range(5):
            ax.text(
                j,
                i,
                annotations[i, j],
                ha="center",
                va="center",
                fontsize=6.4,
                color=INK,
                fontweight="bold" if target_values[i, j] < 0.999 else "normal",
            )
        ax_unique.text(
            0,
            i,
            f"{100 * uniqueness[i, 0]:.0f}%",
            ha="center",
            va="center",
            fontsize=6.4,
            color=INK,
        )

    labels = [f"{row['code']}  {row['label']}" for row in audit]
    ax.set_yticks(range(len(audit)), labels)
    ax.set_xticks(
        range(5),
        (
            "Train\nmaps",
            "Test\nmaps",
            "Maps with\n10 scenes",
            "Density\nprobes",
            "Ego-speed\nprobes",
        ),
    )
    ax.xaxis.tick_top()
    ax.tick_params(axis="both", length=0, pad=4)
    ax_unique.set_xticks((0,), ("Unique\nplaces",))
    ax_unique.xaxis.tick_top()
    ax_unique.tick_params(axis="both", length=0, labelleft=False, pad=4)
    for axis in (ax, ax_unique):
        for spine in axis.spines.values():
            spine.set_visible(False)

    start = 0
    for group in GROUP_ORDER:
        group_rows = [row for row in audit if row["group"] == group]
        if start > 0:
            for axis in (ax, ax_unique):
                axis.axhline(start - 0.5, color="white", linewidth=3.0)
        ax.text(
            -0.64,
            start - 0.58,
            group.upper(),
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="bottom",
            fontsize=6.8,
            color=MID,
            fontweight="bold",
            clip_on=False,
        )
        start += len(group_rows)

    coverage_bar = fig.colorbar(
        image,
        ax=ax,
        location="bottom",
        fraction=0.025,
        pad=0.055,
        aspect=45,
    )
    coverage_bar.set_label("Protocol-target attainment", fontsize=7.0)
    coverage_bar.set_ticks((0.75, 0.9, 1.0))
    coverage_bar.set_ticklabels(("75%", "90%", "100%"))
    unique_bar = fig.colorbar(
        unique_image,
        ax=ax_unique,
        location="bottom",
        fraction=0.12,
        pad=0.055,
        aspect=9,
    )
    unique_bar.set_label("Unique", fontsize=7.0)
    unique_bar.set_ticks((0.5, 1.0))
    unique_bar.set_ticklabels(("50%", "100%"))
    fig.suptitle(
        "Per-sign coverage audit of the canonical generated-scene manifests",
        x=0.075,
        y=0.985,
        ha="left",
        fontsize=12.0,
        fontweight="bold",
    )
    fig.text(
        0.075,
        0.025,
        (
            "Gray speed cells denote physics-conditioned approach speeds rather than the generic three-probe grid. "
            "Place uniqueness is descriptive: reuse is allowed only within a split and compatible behavioral family."
        ),
        ha="left",
        va="bottom",
        fontsize=6.6,
        color=MID,
    )
    return save_figure(
        fig,
        output_dir,
        "scene_per_sign_audit",
        "TrafficRuleBench per-sign generated-scene audit",
    )


def write_summary_tsv(data: SceneDataset, output_path: Path) -> None:
    counts = canonical_counts(data)
    rows: list[tuple[str, str, str, str]] = []
    for metric, value in counts.items():
        if isinstance(value, float):
            text = f"{value:.6f}"
        else:
            text = str(value)
        rows.append(("overview", "all", metric, text))

    for family, pool_rows in data.pools.items():
        rows.append(("source_pool", family, "maps", str(len(pool_rows))))
        for subtype, value in sorted(subtype_counts(pool_rows, family, pool=True).items()):
            rows.append(("source_pool", family, f"subtype_{subtype}", str(value)))
        selected = [row for row in data.maps if row["_map_family"] == family]
        rows.append(("benchmark", family, "map_allocations", str(len(selected))))
        for subtype, value in sorted(subtype_counts(data.maps, family, pool=False).items()):
            rows.append(("benchmark", family, f"subtype_{subtype}", str(value)))

    matrix, n_maps = speed_density_matrix(data)
    for density in range(3):
        for speed in range(3):
            rows.append(
                (
                    "stress_grid",
                    f"density_{density}_speed_{speed}",
                    "map_weighted_percent",
                    f"{matrix[density, speed]:.6f}",
                )
            )
    rows.append(("stress_grid", "all", "eligible_maps", str(n_maps)))

    for field, label in (
        ("spawn_velocity_ms", "ego_speed"),
        ("traffic_density", "traffic_density"),
        ("max_path_length_m", "route_budget"),
        ("profile_ACC_FACTOR", "npc_acceleration"),
        ("profile_DEACC_FACTOR", "npc_deceleration"),
        ("background_npc_count", "npc_count"),
    ):
        sign, map_fraction, augmentation, n = variance_decomposition(data, field)
        rows.extend(
            (
                ("variance", label, "sign_fraction", f"{sign:.6f}"),
                ("variance", label, "map_fraction", f"{map_fraction:.6f}"),
                ("variance", label, "augmentation_fraction", f"{augmentation:.6f}"),
                ("variance", label, "scenario_rows", str(n)),
            )
        )

    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(("section", "group", "metric", "value"))
        writer.writerows(rows)


def write_audit_tsv(data: SceneDataset, output_path: Path) -> None:
    rows = per_sign_audit(data)
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_provenance(data: SceneDataset, output_path: Path) -> None:
    payload = {
        "statistical_units": {
            "source_pool_map": "one row in scene_collection/maps/index/*.jsonl",
            "map_allocation": "unique (sign_id, split, parent(net_path))",
            "place": "junction_id or osm_way_id",
            "scenario": "one canonical real_manifest.jsonl row",
        },
        "excluded": [
            "debug manifests",
            "runs_rl3 restricted-lane extension",
            "local partial speed_limit manifest (replaced by runs_v7)",
        ],
        "manifest_paths": [str(path.resolve()) for path in data.manifest_paths],
        "counts": canonical_counts(data),
        "source_pool_counts": {
            family: len(rows) for family, rows in data.pools.items()
        },
    }
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def validate_targets(data: SceneDataset) -> list[str]:
    warnings: list[str] = []
    for row in per_sign_audit(data):
        if row["train_maps"] != 80 or row["test_maps"] != 20:
            warnings.append(
                f"{row['sign_id']}: maps={row['train_maps']}/{row['test_maps']} "
                "(expected 80/20)"
            )
        if row["complete_map_fraction"] < 1.0:
            warnings.append(
                f"{row['sign_id']}: only "
                f"{100 * row['complete_map_fraction']:.1f}% maps have 10 scenarios"
            )
    if len(data.rows) != 25_000:
        warnings.append(f"canonical scenarios={len(data.rows):,} (expected 25,000)")
    return warnings


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    data = load_dataset(repo_root, args.extra_runs_root.resolve())

    outputs: list[Path] = []
    for make_figure in (
        plot_main_overview,
        plot_map_diversity,
        plot_augmentation_coverage,
        plot_nuplan_calibration,
        plot_audit_matrix,
    ):
        outputs.extend(make_figure(data, output_dir))

    summary_path = output_dir / "scene_statistics_summary.tsv"
    audit_path = output_dir / "scene_per_sign_audit.tsv"
    provenance_path = output_dir / "scene_statistics_provenance.json"
    write_summary_tsv(data, summary_path)
    write_audit_tsv(data, audit_path)
    write_provenance(data, provenance_path)
    outputs.extend((summary_path, audit_path, provenance_path))

    warnings = validate_targets(data)
    counts = canonical_counts(data)
    print(
        f"Canonical snapshot: {counts['signs']} signs, "
        f"{counts['map_allocations']:,} map allocations, "
        f"{counts['scenarios']:,} scenarios, "
        f"{counts['unique_places']:,} unique places"
    )
    for warning in warnings:
        print(f"WARNING: {warning}")
    for path in outputs:
        print(f"Wrote {path}")
    if args.strict_targets and warnings:
        raise SystemExit("Strict protocol validation failed.")


if __name__ == "__main__":
    main()
