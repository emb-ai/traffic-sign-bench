"""Render the three tightly framed map crops used by S03_RealMaps.

The previews intentionally omit spawn markers and legends: the scene adds its
own sign overlay and labels. Run from the repository root.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from traffic_bench.scene_collection.preview import (
    parse_sumo_net,
    render_network,
    routes_from_dual_path_meta,
)


OUTPUT_DIR = ROOT / "icra-video" / "public" / "real_maps"

SCENES = {
    "junction": {
        "path": ROOT / "data" / "scenes" / "yield" / "junc_1057163165",
        "bounds": (11986.58, 12326.58, 39806.64, 39997.88),
    },
    "dual_path": {
        "path": ROOT
        / "data"
        / "scenes"
        / "direction_right"
        / "dual_T_1303406452_l_r_b5c03734",
        "bounds": (35112.0, 35592.0, 15051.0, 15321.0),
    },
    "corridor": {
        "path": ROOT / "data" / "scenes" / "detour_right" / "seg_1241471060",
        "bounds": (10873.49, 11193.49, 33496.82, 33676.82),
    },
}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, config in SCENES.items():
        scene_dir = config["path"]
        meta = json.loads((scene_dir / "meta.json").read_text(encoding="utf-8"))
        edges, junctions = parse_sumo_net(scene_dir / "map.net.xml")

        baseline = None
        compliant = None
        if name == "dual_path":
            baseline, compliant, _ = routes_from_dual_path_meta(meta)
        elif name == "corridor":
            compliant = [str(meta["road_id"])]

        render_network(
            edges,
            junctions,
            OUTPUT_DIR / f"{name}.png",
            figsize=(12, 6.75),
            dpi=120,
            baseline_edge_ids=baseline,
            compliant_edge_ids=compliant,
            legend=False,
            show_spawn_marker=False,
            view_bounds=config["bounds"],
        )


if __name__ == "__main__":
    main()
