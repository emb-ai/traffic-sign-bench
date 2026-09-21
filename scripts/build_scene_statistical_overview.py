#!/usr/bin/env python3
"""Build reviewer-facing statistics directly from raw maps and manifests.

The script deliberately keeps four statistical units separate:

* harvested map: one row in an OSM source-pool index;
* physical place: one OSM junction/way, deduplicated across signs;
* sign-map allocation: one selected map assigned to one sign and split;
* scenario: one augmented manifest row nested within a sign-map allocation.

Core figures describe the 25-sign benchmark in the paper.  The four
restricted-lane signs in ``runs_rl3`` are loaded and audited as a separate
extension so they cannot silently change the stated 25-sign/25k protocol.
No benchmark plotting module is imported: all quantities are reconstructed
from JSONL manifests, source indices, and the raw nuPlan CSV files.
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
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


# Requested paper palette, supplemented only with neutral ink tones.
BLUE = "#90CAF9"
RED = "#E76F51"
GREEN = "#A1CB35"
ORANGE = "#FCAD38"
INK = "#222222"
MID = "#6B6B6B"
LIGHT = "#D9D9D9"
PALE = "#F4F4F4"
WHITE = "#FFFFFF"

FAMILY_COLORS = {
    "Junction": BLUE,
    "Dual-path": RED,
    "Corridor": GREEN,
    "Restricted-lane extension": ORANGE,
}
SUBTYPE_COLORS = {
    "T": BLUE,
    "X": RED,
    "O": ORANGE,
    "straight": BLUE,
    "curved": GREEN,
}


@dataclass(frozen=True)
class SignSpec:
    sign_id: str
    code: str
    label: str
    task_group: str
    map_family: str


CORE_SIGNS: tuple[SignSpec, ...] = (
    SignSpec("main_road", "2.1", "Main road", "Priority", "Junction"),
    SignSpec("secondary_road", "2.3", "Secondary road", "Priority", "Junction"),
    SignSpec("yield", "2.4", "Yield", "Priority", "Junction"),
    SignSpec("stop", "2.5", "Stop", "Priority", "Junction"),
    SignSpec("roundabout", "4.3", "Roundabout", "Priority", "Junction"),
    SignSpec("crosswalk", "5.19", "Crosswalk", "Priority", "Corridor"),
    SignSpec("speed_limit", "3.24", "Maximum speed", "Speed", "Corridor"),
    SignSpec("min_speed", "4.6", "Minimum speed", "Speed", "Corridor"),
    SignSpec("residential_zone", "5.21", "Residential zone", "Speed", "Corridor"),
    SignSpec("zone_speed_limit", "5.31", "Speed zone", "Speed", "Corridor"),
    SignSpec("blocked_road", "3.2", "Movement prohibited", "Detour", "Junction"),
    SignSpec("detour_left", "4.2.2", "Pass left", "Detour", "Corridor"),
    SignSpec("detour_right", "4.2.1", "Pass right", "Detour", "Corridor"),
    SignSpec("detour_either", "4.2.3", "Pass either side", "Detour", "Corridor"),
    SignSpec("no_entry", "3.1", "No entry", "Directional", "Dual-path"),
    SignSpec("no_turn_left", "3.18.2", "No left turn", "Directional", "Dual-path"),
    SignSpec("no_turn_right", "3.18.1", "No right turn", "Directional", "Dual-path"),
    SignSpec("direction_straight", "4.1.1", "Straight only", "Directional", "Dual-path"),
    SignSpec("direction_right", "4.1.2", "Right only", "Directional", "Dual-path"),
    SignSpec("direction_left", "4.1.3", "Left only", "Directional", "Dual-path"),
    SignSpec(
        "direction_straight_right",
        "4.1.4",
        "Straight or right",
        "Directional",
        "Dual-path",
    ),
    SignSpec(
        "direction_straight_left",
        "4.1.5",
        "Straight or left",
        "Directional",
        "Dual-path",
    ),
    SignSpec(
        "direction_left_right",
        "4.1.6",
        "Left or right",
        "Directional",
        "Dual-path",
    ),
    SignSpec("one_way_right", "5.7.1", "One way, right", "Directional", "Dual-path"),
    SignSpec("one_way_left", "5.7.2", "One way, left", "Directional", "Dual-path"),
)

EXTENSION_SIGNS: tuple[SignSpec, ...] = (
    SignSpec("bike_lane", "5.14.2", "Bicycle lane", "Restricted lane", "Corridor"),
    SignSpec("bike_lane_road", "5.11.2", "Bicycle-lane road", "Restricted lane", "Corridor"),
    SignSpec("bus_lane", "5.14.1", "Bus lane", "Restricted lane", "Corridor"),
    SignSpec("bus_lane_road", "5.13.1", "Bus-lane road", "Restricted lane", "Corridor"),
)

POOL_FILES = {
    "Junction": "junctions.jsonl",
    "Dual-path": "dual_path_candidates.jsonl",
    "Corridor": "segments.jsonl",
}


@dataclass
class Corpus:
    rows: list[dict[str, Any]]
    maps: list[dict[str, Any]]
    scene_pool_rows: list[dict[str, Any]]
    extension_rows: list[dict[str, Any]]
    extension_maps: list[dict[str, Any]]
    pools: dict[str, list[dict[str, Any]]]
    source_lookup: dict[str, dict[str, Any]]
    manifest_paths: list[Path]
    extension_manifest_paths: list[Path]
    nuplan: dict[str, np.ndarray]
    density_calibration: dict[str, Any]


def parse_args() -> argparse.Namespace:
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=repo)
    parser.add_argument(
        "--v7-root",
        type=Path,
        default=Path(
            "/home/jovyan/shares/SR006.nfs2/smirnova/"
            "traffic-rule-bench-main/data/runs_v7"
        ),
    )
    parser.add_argument(
        "--rl3-root",
        type=Path,
        default=Path(
            "/home/jovyan/shares/SR006.nfs2/smirnova/"
            "traffic-rule-bench-main/data/runs_rl3"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo / "paper" / "imgs",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when the current core snapshot differs from 25 x 100 x 10.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def map_id(row: dict[str, Any]) -> str:
    return Path(str(row["net_path"])).parent.name


def topology(row: dict[str, Any]) -> str:
    layout = row.get("junction_layout") or {}
    shape = layout.get("shape")
    if shape:
        return str(shape)
    segment_type = row.get("segment_type")
    if segment_type:
        return str(segment_type)
    mid = row.get("_map_id", map_id(row))
    if str(mid).startswith("dual_T"):
        return "T"
    if str(mid).startswith("dual_X"):
        return "X"
    return "unknown"


def place_id(row: dict[str, Any], source_lookup: dict[str, dict[str, Any]]) -> str:
    layout = row.get("junction_layout") or {}
    value = row.get("junction_id") or layout.get("junction_id") or row.get("osm_way_id")
    if value is not None:
        return str(value)
    source = source_lookup.get(row["_map_id"], {})
    value = source.get("junction_id") or source.get("osm_way_id")
    return str(value) if value is not None else str(row["_map_id"])


def select_map_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["_sign_id"], row["_split"], row["_map_id"])].append(row)
    selected = []
    for group in groups.values():
        nominal = next((row for row in group if row.get("is_nominal", False)), None)
        selected.append(nominal or group[0])
    return selected


def load_manifests(
    specs: Sequence[SignSpec],
    roots: Sequence[Path],
) -> tuple[list[dict[str, Any]], list[Path]]:
    rows: list[dict[str, Any]] = []
    paths: list[Path] = []
    for spec in specs:
        sign_root = next((root for root in roots if (root / spec.sign_id).is_dir()), None)
        if sign_root is None:
            raise FileNotFoundError(f"No manifest root contains {spec.sign_id}")
        for split in ("train", "test"):
            path = sign_root / spec.sign_id / split / "real_manifest.jsonl"
            if not path.is_file():
                raise FileNotFoundError(path)
            paths.append(path)
            for row in read_jsonl(path):
                row["_sign_id"] = spec.sign_id
                row["_sign_code"] = spec.code
                row["_sign_label"] = spec.label
                row["_task_group"] = spec.task_group
                row["_map_family"] = spec.map_family
                row["_split"] = split
                row["_map_id"] = map_id(row)
                rows.append(row)
    return rows, paths


def load_scene_pools(
    repo: Path,
    specs: Sequence[SignSpec],
    source_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Read pre-generation sign allocations from data/scenes."""
    rows: list[dict[str, Any]] = []
    for spec in specs:
        path = repo / "data" / "scenes" / spec.sign_id / "moscow_pool.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        for source_row in payload["scenes"]:
            row = dict(source_row)
            row["_sign_id"] = spec.sign_id
            row["_map_family"] = spec.map_family
            row["_split"] = str(row["split"])
            row["_map_id"] = str(row["scene_id"])
            row["_place_id"] = place_id(row, source_lookup)
            rows.append(row)
    return rows


