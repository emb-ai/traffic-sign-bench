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
sys.path.insert(0, str(T))
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
J = centres("junctions.jsonl"); S = centres("segments.jsonl")
junction_xy = {}
for line in open(idx / "junctions.jsonl"):
    d = json.loads(line)
    if d.get("center_xy"):
        junction_xy[str(d["junction_id"])] = tuple(map(float, d["center_xy"]))
D = []
for i, line in enumerate(open(idx / "dual_path_candidates.jsonl")):
    d = json.loads(line)
    if str(d.get("junction_id")) in junction_xy:
        x, y = junction_xy[str(d["junction_id"])]
        # Dual-path crops share junction centres. A tiny deterministic display
        # jitter keeps their orange markers visible instead of hiding under blue.
        a = i * 2.3999632297
        D.append((x + 85 * __import__("math").cos(a), y + 85 * __import__("math").sin(a)))
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
    # Tuned for a 790 px-wide 1080p video panel: the earlier hairlines vanished
    # after browser downsampling even though the 4000 px source looked correct.
    ax.add_collection(LineCollection(lines, colors="#8795a1", linewidths=1.0, alpha=0.72, zorder=1))
ax.scatter([p[0] for p in S], [p[1] for p in S], s=7.0, c="#7ea72a", lw=0, alpha=0.94, zorder=2)
ax.scatter([p[0] for p in D], [p[1] for p in D], s=7.0, c="#e8961f", lw=0, alpha=0.94, zorder=3)
ax.scatter([p[0] for p in J], [p[1] for p in J], s=7.0, c="#3c8dd8", lw=0, alpha=0.94, zorder=4)
fig.savefig(out, dpi=200, facecolor="white")
json.dump({"xlim": [xmin, xmax], "ylim": [ymin, ymax], "width_px": W, "height_px": H, "n_junctions": len(J), "n_segments": len(S), "n_dual_path": len(D), "roads_drawn": bool(lines)}, open(str(out) + ".json", "w"), indent=1)
print("wrote", out, W, H)
