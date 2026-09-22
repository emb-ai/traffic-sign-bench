#!/usr/bin/env bash
# cherry_one_row.sh <family> <scene_uid> <policy plant2|plant2_ft> <gpu>: one test episode with a GIF (same args as
# reports/cherry_gifs/scripts/one.sh and ft_rl3 eval_map20.sh). Output: icra-video/generated/cherry/<family>/<uid>/<policy>/
set -u
SM=/home/jovyan/shares/SR006.nfs2/smirnova
M=$SM/traffic-rule-bench-main; EVALTREE=$SM/trb_stop; PY=$SM/.conda-envs/plant2/bin/python3
FT_CK=$EVALTREE/third_party/plant2/PlanT/checkpoints_ft/nj_jt22_lr1e4_bs128_ld08/epoch=026_nj_jt22_lr1e4_bs128_ld08_1.ckpt
Z=/home/jovyan/shares/SR006.nfs2/zinkovich/zinkovich/traffic-rule-bench
FAM=$1; UID_=$2; POL=$3; GPU=$4
MAN=$Z/data/runs/$FAM/test/real_manifest.jsonl; SC=$Z/data/scenes/$FAM
O=$M/icra-video/generated/cherry/$FAM/$UID_/$POL; rm -rf "$O"; mkdir -p "$O/out" "$O/gifs"
SEED=$(echo "$UID_" | sed -E 's/.*seed([0-9]+).*/\1/'); SID=$(echo "$UID_" | sed -E 's/_lane0.*//; s/_rl[0-9]+.*//; s/_td[0-9]+.*//')
grep "\"seed\": $SEED" "$MAN" | grep "\"scene_id\": \"$SID\"" | head -1 > "$O/row.jsonl"
[ -s "$O/row.jsonl" ] || { echo "row not found $UID_" >&2; exit 2; }
args=(manifest="$O/row.jsonl" scenes_root="$SC" run_name=cherry_$POL output_dir="$O/out" max_steps=600 gif.enabled=true gif.dir="$O/gifs" gif.window_m=80)
case $POL in
  plant2)    args+=(policy=plant2 "model_path=$M/checkpoints/plant2_pretrain/epoch\=029_final_3.ckpt") ;;
  plant2_ft) args+=(policy=plant2 "model_path=${FT_CK//=/\\=}" plant2_action_mode=pid) ;;
esac
cd "$EVALTREE" || exit 1
env CUDA_VISIBLE_DEVICES=$GPU SDL_VIDEODRIVER=dummy OMP_NUM_THREADS=1 PYTHONPATH=$EVALTREE/third_party/metadrive:$EVALTREE \
    PLANT2_SIGN_RADIUS_M=120 DUAL_PATH_REROUTE=0 nice -n 19 "$PY" -m traffic_bench.eval run "${args[@]}" > "$O/run.log" 2>&1
echo "[$FAM $UID_ $POL] rc=$? gifs=$(ls $O/gifs | grep -c gif)"; tail -c 400 $O/out/episodes_*.jsonl 2>/dev/null | head -c 400