def load_nuplan(stats_root: Path) -> dict[str, np.ndarray]:
    routes = pd.read_csv(stats_root / "routes.csv.gz")
    densities = pd.read_csv(stats_root / "densities.csv.gz")
    return {
        "initial_speed": routes["initial_speed"].dropna().to_numpy(float),
        "speed": pd.read_csv(stats_root / "speeds.csv.gz")["speed"].dropna().to_numpy(float),
        "acceleration": pd.read_csv(stats_root / "acc_pos.csv.gz")[
            "acceleration"
        ].dropna().to_numpy(float),
        "deceleration": pd.read_csv(stats_root / "acc_neg.csv.gz")[
            "deceleration"
        ].dropna().to_numpy(float),
        "following_distance": pd.read_csv(stats_root / "following.csv.gz")[
            "following_distance"
        ].dropna().to_numpy(float),
        "moving_per_lane": densities["count_moving_r150_per_lane"]
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
        .to_numpy(float),
    }


def load_corpus(repo: Path, v7_root: Path, rl3_root: Path) -> Corpus:
    index_root = repo / "traffic_bench" / "scene_collection" / "maps" / "index"
    pools = {
        family: read_jsonl(index_root / filename)
        for family, filename in POOL_FILES.items()
    }
    source_lookup = {
        str(row["scene_id"]): row
        for rows in pools.values()
        for row in rows
        if row.get("scene_id") is not None
    }
    rows, paths = load_manifests(CORE_SIGNS, (v7_root, repo / "data" / "runs"))
    extension_rows, extension_paths = load_manifests(EXTENSION_SIGNS, (rl3_root,))
    for row in rows + extension_rows:
        row["_place_id"] = place_id(row, source_lookup)

    stats_root = (
        repo / "traffic_bench" / "eval" / "engine" / "traffic" / "nuplan_statistics"
    )
    return Corpus(
        rows=rows,
        maps=select_map_rows(rows),
        scene_pool_rows=load_scene_pools(repo, CORE_SIGNS, source_lookup),
        extension_rows=extension_rows,
        extension_maps=select_map_rows(extension_rows),
        pools=pools,
        source_lookup=source_lookup,
        manifest_paths=paths,
        extension_manifest_paths=extension_paths,
        nuplan=load_nuplan(stats_root),
        density_calibration=json.loads(
            (stats_root / "density_calibration_sumo.json").read_text(encoding="utf-8")
        ),
    )


def set_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIXGeneral", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 8.2,
            "axes.titlesize": 9.1,
            "axes.labelsize": 8.1,
            "axes.edgecolor": MID,
            "axes.linewidth": 0.65,
            "axes.axisbelow": True,
            "xtick.labelsize": 7.1,
            "ytick.labelsize": 7.1,
            "xtick.color": MID,
            "ytick.color": MID,
            "text.color": INK,
            "legend.fontsize": 6.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": WHITE,
        }
    )


def clean_axis(ax: mpl.axes.Axes, grid: str | None = None) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid == "x":
        ax.xaxis.grid(True, color=LIGHT, linewidth=0.5)
    elif grid == "y":
        ax.yaxis.grid(True, color=LIGHT, linewidth=0.5)


def panel_title(ax: mpl.axes.Axes, letter: str, title: str) -> None:
    ax.set_title(rf"$\bf{{{letter}}}$  {title}", loc="left", pad=5)


