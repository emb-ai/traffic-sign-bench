"""Generate the timed English narration used by the Remotion composition.

The script is intentionally driven by src/config/voiceover.json so the spoken
audio, subtitles, and timing document share one source of truth.
"""

from __future__ import annotations

import asyncio
import argparse
import json
import re
import subprocess
from pathlib import Path

import edge_tts


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "src/config/voiceover.json"
OUTPUT_DIR = ROOT / "public/voiceover"


def media_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def rate_value(rate: str) -> int:
    match = re.fullmatch(r"([+-])(\d+)%", rate)
    if not match:
        raise ValueError(f"Unsupported Edge TTS rate: {rate}")
    value = int(match.group(2))
    return value if match.group(1) == "+" else -value


def format_rate(value: int) -> str:
    return f"{value:+d}%"


async def synthesize(
    *,
    text: str,
    output: Path,
    voice: str,
    rate: str,
    pitch: str,
) -> None:
    temporary = output.with_suffix(".tmp.mp3")
    await edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch,
    ).save(str(temporary))
    temporary.replace(output)


async def main(scene_filter: str | None = None) -> None:
    script = json.loads(SCRIPT_PATH.read_text())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "durations.json"
    report: dict[str, dict[str, float | str]] = {}
    if scene_filter and report_path.exists():
        report = json.loads(report_path.read_text())

    for scene, cues in script["cues"].items():
        if scene_filter and scene != scene_filter:
            continue
        for cue in cues:
            output = OUTPUT_DIR / f"{cue['id']}.mp3"
            text = cue.get("tts", cue["text"])
            target = float(cue["to"]) - float(cue["from"]) - 0.08
            rate = script["rate"]

            for attempt in range(3):
                await synthesize(
                    text=text,
                    output=output,
                    voice=script["voice"],
                    rate=rate,
                    pitch=script["pitch"],
                )
                duration = media_duration(output)
                if duration <= target:
                    break

                current_multiplier = 1 + rate_value(rate) / 100
                required_multiplier = current_multiplier * duration / target * 1.03
                required_rate = round((required_multiplier - 1) * 100)
                if required_rate > 20:
                    raise RuntimeError(
                        f"{cue['id']} needs rate {required_rate:+d}%, "
                        f"which is too fast for clear narration"
                    )
                rate = format_rate(required_rate)
            else:
                raise RuntimeError(f"{cue['id']} still exceeds its cue window")

            report[cue["id"]] = {
                "scene": scene,
                "from": cue["from"],
                "to": cue["to"],
                "duration": round(duration, 3),
                "rate": rate,
            }
            print(
                f"{cue['id']}: {duration:5.2f}s / {target:5.2f}s "
                f"at {rate}"
            )

    report_path.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scene",
        help="Regenerate one scene while preserving the existing duration report",
    )
    args = parser.parse_args()
    asyncio.run(main(args.scene))
