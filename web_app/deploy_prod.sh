#!/usr/bin/env bash
set -euo pipefail

# Figure out where we live and where the repo root is
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Pick up tag from first arg (or fall back to TAG in .env, then to "latest")
TAG=${1:-${TAG:-latest}}
export TAG

# 1) Pull fresh images
docker compose \
  --env-file "$ROOT_DIR/.env" \
  -f "$SCRIPT_DIR/docker_compose_prod.yml" \
  pull

# 2) Recreate containers (force-recreate kills the old ones, avoiding name conflicts)
docker compose \
  --env-file "$ROOT_DIR/.env" \
  -f "$SCRIPT_DIR/docker_compose_prod.yml" \
  up -d --force-recreate --remove-orphans