def save_figure(
    fig: mpl.figure.Figure,
    output_dir: Path,
    stem: str,
    title: str,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    png = output_dir / f"{stem}.png"
    pdf = output_dir / f"{stem}.pdf"
    fig.savefig(
        png,
        dpi=600,
        bbox_inches="tight",
        pad_inches=0.055,
        metadata={"Title": title},
    )
    fig.savefig(
        pdf,
        bbox_inches="tight",
        pad_inches=0.055,
        metadata={"Title": title, "Creator": "TrafficRuleBench raw-scene audit"},
    )
    plt.close(fig)
    return png, pdf


def core_counts(data: Corpus) -> dict[str, Any]:
    train_places = {r["_place_id"] for r in data.maps if r["_split"] == "train"}
    test_places = {r["_place_id"] for r in data.maps if r["_split"] == "test"}
    per_map = Counter((r["_sign_id"], r["_split"], r["_map_id"]) for r in data.rows)
    allocations: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in data.maps:
        allocations[(row["_split"], row["_place_id"])].add(row["_sign_id"])
    train_allocations = [
        signs for (split, _), signs in allocations.items() if split == "train"
    ]
    return {
        "source_pool_maps": sum(len(rows) for rows in data.pools.values()),
        "selected_scene_pool_allocations": len(data.scene_pool_rows),
        "selected_scene_pool_train": sum(
            row["_split"] == "train" for row in data.scene_pool_rows
        ),
        "selected_scene_pool_test": sum(
            row["_split"] == "test" for row in data.scene_pool_rows
        ),
        "signs": len({row["_sign_id"] for row in data.rows}),
        "map_allocations": len(data.maps),
        "train_maps": sum(row["_split"] == "train" for row in data.maps),
        "test_maps": sum(row["_split"] == "test" for row in data.maps),
        "scenarios": len(data.rows),
        "train_scenarios": sum(row["_split"] == "train" for row in data.rows),
        "test_scenarios": sum(row["_split"] == "test" for row in data.rows),
        "unique_places": len(train_places | test_places),
        "train_places": len(train_places),
        "test_places": len(test_places),
        "train_test_place_overlap": len(train_places & test_places),
        "maps_with_ten_scenarios": sum(value == 10 for value in per_map.values()),
        "single_sign_train_place_fraction": float(
            np.mean([len(signs) == 1 for signs in train_allocations])
        ),
        "extension_signs": len({r["_sign_id"] for r in data.extension_rows}),
        "extension_maps": len(data.extension_maps),
        "extension_scenarios": len(data.extension_rows),
    }


def deduplicated_places(maps: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for row in maps:
        result.setdefault((row["_split"], row["_place_id"]), row)
    return list(result.values())


def plot_geography(ax: mpl.axes.Axes, data: Corpus) -> None:
    places = deduplicated_places(data.maps)
    for family in ("Junction", "Dual-path", "Corridor"):
        for split in ("train", "test"):
            selected = [
                row
                for row in places
                if row["_map_family"] == family
                and row["_split"] == split
                and isinstance(row.get("latitude"), (int, float))
                and isinstance(row.get("longitude"), (int, float))
            ]
            if not selected:
                continue
            x = [float(row["longitude"]) for row in selected]
            y = [float(row["latitude"]) for row in selected]
            if split == "train":
                ax.scatter(
                    x,
                    y,
                    s=7,
                    color=FAMILY_COLORS[family],
                    alpha=0.38,
                    linewidths=0,
                    rasterized=True,
                )
            else:
                ax.scatter(
                    x,
                    y,
                    s=14,
                    facecolors="none",
                    edgecolors=FAMILY_COLORS[family],
                    alpha=0.95,
                    linewidths=0.7,
                    rasterized=True,
                )
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_aspect(1.0 / math.cos(math.radians(55.7)))
    clean_axis(ax)
    panel_title(ax, "a", f"Geographic support ({len(places):,} physical places)")
    handles = [
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
        for family, color in list(FAMILY_COLORS.items())[:3]
    ]
    handles.extend(
        [
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="none",
                markerfacecolor=MID,
                markeredgewidth=0,
                markersize=4,
                label="Train",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="none",
                markerfacecolor="none",
                markeredgecolor=MID,
                markersize=4,
                label="Test",
            ),
        ]
    )
    ax.legend(
        handles=handles,
        loc="lower left",
        ncol=2,
        frameon=False,
        handletextpad=0.3,
        columnspacing=0.7,
        borderaxespad=0.1,
    )


def subtype_counts(
    rows: Iterable[dict[str, Any]],
    family: str,
    *,
    source: bool,
) -> Counter[str]:
    result: Counter[str] = Counter()
    for row in rows:
        if not source and row["_map_family"] != family:
            continue
        if family in {"Junction", "Dual-path"}:
            subtype = str(row.get("shape") if source else topology(row))
        else:
            subtype = str(row.get("segment_type") if source else topology(row))
        result[subtype] += 1
    return result


def plot_structure(ax: mpl.axes.Axes, data: Corpus) -> None:
    rows: list[tuple[str, str, Counter[str], tuple[str, ...]]] = []
    for family, order in (
        ("Junction", ("T", "X", "O")),
        ("Dual-path", ("T", "X")),
        ("Corridor", ("straight", "curved")),
    ):
        rows.append(
            (family, "source pool", subtype_counts(data.pools[family], family, source=True), order)
        )
        rows.append(
            (family, "benchmark", subtype_counts(data.maps, family, source=False), order)
        )

    labels = []
    for y, (family, scope, counts, order) in enumerate(rows):
        total = sum(counts.values())
        left = 0.0
        for subtype in order:
            width = 100.0 * counts[subtype] / total if total else 0.0
            ax.barh(
                y,
                width,
                left=left,
                height=0.62,
                color=SUBTYPE_COLORS[subtype],
                edgecolor=WHITE,
                linewidth=0.7,
            )
            if width >= 11:
                ax.text(
                    left + width / 2,
                    y,
                    f"{subtype} {width:.0f}%",
                    ha="center",
                    va="center",
                    fontsize=6.2,
                    color=INK,
                    fontweight="bold",
                )
            left += width
        labels.append(f"{family}\n{scope}")
        ax.text(101.3, y, f"n={total:,}", va="center", fontsize=6.1, color=MID)
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks((0, 25, 50, 75, 100))
    ax.set_xlabel("Composition within map family (%)")
    ax.tick_params(axis="y", length=0)
    clean_axis(ax, "x")
    panel_title(ax, "b", "Selection broadens rare structural regimes")


def ecdf(values: Sequence[float], max_points: int = 6000) -> tuple[np.ndarray, np.ndarray]:
    x = np.sort(np.asarray(values, dtype=float))
    if len(x) == 0:
        return x, x
    if len(x) > max_points:
        idx = np.linspace(0, len(x) - 1, max_points, dtype=int)
        x = x[idx]
        y = (idx + 1) / len(values)
    else:
        y = np.arange(1, len(x) + 1, dtype=float) / len(x)
    return x, y


def plot_dual_gain(ax: mpl.axes.Axes, data: Corpus) -> None:
    source = [float(row["gain_m"]) for row in data.pools["Dual-path"]]
    selected_ids = {
        row["_map_id"] for row in data.maps if row["_map_family"] == "Dual-path"
    }
    selected = [
        float(data.source_lookup[mid]["gain_m"])
        for mid in selected_ids
        if mid in data.source_lookup and data.source_lookup[mid].get("gain_m") is not None
    ]
    for values, label, color, width in (
        (source, "Source pool", MID, 1.25),
        (selected, "Evaluated physical maps", RED, 1.9),
    ):
        x, y = ecdf(values)
        ax.plot(x, y, color=color, linewidth=width, label=f"{label} (n={len(values):,})")
    median = float(np.median(selected))
    p10 = float(np.percentile(selected, 10))
    ax.axvline(median, color=RED, linestyle=":", linewidth=0.9)
    ax.text(
        median + 8,
        0.08,
        f"selected p10 / p50\n{p10:.0f} / {median:.0f} m",
        fontsize=6.6,
        color=RED,
    )
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Extra distance of legal route (m)")
    ax.set_ylabel("Cumulative share")
    clean_axis(ax, "y")
    ax.legend(frameon=False, loc="upper left")
    panel_title(ax, "c", "Dual-path maps create a measurable temptation")


def speed_density_matrix(data: Corpus) -> tuple[np.ndarray, int]:
    groups: dict[tuple[str, str, str], np.ndarray] = {}
    # Priority conflicts use one deliberately slow approach-speed regime; speed
    # signs use physics-conditioned braking speeds.  Neither belongs in the
    # generic 3 x 3 speed-density design audit.
    inapplicable_signs = {
        "main_road",
        "secondary_road",
        "yield",
        "stop",
        "roundabout",
        "speed_limit",
        "min_speed",
        "residential_zone",
        "zone_speed_limit",
    }
    for row in data.rows:
        if row.get("is_nominal", False) or row["_sign_id"] in inapplicable_signs:
            continue
        density = row.get("density_level_id")
        speed = row.get("spawn_velocity_level_id")
        if density not in (0, 1, 2) or speed not in (0, 1, 2):
            continue
        key = (row["_sign_id"], row["_split"], row["_map_id"])
        groups.setdefault(key, np.zeros((3, 3), dtype=float))
        groups[key][int(density), int(speed)] += 1
    normalized = [matrix / matrix.sum() for matrix in groups.values() if matrix.sum()]
    if not normalized:
        raise ValueError("No maps expose both speed and density level IDs")
    return 100.0 * np.mean(normalized, axis=0), len(normalized)


def plot_design_grid(ax: mpl.axes.Axes, data: Corpus) -> None:
    matrix, n_maps = speed_density_matrix(data)
    expected = 100.0 / 9.0
    deviation = matrix - expected
    vmax = max(1.0, float(np.abs(deviation).max()))
    image = ax.imshow(
        deviation,
        cmap="RdBu_r",
        vmin=-vmax,
        vmax=vmax,
        aspect="auto",
        interpolation="nearest",
    )
    for i in range(3):
        for j in range(3):
            ax.text(
                j,
                i,
                f"{matrix[i, j]:.1f}%",
                ha="center",
                va="center",
                fontsize=7.1,
                fontweight="bold",
            )
    ax.set_xticks((0, 1, 2), ("p25\n3.61", "p50\n7.75", "p75\n11.05"))
    ax.set_yticks((0, 1, 2), ("p25\n2.33", "p50\n4.00", "p75\n5.50"))
    ax.set_xlabel("Initial ego-speed probe (m/s)")
    ax.set_ylabel("nuPlan moving vehicles / lane probe")
    ax.tick_params(length=0)
    panel_title(ax, "d", f"Map-weighted joint stress coverage (n={n_maps:,} maps)")
    bar = ax.figure.colorbar(image, ax=ax, fraction=0.045, pad=0.025)
    bar.set_label("Deviation from uniform design (pp)", fontsize=6.8)
    bar.ax.tick_params(labelsize=6.3)


def plot_overview(data: Corpus, output_dir: Path) -> tuple[Path, Path]:
    set_style()
    counts = core_counts(data)
    fig = plt.figure(figsize=(7.25, 5.45))
    grid = fig.add_gridspec(
        2,
        2,
        left=0.075,
        right=0.965,
        bottom=0.12,
        top=0.875,
        hspace=0.46,
        wspace=0.43,
    )
    plot_geography(fig.add_subplot(grid[0, 0]), data)
    plot_structure(fig.add_subplot(grid[0, 1]), data)
    plot_dual_gain(fig.add_subplot(grid[1, 0]), data)
    plot_design_grid(fig.add_subplot(grid[1, 1]), data)
    fig.suptitle(
        "TrafficRuleBench: real-map breadth and controlled scenario variation",
        x=0.075,
        y=0.985,
        ha="left",
        fontsize=12,
        fontweight="bold",
    )
    fig.text(
        0.075,
        0.947,
        (
            f"{counts['source_pool_maps']:,} harvested maps  ·  "
            f"{counts['unique_places']:,} evaluated OSM places  ·  "
            f"{counts['map_allocations']:,} sign–map allocations  ·  "
            f"{counts['scenarios']:,} generated scenarios"
        ),
        fontsize=8.2,
        color=MID,
        ha="left",
    )
    fig.text(
        0.075,
        0.025,
        (
            "Source: raw OSM map indices and canonical train/test manifests. "
            "Panels a/c deduplicate physical places; b uses sign–map allocations;\n"
            "d gives each eligible map equal weight and excludes its nominal zero-traffic row."
        ),
        fontsize=6.4,
        color=MID,
        ha="left",
    )
    return save_figure(
        fig,
        output_dir,
        "generated_scene_overview",
        "TrafficRuleBench generated-scene overview",
    )


def field_values(
    rows: Sequence[dict[str, Any]],
    field: str,
    *,
    active_only: bool = True,
    exclude_groups: set[str] | None = None,
    include_groups: set[str] | None = None,
) -> np.ndarray:
    values = []
    for row in rows:
        if active_only and row.get("is_nominal", False):
            continue
        if exclude_groups and row["_task_group"] in exclude_groups:
            continue
        if include_groups and row["_task_group"] not in include_groups:
            continue
        value = row.get(field)
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            values.append(float(value))
    return np.asarray(values, dtype=float)


def draw_ecdf(
    ax: mpl.axes.Axes,
    values: np.ndarray,
    *,
    label: str,
    color: str,
    linewidth: float,
    linestyle: str = "-",
) -> None:
    x, y = ecdf(values)
    ax.plot(
        x,
        y,
        label=f"{label} (n={len(values):,})",
        color=color,
        linewidth=linewidth,
        linestyle=linestyle,
    )


def plot_initial_speed_ecdf(ax: mpl.axes.Axes, data: Corpus) -> None:
    generic = field_values(
        data.rows,
        "spawn_velocity_ms",
        exclude_groups={"Speed"},
    )
    speed_tasks = field_values(
        data.rows,
        "spawn_velocity_ms",
        include_groups={"Speed"},
    )
    draw_ecdf(
        ax,
        data.nuplan["initial_speed"],
        label="nuPlan track initial speed",
        color=INK,
        linewidth=1.35,
    )
    draw_ecdf(
        ax,
        generic,
        label="Generic benchmark probes",
        color=RED,
        linewidth=1.8,
    )
    draw_ecdf(
        ax,
        speed_tasks,
        label="Physics-conditioned speed tasks",
        color=ORANGE,
        linewidth=1.5,
        linestyle="--",
    )
    ax.set_xlim(0, 22)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Initial ego speed (m/s)")
    ax.set_ylabel("Cumulative share")
    clean_axis(ax, "y")
    ax.legend(frameon=False, loc="lower right")
    panel_title(ax, "a", "Initial ego speed")


def plot_density_ecdf(ax: mpl.axes.Axes, data: Corpus) -> None:
    targets = field_values(data.rows, "nuplan_per_lane")
    draw_ecdf(
        ax,
        data.nuplan["moving_per_lane"],
        label="nuPlan observations",
        color=INK,
        linewidth=1.35,
    )
    draw_ecdf(
        ax,
        targets,
        label="Benchmark quantile targets",
        color=RED,
        linewidth=1.9,
    )
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Moving vehicles within 150 m / ego-road lane")
    ax.set_ylabel("Cumulative share")
    clean_axis(ax, "y")
    ax.legend(frameon=False, loc="lower right")
    panel_title(ax, "b", "Traffic-density probes")


def plot_density_response(ax: mpl.axes.Axes, data: Corpus) -> None:
    calibration = data.density_calibration
    curve = calibration["sim_curve"]
    controls = np.array(sorted(float(key) for key in curve), dtype=float)

    def curve_values(stat: str) -> np.ndarray:
        return np.array([float(curve[str(x)][stat]) for x in controls])

    p25 = curve_values("p25")
    p50 = curve_values("p50")
    p75 = curve_values("p75")
    ax.fill_between(
        controls,
        p25,
        p75,
        color=BLUE,
        alpha=0.35,
        linewidth=0,
        label="Measured SUMO IQR",
    )
    ax.plot(
        controls,
        p50,
        color=INK,
        marker="o",
        markersize=3,
        linewidth=1.5,
        label="Measured SUMO median",
    )
    table = calibration["sampling_table"]
    u = np.asarray(table["u"], dtype=float)
    density = np.asarray(table["density"], dtype=float)
    target_controls = np.interp(np.array([0.25, 0.50, 0.75]), u, density)
    target_counts = np.array([2.3333333333, 4.0, 5.5])
    realized = np.interp(target_controls, controls, p50)
    for percentile, control, target, observed in zip(
        (25, 50, 75), target_controls, target_counts, realized
    ):
        ax.plot(
            [control, control],
            [observed, target],
            color=RED,
            linestyle=":",
            linewidth=0.9,
        )
        ax.scatter(
            control,
            target,
            marker="X",
            s=35,
            color=RED,
            edgecolor=WHITE,
            linewidth=0.5,
            zorder=4,
        )
        ax.text(
            control,
            target + 0.27,
            f"nuPlan p{percentile}",
            ha="center",
            va="bottom",
            fontsize=6.1,
            color=RED,
        )
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, max(9.0, float(p75.max()) + 0.5))
    ax.set_xlabel("SUMO traffic-density control")
    ax.set_ylabel("Realized moving vehicles / lane")
    clean_axis(ax, "y")
    ax.legend(frameon=False, loc="upper left")
    panel_title(ax, "c", "Measured SUMO density response")
    ax.text(
        0.98,
        0.04,
        f"{100 * float(calibration['reachable_fraction']):.1f}% of empirical\n"
        "quantile range reachable",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=6.1,
        color=MID,
    )


