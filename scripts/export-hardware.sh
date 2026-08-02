#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
model="${1:-all}"
command -v openscad >/dev/null 2>&1 || { echo "OpenSCAD 2021.01+ is required." >&2; exit 2; }

copy_pack_docs() {
  local id="$1" out="$2"
  for file in BOM.csv README.md wiring.md drawings.md mast-protocol.md; do
    [[ -f "$root/hardware/$id/$file" ]] && cp "$root/hardware/$id/$file" "$out/"
  done
}

export_part() {
  local file="$1" out="$2" part="$3" format="$4"
  if [[ "$format" == "dxf" ]]; then
    openscad -o "$out/$part.dxf" -D "part=\"$part\"" -D 'flat=true' "$file"
  else
    openscad -o "$out/$part.stl" -D "part=\"$part\"" "$file"
  fi
}

export_assembly() {
  local id="$1" preview="$2" out="$3"
  local defines=(-D 'part="assembly"')
  [[ "$id" == "sentinel-rev-a" ]] && defines+=(-D 'mast_extension=1')

  # OpenSCAD 2021.01 sometimes returns 1 after successfully writing a valid
  # multi-body STL. Engineering acceptance therefore checks the artifact, not
  # merely the process exit code.
  local stl="$out/assembly.stl"
  local rc=0
  openscad -o "$stl" "${defines[@]}" "$preview" || rc=$?
  if [[ ! -s "$stl" ]]; then
    echo "Assembly STL export failed for $id (OpenSCAD exit $rc)" >&2
    exit 1
  fi
  if [[ "$rc" -ne 0 ]]; then
    echo "Warning: OpenSCAD exited $rc after producing a non-empty $stl; artifact retained." >&2
  fi

  # Product screenshots are useful locally but are not an engineering gate.
  if [[ "${OPENPATROL_RENDER_PREVIEWS:-0}" == "1" ]]; then
    if openscad -o "$out/assembly.png" --imgsize=1600,1000 --viewall \
      --preview=throwntogether "${defines[@]}" "$preview"; then
      echo "Rendered $out/assembly.png"
    else
      rm -f "$out/assembly.png"
      echo "Warning: PNG preview unavailable; assembly STL and fabrication files are valid." >&2
    fi
  fi
}

export_one() {
  local id="$1" file="$2" preview="$3"
  shift 3
  local out="$root/dist/hardware/$id"
  rm -rf "$out"
  mkdir -p "$out"
  local mode="sheet"
  local part
  for part in "$@"; do
    if [[ "$part" == "--printed" ]]; then mode="printed"; continue; fi
    if [[ "$mode" == "sheet" ]]; then
      export_part "$file" "$out" "$part" dxf
    else
      export_part "$file" "$out" "$part" stl
    fi
  done
  export_assembly "$id" "$preview" "$out"
  copy_pack_docs "$id" "$out"
  echo "Exported $id to $out"
}

export_rover() {
  export_one rover-one-rev-a \
    "$root/hardware/rover-one-rev-a/cad/rover_one.scad" \
    "$root/hardware/rover-one-rev-a/cad/rover_one_family.scad" \
    lower_deck upper_deck cover_top cover_side lidar_plate bumper_bar \
    --printed motor_saddle camera_bracket corner_block cable_guide
}

export_triscout() {
  export_one triscout-rev-a \
    "$root/hardware/triscout-rev-a/cad/triscout.scad" \
    "$root/hardware/triscout-rev-a/cad/triscout_family.scad" \
    lower_deck upper_deck cover_top cover_side lidar_plate bumper_bar \
    --printed motor_saddle camera_bracket corner_block cable_guide
}

export_airscout() {
  export_one airscout-rev-a \
    "$root/hardware/airscout-rev-a/cad/airscout.scad" \
    "$root/hardware/airscout-rev-a/cad/airscout.scad" \
    lower_plate upper_plate camera_plate battery_tray \
    --printed arm_clamp motor_mount landing_leg prop_guard_segment gps_mast shell_top shell_bottom
}

export_sentinel() {
  export_one sentinel-rev-a \
    "$root/hardware/sentinel-rev-a/cad/sentinel.scad" \
    "$root/hardware/sentinel-rev-a/cad/sentinel.scad" \
    lower_deck upper_deck torso_base mast_base head_plate cover_front cover_side bumper_bar \
    --printed motor_saddle mast_bushing mask_frame head_shell corner_block cable_guide led_bezel
}

case "$model" in
  rover-one-rev-a) export_rover ;;
  triscout-rev-a) export_triscout ;;
  airscout-rev-a) export_airscout ;;
  sentinel-rev-a) export_sentinel ;;
  all) export_rover; export_triscout; export_airscout; export_sentinel ;;
  *) echo "Usage: $0 {all|rover-one-rev-a|triscout-rev-a|airscout-rev-a|sentinel-rev-a}" >&2; exit 2 ;;
esac
