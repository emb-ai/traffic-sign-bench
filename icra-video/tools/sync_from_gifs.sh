#!/usr/bin/env bash
# Sync video assets from icra-video/gifs/ → icra-video/public/ for Remotion.
# Source of truth for sign icons is gifs/icons/ (not traffic_bench/signs/icons/).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GIFS="$ROOT/gifs"
PUBLIC="$ROOT/public"

if [[ ! -d "$GIFS/icons" ]]; then
  echo "missing $GIFS/icons — copy project icons there first" >&2
  exit 1
fi

mkdir -p "$PUBLIC/signs" "$PUBLIC/taxonomy/extra"

echo "→ public/signs/  (from gifs/icons/)"
cp -a "$GIFS/icons/." "$PUBLIC/signs/"

# Vienna-convention extras used by S02B_Taxonomy (already live under gifs/signs/<class>/)
if [[ -d "$GIFS/signs" ]]; then
  echo "→ public/taxonomy/extra/  (from gifs/signs/*)"
  find "$GIFS/signs" -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' \) \
    -exec cp -a {} "$PUBLIC/taxonomy/extra/" \;
fi

echo "done."
echo "  signs: $(ls -1 "$PUBLIC/signs" | wc -l)"
echo "  taxonomy/extra: $(ls -1 "$PUBLIC/taxonomy/extra" | wc -l)"