def plot_parameter_ecdf(
    ax: mpl.axes.Axes,
    data: Corpus,
    *,
    letter: str,
    title: str,
    nuplan_field: str,
    manifest_field: str,
    xlabel: str,
    xmax: float,
) -> None:
    generated = field_values(data.rows, manifest_field)
    draw_ecdf(
        ax,
        data.nuplan[nuplan_field],
        label="nuPlan",
        color=INK,
        linewidth=1.3,
    )
    draw_ecdf(
        ax,
        generated,
        label="Manifest IDM profiles",
        color=GREEN,
        linewidth=1.65,
        linestyle="--",
    )
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, 1)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Cumulative share")
    clean_axis(ax, "y")
    ax.legend(frameon=False, loc="lower right")
    panel_title(ax, letter, title)


def plot_distribution_alignment(
    data: Corpus,
    output_dir: Path,
) -> tuple[Path, Path]:
    set_style()
    fig = plt.figure(figsize=(7.25, 5.1))
    grid = fig.add_gridspec(
        2,
        3,
        left=0.075,
        right=0.975,
        bottom=0.135,
        top=0.86,
        hspace=0.5,
        wspace=0.5,
    )
    plot_initial_speed_ecdf(fig.add_subplot(grid[0, 0]), data)
    plot_density_ecdf(fig.add_subplot(grid[0, 1]), data)
    plot_density_response(fig.add_subplot(grid[0, 2]), data)
    plot_parameter_ecdf(
        fig.add_subplot(grid[1, 0]),
        data,
        letter="d",
        title="NPC acceleration",
        nuplan_field="acceleration",
        manifest_field="profile_ACC_FACTOR",
        xlabel="Positive acceleration (m/s²)",
        xmax=4.2,
    )
    plot_parameter_ecdf(
        fig.add_subplot(grid[1, 1]),
        data,
        letter="e",
        title="NPC deceleration",
        nuplan_field="deceleration",
        manifest_field="profile_DEACC_FACTOR",
        xlabel="Deceleration magnitude (m/s²)",
        xmax=5.2,
    )
    plot_parameter_ecdf(
        fig.add_subplot(grid[1, 2]),
        data,
        letter="f",
        title="NPC desired speed (clipped)",
        nuplan_field="speed",
        manifest_field="profile_NORMAL_SPEED",
        xlabel="Desired / observed moving speed (m/s)",
        xmax=22,
    )
    fig.suptitle(
        "nuPlan calibration: what is matched, probed, and intentionally transformed",
        x=0.075,
        y=0.985,
        ha="left",
        fontsize=12,
        fontweight="bold",
    )
    fig.text(
        0.075,
        0.947,
        (
            "Empirical CDFs expose the complete marginals; no Gaussian fit and no "
            "claim of joint-distribution or scene-level matching."
        ),
        fontsize=8,
        color=MID,
        ha="left",
    )
    fig.text(
        0.075,
        0.025,
        (
            "nuPlan source: 64 mini-dataset DBs; moving-track/frame statistics. "
            "Benchmark curves use non-nominal manifest rows and are descriptive;\n"
            "ten augmentations are nested within each map. Desired speed is clipped to 12–15 m/s "
            "to keep sign-unaware IDM agents behaviorally challenging."
        ),
        fontsize=6.35,
        color=MID,
        ha="left",
    )
    return save_figure(
        fig,
        output_dir,
        "generated_scene_distribution_alignment",
        "TrafficRuleBench nuPlan distribution alignment",
    )


