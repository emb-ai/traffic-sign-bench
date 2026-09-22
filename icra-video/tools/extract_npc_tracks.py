"""Extract every traffic participant of ONE real expert replay (run on the server, read-only on the replay).

Usage: python extract_npc_tracks.py <replay.pkl> <out.json>
Output: {"steps": N, "ego_id": id, "objects": {id: {"type", "length", "width", "track": [[step, x, y, heading], ...]}}}
MetaDrive world coordinates, one entry per replay step in which the object exists.
"""
import gzip
import json
import pickle
import sys

path, out = sys.argv[1], sys.argv[2]
raw = open(path, "rb").read(2)
with (gzip.open if raw == b"\x1f\x8b" else open)(path, "rb") as f:
    rep = pickle.load(f)
objs = {}
ego = None
for step, fr in enumerate(rep["frame"]):
    fi = fr[0]
    if ego is None:
        ego = fi._agent_to_object["default_agent"]
    for oid, s in fi.step_info.items():
        pos = s.get("position")
        if pos is None:
            continue
        t = s.get("type")
        tname = t.__name__ if hasattr(t, "__name__") else str(t)
        o = objs.setdefault(oid, {"type": tname, "length": float(s.get("length") or 0), "width": float(s.get("width") or 0), "track": []})
        o["track"].append([step, round(float(pos[0]), 2), round(float(pos[1]), 2), round(float(s.get("heading_theta") or 0.0), 3)])
json.dump({"steps": len(rep["frame"]), "ego_id": ego, "objects": objs}, open(out, "w"))
types = {}
for o in objs.values():
    types[o["type"]] = types.get(o["type"], 0) + 1
print("steps", len(rep["frame"]), "objects", len(objs), types)
