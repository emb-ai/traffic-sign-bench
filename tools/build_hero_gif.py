#!/usr/bin/env python3
"""Build the animated rollout-wall hero used by the top-level README."""

from __future__ import annotations

import argparse
import math
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "video" / "gifs" / "solution"
DEFAULT_OUTPUT = ROOT / "assets" / "hero.gif"

COLS = 6
ROWS = 6
SOURCE_FPS = 25


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(name, size)


def centered_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    text_font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
) -> None:
    draw.text(xy, text, font=text_font, fill=fill, anchor="mm")


def smoothstep(value: float) -> float:
    value = min(1.0, max(0.0, value))
    return value * value * (3.0 - 2.0 * value)


def add_title_card(frame: Image.Image, opacity: float) -> None:
    if opacity <= 0:
        return

    width, height = frame.size
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    card_w = round(width * 0.64)
    card_h = round(height * 0.43)
    left = (width - card_w) // 2
    top = (height - card_h) // 2
    right = left + card_w
    bottom = top + card_h
    alpha = round(235 * opacity)

    draw.rounded_rectangle(
        (left, top, right, bottom),
        radius=18,
        fill=(255, 255, 255, alpha),
        outline=(222, 226, 230, round(220 * opacity)),
        width=1,
    )

    cx = width / 2
    ink = (35, 43, 49)
    muted = (82, 91, 98)
    blue = (20, 103, 145)
    green = (47, 119, 93)
    amber = (160, 105, 20)

    centered_text(draw, (cx, top + 30), "WE INTRODUCE", font(11, bold=True), muted)
    centered_text(draw, (cx, top + 62), "TrafficSignBench", font(31, bold=True), ink)
    centered_text(
        draw,
        (cx, top + 91),
        "The first large-scale benchmark to jointly combine",
        font(11),
        muted,
    )

    pill_y = top + 124
    pill_w = round(card_w * 0.275)
    gap = round(card_w * 0.025)
    pill_h = 38
    total_w = 3 * pill_w + 2 * gap
    pill_left = round(cx - total_w / 2)
    pills = (
        ("Broad Taxonomy", "34 traffic signs", blue),
        ("Rule Checkers", "automatic & verifiable", green),
        ("Targeted Scenarios", "29,000 closed-loop", amber),
    )
    for index, (title, subtitle, color) in enumerate(pills):
        x0 = pill_left + index * (pill_w + gap)
        draw.rounded_rectangle(
            (x0, pill_y, x0 + pill_w, pill_y + pill_h),
            radius=10,
            fill=(*color, round(18 * opacity)),
            outline=(*color, round(45 * opacity)),
        )
        centered_text(
            draw,
            (x0 + pill_w / 2, pill_y + 13),
            title,
            font(10, bold=True),
            color,
        )
        centered_text(
            draw,
            (x0 + pill_w / 2, pill_y + 27),
            subtitle,
            font(7),
            muted,
        )

    metric_y = top + 190
    metrics = (("34", "traffic signs"), ("29,000", "closed-loop scenarios"), ("17", "planners evaluated"))
    metric_centers = (cx - card_w * 0.31, cx, cx + card_w * 0.31)
    for x, (value, label) in zip(metric_centers, metrics):
        value_box = draw.textbbox((0, 0), value, font=font(19, bold=True))
        value_w = value_box[2] - value_box[0]
        draw.text((x - 4, metric_y), value, font=font(19, bold=True), fill=ink, anchor="ra")
        draw.text(
            (x + value_w / 2 - 1, metric_y - 1),
            label,
            font=font(7),
            fill=muted,
            anchor="la",
        )

    frame.alpha_composite(overlay)


