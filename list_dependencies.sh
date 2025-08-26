#!/bin/bash

echo "started"

# Output files
missing_file="missing_licenses.md"
override_file="license_overrides.md"

# Reset missing licenses file
echo "🧹 Resetting $missing_file"
echo "| Package | Version | License | License URL | Description | Source | Catalog URL |" > "$missing_file"
echo "|---------|---------|---------|-------------|-------------|--------|--------------|" >> "$missing_file"

# Track initialized subdirectories
declare -A initialized_dirs
declare -A written_entries

sanitize() {
  echo "$1" | tr '\n\r' ' ' | sed 's/  \+/ /g' | sed 's/|/-/g'
}

is_missing() {
  local val=$(trim "$1")
  [[ -z "$val" || "$val" == "Unknown" || "$val" == "Unknown (invalid or missing response)" ]]
}

trim() {
  local var="$*"
  var="${var#"${var%%[![:space:]]*}"}"
  var="${var%"${var##*[![:space:]]}"}"
  echo -n "$var"
}

lookup_override_license() {
  local pkg="$1"
  local ver="$2"

  if [[ -f "$override_file" ]]; then
    while IFS='|' read -r _ o_pkg o_ver o_license o_licenseUrl o_description o_source _; do
      o_pkg=$(trim "$o_pkg")
      o_ver=$(trim "$o_ver")
      o_license=$(trim "$o_license")
      o_licenseUrl=$(trim "$o_licenseUrl")
      o_description=$(trim "$o_description")
      o_source=$(trim "$o_source")

      [[ "$o_pkg" == "Package" || "$o_pkg" == "----" || -z "$o_pkg" ]] && continue

      if [[ "$o_pkg" == "$pkg" && ( "$o_ver" == "$ver" || "$o_ver" == "latest" || -z "$ver" ) ]]; then
        echo "$o_license|$o_licenseUrl|$o_description|$o_source"
        return 0
      fi
    done < "$override_file"
  fi

  echo ""
}

get_nuget_license() {
  local pkg="$1"
  local ver="$2"
  local project="$3"
  local lower_pkg=$(echo "$pkg" | tr '[:upper:]' '[:lower:]')
  local catalog_url="https://api.nuget.org/v3-flatcontainer/${lower_pkg}/${ver}/${lower_pkg}.nuspec"

  license="Unknown"
  licenseUrl="Unknown"
  description="Unknown"
  source="Unknown"
  projectUrl="Unknown"

  nuspec=$(curl -s -f "$catalog_url")
  if [[ $? -eq 0 && -n "$nuspec" ]]; then
    license=$(echo "$nuspec" | sed -n 's/.*<license type="expression">\([^<]*\)<\/license>.*/\1/p')
    licenseUrl=$(echo "$nuspec" | sed -n 's:.*<licenseUrl>\([^<]*\)</licenseUrl>.*:\1:p')
    description=$(echo "$nuspec" | xmllint --xpath 'string(//*[local-name()="description"])' - 2>/dev/null)
    projectUrl=$(echo "$nuspec" | sed -n 's:.*<projectUrl>\([^<]*\)</projectUrl>.*:\1:p')
    source_repo=$(echo "$nuspec" | sed -n 's/.*<repository [^>]* url="\([^"]*\)".*/\1/p')

    if [[ -n "$source_repo" ]]; then
      source="$source_repo"
    elif [[ -n "$projectUrl" ]]; then
      source="$projectUrl"
    fi
  else
    echo "⚠️ Failed to fetch: $catalog_url" >&2
  fi

  if is_missing "$license" || is_missing "$licenseUrl" || is_missing "$description" || is_missing "$source"; then
    local override=$(lookup_override_license "$pkg" "$ver")
    if [[ -n "$override" ]]; then
      IFS='|' read -r o_license o_licenseUrl o_description o_source <<< "$override"
      [[ -z "$license" || "$license" == "Unknown" ]] && license="$o_license"
      [[ -z "$licenseUrl" || "$licenseUrl" == "Unknown" ]] && licenseUrl="$o_licenseUrl"
      [[ -z "$description" || "$description" == "Unknown" ]] && description="$o_description"
      [[ -z "$source" || "$source" == "Unknown" ]] && source="$o_source"
    fi
  fi

  license=$(sanitize "$license")
  licenseUrl=$(sanitize "$licenseUrl")
  description=$(sanitize "$description")
  source=$(sanitize "$source")

  entry_key="$pkg|$ver"
  if [[ -z "${written_entries[$entry_key]}" ]]; then
    echo "| $pkg | $ver | [$license]($licenseUrl) | $description | $source |" >> "$output_file"
    written_entries[$entry_key]=1
  fi

  if is_missing "$license" || is_missing "$licenseUrl" || is_missing "$description" || is_missing "$source"; then
    missing_key="missing|$pkg|$ver"
    if [[ -z "${written_entries[$missing_key]}" ]]; then
      echo "| $pkg | $ver | $license | $licenseUrl | $description | $source | $catalog_url |" >> "$missing_file"
      written_entries[$missing_key]=1
    fi
  fi
}

# .NET Section
find . -maxdepth 3 -name "*.csproj" | while read -r csproj; do
  project_dir=$(dirname "$csproj")
  base_dir=$(echo "$project_dir" | cut -d'/' -f2)
  output_file="./$base_dir/SRF.md"

  if [[ -z "${initialized_dirs[$base_dir]}" ]]; then
    echo "📝 Resetting $output_file"
    echo "| Package | Version | License | Description | Source |" > "$output_file"
    echo "|---------|---------|---------|-------------|--------|" >> "$output_file"
    initialized_dirs[$base_dir]=1
  fi

  project=$(basename "$csproj")
  echo "🔍 Processing $project"

  grep '<PackageReference' "$csproj" | while read -r line; do
    name=$(echo "$line" | sed -n 's/.*Include="\([^"]*\)".*/\1/p')
    version=$(echo "$line" | sed -n 's/.*Version="\([^"]*\)".*/\1/p')
    [[ -z "$name" || -z "$version" ]] && continue
    get_nuget_license "$name" "$version" "$project"
    echo "✅ Done $name"
  done
done

# Python Section
find . -maxdepth 3 -name "requirements.txt" | while read -r req_file; do
  project_dir=$(dirname "$req_file")
  base_dir=$(echo "$project_dir" | cut -d'/' -f2)
  output_file="./$base_dir/SRF.md"

  if [[ -z "${initialized_dirs[$base_dir]}" ]]; then
    echo "📝 Resetting $output_file"
    echo "| Package | Version | License | Description | Source |" > "$output_file"
    echo "|---------|---------|---------|-------------|--------|" >> "$output_file"
    initialized_dirs[$base_dir]=1
  fi

  echo "🔍 Processing $(basename "$req_file")"
  grep -vE '^#|^\s*$' "$req_file" | while read -r line; do
    pkg=$(echo "$line" | cut -d '=' -f1 | cut -d '<' -f1 | cut -d '>' -f1 | tr -d ' ')
    version=$(echo "$line" | grep -oP '(?<===)[^=<>]+' || echo "")
    version=$(echo "$version" | tr -d '\r\n')
    [[ -z "$pkg" ]] && continue
    [[ -n "$version" ]] && url="https://pypi.org/pypi/${pkg}/${version}/json" || url="https://pypi.org/pypi/${pkg}/json"

    echo "- PKG: $pkg"
    echo "- VERSION: $version"
    echo "- URL: $url"
    json=$(curl -s "$url")
    #echo "- JSON: $json"
    license="Unknown"
    licenseUrl="https://pypi.org/project/$pkg/"
    description="Unknown"
    source="Unknown"
    catalog_url="$url"

    if echo "$json" | jq empty 2>/dev/null; then
      license=$(echo "$json" | jq -r '.info.license // "Unknown"')
      description=$(echo "$json" | jq -r '.info.summary // "Unknown"')
      homepage=$(echo "$json" | jq -r '.info.home_page // empty')
      [[ "$license" == "UNKNOWN" || -z "$license" ]] && license="Unknown"
      [[ -n "$homepage" ]] && source="$homepage"
    else
      license="Unknown (invalid or missing response)"
    fi
    echo "- LICENSE: $license"

    [[ $(echo "$license" | wc -w) -gt 5 ]] && license="Unknown"

    if is_missing "$license" || is_missing "$description" || is_missing "$source"; then
      override=$(lookup_override_license "$pkg" "$version")
      if [[ -n "$override" ]]; then
        IFS='|' read -r o_license o_licenseUrl o_description o_source <<< "$override"
        [[ -z "$license" || "$license" == "Unknown" ]] && license="$o_license"
        [[ -z "$description" || "$description" == "Unknown" ]] && description="$o_description"
        [[ -z "$source" || "$source" == "Unknown" ]] && source="$o_source"
        [[ -z "$licenseUrl" || "$licenseUrl" == "Unknown" ]] && licenseUrl="$o_licenseUrl"
      fi
    fi

    license=$(sanitize "$license")
    licenseUrl=$(sanitize "$licenseUrl")
    description=$(sanitize "$description")
    source=$(sanitize "$source")

    entry_key="$pkg|${version:-latest}"
    if [[ -z "${written_entries[$entry_key]}" ]]; then
      echo "| $pkg | ${version:-latest} | [$license]($licenseUrl) | $description | $source |" >> "$output_file"
      written_entries[$entry_key]=1
    fi

    #if is_missing "$license" || is_missing "$description" || is_missing "$source"; then
    if is_missing "$license"; then
      missing_key="missing|$pkg|${version:-latest}"
      if [[ -z "${written_entries[$missing_key]}" ]]; then
        echo "| $pkg | ${version:-latest} | $license | $licenseUrl | $description | $source | $catalog_url |" >> "$missing_file"
        written_entries[$missing_key]=1
      fi
    fi
    echo "✅ Done $pkg"
  done
done

# Node.js Section
find . -maxdepth 2 -name "package.json" ! -path "*/node_modules/*" | while read -r pkg_json; do
  project_dir=$(dirname "$pkg_json")
  base_dir=$(echo "$project_dir" | cut -d'/' -f2)
  output_file="./$base_dir/SRF.md"

  if [[ -z "${initialized_dirs[$base_dir]}" ]]; then
    echo "📝 Resetting $output_file"
    echo "| Package | Version | License | Description | Source |" > "$output_file"
    echo "|---------|---------|---------|-------------|--------|" >> "$output_file"
    initialized_dirs[$base_dir]=1
  fi

  echo "🔍 Processing $(basename "$pkg_json")"
  jq -r '.dependencies // {} | to_entries[] | "\(.key)@\(.value)"' "$pkg_json" > /tmp/deps.tmp
  jq -r '.devDependencies // {} | to_entries[] | "\(.key)@\(.value)"' "$pkg_json" >> /tmp/deps.tmp

  sort -u /tmp/deps.tmp | while read -r dep; do
    pkg=$(echo "$dep" | cut -d'@' -f1)
    version=$(echo "$dep" | cut -d'@' -f2-)
    [[ -z "$pkg" ]] && continue

    url="https://registry.npmjs.org/$pkg"
    json=$(curl -s "$url")
    catalog_url="$url"

    license="Unknown"
    licenseUrl="https://www.npmjs.com/package/$pkg"
    description="Unknown"
    source="Unknown"

    if echo "$json" | jq empty 2>/dev/null; then
      clean_ver=$(echo "$version" | sed 's/^[^0-9]*//' | cut -d' ' -f1)
      latest_ver=${clean_ver:-$(echo "$json" | jq -r '.["dist-tags"].latest')}
      echo "$pkg $version → $latest_ver"

      license=$(echo "$json" | jq -r --arg ver "$latest_ver" '.versions[$ver].license // "Unknown"')
      description=$(echo "$json" | jq -r --arg ver "$latest_ver" '.versions[$ver].description // "Unknown"')
      homepage=$(echo "$json" | jq -r --arg ver "$latest_ver" '.versions[$ver].homepage // empty')
      repo=$(echo "$json" | jq -r --arg ver "$latest_ver" '.versions[$ver].repository.url // empty')
      [[ -n "$repo" ]] && source="$repo"
      [[ -z "$source" && -n "$homepage" ]] && source="$homepage"
    else
      license="Unknown (invalid or missing response)"
    fi

    [[ $(echo "$license" | wc -w) -gt 5 ]] && license="Unknown"

    if is_missing "$license" || is_missing "$description" || is_missing "$source"; then
      override=$(lookup_override_license "$pkg" "$version")
      if [[ -n "$override" ]]; then
        IFS='|' read -r o_license o_licenseUrl o_description o_source <<< "$override"
        [[ -z "$license" || "$license" == "Unknown" ]] && license="$o_license"
        [[ -z "$licenseUrl" || "$licenseUrl" == "Unknown" ]] && licenseUrl="$o_licenseUrl"
        [[ -z "$description" || "$description" == "Unknown" ]] && description="$o_description"
        [[ -z "$source" || "$source" == "Unknown" ]] && source="$o_source"
      fi
    fi

    license=$(sanitize "$license")
    licenseUrl=$(sanitize "$licenseUrl")
    description=$(sanitize "$description")
    source=$(sanitize "$source")

    entry_key="$pkg|${version:-latest}"
    if [[ -z "${written_entries[$entry_key]}" ]]; then
      echo "| $pkg | ${version:-latest} | [$license]($licenseUrl) | $description | $source |" >> "$output_file"
      written_entries[$entry_key]=1
    fi

    if is_missing "$license" || is_missing "$description" || is_missing "$source"; then
      missing_key="missing|$pkg|${version:-latest}"
      if [[ -z "${written_entries[$missing_key]}" ]]; then
        echo "| $pkg | ${version:-latest} | $license | $licenseUrl | $description | $source | $catalog_url |" >> "$missing_file"
        written_entries[$missing_key]=1
      fi
    fi

    echo "✅ Done $pkg"
  done
done

echo "✅ All dependencies and licenses saved to SRF.md files"
echo "⚠️ Packages with missing licenses saved to $missing_file"
read -rp "Press any key to exit..."
