#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
model="${1:-all}"
command -v openscad >/dev/null 2>&1 || { echo "OpenSCAD 2021.01+ is required." >&2; exit 2; }
export_one() {
  local id="$1" file="$2" out="$root/dist/hardware/$1"
  mkdir -p "$out"
  local sheet_parts=(lower_deck upper_deck cover_top cover_side lidar_plate)
  local printed_parts=(motor_saddle)
  if [[ "$id" == "rover-one-rev-a" ]]; then printed_parts+=(camera_bracket); fi
  for part in "${sheet_parts[@]}"; do
    openscad -o "$out/$part.dxf" -D "part=\"$part\"" -D 'flat=true' "$file"
  done
  for part in "${printed_parts[@]}"; do
    openscad -o "$out/$part.stl" -D "part=\"$part\"" "$file"
  done
  openscad -o "$out/assembly.png" --imgsize=1600,1000 --viewall -D 'part="assembly"' "$file"
  cp "$root/hardware/$id/BOM.csv" "$root/hardware/$id/README.md" "$root/hardware/$id/wiring.md" "$out/"
  echo "Exported $id to $out"
}
case "$model" in
  rover-one-rev-a) export_one "$model" "$root/hardware/rover-one-rev-a/cad/rover_one.scad" ;;
  triscout-rev-a) export_one "$model" "$root/hardware/triscout-rev-a/cad/triscout.scad" ;;
  all) export_one rover-one-rev-a "$root/hardware/rover-one-rev-a/cad/rover_one.scad"; export_one triscout-rev-a "$root/hardware/triscout-rev-a/cad/triscout.scad" ;;
  *) echo "Usage: $0 {all|rover-one-rev-a|triscout-rev-a}" >&2; exit 2 ;;
esac
