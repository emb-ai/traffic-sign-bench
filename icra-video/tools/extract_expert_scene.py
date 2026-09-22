"""Extract one real oracle-collection scene for the fine-tuning section of the ICRA video.

Reads (read-only) the collaborator's trajectory collection:
  data/trajectories/<sign>/final/_merged/all_runs.jsonl      outcome of every expert rollout
  data/trajectories/<sign>/final/experts/experts_scene_uid_top2.jsonl   the actual top-2 selection
  .../<policy>/by_scene/<scene_uid>/<policy>_<variant>/replay.pkl        MetaDrive replay (map + per-step poses)

Writes ONE json with, in MetaDrive coordinates:
  lanes / lines         map polygons and road lines stored inside the replay
  experts[]             policy, variant, outcome flags, per-step ego xy, F-score if it was a quality candidate
  selection             the real pick record (all_candidates with time_eff / comfort / F-score, ranks)
  snapshot              one frame of the top-ranked expert with every object (ego, vehicles, sign plates)

Usage: python extract_expert_scene.py <sign_dir> <scene_uid> <out.json> [snapshot_step]
Must be run with PYTHONPATH containing traffic-rule-bench-main and its metadrive (the pickles hold metadrive classes).
"""
import gzip
import json
import pickle
import re
import sys
from pathlib import Path

Z = Path("/home/jovyan/shares/SR006.nfs2/zinkovich/zinkovich/traffic-rule-bench/data/trajectories")


def fix(p: str) -> str:
    p = p.replace("/mnt/virtual_ai0001053-01202_SR006-nfs2", "/home/jovyan/shares/SR006.nfs2")
    return re.sub(r"trajectories_\d+_\d+", "final", p)


def load_replay(path: str):
    raw = open(path, "rb").read(2)
    opener = gzip.open if raw == b"\x1f\x8b" else open
    with opener(path, "rb") as f:
        return pickle.load(f)


def ego_track(rep):
    pts = []
    for fr in rep["frame"]:
        fi = fr[0]
        oid = fi._agent_to_object["default_agent"]
        s = fi.step_info.get(oid)
        if s is None:
            raise ValueError("ego missing in a frame")
        x, y = s["position"][:2]
        pts.append([round(float(x), 3), round(float(y), 3), round(float(s["heading_theta"]), 4)])
    return pts


def objects_at(rep, step: int):
    fi = rep["frame"][step][0]
    ego = fi._agent_to_object["default_agent"]
    out = []
    for oid, s in fi.step_info.items():
        t = s.get("type")
        tname = t.__name__ if hasattr(t, "__name__") else str(t)
        pos = s.get("position")
        if pos is None:
            continue
        o = {"id": oid, "type": tname, "x": float(pos[0]), "y": float(pos[1]),
             "heading": float(s.get("heading_theta") or 0.0), "is_ego": oid == ego}
        for k in ("length", "width", "sign_code", "pdd_code", "sign_class"):
            if k in s:
                o[k] = s[k] if isinstance(s[k], (int, float, str)) else str(s[k])
        out.append(o)
    return out


def main():
    sign, uid, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    snap_step = int(sys.argv[4]) if len(sys.argv) > 4 else None
    rows = [json.loads(l) for l in open(Z / sign / "final/_merged/all_runs.jsonl")]
    rows = [r for r in rows if r["scene_uid"] == uid]
    if len({(r["policy"], r["variant"]) for r in rows}) != 8:
        raise SystemExit(f"expected 8 expert runs for {uid}, got {len(rows)}")
    picks = [json.loads(l) for l in open(Z / sign / "final/experts/experts_scene_uid_top2.jsonl")]
    picks = sorted([p for p in picks if p["scene_uid"] == uid], key=lambda p: p["rank"])
    if not picks:
        raise SystemExit(f"no pick record for {uid}")
    cand_f1 = {(c["policy"], c["variant"]): c for c in picks[0]["all_candidates"]}
    selected = {(p["winner_policy"], p["winner_variant"]): p["rank"] for p in picks}

    experts, lanes, lines, meta = [], None, None, None
    for r in sorted(rows, key=lambda r: (r["policy"], r["variant"])):
        rep = load_replay(fix(r["pkl_path"]))
        if lanes is None:
            mf = rep["map_data"]["map_features"]
            lanes = [[[round(float(p[0]), 3), round(float(p[1]), 3)] for p in f["polygon"]]
                     for f in mf.values() if f.get("type", "").startswith("LANE") and len(f.get("polygon", [])) > 2]
            lines = [[[round(float(p[0]), 3), round(float(p[1]), 3)] for p in f["polyline"]]
                     for f in mf.values() if f.get("type", "").startswith("ROAD_LINE")]
        viol = {k: v for k, v in (r.get("violations_by_class_event") or {}).items() if v}
        key = (r["policy"], r["variant"])
        experts.append({
            "policy": r["policy"], "variant": r["variant"],
            "arrived_dest": bool(r["arrived_dest"]), "crashed": bool(r["crashed"]),
            "out_of_road": bool(r["out_of_road"]), "violations": viol,
            "final_step": int(r["final_step"]), "frame_smooth_ratio": r.get("frame_smooth_ratio"),
            "quality_candidate": key in cand_f1, "f1": cand_f1.get(key, {}).get("f1"),
            "time_eff": cand_f1.get(key, {}).get("time_eff"), "comfort": cand_f1.get(key, {}).get("comfort"),
            "selected_rank": selected.get(key),
            "track": ego_track(rep),
            "replay": fix(r["pkl_path"]),
        })
        if meta is None:
            meta = {k: r.get(k) for k in ("scene_id", "scene_uid", "sign_code", "sign_slug", "seed", "var_idx",
                                          "net_path", "initial_speed_mps")}

    top = next(e for e in experts if e["selected_rank"] == 1)
    rep = load_replay(top["replay"])
    step = snap_step if snap_step is not None else len(rep["frame"]) // 3
    snapshot = {"policy": top["policy"], "variant": top["variant"], "step": step, "objects": objects_at(rep, step)}
    snapshot_start = {"step": 0, "objects": objects_at(rep, 0)}

    json.dump({
        "meta": meta,
        "selection": {k: picks[0][k] for k in ("beta", "horizon", "scene_min_step", "best_idm_variant",
                                               "all_attempts_n", "all_passing_n", "passing_candidates_n",
                                               "all_candidates")} | {
            "ranks": [{"rank": p["rank"], "policy": p["winner_policy"], "variant": p["winner_variant"],
                       "f1": p["f1_score"]} for p in picks]},
        "experts": experts, "lanes": lanes, "lines": lines,
        "snapshot": snapshot, "snapshot_start": snapshot_start,
    }, open(out, "w"))
    print("wrote", out, "experts", len(experts), "lanes", len(lanes), "snapshot objects", len(snapshot["objects"]))
    for e in experts:
        print(f"  {e['policy']:12s} {e['variant']:8s} dest={e['arrived_dest']} crash={e['crashed']} "
              f"oor={e['out_of_road']} viol={e['violations']} steps={len(e['track'])} f1={e['f1']} rank={e['selected_rank']}")
    print("types in snapshot:", sorted({o["type"] for o in snapshot["objects"]}))


if __name__ == "__main__":
    main()
