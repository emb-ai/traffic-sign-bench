"""Light assets for the architecture / fine-tuning preview (run locally).

Inputs (all real, pulled from the server):
  generated/finetune/arch/arch_frames.json   PlanT-2 training samples of the rank-1 selected trajectory (IDMe-s1)
                                             of scene c0 + targets, from extract_arch_frames.py
  generated/finetune/arch/bev_in_*.png       BEV raster exactly as the model receives it (rot90 + centre crop)
  generated/finetune/expert_scene_dirR.json  replay map + full-rate expert track of the same scene
Outputs (public/finetune/arch/):
  arch.json      per frame, everything in the EGO frame with x forward / y RIGHT (metres):
                 boxes, route, lanes, lines, targets (path / waypoints), expert future track
  bev_<f>.png    the model's BEV input, rotated for display so that forward is up, project colours

Conventions verified in this script (raises otherwise):
  boxes    : y right  (sign box matches the replay sign position at every extracted frame)
  route / path / waypoints : y left in the dump (path target matches the expert replay track) -> flipped here
  BEV      : ego-centred, 4 px/m, forward = image left in the model input (fit to replay lanes)
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "generated/finetune"
# usage: prepare_arch_assets.py <scene id> <scene json (rel. to generated/finetune)> <arch dir (rel.)>
SID, SCENE_JSON, ARCH_DIR = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = ROOT / "public/finetune/arch" / SID
OUT.mkdir(parents=True, exist_ok=True)

A = json.loads((SRC / ARCH_DIR / "arch_frames.json").read_text())
S = json.loads((SRC / SCENE_JSON).read_text())
track = next(e for e in S["experts"] if e["selected_rank"] == 1)["track"]  # replay step i+1 == dump frame i
npc_file = SRC / ARCH_DIR / "npc_tracks.json"
NPC = json.loads(npc_file.read_text()) if npc_file.exists() else None
sign_world = None
PAL = np.array([[255, 255, 255], [214, 214, 214], [235, 190, 60], [120, 150, 210]], dtype=np.uint8)


def w2e(p, ego):
    dx, dy = p[0] - ego[0], p[1] - ego[1]
    c, s = math.cos(ego[2]), math.sin(ego[2])
    return [round(c * dx + s * dy, 2), round(s * dx - c * dy, 2)]  # x forward, y right


def e2w(p, ego):
    c, s = math.cos(ego[2]), math.sin(ego[2])
    return [ego[0] + p[0] * c + p[1] * s, ego[1] + p[0] * s - p[1] * c]


def scene_vehicles(f, ego):
    if NPC is None:
        return []
    step = f["frame"] + 1
    inputs = [(b["x"], b["y"]) for b in f["boxes"] if b["class"] == "car"]
    out = []
    for oid, o in NPC["objects"].items():
        if oid == NPC["ego_id"]:
            continue
        q = next((q for q in o["track"] if q[0] == step), None)
        if q is None:
            continue
        x, y = w2e(q[1:3], ego)
        if abs(x) > 120 or abs(y) > 120:
            continue
        yaw = (q[3] - ego[2] + math.pi) % (2 * math.pi) - math.pi  # same convention as the dump boxes (checked)
        out.append({"x": x, "y": y, "yaw": round(yaw, 3), "extent": [o["length"] / 2, o["width"] / 2, 0.8],
                    "in_input": any(math.dist((x, y), p) < 1.5 for p in inputs)})
    missing = [p for p in inputs if p != (0.0, 0.0) and not any(math.dist(p, (v["x"], v["y"])) < 1.5 for v in out)]
    if missing:
        raise ValueError(f"frame {f['frame']}: model-input boxes without a replay vehicle: {missing}")
    return out


frames = []
for f in A["frames"]:
    ego = track[f["frame"] + 1]
    if math.hypot(ego[0] - f["ego_pos_global"][0], ego[1] - f["ego_pos_global"][1]) > 0.05:
        raise ValueError(f"frame {f['frame']}: dump pose != replay pose")
    sign = next(b for b in f["boxes"] if b["pdd_code"])
    if sign_world is None:
        sign_world = e2w((sign["x"], sign["y"]), ego)
    elif math.dist(w2e(sign_world, ego), (sign["x"], sign["y"])) > 0.1:
        raise ValueError(f"frame {f['frame']}: sign box does not match the y-right convention")
    flip = lambda pts: [[round(p[0], 2), round(-p[1], 2)] for p in pts]  # y left -> y right
    path = flip(f["targets"]["path"])
    fut = [w2e(p, ego) for p in track[f["frame"] + 1: f["frame"] + 42]]
    # beyond the distance actually travelled in 4 s, dataset.py extends the path along the final heading
    travelled = sum(math.dist(a, b) for a, b in zip(fut, fut[1:]))
    err = max(min(math.dist(p, q) for q in fut) for p in path[:max(2, int(travelled) - 1)])
    if err > 0.5:
        raise ValueError(f"frame {f['frame']}: path target is {err:.2f} m off the expert track")

    def near(poly, r=95):
        return any(abs(q[0]) < r and abs(q[1]) < r for q in poly)

    lanes = [[w2e(q, ego) for q in L] for L in S["lanes"]]
    lines = [[w2e(q, ego) for q in L] for L in S["lines"]]
    bev = np.array(Image.open(SRC / ARCH_DIR / f["bev_in"]))
    Image.fromarray(PAL[np.clip(np.rot90(bev, k=-1), 0, 3)]).resize((256, 256), Image.NEAREST).save(OUT / f"bev_{f['frame']:04d}.png")
    frames.append({
        "frame": f["frame"],
        "boxes": [{"class": b["class"], "pdd_code": b["pdd_code"], "x": round(b["x"], 2), "y": round(b["y"], 2),
                   "yaw": round(b["yaw"], 3), "extent": b["extent"]} for b in f["boxes"]],
        "route": flip(f["route_original"]),
        "lanes": [L for L in lanes if near(L)],
        "lines": [L for L in lines if near(L)],
        "speed_limit_kmh": round(f["speed_limit_mps"] * 3.6),
        "ego_speed_mps": round(f["ego_speed"], 2),
        "targets": {"path": path, "waypoints": flip(f["targets"]["waypoints"]),
                    "speed_mps": round(f["targets"]["speed_mps"], 2), "speed_two_hot": f["targets"]["speed_two_hot"],
                    "speed_bins_mps": f["targets"]["speed_bins_mps"]},
        "expert_future": fut,
        # every traffic participant of the replay at this step (ego frame); in_input = it is also a model-input box
        "scene_vehicles": scene_vehicles(f, ego),
        "bev": f"finetune/arch/{SID}/bev_{f['frame']:04d}.png",
        "bev_m": 32.0,  # 128 px at 4 px/m, ego-centred
    })

rank1 = next(e for e in S["experts"] if e["selected_rank"] == 1)
json.dump({"route_name": A["route"], "n_frames": A["n_frames"], "scene": SID,
           "expert": f"{rank1['policy']}/{rank1['variant']}", "sign_code": S["meta"]["sign_code"], "frames": frames},
          open(ROOT / "public/finetune/arch" / f"{SID}.json", "w"))
for fr in frames:
    s = next(b for b in fr["boxes"] if b["pdd_code"])
    print(SID, fr["frame"], "boxes", len(fr["boxes"]), "scene vehicles", len(fr["scene_vehicles"]),
          "in input", sum(v["in_input"] for v in fr["scene_vehicles"]), "sign", (s["x"], s["y"]), "lanes", len(fr["lanes"]),
          "v", fr["ego_speed_mps"], "target", fr["targets"]["speed_mps"])
