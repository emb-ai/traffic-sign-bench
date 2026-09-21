"""Render the real Moscow crop pool: SUMO road net (light grey) + crop centres from the
scene_collection index (junctions / segments / dual-path). Axes fill the figure, so
pixel <-> SUMO-xy mapping is linear; extents are written to <out>.json.
Writes only under icra-video/generated."""
import json, sys, time
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
T = Path(__file__).resolve().parents[2]
idx = T / "traffic_bench/scene_collection/maps/index"
out = Path(sys.argv[1])
def centres(fn, key="center_xy"):
    pts = []
    for line in open(idx / fn):
        line = line.strip()
        if not line: continue
        d = json.loads(line); c = d.get(key)
        if c: pts.append((float(c[0]), float(c[1])))
    return pts
J = centres("junctions.jsonl"); S = centres("segments.jsonl"); D = centres("dual_path_candidates.jsonl")
print("junctions", len(J), "segments", len(S), "dual", len(D))
lines = []
t0 = time.time()
try:
    from traffic_bench.scene_collection.preview import parse_sumo_net
    edges, junctions = parse_sumo_net(T / "traffic_bench/scene_collection/maps/nets/moscow.net.xml")
    for e in edges:
        for ln in e.get("lanes", []) or []:
            pts = ln.get("points") or ln.get("shape")
            if pts and len(pts) > 1: lines.append(pts)
        if not e.get("lanes"):
            pts = e.get("points") or e.get("shape")
            if pts and len(pts) > 1: lines.append(pts)
    print("net edges", len(edges), "polylines", len(lines), "in", round(time.time() - t0), "s")
except Exception as ex:
    print("net skipped:", repr(ex)[:200])
xs = [p[0] for p in J + S + D]; ys = [p[1] for p in J + S + D]
xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
pad = 0.02 * max(xmax - xmin, ymax - ymin)
xmin -= pad; xmax += pad; ymin -= pad; ymax += pad
W = 4000; H = int(W * (ymax - ymin) / (xmax - xmin))
fig = plt.figure(figsize=(W / 200, H / 200), dpi=200)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax); ax.axis("off"); ax.set_facecolor("white")
if lines:
    ax.add_collection(LineCollection(lines, colors="#c9c9c9", linewidths=0.25, zorder=1))
ax.scatter([p[0] for p in S], [p[1] for p in S], s=1.2, c="#a1cb35", lw=0, alpha=0.8, zorder=2)
ax.scatter([p[0] for p in D], [p[1] for p in D], s=1.2, c="#fcad38", lw=0, alpha=0.8, zorder=3)
ax.scatter([p[0] for p in J], [p[1] for p in J], s=1.2, c="#3c8dd8", lw=0, alpha=0.8, zorder=4)
fig.savefig(out, dpi=200, facecolor="white")
json.dump({"xlim": [xmin, xmax], "ylim": [ymin, ymax], "width_px": W, "height_px": H, "n_junctions": len(J), "n_segments": len(S), "n_dual_path": len(D), "roads_drawn": bool(lines)}, open(str(out) + ".json", "w"), indent=1)
print("wrote", out, W, H)
