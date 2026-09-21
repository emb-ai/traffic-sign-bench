"""Render a benchmark scene crop (SUMO net) as PNG, with dual-path routes when present.
Usage: python icra-video/tools/render_scene_map.py <scene_dir> <out_png> [--no-legend]
Uses traffic_bench.scene_collection.preview (project code); writes only to <out_png>."""
import json, sys
from pathlib import Path
from traffic_bench.scene_collection.preview import parse_sumo_net, render_network, routes_from_dual_path_meta
scene = Path(sys.argv[1]); out = Path(sys.argv[2]); legend = "--no-legend" not in sys.argv
meta = json.loads((scene / "meta.json").read_text())
edges, junctions = parse_sumo_net(scene / "map.net.xml")
base, comp, spawn = routes_from_dual_path_meta(meta)
print("baseline", base, "compliant", comp, "spawn", spawn)
render_network(edges, junctions, out, figsize=(12, 12), dpi=200, baseline_edge_ids=base, compliant_edge_ids=comp, legend=legend)
render_network(edges, junctions, out.with_name(out.stem + "_plain.png"), figsize=(12, 12), dpi=200, legend=False)
print("wrote", out)
