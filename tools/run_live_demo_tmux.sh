#!/usr/bin/env bash
# Run the public MetaDrive demo inside a detached tmux session so it survives
# SSH disconnects.
#
# Usage:
#   bash tools/run_live_demo_tmux.sh
#   tmux attach -t traffic-demo
#   tmux kill-session -t traffic-demo
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION="${TRAFFIC_BENCH_DEMO_TMUX_SESSION:-traffic-demo}"
PORT="${TRAFFIC_BENCH_DEMO_PORT:-8765}"
# Physical GPU 0 is broken on this host — never leave CUDA unset / pinned to 0.
GPU="${TRAFFIC_BENCH_DEMO_GPU:-1}"
PY_BIN="${TRAFFIC_BENCH_DEMO_PYTHON:-/home/jovyan/.mlspace/envs/zinkovich-plant2/bin}"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is required but not installed" >&2
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "[tmux-demo] session '$SESSION' already exists"
  echo "  attach: tmux attach -t $SESSION"
  echo "  kill:   tmux kill-session -t $SESSION"
  if [[ -f /tmp/traffic-bench-demo/public_url.txt ]]; then
    echo "  url:    $(cat /tmp/traffic-bench-demo/public_url.txt)"
  fi
  exit 0
fi

# Symlink demo manifests from runs_icra2027 when data/runs is incomplete.
mkdir -p "$REPO_ROOT/data/runs/yield/test" \
         "$REPO_ROOT/data/runs/crosswalk/test" \
         "$REPO_ROOT/data/runs/blocked_road/test"
for sign in yield crosswalk blocked_road; do
  src="$REPO_ROOT/data/runs_icra2027/$sign/test/real_manifest.jsonl"
  dst="$REPO_ROOT/data/runs/$sign/test/real_manifest.jsonl"
  if [[ -f "$src" && ! -e "$dst" ]]; then
    ln -sfn "$src" "$dst"
  fi
done

CMD=$(cat <<EOF
cd "$REPO_ROOT"
export PATH="$PY_BIN:\$PATH"
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=$GPU
export DISPLAY=:2
export SDL_VIDEODRIVER=dummy
export SDL_AUDIODRIVER=dummy
export PULSE_SERVER=none
export PYTHONPATH="$REPO_ROOT/third_party/metadrive:$REPO_ROOT\${PYTHONPATH:+:\$PYTHONPATH}"
echo "[tmux-demo] starting on GPU $GPU, port $PORT"
bash tools/run_live_demo_public.sh --port $PORT
EOF
)

tmux new-session -d -s "$SESSION" bash -lc "$CMD"
echo "[tmux-demo] started session '$SESSION'"
echo "  attach: tmux attach -t $SESSION"
echo "  wait for URL in /tmp/traffic-bench-demo/public_url.txt"
