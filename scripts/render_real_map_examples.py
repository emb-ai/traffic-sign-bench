#!/usr/bin/env python3
"""Render clean paper figures for representative real-map scene families."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from traffic_bench.scene_collection.paths import (
    DUAL_PATH_CROPS,
    JUNCTION_CROPS,
    SEGMENT_CROPS,
)
from traffic_bench.scene_collection.preview import (
    parse_sumo_net,
    polyline_for_edge_ids,
    routes_from_dual_path_meta,
)


X_JUNCTION_SCENE = JUNCTION_CROPS / "X" / "junc_1077488622"
CURVED_CORRIDOR_SCENE = SEGMENT_CROPS / "seg_131700450_0"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "paper" / "imgs"

T_JUNCTION_SCENES = (
    JUNCTION_CROPS / "T" / "junc_1000613481",
    JUNCTION_CROPS / "T" / "junc_1001441173",
)
CURVED_SCENES = (
    CURVED_CORRIDOR_SCENE,
    SEGMENT_CROPS / "seg_24516088_0",
    SEGMENT_CROPS / "seg_985793343_0",
)
STRAIGHT_MULTILANE_SCENES = (
    SEGMENT_CROPS / "seg_10299371_10",
    SEGMENT_CROPS / "seg_243689859_0",
)
CURVED_MULTILANE_SCENES = (
    SEGMENT_CROPS / "seg_1083417194",
    SEGMENT_CROPS / "seg_26599983_0",
)
DUAL_PATH_SCENES = (
    DUAL_PATH_CROPS / "T" / "l_r" / "dual_T_1000613481_l_r_73424e57",
    DUAL_PATH_CROPS / "X" / "l_r" / "dual_X_1015545863_l_r_781eaf33",
)

BACKGROUND = "#f5f3ee"
SHADOW = "#c9c5bb"
ROAD_EDGE = "#30363b"
ASPHALT = "#515960"
LANE_MARKING = "#f5f1df"
BASELINE = "#c6453d"
COMPLIANT = "#2f7f4f"


def _bounds(
    lanes: Sequence[dict],
    *,
    center: tuple[float, float] | None = None,
    radius_m: float | None = None,
    padding_fraction: float = 0.07,
) -> tuple[float, float, float, float]:
    if center is not None and radius_m is not None:
        cx, cy = center
        return cx - radius_m, cx + radius_m, cy - radius_m, cy + radius_m

    points = [point for lane in lanes for point in lane["points"]]
    if not points:
        raise ValueError("cannot render a scene without lane geometry")
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    pad = max(xmax - xmin, ymax - ymin) * padding_fraction
    return xmin - pad, xmax + pad, ymin - pad, ymax + pad


def _points_per_meter(
    limits: tuple[float, float, float, float],
    figsize: tuple[float, float],
) -> float:
    xmin, xmax, ymin, ymax = limits
    return min(
        figsize[0] * 72.0 / max(xmax - xmin, 1.0),
        figsize[1] * 72.0 / max(ymax - ymin, 1.0),
    )


def _resample(
    points: Sequence[tuple[float, float]],
    count: int = 100,
) -> list[tuple[float, float]]:
    lengths = [0.0]
    for first, second in zip(points, points[1:]):
        lengths.append(
            lengths[-1] + math.hypot(second[0] - first[0], second[1] - first[1])
        )
    total = lengths[-1]
    if total <= 0.0:
        return [points[0]] * count

    sampled: list[tuple[float, float]] = []
    segment = 0
    for index in range(count):
        distance = total * index / (count - 1)
        while segment + 1 < len(lengths) - 1 and lengths[segment + 1] < distance:
            segment += 1
        span = max(lengths[segment + 1] - lengths[segment], 1e-9)
        alpha = (distance - lengths[segment]) / span
        first, second = points[segment], points[segment + 1]
        sampled.append(
            (
                first[0] + alpha * (second[0] - first[0]),
                first[1] + alpha * (second[1] - first[1]),
            )
        )
    return sampled


def _midline(
    first: Sequence[tuple[float, float]],
    second: Sequence[tuple[float, float]],
) -> tuple[list[tuple[float, float]], float]:
    left = _resample(first)
    right = _resample(second)
    direct = sum(
        math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(left, right)
    )
    reverse = sum(
        math.hypot(a[0] - b[0], a[1] - b[1])
        for a, b in zip(left, reversed(right))
    )
    if reverse < direct:
        right.reverse()
        distance = reverse / len(left)
    else:
        distance = direct / len(left)
    return (
        [((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0) for a, b in zip(left, right)],
        distance,
    )


def _paired_lane_markings(lanes: Iterable[dict]) -> list[list[tuple[float, float]]]:
    """Infer physical road pairs from nearby lane centerlines."""
    remaining = [lane for lane in lanes if len(lane.get("points") or []) >= 2]
    markings: list[list[tuple[float, float]]] = []
    while len(remaining) >= 2:
        first = remaining.pop(0)
        candidates = [
            (*_midline(first["points"], lane["points"]), index)
            for index, lane in enumerate(remaining)
        ]
        marking, _distance, match_index = min(candidates, key=lambda item: item[1])
        remaining.pop(match_index)
        markings.append(marking)
    return markings


def _adjacent_lane_markings(lanes: Iterable[dict]) -> list[list[tuple[float, float]]]:
    """Draw separators between adjacent lanes of one directed road edge."""

    def _lane_index(lane: dict) -> int:
        try:
            return int(str(lane.get("lane_id") or "").rsplit("_", 1)[-1])
        except ValueError:
            return 0

    ordered = sorted(lanes, key=_lane_index)
    return [
        _midline(first["points"], second["points"])[0]
        for first, second in zip(ordered, ordered[1:])
    ]


def _render(
    *,
    lanes: Sequence[dict],
    junctions: Sequence[dict],
    limits: tuple[float, float, float, float],
    out_stem: Path,
    lane_markings: Sequence[Sequence[tuple[float, float]]],
    route_polylines: Sequence[
        tuple[Sequence[tuple[float, float]], str]
    ] = (),
    figsize: tuple[float, float] = (4.2, 4.2),
) -> None:
    fig, ax = plt.subplots(figsize=figsize, facecolor=BACKGROUND)
    ax.set_facecolor(BACKGROUND)
    points_per_meter = _points_per_meter(limits, figsize)

    # Each SUMO lane is drawn at its physical width. Adjacent strokes merge
    # into one road surface while retaining a subtle lane-level structure.
    for lane in lanes:
        points = lane.get("points") or []
        if len(points) < 2:
            continue
        width_m = float(lane.get("width") or 3.2)
        ax.plot(
            [point[0] for point in points],
            [point[1] for point in points],
            color=SHADOW,
            linewidth=(width_m + 1.3) * points_per_meter,
            solid_capstyle="butt",
            solid_joinstyle="round",
            zorder=1,
        )

    for lane in lanes:
        points = lane.get("points") or []
        if len(points) < 2:
            continue
        width_m = float(lane.get("width") or 3.2)
        ax.plot(
            [point[0] for point in points],
            [point[1] for point in points],
            color=ROAD_EDGE,
            linewidth=(width_m + 0.45) * points_per_meter,
            solid_capstyle="butt",
            solid_joinstyle="round",
            zorder=2,
        )
        ax.plot(
            [point[0] for point in points],
            [point[1] for point in points],
            color=ASPHALT,
            linewidth=width_m * points_per_meter,
            solid_capstyle="butt",
            solid_joinstyle="round",
            zorder=3,
        )

    if lane_markings:
        ax.add_collection(
            LineCollection(
                lane_markings,
                colors=LANE_MARKING,
                linewidths=max(0.7, 0.38 * points_per_meter),
                linestyles=(0, (7.0, 6.0)),
                alpha=0.92,
                capstyle="butt",
                zorder=4,
            )
        )

    # Cover lane-center guides inside the conflict area and retain the exact
    # junction footprint exported by SUMO.
    for junction in junctions:
        points = junction.get("points") or []
        if len(points) < 3:
            continue
        ax.add_patch(
            mpatches.Polygon(
                points,
                closed=True,
                facecolor=ASPHALT,
                edgecolor=ROAD_EDGE,
                linewidth=max(0.65, 0.24 * points_per_meter),
                joinstyle="round",
                zorder=5,
            )
        )

    for points, color in route_polylines:
        if len(points) < 2:
            continue
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        ax.plot(
            xs,
            ys,
            color=BACKGROUND,
            linewidth=max(2.7, 1.45 * points_per_meter),
            solid_capstyle="round",
            solid_joinstyle="round",
            zorder=6,
        )
        ax.plot(
            xs,
            ys,
            color=color,
            linewidth=max(1.75, 0.92 * points_per_meter),
            solid_capstyle="round",
            solid_joinstyle="round",
            zorder=7,
        )

    xmin, xmax, ymin, ymax = limits
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

    out_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        out_stem.with_suffix(".png"),
        dpi=360,
        facecolor=BACKGROUND,
    )
    fig.savefig(
        out_stem.with_suffix(".pdf"),
        facecolor=BACKGROUND,
    )
    plt.close(fig)


def render_x_junction(output_dir: Path) -> None:
    meta = json.loads((X_JUNCTION_SCENE / "meta.json").read_text(encoding="utf-8"))
    lanes, junctions = parse_sumo_net(X_JUNCTION_SCENE / "map.net.xml")
    junction_id = str(meta["junction_id"])
    target = next(junction for junction in junctions if str(junction["id"]) == junction_id)
    limits = _bounds(
        lanes,
        center=(float(target["x"]), float(target["y"])),
        radius_m=118.0,
    )
    _render(
        lanes=lanes,
        junctions=[target],
        limits=limits,
        out_stem=output_dir / "real_map_x_junction",
        lane_markings=_paired_lane_markings(lanes),
    )


def render_curved_corridor(output_dir: Path) -> None:
    meta = json.loads((CURVED_CORRIDOR_SCENE / "meta.json").read_text(encoding="utf-8"))
    all_lanes, _junctions = parse_sumo_net(CURVED_CORRIDOR_SCENE / "map.net.xml")
    road_id = str(meta["road_id"])
    lanes = [lane for lane in all_lanes if str(lane["id"]) == road_id]
    if not lanes:
        raise ValueError(f"road {road_id!r} not found in {CURVED_CORRIDOR_SCENE}")
    _render(
        lanes=lanes,
        junctions=[],
        limits=_bounds(lanes),
        out_stem=output_dir / "real_map_curved_corridor",
        lane_markings=_adjacent_lane_markings(lanes),
    )


def _render_junction_scene(scene_dir: Path, out_stem: Path) -> None:
    meta = json.loads((scene_dir / "meta.json").read_text(encoding="utf-8"))
    lanes, junctions = parse_sumo_net(scene_dir / "map.net.xml")
    junction_id = str(meta["junction_id"])
    target = next(junction for junction in junctions if str(junction["id"]) == junction_id)
    _render(
        lanes=lanes,
        junctions=[target],
        limits=_bounds(
            lanes,
            center=(float(target["x"]), float(target["y"])),
            radius_m=118.0,
        ),
        out_stem=out_stem,
        lane_markings=_paired_lane_markings(lanes),
    )


def _render_segment_scene(scene_dir: Path, out_stem: Path) -> None:
    meta = json.loads((scene_dir / "meta.json").read_text(encoding="utf-8"))
    all_lanes, _junctions = parse_sumo_net(scene_dir / "map.net.xml")
    road_id = str(meta["road_id"])
    lanes = [lane for lane in all_lanes if str(lane["id"]) == road_id]
    if not lanes:
        raise ValueError(f"road {road_id!r} not found in {scene_dir}")
    _render(
        lanes=lanes,
        junctions=[],
        limits=_bounds(lanes),
        out_stem=out_stem,
        lane_markings=_adjacent_lane_markings(lanes),
    )


def _render_dual_path_scene(scene_dir: Path, out_stem: Path) -> None:
    meta = json.loads((scene_dir / "meta.json").read_text(encoding="utf-8"))
    all_lanes, junctions = parse_sumo_net(scene_dir / "map.net.xml")
    baseline, compliant, _spawn = routes_from_dual_path_meta(meta)
    if not baseline or not compliant:
        raise ValueError(f"dual paths not found in {scene_dir}")

    baseline_poly = polyline_for_edge_ids(all_lanes, baseline)
    compliant_poly = polyline_for_edge_ids(all_lanes, compliant)
    _render(
        lanes=all_lanes,
        junctions=junctions,
        limits=_bounds(all_lanes, padding_fraction=0.08),
        out_stem=out_stem,
        lane_markings=[],
        route_polylines=(
            (compliant_poly, COMPLIANT),
            (baseline_poly, BASELINE),
        ),
    )


def _write_overview(
    items: Sequence[tuple[str, Path]],
    out_stem: Path,
) -> None:
    columns = 3
    rows = math.ceil(len(items) / columns)
    fig, axes = plt.subplots(
        rows,
        columns,
        figsize=(8.1, 2.85 * rows),
        facecolor="white",
    )
    axes_flat = list(axes.flat)
    for ax, (title, image_path) in zip(axes_flat, items):
        ax.imshow(plt.imread(image_path))
        ax.set_title(title, fontsize=10, color="#24282c", pad=5)
        ax.axis("off")
    for ax in axes_flat[len(items) :]:
        ax.axis("off")
    fig.subplots_adjust(
        left=0.015,
        right=0.985,
        bottom=0.015,
        top=0.975,
        wspace=0.055,
        hspace=0.13,
    )
    fig.savefig(out_stem.with_suffix(".png"), dpi=300, facecolor="white")
    fig.savefig(out_stem.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)


def render_extended_examples(output_dir: Path) -> None:
    examples_dir = output_dir / "real_map_examples"
    items: list[tuple[str, Path]] = []

    x_stem = examples_dir / "x_junction"
    _render_junction_scene(X_JUNCTION_SCENE, x_stem)
    items.append(("X junction", x_stem.with_suffix(".png")))

    for index, scene_dir in enumerate(T_JUNCTION_SCENES, 1):
        stem = examples_dir / f"t_junction_{index}"
        _render_junction_scene(scene_dir, stem)
        items.append((f"T junction {index}", stem.with_suffix(".png")))

    for index, scene_dir in enumerate(CURVED_SCENES, 1):
        stem = examples_dir / f"curved_{index}"
        _render_segment_scene(scene_dir, stem)
        items.append((f"Curved corridor {index}", stem.with_suffix(".png")))

    straight_lanes = (3, 4)
    for lanes_count, scene_dir in zip(straight_lanes, STRAIGHT_MULTILANE_SCENES):
        stem = examples_dir / f"straight_{lanes_count}_lanes"
        _render_segment_scene(scene_dir, stem)
        items.append((f"Straight · {lanes_count} lanes", stem.with_suffix(".png")))

    curved_lanes = (3, 4)
    for lanes_count, scene_dir in zip(curved_lanes, CURVED_MULTILANE_SCENES):
        stem = examples_dir / f"curved_{lanes_count}_lanes"
        _render_segment_scene(scene_dir, stem)
        items.append((f"Curved · {lanes_count} lanes", stem.with_suffix(".png")))

    dual_labels = ("Dual path · T", "Dual path · X")
    for index, (label, scene_dir) in enumerate(zip(dual_labels, DUAL_PATH_SCENES), 1):
        stem = examples_dir / f"dual_path_{index}"
        _render_dual_path_scene(scene_dir, stem)
        items.append((label, stem.with_suffix(".png")))

    _write_overview(items, output_dir / "real_map_examples_overview")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    render_x_junction(args.output_dir)
    render_curved_corridor(args.output_dir)
    render_extended_examples(args.output_dir)
    print(f"Wrote map examples to {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
