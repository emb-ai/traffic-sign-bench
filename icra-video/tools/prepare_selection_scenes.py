"""Build the expert-selection scenes for the fine-tuning section (run locally).

Inputs (extracted from the real oracle collection by extract_expert_scene.py, pulled from the server):
  generated/finetune/expert_scene_dirR.json          scene c0 (direction_right, current)
  generated/finetune/cands/c7_direction_left_right.json, c4_roundabout.json
  generated/finetune/cands/sign_frames.json          frame 0 of the rank-1 PlanT-2 dump: ego pose + sign boxes
Outputs: public/finetune/scenes/<id>.json  (map, 8 tracks, outcomes, real selection, sign world position)

Everything shown in the selection table is VERIFIED here against the real pick record; any inconsistency raises.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "generated/finetune"
OUT = ROOT / "public/finetune/scenes"
OUT.mkdir(parents=True, exist_ok=True)

SCENES = {
    "c0": SRC / "expert_scene_dirR.json",
    "c7": SRC / "cands/c7_direction_left_right.json",
    "c4": SRC / "cands/c4_roundabout.json",
    "n04": SRC / "cands2/n04_one_way_right.json",
    "n15": SRC / "cands2/n15_one_way_right.json",
}
signs = json.loads((SRC / "cands/sign_frames.json").read_text())
# scenes with an architecture dump: frame 0 of the rank-1 dump gives the ego pose + the sign box
for sid in SCENES:
    af = SRC / f"arch_{sid}/arch_frames.json"
    if sid not in signs and af.exists():
        f0 = next(f for f in json.loads(af.read_text())["frames"] if f["frame"] == 0)
        signs[sid] = {"pos_global": f0["ego_pos_global"], "theta": f0["ego_theta"],
                      "signs": [b for b in f0["boxes"] if b["pdd_code"]]}
# Geometric off-road check: the benchmark flag (`not vehicle.on_lane`, a ray cast) misses some exits inside SUMO
# junctions. A rollout is marked here when its ego centre stays outside EVERY lane polygon of the replay map for
# OFFROAD_MIN_STEPS consecutive steps. The recorded selection is left untouched; the video shows both.
OFFROAD_MIN_STEPS = 5


def inpoly(pt, poly):
    x, y = pt
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def first_offroad_step(track, lanes):
    run = 0
    for i, q in enumerate(track):
        if any(inpoly(q[:2], L) for L in lanes):
            run = 0
            continue
        run += 1
        if run >= OFFROAD_MIN_STEPS:
            return i - run + 1
    return None


def success(e):
    return (not e["crashed"]) and (not e["out_of_road"]) and e["arrived_dest"] and not any(e["violations"].values())


def verify(sid, d):
    sel = d["selection"]
    ex = {(e["policy"], e["variant"]): e for e in d["experts"]}
    if len(ex) != 8:
        raise ValueError(f"{sid}: expected 8 experts, got {len(ex)}")
    ok = {k for k, e in ex.items() if success(e)}
    cands = {(c["policy"], c["variant"]): c["f1"] for c in sel["all_candidates"]}
    if len(ok) != sel["all_passing_n"]:
        raise ValueError(f"{sid}: successful {len(ok)} != all_passing_n {sel['all_passing_n']}")
    if not set(cands) <= ok:
        raise ValueError(f"{sid}: a quality candidate is not successful: {set(cands) - ok}")
    non_idm_ok = {k for k in ok if k[0] != "idm_rule"}
    if non_idm_ok != {k for k in cands if k[0] != "idm_rule"}:
        raise ValueError(f"{sid}: successful non-IDM experts differ from the non-IDM candidates")
    idm_c = [k for k in cands if k[0] == "idm_rule"]
    idm_ok = [k for k in ok if k[0] == "idm_rule"]
    if idm_ok and (len(idm_c) != 1 or idm_c[0][1] != sel["best_idm_variant"]):
        raise ValueError(f"{sid}: IDM candidate {idm_c} != best_idm_variant {sel['best_idm_variant']}")
    top = sorted(cands, key=lambda k: -cands[k])[:2]
    ranks = {(r["policy"], r["variant"]): r["rank"] for r in sel["ranks"]}
    if [k for k, _ in sorted(ranks.items(), key=lambda kv: kv[1])] != top:
        raise ValueError(f"{sid}: pick record {ranks} is not the top 2 by F-score {top}")
    for k, e in ex.items():
        if e["selected_rank"] != ranks.get(k) or (e["f1"] is not None) != (k in cands):
            raise ValueError(f"{sid}: per-expert fields disagree with the pick record for {k}")
    return {"successful": len(ok), "quality_candidates": len(cands), "retained": len(ranks),
            "idm_successful": len(idm_ok), "best_idm_variant": sel["best_idm_variant"]}


for sid, p in SCENES.items():
    d = json.loads(p.read_text())
    summary = verify(sid, d)
    rank1 = next(e for e in d["experts"] if e["selected_rank"] == 1)
    sf = signs[sid]
    ego = rank1["track"][1]  # dump frame 0 == replay step 1 of the rank-1 trajectory: checked below
    dpos = math.hypot(ego[0] - sf["pos_global"][0], ego[1] - sf["pos_global"][1])
    dth = abs((ego[2] - sf["theta"] + math.pi) % (2 * math.pi) - math.pi)
    if dpos > 0.5 or dth > 0.05:
        raise ValueError(f"{sid}: dump frame 0 pose differs from the rank-1 replay (Δpos {dpos:.2f} m, Δθ {dth:.3f})")
    sb = sf["signs"][0]
    th = ego[2]
    sx = ego[0] + sb["x"] * math.cos(th) + sb["y"] * math.sin(th)  # ego frame: x forward, y right
    sy = ego[1] + sb["x"] * math.sin(th) - sb["y"] * math.cos(th)

    lanes_all = [[q[:2] for q in L] for L in d["lanes"] if len(L) > 2]
    experts = []
    geo = {"successful": 0, "quality_candidates": 0}
    for e in d["experts"]:
        off = first_offroad_step(e["track"], lanes_all) if not e["out_of_road"] else None
        ok_geo = success(e) and off is None
        geo["successful"] += ok_geo
        geo["quality_candidates"] += ok_geo and e["f1"] is not None
        if off is not None and e["selected_rank"]:
            raise ValueError(f"{sid}: a SELECTED trajectory leaves the road geometrically ({e['policy']}/{e['variant']})")
        tr = e["track"][1:]  # drop the pre-spawn frame
        tr = tr[::2] + ([tr[-1]] if len(tr) % 2 == 0 else [])
        experts.append({k: e[k] for k in ("policy", "variant", "arrived_dest", "crashed", "out_of_road", "violations",
                                          "final_step", "quality_candidate", "f1", "selected_rank")}
                       | {"track": [[round(q[0], 2), round(q[1], 2), round(q[2], 3)] for q in tr],
                          # index in the down-sampled track where the geometric off-road run starts (None = never)
                          "offroad_idx": None if off is None else max(0, (off - 1) // 2)})
    xs = [q[0] for e in experts for q in e["track"]]
    ys = [q[1] for e in experts for q in e["track"]]
    pad = 18.0
    x0, x1, y0, y1 = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    cx, cy, half = (x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0) / 2
    view = [cx - half, cy - half, cx + half, cy + half]

    # traffic of the rank-1 replay (real NPC tracks), sampled on the same clock as the down-sampled ego tracks
    npcs = []
    nf = SRC / f"arch_{sid}/npc_tracks.json"
    if nf.exists():
        nt = json.loads(nf.read_text())
        for oid, o in nt["objects"].items():
            if oid == nt["ego_id"]:
                continue
            tr = [[(st - 1) // 2, q[0], q[1], q[2]] for st, *q in o["track"] if st >= 1 and (st - 1) % 2 == 0]
            if any(view[0] - 10 <= q[1] <= view[2] + 10 and view[1] - 10 <= q[2] <= view[3] + 10 for q in tr):
                npcs.append({"length": round(o["length"], 2), "width": round(o["width"], 2), "track": tr})

    def near(poly, m=70):
        return any(view[0] - m <= q[0] <= view[2] + m and view[1] - m <= q[1] <= view[3] + m for q in poly)

    json.dump({
        "id": sid, "meta": d["meta"], "selection": d["selection"], "summary": summary, "view": view,
        "summary_geometric": geo | {"retained": summary["retained"]},
        "lanes": [[[round(q[0], 2), round(q[1], 2)] for q in poly] for poly in d["lanes"] if near(poly)],
        "lines": [[[round(q[0], 2), round(q[1], 2)] for q in l] for l in d["lines"] if near(l)],
        "experts": experts,
        "sign": {"pdd_code": sb["pdd_code"], "x": round(sx, 2), "y": round(sy, 2)},
        "npcs": npcs,
    }, open(OUT / f"{sid}.json", "w"))
    print(sid, "npcs in view", len(npcs), "| geometric", geo, [f"{e['policy']}/{e['variant']}@{e['offroad_idx']}" for e in experts if e["offroad_idx"] is not None])
    print(sid, d["meta"]["sign_code"], summary, "sign", round(sx, 1), round(sy, 1), f"pose check Δ{dpos:.2f} m")