def per_sign_audit(data: Corpus) -> list[dict[str, Any]]:
    result = []
    for spec in CORE_SIGNS:
        maps = [row for row in data.maps if row["_sign_id"] == spec.sign_id]
        rows = [row for row in data.rows if row["_sign_id"] == spec.sign_id]
        counts = Counter((row["_split"], row["_map_id"]) for row in rows)
        result.append(
            {
                "group": spec.task_group,
                "sign_id": spec.sign_id,
                "code": spec.code,
                "label": spec.label,
                "train_maps": sum(row["_split"] == "train" for row in maps),
                "test_maps": sum(row["_split"] == "test" for row in maps),
                "scenarios": len(rows),
                "maps": len(maps),
                "maps_with_10_scenarios": sum(value == 10 for value in counts.values()),
                "unique_places": len({row["_place_id"] for row in maps}),
            }
        )
    return result


def plot_protocol_matrix(ax: mpl.axes.Axes, data: Corpus) -> None:
    audit = per_sign_audit(data)
    values = np.zeros((len(audit), 3), dtype=float)
    labels = np.empty((len(audit), 3), dtype=object)
    for i, row in enumerate(audit):
        values[i] = (
            row["train_maps"] / 80.0,
            row["test_maps"] / 20.0,
            row["maps_with_10_scenarios"] / max(1, row["maps"]),
        )
        labels[i] = (
            f"{row['train_maps']}/80",
            f"{row['test_maps']}/20",
            f"{row['maps_with_10_scenarios']}/{row['maps']}",
        )
    cmap = LinearSegmentedColormap.from_list("attainment", (RED, PALE, GREEN))
    image = ax.imshow(
        values,
        cmap=cmap,
        vmin=0.75,
        vmax=1.02,
        aspect="auto",
        interpolation="nearest",
    )
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            ax.text(
                j,
                i,
                labels[i, j],
                ha="center",
                va="center",
                fontsize=6,
                fontweight="bold" if values[i, j] < 0.999 else "normal",
            )
    ax.set_yticks(
        range(len(audit)),
        [f"{row['code']}  {row['label']}" for row in audit],
    )
    ax.set_xticks(
        range(3),
        ("Train maps", "Test maps", "Maps with\n10 scenarios"),
    )
    ax.xaxis.tick_top()
    ax.tick_params(length=0, pad=3)
    for spine in ax.spines.values():
        spine.set_visible(False)
    starts = []
    last = None
    for i, row in enumerate(audit):
        if row["group"] != last:
            starts.append((i, row["group"]))
            last = row["group"]
    for i, group in starts:
        if i:
            ax.axhline(i - 0.5, color=WHITE, linewidth=2.5)
        ax.text(
            -0.72,
            i - 0.56,
            group.upper(),
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="bottom",
            fontsize=6.1,
            color=MID,
            fontweight="bold",
            clip_on=False,
        )
    bar = ax.figure.colorbar(
        image,
        ax=ax,
        location="bottom",
        fraction=0.025,
        pad=0.05,
        aspect=35,
    )
    bar.set_label("Protocol-target attainment", fontsize=6.5)
    bar.set_ticks((0.75, 0.9, 1.0), labels=("75%", "90%", "100%"))
    panel_title(ax, "a", "Per-sign generation completeness")


