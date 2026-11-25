# TrafficSignBench project page

Static GitHub Pages site with no build-time JavaScript dependencies.

## Live MetaDrive challenge gallery

```bash
conda activate trafficsignbench
pip install -e ".[demo]"

# Requires the yield, crosswalk, blocked_road, and main_road run/scene subsets.
# Maximum-speed and detour demos reuse compatible Moscow roads from
# blocked_road and main_road respectively.
bash tools/run_live_demo.sh
```

Then open <http://localhost:8765>. The server hosts the static site and a
real MetaDrive session selected from four traffic-sign challenges (yield,
crosswalk, detour, maximum speed). Arrow-key state is sent over a WebSocket;
the server steps the benchmark environment, runs the matching executable
checker, and returns 10 FPS square top-down JPEG frames plus live telemetry.

Up to eight drivers are accepted at a time. MetaDrive/Panda3D has process-global
state, so the WebSocket gateway starts each active simulator in an isolated
spawned process. A connection with no control input is closed after two minutes
so abandoned browser tabs cannot hold a slot forever. Both limits are configurable:

```bash
TRAFFIC_BENCH_DEMO_MAX_SESSIONS=8 \
TRAFFIC_BENCH_DEMO_IDLE_TIMEOUT=120 \
bash tools/run_live_demo.sh
```

The first frame takes a few seconds while that session's environment starts.
`GET /api/health` reports `active_sessions`, `available_sessions`, and
`max_sessions`.

Run a simulator/rendering smoke test without opening a port:

```bash
python -m traffic_bench.demo.server --smoke-test
```

## Structure

- `index.html` — semantic page content and metadata
- `static/css/style.css` — responsive design (light page, dark evaluation section)
- `static/js/main.js` — hero intro timeline, sign-sorting animation, map links,
  counters, toggles, in-view video playback, and citation copy
- `static/js/live-simulator.js` — WebSocket video, telemetry, and controls
- `static/site/` — page media exported from `video/` (rollout loops, posters,
  sign icons, Moscow map, country examples)
- `static/media/` — project video and video poster
- `tools/build_site_assets.py` — reproducible export of `static/site/` from the
  video materials (`python docs/tools/build_site_assets.py`)
- `tools/build_site_media.sh` — reproducible media export from
  `video/out/final.mp4`

The old browser-only toy remains in `static/js/simulator.js` for reference but
is no longer loaded.

## Public deployment (GitHub Pages + live demo)

GitHub Pages cannot run Python. Keep the static site there and expose the
MetaDrive backend with an HTTPS WebSocket tunnel.

### One-command Quick Tunnel

```bash
conda activate trafficsignbench   # or zinkovich-plant2
bash tools/run_live_demo_public.sh
```

The script starts the demo server and a Cloudflare Quick Tunnel, then prints:

- the public `https://….trycloudflare.com` URL (serves the docs + `/api/drive`)
- a GitHub Pages link with `?ws=wss://…/api/drive` so the published site talks
  to your running backend

Open either link. The `?ws=` value is remembered in `localStorage` for later
visits to the Pages site until the tunnel URL changes.

### Stable reverse proxy

For a fixed hostname, terminate TLS yourself and set:

```html
<meta name="traffic-bench-demo-ws"
      content="wss://demo.example.org/api/drive">
```

The server already allows `https://emb-ai.github.io`. Extra origins:

```bash
bash tools/run_live_demo.sh \
  --allowed-origin https://emb-ai.github.io
```

The backend has no authentication. It only accepts the published project origin
and same-origin clients by default; prefer a named Cloudflare Tunnel or your own
reverse proxy for anything beyond demos.

## Rebuild media

```bash
bash docs/tools/build_site_media.sh
```

This command crops the PlanT-2 crosswalk rollout from the opening video chapter,
holds the `STEP 50 · VIOLATION` frame for readability, prepares the MP4 for
progressive playback, and exports the poster.

## GitHub Pages

Configure **Settings → Pages → Deploy from a branch**, using `main` and
`/docs` as the publishing source (or sync `docs/` into `gh-pages`).
