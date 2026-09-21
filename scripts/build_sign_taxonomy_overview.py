#!/usr/bin/env python3
"""Build the traffic-sign taxonomy and verifier overview figure."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps


CANVAS_SIZE = (4800, 2800)
BACKGROUND = "#F4F6F8"
CARD_BACKGROUND = "#FFFFFF"
CARD_BORDER = "#DCE2E8"
TEXT = "#18212B"
MUTED = "#66717C"

CATEGORY_COLORS = {
    "Priority": "#4C78A8",
    "Speed": "#E76F51",
    "Obstacles": "#72A447",
    "Routing": "#E3A128",
}

OVERLAY_COLORS = {
    "blue": "#3757FF",
    "green": "#24B476",
    "red": "#E24848",
    "amber": "#F2A437",
    "cyan": "#2AB8CD",
    "white": "#FFFFFF",
}


@dataclass(frozen=True)
class TaxonomyItem:
    label: str
    icons: tuple[str, ...]


@dataclass(frozen=True)
class VerifierSpec:
    category: str
    run_key: str
    title: str
    icon: str
    rule: str
    legend: tuple[tuple[str, str], ...]
    event_fraction: float
    preferred_token: str = "_v2_"


TAXONOMY: dict[str, tuple[TaxonomyItem, ...]] = {
    "Priority": (
        TaxonomyItem("Main road", ("main_road.png",)),
        TaxonomyItem(
            "Secondary roads",
            (
                "secondary_road.png",
                "secondary_road_left.png",
                "secondary_road_right.png",
            ),
        ),
        TaxonomyItem("Stop", ("stop.png",)),
        TaxonomyItem("Yield", ("yield.png",)),
        TaxonomyItem("Crosswalk", ("crosswalk.png",)),
        TaxonomyItem("Roundabout", ("roundabout.png",)),
    ),
    "Speed": (
        TaxonomyItem(
            "Speed limit",
            ("speed_limit_40.png", "end_speed_limit_40.png"),
        ),
        TaxonomyItem(
            "Zone speed limit",
            ("zone_speed_40.png", "end_zone_speed_40.png"),
        ),
        TaxonomyItem(
            "Residential zone",
            ("@residential_start", "@residential_end"),
        ),
        TaxonomyItem("Min speed", ("min_speed.png",)),
    ),
    "Obstacles": (
        TaxonomyItem("Detour right", ("detour_right.png",)),
        TaxonomyItem("Detour left", ("detour_left.png",)),
        TaxonomyItem("Either side", ("detour_either.png",)),
        TaxonomyItem("Blocked road", ("no_traffic.png",)),
        TaxonomyItem("Bus lane road", ("bus_lane_road.png",)),
        TaxonomyItem("Bike lane road", ("bike_lane_road.png",)),
        TaxonomyItem("Bus road", ("bus_lane.png",)),
        TaxonomyItem("Bike road", ("bike_lane.png",)),
    ),
    "Routing": (
        TaxonomyItem("Straight", ("direction_straight.png",)),
        TaxonomyItem("Left", ("direction_left.png",)),
        TaxonomyItem("Right", ("direction_right.png",)),
        TaxonomyItem("Straight / right", ("direction_straight_right.png",)),
        TaxonomyItem("Straight / left", ("direction_straight_left.png",)),
        TaxonomyItem("Left / right", ("direction_left_right.png",)),
        TaxonomyItem("No right turn", ("no_right_turn.png",)),
        TaxonomyItem("No left turn", ("no_left_turn.png",)),
        TaxonomyItem("No entry", ("no_entry.png",)),
        TaxonomyItem("One way right", ("one_way_right.png",)),
        TaxonomyItem("One way left", ("one_way_left.png",)),
    ),
}

SIGN_COUNTS = {
    "Priority": 8,
    "Speed": 7,
    "Obstacles": 8,
    "Routing": 11,
}

VERIFIERS = (
    VerifierSpec(
        category="Priority",
        run_key="crosswalk",
        title="Crosswalk yield",
        icon="crosswalk.png",
        rule="Yield while a pedestrian occupies the crossing",
        legend=(
            ("amber", "verifier zone"),
            ("red", "occupied crossing"),
        ),
        event_fraction=0.55,
    ),
    VerifierSpec(
        category="Speed",
        run_key="speed_limit",
        title="Speed limit",
        icon="speed_limit_40.png",
        rule="Check ego speed inside the signed road segment",
        legend=(
            ("amber", "verified zone"),
            ("white", "ego velocity"),
        ),
        event_fraction=0.58,
    ),
    VerifierSpec(
        category="Obstacles",
        run_key="detour_right",
        title="Detour right",
        icon="detour_right.png",
        rule="Enter the allowed right lane before the obstacle",
        legend=(
            ("amber", "verifier zone"),
            ("green", "allowed lanes"),
            ("red", "obstacle"),
        ),
        event_fraction=0.50,
    ),
    VerifierSpec(
        category="Routing",
        run_key="one_way_right",
        title="One-way right",
        icon="one_way_right.png",
        rule="Match the selected outgoing edge against the forbidden set",
        legend=(
            ("green", "allowed exit"),
            ("red", "forbidden exit"),
        ),
        event_fraction=0.55,
    ),
)


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root / "paper" / "imgs",
    )
    return parser.parse_args()


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    candidates = (
        Path("/usr/share/fonts/truetype/dejavu") / name,
        Path("/usr/share/fonts") / name,
    )
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def alpha_crop(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    if alpha.getextrema() == (255, 255):
        rgb = rgba.convert("RGB")
        background = Image.new("RGB", rgb.size, "white")
        diff = ImageChops.difference(rgb, background).convert("L")
        diff = diff.point(lambda value: 255 if value > 7 else 0)
        bbox = diff.getbbox()
    else:
        bbox = alpha.getbbox()
    return rgba.crop(bbox) if bbox else rgba


def residential_icon(*, ended: bool) -> Image.Image:
    """Draw a neutral international-style residential-zone pictogram."""
    size = 420
    image = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (24, 24, size - 24, size - 24),
        radius=30,
        fill="white",
        outline="#20252A",
        width=12,
    )
    draw.polygon(
        ((80, 180), (165, 105), (250, 180)),
        fill="#4C78A8",
        outline="#20252A",
    )
    draw.rectangle(
        (100, 178, 230, 300),
        fill="#D7E8F5",
        outline="#20252A",
        width=8,
    )
    draw.rectangle((150, 225, 185, 300), fill="#4C78A8")
    draw.ellipse((275, 135, 315, 175), fill="#20252A")
    draw.line((295, 175, 295, 250), fill="#20252A", width=12)
    draw.line((295, 195, 258, 225), fill="#20252A", width=10)
    draw.line((295, 198, 330, 226), fill="#20252A", width=10)
    draw.line((295, 248, 265, 302), fill="#20252A", width=10)
    draw.line((295, 248, 330, 302), fill="#20252A", width=10)
    draw.rounded_rectangle(
        (70, 320, 350, 370),
        radius=20,
        fill="#E9EEF2",
        outline="#20252A",
        width=7,
    )
    draw.ellipse((105, 352, 145, 392), fill="#20252A")
    draw.ellipse((280, 352, 320, 392), fill="#20252A")
    if ended:
        overlay = Image.new("RGBA", image.size, (255, 255, 255, 70))
        image = Image.alpha_composite(image, overlay)
        draw = ImageDraw.Draw(image)
        for offset in (-90, -20, 50, 120):
            draw.line(
                (offset, size - 20, offset + size, 20),
                fill="#20252A",
                width=14,
            )
    return image


def load_icon(icon_dir: Path, name: str) -> Image.Image:
    if name == "@residential_start":
        return residential_icon(ended=False)
    if name == "@residential_end":
        return residential_icon(ended=True)
    path = icon_dir / name
    if not path.is_file():
        raise FileNotFoundError(path)
    return alpha_crop(Image.open(path))


def paste_contain(
    canvas: Image.Image,
    image: Image.Image,
    box: tuple[int, int, int, int],
) -> None:
    x0, y0, x1, y1 = box
    contained = ImageOps.contain(
        image.convert("RGBA"),
        (max(1, x1 - x0), max(1, y1 - y0)),
        Image.Resampling.LANCZOS,
    )
    x = x0 + (x1 - x0 - contained.width) // 2
    y = y0 + (y1 - y0 - contained.height) // 2
    canvas.alpha_composite(contained, (x, y))


def centered_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    text_font: ImageFont.FreeTypeFont,
    fill: str,
    *,
    anchor: str = "mm",
) -> None:
    draw.multiline_text(
        xy,
        text,
        font=text_font,
        fill=fill,
        anchor=anchor,
        align="center",
        spacing=3,
    )


def draw_taxonomy_item(
    canvas: Image.Image,
    icon_dir: Path,
    box: tuple[int, int, int, int],
    item: TaxonomyItem,
    *,
    label_size: int,
) -> None:
    draw = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = box
    icon_bottom = y0 + int((y1 - y0) * 0.72)
    icon_gap = 10
    count = len(item.icons)
    available = x1 - x0 - icon_gap * max(0, count - 1)
    width = available // max(1, count)
    for index, name in enumerate(item.icons):
        ix0 = x0 + index * (width + icon_gap)
        icon = load_icon(icon_dir, name)
        paste_contain(
            canvas,
            icon,
            (ix0 + 4, y0 + 4, ix0 + width - 4, icon_bottom - 5),
        )
        if count == 2:
            centered_text(
                draw,
                (ix0 + width // 2, icon_bottom - 1),
                "START" if index == 0 else "END",
                font(max(16, label_size - 9), bold=True),
                MUTED,
                anchor="ms",
            )
    centered_text(
        draw,
        ((x0 + x1) // 2, y1 - 12),
        item.label,
        font(label_size, bold=True),
        TEXT,
        anchor="ms",
    )


def draw_grid(
    canvas: Image.Image,
    icon_dir: Path,
    items: tuple[TaxonomyItem, ...],
    region: tuple[int, int, int, int],
    *,
    columns: int,
    label_size: int,
) -> None:
    x0, y0, x1, y1 = region
    rows = (len(items) + columns - 1) // columns
    cell_w = (x1 - x0) / columns
    cell_h = (y1 - y0) / rows
    for index, item in enumerate(items):
        row, col = divmod(index, columns)
        left = int(x0 + col * cell_w)
        top = int(y0 + row * cell_h)
        right = int(x0 + (col + 1) * cell_w)
        bottom = int(y0 + (row + 1) * cell_h)
        draw_taxonomy_item(
            canvas,
            icon_dir,
            (left + 8, top + 4, right - 8, bottom - 4),
            item,
            label_size=label_size,
        )


def density_score(path: Path) -> tuple[int, int, int]:
    match = re.search(r"_td(\d+)", path.name)
    density = int(match.group(1)) if match else -1
    profile = 1 if "_v2_" in path.name or "_sv2_" in path.name else 0
    try:
        with Image.open(path) as image:
            frames = int(getattr(image, "n_frames", 1))
    except Exception:
        frames = 0
    return density, profile, frames


def latest_paper_verifier_gifs(repo_root: Path, run_key: str) -> Path:
    debug_root = repo_root / "data" / "runs" / run_key / "debug"
    candidates = []
    if debug_root.is_dir():
        for run in debug_root.iterdir():
            if not run.is_dir() or run.name == "latest":
                continue
            gif_dir = run / "gifs"
            if not gif_dir.is_dir():
                continue
            config = run / "config.yaml"
            config_text = config.read_text(encoding="utf-8") if config.is_file() else ""
            if "paper_verifier" in config_text:
                candidates.append(gif_dir)
    if not candidates:
        latest = debug_root / "latest" / "gifs"
        if latest.is_dir():
            return latest
        raise FileNotFoundError(f"No verifier GIF directory for {run_key}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def choose_source_gif(repo_root: Path, spec: VerifierSpec) -> Path:
    exact_dir = (
        repo_root
        / "data"
        / "runs"
        / spec.run_key
        / "debug"
        / "paper_verifier_exact"
        / "gifs"
    )
    exact_candidates = list(exact_dir.glob("*.gif")) if exact_dir.is_dir() else []
    if exact_candidates:
        return max(exact_candidates, key=lambda path: density_score(path))
    gif_dir = latest_paper_verifier_gifs(repo_root, spec.run_key)
    candidates = []
    for path in gif_dir.glob("*.gif"):
        score = density_score(path)
        if score[2] > 2:
            candidates.append((score, path))
    if not candidates:
        raise FileNotFoundError(f"No readable GIFs in {gif_dir}")
    preferred = [
        item for item in candidates if spec.preferred_token in item[1].name
    ]
    return max(preferred or candidates, key=lambda item: item[0])[1]


def draw_info_card(
    frame: Image.Image,
    icon_dir: Path,
    spec: VerifierSpec,
) -> Image.Image:
    result = frame.convert("RGBA")
    panel = Image.new("RGBA", result.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(panel)
    accent = CATEGORY_COLORS[spec.category]
    draw.rounded_rectangle(
        (22, 20, 615, 252),
        radius=18,
        fill=(255, 255, 255, 255),
        outline=(218, 224, 230, 255),
        width=2,
    )
    draw.rounded_rectangle((34, 32, 44, 238), radius=5, fill=accent)
    icon = load_icon(icon_dir, spec.icon)
    paste_contain(panel, icon, (62, 42, 132, 112))
    draw.text(
        (150, 42),
        spec.category.upper(),
        font=font(18, bold=True),
        fill=accent,
    )
    draw.text(
        (150, 68),
        spec.title,
        font=font(30, bold=True),
        fill=TEXT,
    )
    draw.multiline_text(
        (62, 130),
        spec.rule,
        font=font(21),
        fill=TEXT,
        spacing=5,
    )
    result = Image.alpha_composite(result, panel)
    return draw_legend_footer(result, spec)


def draw_legend_footer(
    frame: Image.Image,
    spec: VerifierSpec,
) -> Image.Image:
    result = frame.convert("RGBA")
    footer = Image.new("RGBA", result.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(footer)
    legend_font = font(16, bold=True)
    content_width = sum(
        26 + int(draw.textlength(label, font=legend_font)) + 30
        for _color_name, label in spec.legend
    )
    footer_right = min(778, max(250, 44 + content_width))
    draw.rounded_rectangle(
        (22, 728, footer_right, 786),
        radius=16,
        fill=(255, 255, 255, 255),
        outline=(218, 224, 230, 255),
        width=2,
    )
    x, y = 44, 757
    for color_name, label in spec.legend:
        color = OVERLAY_COLORS[color_name]
        outline = "#9AA4AE" if color_name == "white" else color
        draw.ellipse(
            (x, y - 9, x + 18, y + 9),
            fill=color,
            outline=outline,
            width=2,
        )
        x += 26
        draw.text(
            (x, y),
            label,
            font=legend_font,
            fill=TEXT,
            anchor="lm",
        )
        x += int(draw.textlength(label, font=legend_font)) + 30
    return Image.alpha_composite(result, footer)


def enhance_gif(
    source: Path,
    output_dir: Path,
    icon_dir: Path,
    spec: VerifierSpec,
) -> tuple[Path, Path, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    gif_path = output_dir / f"{spec.run_key}_verifier.gif"
    frame_path = output_dir / f"{spec.run_key}_verifier.png"

    with Image.open(source) as image:
        frame_count = int(getattr(image, "n_frames", 1))
        event_index = min(
            frame_count - 1,
            max(0, int(round((frame_count - 1) * spec.event_fraction))),
        )
        start = max(0, event_index - 42)
        end = min(frame_count, event_index + 43)
        duration = int(image.info.get("duration", 40) or 40)
        frames = []
        representative = None
        for index in range(start, end):
            image.seek(index)
            processed = draw_info_card(image.convert("RGBA"), icon_dir, spec)
            rgb = processed.convert("RGB")
            frames.append(rgb)
            if index == event_index:
                representative = rgb.copy()
    if not frames or representative is None:
        raise RuntimeError(f"Failed to extract frames from {source}")

    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        optimize=True,
        disposal=2,
    )
    representative.save(frame_path, dpi=(300, 300))
    return gif_path, frame_path, event_index


def enhance_full_gif(
    source: Path,
    output_dir: Path,
    spec: VerifierSpec,
) -> Path:
    """Keep every episode frame and add only the compact colour legend."""
    output_dir.mkdir(parents=True, exist_ok=True)
    gif_path = output_dir / f"{spec.run_key}_verifier_full.gif"

    with Image.open(source) as image:
        frame_count = int(getattr(image, "n_frames", 1))
        duration = int(image.info.get("duration", 40) or 40)
        frames = []
        for index in range(frame_count):
            image.seek(index)
            processed = draw_legend_footer(image.convert("RGBA"), spec)
            frames.append(processed.convert("RGB"))
    if not frames:
        raise RuntimeError(f"Failed to extract frames from {source}")

    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        optimize=True,
        disposal=2,
    )
    return gif_path


def draw_group_panel(
    canvas: Image.Image,
    icon_dir: Path,
    frame_path: Path,
    spec: VerifierSpec,
    panel_box: tuple[int, int, int, int],
) -> None:
    draw = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = panel_box
    accent = CATEGORY_COLORS[spec.category]
    draw.rounded_rectangle(
        panel_box,
        radius=34,
        fill=CARD_BACKGROUND,
        outline=CARD_BORDER,
        width=5,
    )
    draw.rounded_rectangle(
        (x0, y0, x1, y0 + 26),
        radius=24,
        fill=accent,
    )
    draw.rectangle((x0, y0 + 13, x1, y0 + 26), fill=accent)
    draw.text(
        (x0 + 42, y0 + 64),
        spec.category,
        font=font(68, bold=True),
        fill=TEXT,
    )
    draw.text(
        (x1 - 42, y0 + 78),
        f"{SIGN_COUNTS[spec.category]} signs",
        font=font(36, bold=True),
        fill=accent,
        anchor="ra",
    )

    taxonomy_top = y0 + 150
    taxonomy_bottom = y0 + 1450
    items = TAXONOMY[spec.category]
    if spec.category == "Priority":
        draw_grid(
            canvas,
            icon_dir,
            items,
            (x0 + 28, taxonomy_top, x1 - 28, taxonomy_bottom),
            columns=2,
            label_size=38,
        )
    elif spec.category == "Speed":
        draw_grid(
            canvas,
            icon_dir,
            items,
            (x0 + 28, taxonomy_top, x1 - 28, taxonomy_bottom),
            columns=2,
            label_size=38,
        )
    elif spec.category == "Obstacles":
        draw_grid(
            canvas,
            icon_dir,
            items,
            (x0 + 18, taxonomy_top, x1 - 18, taxonomy_bottom),
            columns=4,
            label_size=30,
        )
    else:
        allowed = items[:6]
        restricted = items[6:]
        draw.text(
            (x0 + 38, taxonomy_top + 3),
            "ALLOWED DIRECTIONS",
            font=font(28, bold=True),
            fill=accent,
        )
        draw_grid(
            canvas,
            icon_dir,
            allowed,
            (x0 + 20, taxonomy_top + 38, x1 - 20, taxonomy_top + 620),
            columns=3,
            label_size=27,
        )
        draw.text(
            (x0 + 38, taxonomy_top + 660),
            "RESTRICTED ROUTES",
            font=font(28, bold=True),
            fill=accent,
        )
        draw_grid(
            canvas,
            icon_dir,
            restricted,
            (x0 + 20, taxonomy_top + 695, x1 - 20, taxonomy_bottom),
            columns=3,
            label_size=27,
        )

    divider_y = y0 + 1500
    draw.line(
        (x0 + 34, divider_y, x1 - 34, divider_y),
        fill=CARD_BORDER,
        width=4,
    )
    draw.text(
        (x0 + 38, divider_y + 30),
        "VERIFIER EXAMPLE",
        font=font(28, bold=True),
        fill=accent,
    )
    draw.text(
        (x1 - 38, divider_y + 28),
        spec.title,
        font=font(32, bold=True),
        fill=TEXT,
        anchor="ra",
    )

    frame = Image.open(frame_path).convert("RGBA")
    # Keep the scene square; the large paper figure remains easy to compare.
    paste_contain(
        canvas,
        frame,
        (x0 + 34, divider_y + 82, x1 - 34, y1 - 34),
    )


def build_overview(
    repo_root: Path,
    output_dir: Path,
    frame_paths: dict[str, Path],
) -> tuple[Path, Path]:
    canvas = Image.new("RGBA", CANVAS_SIZE, BACKGROUND)
    icon_dir = repo_root / "traffic_bench" / "signs" / "icons"

    margin_x = 58
    gap = 28
    panel_width = (CANVAS_SIZE[0] - 2 * margin_x - 3 * gap) // 4
    top, bottom = 42, CANVAS_SIZE[1] - 42
    for index, spec in enumerate(VERIFIERS):
        left = margin_x + index * (panel_width + gap)
        right = left + panel_width
        draw_group_panel(
            canvas,
            icon_dir,
            frame_paths[spec.run_key],
            spec,
            (left, top, right, bottom),
        )

    png_path = output_dir / "traffic_sign_taxonomy_and_verifiers.png"
    pdf_path = output_dir / "traffic_sign_taxonomy_and_verifiers.pdf"
    rgb = canvas.convert("RGB")
    rgb.save(png_path, dpi=(600, 600), optimize=True)
    rgb.save(pdf_path, "PDF", resolution=600.0)
    return png_path, pdf_path


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    icon_dir = repo_root / "traffic_bench" / "signs" / "icons"
    verifier_dir = output_dir / "verifier_examples"

    frame_paths: dict[str, Path] = {}
    manifest_lines = [
        "category\trun_key\tsource_gif\trepresentative_frame\t"
        "enhanced_gif\tfull_gif"
    ]
    for spec in VERIFIERS:
        source = choose_source_gif(repo_root, spec)
        gif_path, frame_path, frame_index = enhance_gif(
            source,
            verifier_dir,
            icon_dir,
            spec,
        )
        frame_paths[spec.run_key] = frame_path
        full_gif_path = str(
            enhance_full_gif(source, verifier_dir, spec)
        )
        manifest_lines.append(
            f"{spec.category}\t{spec.run_key}\t{source}\t"
            f"{frame_index}\t{gif_path}\t{full_gif_path}"
        )
        print(f"{spec.category}: {source.name} @ frame {frame_index}")

    manifest_path = verifier_dir / "sources.tsv"
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    png_path, pdf_path = build_overview(repo_root, output_dir, frame_paths)
    print(f"Wrote {png_path}")
    print(f"Wrote {pdf_path}")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
