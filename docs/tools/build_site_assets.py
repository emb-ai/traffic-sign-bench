#!/usr/bin/env python3
"""Export project-page media from the video materials in ``video/``.

Writes short H.264 loops (no audio, faststart), JPEG posters, resized sign
icons, country examples, and the Moscow road-network map into
``docs/static/site``. Re-run after changing the video materials:

    python docs/tools/build_site_assets.py
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
VIDEO = ROOT / "video"
PUBLIC = VIDEO / "build" / "public"
SOLUTION = PUBLIC / "converted" / "solution"
OUT = ROOT / "docs" / "static" / "site"

HERO_TILES = {
    "direction-right": SOLUTION / "dir_r_plant2_ft.mp4",
    "stop-a": SOLUTION / "junc_35925624_rl90_td25_sv0_v0_v0_s2642426466_carl_rule_default.mp4",
    "roundabout": SOLUTION / "rb_0bd89cc1a9bf_rl90_td50_sv0_v1_v1_s3334807197_carl_default.mp4",
    "direction-left-right": SOLUTION / "dir_l_r_plant2_ft.mp4",
    "no-right-turn": SOLUTION / "no_turn_r_plant2_ft.mp4",
    "speed-30": SOLUTION / "seg_25007184_0_l1_v1_rl120_td50_v1_v1_s1667659565_carl_rule_default.mp4",
    "yield": SOLUTION / "junc_247899940_rl90_td75_sv0_v1_v1_s4282348834_carl_rule_default.mp4",
    "blocked-road": SOLUTION / "junc_252847112_td50_sv1_v1_v1_s1120895108_carl_rule_default.mp4",
    "one-way-right": SOLUTION / "one_way_r_plant2_ft.mp4",
    "direction-straight-right": SOLUTION / "dir_s_r_plant2_ft.mp4",
    "stop-b": SOLUTION / "junc_4974239205_rl120_td25_sv0_v2_v2_s1054559104_carl_rule_default.mp4",
}

# Failure rollouts from the root README.md — keep the original GIFs (no re-encode).
EVAL_SHOWCASE = {
    "carl": ROOT / "assets/rollouts/yield_carl.gif",
    "plant2": ROOT / "assets/rollouts/crosswalk_plant2.gif",
    "ppo": ROOT / "assets/rollouts/ppo_dir_right.gif",
}

# Before/after pairs from the root README.md under assets/rollouts/plant2/.
FT_PAIRS = {
    "direction": (
        ROOT / "assets/rollouts/plant2/direction_s_l/plant2.gif",
        ROOT / "assets/rollouts/plant2/direction_s_l/plant2_ft_n2e8.gif",
    ),
    "speed": (
        ROOT / "assets/rollouts/plant2/speed/plant2.gif",
        ROOT / "assets/rollouts/plant2/speed/plant2_ft.gif",
    ),
}

REAL_MAPS = ("junction", "dual_path", "corridor")

SIGN_ICONS = (
    "speed_limit_50", "min_speed", "zone_speed_40", "residential_zone",
    "main_road", "end_main_road", "secondary_road", "secondary_road_right",
    "yield", "stop", "crosswalk", "roundabout",
    "direction_straight", "direction_right", "direction_left",
    "direction_straight_right", "direction_straight_left", "direction_left_right",
    "no_right_turn", "no_left_turn", "no_uturn", "no_entry",
    "one_way", "one_way_right", "one_way_left",
    "detour_right", "detour_left", "detour_either",
    "no_traffic", "no_overtaking", "no_stopping",
    "bus_lane_road", "bike_lane_road", "only_auto",
    "speed_limit_30", "direction_straight_right",
)

COUNTRIES = ("Russia", "Germany", "France", "Italy", "Turkey", "UK", "China")


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def encode(
    src: Path, dst: Path, vf: str, *,
    fps: int = 24, crf: int = 27, duration: float | None = None, intra: bool = False,
) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    trim = ["-t", str(duration)] if duration else []
    # Scroll-scrubbed clips need every frame to be a keyframe for smooth seeking.
    gop = ["-g", "1", "-bf", "0"] if intra else []
    ffmpeg(
        "-i", str(src), *trim,
        "-vf", f"{vf},fps={fps},format=yuv420p",
        "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), *gop,
        "-profile:v", "high", "-an", "-movflags", "+faststart",
        str(dst),
    )
    ffmpeg("-i", str(dst), "-frames:v", "1", "-q:v", "2", str(dst.with_suffix(".jpg")))


def flatten(src: Path, dst: Path, max_side: int, fmt: str = "PNG", quality: int = 82) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(src)
    image.thumbnail((max_side, max_side), Image.LANCZOS)
    if fmt == "JPEG":
        canvas = Image.new("RGB", image.size, "white")
        rgba = image.convert("RGBA")
        canvas.paste(rgba, mask=rgba.split()[-1])
        canvas.save(dst, "JPEG", quality=quality, optimize=True, progressive=True)
    else:
        image.save(dst, "PNG", optimize=True)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)

    # Hero: the PlanT-2 crosswalk rollout. Frame n is simulator step n (25 fps);
    # the checker flags the violation at step 47.
    problem = next((VIDEO / "gifs" / "problem").glob("*.gif"))
    encode(problem, OUT / "hero" / "crosswalk.mp4", "scale=640:640:flags=lanczos", fps=25, crf=26, intra=True)

    for name, src in HERO_TILES.items():
        encode(src, OUT / "tiles" / f"{name}.mp4", "scale=360:360:flags=lanczos", crf=28, duration=8)

    # Copy README GIFs as-is so the site matches the repo visuals exactly.
    for name, src in EVAL_SHOWCASE.items():
        dst = OUT / "eval" / f"{name}.gif"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        ffmpeg("-i", str(src), "-frames:v", "1", "-q:v", "2", str(dst.with_suffix(".jpg")))

    for name, (base, ft) in FT_PAIRS.items():
        for variant, src in (("base", base), ("ft", ft)):
            dst = OUT / "ft" / f"{name}-{variant}.gif"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            ffmpeg("-i", str(src), "-frames:v", "1", "-q:v", "2", str(dst.with_suffix(".jpg")))

    for name in REAL_MAPS:
        encode(PUBLIC / "real_maps" / f"{name}.gif", OUT / "maps" / f"{name}.mp4", "scale=480:480:flags=lanczos", crf=26)
        flatten(PUBLIC / "real_maps" / f"{name}.png", OUT / "maps" / f"{name}-crop.jpg", 900, "JPEG")
    flatten(PUBLIC / "figures" / "moscow_crops_overview.png", OUT / "maps" / "moscow.jpg", 1500, "JPEG", 80)

    for icon in dict.fromkeys(SIGN_ICONS):
        src = PUBLIC / "signs" / f"{icon}.png"
        if not src.exists():
            src = src.with_suffix(".jpg")
        flatten(src, OUT / "signs" / f"{icon}.png", 160)

    for group in ("speed", "priority", "routing", "obstacles"):
        flatten(PUBLIC / "fig1" / f"{group}.png", OUT / "checkers" / f"{group}.png", 640)

    for country in COUNTRIES:
        for sign in ("yield", "direction_left"):
            flatten(PUBLIC / "countries" / sign / f"{country}.png", OUT / "countries" / sign / f"{country.lower()}.png", 220)
    for flag in (PUBLIC / "flags").glob("*.png"):
        flatten(flag, OUT / "flags" / flag.name, 96)

    total = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    print(f"Wrote {total / 1e6:.1f} MB to {OUT}")


if __name__ == "__main__":
    main()
