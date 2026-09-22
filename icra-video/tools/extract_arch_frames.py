"""Extract the real PlanT-2 training sample(s) for the architecture / fine-tuning preview (run on the server).

Reads (read-only) one dumped route of the fine-tuning data (ft_rl3 dump of a selected expert trajectory) and
reproduces, with the same code as third_party/plant2/PlanT/dataset.py (final run nj_jt22_lr1e4_bs128_ld08):
  inputs   boxes (class / pdd_code / x / y / yaw / extent), route_original[:20], speed_limit, BEV raster
           (rot90 + crop [64:-64, 64:-64] exactly as dataset.py feeds the ResNet)
  targets  waypoints : 8 future ego positions, WPS_STRIDE=1           (dataset.py __getitem__)
           path      : realised future over 40 frames, arc-length 1 m, 20 points  (PATH_TARGET=future)
           speed     : min ego speed over the next 1 frame (TS_LOOKAHEAD=1, default window 1) → two-hot, 8 bins
The recipe values are the ones printed in the final run's training log
(tmp/ft_rl3/logs/train_nj_jt22_lr1e4_bs128_ld08.log).
Usage: python extract_arch_frames.py <route_dir> <out_dir> <frame> [<frame> ...]
"""
import gzip
import json
import os
import sys

import numpy as np
from PIL import Image

route, out = sys.argv[1], sys.argv[2]
frames = [int(f) for f in sys.argv[3:]]
os.makedirs(out, exist_ok=True)
TARGET_SPEEDS = [0.0, 4.0, 8.0, 10, 13.88888888, 16, 17.77777777, 20]  # plant_variables.py
MIN_EXTEND_STEP_M = 0.05


def load(p):
    return json.load(gzip.open(p))


def interpolate_route(points):  # dataset.py, verbatim logic
    r = np.concatenate((np.zeros_like(points[:1]), points))
    shift = np.roll(r, 1, axis=0)
    shift[0] = shift[1]
    d = np.cumsum(np.linalg.norm(r - shift, axis=1)) + np.arange(len(r)) * 1e-4
    x = np.arange(0, 20, 1)
    return np.array([np.interp(x, d, r[:, 0]), np.interp(x, d, r[:, 1])]).T


def future_path(mats, path_len=20):  # dataset.py _future_path
    pts = (np.linalg.inv(mats[0]) @ mats[:, :, 3].T).T[:, :2]
    travelled = float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum())
    if travelled < path_len + 1.0 and len(pts) > 2:
        step = pts[-1] - pts[-2]
        norm = float(np.linalg.norm(step))
        if norm < MIN_EXTEND_STEP_M:
            net = pts[-1] - pts[0]
            if np.linalg.norm(net) >= MIN_EXTEND_STEP_M:
                step, norm = net, float(np.linalg.norm(net))
            else:
                step, norm = np.array([1.0, 0.0]), 1.0
        pts = np.vstack([pts, pts[-1] + step / norm * (path_len + 1.0 - travelled)])
    return interpolate_route(pts[1:])


def two_hot(v):
    ts = TARGET_SPEEDS
    out = [0.0] * len(ts)
    if v <= ts[0]:
        out[0] = 1.0
    elif v >= ts[-1]:
        out[-1] = 1.0
    else:
        j = next(i for i in range(1, len(ts)) if v < ts[i])
        w = (v - ts[j - 1]) / (ts[j] - ts[j - 1])
        out[j - 1], out[j] = 1 - w, w
    return out


names = sorted(os.listdir(f"{route}/boxes"))
meas = [f"{route}/measurements/{n}" for n in names]
res = []
for f in frames:
    m = load(meas[f])
    b = load(f"{route}/boxes/{names[f]}")
    stem = names[f].split(".")[0]
    bev = np.array(Image.open(f"{route}/bev_no_car_semantics/{stem}.png"))
    if bev.ndim == 3:
        bev = bev[..., 0]
    bev_in = np.rot90(bev, k=1)[64:-64, 64:-64]  # torch.rot90(dims=(1,2)) on (C,H,W) == np.rot90(k=1) on (H,W)
    Image.fromarray(bev_in.astype(np.uint8)).save(f"{out}/bev_in_{f:04d}.png")
    fut = [load(meas[i]) for i in range(f, min(len(meas), f + 41))]
    mats = np.asarray([x["ego_matrix"] for x in fut], dtype=np.float64)
    inv = np.linalg.inv(mats[0])
    wps = (inv @ mats[1:9, :, 3].T).T[:, :2]
    speeds = [float(x["ego_speed"] if "ego_speed" in x else x["speed"]) for x in fut[:2]]
    v = min(speeds)
    v = 0.0 if v < 0.5 else v
    res.append({
        "frame": f,
        "boxes": [{"class": o["class"], "pdd_code": o.get("pdd_code"), "x": o["position"][0], "y": o["position"][1],
                   "yaw": o.get("yaw", 0.0), "extent": o.get("extent")} for o in b],
        "route_original": m["route_original"][:20],
        "route": m["route"][:20],
        "speed_limit_mps": m["speed_limit"],
        "ego_speed": speeds[0],
        "targets": {"waypoints": wps.tolist(), "path": future_path(mats).tolist(),
                    "speed_mps": v, "speed_two_hot": two_hot(v), "speed_bins_mps": TARGET_SPEEDS},
        "bev_in": f"bev_in_{f:04d}.png",
        "ego_pos_global": m.get("pos_global"), "ego_theta": m.get("theta"),
    })
json.dump({"route": os.path.basename(route), "n_frames": len(names), "frames": res}, open(f"{out}/arch_frames.json", "w"))
print("frames", frames, "of", len(names), "bev shape in", bev_in.shape, "labels", sorted(set(np.unique(bev_in).tolist())))
for r in res:
    print(r["frame"], "boxes", len(r["boxes"]), "sign", [(round(o["x"], 1), round(o["y"], 1)) for o in r["boxes"] if o["pdd_code"]],
          "v", round(r["ego_speed"], 2), "target v", round(r["targets"]["speed_mps"], 2),
          "wp8", [round(c, 1) for c in r["targets"]["waypoints"][-1]], "path19", [round(c, 1) for c in r["targets"]["path"][-1]],
          "route19", [round(c, 1) for c in r["route_original"][-1]])
