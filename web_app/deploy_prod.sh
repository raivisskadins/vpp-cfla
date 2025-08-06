#!/usr/bin/env bash
set -euo pipefail


SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"


TAG=${1:-${TAG:-latest}}
export TAG


docker compose \
  --env-file "$ROOT_DIR/.env" \
  -f "$SCRIPT_DIR/docker_compose_prod.yml" \
  pull


docker compose \
  --env-file "$ROOT_DIR/.env" \
  -f "$SCRIPT_DIR/docker_compose_prod.yml" \
  up -d --force-recreate --remove-orphans
