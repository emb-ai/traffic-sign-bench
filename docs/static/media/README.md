Media used by the project page.

- `final.mp4`: the paper overview video, copied from `video/out/final.mp4`.
- `crosswalk-plant2.gif`: the opening PlanT-2 rollout cropped from the video,
  ending on the verifier's `STEP 50 · VIOLATION` state.
- `video-poster.jpg`: poster frame exported from the benchmark reveal chapter.
- `slides/`: settled chapter frames from the overview video (plus the authored
  baseline-evaluation slide) for the on-page deck.
- `rollouts/`: compressed baseline and PlanT 2.0 / PlanT 2.0-FT comparison GIFs
  (sourced from `assets/rollouts/`).

Regenerate overview media from the repository root:

```bash
bash docs/tools/build_site_media.sh
```

Compress rollouts after copying from `assets/`:

```bash
python docs/tools/compress_gifs.py docs/static/media/rollouts --in-place --max-side 560 --max-frames 80 --colors 96
```