def render_frame(
    sources: list[Image.Image],
    frame_index: int,
    fps: int,
    duration: float,
    size: tuple[int, int],
) -> Image.Image:
    width, height = size
    time_sec = frame_index / fps

    # The ICRA camera moved from 5.4× to 1× in 7.2 seconds. Here the same
    # movement fills nearly the entire, longer GIF so the reveal is calmer.
    zoom_progress = smoothstep(time_sec / (duration - 0.55))
    zoom = 5.4 + (1.0 - 5.4) * zoom_progress

    tile_w = width / COLS
    tile_h = height / ROWS
    projected_w = tile_w * zoom
    projected_h = tile_h * zoom

    # Start on a representative central rollout, then settle on the exact
    # centre of the complete 6×6 wall.
    start_center = (2.48, 2.38)
    end_center = (3.0, 3.0)
    center_x = (start_center[0] + (end_center[0] - start_center[0]) * zoom_progress) * tile_w
    center_y = (start_center[1] + (end_center[1] - start_center[1]) * zoom_progress) * tile_h
    offset_x = width / 2 - center_x * zoom
    offset_y = height / 2 - center_y * zoom

    canvas = Image.new("RGBA", size, (226, 228, 229, 255))
    source_frame = math.floor(time_sec * SOURCE_FPS)

    for index, source in enumerate(sources):
        row, col = divmod(index, COLS)
        x0 = round(offset_x + col * projected_w)
        y0 = round(offset_y + row * projected_h)
        x1 = round(offset_x + (col + 1) * projected_w)
        y1 = round(offset_y + (row + 1) * projected_h)
        if x1 <= 0 or y1 <= 0 or x0 >= width or y0 >= height:
            continue

        source.seek(source_frame % source.n_frames)
        image = source.convert("RGB")
        src_w, src_h = image.size
        crop_h = round(src_w * 9 / 16)
        crop_top = max(0, (src_h - crop_h) // 2)
        image = image.crop((0, crop_top, src_w, min(src_h, crop_top + crop_h)))
        image = image.resize((max(1, x1 - x0), max(1, y1 - y0)), Image.Resampling.LANCZOS)
        canvas.paste(image, (x0, y0))

        border = max(1, round(2 * min(1.0, zoom)))
        ImageDraw.Draw(canvas).rounded_rectangle(
            (x0, y0, x1 - 1, y1 - 1),
            radius=max(2, round(9 * zoom)),
            outline=(184, 188, 191, 255),
            width=border,
        )

    card_opacity = smoothstep((time_sec - 1.15) / 0.85)
    add_title_card(canvas, card_opacity)
    return canvas.convert("RGB")


def encode(
    source_dir: Path,
    output: Path,
    *,
    width: int,
    height: int,
    fps: int,
    duration: float,
    colors: int,
) -> None:
    paths = sorted(source_dir.glob("*.gif"))
    expected = COLS * ROWS
    if len(paths) != expected:
        raise SystemExit(f"Expected {expected} source GIFs in {source_dir}, found {len(paths)}")

    sources = [Image.open(path) for path in paths]
    output.parent.mkdir(parents=True, exist_ok=True)
    frame_count = round(duration * fps)

    with tempfile.TemporaryDirectory(prefix="traffic-sign-bench-hero-") as temp_dir:
        intermediate = Path(temp_dir) / "hero.mkv"
        palette = Path(temp_dir) / "palette.png"

        writer = subprocess.Popen(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "-s",
                f"{width}x{height}",
                "-r",
                str(fps),
                "-i",
                "-",
                "-an",
                "-c:v",
                "ffv1",
                str(intermediate),
            ],
            stdin=subprocess.PIPE,
        )
        assert writer.stdin is not None
        try:
            for frame_index in range(frame_count):
                frame = render_frame(sources, frame_index, fps, duration, (width, height))
                writer.stdin.write(frame.tobytes())
        finally:
            writer.stdin.close()
        if writer.wait() != 0:
            raise SystemExit("ffmpeg failed while writing the lossless intermediate")

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-i",
                str(intermediate),
                "-vf",
                f"palettegen=max_colors={colors}:stats_mode=diff",
                str(palette),
            ],
            check=True,
        )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-i",
                str(intermediate),
                "-i",
                str(palette),
                "-lavfi",
                "paletteuse=dither=sierra2_4a:diff_mode=rectangle",
                "-loop",
                "0",
                str(output),
            ],
            check=True,
        )

    for source in sources:
        source.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=576)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--colors", type=int, default=128)
    args = parser.parse_args()

    encode(
        args.source,
        args.output,
        width=args.width,
        height=args.height,
        fps=args.fps,
        duration=args.duration,
        colors=args.colors,
    )


if __name__ == "__main__":
    main()
