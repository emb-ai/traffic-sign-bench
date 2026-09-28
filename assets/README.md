# assets/

Media used by the top-level [`README.md`](../README.md). Nothing here is read at run time.

| Path | Content | Source |
| --- | --- | --- |
| `hero.gif` | rollout wall + title card (3×7 mosaic) | `video/trafficsignbench_scene` Remotion scene |
| `figures/*.png` | designed result and method figures | single frames of the project video, white margins trimmed |
| `rollouts/*_base.gif`, `*_ft.gif` | PlanT-2 vs PlanT-2-FT on four rules | curated closed-loop clips (`stop` 2.5, `detour` 4.2.1, `zone_speed` 5.31, `reroute` 4.1.6) |
| `rollouts/{junction,dual_path,corridor}.gif` | the three scene families | closed-loop rollouts on released scenes |
| `signs/*.png` | sign artwork, 128 px, transparent, square-padded | paper sign plates |

The `video/` Remotion project the figures were exported from is gitignored; keep a copy
outside the repo if you need to re-export.

Re-exporting a figure is a frame grab plus a trim:

```bash
ffmpeg -ss <seconds> -i <video>.mp4 -frames:v 1 frame.png
```

GIFs are two-pass ffmpeg (`palettegen` → `paletteuse`) at 8–12 fps and 260–880 px, 48–64
colours. Keep the total under roughly 20 MB so the README stays fast to load; `hero.gif` is
the only file above 2 MB.