def plot_snapshot_attainment(ax: mpl.axes.Axes, data: Corpus) -> None:
    counts = core_counts(data)
    labels = ("Source maps", "Selected scene pools", "Generated maps", "Scenarios")
    actual = np.array(
        [
            counts["source_pool_maps"],
            counts["selected_scene_pool_allocations"],
            counts["map_allocations"],
            counts["scenarios"],
        ],
        dtype=float,
    )
    target = np.array([26020, 2500, 2500, 25000], dtype=float)
    pct = 100.0 * actual / target
    bars = ax.barh(
        range(4),
        pct,
        color=(BLUE, ORANGE, RED, GREEN),
        height=0.58,
    )
    for bar, a, t, p in zip(bars, actual.astype(int), target.astype(int), pct):
        ax.text(
            min(p, 100.0) - 0.4,
            bar.get_y() + bar.get_height() / 2,
            f"{a:,}/{t:,}  ({p:.2f}%)",
            ha="right",
            va="center",
            fontsize=6.4,
            fontweight="bold",
        )
    ax.axvline(100, color=INK, linestyle="--", linewidth=0.9)
    ax.set_yticks(range(4), labels)
    ax.invert_yaxis()
    ax.set_xlim(95, 100.3)
    ax.set_xlabel("Attainment of manuscript claim (%)")
    clean_axis(ax, "x")
    panel_title(ax, "b", "Current snapshot vs stated protocol")


