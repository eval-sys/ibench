#!/usr/bin/env bash
set -euo pipefail
# The environment supplies Music Library and admin (server/initial_setup.go).
# Only the missing song data is owned by this issue. Import real tagged files.
fixture_music=/tmp/navidrome-runtime/music/composer-studies
mkdir -p "$fixture_music"
while IFS='|' read -r file title composer track; do
  ffmpeg -nostdin -hide_banner -loglevel error -y -f lavfi -i 'anullsrc=r=44100:cl=stereo' \
    -t 12 -c:a flac -metadata title="$title" -metadata artist='Chamber Ensemble' \
    -metadata album_artist='Chamber Ensemble' -metadata album='Composer Studies' \
    -metadata composer="$composer" -metadata track="$track" -metadata date=2024 \
    "$fixture_music/$file"
  # Scan after each new file so table insertion order is independent of worker scheduling.
  /workspace/app/navidrome scan --full --target 1:composer-studies \
    --datafolder /tmp/navidrome-runtime/data --musicfolder /tmp/navidrome-runtime/music
done <<'TRACKS'
01-amber.flac|Amber Waltz|Clara Vale|1
02-blue.flac|Blue Nocturne|Ada Rowan|2
03-cedar.flac|Cedar Prelude|Dorian Lake|3
04-dawn.flac|Dawn Sonata|Bruno Reed|4
TRACKS
