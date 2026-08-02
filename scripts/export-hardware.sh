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

  # OpenSCAD 2021.01 can return 1 for valid multi-body CSG exports. The gate
  # therefore validates the artifact itself rather than trusting that exit code.
  local csg="$out/assembly.csg"
  if ! openscad -o "$csg" "${defines[@]}" "$preview"; then
    if [[ ! -s "$csg" ]]; then
      echo "Assembly CSG export failed for $id" >&2
      exit 1
    fi
    echo "Warning: OpenSCAD returned non-zero after producing $csg; artifact retained and validated." >&2
  fi
  [[ -s "$csg" ]] || { echo "Assembly CSG is empty for $id" >&2; exit 1; }

  # A combined STL is convenient for interference review but multi-body visual
  # assemblies are not fabrication solids. Generate it only when explicitly asked.
  if [[ "${OPENPATROL_EXPORT_ASSEMBLY_STL:-0}" == "1" ]]; then
    if ! openscad -o "$out/assembly.stl" "${defines[@]}" "$preview"; then
      if [[ -s "$out/assembly.stl" ]]; then
        echo "Warning: OpenSCAD returned non-zero after producing assembly.stl." >&2
      else
        rm -f "$out/assembly.stl"
        echo "Warning: combined assembly STL unavailable; CSG and fabrication parts remain valid." >&2
      fi
    fi
  fi

  # Product screenshots are useful locally but are not an engineering gate.
  if [[ "${OPENPATROL_RENDER_PREVIEWS:-0}" == "1" ]]; then
    if openscad -o "$out/assembly.png" --imgsize=1600,1000 --viewall \
      --preview=throwntogether "${defines[@]}" "$preview"; then
      echo "Rendered $out/assembly.png"
    else
      rm -f "$out/assembly.png"
      echo "Warning: PNG preview unavailable; assembly CSG and fabrication files are valid." >&2
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