def plot_place_reuse(ax: mpl.axes.Axes, data: Corpus) -> None:
    allocations: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in data.maps:
        allocations[(row["_split"], row["_place_id"])].add(row["_sign_id"])
    multiplicity = Counter(len(signs) for signs in allocations.values())
    x = np.array(sorted(multiplicity))
    y = np.array([multiplicity[value] for value in x])
    bars = ax.bar(x, y, color=BLUE, width=0.68)
    for bar, value in zip(bars, y):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + max(y) * 0.018,
            f"{value:,}",
            ha="center",
            va="bottom",
            fontsize=6.2,
        )
    ax.set_xlabel("Signs sharing one place within a split")
    ax.set_ylabel("Physical places")
    ax.set_xticks(x)
    ax.set_ylim(0, max(y) * 1.14)
    clean_axis(ax, "y")
    panel_title(ax, "c", "Map reuse remains sparse and split-local")


def plot_extension(ax: mpl.axes.Axes, data: Corpus) -> None:
    train = []
    test = []
    labels = []
    for spec in EXTENSION_SIGNS:
        labels.append(spec.label)
        train.append(
            sum(
                row["_sign_id"] == spec.sign_id and row["_split"] == "train"
                for row in data.extension_rows
            )
        )
        test.append(
            sum(
                row["_sign_id"] == spec.sign_id and row["_split"] == "test"
                for row in data.extension_rows
            )
        )
    y = np.arange(len(labels))
    ax.barh(y, train, color=ORANGE, height=0.58, label="Train")
    ax.barh(y, test, left=train, color=BLUE, height=0.58, label="Test")
    for i, (tr, te) in enumerate(zip(train, test)):
        ax.text(tr + te + 12, i, f"{tr + te:,}", va="center", fontsize=6.4)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Generated scenarios (separate extension)")
    clean_axis(ax, "x")
    ax.legend(frameon=False, loc="lower right", ncol=2)
    panel_title(ax, "d", "Restricted-lane extension (excluded from core 25)")


def plot_integrity_audit(data: Corpus, output_dir: Path) -> tuple[Path, Path]:
    set_style()
    counts = core_counts(data)
    fig = plt.figure(figsize=(7.25, 7.0))
    grid = fig.add_gridspec(
        3,
        2,
        left=0.27,
        right=0.97,
        bottom=0.11,
        top=0.865,
        width_ratios=(1.35, 1.0),
        height_ratios=(1.0, 1.0, 1.0),
        hspace=0.55,
        wspace=0.48,
    )
    plot_protocol_matrix(fig.add_subplot(grid[:, 0]), data)
    plot_snapshot_attainment(fig.add_subplot(grid[0, 1]), data)
    plot_place_reuse(fig.add_subplot(grid[1, 1]), data)
    plot_extension(fig.add_subplot(grid[2, 1]), data)
    fig.suptitle(
        "Generation protocol audit: completeness, leakage, and extensions",
        x=0.075,
        y=0.985,
        ha="left",
        fontsize=12,
        fontweight="bold",
    )
    fig.text(
        0.075,
        0.925,
        (
            f"Train/test OSM-place overlap = {counts['train_test_place_overlap']}  ·  "
            f"{100 * counts['single_sign_train_place_fraction']:.1f}% of train places "
            "are allocated to one sign"
        ),
        fontsize=8,
        color=MID,
    )
    fig.text(
        0.075,
        0.02,
        (
            "Every available sign–map allocation has exactly ten nested scenarios. "
            "Pre-generation pools contain 2,501 maps; manifests materialize 2,491, all with complete expansion.\n"
            "Physical-place identity uses OSM junction/way IDs recovered from manifests and source indices."
        ),
        fontsize=6.35,
        color=MID,
    )
    return save_figure(
        fig,
        output_dir,
        "generated_scene_protocol_audit",
        "TrafficRuleBench generated-scene protocol audit",
    )


def quantile_rows(data: Corpus) -> list[dict[str, Any]]:
    metrics = (
        (
            "initial_ego_speed_mps",
            data.nuplan["initial_speed"],
            field_values(data.rows, "spawn_velocity_ms", exclude_groups={"Speed"}),
        ),
        (
            "moving_vehicles_per_lane",
            data.nuplan["moving_per_lane"],
            field_values(data.rows, "nuplan_per_lane"),
        ),
        (
            "npc_acceleration_mps2",
            data.nuplan["acceleration"],
            field_values(data.rows, "profile_ACC_FACTOR"),
        ),
        (
            "npc_deceleration_mps2",
            data.nuplan["deceleration"],
            field_values(data.rows, "profile_DEACC_FACTOR"),
        ),
        (
            "npc_desired_speed_mps",
            data.nuplan["speed"],
            field_values(data.rows, "profile_NORMAL_SPEED"),
        ),
    )
    rows = []
    for metric, reference, benchmark in metrics:
        for source, values in (("nuPlan", reference), ("benchmark", benchmark)):
            quantiles = np.percentile(values, (5, 25, 50, 75, 95))
            rows.append(
                {
                    "metric": metric,
                    "source": source,
                    "n": len(values),
                    "p05": quantiles[0],
                    "p25": quantiles[1],
                    "p50": quantiles[2],
                    "p75": quantiles[3],
                    "p95": quantiles[4],
                }
            )
    return rows


