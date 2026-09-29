# TrafficSignBench project page

Static GitHub Pages site with no build-time JavaScript dependencies.

## Local preview

```bash
python -m http.server 8000 --directory docs
```

Then open <http://localhost:8000>.

## Structure

- `index.html` — semantic page content and metadata
- `static/css/style.css` — responsive light-theme design
- `static/js/main.js` — navigation, reveal effects, citation copy, and the
  browser-only interactive rule checker
- `static/media/` — teaser GIF, project video, and video poster
- `tools/build_site_media.sh` — reproducible media export from
  `video/out/final.mp4`

The driving playground is deterministic and runs entirely in the browser. It
does not load MetaDrive or call a backend, so it works on GitHub Pages.

## Rebuild media

```bash
bash docs/tools/build_site_media.sh
```

This command crops the PlanT-2 crosswalk rollout from the opening video chapter,
holds the `STEP 50 · VIOLATION` frame for readability, prepares the MP4 for
progressive playback, and exports the poster.

## GitHub Pages

Configure **Settings → Pages → Deploy from a branch**, using `main` and
`/docs`. The committed `.nojekyll` file keeps the static paths unchanged.
