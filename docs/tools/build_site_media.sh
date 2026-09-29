#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INPUT="${ROOT}/video/out/final.mp4"
GAP_SLIDE="${ROOT}/video/out/s09-gap.png"
OUT="${ROOT}/docs/static/media"
SLIDES_OUT="${OUT}/slides"
HF_SLIDES="${ROOT}/dist/hf-traffic-sign-bench/assets/slides"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required to build the website media." >&2
  exit 1
fi

if [[ ! -f "${INPUT}" ]]; then
  echo "Missing source video: ${INPUT}" >&2
  exit 1
fi

mkdir -p "${OUT}" "${SLIDES_OUT}" "${HF_SLIDES}"

# Preserve the authored encode while moving the MP4 metadata to the front so
# playback can begin before the whole file has downloaded.
ffmpeg -hide_banner -loglevel error -y \
  -i "${INPUT}" -map 0 -c copy -movflags +faststart \
  "${OUT}/final.mp4"

# The opening chapter contains the PlanT-2 crosswalk rollout at x=37, y=34.
# Export only that card, not the surrounding slide. The final frame is held so
# STEP 50 · VIOLATION remains readable before the GIF loops.
ffmpeg -hide_banner -loglevel error -y \
  -ss 10.2 -t 5.5 -i "${INPUT}" \
  -filter_complex \
  "[0:v]crop=890:870:37:34,scale=720:720:flags=lanczos,fps=10,tpad=stop_mode=clone:stop_duration=1.4,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle" \
  -loop 0 "${OUT}/crosswalk-plant2.gif"

# The clean benchmark reveal makes a more representative video poster than a
# random first frame.
ffmpeg -hide_banner -loglevel error -y \
  -ss 25.5 -i "${INPUT}" -frames:v 1 \
  -vf "scale=1600:-2:flags=lanczos" -q:v 3 \
  "${OUT}/video-poster.jpg"

# Settled chapter frames for the project-page slides deck / HF dataset card.
declare -A SLIDE_TIMES=(
  [01_problem]=20.8
  [02_benchmark]=28.8
  [03_taxonomy]=43.0
  [04_portability]=56.0
  [05_real_maps]=71.0
  [06_diversity]=86.0
  [08_architecture]=138.0
  [09_conclusion]=171.0
)

for name in 01_problem 02_benchmark 03_taxonomy 04_portability 05_real_maps 06_diversity 08_architecture 09_conclusion; do
  t="${SLIDE_TIMES[${name}]}"
  ffmpeg -hide_banner -loglevel error -y \
    -ss "${t}" -i "${INPUT}" -frames:v 1 \
    -vf "scale=1600:-2:flags=lanczos" -q:v 2 \
    "${SLIDES_OUT}/${name}.jpg"
  cp "${SLIDES_OUT}/${name}.jpg" "${HF_SLIDES}/${name}.jpg"
done

# Prefer the authored gap slide over a mid-animation video frame.
if [[ -f "${GAP_SLIDE}" ]]; then
  cp "${GAP_SLIDE}" "${SLIDES_OUT}/07_baselines.png"
  cp "${GAP_SLIDE}" "${HF_SLIDES}/07_baselines.png"
else
  ffmpeg -hide_banner -loglevel error -y \
    -ss 101.0 -i "${INPUT}" -frames:v 1 \
    -vf "scale=1600:-2:flags=lanczos" -q:v 2 \
    "${SLIDES_OUT}/07_baselines.jpg"
  cp "${SLIDES_OUT}/07_baselines.jpg" "${HF_SLIDES}/07_baselines.jpg"
fi

echo "Website media written to ${OUT}"
echo "Slide frames written to ${SLIDES_OUT} and ${HF_SLIDES}"