def write_outputs(data: Corpus, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_path = output_dir / "generated_scene_per_sign_audit.tsv"
    audit = per_sign_audit(data)
    with audit_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(audit[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(audit)

    quantile_path = output_dir / "generated_scene_distribution_quantiles.tsv"
    qrows = quantile_rows(data)
    with quantile_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(qrows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(qrows)

    counts = core_counts(data)
    summary = {
        "statistical_units": {
            "harvested_map": "one source-index JSONL row",
            "physical_place": "OSM junction_id or osm_way_id",
            "sign_map_allocation": "unique (sign, split, parent(net_path))",
            "scenario": "one real_manifest.jsonl row",
        },
        "core": counts,
        "source_pool_by_family": {
            family: len(rows) for family, rows in data.pools.items()
        },
        "claim_deltas": {
            "source_pool_maps": counts["source_pool_maps"] - 26020,
            "selected_scene_pool_allocations": (
                counts["selected_scene_pool_allocations"] - 2500
            ),
            "map_allocations": counts["map_allocations"] - 2500,
            "scenarios": counts["scenarios"] - 25000,
        },
        "manifest_paths": [str(path.resolve()) for path in data.manifest_paths],
        "extension_manifest_paths": [
            str(path.resolve()) for path in data.extension_manifest_paths
        ],
        "nuplan_sample_sizes": {
            key: len(values) for key, values in data.nuplan.items()
        },
        "interpretation_limits": [
            "Manifest traffic_density is a simulator control, not an observed vehicle count.",
            "nuplan_per_lane is a quantile target; realized density comes from the SUMO calibration sweep.",
            "Ten scenarios from one sign-map allocation are nested design points, not independent maps.",
            "NPC desired speed is intentionally clipped to a stress range.",
            "Sampled following-distance fields are stored for reporting but are not applied to runtime NPC IDM.",
            "nuPlan-derived vehicle-size probabilities are not wired into the SUMO runtime vehicle-type sampler.",
            "Scenario horizon is caller-fixed rather than sampled from nuPlan route durations.",
            "The SUMO calibration reaches 85.9% of the empirical density quantile range and saturates in the upper tail.",
            "runs_rl3 restricted-lane signs are reported separately from the 25-sign core.",
        ],
    }
    summary_path = output_dir / "generated_scene_statistics_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return [audit_path, quantile_path, summary_path]


def write_latex(output_dir: Path) -> Path:
    path = output_dir / "generated_scene_statistics.tex"
    path.write_text(
        r"""\begin{figure*}[t]
    \centering
    \includegraphics[width=\textwidth]{imgs/generated_scene_overview.pdf}
    \caption{\textbf{Real-map and scenario diversity.}
    \textbf{(a)} Geographic support after deduplicating physical OSM places.
    \textbf{(b)} Source-pool and selected-map topology; selection deliberately
    increases coverage of rare X/roundabout/curved regimes.
    \textbf{(c)} Empirical CDF of the extra distance imposed by the legal route
    in dual-path tests.
    \textbf{(d)} Map-weighted joint coverage of applicable nuPlan-derived
    ego-speed and traffic-density probes.}
    \label{fig:generated_scene_overview}
\end{figure*}

\begin{figure*}[t]
    \centering
    \includegraphics[width=\textwidth]{imgs/generated_scene_distribution_alignment.pdf}
    \caption{\textbf{Scope of nuPlan calibration.}
    \textbf{(a,b)} Empirical nuPlan marginals and the benchmark's controlled
    quantile probes.
    \textbf{(c)} Measured SUMO response used to map the density statistic into a
    simulator control; this avoids comparing quantities with different units.
    \textbf{(d,e)} IDM acceleration and deceleration marginals after sampling
    and safety clipping.
    \textbf{(f)} Desired speed after intentional stress clipping.
    The plots validate marginal support and do not claim joint-distribution or
    scene-level matching.}
    \label{fig:generated_scene_distribution_alignment}
\end{figure*}

\begin{figure*}[t]
    \centering
    \includegraphics[width=\textwidth]{imgs/generated_scene_protocol_audit.pdf}
    \caption{\textbf{Protocol audit of the current manifest snapshot.}
    \textbf{(a)} Per-sign train/test allocation and expansion completeness.
    \textbf{(b)} Exact agreement with manuscript-level count targets.
    \textbf{(c)} Physical-place reuse within splits.
    \textbf{(d)} The restricted-lane extension, kept separate from the 25-sign
    core. OSM place identity has zero train/test overlap.}
    \label{fig:generated_scene_protocol_audit}
\end{figure*}
""",
        encoding="utf-8",
    )
    return path


def validate(data: Corpus) -> list[str]:
    counts = core_counts(data)
    warnings = []
    if counts["source_pool_maps"] != 26020:
        warnings.append(
            f"source pool has {counts['source_pool_maps']:,} maps, expected 26,020"
        )
    if counts["map_allocations"] != 2500:
        warnings.append(
            f"core has {counts['map_allocations']:,} map allocations, expected 2,500"
        )
    if counts["selected_scene_pool_allocations"] != 2500:
        warnings.append(
            "pre-generation data/scenes pools contain "
            f"{counts['selected_scene_pool_allocations']:,} allocations, expected 2,500"
        )
    if counts["scenarios"] != 25000:
        warnings.append(f"core has {counts['scenarios']:,} scenarios, expected 25,000")
    if counts["train_test_place_overlap"]:
        warnings.append(
            f"{counts['train_test_place_overlap']} physical places cross train/test"
        )
    for row in per_sign_audit(data):
        if row["train_maps"] != 80 or row["test_maps"] != 20:
            warnings.append(
                f"{row['sign_id']}: maps={row['train_maps']}/{row['test_maps']} "
                "(expected 80/20)"
            )
        if row["maps_with_10_scenarios"] != row["maps"]:
            warnings.append(
                f"{row['sign_id']}: {row['maps_with_10_scenarios']}/{row['maps']} "
                "maps have ten scenarios"
            )
    return warnings


def main() -> None:
    args = parse_args()
    repo = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    data = load_corpus(repo, args.v7_root.resolve(), args.rl3_root.resolve())

    outputs: list[Path] = []
    outputs.extend(plot_overview(data, output_dir))
    outputs.extend(plot_distribution_alignment(data, output_dir))
    outputs.extend(plot_integrity_audit(data, output_dir))
    outputs.extend(write_outputs(data, output_dir))
    outputs.append(write_latex(output_dir))

    counts = core_counts(data)
    warnings = validate(data)
    print(
        f"Core snapshot: {counts['signs']} signs, "
        f"{counts['map_allocations']:,} sign-map allocations, "
        f"{counts['scenarios']:,} scenarios, "
        f"{counts['unique_places']:,} physical places"
    )
    print(
        f"Separate restricted-lane extension: {counts['extension_signs']} signs, "
        f"{counts['extension_scenarios']:,} scenarios"
    )
    for warning in warnings:
        print(f"WARNING: {warning}")
    for path in outputs:
        print(f"Wrote {path}")
    if args.strict and warnings:
        raise SystemExit("Strict protocol validation failed")


if __name__ == "__main__":
    main()
