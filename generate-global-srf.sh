#!/bin/bash

# Configuration
output_file="SRF-VPP-CFLA.md"
global_deps_file="global-SRF.md"
mappings_file="mappings.md"

# Start fresh
echo "🧹 Resetting $output_file"
> "$output_file"

# Project title
echo "# VPP-CFLA Software" >> "$output_file"
echo "" >> "$output_file"

# Global Dependencies Section
echo "## Global dependencies" >> "$output_file"
echo "" >> "$output_file"

if [[ -f "$global_deps_file" ]]; then
  cat "$global_deps_file" >> "$output_file"
else
  echo "_No global dependencies found_" >> "$output_file"
fi

echo "" >> "$output_file"

# Parse mappings.md
if [[ -f "$mappings_file" ]]; then
  tail -n +3 "$mappings_file" | while IFS="|" read -r _ component source; do
  component=$(echo "$component" | xargs)
  source=$(echo "$source" | tr -d '\r' | tr '\\' '/' | sed 's/|$//' | xargs)

  echo "🔍 Normalized path: $source"

  srf_path="$source/SRF.md"

  echo "## $component" >> "$output_file"
  echo "" >> "$output_file"

  if [[ -f "$srf_path" ]]; then
    cat "$srf_path" >> "$output_file"
  else
    echo "_SRF.md not found at path: $srf_path_" >> "$output_file"
  fi

  echo "" >> "$output_file"
    done
else
  echo "_No mappings found (missing $mappings_file)_" >> "$output_file"
fi

echo "✅ Global SRF generated at $output_file"
read -rp "Press any key to exit..."